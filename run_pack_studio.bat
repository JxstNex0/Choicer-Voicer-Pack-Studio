@echo off
title Choicer Voicer Pack Studio
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Launch failed. Installing requirements and retrying...
    pip install -r requirements.txt
    python main.py
    pause
)
