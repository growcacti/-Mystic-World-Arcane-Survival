# Mystic World — Arcane Survival

## Quick start: MX Linux / Debian

Extract the ZIP first. Open a terminal in the Mystic_World_Improved folder:

```bash
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python game.py
```

On later launches, activate .venv and run `python game.py` again.
Or use `bash run_linux.sh` after installing the requirements.

## Windows

Install Python 3.10 or later, then open a terminal in the extracted folder:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe game.py
```

After installation, double-click run_windows.bat.
The assets are located relative to game.py, so launching from another directory works.

## Controls

| Key / mouse | Action |
| --- | --- |
| Enter | Start / restart after game over |
| WASD or arrows | Move, including diagonal movement |
| Hold Space | Fire in the last facing direction |
| Hold left mouse | Aim at the pointer and fire |
| Shift | Dash; 2 second cooldown, briefly protects against contact damage |
| E or right mouse | Area spell; 35 mana, 4 second cooldown, blocked by walls |
| P or Escape | Pause / resume during play |
| F1 | Open / close help during play |
| M | Show / hide minimap |
| H | Show / hide collision outlines |
| R | Restart after game over |
| Close window | Save score and quit |

## Gameplay and improvements

- Survive escalating waves: six enemies in wave one, up to thirty per wave.
- Enemies have health bars, follow you, and use grid pathfinding around obstacles.
- Spells deal 30 damage; the area spell deals 80 damage within 170 pixels.
- Each defeated enemy awards 100 points and produces a particle explosion.
- Enemies may drop green health or blue mana pickups; collect them within 25 seconds.
- Mana regenerates. Completing a wave restores 10 health before the next wave.
- Contact damage is 12 health, with an 0.85 second protection interval.
- Movement and spell speed use elapsed time. Diagonal movement is normalized.
- Axis-by-axis wall collision allows sliding along walls. Substeps stop dashes
  crossing thin walls. Swept spell collision stops fast shots crossing targets.
- Main menu, pause, help, game over, restart, minimap and a clearer HUD.
- High score is saved under ~/.config/mystic_world/scores.json on Linux, or
  %APPDATA%\mystic_world\scores.json on Windows. An unwritable save location
  does not prevent play.
- No pytmx dependency or external tileset paths. Images load once at startup.

## Checks performed

Eight automated regression checks pass for dash collision, wall sliding,
spell damage/scoring, wall-blocked spells, contact damage cooldown,
area-spell cooldown/cost, reset, and wave creation. A deterministic headless
simulation and a rendered screen inspection also passed with Python 3.12
and pygame-ce 2.5.8. Interactive play on your Linux/Windows machine still needs
verification; this package is source code, not a standalone executable.

Run the included checks:

```bash
python -m unittest discover -v
python game.py --smoke-test
```

## Editing and expanding

The main settings and mechanics are in game.py. The original wall and spawn
coordinates are in assets/world.json. The map background is assets/world.jpeg.
You can add new enemy types, objectives, sounds or additional maps here.
The original Tiled editor maps and unused art remain in your uploaded archive.

Limitations: this edition has one map and endless survival waves. No audio,
full-game save/resume, or campaign progression is included. Grid pathfinding
is approximate, so an enemy may hesitate at a narrow passage. The original
wall coordinates may not match every visible decorative object; H shows which
objects are solid. A window of at least 1100 × 780 is recommended for the HUD.

