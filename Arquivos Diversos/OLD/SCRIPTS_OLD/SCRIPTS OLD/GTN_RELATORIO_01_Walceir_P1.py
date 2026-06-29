"""
GTN_RELATORIO_01_Walceir_P1.py
Versão de diagnóstico: sem métricas pesadas e com tempo por linha.

Como funciona:
- Carrega o .env da pasta credenciais.
- Desliga flags conhecidas de métricas/dashboard/consolidado durante execução.
- Executa somente o RELATORIO_01.
- Grava um CSV de tempo por linha em:
      logs_tempo_linhas/tempo_linhas_WALCEIR_P1.csv
- Mantém ativa a tela/janela de tempo do script base, caso exista.
- Mostra no terminal o tempo de cada linha assim que a linha fecha.

Observação importante:
Este chamador não altera o arquivo base. Ele mede o tempo pelas mensagens de terminal
que mencionam LINHA/TR. Para medição cirúrgica dentro da função exata de processamento,
é necessário ajustar o arquivo base Oficial_v1_PLACEHOLDER_COM_LINHA_PREENCHIDA_RELATORIOS_01_A_19.py.
"""

from __future__ import annotations

import atexit
import builtins
import csv
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_MODULE = "Oficial_v1_PLACEHOLDER_COM_LINHA_PREENCHIDA_RELATORIOS_01_A_19"
PASTA_CREDENCIAIS = "credenciais"

ENV_CANDIDATOS = (
    ".env_WALCEIR_P1_SEM_METRICAS",
    "env_WALCEIR_P1_SEM_METRICAS.env",
    ".env_WALCEIR_P1",
    "env_WALCEIR_P1.env",
    ".env_WALCEIR_P1.env",
    "ENV_WALCEIR_P1.env",
    "ENV_EXCLUSIVO_GTNR_RELATORIO_01_WALCEIR_P1.env",
)

FLAGS_CONFLITANTES = (
    "RELATORIO_UNICO",
    "EXECUTAR_SOMENTE_RELATORIO",
    "SOMENTE_RELATORIO",
    "RELATORIO_UNICO_NOME",
    "RELATORIO_UNICO_SAVED_VALUE",
)

# Flags defensivas. Se o arquivo base conhecer alguma delas, ele desliga a métrica.
# Se o arquivo base não conhecer, não quebra nada.
FLAGS_DESLIGAR_METRICAS = {
    "GERAR_METRICAS": "N",
    "GERAR_METRICAS_FINAL": "N",
    "GERAR_METRICAS_DURANTE_EXECUCAO": "N",
    "GERAR_RESUMO_METRICAS": "N",
    "GERAR_HTML_METRICAS": "N",
    "GERAR_DASHBOARD": "N",
    "ATUALIZAR_DASHBOARD": "N",
    "GERAR_PORTAL": "N",
    "GERAR_GRAFICOS": "N",
    "GERAR_INDICADORES": "N",
    "GERAR_CONSOLIDADO_FINAL": "N",
    "EXIBIR_TELA_TEMPO": "S",
    "LOG_DETALHADO": "N",
    "MODO_DIAGNOSTICO_TEMPO_LINHA": "S",
}


class CronometroLinhasTerminal:
    """Mede duração aproximada por linha usando as mensagens impressas no terminal."""

    RE_LINHA = re.compile(
        r"(?:\bLINHA\b|\bLinha\b|\blinha\b|\bTR\b|tr:nth-child)"
        r"[^0-9]{0,25}(\d{1,6})",
        re.IGNORECASE,
    )
    RE_PAGINA = re.compile(r"(?:PÁGINA|PAGINA|Página|pagina)\s*[:#\- ]*\s*(\d{1,6})", re.IGNORECASE)

    def __init__(self, caminho_csv: Path, mostrar_tela: bool = True) -> None:
        self.caminho_csv = caminho_csv
        self.mostrar_tela = mostrar_tela
        self.caminho_csv.parent.mkdir(parents=True, exist_ok=True)
        self.pagina_atual: Optional[str] = None
        self.linha_atual: Optional[str] = None
        self.inicio_perf: Optional[float] = None
        self.inicio_iso: Optional[str] = None
        self.ultimo_evento: str = ""
        self.contador = 0
        self._criar_cabecalho()

    def _criar_cabecalho(self) -> None:
        if self.caminho_csv.exists() and self.caminho_csv.stat().st_size > 0:
            return
        with self.caminho_csv.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "SEQ",
                "RELATORIO",
                "RESPONSAVEL",
                "PRIORIDADE",
                "PAGINA",
                "LINHA_TR",
                "INICIO",
                "FIM",
                "TEMPO_SEGUNDOS",
                "STATUS_FECHAMENTO",
                "ULTIMO_EVENTO",
            ])

    def observar_texto(self, texto: str) -> None:
        texto_limpo = " ".join(str(texto).split())
        if not texto_limpo:
            return

        pagina = self._extrair_pagina(texto_limpo)
        if pagina:
            self.pagina_atual = pagina

        linha = self._extrair_linha(texto_limpo)
        if linha:
            self._trocar_linha(linha, texto_limpo)
        elif self.linha_atual:
            self.ultimo_evento = texto_limpo[:500]

    def _extrair_pagina(self, texto: str) -> Optional[str]:
        achou = self.RE_PAGINA.search(texto)
        return achou.group(1) if achou else None

    def _extrair_linha(self, texto: str) -> Optional[str]:
        achou = self.RE_LINHA.search(texto)
        if not achou:
            return None
        return achou.group(1)

    def _trocar_linha(self, nova_linha: str, evento: str) -> None:
        if self.linha_atual is None:
            self._iniciar_linha(nova_linha, evento)
            return

        if nova_linha != self.linha_atual:
            self.finalizar_linha("FIM_POR_NOVA_LINHA")
            self._iniciar_linha(nova_linha, evento)
        else:
            self.ultimo_evento = evento[:500]

    def _iniciar_linha(self, linha: str, evento: str) -> None:
        self.linha_atual = linha
        self.inicio_perf = time.perf_counter()
        self.inicio_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ultimo_evento = evento[:500]

    def finalizar_linha(self, status: str = "FIM_EXECUCAO") -> None:
        if self.linha_atual is None or self.inicio_perf is None:
            return

        fim_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        segundos = round(time.perf_counter() - self.inicio_perf, 3)
        self.contador += 1

        pagina = self.pagina_atual or ""
        linha = self.linha_atual
        ultimo_evento = self.ultimo_evento

        with self.caminho_csv.open("a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                self.contador,
                "RELATORIO_01_Walceir_P1",
                "Walceir",
                "P1",
                pagina,
                linha,
                self.inicio_iso or "",
                fim_iso,
                str(segundos).replace(".", ","),
                status,
                ultimo_evento,
            ])

        if self.mostrar_tela:
            # Usa sys.__stdout__ para não alimentar novamente o monitor de print.
            msg = (
                f"[TEMPO LINHA] Página={pagina or '-'} | Linha/TR={linha} | "
                f"Tempo={segundos:.3f}s | Fechamento={status}\n"
            )
            try:
                sys.__stdout__.write(msg)
                sys.__stdout__.flush()
            except Exception:
                pass

        self.linha_atual = None
        self.inicio_perf = None
        self.inicio_iso = None
        self.ultimo_evento = ""


def encontrar_arquivo_env(pasta_script: Path) -> Path:
    pasta_credenciais = pasta_script / PASTA_CREDENCIAIS

    if not pasta_credenciais.exists():
        raise FileNotFoundError(
            f"Pasta de credenciais não encontrada: {pasta_credenciais}\n\n"
            "Crie a pasta 'credenciais' dentro da pasta do projeto."
        )

    for nome in ENV_CANDIDATOS:
        candidato = pasta_credenciais / nome
        if candidato.exists():
            return candidato

    encontrados = sorted(p.name for p in pasta_credenciais.iterdir() if p.is_file())
    lista_encontrados = "\n".join(f"       - {nome}" for nome in encontrados) or "       Nenhum arquivo encontrado."
    lista_esperados = "\n".join(f"       - credenciais/{nome}" for nome in ENV_CANDIDATOS)

    raise FileNotFoundError(
        "Nenhum arquivo .env aceito foi encontrado dentro da pasta credenciais.\n\n"
        "Nomes aceitos:\n"
        f"{lista_esperados}\n\n"
        "Arquivos encontrados na pasta credenciais:\n"
        f"{lista_encontrados}"
    )


def carregar_env_arquivo(caminho_env: Path, sobrescrever: bool = True) -> None:
    for numero_linha, linha in enumerate(caminho_env.read_text(encoding="utf-8-sig").splitlines(), start=1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if linha.lower().startswith("export "):
            linha = linha[7:].strip()
        if "=" not in linha:
            print(f"[AVISO] Linha ignorada no .env ({numero_linha}): {linha}")
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip()
        if not chave:
            continue
        if (valor.startswith('"') and valor.endswith('"')) or (valor.startswith("'") and valor.endswith("'")):
            valor = valor[1:-1]
        if sobrescrever or chave not in os.environ:
            os.environ[chave] = valor


def configurar_ambiente() -> tuple[Path, Path]:
    pasta_script = Path(__file__).resolve().parent
    os.chdir(pasta_script)
    if str(pasta_script) not in sys.path:
        sys.path.insert(0, str(pasta_script))

    caminho_env = encontrar_arquivo_env(pasta_script)
    carregar_env_arquivo(caminho_env, sobrescrever=True)

    for nome_variavel in FLAGS_CONFLITANTES:
        os.environ.pop(nome_variavel, None)

    os.environ["RELATORIO_UNICO_INDICE"] = "1"

    for chave, valor in FLAGS_DESLIGAR_METRICAS.items():
        os.environ[chave] = valor

    caminho_csv = Path(os.environ.get(
        "ARQUIVO_TEMPO_LINHAS",
        "logs_tempo_linhas/tempo_linhas_WALCEIR_P1.csv",
    ))
    if not caminho_csv.is_absolute():
        caminho_csv = pasta_script / caminho_csv

    mostrar_tempo_tela = os.environ.get("EXIBIR_TEMPO_LINHA_TELA", "S").strip().upper() not in {"N", "NAO", "NÃO", "FALSE", "0"}

    print(f"[CONFIGURAÇÃO] Credenciais carregadas de: {caminho_env}")
    print("[CONFIGURAÇÃO] Métricas/dashboard/consolidado desligados para diagnóstico de performance.")
    print("[CONFIGURAÇÃO] Tela/janela de tempo do script base: LIGADA")
    print(f"[CONFIGURAÇÃO] Tempo por linha será gravado em: {caminho_csv}")
    print(f"[CONFIGURAÇÃO] Exibir tempo de cada linha na tela: {'SIM' if mostrar_tempo_tela else 'NÃO'}")
    print("[CONFIGURAÇÃO] Execução travada no RELATORIO_01 - Walceir P1")

    return caminho_env, caminho_csv, mostrar_tempo_tela


def instalar_monitor_de_print(cronometro: CronometroLinhasTerminal) -> None:
    print_original = builtins.print

    def print_monitorado(*args, **kwargs):
        texto = " ".join(str(arg) for arg in args)
        try:
            cronometro.observar_texto(texto)
        except Exception:
            # Jamais deixar o monitor de tempo derrubar o processo principal.
            pass
        return print_original(*args, **kwargs)

    builtins.print = print_monitorado


def importar_motor_principal():
    try:
        return __import__(BASE_MODULE)
    except ModuleNotFoundError as erro:
        raise SystemExit(
            "[ERRO] Não encontrei o arquivo base:\n"
            f"       {BASE_MODULE}.py\n\n"
            "Coloque este script na mesma pasta do arquivo base."
        ) from erro


def main() -> None:
    try:
        _, caminho_csv, mostrar_tempo_tela = configurar_ambiente()
    except FileNotFoundError as erro:
        raise SystemExit(f"[ERRO] {erro}") from erro

    cronometro = CronometroLinhasTerminal(caminho_csv, mostrar_tela=mostrar_tempo_tela)
    instalar_monitor_de_print(cronometro)
    atexit.register(lambda: cronometro.finalizar_linha("FIM_EXECUCAO"))

    base = importar_motor_principal()
    if not hasattr(base, "run"):
        raise SystemExit(f"[ERRO] O módulo {BASE_MODULE}.py foi encontrado, mas não possui a função run().")

    inicio = time.perf_counter()
    try:
        base.run()
    finally:
        cronometro.finalizar_linha("FIM_EXECUCAO")
        total = round(time.perf_counter() - inicio, 3)
        print(f"[TEMPO TOTAL] Execução finalizada em {total} segundos.")
        print(f"[TEMPO LINHAS] CSV gerado em: {caminho_csv}")


if __name__ == "__main__":
    main()
