"""API monitoring cybersécurité (données simulées CSV) — section admin."""
from __future__ import annotations

import os
from pathlib import Path

from flask import jsonify, request, session

from cyber_monitoring.data_engine import (
    apply_filters,
    build_dashboard_payload,
    default_events_path,
    filter_options,
    load_events,
    save_events_csv,
)
from utils.audit import log_audit
from database import get_db


# Cache mémoire simple du DataFrame courant (session upload ou défaut)
_DATA_CACHE: dict = {'df': None, 'source': 'default', 'mtime': None}


def _parse_list(value) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return items or None
    if isinstance(value, str):
        items = [v.strip() for v in value.split(',') if v.strip()]
        return items or None
    return None


def _get_base_df():
    """Charge le CSV actif (upload mémoire ou fichier simulé par défaut)."""
    if _DATA_CACHE.get('source') == 'upload' and _DATA_CACHE.get('df') is not None:
        return _DATA_CACHE['df']
    path = default_events_path()
    mtime = path.stat().st_mtime if path.exists() else None
    if _DATA_CACHE['df'] is None or _DATA_CACHE.get('mtime') != mtime:
        _DATA_CACHE['df'] = load_events(path if path.exists() else None)
        _DATA_CACHE['source'] = 'default'
        _DATA_CACHE['mtime'] = path.stat().st_mtime if path.exists() else None
    return _DATA_CACHE['df']


def register_cyber_routes(app, admin_required, sanitize_input):
    upload_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'cyber_monitoring' / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.route('/api/admin/cyber/options', methods=['GET'])
    @admin_required
    def api_cyber_options():
        try:
            df = _get_base_df()
            return jsonify({'success': True, 'options': filter_options(df), 'source': _DATA_CACHE['source']})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/cyber/dashboard', methods=['GET', 'POST'])
    @admin_required
    def api_cyber_dashboard():
        try:
            payload_in = request.get_json(silent=True) or {}
            args = request.args
            date_start = payload_in.get('date_start') or args.get('date_start')
            date_end = payload_in.get('date_end') or args.get('date_end')
            granularity = sanitize_input(
                payload_in.get('granularity') or args.get('granularity') or 'heure', 20
            )
            if granularity not in ('heure', 'jour'):
                granularity = 'heure'
            top_dimension = sanitize_input(
                payload_in.get('top_dimension') or args.get('top_dimension') or 'adresse_ip', 40
            )
            donut_mode = sanitize_input(
                payload_in.get('donut_mode') or args.get('donut_mode') or 'type_utilisateur', 40
            )

            df = apply_filters(
                _get_base_df(),
                date_start=date_start,
                date_end=date_end,
                pays=_parse_list(payload_in.get('pays') or args.get('pays')),
                type_activite=_parse_list(payload_in.get('type_activite') or args.get('type_activite')),
                gravite=_parse_list(payload_in.get('gravite') or args.get('gravite')),
                type_utilisateur=_parse_list(payload_in.get('type_utilisateur') or args.get('type_utilisateur')),
                service_cible=_parse_list(payload_in.get('service_cible') or args.get('service_cible')),
            )
            data = build_dashboard_payload(
                df,
                granularity=granularity,
                top_dimension=top_dimension,
                donut_mode=donut_mode,
            )
            data['source'] = _DATA_CACHE['source']
            data['options'] = filter_options(_get_base_df())
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            app.logger.exception('cyber dashboard')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/cyber/upload', methods=['POST'])
    @admin_required
    def api_cyber_upload():
        if 'file' not in request.files:
            return jsonify({'error': 'fichier CSV requis'}), 400
        f = request.files['file']
        if not f.filename or not f.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Seuls les fichiers .csv sont acceptés'}), 400
        try:
            raw = f.read()
            if len(raw) > 40 * 1024 * 1024:
                return jsonify({'error': 'Fichier trop volumineux (max 40 Mo)'}), 400
            df = load_events(raw)
            # Persister l'upload admin (remplace le jeu actif en mémoire)
            dest = upload_dir / 'events_uploaded.csv'
            save_events_csv(df, dest)
            _DATA_CACHE['df'] = df
            _DATA_CACHE['source'] = 'upload'
            _DATA_CACHE['mtime'] = dest.stat().st_mtime
            try:
                with get_db() as conn:
                    log_audit(
                        conn, session.get('admin_id'), 'upload', 'cyber_events',
                        None, {'rows': len(df), 'filename': sanitize_input(f.filename, 200)},
                    )
                    conn.commit()
            except Exception:
                pass
            return jsonify({
                'success': True,
                'rows': int(len(df)),
                'message': f'CSV chargé ({len(df)} événements)',
                'options': filter_options(df),
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/cyber/reset', methods=['POST'])
    @admin_required
    def api_cyber_reset():
        """Revenir au jeu de données simulé par défaut."""
        try:
            _DATA_CACHE['source'] = 'default'
            _DATA_CACHE['df'] = None
            _DATA_CACHE['mtime'] = None
            df = _get_base_df()
            return jsonify({
                'success': True,
                'rows': int(len(df)),
                'options': filter_options(df),
                'message': 'Jeu simulé restauré',
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
