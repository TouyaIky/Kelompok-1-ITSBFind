"""
SATU-SATUNYA tempat untuk mengedit profil anggota kelompok.
Dipakai oleh landing page dan halaman About Us setelah login.

Setiap anggota:
  name     : nama lengkap
  nim      : NIM
  photo    : nama file foto di folder static/images/team/ (mis. "52250036.jpg")
  github   : link profil GitHub, kosongkan "" jika tidak ada
  linkedin : link profil LinkedIn, kosongkan "" jika tidak ada

Foto: letakkan file di static/images/team/ (JPG/JPEG/PNG/WEBP, disarankan persegi dan di bawah 500 KB).
Jika "photo" dikosongkan, sistem otomatis mencari file bernama <NIM>.jpg / .jpeg / .png / .webp.
Jika filenya tidak ditemukan, kartu menampilkan avatar inisial (tidak error).
Tombol GitHub/LinkedIn hanya tampil jika link diisi dan diawali "https://".
"""

PROJECT = {
    "name": "ITSB FIND",
    "institution": "Institut Teknologi Sains Bandung",
    "type": "University Group Project",
    "purpose": "Campus Lost and Found Platform",
}

TEAM_MEMBERS = [
    {"name": "Ahmad Rizki Mubarak", "nim": "52250036", "photo": "foto-rizki.jpg", "github": "https://github.com/TouyaIky", "linkedin": "https://www.linkedin.com/in/mubarak-050807arm/"},
    {"name": "Arya Fharezi", "nim": "52250006", "photo": "foto-arya.jpg", "github": "https://github.com/aryafharezi", "linkedin": "https://www.linkedin.com/in/arya-fharezi-820746415"},
    {"name": "M. Fitrah Aidil Harahap", "nim": "52250031", "photo": "foto-aidil.png", "github": "https://github.com/aidilharhap11", "linkedin": "https://www.linkedin.com/in/muhammad-fitrah-aidil-harahap"},
    {"name": "M. Yustian Putra Muhadi", "nim": "52250015", "photo": "foto-yustian.jpeg", "github": "https://github.com/myustianputramuhadi", "linkedin": "https://www.linkedin.com/in/m-yustian-putra-muhadi-84360738a"},
    {"name": "Paskalis Farelnata Zamasi", "nim": "52250043", "photo": "foto-kalis.jpg", "github": "https://github.com/paskalisfarelnata", "linkedin": "https://www.linkedin.com/in/paskalis-farelnata-3b034338a/"},
]
