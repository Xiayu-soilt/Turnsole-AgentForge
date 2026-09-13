@echo off
title Turnsole AgentForge Stopper
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_all.ps1"
pause
