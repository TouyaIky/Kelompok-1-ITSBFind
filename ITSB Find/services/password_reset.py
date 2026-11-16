import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from database.db import execute, query

FMT = "%Y-%m-%d %H:%M:%S"


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(user_id, minutes):
    """Buat token acak aman; hanya HASH-nya disimpan. Token lama yang belum dipakai dinonaktifkan."""
    execute("UPDATE password_reset_tokens SET used=1 WHERE user_id=? AND used=0", (user_id,))
    token = secrets.token_urlsafe(32)
    expires = (_now() + timedelta(minutes=minutes)).strftime(FMT)
    execute("INSERT INTO password_reset_tokens(user_id,token_hash,expires_at,created_at) VALUES (?,?,?,?)",
            (user_id, _hash(token), expires, _now().strftime(FMT)))
    return token


def recent_count(user_id, minutes=60):
    since = (_now() - timedelta(minutes=minutes)).strftime(FMT)
    return query("SELECT COUNT(*) c FROM password_reset_tokens WHERE user_id=? AND created_at>=?",
                 (user_id, since), one=True)["c"]


def find_valid(token):
    """Return row token jika ada, belum dipakai, dan belum kedaluwarsa."""
    if not token or len(token) > 200:
        return None
    row = query("SELECT * FROM password_reset_tokens WHERE token_hash=?", (_hash(token),), one=True)
    if not row or row["used"]:
        return None
    if datetime.strptime(row["expires_at"], FMT) < _now():
        return None
    return row


def consume(token_id):
    execute("UPDATE password_reset_tokens SET used=1 WHERE id=?", (token_id,))
