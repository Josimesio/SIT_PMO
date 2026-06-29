import os
import re
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
TIMEOUT_DOWNLOAD = 180000

# ============================================================
# RELATÓRIO APEX
#
# RELATORIO_APEX_ID:
#   ID da região do relatório no Oracle APEX.
#   Exemplo na tela: #R35932200234408468_saved_reports
#
# RELATORIO_SALVO_VALUE:
#   VALUE real da opção dentro do combo de relatórios salvos.
#   Comando validado:
#   page.locator("#R35932200234408468_saved_reports").select_option("96461147945312616")
# ============================================================
RELATORIO_APEX_ID = os.getenv("RELATORIO_APEX_ID", "35932200234408468").strip()
RELATORIO_SALVO_VALUE = os.getenv("RELATORIO_SALVO_VALUE", "96461147945312616").strip()

# ============================================================
# PROCESSAMENTO APÓS CARREGAR O RELATÓRIO
#
# Fluxo:
# 1) Seleciona o relatório salvo correto.
# 2) Clica no botão Ir do relatório correto.
# 3) Depois do print [INFO] URL atual, inicia os downloads.
# 4) Processa Editar first/nth(1..5).
# 5) Processa tr:nth-child(9) até tr:nth-child(1002).
# 6) Clica em Próximo e repete até não existir próximo.
# ============================================================
DOWNLOAD_DIR = BASE_DIR / os.getenv("DOWNLOAD_DIR", "downloads_gtn")

PROCESSAR_EDITAR_INICIAL = os.getenv("PROCESSAR_EDITAR_INICIAL", "S").strip().upper() == "S"
EDITAR_INDICE_INICIO = int(os.getenv("EDITAR_INDICE_INICIO", "0"))
EDITAR_INDICE_FIM = int(os.getenv("EDITAR_INDICE_FIM", "5"))

PROCESSAR_TR_CHILD = os.getenv("PROCESSAR_TR_CHILD", "S").strip().upper() == "S"
TR_CHILD_INICIO = int(os.getenv("TR_CHILD_INICIO", "9"))
TR_CHILD_FIM = int(os.getenv("TR_CHILD_FIM", "1002"))

# Evita travar 60s para cada linha inexistente no final da página.
TIMEOUT_LINHA_CURTO = int(os.getenv("TIMEOUT_LINHA_CURTO", "5000"))
MAX_LINHAS_INEXISTENTES_SEGUIDAS = int(os.getenv("MAX_LINHAS_INEXISTENTES_SEGUIDAS", "10"))


# ============================================================
# UTILITÁRIOS
# ============================================================
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

    aguardar_processamento_apex(page)


def aguardar_processamento_apex(page):
    """Tenta esperar overlays de processamento do Oracle APEX sumirem."""
    seletores = [
        ".u-Processing",
        ".a-Processing",
        ".apex_wait_overlay",
        ".ui-widget-overlay",
    ]

    for seletor in seletores:
        try:
            page.locator(seletor).first.wait_for(state="hidden", timeout=8000)
        except Exception:
            pass


def aguardar_relatorio_pronto(page):
    """Aguarda algum sinal de que o relatório renderizou."""
    aguardar_processamento_apex(page)

    try:
        page.get_by_role("cell", name="Editar").first.wait_for(state="visible", timeout=30000)
        return True
    except Exception:
        pass

    try:
        page.locator("tr > .a-IRR-linkCol").first.wait_for(state="visible", timeout=30000)
        return True
    except Exception:
        pass

    return False


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


def limpar_nome_arquivo(nome):
    nome = nome or "download"
    nome = re.sub(r'[\\/:*?"<>|]+', "_", nome)
    nome = re.sub(r"\s+", "_", nome).strip("._ ")
    return nome or "download"


def caminho_unico(caminho):
    """Evita sobrescrever arquivo se o nome já existir."""
    if not caminho.exists():
        return caminho

    base = caminho.stem
    ext = caminho.suffix
    pasta = caminho.parent

    contador = 2
    while True:
        novo = pasta / f"{base}_{contador}{ext}"
        if not novo.exists():
            return novo
        contador += 1


def obter_frame(page, titulo):
    iframe = page.locator(f'iframe[title="{titulo}"]').first
    iframe.wait_for(state="attached", timeout=TIMEOUT_PADRAO)

    try:
        iframe.wait_for(state="visible", timeout=TIMEOUT_PADRAO)
    except Exception:
        # Alguns iframes do APEX podem estar tecnicamente anexados, mas sem estado visible claro.
        pass

    return iframe.content_frame


# ============================================================
# SELEÇÃO DO RELATÓRIO
# ============================================================
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
    aguardar_relatorio_pronto(page)

    print("[OK] Relatório selecionado e botão Ir executado.")
    print(f"[INFO] URL atual: {page.url}")


# ============================================================
# MODAIS / JANELAS
# ============================================================
def fechar_modal_se_existir(page):
    """Fecha modais do APEX se existirem. Não quebra o fluxo se não encontrar."""
    tentativas = [
        lambda: page.get_by_role("dialog", name="Execução de Teste").get_by_label("Fechar"),
        lambda: page.get_by_role("dialog", name="Cenário e Execuções").get_by_label("Fechar"),
        lambda: page.get_by_role("button", name="Fechar"),
        lambda: page.locator("button[title='Fechar']"),
        lambda: page.locator("button[aria-label='Fechar']"),
        lambda: page.locator(".ui-dialog-titlebar-close"),
    ]

    for criar_locator in tentativas:
        try:
            locator = criar_locator().first
            if locator.count() > 0:
                locator.click(timeout=3000)
                page.wait_for_timeout(1000)
        except Exception:
            pass

    # Escape ajuda quando o modal ficou aberto, mas o botão não foi capturado.
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass

    aguardar_processamento_apex(page)


# ============================================================
# DOWNLOAD DE UMA EXECUÇÃO
# ============================================================
def baixar_execucao_aberta(page, origem, numero_pagina):
    """Com o modal de cenário aberto, entra no Edit e baixa a execução."""
    frame_cenario = obter_frame(page, "Cenário e Execuções")

    print(f"[VALIDAÇÃO] Verificando link Edit para {origem}...")
    link_edit = frame_cenario.get_by_role("link", name="Edit")

    try:
        link_edit.wait_for(state="visible", timeout=5000)
    except Exception:
        print(f"[SEM EDIT] {origem} não possui link Edit. Fechando e seguindo.")
        fechar_modal_se_existir(page)
        return False

    print(f"[DOWNLOAD] Clicando em Edit para {origem}...")
    link_edit.click(timeout=TIMEOUT_PADRAO)
    page.wait_for_timeout(2500)
    aguardar_processamento_apex(page)

    frame_execucao = obter_frame(page, "Execução de Teste")

    print(f"[DOWNLOAD] Abrindo Ações para {origem}...")
    frame_execucao.get_by_role("button", name="Ações", exact=True).click(timeout=TIMEOUT_PADRAO)
    page.wait_for_timeout(1200)

    print(f"[DOWNLOAD] Clicando em Fazer Download no menu para {origem}...")
    try:
        frame_execucao.get_by_role("menuitem", name="Fazer Download").click(timeout=5000)
    except Exception:
        frame_execucao.locator("span").filter(has_text="Fazer Download").click(timeout=5000)

    page.wait_for_timeout(1200)

    print(f"[DOWNLOAD] Confirmando Fazer Download para {origem}...")
    with page.expect_download(timeout=TIMEOUT_DOWNLOAD) as download_info:
        frame_execucao.get_by_role("button", name="Fazer Download").click(timeout=TIMEOUT_PADRAO)

    download = download_info.value
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    nome_original = limpar_nome_arquivo(download.suggested_filename)
    nome_final = f"pagina_{numero_pagina}_{limpar_nome_arquivo(origem)}_{nome_original}"
    destino = caminho_unico(DOWNLOAD_DIR / nome_final)

    download.save_as(str(destino))
    print(f"[OK] Download salvo em: {destino}")

    fechar_modal_se_existir(page)
    page.wait_for_timeout(1500)
    return True


def baixar_execucao_por_indice(page, indice, numero_pagina):
    origem = f"editar_indice_{indice}"

    try:
        print(f"[PÁGINA {numero_pagina}] Processando {origem}...")

        celulas_editar = page.get_by_role("cell", name="Editar")
        locator = celulas_editar.first if indice == 0 else celulas_editar.nth(indice)

        locator.wait_for(state="visible", timeout=TIMEOUT_LINHA_CURTO)
        locator.click(timeout=TIMEOUT_PADRAO)

        page.wait_for_timeout(2500)
        aguardar_processamento_apex(page)

        return baixar_execucao_aberta(page, origem, numero_pagina)

    except Exception as e:
        print(f"[ERRO] Falha em {origem}. Fechando janelas e seguindo.")
        print(f"[DETALHE] {e}")
        fechar_modal_se_existir(page)
        page.wait_for_timeout(1000)
        return False


def baixar_execucao_por_tr_child(page, linha_child, numero_pagina):
    origem = f"tr_child_{linha_child}"

    try:
        print(f"[PÁGINA {numero_pagina}] Processando tr:nth-child({linha_child})...")

        linha_link = page.locator(f"tr:nth-child({linha_child}) > .a-IRR-linkCol").first
        linha_link.wait_for(state="visible", timeout=TIMEOUT_LINHA_CURTO)

        linha_link.click(timeout=TIMEOUT_PADRAO)
        page.wait_for_timeout(2500)
        aguardar_processamento_apex(page)

        return baixar_execucao_aberta(page, origem, numero_pagina)

    except PlaywrightTimeoutError:
        print(f"[SEM LINHA] tr:nth-child({linha_child}) não encontrado/visível.")
        return None

    except Exception as e:
        print(f"[ERRO] Falha no tr:nth-child({linha_child}). Fechando janelas e seguindo.")
        print(f"[DETALHE] {e}")
        fechar_modal_se_existir(page)
        page.wait_for_timeout(1000)
        return False


# ============================================================
# PROCESSAMENTO DE PÁGINA / PAGINAÇÃO
# ============================================================
def processar_pagina_atual(page, numero_pagina):
    print("=" * 100)
    print(f"[PÁGINA {numero_pagina}] INICIANDO PROCESSAMENTO DA PÁGINA ATUAL")
    print("=" * 100)

    aguardar_relatorio_pronto(page)

    downloads_ok = 0
    sem_edit_ou_erro = 0
    linhas_inexistentes = 0

    if PROCESSAR_EDITAR_INICIAL:
        print(
            f"[PÁGINA {numero_pagina}] Processando Editar índice "
            f"{EDITAR_INDICE_INICIO} até {EDITAR_INDICE_FIM}..."
        )

        for indice in range(EDITAR_INDICE_INICIO, EDITAR_INDICE_FIM + 1):
            resultado = baixar_execucao_por_indice(page, indice, numero_pagina)

            if resultado is True:
                downloads_ok += 1
            else:
                sem_edit_ou_erro += 1

        print(
            f"[PÁGINA {numero_pagina}] Bloco Editar finalizado. "
            f"Downloads OK: {downloads_ok}. Sem Edit/erro: {sem_edit_ou_erro}."
        )

    if PROCESSAR_TR_CHILD:
        print(
            f"[PÁGINA {numero_pagina}] Processando tr:nth-child({TR_CHILD_INICIO}) "
            f"até tr:nth-child({TR_CHILD_FIM})..."
        )

        for linha_child in range(TR_CHILD_INICIO, TR_CHILD_FIM + 1):
            resultado = baixar_execucao_por_tr_child(page, linha_child, numero_pagina)

            if resultado is True:
                downloads_ok += 1
                linhas_inexistentes = 0
            elif resultado is None:
                linhas_inexistentes += 1

                if linhas_inexistentes >= MAX_LINHAS_INEXISTENTES_SEGUIDAS:
                    print(
                        f"[PÁGINA {numero_pagina}] {linhas_inexistentes} linhas seguidas não encontradas. "
                        "Encerrando varredura desta página."
                    )
                    break
            else:
                sem_edit_ou_erro += 1
                linhas_inexistentes = 0

        print(
            f"[PÁGINA {numero_pagina}] Bloco tr:nth-child finalizado. "
            f"Downloads OK: {downloads_ok}. Sem Edit/erro: {sem_edit_ou_erro}."
        )

    return {
        "downloads_ok": downloads_ok,
        "sem_edit_ou_erro": sem_edit_ou_erro,
    }


def clicar_proximo_se_existir(page, numero_pagina):
    print(f"[PÁGINA {numero_pagina}] Procurando botão Próximo...")

    candidatos = [
        lambda: page.get_by_role("button", name="Próximo").first,
        lambda: page.get_by_role("link", name="Próximo").first,
        lambda: page.locator("a[aria-label='Próximo']").first,
        lambda: page.locator("button[aria-label='Próximo']").first,
    ]

    for criar_locator in candidatos:
        try:
            botao_proximo = criar_locator()
            botao_proximo.wait_for(state="visible", timeout=5000)

            try:
                if not botao_proximo.is_enabled(timeout=2000):
                    print(f"[PÁGINA {numero_pagina}] Próximo encontrado, mas desabilitado. Fim.")
                    return False
            except Exception:
                pass

            print(f"[PÁGINA {numero_pagina}] Clicando em Próximo...")
            botao_proximo.click(timeout=TIMEOUT_PADRAO)

            print(f"[PÁGINA {numero_pagina}] Aguardando próxima página carregar...")
            page.wait_for_timeout(8000)
            aguardar_carregamento(page)
            aguardar_relatorio_pronto(page)
            page.wait_for_timeout(3000)

            print(f"[PÁGINA {numero_pagina}] Próxima página carregada. URL atual: {page.url}")
            return True

        except Exception:
            continue

    print(f"[PÁGINA {numero_pagina}] Não encontrei botão Próximo disponível. Processo encerrado.")
    return False


def processar_todas_as_paginas(page):
    print("=" * 100)
    print("[INÍCIO] Processamento após carregar o relatório")
    print("=" * 100)

    total_paginas = 0
    total_downloads_ok = 0
    total_sem_edit_ou_erro = 0

    numero_pagina = 1

    while True:
        resumo = processar_pagina_atual(page, numero_pagina)

        total_paginas += 1
        total_downloads_ok += resumo["downloads_ok"]
        total_sem_edit_ou_erro += resumo["sem_edit_ou_erro"]

        conseguiu_ir_proxima = clicar_proximo_se_existir(page, numero_pagina)

        if not conseguiu_ir_proxima:
            print("[FIM] Não existe mais botão Próximo disponível. Todos os cenários possíveis foram percorridos.")
            break

        numero_pagina += 1

    print("=" * 100)
    print("[RESUMO FINAL]")
    print(f"Total de páginas processadas: {total_paginas}")
    print(f"Total de downloads OK: {total_downloads_ok}")
    print(f"Total sem Edit/erro/pulados: {total_sem_edit_ou_erro}")
    print(f"Pasta de downloads: {DOWNLOAD_DIR}")
    print("=" * 100)


# ============================================================
# FLUXO PRINCIPAL
# ============================================================
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

            # ============================================================
            # AQUI COMEÇA O QUE VOCÊ PEDIU:
            # depois de carregar o relatório e imprimir [INFO] URL atual.
            # ============================================================
            processar_todas_as_paginas(page)

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
