@echo off
rem Collecte des commentaires. Sans argument : toutes les sources, puis la fenêtre attend une touche.
rem Avec des sources (Collecter.bat youtube bluesky) : seulement celles-là, sans attendre (planification).
chcp 65001 >nul
cd /d "%~dp0"
python -m collecte %*
if "%~1"=="" (
  echo.
  echo Bilan : donnees\bilan.md
  pause
)
