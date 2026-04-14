from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import time
import threading
import json
import os
import hashlib
import hmac

app = FastAPI()

# ====== TUYA CONFIG ======
ACCESS_ID = ("7pevmfxdk4scr8fktm73")
ACCESS_KEY = ("96134c27114a48c5b919ff14b849470e")
DEVICE_ID = ("bfd9be3339d266be8fzsva")

BASE_URL = "https://openapi.tuyaeu.com"

print("ACCESS_ID:", ACCESS_ID)
print("ACCESS_KEY:", ACCESS_KEY)
print("DEVICE_ID:", DEVICE_ID)

# ====== TELEGRAM ======
TELEGRAM_TOKEN = "8744898246:AAGClWc9KqAc7xDZhVePZhnanqvalt9Y_ps"
CHAT_ID = "7885300813"

# ====== DATA ======
mode = "HOME"
movements = []
last_alert = None

# ====== SAVE / LOAD ======
def save_movements():
    with open("movements.json", "w") as f:
        json.dump(movements, f)

def load_movements():
    global movements
    try:
        with open("movements.json", "r") as f:
            movements = json.load(f)
    except:
        movements = []

load_movements()

# ====== TELEGRAM ======
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
    except:
        print("TELEGRAM ERROR")

# ====== TUYA TOKEN ======
def get_token():
    timestamp = str(int(time.time() * 1000))
    
    method = "GET"
    url_path = "/v1.0/token?grant_type=1"
    body = ""

    sign_str = method + "\n" + hashlib.sha256(body.encode()).hexdigest() + "\n\n" + url_path

    sign = hmac.new(
        ACCESS_KEY.encode(),
        (ACCESS_ID + timestamp + sign_str).encode(),
        hashlib.sha256
    ).hexdigest().upper()

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256"
    }

    url = f"{BASE_URL}{url_path}"

    res = requests.get(url, headers=headers).json()
    print("TOKEN DEBUG:", res)

    if res.get("success"):
        return res["result"]["access_token"]
    else:
        return None

# ====== TUYA STATUS ======
def get_status():
    token = get_token()
    if not token:
        print("❌ Není token")
        return None

    timestamp = str(int(time.time() * 1000))
    method = "GET"
    url_path = f"/v1.0/devices/{DEVICE_ID}/status"
    body = ""

    # 🔐 správný sign string (Tuya v2)
    sign_str = method + "\n" + hashlib.sha256(body.encode()).hexdigest() + "\n\n" + url_path

    sign = hmac.new(
        ACCESS_KEY.encode(),
        (ACCESS_ID + token + timestamp + sign_str).encode(),
        hashlib.sha256
    ).hexdigest().upper()

    headers = {
        "client_id": ACCESS_ID,
        "access_token": token,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256"
    }

    url = f"{BASE_URL}{url_path}"

    try:
        res = requests.get(url, headers=headers).json()

        # 🔍 DEBUG (DŮLEŽITÉ)
        print("STATUS RESPONSE:", res)

        return res.get("result", [])
    except Exception as e:
        print("STATUS ERROR:", e)
        return None

# ====== MONITOR ======
def monitor():
    while True:
        status = get_status()
        
        if status:
            for item in status:
                if item["code"] == "pir" and item["value"] == "pir":
                    print("POHYB DETEKOVÁN")
                    send_telegram("🚨 POHYB DETEKOVÁN!")
        
        time.sleep(5)

# ====== START THREAD ======
threading.Thread(target=monitor, daemon=True).start()

# TEST TELEGRAM
send_telegram("TEST ZPRÁVA")

# ====== API ======
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>Alarm systém</h1>
    <button onclick="fetch('/set_mode/AWAY', {method:'POST'})">Zapnout</button>
    <button onclick="fetch('/set_mode/HOME', {method:'POST'})">Vypnout</button>
    <h2>Pohyby:</h2>
    <ul id="list"></ul>

    <script>
    async function load(){
        let res = await fetch('/movements')
        let data = await res.json()
        let list = document.getElementById("list")
        list.innerHTML = ""
        data.forEach(m => {
            let li = document.createElement("li")
            li.innerText = m.time + " - " + m.type
            list.appendChild(li)
        })
    }
    setInterval(load, 2000)
    load()
    </script>
    """

@app.get("/movements")
def get_movements():
    return movements

@app.post("/set_mode/{new_mode}")
def set_mode(new_mode: str):
    global mode
    mode = new_mode
    return {"mode": mode}
