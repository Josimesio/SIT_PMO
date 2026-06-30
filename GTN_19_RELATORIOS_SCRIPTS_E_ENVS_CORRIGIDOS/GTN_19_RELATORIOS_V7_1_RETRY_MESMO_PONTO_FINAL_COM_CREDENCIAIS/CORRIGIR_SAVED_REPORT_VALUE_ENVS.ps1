# ============================================================
# CORRIGIR_SAVED_REPORT_VALUE_ENVS.ps1
#
# Objetivo:
# - Corrigir os .env que estão sem saved_report_value
# - Preservar todos os demais campos existentes
# - Criar backup automático antes de alterar
#
# Pasta alvo:
# C:\REPOSITORIOS\GTN_PMO\SIT_PMO\GTN_19_RELATORIOS_SCRIPTS_E_ENVS_CORRIGIDOS\GTN_19_RELATORIOS_V7_1_RETRY_MESMO_PONTO_FINAL_COM_CREDENCIAIS\credenciais
# ============================================================

$ErrorActionPreference = "Stop"

$Projeto = "C:\REPOSITORIOS\GTN_PMO\SIT_PMO"
$PastaBase = Join-Path $Projeto "GTN_19_RELATORIOS_SCRIPTS_E_ENVS_CORRIGIDOS\GTN_19_RELATORIOS_V7_1_RETRY_MESMO_PONTO_FINAL_COM_CREDENCIAIS"
$PastaCredenciais = Join-Path $PastaBase "credenciais"

$Mapa = @{
    "env_CAMILA_P3.env"          = "96449983914285918"
    "env_RENATOMEZZALIRA_P1.env" = "96836102112838540"
    "env_RENATOMEZZALIRA_P2.env" = "96840562521859779"
    "env_ADRIELSILVA_P1.env"    = "96896222567721463"
    "env_DEISEROSA_P1.env"      = "96898268944724974"
    "env_DEISEROSA_P3.env"      = "96913647909993268"
}

function Atualizar-Env {
    param(
        [string]$Arquivo,
        [string]$Valor
    )

    if (!(Test-Path $Arquivo)) {
        Write-Host "[ERRO] Arquivo não encontrado: $Arquivo"
        return
    }

    $Backup = "$Arquivo.bak_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $Arquivo $Backup -Force

    $Linhas = Get-Content $Arquivo -Encoding UTF8

    $Encontrou = $false
    $NovasLinhas = foreach ($Linha in $Linhas) {
        if ($Linha -match '^\s*saved_report_value\s*=') {
            $Encontrou = $true
            "saved_report_value=$Valor"
        }
        elseif ($Linha -match '^\s*SAVED_REPORT_VALUE\s*=') {
            $Encontrou = $true
            "saved_report_value=$Valor"
        }
        else {
            $Linha
        }
    }

    if (-not $Encontrou) {
        $NovasLinhas += ""
        $NovasLinhas += "# Valor do relatório salvo no APEX"
        $NovasLinhas += "saved_report_value=$Valor"
    }

    Set-Content -Path $Arquivo -Value $NovasLinhas -Encoding UTF8

    Write-Host "[OK] Atualizado: $Arquivo"
    Write-Host "     saved_report_value=$Valor"
    Write-Host "     Backup: $Backup"
}

Write-Host "============================================================"
Write-Host "[GTN] Corrigir saved_report_value dos .env"
Write-Host "============================================================"
Write-Host "[INFO] Pasta credenciais: $PastaCredenciais"
Write-Host ""

if (!(Test-Path $PastaCredenciais)) {
    throw "[ERRO] Pasta de credenciais não encontrada: $PastaCredenciais"
}

foreach ($Item in $Mapa.GetEnumerator()) {
    $ArquivoEnv = Join-Path $PastaCredenciais $Item.Key
    Atualizar-Env -Arquivo $ArquivoEnv -Valor $Item.Value
    Write-Host ""
}

Write-Host "============================================================"
Write-Host "[OK] Correção finalizada."
Write-Host "============================================================"
Write-Host ""
Write-Host "Agora rode novamente:"
Write-Host ""
Write-Host "& c:/REPOSITORIOS/GTN_PMO/SIT_PMO/.venv/Scripts/python.exe c:/REPOSITORIOS/GTN_PMO/SIT_PMO/GTN_EXECUTAR_RECUPERAR_LINHAS_FALTANTES_V2.py"
