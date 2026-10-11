"""Routes avancées : 2FA, médiathèque, corbeille, audit."""
from __future__ import annotations

import os

from flask import jsonify, request, session
from database import get_db, rows_to_list
from utils.audit import log_audit
from utils.media_library import validate_and_save
from utils.security_log import log_security_event
from utils.totp_2fa import (
    consume_backup_code,
    generate_backup_codes,
    generate_totp_secret,
    hash_backup_codes,
    provisioning_uri,
    seal_secret,
    totp_available,
    unseal_secret,
    verify_totp,
)


SOFT_DELETE_ENTITIES = {
    'projects': 'projects',
    'career': 'career',
    'certifications': 'certifications',
    'skills': 'skills',
    'partners': 'partners',
    'media': 'media_assets',
}


def register_advanced_routes(app, admin_required, sanitize_input):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    @app.route('/api/admin/2fa/setup', methods=['POST'])
    @admin_required
    def api_2fa_setup():
        if not totp_available():
            return jsonify({'error': 'pyotp non installé sur le serveur'}), 503
        username = session.get('admin_username') or 'admin'
        secret = generate_totp_secret()
        session['pending_totp_secret'] = secret
        return jsonify({
            'secret': secret,
            'otpauth_url': provisioning_uri(secret, username),
            'message': 'Scannez le secret dans votre application TOTP, puis confirmez avec /api/admin/2fa/enable',
        })

    @app.route('/api/admin/2fa/enable', methods=['POST'])
    @admin_required
    def api_2fa_enable():
        data = request.get_json(silent=True) or {}
        code = sanitize_input(data.get('code'), 12)
        secret = session.get('pending_totp_secret')
        if not secret or not verify_totp(secret, code):
            return jsonify({'error': 'Code TOTP invalide'}), 400
        codes = generate_backup_codes()
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    UPDATE admin_users
                    SET totp_secret = ?, totp_enabled = 1, backup_codes = ?
                    WHERE id = ?
                    ''',
                    (seal_secret(secret), hash_backup_codes(codes), session.get('admin_id')),
                )
                log_audit(conn, session.get('admin_id'), 'enable_2fa', 'admin_users', session.get('admin_id'))
                conn.commit()
            session.pop('pending_totp_secret', None)
            return jsonify({
                'success': True,
                'backup_codes': codes,
                'warning': 'Conservez ces codes de secours : ils ne seront plus réaffichés.',
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/2fa/disable', methods=['POST'])
    @admin_required
    def api_2fa_disable():
        data = request.get_json(silent=True) or {}
        code = sanitize_input(data.get('code'), 12)
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT totp_secret, totp_enabled FROM admin_users WHERE id = ?',
                    (session.get('admin_id'),),
                )
                row = cursor.fetchone()
                if not row or not row['totp_enabled']:
                    return jsonify({'error': '2FA déjà désactivée'}), 400
                secret = unseal_secret(row['totp_secret'])
                if not verify_totp(secret, code):
                    return jsonify({'error': 'Code TOTP invalide'}), 400
                cursor.execute(
                    '''
                    UPDATE admin_users
                    SET totp_secret = NULL, totp_enabled = 0, backup_codes = NULL
                    WHERE id = ?
                    ''',
                    (session.get('admin_id'),),
                )
                log_audit(conn, session.get('admin_id'), 'disable_2fa', 'admin_users', session.get('admin_id'))
                conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/2fa/status', methods=['GET'])
    @admin_required
    def api_2fa_status():
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT totp_enabled FROM admin_users WHERE id = ?',
                    (session.get('admin_id'),),
                )
                row = cursor.fetchone()
                enabled = bool(row and row['totp_enabled'])
            return jsonify({'enabled': enabled, 'available': totp_available()})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/media', methods=['GET'])
    @admin_required
    def api_media_list():
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT * FROM media_assets
                    WHERE deleted_at IS NULL
                    ORDER BY id DESC
                    '''
                )
                return jsonify(rows_to_list(cursor.fetchall()))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/media', methods=['POST'])
    @admin_required
    def api_media_upload():
        if 'file' not in request.files:
            return jsonify({'error': 'fichier requis'}), 400
        try:
            meta = validate_and_save(request.files['file'], base_dir)
            alt = sanitize_input(request.form.get('alt_text'), 200)
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO media_assets (filename, original_name, path, mime_hint, size, alt_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        meta['filename'], meta['original_name'], meta['path'],
                        meta['mime_hint'], meta['size'], alt,
                    ),
                )
                asset_id = cursor.lastrowid
                log_audit(conn, session.get('admin_id'), 'create', 'media_assets', asset_id, meta)
                log_security_event(
                    conn, 'upload_ok', severity='info', path='/api/media',
                    ip_address=request.remote_addr or '',
                    details={'filename': meta['filename']},
                )
                conn.commit()
            return jsonify({'success': True, 'asset': {**meta, 'id': asset_id, 'url': f"/static/{meta['path']}"}}), 201
        except ValueError as e:
            try:
                with get_db() as conn:
                    log_security_event(
                        conn, 'upload_rejected', severity='warning', path='/api/media',
                        ip_address=request.remote_addr or '',
                        details={'reason': str(e)},
                    )
            except Exception:
                pass
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/media/<int:asset_id>', methods=['DELETE'])
    @admin_required
    def api_media_delete(asset_id):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE media_assets SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
                    (asset_id,),
                )
                log_audit(conn, session.get('admin_id'), 'soft_delete', 'media_assets', asset_id)
                conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/trash', methods=['GET'])
    @admin_required
    def api_trash_list():
        items = []
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                for key, table in SOFT_DELETE_ENTITIES.items():
                    title_col = 'title' if table != 'media_assets' else 'original_name'
                    if table == 'partners':
                        title_col = 'name'
                    if table == 'skills':
                        title_col = 'title'
                    cursor.execute(
                        f'''
                        SELECT id, {title_col} AS label, deleted_at
                        FROM {table}
                        WHERE deleted_at IS NOT NULL
                        ORDER BY deleted_at DESC
                        LIMIT 50
                        '''
                    )
                    for row in cursor.fetchall():
                        d = dict(row)
                        items.append({
                            'entity': key,
                            'id': d['id'],
                            'label': d.get('label') or f'#{d["id"]}',
                            'deleted_at': d.get('deleted_at'),
                        })
            items.sort(key=lambda x: x.get('deleted_at') or '', reverse=True)
            return jsonify(items[:100])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/trash/restore', methods=['POST'])
    @admin_required
    def api_trash_restore():
        data = request.get_json(silent=True) or {}
        entity = data.get('entity')
        item_id = data.get('id')
        table = SOFT_DELETE_ENTITIES.get(entity)
        if not table or item_id is None:
            return jsonify({'error': 'entity/id requis'}), 400
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'UPDATE {table} SET deleted_at = NULL WHERE id = ?',
                    (int(item_id),),
                )
                if table == 'certifications':
                    cursor.execute(
                        "UPDATE certifications SET status = 'published' WHERE id = ?",
                        (int(item_id),),
                    )
                log_audit(conn, session.get('admin_id'), 'restore', table, item_id)
                conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/trash/purge', methods=['POST'])
    @admin_required
    def api_trash_purge():
        data = request.get_json(silent=True) or {}
        entity = data.get('entity')
        item_id = data.get('id')
        table = SOFT_DELETE_ENTITIES.get(entity)
        if not table or item_id is None:
            return jsonify({'error': 'entity/id requis'}), 400
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'DELETE FROM {table} WHERE id = ? AND deleted_at IS NOT NULL',
                    (int(item_id),),
                )
                log_audit(conn, session.get('admin_id'), 'purge', table, item_id)
                conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/audit', methods=['GET'])
    @admin_required
    def api_audit_list():
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM audit_log ORDER BY id DESC LIMIT 100'
                )
                return jsonify(rows_to_list(cursor.fetchall()))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
