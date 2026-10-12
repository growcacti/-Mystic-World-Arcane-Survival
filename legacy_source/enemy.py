import pygame as pg
from pygame import font
from random import uniform, choice, randint, random
from config import *
from itertools import cycle, repeat
vec = pg.math.Vector2

class Enemy(pg.sprite.Sprite):
    def __init__(self, game, px, py):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.sheet = pg.image.load("img/g.png").convert_alpha()
        self.size = (32, 36)
        self.frames = self.strip(self.sheet, (0, 72), self.size, 3)
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.last_direction = NME_DICT["DOWN"]  # Add the last_direction attribute
        self.rect = self.image.get_rect()
        self.animation_speed = 200  # Milliseconds per frame
        self.last_update = 0
        self.pos = vec(px, py)
        self.vel = vec(0, 0)
        self.hit_rect = self.rect
        self.game = game
        self.health = NME_HEALTH
        self.direction = vec(0,0)
        self.direction = self.game.player.pos -self.pos
    # Rest of the code...


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
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.image = self.frames[self.frame_index]

    def move_towards_player(self):
        player_pos = self.game.player.pos
        self.direction = player_pos - self.pos
        if self.direction.length_squared() > 0:
            self.direction.normalize_ip()
          
        self.vel = self.direction * NME_SPEED

        # Update last_direction based on movement direction
        if abs(self.direction.x) > abs(self.direction.y):
            if self.direction.x > 0:
                self.last_direction = NME_DICT["RIGHT"]
            else:
                self.last_direction = NME_DICT["LEFT"]
        elif abs(self.direction.x) < abs(self.direction.y):
            if self.direction.y > 0:
                self.last_direction = NME_DICT["DOWN"]
            else:
                self.last_direction = NME_DICT["UP"]

    def update(self):
        self.rect.center = self.pos
        self.move_towards_player()
        self.animate()
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        self.hit_rect.center = self.rect.center 
        self.get_move()  # Call the get_move method to update the direction
        
        spell_hits = pg.sprite.spritecollide(self, self.game.spells, True)
        for spell in spell_hits:
            # Increase the player's score
            self.game.player.score += 1
            # Remove the enemy sprite from groups and kill it
            self.kill()
    def get_move(self):
        if abs(self.direction.x) > abs(self.direction.y):
            if self.direction.x > 0:
                self.last_direction = NME_DICT["RIGHT"]
                self.frames = self.strip(self.sheet, (0, 36), self.size, 3)
                self.vel.x = NME_SPEED
            else:       
                self.last_direction = NME_DICT["LEFT"]
                self.frames = self.strip(self.sheet, (0, 108), self.size, 3)
                self.vel.x = -NME_SPEED
        else:
            if self.direction.y > 0:
                self.last_direction = NME_DICT["DOWN"]
                self.frames = self.strip(self.sheet, (0, 72), self.size, 3)
                self.vel.y = NME_SPEED
            else:       
                self.last_direction = NME_DICT["UP"]
                self.frames = self.strip(self.sheet, (0, 0), self.size, 3)
                self.vel.y = -NME_SPEED




    def draw(self):
        self.game.screen.blit(self.image, self.game.camera.apply(self))



