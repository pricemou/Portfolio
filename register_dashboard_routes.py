"""
Routes Flask pour le tableau de bord cybersécurité (intégré au portfolio).
Les agrégats viennent de dashboard/engine.py — mêmes données que Streamlit.
"""

from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

from flask import jsonify, render_template, request, session

# Import du moteur (dossier dashboard/)
import sys

ROOT = Path(__file__).resolve().parent
DASH_DIR = ROOT / "dashboard"
UPLOAD_DIR = DASH_DIR / "_uploads"
if str(DASH_DIR) not in sys.path:
    sys.path.insert(0, str(DASH_DIR))

from engine import (  # noqa: E402
    charger_csv,
    charger_depuis_bytes,
    construire_payload,
    filtrer,
    options_filtres,
)


@lru_cache(maxsize=1)
def _df_base_cached(mtime_ns: int):
    """Cache mémoire invalidé quand events.csv change."""
    return charger_csv()


def _df_base():
    from engine import chemin_csv_defaut

    path = chemin_csv_defaut()
    if not path.is_file():
        return None
    return _df_base_cached(path.stat().st_mtime_ns)


def _parse_list(name: str) -> list[str] | None:
    raw = request.args.getlist(name) or request.args.getlist(f"{name}[]")
    if not raw and request.args.get(name):
        raw = [x.strip() for x in request.args.get(name).split(",") if x.strip()]
    return raw or None


def _session_upload_df():
    """DataFrame téléversé (fichier temporaire référencé en session)."""
    path_str = session.get("cyber_csv_path")
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_file():
        session.pop("cyber_csv_path", None)
        return None
    try:
        return charger_csv(path)
    except Exception:
        session.pop("cyber_csv_path", None)
        return None


def register_dashboard_routes(app):
    @app.route("/dashboard")
    def cyber_dashboard_page():
        """Page publique du monitoring cybersécurité (dans le site)."""
        from datetime import datetime

        return render_template(
            "dashboard.html",
            page_title="Monitoring cybersécurité",
            current_year=datetime.now().year,
        )

    @app.route("/api/dashboard/meta", methods=["GET"])
    def api_dashboard_meta():
        df = _session_upload_df() or _df_base()
        if df is None:
            return jsonify(
                {
                    "error": "events.csv introuvable",
                    "hint": "python dashboard/generate_events.py",
                }
            ), 503
        return jsonify(options_filtres(df))

    @app.route("/api/dashboard/data", methods=["GET"])
    def api_dashboard_data():
        df = _session_upload_df() or _df_base()
        if df is None:
            return jsonify({"error": "events.csv introuvable"}), 503

        filtered = filtrer(
            df,
            debut=request.args.get("debut") or None,
            fin=request.args.get("fin") or None,
            pays=_parse_list("pays"),
            activites=_parse_list("activite"),
            gravites=_parse_list("gravite"),
            utilisateurs=_parse_list("utilisateur"),
            services=_parse_list("service"),
        )
        payload = construire_payload(
            filtered,
            granularite=request.args.get("granularite", "heure"),
            top_dimension=request.args.get("top", "ip"),
            donut_mode=request.args.get("donut", "utilisateur"),
        )
        return jsonify(payload)

    @app.route("/api/dashboard/upload", methods=["POST"])
    def api_dashboard_upload():
        """Téléversement CSV (mêmes colonnes) pour la session courante."""
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"error": "fichier requis"}), 400
        try:
            contenu = f.read()
            if len(contenu) > 8 * 1024 * 1024:
                return jsonify({"error": "fichier trop volumineux (max 8 Mo)"}), 400
            df = charger_depuis_bytes(contenu)
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".csv", dir=str(UPLOAD_DIR), prefix="cyber_"
            )
            tmp.write(contenu)
            tmp.close()
            # Supprimer l'ancien upload de session s'il existe
            old = session.get("cyber_csv_path")
            if old and Path(old).is_file() and str(UPLOAD_DIR) in old:
                try:
                    Path(old).unlink()
                except OSError:
                    pass
            session["cyber_csv_path"] = tmp.name
            session.modified = True
            return jsonify({"success": True, "lignes": len(df), "nom": f.filename})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/dashboard/reset", methods=["POST"])
    def api_dashboard_reset():
        old = session.pop("cyber_csv_path", None)
        if old and Path(old).is_file() and str(UPLOAD_DIR) in str(old):
            try:
                Path(old).unlink()
            except OSError:
                pass
        _df_base_cached.cache_clear()
        return jsonify({"success": True})
