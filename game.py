"""Mystic World: original artwork, repaired combat and an expandable arena game."""
from pathlib import Path
import argparse
import heapq
import json
import math
import os
import random
import pygame as pg

ROOT = Path(__file__).resolve().parent
V = pg.Vector2
CELL = 40


def move_actor(actor, displacement, walls, bounds):
    """Resolve each axis in small steps so even dashes cannot cross thin walls."""
    steps = max(1, math.ceil(max(abs(displacement.x), abs(displacement.y)) / 8))
    step = displacement / steps
    for _ in range(steps):
        for axis in (0, 1):
            actor.pos[axis] += step[axis]
            actor.rect.center = round(actor.pos.x), round(actor.pos.y)
            for wall in walls:
                if actor.rect.colliderect(wall):
                    if axis == 0:
                        if step.x > 0: actor.rect.right = wall.left
                        elif step.x < 0: actor.rect.left = wall.right
                    else:
                        if step.y > 0: actor.rect.bottom = wall.top
                        elif step.y < 0: actor.rect.top = wall.bottom
                    actor.pos.update(actor.rect.center)
            actor.rect.clamp_ip(bounds)
            actor.pos.update(actor.rect.center)


class Actor:
    def __init__(self, pos, health=100):
        self.pos = V(pos)
        self.rect = pg.Rect(0, 0, 24, 26)
        self.rect.center = self.pos
        self.health = health
        self.max_health = health
        self.facing = V(0, 1)
        self.anim = 0.0
        self.flash = 0.0
        self.path = []
        self.repath = 0.0


class Game:
    def __init__(self, seed=None):
        pg.init()
        self.screen = pg.display.set_mode((1100, 780), pg.RESIZABLE)
        pg.display.set_caption('Mystic World — Arcane Survival')
        self.clock = pg.time.Clock()
        self.font = pg.font.Font(None, 25)
        self.big = pg.font.Font(None, 65)
        self.rng = random.Random(seed)
        self.world = pg.image.load(str(ROOT / 'assets/world.jpeg')).convert()
        data = json.loads((ROOT / 'assets/world.json').read_text())
        self.bounds = pg.Rect(0, 0, data['width'], data['height'])
        self.walls = []
        self.spawn_points = []
        self.start = V(1432, 1968)
        for o in data['objects']:
            p = V(float(o['x']), float(o['y']))
            if o['name'] == 'wall':
                self.walls.append(pg.Rect(round(p.x), round(p.y), max(1, round(float(o.get('width', 1)))), max(1, round(float(o.get('height', 1))))))
            elif o['name'] == 'player': self.start = p
            elif o['name'] == 'nme': self.spawn_points.append(p)
        self.frames = {}
        for name in ('count', 'countattack', 'g', 'force'):
            sheet = pg.image.load(str(ROOT / f'assets/{name}.png')).convert_alpha()
            self.frames[name] = [[sheet.subsurface((x * 32, y * 36, 32, 36)).copy() for x in range(3)] for y in range(4)]
        self.mini = pg.transform.smoothscale(self.world, (170, 170))
        self.blocked = set()
        for y in range(self.bounds.height // CELL):
            for x in range(self.bounds.width // CELL):
                r = pg.Rect(x * CELL - 12, y * CELL - 13, CELL + 24, CELL + 26)
                if any(r.colliderect(w) for w in self.walls): self.blocked.add((x, y))
        config_root = Path(os.environ.get('APPDATA', str(Path.home() / '.config')))
        self.save_path = config_root / 'mystic_world' / 'scores.json'
        self.best = 0
        self.save_notice = ''
        try: self.best = max(0, int(json.loads(self.save_path.read_text()).get('best', 0)))
        except (OSError, ValueError, TypeError): pass
        self.debug = False
        self.minimap = True
        self.running = True
        self.reset()
        self.state = 'menu'

    def free(self, pos):
        r = pg.Rect(0, 0, 26, 28)
        r.center = pos
        return self.bounds.contains(r) and not any(r.colliderect(w) for w in self.walls)

    def safe_pos(self, preferred=None, far=False):
        if preferred is not None and self.free(preferred): return V(preferred)
        for _ in range(2000):
            p = V(self.rng.randrange(50, 3150), self.rng.randrange(50, 3150))
            if self.free(p) and (not far or p.distance_to(self.player.pos) > 360): return p
        return self.start.copy()

    def reset(self):
        self.player = Actor(self.safe_pos(self.start))
        self.enemies = []
        self.shots = []
        self.particles = []
        self.pickups = []
        self.pulses = []
        self.score = 0
        self.wave = 0
        self.elapsed = 0
        self.mana = 100.0
        self.shot_cd = self.dash_cd = self.nova_cd = self.invulnerable = 0.0
        self.dash_left = self.attack_left = 0.0
        self.dash_direction = V(0, 1)
        self.next_wave = 1.0
        self.camera = V()
        self.state = 'playing'
        self.update_camera()

    def spawn_wave(self):
        self.wave += 1
        count = min(4 + self.wave * 2, 30)
        for i in range(count):
            p = self.safe_pos(self.spawn_points[i] if i < len(self.spawn_points) else None, far=True)
            enemy = Actor(p, 45 + min(self.wave, 20) * 5)
            enemy.speed = min(80 + self.wave * 5, 170)
            enemy.repath = self.rng.random()
            self.enemies.append(enemy)
        self.next_wave = 3.0

    def route(self, start, goal):
        a = (int(start.x // CELL), int(start.y // CELL))
        b = (int(goal.x // CELL), int(goal.y // CELL))
        if a == b: return []
        def h(p): return abs(p[0] - b[0]) + abs(p[1] - b[1])
        queue = [(h(a), 0, a)]
        cost = {a: 0}
        came = {}
        end = None
        for _ in range(3500):
            if not queue: break
            _, g, p = heapq.heappop(queue)
            if g != cost.get(p): continue
            if p == b: end = p; break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = p[0] + dx, p[1] + dy
                if not (0 <= q[0] < 80 and 0 <= q[1] < 80): continue
                if q in self.blocked and q != b: continue
                ng = g + 1
                if ng < cost.get(q, 999999):
                    cost[q] = ng; came[q] = p
                    heapq.heappush(queue, (ng + h(q), ng, q))
        if end is None: return []
        result = []
        while end != a:
            result.append(V((end[0] + .5) * CELL, (end[1] + .5) * CELL))
            end = came[end]
        return list(reversed(result))

    def line_clear(self, a, b):
        return not any(w.inflate(26, 28).clipline(a, b) for w in self.walls)

    def fire(self, aim=None):
        if self.shot_cd > 0 or self.mana < 4: return
        direction = V(aim) - self.player.pos if aim is not None else self.player.facing.copy()
        if direction.length_squared() < 1: direction = self.player.facing.copy()
        direction.normalize_ip()
        self.player.facing = direction
        self.shots.append({'pos': self.player.pos.copy(), 'vel': direction * 650, 'life': 1.8})
        self.mana -= 4
        self.shot_cd = .18
        self.attack_left = .16

    def burst(self, pos, color, count=16):
        for _ in range(count):
            v = V(self.rng.uniform(-1, 1), self.rng.uniform(-1, 1)) * self.rng.uniform(50, 180)
            self.particles.append({'pos': V(pos), 'vel': v, 'life': self.rng.uniform(.25, .6), 'color': color})

    def damage_enemy(self, enemy, amount):
        if enemy not in self.enemies: return
        enemy.health -= amount
        enemy.flash = .12
        if enemy.health <= 0:
            self.enemies.remove(enemy)
            self.score += 100
            self.burst(enemy.pos, (255, 160, 65), 24)
            if self.rng.random() < .35:
                self.pickups.append({'pos': enemy.pos.copy(), 'type': self.rng.choice(['health', 'mana']), 'life': 25})

    def nova(self):
        if self.nova_cd > 0 or self.mana < 35: return
        self.mana -= 35
        self.nova_cd = 4
        self.pulses.append([self.player.pos.copy(), .45])
        for e in self.enemies[:]:
            if e.pos.distance_to(self.player.pos) < 170 and self.line_clear(self.player.pos, e.pos):
                self.damage_enemy(e, 80)

    def save_score(self):
        self.best = max(self.best, self.score)
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.save_path.with_suffix('.tmp')
            temp.write_text(json.dumps({'best': self.best}, indent=2))
            temp.replace(self.save_path)
        except OSError: self.save_notice = 'High score could not be saved on this computer.'

    def update_camera(self):
        size = V(self.screen.get_size())
        self.camera = self.player.pos - size / 2
        self.camera.x = max(0, min(self.camera.x, max(0, self.bounds.width - size.x)))
        self.camera.y = max(0, min(self.camera.y, max(0, self.bounds.height - size.y)))

    def update(self, dt, movement=None, shooting=None):
        self.elapsed += dt
        for name in ('shot_cd', 'dash_cd', 'nova_cd', 'invulnerable', 'attack_left'):
            setattr(self, name, max(0, getattr(self, name) - dt))
        self.mana = min(100, self.mana + 14 * dt)
        keys = pg.key.get_pressed()
        if movement is None:
            movement = V(int(keys[pg.K_d] or keys[pg.K_RIGHT]) - int(keys[pg.K_a] or keys[pg.K_LEFT]),
                         int(keys[pg.K_s] or keys[pg.K_DOWN]) - int(keys[pg.K_w] or keys[pg.K_UP]))
        movement = V(movement)
        if movement.length_squared():
            movement.normalize_ip()
            self.player.facing = movement.copy()
            self.player.anim += dt * 10
        if self.dash_left > 0:
            move = self.dash_direction * 720
            self.dash_left = max(0, self.dash_left - dt)
        else: move = movement * 235
        move_actor(self.player, move * dt, self.walls, self.bounds)
        self.update_camera()
        if shooting is None:
            if pg.mouse.get_pressed()[0]: self.fire(V(pg.mouse.get_pos()) + self.camera)
            elif keys[pg.K_SPACE]: self.fire()
        elif shooting: self.fire()
        for enemy in self.enemies[:]:
            enemy.repath -= dt
            enemy.flash = max(0, enemy.flash - dt)
            if self.line_clear(enemy.pos, self.player.pos): target = self.player.pos
            else:
                if enemy.repath <= 0:
                    enemy.path = self.route(enemy.pos, self.player.pos)
                    enemy.repath = 1.2 + self.rng.random() * .4
                while enemy.path and enemy.pos.distance_to(enemy.path[0]) < 12: enemy.path.pop(0)
                target = enemy.path[0] if enemy.path else self.player.pos
            direction = target - enemy.pos
            if direction.length_squared() > 1:
                direction.normalize_ip()
                enemy.facing = direction
                move_actor(enemy, direction * enemy.speed * dt, self.walls, self.bounds)
            enemy.anim += dt * 7
            if enemy.rect.colliderect(self.player.rect) and self.invulnerable <= 0:
                self.player.health = max(0, self.player.health - 12)
                self.invulnerable = .85
                self.burst(self.player.pos, (255, 70, 95), 8)
                if self.player.health <= 0:
                    self.state = 'over'; self.save_score(); return
        for shot in self.shots[:]:
            old = shot['pos'].copy()
            shot['pos'] += shot['vel'] * dt
            shot['life'] -= dt
            # Swept collision: choose the earliest wall/enemy along this segment.
            collisions = []
            for wall in self.walls:
                line = wall.inflate(10, 10).clipline(old, shot['pos'])
                if line: collisions.append((old.distance_squared_to(line[0]), None))
            for enemy in self.enemies:
                line = enemy.rect.inflate(10, 10).clipline(old, shot['pos'])
                if line: collisions.append((old.distance_squared_to(line[0]), enemy))
            if collisions:
                _, enemy = min(collisions, key=lambda c: c[0])
                if enemy is not None: self.damage_enemy(enemy, 30)
                self.burst(shot['pos'], (110, 215, 255), 5)
                self.shots.remove(shot)
            elif shot['life'] <= 0 or not self.bounds.collidepoint(shot['pos']): self.shots.remove(shot)
        for pickup in self.pickups[:]:
            pickup['life'] -= dt
            if pickup['pos'].distance_to(self.player.pos) < 28:
                if pickup['type'] == 'health': self.player.health = min(100, self.player.health + 30)
                else: self.mana = min(100, self.mana + 40)
                self.pickups.remove(pickup)
            elif pickup['life'] <= 0: self.pickups.remove(pickup)
        for p in self.particles[:]:
            p['life'] -= dt; p['pos'] += p['vel'] * dt
            if p['life'] <= 0: self.particles.remove(p)
        for pulse in self.pulses[:]:
            pulse[1] -= dt
            if pulse[1] <= 0: self.pulses.remove(pulse)
        if not self.enemies:
            self.next_wave -= dt
            if self.next_wave <= 0:
                self.player.health = min(100, self.player.health + 10)
                self.spawn_wave()

    def dash(self):
        if self.dash_cd <= 0:
            self.dash_direction = self.player.facing.copy()
            self.dash_left = .18
            self.dash_cd = 2.0
            self.invulnerable = max(self.invulnerable, .25)

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.save_score(); self.running = False
            elif event.type == pg.KEYDOWN:
                key = event.key
                if key in (pg.K_RETURN, pg.K_r) and self.state in ('menu', 'over'): self.reset()
                elif key in (pg.K_ESCAPE, pg.K_p):
                    if self.state == 'playing': self.state = 'paused'
                    elif self.state == 'paused': self.state = 'playing'
                    else: self.running = False
                elif key == pg.K_F1:
                    if self.state == 'playing': self.state = 'help'
                    elif self.state == 'help': self.state = 'playing'
                elif key == pg.K_m: self.minimap = not self.minimap
                elif key == pg.K_h: self.debug = not self.debug
                elif self.state == 'playing':
                    if key in (pg.K_LSHIFT, pg.K_RSHIFT): self.dash()
                    elif key == pg.K_e: self.nova()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3 and self.state == 'playing': self.nova()

    def text(self, value, pos, color=(228, 237, 247), big=False, center=False):
        image = (self.big if big else self.font).render(value, True, color)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.screen.blit(image, rect)

    def point(self, pos): return round(pos.x - self.camera.x), round(pos.y - self.camera.y)

    def draw_actor(self, actor, name):
        facing = actor.facing
        row = (1 if facing.x > 0 else 3) if abs(facing.x) > abs(facing.y) else (2 if facing.y >= 0 else 0)
        frame = self.frames[name][row][int(actor.anim) % 3]
        if actor.flash > 0:
            frame = frame.copy(); frame.fill((100, 80, 80, 0), special_flags=pg.BLEND_RGBA_ADD)
        self.screen.blit(frame, frame.get_rect(center=self.point(actor.pos)))
        if name == 'g':
            x, y = self.point(actor.pos)
            pg.draw.rect(self.screen, (30, 20, 30), (x - 16, y - 24, 32, 4))
            pg.draw.rect(self.screen, (255, 110, 100), (x - 16, y - 24, round(32 * actor.health / actor.max_health), 4))
        if self.debug: pg.draw.rect(self.screen, (0, 255, 220), actor.rect.move(-self.camera.x, -self.camera.y), 1)

    def draw(self):
        self.screen.fill((12, 17, 26))
        self.screen.blit(self.world, (-round(self.camera.x), -round(self.camera.y)))
        for pickup in self.pickups:
            color = (70, 240, 120) if pickup['type'] == 'health' else (80, 190, 255)
            pg.draw.circle(self.screen, color, self.point(pickup['pos']), 10)
            self.text('+' if pickup['type'] == 'health' else '*', V(self.point(pickup['pos'])) - V(5, 9))
        for enemy in sorted(self.enemies, key=lambda e: e.pos.y): self.draw_actor(enemy, 'g')
        if self.invulnerable <= 0 or int(self.elapsed * 14) % 2:
            self.draw_actor(self.player, 'countattack' if self.attack_left > 0 else 'count')
        for shot in self.shots:
            pos = self.point(shot['pos'])
            pg.draw.circle(self.screen, (70, 130, 255), pos, 8)
            pg.draw.circle(self.screen, (200, 245, 255), pos, 4)
        for pulse in self.pulses:
            pg.draw.circle(self.screen, (130, 210, 255), self.point(pulse[0]), max(1, round(170 * (1 - pulse[1] / .45))), 3)
        for p in self.particles: pg.draw.circle(self.screen, p['color'], self.point(p['pos']), max(1, round(p['life'] * 6)))
        if self.debug:
            for w in self.walls: pg.draw.rect(self.screen, (0, 255, 220), w.move(-self.camera.x, -self.camera.y), 1)
        width, height = self.screen.get_size()
        pg.draw.rect(self.screen, (15, 23, 37), (0, 0, width, 92))
        self.text('MYSTIC WORLD', (20, 12), (160, 210, 255))
        for y, amount, color, label in [(42, self.player.health, (65, 205, 120), 'Health'), (65, self.mana, (70, 155, 255), 'Mana')]:
            pg.draw.rect(self.screen, (45, 55, 75), (80, y, 160, 15), border_radius=4)
            pg.draw.rect(self.screen, color, (80, y, round(160 * amount / 100), 15), border_radius=4)
            self.text(label, (20, y - 2)); self.text(str(int(amount)), (247, y - 2))
        self.text(f'Wave {self.wave}   Enemies {len(self.enemies)}   Score {self.score}   Best {max(self.best, self.score)}', (305, 17))
        self.text(f'Dash: {self.dash_cd:.1f}s   Nova: {self.nova_cd:.1f}s  (35 mana)', (305, 48))
        pg.draw.rect(self.screen, (15, 23, 37), (0, height - 30, width, 30))
        self.text('WASD / Arrows: move    Space / Left mouse: fire    Shift: dash    E / Right mouse: nova    F1: help', (14, height - 24))
        if self.minimap:
            origin = V(width - 184, 105)
            self.screen.blit(self.mini, origin)
            pg.draw.rect(self.screen, (120, 170, 220), (*origin, 170, 170), 2)
            for e in self.enemies: pg.draw.circle(self.screen, (255, 85, 85), origin + e.pos * (170 / 3200), 2)
            pg.draw.circle(self.screen, (100, 255, 170), origin + self.player.pos * (170 / 3200), 4)
        if not self.enemies and self.state == 'playing': self.text(f'Next wave in {math.ceil(self.next_wave)}', (width / 2, 130), center=True)
        if self.state != 'playing':
            overlay = pg.Surface((width, height), pg.SRCALPHA); overlay.fill((7, 13, 24, 220)); self.screen.blit(overlay, (0, 0))
            title = {'menu': 'MYSTIC WORLD', 'paused': 'PAUSED', 'over': 'GAME OVER', 'help': 'HOW TO PLAY'}[self.state]
            self.text(title, (width / 2, height / 2 - 165), big=True, center=True)
            lines = ['Survive enemy waves in your original world.', 'WASD / Arrows to move. Hold Space to fire where you face.', 'Hold left mouse to aim and fire. Shift to dash.', 'E / Right mouse: area spell (35 mana, 4 second cooldown).', 'Green pickups restore health; blue pickups restore mana.', 'P / Escape: pause. M: minimap. H: collision outlines.', 'F1: show or close this help. Close the window to quit.']
            if self.state == 'over': lines = [f'Score: {self.score}     Best: {self.best}     Waves reached: {self.wave}', 'Press Enter or R to start again.', self.save_notice]
            elif self.state == 'paused': lines = ['P / Escape to resume.', 'Close the window to quit.']
            elif self.state == 'menu': lines += ['Press Enter to begin.']
            for i, line in enumerate(lines): self.text(line, (width / 2, height / 2 - 75 + i * 31), center=True)
        pg.display.flip()

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(60) / 1000, .05)
                self.events()
                if self.state == 'playing': self.update(dt)
                self.draw()
        finally: pg.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke-test', action='store_true', help='Run a deterministic headless game simulation')
    args = parser.parse_args()
    if args.smoke_test:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    game = Game(seed=42 if args.smoke_test else None)
    if args.smoke_test:
        game.state = 'playing'
        for i in range(360):
            game.update(1 / 60, movement=(1, 0) if i < 120 else (0, 1), shooting=True)
            game.draw()
        print(f'Smoke test passed: wave={game.wave}, enemies={len(game.enemies)}, health={game.player.health}')
        pg.quit()
    else: game.run()


if __name__ == '__main__': main()
