import pandas as pd
from datetime import datetime
import re

# ---------- CONFIG ----------
FILE_NAME = "SD Swasta PAB 22 Patumbak I.xlsx"
DIR = "data/patumbak_2/1/"

# ---------- UTILS ----------
def parse_tgl_lahir(value):
    if pd.isna(value):
        return None

    text = str(value).strip()

    # 1️⃣ Try standard ISO or Excel date (e.g., 2018-02-24, 08/04/2014)
    try:
        dt = pd.to_datetime(text, errors="raise")
        return dt.strftime("%Y-%d-%m")
    except Exception:
        pass

    # 2️⃣ Try pattern like 'DELITUA, 29 MEI 2019' or '29 MEI 2019'
    match = re.search(r"(\d{1,2})\s+([A-Z]+)\s+(\d{4})", text.upper())
    print("Parsing tgl_lahir:", text, "->", match)
    if match:
        day, month_text, year = match.groups()
        month_map = {
            "JAN": "01", "JANUARI": "01",
            "FEB": "02", "FEBRUARI": "02",
            "MAR": "03", "MARET": "03",
            "APR": "04", "APRIL": "04",
            "MEI": "05",
            "JUN": "06", "JUNI": "06",
            "JUL": "07", "JULI": "07",
            "AGS": "08", "AGUSTUS": "08",
            "SEP": "09", "SEPT": "09", "SEPTEMBER": "09",
            "OKT": "10", "OKTOBER": "10",
            "NOV": "11", "NOVEMBER": "11",
            "DES": "12", "DESEMBER": "12"
        }
        month = month_map.get(month_text[:3], "01")
        return f"{year}-{day.zfill(2)}-{month}"

    # 3️⃣ If all fails, return None
    return None


def clean_sheet(df, sheet_name):
    col_map = {
        "nama_peserta": next((c for c in df.columns if "NAMA SISWA" in str(c).upper()), None),
        "jenis_kelamin_id": next((c for c in df.columns if str(c).strip().upper() == "JK"), None),
        "nik": next((c for c in df.columns if "NIK" in str(c).upper()), None),
        "tgl_lahir": df.columns[4] if len(df.columns) > 4 else None,
        "alamat_ktp": next((c for c in df.columns if "ALAMAT" in str(c).upper()), None),
    }

    print(f"📄 Sheet: {sheet_name} — Column mapping: {col_map}")

    if not all([col_map["nama_peserta"], col_map["jenis_kelamin_id"], col_map["nik"], col_map["tgl_lahir"], col_map["alamat_ktp"]]):
        print(f"⚠️ Sheet {sheet_name} dilewati — kolom esensial hilang.")
        return None
    
    df_clean = pd.DataFrame()
    df_clean["nik"] = (
        df[col_map["nik"]]
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .str.strip()
    )
    df_clean["nama_peserta"] = (
        df[col_map["nama_peserta"]]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    df_clean["jenis_kelamin_id"] = (
        df[col_map["jenis_kelamin_id"]]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({
            "P": "2", "PEREMPUAN": "2", "WANITA": "2", "W": "2",
            "L": "1", "LAKI-LAKI": "1", "PRIA": "1"
        })
        .replace({"NAN": "", "NONE": "", "": ""})
    )

    # ✅ Combined date parser (supports both formats)
    df_clean["tgl_lahir"] = df[col_map["tgl_lahir"]].apply(parse_tgl_lahir)

    df_clean["alamat_ktp"] = (
        df[col_map["alamat_ktp"]]
        .astype(str)
        .str.strip()
        .replace({"nan": "", "None": ""})
    )

    # Remove empty rows
    df_clean = df_clean[
        ~(df_clean[["nik", "nama_peserta", "tgl_lahir", "alamat_ktp"]].eq("").all(axis=1))
    ]

    df_clean["sheet_name"] = sheet_name

    return df_clean


def main():
    excel = pd.ExcelFile(f"{DIR}{FILE_NAME}")
    sheet_names = excel.sheet_names
    print("📘 Sheets in file:", sheet_names)

    all_clean = [] 

    for sheet in sheet_names:
        try:
            df = pd.read_excel(f"{DIR}{FILE_NAME}", sheet_name=sheet, header=5)
        except Exception as e:
            print(f"❌ Gagal membaca sheet {sheet}: {e}")
            continue

        cleaned = clean_sheet(df, sheet)
        if cleaned is not None:
            all_clean.append(cleaned)

    if not all_clean:
        raise ValueError("❌ Tidak ada sheet yang berhasil dibersihkan.")

    df_all = pd.concat(all_clean, ignore_index=True)

    output_file = f"{DIR}clean_{FILE_NAME}"
    df_all.to_excel(output_file, index=False)
    print(f"✅ Cleaning completed. Semua sheet digabungkan dan disimpan ke: {output_file}")

if __name__ == "__main__":
    main()
