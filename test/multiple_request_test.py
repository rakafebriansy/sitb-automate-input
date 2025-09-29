
import os
import time
import random
import argparse
import logging
import sys
from collections import defaultdict

import requests
from dotenv import load_dotenv

# ---- konfigurasi default ----
load_dotenv(override=True)

LOGIN_URL = os.getenv("LOGIN_URL")
TARGET_URL = os.getenv("TARGET_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Default runtime controls (bisa dioverride via CLI)
DEFAULT_DELAY_MIN = 0.1
DEFAULT_DELAY_MAX = 0.5
DEFAULT_PAUSE_EVERY = 1000
DEFAULT_PAUSE_SECONDS = 30
DEFAULT_RELOGIN_ON_EXPIRE = True
DEFAULT_REQUEST_TIMEOUT = 15
DEFAULT_VERIFY_SSL = False

# ---- helpers ----

def login(session, login_url, username, password, timeout, verify):
    if not login_url:
        logging.error("LOGIN_URL tidak diset di .env")
        return False
    creds = {"username": username, "password": password}
    try:
        r = session.post(login_url, data=creds, timeout=timeout, verify=verify)
    except Exception as e:
        logging.error("Gagal koneksi saat login: %s", e)
        return False

    ok = False
    if r.status_code in (200, 302):
        ok = True
    body = (r.text or "").lower()
    print(username)
    print(password)
    # contoh heuristik kuat: jika masih ada kata 'login' dan tidak ada indikasi dashboard -> gagal
    if "login" in body and "selamat datang di sistem informasi tuberkulosis" not in body and r.status_code == 200:
        ok = False

    logging.debug("[LOGIN] status=%s, ok=%s, cookies=%s", r.status_code, ok, session.cookies.get_dict())
    return ok


def is_session_expired(response):
    if response is None:
        return True
    if response.status_code in (401, 403):
        return True
    for hist in getattr(response, "history", []):
        loc = getattr(hist, "headers", {}).get("Location", "") or ""
        if "login" in loc.lower():
            return True
    try:
        text = (response.text or "").lower()
        if "login" in text and "selamat datang di sistem informasi tuberkulosis" not in text:
            return True
        if "session expired" in text or ("sesi" in text and "expired" in text):
            return True
    except Exception:
        pass
    return False


def build_fake_params(row_idx):
    return {
        "nama_peserta": f"Peserta-{row_idx}",
        "nik": "0000000000000000",
        "berat_badan": str(random.randint(45, 85)),
        "tinggi_badan": str(random.randint(145, 185)),
        "keterangan": "test_session_ping",
    }


# ---- single-run runner ----
def run_once(count,
             login_url,
             target_url,
             username,
             password,
             delay_min,
             delay_max,
             pause_every,
             pause_seconds,
             relogin_on_expire,
             timeout,
             verify):
    """Jalankan satu skenario sebanyak `count` request dan kembalikan statistik."""
    stats = defaultdict(int)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "SessionExpiryTester/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    logging.info("--> Starting run: %d requests", count)

    # login awal
    if not login(session, login_url, username, password, timeout, verify):
        logging.error("Login awal gagal. Aborting run.")
        stats['failed_login_initial'] = 1
        return stats

    for i in range(count):
        params = build_fake_params(i)
        try:
            resp = session.get(target_url, params=params, timeout=timeout, verify=verify)
            stats['attempted'] += 1
        except Exception as e:
            logging.warning("Request #%d gagal: %s", i + 1, e)
            stats['network_errors'] += 1
            time.sleep(1)
            continue

        logging.info("[%d/%d] GET %s -> %s", i + 1, count, resp.url, resp.status_code)

        if is_session_expired(resp):
            logging.warning("Session dianggap EXPIRED pada request #%d (status %s)", i + 1, resp.status_code)
            stats['expired'] += 1
            if relogin_on_expire:
                logging.info("Mencoba re-login ...")
                ok = login(session, login_url, username, password, timeout, verify)
                if ok:
                    stats['relogin_success'] += 1
                    logging.info("Re-login berhasil. Lanjutkan.")
                    time.sleep(1.0 + random.random() * 2.0)
                else:
                    stats['relogin_failed'] += 1
                    logging.error("Re-login gagal. Menghentikan run.")
                    break
            else:
                logging.info("RELOGIN_ON_EXPIRE=False, berhenti.")
                break

        # delay acak
        dt = random.uniform(delay_min, delay_max)
        time.sleep(dt)

        if pause_every and (i + 1) % pause_every == 0:
            logging.info("Pause after %d requests for %d seconds", i + 1, pause_seconds)
            time.sleep(pause_seconds)

    logging.info("---> Finished run: attempted=%d, expired=%d, relogin_success=%d, relogin_failed=%d, network_errors=%d",
                 stats.get('attempted', 0), stats.get('expired', 0), stats.get('relogin_success', 0), stats.get('relogin_failed', 0), stats.get('network_errors', 0))
    return stats


# ---- CLI / orchestration ----
def parse_counts(s):
    parts = [p.strip() for p in s.split(',') if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            logging.warning("Invalid count skipped: %s", p)
    return out


def main_cli():
    parser = argparse.ArgumentParser(description="Session expiration tester - multiple counts")
    parser.add_argument('--counts', type=str, required=True,
                        help='Comma-separated counts, mis: 100,1000,10000')
    parser.add_argument('--delay-min', type=float, default=DEFAULT_DELAY_MIN)
    parser.add_argument('--delay-max', type=float, default=DEFAULT_DELAY_MAX)
    parser.add_argument('--pause-every', type=int, default=DEFAULT_PAUSE_EVERY)
    parser.add_argument('--pause-seconds', type=int, default=DEFAULT_PAUSE_SECONDS)
    parser.add_argument('--no-relogin', dest='relogin', action='store_false')
    parser.add_argument('--timeout', type=int, default=DEFAULT_REQUEST_TIMEOUT)
    parser.add_argument('--verify', dest='verify', action='store_true')
    parser.add_argument('--log-level', default='INFO')

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format='%(asctime)s %(levelname)s %(message)s',
                        stream=sys.stdout)

    counts = parse_counts(args.counts)
    if not counts:
        logging.error("No valid counts provided. Use --counts 100,1000")
        return

    if not TARGET_URL:
        logging.error("TARGET_URL tidak diset di .env")
        return

    # Run each scenario sequentially and collect global report
    overall = {}
    for c in counts:
        stats = run_once(c,
                         LOGIN_URL,
                         TARGET_URL,
                         USERNAME,
                         PASSWORD,
                         args.delay_min,
                         args.delay_max,
                         args.pause_every,
                         args.pause_seconds,
                         args.relogin,
                         args.timeout,
                         args.verify)
        overall[c] = dict(stats)

        # singkat jeda antar skenario agar server tidak kebanjiran
        time.sleep(2)

    # Print final summary
    logging.info("\n==== FINAL SUMMARY ====")
    for c, s in overall.items():
        logging.info("Count=%d -> %s", c, s)


if __name__ == '__main__':
    main_cli()
