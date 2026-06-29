# Script individual do RELATORIO_13_RenatoMezzalira_P1
# Padrao: carrega credenciais/env_RENATOMEZZALIRA_P1.env antes de importar o motor principal.
# Nao duplique credenciais no codigo. O .env manda; o script apenas escolhe o arquivo certo.

from pathlib import Path
import os


RELATORIO_INDICE = "13"
RELATORIO_NOME = "RELATORIO_13_RenatoMezzalira_P1"
ARQUIVO_ENV = "env_RENATOMEZZALIRA_P1.env"
MODULO_BASE = "Oficial_v1_PLACEHOLDER_COM_LINHA_PREENCHIDA_RELATORIOS_01_A_19"


BASE_DIR = Path(__file__).resolve().parent
CAMINHO_ENV = BASE_DIR / "credenciais" / ARQUIVO_ENV


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

            if "=" not in linha:
                print(f"[AVISO] Linha ignorada no .env {caminho_env.name}:{numero_linha} -> {linha}")
                continue

            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")

            if chave:
                os.environ[chave] = valor


def preparar_execucao_exclusiva() -> None:
    """Garante que o motor base rode somente o relatorio deste script."""
    os.environ["RELATORIO_UNICO_INDICE"] = RELATORIO_INDICE

    # Remove nomes antigos/alternativos que poderiam conflitar com o indice.
    for chave in (
        "RELATORIO_UNICO",
        "EXECUTAR_SOMENTE_RELATORIO",
        "SOMENTE_RELATORIO",
        "RELATORIO_UNICO_NOME",
        "RELATORIO_UNICO_SAVED_VALUE",
    ):
        os.environ.pop(chave, None)


def main() -> None:
    carregar_env(CAMINHO_ENV)
    preparar_execucao_exclusiva()

    print(f"[CONFIGURACAO] Relatorio: {RELATORIO_NOME}")
    print(f"[CONFIGURACAO] Indice travado: {RELATORIO_INDICE}")
    print(f"[CONFIGURACAO] Env carregado: {CAMINHO_ENV}")

    try:
        import Oficial_v1_PLACEHOLDER_COM_LINHA_PREENCHIDA_RELATORIOS_01_A_19 as base
    except ModuleNotFoundError as erro:
        print("")
        print("[ERRO] Motor principal nao encontrado.")
        print(f"Coloque este script na mesma pasta do arquivo: {MODULO_BASE}.py")
        print(f"Pasta atual: {BASE_DIR}")
        raise SystemExit(1) from erro

    base.run()


if __name__ == "__main__":
    main()
