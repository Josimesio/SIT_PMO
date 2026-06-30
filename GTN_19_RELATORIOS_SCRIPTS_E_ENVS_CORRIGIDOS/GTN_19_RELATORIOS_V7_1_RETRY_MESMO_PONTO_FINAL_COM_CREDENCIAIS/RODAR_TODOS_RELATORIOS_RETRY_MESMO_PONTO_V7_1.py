# Executor resiliente V7.1 para GTN
# - Roda os 19 scripts em sequencia.
# - Monitora progresso por linha/indice.
# - Se uma linha fica sem avanço por muito tempo, mata o processo e TENTA NOVAMENTE O MESMO PONTO.
# - Nao pula cenário. Se houver Edit, tenta baixar. Se nao houver Edit, o script deve gerar placeholder.
# - Se o mesmo ponto falhar repetidamente acima do limite, para e informa o ponto para análise.
# - Nao altera credenciais; usa os .env de cada script.

from __future__ import annotations

import os
import re
import sys
import time
import queue
import signal
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = Path(os.environ.get("GTN_PYTHON_EXE", sys.executable))

# Ajuste fino por env, sem mexer no codigo:
#   GTN_STALL_TIMEOUT_SEGUNDOS=240
#   GTN_MAX_REINICIOS_POR_RELATORIO=50
STALL_TIMEOUT_SEGUNDOS = int(os.environ.get("GTN_STALL_TIMEOUT_SEGUNDOS", "240"))
MAX_REINICIOS_POR_RELATORIO = int(os.environ.get("GTN_MAX_REINICIOS_POR_RELATORIO", "50"))

SCRIPTS = [
    "GTN_RELATORIO_01_Walceir_P1.py",
    "GTN_RELATORIO_02_Walceir_P2.py",
    "GTN_RELATORIO_03_Walceir_P3.py",
    "GTN_RELATORIO_04_Walceir_P9.py",
    "GTN_RELATORIO_05_LucasRamos_P1.py",
    "GTN_RELATORIO_06_LucasRamos_P2.py",
    "GTN_RELATORIO_07_LucasRamos_P3.py",
    "GTN_RELATORIO_08_LucasRamos_P9.py",
    "GTN_RELATORIO_09_Camila_P1.py",
    "GTN_RELATORIO_10_Camila_P2.py",
    "GTN_RELATORIO_11_Camila_P3.py",
    "GTN_RELATORIO_12_Camila_P9.py",
    "GTN_RELATORIO_13_RenatoMezzalira_P1.py",
    "GTN_RELATORIO_14_RenatoMezzalira_P2.py",
    "GTN_RELATORIO_15_RenatoMezzalira_P3.py",
    "GTN_RELATORIO_16_AdrielSilva_P1.py",
    "GTN_RELATORIO_17_AdrielSilva_P3.py",
    "GTN_RELATORIO_18_DeiseRosa_P1.py",
    "GTN_RELATORIO_19_DeiseRosa_P3.py",
]

RE_PROCESSANDO = re.compile(r"Processando\s+(editar_indice_\d+|tr_child_\d+)", re.IGNORECASE)
RE_ORIGEM_STATUS = re.compile(r"origem=(editar_indice_\d+|tr_child_\d+).*?status=([^ |]+)", re.IGNORECASE)
RE_LINHA_RELATORIOS = re.compile(r"Linha RELATORIOS:\s*([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^;]+);", re.IGNORECASE)

@dataclass
class EstadoRelatorio:
    nome_script: str
    editar_inicio_original: Optional[int] = None
    editar_fim_original: Optional[int] = None
    tr_inicio_original: Optional[int] = None
    tr_fim_original: Optional[int] = None
    atual_origem: Optional[str] = None
    ultimo_sucesso_origem: Optional[str] = None
    tentativas: int = 0
    resume_editar_inicio: Optional[int] = None
    resume_editar_fim: Optional[int] = None
    resume_tr_inicio: Optional[int] = None
    resume_tr_fim: Optional[int] = None

    def aplicar_linha_relatorios(self, linha: str) -> None:
        m = RE_LINHA_RELATORIOS.search(linha)
        if not m:
            return
        self.editar_inicio_original = int(m.group(4))
        self.editar_fim_original = int(m.group(5))
        self.tr_inicio_original = int(m.group(6))
        self.tr_fim_original = int(m.group(7))

    def registrar_linha(self, linha: str) -> None:
        m = RE_PROCESSANDO.search(linha)
        if m:
            self.atual_origem = m.group(1)
        m = RE_ORIGEM_STATUS.search(linha)
        if m:
            origem = m.group(1)
            status = m.group(2)
            if status.upper() in {"DOWNLOAD_OK", "PLACEHOLDER_GERADO", "SEM_EDIT_PLACEHOLDER"}:
                self.ultimo_sucesso_origem = origem
                self.atual_origem = None

    def montar_env_resume(self) -> dict[str, str]:
        env = {}
        tr_fim = self.tr_fim_original
        if self.atual_origem:
            origem = self.atual_origem
        else:
            origem = self.ultimo_sucesso_origem

        if not origem:
            return env

        # Se travou no TR, retoma do MESMO TR atual. Se só temos último sucesso, retoma do próximo porque o anterior já concluiu.
        if origem.startswith("tr_child_"):
            tr = int(origem.split("_")[-1])
            if not self.atual_origem:
                tr += 1
            env["GTN_RESUME_EDITAR_INICIO"] = "1"
            env["GTN_RESUME_EDITAR_FIM"] = "0"  # intervalo vazio; pula editar_indice
            env["GTN_RESUME_TR_INICIO"] = str(tr)
            if tr_fim is not None:
                env["GTN_RESUME_TR_FIM"] = str(tr_fim)
            return env

        # Se travou no editar_indice, retoma do MESMO indice e mantém TR original depois.
        if origem.startswith("editar_indice_"):
            idx = int(origem.split("_")[-1])
            if not self.atual_origem:
                idx += 1
            env["GTN_RESUME_EDITAR_INICIO"] = str(idx)
            if self.editar_fim_original is not None:
                env["GTN_RESUME_EDITAR_FIM"] = str(self.editar_fim_original)
            if self.tr_inicio_original is not None:
                env["GTN_RESUME_TR_INICIO"] = str(self.tr_inicio_original)
            if self.tr_fim_original is not None:
                env["GTN_RESUME_TR_FIM"] = str(self.tr_fim_original)
            return env

        return env


def _reader_thread(proc: subprocess.Popen, outq: queue.Queue) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        outq.put(line)
    outq.put(None)


def matar_processo(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=8)
        return
    except Exception:
        pass
    try:
        proc.kill()
        proc.wait(timeout=5)
    except Exception:
        pass


def rodar_script_resiliente(nome_script: str) -> int:
    estado = EstadoRelatorio(nome_script=nome_script)
    script_path = BASE_DIR / nome_script
    if not script_path.exists():
        print(f"[ERRO] Script não encontrado: {script_path}")
        return 1

    while True:
        estado.tentativas += 1
        env = os.environ.copy()
        env.update(estado.montar_env_resume())

        print("=" * 100)
        print(f"[EXECUTOR V7.1] Rodando {nome_script} | tentativa {estado.tentativas}/{MAX_REINICIOS_POR_RELATORIO}")
        if any(k.startswith("GTN_RESUME_") for k in env):
            print("[EXECUTOR V7.1] Retomada aplicada:")
            for k in sorted(k for k in env if k.startswith("GTN_RESUME_")):
                print(f"  {k}={env[k]}")
        print("=" * 100)

        proc = subprocess.Popen(
            [str(PYTHON_EXE), str(script_path)],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        outq: queue.Queue = queue.Queue()
        th = threading.Thread(target=_reader_thread, args=(proc, outq), daemon=True)
        th.start()

        ultimo_output = time.monotonic()
        ultimo_progresso = time.monotonic()
        terminou_stdout = False

        while True:
            try:
                item = outq.get(timeout=1)
            except queue.Empty:
                item = ""

            if item is None:
                terminou_stdout = True
            elif item:
                print(item, end="")
                ultimo_output = time.monotonic()
                antes = (estado.atual_origem, estado.ultimo_sucesso_origem)
                estado.aplicar_linha_relatorios(item)
                estado.registrar_linha(item)
                depois = (estado.atual_origem, estado.ultimo_sucesso_origem)
                if depois != antes or "[MÉTRICA]" in item or "[PLACEHOLDER]" in item:
                    ultimo_progresso = time.monotonic()

            rc = proc.poll()
            if rc is not None and terminou_stdout:
                if rc == 0:
                    print(f"\n[EXECUTOR V7.1] {nome_script} finalizado com sucesso.")
                    return 0
                print(f"\n[EXECUTOR V7.1][AVISO] {nome_script} terminou com código {rc}.")
                break

            sem_progresso = time.monotonic() - ultimo_progresso
            if sem_progresso >= STALL_TIMEOUT_SEGUNDOS:
                print("\n" + "!" * 100)
                print(f"[EXECUTOR V7.1][TRAVA] Sem progresso por {int(sem_progresso)}s em {nome_script}.")
                print(f"[EXECUTOR V7.1][TRAVA] Origem atual: {estado.atual_origem}")
                print(f"[EXECUTOR V7.1][TRAVA] Último sucesso: {estado.ultimo_sucesso_origem}")
                print("[EXECUTOR V7.1][TRAVA] Encerrando processo e tentando novamente o MESMO ponto travado. Nada será pulado.")
                print("!" * 100)
                matar_processo(proc)
                break

        if estado.tentativas >= MAX_REINICIOS_POR_RELATORIO:
            print(f"[EXECUTOR V7.1][ERRO] Limite de reinícios atingido para {nome_script}.")
            return 1

        resume = estado.montar_env_resume()
        if not resume:
            print(f"[EXECUTOR V7.1][ERRO] Não consegui determinar ponto de retomada para {nome_script}.")
            return 1

        time.sleep(5)


def main() -> int:
    print(f"[EXECUTOR V7.1] Python: {PYTHON_EXE}")
    print(f"[EXECUTOR V7.1] Pasta: {BASE_DIR}")
    print(f"[EXECUTOR V7.1] Timeout sem progresso: {STALL_TIMEOUT_SEGUNDOS}s")
    print(f"[EXECUTOR V7.1] Limite de reinícios por relatório: {MAX_REINICIOS_POR_RELATORIO}")
    print("[EXECUTOR V7.1] Política: NÃO PULAR cenário. Em trava, reinicia e tenta o mesmo editar_indice/tr_child.")

    falhas = []
    for script in SCRIPTS:
        rc = rodar_script_resiliente(script)
        if rc != 0:
            falhas.append(script)
            # Continua nos próximos para não perder a rodada inteira.

    print("=" * 100)
    if falhas:
        print("[EXECUTOR V7.1] Finalizado com falhas:")
        for f in falhas:
            print(f" - {f}")
        return 1

    print("[EXECUTOR V7.1] Todos os relatórios finalizados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
