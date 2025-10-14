import pandas as pd

# ---------- CONFIG ----------
FILE_NAME = "SMP PAB 5.xlsx"
DIR = "data/patumbak_2/5/"

# ---------- MAIN ----------
def main():
    df = pd.read_excel(f"{DIR}{FILE_NAME}", header=[4,5])
    print("Columns detected:", df.columns.tolist())

    col_map = {
        "nama_peserta": next((c for c in df.columns if "NAMA" in str(c).upper()), None),
        "tgl_lahir": next((c for c in df.columns if "TANGGAL" in str(c).upper()), None),
        "nik": next((c for c in df.columns if "NIK" in str(c).upper()), None),
    }

    print("Column mapping:", col_map)

    if not all(col_map.values()):
        print("Kolom penting tidak lengkap, periksa kembali header Excel.")
        return

    df_clean = pd.DataFrame()
    df_clean["nama_peserta"] = (
        df[col_map["nama_peserta"]]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_clean["nik"] = (
        df[col_map["nik"]]
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .str.strip()
    )

    df_clean["tgl_lahir"] = pd.to_datetime(
        df[col_map["tgl_lahir"]], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df_clean = df_clean.dropna(subset=["nama_peserta", "tgl_lahir", "nik"], how="all")

    output_file = f"{DIR}clean_{FILE_NAME}"
    df_clean.to_excel(output_file, index=False)
    print(f"✅ Data cleaned and saved to: {output_file}")

if __name__ == "__main__":
    main()
