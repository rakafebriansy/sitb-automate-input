import pandas as pd
import json
import re
from datetime import datetime

# ---------- Config ----------
INPUT_FILE = "data/hamper/Data Verifikasi Usulan PBI September.xlsx"
KECAMATAN_FILE = "data/helper/kecamatan.json"
KELURAHAN_FILE = "data/helper/kelurahan.json"
OUTPUT_FILE = "data/hamper/Data_Verifikasi_clean.xlsx"

# ---------- Load JSON ----------
with open(KECAMATAN_FILE, "r", encoding="utf-8") as f:
    kecamatan_data = json.load(f)

with open(KELURAHAN_FILE, "r", encoding="utf-8") as f:
    kelurahan_data = json.load(f)

# ---------- Mapping dict ----------
kecamatan_map = {item["text"].strip().upper(): item["value"] for item in kecamatan_data if item["value"]}
kelurahan_map = {item["kelurahan_nama"].strip().upper(): item["kelurahan_id"] for item in kelurahan_data if item["kelurahan_id"]}

# ---------- Read Excel properly ----------
df_raw = pd.read_excel(INPUT_FILE, header=3)  # header row = index 3
df_raw = df_raw.dropna(how="all")  # drop empty rows
df_raw.columns = [str(c).strip() for c in df_raw.columns]  # clean column names

print("🧩 Columns detected:", df_raw.columns.tolist())

# ---------- Extract columns ----------
df_clean = pd.DataFrame()
df_clean["nik"] = df_raw.iloc[:, 5].astype(str).str.strip()  # Column F
df_clean["nama_peserta"] = df_raw.iloc[:, 7].astype(str).str.upper().str.strip()  # Column H
df_clean["tgl_lahir"] = pd.to_datetime(df_raw.iloc[:, 10], errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")  # Column K
df_clean["jenis_kelamin_id"] = df_raw.iloc[:, 11].astype(str).str.strip().replace({"1": "1", "L": "1", "LAKI-LAKI": "1", "2": "2", "P": "2", "PEREMPUAN": "2"})
df_clean["alamat_ktp"] = df_raw.iloc[:, 13].astype(str).str.strip()  # Column N

# Kecamatan & Desa mapping
df_clean["nama_kecamatan_raw"] = df_raw.iloc[:, 14].astype(str).str.strip().str.upper()
df_clean["nama_desa_raw"] = df_raw.iloc[:, 15].astype(str).str.strip().str.upper()

df_clean["kecamatan_id"] = df_clean["nama_kecamatan_raw"].map(kecamatan_map)
df_clean["kelurahan_id"] = df_clean["nama_desa_raw"].map(kelurahan_map)

# Skip rows without mapped kelurahan
df_clean = df_clean[df_clean["kelurahan_id"].notna()]

# ---------- Clean text ----------
for col in df_clean.select_dtypes(include=["object"]).columns:
    df_clean[col] = df_clean[col].replace(r"[\r\n\t]", " ", regex=True).str.strip()

# ---------- Save ----------
df_clean.to_excel(OUTPUT_FILE, index=False)
print(f"✅ Cleaning complete. Output saved to {OUTPUT_FILE}")
print("✅ Rows:", len(df_clean))
