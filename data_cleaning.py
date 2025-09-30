import pandas as pd
import re
import os
import json
from dotenv import load_dotenv

# ---------- Config ----------
load_dotenv(override=True)
INPUT_FILE = "data/data entri TB .xls"
OUTPUT_FILE = "data/data_clean.xlsx"

# ---------- Utils ----------
def extract_values(text):
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

def to_float(value):
    if not value:
        return None
    v = value.strip().replace(",", ".")
    v = re.sub(r"[^\d.]", "", v)
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None

# ---------- Load Kelurahan/Desa Data ----------
with open("data/kelurahan.json", "r", encoding="utf-8") as f:
    desa_data = json.load(f)

desa_mapping = {
    item["text"].upper().strip(): item["value"]
    for item in desa_data
    if item["value"]
}

# ---------- Load Master Data ----------
df = pd.read_excel(
    INPUT_FILE,
    engine="xlrd",
    converters={"NIK": lambda x: str(x).strip()} # read NIK as string
)

# ---------- Clean 'Hasil Pemeriksaan' Column ----------
df["HASIL PEMERIKSAAN_clean"] = (
    df["HASIL PEMERIKSAAN"]
    .astype(str) #change to string first
    .str.upper() # capitalize
    .str.replace(r"\s+", " ", regex=True) # fix space
    .str.replace(";", ":", regex=False) # fix separator
)
parsed = df["HASIL PEMERIKSAAN_clean"].apply(extract_values).apply(pd.Series)

df_clean = pd.concat([df, parsed], axis=1)

# ---------- Clean 'UMUR' Column ----------
df_clean["UMUR"] = (
    df_clean["UMUR"]
    .astype(str)
    .str.extract(r"(\d+)")
    .astype(float)
    .astype("Int64") # replace back to integer (nullable)
)

# ---------- Clean 'Jenis Kelamin' Column ----------
df_clean["Jenis Kelamin"] = (
    df_clean["Jenis Kelamin"]
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
    .str.title() # replace back to "1" or "2"
)

# ---------- Clean 'Desa' Column ----------
df_clean["Desa"] = (
    df_clean["Desa"]
    .astype(str)
    .str.strip()
    .str.upper()
    .map(desa_mapping) # replace with value code
)

# ---------- Clean 'Nama Pasien' Column ----------
if "Nama Pasien" in df_clean.columns:
    df_clean["Nama Pasien"] = df_clean["Nama Pasien"].astype(str).str.upper()

# ---------- Final Cleaning ----------
# make sure all object columns are string
for col in df_clean.select_dtypes(include=["object"]).columns:
    df_clean[col] = df_clean[col].astype(str)
    # remove leading/trailing whitespace
    df_clean[col] = df_clean[col].str.replace(r"[\r\n\t]", " ", regex=True)
    # fix equal sign
    df_clean[col] = df_clean[col].apply(lambda x: "'"+x if x.strip().startswith("=") else x)
df_clean.to_excel(OUTPUT_FILE, index=False)

print("Cleaning completed. Output saved to", OUTPUT_FILE)
