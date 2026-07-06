# Batch Check Pengumuman Guide

## Instalasi

### Requirements
- Python 3.8+
- Chrome/Chromium browser (untuk Selenium)

### Langkah Instalasi

#### 1. Clone atau download project
```bash
cd /path/to/project
```

#### 2. Install dependencies menggunakan requirements.txt
```bash
# Menggunakan pip
pip install -r requirements.txt

# Atau jika menggunakan virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# atau: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 3. Verifikasi instalasi
```bash
python -c "import selenium, requests, certifi; print('All packages installed!')"
```

#### Dependencies yang terinstall:
- **selenium** (>=4.0.0) - Web automation untuk extract CSRF token
- **requests** (>=2.31.0) - HTTP requests library
- **certifi** (>=2024.0.0) - SSL certificate bundle

## Deskripsi
Script untuk batch checking pengumuman dari daftar nomor registrasi dan tanggal lahir dari file.txt

## Files

1. **check_pengumuman.py** - Script utama (sudah di-refactor)
   - `get_csrf_token_and_cookies()` - Extract CSRF token & cookies
   - `check_pengumuman(nomor, tgl_lahir)` - Check single entry

2. **batch_check.py** - Wrapper untuk batch processing
   - `load_list_from_file(filename)` - Baca dari CSV
   - `batch_check(input_file, output_file)` - Process batch

3. **data.txt** - Contoh input file

## Format Input File (CSV)

File harus berisi 2 kolom terpisah koma:
```
nomor_pendaftaran,tgl_lahir
7261101095,01-03-2008
```

**Catatan:** Tanggal format DD-MM-YYYY

## Cara Penggunaan

### 1. Siapkan data.txt dengan format yang benar
```
7261101094,28-02-2008
```

### 2. Jalankan batch check
```bash
python batch_check.py data.txt
```

Output di console:
```
✓ Loaded 2 entries from 'data.txt'
Processing...

[1/2] Checking 0000000000... Status: 200

============================================================
SUMMARY: 2 entries processed
✓ Success: 2
✗ Failed: 0
============================================================
```

### 3. Simpan hasil ke file JSON (optional)
```bash
python batch_check.py data.txt results.json
```

Akan generate `results.json` dengan format:
```json
[
  {
    "nomor_pendaftaran": "70202020",
    "tgl_lahir": "01-01-2008",
    "status": 200,
    "success": true,
    "data": { ... }
  },
  ...
]
```

## Output Format

Setiap entry di hasil memiliki:
- `nomor_pendaftaran` - Nomor registrasi
- `tgl_lahir` - Tanggal lahir
- `status` - HTTP status code atau ERROR
- `success` - Boolean (true/false)
- `data` - Data lengkap dari API (jika success)
- `error` - Pesan error (jika gagal)

## Contoh Penggunaan

```bash
# Hanya display di console
python batch_check.py data.txt

# Save ke file JSON
python batch_check.py data.txt hasil_check.json

# Gunakan output JSON untuk proses lanjutan
cat hasil_check.json | jq '.[] | select(.success==true)'
```

## Troubleshooting

### "File not found"
- Pastikan `data.txt` ada di folder yang sama
- Cek nama file dengan `ls -la data.txt`

### "Only 1 column found"
- Format harus CSV dengan koma: `nomor,tanggal`
- Jangan pakai space: `nomor, tanggal` ❌
- Harus: `nomor,tanggal` ✓

### Timeout/Error saat request
- Script pakai delay 1 detik antar request untuk avoid rate limiting
- Kalau tetap error, cek koneksi internet atau status website

### CSRF token error
- Browser Selenium perlu Chrome/Chromium installed
- Cek: `which chromedriver` atau `which google-chrome`
