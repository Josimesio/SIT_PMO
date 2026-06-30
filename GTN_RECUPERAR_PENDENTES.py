# -*- coding: utf-8 -*-
"""
GTN_RECUPERAR_PENDENTES.py

Recupera somente os cenários/linhas que não baixaram na execução principal do GTN.

O que este script faz:
1. Lê a métrica de linhas gerada pelo script principal.
2. Identifica registros pendentes de download.
3. Descobre qual .env usar pelo relatório original da linha.
4. Acessa o APEX/GTN com Playwright.
5. Processa apenas as linhas pendentes.
6. Se encontrar Edit/atividade, tenta baixar.
7. Se não encontrar Edit/atividade, cria placeholder no padrão mínimo.
8. Gera log de recuperação.

Como rodar:
    python GTN_RECUPERAR_PENDENTES.py --metricas metricas_linhas_20260629_084411.csv

Modo simulação, sem abrir navegador:
    python GTN_RECUPERAR_PENDENTES.py --metricas metricas_linhas_20260629_084411.csv --dry-run

Observação importante:
- O script foi feito para ser flexível com nomes de colunas diferentes.
- Para ficar 100% plug-and-play no seu ambiente, mantenha seus arquivos .env no padrão:
      credenciais/env_WALCEIR_P1.env
      credenciais/env_WALCEIR_P2.env
      credenciais/env_WALCEIR_P3.env
      credenciais/env_WALCEIR_P9.env
      credenciais/env_CAMILA_P1.env
      ...
- Se a métrica já tiver uma coluna ENV_FILE, o script usa ela acima de qualquer inferência.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
    PlaywrightTimeoutError = Exception


# ============================================================
# MAPEAMENTO PADRÃO RELATÓRIO -> .ENV
# Ajuste/complete aqui se surgirem novos relatórios.
# Se a métrica tiver coluna ENV_FILE, ela tem prioridade.
# ============================================================
MAPA_ENV_PADRAO = {
    "RELATORIO_01": "env_WALCEIR_P1.env",
    "RELATORIO_02": "env_WALCEIR_P2.env",
    "RELATORIO_03": "env_WALCEIR_P3.env",
    "RELATORIO_04": "env_WALCEIR_P9.env",
    "RELATORIO_05": "env_CAMILA_P1.env",
    "RELATORIO_06": "env_CAMILA_P2.env",
    "RELATORIO_07": "env_CAMILA_P3.env",
    "RELATORIO_08": "env_CAMILA_P9.env",
}

# Se aparecer "WALCEIR P1", "Walceir_P1", "CAMILA-P2" etc.
PADRAO_LIDER_PERIODO = re.compile(r"([A-ZÀ-Úa-zà-ú]+)[\s_\-]+P\s*(\d+)", re.IGNORECASE)


# ============================================================
# UTILITÁRIOS DE TEXTO / CSV
# ============================================================
def remover_acentos(texto: str) -> str:
    texto = str(texto or "")
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def chave_coluna(nome: str) -> str:
    nome = remover_acentos(nome).lower().strip()
    return re.sub(r"[^a-z0-9]+", "", nome)


def normalizar_texto(valor: object) -> str:
    return remover_acentos(str(valor or "")).lower().strip()


def limpar_nome_arquivo(valor: object, limite: int = 120) -> str:
    texto = remover_acentos(str(valor or "")).strip()
    texto = re.sub(r"[^A-Za-z0-9_.\-]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("._-")
    return (texto or "SEM_NOME")[:limite]


def sniff_delimitador(path: Path) -> str:
    amostra = path.read_bytes()[:8192]
    texto = ""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            texto = amostra.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialect = csv.Sniffer().sniff(texto, delimiters=";,\t|")
        return dialect.delimiter
    except Exception:
        return ";" if texto.count(";") >= texto.count(",") else ","


def ler_csv_flex(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    delimitador = sniff_delimitador(path)
    ultimo_erro = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f, delimiter=delimitador)
                linhas = [dict(row) for row in reader]
                campos = list(reader.fieldnames or [])
                return linhas, campos
        except UnicodeDecodeError as exc:
            ultimo_erro = exc
            continue
    raise RuntimeError(f"Não consegui ler o CSV {path}. Erro: {ultimo_erro}")


def escrever_csv(path: Path, linhas: List[Dict[str, object]], campos: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for row in linhas:
            writer.writerow({c: row.get(c, "") for c in campos})


def mapa_colunas(row: Dict[str, str]) -> Dict[str, str]:
    return {chave_coluna(k): k for k in row.keys()}


def valor_por_alias(row: Dict[str, str], aliases: Iterable[str], default: str = "") -> str:
    mapa = mapa_colunas(row)
    for alias in aliases:
        real = mapa.get(chave_coluna(alias))
        if real is not None:
            valor = row.get(real)
            if valor is not None and str(valor).strip() != "":
                return str(valor).strip()
    return default


def inteiro_ou_none(valor: object) -> Optional[int]:
    texto = str(valor or "").strip()
    if not texto:
        return None
    m = re.search(r"\d+", texto)
    return int(m.group(0)) if m else None


# ============================================================
# DETECÇÃO DE PENDÊNCIAS
# ============================================================
COLS_RELATORIO = [
    "RELATORIO", "RELATÓRIO", "NOME_RELATORIO", "NOME_RELATÓRIO", "COD_RELATORIO",
    "RELATORIO_ORIGEM", "ARQUIVO_SCRIPT", "SCRIPT", "FRENTE_RELATORIO",
]

COLS_ENV = ["ENV_FILE", "ARQUIVO_ENV", "ENV", "CREDENCIAL", "CREDENCIAIS"]
COLS_PAGINA = ["PAGINA", "PÁGINA", "PAGINA_APEX", "PÁGINA_APEX", "NUMERO_PAGINA"]
COLS_LINHA = ["LINHA", "ORIGEM_LINHA", "INDICE_LINHA", "ÍNDICE_LINHA", "ROW", "ROW_INDEX", "TR_NTH_CHILD"]
COLS_LIDER = ["LIDER_CENARIO", "LÍDER_CENÁRIO", "LIDER", "LÍDER", "RESPONSAVEL", "RESPONSÁVEL"]
COLS_STATUS = ["STATUS", "STATUS_CENARIO", "STATUS_CENÁRIO", "SITUACAO", "SITUAÇÃO"]
COLS_STATUS_DOWNLOAD = [
    "STATUS_DOWNLOAD", "DOWNLOAD", "BAIXOU", "ARQUIVO_BAIXADO", "STATUS_ARQUIVO",
    "STATUS_EDIT_CENARIO", "STATUS_EDIT_CENÁRIO", "RESULTADO", "RESULTADO_LINHA",
]
COLS_ERRO = ["ERRO", "MENSAGEM_ERRO", "EXCEPTION", "TIMEOUT", "OBS", "OBSERVACAO", "OBSERVAÇÃO"]
COLS_ARQUIVO = ["ARQUIVO", "ARQUIVO_BAIXADO", "CAMINHO_ARQUIVO", "PATH", "DOWNLOAD_PATH", "PLACEHOLDER"]
COLS_ID_CENARIO = [
    "IDENTIFICADOR_DE_CENARIO", "IDENTIFICADOR_DE_CENÁRIO", "IDENTIFICADOR CENARIO",
    "IDENTIFICADOR CENÁRIO", "ID_CENARIO", "ID_CENÁRIO", "CODIGO_CENARIO", "CÓDIGO_CENÁRIO",
]
COLS_NOME_CENARIO = ["NOME_CENARIO", "NOME_CENÁRIO", "CENARIO", "CENÁRIO", "DESCRICAO_CENARIO", "DESCRIÇÃO_CENÁRIO"]
COLS_COMANDO = ["COMANDO_CENARIO_EXECUCOES", "COMANDO", "COMANDO_EXECUCAO", "COMANDO_EXECUÇÃO"]

TERMOS_SUCESSO = [
    "baixado", "download ok", "download_ok", "sucesso", "ok", "arquivo gerado", "placeholder criado",
    "placeholder_criado", "sem edit placeholder", "sem_edit_placeholder", "nao iniciado placeholder",
    "não iniciado placeholder", "criado placeholder",
]

TERMOS_FALHA = [
    "falha", "erro", "timeout", "nao baixou", "não baixou", "sem download", "sem_download",
    "download falhou", "travou", "exception", "interrompido", "aborted", "failed", "pendente",
]


def extrair_identificador_do_comando(comando: str) -> str:
    """Extrai identificador de comandos do tipo get_by_text("BELLO.PTM.001.V2")."""
    if not comando:
        return ""
    m = re.search(r"get_by_text\([\"']([^\"']+)[\"']", comando)
    return m.group(1).strip() if m else ""


def arquivo_existe(valor: str, base_dir: Optional[Path] = None) -> bool:
    if not valor:
        return False
    candidatos = [Path(valor)]
    if base_dir and not Path(valor).is_absolute():
        candidatos.append(base_dir / valor)
    return any(p.exists() and p.is_file() and p.stat().st_size > 0 for p in candidatos)


def linha_ja_teve_sucesso(row: Dict[str, str], base_dir: Optional[Path] = None) -> bool:
    textos = []
    for cols in (COLS_STATUS_DOWNLOAD, COLS_ERRO):
        v = valor_por_alias(row, cols)
        if v:
            textos.append(normalizar_texto(v))

    texto = " | ".join(textos)

    # Caminho de arquivo existente vale como sucesso.
    for col in COLS_ARQUIVO:
        v = valor_por_alias(row, [col])
        if arquivo_existe(v, base_dir=base_dir):
            return True

    # Termos explícitos de sucesso.
    if any(t in texto for t in TERMOS_SUCESSO):
        # Cuidado: "ok" sozinho pode ser genérico, mas em métrica normalmente é intencional.
        return True

    return False


def linha_deve_recuperar(row: Dict[str, str], base_dir: Optional[Path] = None) -> bool:
    if linha_ja_teve_sucesso(row, base_dir=base_dir):
        return False

    textos_relevantes = []
    for cols in (COLS_STATUS_DOWNLOAD, COLS_ERRO):
        v = valor_por_alias(row, cols)
        if v:
            textos_relevantes.append(normalizar_texto(v))

    texto = " | ".join(textos_relevantes)

    if any(t in texto for t in TERMOS_FALHA):
        return True

    # Se há cenário/linha, mas não há arquivo nem status claro de sucesso, considera pendente.
    id_cenario = valor_por_alias(row, COLS_ID_CENARIO)
    nome_cenario = valor_por_alias(row, COLS_NOME_CENARIO)
    linha = valor_por_alias(row, COLS_LINHA)
    relatorio = valor_por_alias(row, COLS_RELATORIO)

    if relatorio and (id_cenario or nome_cenario or linha):
        # Se campos de download existem e estão vazios, é suspeito/pendente.
        mapa = mapa_colunas(row)
        tem_coluna_download = any(chave_coluna(c) in mapa for c in COLS_STATUS_DOWNLOAD + COLS_ARQUIVO)
        if tem_coluna_download:
            return True

    return False


# ============================================================
# ENV
# ============================================================
def carregar_env(path: Path) -> Dict[str, str]:
    env = {}
    if not path.exists():
        raise FileNotFoundError(f"Arquivo .env não encontrado: {path}")

    with path.open("r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            env[k] = v
    return env


def env_get(env: Dict[str, str], aliases: Iterable[str], default: str = "") -> str:
    mapa = {chave_coluna(k): k for k in env.keys()}
    for a in aliases:
        real = mapa.get(chave_coluna(a))
        if real:
            return env.get(real, default)
    return default


def inferir_env_file(row: Dict[str, str], cred_dir: Path) -> Path:
    # 1) Coluna explícita na métrica.
    env_col = valor_por_alias(row, COLS_ENV)
    if env_col:
        p = Path(env_col)
        if not p.is_absolute():
            p = cred_dir / env_col
        return p

    relatorio = valor_por_alias(row, COLS_RELATORIO)
    rel_norm = remover_acentos(relatorio).upper()

    # 2) RELATORIO_XX.
    m = re.search(r"RELATORIO[_\s\-]*(\d+)", rel_norm)
    if m:
        cod = f"RELATORIO_{int(m.group(1)):02d}"
        if cod in MAPA_ENV_PADRAO:
            return cred_dir / MAPA_ENV_PADRAO[cod]

    # 3) Nome do líder e período dentro do relatório: WALCEIR P1 => env_WALCEIR_P1.env.
    m = PADRAO_LIDER_PERIODO.search(relatorio)
    if m:
        nome = limpar_nome_arquivo(m.group(1)).upper()
        periodo = f"P{m.group(2)}"
        return cred_dir / f"env_{nome}_{periodo}.env"

    # 4) Tenta pelo líder + alguma marca Pn no relatório.
    lider = valor_por_alias(row, COLS_LIDER)
    combinado = f"{relatorio} {lider}"
    m = PADRAO_LIDER_PERIODO.search(combinado)
    if m:
        nome = limpar_nome_arquivo(m.group(1)).upper()
        periodo = f"P{m.group(2)}"
        return cred_dir / f"env_{nome}_{periodo}.env"

    raise RuntimeError(
        "Não consegui inferir o .env desta linha. "
        "Inclua uma coluna ENV_FILE na métrica ou complete MAPA_ENV_PADRAO no script. "
        f"Relatório lido: {relatorio!r}"
    )


# ============================================================
# MODELOS DE DADOS
# ============================================================
@dataclass
class RegistroPendente:
    original: Dict[str, str]
    indice_csv: int
    relatorio: str
    env_file: Path
    pagina: Optional[int]
    linha: Optional[int]
    lider: str
    status_cenario: str
    identificador: str
    nome_cenario: str
    comando: str


@dataclass
class ResultadoRecuperacao:
    indice_csv: int
    relatorio: str
    env_file: str
    pagina: str
    linha: str
    lider: str
    status_cenario: str
    identificador: str
    nome_cenario: str
    resultado: str
    arquivo_saida: str = ""
    mensagem: str = ""
    inicio: str = ""
    fim: str = ""
    duracao_seg: str = ""


# ============================================================
# PLAYWRIGHT - AÇÕES GENÉRICAS
# ============================================================
def primeiro_valor(*valores: str) -> str:
    for v in valores:
        if v:
            return v
    return ""


def seletor_saved_report(env: Dict[str, str]) -> str:
    seletor = env_get(env, ["SELECTOR_SAVED_REPORTS", "SAVED_REPORTS_SELECTOR", "SELETOR_SAVED_REPORTS"])
    if seletor:
        return seletor

    region_id = env_get(env, ["APEX_REGION_ID", "REGION_ID", "IRR_REGION_ID", "APEX_ID"])
    if region_id:
        return f"#R{region_id}_saved_reports"

    # Padrão do seu ambiente informado nas execuções anteriores.
    return "#R35932200234408468_saved_reports"


def valor_saved_report(env: Dict[str, str]) -> str:
    return env_get(env, [
        "SAVED_REPORT_VALUE", "RELATORIO_VALUE", "VALUE_RELATORIO", "SELECT_OPTION_VALUE",
        "APEX_SAVED_REPORT_VALUE", "SAVED_REPORT_OPTION", "REPORT_VALUE",
    ])


def url_inicial(env: Dict[str, str]) -> str:
    return env_get(env, ["URL", "BASE_URL", "APEX_URL", "GTN_URL", "LOGIN_URL", "URL_LOGIN"])


def usuario_env(env: Dict[str, str]) -> str:
    return env_get(env, ["USUARIO", "USUARIO_GTN", "USERNAME", "LOGIN", "USER", "APEX_USER"])


def senha_env(env: Dict[str, str]) -> str:
    return env_get(env, ["SENHA", "SENHA_GTN", "PASSWORD", "PASS", "APEX_PASSWORD"])


def tentar_preencher_primeiro(page, seletores: List[str], valor: str, timeout: int = 1500) -> bool:
    if not valor:
        return False
    for sel in seletores:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.fill(valor)
            return True
        except Exception:
            continue
    return False


def tentar_clicar_primeiro(page, seletores: List[str], timeout: int = 2000) -> bool:
    for sel in seletores:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(timeout=timeout)
            return True
        except Exception:
            continue
    return False


def login_se_necessario(page, env: Dict[str, str], timeout: int) -> None:
    """
    Login genérico.
    Se a página já estiver logada, não faz nada.
    Para ambientes mais chatos, ajuste no .env:
      SELECTOR_USUARIO=#P9999_USERNAME
      SELECTOR_SENHA=#P9999_PASSWORD
      SELECTOR_LOGIN=#B126_LOGIN
    """
    usuario = usuario_env(env)
    senha = senha_env(env)

    sel_usuario_env = env_get(env, ["SELECTOR_USUARIO", "SELETOR_USUARIO", "USERNAME_SELECTOR"])
    sel_senha_env = env_get(env, ["SELECTOR_SENHA", "SELETOR_SENHA", "PASSWORD_SELECTOR"])
    sel_login_env = env_get(env, ["SELECTOR_LOGIN", "SELETOR_LOGIN", "LOGIN_SELECTOR"])

    seletores_usuario = [s for s in [sel_usuario_env] if s] + [
        "#P9999_USERNAME", "#P101_USERNAME", "#P1_USERNAME",
        "input[name='p_t01']", "input[name='username']", "input[type='text']",
    ]
    seletores_senha = [s for s in [sel_senha_env] if s] + [
        "#P9999_PASSWORD", "#P101_PASSWORD", "#P1_PASSWORD",
        "input[name='p_t02']", "input[name='password']", "input[type='password']",
    ]
    seletores_login = [s for s in [sel_login_env] if s] + [
        "button:has-text('Entrar')", "button:has-text('Login')", "button:has-text('Sign In')",
        "input[type='submit']", "#B126_LOGIN", ".t-Button:has-text('Entrar')",
    ]

    preencheu_usuario = tentar_preencher_primeiro(page, seletores_usuario, usuario)
    preencheu_senha = tentar_preencher_primeiro(page, seletores_senha, senha)

    if preencheu_usuario and preencheu_senha:
        clicou = tentar_clicar_primeiro(page, seletores_login)
        if not clicou:
            page.keyboard.press("Enter")
        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass


def selecionar_relatorio_salvo(page, env: Dict[str, str], timeout: int) -> None:
    seletor = seletor_saved_report(env)
    value = valor_saved_report(env)

    if not value:
        # Se o .env não informar value, presume que a URL/script já abre no relatório correto.
        return

    page.locator(seletor).wait_for(state="visible", timeout=timeout)
    page.locator(seletor).select_option(value)
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    time.sleep(1)


def ir_para_pagina_apex(page, pagina: Optional[int], timeout: int) -> None:
    if not pagina or pagina <= 1:
        return

    for _ in range(pagina - 1):
        clicou = False
        candidatos = [
            "button:has-text('Próximo')",
            "button:has-text('Proximo')",
            "a:has-text('Próximo')",
            "a:has-text('Proximo')",
            "button:has-text('Next')",
            "a:has-text('Next')",
            ".a-IRR-pagination-item--next button",
            ".a-IRR-pagination-item--next a",
        ]
        for sel in candidatos:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_enabled():
                    loc.click(timeout=timeout)
                    clicou = True
                    break
            except Exception:
                continue

        if not clicou:
            raise RuntimeError(f"Não encontrei botão Próximo para chegar na página {pagina}.")

        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass
        time.sleep(1)


def abrir_linha_ou_cenario(page, reg: RegistroPendente, env: Dict[str, str], timeout: int) -> None:
    """Abre o cenário pela linha do IRR ou pelo identificador do cenário."""
    template = env_get(env, ["SELECTOR_LINHA_TEMPLATE", "SELETOR_LINHA_TEMPLATE"])
    if not template:
        template = "tr:nth-child({linha}) > .a-IRR-linkCol"

    # 1) Tenta linha específica.
    if reg.linha:
        seletor = template.format(linha=reg.linha)
        try:
            loc = page.locator(seletor).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click(timeout=timeout)
            try:
                page.wait_for_load_state("networkidle", timeout=timeout)
            except Exception:
                pass
            return
        except Exception:
            # Cai para identificador.
            pass

    # 2) Tenta pelo identificador exato.
    if reg.identificador:
        candidatos = [
            lambda: page.get_by_text(reg.identificador, exact=True).first,
            lambda: page.locator(f"text={reg.identificador}").first,
        ]
        for criar in candidatos:
            try:
                loc = criar()
                loc.wait_for(state="visible", timeout=timeout)
                loc.click(timeout=timeout)
                try:
                    page.wait_for_load_state("networkidle", timeout=timeout)
                except Exception:
                    pass
                return
            except Exception:
                continue

    raise RuntimeError(
        f"Não consegui abrir a linha/cenário. Linha={reg.linha}, Identificador={reg.identificador!r}"
    )


def frames_com_pagina(page):
    yield page
    for frame in page.frames:
        yield frame


def procurar_e_clicar_edit(page, env: Dict[str, str], timeout: int) -> bool:
    """
    Procura o primeiro Edit/Editar em page e iframes.
    Se seu ambiente exige um seletor específico, coloque no .env:
      SELECTOR_EDIT=a:has-text('Edit')
    """
    selector_edit = env_get(env, ["SELECTOR_EDIT", "SELETOR_EDIT"])
    seletores = [s for s in [selector_edit] if s] + [
        "a:has-text('Edit')",
        "button:has-text('Edit')",
        "span:has-text('Edit')",
        "a:has-text('Editar')",
        "button:has-text('Editar')",
        ".a-IRR-linkCol:has-text('Edit')",
        ".a-IRR-linkCol",
    ]

    for ctx in frames_com_pagina(page):
        for sel in seletores:
            try:
                loc = ctx.locator(sel).first
                if loc.count() > 0:
                    loc.wait_for(state="visible", timeout=min(timeout, 5000))
                    loc.click(timeout=timeout)
                    try:
                        page.wait_for_load_state("networkidle", timeout=timeout)
                    except Exception:
                        pass
                    return True
            except Exception:
                continue
    return False


def tentar_download_atividade(page, env: Dict[str, str], destino: Path, timeout: int) -> Tuple[bool, str]:
    """
    Tenta disparar download usando seletores comuns ou seletores do .env.
    Ajuste no .env se necessário:
      SELECTOR_DOWNLOAD_ATIVIDADE=button:has-text('Download')
    """
    selector_download = env_get(env, [
        "SELECTOR_DOWNLOAD_ATIVIDADE", "SELETOR_DOWNLOAD_ATIVIDADE", "SELECTOR_DOWNLOAD", "SELETOR_DOWNLOAD"
    ])
    seletores = [s for s in [selector_download] if s] + [
        "button:has-text('Download')",
        "a:has-text('Download')",
        "button:has-text('Baixar')",
        "a:has-text('Baixar')",
        "button:has-text('Exportar')",
        "a:has-text('Exportar')",
        "button:has-text('CSV')",
        "a:has-text('CSV')",
        "button:has-text('Excel')",
        "a:has-text('Excel')",
    ]

    destino.parent.mkdir(parents=True, exist_ok=True)

    for ctx in frames_com_pagina(page):
        for sel in seletores:
            try:
                loc = ctx.locator(sel).first
                if loc.count() <= 0:
                    continue
                loc.wait_for(state="visible", timeout=min(timeout, 5000))
                with page.expect_download(timeout=timeout) as download_info:
                    loc.click(timeout=timeout)
                download = download_info.value
                nome_sugerido = limpar_nome_arquivo(download.suggested_filename or destino.name)
                final = destino
                if final.suffix == "":
                    final = final.with_name(final.name + "_" + nome_sugerido)
                download.save_as(str(final))
                return True, str(final)
            except Exception:
                continue

    return False, "Não encontrei botão/link de download após abrir Edit."


def criar_placeholder(reg: RegistroPendente, output_dir: Path, motivo: str) -> str:
    pasta = output_dir / "placeholders"
    pasta.mkdir(parents=True, exist_ok=True)

    nome_base = "__".join([
        limpar_nome_arquivo(reg.relatorio),
        limpar_nome_arquivo(reg.lider),
        limpar_nome_arquivo(reg.identificador or reg.nome_cenario or f"LINHA_{reg.linha}"),
        "PLACEHOLDER",
    ])
    path = pasta / f"{nome_base}.csv"

    comando = reg.comando
    if not comando and reg.identificador:
        comando = (
            'page.locator("iframe[title=\\"Cenário e Execuções\\"]")'
            f'.content_frame.get_by_text("{reg.identificador}", exact=True).click()'
        )

    campos = [
        "LIDER_CENARIO",
        "STATUS_EDIT_CENARIO",
        "IDENTIFICADOR_DE_CENARIO",
        "COMANDO_CENARIO_EXECUCOES",
        "NOME_CENARIO",
        "PAGINA_APEX",
        "ORIGEM_LINHA",
        "MOTIVO_PLACEHOLDER",
        "DATA_GERACAO_PLACEHOLDER",
    ]

    linha = {
        "LIDER_CENARIO": reg.lider,
        "STATUS_EDIT_CENARIO": "SEM_EDIT_OU_SEM_ATIVIDADE",
        "IDENTIFICADOR_DE_CENARIO": reg.identificador,
        "COMANDO_CENARIO_EXECUCOES": comando,
        "NOME_CENARIO": reg.nome_cenario,
        "PAGINA_APEX": reg.pagina or "",
        "ORIGEM_LINHA": reg.linha or "",
        "MOTIVO_PLACEHOLDER": motivo,
        "DATA_GERACAO_PLACEHOLDER": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    escrever_csv(path, [linha], campos)
    return str(path)


def voltar_para_relatorio(page, env: Dict[str, str], timeout: int) -> None:
    seletor_voltar = env_get(env, ["SELECTOR_VOLTAR_RELATORIO", "SELETOR_VOLTAR_RELATORIO"])
    if seletor_voltar:
        try:
            page.locator(seletor_voltar).first.click(timeout=timeout)
            page.wait_for_load_state("networkidle", timeout=timeout)
            return
        except Exception:
            pass

    # Fallback prático: navegador voltar.
    try:
        page.go_back(wait_until="networkidle", timeout=timeout)
    except Exception:
        pass


# ============================================================
# PIPELINE
# ============================================================
def montar_registros_pendentes(
    linhas: List[Dict[str, str]],
    cred_dir: Path,
    base_dir_arquivos: Optional[Path],
    somente_relatorios: Optional[List[str]] = None,
    limite: Optional[int] = None,
) -> List[RegistroPendente]:
    pendentes: List[RegistroPendente] = []
    filtro_rel = {normalizar_texto(x) for x in (somente_relatorios or [])}

    for idx, row in enumerate(linhas, start=2):  # + cabeçalho do CSV
        relatorio = valor_por_alias(row, COLS_RELATORIO)
        if filtro_rel and normalizar_texto(relatorio) not in filtro_rel:
            # Também aceita trecho do texto.
            if not any(f in normalizar_texto(relatorio) for f in filtro_rel):
                continue

        if not linha_deve_recuperar(row, base_dir=base_dir_arquivos):
            continue

        comando = valor_por_alias(row, COLS_COMANDO)
        identificador = valor_por_alias(row, COLS_ID_CENARIO)
        if not identificador:
            identificador = extrair_identificador_do_comando(comando)

        nome_cenario = valor_por_alias(row, COLS_NOME_CENARIO)
        pagina = inteiro_ou_none(valor_por_alias(row, COLS_PAGINA))
        linha = inteiro_ou_none(valor_por_alias(row, COLS_LINHA))
        lider = valor_por_alias(row, COLS_LIDER)
        status_cenario = valor_por_alias(row, COLS_STATUS)

        try:
            env_file = inferir_env_file(row, cred_dir)
        except Exception as exc:
            # Mantém como pendente mesmo assim, para aparecer no CSV/log.
            env_file = Path(f"ERRO_INFERIR_ENV__{limpar_nome_arquivo(str(exc), 80)}")

        pendentes.append(
            RegistroPendente(
                original=row,
                indice_csv=idx,
                relatorio=relatorio,
                env_file=env_file,
                pagina=pagina,
                linha=linha,
                lider=lider,
                status_cenario=status_cenario,
                identificador=identificador,
                nome_cenario=nome_cenario,
                comando=comando,
            )
        )

        if limite and len(pendentes) >= limite:
            break

    return pendentes


def salvar_pendentes_detectados(pendentes: List[RegistroPendente], path: Path) -> None:
    campos = [
        "INDICE_CSV", "RELATORIO", "ENV_FILE", "PAGINA_APEX", "ORIGEM_LINHA",
        "LIDER_CENARIO", "STATUS_CENARIO", "IDENTIFICADOR_DE_CENARIO", "NOME_CENARIO",
        "COMANDO_CENARIO_EXECUCOES",
    ]
    linhas = []
    for r in pendentes:
        linhas.append({
            "INDICE_CSV": r.indice_csv,
            "RELATORIO": r.relatorio,
            "ENV_FILE": str(r.env_file),
            "PAGINA_APEX": r.pagina or "",
            "ORIGEM_LINHA": r.linha or "",
            "LIDER_CENARIO": r.lider,
            "STATUS_CENARIO": r.status_cenario,
            "IDENTIFICADOR_DE_CENARIO": r.identificador,
            "NOME_CENARIO": r.nome_cenario,
            "COMANDO_CENARIO_EXECUCOES": r.comando,
        })
    escrever_csv(path, linhas, campos)


def agrupar_por_env(pendentes: List[RegistroPendente]) -> Dict[Path, List[RegistroPendente]]:
    grupos: Dict[Path, List[RegistroPendente]] = {}
    for p in pendentes:
        grupos.setdefault(p.env_file, []).append(p)
    return grupos


def processar_pendentes_playwright(
    pendentes: List[RegistroPendente],
    output_dir: Path,
    headless: bool,
    timeout: int,
    slow_mo: int,
) -> List[ResultadoRecuperacao]:
    if sync_playwright is None:
        raise RuntimeError(
            "Playwright não está instalado/importável neste Python. Instale com:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        )

    resultados: List[ResultadoRecuperacao] = []
    grupos = agrupar_por_env(pendentes)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(timeout)

        for env_file, regs in grupos.items():
            if not env_file.exists():
                for reg in regs:
                    resultados.append(ResultadoRecuperacao(
                        indice_csv=reg.indice_csv,
                        relatorio=reg.relatorio,
                        env_file=str(env_file),
                        pagina=str(reg.pagina or ""),
                        linha=str(reg.linha or ""),
                        lider=reg.lider,
                        status_cenario=reg.status_cenario,
                        identificador=reg.identificador,
                        nome_cenario=reg.nome_cenario,
                        resultado="FALHA_ENV_NAO_ENCONTRADO",
                        mensagem=f"Arquivo .env não encontrado: {env_file}",
                    ))
                continue

            env = carregar_env(env_file)
            url = url_inicial(env)
            if not url:
                for reg in regs:
                    resultados.append(ResultadoRecuperacao(
                        indice_csv=reg.indice_csv,
                        relatorio=reg.relatorio,
                        env_file=str(env_file),
                        pagina=str(reg.pagina or ""),
                        linha=str(reg.linha or ""),
                        lider=reg.lider,
                        status_cenario=reg.status_cenario,
                        identificador=reg.identificador,
                        nome_cenario=reg.nome_cenario,
                        resultado="FALHA_URL_NAO_INFORMADA",
                        mensagem="Informe URL/APEX_URL/GTN_URL/LOGIN_URL no .env.",
                    ))
                continue

            print("=" * 100)
            print(f"[ENV] {env_file}")
            print(f"[QTD] {len(regs)} pendente(s)")
            print("=" * 100)

            try:
                page.goto(url, wait_until="networkidle", timeout=timeout)
                login_se_necessario(page, env, timeout)
                selecionar_relatorio_salvo(page, env, timeout)
            except Exception as exc:
                for reg in regs:
                    resultados.append(ResultadoRecuperacao(
                        indice_csv=reg.indice_csv,
                        relatorio=reg.relatorio,
                        env_file=str(env_file),
                        pagina=str(reg.pagina or ""),
                        linha=str(reg.linha or ""),
                        lider=reg.lider,
                        status_cenario=reg.status_cenario,
                        identificador=reg.identificador,
                        nome_cenario=reg.nome_cenario,
                        resultado="FALHA_ABRIR_RELATORIO",
                        mensagem=str(exc),
                    ))
                continue

            pagina_atual_processada = 1

            for reg in regs:
                inicio_dt = datetime.now()
                inicio = inicio_dt.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[RECUPERANDO] CSV linha {reg.indice_csv} | Relatório={reg.relatorio} | Página={reg.pagina} | Linha={reg.linha} | Cenário={reg.identificador or reg.nome_cenario}")

                try:
                    # Para evitar inconsistência ao mudar página/linha, recarrega o relatório salvo a cada item.
                    # É mais lento, mas mais seguro para recuperar pendências sem pular nada.
                    page.goto(url, wait_until="networkidle", timeout=timeout)
                    login_se_necessario(page, env, timeout)
                    selecionar_relatorio_salvo(page, env, timeout)
                    ir_para_pagina_apex(page, reg.pagina, timeout)

                    abrir_linha_ou_cenario(page, reg, env, timeout)

                    achou_edit = procurar_e_clicar_edit(page, env, timeout)
                    if not achou_edit:
                        placeholder = criar_placeholder(reg, output_dir, "Não encontrou Edit/atividade para esta linha.")
                        resultado = "PLACEHOLDER_CRIADO_SEM_EDIT"
                        mensagem = "Não encontrou Edit/atividade. Placeholder criado."
                        arquivo_saida = placeholder
                    else:
                        nome_saida = "__".join([
                            limpar_nome_arquivo(reg.relatorio),
                            limpar_nome_arquivo(reg.lider),
                            limpar_nome_arquivo(reg.identificador or reg.nome_cenario or f"LINHA_{reg.linha}"),
                            "RECUPERADO",
                        ])
                        destino = output_dir / "downloads" / f"{nome_saida}.csv"
                        ok, info = tentar_download_atividade(page, env, destino, timeout)
                        if ok:
                            resultado = "DOWNLOAD_RECUPERADO"
                            mensagem = "Download recuperado com sucesso."
                            arquivo_saida = info
                        else:
                            placeholder = criar_placeholder(reg, output_dir, info)
                            resultado = "PLACEHOLDER_CRIADO_SEM_DOWNLOAD"
                            mensagem = info
                            arquivo_saida = placeholder

                except Exception as exc:
                    try:
                        placeholder = criar_placeholder(reg, output_dir, f"Erro na recuperação: {exc}")
                        resultado = "PLACEHOLDER_CRIADO_COM_ERRO"
                        mensagem = str(exc)
                        arquivo_saida = placeholder
                    except Exception as exc2:
                        resultado = "FALHA_GERAL"
                        mensagem = f"Erro original: {exc} | Erro placeholder: {exc2}"
                        arquivo_saida = ""

                fim_dt = datetime.now()
                fim = fim_dt.strftime("%Y-%m-%d %H:%M:%S")
                duracao = f"{(fim_dt - inicio_dt).total_seconds():.2f}"

                print(f"[RESULTADO] {resultado} | {mensagem} | {arquivo_saida}")

                resultados.append(ResultadoRecuperacao(
                    indice_csv=reg.indice_csv,
                    relatorio=reg.relatorio,
                    env_file=str(env_file),
                    pagina=str(reg.pagina or ""),
                    linha=str(reg.linha or ""),
                    lider=reg.lider,
                    status_cenario=reg.status_cenario,
                    identificador=reg.identificador,
                    nome_cenario=reg.nome_cenario,
                    resultado=resultado,
                    arquivo_saida=arquivo_saida,
                    mensagem=mensagem,
                    inicio=inicio,
                    fim=fim,
                    duracao_seg=duracao,
                ))

        context.close()
        browser.close()

    return resultados


def salvar_log_resultados(resultados: List[ResultadoRecuperacao], path: Path) -> None:
    campos = [
        "INDICE_CSV", "RELATORIO", "ENV_FILE", "PAGINA_APEX", "ORIGEM_LINHA",
        "LIDER_CENARIO", "STATUS_CENARIO", "IDENTIFICADOR_DE_CENARIO", "NOME_CENARIO",
        "RESULTADO", "ARQUIVO_SAIDA", "MENSAGEM", "INICIO", "FIM", "DURACAO_SEG",
    ]
    linhas = []
    for r in resultados:
        linhas.append({
            "INDICE_CSV": r.indice_csv,
            "RELATORIO": r.relatorio,
            "ENV_FILE": r.env_file,
            "PAGINA_APEX": r.pagina,
            "ORIGEM_LINHA": r.linha,
            "LIDER_CENARIO": r.lider,
            "STATUS_CENARIO": r.status_cenario,
            "IDENTIFICADOR_DE_CENARIO": r.identificador,
            "NOME_CENARIO": r.nome_cenario,
            "RESULTADO": r.resultado,
            "ARQUIVO_SAIDA": r.arquivo_saida,
            "MENSAGEM": r.mensagem,
            "INICIO": r.inicio,
            "FIM": r.fim,
            "DURACAO_SEG": r.duracao_seg,
        })
    escrever_csv(path, linhas, campos)


def localizar_metrica_mais_recente() -> Optional[Path]:
    candidatos = []
    padroes = [
        "metricas_linhas_*.csv",
        "*metricas*linhas*.csv",
        "metricas_*.csv",
    ]
    for padrao in padroes:
        candidatos.extend(Path.cwd().glob(padrao))
    candidatos = [p for p in candidatos if p.is_file()]
    if not candidatos:
        return None
    return max(candidatos, key=lambda p: p.stat().st_mtime)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recupera somente linhas/cenários GTN que não baixaram.")
    parser.add_argument("--metricas", help="CSV de métricas de linhas. Ex.: metricas_linhas_20260629_084411.csv")
    parser.add_argument("--cred-dir", default="credenciais", help="Pasta dos .env. Padrão: credenciais")
    parser.add_argument("--output-dir", default="output/recuperacao_pendentes", help="Pasta de saída")
    parser.add_argument("--base-dir-arquivos", default=".", help="Base para validar arquivos já baixados citados na métrica")
    parser.add_argument("--somente-relatorio", action="append", help="Filtra relatório. Pode repetir. Ex.: --somente-relatorio RELATORIO_01")
    parser.add_argument("--limite", type=int, default=None, help="Limita quantidade de pendentes para teste")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout Playwright em ms. Padrão: 30000")
    parser.add_argument("--slow-mo", type=int, default=0, help="Slow motion Playwright em ms")
    parser.add_argument("--headless", action="store_true", help="Roda sem abrir navegador")
    parser.add_argument("--dry-run", action="store_true", help="Só identifica pendentes e gera CSV; não abre navegador")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    metricas = Path(args.metricas) if args.metricas else localizar_metrica_mais_recente()
    if not metricas:
        print("[ERRO] Informe --metricas ou deixe um arquivo metricas_linhas_*.csv na pasta atual.")
        return 2
    if not metricas.exists():
        print(f"[ERRO] Arquivo de métricas não encontrado: {metricas}")
        return 2

    cred_dir = Path(args.cred_dir)
    output_dir = Path(args.output_dir)
    base_dir_arquivos = Path(args.base_dir_arquivos) if args.base_dir_arquivos else None

    print("=" * 100)
    print("GTN - RECUPERAÇÃO DE PENDENTES")
    print(f"Métricas: {metricas}")
    print(f"Credenciais: {cred_dir}")
    print(f"Saída: {output_dir}")
    print("=" * 100)

    linhas, campos = ler_csv_flex(metricas)
    print(f"[INFO] Linhas lidas na métrica: {len(linhas)}")

    pendentes = montar_registros_pendentes(
        linhas=linhas,
        cred_dir=cred_dir,
        base_dir_arquivos=base_dir_arquivos,
        somente_relatorios=args.somente_relatorio,
        limite=args.limite,
    )

    pendentes_path = output_dir / "pendentes_para_recuperar.csv"
    salvar_pendentes_detectados(pendentes, pendentes_path)

    print(f"[INFO] Pendentes detectados: {len(pendentes)}")
    print(f"[INFO] Lista gerada: {pendentes_path}")

    if not pendentes:
        print("[OK] Nenhuma linha pendente detectada.")
        return 0

    print("\n[RESUMO POR ENV]")
    grupos = agrupar_por_env(pendentes)
    for env_file, regs in grupos.items():
        status = "OK" if env_file.exists() else "NÃO ENCONTRADO"
        print(f"  - {env_file}: {len(regs)} pendente(s) | {status}")

    if args.dry_run:
        print("\n[DRY-RUN] Simulação finalizada. Nenhum acesso ao GTN/APEX foi feito.")
        return 0

    resultados = processar_pendentes_playwright(
        pendentes=pendentes,
        output_dir=output_dir,
        headless=args.headless,
        timeout=args.timeout,
        slow_mo=args.slow_mo,
    )

    log_path = output_dir / f"log_recuperacao_pendentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    salvar_log_resultados(resultados, log_path)

    print("=" * 100)
    print("[FIM] Recuperação finalizada")
    print(f"Log: {log_path}")
    print("=" * 100)

    total_download = sum(1 for r in resultados if r.resultado == "DOWNLOAD_RECUPERADO")
    total_placeholder = sum(1 for r in resultados if r.resultado.startswith("PLACEHOLDER"))
    total_falha = len(resultados) - total_download - total_placeholder

    print(f"Downloads recuperados: {total_download}")
    print(f"Placeholders criados: {total_placeholder}")
    print(f"Falhas: {total_falha}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
