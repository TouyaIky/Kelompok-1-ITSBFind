from database.db import get_db, query

BASE = ("SELECT r.*, f.item_name, f.category, f.photo, o.name AS officer FROM item_returns r "
        "JOIN found_items f ON f.id=r.found_item_id JOIN users o ON o.id=r.officer_id")


def all_rows():
    return query(BASE + " ORDER BY r.id DESC")


def get(rid):
    return query(BASE + " WHERE r.id=?", (rid,), one=True)


def create(found_id, owner_name, owner_type, owner_phone, officer_id, doc_photo, notes):
    """Atomik: status hanya berubah dari 'stored' ke 'returned' satu kali, sehingga tidak bisa dikembalikan dua kali."""
    db = get_db()
    try:
        cur = db.execute("UPDATE found_items SET status='returned' WHERE id=? AND status='stored'", (found_id,))
        if cur.rowcount != 1:
            db.rollback()
            return False
        db.execute("INSERT INTO item_returns(found_item_id,owner_name,owner_type,owner_phone,officer_id,return_date,documentation_photo,verification_notes)"
                   " VALUES (?,?,?,?,?,datetime('now','localtime'),?,?)",
                   (found_id, owner_name, owner_type, owner_phone, officer_id, doc_photo, notes))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
