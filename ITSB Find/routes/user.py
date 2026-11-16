from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import settings as S
from database.db import query
from models import found_item as FI, lost_item as LI, user as U
from services.image_validation import save_valid_image
from services.matching import count_candidates, find_matches
from services.security import login_required, valid_password, valid_phone

bp = Blueprint("user", __name__)


def _security_home():
    return redirect(url_for("satpam.dashboard")) if g.user["role"] == "security" else None


@bp.route("/dashboard")
@login_required
def dashboard():
    if (r := _security_home()):
        return r
    uid = g.user["id"]
    found, lost = FI.counts(), LI.counts()
    mine = query("""SELECT 'found' kind, id, item_name, status, created_at FROM found_items WHERE user_id=?
                    UNION ALL SELECT 'lost', id, item_name, status, created_at FROM lost_items WHERE user_id=?
                    ORDER BY created_at DESC, id DESC LIMIT 5""", (uid, uid))
    activity = query("""SELECT 'found' kind, item_name, status, created_at FROM found_items WHERE status!='pending'
                        UNION ALL SELECT 'lost', item_name, status, created_at FROM lost_items
                        ORDER BY created_at DESC LIMIT 6""")
    latest = query("SELECT id,item_name,location,date_found,photo FROM found_items WHERE status='stored' ORDER BY id DESC LIMIT 4")
    cats = query("SELECT category, COUNT(*) n FROM found_items WHERE status!='pending' GROUP BY category ORDER BY n DESC")
    return render_template("dashboard.html", found=found, lost=lost, mine=mine, activity=activity, latest=latest,
                           chart={"labels": [c["category"] for c in cats], "values": [c["n"] for c in cats]})


# ---------- Daftar publik (boleh dibuka tanpa login / Mode Tamu) ----------
def _filters():
    f = {k: request.args.get(k, "").strip() for k in ("q", "category", "location", "date_from", "date_to", "status")}
    for k in ("date_from", "date_to"):
        try:
            date.fromisoformat(f[k]) if f[k] else None
        except ValueError:
            f[k] = ""
    return f, ("oldest" if request.args.get("sort") == "oldest" else "newest")


@bp.route("/found-items")
def found_items():
    f, sort = _filters()
    items = FI.public_list(f["q"], f["category"], f["location"], f["date_from"], f["date_to"], f["status"], sort)
    return render_template("found_items.html", items=items, f=f, sort=sort, categories=S.CATEGORIES, locations=FI.locations())


@bp.route("/lost-items")
def lost_items():
    f, sort = _filters()
    rows = [dict(r) for r in LI.public_list(f["q"], f["category"], f["location"], f["date_from"], f["date_to"], f["status"], sort)]
    stored = FI.stored_for_matching()
    for r in rows:      # petunjuk saja; status laporan tidak berubah
        r["candidates"] = count_candidates(r, stored) if r["status"] == "open" else 0
    if f["status"] == "candidates":
        rows = [r for r in rows if r["candidates"] > 0]
    return render_template("lost_items.html", items=rows, f=f, sort=sort, categories=S.CATEGORIES, locations=LI.locations())


# ---------- Pelaporan ----------
def _read_report_form():
    d = {k: request.form.get(k, "").strip() for k in ("item_name", "category", "description", "location", "date", "time", "phone")}
    err = None
    phone, phone_err = valid_phone(d["phone"])
    if not all(d.values()):
        err = "Seluruh kolom wajib diisi, termasuk nomor telepon."
    elif d["category"] not in S.CATEGORIES:
        err = "Kategori tidak valid."
    elif len(d["item_name"]) > 100 or len(d["location"]) > 100 or not 10 <= len(d["description"]) <= 1000:
        err = "Nama/lokasi maksimal 100 karakter dan deskripsi 10–1000 karakter."
    elif phone_err:
        err = phone_err
    else:
        d["phone"] = phone
        try:
            dt = date.fromisoformat(d["date"])
            datetime.strptime(d["time"], "%H:%M")
            if dt > date.today():
                err = "Tanggal tidak boleh di masa depan."
        except ValueError:
            err = "Format tanggal atau waktu tidak valid."
    return d, err


def _save_photo(required):
    return save_valid_image(request.files.get("photo"), current_app.config["UPLOAD_FOLDER"],
                            current_app.config["MAX_IMAGE_BYTES"], current_app.config["ALLOWED_IMAGE_EXT"], required)


def _report_page(template, **extra):
    return render_template(template, categories=S.CATEGORIES, suggestions=S.LOCATION_SUGGESTIONS,
                           today=date.today().isoformat(), **extra)


@bp.route("/report-found", methods=["GET", "POST"])
@login_required
def report_found():
    d = {"phone": g.user["phone"]}
    if request.method == "POST":
        d, err = _read_report_form()
        photo = None
        if not err:
            photo, err = _save_photo(True)
        if err:
            flash(err, "error")
        else:
            FI.create(g.user["id"], d, photo)
            flash("Laporan tersimpan. Serahkan barang ke Satpam agar tampil di daftar barang temuan.", "success")
            return redirect(url_for("user.my_reports"))
    return _report_page("report_found.html", d=d)


@bp.route("/report-lost", methods=["GET", "POST"])
@login_required
def report_lost():
    d = {"phone": g.user["phone"]}
    if request.method == "POST":
        d, err = _read_report_form()
        photo = None
        if not err:
            photo, err = _save_photo(False)
        if err:
            flash(err, "error")
        else:
            lid = LI.create(g.user["id"], d, photo)       # langsung tersimpan & tampil, tanpa persetujuan petugas
            flash("Laporan barang hilang tersimpan. Berikut rekomendasi barang temuan yang mungkin cocok.", "success")
            return redirect(url_for("user.lost_detail", lid=lid))
    return _report_page("report_lost.html", d=d)


@bp.route("/my-reports")
@login_required
def my_reports():
    return render_template("my_reports.html", found=FI.by_user(g.user["id"]), lost=LI.by_user(g.user["id"]))


@bp.route("/lost/<int:lid>")
@login_required
def lost_detail(lid):
    lost = LI.get(lid)
    if not lost or (lost["user_id"] != g.user["id"] and g.user["role"] != "security"):
        abort(404)
    matches = find_matches(lost, FI.stored_for_matching()) if lost["status"] == "open" else []
    return render_template("lost_detail.html", lost=lost, matches=matches)


@bp.route("/lost/<int:lid>/resolve", methods=["POST"])
@login_required
def lost_resolve(lid):
    LI.resolve(lid, g.user["id"])
    flash("Laporan ditandai selesai. Semoga barangmu kembali dengan aman!", "success")
    return redirect(url_for("user.my_reports"))


# ---------- Profil (semua peran) ----------
@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "profile":
            name, (phone, err) = request.form.get("name", "").strip(), valid_phone(request.form.get("phone", ""))
            if not 3 <= len(name) <= 80:
                err = "Nama lengkap harus 3–80 karakter."
            if err:
                flash(err, "error")
            else:
                U.update_profile(g.user["id"], name, phone)
                flash("Profil berhasil diperbarui.", "success")
                return redirect(url_for("user.profile"))
        elif action == "password":
            cur, new, conf = (request.form.get(k, "") for k in ("current", "password", "confirm"))
            err = None
            if not check_password_hash(U.password_hash(g.user["id"]), cur):
                err = "Password saat ini salah."
            elif new != conf:
                err = "Password baru dan konfirmasinya tidak sama."
            else:
                err = valid_password(new)
            if err:
                flash(err, "error")
            else:
                U.set_password(g.user["id"], generate_password_hash(new))
                flash("Password berhasil diganti.", "success")
                return redirect(url_for("user.profile"))
    return render_template("profile.html")
