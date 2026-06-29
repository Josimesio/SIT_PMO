# Script individual do RELATORIO_14_RenatoMezzalira_P2
# Padrao corrigido: carrega credenciais/env_RENATOMEZZALIRA_P2.env, normaliza o relatorio exclusivo e importa o motor principal.
# Importante: cada .env especifico contem somente 1 relatorio. Por isso o indice interno usado no motor sempre e 1.

from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import sys
import traceback


RELATORIO_INDICE_ORIGINAL = "14"
RELATORIO_INDICE_MOTOR = "1"
RELATORIO_NOME = "RELATORIO_14_RenatoMezzalira_P2"
RELATORIO_LIDER = "RenatoMezzalira"
RELATORIO_PRIORIDADE = "P2"
RELATORIO_QTD = "125"
RELATORIO_APEX_ID = "35932200234408468"
RELATORIO_SAVED_VALUE = "96840562521859779"
ARQUIVO_ENV = "env_RENATOMEZZALIRA_P2.env"

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
    return f"{RELATORIO_NOME}|{RELATORIO_APEX_ID}|{RELATORIO_SAVED_VALUE}|0|5|9|{RELATORIO_QTD};"


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


def main() -> None:
    carregar_env(CAMINHO_ENV)
    preparar_execucao_exclusiva()

    print(f"[CONFIGURACAO] Relatorio: {RELATORIO_NOME}")
    print(f"[CONFIGURACAO] Indice original do relatorio: {RELATORIO_INDICE_ORIGINAL}")
    print(f"[CONFIGURACAO] Indice usado no motor apos carregar env exclusivo: {RELATORIO_INDICE_MOTOR}")
    print(f"[CONFIGURACAO] Env carregado: {CAMINHO_ENV}")
    print(f"[CONFIGURACAO] Linha RELATORIOS: {os.environ['RELATORIOS']}")

    base = importar_motor_principal()

    if not hasattr(base, "run"):
        raise SystemExit("[ERRO] O motor principal foi encontrado, mas nao possui a funcao run().")

    base.run()


if __name__ == "__main__":
    main()
