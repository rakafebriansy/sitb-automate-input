from dotenv import load_dotenv
import os
import requests

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

# 3. send data
target_url = os.getenv("TARGET_URL")

payload = {
    "tgl_skrining": "2025-09-28",
    "kegiatan_id": "1",
    "metode_id": "2",
    "tempat_skrining_id": "3",
    "nama_peserta": "Contoh Peserta 2",
    "nik": "1234567890123456",
    "tgl_lahir": "2001-02-01",
    "jenis_kelamin_id": "1",
    "alamat_ktp": "Jl. Melati No. 123",
    "berat_badan": "63",
    "tinggi_badan": "175",
    "imt": "440.92",
    "hasil_skrining_id": "1",
    "tindak_lanjut_id": "3",
    "keterangan": "Pasien dummy testing",
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
    "umur_th": "24",
    "umur_bl": "7",
    "no_telp": "081234567890",
    "terduga_tb_id": "2"
}

r = session.post(target_url, data=payload, verify=False)

print("Data sent: ", payload != None)
print("Status:", r.status_code)
print("Response:", r.text)
