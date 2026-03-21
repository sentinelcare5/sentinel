from fastapi import FastAPI
from datetime import datetime
from typing import List

app = FastAPI()

movements: List[datetime] = []

@app.post("/movement")
def add_movement(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    movements.append(dt)
    movements.sort()
    return {"status": "movement stored", "total_movements": len(movements)}

@app.get("/status")
def check_status():
    if len(movements) < 3:
        return {"status": "not enough data"}

    # spočítat mezery mezi pohyby
    gaps = []
    for i in range(1, len(movements)):
        diff = movements[i] - movements[i-1]
        gaps.append(diff.total_seconds() / 60)

    avg_gap = sum(gaps) / len(gaps)

    last_movement = movements[-1]
    now = datetime.now()
    current_gap = (now - last_movement).total_seconds() / 60

    if current_gap > avg_gap * 2:
        return {
            "status": "ALERT",
            "inactive_minutes": round(current_gap, 1),
            "avg_gap": round(avg_gap, 1)
        }

    return {
        "status": "OK",
        "inactive_minutes": round(current_gap, 1),
        "avg_gap": round(avg_gap, 1)
    }
from datetime import datetime
from typing import List

app = FastAPI()

movements: List[datetime] = []

@app.post("/movement")
def add_movement(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    movements.append(dt)
    movements.sort()
    return {"status": "movement stored", "total_movements": len(movements)}

@app.get("/status")
def check_status():
    if len(movements) < 3:
        return {"status": "not enough data"}

    # spočítat mezery mezi pohyby
    gaps = []
    for i in range(1, len(movements)):
        diff = movements[i] - movements[i-1]
        gaps.append(diff.total_secon
from datetime import datetime
from typing import List

app = FastAPI()

movements: List[datetime] = []

@app.post("/movement")
def add_movement(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    movements.append(dt)
    movements.sort()
    return {"status": "movement stored", "total_movements": len(movements)}

@app.get("/status")
def check_status():
    if len(movements) < 3:
        return {"status": "not enough data"}

    # spočítat mezery mezi pohyby
    gaps = []
    for i in range(1, len(movements)):
        diff = movements[i] - movements[i-1]
        gaps.append(diff.total_seconds() / 60)

    avg_gap = sum(gaps) / len(gaps)

    last_movement = movements[-1]
    now = datetime.now()
    current_gap = (now - last_movement).total_seconds() / 60

    if current_gap > avg_gap * 2:
        return {
            "status": "ALERT",
            "inactive_minutes": round(current_gap, 1),
            "avg_gap": round(avg_gap, 1)
        }

    return {
        "status": "OK",
        "inactive_minutes": round(current_gap, 1),
        "avg_gap": round(avg_gap, 1)
    }
from fastapi import FastAPI
from datetime import datetime
from typing import List

app = FastAPI()

movements: List[datetime] = []

@app.post("/movement")
def add_movement(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    movements.append(dt)
    movements.sort()
    return {"status": "movement stored", "total_movements": len(movements)}

@app.get("/status")
def check_status():
    if len(movements) < 3:
        return {"status": "not enough data"}

    # spočítat mezery mezi pohyby
    gaps = []
    for i in range(1, len(movements)):
        diff = movements[i] - movements[i-1]
        gaps.append(diff.total_seconds() / 60)

    avg_gap = sum(gaps) / len(gaps)

    last_movement = movements[-1]
    now = datetime.now()
    current_gap = (now - last_movement).total_second
    }



from fastapi import FastAPI
from datetime import datetime
from typing import List

app = FastAPI()

movements: List[datetime] = []
ALERT_THRESHOLD_MINUTES = 120

@app.post("/movement")
def add_movement(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    movements.append(dt)
    return {"status": "movement stored", "total_movements": len(movements)}

@app.get("/status")
def check_status():
    if len(movements) < 1:
        return {"status": "no data"}

    last_movement = movements[-1]
    now = datetime.now()
    diff_minutes = (now - last_movement).total_seconds() / 60

    if diff_minutes > ALERT_THRESHOLD_MINUTES:
        return {
            "status": "ALERT",
            "inactive_minutes": round(diff_minutes, 1)
        }

    return {
        "status": "OK",
        "inactive_minutes": round(diff_minutes, 1)
    }

