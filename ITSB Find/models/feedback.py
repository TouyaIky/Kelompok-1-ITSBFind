from database.db import execute, query


def create(user_id, name, email, category, subject, message):
    return execute("INSERT INTO feedback(user_id,sender_name,sender_email,category,subject,message) VALUES (?,?,?,?,?,?)",
                   (user_id, name, email, category, subject, message))


def set_status(fid, status):
    execute("UPDATE feedback SET email_status=? WHERE id=?", (status, fid))


def recent_duplicate(email, message):
    return query("SELECT 1 FROM feedback WHERE sender_email=? AND message=? AND created_at >= datetime('now','-2 minutes')",
                 (email, message), one=True) is not None


def all_rows():
    return query("SELECT * FROM feedback ORDER BY id DESC")
