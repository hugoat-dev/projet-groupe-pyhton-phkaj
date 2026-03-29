#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================
Eco Arcade V2 ENHANCED - Jeu d'arcade écologique
===========================================
Améliorations graphiques :
  • Shake écran sur collision
  • Textes de score flottants (+1, +2…)
  • Eau animée avec vagues sinusoïdales + caustiques
  • Parallaxe jungle (3 couches)
  • Étoiles parallaxes dans l'espace (3 vitesses)
  • Nébuleuse procédurale en fond spatial
  • Flammes réacteur sur le vaisseau
  • Particules de tuyau d'échappement voiture
  • Explosions multi-couches
  • Bulles et algues dans l'océan
  • Grappin avec traînée de corde ondulante
  • Effets de splash eau
  • HUD modernisé avec barres animées
  • Transitions de fondu entre états
  • Lueur pulsante sur les boutons
  • Titre animé avec shimmer
"""

import os, json, math, random, sys
from dataclasses import dataclass, field
import pygame

# ─── CONFIG ──────────────────────────────────────────────────────────────────
WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
W, H = WINDOW_WIDTH, WINDOW_HEIGHT
FRAME_RATE = 60
SAVE_PATH = "eco_arcade_save.json"


def clamp(x, a, b):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_col(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

# ─── SAVE ────────────────────────────────────────────────────────────────────
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

# ─── PALETTES ────────────────────────────────────────────────────────────────
def palette(color_mode: str):
    if color_mode == "deuteranopia":
        return {"bg":(20,25,35),"panel":(245,245,245),"text":(20,25,35),"muted":(90,95,105),
                "accent":(0,170,255),"accent2":(255,170,0),"danger":(255,80,80),"ok":(0,180,255),
                "water_top":(130,200,255),"water_deep":(25,75,135),"jungle":(35,95,50)}
    return {"bg":(18,22,30),"panel":(245,245,245),"text":(18,22,30),"muted":(95,100,112),
            "accent":(70,210,140),"accent2":(255,220,70),"danger":(255,70,70),"ok":(70,210,140),
            "water_top":(145,215,255),"water_deep":(25,85,150),"jungle":(25,105,45)}

# ─── UTILITAIRES GRAPHIQUES ───────────────────────────────────────────────────
def rounded_rect_surf(size, color, radius=12, border=0, border_color=(0,0,0,0)):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    rect = surf.get_rect()
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border > 0:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)
    return surf

def vertical_gradient(size, top_col, bot_col):
    surf = pygame.Surface(size)
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        c = (int(lerp(top_col[0], bot_col[0], t)),
             int(lerp(top_col[1], bot_col[1], t)),
             int(lerp(top_col[2], bot_col[2], t)))
        pygame.draw.line(surf, c, (0, y), (w, y))
    return surf.convert()

def draw_glow(surf, pos, radius, color, alpha=80):
    glow = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    for r in range(radius, 0, -4):
        a = int(alpha * (1 - r / radius) ** 2)
        pygame.draw.circle(glow, (*color[:3], a), (radius, radius), r)
    surf.blit(glow, (pos[0]-radius, pos[1]-radius), special_flags=pygame.BLEND_RGBA_ADD)

# ─── CACHE SPRITES ───────────────────────────────────────────────────────────
SPRITES = {}

def trash_sprite(kind: str, size=30):
    key = ("trash", kind, size)
    if key in SPRITES: return SPRITES[key]
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    if kind == "bottle":
        pygame.draw.rect(s,(90,145,210),(size*.36,size*.18,size*.28,size*.58),border_radius=6)
        pygame.draw.rect(s,(65,120,185),(size*.40,size*.08,size*.20,size*.14),border_radius=4)
        pygame.draw.circle(s,(180,230,255,100),(int(size*.48),int(size*.42)),int(size*.13))
        # étiquette
        pygame.draw.rect(s,(200,80,80,160),(int(size*.38),int(size*.35),int(size*.24),int(size*.18)),border_radius=2)
    elif kind == "can":
        pygame.draw.ellipse(s,(195,195,210),(size*.25,size*.22,size*.50,size*.62))
        pygame.draw.ellipse(s,(160,160,175),(size*.28,size*.26,size*.44,size*.54),2)
        for i in range(3):
            pygame.draw.line(s,(230,230,240),(int(size*.30),int(size*.38+i*7)),(int(size*.70),int(size*.38+i*7)),1)
    elif kind == "bag":
        pts=[(size*.50,size*.10),(size*.80,size*.30),(size*.70,size*.85),(size*.30,size*.85),(size*.20,size*.30)]
        pygame.draw.polygon(s,(220,220,235,130),pts)
        pygame.draw.polygon(s,(175,175,195,200),pts,2)
        pygame.draw.line(s,(150,150,170,180),(int(size*.42),int(size*.10)),(int(size*.38),int(size*.28)),2)
        pygame.draw.line(s,(150,150,170,180),(int(size*.58),int(size*.10)),(int(size*.62),int(size*.28)),2)
    elif kind == "tire":
        pygame.draw.circle(s,(25,25,30),(size//2,size//2),int(size*.34))
        pygame.draw.circle(s,(60,60,70),(size//2,size//2),int(size*.20))
        pygame.draw.circle(s,(35,35,42),(size//2,size//2),int(size*.12))
        for a in range(0,360,45):
            r=math.radians(a)
            pygame.draw.line(s,(42,42,52),
                (size//2+int(math.cos(r)*size*.14),size//2+int(math.sin(r)*size*.14)),
                (size//2+int(math.cos(r)*size*.30),size//2+int(math.sin(r)*size*.30)),2)
    else:  # box
        pygame.draw.rect(s,(150,100,55),(size*.18,size*.26,size*.64,size*.52),border_radius=4)
        pygame.draw.rect(s,(110,70,35),(size*.18,size*.26,size*.64,size*.52),2,border_radius=4)
        pygame.draw.line(s,(110,70,35),(size*.18,size*.38),(size*.82,size*.38),2)
        pygame.draw.line(s,(110,70,35),(size*.50,size*.26),(size*.50,size*.78),2)
        # bande scotch
        pygame.draw.rect(s,(200,180,100,160),(int(size*.44),int(size*.26),int(size*.12),int(size*.52)))
    SPRITES[key] = s.convert_alpha()
    return SPRITES[key]

def boat_sprite():
    key=("boat",)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((96,60),pygame.SRCALPHA)
    hull=[(10,30),(16,14),(48,7),(80,14),(86,30),(80,46),(48,52),(16,46)]
    pygame.draw.polygon(s,(55,150,245),hull)
    pygame.draw.polygon(s,(15,55,145),hull,3)
    # fenêtres
    for ox in (30,52):
        pygame.draw.rect(s,(210,240,255),(ox,20,14,12),border_radius=4)
        pygame.draw.rect(s,(15,55,145),(ox,20,14,12),2,border_radius=4)
    # pont
    pygame.draw.rect(s,(200,205,220),(22,34,52,10),border_radius=3)
    # lumière
    pygame.draw.circle(s,(255,230,80),( 48,10),5)
    pygame.draw.circle(s,(255,230,80,80),(48,10),9)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def grapple_sprite():
    key=("grapple",)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((34,34),pygame.SRCALPHA)
    pygame.draw.circle(s,(180,180,195),(17,17),10)
    pygame.draw.circle(s,(120,120,135),(17,17),8,2)
    for a in(0,120,240):
        r=math.radians(a)
        pygame.draw.line(s,(145,145,158),(17+9*math.cos(r),17+9*math.sin(r)),(17+17*math.cos(r),17+17*math.sin(r)),4)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def fish_sprite(direction=-1, color=None):
    col = color or (255,165,60)
    key=("fish",direction,col)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((48,32),pygame.SRCALPHA)
    body=pygame.Rect(8,8,28,16)
    pygame.draw.ellipse(s,col,body)
    pygame.draw.ellipse(s,(max(0,col[0]-30),max(0,col[1]-40),max(0,col[2]-20)),body,2)
    tail=[(8,16),(2,9),(2,23)] if direction<0 else [(36,16),(44,9),(44,23)]
    eye=(20,14) if direction<0 else (26,14)
    pygame.draw.polygon(s,col,tail)
    pygame.draw.circle(s,(255,255,255),eye,3)
    pygame.draw.circle(s,(0,0,0),eye,2)
    # nageoire dorsale
    fin_pts = [(18,8),(22,3),(28,8)] if direction<0 else [(20,8),(24,3),(30,8)]
    pygame.draw.polygon(s,col,fin_pts)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def car_sprite():
    key=("car",)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((120,90),pygame.SRCALPHA)
    # carrosserie
    pygame.draw.rect(s,(55,195,125),(12,22,96,58),border_radius=14)
    pygame.draw.rect(s,(20,100,40),(12,22,96,58),3,border_radius=14)
    # vitres
    pygame.draw.rect(s,(180,235,255),(26,32,68,20),border_radius=8)
    pygame.draw.rect(s,(0,0,0),(26,32,68,20),2,border_radius=8)
    pygame.draw.line(s,(0,0,0),(60,32),(60,52),2)
    # toit / bac
    pygame.draw.rect(s,(165,172,185),(20,5,80,20),border_radius=6)
    pygame.draw.rect(s,(90,95,110),(20,5,80,20),2,border_radius=6)
    # ligne de recyclage sur le bac
    pygame.draw.line(s,(70,210,140,200),(30,15),(90,15),2)
    # roues
    for x in(28,92):
        for y in(28,76):
            pygame.draw.circle(s,(15,15,18),(x,y),12)
            pygame.draw.circle(s,(55,55,68),(x,y),8)
            pygame.draw.circle(s,(90,90,100),(x,y),4)
    # phares
    pygame.draw.circle(s,(255,235,100),(34,82),5)
    pygame.draw.circle(s,(255,235,100),(86,82),5)
    # reflet carrosserie
    pygame.draw.rect(s,(120,240,175,60),(24,28,40,10),border_radius=4)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def monkey_sprite():
    key=("monkey",)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((54,56),pygame.SRCALPHA)
    pygame.draw.circle(s,(145,90,38),(27,25),19)
    pygame.draw.circle(s,(170,115,62),(15,19),8)
    pygame.draw.circle(s,(170,115,62),(39,19),8)
    pygame.draw.ellipse(s,(225,195,155),(17,23,20,18))
    for eye,p in [((22,27),(20,27)),((32,27),(30,27))]:
        pygame.draw.circle(s,(255,255,255),eye,4)
        pygame.draw.circle(s,(0,0,0),p,2)
    pygame.draw.arc(s,(0,0,0),(19,32,16,10),0,math.pi,2)
    pygame.draw.line(s,(145,90,38),(36,38),(50,52),6)
    pygame.draw.circle(s,(170,115,62),(50,52),5)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def ship_sprite():
    key=("ship",)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((56,72),pygame.SRCALPHA)
    pts=[(28,6),(44,44),(28,40),(12,44)]
    pygame.draw.polygon(s,(150,65,225),pts)
    pygame.draw.polygon(s,(90,30,150),pts,2)
    # ailes
    pygame.draw.polygon(s,(125,50,200),[(12,44),(4,62),(14,52)])
    pygame.draw.polygon(s,(125,50,200),[(44,44),(52,62),(42,52)])
    # cockpit
    pygame.draw.ellipse(s,(170,235,255),(20,14,16,14))
    pygame.draw.ellipse(s,(250,250,255),(23,17,10,8))
    # détails carlingue
    pygame.draw.rect(s,(220,220,240),(18,40,5,10),border_radius=2)
    pygame.draw.rect(s,(220,220,240),(33,40,5,10),border_radius=2)
    # ligne centrale
    pygame.draw.line(s,(180,100,240),(28,6),(28,40),2)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def laser_sprite():
    key=("laser",)
    if key in SPRITES: return SPRITES[key]
    s=pygame.Surface((6,28),pygame.SRCALPHA)
    pygame.draw.rect(s,(80,255,255),(0,0,6,28),border_radius=3)
    pygame.draw.rect(s,(255,255,255),(1,2,4,24),border_radius=2)
    # tip brillante
    pygame.draw.ellipse(s,(200,255,255),(0,0,6,6))
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

def debris_sprite(kind: str):
    key=("debris",kind)
    if key in SPRITES: return SPRITES[key]
    if kind=="small":
        s=pygame.Surface((26,26),pygame.SRCALPHA)
        pts=[(13,2),(22,9),(19,21),(8,23),(3,11)]
        pygame.draw.polygon(s,(135,135,150),pts)
        pygame.draw.polygon(s,(80,80,95),pts,2)
        pygame.draw.line(s,(165,165,178),(8,10),(20,18),1)
    elif kind=="medium":
        s=pygame.Surface((40,40),pygame.SRCALPHA)
        pygame.draw.rect(s,(110,110,128),(6,6,28,28),border_radius=5)
        pygame.draw.rect(s,(70,70,88),(6,6,28,28),2,border_radius=5)
        pygame.draw.line(s,(165,165,180),(6,6),(34,34),2)
        pygame.draw.line(s,(165,165,180),(34,6),(6,34),2)
        pygame.draw.circle(s,(90,90,108),(20,20),6)
    else:
        s=pygame.Surface((56,56),pygame.SRCALPHA)
        pygame.draw.circle(s,(100,100,122),(28,28),24)
        pygame.draw.circle(s,(70,70,92),(28,28),19)
        for a in(0,90,180,270):
            r=math.radians(a)
            x=28+16*math.cos(r); y=28+16*math.sin(r)
            pygame.draw.circle(s,(78,78,98),(int(x),int(y)),6)
        # cratère
        pygame.draw.circle(s,(55,55,75),(20,20),5)
        pygame.draw.circle(s,(55,55,75),(35,32),3)
    SPRITES[key]=s.convert_alpha()
    return SPRITES[key]

# ─── SYSTÈME DE PARTICULES ENRICHI ───────────────────────────────────────────
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    age: float
    kind: str
    size: float
    col: tuple
    gravity: float = 0.0
    rot: float = 0.0
    rot_speed: float = 0.0

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= (1.0 - 0.8 * dt)
        self.vy *= (1.0 - 0.8 * dt)
        self.rot += self.rot_speed * dt

    def dead(self):
        return self.age >= self.life

    def draw(self, screen):
        t = 1.0 - (self.age / max(1e-6, self.life))
        a = int(255 * clamp(t, 0.0, 1.0))
        r = max(1, int(self.size * clamp(t, 0.1, 1.0)))
        surf = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.col[:3], a), (r+1, r+1), r)
        screen.blit(surf, (int(self.x-r), int(self.y-r)))

# ─── TEXTE FLOTTANT (SCORE) ───────────────────────────────────────────────────
@dataclass
class FloatText:
    x: float
    y: float
    text: str
    col: tuple
    life: float = 1.2
    age: float = 0.0
    font: object = None

    def update(self, dt):
        self.age += dt
        self.y -= 55 * dt

    def dead(self):
        return self.age >= self.life

    def draw(self, screen):
        t = 1.0 - (self.age / max(1e-6, self.life))
        a = int(255 * min(1.0, t * 2))
        scale = 1.0 + 0.3 * (1.0 - t)
        txt = self.font.render(self.text, True, self.col)
        # agrandir légèrement
        w, h = txt.get_width(), txt.get_height()
        big = pygame.transform.scale(txt, (int(w*scale), int(h*scale)))
        big.set_alpha(a)
        screen.blit(big, (int(self.x - big.get_width()//2), int(self.y - big.get_height()//2)))

# ─── SYSTÈME DE SHAKE ────────────────────────────────────────────────────────
class ScreenShake:
    def __init__(self):
        self.intensity = 0.0
        self.trauma = 0.0

    def shake(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - dt * 2.5)
        self.intensity = self.trauma ** 2

    def offset(self):
        if self.intensity < 0.001:
            return (0, 0)
        mx = 18 * self.intensity
        return (random.uniform(-mx, mx), random.uniform(-mx, mx))

# ─── FONDU ENTRE ÉTATS ────────────────────────────────────────────────────────
class FadeTransition:
    def __init__(self, duration=0.35):
        self.duration = duration
        self.timer = 0.0
        self.fading_out = True  # True = fade out (noircir), False = fade in (éclaircir)
        self.done = False
        self.alpha = 0

    def update(self, dt):
        self.timer += dt
        t = min(1.0, self.timer / self.duration)
        if self.fading_out:
            self.alpha = int(255 * t)
            if self.timer >= self.duration:
                self.fading_out = False
                self.timer = 0.0
        else:
            self.alpha = int(255 * (1.0 - t))
            if self.timer >= self.duration:
                self.done = True

    def draw(self, screen):
        if self.alpha > 0:
            ov = pygame.Surface((W, H))
            ov.fill((0, 0, 0))
            ov.set_alpha(self.alpha)
            screen.blit(ov, (0, 0))

# ─── MENU PARTICULES ──────────────────────────────────────────────────────────
class MenuParticles:
    def __init__(self):
        self.items = []
        self.spawn_t = 0.0

    def update(self, dt, mode, intensity):
        rate = {"low": 0.35, "med": 0.18, "high": 0.08}.get(intensity, 0.18)
        self.spawn_t += dt
        while self.spawn_t >= rate:
            self.spawn_t -= rate
            if mode == "ocean":
                x = random.uniform(0, W)
                self.items.append(["bubble", x, H+10, random.uniform(-12,12),
                                   random.uniform(-60,-90), random.uniform(0.8,1.6), random.uniform(0,6)])
            elif mode == "jungle":
                x = random.uniform(0, W)
                self.items.append(["leaf", x, -14, random.uniform(-18,18),
                                   random.uniform(40,70), random.uniform(0, math.tau), random.uniform(0.8,1.3)])
            else:
                self.items.append(["star", random.uniform(0,W), random.uniform(0,H),
                                   0, random.uniform(25,120), random.uniform(1,2.8), 0])
        for it in self.items:
            if it[0]=="bubble":
                it[1]+=it[3]*dt; it[2]+=it[4]*dt
                it[1]+=math.sin(pygame.time.get_ticks()/500+it[6])*0.2
            elif it[0]=="leaf":
                it[1]+=it[3]*dt; it[2]+=it[4]*dt; it[5]+=1.5*dt
                it[1]+=math.sin(it[5])*14*dt
            else:
                it[2]+=it[4]*dt
                if it[2]>H+10: it[2]=-10; it[1]=random.uniform(0,W)
        self.items=[it for it in self.items if -80<it[2]<H+80]

    def draw(self, screen, mode):
        if mode=="ocean":
            for it in self.items:
                if it[0]!="bubble": continue
                r=max(2,int(3*it[5]))
                pygame.draw.circle(screen,(220,248,255),(int(it[1]),int(it[2])),r,2)
                pygame.draw.circle(screen,(255,255,255,60),(int(it[1]-r//3),int(it[2]-r//3)),max(1,r//3))
        elif mode=="jungle":
            for it in self.items:
                if it[0]!="leaf": continue
                ang=it[5]; sc=it[6]
                pts=[(it[1]+math.cos(ang+k*math.tau/6)*((9 if k%2==0 else 5)*sc),
                      it[2]+math.sin(ang+k*math.tau/6)*((9 if k%2==0 else 5)*sc)) for k in range(6)]
                pygame.draw.polygon(screen,(100,215,130),pts)
                pygame.draw.polygon(screen,(35,115,62),pts,1)
        else:
            for it in self.items:
                if it[0]!="star": continue
                r=max(1,int(it[5]))
                pygame.draw.circle(screen,(248,248,255),(int(it[1]),int(it[2])),r)
                if r>1: pygame.draw.circle(screen,(255,255,255,60),(int(it[1]),int(it[2])),r+2)

# ─── ARCHITECTURE DES ÉTATS ───────────────────────────────────────────────────
class State:
    def __init__(self, game):
        self.game = game
    def enter(self, **kwargs): pass
    def exit(self): pass
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, screen): pass

# ─── BOUTON AMÉLIORÉ ──────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, label, font):
        self.base_rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.hover = False
        self.pulse = 0.0
        self.shimmer = random.uniform(0, math.tau)

    def update(self, dt, mouse_pos):
        self.hover = self.base_rect.collidepoint(mouse_pos)
        self.pulse = clamp(self.pulse + dt*(8 if self.hover else -12), 0.0, 1.0)
        self.shimmer += dt * 2.5

    def draw(self, screen, pal, selected=False):
        t = max(self.pulse, 1.0 if selected else 0.0)
        grow = int(lerp(0, 12, t))
        rect = self.base_rect.inflate(grow, int(grow*0.5))

        # ombre portée
        shadow = rounded_rect_surf((rect.w, rect.h), (0,0,0,90), radius=14)
        screen.blit(shadow, (rect.x+2, rect.y+6))

        # corps
        if t > 0:
            body_col = (*pal["accent"], 230)
        else:
            body_col = (35, 40, 52, 210)
        border_col = pal["accent2"] if t > 0 else (200, 205, 215)
        body = rounded_rect_surf((rect.w, rect.h), body_col, radius=14, border=2, border_color=border_col)
        screen.blit(body, rect.topleft)

        # glow externe si sélectionné
        if t > 0.05:
            glow_a = int(50 * t)
            glow = pygame.Surface((rect.w+22, rect.h+22), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*pal["accent2"], glow_a), glow.get_rect(), border_radius=20)
            screen.blit(glow, (rect.x-11, rect.y-11))

        # effet shimmer sur la ligne supérieure
        if t > 0.1:
            sh_x = rect.x + int((math.sin(self.shimmer)*0.5+0.5) * rect.w)
            sh_surf = pygame.Surface((60, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(sh_surf, (255,255,255,30), sh_surf.get_rect(), border_radius=14)
            screen.blit(sh_surf, (sh_x - 30, rect.y))

        txt = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))

# ─── MENU PRINCIPAL ───────────────────────────────────────────────────────────
class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font_title = pygame.font.Font(None, 90)
        self.font_btn = pygame.font.Font(None, 38)
        self.font_small = pygame.font.Font(None, 22)
        self.bg_ocean = vertical_gradient((W, H), (30,140,210), (12,50,115))
        self.bg_jungle = vertical_gradient((W, H), (35,155,80), (15,65,40))
        self.bg_space = vertical_gradient((W, H), (8,10,18), (22,12,38))
        self.selected = 0
        labels = ["Océan (Grappin)","Jungle (Voiture)","Espace (Lasers)","Instructions","Paramètres","Quitter"]
        self.actions = ["ocean","jungle","space","instructions","settings","quit"]
        self.buttons = []
        bw, bh = 360, 56
        sy = 190
        for i, lab in enumerate(labels):
            r = pygame.Rect(W//2 - bw//2, sy + i*68, bw, bh)
            self.buttons.append(Button(r, lab, self.font_btn))
        self.particles = MenuParticles()
        self.title_t = 0.0
        self.fade = FadeTransition(0.4)
        self.fade.fading_out = False  # Fade in à l'entrée

    def _preview_mode(self):
        if self.selected == 0: return "ocean"
        if self.selected == 1: return "jungle"
        if self.selected == 2: return "space"
        return "space"

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected+1)%len(self.buttons)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected-1)%len(self.buttons)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self.selected)
            elif e.key == pygame.K_i:
                self.game.transition_to(InstructionsState(self.game))
            elif e.key == pygame.K_ESCAPE:
                self.game.running = False
        elif e.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.base_rect.collidepoint(e.pos): self.selected = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, b in enumerate(self.buttons):
                if b.base_rect.collidepoint(e.pos): self._activate(i)

    def _activate(self, idx):
        act = self.actions[idx]
        if act == "ocean":   self.game.transition_to(OceanGameState(self.game))
        elif act == "jungle": self.game.transition_to(JungleGameState(self.game))
        elif act == "space":  self.game.transition_to(SpaceGameState(self.game))
        elif act == "instructions": self.game.transition_to(InstructionsState(self.game))
        elif act == "settings":     self.game.transition_to(SettingsState(self.game))
        else: self.game.running = False

    def update(self, dt):
        self.pal = palette(self.game.data["settings"]["color_mode"])
        self.title_t += dt
        mode = self._preview_mode()
        inten = self.game.data["settings"]["particles"]
        self.particles.update(dt, mode, inten)
        mp = pygame.mouse.get_pos()
        for b in self.buttons: b.update(dt, mp)
        self.fade.update(dt)

    def draw(self, screen):
        mode = self._preview_mode()
        bg = self.bg_space if mode=="space" else self.bg_ocean if mode=="ocean" else self.bg_jungle
        screen.blit(bg, (0,0))
        self.particles.draw(screen, mode)

        # Titre avec effet shimmer/wave
        t = self.title_t
        title_str = "Eco Arcade"
        for i, ch in enumerate(title_str):
            wave_y = int(math.sin(t*2.8 + i*0.45) * 5)
            sh = self.font_title.render(ch, True, (0,0,0))
            tl = self.font_title.render(ch, True, (255,255,255))
            x_off = 0
            total_w = self.font_title.size(title_str)[0]
            char_x = W//2 - total_w//2 + self.font_title.size(title_str[:i])[0]
            screen.blit(sh, (char_x+3, 62+wave_y+3))
            screen.blit(tl, (char_x, 62+wave_y))

        sub = self.font_small.render("V2 Enhanced — pure pygame, aucun asset externe", True, self.pal["accent2"])
        screen.blit(sub, (W//2 - sub.get_width()//2, 140))

        for i, b in enumerate(self.buttons):
            b.draw(screen, self.pal, selected=(i==self.selected))

        hint = self.font_small.render("↑↓: naviguer | Entrée: lancer | I: instructions | ESC: quitter",
                                      True, (230,235,245))
        screen.blit(hint, (W//2 - hint.get_width()//2, H-30))
        self.fade.draw(screen)

# ─── INSTRUCTIONS ─────────────────────────────────────────────────────────────
class InstructionsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_t = pygame.font.Font(None, 54)
        self.font = pygame.font.Font(None, 24)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_i):
            self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        pal = palette(self.game.data["settings"]["color_mode"])
        screen.fill((18,32,55))
        panel = rounded_rect_surf((760, 520),(255,255,255,230),radius=16,border=2,border_color=(0,0,0,40))
        screen.blit(panel,(70,40))
        t = self.font_t.render("Instructions", True, (15,28,52))
        screen.blit(t,(W//2-t.get_width()//2,58))
        lines=[
            ("OCÉAN — Grappin", True),
            ("• A/D ou ←→: déplacer le bateau.", False),
            ("• SPACE: lancer le grappin (descend puis remonte).", False),
            ("• Déchets pêchés = +10 pts. Poissons = -1 vie si touchés.", False),
            ("JUNGLE — Voiture", True),
            ("• A/D ou ←→: déplacer la voiture.", False),
            ("• Le bac en haut de la voiture collecte les déchets.", False),
            ("• Singe = obstacle: collision => -1 vie + invincibilité 1s.", False),
            ("ESPACE — Lasers", True),
            ("• A/D ou ←→: gauche/droite.", False),
            ("• SPACE: tirer (énergie + cooldown).", False),
            ("• Débris: small(1), medium(2), large(3) points.", False),
            ("", False),
            ("P: Pause | ESC / I: retour au menu", False),
        ]
        y=128
        for txt, is_title in lines:
            if is_title:
                f=pygame.font.Font(None,30); col=(15,28,52)
            else:
                f=self.font; col=pal["text"]
            r=f.render(txt,True,col)
            screen.blit(r,(110,y))
            y+=30

# ─── PARAMÈTRES ───────────────────────────────────────────────────────────────
class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_t = pygame.font.Font(None,56)
        self.font = pygame.font.Font(None,28)
        self.small = pygame.font.Font(None,22)
        self.items = ["particles","color_mode"]
        self.idx = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                save_now(self.game.data)
                self.game.transition_to(MenuState(self.game))
            elif e.key in (pygame.K_UP,pygame.K_w): self.idx=(self.idx-1)%len(self.items)
            elif e.key in (pygame.K_DOWN,pygame.K_s): self.idx=(self.idx+1)%len(self.items)
            elif e.key in (pygame.K_LEFT,pygame.K_a,pygame.K_RIGHT,pygame.K_d):
                key=self.items[self.idx]
                vals=["low","med","high"] if key=="particles" else ["normal","deuteranopia"]
                cur=self.game.data["settings"][key]
                i=vals.index(cur)
                i=(i+(1 if e.key in (pygame.K_RIGHT,pygame.K_d) else -1))%len(vals)
                self.game.data["settings"][key]=vals[i]

    def draw(self, screen):
        screen.fill((22,22,30))
        panel=rounded_rect_surf((720,420),(255,255,255,230),radius=16,border=2,border_color=(0,0,0,40))
        screen.blit(panel,(90,90))
        t=self.font_t.render("Paramètres",True,(15,28,52))
        screen.blit(t,(W//2-t.get_width()//2,108))
        labels={"particles":"Intensité particules","color_mode":"Mode couleurs"}
        y=200
        for i,key in enumerate(self.items):
            sel=(i==self.idx)
            col=(15,28,52) if sel else (90,95,108)
            name=self.font.render(labels[key],True,col)
            screen.blit(name,(140,y))
            val=str(self.game.data["settings"][key])
            v=self.font.render(f"<  {val}  >",True,col)
            screen.blit(v,(560,y))
            y+=70
        hint=self.small.render("←→: changer | ESC: retour",True,(20,25,35))
        screen.blit(hint,(W//2-hint.get_width()//2,455))

# ─── PAUSE ────────────────────────────────────────────────────────────────────
class PauseState(State):
    def __init__(self, game, under_state):
        super().__init__(game)
        self.under = under_state
        self.font = pygame.font.Font(None,58)
        self.small = pygame.font.Font(None,26)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.game.pop_state()
            elif e.key == pygame.K_m:
                self.game.transition_to(MenuState(self.game))

    def draw(self, screen):
        self.under.draw(screen)
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,165))
        screen.blit(ov,(0,0))
        panel=rounded_rect_surf((540,240),(255,255,255,238),radius=18)
        screen.blit(panel,(W//2-270,H//2-120))
        t=self.font.render("PAUSE",True,(18,22,30))
        screen.blit(t,(W//2-t.get_width()//2,H//2-90))
        for i, txt in enumerate(["P / ESC : reprendre","M : menu principal"]):
            r=self.small.render(txt,True,(18,22,30))
            screen.blit(r,(W//2-r.get_width()//2,H//2+15+i*34))

# ─── FIN DE PARTIE ────────────────────────────────────────────────────────────
class EndState(State):
    def __init__(self, game, mode, score, details):
        super().__init__(game)
        self.mode = mode
        self.score = score
        self.details = details
        self.font = pygame.font.Font(None,66)
        self.small = pygame.font.Font(None,28)
        self.t = 0.0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.game.transition_to(MenuState(self.game))

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        pal=palette(self.game.data["settings"]["color_mode"])
        screen.fill((8,10,16))
        # Fond animé
        for i in range(8):
            a=self.t*0.5+i*math.tau/8
            x=W//2+int(math.cos(a)*200)
            y=H//2+int(math.sin(a)*120)
            draw_glow(screen,(x,y),40,pal["accent"],25)

        panel=rounded_rect_surf((740,440),(255,255,255,238),radius=20)
        screen.blit(panel,(80,80))
        best=self.game.data["best"][self.mode]
        new_record=self.score>best
        if new_record:
            self.game.data["best"][self.mode]=self.score
            save_now(self.game.data)
            best=self.score

        title=self.font.render("Fin de partie",True,(15,22,38))
        screen.blit(title,(W//2-title.get_width()//2,100))

        if new_record:
            rec=pygame.font.Font(None,34).render("★ NOUVEAU RECORD ★",True,(255,200,40))
            screen.blit(rec,(W//2-rec.get_width()//2,158))

        y=200 if not new_record else 220
        for k,v in [("Mode",self.mode.upper()),("Score",str(self.score)),("Meilleur",str(best))]+list(self.details):
            col=pal["accent2"] if k=="Score" else pal["text"]
            r=self.small.render(f"{k} : {v}",True,col)
            screen.blit(r,(140,y))
            y+=36

        hint=pygame.font.Font(None,24).render("ESC / Entrée : menu",True,pal["danger"])
        screen.blit(hint,(W//2-hint.get_width()//2,480))

# ─── JEU 1 : OCÉAN ────────────────────────────────────────────────────────────
class OceanGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal = palette(game.data["settings"]["color_mode"])
        self.font = pygame.font.Font(None, 26)
        self.score_font = pygame.font.Font(None, 36)
        self.surface_y = 125
        self.bg_deep = vertical_gradient((W, H), (60,170,230), (12,50,125))
        self.boat_img = boat_sprite()
        self.gr_img = grapple_sprite()
        self.boat_x, self.boat_y = W*0.5, 60
        self.boat_vx = 0.0
        self.gr_active, self.gr_state = False, "idle"
        self.gr_y = self.boat_y + 44
        self.gr_speed = 225.0
        self.gr_max_depth = H - 85
        self.gr_caught = None
        self.trash, self.fish = [], []
        self.bubbles = []      # particules bulles permanentes
        self.seaweeds = []     # algues décoratives
        self.splashes = []     # particules splash entrée grappin
        self.fx = []
        self.float_texts = []
        self.shake = ScreenShake()
        self.spawn_t = 0.0
        self.collected, self.impacts, self.lives, self.time_left = 0, 0, 3, 75.0
        self.impact_threshold, self.next_impact_loss, self.flash_t = 3, 3, 0.0
        self.wave_t = 0.0
        self.caustic_t = 0.0
        self.inv_frames = 0.0
        # Algues
        for _ in range(12):
            self.seaweeds.append({"x": random.uniform(0, W), "ph": random.uniform(0, math.tau),
                                  "h": random.uniform(25, 55), "col": random.choice([(40,150,80),(30,120,65),(55,170,90)])})
        for _ in range(7): self._spawn_trash(x=W+random.uniform(0,350))
        for _ in range(10): self._spawn_fish(x=W+random.uniform(0,500))
        # Bulles d'ambiance
        for _ in range(20):
            self.bubbles.append({"x":random.uniform(0,W),"y":random.uniform(self.surface_y,H),
                                 "r":random.uniform(2,6),"sp":random.uniform(18,40),"ph":random.uniform(0,math.tau)})

    def _spawn_trash(self, x=None):
        k=random.choice(["bottle","can","bag","tire","box"])
        y=random.uniform(self.surface_y+40, H-55)
        self.trash.append({"k":k,"x":W+40 if x is None else x,"y":y,
                           "vx":-random.uniform(48,90),"t":random.uniform(0,10),
                           "rot":random.uniform(0,360),"rots":random.uniform(-28,28),
                           "img":trash_sprite(k,30)})

    def _spawn_fish(self, x=None):
        y=random.uniform(self.surface_y+35, H-50)
        cols=[(255,165,60),(255,100,100),(120,200,255),(255,210,80),(180,120,255)]
        col=random.choice(cols)
        self.fish.append({"x":W+40 if x is None else x,"y":y,
                          "vx":-random.uniform(72,125),"t":random.uniform(0,10),
                          "img":fish_sprite(direction=-1, color=col),"bob":random.uniform(0,math.tau)})

    def _splash(self, x, y):
        for _ in range(8):
            ang=random.uniform(-math.pi,0)
            sp=random.uniform(40,120)
            self.splashes.append(Particle(x,y,math.cos(ang)*sp,math.sin(ang)*sp,0.4,0,"splash",3,(190,230,255),gravity=180))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p: self.game.push_state(PauseState(self.game,self))
            elif e.key == pygame.K_ESCAPE: self.game.transition_to(MenuState(self.game))
            elif e.key == pygame.K_SPACE and not self.gr_active:
                self.gr_active=True; self.gr_state="down"
                self.gr_y=self.boat_y+44; self.gr_caught=None
                self._splash(self.boat_x, self.surface_y)

    def update(self, dt):
        self.pal=palette(self.game.data["settings"]["color_mode"])
        self.time_left-=dt
        self.wave_t+=dt; self.caustic_t+=dt*0.7
        if self.flash_t>0: self.flash_t-=dt
        if self.inv_frames>0: self.inv_frames-=dt
        self.shake.update(dt)

        if self.time_left<=0 or self.lives<=0:
            score=max(0, self.collected*10 - self.impacts*3)
            self.game.transition_to(EndState(self.game,"ocean",score,
                [("Déchets récupérés",self.collected),("Poissons impactés",self.impacts)]))
            return

        keys=pygame.key.get_pressed()
        ax=0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax-=1300.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax+=1300.0
        self.boat_vx+=ax*dt
        self.boat_vx-=self.boat_vx*7.5*dt
        self.boat_vx=clamp(self.boat_vx,-320,320)
        self.boat_x=clamp(self.boat_x+self.boat_vx*dt,70,W-70)

        gr_x=self.boat_x
        if self.gr_active:
            if self.gr_state=="down":
                self.gr_y+=self.gr_speed*dt
                if self.gr_y>=self.gr_max_depth: self.gr_state="up"
                if self.gr_caught is None:
                    for t in self.trash:
                        if (gr_x-t["x"])**2+(self.gr_y-t["y"])**2<28**2:
                            self.gr_caught=t; self.gr_state="up"; break
                for f in self.fish:
                    if (gr_x-f["x"])**2+(self.gr_y-f["y"])**2<26**2:
                        self.lives-=1; self.flash_t=0.5; self.shake.shake(0.5)
                        self.gr_state="up"; break
            elif self.gr_state=="up":
                self.gr_y-=self.gr_speed*dt
                if self.gr_caught:
                    self.gr_caught["x"]=gr_x; self.gr_caught["y"]=self.gr_y+18
                if self.gr_y<=self.boat_y+44:
                    self.gr_active=False; self.gr_state="idle"
                    if self.gr_caught:
                        if self.gr_caught in self.trash: self.trash.remove(self.gr_caught)
                        self.collected+=1
                        self.float_texts.append(FloatText(gr_x, self.boat_y-20,"+10",
                                                           self.pal["accent"],font=self.score_font))
                        # particules de collection
                        for _ in range(10):
                            self.fx.append(Particle(gr_x,self.boat_y,
                                random.uniform(-60,60),random.uniform(-80,-20),0.5,0,"collect",3,
                                self.pal["accent"],gravity=60))
                        self.gr_caught=None

        for t in self.trash[:]:
            if t is self.gr_caught: continue
            t["x"]+=t["vx"]*dt; t["t"]+=dt; t["rot"]+=t["rots"]*dt
            if t["x"]<-80: self.trash.remove(t); continue
            for f in self.fish:
                if (t["x"]-f["x"])**2+(t["y"]-f["y"])**2<32**2:
                    self.impacts+=1
                    if t in self.trash: self.trash.remove(t)
                    # Particules impact
                    for _ in range(6):
                        self.fx.append(Particle(t["x"],t["y"],
                            random.uniform(-50,50),random.uniform(-50,50),0.4,0,"impact",2,(255,150,50)))
                    break

        for f in self.fish[:]:
            f["x"]+=f["vx"]*dt; f["t"]+=dt; f["bob"]+=dt*2.2
            if f["x"]<-80: self.fish.remove(f)

        if self.impacts>=self.next_impact_loss:
            self.lives-=1; self.flash_t=0.6; self.shake.shake(0.4)
            self.next_impact_loss+=self.impact_threshold

        self.spawn_t+=dt
        if self.spawn_t>=1.25:
            self.spawn_t=0.0
            if len(self.trash)<9: self._spawn_trash()
            if len(self.fish)<12: self._spawn_fish()

        # Bulles
        for b in self.bubbles:
            b["y"]-=b["sp"]*dt
            b["x"]+=math.sin(b["ph"]+self.wave_t*1.2)*14*dt
            if b["y"]<self.surface_y:
                b["y"]=random.uniform(H-100,H)
                b["x"]=random.uniform(0,W)

        # Particules
        for p in self.fx[:]+self.splashes[:]:
            p.update(dt)
        self.fx=[p for p in self.fx if not p.dead()]
        self.splashes=[p for p in self.splashes if not p.dead()]
        for ft in self.float_texts[:]:
            ft.update(dt)
        self.float_texts=[ft for ft in self.float_texts if not ft.dead()]

    def _draw_animated_water(self, screen):
        # Surface ondulée
        pts=[(0,H)]
        for x in range(0,W+4,4):
            y=self.surface_y+int(math.sin(x*0.018+self.wave_t*2.2)*5+math.sin(x*0.035+self.wave_t*1.4)*3)
            pts.append((x,y))
        pts.append((W,H))
        surf=pygame.Surface((W,H),pygame.SRCALPHA)
        pygame.draw.polygon(surf,(60,170,230,180),pts)
        screen.blit(surf,(0,0))
        # ligne de surface lumineuse
        wave_pts=[]
        for x in range(0,W+2,2):
            y=self.surface_y+int(math.sin(x*0.018+self.wave_t*2.2)*5+math.sin(x*0.035+self.wave_t*1.4)*3)
            wave_pts.append((x,y))
        if len(wave_pts)>1:
            pygame.draw.lines(screen,(200,240,255),False,wave_pts,3)
            pygame.draw.lines(screen,(255,255,255,120),False,wave_pts,1)

    def _draw_caustics(self, screen):
        # Motifs caustiques (lumière sous l'eau)
        for i in range(5):
            x=int((W/5)*i+W/10+math.sin(self.caustic_t+i*1.3)*30)
            y=int(self.surface_y+60+math.cos(self.caustic_t*0.8+i*0.9)*25)
            size=int(20+math.sin(self.caustic_t*1.5+i)*8)
            s=pygame.Surface((size*2,size*2),pygame.SRCALPHA)
            pygame.draw.ellipse(s,(255,255,200,18),(0,0,size*2,size*2))
            screen.blit(s,(x-size,y-size))

    def draw(self, screen):
        ox,oy=self.shake.offset()
        draw_surf=screen

        # Fond
        draw_surf.blit(self.bg_deep,(int(ox),int(oy)))
        # Ciel
        pygame.draw.rect(draw_surf,(160,215,255),(int(ox),int(oy),W,self.surface_y))

        # Algues
        wt=self.wave_t
        for sw in self.seaweeds:
            bx=int(sw["x"]+ox); by=H+int(oy)
            pts=[]
            segs=8
            for i in range(segs+1):
                t2=i/segs
                sway=math.sin(wt*1.8+sw["ph"]+t2*3)*10*t2
                pts.append((bx+int(sway), by-int(sw["h"]*t2)))
            if len(pts)>1:
                pygame.draw.lines(draw_surf,sw["col"],False,pts,3)

        self._draw_caustics(draw_surf)

        # Eau animée
        self._draw_animated_water(draw_surf)

        # Bulles d'ambiance
        for b in self.bubbles:
            bx,by=int(b["x"]+ox),int(b["y"]+oy)
            r=int(b["r"])
            pygame.draw.circle(draw_surf,(220,248,255),(bx,by),r,1)

        # Poissons
        for f in self.fish:
            bob=math.sin(f["bob"])*4
            draw_surf.blit(f["img"],(int(f["x"]-24+ox),int(f["y"]-16+bob+oy)))

        # Déchets
        for t in self.trash:
            img=pygame.transform.rotate(t["img"],t["rot"])
            bob=math.sin(t["t"]*1.6)*2
            draw_surf.blit(img,img.get_rect(center=(int(t["x"]+ox),int(t["y"]+bob+oy))))

        # Corde grappin avec ondulation
        if self.gr_active:
            gr_x,gr_y=int(self.boat_x+ox),int(self.gr_y+oy)
            by=int(self.boat_y+44+oy)
            segs=12
            pts=[]
            for i in range(segs+1):
                frac=i/segs
                cx=int(self.boat_x+ox)+int(math.sin(frac*math.pi+self.wave_t*4)*5*(1-frac)*self.gr_active)
                cy=by+int((gr_y-by)*frac)
                pts.append((cx,cy))
            if len(pts)>1:
                pygame.draw.lines(draw_surf,(100,100,112),False,pts,2)
            draw_surf.blit(self.gr_img,(gr_x-17,gr_y-17))

        # Particules
        for p in self.splashes+self.fx: p.draw(draw_surf)

        # Bateau
        draw_surf.blit(self.boat_img,(int(self.boat_x-48+ox),int(self.boat_y-28+oy)))

        # Textes flottants
        for ft in self.float_texts: ft.draw(draw_surf)

        # ─── HUD ───
        bar=pygame.Surface((W,72),pygame.SRCALPHA)
        pygame.draw.rect(bar,(255,255,255,215),bar.get_rect())
        draw_surf.blit(bar,(0,0))
        c1=self.pal["text"]
        c2=self.pal["danger"] if self.flash_t>0 else self.pal["text"]
        # Barre de temps
        tpct=self.time_left/75.0
        pygame.draw.rect(draw_surf,(220,220,225),(W//2-100,50,200,12),border_radius=6)
        pygame.draw.rect(draw_surf,lerp_col((255,60,60),(70,210,140),tpct),(W//2-100,50,int(200*tpct),12),border_radius=6)
        draw_surf.blit(self.font.render(f"Déchets: {self.collected}",True,c1),(14,10))
        draw_surf.blit(self.font.render(f"Impacts: {self.impacts}",True,c1),(14,38))
        draw_surf.blit(self.font.render(f"Vie: {self.lives}",True,c2),(W-120,10))
        draw_surf.blit(self.font.render(f"{int(self.time_left)}s",True,c1),(W-80,38))

# ─── JEU 2 : JUNGLE ───────────────────────────────────────────────────────────
class JungleGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal=palette(game.data["settings"]["color_mode"])
        self.font=pygame.font.Font(None,26)
        self.score_font=pygame.font.Font(None,36)
        # Parallaxe 3 couches
        self.bg_sky=vertical_gradient((W,H),(50,170,90),(18,70,42))
        self.parallax=[
            {"surf":self._make_treeline(W,H,0.45,(18,80,38),(25,100,48),80,50),  "x":0.0,"sp":20},
            {"surf":self._make_treeline(W,H,0.55,(28,110,52),(38,140,62),60,40), "x":0.0,"sp":50},
            {"surf":self._make_treeline(W,H,0.68,(35,130,60),(50,165,75),45,30), "x":0.0,"sp":90},
        ]
        self.road_w=int(W*0.52); self.road_x=W//2-int(W*0.52)//2
        self.scroll=0.0
        self.car_img=car_sprite()
        self.car_x,self.car_y=W*0.5,H-120
        self.car_vx,self.acc,self.drag,self.maxv=0.0,1100.0,9.0,280.0
        self.exhaust_t=0.0
        self.trash,self.monkeys=[],[]
        self.fx,self.float_texts=[],[]
        self.shake=ScreenShake()
        self.spawn_t,self.diff=0.0,0.0
        self.score,self.lives,self.time_left=0,3,70.0
        self.inv_t,self.knock_v=0.0,0.0
        for _ in range(4): self._spawn_trash(y=random.uniform(-250,-40))

    def _make_treeline(self,w,h,horizon_frac,col1,col2,tree_w,tree_h):
        surf=pygame.Surface((w*2,h),pygame.SRCALPHA)
        horizon_y=int(h*horizon_frac)
        pygame.draw.rect(surf,col1,(0,horizon_y,w*2,h-horizon_y))
        for x in range(0,w*2,tree_w+random.randint(5,20)):
            bh=random.randint(int(tree_h*0.7),tree_h)
            bx=x+random.randint(-10,10)
            # tronc
            pygame.draw.rect(surf,(80,50,25),(bx+tree_w//2-4,horizon_y-bh+bh//2,8,bh//2+20))
            # feuillage
            for i in range(3):
                r=tree_w//2+i*6
                cy=horizon_y-bh+i*bh//4
                pygame.draw.circle(surf,col2,(bx+tree_w//2,cy),r)
                pygame.draw.circle(surf,col1,(bx+tree_w//2,cy),r,2)
        return surf.convert_alpha()

    def _spawn_trash(self, y=None):
        k=random.choice(["bottle","can","bag","tire","box"])
        x=random.uniform(self.road_x+60,self.road_x+self.road_w-60)
        self.trash.append({"k":k,"x":x,"y":-40 if y is None else y,
                           "rot":random.uniform(0,360),"rots":random.uniform(-45,45),"img":trash_sprite(k,28)})

    def _spawn_monkey(self):
        x=random.uniform(self.road_x+70,self.road_x+self.road_w-70)
        self.monkeys.append({"x":x,"y":-50,"t":random.uniform(0,10),"img":monkey_sprite()})

    def _exhaust(self, dt):
        self.exhaust_t+=dt
        if self.exhaust_t>0.06:
            self.exhaust_t=0.0
            spd=abs(self.car_vx)*0.3+60
            for side in (-1,1):
                self.fx.append(Particle(
                    self.car_x+side*38, self.car_y+48,
                    self.car_vx*0.1+random.uniform(-10,10), random.uniform(20,50),
                    0.35, 0, "exhaust", random.uniform(4,9),
                    (155,155,162), gravity=0))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key==pygame.K_p: self.game.push_state(PauseState(self.game,self))
            elif e.key==pygame.K_ESCAPE: self.game.transition_to(MenuState(self.game))

    def update(self, dt):
        self.pal=palette(self.game.data["settings"]["color_mode"])
        self.time_left-=dt
        if self.inv_t>0: self.inv_t-=dt
        self.shake.update(dt)
        if self.time_left<=0 or self.lives<=0:
            self.game.transition_to(EndState(self.game,"jungle",self.score,
                [("Déchets collectés",self.score),("Vies restantes",self.lives)]))
            return

        self.diff+=dt
        speed=142.0+self.diff*2.0

        keys=pygame.key.get_pressed()
        ax=0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax-=self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax+=self.acc
        self.car_vx+=ax*dt
        self.car_vx-=self.car_vx*self.drag*dt
        if abs(self.knock_v)>1:
            self.car_vx+=self.knock_v
            self.knock_v*=(1.0-7.0*dt)
        self.car_x=clamp(self.car_x+self.car_vx*dt,self.road_x+70,self.road_x+self.road_w-70)
        self.scroll=(self.scroll+speed*dt)%50

        # Parallaxe
        for layer in self.parallax:
            layer["x"]=(layer["x"]-layer["sp"]*dt)%(W)

        # Échappement
        if abs(self.car_vx)>20 or abs(ax)>0.1:
            self._exhaust(dt)

        car_rect=pygame.Rect(0,0,120,90); car_rect.center=(int(self.car_x),int(self.car_y))
        bin_rect=pygame.Rect(car_rect.left+20,car_rect.top+2,car_rect.width-40,20)

        for t in self.trash[:]:
            t["y"]+=speed*dt; t["rot"]+=t["rots"]*dt
            tr=pygame.Rect(0,0,28,28); tr.center=(int(t["x"]),int(t["y"]))
            if bin_rect.colliderect(tr):
                self.score+=1
                self.float_texts.append(FloatText(t["x"],t["y"]-20,"+1",self.pal["accent"],font=self.score_font))
                for _ in range(5):
                    self.fx.append(Particle(t["x"],t["y"],random.uniform(-40,40),random.uniform(-50,-10),
                                            0.4,0,"collect",3,self.pal["accent"],gravity=50))
                self.trash.remove(t)
            elif t["y"]>H+60: self.trash.remove(t)

        for m in self.monkeys[:]:
            m["y"]+=(speed*1.05)*dt; m["t"]+=dt
            mr=pygame.Rect(0,0,46,46); mr.center=(int(m["x"]),int(m["y"]))
            if self.inv_t<=0 and car_rect.inflate(-20,-18).colliderect(mr):
                self.lives-=1; self.inv_t=1.0
                self.shake.shake(0.6)
                self.knock_v=(145 if self.car_x<m["x"] else -145)
                # Explosion collision
                for _ in range(14):
                    self.fx.append(Particle(m["x"],m["y"],random.uniform(-70,70),random.uniform(-70,20),
                                            0.55,0,"boom",4,self.pal["danger"],gravity=80))
                self.monkeys.remove(m)
            elif m["y"]>H+70: self.monkeys.remove(m)

        self.spawn_t+=dt
        if self.spawn_t>=max(0.55,1.05-self.diff*0.01):
            self.spawn_t=0.0
            if random.random()<0.72 and len(self.trash)<10: self._spawn_trash()
            if random.random()<(0.25+self.diff*0.002) and len(self.monkeys)<7: self._spawn_monkey()

        for p in self.fx[:]:
            p.update(dt)
        self.fx=[p for p in self.fx if not p.dead()]
        for ft in self.float_texts[:]:
            ft.update(dt)
        self.float_texts=[ft for ft in self.float_texts if not ft.dead()]

    def draw(self, screen):
        ox,oy=self.shake.offset()
        screen.blit(self.bg_sky,(int(ox),int(oy)))

        # Parallaxe arbres
        for layer in self.parallax:
            for rep in range(3):
                x=int(layer["x"]+ox-W+rep*W)
                screen.blit(layer["surf"],(x,int(oy)))

        # Route
        pygame.draw.rect(screen,(42,42,50),(int(self.road_x+ox),int(oy),self.road_w,H))
        # Bordures route
        for side,bx in [(-1,self.road_x),(1,self.road_x+self.road_w)]:
            for i in range(4):
                stripe_x=bx+side*i*3
                pygame.draw.line(screen,(255,255,255),(int(stripe_x+ox),0),(int(stripe_x+ox),H),1 if i>0 else 3)

        # Lignes centrales
        for y in range(int(-self.scroll),H,50):
            pygame.draw.rect(screen,(240,240,245),(int(W//2-6+ox),int(y+oy),12,28),border_radius=4)

        # Déchets
        for t in self.trash:
            img=pygame.transform.rotate(t["img"],t["rot"])
            screen.blit(img,img.get_rect(center=(int(t["x"]+ox),int(t["y"]+oy))))

        # Singes
        for m in self.monkeys:
            bob=math.sin(m["t"]*6)*2
            screen.blit(m["img"],(int(m["x"]-27+ox),int(m["y"]-27+bob+oy)))

        # Particules
        for p in self.fx: p.draw(screen)

        # Voiture (clignotement si invincible)
        if self.inv_t<=0 or (int(self.inv_t*14)%2==0):
            screen.blit(self.car_img,(int(self.car_x-60+ox),int(self.car_y-45+oy)))

        # Textes flottants
        for ft in self.float_texts: ft.draw(screen)

        # ─── HUD ───
        bar=pygame.Surface((W,68),pygame.SRCALPHA)
        pygame.draw.rect(bar,(255,255,255,215),bar.get_rect())
        screen.blit(bar,(0,0))
        screen.blit(self.font.render(f"Score: {self.score}",True,self.pal["text"]),(14,10))
        screen.blit(self.font.render(f"Vie: {self.lives}",True,self.pal["danger"]),(W-120,10))
        # Barre de temps
        tpct=self.time_left/70.0
        pygame.draw.rect(screen,(220,220,225),(W//2-100,48,200,12),border_radius=6)
        pygame.draw.rect(screen,lerp_col((255,60,60),(70,210,140),tpct),(W//2-100,48,int(200*tpct),12),border_radius=6)
        screen.blit(self.font.render(f"{int(self.time_left)}s",True,self.pal["text"]),(W//2+108,40))

# ─── JEU 3 : ESPACE ───────────────────────────────────────────────────────────
class SpaceGameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.pal=palette(game.data["settings"]["color_mode"])
        self.font=pygame.font.Font(None,26)
        self.score_font=pygame.font.Font(None,38)
        self.ship_img=ship_sprite()
        self.ship_x,self.ship_y=W*0.5,H-95
        self.vx,self.acc,self.drag,self.maxv=0.0,1250.0,10.0,300.0
        self.laser_img=laser_sprite()
        self.lasers,self.cool=[],0.0
        self.energy,self.energy_max,self.energy_regen,self.shot_cost=100.0,100.0,28.0,12.0
        self.debris=[]; self.fx=[]; self.float_texts=[]
        self.shake=ScreenShake()
        self.spawn_t,self.diff=0.0,0.0
        self.score,self.lives,self.time_left=0,3,60.0
        self.thruster_t=0.0
        # Étoiles sur 3 couches de parallaxe
        self.stars_layers=[
            [{"x":random.uniform(0,W),"y":random.uniform(0,H),"r":1,"sp":20+random.uniform(0,10)} for _ in range(100)],
            [{"x":random.uniform(0,W),"y":random.uniform(0,H),"r":1,"sp":50+random.uniform(0,20)} for _ in range(60)],
            [{"x":random.uniform(0,W),"y":random.uniform(0,H),"r":2,"sp":90+random.uniform(0,30)} for _ in range(25)],
        ]
        # Nébuleuses
        self.nebulas=[]
        for _ in range(5):
            self.nebulas.append({"x":random.uniform(0,W),"y":random.uniform(0,H),
                                  "r":random.randint(80,180),
                                  "col":random.choice([(80,30,120),(20,60,130),(130,30,80),(25,100,120)]),
                                  "a":random.randint(15,35)})

    def _spawn_debris(self):
        sz=random.choices(["small","medium","large"],weights=[0.6,0.3,0.1])[0]
        hp={"small":1,"medium":2,"large":3}[sz]
        self.debris.append({"sz":sz,"hp":hp,"max_hp":hp,"img":debris_sprite(sz),
                             "x":random.uniform(40,W-40),"y":-65,
                             "vx":random.uniform(-12,12),"vy":random.uniform(55,105+self.diff*2),
                             "rot":random.uniform(0,360),"rots":random.uniform(-65,65)})

    def _thruster(self, dt):
        self.thruster_t+=dt
        if self.thruster_t>0.04:
            self.thruster_t=0.0
            for side in (-12,0,12):
                self.fx.append(Particle(
                    self.ship_x+side, self.ship_y+34,
                    random.uniform(-8,8), random.uniform(60,110),
                    0.3, 0, "thruster", random.uniform(3,7),
                    random.choice([(255,160,50),(255,100,30),(200,200,255)]),
                    gravity=0))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key==pygame.K_p: self.game.push_state(PauseState(self.game,self))
            elif e.key==pygame.K_ESCAPE: self.game.transition_to(MenuState(self.game))
            elif e.key==pygame.K_SPACE:
                if self.cool<=0 and self.energy>=self.shot_cost:
                    self.energy-=self.shot_cost; self.cool=0.18
                    self.lasers.append([self.ship_x-18,self.ship_y+10])
                    self.lasers.append([self.ship_x+18,self.ship_y+10])

    def update(self, dt):
        self.pal=palette(self.game.data["settings"]["color_mode"])
        self.time_left-=dt; self.diff+=dt
        self.shake.update(dt)
        if self.time_left<=0 or self.lives<=0:
            self.game.transition_to(EndState(self.game,"space",self.score,
                [("Débris détruits",self.score),("Vies restantes",self.lives)]))
            return

        # Étoiles parallaxes
        for layer in self.stars_layers:
            for s in layer:
                s["y"]+=s["sp"]*dt
                if s["y"]>H: s["y"]=-5; s["x"]=random.uniform(0,W)

        # Vaisseau
        keys=pygame.key.get_pressed()
        ax=0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: ax-=self.acc
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ax+=self.acc
        self.vx+=ax*dt
        self.vx-=self.vx*self.drag*dt
        self.vx=clamp(self.vx,-self.maxv,self.maxv)
        self.ship_x=clamp(self.ship_x+self.vx*dt,40,W-40)

        # Réacteur permanent
        self._thruster(dt)

        # Énergie & Laser
        self.energy=min(self.energy_max,self.energy+self.energy_regen*dt)
        if self.cool>0: self.cool-=dt
        for l in self.lasers[:]:
            l[1]-=560*dt
            if l[1]<-20: self.lasers.remove(l)

        # Débris
        ship_rect=pygame.Rect(self.ship_x-25,self.ship_y-20,50,60)
        for d in self.debris[:]:
            d["y"]+=d["vy"]*dt; d["x"]+=d["vx"]*dt; d["rot"]+=d["rots"]*dt
            d_rect=pygame.Rect(0,0,d["img"].get_width(),d["img"].get_height())
            d_rect.center=(int(d["x"]),int(d["y"]))

            hit=False
            for l in self.lasers[:]:
                if d_rect.collidepoint((int(l[0]),int(l[1]))):
                    if l in self.lasers: self.lasers.remove(l)
                    d["hp"]-=1; hit=True
                    for _ in range(5):
                        self.fx.append(Particle(d["x"],d["y"],
                            random.uniform(-50,50),random.uniform(-50,50),0.35,0,"spark",2,self.pal["accent2"]))
                    if d["hp"]<=0:
                        pts=1 if d["sz"]=="small" else 2 if d["sz"]=="medium" else 3
                        self.score+=pts
                        self.float_texts.append(FloatText(d["x"],d["y"],f"+{pts}",self.pal["accent2"],font=self.score_font))
                        for _ in range(20):
                            col=random.choice([self.pal["danger"],(255,200,50),(255,120,30)])
                            self.fx.append(Particle(d["x"],d["y"],
                                random.uniform(-100,100),random.uniform(-100,100),0.7,0,"boom",
                                random.uniform(2,6),col))
                        if d in self.debris: self.debris.remove(d)
                        break
            if hit and d not in self.debris: continue
            if d_rect.colliderect(ship_rect):
                self.lives-=1; self.shake.shake(0.8)
                for _ in range(18):
                    self.fx.append(Particle(self.ship_x,self.ship_y,
                        random.uniform(-90,90),random.uniform(-90,90),0.8,0,"boom",
                        random.uniform(3,7),self.pal["danger"]))
                if d in self.debris: self.debris.remove(d)
            elif d["y"]>H+50:
                if d in self.debris: self.debris.remove(d)

        self.spawn_t+=dt
        if self.spawn_t>=max(0.38,1.2-self.diff*0.02):
            self.spawn_t=0.0
            self._spawn_debris()

        for p in self.fx[:]:
            p.update(dt)
        self.fx=[p for p in self.fx if not p.dead()]
        for ft in self.float_texts[:]:
            ft.update(dt)
        self.float_texts=[ft for ft in self.float_texts if not ft.dead()]

    def draw(self, screen):
        ox,oy=self.shake.offset()
        screen.fill((8,10,18))

        # Nébuleuses
        for nb in self.nebulas:
            ns=pygame.Surface((nb["r"]*2,nb["r"]*2),pygame.SRCALPHA)
            pygame.draw.circle(ns,(*nb["col"],nb["a"]),(nb["r"],nb["r"]),nb["r"])
            screen.blit(ns,(int(nb["x"]-nb["r"]+ox),int(nb["y"]-nb["r"]+oy)))

        # Étoiles couches
        star_cols=[(200,200,200),(230,230,240),(255,255,255)]
        for li,layer in enumerate(self.stars_layers):
            col=star_cols[li]
            for s in layer:
                r=s["r"]
                pygame.draw.circle(screen,col,(int(s["x"]+ox),int(s["y"]+oy)),r)
                if li==2:
                    pygame.draw.circle(screen,(*col,60),(int(s["x"]+ox),int(s["y"]+oy)),r+2)

        # Lasers avec lueur
        for l in self.lasers:
            screen.blit(self.laser_img,(int(l[0]+ox),int(l[1]+oy)))
            draw_glow(screen,(int(l[0]+3+ox),int(l[1]+14+oy)),18,(0,255,255),40)

        # Vaisseau
        screen.blit(self.ship_img,(int(self.ship_x-28+ox),int(self.ship_y-35+oy)))

        # Débris avec barre de vie si >1 HP
        for d in self.debris:
            img=pygame.transform.rotate(d["img"],d["rot"])
            cx,cy=int(d["x"]+ox),int(d["y"]+oy)
            screen.blit(img,img.get_rect(center=(cx,cy)))
            if d["max_hp"]>1:
                bw=img.get_width()
                pct=d["hp"]/d["max_hp"]
                pygame.draw.rect(screen,(80,80,80),(cx-bw//2,cy-img.get_height()//2-10,bw,5),border_radius=2)
                pygame.draw.rect(screen,lerp_col((255,60,60),(70,210,140),pct),
                                 (cx-bw//2,cy-img.get_height()//2-10,int(bw*pct),5),border_radius=2)

        # Particules
        for p in self.fx: p.draw(screen)
        for ft in self.float_texts: ft.draw(screen)

        # ─── HUD ───
        bar=pygame.Surface((W,70),pygame.SRCALPHA)
        pygame.draw.rect(bar,(255,255,255,25),bar.get_rect())
        screen.blit(bar,(0,0))
        screen.blit(self.font.render(f"Score: {self.score}",True,(255,255,255)),(20,18))
        screen.blit(self.font.render(f"Vie: {self.lives}",True,self.pal["danger"]),(W-100,18))

        # Barre énergie
        pygame.draw.rect(screen,(45,45,55),(W//2-105,22,210,18),border_radius=9)
        pct=self.energy/self.energy_max
        ecol=self.pal["accent"] if pct>0.3 else self.pal["danger"]
        pygame.draw.rect(screen,ecol,(W//2-103,24,int(206*pct),14),border_radius=7)
        etxt=self.font.render("NRJ",True,(200,200,210))
        screen.blit(etxt,(W//2-135,20))

        # Barre de temps (droite)
        tpct=self.time_left/60.0
        pygame.draw.rect(screen,(45,45,55),(W-30,20,14,H-40),border_radius=7)
        fill_h=int((H-40)*tpct)
        pygame.draw.rect(screen,lerp_col((255,60,60),(70,210,140),tpct),
                         (W-30,20+(H-40)-fill_h,14,fill_h),border_radius=7)

# ─── CLASSE PRINCIPALE ────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Eco Arcade V2 Enhanced")
        self.screen=pygame.display.set_mode((W, H))
        self.clock=pygame.time.Clock()
        self.running=True
        self.data=load_save()
        self.state_stack=[]
        self.transition_to(MenuState(self))

    def transition_to(self, state):
        self.state_stack=[state]
        state.enter()

    def push_state(self, state):
        self.state_stack.append(state)
        state.enter()

    def pop_state(self):
        if len(self.state_stack)>1:
            s=self.state_stack.pop()
            s.exit()

    def run(self):
        while self.running:
            dt=min(self.clock.tick(FRAME_RATE)/1000.0, 0.05)  # cap dt à 50ms
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    self.running=False
                elif self.state_stack:
                    self.state_stack[-1].handle_event(event)
            if self.state_stack:
                self.state_stack[-1].update(dt)
                self.state_stack[-1].draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

if __name__=="__main__":
    game=Game()
    game.run()