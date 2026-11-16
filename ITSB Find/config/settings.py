import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _flag(name, default="0"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DEBUG = _flag("FLASK_DEBUG", "1")
    DATABASE = str(BASE_DIR / "database" / "itsb_find.db")
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024          # batas keras request (3 MB)
    MAX_IMAGE_BYTES = 2 * 1024 * 1024             # batas foto (2 MB)
    ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png"}
    APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")
    SEED_DEMO = _flag("SEED_DEMO", "0")
    PRIVATE_UPLOAD_FOLDER = str(BASE_DIR / "instance" / "private_uploads")   # foto dokumentasi: TIDAK publik
    # Akun Satpam awal (dibuat otomatis jika belum ada akun Satpam). Ganti di .env!
    # Nama variabel lama ADMIN_* tetap didukung agar .env lama tidak rusak.
    SECURITY_NAME = os.getenv("SECURITY_NAME", os.getenv("ADMIN_NAME", "Satpam ITSB"))
    SECURITY_EMAIL = os.getenv("SECURITY_EMAIL", os.getenv("ADMIN_EMAIL", "satpam@itsb.test"))
    SECURITY_PHONE = os.getenv("SECURITY_PHONE", "081200000000")
    SECURITY_PASSWORD = os.getenv("SECURITY_PASSWORD", os.getenv("ADMIN_PASSWORD", "Satpam12345"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _flag("SESSION_COOKIE_SECURE", "0")
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8      # 8 jam

    RESET_TOKEN_MINUTES = 30

    EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID", "")
    EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY", "")
    EMAILJS_PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY", "")
    EMAILJS_FEEDBACK_TEMPLATE_ID = os.getenv("EMAILJS_FEEDBACK_TEMPLATE_ID", "")
    EMAILJS_RESET_TEMPLATE_ID = os.getenv("EMAILJS_RESET_TEMPLATE_ID", "")


CATEGORIES = [
    "Elektronik", "Dompet & Dokumen", "Kartu (KTM/ATM)", "Tas", "Kunci",
    "Pakaian & Aksesori", "Alat Tulis & Buku", "Botol & Peralatan Makan", "Lainnya",
]
LOCATION_SUGGESTIONS = [
    "Perpustakaan", "Kantin", "Masjid / Musala", "Parkiran", "Laboratorium",
    "Ruang Kelas", "Lobi", "Toilet", "Lapangan", "Taman Kampus",
]
USER_TYPES = [("student", "Mahasiswa"), ("lecturer", "Dosen"), ("guest", "Tamu"), ("staff", "Staff ITSB")]
ROLE_LABELS = dict(USER_TYPES, security="Satpam")
FEEDBACK_CATEGORIES = ["Kritik", "Saran", "Bug atau kendala", "Masukan fitur", "Lainnya"]
