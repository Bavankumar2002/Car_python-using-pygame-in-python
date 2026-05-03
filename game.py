import pygame
import random
import math
import sys
import os

pygame.init()
pygame.mixer.init()

# ── Screen & constants ──────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 650
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🏎  TURBO BLAZE RACING")
clock = pygame.time.Clock()

# ── Colours ─────────────────────────────────────────────────────────────────
BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (80,  80,  80)
D_GRAY  = (50,  50,  50)
ASPHALT = (35,  35,  40)
L_ASPH  = (55,  55,  62)
YELLOW  = (255, 215,   0)
RED     = (220,  30,  30)
GREEN   = (30,  200,  80)
BLUE    = (30,  80,  220)
CYAN    = (0,  220, 220)
ORANGE  = (255, 120,   0)
PINK    = (255,  50, 150)
LIME    = (160, 255,   0)
PURPLE  = (140,  40, 220)
SKY_TOP = (10,   20,  60)
SKY_BOT = (20,   60, 120)
ROAD_L  = (60,  60,  70)
STRIPE  = (230, 190,   0)
GRASS_D = (20,  80,  20)
GRASS_L = (30, 110,  30)
NEON_R  = (255,  30,  80)
NEON_B  = (30,  80, 255)

# ── Road geometry ───────────────────────────────────────────────────────────
ROAD_LEFT  = 180
ROAD_RIGHT = 720
ROAD_W     = ROAD_RIGHT - ROAD_LEFT
LANE_W     = ROAD_W // 4   # 4 lanes
LANES      = [ROAD_LEFT + LANE_W * i + LANE_W // 2 for i in range(4)]

# ── Helpers ──────────────────────────────────────────────────────────────────

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i]-c1[i])*t) for i in range(3))

def draw_rounded_rect(surf, color, rect, r=12, border=0, border_color=BLACK):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if border:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=r)

# ── Fonts ────────────────────────────────────────────────────────────────────
try:
    FONT_BIG   = pygame.font.SysFont("impact", 72)
    FONT_MED   = pygame.font.SysFont("impact", 36)
    FONT_SM    = pygame.font.SysFont("impact", 24)
    FONT_TINY  = pygame.font.SysFont("impact", 18)
    FONT_HUD   = pygame.font.SysFont("consolas", 22, bold=True)
except:
    FONT_BIG  = pygame.font.Font(None, 80)
    FONT_MED  = pygame.font.Font(None, 40)
    FONT_SM   = pygame.font.Font(None, 28)
    FONT_TINY = pygame.font.Font(None, 20)
    FONT_HUD  = pygame.font.Font(None, 24)

# ══════════════════════════════════════════════════════════════════════════════
# PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=4):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life  = self.max_life = life
        self.size  = size

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.15          # gravity
        self.vx *= 0.97
        self.life -= 1

    def draw(self, surf):
        alpha = self.life / self.max_life
        r = max(1, int(self.size * alpha))
        c = lerp_color(self.color, BLACK, 1 - alpha)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r)

    @property
    def alive(self): return self.life > 0

particles = []

def spawn_exhaust(x, y, speed, color=(80,80,80)):
    for _ in range(2):
        particles.append(Particle(
            x + random.uniform(-3,3), y,
            random.uniform(-1,1), random.uniform(-1, -0.3)*speed*0.08,
            color, random.randint(18, 30), random.randint(3,7)
        ))

def spawn_crash(x, y):
    for _ in range(40):
        a = random.uniform(0, 2*math.pi)
        s = random.uniform(2, 8)
        particles.append(Particle(
            x, y, math.cos(a)*s, math.sin(a)*s,
            random.choice([YELLOW, ORANGE, RED, WHITE]),
            random.randint(25, 50), random.randint(3,8)
        ))

def spawn_skid(x, y):
    for _ in range(6):
        particles.append(Particle(
            x+random.uniform(-5,5), y+random.uniform(-2,2),
            random.uniform(-2,2), random.uniform(-1,1),
            (30,30,30), random.randint(10,20), random.randint(2,5)
        ))

# ══════════════════════════════════════════════════════════════════════════════
# CAR DRAWING (detailed, no sprites needed)
# ══════════════════════════════════════════════════════════════════════════════
def draw_car(surf, x, y, color, accent, scale=1.0, glow=False):
    """Draw a detailed top-down car."""
    W = int(36 * scale)
    H = int(64 * scale)
    cx, cy = int(x), int(y)

    if glow:
        gsurf = pygame.Surface((W+30, H+30), pygame.SRCALPHA)
        pygame.draw.ellipse(gsurf, (*color[:3], 60), (10, 10, W+10, H+10))
        surf.blit(gsurf, (cx - W//2 - 15, cy - H//2 - 15))

    # Shadow
    shadow = pygame.Surface((W+8, H+8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0,0,0,80), (4, 4, W, H))
    surf.blit(shadow, (cx - W//2 - 2, cy - H//2 + 6))

    # Body
    body_rect = pygame.Rect(cx - W//2, cy - H//2, W, H)
    pygame.draw.rect(surf, color, body_rect, border_radius=int(10*scale))

    # Cabin
    cab_w = int(W * 0.7); cab_h = int(H * 0.38)
    cab_rect = pygame.Rect(cx - cab_w//2, cy - cab_h//2 - int(4*scale), cab_w, cab_h)
    pygame.draw.rect(surf, lerp_color(color, WHITE, 0.4), cab_rect, border_radius=int(7*scale))

    # Windshield
    ws_w = int(cab_w * 0.8); ws_h = int(cab_h * 0.5)
    pygame.draw.rect(surf, (160,220,255,200),
        (cx - ws_w//2, cy - cab_h//2 - int(4*scale), ws_w, ws_h),
        border_radius=int(4*scale))

    # Headlights
    hl = int(7*scale)
    for dx in [-W//2+int(4*scale), W//2-int(4*scale)-hl]:
        pygame.draw.rect(surf, (255,255,180), (cx+dx - (W//2 - int(4*scale) - hl if dx<0 else 0),
            cy - H//2 + int(3*scale), hl, int(5*scale)), border_radius=2)

    # Taillights
    for dx in [-1, 1]:
        tx = cx + dx * (W//2 - int(5*scale))
        ty = cy + H//2 - int(8*scale)
        pygame.draw.rect(surf, RED, (tx - int(3*scale), ty, int(6*scale), int(5*scale)), border_radius=2)

    # Wheels
    ww = int(8*scale); wh = int(12*scale)
    for wx in [cx - W//2 - ww//2, cx + W//2 - ww//2]:
        for wy in [cy - H//3, cy + H//3 - wh//2]:
            pygame.draw.rect(surf, (20,20,20), (wx, wy, ww, wh), border_radius=3)
            pygame.draw.rect(surf, (80,80,80), (wx+1, wy+2, ww-2, wh-4), border_radius=2)

    # Racing stripe
    stripe_w = int(4*scale)
    pygame.draw.rect(surf, accent,
        (cx - stripe_w//2, cy - H//2 + int(4*scale), stripe_w, H - int(8*scale)),
        border_radius=2)

    # Number (accent colored)
    num_surf = FONT_TINY.render("01", True, accent)
    surf.blit(num_surf, (cx - num_surf.get_width()//2, cy + int(5*scale)))

# ══════════════════════════════════════════════════════════════════════════════
# PLAYER CAR
# ══════════════════════════════════════════════════════════════════════════════
class PlayerCar:
    COLOR  = (220,  30,  50)
    ACCENT = YELLOW
    W, H   = 36, 64

    def __init__(self):
        self.x    = LANES[1]
        self.y    = HEIGHT - 130
        self.speed      = 0.0      # forward speed (scroll speed)
        self.max_speed  = 14.0
        self.accel      = 0.25
        self.brake_dec  = 0.5
        self.coast_dec  = 0.08
        self.lateral    = 0.0     # left/right velocity
        self.lat_max    = 5.5
        self.lat_accel  = 0.7
        self.lat_fric   = 0.75
        self.invincible = 0       # frames of invincibility after crash
        self.crashed    = False
        self.crash_timer= 0
        self.lives      = 3
        self.turbo      = 100.0   # 0-100
        self.turbo_on   = False

    @property
    def rect(self):
        return pygame.Rect(self.x - self.W//2 + 8, self.y - self.H//2 + 8,
                           self.W - 16, self.H - 16)

    def handle_input(self, keys):
        if self.crashed: return
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed = min(self.speed + self.accel, self.max_speed)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = max(self.speed - self.brake_dec, 0)
        else:
            self.speed = max(self.speed - self.coast_dec, 0)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.lateral = max(self.lateral - self.lat_accel, -self.lat_max)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.lateral = min(self.lateral + self.lat_accel, self.lat_max)
        else:
            self.lateral *= self.lat_fric

        # Turbo boost
        self.turbo_on = (keys[pygame.K_SPACE] and self.turbo > 0 and
                         self.speed > self.max_speed * 0.5)
        if self.turbo_on:
            self.speed = min(self.speed + 0.4, self.max_speed * 1.4)
            self.turbo = max(self.turbo - 1.5, 0)
        else:
            self.turbo = min(self.turbo + 0.3, 100)

    def update(self):
        if self.crashed:
            self.crash_timer -= 1
            if self.crash_timer <= 0:
                self.crashed = False
                self.invincible = 120
                self.speed = 0
            return

        self.x = max(ROAD_LEFT + self.W//2 + 6,
                     min(ROAD_RIGHT - self.W//2 - 6, self.x + self.lateral))

        if self.invincible > 0:
            self.invincible -= 1

        # Exhaust
        col = (NEON_R if self.turbo_on else (70,70,70))
        spawn_exhaust(self.x, self.y + self.H//2, self.speed, col)
        if self.turbo_on:
            spawn_exhaust(self.x - 6, self.y + self.H//2, self.speed, ORANGE)
            spawn_exhaust(self.x + 6, self.y + self.H//2, self.speed, YELLOW)

    def crash(self):
        if self.invincible > 0 or self.crashed: return
        spawn_crash(self.x, self.y)
        self.crashed    = True
        self.crash_timer= 80
        self.speed      = 0
        self.lateral    = 0
        self.lives     -= 1

    def draw(self, surf):
        if self.crashed:
            t = self.crash_timer / 80
            if int(t*10) % 2 == 0:
                draw_car(surf, self.x, self.y, (180,60,60), YELLOW, glow=True)
            return
        if self.invincible > 0 and self.invincible % 6 < 3:
            return
        draw_car(surf, self.x, self.y, self.COLOR, self.ACCENT,
                 glow=self.turbo_on)

# ══════════════════════════════════════════════════════════════════════════════
# ENEMY CAR
# ══════════════════════════════════════════════════════════════════════════════
ENEMY_CONFIGS = [
    ((40, 100, 220), CYAN,   "02"),
    ((30, 180,  80), LIME,   "03"),
    ((180, 40, 200), PINK,   "04"),
    ((220, 120, 20), ORANGE, "05"),
    ((20,  80, 160), WHITE,  "06"),
]

class EnemyCar:
    W, H = 36, 64

    def __init__(self, scroll_speed, difficulty):
        cfg = random.choice(ENEMY_CONFIGS)
        self.color, self.accent = cfg[0], cfg[1]
        lane = random.randint(0, 3)
        self.x = LANES[lane]
        self.y = -self.H
        self.lane_target = lane
        # relative speed to player
        self.rel_speed = random.uniform(-1.5, 1.5) * difficulty
        self.lat_vel   = 0.0
        self.change_timer = random.randint(60, 200)

    @property
    def rect(self):
        return pygame.Rect(self.x - self.W//2 + 8, self.y - self.H//2 + 8,
                           self.W - 16, self.H - 16)

    def update(self, scroll_speed):
        self.y += scroll_speed + self.rel_speed
        self.change_timer -= 1
        if self.change_timer <= 0:
            self.lane_target = random.randint(0, 3)
            self.change_timer = random.randint(60, 200)
        target_x = LANES[self.lane_target]
        self.x += (target_x - self.x) * 0.04
        spawn_exhaust(self.x, self.y - self.H//2, 3, (60,60,60))

    def draw(self, surf):
        draw_car(surf, self.x, self.y, self.color, self.accent)

    @property
    def off_screen(self):
        return self.y > HEIGHT + self.H + 50

# ══════════════════════════════════════════════════════════════════════════════
# ROAD MARKINGS & ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════
class RoadLine:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, speed):
        self.y += speed
        if self.y > HEIGHT + 30:
            self.y -= HEIGHT + 60

    def draw(self, surf):
        pygame.draw.rect(surf, STRIPE, (self.x - 3, int(self.y), 6, 30), border_radius=2)

class Scenery:
    """Trees / poles on the sides."""
    def __init__(self):
        side = random.choice([-1, 1])
        if side == -1:
            self.x = random.randint(10, ROAD_LEFT - 20)
        else:
            self.x = random.randint(ROAD_RIGHT + 20, WIDTH - 10)
        self.y = random.randint(-HEIGHT, 0)
        self.kind = random.choice(["tree", "pole", "bush"])
        self.size = random.randint(12, 22)
        self.color = random.choice([GRASS_D, GRASS_L, (0,100,0), (20,60,20)])

    def update(self, speed):
        self.y += speed * 1.05
        return self.y < HEIGHT + 40

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        if self.kind == "tree":
            pygame.draw.rect(surf, (80,50,20), (x-3, y, 6, 16))
            pygame.draw.circle(surf, self.color, (x, y), self.size)
            pygame.draw.circle(surf, lerp_color(self.color, WHITE, 0.2),
                               (x-3, y-3), self.size//3)
        elif self.kind == "pole":
            pygame.draw.rect(surf, (100,100,110), (x-2, y-30, 4, 30))
            pygame.draw.circle(surf, YELLOW, (x, y-32), 5)
        else:
            pygame.draw.ellipse(surf, self.color, (x-self.size, y-8, self.size*2, 14))

# ══════════════════════════════════════════════════════════════════════════════
# ROAD SCROLL BACKGROUND
# ══════════════════════════════════════════════════════════════════════════════
def build_road_lines():
    lines = []
    # Lane dividers (3 internal lines)
    for li in range(1, 4):
        lx = ROAD_LEFT + LANE_W * li
        for j in range(0, HEIGHT + 60, 60):
            lines.append(RoadLine(lx, j))
    return lines

# ══════════════════════════════════════════════════════════════════════════════
# HUD DRAWING
# ══════════════════════════════════════════════════════════════════════════════
def draw_hud(surf, player, score, hi, level, elapsed):
    # Speed bar
    spd_pct = player.speed / player.max_speed
    bar_rect = pygame.Rect(20, HEIGHT - 90, 160, 20)
    draw_rounded_rect(surf, D_GRAY, bar_rect, r=6)
    fill = pygame.Rect(22, HEIGHT-88, int(156*spd_pct), 16)
    spd_col = lerp_color(GREEN, RED, spd_pct)
    if player.turbo_on: spd_col = YELLOW
    draw_rounded_rect(surf, spd_col, fill, r=5)
    lbl = FONT_HUD.render(f"SPEED  {int(player.speed*20)} km/h", True, WHITE)
    surf.blit(lbl, (20, HEIGHT-110))

    # Turbo bar
    turbo_rect = pygame.Rect(20, HEIGHT - 50, 160, 16)
    draw_rounded_rect(surf, D_GRAY, turbo_rect, r=5)
    t_fill = pygame.Rect(22, HEIGHT-48, int(156*player.turbo/100), 12)
    t_col = CYAN if player.turbo_on else BLUE
    draw_rounded_rect(surf, t_col, t_fill, r=4)
    tlbl = FONT_HUD.render("TURBO [SPACE]", True, CYAN if player.turbo > 20 else GRAY)
    surf.blit(tlbl, (20, HEIGHT-68))

    # Lives
    lv_lbl = FONT_SM.render("LIVES:", True, WHITE)
    surf.blit(lv_lbl, (20, 20))
    for i in range(3):
        col = RED if i < player.lives else (50,50,50)
        draw_car_icon(surf, 110 + i*28, 30, col)

    # Score
    sc_lbl = FONT_HUD.render(f"SCORE  {score:07d}", True, YELLOW)
    surf.blit(sc_lbl, (WIDTH//2 - sc_lbl.get_width()//2, 15))
    hi_lbl = FONT_TINY.render(f"BEST {hi:07d}", True, GRAY)
    surf.blit(hi_lbl, (WIDTH//2 - hi_lbl.get_width()//2, 42))

    # Level / time
    lvl_lbl = FONT_HUD.render(f"LVL {level}", True, LIME)
    surf.blit(lvl_lbl, (WIDTH - 120, 15))
    mins = elapsed // 3600 // 60; secs = (elapsed // 60) % 60
    t_surf = FONT_TINY.render(f"{mins:02d}:{secs:02d}", True, WHITE)
    surf.blit(t_surf, (WIDTH - t_surf.get_width() - 15, 42))

def draw_car_icon(surf, x, y, color):
    pygame.draw.rect(surf, color, (x-7, y-12, 14, 24), border_radius=4)
    pygame.draw.rect(surf, lerp_color(color,WHITE,0.4), (x-5, y-10, 10, 12), border_radius=3)

# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND DRAWING
# ══════════════════════════════════════════════════════════════════════════════
def draw_background(surf, scroll):
    # Sky gradient
    for y in range(200):
        t = y / 200
        c = lerp_color(SKY_TOP, SKY_BOT, t)
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))

    # Grass
    pygame.draw.rect(surf, GRASS_D, (0, 200, WIDTH, HEIGHT))
    # Animated grass stripes
    stripe_off = int(scroll * 0.3) % 40
    for x in range(-40, WIDTH, 40):
        pygame.draw.rect(surf, GRASS_L, (x + stripe_off, 200, 20, HEIGHT), border_radius=0)

    # Road surface
    pygame.draw.rect(surf, ASPHALT, (ROAD_LEFT, 200, ROAD_W, HEIGHT))
    # Road texture shading
    for i in range(0, ROAD_W, 40):
        shade = L_ASPH if (i//40)%2==0 else ASPHALT
        pygame.draw.rect(surf, shade, (ROAD_LEFT+i, 200, 40, HEIGHT))

    # Kerbs (red-white alternating) on road edges
    kerb_h = 18
    for ky in range(200, HEIGHT + kerb_h, kerb_h*2):
        ky_off = int(scroll) % (kerb_h*2)
        y1 = ky - ky_off
        pygame.draw.rect(surf, RED,   (ROAD_LEFT-12, y1,          12, kerb_h))
        pygame.draw.rect(surf, WHITE, (ROAD_LEFT-12, y1+kerb_h,   12, kerb_h))
        pygame.draw.rect(surf, RED,   (ROAD_RIGHT,   y1,          12, kerb_h))
        pygame.draw.rect(surf, WHITE, (ROAD_RIGHT,   y1+kerb_h,   12, kerb_h))

    # Horizon line
    pygame.draw.line(surf, (40,60,80), (0, 200), (WIDTH, 200), 3)

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN STATES
# ══════════════════════════════════════════════════════════════════════════════
def title_screen(hi_score):
    t = 0
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN: return
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        t += 1
        # Animated background
        screen.fill(BLACK)
        for _ in range(2):
            particles.append(Particle(
                random.randint(ROAD_LEFT, ROAD_RIGHT),
                HEIGHT + 10,
                random.uniform(-1,1), random.uniform(-4,-1),
                random.choice([YELLOW, ORANGE, RED]),
                random.randint(30,60), random.randint(3,8)
            ))
        for p in particles[:]: p.update(); p.draw(screen)
        particles[:] = [p for p in particles if p.alive]

        # Road preview
        pygame.draw.rect(screen, ASPHALT, (ROAD_LEFT, 0, ROAD_W, HEIGHT))

        # Neon glow title
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
            s = FONT_BIG.render("TURBO BLAZE", True, NEON_R)
            screen.blit(s, (WIDTH//2 - s.get_width()//2 + ox, 100+oy))
        s = FONT_BIG.render("TURBO BLAZE", True, YELLOW)
        screen.blit(s, (WIDTH//2 - s.get_width()//2, 100))

        sub = FONT_MED.render("RACING", True, CYAN)
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 175))

        # Demo cars
        for i, lane in enumerate(LANES):
            cfg = ENEMY_CONFIGS[i % len(ENEMY_CONFIGS)]
            y_pos = 280 + i * 20 + math.sin(t*0.05 + i)*8
            draw_car(screen, lane, y_pos, cfg[0], cfg[1], scale=0.9)

        blink = FONT_MED.render("PRESS  ENTER  TO  RACE", True,
                                 WHITE if (t//30)%2==0 else GRAY)
        screen.blit(blink, (WIDTH//2 - blink.get_width()//2, 480))

        controls = [
            "↑/W  Accelerate     ↓/S  Brake",
            "←/A  Left     →/D  Right",
            "SPACE  Turbo Boost!",
        ]
        for i, c in enumerate(controls):
            cs = FONT_TINY.render(c, True, (160,160,200))
            screen.blit(cs, (WIDTH//2 - cs.get_width()//2, 540 + i*22))

        hi_s = FONT_SM.render(f"BEST SCORE: {hi_score:07d}", True, YELLOW)
        screen.blit(hi_s, (WIDTH//2 - hi_s.get_width()//2, 430))

        pygame.display.flip()
        clock.tick(FPS)

def game_over_screen(score, hi_score, win=False):
    t = 0
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN: return True
                if e.key == pygame.K_ESCAPE: return False

        t += 1
        screen.fill((10,0,0))
        pygame.draw.rect(screen, (30,0,0), (ROAD_LEFT, 0, ROAD_W, HEIGHT))

        title_col = GREEN if win else RED
        title_txt = "VICTORY!" if win else "GAME OVER"
        for ox,oy in [(-2,0),(2,0),(0,-2),(0,2)]:
            s = FONT_BIG.render(title_txt, True, BLACK)
            screen.blit(s, (WIDTH//2 - s.get_width()//2+ox, 150+oy))
        s = FONT_BIG.render(title_txt, True, title_col)
        screen.blit(s, (WIDTH//2 - s.get_width()//2, 150))

        sc = FONT_MED.render(f"SCORE: {score:07d}", True, YELLOW)
        screen.blit(sc, (WIDTH//2 - sc.get_width()//2, 260))

        hi = FONT_SM.render(f"BEST:  {hi_score:07d}", True, CYAN)
        screen.blit(hi, (WIDTH//2 - hi.get_width()//2, 310))

        if score >= hi_score:
            nw = FONT_SM.render("🏆  NEW RECORD!  🏆", True, YELLOW)
            screen.blit(nw, (WIDTH//2 - nw.get_width()//2, 355))

        blink = FONT_SM.render("ENTER = Play Again    ESC = Quit",
                                True, WHITE if (t//25)%2==0 else GRAY)
        screen.blit(blink, (WIDTH//2 - blink.get_width()//2, 430))

        pygame.display.flip()
        clock.tick(FPS)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN GAME LOOP
# ══════════════════════════════════════════════════════════════════════════════
def game_loop():
    player      = PlayerCar()
    road_lines  = build_road_lines()
    enemies     = []
    scenery     = [Scenery() for _ in range(18)]
    particles.clear()

    score        = 0
    hi_score     = 0          # loaded per session
    level        = 1
    scroll       = 0.0
    spawn_timer  = 0
    elapsed      = 0
    shake        = 0          # screen shake frames

    def get_scroll_speed():
        return player.speed * 0.95 if not player.crashed else 0

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return score, False

        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update()

        sp = get_scroll_speed()
        scroll += sp
        elapsed += 1

        # Level up every 30 seconds
        level = 1 + elapsed // (30 * FPS)
        difficulty = 1 + (level - 1) * 0.4

        # Score
        score += int(sp * 2)

        # Spawn enemies
        spawn_timer -= 1
        if spawn_timer <= 0:
            if len(enemies) < 6 + level:
                enemies.append(EnemyCar(sp, difficulty))
            spawn_timer = max(40, 90 - level*8)

        # Update enemies
        for en in enemies:
            en.update(sp)
            if player.rect.colliderect(en.rect) and not player.crashed:
                player.crash()
                shake = 20
                spawn_skid(player.x, player.y)

        enemies = [e for e in enemies if not e.off_screen]

        # Update road lines
        for rl in road_lines:
            rl.update(sp)

        # Update scenery
        new_sc = []
        for s in scenery:
            if s.update(sp):
                new_sc.append(s)
        scenery = new_sc
        while len(scenery) < 20:
            sc = Scenery()
            sc.y = random.randint(-HEIGHT, -50)
            scenery.append(sc)

        # Update particles
        for p in particles: p.update()
        particles[:] = [p for p in particles if p.alive]

        # Screen shake
        ox = oy = 0
        if shake > 0:
            ox = random.randint(-6, 6)
            oy = random.randint(-6, 6)
            shake -= 1

        # ── DRAW ──────────────────────────────────────────────────────────
        draw_surf = pygame.Surface((WIDTH, HEIGHT))
        draw_background(draw_surf, scroll)

        # Scenery (behind road)
        for s in scenery:
            s.draw(draw_surf)

        # Road lines
        for rl in road_lines:
            rl.draw(draw_surf)

        # Enemies (behind player)
        for en in enemies:
            en.draw(draw_surf)

        # Particles
        for p in particles:
            p.draw(draw_surf)

        # Player
        player.draw(draw_surf)

        # HUD
        draw_hud(draw_surf, player, score, max(score,0), level, elapsed)

        # Level up flash
        if elapsed % (30*FPS) in range(1, 90):
            lv_s = FONT_MED.render(f"LEVEL  {level}!", True, LIME)
            draw_surf.blit(lv_s, (WIDTH//2-lv_s.get_width()//2, HEIGHT//2-20))

        screen.blit(draw_surf, (ox, oy))
        pygame.display.flip()
        clock.tick(FPS)

        # Game over?
        if player.lives <= 0:
            return score, False

    return score, False

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    hi_score = 0
    while True:
        title_screen(hi_score)
        score, win = game_loop()
        hi_score = max(hi_score, score)
        play_again = game_over_screen(score, hi_score, win)
        if not play_again:
            break

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()