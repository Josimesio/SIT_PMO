$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = "f:/REPOSITORIOS/SIT_PMO/.venv/Scripts/python.exe"

if (-not (Test-Path $python)) {
    Write-Host "[AVISO] Python da venv nao encontrado no caminho padrao. Usando python do PATH." -ForegroundColor Yellow
    $python = "python"
}

& $python "$PSScriptRoot\RODAR_TODOS_RELATORIOS_01_A_19.py"
