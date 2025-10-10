import pandas as pd
import re
import json
from datetime import datetime, timedelta

# ---------- CONFIG ----------
INPUT_FILE = "data/rejo/1/lansia.xlsx"
OUTPUT_FILE = "data/rejo/1/lansia_clean.xlsx"
KELURAHAN_FILE = "data/helper/kelurahan.json"

# ---------- UTILS ----------
def to_float(value):
    if not value:
        return None
    v = str(value).strip().replace(",", ".")
    v = re.sub(r"[^\d.]", "", v)
    try:
        return float(v) if v else None
    except ValueError:
        return None


def extract_values(text):
    if pd.isna(text):
        return {"BB": None, "TB": None, "CATATAN": ""}
    
    text = str(text)
    bb = re.search(r"B\s*B\s*[: ]\s*([\d.,]+)", text, re.IGNORECASE)
    tb = re.search(r"T\s*B\s*[: ]\s*([\d.,]+)", text, re.IGNORECASE)

    clean_text = re.sub(
        r"(B\s*B\s*[: ]\s*[\d.,]+\s*(KG)?)|"
        r"(T\s*B\s*[: ]\s*[\d.,]+\s*(CM)?)|",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" ,.-\n\t")

    return {
        "BB": to_float(bb.group(1) if bb else None),
        "TB": to_float(tb.group(1) if tb else None),
        "CATATAN": clean_text,
    }


# ---------- LOAD KELURAHAN MAPPING ----------
with open(KELURAHAN_FILE, "r", encoding="utf-8") as f:
    kelurahan_data = json.load(f)

# Create a mapping dict: KELURAHAN_NAME → {kelurahan_id, kecamatan_id}
kelurahan_mapping = {
    item["kelurahan_nama"].upper().strip(): {
        "kelurahan_id": item["kelurahan_id"],
        "kecamatan_id": item["kecamatan_id"],
    }
    for item in kelurahan_data if item["kelurahan_id"]
}

# ---------- LOAD RAW DATA ----------
df = pd.read_excel(INPUT_FILE)

# ---------- SELECT & CLEAN RELEVANT COLUMNS ----------
df_clean = pd.DataFrame()

# NIK (ID number)
df_clean["nik"] = df["NIK"].astype(str).str.strip()

# Participant name (uppercase)
df_clean["nama_peserta"] = df["Nama Pasien"].astype(str).str.upper().str.strip()

# Age
df_clean["umur"] = (
    df["UMUR"]
    .astype(str)
    .str.extract(r"(\d+)")
    .astype(float)
    .fillna(0)
    .astype(int)
)

# Estimate birth date from current year - age
current_year = datetime.now().year
df_clean["tgl_lahir"] = df_clean["umur"].apply(
    lambda x: datetime(current_year - int(x), 7, 1).strftime("%Y-%m-%d") if x > 0 else ""
)

# Gender → 1 for male, 2 for female
df_clean["jenis_kelamin_id"] = (
    df["Jenis Kelamin"]
    .astype(str)
    .str.strip()
    .str.upper()
    .replace({
        "L": "1",
        "LAKI-LAKI": "1",
        "LAKI": "1",
        "PRIA": "1",
        "P": "2",
        "PEREMPUAN": "2",
        "WANITA": "2"
    })
)

# Date (convert to yyyy-mm-dd)
df_clean["tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce").dt.strftime("%Y-%m-%d")

# Extract weight/height/notes from column "O"
parsed = df["O"].apply(extract_values).apply(pd.Series)
df_clean["berat_badan"] = parsed["BB"]
df_clean["tinggi_badan"] = parsed["TB"]

# Combine notes from column S and parsed CATATAN
df_clean["catatan"] = (
    df["S"].astype(str).fillna("").str.strip() + " | " + parsed["CATATAN"].astype(str)
)

# ---------- MAP DESA TO KELURAHAN & KECAMATAN ----------
df_clean["nama_desa_raw"] = df["Desa"].astype(str).str.upper().str.strip()

# Match Desa name with mapping JSON
df_clean["kelurahan_id"] = df_clean["nama_desa_raw"].map(
    lambda x: kelurahan_mapping.get(x, {}).get("kelurahan_id", None)
)
df_clean["kecamatan_id"] = df_clean["nama_desa_raw"].map(
    lambda x: kelurahan_mapping.get(x, {}).get("kecamatan_id", None)
)

# ---------- FILTER ONLY VALID ROWS ----------
before_count = len(df_clean)
df_clean = df_clean.dropna(subset=["kelurahan_id"])  # Skip rows without valid desa
after_count = len(df_clean)
skipped = before_count - after_count

print(f"🧹 Total rows before cleaning: {before_count}")
print(f"✅ Valid rows with kelurahan match: {after_count}")
print(f"⚠️ Skipped rows (no desa match): {skipped}")

# ---------- FINAL CLEANING ----------
for col in df_clean.select_dtypes(include=["object"]).columns:
    df_clean[col] = df_clean[col].astype(str)
    df_clean[col] = df_clean[col].str.replace(r"[\r\n\t]", " ", regex=True).str.strip()
    df_clean[col] = df_clean[col].apply(
        lambda x: "'" + str(x) if str(x).startswith("=") else str(x)
    )

# ---------- SAVE OUTPUT ----------
df_clean.to_excel(OUTPUT_FILE, index=False)
print(f"\n✅ Cleaning completed successfully!")
print(f"📁 Saved cleaned data to: {OUTPUT_FILE}")
print(f"📊 Final columns: {list(df_clean.columns)}")
