"""Laporan kehilangan. Status: open (belum ditemukan) | resolved (selesai).
Status TIDAK berubah otomatis walau ada barang temuan yang mirip."""
from database.db import execute, query

PUBLIC = "l.id,l.item_name,l.category,l.description,l.location,l.date_lost,l.time_lost,l.photo,l.status,l.created_at"
PUBLIC_VIEW = f"SELECT {PUBLIC} FROM lost_items l"
STAFF_VIEW = "SELECT l.*, u.name AS reporter, u.role AS reporter_role, u.nim FROM lost_items l JOIN users u ON u.id=l.user_id"


def create(user_id, d, photo):
    return execute(
        "INSERT INTO lost_items(user_id,item_name,category,description,location,date_lost,time_lost,photo,reporter_phone)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, d["item_name"], d["category"], d["description"], d["location"], d["date"], d["time"], photo, d["phone"]))


def get(lid):
    return query("SELECT l.*, u.name AS reporter FROM lost_items l JOIN users u ON u.id=l.user_id WHERE l.id=?", (lid,), one=True)


def public_list(q="", category="", location="", date_from="", date_to="", status="", sort="newest"):
    sql = PUBLIC_VIEW + " WHERE 1=1"
    args = []
    if q:
        sql += " AND (l.item_name LIKE ? OR l.description LIKE ? OR l.location LIKE ?)"; args += [f"%{q}%"] * 3
    if category:
        sql += " AND l.category=?"; args.append(category)
    if location:
        sql += " AND l.location=?"; args.append(location)
    if date_from:
        sql += " AND l.date_lost>=?"; args.append(date_from)
    if date_to:
        sql += " AND l.date_lost<=?"; args.append(date_to)
    if status == "resolved":
        sql += " AND l.status='resolved'"
    elif status in ("open", "candidates"):
        sql += " AND l.status='open'"           # 'candidates' disaring lagi di route (butuh skor kemiripan)
    sql += " ORDER BY l.date_lost ASC, l.id ASC" if sort == "oldest" else " ORDER BY l.date_lost DESC, l.id DESC"
    return query(sql, args)


def locations():
    return [r["location"] for r in query("SELECT DISTINCT location FROM lost_items ORDER BY location")]


def by_user(uid):
    return query("SELECT * FROM lost_items WHERE user_id=? ORDER BY id DESC", (uid,))


def staff_list():
    return query(STAFF_VIEW + " ORDER BY l.id DESC")


def resolve(lid, user_id=None):
    """Tandai selesai. user_id diisi untuk pemilik laporan; None untuk Satpam."""
    if user_id is None:
        execute("UPDATE lost_items SET status='resolved' WHERE id=?", (lid,))
    else:
        execute("UPDATE lost_items SET status='resolved' WHERE id=? AND user_id=?", (lid, user_id))


def counts():
    r = query("SELECT COUNT(*) total, SUM(status='open') open FROM lost_items", one=True)
    return {k: (r[k] or 0) for k in r.keys()}
