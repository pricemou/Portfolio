"""2FA TOTP pour l'admin (pyotp) + codes de secours hachés."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets

try:
    import pyotp
except ImportError:  # pragma: no cover
    pyotp = None

from utils.security import hash_password, check_password


def totp_available() -> bool:
    return pyotp is not None


def _seal_key() -> bytes:
    secret = os.getenv("SECRET_KEY", "dev-secret")
    return hashlib.sha256(f"totp-seal::{secret}".encode("utf-8")).digest()


def seal_secret(plain: str) -> str:
    raw = plain.encode("utf-8")
    key = _seal_key()
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return base64.urlsafe_b64encode(xored).decode("ascii")


def unseal_secret(sealed: str) -> str:
    raw = base64.urlsafe_b64decode(sealed.encode("ascii"))
    key = _seal_key()
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return plain.decode("utf-8")


def generate_totp_secret() -> str:
    if not pyotp:
        raise RuntimeError("pyotp non installé")
    return pyotp.random_base32()


def provisioning_uri(secret: str, username: str, issuer: str = "Portfolio Claude") -> str:
    if not pyotp:
        raise RuntimeError("pyotp non installé")
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    if not pyotp or not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(code.strip().replace(" ", ""), valid_window=1))


def generate_backup_codes(n: int = 8) -> list[str]:
    return [secrets.token_hex(4).upper() for _ in range(n)]


def hash_backup_codes(codes: list[str]) -> str:
    return json.dumps([hash_password(c) for c in codes], ensure_ascii=False)


def consume_backup_code(hashed_json: str, code: str) -> tuple[bool, str | None]:
    """Retourne (ok, nouveau_json_ou_None)."""
    try:
        hashes = json.loads(hashed_json or "[]")
    except json.JSONDecodeError:
        return False, None
    remaining = []
    matched = False
    for h in hashes:
        if not matched and check_password(code.strip().upper(), h):
            matched = True
            continue
        remaining.append(h)
    if not matched:
        return False, None
    return True, json.dumps(remaining, ensure_ascii=False)
