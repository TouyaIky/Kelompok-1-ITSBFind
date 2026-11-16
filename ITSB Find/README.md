# ITSB FIND — Lost & Found Kampus ITSB
Flask + SQLite + Pillow + EmailJS. Proyek tugas kelompok, Institut Teknologi Sains Bandung.

## 1. Menjalankan di Windows
1. Instal Python 3.10+ (centang **Add Python to PATH**).
2. Klik dua kali **`run.bat`** (membuat venv, menginstal paket, menyalin `.env.example` → `.env`, menjalankan server).
3. Buka **http://127.0.0.1:5000**

Manual: `python -m venv venv` → `venv\Scripts\activate` → `pip install -r requirements.txt` → `python app.py`.
Database (`database/itsb_find.db`) dibuat otomatis saat pertama kali jalan. Hapus file itu untuk mengulang dari awal.

## 2. Peran, akun Satpam, dan database kosong
Peran pengguna: `student` (Mahasiswa), `lecturer` (Dosen), `guest` (Tamu), `staff` (Staff ITSB), dan `security` (Satpam).
Empat jenis pertama mendaftar sendiri lewat **Register**; field NIM hanya muncul dan wajib untuk Mahasiswa. **Satpam tidak bisa dipilih di Register.**

Database default **kosong**. Satu akun Satpam awal dibuat otomatis saat pertama kali jalan jika belum ada akun Satpam:

| Peran | Email | Password |
|---|---|---|
| Satpam | `satpam@itsb.test` | `Satpam12345` |

Ganti lewat `.env` (`SECURITY_EMAIL`, `SECURITY_PASSWORD`, dst.) sebelum dijalankan pertama kali. Nama lama `ADMIN_*` tetap dibaca.

### Membuat akun Satpam tambahan
```
python manage.py create-security        # password diminta tanpa tampil di layar
python manage.py list-security
```
Satu-satunya cara membuat Satpam: perintah ini, atau akun awal dari `.env`.

### Data contoh (opsional)
Set `SEED_DEMO=1` di `.env`, hapus `database/itsb_find.db`, jalankan ulang. Dibuat: 2 mahasiswa + 1 dosen (`mahasiswa@itsb.test`, `rani@itsb.test`, `dosen@itsb.test`, password `User12345`), 6 barang temuan berfoto "FOTO DEMO", 3 laporan hilang, 1 pengembalian berfoto dokumentasi demo.
Membersihkan: set `SEED_DEMO=0`, hapus `database/itsb_find.db`, `static/uploads/demo_*`, dan folder `instance/`.

## 3. Profil & foto 5 anggota kelompok
Edit **satu file**: `config/team_members.py`. Setiap anggota: `name`, `nim`, `photo`, `github`, `linkedin`.
- **Foto:** simpan file di folder `static/images/team/` (JPG/JPEG/PNG/WEBP, disarankan persegi dan di bawah 500 KB), lalu isi `photo` dengan nama filenya. Jika `photo` kosong, sistem mencari file bernama `<NIM>.jpg` / `.jpeg` / `.png` / `.webp`. Jika file tidak ada, kartu menampilkan avatar inisial.
- Tombol GitHub dan LinkedIn hanya tampil jika link diisi (harus diawali `https://`).
- Berlaku di landing page dan About Us setelah login. Server perlu di-restart (atau refresh jika `FLASK_DEBUG=1`).

## 3b. Logo ITSB FIND
Simpan file logo di `static/images/` dengan nama `logo.png` (atau `logo.svg`, `logo.webp`, `logo.jpg`), lalu refresh dengan Ctrl+F5. Logo otomatis tampil di navbar, sidebar, halaman login/register, footer, dan ikon tab browser. Jika file tidak ada, tampil logo bawaan.
Pengaturan tambahan di `config/branding.py`: `LOGO_FILE` (nama file lain), `SHOW_NAME` (tampilkan/sembunyikan teks "ITSB FIND" di samping logo), `LOGO_HEIGHT` (tinggi logo, px). Disarankan logo berlatar transparan dan terbaca di latar gelap.

## 4. Konfigurasi EmailJS (Kritik & Saran + Lupa Password)
Pengiriman dilakukan dari **backend Flask** lewat REST API EmailJS, sehingga token reset mentah dan Private Key tidak pernah ada di JavaScript browser, dan status sukses/gagal tercatat akurat.

1. Daftar di https://www.emailjs.com → **Email Services → Add New Service** (mis. Gmail) → hubungkan email pengirim. Catat **Service ID**.
2. **Account → General**: salin **Public Key**. **Account → API keys**: salin **Private Key**.
3. **Account → Security**: aktifkan **"Allow EmailJS API for non-browser applications"** (wajib, kalau tidak server ditolak).
4. **Email Templates → Create New Template** dua kali:
   - **Feedback**: isi *Content* dengan `emailjs_templates/feedback.html` (mode Code `</>`). Tab *Settings*: **To Email** = email pengelola ITSB FIND (ketik langsung), **Reply To** = `{{reply_to}}`, **Subject** = `[{{app_name}}] {{category}}: {{subject}}`. Catat **Template ID**.
   - **Reset password**: isi dengan `emailjs_templates/reset_password.html`. **To Email** = `{{to_email}}`, **Subject** = `Reset password ITSB FIND`. Catat **Template ID**.
5. Isi `.env`:
```
EMAILJS_SERVICE_ID=service_xxx
EMAILJS_PUBLIC_KEY=xxxx
EMAILJS_PRIVATE_KEY=xxxx
EMAILJS_FEEDBACK_TEMPLATE_ID=template_xxx
EMAILJS_RESET_TEMPLATE_ID=template_xxx
APP_BASE_URL=http://127.0.0.1:5000
```
6. Restart server. **Uji:** kirim Kritik dan Saran dari landing page → cek inbox pengelola dan menu *Kritik dan Saran* di akun Satpam (kolom Email: Terkirim/Gagal). Lalu coba *Lupa Password?* dengan email akun demo yang kamu ganti ke email asli.

Tanpa konfigurasi: kritik/saran tetap **disimpan** dan dapat dibaca di menu Kritik dan Saran akun Satpam (kolom Email: "Belum terkirim"); pengunjung diberi tahu pesannya diterima, bukan "email terkirim". Reset password tetap menampilkan pesan generik; pada mode `FLASK_DEBUG=1` link reset dicetak di terminal untuk pengujian lokal. Matikan debug saat dipublikasikan.
Catatan: paket gratis EmailJS punya kuota bulanan terbatas.

## 5. Struktur & fungsi
- `app.py` — pabrik aplikasi, CSRF, header keamanan, penanganan error.
- `config/settings.py` — konfigurasi dari `.env`, daftar kategori. `config/team_members.py` — profil tim.
- `database/` — koneksi SQLite, skema, dan seed demo.
- `models/` — query per tabel (semua berparameter). `services/` — pencocokan, validasi gambar, EmailJS, token reset, keamanan.
- `routes/` — `main` (landing/about/mode tamu), `auth`, `user` (daftar, laporan, profil), `feedback`, `satpam`. `manage.py` — membuat akun Satpam.
- `templates/`, `static/` — UI. `emailjs_templates/` — HTML email. `tests/` — uji otomatis.

## 6. Alur status barang (tanpa klaim online)
`pending` (laporan masuk, barang belum diserahkan) → Satpam konfirmasi penerimaan → `stored` (tampil sebagai **Belum Dikembalikan**) → pemilik **datang langsung ke pos Satpam**; Satpam memeriksa identitas dan bukti, menyerahkan barang, memotret serah terima, lalu mengisi form di menu *Pengembalian Barang* → `returned` (**Sudah Dikembalikan**).
Tidak ada form klaim, upload bukti, atau persetujuan klaim di website. Barang tidak bisa dikembalikan dua kali. Jika kepemilikan belum terbukti, Satpam cukup tidak memproses; barang tetap `stored`.
Laporan kehilangan: `open` (Belum Ditemukan) → `resolved` (Selesai). Status **tidak** berubah otomatis karena ada barang mirip; hanya pemilik laporan atau Satpam yang menyelesaikannya. Filter "Memiliki Kandidat Barang Temuan" hanyalah petunjuk dari pencocokan.

## 6b. Privasi
- Nomor telepon pelapor (form temuan/hilang) hanya tampil di dashboard Satpam. Query publik sengaja tidak memilih kolomnya, jadi tidak ada di HTML maupun data modal.
- Foto dokumentasi pengembalian disimpan di `instance/private_uploads/` (bukan folder `static`) dan hanya bisa diambil lewat route `/satpam/return-photo/<id>` yang memeriksa role. Foto barang temuan/hilang tetap publik karena memang ditampilkan di daftar.

## 6c. Migrasi dari versi sebelumnya
Saat dijalankan, database lama (skema v1) otomatis dimigrasi ke v2 dan **semua data dipertahankan**; salinan cadangan dibuat di `database/itsb_find.db.backup-v1`. Pemetaan: role `admin`→`security`, `user`→`student`; status lama → `pending/stored/returned` dan `open/resolved`; catatan bukti lama → `verification_notes`. Laporan lama tidak punya nomor telepon (kosong) dan pengembalian lama tidak punya foto dokumentasi. Akun lama tetap dapat login dengan password yang sama (nomor telepon bisa dilengkapi di menu Profil).

## 7. Keputusan teknis
- `config.py` pada struktur contoh bentrok dengan folder `config/`, jadi dipakai `config/settings.py`.
- Role dicek di backend (403 untuk non-Satpam), bukan hanya disembunyikan di menu.
- Mode Tamu hanya menandai sesi (`/guest`); tidak ada akun yang dibuat. Daftar barang juga bisa dibuka tanpa menekan tombol itu.
- Rate limit disimpan di memori proses (cukup untuk demo; produksi multi-proses sebaiknya Redis). Pembatasan reset juga dicek di database.
- Foto dibaca ulang dan disimpan ulang oleh Pillow (metadata dihapus, maks 1280 px).
- Font dan ikon dimuat dari Google Fonts dan unpkg (Lucide), Chart.js dari jsDelivr: butuh internet saat dibuka.

## 8. Pengujian
`python -m unittest tests.test_smoke -v` — 23 uji: registrasi 4 jenis pengguna, NIM hanya untuk mahasiswa, Satpam tidak bisa didaftarkan, Mode Tamu, akses Satpam (403), filter kedua daftar, status laporan tidak otomatis selesai, privasi nomor telepon, alur pengembalian lengkap dengan foto (validasi 2 MB, tidak bisa dua kali, foto privat), migrasi dari database lama, reset password, Kritik dan Saran, payload EmailJS (mock), database kosong.
Email asli lewat EmailJS **belum diuji** karena kredensial belum ada. Tampilan visual perlu dicek langsung di browser.

## 9. Cara menguji manual
- **Mode Tamu:** buka beranda tanpa login → klik *Masuk sebagai Tamu*. Coba cari dan filter di kedua daftar, buka detail barang. Tekan *Laporkan…* → muncul modal Login/Register. Buka `/satpam/` → diarahkan ke login.
- **Pengembalian:** (1) daftar sebagai mahasiswa, *Laporkan Barang Temuan* (isi nomor telepon, foto wajib). (2) Login Satpam → *Barang Temuan* → *Konfirmasi penerimaan*. (3) Barang tampil di daftar publik sebagai Belum Dikembalikan. (4) Satpam → *Pengembalian Barang* → cari barang → *Proses pengembalian* → isi pemilik, jenis, telepon, catatan, unggah foto → *Tinjau & konfirmasi* → *Ya, serahkan barang*. (5) Status jadi Sudah Dikembalikan; cek *Riwayat Pengembalian* (foto hanya terlihat oleh Satpam).
