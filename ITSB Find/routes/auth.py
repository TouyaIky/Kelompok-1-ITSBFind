from flask import (Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from models import user as U
from services import password_reset as PR
from services.email_service import send_email, is_configured
from config.settings import USER_TYPES
from services.security import EMAIL_RE, client_ip, rate_limited, valid_password, valid_phone

bp = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("dummy-password-for-timing")


def _home():
    return redirect(url_for("satpam.dashboard" if g.user and g.user["role"] == "security" else "user.dashboard"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return _home()
    form = {"user_type": "student"}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in ("user_type", "name", "email", "nim", "phone")}
        pw, pw2 = request.form.get("password", ""), request.form.get("confirm", "")
        allowed = {k for k, _ in USER_TYPES}          # 'security' sengaja tidak ada: Satpam tidak bisa mendaftar sendiri
        err = None
        phone, phone_err = valid_phone(form["phone"])
        is_student = form["user_type"] == "student"
        if rate_limited(f"reg:{client_ip()}", 10, 3600):
            err = "Terlalu banyak percobaan pendaftaran. Coba lagi nanti."
        elif form["user_type"] not in allowed:
            err = "Pilih jenis pengguna yang valid."
        elif not all([form["name"], form["email"], form["phone"], pw, pw2]) or (is_student and not form["nim"]):
            err = "Seluruh data wajib diisi." if not is_student else "Seluruh data wajib diisi, termasuk NIM."
        elif len(form["name"]) < 3 or len(form["name"]) > 80:
            err = "Nama lengkap harus 3–80 karakter."
        elif not EMAIL_RE.match(form["email"]):
            err = "Format email tidak valid."
        elif phone_err:
            err = phone_err
        elif is_student and (not form["nim"].isalnum() or not 5 <= len(form["nim"]) <= 20):
            err = "NIM harus 5–20 karakter huruf/angka."
        elif pw != pw2:
            err = "Password dan konfirmasi password tidak sama."
        elif valid_password(pw):
            err = valid_password(pw)
        elif U.email_taken(form["email"]):
            err = "Email sudah digunakan akun lain."
        elif is_student and U.nim_taken(form["nim"]):
            err = "NIM sudah digunakan akun lain."
        if err:
            flash(err, "error")
        else:
            U.create(form["name"], form["email"], form["nim"] if is_student else None, phone, form["user_type"],
                     generate_password_hash(pw))
            flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", form=form, user_types=USER_TYPES)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return _home()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        key = f"login:{client_ip()}:{email}"
        from services.security import peek_count
        if peek_count(key, 300) >= 5:
            flash("Terlalu banyak percobaan login. Coba lagi dalam beberapa menit.", "error")
            return render_template("login.html", email=email), 429
        user = U.by_email(email) if email else None
        ok = check_password_hash(user["password_hash"] if user else DUMMY_HASH, pw) and user is not None
        if not ok:
            rate_limited(key, 5, 300)   # hanya kegagalan yang dihitung
            flash("Email atau password salah.", "error")
            return render_template("login.html", email=email), 401
        session.clear()                 # cegah session fixation
        session["uid"] = user["id"]
        session.permanent = True
        flash(f"Selamat datang, {user['name'].split()[0]}!", "success")
        return redirect(url_for("satpam.dashboard" if user["role"] == "security" else "user.dashboard"))
    return render_template("login.html", email="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("main.landing"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        generic = "Jika email terdaftar, instruksi reset password akan dikirim."
        if rate_limited(f"reset-ip:{client_ip()}", 5, 3600):
            flash("Terlalu banyak permintaan reset. Coba lagi dalam satu jam.", "error")
            return render_template("forgot_password.html"), 429
        if not EMAIL_RE.match(email):
            flash("Masukkan alamat email yang valid.", "error")
            return render_template("forgot_password.html"), 400
        user = U.by_email(email)
        if user and PR.recent_count(user["id"]) < 3:
            token = PR.create_token(user["id"], current_app.config["RESET_TOKEN_MINUTES"])
            base = current_app.config["APP_BASE_URL"] or request.url_root.rstrip("/")
            link = f"{base}{url_for('auth.reset_password', token=token)}"
            status, detail = send_email("reset", {
                "to_email": user["email"], "to_name": user["name"], "reset_link": link,
                "expires_minutes": current_app.config["RESET_TOKEN_MINUTES"], "app_name": "ITSB FIND"})
            if status != "sent":
                current_app.logger.warning("Reset email tidak terkirim (%s): %s", status, detail)
                if current_app.debug and not is_configured("reset"):
                    # HANYA mode pengembangan: tampilkan link di terminal agar bisa diuji tanpa EmailJS.
                    print(f"\n[DEV] Link reset untuk {user['email']}: {link}\n")
        flash(generic, "info")            # pesan sama untuk email terdaftar maupun tidak
        return redirect(url_for("auth.forgot_password"))
    return render_template("forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    row = PR.find_valid(token)
    if not row:
        flash("Tautan reset tidak valid atau sudah kedaluwarsa. Silakan minta tautan baru.", "error")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        pw, pw2 = request.form.get("password", ""), request.form.get("confirm", "")
        err = ("Password dan konfirmasi password tidak sama." if pw != pw2 else valid_password(pw))
        if err:
            flash(err, "error")
            return render_template("reset_password.html", token=token), 400
        U.set_password(row["user_id"], generate_password_hash(pw))
        PR.consume(row["id"])
        flash("Password berhasil diperbarui. Silakan login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", token=token)
