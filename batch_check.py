#!/usr/bin/env python3
r"""
Batch Check Pengumuman

Memeriksa status pengumuman untuk multiple entries dari file CSV.

INSTALASI:
==========

WINDOWS:
--------
1. Install Python 3.8+ dari https://www.python.org/downloads/
   - Pilih "Add Python to PATH" saat install
   - Verifikasi: buka Command Prompt, ketik: python --version

2. Buka Command Prompt dan navigasi ke folder project:
   cd C:\path\to\project

3. Install dependencies:
   pip install -r requirements.txt
   (atau install secara manual: pip install requests)

4. Jalankan script:
   python batch_check.py data.csv results.json

LINUX / MAC:
-----------
1. Verifikasi Python 3 sudah terinstall:
   python3 --version

2. Jika belum ada, install:
   Ubuntu/Debian: sudo apt-get install python3 python3-pip
   Fedora: sudo dnf install python3 python3-pip
   macOS: brew install python3

3. Buka Terminal dan navigasi ke folder project:
   cd /path/to/project

4. Install dependencies:
   pip3 install -r requirements.txt
   (atau: pip install -r requirements.txt)

5. Jalankan script:
   python3 batch_check.py data.csv results.json
   (atau: python batch_check.py data.csv results.json)

FILE YANG DIPERLUKAN:
====================
- batch_check.py (script ini)
- check_pengumuman.py (module untuk check)
- requirements.txt (dependencies)
- data.csv (input file dengan format: nomor_pendaftaran,tgl_lahir)

FORMAT INPUT CSV:
=================
nomor_pendaftaran,tgl_lahir
7000000001,15-05-2005
7000000002,20-08-2006
"""
import csv
import json
import sys
import time
import os
from check_pengumuman import check_pengumuman, get_csrf_token_and_cookies

def load_list_from_file(filename):
    """Load nomor_pendaftaran and tgl_lahir from CSV file"""
    entries = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    entries.append({
                        "nomor_pendaftaran": row[0].strip(),
                        "tgl_lahir": row[1].strip(),
                    })
    except FileNotFoundError:
        print(f"✗ File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)

    return entries


def load_checkpoint(output_file):
    """Load existing results from checkpoint file"""
    if output_file and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_checkpoint(output_file, results):
    """Save results to checkpoint file"""
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


def batch_check(input_file, output_file=None, verbose=False):
    """Process multiple entries from input file with resume support"""
    entries = load_list_from_file(input_file)

    if not entries:
        print("✗ No entries found in file")
        return

    # Load existing results if resuming
    results = load_checkpoint(output_file)
    processed_nomors = {r['nomor_pendaftaran'] for r in results}

    remaining_entries = [e for e in entries if e['nomor_pendaftaran'] not in processed_nomors]

    if results:
        print(f"✓ Resuming: {len(results)} entries already processed, {len(remaining_entries)} remaining")
    else:
        print(f"✓ Loaded {len(entries)} entries from '{input_file}'")

    if not remaining_entries:
        print("✓ All entries already processed!")
        print_summary(results, output_file)
        return results

    print(f"Processing {len(remaining_entries)} entries...\n")

    # Fetch CSRF token once at the start
    print("Initializing session...", end=" ", flush=True)
    try:
        csrf_token, cookies = get_csrf_token_and_cookies()
        print("✓\n")
    except Exception as e:
        print(f"✗\n✗ Failed to initialize session: {e}")
        return results

    # Process remaining entries
    already_processed = len(results)
    for i, entry in enumerate(remaining_entries, 1):
        nomor = entry['nomor_pendaftaran']
        print(f"[{already_processed+i}/{len(entries)}] Checking {nomor}...", end=" ", flush=True)

        try:
            result = check_pengumuman(
                nomor,
                entry["tgl_lahir"],
                csrf_token=csrf_token,
                cookies=cookies,
                verbose=False
            )
            results.append(result)

            id_status_diterima = result.get('data', {}).get('id_status_diterima')
            if id_status_diterima == 1:
                status_text = "DITERIMA ✓"
            elif result.get('success'):
                status_text = f"Status: {id_status_diterima}"
            else:
                status_text = f"FAILED: {result.get('status', 'Unknown')}"
            print(status_text)
        except Exception as e:
            results.append({
                "nomor_pendaftaran": nomor,
                "tgl_lahir": entry["tgl_lahir"],
                "status": "ERROR",
                "success": False,
                "error": str(e)[:200],
            })
            print(f"ERROR: {str(e)[:50]}")

        # Save checkpoint every 5 entries
        if i % 5 == 0:
            save_checkpoint(output_file, results)
            print(f"  (checkpoint saved)\n")

        time.sleep(1)  # Delay to avoid rate limiting

    # Final save
    print_summary(results, output_file)
    save_checkpoint(output_file, results)
    return results


def print_summary(results, output_file):
    """Print summary of results"""
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(results)} entries processed")
    success_count = sum(1 for r in results if r.get('success'))
    diterima_count = sum(1 for r in results if (r.get('data') or {}).get('id_status_diterima') == 1)
    print(f"✓ Success: {success_count}")
    print(f"✓ DITERIMA: {diterima_count}")
    print(f"✗ Failed: {len(results) - success_count}")
    print(f"{'='*60}\n")

    if output_file:
        print(f"✓ Results saved to '{output_file}'")
    else:
        print("Results:")
        for result in results:
            nomor = result['nomor_pendaftaran']
            data = result.get('data') or {}
            id_status_diterima = data.get('id_status_diterima')
            if id_status_diterima == 1:
                status_str = "✓ DITERIMA"
            elif result.get('success'):
                status_str = f"✓ Status: {id_status_diterima}"
            else:
                status_str = "✗ FAILED"
            print(f"  {status_str} {nomor}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_check.py <input_file.txt> [output_file.json]")
        print("\nExample:")
        print("  python batch_check.py data.txt results.json")
        print("\nInput file format (CSV):")
        print("  0000000000,00-00-0000")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    batch_check(input_file, output_file)
