@echo off
title Turnsole AgentForge Launcher
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_all.ps1"
if errorlevel 1 pause
