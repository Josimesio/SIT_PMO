import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Playwright, TimeoutError as PlaywrightTimeoutError


LOGIN_URL = "https://gtn.ninecon.com.br/ords/r/gtn/gtn/login"
DOWNLOAD_DIR = Path("downloads")

USUARIO = os.getenv("GTN_USER")
SENHA = os.getenv("GTN_PASS")


def validar_credenciais():
    if not USUARIO or not SENHA:
        raise Exception(
    "Defina as variáveis de ambiente GTN_USER e GTN_PASS antes de rodar o script."
)


def fazer_login(page):
    print("Acessando GTN...")

    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    page.get_by_role("textbox", name="Usuário").fill(USUARIO)
    page.get_by_role("textbox", name="Senha").fill(SENHA)
    page.get_by_role("button", name="Acessar").click()

    page.wait_for_load_state("networkidle")

    print("Login executado.")


def abrir_execucao_de_testes(page):
    print("Abrindo menu de navegação...")

    page.get_by_role("button", name="Navegação Principal").click()

    try:
        page.get_by_role("treeitem", name="Execução de Testes").click(timeout=10000)
    except PlaywrightTimeoutError:
        print("Não encontrou o item pelo menu. Tentando URL direta...")
        page.goto(
            "https://gtn.ninecon.com.br/ords/r/gtn/gtn/execu%C3%A7%C3%A3o-dos-testes",
            wait_until="domcontentloaded"
        )

        page.wait_for_load_state("networkidle")

        print("Tela de execução de testes aberta.")


def configurar_relatorio(page):
    print("Configurando relatório...")

    page.locator("#R35932200234408468_saved_reports").select_option("36017690830433903")
    page.get_by_label("Linhas").select_option("1000")

    page.wait_for_timeout(1500)

    print("Relatório configurado.")


def abrir_primeiro_cenario(page):
    print("Abrindo primeiro cenário...")

    page.get_by_role("link", name="Editar").first.click()
    page.wait_for_timeout(2000)

    print("Primeiro cenário aberto.")


def fechar_modal(page):
    print("Fechando modal...")

    try:
        page.get_by_role("button", name="Fechar").click(timeout=5000)
    except PlaywrightTimeoutError:
        print("Botão Fechar não encontrado.")

        page.wait_for_timeout(1000)


def run(playwright: Playwright) -> None:
    validar_credenciais()

    DOWNLOAD_DIR.mkdir(exist_ok=True)

    browser = playwright.chromium.launch(
        headless=False,
        slow_mo=300
    )

    context = browser.new_context(
        accept_downloads=True
    )

    page = context.new_page()

    try:
        fazer_login(page)
        abrir_execucao_de_testes(page)
        configurar_relatorio(page)
        abrir_primeiro_cenario(page)
        fechar_modal(page)

        print("Script finalizado com sucesso.")

    except Exception as erro:
        print(f"Erro durante execução: {erro}")

    finally:
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)