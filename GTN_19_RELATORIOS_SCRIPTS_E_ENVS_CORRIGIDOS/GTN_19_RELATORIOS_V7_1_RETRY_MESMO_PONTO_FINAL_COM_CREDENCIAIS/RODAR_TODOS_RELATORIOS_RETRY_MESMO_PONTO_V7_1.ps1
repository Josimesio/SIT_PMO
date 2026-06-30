$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BaseDir

if (-not $env:GTN_STALL_TIMEOUT_SEGUNDOS) { $env:GTN_STALL_TIMEOUT_SEGUNDOS = "240" }
if (-not $env:GTN_MAX_REINICIOS_POR_RELATORIO) { $env:GTN_MAX_REINICIOS_POR_RELATORIO = "50" }

Write-Host "[V7.1] Rodando executor resiliente sem pular cenário..." -ForegroundColor Cyan
Write-Host "[V7.1] Timeout sem progresso: $env:GTN_STALL_TIMEOUT_SEGUNDOS segundos" -ForegroundColor Cyan
Write-Host "[V7.1] Max reinícios por relatório: $env:GTN_MAX_REINICIOS_POR_RELATORIO" -ForegroundColor Cyan

& f:/REPOSITORIOS/SIT_PMO/.venv/Scripts/python.exe "$BaseDir/RODAR_TODOS_RELATORIOS_RETRY_MESMO_PONTO_V7_1.py"
exit $LASTEXITCODE
