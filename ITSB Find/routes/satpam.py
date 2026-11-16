import os
from datetime import datetime, timedelta

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template, request, send_from_directory, url_for)

from config.settings import USER_TYPES
from database.db import query
from models import feedback as F, found_item as FI, lost_item as LI, returns as R
from services.image_validation import save_valid_image
from services.matching import count_candidates
from services.security import role_required, valid_phone

bp = Blueprint("satpam", __name__, url_prefix="/satpam")
OWNER_TYPES = dict(USER_TYPES)


@bp.route("/")
@role_required("security")
def dashboard():
    found, lost = FI.counts(), LI.counts()
    week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent = query("SELECT (SELECT COUNT(*) FROM found_items WHERE created_at>=?) + (SELECT COUNT(*) FROM lost_items WHERE created_at>=?) n",
                   (week, week), one=True)["n"]
    activity = query("""SELECT 'Laporan temuan' kind, f.item_name, u.name actor, f.status, f.created_at ts FROM found_items f JOIN users u ON u.id=f.user_id
        UNION ALL SELECT 'Laporan hilang', l.item_name, u.name, l.status, l.created_at FROM lost_items l JOIN users u ON u.id=l.user_id
        UNION ALL SELECT 'Pengembalian', f.item_name, r.owner_name, 'returned', r.return_date FROM item_returns r JOIN found_items f ON f.id=r.found_item_id
        ORDER BY ts DESC LIMIT 10""")
    return render_template("satpam/dashboard.html", found=found, lost=lost, recent=recent, activity=activity,
                           pending=FI.staff_list("pending"))


@bp.route("/found")
@role_required("security")
def found():
    status = request.args.get("status", "")
    return render_template("satpam/found.html", items=FI.staff_list(status), status=status)


@bp.route("/found/<int:fid>/confirm", methods=["POST"])
@role_required("security")
def confirm(fid):
    if not FI.get_staff(fid):
        abort(404)
    if FI.confirm_receipt(fid, g.user["id"]):
        flash("Penerimaan barang dikonfirmasi. Barang kini tampil di Daftar Barang Temuan.", "success")
    else:
        flash("Barang ini sudah dikonfirmasi sebelumnya.", "info")
    return redirect(request.referrer or url_for("satpam.found"))


@bp.route("/lost")
@role_required("security")
def lost():
    stored = FI.stored_for_matching()
    rows = [dict(r) for r in LI.staff_list()]
    for r in rows:
        r["candidates"] = count_candidates(r, stored) if r["status"] == "open" else 0
    return render_template("satpam/lost.html", items=rows)


@bp.route("/lost/<int:lid>/resolve", methods=["POST"])
@role_required("security")
def lost_resolve(lid):
    if not LI.get(lid):
        abort(404)
    LI.resolve(lid)
    flash("Laporan kehilangan ditandai selesai.", "success")
    return redirect(url_for("satpam.lost"))


# ---------- Pengembalian barang (dilakukan langsung di pos Satpam) ----------
@bp.route("/returns")
@role_required("security")
def returns():
    q = request.args.get("q", "").strip()
    return render_template("satpam/returns.html", items=FI.search_stored(q), q=q)


@bp.route("/returns/<int:fid>", methods=["GET", "POST"])
@role_required("security")
def return_item(fid):
    item = FI.get_staff(fid)
    if not item:
        abort(404)
    if item["status"] != "stored":
        flash("Barang ini tidak dalam status disimpan, jadi tidak dapat dikembalikan.", "error")
        return redirect(url_for("satpam.returns"))
    d = {"owner_type": "student"}
    if request.method == "POST":
        d = {k: request.form.get(k, "").strip() for k in ("owner_name", "owner_type", "owner_phone", "notes")}
        phone, err = valid_phone(d["owner_phone"])
        if not (d["owner_name"] and d["notes"]):
            err = "Nama pemilik dan catatan verifikasi kepemilikan wajib diisi."
        elif d["owner_type"] not in OWNER_TYPES:
            err = "Pilih jenis pengguna pemilik."
        elif len(d["owner_name"]) > 100 or len(d["notes"]) > 500:
            err = "Isian terlalu panjang."
        photo = None
        if not err:
            photo, err = save_valid_image(request.files.get("photo"), current_app.config["PRIVATE_UPLOAD_FOLDER"],
                                          current_app.config["MAX_IMAGE_BYTES"], current_app.config["ALLOWED_IMAGE_EXT"], True)
        if err:
            flash(err, "error")
        else:
            try:
                ok = R.create(fid, d["owner_name"], d["owner_type"], phone, g.user["id"], photo, d["notes"])
            except Exception:
                ok = False
            if ok:
                flash("Pengembalian dikonfirmasi. Status barang: Sudah Dikembalikan.", "success")
                return redirect(url_for("satpam.history"))
            try:
                os.remove(os.path.join(current_app.config["PRIVATE_UPLOAD_FOLDER"], photo))
            except OSError:
                pass
            flash("Pengembalian gagal diproses. Barang mungkin sudah dikembalikan.", "error")
            return redirect(url_for("satpam.returns"))
    return render_template("satpam/return_form.html", item=item, d=d, owner_types=USER_TYPES)


@bp.route("/history")
@role_required("security")
def history():
    return render_template("satpam/history.html", rows=R.all_rows())


@bp.route("/return-photo/<int:rid>")
@role_required("security")
def return_photo(rid):
    """Foto dokumentasi hanya bisa diambil lewat route ini (dicek role di backend). Foto tidak berada di folder static."""
    row = R.get(rid)
    if not row or not row["documentation_photo"]:
        abort(404)
    resp = send_from_directory(current_app.config["PRIVATE_UPLOAD_FOLDER"], row["documentation_photo"])
    resp.headers["Cache-Control"] = "private, no-store"
    return resp


@bp.route("/feedback")
@role_required("security")
def feedback():
    return render_template("satpam/feedback.html", rows=F.all_rows())
