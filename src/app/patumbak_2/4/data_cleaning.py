import pandas as pd
import re
from datetime import datetime

# ---------- CONFIG ----------
FILE_NAME = "SMK N 1 Patumbak.xlsx"
DIR = "data/patumbak_2/4/"

# ---------- UTILS ----------
def detect_header_and_read(path, sheet_name, header_start=7, header_end=11):
    """
    Reads a sheet and merges multi-row headers (like row 8-11).
    """
    # Read a wide header range (no actual data yet)
    df_header = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=header_end)
    merged_headers = df_header.iloc[header_start-1:header_end].fillna("")
    # Merge multi-row headers into a single line
    headers = (
        merged_headers.apply(
            lambda col: " ".join([str(x).strip() for x in col if str(x).strip() != ""])
        )
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .tolist()
    )

    # Re-read sheet using computed header row
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_end)
    df.columns = headers[:len(df.columns)]
    return df


# ---------- UTILS ----------
def parse_tgl_lahir(value):
    """
    Parse possible date formats:
    - 'Medan, 12/06/2010'
    - 'DELITUA, 29 MEI 2019'
    - '2018-02-24' or '08/04/2014'
    """
    if pd.isna(value):
        return None

    text = str(value).strip().upper()

    # 🟡 Pattern 1: "PLACE, DD/MM/YYYY" or "DD/MM/YYYY"
    match_slash = re.search(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})", text)
    if match_slash:
        day, month, year = match_slash.groups()
        return f"{year}-{day.zfill(2)}-{month.zfill(2)}"

    # 🟢 Pattern 2: "PLACE, 29 MEI 2019" or "29 MEI 2019"
    match_text = re.search(r"(\d{1,2})\s+([A-Z]+)\s+(\d{4})", text)
    if match_text:
        day, month_text, year = match_text.groups()
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

    # 🔵 Pattern 3: Try standard Excel or ISO date (e.g., 2018-02-24)
    try:
        dt = pd.to_datetime(text, errors="raise")
        return dt.strftime("%Y-%d-%m")
    except Exception:
        return None


def clean_data(df, sheet_name):
    """
    Cleans and normalizes columns according to user rules.
    """

    # Detect columns dynamically
    col_map = {
        "nik": next((c for c in df.columns if "NIK" in str(c).upper()), None),
        "nama_peserta": next((c for c in df.columns if "NAMA" in str(c).upper()), None),
        "tgl_lahir": next((c for c in df.columns if "TEMPAT" in str(c).upper() and "LAHIR" in str(c).upper()), None),
        "no_hp": next((c for c in df.columns if "HP" in str(c).upper()), None),
        "jk_p": next((c for c in df.columns if re.search(r"\bP\b|\bP\*", str(c).upper())), None),
        "jk_l": next((c for c in df.columns if re.search(r"\bL\b", str(c).upper())), None),
    }

    print(f"📄 Sheet: {sheet_name} — Column map detected: {col_map}")

    df_clean = pd.DataFrame()

    # --- Basic columns ---
    df_clean["nik"] = (
        df[col_map["nik"]]
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .str.strip()
        if col_map["nik"] else ""
    )

    df_clean["nama_peserta"] = (
        df[col_map["nama_peserta"]]
        .astype(str)
        .str.strip()
        .str.upper()
        if col_map["nama_peserta"] else ""
    )

    # --- Gender logic ---
    jk_series = pd.Series([""] * len(df))
    if col_map["jk_p"] and col_map["jk_l"]:
        jk_series = df.apply(
            lambda row: "2" if str(row[col_map["jk_p"]]).strip().upper() == "P"
            else ("1" if str(row[col_map["jk_l"]]).strip().upper() == "L" else ""),
            axis=1
        )
    df_clean["jenis_kelamin_id"] = jk_series

    # --- Date of birth ---
    if col_map["tgl_lahir"]:
        df_clean["tgl_lahir"] = df[col_map["tgl_lahir"]].apply(parse_tgl_lahir)
    else:
        df_clean["tgl_lahir"] = ""

    # --- Phone ---
    if col_map["no_hp"]:
        df_clean["no_hp"] = (
            df[col_map["no_hp"]]
            .astype(str)
            .str.replace(r"[^\d+]", "", regex=True)
            .str.strip()
        )
    else:
        df_clean["no_hp"] = ""

    # Remove completely empty rows
    df_clean = df_clean[~(df_clean.eq("").all(axis=1))]

    df_clean["sheet_name"] = sheet_name
    return df_clean


# ---------- MAIN ----------
def main():
    input_file = f"{DIR}{FILE_NAME}"
    output_file = f"{DIR}clean_{FILE_NAME}"
    excel = pd.ExcelFile(input_file)
    all_clean = []

    for sheet in excel.sheet_names:
        print(f"\n📘 Processing sheet: {sheet}")
        try:
            df = detect_header_and_read(input_file, sheet, header_start=8, header_end=11)
        except Exception as e:
            print(f"❌ Failed to read {sheet}: {e}")
            continue

        cleaned = clean_data(df, sheet)
        if cleaned is not None and not cleaned.empty:
            all_clean.append(cleaned)

    if not all_clean:
        print("❌ No data cleaned.")
        return

    df_final = pd.concat(all_clean, ignore_index=True)
    df_final.to_excel(output_file, index=False)
    print(f"\n✅ Cleaning complete. Output saved to: {output_file}")


if __name__ == "__main__":
    main()
