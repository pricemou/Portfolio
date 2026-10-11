"""Routes admin/contenu ajoutées (career, certifications, monitoring, pages légales)."""
from __future__ import annotations

from datetime import datetime

from flask import jsonify, render_template, request, session
from database import get_db, row_to_dict, rows_to_list
from utils.privacy import client_ip_from_request, hash_ip
from utils.security_log import log_security_event, recent_security_stats


def register_extra_routes(app, admin_required, sanitize_input):
    @app.route('/confidentialite')
    def page_confidentialite():
        return _render_site_page('confidentialite')

    @app.route('/mentions-legales')
    def page_mentions():
        return _render_site_page('mentions')

    def _render_site_page(slug):
        page = {'slug': slug, 'title': slug, 'body': ''}
        try:
            with get_db() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM site_pages WHERE slug = ?', (slug,))
                    row = cursor.fetchone()
                    if row:
                        page = row_to_dict(row)
        except Exception as e:
            app.logger.error(f"Erreur page {slug}: {e}")
        return render_template(
            'legal.html',
            page=page,
            current_year=datetime.now().year,
            homepage_data=None,
        )

    @app.route('/api/career', methods=['GET'])
    @admin_required
    def api_career_list():
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM career
                    WHERE deleted_at IS NULL OR deleted_at = ''
                    ORDER BY order_index ASC, id ASC
                ''')
                return jsonify(rows_to_list(cursor.fetchall()))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/career', methods=['POST'])
    @admin_required
    def api_career_create():
        data = request.get_json(silent=True) or {}
        title = sanitize_input(data.get('title'), 200)
        if not title:
            return jsonify({'error': 'title requis'}), 400
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO career (title, org, location, start, end, kind, bullets, order_index, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        title,
                        sanitize_input(data.get('org'), 200),
                        sanitize_input(data.get('location'), 120),
                        sanitize_input(data.get('start'), 40),
                        sanitize_input(data.get('end'), 40),
                        sanitize_input(data.get('kind') or 'emploi', 40),
                        sanitize_input(data.get('bullets'), 2000),
                        int(data.get('order_index') or 0),
                        sanitize_input(data.get('status') or 'published', 40),
                    ),
                )
                conn.commit()
                return jsonify({'success': True, 'id': cursor.lastrowid}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/career/<int:item_id>', methods=['PUT'])
    @admin_required
    def api_career_update(item_id):
        data = request.get_json(silent=True) or {}
        fields = []
        values = []
        mapping = {
            'title': 200, 'org': 200, 'location': 120, 'start': 40, 'end': 40,
            'kind': 40, 'bullets': 2000, 'status': 40,
        }
        for key, maxlen in mapping.items():
            if key in data:
                fields.append(f'{key} = ?')
                values.append(sanitize_input(data.get(key), maxlen))
        if 'order_index' in data:
            fields.append('order_index = ?')
            values.append(int(data.get('order_index') or 0))
        if not fields:
            return jsonify({'error': 'Aucun champ'}), 400
        values.append(item_id)
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'''
                    UPDATE career SET {', '.join(fields)}
                    WHERE id = ? AND (deleted_at IS NULL OR deleted_at = '')
                    ''',
                    values,
                )
                if cursor.rowcount < 1:
                    return jsonify({'error': 'Entrée introuvable'}), 404
                from utils.audit import log_audit
                log_audit(conn, session.get('admin_id'), 'update', 'career', item_id, data)
                conn.commit()
                return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/career/<int:item_id>', methods=['DELETE'])
    @admin_required
    def api_career_delete(item_id):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    UPDATE career SET deleted_at = CURRENT_TIMESTAMP, status = 'archived'
                    WHERE id = ? AND (deleted_at IS NULL OR deleted_at = '')
                    ''',
                    (item_id,),
                )
                if cursor.rowcount < 1:
                    return jsonify({'error': 'Entrée introuvable'}), 404
                from utils.audit import log_audit
                log_audit(conn, session.get('admin_id'), 'soft_delete', 'career', item_id)
                conn.commit()
                return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/certifications', methods=['GET'])
    @admin_required
    def api_certs_list():
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT * FROM certifications
                    WHERE deleted_at IS NULL OR deleted_at = ''
                    ORDER BY featured DESC, order_index ASC, id ASC
                    '''
                )
                return jsonify(rows_to_list(cursor.fetchall()))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/certifications', methods=['POST'])
    @admin_required
    def api_certs_create():
        data = request.get_json(silent=True) or {}
        title = sanitize_input(data.get('title'), 300)
        code = sanitize_input(data.get('code'), 64)
        if not title or not code:
            return jsonify({'error': 'title et code requis'}), 400
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO certifications
                    (domain, title, code, url, skill_fr, skill_en, featured, order_index, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        sanitize_input(data.get('domain'), 80),
                        title,
                        code,
                        sanitize_input(data.get('url'), 500),
                        sanitize_input(data.get('skill_fr'), 500),
                        sanitize_input(data.get('skill_en'), 500),
                        1 if data.get('featured') else 0,
                        int(data.get('order_index') or 0),
                        sanitize_input(data.get('status') or 'published', 40),
                    ),
                )
                conn.commit()
                return jsonify({'success': True, 'id': cursor.lastrowid}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/certifications/<int:item_id>', methods=['PUT'])
    @admin_required
    def api_certs_update(item_id):
        data = request.get_json(silent=True) or {}
        fields, values = [], []
        for key, maxlen in {
            'domain': 80, 'title': 300, 'code': 64, 'url': 500,
            'skill_fr': 500, 'skill_en': 500, 'status': 40,
        }.items():
            if key in data:
                fields.append(f'{key} = ?')
                values.append(sanitize_input(data.get(key), maxlen))
        if 'featured' in data:
            fields.append('featured = ?')
            values.append(1 if data.get('featured') else 0)
        if 'order_index' in data:
            fields.append('order_index = ?')
            values.append(int(data.get('order_index') or 0))
        if not fields:
            return jsonify({'error': 'Aucun champ'}), 400
        fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(item_id)
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE certifications SET {', '.join(fields)} WHERE id = ?",
                    values,
                )
                conn.commit()
                return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/certifications/<int:item_id>', methods=['DELETE'])
    @admin_required
    def api_certs_delete(item_id):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE certifications
                    SET status='archived', deleted_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (item_id,),
                )
                from utils.audit import log_audit
                log_audit(conn, session.get('admin_id'), 'soft_delete', 'certifications', item_id)
                conn.commit()
                return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/monitoring/overview', methods=['GET'])
    @admin_required
    def api_monitoring_overview():
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM analytics WHERE type='page_view' AND date = date('now')"
                )
                views_today = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM analytics WHERE type='visitor' AND date = date('now')"
                )
                visitors_today = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM contacts WHERE read = 0")
                unread = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM error_logs WHERE resolved = 0")
                open_errors = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM login_history
                    WHERE success = 0 AND login_time >= datetime('now', '-24 hours')
                    """
                )
                failed_logins = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM security_events
                    WHERE severity IN ('warning', 'critical')
                      AND created_at >= datetime('now', '-24 hours')
                    """
                )
                security_alerts = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT created_at, type, severity, path
                    FROM security_events
                    ORDER BY id DESC LIMIT 15
                    """
                )
                recent_security = rows_to_list(cursor.fetchall())
                cursor.execute(
                    """
                    SELECT created_at, level, message, path, resolved
                    FROM error_logs
                    ORDER BY id DESC LIMIT 15
                    """
                )
                recent_errors = rows_to_list(cursor.fetchall())
                return jsonify({
                    'views_today': views_today,
                    'visitors_today': visitors_today,
                    'unread_contacts': unread,
                    'open_errors': open_errors,
                    'failed_logins_24h': failed_logins,
                    'security_alerts_24h': security_alerts,
                    'security_breakdown': recent_security_stats(conn, 24),
                    'recent_security': recent_security,
                    'recent_errors': recent_errors,
                })
        except Exception as e:
            app.logger.error(f"monitoring overview: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/site-pages/<slug>', methods=['GET', 'PUT'])
    @admin_required
    def api_site_page(slug):
        slug = sanitize_input(slug, 80)
        if slug not in ('confidentialite', 'mentions'):
            return jsonify({'error': 'slug invalide'}), 400
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                if request.method == 'GET':
                    cursor.execute('SELECT * FROM site_pages WHERE slug = ?', (slug,))
                    row = cursor.fetchone()
                    return jsonify(row_to_dict(row) or {})
                data = request.get_json(silent=True) or {}
                title = sanitize_input(data.get('title'), 200)
                body = sanitize_input(data.get('body'), 20000)
                cursor.execute(
                    '''
                    INSERT INTO site_pages (slug, title, body, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(slug) DO UPDATE SET
                        title=excluded.title,
                        body=excluded.body,
                        updated_at=CURRENT_TIMESTAMP
                    ''',
                    (slug, title, body),
                )
                conn.commit()
                return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
