"""Journal d'audit des actions admin."""
from __future__ import annotations

import json
from datetime import datetime


def log_audit(conn, admin_id, action, entity, entity_id=None, diff=None):
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log (created_at, admin_id, action, entity, entity_id, diff)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                str(admin_id or "")[:40],
                (action or "")[:40],
                (entity or "")[:80],
                str(entity_id) if entity_id is not None else None,
                json.dumps(diff or {}, ensure_ascii=False)[:4000],
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"Erreur audit: {e}")
