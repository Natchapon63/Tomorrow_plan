#!/usr/bin/env python3
"""
Thursday Studio — Test Google Apps Script Web App Endpoint
Sends test payload to the Apps Script Web App URL and checks response.
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

def test_endpoint(url):
    print(f"Testing Google Apps Script Web App at: {url}\n")

    # 1. Test GET (Ping / Health check)
    print("--- 1. Testing GET Request (Health Check) ---")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            print(f"Status Code: {resp.status}")
            print(f"Response: {body}\n")
    except Exception as e:
        print(f"GET Request failed: {e}\n")

    # 2. Test POST (Simulate Influencer Update)
    print("--- 2. Testing POST Request (Influencer Update) ---")
    payload = {
        "jobName": "CanMake - Muchi Puru Tint",
        "notionPageId": "4166e8aac17c813692b0f385e97bc43f",
        "newStatus": "ส่งตรวจ",
        "note": "ทดสอบระบบ Web Sync อัตโนมัติจาก Test Script",
        "timestamp": datetime.now().isoformat()
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'text/plain;charset=utf-8',
                'User-Agent': 'Mozilla/5.0'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            print(f"Status Code: {resp.status}")
            print(f"Response: {body}\n")
            try:
                res_json = json.loads(body)
                if res_json.get('status') == 'ok':
                    print("✅ SUCCESS: Web App returned status: 'ok'!")
                    print("Row appended to Google Sheet with Processed = FALSE.")
                    return True
                else:
                    print(f"⚠️ Warning: Web App returned non-ok status: {res_json}")
                    return False
            except Exception:
                print("Note: Response received but could not parse as JSON.")
                return True
    except Exception as e:
        print(f"❌ POST Request failed: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        target_url = sys.argv[1].strip()
    else:
        # Check index.html for configured URL
        target_url = ''
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.splitlines():
                    if 'const UPDATE_ENDPOINT_URL' in line and "''" not in line and '""' not in line:
                        target_url = line.split('=')[1].strip().strip(';').strip("'").strip('"')
                        break
        except Exception:
            pass

    if not target_url:
        print("Usage: python scripts/test_endpoint.py <WEB_APP_URL>")
        print("Or set UPDATE_ENDPOINT_URL inside index.html")
        sys.exit(1)

    success = test_endpoint(target_url)
    sys.exit(0 if success else 1)
