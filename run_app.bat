@echo off
title NeuroGen AI - Question Paper Generator

echo ===================================================
echo 🚀 Starting NeuroGen AI...
echo ===================================================

echo [1/3] Checking dependencies...
pip install -r backend/requirements.txt

echo [2/3] Starting Backend Server (Flask)...
start "NeuroGen Backend" python backend/app.py

echo [3/3] Starting Frontend Server...
start "NeuroGen Frontend" python -m http.server 8000

echo Opening application in browser...
timeout /t 5 >nul
start http://localhost:8000/frontend/index.html

echo ===================================================
echo ✅ System Online!
echo Keep this window open. Close the other windows to stop.
echo ===================================================
pause
