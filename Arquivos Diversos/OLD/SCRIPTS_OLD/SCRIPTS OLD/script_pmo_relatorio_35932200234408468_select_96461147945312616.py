import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GTN_USUARIO = os.getenv("GTN_USUARIO") or os.getenv("GTN_USER")
GTN_SENHA = os.getenv("GTN_SENHA") or os.getenv("GTN_PASS")

URL_LOGIN = os.getenv(
    "URL_LOGIN",
    "https://gtn.ninecon.com.br/ords/r/gtn/gtn/login?session=601689329474445&tz=-3:00",
)

TIMEOUT_PADRAO = 60000

# ============================================================
# RELATÓRIO APEX
#
# RELATORIO_APEX_ID:
#   ID da região do relatório no Oracle APEX.
#   Exemplo na tela: #R35932200234408468_saved_reports
#
# RELATORIO_SALVO_VALUE:
#   VALUE real da opção dentro do combo de relatórios salvos.
#   Exemplo gravado pelo Playwright:
#   page.locator("#R35932200234408468_saved_reports").select_option("96461147945312616")
# ============================================================
RELATORIO_APEX_ID = os.getenv("RELATORIO_APEX_ID", "35932200234408468").strip()
RELATORIO_SALVO_VALUE = os.getenv("RELATORIO_SALVO_VALUE", "96461147945312616").strip()


def seletor_select_relatorio():
    return f"#R{RELATORIO_APEX_ID}_saved_reports"


def seletor_botao_ir_relatorio():
    return f"#R{RELATORIO_APEX_ID}_saved_reports_go"


def validar_env():
    if not GTN_USUARIO:
        raise Exception("Não encontrei GTN_USUARIO ou GTN_USER no arquivo .env.")

    if not GTN_SENHA:
        raise Exception("Não encontrei GTN_SENHA ou GTN_PASS no arquivo .env.")

    if not RELATORIO_APEX_ID:
        raise Exception("RELATORIO_APEX_ID não pode ficar vazio no .env.")

    if not RELATORIO_SALVO_VALUE:
        raise Exception("RELATORIO_SALVO_VALUE não pode ficar vazio no .env.")


def aguardar_carregamento(page):
    """Aguarda a página estabilizar sem quebrar caso o APEX mantenha requisições abertas."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=20000)
    except Exception:
        pass

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass


def listar_opcoes_relatorio(select_relatorio):
    """Lista opções do combo para diagnóstico quando o value não for encontrado."""
    try:
        return select_relatorio.evaluate(
            """
            el => Array.from(el.options).map(opt => ({
                value: opt.value,
                text: opt.textContent.trim(),
                selected: opt.selected
            }))
            """
        )
    except Exception as e:
        return [{"erro": str(e)}]


def selecionar_relatorio_apex(page):
    select_id = seletor_select_relatorio()
    botao_ir_id = seletor_botao_ir_relatorio()

    print(f"[14] Aguardando select do relatório APEX {RELATORIO_APEX_ID}...")
    print(f"[INFO] Select esperado: {select_id}")

    select_relatorio = page.locator(select_id)
    select_relatorio.wait_for(state="visible", timeout=TIMEOUT_PADRAO)

    page.wait_for_timeout(1000)

    print(f"[15] Selecionando relatório salvo pelo VALUE real: {RELATORIO_SALVO_VALUE}")

    try:
        # Equivalente ao comando gravado pelo Playwright:
        # page.locator("#R35932200234408468_saved_reports").select_option("96461147945312616")
        select_relatorio.select_option(value=RELATORIO_SALVO_VALUE, timeout=TIMEOUT_PADRAO)
    except Exception:
        print("[ERRO] Não consegui selecionar o relatório salvo pelo VALUE informado.")
        print("[DIAGNÓSTICO] Opções encontradas no combo:")
        for opcao in listar_opcoes_relatorio(select_relatorio):
            print(opcao)
        raise

    page.wait_for_timeout(3000)

    print(f"[16] Aguardando botão Ir do relatório APEX {RELATORIO_APEX_ID}...")
    print(f"[INFO] Botão Ir esperado: {botao_ir_id}")

    botao_ir = page.locator(botao_ir_id)

    try:
        botao_ir.wait_for(state="visible", timeout=15000)
    except Exception:
        print("[AVISO] Não encontrei botão Ir pelo ID exato. Tentando pelo botão Ir visível da tela.")
        botao_ir = page.get_by_role("button", name="Ir", exact=True)
        botao_ir.wait_for(state="visible", timeout=TIMEOUT_PADRAO)

    page.wait_for_timeout(1500)

    print(f"[17] Clicando no botão Ir do relatório APEX {RELATORIO_APEX_ID}...")
    botao_ir.click()

    page.wait_for_timeout(7000)
    aguardar_carregamento(page)

    print("[OK] Relatório selecionado e botão Ir executado.")
    print(f"[INFO] URL atual: {page.url}")


def run():
    validar_env()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            slow_mo=300,
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(TIMEOUT_PADRAO)

        try:
            print("[1] Abrindo tela de login...")
            page.goto(URL_LOGIN, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            print("[2] Preenchendo usuário...")
            campo_usuario = page.get_by_role("textbox", name="Usuário")
            campo_usuario.wait_for(state="visible")
            campo_usuario.fill(GTN_USUARIO)

            page.wait_for_timeout(800)

            print("[3] Indo para senha...")
            campo_usuario.press("Tab")
            page.wait_for_timeout(800)

            print("[4] Preenchendo senha...")
            campo_senha = page.get_by_role("textbox", name="Senha")
            campo_senha.wait_for(state="visible")
            campo_senha.fill(GTN_SENHA)

            page.wait_for_timeout(1000)

            print("[5] Clicando em Acessar...")
            botao_acessar = page.get_by_role("button", name="Acessar")
            botao_acessar.wait_for(state="visible")
            botao_acessar.click()

            print("[6] Aguardando pós-login/renderização...")
            page.wait_for_timeout(5000)
            aguardar_carregamento(page)
            page.wait_for_timeout(3000)

            print(f"[INFO] URL atual depois do login: {page.url}")

            print("[7] Aguardando botão Navegação Principal...")
            botao_nav = page.get_by_role("button", name="Navegação Principal")
            botao_nav.wait_for(state="visible", timeout=TIMEOUT_PADRAO)

            page.wait_for_timeout(1500)

            print("[8] Clicando em Navegação Principal...")
            botao_nav.click()
            page.wait_for_timeout(3000)

            print("[9] Aguardando toggle da árvore...")
            toggle_arvore = page.locator(".a-TreeView-toggle:visible").first
            toggle_arvore.wait_for(state="visible", timeout=TIMEOUT_PADRAO)

            page.wait_for_timeout(1000)

            print("[10] Clicando no toggle da árvore...")
            toggle_arvore.click()
            page.wait_for_timeout(3000)

            print("[11] Aguardando item Execução de Testes...")
            item_execucao = page.get_by_role("treeitem", name="Execução de Testes")
            item_execucao.wait_for(state="visible", timeout=TIMEOUT_PADRAO)

            page.wait_for_timeout(1000)

            print("[12] Clicando em Execução de Testes...")
            item_execucao.click()
            page.wait_for_timeout(7000)
            aguardar_carregamento(page)

            print("[OK] Clique em Execução de Testes executado.")
            print(f"[INFO] URL atual após clique em Execução de Testes: {page.url}")

            print("[13] Mantendo a página atual de Execução de Testes.")
            print("[INFO] Não vou usar page.goto com session/cs fixos, porque isso pode voltar para o login.")
            print(f"[INFO] URL atual válida: {page.url}")

            page.wait_for_timeout(7000)

            selecionar_relatorio_apex(page)

            print("[FIM] Script finalizado até a seleção/aplicação do relatório.")
            print("[INFO] O navegador ficará aberto para validação visual.")
            input("Pressione ENTER aqui no terminal para fechar o navegador...")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    try:
        run()
    except PlaywrightTimeoutError as e:
        print("[ERRO] Timeout no Playwright.")
        print(e)
        raise
    except Exception as e:
        print("[ERRO] Falha geral.")
        print(e)
        raise
