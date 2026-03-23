from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import time
import hmac
import hashlib
import threading
import json
import os

# =====================
# 🔑 NASTAVENÍ
# =====================

ACCESS_ID = "k95a3783r5teaydsgkdf"
ACCESS_SECRET = "761363a195fc4d258a055895b8a10b5a"
DEVICE_ID = "bfd9be3339d266be8fzsva"
BASE_URL = "https://openapi.tuyaeu.com"

TELEGRAM_TOKEN = "8744898246:AAGClWc9KqAc7xDZhVePZhnanqvalt9Y_ps"
CHAT_ID = "7885300813"

app = FastAPI()

# =====================
# 📦 DATA
# =====================

mode = "HOME"
movements = []
if os.path.exists("movements.json"):
    with open("movements.json", "r") as f:
        movements = json.load(f)
last_alert = None


# =====================
# 🔐 TUYA AUTH
# =====================

def generate_sign(t, method, path, token=""):
    body = ""
    content_hash = hashlib.sha256(body.encode()).hexdigest()

    string_to_sign = f"{method}\n{content_hash}\n\n{path}"

    sign_str = ACCESS_ID + token + str(t) + string_to_sign

    sign = hmac.new(
        ACCESS_SECRET.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest().upper()

    return sign


def get_token():
    t = int(time.time() * 1000)
    path = "/v1.0/token?grant_type=1"

    sign = generate_sign(t, "GET", path)

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": str(t),
        "sign_method": "HMAC-SHA256"
    }

    url = BASE_URL + path
    res = requests.get(url, headers=headers)
    data = res.json()

    if data.get("success"):
        print("TOKEN OK")
        return data["result"]["access_token"]
    else:
        print("TUYA TOKEN ERROR:", data)
        return None


# =====================
# 📱 TELEGRAM
# =====================

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)


# =====================
# 🔥 MONITOR
# =====================

import time

def monitor():
    global last_alert

    while True:
        try:
            token = get_token()
            data = get_device_status(token)

            for item in data:
                code = item.get("code")
                value = item.get("value")

                print(item)

                # 🚨 POHYB
                if code == "pir":

                    print("PIR:", value)

                    if value in ["1", "true", "pir"] and mode == "AWAY":
                        print("🚨 ALERT SENT")
                        send_telegram_alert("🚨 Pohyb detekován!")

                        current_time = time.strftime('%Y-%m-%d %H:%M:%S')

                        movements.append({
                            "time": current_time,
                            "type": "motion"
                        })

                        save_movements()

                        print("🚨 ALERT")

                    elif value == "none":
                        last_alert = None

        except Exception as e:
            print("Monitor error:", e)

        time.sleep(5)


# =====================
# 🚀 START MONITORU
# =====================

@app.on_event("startup")
def start():
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()


# =====================
# 🌐 API
# =====================

@app.get("/movements")
def get_movements():
    return movements


@app.post("/set_mode/{new_mode}")
def set_mode(new_mode: str):
    global mode
    mode = new_mode.upper()
    return {"mode": mode}


# =====================
# 🎛️ DASHBOARD
# =====================

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <head>
        <title>Sentinel</title>
        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: #0f172a;
                color: white;
            }

            h1 {
                margin-top: 20px;
            }

            .status {
                font-size: 30px;
                margin: 20px;
            }

            .safe { color: #22c55e; }
            .alert { color: #ef4444; }

            button {
                padding: 10px 20px;
                margin: 10px;
                font-size: 16px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }

            .home { background: #22c55e; }
            .away { background: #ef4444; }

            ul {
                list-style: none;
                padding: 0;
            }

            li {
                margin: 5px;
                padding: 10px;
                background: #1e293b;
                border-radius: 8px;
            }
        </style>
    </head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <body>

        <h1>🏠 Sentinel Dashboard</h1>

        <div class="status" id="status">Načítání...</div>

        <button class="home" onclick="setMode('HOME')">HOME</button>
        <button class="away" onclick="setMode('AWAY')">AWAY</button>

        <h2>📊 Historie pohybu</h2>
        <canvas id="chart" width="400" height="200"></canvas>
        <ul id="list"></ul>

        <script>
let chart;

async function loadChart() {
    const res = await fetch('/stats');
    const data = await res.json();

    const labels = Object.keys(data);
    const values = Object.values(data);

    if (chart) {
        chart.destroy();
    }

    const ctx = document.getElementById('chart').getContext('2d');

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Počet pohybů',
                data: values,
                borderWidth: 2,
                fill: false
            }]
        }
    });
}    

        let lastMovementTime = null;

            async function load() {
                const res = await fetch('/movements');
                const data = await res.json();

                const list = document.getElementById('list');
                list.innerHTML = "";

                if (data.length > 0) {
                    lastMovementTime = data[data.length - 1].time;
                }

                data.slice().reverse().forEach(item => {
                    const li = document.createElement('li');
                    li.innerText = item.time + " - pohyb";
                    list.appendChild(li);
                });

                updateStatus();
            }

            function updateStatus() {
                const status = document.getElementById('status');

                if (!lastMovementTime) {
                    status.innerText = "🟢 Klid";
                    status.className = "status safe";
                    return;
                }

                const now = new Date();
                const parts = lastMovementTime.split(" ");
                const timePart = parts[1];
                const [h, m, s] = timePart.split(":");
                const last = new Date();
                last.setHours(h, m, s);

                const diff = (now - last) / 1000;

                if (diff < 10) {
                    status.innerText = "🔴 Pohyb DETEKOVÁN";
                    status.className = "status alert";
                } else {
                    status.innerText = "🟢 Klid";
                    status.className = "status safe";
                }
            }

            async function load() {
    const res = await fetch('/movements');
    const data = await res.json();

    const list = document.getElementById('list');
    list.innerHTML = "";

    if (data.length > 0) {
        lastMovementTime = data[data.length - 1].time;
    }

    data.slice().reverse().forEach(item => {
        const li = document.createElement('li');
        li.innerText = item.time + " - pohyb";
        list.appendChild(li);
    });

    updateStatus();
    loadChart(); // 🔥 přidáno
} 

        </script>

    </body>
    </html>
    """

@app.get("/stats")
def get_stats():
    stats = {}

    for m in movements:
        time_key = m["time"][:5]  # HH:MM
        stats[time_key] = stats.get(time_key, 0) + 1

    return stats

def save_movements():
    with open("movements.json", "w") as f:
        json.dump(movements, f)
