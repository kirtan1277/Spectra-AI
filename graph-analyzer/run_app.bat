@echo off
title Graph Analyzer Server
echo ==================================================
echo  Starting Graph Analyzer...
echo ==================================================
cd /d "%~dp0"
python -u app.py
pause
