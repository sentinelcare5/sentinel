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
ACCESS_ID = os.getenv("ACCESS_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
DEVICE_ID = os.getenv("DEVICE_ID")
BASE_URL = "https://openapi.tuyaeu.com"

# ====== TELEGRAM ======
TELEGRAM_TOKEN = os.getenv("8744898246:AAGClWc9KqAc7xDZhVePZhnanqvalt9Y_ps")
CHAT_ID = os.getenv("7885300813")

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
def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram není nastaven")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except:
        print("Telegram error")

# ====== TUYA TOKEN ======
def get_token():
    url = "/v1.0/token?grant_type=1"
    t = str(int(time.time() * 1000))

    message = ACCESS_ID + t
    sign = hmac.new(
        ACCESS_KEY.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest().upper()

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256"
    }

    response = requests.get(BASE_URL + url, headers=headers)
    data = response.json()

    if not data.get("success"):
        print("TOKEN ERROR:", data)
        return None

    return data["result"]["access_token"]

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
        return res.get("result", [])
    except:
        print("STATUS ERROR")
        return None

# ====== MONITOR ======
def monitor():
    global last_alert

    while True:
        try:
            status = get_status()

            if status:
                for item in status:
                    code = item.get("code")
                    value = item.get("value")

                    if code == "pir":
                        print("PIR:", value)

                        # 🚨 POHYB
                        if value in ["1", "true", "pir"] and mode == "AWAY":
                            now = time.strftime('%Y-%m-%d %H:%M:%S')

                            if last_alert != now:
                                print("🚨 ALERT SENT")
                                send_telegram_alert("🚨 Pohyb detekován!")

                                movements.append({
                                    "time": now,
                                    "type": "motion"
                                })

                                save_movements()
                                last_alert = now

                        elif value == "none":
                            last_alert = None

        except Exception as e:
            print("Monitor error:", e)

        time.sleep(5)

# ====== START MONITOR THREAD ======
threading.Thread(target=monitor, daemon=True).start()

# ====== API ======
@app.get("/movements")
def get_movements():
    return movements

@app.post("/set_mode/{new_mode}")
def set_mode(new_mode: str):
    global mode
    mode = new_mode
    return {"mode": mode}

# ====== WEB UI ======
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Sentinel</title>
    </head>
    <body>
        <h1>Sentinel Security</h1>

        <button onclick="setMode('HOME')">HOME</button>
        <button onclick="setMode('AWAY')">AWAY</button>

        <h2>Pohyby:</h2>
        <ul id="list"></ul>

        <script>
        async function load() {
            let res = await fetch('/movements')
            let data = await res.json()

            let list = document.getElementById("list")
            list.innerHTML = ""

            data.reverse().forEach(item => {
                let li = document.createElement("li")
                li.innerText = item.time + " - " + item.type
                list.appendChild(li)
            })
        }

        async function setMode(mode) {
            await fetch('/set_mode/' + mode, {method: 'POST'})
        }

        setInterval(load, 3000)
        load()
        </script>
    </body>
    </html>
    """
