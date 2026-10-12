"""Headless regressions for collision, combat, wave progression and reset."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
import pygame as pg
from game import Actor, Game, V, move_actor

class MechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.game = Game(seed=7)
    @classmethod
    def tearDownClass(cls): pg.quit()
    def setUp(self): self.game.reset()

    def test_dash_cannot_cross_thin_wall(self):
        actor = Actor((60, 100))
        wall = pg.Rect(100, 0, 2, 200)
        move_actor(actor, V(400, 0), [wall], pg.Rect(0, 0, 600, 600))
        self.assertEqual(actor.rect.right, wall.left)
        self.assertFalse(actor.rect.colliderect(wall))

    def test_wall_slide(self):
        actor = Actor((60, 70))
        move_actor(actor, V(100, 80), [pg.Rect(100, 0, 5, 400)], pg.Rect(0, 0, 600, 600))
        self.assertEqual(actor.rect.right, 100)
        self.assertGreater(actor.pos.y, 140)

    def combat_setup(self):
        g = self.game
        g.walls_original = g.walls
        self.addCleanup(setattr, g, 'walls', g.walls_original)
        g.walls = []
        g.player = Actor((500, 500))
        g.player.facing = V(1, 0)
        g.enemies = [Actor((600, 500), 30)]
        g.enemies[0].speed = 0
        return g

    def test_spell_kills_once(self):
        g = self.combat_setup(); g.fire()
        for _ in range(20): g.update(.01, (0, 0), False)
        self.assertEqual(g.score, 100)
        self.assertEqual(len(g.enemies), 0)
        self.assertEqual(len(g.shots), 0)

    def test_wall_blocks_spell(self):
        g = self.combat_setup(); g.walls = [pg.Rect(550, 450, 2, 100)]
        g.fire()
        g.update(.2, (0, 0), False)
        self.assertEqual(g.score, 0)
        self.assertEqual(g.enemies[0].health, 30)

    def test_contact_damage_has_cooldown(self):
        g = self.combat_setup(); g.enemies[0].pos = g.player.pos.copy()
        g.enemies[0].rect.center = g.player.pos
        for _ in range(20): g.update(.01, (0, 0), False)
        self.assertEqual(g.player.health, 88)

    def test_nova_cost_and_cooldown(self):
        g = self.combat_setup(); g.nova(); g.nova()
        self.assertEqual(g.mana, 65)
        self.assertEqual(g.score, 100)

    def test_reset_clears_entities(self):
        g = self.combat_setup(); g.fire(); g.reset()
        self.assertEqual(g.shots, [])
        self.assertEqual(g.enemies, [])
        self.assertEqual(g.player.health, 100)

    def test_wave_starts(self):
        g = self.game
        for _ in range(70): g.update(1 / 60, (0, 0), False)
        self.assertEqual(g.wave, 1)
        self.assertEqual(len(g.enemies), 6)

if __name__ == '__main__': unittest.main()
