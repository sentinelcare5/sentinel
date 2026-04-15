import time
import hmac
import hashlib
import requests
import threading
import os

from fastapi import FastAPI

# ====== CONFIG ======
import os

ACCESS_ID = ("7h8fj4rs5y33yhsh9j4n")
ACCESS_KEY = ("9534ef18d8544be5b1a9c9fd76514121")
DEVICE_ID = ("bfd9be3339d266be8fzsva")

# bezpečné ořezání mezer
if ACCESS_ID:
    ACCESS_ID = ACCESS_ID.strip()
if ACCESS_KEY:
    ACCESS_KEY = ACCESS_KEY.strip()
if DEVICE_ID:
    DEVICE_ID = DEVICE_ID.strip()

print("ACCESS_ID:", ACCESS_ID)
print("ACCESS_KEY:", ACCESS_KEY)
print("DEVICE_ID:", DEVICE_ID)

BASE_URL = "https://openapi.tuyaeu.com"

TELEGRAM_TOKEN = ("8744898246:AAGClWc9KqAc7xDZhVePZhnanqvalt9Y_ps")
CHAT_ID = ("7885300813")

MODE = "AWAY"  # HOME / AWAY
last_alert = 0

app = FastAPI()

# ====== TELEGRAM ======
def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text
        }
        requests.post(url, data=data)
    except:
        print("TELEGRAM ERROR")


# ====== TUYA TOKEN =======
def get_token():
    timestamp = str(int(time.time() * 1000))

    method = "GET"
    url_path = "/v1.0/token?grant_type=1"

    # ❗ KLÍČOVÉ: dva \n před timestamp
    sign_str = method + "\n" + url_path + "\n\n" + timestamp

    sign = hmac.new(
        ACCESS_KEY.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256"
    }

    url = BASE_URL + url_path

    res = requests.get(url, headers=headers).json()

    print("SIGN STRING:", sign_str)
    print("TOKEN DEBUG:", res)

    if res.get("success"):
        return res["result"]["access_token"]

    return None

# ====== TUYA STATUS ======
def get_status():
    token = get_token()
    if not token:
        return None
                                
    timestamp = str(int(time.time() * 1000))
    sign_str = ACCESS_ID + token + timestamp

    sign = hmac.new( 
        ACCESS_KEY.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest().upper()
                        
    headers = {
        "client_id": ACCESS_ID,
        "access_token": token,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256" 
    }

    url = f"{BASE_URL}/v1.0/devices/{DEVICE_ID}/status"
                        
    try:
        res = requests.get(url, headers=headers).json()

        # 👇 TOTO TAM PŘIDEJ
        print("FULL RESPONSE:", res)

        return res.get("result", [])
    except Exception as e:
        print("STATUS ERROR:", e)
        return None

# ====== MONITOR ======
def monitor():
    global last_alert

    while True:
        try:
            status = get_status()

            if status:
                for item in status:
                    if item["code"] == "pir":
                        print("PIR:", item["value"])

                        if MODE == "AWAY" and item["value"] == "pir":
                            if time.time() - last_alert > 30:
                                print("🚨 POHYB DETEKOVÁN")
                                send_telegram("🚨 POHYB DETEKOVÁN!")
                                last_alert = time.time()

            time.sleep(5)

        except Exception as e:
            print("Monitor error:", e)
            time.sleep(5)


# ====== API ======
@app.get("/")
def home():
    return {"status": "running", "mode": MODE}


@app.get("/set_mode/{mode}")
def set_mode(mode: str):
    global MODE
    MODE = mode.upper()
    return {"mode": MODE}


@app.get("/test")
def test():
    send_telegram("✅ TEST FUNGUJE")
    return {"ok": True}


# ====== START ======
def start_monitor():
    thread = threading.Thread(target=monitor)
    thread.daemon = True
    thread.start()


start_monitor()
