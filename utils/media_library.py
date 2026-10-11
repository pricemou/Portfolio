"""Médiathèque : uploads validés (type + taille), hors exécutable."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

ALLOWED = {
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".png": b"\x89PNG\r\n\x1a\n",
    ".webp": b"RIFF",
    ".pdf": b"%PDF",
    ".gif": b"GIF8",
}
MAX_BYTES = 2 * 1024 * 1024


def uploads_dir(base_dir: str | Path) -> Path:
    path = Path(base_dir) / "static" / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    # Empêcher l'exécution via .htaccess n'est pas portable ; noms UUID suffisent.
    return path


def validate_and_save(file_storage, base_dir: str | Path) -> dict:
    filename = (file_storage.filename or "").strip()
    if not filename or "." not in filename:
        raise ValueError("Nom de fichier invalide")
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED:
        raise ValueError("Type de fichier non autorisé")
    data = file_storage.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Fichier trop volumineux (max 2 Mo)")
    if len(data) < 4:
        raise ValueError("Fichier vide ou invalide")
    magic = ALLOWED[ext]
    if ext == ".webp":
        if not (data.startswith(b"RIFF") and b"WEBP" in data[:16]):
            raise ValueError("Contenu WebP invalide")
    elif not data.startswith(magic):
        raise ValueError("Contenu fichier invalide")
    new_name = f"{uuid.uuid4().hex}{ext}"
    dest = uploads_dir(base_dir) / new_name
    dest.write_bytes(data)
    return {
        "filename": new_name,
        "original_name": filename[:200],
        "path": f"uploads/{new_name}",
        "mime_hint": ext.lstrip("."),
        "size": len(data),
    }
