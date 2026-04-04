import os, json
import pygame

W, H = 900, 600
FPS = 60
_BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(_BASE, "assets")
SAVE = os.path.join(_BASE, "..", "save_simple.json")

def clamp(x, a, b): return max(a, min(b, x))
def lerp_col(c1, c2, t): return tuple(int(c1[i] + (c2[i]-c1[i]) * t) for i in range(3))

_cache = {}
_SIZES = {
    "boat": (96,60), "grapple": (34,34),
    "fish_orange": (48,32), "fish_blue": (48,32), "fish_purple": (48,32),
    "car": (180,135), "monkey": (54,56),
    "ship": (56,72), "laser": (6,28),
    "debris_small": (26,26), "debris_medium": (40,40), "debris_large": (56,56),
    "trash_bottle": (55,55), "trash_can": (55,55), "trash_bag": (55,55),
    "trash_tire": (55,55), "trash_box": (55,55),
}

def sprite(name, size=None):
    sz = size or _SIZES.get(name)
    k = (name, sz)
    if k in _cache: return _cache[k]
    img = pygame.image.load(os.path.join(ASSETS, f"{name}.png")).convert_alpha()
    if sz: img = pygame.transform.scale(img, sz)
    _cache[k] = img
    return img

def load_save():
    try:
        with open(SAVE) as f:
            return json.load(f)
    except:
        return {"best": {"ocean": 0, "jungle": 0, "space": 0}}

def save_now(data):
    try:
        with open(SAVE, "w") as f: json.dump(data, f)
    except: pass
