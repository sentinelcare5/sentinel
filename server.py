from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import time
import threading
import json

app = FastAPI()

# ====== TUYA CONFIG ======
ACCESS_ID = "k95a3783r5teaydsgkdf"
ACCESS_KEY = "761363a195fc4d258a055895b8a10b5a"
DEVICE_ID = "bfd9be3339d266be8fzsva"
BASE_URL = "https://openapi.tuyaeu.com"

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

# ====== TELEGRAM ALERT ======
def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ====== TUYA TOKEN ======
def get_token():
    url = f"{BASE_URL}/v1.0/token?grant_type=1"
    headers = {
        "client_id": ACCESS_ID,
        "sign": ACCESS_KEY,
    }
    res = requests.get(url, headers=headers)
    return res.json()["result"]["access_token"]

# ====== TUYA DEVICE ======
def get_device_status(token):
    url = f"{BASE_URL}/v1.0/devices/{DEVICE_ID}/status"
    headers = {
        "client_id": ACCESS_ID,
        "access_token": token,
    }
    res = requests.get(url, headers=headers)
    return res.json()["result"]

# ====== MONITOR ======
def monitor():
    global last_alert

    while True:
        try:
            token = get_token()
            print("TOKEN OK")

            data = get_device_status(token)

            for item in data:
                code = item.get("code")
                value = item.get("value")

                print(item)

                # 🚨 PIR DETEKCE
                if code == "pir":

                    print("PIR:", value)

                    if value in ["1", "true", "pir"] and mode == "AWAY":

                        # anti-spam (1 alert za 30s)
                        if last_alert is None or time.time() - last_alert > 30:

                            print("🚨 ALERT SENT")
                            send_telegram_alert("🚨 Pohyb detekován!")

                            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

                            movements.append({
                                "time": current_time,
                                "type": "motion"
                            })

                            save_movements()

                            last_alert = time.time()

                    elif value == "none":
                        pass

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

# ====== DASHBOARD ======
@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <head>
        <title>Sentinel Dashboard</title>
    </head>
    <body style="background:#0b1a2b;color:white;text-align:center;font-family:sans-serif;">
        <h1>🏠 Sentinel Dashboard</h1>
        <h2 id="status">Načítání...</h2>

        <button onclick="setMode('HOME')" style="background:green;color:white;padding:10px;">HOME</button>
        <button onclick="setMode('AWAY')" style="background:red;color:white;padding:10px;">AWAY</button>

        <h2>📊 Historie pohybu</h2>
        <ul id="list"></ul>

        <script>
        async function load() {
            try {
                let res = await fetch("/movements");
                let data = await res.json();

                document.getElementById("status").innerText = "Online";

                let list = document.getElementById("list");
                list.innerHTML = "";

                data.reverse().forEach(m => {
                    let li = document.createElement("li");
                    li.innerText = m.time + " - " + m.type;
                    list.appendChild(li);
                });

            } catch(e) {
                document.getElementById("status").innerText = "Chyba načítání";
            }
        }

        async function setMode(mode) {
            await fetch("/set_mode/" + mode, {method:"POST"});
        }

        setInterval(load, 3000);
        load();
        </script>
    </body>
    </html>
    """
