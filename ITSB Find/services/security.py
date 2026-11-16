import re
import secrets
import time
from collections import defaultdict, deque
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

_hits = defaultdict(deque)


def rate_limited(key, limit, window_seconds):
    """True jika `key` sudah melewati batas. Mencatat setiap pemanggilan. (In-memory, per proses.)"""
    now = time.time()
    q = _hits[key]
    while q and now - q[0] > window_seconds:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def peek_count(key, window_seconds):
    now = time.time()
    return sum(1 for t in _hits[key] if now - t <= window_seconds)


def reset_rate_limits():
    _hits.clear()


def client_ip():
    return request.remote_addr or "unknown"


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def check_csrf():
    sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("_csrf", "")
    if not expected or not secrets.compare_digest(sent, expected):
        abort(400, "Sesi formulir tidak valid. Muat ulang halaman lalu coba lagi.")


def valid_password(pw):
    if len(pw) < 8:
        return "Password minimal 8 karakter."
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        return "Password harus mengandung huruf dan angka."
    if len(pw) > 128:
        return "Password terlalu panjang."
    return None


def valid_phone(raw):
    """Normalisasi nomor telepon. Return (nomor | None, pesan error | None)."""
    p = re.sub(r"[\s\-().]", "", raw or "")
    if not re.fullmatch(r"\+?\d{9,15}", p):
        return None, "Nomor telepon tidak valid (9–15 digit, boleh diawali +)."
    return p, None


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if g.user is None:
            flash("Silakan login terlebih dahulu untuk mengakses fitur ini.", "info")
            return redirect(url_for("auth.login"))
        return view(*a, **kw)
    return wrapped


def role_required(role):
    def deco(view):
        @wraps(view)
        def wrapped(*a, **kw):
            if g.user is None:
                flash("Silakan login terlebih dahulu.", "info")
                return redirect(url_for("auth.login"))
            if g.user["role"] != role:   # validasi role di backend, bukan hanya menyembunyikan menu
                abort(403)
            return view(*a, **kw)
        return wrapped
    return deco
