@echo off
setlocal
cd /d "%~dp0"
if exist "EnerAtlas-Windows-portatil.zip" (echo O ZIP ja existe. Use o arquivo existente ou outra pasta. & pause & exit /b 1)
if not exist "EnerAtlas-Windows-portatil.zip.part001" (echo Falta EnerAtlas-Windows-portatil.zip.part001. Baixe todas as partes na mesma pasta. & pause & exit /b 1)
if not exist "EnerAtlas-Windows-portatil.zip.part002" (echo Falta EnerAtlas-Windows-portatil.zip.part002. Baixe todas as partes na mesma pasta. & pause & exit /b 1)
if not exist "EnerAtlas-Windows-portatil.zip.part003" (echo Falta EnerAtlas-Windows-portatil.zip.part003. Baixe todas as partes na mesma pasta. & pause & exit /b 1)
if not exist "EnerAtlas-Windows-portatil.zip.part004" (echo Falta EnerAtlas-Windows-portatil.zip.part004. Baixe todas as partes na mesma pasta. & pause & exit /b 1)
echo Reunindo o pacote. Aguarde...
copy /b "EnerAtlas-Windows-portatil.zip.part001"+"EnerAtlas-Windows-portatil.zip.part002"+"EnerAtlas-Windows-portatil.zip.part003"+"EnerAtlas-Windows-portatil.zip.part004" "EnerAtlas-Windows-portatil.zip" >nul
if errorlevel 1 (echo Nao foi possivel reunir. Verifique espaco livre. & pause & exit /b 1)
powershell -NoProfile -Command "if ((Get-FileHash -LiteralPath 'EnerAtlas-Windows-portatil.zip' -Algorithm SHA256).Hash -ne '581cb0ba0e45c5251e38269b4f4f6420021a15f335eba46a2f3004ee0dab6e42') {exit 1}"
if errorlevel 1 (echo O hash nao confere. Preserve os arquivos e baixe as partes novamente. & pause & exit /b 1)
echo Pacote conferido. Extraia o ZIP e abra EnerAtlas.exe.
start "" "EnerAtlas-Windows-portatil.zip"
pause
