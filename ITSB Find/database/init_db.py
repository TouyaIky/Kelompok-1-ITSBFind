import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from werkzeug.security import generate_password_hash

SCHEMA_VERSION = 2


def _core_tables(sfx=""):
    """Tabel yang berubah di versi 2. `sfx` dipakai saat migrasi (tabel sementara)."""
    return f"""
CREATE TABLE users{sfx} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    nim TEXT UNIQUE,
    phone TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student','lecturer','guest','staff','security')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE found_items{sfx} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    date_found TEXT NOT NULL,
    time_found TEXT NOT NULL,
    photo TEXT NOT NULL,
    reporter_phone TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','stored','returned')),
    received_by INTEGER REFERENCES users(id),
    received_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE lost_items{sfx} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    date_lost TEXT NOT NULL,
    time_lost TEXT NOT NULL,
    photo TEXT,
    reporter_phone TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE item_returns{sfx} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    found_item_id INTEGER NOT NULL UNIQUE REFERENCES found_items(id),
    owner_id INTEGER REFERENCES users(id),
    owner_name TEXT NOT NULL,
    owner_type TEXT NOT NULL DEFAULT '',
    owner_phone TEXT NOT NULL DEFAULT '',
    owner_identity TEXT,
    officer_id INTEGER NOT NULL REFERENCES users(id),
    return_date TEXT NOT NULL,
    documentation_photo TEXT,
    verification_notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'returned'
);
"""


COMMON_TABLES = """
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    sender_name TEXT NOT NULL,
    sender_email TEXT NOT NULL,
    category TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email_status TEXT NOT NULL DEFAULT 'pending'
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_found_status ON found_items(status);
CREATE INDEX IF NOT EXISTS idx_found_user ON found_items(user_id);
CREATE INDEX IF NOT EXISTS idx_lost_user ON lost_items(user_id);
CREATE INDEX IF NOT EXISTS idx_lost_status ON lost_items(status);
CREATE INDEX IF NOT EXISTS idx_reset_user ON password_reset_tokens(user_id);
"""

MIGRATE_V1_V2 = """
PRAGMA foreign_keys = OFF;
BEGIN;
""" + _core_tables("_new") + """
INSERT INTO users_new(id,name,email,nim,phone,password_hash,role,created_at)
  SELECT id,name,email,nim,'',password_hash,CASE role WHEN 'admin' THEN 'security' ELSE 'student' END,created_at FROM users;
INSERT INTO found_items_new(id,user_id,item_name,category,description,location,date_found,time_found,photo,reporter_phone,status,received_by,received_at,created_at)
  SELECT id,user_id,item_name,category,description,location,date_found,time_found,photo,'',
         CASE status WHEN 'Menunggu Penyerahan' THEN 'pending' WHEN 'Tersimpan di Satpam' THEN 'stored' ELSE 'returned' END,
         received_by,received_at,created_at FROM found_items;
INSERT INTO lost_items_new(id,user_id,item_name,category,description,location,date_lost,time_lost,photo,reporter_phone,status,created_at)
  SELECT id,user_id,item_name,category,description,location,date_lost,time_lost,photo,'',
         CASE status WHEN 'Sudah Ditemukan' THEN 'resolved' ELSE 'open' END,created_at FROM lost_items;
INSERT INTO item_returns_new(id,found_item_id,owner_id,owner_name,owner_type,owner_phone,owner_identity,officer_id,return_date,documentation_photo,verification_notes,status)
  SELECT id,found_item_id,owner_id,owner_name,'','',owner_identity,officer_id,return_date,NULL,proof_notes,'returned' FROM item_returns;
DROP TABLE item_returns; DROP TABLE found_items; DROP TABLE lost_items; DROP TABLE users;
ALTER TABLE users_new RENAME TO users;
ALTER TABLE found_items_new RENAME TO found_items;
ALTER TABLE lost_items_new RENAME TO lost_items;
ALTER TABLE item_returns_new RENAME TO item_returns;
PRAGMA user_version = 2;
COMMIT;
PRAGMA foreign_keys = ON;
"""


def _has_table(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def init_db(app):
    cfg = app.config
    db_path = Path(cfg["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Path(cfg["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["PRIVATE_UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    existed = db_path.exists() and db_path.stat().st_size > 0
    conn = sqlite3.connect(db_path)
    version = conn.execute("PRAGMA user_version").fetchone()[0]

    if _has_table(conn, "users") and version < SCHEMA_VERSION:
        conn.close()                                                   # data lama dipertahankan
        shutil.copy2(db_path, str(db_path) + ".backup-v1")
        conn = sqlite3.connect(db_path)
        conn.executescript(MIGRATE_V1_V2)
    elif not _has_table(conn, "users"):
        conn.executescript(_core_tables() + f"PRAGMA user_version = {SCHEMA_VERSION};")
    conn.executescript(COMMON_TABLES + INDEXES)
    conn.commit()

    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0 and cfg["SEED_DEMO"]:
        _seed(conn, cfg["UPLOAD_FOLDER"], cfg["PRIVATE_UPLOAD_FOLDER"], cfg)
    if conn.execute("SELECT COUNT(*) FROM users WHERE role='security'").fetchone()[0] == 0:
        _create_security(conn, cfg)
    conn.close()


def _create_security(conn, cfg):
    """Akun Satpam awal. Akun Satpam TIDAK bisa dibuat lewat halaman Register."""
    cur = conn.execute(
        "INSERT OR IGNORE INTO users(name,email,nim,phone,password_hash,role) VALUES (?,?,NULL,?,?, 'security')",
        (cfg["SECURITY_NAME"], cfg["SECURITY_EMAIL"].lower(), cfg["SECURITY_PHONE"], generate_password_hash(cfg["SECURITY_PASSWORD"])))
    conn.commit()
    return cur.lastrowid


def _make_photo(folder, filename, label, color):
    img = Image.new("RGB", (800, 600), (18, 20, 28))
    d = ImageDraw.Draw(img)
    for i in range(600):
        r, g, b = (int(c * (1 - i / 900)) for c in color)
        d.line([(0, i), (800, i)], fill=(max(r, 12), max(g, 12), max(b, 16)))
    d.rounded_rectangle((250, 160, 550, 440), radius=40, outline=(255, 255, 255), width=6)
    d.ellipse((350, 230, 450, 330), outline=(255, 255, 255), width=6)
    try:
        font = ImageFont.load_default(size=34)
    except TypeError:
        font = ImageFont.load_default()
    w = d.textlength(label, font=font)
    d.text(((800 - w) / 2, 480), label, fill=(255, 255, 255), font=font)
    d.text((24, 24), "FOTO DEMO", fill=(255, 255, 255), font=font)
    img.save(Path(folder) / filename, "JPEG", quality=82)


def _seed(conn, upload_folder, private_folder, cfg):
    now = datetime.now()
    day = lambda n: (now - timedelta(days=n)).strftime("%Y-%m-%d")
    officer = _create_security(conn, cfg) or conn.execute("SELECT id FROM users WHERE role='security'").fetchone()[0]
    ids = {}
    for name, email, nim, phone, role in [
        ("Mahasiswa Demo", "mahasiswa@itsb.test", "10122001", "081211110001", "student"),
        ("Rani Pratiwi", "rani@itsb.test", "10122002", "081211110002", "student"),
        ("Dr. Dimas Saputra", "dosen@itsb.test", None, "081211110003", "lecturer")]:
        cur = conn.execute("INSERT INTO users(name,email,nim,phone,password_hash,role) VALUES (?,?,?,?,?,?)",
                           (name, email, nim, phone, generate_password_hash("User12345"), role))
        ids[email] = cur.lastrowid
    u1, u2, u3 = ids["mahasiswa@itsb.test"], ids["rani@itsb.test"], ids["dosen@itsb.test"]

    found = [
        ("Dompet kulit cokelat", "Dompet & Dokumen", "Dompet kulit cokelat tua, ada gantungan kunci kecil berbentuk bintang di resletingnya.", "Perpustakaan", 2, "10:20", "stored", u2, (110, 70, 40)),
        ("Earbuds nirkabel putih", "Elektronik", "Case earbuds putih dengan stiker bulan sabit di tutupnya, ada goresan di sisi kiri.", "Ruang Kelas", 3, "15:45", "stored", u3, (40, 70, 120)),
        ("Botol minum biru tua", "Botol & Peralatan Makan", "Botol stainless biru tua 750 ml, ada penyok kecil di dasar dan stiker kucing.", "Kantin", 5, "12:10", "stored", u2, (30, 60, 110)),
        ("Kunci motor dengan gantungan merah", "Kunci", "Kunci motor dengan gantungan karet berwarna merah bertuliskan nama toko.", "Parkiran", 1, "17:05", "stored", u3, (120, 25, 35)),
        ("Jaket hoodie abu-abu", "Pakaian & Aksesori", "Hoodie abu-abu ukuran L, ada noda tinta kecil di lengan kanan.", "Laboratorium", 8, "09:30", "returned", u1, (70, 70, 80)),
        ("Buku catatan bersampul hitam", "Alat Tulis & Buku", "Buku catatan A5 bersampul hitam, halaman pertama berisi catatan kalkulus.", "Lobi", 0, "08:15", "pending", u2, (50, 50, 60)),
    ]
    fids = []
    for i, (name, cat, desc, loc, ago, tm, status, owner, color) in enumerate(found):
        fn = f"demo_found_{i+1}.jpg"
        _make_photo(upload_folder, fn, name[:28], color)
        received = (now - timedelta(days=ago)).strftime("%Y-%m-%d %H:%M:%S") if status != "pending" else None
        cur = conn.execute(
            "INSERT INTO found_items(user_id,item_name,category,description,location,date_found,time_found,photo,reporter_phone,status,received_by,received_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (owner, name, cat, desc, loc, day(ago), tm, fn, "0812" + str(owner).zfill(8), status, officer if received else None, received))
        fids.append(cur.lastrowid)
    _make_photo(private_folder, "demo_return_1.jpg", "Dokumentasi serah terima", (30, 90, 70))
    conn.execute(
        "INSERT INTO item_returns(found_item_id,owner_name,owner_type,owner_phone,officer_id,return_date,documentation_photo,verification_notes)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (fids[4], "Mahasiswa Demo", "student", "081211110001", officer, day(6) + " 10:30:00", "demo_return_1.jpg",
         "Pemilik menyebutkan noda tinta di lengan kanan dan menunjukkan KTM."))

    for name, cat, desc, loc, ago, tm, owner in [
        ("Dompet cokelat", "Dompet & Dokumen", "Dompet kulit cokelat dengan gantungan bintang kecil.", "Perpustakaan", 3, "10:00", u1),
        ("Botol minum", "Botol & Peralatan Makan", "Botol biru tua stainless, ada stiker kucing.", "Kantin", 6, "12:00", u3),
        ("Charger laptop", "Elektronik", "Charger laptop 65W warna hitam dengan kabel dililit karet.", "Ruang Kelas", 2, "14:30", u2)]:
        conn.execute("INSERT INTO lost_items(user_id,item_name,category,description,location,date_lost,time_lost,reporter_phone)"
                     " VALUES (?,?,?,?,?,?,?,?)", (owner, name, cat, desc, loc, day(ago), tm, "0812" + str(owner).zfill(8)))
    conn.execute(
        "INSERT INTO feedback(user_id,sender_name,sender_email,category,subject,message,email_status) VALUES (?,?,?,?,?,?,?)",
        (u1, "Mahasiswa Demo", "mahasiswa@itsb.test", "Saran", "Notifikasi barang cocok",
         "Akan lebih baik jika ada pengingat ketika ada barang temuan yang mirip dengan laporan saya.", "not_configured"))
    conn.commit()
