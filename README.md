# ITSB FIND
### Sistem Informasi Lost & Found Institut Teknologi Sains Bandung

<p align="center">
  <img src="Logo.png" alt="Logo ITSB FIND" width="180">
</p>

<p align="center">
  **Kelompok 1 — Sains Data ITSB**
</p>

<p align="center">
  *Membantu menemukan kembali, menghubungkan pemilik dengan barang yang hilang.*
</p>

---

## Tentang Proyek

**ITSB FIND** merupakan aplikasi berbasis web yang dikembangkan oleh Kelompok 1, mahasiswa Program Studi Sains Data Institut Teknologi Sains Bandung (ITSB), sebagai solusi digital untuk membantu pengelolaan informasi barang hilang dan barang temuan di lingkungan kampus.

Permasalahan kehilangan barang di lingkungan kampus dapat menyulitkan pemilik dalam memperoleh informasi mengenai keberadaan barangnya. Di sisi lain, informasi mengenai barang yang ditemukan juga belum tentu dapat tersampaikan kepada pemilik secara efektif.

Oleh karena itu, ITSB FIND dikembangkan sebagai sistem informasi yang menyediakan wadah terpusat untuk pelaporan, pencarian, pendataan, serta pengelolaan barang hilang dan temuan.

Melalui aplikasi ini, pengguna dapat melaporkan barang yang hilang maupun ditemukan, sedangkan petugas Satpam memiliki akses khusus untuk membantu proses verifikasi dan pengelolaan pengembalian barang.

## Tujuan Pengembangan

1. Mempermudah civitas akademika ITSB dalam melaporkan barang hilang dan barang temuan.
2. Menyediakan informasi barang hilang dan temuan dalam satu platform.
3. Mempermudah proses pencarian informasi barang.
4. Membantu petugas Satpam dalam mengelola data dan proses pengembalian barang.
5. Meningkatkan keteraturan pendataan barang hilang dan temuan di lingkungan kampus.

## Fitur Aplikasi

### 1. Fitur Pengguna
- Registrasi dan login akun.
- Melaporkan barang yang hilang.
- Melaporkan barang yang ditemukan.
- Mengunggah foto barang sebagai informasi pendukung.
- Melihat daftar barang hilang dan barang temuan.
- Mencari dan memfilter informasi barang.
- Melihat detail informasi barang.
- Mengelola informasi akun pengguna.

### 2. Fitur Petugas Satpam
- Login melalui halaman khusus petugas.
- Melihat dan mengelola laporan barang hilang dan temuan.
- Melakukan pengelolaan status laporan.
- Membantu proses verifikasi barang.
- Mengelola proses pengembalian barang.
- Mencatat dokumentasi serah terima barang.

### 3. Fitur Pendukung
- Akses pengunjung untuk melihat informasi barang.
- Pengelolaan foto dan aset aplikasi.
- Halaman profil tim pengembang.
- Fitur pendukung pengiriman email melalui integrasi EmailJS.

## Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| Flask | Framework pengembangan aplikasi web |
| SQLite | Sistem manajemen basis data |
| HTML | Struktur halaman web |
| CSS | Pengaturan tampilan dan desain |
| JavaScript | Interaksi pada sisi pengguna |
| Pillow | Pemrosesan gambar |
| EmailJS | Integrasi layanan email |

## Struktur Repository

Repository ini memiliki beberapa folder dan berkas utama:

| Folder / File | Keterangan |
|---|---|
| `ITSB Find/` | Folder utama yang berisi source code dan komponen aplikasi. |
| `Presentasi/` | Berisi materi presentasi proyek Kelompok 1. |
| `ITSB Find.zip` | Arsip ZIP berisi salinan proyek untuk memudahkan pengunduhan. |
| `Logo.png` | Logo aplikasi ITSB FIND. |
| `README.md` | Dokumentasi utama repository. |
| `Swimlane.md` | Dokumentasi diagram Swimlane yang menggambarkan alur proses sistem. |

Folder `ITSB Find/` merupakan sumber utama kode program aplikasi. Arsip ZIP disediakan sebagai alternatif untuk memperoleh salinan proyek secara keseluruhan.

## Dokumentasi Proyek

Repository ini juga menyediakan dokumentasi pendukung, yaitu:

- **Presentasi Kelompok:** Materi yang menjelaskan latar belakang, tujuan, rancangan, fitur, dan pengembangan ITSB FIND.
- **Swimlane Diagram:** Visualisasi alur proses dan interaksi antara pihak-pihak yang terlibat dalam sistem.
- **Source Code:** Implementasi aplikasi yang dapat dipelajari dan dikembangkan lebih lanjut.

## Cara Menjalankan Aplikasi

Aplikasi dapat dijalankan secara lokal dengan langkah-langkah berikut.

### 1. Persyaratan

Pastikan perangkat telah memiliki:
- Python 3.10 atau lebih baru.
- Git (opsional, untuk mengkloning repository).
- Terminal atau Command Prompt.

### 2. Unduh Repository

Clone repository:

```bash
git clone https://github.com/TouyaIky/ITSB-Find.git
```

Masuk ke folder proyek:

```bash
cd ITSB-Find
```

Jika menggunakan arsip ZIP, unduh dan ekstrak terlebih dahulu, kemudian masuk ke folder proyek.

### 3. Buat Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instal Dependensi

```bash
pip install -r requirements.txt
```

### 5. Konfigurasi Environment

Salin file konfigurasi contoh:

Windows:

```bash
copy .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Sesuaikan nilai konfigurasi di dalam file `.env`, terutama `SECRET_KEY` dan kredensial akun petugas Satpam.

Untuk fitur email, konfigurasi EmailJS perlu diisi menggunakan kredensial layanan yang sesuai.

### 6. Jalankan Aplikasi

```bash
python app.py
```

Setelah aplikasi berjalan, buka browser dan akses:

```text
http://127.0.0.1:5000
```

## Akses Aplikasi Online

ITSB FIND juga dapat diakses melalui alamat berikut:

**Website:** https://touya05.pythonanywhere.com

## Tim Pengembang

Proyek ITSB FIND dikembangkan oleh:

**Kelompok 1 — Program Studi Sains Data**  
**Institut Teknologi Sains Bandung (ITSB)**

| No. | Nama Anggota |
|---|---|
| 1 | Yustian |
| 2 | Arya |
| 3 | Ahmad Rizki Mubarak |
| 4 | Paskalis |
| 5 | Aidil |

## Penutup

ITSB FIND merupakan bentuk implementasi pemanfaatan teknologi informasi untuk membantu menyelesaikan permasalahan sederhana yang dapat dijumpai di lingkungan kampus.

Melalui proyek ini, diharapkan proses pelaporan, pencarian, pendataan, dan pengembalian barang hilang maupun barang temuan dapat dilakukan secara lebih terstruktur dan mudah diakses.

---

<p align="center">
  **ITSB FIND — Find What Matters, Return What Belongs.**
</p>

<p align="center">
  Dikembangkan oleh Kelompok 1 | Sains Data ITSB
</p>
