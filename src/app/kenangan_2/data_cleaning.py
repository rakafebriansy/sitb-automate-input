import pandas as pd
import re
import json
from datetime import datetime

# ---------- Config ----------
INPUT_FILE = "data/kenangan_2/Daftar Pasien.xlsx"
OUTPUT_FILE = "data/kenangan_2/Daftar Pasien_clean.xlsx"
KELURAHAN_FILE = "data/helper/kelurahan.json"
KECAMATAN_FILE = "data/helper/kecamatan.json"

# ---------- Utils ----------
def to_int(value):
    """Extract digits only from the text (e.g., '45 thn' → 45)."""
    if pd.isna(value):
        return None
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else None

# ---------- Load reference JSON ----------
with open(KECAMATAN_FILE, "r", encoding="utf-8") as f:
    kecamatan_data = json.load(f)

with open(KELURAHAN_FILE, "r", encoding="utf-8") as f:
    kelurahan_data = json.load(f)

# Create mapping dictionaries for faster lookup
kecamatan_map = {item["text"].upper(): item["value"] for item in kecamatan_data if item["value"]}
kelurahan_map = {item["kelurahan_nama"].upper(): item for item in kelurahan_data if item["kelurahan_id"]}

# ---------- Load Excel File ----------
df = pd.read_excel(INPUT_FILE)
print("🧩 Columns detected:", df.columns.tolist())

# ---------- Data Cleaning ----------
df_clean = pd.DataFrame()

# --- Clean NIK ---
df_clean["nik"] = df["NIK"].astype(str).str.strip()

# --- Clean Name (uppercase) ---
df_clean["nama_peserta"] = df["Nama Pasien"].astype(str).str.upper().str.strip()

# --- Clean Age (extract number only) ---
df_clean["umur"] = df["UMUR"].apply(to_int)

# --- Clean Gender ---
# Convert gender text into numeric code (1 = Male, 2 = Female)
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
        "PRIA": "1"
    })
    .replace("NAN", "")
)

# --- Clean Desa (Desa) and map to Kelurahan & Kecamatan IDs ---
df_clean["nama_desa_raw"] = df["Desa"].astype(str).str.strip().str.upper()
df_clean["kelurahan_id"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_map.get(x, {}).get("kelurahan_id"))
df_clean["kecamatan_id"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_map.get(x, {}).get("kecamatan_id"))

# --- Report unmatched desa ---
valid_df = df_clean.dropna(subset=["kelurahan_id", "kecamatan_id"])
not_found = df_clean[df_clean["kelurahan_id"].isna()]["nama_desa_raw"].unique()

if len(not_found) > 0:
    print("⚠️ Desa not found in JSON mapping:", list(not_found))

# ---------- Final Cleaning ----------
# Remove unwanted line breaks or tabs in text columns
for col in valid_df.select_dtypes(include=["object"]).columns:
    valid_df.loc[:, col] = (
        valid_df[col]
        .astype(str)
        .str.replace(r"[\r\n\t]", " ", regex=True)
    )

# ---------- Save Output ----------
valid_df.to_excel(OUTPUT_FILE, index=False)
print(f"✅ Cleaning completed. Output saved to {OUTPUT_FILE}")
print(f"📊 Total valid rows: {len(valid_df)}")
