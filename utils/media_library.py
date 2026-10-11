"""Médiathèque : uploads validés (type + taille), hors exécutable."""
from __future__ import annotations

import io
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
MAX_BYTES = 8 * 1024 * 1024
MAX_IMAGE_WIDTH = 1600
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def uploads_dir(base_dir: str | Path) -> Path:
    path = Path(base_dir) / "static" / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _optimize_image(data: bytes, ext: str) -> tuple[bytes, str]:
    """Redimensionne / compresse les images pour un stockage raisonnable."""
    try:
        from PIL import Image
    except ImportError:
        return data, ext

    if ext == ".gif":
        return data, ext

    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB") if img.mode in ("RGBA", "P", "LA") else img
        if img.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / float(img.width)
            img = img.resize(
                (MAX_IMAGE_WIDTH, max(1, round(img.height * ratio))),
                Image.Resampling.LANCZOS,
            )
        buf = io.BytesIO()
        # JPEG pour un bon rapport poids/qualité (aperçus admin & couvertures)
        img.save(buf, format="JPEG", quality=85, optimize=True)
        out = buf.getvalue()
        if len(out) < len(data) or ext in (".png", ".webp"):
            return out, ".jpg"
        return data, ext
    except Exception:
        return data, ext


def validate_and_save(file_storage, base_dir: str | Path) -> dict:
    filename = (file_storage.filename or "").strip()
    if not filename or "." not in filename:
        raise ValueError("Nom de fichier invalide")
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED:
        raise ValueError("Type de fichier non autorisé")
    data = file_storage.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Fichier trop volumineux (max 8 Mo)")
    if len(data) < 4:
        raise ValueError("Fichier vide ou invalide")
    magic = ALLOWED[ext]
    if ext == ".webp":
        if not (data.startswith(b"RIFF") and b"WEBP" in data[:16]):
            raise ValueError("Contenu WebP invalide")
    elif not data.startswith(magic):
        raise ValueError("Contenu fichier invalide")

    if ext in IMAGE_EXTS:
        data, ext = _optimize_image(data, ext)

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
