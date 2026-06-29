from __future__ import annotations

from pathlib import Path
from datetime import datetime
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs_execucao_19_relatorios"
LOG_DIR.mkdir(exist_ok=True)

SCRIPTS = ['GTN_RELATORIO_01_Walceir_P1.py', 'GTN_RELATORIO_02_Walceir_P2.py', 'GTN_RELATORIO_03_Walceir_P3.py', 'GTN_RELATORIO_04_Walceir_P9.py', 'GTN_RELATORIO_05_LucasRamos_P1.py', 'GTN_RELATORIO_06_LucasRamos_P2.py', 'GTN_RELATORIO_07_LucasRamos_P3.py', 'GTN_RELATORIO_08_LucasRamos_P9.py', 'GTN_RELATORIO_09_Camila_P1.py', 'GTN_RELATORIO_10_Camila_P2.py', 'GTN_RELATORIO_11_Camila_P3.py', 'GTN_RELATORIO_12_Camila_P9.py', 'GTN_RELATORIO_13_RenatoMezzalira_P1.py', 'GTN_RELATORIO_14_RenatoMezzalira_P2.py', 'GTN_RELATORIO_15_RenatoMezzalira_P3.py', 'GTN_RELATORIO_16_AdrielSilva_P1.py', 'GTN_RELATORIO_17_AdrielSilva_P3.py', 'GTN_RELATORIO_18_DeiseRosa_P1.py', 'GTN_RELATORIO_19_DeiseRosa_P3.py']


def main() -> None:
    inicio_geral = datetime.now()
    print("=" * 100)
    print("EXECUTOR GTN - 19 RELATORIOS - PADRAO V6")
    print(f"Inicio: {inicio_geral:%d/%m/%Y %H:%M:%S}")
    print(f"Python: {sys.executable}")
    print(f"Pasta: {BASE_DIR}")
    print("=" * 100)

    resultados = []
    for i, script in enumerate(SCRIPTS, start=1):
        caminho = BASE_DIR / script
        print("\n" + "=" * 100)
        print(f"[{i:02d}/19] Executando: {script}")
        print("=" * 100)

        if not caminho.exists():
            print(f"[ERRO] Script nao encontrado: {caminho}")
            resultados.append((script, "NAO_ENCONTRADO", -1))
            continue

        log_path = LOG_DIR / f"{caminho.stem}_{datetime.now():%Y%m%d_%H%M%S}.log"
        with log_path.open("w", encoding="utf-8-sig") as log:
            proc = subprocess.run(
                [sys.executable, str(caminho)],
                cwd=str(BASE_DIR),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        status = "OK" if proc.returncode == 0 else "ERRO"
        resultados.append((script, status, proc.returncode))
        print(f"[{status}] returncode={proc.returncode} | log={log_path}")

        if proc.returncode != 0:
            print("[AVISO] Parei no primeiro erro para evitar efeito cascata.")
            break

    print("\n" + "=" * 100)
    print("RESUMO")
    for script, status, code in resultados:
        print(f"{status:14} | {code:4} | {script}")
    print(f"Fim: {datetime.now():%d/%m/%Y %H:%M:%S}")
    print("=" * 100)


if __name__ == "__main__":
    main()
