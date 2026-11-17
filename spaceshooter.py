# -*- coding: utf-8 -*-
"""
=====================================================================
  GALAXY STRIKE  -  Pixel Space Shooter  (Python + Pygame)
  Mobile touch version | Pydroid3 / Acode ke liye single file
=====================================================================
CONTROLS (Mobile):
  * Screen par ungli rakh kar DRAG karo -> ship us direction mein move
  * Auto-fire: jab enemy RANGE ke andar ho tab bullets khud chalti hain
  * Top-right "II" button = Pause
CONTROLS (PC testing):
  * Arrow keys / WASD = move, P = pause, ESC = quit

Sab graphics (pixel art) aur sounds code se generate hote hain,
koi external image / sound file nahi chahiye.
=====================================================================
"""
import pygame
import random
import math
import json
import os
import sys
import array

# ------------------------------------------------------------------
#  INIT
# ------------------------------------------------------------------
try:
    pygame.mixer.pre_init(22050, -16, 1, 512)
except Exception:
    pass
pygame.init()

LW, LH = 180, 320            # logical (pixel-art) resolution
TH = LH * 2                  # background tile height

try:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
except Exception:
    screen = pygame.display.set_mode((360, 640))
SW, SH = screen.get_size()
SCALE = min(SW / LW, SH / LH)
DW, DH = int(LW * SCALE), int(LH * SCALE)
OX, OY = (SW - DW) // 2, (SH - DH) // 2
canvas = pygame.Surface((LW, LH))
pygame.display.set_caption("Galaxy Strike")
clock = pygame.time.Clock()

F_S = pygame.font.Font(None, 14)
F_M = pygame.font.Font(None, 20)
F_B = pygame.font.Font(None, 34)

try:
    BASE = os.path.dirname(os.path.abspath(__file__))
except Exception:
    BASE = os.getcwd()
SAVE_FILE = os.path.join(BASE, "galaxy_strike_save.json")


def load_save():
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"best": 0, "coins": 0}


def write_save(d):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(d, f)
    except Exception:
        pass


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def text(surf, font, s, color, x, y, align="c", shadow=True):
    img = font.render(s, False, color)
    r = img.get_rect()
    if align == "c":
        r.center = (x, y)
    elif align == "l":
        r.midleft = (x, y)
    else:
        r.midright = (x, y)
    if shadow:
        surf.blit(font.render(s, False, (0, 0, 0)), (r.x + 1, r.y + 1))
    surf.blit(img, r)


def loading(msg):
    canvas.fill((8, 6, 30))
    text(canvas, F_M, msg, (200, 220, 255), LW // 2, LH // 2)
    blit_canvas()
    pygame.display.flip()


def blit_canvas(sx=0, sy=0):
    scaled = pygame.transform.scale(canvas, (DW, DH))
    screen.fill((0, 0, 0))
    screen.blit(scaled, (OX + sx, OY + sy))


# ------------------------------------------------------------------
#  PIXEL ART SPRITES (all drawn from text maps)
# ------------------------------------------------------------------
PAL = {
    "W": (225, 235, 255), "C": (70, 225, 255), "B": (50, 100, 235),
    "R": (255, 70, 70), "O": (255, 150, 40), "Y": (255, 230, 80),
    "D": (35, 35, 70), "G": (80, 230, 110), "P": (150, 70, 220),
    "K": (255, 90, 200), "S": (140, 150, 175), "T": (60, 70, 100),
}


def make_sprite(rows, pal=PAL, mirror=True):
    w = max(len(r) for r in rows)
    rows = [r.rjust(w, ".") for r in rows]
    if mirror:
        rows = [r + r[-2::-1] for r in rows]
    surf = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal:
                surf.set_at((x, y), pal[ch])
    return surf


def flash_of(spr):
    f = spr.copy()
    f.fill((120, 120, 120, 0), special_flags=pygame.BLEND_RGB_ADD)
    return f


PLAYER_HALF = [
    ".....W", ".....W", "....WC", "....WC", "...WWC", "..BWWC",
    ".BBWWW", "BBBWWW", "B.BWRW", "B..WWW", "....DD", ".....D",
]
E0_HALF = [
    "....K", "..KKK", ".KKWK", "KKKRK", "KDKKK", "K.KD.", "....D",
]
E1_HALF = [
    "...DDS", "..DSSS", ".DSGGS", "DSSGRS", "DSSSSS", "D.DS.S", "....D.",
]
E2_HALF = [
    "...SSSS", ".SSPPPP", "SSPPWWP", "SPPWRRW", "SPPPPPP", "SSDDPPP",
    ".S.DDPP", "...S.DD",
]
BOSS_HALF = [
    "..............WW", ".............SSD", "......S.....SSDD", ".....SDS..SSDDPP",
    "....SDDDSSDDPPPP", "..SSDDPPPDDPPCCC", ".SDDPPPPPPPPCWWC",
    "SDDPPPPKPPPPCWWC", "SDPPPPKKKPPPPCCC", "SDPPPPPKPPPPPPPP",
    "SDDPPPPPPPPPPPPP", ".SDDSSPPPPPSSSSS", "..SS.DDSSSDDDDDD",
    "......DD.SSRROOO", ".......D...RROOY",
]
HEART = [".RR.RR.", "RWRRRRR", "RRRRRRR", ".RRRRR.", "..RRR..", "...R..."]
SHIELD = ["CCCCCCC", "CBBBBBC", "CBBWBBC", "CBBBBBC", ".CBBBC.", "..CBC..", "...C..."]
STAR = ["...Y...", "...Y...", "YYYYYYY", ".YYYYY.", "..YYY..", ".YY.YY.", "Y.....Y"]

SPR = {}
FLS = {}


def build_sprites():
    SPR["player"] = make_sprite(PLAYER_HALF)
    pal2 = dict(PAL)
    pal2.update({"K": (255, 150, 40), "D": (90, 40, 20)})
    SPR[0] = make_sprite(E0_HALF, pal2)
    SPR[1] = make_sprite(E1_HALF)
    SPR[2] = make_sprite(E2_HALF)
    b = make_sprite(BOSS_HALF)
    SPR["boss"] = pygame.transform.scale(b, (b.get_width() * 2, b.get_height() * 2))
    SPR["heart"] = make_sprite(HEART, mirror=False)
    SPR["shield"] = make_sprite(SHIELD, mirror=False)
    SPR["star"] = make_sprite(STAR, mirror=False)
    for k in (0, 1, 2, "boss", "player"):
        FLS[k] = flash_of(SPR[k])


ESIZE = {0: (9, 7), 1: (11, 7), 2: (13, 8)}


# ------------------------------------------------------------------
#  SOUND (synthesised, no files)
# ------------------------------------------------------------------
RATE = 22050
SND = {}
MUSIC = None


def tone_arr(f0, f1, dur, vol=0.3, wave="sq", noise=0.0):
    n = max(1, int(RATE * dur))
    buf = array.array("h")
    ph = 0.0
    for i in range(n):
        p = i / n
        ph += (f0 + (f1 - f0) * p) / RATE
        x = ph % 1.0
        if wave == "sq":
            s = 1.0 if x < 0.5 else -1.0
        elif wave == "tri":
            s = 4 * abs(x - 0.5) - 1
        elif wave == "saw":
            s = 2 * x - 1
        else:
            s = random.uniform(-1, 1)
        if noise:
            s = s * (1 - noise) + random.uniform(-1, 1) * noise
        env = (1 - p) ** 1.5
        if i < 100:
            env *= i / 100.0
        buf.append(int(s * env * vol * 32767))
    return buf


def snd(arr):
    return pygame.mixer.Sound(buffer=arr.tobytes())


def cat(*arrs):
    out = array.array("h")
    for a in arrs:
        out.extend(a)
    return out


def build_sounds():
    global MUSIC
    if not pygame.mixer.get_init():
        return
    try:
        SND["shoot"] = snd(tone_arr(1100, 350, 0.07, 0.16, "sq"))
        SND["hit"] = snd(tone_arr(260, 120, 0.06, 0.25, "noise", 0.2))
        SND["boom"] = snd(tone_arr(300, 40, 0.4, 0.5, "saw", 0.8))
        SND["bigboom"] = snd(tone_arr(200, 30, 0.9, 0.6, "saw", 0.85))
        SND["coin"] = snd(cat(tone_arr(988, 988, 0.05, 0.22), tone_arr(1319, 1319, 0.12, 0.22)))
        SND["power"] = snd(cat(tone_arr(523, 523, 0.07, 0.25, "tri"), tone_arr(659, 659, 0.07, 0.25, "tri"),
                               tone_arr(784, 784, 0.07, 0.25, "tri"), tone_arr(1047, 1047, 0.18, 0.25, "tri")))
        SND["hurt"] = snd(tone_arr(220, 70, 0.28, 0.5, "saw", 0.3))
        SND["warn"] = snd(cat(tone_arr(500, 850, 0.4, 0.3), tone_arr(500, 850, 0.4, 0.3), tone_arr(500, 850, 0.4, 0.3)))
        SND["over"] = snd(cat(tone_arr(400, 300, 0.2, 0.3, "tri"), tone_arr(300, 200, 0.2, 0.3, "tri"),
                              tone_arr(200, 90, 0.5, 0.3, "tri")))
        SND["level"] = snd(cat(tone_arr(523, 523, 0.1, 0.25, "tri"), tone_arr(659, 659, 0.1, 0.25, "tri"),
                               tone_arr(784, 784, 0.1, 0.25, "tri"), tone_arr(1047, 1047, 0.1, 0.25, "tri"),
                               tone_arr(1319, 1319, 0.3, 0.25, "tri")))
        SND["start"] = snd(cat(tone_arr(330, 330, 0.08, 0.25), tone_arr(440, 440, 0.08, 0.25),
                               tone_arr(660, 660, 0.2, 0.25)))
        SND["shoot"].set_volume(0.5)
        # background music loop
        chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (130.8, 164.8, 196.0), (196.0, 246.9, 293.7)]
        bass = [110.0, 87.3, 65.4, 98.0]
        pattern = [0, 1, 2, 1, 0, 1, 2, 1]
        step = 0.17
        out = array.array("h")
        for ci in range(4):
            for k in range(8):
                f = chords[ci][pattern[k]] * 2
                a = tone_arr(f, f, step, 0.07, "tri")
                b = tone_arr(bass[ci], bass[ci], step, 0.09, "sq")
                m = array.array("h", [clamp(a[i] + b[i], -32000, 32000) for i in range(len(a))])
                out.extend(m)
        MUSIC = snd(out)
        MUSIC.set_volume(0.45)
    except Exception:
        pass


def play(name):
    s = SND.get(name)
    if s:
        try:
            s.play()
        except Exception:
            pass


# ------------------------------------------------------------------
#  BACKGROUND (nebula + planets + parallax stars)
# ------------------------------------------------------------------
THEMES = [
    ((10, 6, 40), [(100, 40, 170), (40, 70, 180)]),
    ((4, 22, 32), [(20, 130, 130), (30, 90, 170)]),
    ((34, 6, 18), [(170, 40, 60), (160, 95, 30)]),
    ((8, 26, 14), [(40, 150, 60), (120, 160, 40)]),
]


def draw_planet(s, cx, cy, r, col, bands=False):
    lx, ly = -0.6, -0.6
    for yy in range(-r, r + 1):
        for xx in range(-r, r + 1):
            d = math.hypot(xx, yy)
            if d <= r:
                nx, ny = xx / r, yy / r
                nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
                l = nx * lx + ny * ly + nz * 0.6
                lv = 1.15 if l > 0.55 else 0.9 if l > 0.1 else 0.62 if l > -0.3 else 0.38
                c = col
                if bands and (yy // 3) % 2 == 0:
                    c = tuple(min(255, int(v * 0.85 + 30)) for v in col)
                s.set_at(((cx + xx) % LW, (cy + yy) % TH), tuple(min(255, int(v * lv)) for v in c))


def build_bg(level):
    base, cols = THEMES[(level - 1) % len(THEMES)]
    s = pygame.Surface((LW, TH))
    for y in range(TH):
        f = 0.8 + 0.3 * math.sin(y / TH * 2 * math.pi)
        pygame.draw.line(s, tuple(int(v * f) for v in base), (0, y), (LW, y))
    rnd = random.Random(level * 77)
    for _ in range(11):
        cx, cy = rnd.randint(0, LW), rnd.randint(0, TH)
        r = rnd.randint(22, 40)
        col = rnd.choice(cols)
        c1 = tuple(int(base[i] * 0.5 + col[i] * 0.5) for i in range(3))
        c2 = tuple(int(base[i] * 0.7 + col[i] * 0.3) for i in range(3))
        c3 = tuple(int(base[i] * 0.85 + col[i] * 0.15) for i in range(3))
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                d = math.hypot(xx, yy)
                if d >= r:
                    continue
                st = 1 - d / r
                px, py = (cx + xx) % LW, (cy + yy) % TH
                if st > 0.55:
                    s.set_at((px, py), c1)
                elif st > 0.25 and (xx + yy) % 2 == 0:
                    s.set_at((px, py), c2)
                elif st > 0.05 and xx % 2 == 0 and yy % 2 == 0:
                    s.set_at((px, py), c3)
    pc = [(200, 120, 70), (90, 150, 220), (170, 90, 200), (110, 200, 130)]
    draw_planet(s, rnd.randint(20, 160), rnd.randint(40, 200), rnd.randint(13, 20), rnd.choice(pc), True)
    draw_planet(s, rnd.randint(20, 160), rnd.randint(330, 560), rnd.randint(9, 15), rnd.choice(pc), False)
    return s


# ------------------------------------------------------------------
#  GAME
# ------------------------------------------------------------------
RANGE = 170          # attack range (logical px)
SAVE = load_save()


class Game:
    def __init__(self):
        self.state = "menu"
        self.t = 0.0
        self.best = SAVE.get("best", 0)
        self.total_coins = SAVE.get("coins", 0)
        self.stars = []
        for layer, (n, sp, col) in enumerate([(35, 12, (90, 90, 130)), (25, 28, (150, 150, 190)), (14, 55, (255, 255, 255))]):
            for _ in range(n):
                self.stars.append([random.uniform(0, LW), random.uniform(0, LH), sp, layer, col])
        self.bg = None
        self.bg_off = 0.0
        self.shake = 0.0
        self.dragging = False
        self.last = (0, 0)
        self.music_on = False
        self.reset()

    # ---------------- setup ----------------
    def reset(self):
        self.px, self.py = LW / 2, LH - 48
        self.hp, self.maxhp = 100, 100
        self.shield = 0.0
        self.power = 1
        self.inv = 0.0
        self.fire_cd = 0.0
        self.bullets, self.ebul, self.enemies = [], [], []
        self.items, self.parts, self.texts = [], [], []
        self.score = 0
        self.coins = 0
        self.level = 1
        self.kills = 0
        self.boss_need = 14
        self.boss = None
        self.warn = 0.0
        self.wave_t = 1.0
        self.over_t = 0.0
        self.in_range = False
        self.banner = 0.0
        self.minion_t = 5.0
        self.set_bg(1)

    def set_bg(self, lv):
        self.bg = build_bg(lv)

    # ---------------- helpers ----------------
    def add_text(self, x, y, s, col=(255, 255, 255)):
        self.texts.append([x, y, s, col, 0.9])

    def explode(self, x, y, n=14, cols=((255, 220, 80), (255, 140, 40), (255, 80, 40), (255, 255, 255))):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            sp = random.uniform(15, 80)
            self.parts.append([x, y, math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.3, 0.7), random.choice(cols)])

    def ebullet(self, x, y, vx, vy, dmg=10):
        self.ebul.append([x, y, vx, vy, dmg])

    def drop(self, x, y, kind):
        self.items.append({"x": x, "y": y, "k": kind, "t": random.uniform(0, 6)})

    # ---------------- waves ----------------
    def spawn_wave(self):
        lv = self.level
        pat = random.choice(["line", "vee", "zig", "side", "line"])

        def pick():
            r = random.random()
            if lv >= 3 and r < 0.25:
                return 2
            if lv >= 2 and r < 0.5:
                return 1
            return 0 if random.random() < 0.7 else 1

        def mk(k, x, y, mv=0, amp=0, vx=0, ph=0.0):
            hp = {0: 3 + lv // 2, 1: 6 + lv, 2: 12 + 2 * lv}[k]
            spd = {0: 32, 1: 26, 2: 20}[k] + lv
            self.enemies.append({"x": x, "y": y, "bx": x, "k": k, "hp": hp, "maxhp": hp, "t": 0.0,
                                 "mv": mv, "amp": amp, "vx": vx, "spd": spd, "fr": random.uniform(1.4, 2.2),
                                 "ph": ph, "st": random.uniform(1.0, 3.0), "fl": 0.0})

        if pat == "line":
            k = pick()
            for i in range(5):
                mk(k, 22 + i * 34, -10)
        elif pat == "vee":
            k = pick()
            for i in range(5):
                mk(k, 22 + i * 34, -10 - abs(i - 2) * 14)
        elif pat == "zig":
            k = pick()
            bx = random.randint(50, 130)
            for i in range(5):
                mk(k, bx, -10 - i * 20, 0, 38, 0, -i * 0.7)
        else:
            k = pick()
            left = random.random() < 0.5
            for i in range(4):
                mk(k, 10 if left else LW - 10, -10 - i * 22, 1, 0, 40 if left else -40)

    def spawn_boss(self):
        hp = 110 + 55 * self.level
        self.boss = {"x": LW / 2, "y": -40.0, "hp": hp, "maxhp": hp, "t": 0.0, "state": "enter",
                     "atk": 1.5, "pat": 0, "fl": 0.0, "mt": 0.0}

    # ---------------- damage ----------------
    def hurt(self, d):
        if self.inv > 0 or self.state != "play":
            return
        if self.shield > 0:
            self.add_text(self.px, self.py - 14, "BLOCK", (120, 220, 255))
            return
        self.hp -= d
        self.inv = 0.9
        self.shake = 5
        play("hurt")
        if self.hp <= 0:
            self.hp = 0
            self.explode(self.px, self.py, 40)
            play("bigboom")
            self.state = "over"
            self.over_t = 0.0
            self.best = max(self.best, self.score)
            self.total_coins += self.coins
            SAVE["best"] = self.best
            SAVE["coins"] = self.total_coins
            write_save(SAVE)
            if MUSIC:
                MUSIC.fadeout(900)
                self.music_on = False
            play("over")

    def kill_enemy(self, e):
        if e in self.enemies:
            self.enemies.remove(e)
        self.explode(e["x"], e["y"], 12)
        play("boom")
        self.score += {0: 10, 1: 20, 2: 40}[e["k"]]
        if self.boss is None:
            self.kills += 1
        for _ in range({0: 1, 1: 2, 2: 3}[e["k"]]):
            self.drop(e["x"] + random.uniform(-6, 6), e["y"] + random.uniform(-4, 4), "coin")
        if random.random() < 0.14:
            self.drop(e["x"], e["y"], random.choice(["heart", "heart", "shield", "star"]))

    def kill_boss(self):
        b = self.boss
        self.boss = None
        for _ in range(6):
            self.explode(b["x"] + random.uniform(-25, 25), b["y"] + random.uniform(-12, 12), 18)
        play("bigboom")
        self.shake = 14
        self.score += 500 * self.level
        for _ in range(22):
            self.drop(b["x"] + random.uniform(-26, 26), b["y"] + random.uniform(-12, 12), "coin")
        self.drop(b["x"], b["y"], "heart")
        self.drop(b["x"] - 14, b["y"], "shield")
        self.drop(b["x"] + 14, b["y"], "star")
        self.enemies = []
        self.ebul = []
        self.level += 1
        self.kills = 0
        self.boss_need = 14 + self.level * 4
        self.hp = min(self.maxhp, self.hp + 30)
        self.banner = 2.5
        self.set_bg(self.level)
        play("level")

    # ---------------- boss attack ----------------
    def boss_attack(self, b):
        p = b["pat"] % 3
        bs = 85 + self.level * 4
        if p == 0:
            a = math.atan2(self.py - b["y"], self.px - b["x"])
            for off in (-0.28, 0, 0.28):
                self.ebullet(b["x"], b["y"] + 10, math.cos(a + off) * bs, math.sin(a + off) * bs, 12)
        elif p == 1:
            n = 14
            rot = b["t"]
            for i in range(n):
                a = rot + i * 6.283 / n
                self.ebullet(b["x"], b["y"] + 6, math.cos(a) * 65, abs(math.sin(a)) * 65 + 20, 10)
        else:
            for _ in range(7):
                self.ebullet(random.uniform(8, LW - 8), b["y"] + 12, 0, bs * 0.9, 10)
        b["pat"] += 1

    # ---------------- update ----------------
    def update(self, dt):
        self.t += dt
        self.bg_off = (self.bg_off + 28 * dt) % TH
        for s in self.stars:
            s[1] += s[2] * dt
            if s[1] > LH:
                s[1] = 0
                s[0] = random.uniform(0, LW)
        if self.state == "menu":
            return
        if self.state == "pause":
            return
        if self.state == "over":
            self.over_t += dt
            self.update_fx(dt)
            self.shake = max(0, self.shake - 20 * dt)
            return

        # keyboard (PC testing)
        k = pygame.key.get_pressed()
        mx = (k[pygame.K_RIGHT] or k[pygame.K_d]) - (k[pygame.K_LEFT] or k[pygame.K_a])
        my = (k[pygame.K_DOWN] or k[pygame.K_s]) - (k[pygame.K_UP] or k[pygame.K_w])
        self.px += mx * 120 * dt
        self.py += my * 120 * dt
        self.px = clamp(self.px, 8, LW - 8)
        self.py = clamp(self.py, 30, LH - 14)

        self.inv = max(0, self.inv - dt)
        self.shield = max(0, self.shield - dt)
        self.fire_cd -= dt
        self.banner = max(0, self.banner - dt)
        self.shake = max(0, self.shake - 20 * dt)

        # ---- in-range check (auto attack only inside range) ----
        self.in_range = False
        targets = list(self.enemies)
        if self.boss and self.boss["y"] > 0:
            targets.append(self.boss)
        for e in targets:
            if e["y"] < self.py - 4 and e["y"] > -2 and math.hypot(e["x"] - self.px, e["y"] - self.py) <= RANGE:
                self.in_range = True
                break
        if self.in_range and self.fire_cd <= 0:
            self.fire_cd = 0.16
            self.fire()

        # ---- spawn logic ----
        if self.boss is None and self.warn <= 0:
            if self.kills >= self.boss_need:
                self.warn = 3.0
                play("warn")
            else:
                self.wave_t -= dt
                if self.wave_t <= 0:
                    self.spawn_wave()
                    self.wave_t = max(1.1, 2.6 - 0.12 * self.level)
        if self.warn > 0:
            self.warn -= dt
            if self.warn <= 0:
                self.spawn_boss()

        # ---- player bullets ----
        for b in self.bullets[:]:
            b[0] += b[2] * dt
            b[1] += b[3] * dt
            if b[1] < -8 or b[0] < -8 or b[0] > LW + 8:
                self.bullets.remove(b)
                continue
            hit = False
            for e in self.enemies:
                w, h = ESIZE[e["k"]]
                if abs(b[0] - e["x"]) < w / 2 + 1 and abs(b[1] - e["y"]) < h / 2 + 1:
                    e["hp"] -= b[4]
                    e["fl"] = 0.07
                    hit = True
                    self.explode(b[0], b[1], 3, ((255, 255, 200), (120, 220, 255)))
                    if e["hp"] <= 0:
                        self.kill_enemy(e)
                    else:
                        play("hit")
                    break
            if not hit and self.boss and abs(b[0] - self.boss["x"]) < 29 and abs(b[1] - self.boss["y"]) < 14:
                self.boss["hp"] -= b[4]
                self.boss["fl"] = 0.06
                hit = True
                self.explode(b[0], b[1], 3, ((255, 255, 200), (255, 150, 60)))
                if self.boss["hp"] <= 0:
                    self.kill_boss()
            if hit and b in self.bullets:
                self.bullets.remove(b)

        # ---- enemies ----
        for e in self.enemies[:]:
            e["t"] += dt
            e["fl"] = max(0, e["fl"] - dt)
            if e["mv"] == 0:
                e["y"] += e["spd"] * dt
                e["x"] = clamp(e["bx"] + e["amp"] * math.sin(e["t"] * e["fr"] + e["ph"]), 8, LW - 8)
            else:
                e["y"] += e["spd"] * dt * 0.6
                e["x"] += e["vx"] * dt
                if e["x"] < 8 or e["x"] > LW - 8:
                    e["vx"] *= -1
                    e["x"] = clamp(e["x"], 8, LW - 8)
            if e["y"] > LH + 15:
                self.enemies.remove(e)
                continue
            e["st"] -= dt
            if e["st"] <= 0 and 5 < e["y"] < LH - 90:
                sp = min(110, 62 + self.level * 3)
                if e["k"] == 0:
                    if self.level >= 2:
                        self.ebullet(e["x"], e["y"] + 5, 0, sp, 8)
                    e["st"] = 3.5
                elif e["k"] == 1:
                    a = math.atan2(self.py - e["y"], self.px - e["x"])
                    self.ebullet(e["x"], e["y"] + 5, math.cos(a) * sp, math.sin(a) * sp, 10)
                    e["st"] = 2.6
                else:
                    for off in (-0.3, 0, 0.3):
                        a = math.pi / 2 + off
                        self.ebullet(e["x"], e["y"] + 6, math.cos(a) * sp, math.sin(a) * sp, 10)
                    e["st"] = 2.4
            w, h = ESIZE[e["k"]]
            if abs(e["x"] - self.px) < w / 2 + 4 and abs(e["y"] - self.py) < h / 2 + 5:
                self.hurt(20)
                self.kill_enemy(e)

        # ---- boss ----
        b = self.boss
        if b:
            b["t"] += dt
            b["fl"] = max(0, b["fl"] - dt)
            if b["state"] == "enter":
                b["y"] += 32 * dt
                if b["y"] >= 44:
                    b["y"] = 44
                    b["state"] = "fight"
            else:
                b["x"] = LW / 2 + 52 * math.sin(b["t"] * (0.8 if b["hp"] > b["maxhp"] * 0.5 else 1.3))
                b["atk"] -= dt
                if b["atk"] <= 0:
                    self.boss_attack(b)
                    b["atk"] = 1.5 if b["hp"] > b["maxhp"] * 0.5 else 0.95
                b["mt"] += dt
                if b["mt"] > 7 and len(self.enemies) < 4:
                    b["mt"] = 0
                    for sx in (-20, 20):
                        hp = 3 + self.level // 2
                        self.enemies.append({"x": b["x"] + sx, "y": b["y"] + 12, "bx": b["x"] + sx, "k": 0, "hp": hp,
                                             "maxhp": hp, "t": 0.0, "mv": 1, "amp": 0, "vx": sx * 2, "spd": 40,
                                             "fr": 1, "ph": 0, "st": 2, "fl": 0.0})
            if abs(b["x"] - self.px) < 30 and abs(b["y"] - self.py) < 18:
                self.hurt(25)

        # ---- enemy bullets ----
        for eb in self.ebul[:]:
            eb[0] += eb[2] * dt
            eb[1] += eb[3] * dt
            if eb[1] > LH + 6 or eb[1] < -10 or eb[0] < -8 or eb[0] > LW + 8:
                self.ebul.remove(eb)
                continue
            if math.hypot(eb[0] - self.px, eb[1] - self.py) < 6:
                self.ebul.remove(eb)
                self.hurt(eb[4])

        # ---- items ----
        for it in self.items[:]:
            it["t"] += dt
            d = math.hypot(self.px - it["x"], self.py - it["y"])
            if it["k"] == "coin" and d < 42:
                a = math.atan2(self.py - it["y"], self.px - it["x"])
                it["x"] += math.cos(a) * 140 * dt
                it["y"] += math.sin(a) * 140 * dt
            else:
                it["y"] += 32 * dt
            if it["y"] > LH + 10:
                self.items.remove(it)
                continue
            if d < 11:
                self.items.remove(it)
                k = it["k"]
                if k == "coin":
                    self.coins += 1
                    self.score += 5
                    play("coin")
                elif k == "heart":
                    self.hp = min(self.maxhp, self.hp + 30)
                    self.add_text(self.px, self.py - 14, "+30 HP", (255, 110, 110))
                    play("power")
                elif k == "shield":
                    self.shield = 8.0
                    self.add_text(self.px, self.py - 14, "SHIELD!", (120, 220, 255))
                    play("power")
                elif k == "star":
                    if self.power < 3:
                        self.power += 1
                        self.add_text(self.px, self.py - 14, "POWER UP!", (255, 230, 80))
                    else:
                        self.score += 50
                        self.add_text(self.px, self.py - 14, "+50", (255, 230, 80))
                    play("power")
        self.update_fx(dt)

    def update_fx(self, dt):
        for p in self.parts[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
            if p[4] <= 0:
                self.parts.remove(p)
        for t in self.texts[:]:
            t[1] -= 18 * dt
            t[4] -= dt
            if t[4] <= 0:
                self.texts.remove(t)

    def fire(self):
        x, y = self.px, self.py - 8
        if self.power == 1:
            self.bullets.append([x, y, 0, -270, 1])
        elif self.power == 2:
            self.bullets.append([x - 3, y, 0, -270, 1])
            self.bullets.append([x + 3, y, 0, -270, 1])
        else:
            self.bullets.append([x, y, 0, -275, 1])
            self.bullets.append([x - 4, y + 2, -32, -262, 1])
            self.bullets.append([x + 4, y + 2, 32, -262, 1])
        play("shoot")

    # ---------------- input ----------------
    def to_logical(self, pos):
        return (pos[0] - OX) / SCALE, (pos[1] - OY) / SCALE

    def pause_hit(self, lp):
        return lp[0] > LW - 24 and lp[1] < 20

    def start_game(self):
        self.reset()
        self.state = "play"
        play("start")
        if MUSIC and not self.music_on:
            try:
                MUSIC.play(loops=-1)
                self.music_on = True
            except Exception:
                pass

    def toggle_pause(self):
        if self.state == "play":
            self.state = "pause"
            self.dragging = False
            try:
                pygame.mixer.pause()
            except Exception:
                pass
        elif self.state == "pause":
            self.state = "play"
            try:
                pygame.mixer.unpause()
            except Exception:
                pass

    def on_down(self, pos):
        lp = self.to_logical(pos)
        if self.state == "menu":
            self.start_game()
        elif self.state == "over":
            if self.over_t > 0.8:
                self.start_game()
        elif self.state == "pause":
            self.toggle_pause()
        elif self.state == "play":
            if self.pause_hit(lp):
                self.toggle_pause()
            else:
                self.dragging = True
                self.last = lp

    def on_move(self, pos):
        if self.state == "play" and self.dragging:
            lp = self.to_logical(pos)
            self.px = clamp(self.px + (lp[0] - self.last[0]) * 1.35, 8, LW - 8)
            self.py = clamp(self.py + (lp[1] - self.last[1]) * 1.35, 30, LH - 14)
            self.last = lp

    def on_up(self):
        self.dragging = False

    # ---------------- drawing ----------------
    def bar(self, x, y, w, h, ratio, col, back=(40, 20, 30)):
        pygame.draw.rect(canvas, (0, 0, 0), (x - 1, y - 1, w + 2, h + 2))
        pygame.draw.rect(canvas, back, (x, y, w, h))
        fw = int(w * clamp(ratio, 0, 1))
        if fw > 0:
            pygame.draw.rect(canvas, col, (x, y, fw, h))
            pygame.draw.rect(canvas, tuple(min(255, c + 70) for c in col), (x, y, fw, 1))

    def draw_bg(self):
        off = int(self.bg_off)
        canvas.blit(self.bg, (0, off - TH))
        canvas.blit(self.bg, (0, off))
        for s in self.stars:
            x, y = int(s[0]), int(s[1])
            if s[3] == 2:
                pygame.draw.rect(canvas, s[4], (x, y, 1, 2))
            else:
                canvas.set_at((x, y), s[4])

    def draw_ship(self, x, y, flame=True, alpha_blink=False):
        spr = SPR["player"]
        if flame:
            fl = 2 + int((self.t * 30) % 3)
            pygame.draw.rect(canvas, (255, 150, 40), (int(x) - 2, int(y) + 5, 2, fl))
            pygame.draw.rect(canvas, (255, 150, 40), (int(x) + 1, int(y) + 5, 2, fl))
            pygame.draw.rect(canvas, (255, 240, 120), (int(x) - 1, int(y) + 5, 2, fl - 1))
            pygame.draw.rect(canvas, (255, 240, 120), (int(x) + 2, int(y) + 5, 1, fl - 1))
        canvas.blit(spr, (int(x) - spr.get_width() // 2, int(y) - spr.get_height() // 2))

    def draw_play(self):
        self.draw_bg()
        # items
        for it in self.items:
            x, y = int(it["x"]), int(it["y"])
            if it["k"] == "coin":
                w = max(1, int(abs(math.cos(it["t"] * 6)) * 5))
                pygame.draw.ellipse(canvas, (255, 200, 40), (x - w // 2 - 1, y - 3, w + 2, 6))
                if w > 2:
                    pygame.draw.rect(canvas, (255, 245, 150), (x - 1, y - 2, 1, 3))
            else:
                by = y + int(math.sin(it["t"] * 5) * 1.5)
                col = {"heart": (255, 70, 90), "shield": (70, 190, 255), "star": (255, 220, 60)}[it["k"]]
                pygame.draw.circle(canvas, (15, 15, 40), (x, by), 7)
                pygame.draw.circle(canvas, col, (x, by), 7, 1)
                spr = SPR[it["k"]]
                canvas.blit(spr, (x - spr.get_width() // 2, by - spr.get_height() // 2))
        # range ring (dotted)
        rc = (80, 255, 130) if self.in_range else (70, 120, 170)
        for i in range(0, 180, 9):
            a = math.radians(180 + i)
            rx = self.px + math.cos(a) * RANGE
            ry = self.py + math.sin(a) * RANGE
            if 0 <= rx < LW and 0 <= ry < LH:
                canvas.set_at((int(rx), int(ry)), rc)
        # enemies
        for e in self.enemies:
            spr = FLS[e["k"]] if e["fl"] > 0 else SPR[e["k"]]
            canvas.blit(spr, (int(e["x"]) - spr.get_width() // 2, int(e["y"]) - spr.get_height() // 2))
            w = 12
            if e["y"] > -4:
                self.bar(int(e["x"]) - w // 2, int(e["y"]) - ESIZE[e["k"]][1] // 2 - 4, w, 2,
                         e["hp"] / e["maxhp"], (255, 60, 60), (60, 10, 10))
        # boss
        b = self.boss
        if b:
            spr = FLS["boss"] if b["fl"] > 0 else SPR["boss"]
            canvas.blit(spr, (int(b["x"]) - spr.get_width() // 2, int(b["y"]) - spr.get_height() // 2))
            f = 2 + int((self.t * 20) % 3)
            for dx in (-14, 14):
                pygame.draw.rect(canvas, (255, 160, 40), (int(b["x"]) + dx - 1, int(b["y"]) - 15 + 30, 3, f))
        # bullets
        for bl in self.bullets:
            pygame.draw.rect(canvas, (120, 230, 255), (int(bl[0]) - 1, int(bl[1]) - 3, 2, 6))
            pygame.draw.rect(canvas, (255, 255, 255), (int(bl[0]) - 1, int(bl[1]) - 3, 1, 3))
        for eb in self.ebul:
            pygame.draw.circle(canvas, (255, 60, 60), (int(eb[0]), int(eb[1])), 2)
            canvas.set_at((int(eb[0]), int(eb[1])), (255, 230, 200))
        # player
        if self.state == "play" or self.state == "pause":
            if not (self.inv > 0 and int(self.t * 20) % 2 == 0):
                self.draw_ship(self.px, self.py)
            if self.shield > 0:
                blink = self.shield < 2 and int(self.t * 10) % 2 == 0
                if not blink:
                    pygame.draw.circle(canvas, (90, 210, 255), (int(self.px), int(self.py)), 13, 1)
                    if int(self.t * 8) % 2 == 0:
                        pygame.draw.circle(canvas, (40, 120, 200), (int(self.px), int(self.py)), 11, 1)
        # particles / texts
        for p in self.parts:
            canvas.set_at((int(p[0]), int(p[1])), p[5])
            if p[4] > 0.35:
                canvas.set_at((int(p[0]) + 1, int(p[1])), p[5])
        for t in self.texts:
            text(canvas, F_S, t[2], t[3], int(t[0]), int(t[1]))
        self.draw_hud()
        # warning
        if self.warn > 0:
            if int(self.t * 4) % 2 == 0:
                ov = pygame.Surface((LW, LH), pygame.SRCALPHA)
                ov.fill((255, 0, 0, 45))
                canvas.blit(ov, (0, 0))
            pygame.draw.rect(canvas, (120, 0, 0), (0, LH // 2 - 22, LW, 40))
            pygame.draw.rect(canvas, (255, 60, 60), (0, LH // 2 - 22, LW, 40), 1)
            text(canvas, F_B, "WARNING!", (255, 230, 120), LW // 2, LH // 2 - 8)
            text(canvas, F_S, "MOTHERSHIP APPROACHING", (255, 255, 255), LW // 2, LH // 2 + 10)
        if self.banner > 0:
            text(canvas, F_B, "LEVEL %d" % self.level, (120, 255, 160), LW // 2, LH // 2 - 30)
            text(canvas, F_S, "Boss defeated! +30 HP", (255, 255, 255), LW // 2, LH // 2 - 12)

    def draw_hud(self):
        canvas.blit(SPR["heart"], (3, 3))
        self.bar(13, 4, 62, 6, self.hp / self.maxhp,
                 (60, 220, 90) if self.hp > 50 else (255, 190, 50) if self.hp > 25 else (255, 60, 60))
        text(canvas, F_S, "%d" % self.hp, (255, 255, 255), 78, 7, "l")
        if self.shield > 0:
            canvas.blit(SPR["shield"], (3, 13))
            self.bar(13, 15, 62, 4, self.shield / 8.0, (80, 200, 255), (10, 30, 60))
        text(canvas, F_S, "LV %d" % self.level, (255, 255, 160), 112, 7)
        text(canvas, F_S, "%d" % self.score, (255, 255, 255), LW - 20, 7, "r")
        pygame.draw.circle(canvas, (255, 200, 40), (LW - 28, 19), 3)
        text(canvas, F_S, "%d" % self.coins, (255, 220, 80), LW - 22, 19, "r")
        # pause button
        pygame.draw.rect(canvas, (20, 20, 50), (LW - 16, 3, 12, 11))
        pygame.draw.rect(canvas, (150, 170, 220), (LW - 16, 3, 12, 11), 1)
        pygame.draw.rect(canvas, (255, 255, 255), (LW - 13, 5, 2, 7))
        pygame.draw.rect(canvas, (255, 255, 255), (LW - 9, 5, 2, 7))
        # power level
        for i in range(self.power):
            canvas.blit(SPR["star"], (3 + i * 8, LH - 10), (0, 0, 7, 7))
        if self.in_range is False and self.state == "play" and self.enemies:
            text(canvas, F_S, "OUT OF RANGE", (255, 120, 120), LW // 2, LH - 8) if int(self.t * 3) % 2 == 0 else None
        # boss bar
        if self.boss:
            b = self.boss
            self.bar(30, 27, 120, 6, b["hp"] / b["maxhp"], (230, 50, 220), (50, 10, 50))
            text(canvas, F_S, "MOTHERSHIP", (255, 200, 255), LW // 2, 38)

    def draw_menu(self):
        self.draw_bg()
        bob = math.sin(self.t * 2) * 3
        text(canvas, F_B, "GALAXY", (90, 230, 255), LW // 2, 52 + bob)
        text(canvas, F_B, "STRIKE", (255, 190, 60), LW // 2, 80 + bob)
        text(canvas, F_S, "- PIXEL SPACE SHOOTER -", (200, 200, 255), LW // 2, 100)
        sx = LW // 2 + math.sin(self.t * 1.3) * 30
        sy = 175 + math.sin(self.t * 2.6) * 6
        self.draw_ship(sx, sy)
        spr = SPR["boss"]
        canvas.blit(spr, (LW // 2 - spr.get_width() // 2, 118 + int(math.sin(self.t * 1.5) * 3) - 40 + 40 - 20))
        text(canvas, F_S, "BEST: %d" % self.best, (255, 255, 255), LW // 2, 215)
        pygame.draw.circle(canvas, (255, 200, 40), (LW // 2 - 24, 229), 3)
        text(canvas, F_S, "COINS: %d" % self.total_coins, (255, 220, 80), LW // 2 - 18, 229, "l")
        if int(self.t * 2) % 2 == 0:
            text(canvas, F_M, "TAP TO START", (120, 255, 160), LW // 2, 258)
        text(canvas, F_S, "Drag = move ship", (170, 190, 230), LW // 2, 280)
        text(canvas, F_S, "Auto-fire inside RANGE", (170, 190, 230), LW // 2, 292)
        text(canvas, F_S, "Collect coins, hearts, shields, stars", (170, 190, 230), LW // 2, 304)

    def draw_over(self):
        self.draw_play()
        ov = pygame.Surface((LW, LH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        canvas.blit(ov, (0, 0))
        text(canvas, F_B, "GAME OVER", (255, 80, 80), LW // 2, 100)
        text(canvas, F_M, "SCORE: %d" % self.score, (255, 255, 255), LW // 2, 140)
        text(canvas, F_M, "BEST: %d" % self.best, (255, 230, 120), LW // 2, 160)
        text(canvas, F_M, "COINS EARNED: %d" % self.coins, (255, 210, 60), LW // 2, 180)
        text(canvas, F_S, "LEVEL REACHED: %d" % self.level, (160, 220, 255), LW // 2, 198)
        if self.over_t > 0.8 and int(self.t * 2) % 2 == 0:
            text(canvas, F_M, "TAP TO RETRY", (120, 255, 160), LW // 2, 240)

    def draw_pause(self):
        self.draw_play()
        ov = pygame.Surface((LW, LH), pygame.SRCALPHA)
        ov.fill((0, 0, 20, 160))
        canvas.blit(ov, (0, 0))
        text(canvas, F_B, "PAUSED", (255, 255, 255), LW // 2, 130)
        text(canvas, F_S, "Tap anywhere to resume", (180, 200, 255), LW // 2, 160)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "over":
            self.draw_over()
        elif self.state == "pause":
            self.draw_pause()
        else:
            self.draw_play()
        sx = sy = 0
        if self.shake > 0:
            sx = int(random.uniform(-self.shake, self.shake) * SCALE * 0.5)
            sy = int(random.uniform(-self.shake, self.shake) * SCALE * 0.5)
        blit_canvas(sx, sy)
        pygame.display.flip()


# ------------------------------------------------------------------
#  MAIN
# ------------------------------------------------------------------
def main():
    loading("LOADING...")
    build_sprites()
    loading("GENERATING SOUNDS...")
    build_sounds()
    loading("BUILDING GALAXY...")
    game = Game()
    bg_events = [getattr(pygame, n) for n in ("APP_WILLENTERBACKGROUND", "WINDOWFOCUSLOST") if hasattr(pygame, n)]
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or ev.key == getattr(pygame, "K_AC_BACK", -999):
                    if game.state == "play":
                        game.toggle_pause()
                    elif game.state == "menu":
                        running = False
                    elif game.state == "pause":
                        game.toggle_pause()
                    else:
                        game.state = "menu"
                elif ev.key == pygame.K_p:
                    game.toggle_pause()
                elif ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if game.state == "menu" or (game.state == "over" and game.over_t > 0.8):
                        game.start_game()
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                game.on_down(ev.pos)
            elif ev.type == pygame.MOUSEMOTION:
                if ev.buttons and ev.buttons[0]:
                    game.on_move(ev.pos)
            elif ev.type == pygame.MOUSEBUTTONUP:
                game.on_up()
            elif ev.type in bg_events:
                if game.state == "play":
                    game.toggle_pause()
        game.update(dt)
        game.draw()
    SAVE["best"] = max(SAVE.get("best", 0), game.best)
    write_save(SAVE)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
