import requests
import pandas as pd
import random
import time
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import os
import json

# ---------- CONFIG ----------
load_dotenv(override=True)
FILE_NAME = "data/rejo/4/dm_clean.xlsx"
STATE_FILE = "data/rejo/4/state.json"
ITERATE = None

# ---------- DATA ----------
df = pd.read_excel(FILE_NAME)
print(f"[INFO] {len(df)} rows loaded")

def random_date_in_year(year=2025, start_month=1, end_month=12, dmy=False):
    start_date = date(year, start_month, 1)
    end_date = date(year, 12, 31) if end_month == 12 else date(year, end_month + 1, 1) - timedelta(days=1)
    result_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    return result_date.strftime("%d-%m-%Y") if dmy else result_date.strftime("%Y-%m-%d")

def load_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {}

def save_state(state_file, state):
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

def generate_phone_number(international=False):
    prefixes = ["0811", "0812", "0813", "0821", "0822", "0823",
                "0852", "0853", "0851", "0856", "0857", "0858",
                "0895", "0896", "0897", "0898", "0899"]
    prefix = random.choice(prefixes)
    number = ''.join(random.choices("0123456789", k=random.randint(6, 8)))
    phone = prefix + number
    return "+62" + phone[1:] if international else phone


# ---------- LOGIN ----------
login_url = os.getenv("LOGIN_URL")
session = requests.Session()
credentials = {"username": os.getenv("USERNAME"), "password": os.getenv("PASSWORD")}
print("[◌] Logging in...")
resp = session.post(login_url, data=credentials, verify=False)
if resp.status_code != 200:
    print("[!] Login failed")
    exit()
print("[✔] Login success")


# ---------- Load State ----------
state = load_state(STATE_FILE)
current_year = datetime.now().year
target_url = os.getenv("TARGET_URL")

# ---------- Load Data ----------
print(f"\n📘 Memproses file: {FILE_NAME}")
df = pd.read_excel(FILE_NAME)

# per file progress
state = load_state(STATE_FILE)
start_index = state["last_row"]
iterate_count = ITERATE + start_index if (ITERATE and ITERATE > 0) else len(df)
print(f"[INFO] Total rows to process: {iterate_count} (of {len(df)})")

# ---------- LOOP ----------
for idx in range(start_index, iterate_count):
    row = df.iloc[idx]

    kecamatan_id = str(row.get("kecamatan_id", None))
    kelurahan_id = str(row.get("kelurahan_id", None))

    if(kecamatan_id == None or kelurahan_id == None):
        break

    nama_peserta = row.get("nama_peserta")
    umur_raw = row.get("umur", None)
    if pd.isna(umur_raw) or str(umur_raw).strip() == "" or umur_raw == 0:
        umur_th = random.randint(10, 50)
    else:
        umur_th = int(float(umur_raw))
    jk = str(row.get("jenis_kelamin_id", "1")).strip()

    # default BB/TB with random ±5 variation
    if jk == "1":
        default_bb = random.randint(50, 60)
        default_tb = random.randint(155, 165)
    else:
        default_bb = random.randint(60, 70)
        default_tb = random.randint(165, 175)


    bb_raw = row.get("berat_badan", None) 
    tb_raw = row.get("tinggi_badan", None)

    if pd.isna(bb_raw) or str(bb_raw).strip() == "" or bb_raw == 0 or bb_raw:
        bb = default_bb
    else:
        bb = int(float(bb_raw))

    if pd.isna(tb_raw) or str(tb_raw).strip() == "" or tb_raw == 0:
        tb = default_tb
    else:
        tb = int(float(tb_raw))

    imt = round(bb / ((tb / 100) ** 2), 1)

    tgl_skrining = random_date_in_year(2025,end_month=8)

    payload = {
        "tgl_skrining": tgl_skrining,
        "kegiatan_id": "99",
        "metode_id": "99",
        "tempat_skrining_id": "3",
        "alamat_ktp": str(row.get("alamat_ktp", "Alamat tidak diketahui")),
        "hasil_skrining_id": "1",
        "tindak_lanjut_id": "3",
        "keterangan": row.get("catatan", "tidak ada catatan"),
        "status_domisili_id": "1",
        "pekerjaan_id": "16",
        "riwayat_kontak_tb_id": "2",
        "status_gizi_id": "3",
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
        "gejala_1_1_id": "0",
        "gejala_1_3_id": "0",
        "gejala_1_4_id": "0",
        "gejala_1_5_id": "0",
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
        "unit_pelaksana_id": "587",
        "umur_th": str(umur_th),
        "umur_bl": "0",
        "no_telp": generate_phone_number(),
        "terduga_tb_id": "0",

        "nama_peserta": nama_peserta,
        "nik": str(row.get("nik")),
        "tgl_lahir": row.get("tgl_lahir") if not pd.isna(row.get("tgl_lahir", None)) else random_date_in_year(current_year - umur_th),
        "jenis_kelamin_id": jk,
        "provinsi_ktp_id": "2",
        "kabupaten_ktp_id": "35",
        "kecamatan_ktp_id": str(kecamatan_id),
        "kelurahan_ktp_id": str(kelurahan_id),
        "berat_badan": str(bb),
        "tinggi_badan": str(tb),
        "imt": imt,
    }

    try:
        r = session.post(target_url, data=payload, verify=False)
        print(f"Row {idx + 1} -> {nama_peserta} | {tgl_skrining} -> Status {r.status_code}")
        print(f"RESPONSE: {print(r.text)}")

        if r.status_code == 200:
            state["last_row"] = idx + 1
            save_state(STATE_FILE, state)
        else:
            print("Response:", r.text)
            break

        # random delay duration
        time.sleep(random.uniform(0.2, 0.7))

        # pause (sleep) for 15 seconds every 1000 rows
        if (idx + 1) % 1000 == 0:
            print("[INFO] Reached", idx + 1, "rows, sleeping for 15 seconds...")
            time.sleep(15)

    except Exception as e:
        print(f"[ERROR] Gagal di baris {idx + 1}: {e}")
        break

print("\n✅ All records submitted successfully.")
