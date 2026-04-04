import os
import pygame

_BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_BASE, "assets")
_cache = {}

# Taille d'affichage de chaque sprite dans le jeu
_DEFAULT_SIZES = {
    "boat":          (96, 60),
    "grapple":       (34, 34),
    "fish_orange":   (48, 32),
    "fish_red":      (48, 32),
    "fish_blue":     (48, 32),
    "fish_yellow":   (48, 32),
    "fish_purple":   (48, 32),
    "car":           (180, 135),
    "monkey":        (54, 56),
    "ship":          (56, 72),
    "laser":         (6, 28),
    "debris_small":  (26, 26),
    "debris_medium": (40, 40),
    "debris_large":  (56, 56),
    "trash_bottle":  (30, 30),
    "trash_can":     (30, 30),
    "trash_bag":     (30, 30),
    "trash_tire":    (30, 30),
    "trash_box":     (30, 30),
}


def load_sprite(name, size=None):
    final_size = size or _DEFAULT_SIZES.get(name)
    key = (name, final_size)
    if key in _cache:
        return _cache[key]
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    img = pygame.image.load(path).convert_alpha()
    if final_size:
        img = pygame.transform.scale(img, final_size)
    _cache[key] = img
    return img
