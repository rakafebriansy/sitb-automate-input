import pandas as pd
import re
import json
import os
from datetime import datetime

# ---------- Config ----------
INPUT_DIR = "data/mulyorejo"
OUTPUT_DIR = "data/mulyorejo"
KELURAHAN_FILE = "data/mulyorejo/kelurahan.json"

# ---------- Utils ----------
def to_float(value):
    if not value:
        return None
    v = str(value).strip().replace(",", ".")
    v = re.sub(r"[^\d.]", "", v)
    return float(v) if v else None

def extract_values(text):
    if pd.isna(text):
        return {"BB": None, "TB": None, "CATATAN": ""}
    text = str(text)
    bb = re.search(r"B\s*B\s*[: ]\s*([\d.,]+)", text, re.IGNORECASE)
    tb = re.search(r"T\s*B\s*[: ]\s*([\d.,]+)", text, re.IGNORECASE)
    clean_text = re.sub(
        r"(B\s*B\s*[: ]\s*[\d.,]+\s*(KG)?)|"
        r"(T\s*B\s*[: ]\s*[\d.,]+\s*(CM)?)",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" ,.-\n\t")
    return {"BB": to_float(bb.group(1) if bb else None),
            "TB": to_float(tb.group(1) if tb else None),
            "CATATAN": clean_text}

today = datetime.today()

def hitung_umur_lengkap(tgl):
    if pd.isna(tgl):
        return pd.Series({"umur_th": 0, "umur_bl": 0})
    try:
        tgl_lahir = pd.to_datetime(tgl, errors="coerce")
        if pd.isna(tgl_lahir):
            return pd.Series({"umur_th": 0, "umur_bl": 0})

        years = today.year - tgl_lahir.year
        months = today.month - tgl_lahir.month

        # Fix if day passed
        if today.day < tgl_lahir.day:
            months -= 1

        # Fix if month is negative
        if months < 0:
            years -= 1
            months += 12

        return pd.Series({"umur_th": years, "umur_bl": months})
    except:
        return pd.Series({"umur_th": 0, "umur_bl": 0})

def find_col(df, keyword):
    """Cari kolom berdasarkan kata kunci (case-insensitive)."""
    matches = [c for c in df.columns if keyword.lower() in c.lower()]
    if not matches:
        raise KeyError(f"Kolom dengan kata kunci '{keyword}' tidak ditemukan di Excel.")
    return matches[0]

# ---------- Load kelurahan mapping ----------
with open(KELURAHAN_FILE, "r", encoding="utf-8") as f:
    desa_data = json.load(f)

desa_mapping = {
    item["text"].lower().strip(): item["value"]
    for item in desa_data if item["value"]
}

# ---------- Loop all DATA 4–11 files ----------
for i in range(4, 12):
    input_file = os.path.join(INPUT_DIR, f"DATA {i}.xlsx")
    output_file = os.path.join(OUTPUT_DIR, f"DATA {i}_clean.xlsx")

    if not os.path.exists(input_file):
        print(f"⚠️ File tidak ditemukan: {input_file}, dilewati.")
        continue

    print(f"\n🔹 Memproses: {input_file}")

    # ---------- Load Excel (2 header rows) ----------
    df = pd.read_excel(input_file, header=[0, 1])

    # Get all column names, remove ones that contain 'Unnamed', and join into a clean string
    df.columns = [
        " ".join([str(c1), str(c2)]).strip()
        for c1, c2 in df.columns
    ]
    df.columns = [re.sub(r"Unnamed.*", "", c).strip() for c in df.columns]

    # print("  Kolom Excel:", df.columns.tolist())

    # ---------- Clean and map ----------
    df_clean = pd.DataFrame()

    col_nik = find_col(df, "NIK/KITAS/KITAP")
    col_nama = find_col(df, "Nama Lengkap")
    col_tgl = find_col(df, "dd/mm/yyyy")
    col_jk = find_col(df, "Jenis Kelamin")
    col_alamat = find_col(df, "Alamat Tempat Tinggal")
    col_kec = find_col(df, "Nama Kecamatan")
    col_desa = find_col(df, "Nama Desa")

    df_clean["nik"] = df[col_nik].astype(str).str.strip()
    df_clean["nama_peserta"] = df[col_nama].astype(str).str.upper().str.strip()
    df_clean["tgl_lahir"] = pd.to_datetime(df[col_tgl], dayfirst= True, errors="coerce").dt.strftime("%Y-%m-%d")

    df_clean[["umur_th", "umur_bl"]] = df_clean["tgl_lahir"].apply(hitung_umur_lengkap)

    df_clean["jenis_kelamin_id"] = (
        df[col_jk]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({
            "L": "1", "LAKI-LAKI": "1", "LAKI2": "1", "PRIA": "1",
            "P": "2", "PEREMPUAN": "2", "WANITA": "2", "W": "2"
        })
    )

    df_clean["alamat_ktp"] = df[col_alamat].astype(str).str.strip()
    df_clean["nama_kecamatan"] = df[col_kec].astype(str).str.upper().str.strip()

    # ---------- Normalization and Desa Mapping ----------
    df_clean["nama_desa_raw"] = (
        df[col_desa]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({
            "mulio rejo": "mulyorejo",
            "mulyo rejo": "mulyorejo",
            "lalang": "kampung lalang",
        })
    )
    df_clean["nama_desa"] = df_clean["nama_desa_raw"].map(desa_mapping)

    not_found = df_clean[df_clean["nama_desa"].isna()]["nama_desa_raw"].unique()
    if len(not_found) > 0:
        print("  ⚠️ Desa tidak ditemukan dalam JSON:", list(not_found))

    # optional BB/TB extract
    if "HASIL PEMERIKSAAN" in df.columns:
        parsed = df["HASIL PEMERIKSAAN"].astype(str).apply(extract_values).apply(pd.Series)
        df_clean = pd.concat([df_clean, parsed], axis=1)

    # final cleaning
    for col in df_clean.select_dtypes(include=["object"]).columns:
        df_clean[col] = df_clean[col].astype(str).str.replace(r"[\r\n\t]", " ", regex=True)
        df_clean[col] = df_clean[col].apply(lambda x: "'" + x if x.strip().startswith("=") else x)

    # save
    df_clean.to_excel(output_file, index=False)
    print(f"  ✅ Cleaning selesai: {output_file}")
