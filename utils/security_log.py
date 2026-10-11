"""Journalisation sécurité et erreurs pour le dashboard admin."""
from __future__ import annotations

import json
from datetime import datetime

from utils.privacy import hash_ip


def log_security_event(conn, event_type, severity="info", path="", ip_address="", details=None):
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO security_events (created_at, type, severity, path, ip_hash, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                (event_type or "unknown")[:80],
                (severity or "info")[:20],
                (path or "")[:500],
                hash_ip(ip_address),
                json.dumps(details or {}, ensure_ascii=False)[:2000],
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"Erreur log_security_event: {e}")


def log_error_event(conn, source, level, message, path="", user_agent="", stack=""):
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO error_logs (created_at, source, level, message, stack, path, user_agent, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                (source or "server")[:40],
                (level or "error")[:20],
                (message or "")[:1000],
                (stack or "")[:3000],
                (path or "")[:500],
                (user_agent or "")[:500],
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"Erreur log_error_event: {e}")


def recent_security_stats(conn, hours=24):
    if conn is None:
        return {}
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT type, severity, COUNT(*) as n
        FROM security_events
        WHERE created_at >= datetime('now', ?)
        GROUP BY type, severity
        """,
        (f"-{int(hours)} hours",),
    )
    rows = cursor.fetchall()
    return [
        {
            "type": r[0] if not hasattr(r, "keys") else r["type"],
            "severity": r[1] if not hasattr(r, "keys") else r["severity"],
            "count": r[2] if not hasattr(r, "keys") else r["n"],
        }
        for r in rows
    ]
