"""Zektzerite Zig — neon light-cycle arcade for ElbowOS. Python 3 + pygame.

Steer a lime bike, ribbon the grid, snatch gold prisms, and box coral/ice rivals.
Arrow keys or A/D turn. R restarts.
"""
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/ZEKTZERITE_ZIG_ElbowOS.mp4")
COLS, ROWS, CELL = 15, 26, 58
OX = (W - COLS * CELL) // 2
OY = 250
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # R D L U
WINE = (22, 6, 28)
GRID = (78, 36, 52)
LIME = (190, 255, 70)
CORAL = (255, 96, 78)
ICE = (90, 220, 255)
GOLD = (255, 206, 64)
INK = (12, 4, 18)
CREAM = (255, 236, 214)


class Bike:
    def __init__(self, x, y, d, color, name):
        self.x, self.y, self.d = x, y, d
        self.color, self.name = color, name
        self.alive = True
        self.wait = 0
        self.trail = []

    def reset(self, x, y, d):
        self.x, self.y, self.d = x, y, d
        self.alive = True
        self.wait = 0
        self.trail = [(x, y)]


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not RECORD else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption("Zektzerite Zig")
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 40, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 32, bold=True)
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        random.seed(11 if RECORD or not PLAY else None)
        self.tick = 0
        self.score = 0
        self.prisms = 0
        self.flash = 0
        self.walls = set()
        for x in range(5, 10):
            self.walls.add((x, 12))
        for y in range(8, 13):
            self.walls.add((3, y))
            self.walls.add((11, y))
        self.occ = set(self.walls)
        self.player = Bike(7, 22, 3, LIME, "YOU")
        self.rivals = [Bike(2, 4, 1, CORAL, "CORAL"), Bike(12, 4, 1, ICE, "ICE")]
        for b in [self.player] + self.rivals:
            b.trail = [(b.x, b.y)]
            self.occ.add((b.x, b.y))
        self.nodes = []
        self.spawn_nodes(5)
        self.sparks = []

    def spawn_nodes(self, n):
        while len(self.nodes) < n:
            c = (random.randrange(COLS), random.randrange(ROWS))
            if c not in self.occ and c not in self.nodes:
                self.nodes.append(c)

    def blocked(self, x, y):
        return not (0 <= x < COLS and 0 <= y < ROWS) or (x, y) in self.occ

    def open_ray(self, x, y, d):
        dx, dy = DIRS[d]
        n = 0
        for _ in range(8):
            x, y = x + dx, y + dy
            if self.blocked(x, y):
                break
            n += 1
        return n

    def steer(self, bike, toward=None):
        options = []
        for turn in (0, -1, 1):
            nd = (bike.d + turn) % 4
            dx, dy = DIRS[nd]
            nx, ny = bike.x + dx, bike.y + dy
            if not self.blocked(nx, ny):
                options.append((self.open_ray(bike.x, bike.y, nd), turn, nd, nx, ny))
        if not options:
            return
        if toward:
            tx, ty = toward
            options.sort(key=lambda o: (-o[0], abs(o[3] - tx) + abs(o[4] - ty)))
        else:
            options.sort(key=lambda o: -o[0])
        best = options[0]
        if best[1] != 0 and (best[0] >= 2 or self.open_ray(bike.x, bike.y, bike.d) < 2):
            bike.d = best[2]

    def step_bike(self, bike):
        if not bike.alive:
            bike.wait -= 1
            if bike.wait <= 0:
                self.respawn(bike)
            return
        dx, dy = DIRS[bike.d]
        nx, ny = bike.x + dx, bike.y + dy
        if self.blocked(nx, ny):
            bike.alive = False
            bike.wait = 18
            self.flash = 8
            self.sparks.append([OX + bike.x * CELL + CELL // 2, OY + bike.y * CELL + CELL // 2, bike.color, 14])
            return
        bike.x, bike.y = nx, ny
        bike.trail.append((nx, ny))
        self.occ.add((nx, ny))
        if (nx, ny) in self.nodes:
            self.nodes.remove((nx, ny))
            self.score += 80
            self.prisms += 1
            self.spawn_nodes(5)
            self.sparks.append([OX + nx * CELL + CELL // 2, OY + ny * CELL + CELL // 2, GOLD, 16])

    def respawn(self, bike):
        for _ in range(40):
            x, y = random.randrange(1, COLS - 1), random.randrange(1, ROWS - 1)
            if (x, y) not in self.occ and not self.blocked(x, y - 1):
                bike.reset(x, y, 3)
                self.occ.add((x, y))
                return
        bike.wait = 10

    def update(self, turn=0):
        self.tick += 1
        if turn and self.player.alive:
            self.player.d = (self.player.d + turn) % 4
        if self.tick % 3 == 0:
            goal = min(self.nodes, key=lambda n: abs(n[0] - self.player.x) + abs(n[1] - self.player.y), default=None)
            if turn == 0:
                self.steer(self.player, goal)
            for r in self.rivals:
                g = min(self.nodes, key=lambda n: abs(n[0] - r.x) + abs(n[1] - r.y), default=None)
                self.steer(r, g)
            self.step_bike(self.player)
            for r in self.rivals:
                self.step_bike(r)
            if self.player.alive:
                self.score += 1
        self.sparks = [s for s in self.sparks if s[3] > 0]
        for s in self.sparks:
            s[3] -= 1
        if self.flash:
            self.flash -= 1

    def cell_rect(self, x, y, pad=4):
        return pygame.Rect(OX + x * CELL + pad, OY + y * CELL + pad, CELL - pad * 2, CELL - pad * 2)

    def draw(self, surf):
        surf.fill(WINE)
        for i in range(8):
            pygame.draw.circle(surf, (40 + i * 4, 10, 36), (W // 2, 420 + i * 90), 520 - i * 40, 2)
        pygame.draw.rect(surf, (48, 16, 40), (OX - 14, OY - 14, COLS * CELL + 28, ROWS * CELL + 28), border_radius=18)
        pygame.draw.rect(surf, INK, (OX - 6, OY - 6, COLS * CELL + 12, ROWS * CELL + 12), border_radius=12)
        for x in range(COLS):
            for y in range(ROWS):
                pygame.draw.rect(surf, GRID, self.cell_rect(x, y, 8), 1, border_radius=4)
        for x, y in self.walls:
            pygame.draw.rect(surf, (120, 48, 72), self.cell_rect(x, y, 6), border_radius=6)
        for bike in self.rivals + [self.player]:
            col = bike.color
            for i, (x, y) in enumerate(bike.trail[-48:]):
                shade = tuple(max(0, c - 80 + i) for c in col)
                pygame.draw.rect(surf, shade, self.cell_rect(x, y, 10), border_radius=8)
            if bike.alive:
                cx = OX + bike.x * CELL + CELL // 2
                cy = OY + bike.y * CELL + CELL // 2
                dx, dy = DIRS[bike.d]
                nose = (cx + dx * 22, cy + dy * 22)
                wing = (-dy, dx)
                pts = [nose, (cx - dx * 16 + wing[0] * 16, cy - dy * 16 + wing[1] * 16),
                       (cx - dx * 16 - wing[0] * 16, cy - dy * 16 - wing[1] * 16)]
                pygame.draw.polygon(surf, col, pts)
                pygame.draw.circle(surf, CREAM, (int(cx), int(cy)), 6)
        for x, y in self.nodes:
            r = self.cell_rect(x, y, 14)
            pygame.draw.polygon(surf, GOLD, [(r.centerx, r.top), (r.right, r.centery), (r.centerx, r.bottom), (r.left, r.centery)])
        for sx, sy, col, life in self.sparks:
            pygame.draw.circle(surf, col, (int(sx), int(sy)), 8 + life)
        title = self.font.render("ZEKTZERITE ZIG", True, LIME)
        surf.blit(title, title.get_rect(center=(W // 2, 92)))
        sub = self.mid.render(f"SCORE {self.score}   PRISMS {self.prisms}", True, GOLD)
        surf.blit(sub, sub.get_rect(center=(W // 2, 164)))
        tag = self.small.render("x.com/ElbowOS", True, ICE)
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 78)))
        hint = self.small.render("LIGHT-CYCLE  ·  A/D TURN", True, CREAM)
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 128)))

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
            "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        for _ in range(frames):
            self.update(0)
            self.draw(self.screen)
            raw = pygame.image.tobytes(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                err = proc.stderr.read().decode("utf-8", "ignore")
                raise SystemExit(f"ffmpeg pipe broke:\n{err[-1500:]}")
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

    def play_interactive(self):
        running = True
        while running:
            turn = 0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_a, pygame.K_LEFT):
                        turn = -1
                    elif ev.key in (pygame.K_d, pygame.K_RIGHT):
                        turn = 1
                    elif ev.key == pygame.K_r:
                        self.reset()
                    elif ev.key == pygame.K_ESCAPE:
                        running = False
            self.update(turn)
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
