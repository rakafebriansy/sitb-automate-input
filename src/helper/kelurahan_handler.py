import requests
import json
import time
import urllib3

# ---------- Config ----------
INPUT_JSON = "data/helper/kecamatan.json"
OUTPUT_JSON = "data/helper/kelurahan.json"
BASE_URL = "https://sulawesi.sitb.id/sitb2024/ref/Kelurahan/LookupData"

# ---------- Nonaktifkan SSL Warning ----------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- Load Kecamatan Data ----------
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    kecamatan_list = json.load(f)

# ---------- Hasil akhir ----------
all_kelurahan = []

# ---------- Loop setiap kecamatan ----------
for item in kecamatan_list:
    kec_id = item.get("value")
    kec_nama = item.get("text")

    if not kec_id or not kec_nama:
        continue

    # Payload x-www-form-urlencoded
    payload = {
        "item[value]": "id",
        "item[text]": "nama",
        "parent[kecamatan_id]": kec_id,
        "order[nama]": ""
    }

    print(f"🔹 Fetching Kelurahan untuk Kecamatan: {kec_nama} (ID={kec_id})")

    try:
        # Kirim POST request dengan form data
        resp = requests.post(
            BASE_URL,
            data=payload,
            timeout=10,
            verify=False,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        resp.raise_for_status()

        data = resp.json() if resp.text.strip().startswith("[") else []
        if not isinstance(data, list):
            print(f"⚠️ Data tidak valid untuk {kec_nama}: {resp.text[:100]}")
            continue

        for d in data:
            all_kelurahan.append({
                "kecamatan_id": kec_id,
                "kecamatan_nama": kec_nama,
                "kelurahan_id": d.get("value"),
                "kelurahan_nama": d.get("text")
            })

        print(f"✅ {len(data)} kelurahan ditemukan di {kec_nama}")
        time.sleep(0.5)

    except Exception as e:
        print(f"❌ Error pada {kec_nama}: {e}")

# ---------- Simpan hasil ----------
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(all_kelurahan, f, indent=2, ensure_ascii=False)

print(f"\n🎉 Done! Total kelurahan berhasil diambil: {len(all_kelurahan)}")
print(f"📁 Data disimpan di: {OUTPUT_JSON}")
