"""Barang temuan. Status: pending (menunggu penyerahan) | stored (disimpan Satpam) | returned (sudah dikembalikan).
Kolom publik ditulis eksplisit: reporter_phone TIDAK PERNAH ikut dipilih pada query publik."""
from database.db import execute, get_db, query

PUBLIC = "f.id,f.item_name,f.category,f.description,f.location,f.date_found,f.time_found,f.photo,f.status,f.received_at,f.created_at"
PUBLIC_VIEW = f"SELECT {PUBLIC} FROM found_items f"
STAFF_VIEW = "SELECT f.*, u.name AS reporter, u.role AS reporter_role FROM found_items f JOIN users u ON u.id=f.user_id"


def create(user_id, d, photo):
    return execute(
        "INSERT INTO found_items(user_id,item_name,category,description,location,date_found,time_found,photo,reporter_phone)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, d["item_name"], d["category"], d["description"], d["location"], d["date"], d["time"], photo, d["phone"]))


def get_staff(fid):
    return query(STAFF_VIEW + " WHERE f.id=?", (fid,), one=True)


def stored_for_matching():
    return query(f"SELECT {PUBLIC} FROM found_items f WHERE f.status='stored'")


def public_list(q="", category="", location="", date_from="", date_to="", status="", sort="newest"):
    sql = PUBLIC_VIEW + " WHERE f.status IN ('stored','returned')"
    args = []
    if q:
        sql += " AND (f.item_name LIKE ? OR f.description LIKE ? OR f.location LIKE ?)"; args += [f"%{q}%"] * 3
    if category:
        sql += " AND f.category=?"; args.append(category)
    if location:
        sql += " AND f.location=?"; args.append(location)
    if date_from:
        sql += " AND f.date_found>=?"; args.append(date_from)
    if date_to:
        sql += " AND f.date_found<=?"; args.append(date_to)
    if status in ("stored", "returned"):
        sql += " AND f.status=?"; args.append(status)
    sql += " ORDER BY f.date_found ASC, f.id ASC" if sort == "oldest" else " ORDER BY f.date_found DESC, f.id DESC"
    return query(sql, args)


def locations():
    return [r["location"] for r in query(
        "SELECT DISTINCT location FROM found_items WHERE status IN ('stored','returned') ORDER BY location")]


def by_user(uid):
    return query("SELECT * FROM found_items WHERE user_id=? ORDER BY id DESC", (uid,))


def staff_list(status=""):
    if status in ("pending", "stored", "returned"):
        return query(STAFF_VIEW + " WHERE f.status=? ORDER BY f.id DESC", (status,))
    return query(STAFF_VIEW + " ORDER BY CASE f.status WHEN 'pending' THEN 0 WHEN 'stored' THEN 1 ELSE 2 END, f.id DESC")


def search_stored(q=""):
    sql = STAFF_VIEW + " WHERE f.status='stored'"
    args = []
    if q:
        sql += " AND (f.item_name LIKE ? OR f.id=?)"
        args = [f"%{q}%", int(q) if q.isdigit() else -1]
    return query(sql + " ORDER BY f.id DESC LIMIT 50", args)


def confirm_receipt(fid, officer_id):
    db = get_db()
    cur = db.execute("UPDATE found_items SET status='stored', received_by=?, received_at=datetime('now','localtime')"
                     " WHERE id=? AND status='pending'", (officer_id, fid))
    db.commit()
    return cur.rowcount == 1


def counts():
    r = query("SELECT COUNT(*) total, SUM(status='stored') stored, SUM(status='returned') returned,"
              " SUM(status='pending') pending FROM found_items", one=True)
    c = {k: (r[k] or 0) for k in r.keys()}
    c["received"] = c["stored"] + c["returned"]      # barang yang sudah diterima Satpam
    return c
