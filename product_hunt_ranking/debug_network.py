import requests
import socket
import sys

def check_connectivity():
    print("1. Testing DNS resolution for sheets.googleapis.com...")
    try:
        ip = socket.gethostbyname("sheets.googleapis.com")
        print(f"   Success: Resolved to {ip}")
    except Exception as e:
        print(f"   Failed: {e}")
        return

    print("\n2. Testing HTTPS connection to Google Sheets API (No Auth)...")
    try:
        response = requests.get("https://sheets.googleapis.com/v4/spreadsheets", timeout=5)
        print(f"   Success: Connected! Status Code: {response.status_code}")
        print("   (404 or 401 is GOOD - it means we reached the server)")
    except Exception as e:
        print(f"   Failed to connect: {e}")

if __name__ == "__main__":
    check_connectivity()
