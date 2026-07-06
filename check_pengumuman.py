import certifi
import requests
import re
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

base_url = "https://admission.its.ac.id"
pengumuman_page = f"{base_url}/pengumuman/smits-ace/2"
api_url = f"{base_url}/pengumuman/get-pengumuman"

ca_bundle = os.path.join(os.path.dirname(__file__), "combined_ca.pem")


def get_csrf_token_and_cookies():
    """Extract CSRF token and cookies from browser"""
    headers = {
        "Accept": "*/*",
        "Accept-Language": "id,en-US;q=0.9,en;q=0.8,ar;q=0.7",
        "Origin": base_url,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        ),
    }

    cookies = {
        "_pk_id.11.ea51": "33613ff0041be4ec.1778853260.",
        "_pk_ses.11.ea51": "1",
    }

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(pengumuman_page)
        time.sleep(3)

        page_source = driver.page_source

        # Try different patterns to find token
        token_match = re.search(r'name="_token"\s+value="([^"]+)"', page_source)
        if not token_match:
            token_match = re.search(r'content="([^"]+)"\s+name="csrf-token"', page_source)
        if not token_match:
            token_match = re.search(r'"_token"\s*:\s*"([^"]+)"', page_source)
        if not token_match:
            token_match = re.search(r"formData\.append\('_token',\s*'([^']+)'", page_source)
        if not token_match:
            token_match = re.search(r"_token.*?['\"]([a-zA-Z0-9/+]+={0,2})['\"]", page_source)

        csrf_token = token_match.group(1) if token_match else "UNKNOWN"

        # Get cookies from Selenium
        selenium_cookies = driver.get_cookies()
        for cookie in selenium_cookies:
            cookies[cookie['name']] = cookie['value']

        if csrf_token != "UNKNOWN":
            cookies["XSRF-TOKEN"] = csrf_token

        return csrf_token, cookies

    finally:
        driver.quit()


def check_pengumuman(nomor_pendaftaran, tgl_lahir, csrf_token=None, cookies=None, verbose=False):
    """Check pengumuman status for given registration number and birth date.
    Pass csrf_token and cookies to reuse across multiple requests."""
    try:
        if csrf_token is None or cookies is None:
            csrf_token, cookies = get_csrf_token_and_cookies()

        headers = {
            "Accept": "*/*",
            "Accept-Language": "id,en-US;q=0.9,en;q=0.8,ar;q=0.7",
            "Origin": base_url,
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
            ),
            "Referer": pengumuman_page,
            "X-CSRF-TOKEN": cookies.get("XSRF-TOKEN", csrf_token),
            "X-Requested-With": "XMLHttpRequest",
        }

        data = {
            "nomor_pendaftaran": nomor_pendaftaran,
            "tgl_lahir": tgl_lahir,
            "jalur_masuk": "smits-ace",
        }

        session = requests.Session()
        resp = session.post(api_url, headers=headers, cookies=cookies, data=data, verify=ca_bundle, timeout=30)

        if verbose:
            print(f"\n[{nomor_pendaftaran}] Status: {resp.status_code}")

        try:
            json_data = resp.json()
            if verbose:
                print(json.dumps(json_data, indent=2))
            return {
                "nomor_pendaftaran": nomor_pendaftaran,
                "tgl_lahir": tgl_lahir,
                "status": resp.status_code,
                "success": json_data.get('result', False),
                "data": json_data.get('data', {}),
            }
        except json.JSONDecodeError:
            return {
                "nomor_pendaftaran": nomor_pendaftaran,
                "tgl_lahir": tgl_lahir,
                "status": resp.status_code,
                "success": False,
                "error": resp.text[:500],
            }

    except requests.Timeout:
        return {
            "nomor_pendaftaran": nomor_pendaftaran,
            "tgl_lahir": tgl_lahir,
            "status": "TIMEOUT",
            "success": False,
            "error": "Request timeout",
        }
    except requests.RequestException as e:
        return {
            "nomor_pendaftaran": nomor_pendaftaran,
            "tgl_lahir": tgl_lahir,
            "status": "ERROR",
            "success": False,
            "error": f"Request failed: {str(e)[:200]}",
        }
    except Exception as e:
        return {
            "nomor_pendaftaran": nomor_pendaftaran,
            "tgl_lahir": tgl_lahir,
            "status": "ERROR",
            "success": False,
            "error": str(e)[:200],
        }


if __name__ == "__main__":
    # Single check mode
    nomor_pendaftaran = "0000000000"
    tgl_lahir = "00-00-0000"

    print("Starting single check...")
    result = check_pengumuman(nomor_pendaftaran, tgl_lahir, verbose=True)
    print("\nResult:", json.dumps(result, indent=2))
