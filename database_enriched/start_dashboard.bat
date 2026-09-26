@echo off
title Car Database Dashboard (GitHub)
cd /d "%~dp0"
echo Opening dashboard at http://localhost:3002 ...
start "" http://localhost:3002
set PORT=3002
node --no-warnings server.js
pause
