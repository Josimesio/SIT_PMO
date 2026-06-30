$ErrorActionPreference = "Stop"
$Base = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = "f:/REPOSITORIOS/SIT_PMO/.venv/Scripts/python.exe"
Set-Location $Base
& $Py "$Base/RODAR_TODOS_RELATORIOS_RESILIENTE_V7.py"
