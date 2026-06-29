# Script individual do RELATORIO_17_AdrielSilva_P3
# Padrao V6.1: carrega credenciais/env_ADRIELSILVA_P3.env, normaliza o relatorio exclusivo, aplica metricas e otimizações seguras.
# Importante: cada .env especifico contem somente 1 relatorio. Por isso o indice interno usado no motor sempre e 1.

from __future__ import annotations

from pathlib import Path
import atexit
import builtins
import csv
import functools
import importlib.util
import os
import re
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Optional


RELATORIO_INDICE_ORIGINAL = "17"
RELATORIO_INDICE_MOTOR = "1"
RELATORIO_NOME = "RELATORIO_17_AdrielSilva_P3"
RELATORIO_LIDER = "AdrielSilva"
RELATORIO_PRIORIDADE = "P3"
RELATORIO_TOTAL_CENARIOS = "25"
RELATORIO_EDITAR_INICIO = "0"
RELATORIO_EDITAR_FIM = "5"
RELATORIO_TR_INICIO = "9"
RELATORIO_TR_FIM = "27"
# Compatibilidade com versões anteriores do wrapper/env.
RELATORIO_QTD = RELATORIO_TOTAL_CENARIOS
RELATORIO_APEX_ID = "35932200234408468"
RELATORIO_SAVED_VALUE = "96911676179989837"
ARQUIVO_ENV = "env_ADRIELSILVA_P3.env"

MODULOS_BASE_CANDIDATOS = (
    "Oficial_v1_PLACEHOLDER_COM_LINHA_PREENCHIDA_RELATORIOS_01_A_19",
    "Oficial_v1_PLACEHOLDER_COM_LINHA_PREENCHIDA",
)

BASE_DIR = Path(__file__).resolve().parent
CAMINHO_ENV = BASE_DIR / "credenciais" / ARQUIVO_ENV

CHAVES_CONFLITANTES = (
    "RELATORIO_UNICO",
    "EXECUTAR_SOMENTE_RELATORIO",
    "SOMENTE_RELATORIO",
    "RELATORIO_UNICO_NOME",
    "RELATORIO_UNICO_SAVED_VALUE",
)


def carregar_env(caminho_env: Path) -> None:
    """Carrega variaveis KEY=VALUE de um arquivo .env simples, sem depender de python-dotenv."""
    if not caminho_env.exists():
        print(f"[ERRO] Arquivo de credenciais nao encontrado: {caminho_env}")
        print("")
        print("Confirme se o arquivo esta exatamente neste caminho:")
        print(f"       credenciais/{ARQUIVO_ENV}")
        print("")
        print("Exemplo no Windows:")
        print(f"       {CAMINHO_ENV}")
        raise SystemExit(1)

    with caminho_env.open("r", encoding="utf-8-sig") as arquivo:
        for numero_linha, linha in enumerate(arquivo, start=1):
            linha = linha.strip()

            if not linha or linha.startswith("#"):
                continue

            if linha.lower().startswith("export "):
                linha = linha[7:].strip()

            if "=" not in linha:
                print(f"[AVISO] Linha ignorada no .env {caminho_env.name}:{numero_linha} -> {linha}")
                continue

            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")

            if chave:
                os.environ[chave] = valor


def montar_linha_relatorio() -> str:
    """Formato esperado pelo motor: nome|apex_id|saved_value|editar_inicio|editar_fim|tr_inicio|tr_fim;"""
    return (
        f"{RELATORIO_NOME}|{RELATORIO_APEX_ID}|{RELATORIO_SAVED_VALUE}|"
        f"{RELATORIO_EDITAR_INICIO}|{RELATORIO_EDITAR_FIM}|{RELATORIO_TR_INICIO}|{RELATORIO_TR_FIM};"
    )


def preparar_execucao_exclusiva() -> None:
    """Garante que o motor base rode somente o relatorio deste script."""
    for chave in CHAVES_CONFLITANTES:
        os.environ.pop(chave, None)

    os.environ["RELATORIO_UNICO_INDICE"] = RELATORIO_INDICE_MOTOR
    os.environ["RELATORIOS"] = montar_linha_relatorio()

    os.environ["RELATORIO_ORIGINAL_INDICE"] = RELATORIO_INDICE_ORIGINAL
    os.environ["RELATORIO_ATUAL_NOME"] = RELATORIO_NOME
    os.environ["RELATORIO_ATUAL_LIDER"] = RELATORIO_LIDER
    os.environ["RELATORIO_ATUAL_PRIORIDADE"] = RELATORIO_PRIORIDADE
    os.environ["RELATORIO_ATUAL_SAVED_VALUE"] = RELATORIO_SAVED_VALUE
    os.environ["RELATORIO_ATUAL_QTD"] = RELATORIO_QTD
    os.environ["RELATORIO_ATUAL_TOTAL_CENARIOS"] = RELATORIO_TOTAL_CENARIOS
    os.environ["RELATORIO_ATUAL_EDITAR_INICIO"] = RELATORIO_EDITAR_INICIO
    os.environ["RELATORIO_ATUAL_EDITAR_FIM"] = RELATORIO_EDITAR_FIM
    os.environ["RELATORIO_ATUAL_TR_INICIO"] = RELATORIO_TR_INICIO
    os.environ["RELATORIO_ATUAL_TR_FIM"] = RELATORIO_TR_FIM


def pastas_para_busca_motor() -> list[Path]:
    candidatos = []
    for pasta in (
        BASE_DIR,
        Path.cwd(),
        BASE_DIR.parent,
        Path(r"F:\REPOSITORIOS\SIT_PMO"),
    ):
        try:
            pasta_resolvida = pasta.resolve()
        except Exception:
            pasta_resolvida = pasta
        if pasta_resolvida not in candidatos:
            candidatos.append(pasta_resolvida)
    return candidatos


def localizar_motor_principal() -> tuple[str, Path]:
    """Localiza o arquivo do motor principal sem depender do import direto do Python."""
    candidatos_pasta = pastas_para_busca_motor()

    for nome_modulo in MODULOS_BASE_CANDIDATOS:
        nome_arquivo = f"{nome_modulo}.py"
        for pasta in candidatos_pasta:
            caminho = pasta / nome_arquivo
            if caminho.exists():
                print(f"[CONFIGURACAO] Motor principal encontrado: {caminho}")
                return nome_modulo, caminho

    print("")
    print("[ERRO] Motor principal nao encontrado.")
    print("Arquivos esperados:")
    for nome_modulo in MODULOS_BASE_CANDIDATOS:
        print(f" - {nome_modulo}.py")
    print(f"Pasta do script: {BASE_DIR}")
    print(f"Pasta atual: {Path.cwd()}")
    print("")
    print("Arquivos Oficial*.py* encontrados nas pastas verificadas:")

    encontrou = False
    for pasta in candidatos_pasta:
        if not pasta.exists() or not pasta.is_dir():
            continue
        for arquivo in sorted(pasta.glob("Oficial*.py*")):
            encontrou = True
            print(f" - {arquivo}")

    if not encontrou:
        print(" - Nenhum arquivo Oficial*.py* encontrado.")

    raise SystemExit(1)


def importar_motor_principal():
    """
    Importa o motor principal pelo caminho fisico do arquivo.
    Se faltar uma dependencia interna, mostra o modulo ausente e o traceback real.
    """
    nome_modulo, caminho_motor = localizar_motor_principal()

    pasta_motor = str(caminho_motor.parent)
    if pasta_motor not in sys.path:
        sys.path.insert(0, pasta_motor)

    try:
        spec = importlib.util.spec_from_file_location(nome_modulo, caminho_motor)
        if spec is None or spec.loader is None:
            raise ImportError(f"Nao foi possivel criar spec de importacao para: {caminho_motor}")

        modulo = importlib.util.module_from_spec(spec)
        sys.modules[nome_modulo] = modulo
        spec.loader.exec_module(modulo)
        return modulo

    except ModuleNotFoundError as erro:
        print("")
        print("[ERRO] O motor principal foi localizado, mas uma dependencia interna nao foi encontrada.")
        print(f"[ERRO] Motor localizado em: {caminho_motor}")
        print(f"[ERRO] Dependencia/modulo ausente: {erro.name}")
        print("")
        print("Traceback real para diagnostico:")
        traceback.print_exc()
        raise SystemExit(1) from erro

    except Exception as erro:
        print("")
        print("[ERRO] O motor principal foi localizado, mas falhou ao carregar/executar a importacao.")
        print(f"[ERRO] Motor localizado em: {caminho_motor}")
        print(f"[ERRO] Tipo: {type(erro).__name__}")
        print(f"[ERRO] Detalhe: {erro}")
        print("")
        print("Traceback real para diagnostico:")
        traceback.print_exc()
        raise SystemExit(1) from erro



# ======================================================================================
# MÉTRICAS REAIS DE EXECUÇÃO
# ======================================================================================

def env_bool(nome: str, padrao: bool = True) -> bool:
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().upper() not in {"N", "NAO", "NÃO", "FALSE", "0", "OFF", "DESLIGADO"}


def agora_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def nome_unico_metricas(caminho: Path, execucao_id: str) -> Path:
    """Evita PermissionError quando CSV antigo esta aberto no Excel/VSCode."""
    return caminho.with_name(f"{caminho.stem}_{execucao_id}{caminho.suffix}")


def caminho_fallback(caminho: Path, execucao_id: str) -> Path:
    """Fallback final se a pasta/arquivo principal estiver bloqueado."""
    pasta_fallback = caminho.parent / "fallback_metricas_bloqueadas"
    return pasta_fallback / f"{caminho.stem}_{execucao_id}_fallback{caminho.suffix}"


def garantir_csv(caminho: Path, cabecalho: list[str]) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists() and caminho.stat().st_size > 0:
        return caminho
    try:
        with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            writer.writerow(cabecalho)
        return caminho
    except PermissionError:
        # Arquivo provavelmente aberto no Excel. Nao derruba a automacao.
        alt = caminho.with_name(f"{caminho.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{caminho.suffix}")
        alt.parent.mkdir(parents=True, exist_ok=True)
        with alt.open("w", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            writer.writerow(cabecalho)
        print(f"[AVISO] CSV bloqueado: {caminho}")
        print(f"[AVISO] Gravando métricas em arquivo alternativo: {alt}")
        return alt


def anexar_csv(caminho: Path, linha: list[Any], cabecalho: Optional[list[str]] = None, execucao_id: str = "") -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    try:
        with caminho.open("a", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            writer.writerow(linha)
        return caminho
    except PermissionError:
        # Nao podemos deixar uma métrica matar o robô.
        # Excel costuma bloquear CSV aberto no Windows.
        alt = caminho_fallback(caminho, execucao_id or datetime.now().strftime("%Y%m%d_%H%M%S"))
        alt.parent.mkdir(parents=True, exist_ok=True)
        precisa_cabecalho = not alt.exists() or alt.stat().st_size == 0
        with alt.open("a", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            if precisa_cabecalho and cabecalho:
                writer.writerow(cabecalho)
            writer.writerow(linha)
        try:
            sys.__stdout__.write(f"[AVISO] CSV bloqueado pelo Windows/Excel: {caminho}\n")
            sys.__stdout__.write(f"[AVISO] Métrica gravada no fallback: {alt}\n")
            sys.__stdout__.flush()
        except Exception:
            pass
        return alt


def anexar_linhas_csv(caminho: Path, linhas: list[list[Any]], cabecalho: Optional[list[str]] = None, execucao_id: str = "") -> Path:
    """Grava várias linhas em uma única abertura de arquivo. V5 reduz overhead de métricas."""
    if not linhas:
        return caminho
    caminho.parent.mkdir(parents=True, exist_ok=True)
    try:
        with caminho.open("a", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            writer.writerows(linhas)
        return caminho
    except PermissionError:
        alt = caminho_fallback(caminho, execucao_id or datetime.now().strftime("%Y%m%d_%H%M%S"))
        alt.parent.mkdir(parents=True, exist_ok=True)
        precisa_cabecalho = not alt.exists() or alt.stat().st_size == 0
        with alt.open("a", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            if precisa_cabecalho and cabecalho:
                writer.writerow(cabecalho)
            writer.writerows(linhas)
        try:
            sys.__stdout__.write(f"[AVISO] CSV bloqueado pelo Windows/Excel: {caminho}\n")
            sys.__stdout__.write(f"[AVISO] Métricas gravadas no fallback: {alt}\n")
            sys.__stdout__.flush()
        except Exception:
            pass
        return alt


class MetricaExecucao:
    """
    Coletor leve de métricas reais.

    Gera 3 arquivos:
    - metricas_relatorios.csv: resumo da execução inteira.
    - metricas_linhas.csv: tempo por linha/cenário detectado no terminal.
    - metricas_etapas.csv: tempo das principais chamadas Playwright, quando possível.

    Observação:
    Para medir etapas funcionais exatas como "abrir iframe", "clicar edit", "salvar download"
    com 100% de precisão, o ideal é instrumentar também o motor principal. Este wrapper já
    mede as operações Playwright reais sem alterar o motor.
    """

    RE_PAGINA = re.compile(r"(?:PÁGINA|PAGINA|Página|pagina)\s*[:#\-\] ]*\s*(\d{1,6})", re.IGNORECASE)
    RE_LINHA = re.compile(
        r"(?:\bLINHA\b|\bLinha\b|\blinha\b|\bTR\b|tr:nth-child)"
        r"[^0-9]{0,35}(\d{1,6})",
        re.IGNORECASE,
    )

    def __init__(
        self,
        relatorio_nome: str,
        lider: str,
        prioridade: str,
        indice_original: str,
        saved_value: str,
    ) -> None:
        self.relatorio_nome = relatorio_nome
        self.lider = lider
        self.prioridade = prioridade
        self.indice_original = indice_original
        self.saved_value = saved_value

        self.habilitado = env_bool("MEDIR_METRICAS_REAIS", True)
        self.medir_playwright = env_bool("METRICAS_MEDIR_PLAYWRIGHT", True)
        self.salvar_etapas = env_bool("METRICAS_SALVAR_ETAPAS", True)
        self.exibir_tela = env_bool("METRICAS_EXIBIR_TELA", True)
        self.buffer_em_memoria = env_bool("METRICAS_BUFFER_EM_MEMORIA", True)
        self.ignorar_etapas = env_lista("METRICAS_IGNORAR_ETAPAS", "LOCATOR_COUNT")
        self._buffer_etapas: list[list[Any]] = []

        pasta = Path(os.environ.get("METRICAS_PASTA", "metricas_execucao"))
        if not pasta.is_absolute():
            pasta = BASE_DIR / pasta

        self.pasta = pasta
        self.execucao_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        arquivo_unico = env_bool("METRICAS_ARQUIVO_UNICO_POR_EXECUCAO", True)
        base_relatorios = self.pasta / "metricas_relatorios.csv"
        base_linhas = self.pasta / "metricas_linhas.csv"
        base_etapas = self.pasta / "metricas_etapas.csv"

        if arquivo_unico:
            self.arquivo_relatorios = nome_unico_metricas(base_relatorios, self.execucao_id)
            self.arquivo_linhas = nome_unico_metricas(base_linhas, self.execucao_id)
            self.arquivo_etapas = nome_unico_metricas(base_etapas, self.execucao_id)
        else:
            self.arquivo_relatorios = base_relatorios
            self.arquivo_linhas = base_linhas
            self.arquivo_etapas = base_etapas

        self.inicio_perf = time.perf_counter()
        self.inicio_iso = agora_iso()

        self.pagina_atual: str = ""
        self.linha_atual: str = ""
        self.inicio_linha_perf: Optional[float] = None
        self.inicio_linha_iso: str = ""
        self.ultimo_evento_linha: str = ""

        self.paginas_vistas: set[str] = set()
        self.total_linhas = 0
        self.total_downloads = 0
        self.total_sem_edit = 0
        self.total_nao_iniciado = 0
        self.total_erros = 0
        self.total_timeouts = 0
        self.total_etapas = 0
        self.total_etapas_erro = 0

        self.cabecalho_relatorios = [
            "EXECUCAO_ID",
            "RELATORIO",
            "INDICE_ORIGINAL",
            "LIDER",
            "PRIORIDADE",
            "SAVED_VALUE",
            "INICIO",
            "FIM",
            "TEMPO_TOTAL_SEGUNDOS",
            "TOTAL_PAGINAS",
            "TOTAL_LINHAS",
            "TOTAL_DOWNLOADS",
            "TOTAL_SEM_EDIT",
            "TOTAL_NAO_INICIADO",
            "TOTAL_ERROS",
            "TOTAL_TIMEOUTS",
            "TOTAL_ETAPAS_PLAYWRIGHT",
            "TOTAL_ETAPAS_ERRO",
            "LINHAS_POR_MINUTO",
            "STATUS_FINAL",
            "ERRO_FINAL",
        ]
        self.cabecalho_linhas = [
            "EXECUCAO_ID",
            "RELATORIO",
            "INDICE_ORIGINAL",
            "LIDER",
            "PRIORIDADE",
            "PAGINA",
            "LINHA_TR",
            "INICIO",
            "FIM",
            "TEMPO_TOTAL_LINHA_SEGUNDOS",
            "STATUS_FECHAMENTO",
            "ULTIMO_EVENTO",
        ]
        self.cabecalho_etapas = [
            "EXECUCAO_ID",
            "RELATORIO",
            "INDICE_ORIGINAL",
            "LIDER",
            "PRIORIDADE",
            "PAGINA",
            "LINHA_TR",
            "ETAPA",
            "INICIO",
            "FIM",
            "TEMPO_SEGUNDOS",
            "STATUS",
            "DETALHE",
            "ERRO",
        ]

        if self.habilitado:
            self.arquivo_relatorios = garantir_csv(self.arquivo_relatorios, self.cabecalho_relatorios)
            self.arquivo_linhas = garantir_csv(self.arquivo_linhas, self.cabecalho_linhas)
            self.arquivo_etapas = garantir_csv(self.arquivo_etapas, self.cabecalho_etapas)

    def observar_terminal(self, texto: str) -> None:
        if not self.habilitado:
            return

        texto_limpo = " ".join(str(texto).split())
        if not texto_limpo:
            return

        lower = texto_limpo.lower()

        pagina = self._extrair_pagina(texto_limpo)
        if pagina:
            self.pagina_atual = pagina
            self.paginas_vistas.add(pagina)

        linha = self._extrair_linha(texto_limpo)
        if linha:
            self._trocar_linha(linha, texto_limpo)
        elif self.linha_atual:
            self.ultimo_evento_linha = texto_limpo[:500]

        if "timeout" in lower:
            self.total_timeouts += 1
        if "[erro]" in lower or "erro" in lower or "exception" in lower:
            self.total_erros += 1
        if "sem edit" in lower or "sem botão edit" in lower or "sem botao edit" in lower:
            self.total_sem_edit += 1
        if "não iniciado" in lower or "nao iniciado" in lower:
            self.total_nao_iniciado += 1
        if "download" in lower and ("ok" in lower or "salvo" in lower or "finalizado" in lower or "baixado" in lower):
            self.total_downloads += 1

    def _extrair_pagina(self, texto: str) -> Optional[str]:
        achou = self.RE_PAGINA.search(texto)
        return achou.group(1) if achou else None

    def _extrair_linha(self, texto: str) -> Optional[str]:
        achou = self.RE_LINHA.search(texto)
        return achou.group(1) if achou else None

    def _trocar_linha(self, nova_linha: str, evento: str) -> None:
        if self.linha_atual == "":
            self._iniciar_linha(nova_linha, evento)
            return

        if nova_linha != self.linha_atual:
            self.finalizar_linha("FIM_POR_NOVA_LINHA")
            self._iniciar_linha(nova_linha, evento)
        else:
            self.ultimo_evento_linha = evento[:500]

    def _iniciar_linha(self, linha: str, evento: str) -> None:
        self.linha_atual = linha
        self.inicio_linha_perf = time.perf_counter()
        self.inicio_linha_iso = agora_iso()
        self.ultimo_evento_linha = evento[:500]

        if self.exibir_tela:
            self._stdout(
                f"[METRICA] Iniciando medição da linha/TR={linha} "
                f"| Página={self.pagina_atual or '-'}\n"
            )

    def finalizar_linha(self, status: str = "FIM_EXECUCAO") -> None:
        if not self.habilitado:
            return
        if not self.linha_atual or self.inicio_linha_perf is None:
            return

        fim_iso = agora_iso()
        segundos = round(time.perf_counter() - self.inicio_linha_perf, 3)
        self.total_linhas += 1

        self.arquivo_linhas = anexar_csv(self.arquivo_linhas, [
            self.execucao_id,
            self.relatorio_nome,
            self.indice_original,
            self.lider,
            self.prioridade,
            self.pagina_atual,
            self.linha_atual,
            self.inicio_linha_iso,
            fim_iso,
            str(segundos).replace(".", ","),
            status,
            self.ultimo_evento_linha,
        ], self.cabecalho_linhas, self.execucao_id)

        if self.exibir_tela:
            self._stdout(
                f"[METRICA LINHA] Relatório={self.relatorio_nome} "
                f"| Página={self.pagina_atual or '-'} "
                f"| Linha/TR={self.linha_atual} "
                f"| Tempo={segundos:.3f}s "
                f"| Status={status}\n"
            )

        self.linha_atual = ""
        self.inicio_linha_perf = None
        self.inicio_linha_iso = ""
        self.ultimo_evento_linha = ""

    def registrar_etapa(
        self,
        etapa: str,
        inicio_iso: str,
        tempo_segundos: float,
        status: str,
        detalhe: str = "",
        erro: str = "",
    ) -> None:
        if not self.habilitado or not self.salvar_etapas:
            return

        etapa_normalizada = str(etapa).upper()
        if etapa_normalizada in self.ignorar_etapas:
            return

        self.total_etapas += 1
        if status != "OK":
            self.total_etapas_erro += 1

        if "timeout" in (erro or "").lower():
            self.total_timeouts += 1

        linha_csv = [
            self.execucao_id,
            self.relatorio_nome,
            self.indice_original,
            self.lider,
            self.prioridade,
            self.pagina_atual,
            self.linha_atual,
            etapa,
            inicio_iso,
            agora_iso(),
            str(round(tempo_segundos, 3)).replace(".", ","),
            status,
            detalhe[:500],
            erro[:500],
        ]

        if self.buffer_em_memoria:
            self._buffer_etapas.append(linha_csv)
        else:
            self.arquivo_etapas = anexar_csv(self.arquivo_etapas, linha_csv, self.cabecalho_etapas, self.execucao_id)

    def flush_etapas(self) -> None:
        if not self.habilitado or not self.salvar_etapas:
            return
        if not self.buffer_em_memoria:
            return
        if not self._buffer_etapas:
            return
        self.arquivo_etapas = anexar_linhas_csv(
            self.arquivo_etapas,
            self._buffer_etapas,
            self.cabecalho_etapas,
            self.execucao_id,
        )
        self._buffer_etapas.clear()

    def finalizar_relatorio(self, status_final: str = "OK", erro_final: str = "") -> None:
        if not self.habilitado:
            return

        self.finalizar_linha("FIM_RELATORIO")
        self.flush_etapas()

        fim_iso = agora_iso()
        total_segundos = round(time.perf_counter() - self.inicio_perf, 3)
        linhas_por_minuto = round((self.total_linhas / total_segundos) * 60, 3) if total_segundos > 0 else 0

        self.arquivo_relatorios = anexar_csv(self.arquivo_relatorios, [
            self.execucao_id,
            self.relatorio_nome,
            self.indice_original,
            self.lider,
            self.prioridade,
            self.saved_value,
            self.inicio_iso,
            fim_iso,
            str(total_segundos).replace(".", ","),
            len(self.paginas_vistas),
            self.total_linhas,
            self.total_downloads,
            self.total_sem_edit,
            self.total_nao_iniciado,
            self.total_erros,
            self.total_timeouts,
            self.total_etapas,
            self.total_etapas_erro,
            str(linhas_por_minuto).replace(".", ","),
            status_final,
            erro_final[:500],
        ], self.cabecalho_relatorios, self.execucao_id)

        if self.exibir_tela:
            self._stdout(
                "\n"
                f"[METRICA RESUMO] Relatório={self.relatorio_nome}\n"
                f"[METRICA RESUMO] Tempo total={total_segundos:.3f}s | "
                f"Linhas={self.total_linhas} | "
                f"Páginas={len(self.paginas_vistas)} | "
                f"Etapas Playwright={self.total_etapas} | "
                f"Erros={self.total_erros} | "
                f"Timeouts={self.total_timeouts}\n"
                f"[METRICA RESUMO] Arquivos em: {self.pasta}\n"
                f"[METRICA RESUMO] Relatório CSV: {self.arquivo_relatorios}\n"
                f"[METRICA RESUMO] Linhas CSV: {self.arquivo_linhas}\n"
                f"[METRICA RESUMO] Etapas CSV: {self.arquivo_etapas}\n"
            )

    def _stdout(self, mensagem: str) -> None:
        try:
            sys.__stdout__.write(mensagem)
            sys.__stdout__.flush()
        except Exception:
            pass


def instalar_monitor_de_print(metricas: MetricaExecucao) -> None:
    if not metricas.habilitado:
        return

    print_original = builtins.print

    def print_monitorado(*args: Any, **kwargs: Any) -> Any:
        texto = " ".join(str(arg) for arg in args)
        try:
            metricas.observar_terminal(texto)
        except Exception:
            # Métrica não pode derrubar a execução principal.
            pass
        return print_original(*args, **kwargs)

    builtins.print = print_monitorado


def _detalhe_playwright_seguro(objeto: Any, metodo: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """
    Evita gravar senha, URL de sessão ou valores sensíveis.
    A ideia é medir tempo, não vazar dado.
    """
    try:
        nome_objeto = type(objeto).__name__
    except Exception:
        nome_objeto = "Objeto"

    if metodo in {"fill", "type", "press_sequentially"}:
        return f"{nome_objeto}.{metodo}(valor_oculto)"

    if metodo == "goto":
        return f"{nome_objeto}.{metodo}(url_oculta)"

    try:
        return f"{nome_objeto}.{metodo}"
    except Exception:
        return metodo



def env_int(nome: str, padrao: int) -> int:
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    try:
        return int(str(valor).strip())
    except Exception:
        return padrao


def env_lista(nome: str, padrao: str = "") -> set[str]:
    valor = os.environ.get(nome, padrao)
    partes = []
    for pedaco in str(valor).replace(";", ",").split(","):
        item = pedaco.strip().upper()
        if item:
            partes.append(item)
    return set(partes)


class ConfigOtimizacaoGTN:
    """Configuração de otimização controlada por .env."""

    def __init__(self) -> None:
        self.habilitada = env_bool("OTIMIZAR_ESPERAS_GTN", True)
        self.cap_wait_timeout = env_bool("OTIMIZAR_WAIT_FOR_TIMEOUT", True)
        self.cap_overlay = env_bool("OTIMIZAR_OVERLAY_APEX", True)
        self.cap_proximo = env_bool("OTIMIZAR_PROXIMO", True)
        self.cap_saved_report_go = env_bool("OTIMIZAR_SAVED_REPORT_GO", True)
        self.cap_slow_mo = env_bool("OTIMIZAR_SLOW_MO_BROWSER", True)
        # V6.1: evita sensação de travamento ao ler HTML do modal.
        # No log do Walceir P1, o inner_text do iframe aguardou 4000ms
        # antes de cair no fallback do identificador. Isso soma muito em volume.
        self.cap_modal_inner_text = env_bool("OTIMIZAR_MODAL_INNER_TEXT", True)

        # V6: conserva os ganhos da V5, mas corrige o gargalo real observado no log:
        # cenários SEM_EDIT aguardavam 15000ms cada antes de gerar placeholder.
        # O timeout do Edit agora é controlado por env, com padrão conservador de 5000ms.
        self.max_wait_timeout_ms = max(0, env_int("MAX_WAIT_FOR_TIMEOUT_MS", 450))
        self.overlay_timeout_ms = max(300, env_int("OVERLAY_TIMEOUT_MS", 1000))
        self.proximo_timeout_ms = max(300, env_int("PROXIMO_TIMEOUT_MS", 500))
        self.saved_report_go_timeout_ms = max(500, env_int("SAVED_REPORT_GO_TIMEOUT_MS", 2000))
        self.modal_inner_text_timeout_ms = max(800, env_int("MODAL_INNER_TEXT_TIMEOUT_MS", 1500))
        self.cap_timeout_edit_execucao = env_bool("OTIMIZAR_TIMEOUT_EDIT_EXECUCAO", True)
        self.timeout_edit_execucao_ms = max(1500, env_int("TIMEOUT_EDIT_EXECUCAO_OTIMIZADO_MS", 5000))
        self.slow_mo_browser_ms = max(0, env_int("SLOW_MO_BROWSER_MS", 0))
        # V3: não cortar waits fixos durante login/home/menu inicial.
        # O corte de Page.wait_for_timeout só entra quando a URL já é a tela de execução.
        self.wait_timeout_somente_execucao = env_bool("OTIMIZAR_WAIT_FOR_TIMEOUT_SOMENTE_EXECUCAO", True)


def _texto_locator_seguro(objeto: Any) -> str:
    try:
        return str(objeto)
    except Exception:
        try:
            return repr(objeto)
        except Exception:
            return ""


def _locator_parece_overlay_apex(objeto: Any) -> bool:
    texto = _texto_locator_seguro(objeto).lower()
    return ".ui-widget-overlay" in texto or "ui-widget-overlay" in texto


def _locator_parece_proximo(objeto: Any) -> bool:
    texto = _texto_locator_seguro(objeto).lower()
    # cobre Próximo, Proximo, aria-label, get_by_role e seletores APEX comuns.
    return (
        "próximo" in texto
        or "proximo" in texto
        or "pagination--next" in texto
        or "next" in texto and ("pagination" in texto or "aria-label" in texto)
    )


def _locator_parece_saved_report_go(objeto: Any) -> bool:
    texto = _texto_locator_seguro(objeto).lower()
    # Botão opcional do relatório salvo. Nas métricas ele esperou 15s e não apareceu,
    # mas o motor continuou normalmente. Então pode ter timeout menor.
    return "saved_reports_go" in texto


def _locator_parece_modal_cenario_execucoes(objeto: Any) -> bool:
    """Identifica leitura do HTML/texto do modal Cenário e Execuções."""
    texto = _texto_locator_seguro(objeto).lower()
    return (
        "cenário e execuções" in texto
        or "cenario e execucoes" in texto
        or "cenário e execuções" in texto
        or "iframe[title=\"cen" in texto
    ) and ("locator(\"html\")" in texto or "locator('html')" in texto or " html" in texto)



def _page_parece_tela_execucao(objeto: Any) -> bool:
    """Evita otimizar esperas fixas durante login/home/menu inicial."""
    try:
        url = str(getattr(objeto, "url", "") or "").lower()
    except Exception:
        url = ""

    if not url:
        return False

    # Durante login/home, o APEX precisa respirar. Mexer aqui quebrou o toggle da árvore.
    if "login" in url or url.rstrip("/").endswith("/home") or "/home" in url:
        return False

    # Só reduz espera fixa quando já estiver na área/tela de execução dos testes.
    termos_execucao = (
        "execu",
        "execucao",
        "execu%c3%a7%c3%a3o",
        "execu%C3%A7%C3%A3o".lower(),
        "execução",
        "teste",
    )
    return any(termo in url for termo in termos_execucao)

def _cap_timeout_kwargs(kwargs: dict[str, Any], novo_timeout: int) -> tuple[dict[str, Any], str]:
    """Retorna kwargs potencialmente ajustado e uma descrição do ajuste."""
    antigo = kwargs.get("timeout")
    if antigo is None:
        kwargs = dict(kwargs)
        kwargs["timeout"] = novo_timeout
        return kwargs, f"timeout definido para {novo_timeout}ms"

    try:
        antigo_int = int(antigo)
    except Exception:
        return kwargs, ""

    if antigo_int > novo_timeout:
        kwargs = dict(kwargs)
        kwargs["timeout"] = novo_timeout
        return kwargs, f"timeout reduzido de {antigo_int}ms para {novo_timeout}ms"

    return kwargs, ""


def instalar_medidor_playwright(metricas: MetricaExecucao) -> None:
    """
    Mede chamadas Playwright reais e aplica otimizações leves sem alterar o motor principal.

    Otimizações aplicadas quando ativadas no .env:
    - reduz esperas fixas Page.wait_for_timeout acima do teto configurado;
    - reduz timeout de espera do overlay APEX .ui-widget-overlay;
    - reduz timeout de ações/esperas em botão Próximo.

    A ideia é cortar espera burra, mantendo a execução funcional.
    """
    if not metricas.habilitado and not env_bool("OTIMIZAR_ESPERAS_GTN", True):
        return

    try:
        import playwright.sync_api._generated as generated
    except Exception as erro:
        print(f"[AVISO] Patch Playwright não instalado: {erro}")
        return

    otim = ConfigOtimizacaoGTN()

    def aplicar_patch(classe: Any, metodo: str, etapa: str) -> None:
        original = getattr(classe, metodo, None)
        if original is None:
            return
        if getattr(original, "_gtn_metricas_patch", False):
            return

        @functools.wraps(original)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            inicio_perf = time.perf_counter()
            inicio_iso = agora_iso()
            detalhe = _detalhe_playwright_seguro(self, metodo, args, kwargs)
            ajuste = ""
            args_ajustados = args
            kwargs_ajustados = kwargs

            # 0) Remover/reduzir slow_mo artificial do browser.
            # O motor principal abre o Chromium com slow_mo=300. Isso é ótimo para assistir,
            # mas ruim para rodar volume. V4 deixa isso controlado por .env.
            if otim.habilitada and otim.cap_slow_mo and etapa == "BROWSER_LAUNCH":
                try:
                    slow_mo_atual = kwargs.get("slow_mo")
                    if slow_mo_atual is not None and int(slow_mo_atual) > otim.slow_mo_browser_ms:
                        kwargs_ajustados = dict(kwargs_ajustados)
                        kwargs_ajustados["slow_mo"] = otim.slow_mo_browser_ms
                        ajuste = f"slow_mo reduzido de {int(slow_mo_atual)}ms para {otim.slow_mo_browser_ms}ms"
                except Exception:
                    pass

            # 1) Cortar espera fixa excessiva: page.wait_for_timeout(2000/3000/5000...)
            if otim.habilitada and otim.cap_wait_timeout and etapa == "PAGE_WAIT_TIMEOUT" and args:
                try:
                    espera_original = int(args[0])
                    pode_otimizar_wait = (
                        not otim.wait_timeout_somente_execucao
                        or _page_parece_tela_execucao(self)
                    )
                    if pode_otimizar_wait and espera_original > otim.max_wait_timeout_ms:
                        args_ajustados = (otim.max_wait_timeout_ms,) + tuple(args[1:])
                        ajuste = f"wait_for_timeout reduzido de {espera_original}ms para {otim.max_wait_timeout_ms}ms"
                    elif not pode_otimizar_wait:
                        # Mantém login/home/menu com a espera original. Foi aqui que a V2 ficou agressiva demais.
                        pass
                except Exception:
                    pass

            # 2) Cortar espera longa do overlay APEX que apareceu como maior gargalo.
            if otim.habilitada and otim.cap_overlay and etapa == "LOCATOR_WAIT_FOR" and _locator_parece_overlay_apex(self):
                estado = str(kwargs.get("state", "")).lower()
                if estado in {"hidden", "detached", ""}:
                    kwargs_ajustados, ajuste_overlay = _cap_timeout_kwargs(kwargs, otim.overlay_timeout_ms)
                    if ajuste_overlay:
                        ajuste = f"overlay APEX: {ajuste_overlay}"

            # 3) O botão saved_reports_go é opcional no GTN. Quando não aparece, não faz sentido aguardar 15s.
            if otim.habilitada and otim.cap_saved_report_go and etapa == "LOCATOR_WAIT_FOR" and _locator_parece_saved_report_go(self):
                kwargs_ajustados, ajuste_saved = _cap_timeout_kwargs(kwargs_ajustados, otim.saved_report_go_timeout_ms)
                if ajuste_saved:
                    ajuste = f"saved report go opcional: {ajuste_saved}"

            # 4) Não deixar botão Próximo consumir vários segundos no fim da última página.
            if otim.habilitada and otim.cap_proximo and _locator_parece_proximo(self):
                if etapa in {"LOCATOR_CLICK", "LOCATOR_WAIT_FOR", "LOCATOR_IS_VISIBLE"}:
                    kwargs_ajustados, ajuste_proximo = _cap_timeout_kwargs(kwargs_ajustados, otim.proximo_timeout_ms)
                    if ajuste_proximo:
                        ajuste = f"botão Próximo: {ajuste_proximo}"

            # 5) Reduzir leitura de texto/HTML do modal quando o motor já possui fallback.
            # Isso ataca o caso: Locator.inner_text timeout 4000ms no iframe Cenário e Execuções.
            if otim.habilitada and otim.cap_modal_inner_text and etapa == "LOCATOR_INNER_TEXT" and _locator_parece_modal_cenario_execucoes(self):
                kwargs_ajustados, ajuste_modal = _cap_timeout_kwargs(kwargs_ajustados, otim.modal_inner_text_timeout_ms)
                if ajuste_modal:
                    ajuste = f"modal cenário/execuções: {ajuste_modal}"

            if ajuste:
                detalhe = f"{detalhe} | OTIMIZADO: {ajuste}"

            try:
                resultado = original(self, *args_ajustados, **kwargs_ajustados)
                tempo = time.perf_counter() - inicio_perf
                if metricas.habilitado and metricas.medir_playwright:
                    metricas.registrar_etapa(etapa, inicio_iso, tempo, "OK", detalhe=detalhe)
                return resultado
            except Exception as erro:
                tempo = time.perf_counter() - inicio_perf
                if metricas.habilitado and metricas.medir_playwright:
                    metricas.registrar_etapa(
                        etapa,
                        inicio_iso,
                        tempo,
                        "ERRO",
                        detalhe=detalhe,
                        erro=f"{type(erro).__name__}: {erro}",
                    )
                raise

        wrapper._gtn_metricas_patch = True  # type: ignore[attr-defined]
        setattr(classe, metodo, wrapper)

    patches = [
        ("Page", "goto", "PAGE_GOTO"),
        ("Page", "reload", "PAGE_RELOAD"),
        ("Page", "wait_for_load_state", "PAGE_WAIT_LOAD_STATE"),
        ("Page", "wait_for_timeout", "PAGE_WAIT_TIMEOUT"),
        ("Page", "expect_download", "PAGE_PREPARAR_EXPECT_DOWNLOAD"),

        ("Locator", "click", "LOCATOR_CLICK"),
        ("Locator", "fill", "LOCATOR_FILL"),
        ("Locator", "select_option", "LOCATOR_SELECT_OPTION"),
        ("Locator", "wait_for", "LOCATOR_WAIT_FOR"),
        ("Locator", "text_content", "LOCATOR_TEXT_CONTENT"),
        ("Locator", "inner_text", "LOCATOR_INNER_TEXT"),
        ("Locator", "count", "LOCATOR_COUNT"),
        ("Locator", "is_visible", "LOCATOR_IS_VISIBLE"),
        ("Locator", "get_attribute", "LOCATOR_GET_ATTRIBUTE"),

        ("Download", "save_as", "DOWNLOAD_SAVE_AS"),
        ("Browser", "close", "BROWSER_CLOSE"),
        ("BrowserType", "launch", "BROWSER_LAUNCH"),
    ]

    total_patches = 0
    for nome_classe, metodo, etapa in patches:
        classe = getattr(generated, nome_classe, None)
        if classe is None:
            continue
        aplicar_patch(classe, metodo, etapa)
        total_patches += 1

    if metricas.exibir_tela:
        print(f"[CONFIGURACAO] Métricas/Otimizações Playwright ativadas. Patches tentados: {total_patches}")
        print(f"[CONFIGURACAO] Otimizar esperas GTN: {'SIM' if otim.habilitada else 'NAO'}")
        if otim.habilitada:
            print(f"[CONFIGURACAO] Teto Page.wait_for_timeout: {otim.max_wait_timeout_ms}ms")
            print(f"[CONFIGURACAO] Wait fixo otimizado somente na tela de execução: {'SIM' if otim.wait_timeout_somente_execucao else 'NAO'}")
            print(f"[CONFIGURACAO] Timeout overlay APEX: {otim.overlay_timeout_ms}ms")
            print(f"[CONFIGURACAO] Timeout botão Próximo: {otim.proximo_timeout_ms}ms")
            print(f"[CONFIGURACAO] Timeout saved_reports_go opcional: {otim.saved_report_go_timeout_ms}ms")
            print(f"[CONFIGURACAO] Timeout leitura modal Cenário/Execuções: {otim.modal_inner_text_timeout_ms}ms")
            print(f"[CONFIGURACAO] Timeout Edit execução: {otim.timeout_edit_execucao_ms}ms")
            print(f"[CONFIGURACAO] Browser slow_mo: {otim.slow_mo_browser_ms}ms")



def aplicar_timeout_edit_execucao_rapido() -> None:
    """
    Reduz o timeout de busca do link Edit quando o cenário não possui execução.

    No log da V5, cada SEM_EDIT consumiu ~18s porque o motor esperava 15000ms.
    Este ajuste força um valor mais prático, controlado por .env, sem mexer no motor.
    """
    if not env_bool("OTIMIZAR_TIMEOUT_EDIT_EXECUCAO", True):
        return

    timeout_ms = max(1500, env_int("TIMEOUT_EDIT_EXECUCAO_OTIMIZADO_MS", 5000))

    # Nome principal já usado no seu projeto. Os aliases são defensivos e não quebram nada
    # caso o motor use outro nome em alguma versão.
    chaves = (
        "TIMEOUT_EDIT_EXECUCAO",
        "TIMEOUT_LINK_EDIT",
        "TIMEOUT_BUSCA_EDIT",
        "TIMEOUT_EDIT_CENARIO",
    )
    for chave in chaves:
        os.environ[chave] = str(timeout_ms)




def main() -> None:
    carregar_env(CAMINHO_ENV)
    preparar_execucao_exclusiva()
    aplicar_timeout_edit_execucao_rapido()

    metricas = MetricaExecucao(
        relatorio_nome=RELATORIO_NOME,
        lider=RELATORIO_LIDER,
        prioridade=RELATORIO_PRIORIDADE,
        indice_original=RELATORIO_INDICE_ORIGINAL,
        saved_value=RELATORIO_SAVED_VALUE,
    )

    instalar_monitor_de_print(metricas)
    instalar_medidor_playwright(metricas)
    atexit.register(lambda: metricas.finalizar_linha("FIM_PROCESSO"))

    print(f"[CONFIGURACAO] Relatorio: {RELATORIO_NOME}")
    print(f"[CONFIGURACAO] Indice original do relatorio: {RELATORIO_INDICE_ORIGINAL}")
    print(f"[CONFIGURACAO] Indice usado no motor apos carregar env exclusivo: {RELATORIO_INDICE_MOTOR}")
    print(f"[CONFIGURACAO] Env carregado: {CAMINHO_ENV}")
    print(f"[CONFIGURACAO] Linha RELATORIOS: {os.environ['RELATORIOS']}")
    print(f"[CONFIGURACAO] TIMEOUT_EDIT_EXECUCAO efetivo: {os.environ.get('TIMEOUT_EDIT_EXECUCAO', '-') }ms")

    if metricas.habilitado:
        print("[CONFIGURACAO] Métricas reais: LIGADAS")
        print(f"[CONFIGURACAO] Pasta de métricas: {metricas.pasta}")
        print(f"[CONFIGURACAO] Medir chamadas Playwright: {'SIM' if metricas.medir_playwright else 'NAO'}")
        print(f"[CONFIGURACAO] Salvar detalhe de etapas: {'SIM' if metricas.salvar_etapas else 'NAO'}")
        print(f"[CONFIGURACAO] Buffer de etapas em memória: {'SIM' if metricas.buffer_em_memoria else 'NAO'}")
        print(f"[CONFIGURACAO] Etapas ignoradas: {', '.join(sorted(metricas.ignorar_etapas)) or '-'}")
        print(f"[CONFIGURACAO] Arquivo etapas: {metricas.arquivo_etapas}")
    else:
        print("[CONFIGURACAO] Métricas reais: DESLIGADAS")

    status_final = "OK"
    erro_final = ""

    try:
        base = importar_motor_principal()

        if not hasattr(base, "run"):
            raise SystemExit("[ERRO] O motor principal foi encontrado, mas nao possui a funcao run().")

        base.run()

    except BaseException as erro:
        status_final = "ERRO"
        erro_final = f"{type(erro).__name__}: {erro}"
        raise

    finally:
        metricas.finalizar_relatorio(status_final=status_final, erro_final=erro_final)


if __name__ == "__main__":
    main()
