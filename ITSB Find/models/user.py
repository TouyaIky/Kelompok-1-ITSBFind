from database.db import execute, query

COLS = "id,name,email,nim,phone,role,created_at"


def by_id(uid):
    return query(f"SELECT {COLS} FROM users WHERE id=?", (uid,), one=True)


def by_email(email):
    return query("SELECT * FROM users WHERE email=?", (email.lower(),), one=True)


def create(name, email, nim, phone, role, password_hash):
    return execute("INSERT INTO users(name,email,nim,phone,role,password_hash) VALUES (?,?,?,?,?,?)",
                   (name, email.lower(), nim or None, phone, role, password_hash))


def nim_taken(nim):
    return query("SELECT 1 FROM users WHERE nim=?", (nim,), one=True) is not None


def email_taken(email, exclude_id=None):
    return query("SELECT 1 FROM users WHERE email=? AND id!=?", (email.lower(), exclude_id or 0), one=True) is not None


def set_password(uid, password_hash):
    execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, uid))


def update_profile(uid, name, phone):
    execute("UPDATE users SET name=?, phone=? WHERE id=?", (name, phone, uid))


def password_hash(uid):
    return query("SELECT password_hash FROM users WHERE id=?", (uid,), one=True)["password_hash"]
