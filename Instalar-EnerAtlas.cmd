@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1" %*
if errorlevel 1 (
  echo.
  echo A instalacao nao foi concluida. Leia o erro acima e execute novamente.
  pause
  exit /b 1
)
