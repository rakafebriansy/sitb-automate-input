import pandas as pd
import re
import json
from datetime import datetime

# ---------- CONFIG ----------
INPUT_FILE = "data/rejo/6/DATA SKRINING MEDAN ESTATE.xlsx"
OUTPUT_FILE = "data/rejo/6/DATA SKRINING MEDAN ESTATE_clean.xlsx"

# ---------- UTILS ----------
def parse_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return datetime.strptime(str(value).strip(), "%d/%m/%Y").date()
    except ValueError:
        # Try Excel auto-format (e.g., 1975-08-21)
        try:
            return pd.to_datetime(value, errors="coerce").date()
        except Exception:
            return None

def calculate_age(birth_date):
    if not birth_date:
        return None, None
    today = datetime.now().date()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    # Adjust negative months/days
    if days < 0:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    return years, months

# ---------- LOAD DATA ----------
df_raw = pd.read_excel(INPUT_FILE, header=None)

# Only pick the needed columns (B, D, G)
# Column indexes in pandas are 0-based, so:
# B → 1, D → 3, G → 6
df = df_raw.iloc[:, [1, 3, 6]].copy()
df.columns = ["nik", "nama_peserta", "tgl_lahir_raw"]

# ---------- MAIN CLEANING ----------
print(f"📘 Cleaning {INPUT_FILE}")

# Normalize NIK
df["nik"] = (
    df["nik"]
    .astype(str)
    .str.replace(r"[^\d]", "", regex=True)
    .str.strip()
)

# Normalize Name
df["nama_peserta"] = (
    df["nama_peserta"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Parse Date of Birth
df["tgl_lahir"] = df["tgl_lahir_raw"].apply(parse_date)

# Calculate Age
df[["umur_th", "umur_bl"]] = df["tgl_lahir"].apply(
    lambda x: pd.Series(calculate_age(x))
)

# ---------- FINAL CLEAN ----------
df_final = df[["nik", "nama_peserta", "tgl_lahir", "umur_th", "umur_bl"]]
df_final["tgl_lahir"] = df_final["tgl_lahir"].apply(
    lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
)

# ---------- SAVE ----------
df_final.to_excel(OUTPUT_FILE, index=False)
print(f"✅ Cleaning completed. Saved to: {OUTPUT_FILE}")