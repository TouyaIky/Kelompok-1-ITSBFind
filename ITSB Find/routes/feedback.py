from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, render_template, request

from config.settings import FEEDBACK_CATEGORIES
from models import feedback as F
from services.email_service import send_email
from services.security import EMAIL_RE, client_ip, rate_limited

bp = Blueprint("feedback", __name__)


@bp.route("/feedback")
def page():
    return render_template("feedback.html", feedback_categories=FEEDBACK_CATEGORIES)


@bp.route("/feedback/send", methods=["POST"])
def send():
    d = request.get_json(silent=True) or request.form
    name = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip()
    category = (d.get("category") or "").strip()
    subject = (d.get("subject") or "").strip()
    message = (d.get("message") or "").strip()
    if g.user:   # data akun dipakai untuk pengguna yang login
        name, email = g.user["name"], g.user["email"]

    def fail(msg, code=400):
        return jsonify(ok=False, message=msg), code

    if rate_limited(f"fb:{client_ip()}", 3, 600):
        return fail("Terlalu banyak pengiriman. Coba lagi beberapa menit lagi.", 429)
    if not all([name, email, category, subject, message]):
        return fail("Semua kolom wajib diisi.")
    if not 2 <= len(name) <= 80:
        return fail("Nama harus 2–80 karakter.")
    if not EMAIL_RE.match(email):
        return fail("Format email tidak valid.")
    if category not in FEEDBACK_CATEGORIES:
        return fail("Kategori tidak valid.")
    if not 3 <= len(subject) <= 120:
        return fail("Subjek harus 3–120 karakter.")
    if not 10 <= len(message) <= 1500:
        return fail("Pesan harus 10–1500 karakter.")
    if F.recent_duplicate(email, message):
        return fail("Pesan yang sama baru saja dikirim.", 429)

    fid = F.create(g.user["id"] if g.user else None, name, email, category, subject, message)
    status, detail = send_email("feedback", {
        "sender_name": name, "sender_email": email, "reply_to": email, "category": category,
        "subject": subject, "message": message, "sent_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        "app_name": "ITSB FIND"})
    F.set_status(fid, status)
    if status == "sent":
        return jsonify(ok=True, status=status, message="Terima kasih! Masukan Anda berhasil dikirim.")
    current_app.logger.warning("Feedback %s: email %s (%s)", fid, status, detail)
    note = ("Pesan Anda sudah kami terima dan tersimpan. Terima kasih!"
            if status == "not_configured" else "Pesan tersimpan, tetapi email belum berhasil dikirim.")
    return jsonify(ok=True, status=status, message=note), 202
