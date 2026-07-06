import json
import openpyxl

with open("results.json", encoding="utf-8") as f:
    results = json.load(f)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Hasil"

headers = ["nomor_pendaftaran", "nama_lengkap", "nama_prodi", "id_status_diterima", "asal_sekolah"]
ws.append(headers)

for item in results:
    data = item.get("data")
    if not data:
        continue
    ws.append([data.get(h) for h in headers])

wb.save("hasil_pendaftaran.xlsx")
print("done")
