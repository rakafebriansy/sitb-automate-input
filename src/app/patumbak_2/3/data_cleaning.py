import pandas as pd
from datetime import datetime
import re
import random

# ---------- CONFIG ----------
FILE_NAME = "SDN 105299 MARINDAL I.xlsx"
DIR = "data/patumbak_2/3/"

# ---------- UTILS ----------
def read_sheet_with_auto_header(path, sheet_name, scan_rows=12, keywords=None):
    """
    Read an Excel sheet and try to auto-detect which row is the header.
    - path: file path
    - sheet_name: name of the sheet
    - scan_rows: how many top rows to scan for header keywords
    - keywords: list of strings to look for in a candidate header row
    Returns: DataFrame read with the detected header (or None if cannot read)
    """
    if keywords is None:
        keywords = ["NAMA", "NIK", "TANGGAL", "ALAMAT", "JK", "NAMA SISWA"]

    # Step 1: read top `scan_rows` rows without header
    try:
        preview = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=scan_rows)
    except Exception as e:
        print(f"❌ Failed to preview sheet {sheet_name}: {e}")
        return None

    # Step 2: find the first row index that contains ANY keyword
    header_row = None
    for i in range(len(preview)):
        row_values = " ".join(
            [str(x).upper() if pd.notna(x) else "" for x in preview.iloc[i].values]
        )
        for kw in keywords:
            if kw.upper() in row_values:
                header_row = i
                break
        if header_row is not None:
            break

    # Step 3: if found, read sheet using that header; otherwise fallback to header=5
    if header_row is not None:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
            print(f"ℹ️ Sheet '{sheet_name}': header detected at row index {header_row} (1-based {header_row+1})")
            return df
        except Exception as e:
            print(f"⚠️ Failed to read sheet {sheet_name} with header={header_row}: {e}")
            # fallthrough to fallback
    else:
        print(f"⚠️ No header row detected in top {scan_rows} rows of sheet '{sheet_name}'. Falling back to header=5")

    # Fallback: try header=5 (original assumption)
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=5)
        print(f"ℹ️ Sheet '{sheet_name}': read with fallback header=5")
        return df
    except Exception as e:
        print(f"❌ Failed to read sheet {sheet_name} with fallback header=5: {e}")
        return None

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
        "tgl_lahir": next((c for c in df.columns if "TANGGAL" in str(c).upper()), None),
        "alamat_ktp": next((c for c in df.columns if "ALAMAT" in str(c).upper()), None),
    }

    print(f"📄 Sheet: {sheet_name} — Column mapping: {col_map}")

    if not all([col_map["nama_peserta"], col_map["nik"], col_map["tgl_lahir"], col_map["alamat_ktp"]]):
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
    if col_map["jenis_kelamin_id"] and col_map["jenis_kelamin_id"] in df.columns:
        df_clean["jenis_kelamin_id"] = (
            df[col_map["jenis_kelamin_id"]]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "P": "2", "PEREMPUAN": "2", "WANITA": "2", "W": "2",
                "L": "1", "LAKI-LAKI": "1", "LAKI - LAKI": "1", "PRIA": "1"
            })
            .replace({"NAN": "", "NONE": "", "": str(random.randint(1,2))})
        )
    else:
        df_clean["jenis_kelamin_id"] = str(random.randint(1,2))

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
    excel_path = f"{DIR}{FILE_NAME}"
    excel = pd.ExcelFile(excel_path)
    sheet_names = excel.sheet_names
    print("📘 Sheets in file:", sheet_names)

    all_clean = [] 

    for sheet in sheet_names:
        try:
            df = read_sheet_with_auto_header(excel_path, sheet_name=sheet, scan_rows=12)
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
