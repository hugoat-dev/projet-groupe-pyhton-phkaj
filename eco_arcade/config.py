import os
import json

WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
W, H = WINDOW_WIDTH, WINDOW_HEIGHT
FRAME_RATE = 60

_BASE = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.join(_BASE, "..", "eco_arcade_save.json")


def clamp(x, a, b):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_col(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def palette(color_mode: str):
    if color_mode == "deuteranopia":
        return {"bg":(20,25,35),"panel":(245,245,245),"text":(20,25,35),"muted":(90,95,105),
                "accent":(0,170,255),"accent2":(255,170,0),"danger":(255,80,80),"ok":(0,180,255),
                "water_top":(130,200,255),"water_deep":(25,75,135),"jungle":(35,95,50)}
    return {"bg":(18,22,30),"panel":(245,245,245),"text":(18,22,30),"muted":(95,100,112),
            "accent":(70,210,140),"accent2":(255,220,70),"danger":(255,70,70),"ok":(70,210,140),
            "water_top":(145,215,255),"water_deep":(25,85,150),"jungle":(25,105,45)}

def load_save():
    default = {
        "best": {"ocean": 0, "jungle": 0, "space": 0},
        "settings": {"particles": "med", "color_mode": "normal", "volume": 0.0},
    }
    if not os.path.exists(SAVE_PATH):
        return default
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in default:
            if k not in data: data[k] = default[k]
        for k in default["best"]: data["best"].setdefault(k, 0)
        for k in default["settings"]: data["settings"].setdefault(k, default["settings"][k])
        return data
    except Exception:
        return default

def save_now(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
