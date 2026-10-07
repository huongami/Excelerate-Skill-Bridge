@echo off
REM Start Jinder. Add --demo to make demo accounts. The passwords show once in this window.
cd /d "%~dp0"
python start.py %*
