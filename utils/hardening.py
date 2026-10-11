"""Configuration de durcissement Flask (sessions + en-têtes HTTP)."""
from __future__ import annotations

import os
from datetime import timedelta


def configure_session_security(app):
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        hours=int(os.getenv("SESSION_HOURS", "8"))
    )
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 Mo


def register_security_headers(app):
    from flask import request

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        # CSP pragmatique (fonts Google + miniatures Coursera / Unsplash)
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: https://s3.amazonaws.com https://*.coursera.org "
            "https://images.unsplash.com https://*.unsplash.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        if os.getenv("ENABLE_HSTS", "False").lower() == "true":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        if (request.path or "").startswith("/admin"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response
