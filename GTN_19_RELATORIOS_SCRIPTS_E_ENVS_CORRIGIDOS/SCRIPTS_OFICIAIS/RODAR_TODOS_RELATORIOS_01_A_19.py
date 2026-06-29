from __future__ import annotations

from pathlib import Path
from datetime import datetime
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable
LOG_DIR = BASE_DIR / "logs_execucao_19_relatorios"
LOG_DIR.mkdir(exist_ok=True)

SCRIPTS = ['GTN_RELATORIO_01_Walceir_P1.py', 'GTN_RELATORIO_02_Walceir_P2.py', 'GTN_RELATORIO_03_Walceir_P3.py', 'GTN_RELATORIO_04_Walceir_P9.py', 'GTN_RELATORIO_05_LucasRamos_P1.py', 'GTN_RELATORIO_06_LucasRamos_P2.py', 'GTN_RELATORIO_07_LucasRamos_P3.py', 'GTN_RELATORIO_08_LucasRamos_P9.py', 'GTN_RELATORIO_09_Camila_P1.py', 'GTN_RELATORIO_10_Camila_P2.py', 'GTN_RELATORIO_11_Camila_P3.py', 'GTN_RELATORIO_12_Camila_P9.py', 'GTN_RELATORIO_13_RenatoMezzalira_P1.py', 'GTN_RELATORIO_14_RenatoMezzalira_P2.py', 'GTN_RELATORIO_15_RenatoMezzalira_P3.py', 'GTN_RELATORIO_16_AdrielSilva_P1.py', 'GTN_RELATORIO_17_AdrielSilva_P3.py', 'GTN_RELATORIO_18_DeiseRosa_P1.py', 'GTN_RELATORIO_19_DeiseRosa_P3.py']


def main() -> None:
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 100)
    print(f"[INICIO] Execucao dos 19 relatorios: {inicio}")
    print(f"[PYTHON] {PYTHON}")
    print(f"[BASE] {BASE_DIR}")
    print("=" * 100)

    falhas = []
    for posicao, script in enumerate(SCRIPTS, start=1):
        caminho = BASE_DIR / script
        log = LOG_DIR / (Path(script).stem + ".log")
        print("\n" + "=" * 100)
        print(f"[{posicao:02d}/19] Rodando: {script}")
        print(f"[LOG] {log}")
        print("=" * 100)
        if not caminho.exists():
            print(f"[ERRO] Script nao encontrado: {caminho}")
            falhas.append(script)
            continue
        with log.open("w", encoding="utf-8") as f:
            processo = subprocess.run([PYTHON, str(caminho)], cwd=str(BASE_DIR), stdout=f, stderr=subprocess.STDOUT, text=True)
        if processo.returncode == 0:
            print(f"[OK] Finalizado sem erro: {script}")
        else:
            print(f"[FALHA] {script} retornou codigo {processo.returncode}. Veja o log.")
            falhas.append(script)
    print("\n" + "=" * 100)
    if falhas:
        print(f"[RESUMO] {len(falhas)} falha(s):")
        for item in falhas:
            print(f" - {item}")
        raise SystemExit(1)
    print("[RESUMO] Todos os 19 scripts finalizaram sem erro de retorno.")
    print("=" * 100)


if __name__ == "__main__":
    main()
