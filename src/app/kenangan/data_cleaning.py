import pandas as pd
import re
import json
from dotenv import load_dotenv
from datetime import date

# ---------- Config ----------
load_dotenv(override=True)
INPUT_FILE = "data/kenangan/DATA KAK SARI CANTEK.xlsx"
OUTPUT_FILE = "data/kenangan/DATA KAK SARI CANTEK_clean.xlsx"
KELURAHAN_FILE = "data/kenangan/kelurahan.json"

# ---------- Utils ----------
def to_float(value):
    if not value:
        return None
    v = str(value).strip().replace(",", ".")
    v = re.sub(r"[^\d.]", "", v)
    return float(v) if v else None

def estimate_birth_date(age: int):
    if pd.isna(age):
        return None
    try:
        today = date.today()
        birth_year = today.year - int(age)
        return date(birth_year, 7, 1).strftime("%Y-%m-%d")
    except Exception:
        return None

# ---------- Load Kelurahan/Desa Data ----------
with open(KELURAHAN_FILE, "r", encoding="utf-8") as f:
    kelurahan_data = json.load(f)

kelurahan_map = {}
for d in kelurahan_data:
    nama_kel = str(d.get("kelurahan_nama", "")).strip().upper()
    if not nama_kel:
        continue
    kelurahan_map[nama_kel] = {
        "kelurahan_id": d.get("kelurahan_id", ""),
        "kecamatan_id": d.get("kecamatan_id", ""),
        "kecamatan_nama": d.get("kecamatan_nama", "")
    }

# ---------- Load Master Data ----------
df = pd.read_excel(INPUT_FILE)

# ---------- Clean & Normalize ----------
df_clean = pd.DataFrame()

# Nomor urut dan tanggal
df_clean["no"] = df["No."]
df_clean["tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce").dt.strftime("%Y-%m-%d")

# Nama Pasien
df_clean["nama_peserta"] = df["Nama Pasien"].astype(str).str.upper().str.strip()

# Umur
df_clean["umur"] = (
    df["UMUR"]
    .astype(str)
    .str.extract(r"(\d+)")
    .astype(float)
    .astype("Int64")
)

# Jenis Kelamin
df_clean["jenis_kelamin_id"] = (
    df["Jenis Kelamin"]
    .astype(str)
    .str.strip()
    .str.upper()
    .replace({
        "P": "2",
        "PEREMPUAN": "2",
        "WANITA": "2",
        "W": "2",
        "L": "1",
        "LAKI-LAKI": "1",
        "LAKI2": "1",
        "PRIA": "1"
    })
)

# NIK
df_clean["nik"] = df["NIK"].astype(str).str.strip()

# Nomor BPJS
df_clean["no_bpjs"] = df.get("NO. BPJS", "").astype(str).str.strip()

# Desa
df_clean["nama_desa_raw"] = df["Desa"].astype(str).str.strip().str.upper()

# Mapping kelurahan & kecamatan based on reference map
df_clean["kelurahan_id"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_map.get(x, {}).get("kelurahan_id", ""))
df_clean["kecamatan_id"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_map.get(x, {}).get("kecamatan_id", ""))
df_clean["kecamatan_resmi"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_map.get(x, {}).get("kecamatan_nama", ""))

# Display warning for kelurahan not found
not_found = df_clean[df_clean["kelurahan_id"] == ""]["nama_desa_raw"].unique()
if len(not_found) > 0:
    print("Desa not found in JSON:", list(not_found))

# ---------- Final Cleaning ----------
for col in df_clean.select_dtypes(include=["object"]).columns:
    df_clean[col] = df_clean[col].astype(str)
    df_clean[col] = df_clean[col].str.replace(r"[\r\n\t]", " ", regex=True)
    df_clean[col] = df_clean[col].apply(lambda x: "'" + x if x.strip().startswith("=") else x)

# ---------- Save ----------
df_clean.to_excel(OUTPUT_FILE, index=False)
print("Cleaning completed. Output saved to", OUTPUT_FILE)

# Statistik tambahan
total_valid = df_clean["kelurahan_id"].astype(bool).sum()
print(f"Found {total_valid} desa with matching reference from a total of {len(df_clean)} rows.")
