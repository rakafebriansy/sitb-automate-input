"""
session_expiration_test.py

Tujuan:
- Simulasikan "pura-pura" kirim data via GET untuk memicu/mengetes session expiration.
- Deteksi session expiry dan (opsional) coba re-login.

Requirements:
pip install python-dotenv requests
"""

import os
import time
import random
import requests
from dotenv import load_dotenv

# ---- konfigurasi ----
load_dotenv(override=True)

LOGIN_URL = os.getenv("LOGIN_URL")         # URL login (POST)
TARGET_URL = os.getenv("TARGET_URL")       # URL yang akan di-get (bisa endpoint data atau "ping")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# kontrol agar aman
MAX_REQUESTS = 500            # total maksimum request dalam satu run
DELAY_MIN = 0.5               # delay antar request minimum (detik)
DELAY_MAX = 2.0               # delay antar request maksimum (detik)
PAUSE_EVERY = 1000            # jeda panjang tiap N request (kamu minta 1000 sebelumnya)
PAUSE_SECONDS = 30            # jeda panjang (detik)
RELOGIN_ON_EXPIRE = True      # coba re-login jika session dianggap expired
REQUEST_TIMEOUT = 15          # timeout network (detik)

# ---- helper ----
def login(session):
    """Melakukan login dan mengembalikan True jika sukses (periksa status atau cookie)."""
    if not LOGIN_URL:
        print("[ERROR] LOGIN_URL tidak diset di .env")
        return False
    creds = {"username": USERNAME, "password": PASSWORD}
    try:
        r = session.post(LOGIN_URL, data=creds, timeout=REQUEST_TIMEOUT, verify=False)
    except Exception as e:
        print("[ERROR] Gagal koneksi saat login:", e)
        return False

    # heuristik sukses: status_code 200 + cookie berubah, atau redirect ke dashboard
    ok = False
    if r.status_code in (200, 302):
        ok = True
    # kadang server return 200 tapi halaman login masih muncul.
    # Periksa seandainya response berisi kata "login" atau "session"
    body = r.text.lower() if r.text else ""
    if "Login" in body and "SELAMAT DATANG DI SISTEM INFORMASI TUBERKULOSIS" not in body and r.status_code == 200:
        ok = False

    print(f"[LOGIN] status={r.status_code}, ok={ok}, cookies={session.cookies.get_dict()}")
    return ok

def is_session_expired(response):
    """
    Heuristik mendeteksi session expiration:
    - HTTP 401/403
    - redirect ke URL yang mengandung 'login'
    - body page mengandung kata 'login'/'session expired' (case-insensitive)
    """
    if response is None:
        return True
    if response.status_code in (401, 403):
        return True
    # redirect history mengandung lokasi menuju login
    for hist in getattr(response, "history", []):
        loc = getattr(hist, "headers", {}).get("Location", "") or ""
        if "login" in loc.lower():
            return True
    # respon final (requests will follow redirects by default)
    try:
        text = response.text.lower() if response.text else ""
        if "login" in text and "logout" not in text:   # sederhana: kalau ada 'login' kemungkinan dikembalikan halaman login
            return True
        if "session expired" in text or "sesi" in text and "expired" in text:
            return True
    except Exception:
        pass
    return False

def build_fake_params(row_idx):
    """Buat query params mirip payload — bebas disesuaikan kolom dataframe jika ada."""
    # contoh params sederhana; jangan kirim data sensitif yang nyata
    return {
        "nama_peserta": f"Peserta-{row_idx}",
        "nik": "0000000000000000",
        "berat_badan": str(random.randint(45, 85)),
        "tinggi_badan": str(random.randint(145, 185)),
        "keterangan": "test_session_ping",
    }

# ---- main runner ----
def main():
    if not TARGET_URL:
        print("[ERROR] TARGET_URL tidak diset di .env")
        return

    session = requests.Session()
    # Optional: set common headers to appear like a normal browser
    session.headers.update({
        "User-Agent": "SessionExpiryTester/1.0 (+https://example.com)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    # login awal
    print("[*] Melakukan login awal ...")
    if not login(session):
        print("[!] Login awal gagal. Hentikan.")
        return

    sent = 0
    for i in range(MAX_REQUESTS):
        sent += 1
        params = build_fake_params(i)
        try:
            # kirim GET request (verify=False meniru environment development; sebaiknya True di production)
            resp = session.get(TARGET_URL, params=params, timeout=REQUEST_TIMEOUT, verify=False)
        except Exception as e:
            print(f"[ERROR] Request #{i} gagal:", e)
            # tunggu sedikit lalu lanjut
            time.sleep(2)
            continue

        # print ringkasan
        print(f"[{i+1}] GET {resp.url} -> status {resp.status_code}")

        # deteksi expired
        if is_session_expired(resp):
            print(f"[!] Session dianggap EXPIRED pada request #{i+1} (status {resp.status_code}).")
            # opsional: simpan response sample
            snippet = (resp.text or "")[:400].replace("\n", " ")
            print("[DEBUG] snippet:", snippet)

            if RELOGIN_ON_EXPIRE:
                print("[*] Mencoba re-login ...")
                ok = login(session)
                if not ok:
                    print("[!] Re-login gagal. Hentikan percobaan.")
                    break
                else:
                    print("[*] Re-login berhasil. Lanjutkan pengujian.")
                    # after re-login, optionally wait a bit
                    time.sleep(1.0 + random.random() * 2.0)
            else:
                print("[*] RELOGIN_ON_EXPIRE=False, berhenti.")
                break

        # delay acak antar request supaya natural
        dt = random.uniform(DELAY_MIN, DELAY_MAX)
        time.sleep(dt)

        # jeda besar tiap PAUSE_EVERY (hanya jika PAUSE_EVERY <= MAX_REQUESTS)
        if PAUSE_EVERY and (i + 1) % PAUSE_EVERY == 0:
            print(f"[*] Done {i+1} requests — pause {PAUSE_SECONDS} seconds...")
            time.sleep(PAUSE_SECONDS)

    print("[*] Selesai run. Total requests attempted:", sent)

if __name__ == "__main__":
    main()
