import requests
import pandas as pd
import random
import time
from datetime import date, timedelta
from dotenv import load_dotenv
import os

# ---------- CONFIG ----------
load_dotenv(override=True)
INPUT_FILE = "data/rejo/4/data_dm_clean.xlsx"
STATE_FILE = "data/rejo/4/state.json"

login_url = os.getenv("LOGIN_URL")
target_url = os.getenv("TARGET_URL")

# ---------- LOGIN ----------
session = requests.Session()
credentials = {"username": os.getenv("USERNAME"), "password": os.getenv("PASSWORD")}
print("[◌] Logging in...")
resp = session.post(login_url, data=credentials, verify=False)
if resp.status_code != 200:
    print("[!] Login failed")
    exit()
print("[✔] Login success")

# ---------- DATA ----------
df = pd.read_excel(INPUT_FILE)
print(f"[INFO] {len(df)} rows loaded")

def random_date_in_year(year=2025):
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime("%Y-%m-%d")

# ---------- LOOP ----------
for idx, row in df.iterrows():
    payload = {
        "tgl_skrining": random_date_in_year(2025),
        "nama_peserta": row["nama_peserta"],
        "nik": row["nik"],
        "tgl_lahir": row["tgl_lahir"],
        "jenis_kelamin_id": row["jenis_kelamin_id"],
        "provinsi_ktp_id": "2",
        "kabupaten_ktp_id": "35",
        "kecamatan_ktp_id": str(row["kecamatan_id"]),
        "kelurahan_ktp_id": str(row["kelurahan_id"]),
        "berat_badan": str(row["berat_badan"]),
        "tinggi_badan": str(row["tinggi_badan"]),
        "imt": str(round(float(row["berat_badan"]) / ((float(row["tinggi_badan"]) / 100) ** 2), 1)) if row["tinggi_badan"] else "",
        "catatan": row["catatan"],
    }

    try:
        r = session.post(target_url, data=payload, verify=False)
        print(f"[{idx+1}] {row['nama_peserta']} -> {r.status_code}")
        if r.status_code != 200:
            print("Response:", r.text)
            break
        time.sleep(random.uniform(0.3, 0.8))
    except Exception as e:
        print(f"❌ Error row {idx+1}: {e}")
        break

print("\n✅ All records submitted successfully.")
