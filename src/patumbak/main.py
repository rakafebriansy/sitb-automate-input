from dotenv import load_dotenv
from datetime import date, timedelta, datetime
import os
import pandas as pd
import random
import requests
import time
import json
import math

# ---------- Config ----------
INPUT_FILE = "data/data_clean.xlsx"
ITERATE = None
STATE_FILE = "data/state.json"
load_dotenv(override=True)

# ---------- Utils ----------
import random
from datetime import date, timedelta

def random_date_in_year(year=2025, start_month=1, end_month=12, dmy=False):
    start_date = date(year, start_month, 1)

    if end_month == 12:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year, end_month + 1, 1) - timedelta(days=1)

    delta_days = (end_date - start_date).days
    random_days = random.randint(0, delta_days)

    result_date = start_date + timedelta(days=random_days)
    return result_date.strftime("%d-%m-%Y") if dmy else result_date.strftime("%Y-%m-%d")

def random_date(start_year=1980, end_year=2010, dmy=False):
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    delta_days = (end_date - start_date).days
    random_days = random.randint(0, delta_days)
    result_date = start_date + timedelta(days=random_days)
    return result_date.strftime("%d-%m-%Y") if dmy else result_date.strftime("%Y-%m-%d")

def load_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"last_row": 0}

def save_state(state_file, state):
    with open(state_file, "w") as f:
        json.dump(state, f)

def generate_phone_number(international=False):
    # Prefix common Indonesia provider (08xx)
    prefixes = ["0811", "0812", "0813", "0821", "0822", "0823",
                "0852", "0853", "0851", "0856", "0857", "0858",
                "0895", "0896", "0897", "0898", "0899"]
    
    prefix = random.choice(prefixes)
    
    # 6-8 digit random number
    length = random.randint(6, 8)
    number = ''.join(random.choices("0123456789", k=length))
    
    phone = prefix + number
    
    if international:
        phone = "+62" + phone[1:]
    
    return phone

# ---------- Login ----------
session = requests.Session()
login_url = os.getenv("LOGIN_URL")

credentials = {
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD")
}

print("[◌] Logging in with:", credentials)

resp = session.post(login_url, data=credentials, verify=False)
print("[INFO] Login response:", resp.status_code)
print("[INFO] Cookies after login:", session.cookies.get_dict())

if resp.status_code != 200:
    print("[!] Login failed, stopping...")
    exit(1)
print("[✔] Login success.")

# ---------- Load Data ----------
df = pd.read_excel(INPUT_FILE)
target_url = os.getenv("TARGET_URL")

state = load_state(STATE_FILE)
start_index = state["last_row"]
print(f"[INFO] Starting from {start_index}")

current_year = datetime.now().year
iterate_count = ITERATE if (ITERATE and ITERATE > 0) else len(df)
print(f"[INFO] Total rows to process: {iterate_count} (of {len(df)})")

for idx in range(start_index, start_index + iterate_count):
    row = df.iloc[idx]
    nama_pasien = row.get("Nama Pasien", f"Peserta-{idx}")
    tgl_skrining = random_date_in_year(2025,end_month=9)
    umur = str(row.get("UMUR", "25"))

    # determine default BB/TB based on gender
    jk = str(row.get("Jenis Kelamin", "1"))
    if jk == "1":
        default_bb = "55"
        default_tb = "160"
    else:
        default_bb = "65"
        default_tb = "170"
    
    # override if BB/TB not available in data
    bb = row.get("BB")
    tb = row.get("TB")
    if pd.isna(bb):
        bb = default_bb
    if pd.isna(tb) or tb == 0:
        tb = default_tb

    bb = float(bb)
    tb = float(tb)

    payload = {
        "tgl_skrining": tgl_skrining,
        "kegiatan_id": "99",
        "metode_id": "99", #str(random.randint(1,3)),
        "tempat_skrining_id": "3",
        "nama_peserta": nama_pasien,
        "nik": str(row.get("NIK", "1234567890123456")),
        "tgl_lahir": random_date_in_year(current_year - int(umur)),
        "jenis_kelamin_id": jk,
        "alamat_ktp": row.get("Desa", "5474"),
        "berat_badan": str(int(bb)),
        "tinggi_badan": str(int(tb)),
        "imt": str(round(bb / ((tb / 100) ** 2), 1)),
        "hasil_skrining_id": "1",
        "tindak_lanjut_id": "3",
        "keterangan": row.get("CATATAN", "tidak ada catatan"),
        "provinsi_ktp_id": "2",
        "kabupaten_ktp_id": "35",
        "kecamatan_ktp_id": "496",
        "kelurahan_ktp_id": "",
        "status_domisili_id": "1",
        "pekerjaan_id": "16",
        "riwayat_kontak_tb_id": "2",
        "risiko_1_id": "0",
        "risiko_2_id": "0",
        "risiko_3_id": "0",
        "risiko_4_id": "0",
        "risiko_5_id": "0",
        "risiko_6_id": "0",
        "risiko_7_id": "0",
        "risiko_8_id": "0",
        "risiko_10_id": "0",
        "risiko_11_id": "0",
        "gejala_2_1_id": "0",
        "gejala_2_3_id": "0",
        "gejala_2_4_id": "0",
        "gejala_2_5_id": "0",
        "gejala_6_id": "0",
        "hasil_skrining_id": "0",
        "cxr_pemeriksaan_id": "0",
        "cxr_alasan": "belum tersedia fasilitas",
        "jenis_unit_pelaksana_id": "4",
        "warga_negara_id": "1",
        "unit_pelaksana_id": "576",
        "umur_th": umur,
        "umur_bl": "0",
        "no_telp": generate_phone_number(),
        "terduga_tb_id": "0"
    }
    try: 
        r = session.post(target_url, data=payload, verify=False)
        print(f"Row {idx + 1} -> {nama_pasien} | {tgl_skrining} -> Status {r.status_code}")

        # if success, update state
        if r.status_code == 200:
            state["last_row"] = idx + 1
            save_state(STATE_FILE, state)
        else:
            print("Response:", r.text)
            break

        # delay random 0.1 to 1 second
        time.sleep(random.uniform(0.1, 0.5))

        # delay 15 seconds every 1000 rows
        if (idx + 1) % 1000 == 0:
            print("[INFO] Reached", idx + 1, "rows, sleeping for 15 seconds...")
            time.sleep(15)
    except Exception as e:
            print(f"[ERROR] Gagal di baris {idx}: {e}")
            break