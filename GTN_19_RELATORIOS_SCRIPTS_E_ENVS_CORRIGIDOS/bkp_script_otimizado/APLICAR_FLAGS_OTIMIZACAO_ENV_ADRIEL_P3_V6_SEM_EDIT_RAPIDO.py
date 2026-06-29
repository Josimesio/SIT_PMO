from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "credenciais" / "env_ADRIELSILVA_P3.env"

FLAGS = {
    "MEDIR_METRICAS_REAIS": "S",
    "METRICAS_MEDIR_PLAYWRIGHT": "S",
    "METRICAS_SALVAR_ETAPAS": "S",
    "METRICAS_EXIBIR_TELA": "S",
    "METRICAS_PASTA": "metricas_execucao",
    "METRICAS_BUFFER_MEMORIA": "S",
    "METRICAS_IGNORAR_ETAPAS": "LOCATOR_COUNT",
    "OTIMIZAR_ESPERAS_GTN": "S",
    "OTIMIZAR_WAIT_FOR_TIMEOUT": "S",
    "OTIMIZAR_WAIT_FOR_TIMEOUT_SOMENTE_EXECUCAO": "S",
    "MAX_WAIT_FOR_TIMEOUT_MS": "450",
    "OTIMIZAR_OVERLAY_APEX": "S",
    "OVERLAY_TIMEOUT_MS": "1000",
    "OTIMIZAR_PROXIMO": "S",
    "PROXIMO_TIMEOUT_MS": "500",
    "OTIMIZAR_SAVED_REPORT_GO": "S",
    "SAVED_REPORT_GO_TIMEOUT_MS": "2000",
    "OTIMIZAR_SLOW_MO_BROWSER": "S",
    "SLOW_MO_BROWSER_MS": "0",
    "OTIMIZAR_TIMEOUT_EDIT_EXECUCAO": "S",
    "TIMEOUT_EDIT_EXECUCAO_OTIMIZADO_MS": "5000",
    "TIMEOUT_EDIT_EXECUCAO": "5000",
    "TIMEOUT_LINK_EDIT": "5000",
    "TIMEOUT_BUSCA_EDIT": "5000",
    "TIMEOUT_EDIT_CENARIO": "5000",
}

def carregar_linhas(path: Path) -> list[str]:
    if not path.exists():
        raise SystemExit(f"[ERRO] Env não encontrado: {path}")
    return path.read_text(encoding="utf-8-sig").splitlines()

def aplicar_flags(linhas: list[str]) -> list[str]:
    existentes = {}
    novas = []
    for linha in linhas:
        stripped = linha.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            chave = stripped.split("=", 1)[0].strip()
            existentes[chave] = True
            if chave in FLAGS:
                novas.append(f"{chave}={FLAGS[chave]}")
            else:
                novas.append(linha)
        else:
            novas.append(linha)

    faltantes = [k for k in FLAGS if k not in existentes]
    if faltantes:
        novas.append("")
        novas.append("# ============================================================")
        novas.append("# MÉTRICAS REAIS + OTIMIZAÇÃO V6 - SEM EDIT RÁPIDO")
        novas.append("# ============================================================")
        for chave in faltantes:
            novas.append(f"{chave}={FLAGS[chave]}")
    return novas

def main() -> None:
    linhas = carregar_linhas(ENV_PATH)
    backup_dir = ENV_PATH.parent / "backup_env_otimizacao"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{ENV_PATH.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ENV_PATH.suffix}"
    backup_path.write_text("\n".join(linhas) + "\n", encoding="utf-8-sig")

    novas = aplicar_flags(linhas)
    ENV_PATH.write_text("\n".join(novas) + "\n", encoding="utf-8-sig")

    print(f"[OK] Env atualizado: {ENV_PATH}")
    print(f"[OK] Backup criado: {backup_path}")
    print("[OK] V6 aplicada: TIMEOUT_EDIT_EXECUCAO=5000ms")

if __name__ == "__main__":
    main()
