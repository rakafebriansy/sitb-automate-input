from dotenv import load_dotenv
from datetime import date, timedelta
import os
import pandas as pd
import random
import requests
import time

def random_date_in_year(year=2025, dmy=False):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
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

# 1. load file .env
load_dotenv(override=True)

# 2. login
session = requests.Session()
login_url = os.getenv("LOGIN_URL")

credentials = {
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD")
}

print("Logging in with:", credentials)

resp = session.post(login_url, data=credentials, verify=False)
print("Login response:", resp.text)
print("Cookies after login:", session.cookies.get_dict())

# 3. kirim data
df = pd.read_excel("data_clean.xlsx")
target_url = os.getenv("TARGET_URL")

for idx, row in df.iterrows():
    payload = {
        "tgl_skrining": random_date_in_year(2025),
        "kegiatan_id": "1",
        "metode_id": "2",
        "tempat_skrining_id": "3",
        "nama_peserta": row.get("NAMA", f"Peserta-{idx}"),
        "nik": str(row.get("NIK", "1234567890123456")),
        "tgl_lahir": random_date(1980, 2010),
        "jenis_kelamin_id": str(row.get("JK", "1")),
        "alamat_ktp": row.get("ALAMAT", "Jl. Dummy"),
        "berat_badan": str(row.get("BB", "60")),
        "tinggi_badan": str(row.get("TB", "170")),
        "imt": str(row.get("IMT", "22.5")),
        "hasil_skrining_id": "1",
        "tindak_lanjut_id": "3",
        "keterangan": row.get("HASIL PEMERIKSAAN", "hasil clean"),
        "provinsi_ktp_id": "2",
        "kabupaten_ktp_id": "35",
        "kecamatan_ktp_id": "496",
        "kelurahan_ktp_id": "5474",
        "status_domisili_id": "1",
        "pekerjaan_id": "5",
        "riwayat_kontak_tb_id": "2",
        "risiko_1_id": "1",
        "risiko_2_id": "1",
        "risiko_3_id": "1",
        "risiko_4_id": "1",
        "risiko_5_id": "2",
        "risiko_6_id": "2",
        "risiko_7_id": "2",
        "risiko_8_id": "1",
        "risiko_10_id": "1",
        "risiko_11_id": "1",
        "gejala_2_1_id": "1",
        "gejala_2_3_id": "1",
        "gejala_2_4_id": "1",
        "gejala_2_5_id": "1",
        "gejala_6_id": "1",
        "cxr_pemeriksaan_id": "1",
        "cxr_alasan": "belum tersedia fasilitas",
        "jenis_unit_pelaksana_id": "4",
        "warga_negara_id": "1",
        "unit_pelaksana_id": "576",
        "umur_th": str(row.get("UMUR_TH", "25")),
        "umur_bl": str(row.get("UMUR_BL", "6")),
        "no_telp": str(row.get("NO_TELP", "081234567890")),
        "terduga_tb_id": "2"
    }

    r = session.post(target_url, data=payload, verify=False)
    print(f"Row {idx} -> Status {r.status_code}")

    # delay antar request (acak biar natural)
    time.sleep(random.uniform(0.5, 2.0))

    # delay tambahan tiap 1000 data
    if (idx + 1) % 1000 == 0:
        print("Pause sejenak 30 detik agar server tidak overload...")
        time.sleep(30)

    if r.status_code != 200:
        print("Response:", r.text)
        break
