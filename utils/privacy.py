"""Minimisation des données personnelles (IP hachées)."""
from __future__ import annotations

import hashlib
import hmac
import os


def get_ip_salt() -> str:
    return os.getenv("IP_HASH_SALT") or os.getenv("SECRET_KEY") or "portfolio-ip-salt"


def hash_ip(ip_address: str | None) -> str:
    """Retourne un hash HMAC-SHA256 de l'IP (jamais stocker l'IP en clair)."""
    raw = (ip_address or "").strip()
    if not raw:
        return ""
    return hmac.new(
        get_ip_salt().encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def client_ip_from_request(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""
