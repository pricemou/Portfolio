"""Chargement des certifications Coursera pour le portfolio Flask."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CERTS_PATH = BASE_DIR / "data" / "certifications.json"
EXPECTED_CERT_COUNT = 45

DOMAIN_LABELS = {
    "python": {"fr": "Python et programmation scientifique", "en": "Python and scientific programming"},
    "data-ai": {"fr": "Data Science, IA et Deep Learning", "en": "Data Science, AI and Deep Learning"},
    "big-data": {"fr": "Big Data", "en": "Big Data"},
    "fullstack": {"fr": "Développement Full Stack et Web", "en": "Full Stack and Web development"},
    "uiux": {"fr": "UI/UX et Design", "en": "UI/UX and Design"},
    "security": {"fr": "Cybersécurité et scripting", "en": "Cybersecurity and scripting"},
}

# Libellés courts pour les puces de filtre (évite les pastilles trop longues)
DOMAIN_FILTER_LABELS = {
    "python": {"fr": "Python", "en": "Python"},
    "data-ai": {"fr": "Data & IA", "en": "Data & AI"},
    "big-data": {"fr": "Big Data", "en": "Big Data"},
    "fullstack": {"fr": "Full Stack", "en": "Full Stack"},
    "uiux": {"fr": "UI/UX", "en": "UI/UX"},
    "security": {"fr": "Sécurité", "en": "Security"},
}


def certificate_image_url(code: str) -> str | None:
    if not code:
        return None
    return (
        "https://s3.amazonaws.com/coursera_assets/meta_images/generated/"
        f"CERTIFICATE_LANDING_PAGE/CERTIFICATE_LANDING_PAGE~{code}/"
        f"CERTIFICATE_LANDING_PAGE~{code}.jpeg"
    )


@lru_cache(maxsize=1)
def load_certifications_json():
    with open(CERTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items") or []
    if len(items) != EXPECTED_CERT_COUNT:
        raise ValueError(f"Expected {EXPECTED_CERT_COUNT} certifications, found {len(items)}")
    codes = [c.get("code") for c in items]
    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate certification codes detected")
    return data


def _format_cert_item(item: dict, lang: str, domains: dict) -> dict:
    code = item.get("code") or ""
    url = item.get("url") or (
        f"https://www.coursera.org/account/accomplishments/certificate/{code}"
    )
    return {
        "id": item.get("id"),
        "domain": item.get("domain"),
        "domain_label": domains.get(item.get("domain"), item.get("domain")),
        "title": item.get("title"),
        "code": code,
        "url": url,
        "verify_url": f"https://www.coursera.org/account/accomplishments/verify/{code}",
        "image": certificate_image_url(code),
        "skill": item.get("skill") or "",
        "featured": bool(item.get("featured")),
    }


def _from_database(lang: str = "fr"):
    from database import get_db_connection

    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, domain, title, code, url, skill_fr, skill_en, featured, order_index
            FROM certifications
            WHERE status = 'published'
              AND (deleted_at IS NULL OR deleted_at = '')
            ORDER BY featured DESC, order_index ASC, id ASC
            """
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        lang = "en" if lang == "en" else "fr"
        domains = {
            key: labels.get(lang) or labels.get("fr") or key
            for key, labels in DOMAIN_LABELS.items()
        }
        filter_domains = {
            key: labels.get(lang) or labels.get("fr") or key
            for key, labels in DOMAIN_FILTER_LABELS.items()
        }
        items = []
        for row in rows:
            d = dict(row)
            skill = d.get("skill_en") if lang == "en" else d.get("skill_fr")
            items.append(_format_cert_item({
                "id": d.get("id"),
                "domain": d.get("domain"),
                "title": d.get("title"),
                "code": d.get("code"),
                "url": d.get("url"),
                "skill": skill or "",
                "featured": d.get("featured"),
            }, lang, domains))
        featured = [c for c in items if c["featured"]]
        return {
            "domains": domains,
            "filter_domains": filter_domains,
            "items": items,
            "featured": featured,
            "total": len(items),
            "source": "database",
        }
    finally:
        conn.close()


def get_certifications_for_lang(lang: str = "fr"):
    db_data = _from_database(lang)
    if db_data:
        return db_data

    data = load_certifications_json()
    lang = "en" if lang == "en" else "fr"
    domains = {
        key: labels.get(lang) or labels.get("fr") or key
        for key, labels in (data.get("domains") or DOMAIN_LABELS).items()
    }
    filter_domains = {
        key: labels.get(lang) or labels.get("fr") or key
        for key, labels in DOMAIN_FILTER_LABELS.items()
        if key in domains
    }
    items = []
    for item in data.get("items") or []:
        skill = item.get("skill") or {}
        items.append(_format_cert_item({
            "domain": item.get("domain"),
            "title": item.get("title"),
            "code": item.get("code"),
            "url": item.get("url"),
            "skill": skill.get(lang) or skill.get("fr") or "",
            "featured": item.get("featured"),
        }, lang, domains))
    featured = [c for c in items if c["featured"]]
    return {
        "domains": domains,
        "filter_domains": filter_domains,
        "items": items,
        "featured": featured,
        "total": len(items),
        "source": "json",
    }
