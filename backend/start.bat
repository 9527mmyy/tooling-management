@echo off
cd /d "%~dp0"
start /B python app.py > flask.log 2>&1
