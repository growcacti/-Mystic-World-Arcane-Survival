import pygame as pg

from config import *



##
##
##class Bullet(pg.sprite.Sprite):
##    def __init__(self, game, pos, dir):
##        self.groups = game.all_sprites, game.bullets
##        pg.sprite.Sprite.__init__(self, self.groups)
##        self.game = game
##        self.image = game.bullet_img
##        self.rect = self.image.get_rect()
##        self.hit_rect = self.rect
##        self.pos = vec(pos)
##        self.rect.center = pos
##        spread = uniform(-GUN_SPREAD, GUN_SPREAD)
##        self.vel = dir.rotate(spread) * BULLET_SPEED
##        self.spawn_time = pg.time.get_ticks()
##
##    def update(self):
##        self.pos += self.vel * self.game.dt
##        self.rect.center = self.pos
##        if pg.sprite.spritecollideany(self, self.game.walls):
##            self.kill()
##

class Obstacle(pg.sprite.Sprite):
    def __init__(self, game, x, y, w, h):
        self.groups = game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game

        self.rect = pg.Rect(x, y, w, h)
        self.hit_rect = self.rect
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
