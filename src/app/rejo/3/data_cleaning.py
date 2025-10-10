import pandas as pd
import re
import json
from datetime import datetime

# ---------- CONFIG ----------
INPUT_FILE = "data/rejo/3/data ht pasien rawat jalan 2025.xlsx"
OUTPUT_FILE = "data/rejo/3/data_ht_clean.xlsx"
KELURAHAN_FILE = "data/helper/kelurahan.json"

# ---------- UTILS ----------
def to_float(value):
    if not value:
        return None
    v = str(value).strip().replace(",", ".")
    v = re.sub(r"[^\d.]", "", v)
    try:
        return float(v)
    except ValueError:
        return None


def extract_values(text):
    if pd.isna(text):
        return {"BB": None, "TB": None}
    text = str(text)
    bb = re.search(r"B\s*B\s*[: ]\s*([\d.,]+)", text, re.IGNORECASE)
    tb = re.search(r"T\s*B\s*[: ]\s*([\d.,]+)", text, re.IGNORECASE)
    return {
        "BB": to_float(bb.group(1) if bb else None),
        "TB": to_float(tb.group(1) if tb else None),
    }

# ---------- LOAD MAPPING ----------
with open(KELURAHAN_FILE, "r", encoding="utf-8") as f:
    kelurahan_data = json.load(f)

kelurahan_mapping = {
    item["kelurahan_nama"].upper().strip(): {
        "kelurahan_id": item["kelurahan_id"],
        "kecamatan_id": item["kecamatan_id"],
    }
    for item in kelurahan_data
}

# ---------- MAIN CLEANING ----------
print(f"📘 Cleaning {INPUT_FILE}")
df = pd.read_excel(INPUT_FILE, header=None)
df.columns = [f"col_{i}" for i in range(1, len(df.columns) + 1)]
df_clean = pd.DataFrame()

# A = umur
df_clean["umur"] = (
    df["col_1"].astype(str).str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
)

# B = nik
df_clean["nik"] = df["col_2"].astype(str).str.strip()

# J = nama_peserta
df_clean["nama_peserta"] = df["col_10"].astype(str).str.upper().str.strip()

# L = jenis_kelamin_id
df_clean["jenis_kelamin_id"] = (
    df["col_12"]
    .astype(str)
    .str.strip()
    .str.upper()
    .replace({
        "L": "1",
        "LAKI": "1",
        "LAKI-LAKI": "1",
        "PRIA": "1",
        "P": "2",
        "PEREMPUAN": "2",
        "WANITA": "2",
    })
)

# M = desa
df_clean["nama_desa_raw"] = df["col_13"].astype(str).str.upper().str.strip()
df_clean["kelurahan_id"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_mapping.get(x, {}).get("kelurahan_id"))
df_clean["kecamatan_id"] = df_clean["nama_desa_raw"].map(lambda x: kelurahan_mapping.get(x, {}).get("kecamatan_id"))

# O = tinggi_badan dan berat_badan
parsed = df["col_15"].apply(extract_values).apply(pd.Series)
df_clean["berat_badan"] = parsed["BB"]
df_clean["tinggi_badan"] = parsed["TB"]

# P = catatan
df_clean["catatan"] = df["col_16"].astype(str).fillna("").str.strip()

# Tgl lahir
current_year = datetime.now().year
df_clean["tgl_lahir"] = df_clean["umur"].apply(
    lambda x: datetime(current_year - int(x), 7, 1).strftime("%Y-%m-%d") if x > 0 else ""
)

# Drop desa invalid
before = len(df_clean)
df_clean = df_clean.dropna(subset=["kelurahan_id"])
after = len(df_clean)
print(f"✅ Valid rows: {after}/{before}")

df_clean.to_excel(OUTPUT_FILE, index=False)
print(f"💾 Saved cleaned data to {OUTPUT_FILE}")
