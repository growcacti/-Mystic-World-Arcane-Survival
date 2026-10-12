import pygame as pg
import sys
from os import path

from config import *
from player import *
from enemy import *
from tilemap import *
from other_sprites import *




class Game:
    def __init__(self):
        pg.init()
        self.all_sprites = pg.sprite.Group()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
       
        self.player = Player(self, 600, 600)
        self.spells = pg.sprite.Group()
        
        self.clock = pg.time.Clock()
        self.load_data()
        self.score_font = pg.font.Font(None, 28)  # Create a font object for the score
    def load_data(self):
        game_folder = path.dirname(__file__)
        img_folder = path.join(game_folder, 'img')
        map_folder = path.join(game_folder, 'maps')
        self.map = TiledMap(path.join(map_folder, 'L2.tmx'))
        self.map_img = self.map.make_map()
        self.map_rect = self.map_img.get_rect()
        self.enemies = pg.sprite.Group() 

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
       
        for tile_object in self.map.tmxdata.objects:
            if tile_object.name == 'player':
                self.player = Player(self, tile_object.x, tile_object.y)
            if tile_object.name == 'nme':
                self.nme = Enemy(self, tile_object.x, tile_object.y)
                self.enemies.add(self.nme)
            if tile_object.name == 'wall':
                Obstacle(self, tile_object.x, tile_object.y,
                         tile_object.width, tile_object.height)
                self.wall_img = tile_object.name
              
        self.nme = pg.sprite.Group()       
        self.camera = Camera(self.map.width, self.map.height)
        self.draw_debug = False

    def run(self):
        # game loop - set self.playing = False to end the game
        loop = True
        while loop:
            
            self.dt = self.clock.tick(FPS) / 1000.0  # fix for Python 2.x
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        loop = False
        sys.exit()

    def update(self):
        self.camera.update(self.player)
        
        
        self.all_sprites.update()
          # Check for collisions between player and walls
        player_collisions = pg.sprite.spritecollide(self.player, self.walls, False)
        if player_collisions:
            # Adjust player's position to avoid the walls
            self.player.pos -= self.player.vel * self.dt

        for enemy in self.enemies:
            enemy_collisions = pg.sprite.spritecollide(enemy, self.walls, False)
            if enemy_collisions:
                # Adjust enemy's position to avoid the walls
                enemy.pos -= enemy.vel * self.dt

                
        self.spells.update()
        spell_hits = pg.sprite.spritecollide(self.player, self.nme, True)
        if spell_hits:
            self.player.score += 1
            self.player.score += len(nme)

        hits = pg.sprite.groupcollide(self.nme, self.spells, True, True)
        for self.nme in hits:
            # Increase the player's score
            self.player.score += 1
            # Remove the enemy sprite from groups and kill it
            self.nme.kill()
        if self.nme and pg.sprite.collide_rect(self.player, self.nme):
            self.player.health -= 10  # Decrease health by 1 if player collides with the nme
            self.player.health_bar.update()
        nme_collisions = pg.sprite.spritecollide(self.player, self.enemies, False)
        if nme_collisions:
            self.player.health -= 10  # Decrease health by 1 for each nme collision
            self.player.health_bar.update()
        
      
       
    def draw(self):
        pg.display.set_caption("Player Position: ({0}, {1})".format(self.player.pos[0], self.player.pos[1]))
   
        self.screen.blit(self.map_img, self.camera.apply_rect(self.map_rect))
   
        for sprite in self.all_sprites:
            
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.draw_debug:
                pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(sprite.hit_rect), 1)
        if self.draw_debug:
            for wall in self.walls:
                pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(wall.rect), 1)

        if self.draw_debug:
            for wall in self.walls:
                pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(wall.rect), 1)

##        for spell in self.spells:
##            self.screen.blit(spell.image, self.camera.apply(spell))

        score_text = self.score_font.render("Score: {}".format((self.player.score)), True, CYAN)
        score_rect = score_text.get_rect()
        score_rect.topright = SCORE_POSITION
        self.screen.blit(score_text, score_rect)
        self.player.health_bar.draw(self.screen)
        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_h:
                    self.draw_debug = not self.draw_debug
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        spell = Spell(self, self.player.rect.centerx, self.player.rect.centery, self.player.direction,self.player.facing, self.player.angle)
                        self.player.fire_spell(self.player.angle)

# create the game object
g = Game()

while True:
    g.new()
    g.run()
  
