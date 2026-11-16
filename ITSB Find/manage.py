"""Alat administrasi. Akun Satpam hanya bisa dibuat lewat sini (atau akun awal dari .env), bukan lewat halaman Register.

  python manage.py create-security        # membuat akun Satpam baru (password diminta tanpa tampil di layar)
  python manage.py list-security          # melihat daftar akun Satpam
"""
import argparse
import getpass
import sys

from werkzeug.security import generate_password_hash

from app import app
from database.db import execute, query
from models import user as U
from services.security import EMAIL_RE, valid_password, valid_phone


def create_security(args):
    name = args.name or input("Nama lengkap Satpam: ").strip()
    email = (args.email or input("Email: ")).strip().lower()
    phone, err = valid_phone(args.phone or input("Nomor telepon: "))
    if len(name) < 3 or not EMAIL_RE.match(email) or err:
        sys.exit(err or "Nama atau email tidak valid.")
    pw = args.password or getpass.getpass("Password (min. 8 karakter, huruf+angka): ")
    if valid_password(pw):
        sys.exit(valid_password(pw))
    with app.app_context():
        if U.email_taken(email):
            sys.exit("Email sudah terdaftar.")
        execute("INSERT INTO users(name,email,nim,phone,password_hash,role) VALUES (?,?,NULL,?,?, 'security')",
                (name, email, phone, generate_password_hash(pw)))
    print(f"Akun Satpam dibuat: {email}")


def list_security(_):
    with app.app_context():
        for r in query("SELECT name,email,phone,created_at FROM users WHERE role='security'"):
            print(f"{r['name']} <{r['email']}> {r['phone']} (dibuat {r['created_at']})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-security")
    for a in ("name", "email", "phone", "password"):
        c.add_argument(f"--{a}")
    c.set_defaults(fn=create_security)
    sub.add_parser("list-security").set_defaults(fn=list_security)
    a = ap.parse_args()
    a.fn(a)
