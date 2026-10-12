import pygame as pg
from pygame import font
from itertools import cycle
from random import uniform, choice, randint, random
from config import *

vec = pg.math.Vector2
class Player(pg.sprite.Sprite):
    def __init__(self, game, px, py):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.sheet = pg.image.load("img/count.png").convert_alpha()
        self.attack = pg.image.load("img/countattack.png").convert_alpha()
        self.size = (32, 36)
        self.frames_down = self.strip(self.sheet, (0, 72), self.size, 3)
        self.frames_up = self.strip(self.sheet, (0, 0), self.size, 3)
        self.frames_left = self.strip(self.sheet, (0, 106), self.size, 3)
        self.frames_right = self.strip(self.sheet, (0, 37), self.size, 3)
        self.attack_frames_down = self.strip(self.attack, (0, 72), self.size, 3)
        self.attack_frames_up = self.strip(self.attack, (0, 0), self.size, 3)
        self.attack_frames_left = self.strip(self.attack, (0, 106), self.size, 3)
        self.attack_frames_right = self.strip(self.attack, (0, 37), self.size, 3)
        self.frame_index = 0
        self.attack_index = 0
        self.animation_speed = 100  # Milliseconds per frame
        self.last_update = 0
        self.last_direction = None
        self.image = self.frames_down[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.topleft = (px, py)
        self.pos = vec(px, py)
        self.vel = vec(0, 0)
        self.hit_rect = self.rect
        self.game = game
        self.font = pg.font.Font
        self.last_shot = 0
        self.health = PLAYER_HEALTH
        self.facing = None
        self.start = (1, 1)
        self.direction = vec(0, 0)
        self.score = 0
        self.max_health = PLAYER_HEALTH
        self.health = self.max_health
        self.health_bar = HealthBar(self)
        self.angle = 270
        self.fsize = (32, 36)

    def strip(self, sheet, start, size, columns, rows=1):
        self.frames = []
        for j in range(rows):
            for i in range(columns):
                location = (start[0] + size[0] * i, start[1] + size[1] * j)
                self.frames.append(sheet.subsurface(pg.Rect(location, size)))
        return self.frames
    def animate(self):
        now = pg.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            if self.vel == vec(0, 0):
                self.frame_index = 0
                self.last_direction = self.facing
            else:
                if self.last_direction == DIRECT_DICT["LEFT"]:
                    self.frames = self.frames_left
                    self.attack_frames = self.attack_frames_left
                elif self.last_direction == DIRECT_DICT["RIGHT"]:
                    self.frames = self.frames_right
                    self.attack_frames = self.attack_frames_right
                elif self.last_direction == DIRECT_DICT["UP"]:
                    self.frames = self.frames_up
                    self.attack_frames = self.attack_frames_up
                elif self.last_direction == DIRECT_DICT["DOWN"]:
                    self.frames = self.frames_down
                    self.attack_frames = self.attack_frames_down
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.image = self.frames[self.frame_index]
    def attack(self):
        now = pg.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            if self.vel == vec(0, 0):
                self.frame_index = 0
                self.last_direction = self.facing
            else:
                if self.last_direction == DIRECT_DICT["LEFT"]:
                    self.attack_frames = self.attack_frames_left
                    self.frames = self.attack_frames
                elif self.last_direction == DIRECT_DICT["RIGHT"]:
                    self.attack_frames = self.attack_frames_right
                    self.frames = self.attack_frames
                elif self.last_direction == DIRECT_DICT["UP"]:
                    self.attack_frames = self.attack_frames_up
                    self.frames = self.attack_frames
                elif self.last_direction == DIRECT_DICT["DOWN"]:
                    self.attack_frames = self.attack_frames_down
                    self.frames = self.attack_frames
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.image = self.attack_frames[self.frame_index]
    def get_keys(self):
        self.vel = vec(0, 0)
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.start =[0,106]
            self.strip(self.sheet, self.start, self.size, 3)
            self.facing = DIRECT_DICT["LEFT"]
            self.angle = 180
            self.vel.x = -PLAYER_SPEED
        elif keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.start =[0, 37]
            self.strip(self.sheet, self.start, self.size, 3)
            self.facing = DIRECT_DICT["RIGHT"]
            self.angle=0
            self.vel.x = PLAYER_SPEED
        elif keys[pg.K_UP] or keys[pg.K_w]:
            self.start = [0, 0]
            self.strip(self.sheet,self.start, self.size, 3)
            self.facing = DIRECT_DICT["UP"]
            self.angle = 90
            self.vel.y = -PLAYER_SPEED
        elif keys[pg.K_DOWN] or keys[pg.K_s]:
            self.start=[0, 72]
            self.strip(self.sheet, self.start, self.size, 3)
            self.facing = DIRECT_DICT["DOWN"]
            self.angle = 270
            self.vel.y = PLAYER_SPEED

        if self.vel != vec(0, 0):
            self.last_direction = self.facing  # Update the last direction

    def get_direction(self):
        if self.vel.x > 0:
             self.start = [0,37]
             self.facing = DIRECT_DICT["RIGHT"]
             self.direction = vec(1,0)
             self.angle = 0
             return self.facing, self.direction, self.angle
        
        elif self.vel.x < 0:
             self.start = [0,106]
             self.facing = DIRECT_DICT["LEFT"]
             self.direction = vec(-1,0)
             self.angle = 180
             return self.facing, self.direction, self.angle
        elif self.vel.y < 0:
             self.start = [0,0]
             self.facing = DIRECT_DICT["UP"]
             self.direction = vec(0,-1)
             self.angle = 90
             return self.facing, self.direction, self.angle
        elif self.vel.y > 0:
             self.start = [0,72]
             self.facing = DIRECT_DICT["DOWN"]
             self.direction =vec(0,1)
             self.angle = 270
             return self.facing, self.direction, self.angle
        else:
            return self.facing, self.direction, self.angle
    def fire_spell(self, angle):
       
        self.angle = angle
        self.facing, self.direction, self.angle = self.get_direction()
     
        if self.angle == 0:
            self.start = [0,37]
            self.attack_frames = self.attack_frames_right
            self.image = self.attack_frames[self.frame_index]
            self.game.screen.blit(self.image, self.game.camera.apply(self))
            
            spell = Spell(self.game, self.rect.centerx, self.rect.centery, self.facing, self.direction, self.angle)  # Pass self.facing instead of direction
        elif self.angle == 180:
            self.start = [0,106]
            self.attack_frames = self.attack_frames_left
            self.image = self.attack_frames[self.frame_index]
            self.game.screen.blit(self.image, self.game.camera.apply(self))
            spell = Spell(self.game, self.rect.centerx, self.rect.centery, self.facing, self.direction, self.angle)  # Pass self.facing instead of direction
        elif self.angle == 90:
            self.start = [0,0]
            self.attack_frames = self.attack_frames_up
            self.image = self.attack_frames[self.frame_index]
            self.game.screen.blit(self.image, self.game.camera.apply(self))
            spell = Spell(self.game, self.rect.centerx, self.rect.centery, self.facing, self.direction, self.angle)  # Pass self.facing instead of direction
        elif self.angle == 270:
            self.start = [0,72]
            self.attack_frames = self.attack_frames_down
            self.image = self.attack_frames[self.frame_index]
            self.game.screen.blit(self.image, self.game.camera.apply(self))
            spell = Spell(self.game, self.rect.centerx, self.rect.centery, self.facing, self.direction, self.angle)  # Pass self.facing instead of direction
    
        #self.game.spells.add(spell)
        
        self.game.all_sprites.add(spell)
        self.game.spells.add(spell)
    def update(self):
        self.health_bar.update()
        self.get_keys()
        self.animate()
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos

        self.rect.center = self.pos

        self.hit_rect.center = self.rect.center
        spell_hits = pg.sprite.spritecollide(self, self.game.enemies, True)  # Check for spell-enemy collisions
        for enemy in spell_hits:
            self.score += 1  # Increase the score when an enemy is hit

    def draw(self):
        self.game.screen.blit(self.image, self.game.camera.apply(self))
        self.health_bar.draw(self.game.screen)





       
class Spell(pg.sprite.Sprite):
    def __init__(self, game, x, y, facing, direction, angle):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.surf = pg.Surface((32, 36)).convert_alpha()
        self.sheet = pg.image.load("img/force.png").convert_alpha()
        self.size = (32, 36)
        self.frames_down = self.strip(self.sheet, (0, 72), self.size, 3)
        self.frames_up = self.strip(self.sheet, (0, 0), self.size, 3)
        self.frames_left = self.strip(self.sheet, (0, 106), self.size, 3)
        self.frames_right = self.strip(self.sheet, (0, 37), self.size, 3)
        self.frame_iter = cycle(self.get_frames(angle))  # Create an iterator for cycling frames
        self.image = next(self.frame_iter)  # Get the first frame
        self.rect = pg.Rect(self.image.get_rect())
        self.last_update = 0
        self.rect.center = (x, y)
        self.pos = vec(x, y)
        self.animation_speed = 2
        self.direction = direction
        self.facing = facing
        self.angle = angle

    def strip(self, sheet, start, size, columns, rows=1):
        frames = []
        for j in range(rows):
            for i in range(columns):
                location = (start[0] + size[0] * i, start[1] + size[1] * j)
                frames.append(sheet.subsurface(pg.Rect(location, size)))
        return frames

    def get_frames(self, angle):
        if angle == 90:
            return self.frames_up
        elif angle == 270:
            return self.frames_down
        elif angle == 180:
            return self.frames_left
        elif angle == 0:
            return self.frames_right

    def animate(self):
        now = pg.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.image = next(self.frame_iter)

    def update(self):
        self.animate()
        if self.angle == 90:
            # Up
            self.rect.centery -= SPELL_SPEED
        elif self.angle == 270:
            # Down
            self.rect.centery += SPELL_SPEED
        elif self.angle == 180:
            # Left
            self.rect.centerx -= SPELL_SPEED
        elif self.angle == 0:
            # Right
            self.rect.centerx += SPELL_SPEED
        # Remove the spell when it goes off the screen
        if (
            self.rect.left < 0
            or self.rect.right > self.game.map.width
            or self.rect.top < 0
            or self.rect.bottom > self.game.map.height
        ):
            self.kill()

    def draw(self):
        pass
        
class HealthBar:
    def __init__(self, player):
        self.player = player
        self.image = pg.Surface((100, 20))
        self.image.fill((0,0,255))    # Adjust the size as needed
        self.rect = self.image.get_rect()
        self.rect.topleft = (20, 20)  # Position the health bar in the top left corner
        self.max_width = self.rect.width

    def update(self):
        # Calculate the width of the health bar based on the player's health
        health_ratio = self.player.health / self.player.max_health
        self.rect.width = int(self.max_width * health_ratio)

    def draw(self, screen):
        pg.draw.rect(screen, (0, 0, 255), self.rect)  # blue health bar
        
        
