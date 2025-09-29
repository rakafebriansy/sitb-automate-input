import pandas as pd
import re

df = pd.read_excel("data entri TB .xls", engine="xlrd")

df["HASIL PEMERIKSAAN_clean"] = (
    df["HASIL PEMERIKSAAN"]
    .astype(str) #change to string first
    .str.upper() # capitalize
    .str.replace(r"\s+", " ", regex=True) # fix space
    .str.replace(";", ":", regex=False) # fix separator
)

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


parsed = df["HASIL PEMERIKSAAN_clean"].apply(extract_values).apply(pd.Series)

df_clean = pd.concat([df, parsed], axis=1)

# make sure all object columns are string
for col in df_clean.select_dtypes(include=["object"]).columns:
    df_clean[col] = df_clean[col].astype(str)
    # remove leading/trailing whitespace
    df_clean[col] = df_clean[col].str.replace(r"[\r\n\t]", " ", regex=True)
    # fix equal sign
    df_clean[col] = df_clean[col].apply(lambda x: "'"+x if x.strip().startswith("=") else x)
df_clean.to_excel("data_clean.xlsx", index=False)

print("Cleaning selesai! Hasil tersimpan di data_clean.xlsx")
