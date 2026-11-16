"""Pengiriman email lewat EmailJS REST API dari BACKEND.
Dengan cara ini token reset mentah dan Private Key tidak pernah berada di JavaScript publik.

Prasyarat di dashboard EmailJS: Account > Security > aktifkan
"Allow EmailJS API for non-browser applications", lalu pakai Private Key sebagai accessToken."""
import json
import urllib.error
import urllib.request

from flask import current_app

API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def _set(v):
    return bool(v) and not v.startswith("YOUR_")


def is_configured(kind):
    c = current_app.config
    tpl = c["EMAILJS_FEEDBACK_TEMPLATE_ID"] if kind == "feedback" else c["EMAILJS_RESET_TEMPLATE_ID"]
    return _set(c["EMAILJS_SERVICE_ID"]) and _set(c["EMAILJS_PUBLIC_KEY"]) and _set(tpl)


def send_email(kind, params):
    """kind: 'feedback' | 'reset'. Return (status, detail): status in sent | failed | not_configured."""
    if not is_configured(kind):
        return "not_configured", "EmailJS belum dikonfigurasi."
    c = current_app.config
    payload = {
        "service_id": c["EMAILJS_SERVICE_ID"],
        "template_id": c["EMAILJS_FEEDBACK_TEMPLATE_ID"] if kind == "feedback" else c["EMAILJS_RESET_TEMPLATE_ID"],
        "user_id": c["EMAILJS_PUBLIC_KEY"],
        "template_params": params,
    }
    if _set(c["EMAILJS_PRIVATE_KEY"]):
        payload["accessToken"] = c["EMAILJS_PRIVATE_KEY"]
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read().decode(errors="ignore")
            return ("sent", body) if r.status == 200 else ("failed", f"HTTP {r.status}: {body}")
    except urllib.error.HTTPError as e:
        return "failed", f"HTTP {e.code}: {e.read().decode(errors='ignore')[:200]}"
    except Exception as e:  # jaringan, timeout, dll.
        return "failed", str(e)
