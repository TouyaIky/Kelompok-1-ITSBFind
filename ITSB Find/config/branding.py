"""
Pengaturan logo ITSB FIND. Edit file ini lalu refresh (atau restart server).

Cara memasang logo:
  1. Simpan file logo di folder  static/images/  dengan nama  logo.svg / logo.png / logo.webp / logo.jpg
     (atau nama lain, lalu isi LOGO_FILE di bawah).
  2. Refresh browser (Ctrl+F5). Logo tampil di navbar, sidebar, halaman login/register, footer,
     dan menjadi ikon tab browser.
Jika file logo tidak ada, tampil logo bawaan (ikon + teks ITSB FIND).

Saran: latar transparan (PNG/SVG), versi terang/berwarna yang terbaca di latar gelap.
"""

LOGO_FILE = ""        # nama file di static/images/, contoh "logo-itsb.png". Kosongkan untuk deteksi otomatis logo.svg/png/webp/jpg
SHOW_NAME = False     # False = hanya logo (logo sudah memuat nama). True = tambah teks "ITSB FIND" di samping logo
LOGO_HEIGHT = 40      # tinggi logo di navbar/sidebar (px)
