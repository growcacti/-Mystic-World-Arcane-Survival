@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe game.py
) else (
    py game.py
)
if errorlevel 1 pause
