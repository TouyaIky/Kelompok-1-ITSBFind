"""Uji fungsional (Flask test client). Jalankan: python -m unittest tests.test_smoke -v"""
import io, os, shutil, sqlite3, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from werkzeug.security import generate_password_hash
from app import create_app
from services import security, password_reset as PR
from database.db import get_db

SATPAM = ("satpam@itsb.test", "Satpam12345")
USER = ("mahasiswa@itsb.test", "User12345")
PHONE = "089912345678"   # nomor unik untuk uji privasi


def png(size=(60, 40)):
    b = io.BytesIO(); Image.new("RGB", size, (200, 30, 40)).save(b, "PNG"); b.seek(0); return b


def row(app, sql, args=()):
    with app.app_context():
        return get_db().execute(sql, args).fetchone()


class Base(unittest.TestCase):
    seed = True

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.app = create_app({"DATABASE": f"{self.tmp}/t.db", "UPLOAD_FOLDER": f"{self.tmp}/up", "PRIVATE_UPLOAD_FOLDER": f"{self.tmp}/priv",
                               "TESTING": True, "SEED_DEMO": self.seed})
        security.reset_rate_limits()
        self.c = self.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def client(self, creds=None):
        c = self.app.test_client()
        if creds:
            self.post("/login", {"email": creds[0], "password": creds[1]}, c=c)
        return c

    def csrf(self, c):
        c.get("/feedback")
        with c.session_transaction() as s:
            return s["_csrf"]

    def post(self, url, data=None, c=None, **kw):
        c = c or self.c
        data = dict(data or {}); data["_csrf"] = self.csrf(c)
        return c.post(url, data=data, **kw)

    def text(self, c, url):
        return c.get(url).get_data(as_text=True)


class Auth(Base):
    def test_public_pages_and_team(self):
        for u in ["/", "/feedback", "/login", "/register", "/forgot-password", "/about", "/found-items", "/lost-items"]:
            self.assertEqual(self.c.get(u).status_code, 200, u)
        self.assertEqual(self.text(self.c, "/").count('class="member reveal"'), 5)
        self.assertEqual(self.text(self.c, "/about").count('class="member reveal"'), 5)

    def test_register_four_types(self):
        base = {"phone": "081234500000", "password": "abc12345", "confirm": "abc12345"}
        cases = [("student", "Budi Mahasiswa", "m@x.com", "55555"), ("lecturer", "Dr Dosen Satu", "d@x.com", ""),
                 ("guest", "Tamu Satu", "t@x.com", ""), ("staff", "Staff Satu", "s@x.com", "")]
        for typ, name, email, nim in cases:
            r = self.post("/register", {**base, "user_type": typ, "name": name, "email": email, "nim": nim})
            self.assertEqual(r.status_code, 302, typ)
            self.assertEqual(row(self.app, "SELECT role FROM users WHERE email=?", (email,))["role"], typ)
        # NIM wajib hanya untuk mahasiswa
        r = self.post("/register", {**base, "user_type": "student", "name": "Tanpa Nim", "email": "n@x.com", "nim": ""})
        self.assertIn(b"NIM", r.data); self.assertEqual(r.status_code, 200)
        # telepon wajib
        r = self.post("/register", {**base, "phone": "", "user_type": "guest", "name": "Tanpa Telp", "email": "p@x.com"})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(row(self.app, "SELECT 1 FROM users WHERE email='p@x.com'"))

    def test_security_role_cannot_be_registered(self):
        for typ in ("security", "admin", ""):
            r = self.post("/register", {"user_type": typ, "name": "Penyusup", "email": "x@x.com", "nim": "99999", "phone": "081234500000",
                                        "password": "abc12345", "confirm": "abc12345", "role": "security"})
            self.assertEqual(r.status_code, 200)
        self.assertIsNone(row(self.app, "SELECT 1 FROM users WHERE email='x@x.com'"))

    def test_login_logout_and_lockout(self):
        c = self.client(USER)
        self.assertEqual(c.get("/dashboard").status_code, 200)
        self.post("/logout", c=c)
        self.assertEqual(c.get("/dashboard").status_code, 302)
        security.reset_rate_limits()
        for _ in range(5):
            self.assertEqual(self.post("/login", {"email": USER[0], "password": "salah"}).status_code, 401)
        self.assertEqual(self.post("/login", {"email": USER[0], "password": USER[1]}).status_code, 429)

    def test_csrf_required(self):
        self.assertEqual(self.c.post("/login", data={"email": "a", "password": "b"}).status_code, 400)

    def test_profile(self):
        c = self.client(USER)
        self.assertEqual(c.get("/profile").status_code, 200)
        self.post("/profile", {"action": "profile", "name": "Nama Baru", "phone": "081300000001"}, c=c)
        self.assertEqual(row(self.app, "SELECT name,phone FROM users WHERE email=?", (USER[0],))["phone"], "081300000001")
        r = self.post("/profile", {"action": "password", "current": "salah", "password": "Baru12345", "confirm": "Baru12345"}, c=c)
        self.assertIn(b"salah", r.data)
        self.post("/profile", {"action": "password", "current": USER[1], "password": "Baru12345", "confirm": "Baru12345"}, c=c)
        security.reset_rate_limits()
        self.assertEqual(self.post("/login", {"email": USER[0], "password": "Baru12345"}).status_code, 302)


class Team(Base):
    def test_team_photo_and_links(self):
        folder = os.path.join(self.app.static_folder, "images", "team")
        f1, f2 = os.path.join(folder, "foto-rizki.jpg"), os.path.join(folder, "foto-yustian.jpeg")
        Image.new("RGB", (80, 80), (10, 90, 200)).save(f1, "JPEG"); Image.new("RGB", (80, 80)).save(f2, "PNG")
        try:
            html = self.text(self.c, "/")
            self.assertIn("images/team/foto-rizki.jpg", html)     # dari kolom photo
            self.assertEqual(html.count('class="member reveal"'), 5)
            self.assertNotIn("foto-arya", html)       # file tidak ada -> inisial, tanpa gambar rusak
            self.assertIn("https://github.com/aryafharezi\"", html)   # spasi di ujung link dibersihkan
            self.assertEqual(html.count('aria-label="LinkedIn '), 5)
            self.assertEqual(html.count('aria-label="GitHub '), 5)
            self.assertIn("images/team/foto-rizki.jpg", self.text(self.client(USER), "/about"))
        finally:
            for f in (f1, f2):
                os.path.exists(f) and os.remove(f)


class Branding(Base):
    def test_logo_fallback_and_custom(self):
        folder = os.path.join(self.app.static_folder, "images"); f = os.path.join(folder, "logo.png")
        self.assertIn("logo-mark", self.text(self.c, "/"))                    # tanpa file: logo bawaan
        self.assertNotIn("logo-img", self.text(self.c, "/"))
        Image.new("RGBA", (120, 40), (224, 32, 47, 255)).save(f, "PNG")
        try:
            for url in ["/", "/login", "/found-items", "/about"]:
                html = self.text(self.c, url)
                self.assertIn('class="logo-img"', html, url); self.assertIn("images/logo.png?v=", html, url)
            self.assertIn('rel="icon" href="/static/images/logo.png', self.text(self.c, "/"))
            self.assertIn("logo-img", self.text(self.client(USER), "/dashboard"))
            self.assertIn("logo-img", self.text(self.client(SATPAM), "/satpam/"))
            self.assertNotIn("ITSB <b>FIND</b>", self.text(self.c, "/"))       # default: hanya logo, tidak dobel
            from config import branding
            branding.SHOW_NAME = True
            try:
                self.assertIn("ITSB <b>FIND</b>", self.text(self.c, "/"))
            finally:
                branding.SHOW_NAME = False
        finally:
            os.path.exists(f) and os.remove(f)


class Guest(Base):
    def test_guest_mode(self):
        c = self.app.test_client()
        r = c.get("/guest")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(row(self.app, "SELECT COUNT(*) n FROM users")["n"], 4)       # tidak ada akun sementara
        for u in ["/found-items", "/lost-items", "/about"]:
            self.assertIn("Mode Tamu", self.text(c, u), u)
        self.assertIn('data-modal-open=loginModal', self.text(c, "/found-items"))   # fitur lapor memicu modal login
        for u in ["/dashboard", "/report-found", "/report-lost", "/my-reports", "/profile", "/satpam/", "/satpam/found", "/satpam/returns"]:
            self.assertEqual(c.get(u).status_code, 302, u)
        self.assertEqual(c.post("/report-found", data={"_csrf": self.csrf(c)}).status_code, 302)

    def test_regular_user_blocked_from_satpam(self):
        c = self.client(USER)
        for u in ["/satpam/", "/satpam/found", "/satpam/lost", "/satpam/returns", "/satpam/history", "/satpam/feedback", "/satpam/return-photo/1"]:
            self.assertEqual(c.get(u).status_code, 403, u)
        self.assertEqual(self.post("/satpam/found/1/confirm", c=c).status_code, 403)
        self.assertEqual(self.post("/satpam/returns/1", c=c).status_code, 403)


class Lists(Base):
    def test_filters(self):
        g = self.app.test_client()
        self.assertIn("Dompet kulit", self.text(g, "/found-items?q=dompet"))
        self.assertNotIn("Dompet kulit", self.text(g, "/found-items?category=Kunci"))
        self.assertNotIn("Buku catatan", self.text(g, "/found-items"))          # status pending belum publik
        self.assertIn("Jaket hoodie", self.text(g, "/found-items?status=returned"))
        self.assertNotIn("Jaket hoodie", self.text(g, "/found-items?status=stored"))
        self.assertNotIn("Dompet kulit", self.text(g, "/found-items?date_from=2999-01-01"))
        self.assertIn("Charger laptop", self.text(g, "/lost-items?q=charger"))
        self.assertNotIn("Charger laptop", self.text(g, "/lost-items?category=Kunci"))

    def test_lost_status_filters_and_no_auto_resolve(self):
        g = self.app.test_client()
        cand = self.text(g, "/lost-items?status=candidates")
        self.assertIn("Dompet cokelat", cand); self.assertNotIn("Charger laptop", cand)
        self.assertIn("Dompet cokelat", self.text(g, "/lost-items?status=open"))
        self.assertNotIn("Dompet cokelat", self.text(g, "/lost-items?status=resolved"))
        self.assertEqual(row(self.app, "SELECT status FROM lost_items WHERE item_name='Dompet cokelat'")["status"], "open")
        # hanya pemilik / Satpam yang bisa menyelesaikan
        c = self.client(SATPAM); self.post("/satpam/lost/1/resolve", c=c)
        self.assertIn("Dompet cokelat", self.text(g, "/lost-items?status=resolved"))


class Privacy(Base):
    def report(self, c, path, name, **over):
        data = {"item_name": name, "category": "Elektronik", "description": "Earbuds putih dengan stiker bulan", "location": "Ruang Kelas",
                "date": "2026-10-30", "time": "10:00", "phone": PHONE, "photo": (png(), "f.png")}
        data.update(over)
        return self.post(path, data, c=c, content_type="multipart/form-data")

    def test_phone_required_and_private(self):
        u = self.client(("rani@itsb.test", "User12345"))
        r = self.report(u, "/report-found", "Earbuds", phone="")
        self.assertIn(b"nomor telepon", r.data.lower())
        r = self.report(u, "/report-found", "Earbuds", phone="abc")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.report(u, "/report-found", "Earbuds nirkabel privat").status_code, 302)
        self.assertEqual(self.report(u, "/report-lost", "Dompet privat", photo=(io.BytesIO(b""), "")).status_code, 302)
        fid = row(self.app, "SELECT id FROM found_items WHERE item_name='Earbuds nirkabel privat'")["id"]
        sat = self.client(SATPAM); self.post(f"/satpam/found/{fid}/confirm", c=sat)
        # tidak ada satu pun halaman non-Satpam yang memuat nomor tersebut
        other = self.client(USER)
        for who, c in {"guest": self.app.test_client(), "user-lain": other, "pelapor": u}.items():
            for url in ["/found-items", "/lost-items", "/found-items?q=privat", "/lost-items?q=privat", "/about", "/dashboard", "/my-reports", "/profile"]:
                self.assertNotIn(PHONE, self.text(c, url), f"{who} {url}")
        self.assertEqual(other.get(f"/lost/{row(self.app, 'SELECT id FROM lost_items WHERE item_name=\"Dompet privat\"')['id']}").status_code, 404)
        # Satpam melihatnya
        self.assertIn(PHONE, self.text(sat, "/satpam/found"))
        self.assertIn(PHONE, self.text(sat, "/satpam/lost"))

    def test_public_queries_never_select_phone(self):
        from models import found_item, lost_item
        self.assertNotIn("phone", found_item.PUBLIC); self.assertNotIn("phone", lost_item.PUBLIC)


class Returns(Base):
    def make_stored(self):
        u = self.client(("rani@itsb.test", "User12345"))
        data = {"item_name": "Earbuds kembali", "category": "Elektronik", "description": "Earbuds putih stiker bulan", "location": "Kantin",
                "date": "2026-10-30", "time": "10:00", "phone": PHONE, "photo": (png(), "f.png")}
        self.post("/report-found", data, c=u, content_type="multipart/form-data")
        fid = row(self.app, "SELECT id FROM found_items WHERE item_name='Earbuds kembali'")["id"]
        sat = self.client(SATPAM)
        self.assertEqual(row(self.app, "SELECT status FROM found_items WHERE id=?", (fid,))["status"], "pending")
        self.post(f"/satpam/found/{fid}/confirm", c=sat)
        self.assertEqual(row(self.app, "SELECT status FROM found_items WHERE id=?", (fid,))["status"], "stored")
        return fid, sat

    def ret(self, sat, fid, photo="ok", **over):
        d = {"owner_name": "Pemilik Asli", "owner_type": "student", "owner_phone": "081377770000", "notes": "KTM cocok, menyebut stiker bulan"}
        d.update(over)
        if photo == "ok": d["photo"] = (png(), "doc.png")
        elif photo is not None: d["photo"] = photo
        return self.post(f"/satpam/returns/{fid}", d, c=sat, content_type="multipart/form-data")

    def test_full_return_flow(self):
        fid, sat = self.make_stored()
        self.assertIn("Earbuds kembali", self.text(sat, "/satpam/returns?q=earbuds"))
        self.assertIn("Earbuds kembali", self.text(sat, f"/satpam/returns?q={fid}"))
        self.assertEqual(sat.get(f"/satpam/returns/{fid}").status_code, 200)
        # validasi
        self.assertIn(b"Foto wajib", self.ret(sat, fid, photo=None).data)
        self.assertIn(b"2 MB", self.ret(sat, fid, photo=(io.BytesIO(b"\xff\xd8" + b"0" * (2 * 1024 * 1024 + 10)), "b.png")).data)
        self.assertIn(b"Foto", self.ret(sat, fid, photo=(io.BytesIO(b"bukan gambar"), "x.png")).data)
        self.assertIn(b"wajib", self.ret(sat, fid, notes="").data)
        self.assertEqual(row(self.app, "SELECT status FROM found_items WHERE id=?", (fid,))["status"], "stored")
        # sukses
        self.assertEqual(self.ret(sat, fid).status_code, 302)
        self.assertEqual(row(self.app, "SELECT status FROM found_items WHERE id=?", (fid,))["status"], "returned")
        r = row(self.app, "SELECT * FROM item_returns WHERE found_item_id=?", (fid,))
        self.assertEqual((r["owner_name"], r["owner_type"], r["owner_phone"]), ("Pemilik Asli", "student", "081377770000"))
        self.assertTrue(r["officer_id"]); self.assertTrue(r["return_date"])
        # foto privat: bukan di folder publik
        self.assertTrue(os.path.exists(f"{self.tmp}/priv/{r['documentation_photo']}"))
        self.assertFalse(os.path.exists(f"{self.tmp}/up/{r['documentation_photo']}"))
        self.assertIn("Pemilik Asli", self.text(sat, "/satpam/history"))
        # tidak bisa dua kali
        self.assertEqual(self.ret(sat, fid).status_code, 302)
        self.assertEqual(row(self.app, "SELECT COUNT(*) n FROM item_returns WHERE found_item_id=?", (fid,))["n"], 1)
        self.assertEqual(len(os.listdir(f"{self.tmp}/priv")), 2)   # demo + 1 (foto percobaan ke-2 dibersihkan)
        # status tampil sebagai sudah dikembalikan
        self.assertIn("Earbuds kembali", self.text(self.app.test_client(), "/found-items?status=returned"))
        # akses foto: hanya Satpam
        rid = r["id"]
        self.assertEqual(sat.get(f"/satpam/return-photo/{rid}").status_code, 200)
        self.assertEqual(sat.get(f"/satpam/return-photo/{rid}").headers["Cache-Control"], "private, no-store")
        self.assertEqual(self.client(USER).get(f"/satpam/return-photo/{rid}").status_code, 403)
        self.assertEqual(self.app.test_client().get(f"/satpam/return-photo/{rid}").status_code, 302)
        self.assertEqual(self.app.test_client().get(f"/static/../instance/{r['documentation_photo']}").status_code, 404)

    def test_cannot_return_pending(self):
        sat = self.client(SATPAM)
        pend = row(self.app, "SELECT id FROM found_items WHERE status='pending'")["id"]
        self.assertEqual(sat.get(f"/satpam/returns/{pend}").status_code, 302)
        self.assertEqual(self.ret(sat, pend).status_code, 302)
        self.assertEqual(row(self.app, "SELECT status FROM found_items WHERE id=?", (pend,))["status"], "pending")

    def test_dashboard_stats(self):
        fid, sat = self.make_stored()
        before = self.text(sat, "/satpam/")
        self.ret(sat, fid)
        self.assertEqual(sat.get("/satpam/").status_code, 200)
        from models import found_item
        with self.app.app_context():
            c = found_item.counts()
        self.assertEqual((c["stored"], c["returned"]), (4, 2))


class Matching(Base):
    def test_scores(self):
        from services.matching import score, level
        a = {"item_name": "Dompet cokelat", "category": "Dompet & Dokumen", "description": "dompet kulit gantungan bintang", "location": "Perpustakaan", "date_lost": "2026-10-30"}
        b = {"item_name": "Dompet kulit cokelat", "category": "Dompet & Dokumen", "description": "gantungan bintang kecil", "location": "Perpustakaan", "date_found": "2026-10-31"}
        c = {"item_name": "Kunci motor", "category": "Kunci", "description": "gantungan merah", "location": "Parkiran", "date_found": "2026-10-31"}
        self.assertEqual(level(score(a, b))[1], "high"); self.assertIsNone(level(score(a, c))[0])

    def test_owner_sees_matches(self):
        c = self.client(USER)
        self.assertIn("Dompet kulit cokelat", self.text(c, "/lost/1"))


class Reset(Base):
    def test_reset_flow(self):
        r = self.post("/forgot-password", {"email": "tidak@ada.com"}, follow_redirects=True)
        self.assertIn("Jika email terdaftar".encode(), r.data)
        with self.app.app_context():
            uid = get_db().execute("SELECT id FROM users WHERE email=?", (USER[0],)).fetchone()["id"]
            token = PR.create_token(uid, 30)
            self.assertNotEqual(get_db().execute("SELECT token_hash FROM password_reset_tokens").fetchone()["token_hash"], token)
        self.assertEqual(self.c.get(f"/reset-password/{token}").status_code, 200)
        self.assertEqual(self.post(f"/reset-password/{token}", {"password": "pendek", "confirm": "pendek"}).status_code, 400)
        self.assertEqual(self.post(f"/reset-password/{token}", {"password": "Baru12345", "confirm": "Baru12345"}).status_code, 302)
        self.assertEqual(self.c.get(f"/reset-password/{token}").status_code, 302)
        self.assertEqual(self.post("/login", {"email": USER[0], "password": "Baru12345"}).status_code, 302)

    def test_expired_invalid_and_limit(self):
        with self.app.app_context():
            token = PR.create_token(get_db().execute("SELECT id FROM users LIMIT 1").fetchone()["id"], -1)
        self.assertEqual(self.c.get(f"/reset-password/{token}").status_code, 302)
        self.assertEqual(self.c.get("/reset-password/ngawur").status_code, 302)
        for _ in range(5): self.post("/forgot-password", {"email": USER[0]})
        self.assertEqual(self.post("/forgot-password", {"email": USER[0]}).status_code, 429)


class Feedback(Base):
    OK = {"name": "Tamu", "email": "tamu@x.com", "category": "Saran", "subject": "Halo", "message": "Pesan percobaan yang cukup panjang."}

    def test_feedback_and_visibility(self):
        h = {"X-CSRF-Token": self.csrf(self.c)}
        self.assertEqual(self.c.post("/feedback/send", json={**self.OK, "message": "pendek"}, headers=h).status_code, 400)
        r = self.c.post("/feedback/send", json=self.OK, headers=h)
        self.assertEqual(r.status_code, 202); self.assertNotEqual(r.get_json()["status"], "sent")
        self.assertEqual(self.c.post("/feedback/send", json=self.OK, headers=h).status_code, 429)
        self.assertEqual(row(self.app, "SELECT email_status FROM feedback WHERE sender_email='tamu@x.com'")["email_status"], "not_configured")
        self.assertIn("Pesan percobaan", self.text(self.client(SATPAM), "/satpam/feedback"))
        self.assertEqual(self.client(USER).get("/satpam/feedback").status_code, 403)

    def test_emailjs_payload_and_failure(self):
        from unittest import mock
        self.app.config.update(EMAILJS_SERVICE_ID="svc", EMAILJS_PUBLIC_KEY="pub", EMAILJS_PRIVATE_KEY="prv", EMAILJS_FEEDBACK_TEMPLATE_ID="tpl")
        cap = {}
        class R:
            status = 200
            def read(self): return b"OK"
            def __enter__(s): return s
            def __exit__(s, *a): pass
        import json
        def fake(req, timeout=0): cap.update(json.loads(req.data)); return R()
        body = {"name": "Tester", "email": "t@x.com", "category": "Kritik", "subject": "Sub", "message": "Isi pesan lengkap ya"}
        with mock.patch("services.email_service.urllib.request.urlopen", fake):
            r = self.c.post("/feedback/send", json=body, headers={"X-CSRF-Token": self.csrf(self.c)})
        self.assertEqual(r.status_code, 200); self.assertEqual(cap["template_id"], "tpl"); self.assertEqual(cap["accessToken"], "prv")
        security.reset_rate_limits()
        with mock.patch("services.email_service.urllib.request.urlopen", side_effect=OSError("down")):
            r = self.c.post("/feedback/send", json={**body, "message": "Pesan kedua yang berbeda ya"}, headers={"X-CSRF-Token": self.csrf(self.c)})
        self.assertEqual(r.get_json()["status"], "failed"); self.assertEqual(r.status_code, 202)


class EmptyDb(Base):
    seed = False

    def test_empty_start(self):
        html = self.text(self.c, "/")
        self.assertEqual(html.count('data-count="0"'), 4)
        c = self.client(SATPAM)
        for u in ["/satpam/", "/satpam/found", "/satpam/lost", "/satpam/returns", "/satpam/history", "/satpam/feedback", "/profile"]:
            self.assertEqual(c.get(u).status_code, 200, u)
        for u in ["/found-items", "/lost-items"]:
            self.assertEqual(self.c.get(u).status_code, 200)


class Migration(unittest.TestCase):
    def test_v1_to_v2_keeps_data(self):
        tmp = tempfile.mkdtemp(); db = f"{tmp}/old.db"
        conn = sqlite3.connect(db)
        conn.executescript(open(os.path.join(os.path.dirname(__file__), "legacy_schema.sql")).read())
        conn.execute("INSERT INTO users(id,name,email,nim,password_hash,role) VALUES (1,'Petugas Lama','admin@itsb.test','ADMIN001',?, 'admin')", (generate_password_hash("Lama12345"),))
        conn.execute("INSERT INTO users(id,name,email,nim,password_hash,role) VALUES (2,'Mhs Lama','mhs@itsb.test','12345',?, 'user')", (generate_password_hash("Lama12345"),))
        conn.execute("INSERT INTO found_items(id,user_id,item_name,category,description,location,date_found,time_found,photo,status) VALUES (1,2,'Dompet lama','Lainnya','deskripsi lama sekali','Kantin','2026-10-01','10:00','a.jpg','Dikembalikan')")
        conn.execute("INSERT INTO found_items(id,user_id,item_name,category,description,location,date_found,time_found,photo,status) VALUES (2,2,'Tas lama','Tas','deskripsi tas lama','Lobi','2026-10-02','10:00','b.jpg','Tersimpan di Satpam')")
        conn.execute("INSERT INTO lost_items(user_id,item_name,category,description,location,date_lost,time_lost,status) VALUES (2,'Kunci lama','Kunci','deskripsi kunci lama','Parkiran','2026-10-03','09:00','Sudah Ditemukan')")
        conn.execute("INSERT INTO item_returns(found_item_id,owner_id,owner_name,owner_identity,proof_notes,officer_id,return_date) VALUES (1,2,'Mhs Lama','NIM 12345','KTM cocok',1,'2026-10-05 10:00:00')")
        conn.execute("INSERT INTO feedback(sender_name,sender_email,category,subject,message) VALUES ('A','a@x.com','Saran','S','pesan lama')")
        conn.commit(); conn.close()
        app = create_app({"DATABASE": db, "UPLOAD_FOLDER": f"{tmp}/up", "PRIVATE_UPLOAD_FOLDER": f"{tmp}/priv", "TESTING": True})
        self.assertTrue(os.path.exists(db + ".backup-v1"))
        with app.app_context():
            d = get_db()
            self.assertEqual(d.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual([r["role"] for r in d.execute("SELECT role FROM users ORDER BY id")], ["security", "student"])
            self.assertEqual([r["status"] for r in d.execute("SELECT status FROM found_items ORDER BY id")], ["returned", "stored"])
            self.assertEqual(d.execute("SELECT status FROM lost_items").fetchone()["status"], "resolved")
            r = d.execute("SELECT * FROM item_returns").fetchone()
            self.assertEqual((r["owner_name"], r["verification_notes"], r["owner_identity"]), ("Mhs Lama", "KTM cocok", "NIM 12345"))
            self.assertEqual(d.execute("SELECT COUNT(*) n FROM feedback").fetchone()["n"], 1)
            self.assertEqual(d.execute("SELECT COUNT(*) n FROM users WHERE role='security'").fetchone()["n"], 1)   # tidak membuat akun ganda
            self.assertEqual(d.execute("PRAGMA foreign_key_check").fetchall(), [])
        c = app.test_client(); c.get("/feedback")
        with c.session_transaction() as s: tok = s["_csrf"]
        r = c.post("/login", data={"email": "admin@itsb.test", "password": "Lama12345", "_csrf": tok})
        self.assertIn("/satpam", r.headers["Location"])
        for u in ["/satpam/", "/satpam/history", "/satpam/found", "/found-items", "/lost-items"]:
            self.assertEqual(c.get(u).status_code, 200, u)
        create_app({"DATABASE": db, "UPLOAD_FOLDER": f"{tmp}/up", "PRIVATE_UPLOAD_FOLDER": f"{tmp}/priv", "TESTING": True})  # idempoten
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
