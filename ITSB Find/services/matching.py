"""Pencocokan sederhana antara laporan barang hilang dan barang temuan (skor 0-1).
Hanya rekomendasi. Kepemilikan tetap diputuskan Satpam secara langsung."""
import re
from datetime import date
from difflib import SequenceMatcher

STOP = {"yang", "dan", "di", "ke", "dari", "dengan", "ada", "itu", "ini", "atau", "pada", "untuk",
        "warna", "berwarna", "kecil", "besar", "sebuah", "saya", "the", "a", "of", "ukuran"}


def _tokens(text):
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) > 1 and w not in STOP}


def _jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def _sim(a, b):
    a, b = (a or "").lower().strip(), (b or "").lower().strip()
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    return max(ratio if ratio >= 0.6 else 0.0, _jaccard(_tokens(a), _tokens(b)))   # kemiripan karakter rendah dianggap kebetulan


def _date_score(lost_date, found_date):
    try:
        d = (date.fromisoformat(found_date) - date.fromisoformat(lost_date)).days
    except (ValueError, TypeError):
        return 0.0
    if d < -1:          # ditemukan sebelum kehilangan: tidak masuk akal
        return 0.0
    if d <= 3:
        return 1.0
    if d <= 14:
        return 0.5
    return 0.1


def score(lost, found):
    s_name = _sim(lost["item_name"], found["item_name"])
    s_cat = 1.0 if lost["category"] == found["category"] else 0.0
    s_desc = _jaccard(_tokens(lost["description"] + " " + lost["item_name"]),
                      _tokens(found["description"] + " " + found["item_name"]))
    s_loc = _sim(lost["location"], found["location"])
    s_date = _date_score(lost["date_lost"], found["date_found"])
    total = 0.35 * s_name + 0.20 * s_cat + 0.25 * min(1.0, s_desc * 2) + 0.10 * s_loc + 0.10 * s_date
    text_part = 0.35 * s_name + 0.25 * min(1.0, s_desc * 2)
    if text_part < 0.10:   # nama & deskripsi nyaris tidak mirip: kategori/lokasi/tanggal saja tidak cukup
        total = min(total, 0.24)
    if not s_cat:          # kategori berbeda: kemungkinan cocok jauh lebih kecil
        total *= 0.7
    return round(total, 3)


def level(total):
    if total >= 0.60:
        return "Kemiripan tinggi", "high"
    if total >= 0.40:
        return "Kemiripan sedang", "mid"
    if total >= 0.25:
        return "Kemiripan rendah", "low"
    return None, None


def find_matches(lost, found_rows, limit=6):
    out = []
    for f in found_rows:
        t = score(lost, f)
        label, key = level(t)
        if label:
            out.append({"item": f, "score": t, "percent": int(t * 100), "label": label, "level": key})
    out.sort(key=lambda m: m["score"], reverse=True)
    return out[:limit]


def count_candidates(lost, found_rows, min_score=0.40):
    """Jumlah barang temuan dengan kemiripan sedang/tinggi. Hanya petunjuk, tidak mengubah status laporan."""
    return sum(1 for f in found_rows if score(lost, f) >= min_score)
