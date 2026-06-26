@echo off
setlocal
if "%~1"=="" (
  echo Uso: atualizar_site.bat "F:\REPOSITORIOS\SIT_PMO\downloads_gtn\consolidado_HH-MM-SS.xlsx"
  exit /b 1
)
python tools\atualizar_site_do_consolidado.py "%~1"
echo.
echo Site atualizado. Abra index.html ou publique esta pasta online.
pause
