$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $BaseDir "..\.venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}
& $Python (Join-Path $BaseDir "RODAR_TODOS_RELATORIOS_01_A_19.py")
