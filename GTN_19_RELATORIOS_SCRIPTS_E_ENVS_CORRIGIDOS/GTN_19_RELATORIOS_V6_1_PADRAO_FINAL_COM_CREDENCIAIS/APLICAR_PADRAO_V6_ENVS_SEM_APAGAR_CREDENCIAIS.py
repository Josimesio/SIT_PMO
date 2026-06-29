from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil

BASE_DIR = Path(__file__).resolve().parent
PASTA_CREDENCIAIS = BASE_DIR / "credenciais"
PASTA_BACKUP = PASTA_CREDENCIAIS / ("backup_env_v6_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

RELATORIOS = [{'idx': 1, 'nome': 'RELATORIO_01_Walceir_P1', 'lider': 'Walceir', 'prioridade': 'P1', 'total': 45, 'saved': '96443782140269930', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 47, 'relatorios_line': 'RELATORIO_01_Walceir_P1|35932200234408468|96443782140269930|0|5|9|47;', 'arquivo_env': 'env_WALCEIR_P1.env', 'arquivo_script': 'GTN_RELATORIO_01_Walceir_P1.py'}, {'idx': 2, 'nome': 'RELATORIO_02_Walceir_P2', 'lider': 'Walceir', 'prioridade': 'P2', 'total': 38, 'saved': '96445783233272755', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 40, 'relatorios_line': 'RELATORIO_02_Walceir_P2|35932200234408468|96445783233272755|0|5|9|40;', 'arquivo_env': 'env_WALCEIR_P2.env', 'arquivo_script': 'GTN_RELATORIO_02_Walceir_P2.py'}, {'idx': 3, 'nome': 'RELATORIO_03_Walceir_P3', 'lider': 'Walceir', 'prioridade': 'P3', 'total': 27, 'saved': '96447734078275977', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 29, 'relatorios_line': 'RELATORIO_03_Walceir_P3|35932200234408468|96447734078275977|0|5|9|29;', 'arquivo_env': 'env_WALCEIR_P3.env', 'arquivo_script': 'GTN_RELATORIO_03_Walceir_P3.py'}, {'idx': 4, 'nome': 'RELATORIO_04_Walceir_P9', 'lider': 'Walceir', 'prioridade': 'P9', 'total': 148, 'saved': '96461147945312616', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 150, 'relatorios_line': 'RELATORIO_04_Walceir_P9|35932200234408468|96461147945312616|0|5|9|150;', 'arquivo_env': 'env_WALCEIR_P9.env', 'arquivo_script': 'GTN_RELATORIO_04_Walceir_P9.py'}, {'idx': 5, 'nome': 'RELATORIO_05_LucasRamos_P1', 'lider': 'LucasRamos', 'prioridade': 'P1', 'total': 88, 'saved': '96466495992333195', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 90, 'relatorios_line': 'RELATORIO_05_LucasRamos_P1|35932200234408468|96466495992333195|0|5|9|90;', 'arquivo_env': 'env_LUCASRAMOS_P1.env', 'arquivo_script': 'GTN_RELATORIO_05_LucasRamos_P1.py'}, {'idx': 6, 'nome': 'RELATORIO_06_LucasRamos_P2', 'lider': 'LucasRamos', 'prioridade': 'P2', 'total': 31, 'saved': '96468946665336064', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 33, 'relatorios_line': 'RELATORIO_06_LucasRamos_P2|35932200234408468|96468946665336064|0|5|9|33;', 'arquivo_env': 'env_LUCASRAMOS_P2.env', 'arquivo_script': 'GTN_RELATORIO_06_LucasRamos_P2.py'}, {'idx': 7, 'nome': 'RELATORIO_07_LucasRamos_P3', 'lider': 'LucasRamos', 'prioridade': 'P3', 'total': 14, 'saved': '96470998136338958', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 16, 'relatorios_line': 'RELATORIO_07_LucasRamos_P3|35932200234408468|96470998136338958|0|5|9|16;', 'arquivo_env': 'env_LUCASRAMOS_P3.env', 'arquivo_script': 'GTN_RELATORIO_07_LucasRamos_P3.py'}, {'idx': 8, 'nome': 'RELATORIO_08_LucasRamos_P9', 'lider': 'LucasRamos', 'prioridade': 'P9', 'total': 10, 'saved': '96473161397342454', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 12, 'relatorios_line': 'RELATORIO_08_LucasRamos_P9|35932200234408468|96473161397342454|0|5|9|12;', 'arquivo_env': 'env_LUCASRAMOS_P9.env', 'arquivo_script': 'GTN_RELATORIO_08_LucasRamos_P9.py'}, {'idx': 9, 'nome': 'RELATORIO_09_Camila_P1', 'lider': 'Camila', 'prioridade': 'P1', 'total': 87, 'saved': '96454201749302012', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 89, 'relatorios_line': 'RELATORIO_09_Camila_P1|35932200234408468|96454201749302012|0|5|9|89;', 'arquivo_env': 'env_CAMILA_P1.env', 'arquivo_script': 'GTN_RELATORIO_09_Camila_P1.py'}, {'idx': 10, 'nome': 'RELATORIO_10_Camila_P2', 'lider': 'Camila', 'prioridade': 'P2', 'total': 36, 'saved': '96451968465288102', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 38, 'relatorios_line': 'RELATORIO_10_Camila_P2|35932200234408468|96451968465288102|0|5|9|38;', 'arquivo_env': 'env_CAMILA_P2.env', 'arquivo_script': 'GTN_RELATORIO_10_Camila_P2.py'}, {'idx': 11, 'nome': 'RELATORIO_11_Camila_P3', 'lider': 'Camila', 'prioridade': 'P3', 'total': 3, 'saved': '96449983914285918', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 2, 'tr_inicio': 9, 'tr_fim': 8, 'relatorios_line': 'RELATORIO_11_Camila_P3|35932200234408468|96449983914285918|0|2|9|8;', 'arquivo_env': 'env_CAMILA_P3.env', 'arquivo_script': 'GTN_RELATORIO_11_Camila_P3.py'}, {'idx': 12, 'nome': 'RELATORIO_12_Camila_P9', 'lider': 'Camila', 'prioridade': 'P9', 'total': 39, 'saved': '96456284157307243', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 41, 'relatorios_line': 'RELATORIO_12_Camila_P9|35932200234408468|96456284157307243|0|5|9|41;', 'arquivo_env': 'env_CAMILA_P9.env', 'arquivo_script': 'GTN_RELATORIO_12_Camila_P9.py'}, {'idx': 13, 'nome': 'RELATORIO_13_RenatoMezzalira_P1', 'lider': 'RenatoMezzalira', 'prioridade': 'P1', 'total': 313, 'saved': '96836102112838540', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 315, 'relatorios_line': 'RELATORIO_13_RenatoMezzalira_P1|35932200234408468|96836102112838540|0|5|9|315;', 'arquivo_env': 'env_RENATOMEZZALIRA_P1.env', 'arquivo_script': 'GTN_RELATORIO_13_RenatoMezzalira_P1.py'}, {'idx': 14, 'nome': 'RELATORIO_14_RenatoMezzalira_P2', 'lider': 'RenatoMezzalira', 'prioridade': 'P2', 'total': 125, 'saved': '96840562521859779', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 127, 'relatorios_line': 'RELATORIO_14_RenatoMezzalira_P2|35932200234408468|96840562521859779|0|5|9|127;', 'arquivo_env': 'env_RENATOMEZZALIRA_P2.env', 'arquivo_script': 'GTN_RELATORIO_14_RenatoMezzalira_P2.py'}, {'idx': 15, 'nome': 'RELATORIO_15_RenatoMezzalira_P3', 'lider': 'RenatoMezzalira', 'prioridade': 'P3', 'total': 231, 'saved': '96838388851852063', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 233, 'relatorios_line': 'RELATORIO_15_RenatoMezzalira_P3|35932200234408468|96838388851852063|0|5|9|233;', 'arquivo_env': 'env_RENATOMEZZALIRA_P3.env', 'arquivo_script': 'GTN_RELATORIO_15_RenatoMezzalira_P3.py'}, {'idx': 16, 'nome': 'RELATORIO_16_AdrielSilva_P1', 'lider': 'AdrielSilva', 'prioridade': 'P1', 'total': 3, 'saved': '96896222567721463', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 2, 'tr_inicio': 9, 'tr_fim': 8, 'relatorios_line': 'RELATORIO_16_AdrielSilva_P1|35932200234408468|96896222567721463|0|2|9|8;', 'arquivo_env': 'env_ADRIELSILVA_P1.env', 'arquivo_script': 'GTN_RELATORIO_16_AdrielSilva_P1.py'}, {'idx': 17, 'nome': 'RELATORIO_17_AdrielSilva_P3', 'lider': 'AdrielSilva', 'prioridade': 'P3', 'total': 25, 'saved': '96911676179989837', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 27, 'relatorios_line': 'RELATORIO_17_AdrielSilva_P3|35932200234408468|96911676179989837|0|5|9|27;', 'arquivo_env': 'env_ADRIELSILVA_P3.env', 'arquivo_script': 'GTN_RELATORIO_17_AdrielSilva_P3.py'}, {'idx': 18, 'nome': 'RELATORIO_18_DeiseRosa_P1', 'lider': 'DeiseRosa', 'prioridade': 'P1', 'total': 111, 'saved': '96898268944724974', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 5, 'tr_inicio': 9, 'tr_fim': 113, 'relatorios_line': 'RELATORIO_18_DeiseRosa_P1|35932200234408468|96898268944724974|0|5|9|113;', 'arquivo_env': 'env_DEISEROSA_P1.env', 'arquivo_script': 'GTN_RELATORIO_18_DeiseRosa_P1.py'}, {'idx': 19, 'nome': 'RELATORIO_19_DeiseRosa_P3', 'lider': 'DeiseRosa', 'prioridade': 'P3', 'total': 2, 'saved': '96913647909993268', 'apex': '35932200234408468', 'edit_inicio': 0, 'edit_fim': 1, 'tr_inicio': 9, 'tr_fim': 8, 'relatorios_line': 'RELATORIO_19_DeiseRosa_P3|35932200234408468|96913647909993268|0|1|9|8;', 'arquivo_env': 'env_DEISEROSA_P3.env', 'arquivo_script': 'GTN_RELATORIO_19_DeiseRosa_P3.py'}]

CHAVES_GERENCIADAS = {
    "RELATORIOS", "RELATORIO_UNICO_INDICE", "RELATORIO_ORIGINAL_INDICE",
    "RELATORIO_ATUAL_NOME", "RELATORIO_ATUAL_LIDER", "RELATORIO_ATUAL_PRIORIDADE",
    "RELATORIO_ATUAL_SAVED_VALUE", "RELATORIO_ATUAL_QTD", "RELATORIO_ATUAL_TOTAL_CENARIOS",
    "RELATORIO_ATUAL_EDITAR_INICIO", "RELATORIO_ATUAL_EDITAR_FIM", "RELATORIO_ATUAL_TR_INICIO",
    "RELATORIO_ATUAL_TR_FIM", "RELATORIO_UNICO", "EXECUTAR_SOMENTE_RELATORIO",
    "SOMENTE_RELATORIO", "RELATORIO_UNICO_NOME", "RELATORIO_UNICO_SAVED_VALUE",
    "MEDIR_METRICAS_REAIS", "METRICAS_MEDIR_PLAYWRIGHT", "METRICAS_SALVAR_ETAPAS",
    "METRICAS_EXIBIR_TELA", "METRICAS_PASTA", "METRICAS_BUFFER_MEMORIA",
    "METRICAS_IGNORAR_ETAPAS", "OTIMIZAR_ESPERAS_GTN", "OTIMIZAR_WAIT_FOR_TIMEOUT",
    "OTIMIZAR_WAIT_FOR_TIMEOUT_SOMENTE_EXECUCAO", "MAX_WAIT_FOR_TIMEOUT_MS",
    "OTIMIZAR_OVERLAY_APEX", "OVERLAY_TIMEOUT_MS", "OTIMIZAR_PROXIMO", "PROXIMO_TIMEOUT_MS",
    "OTIMIZAR_SAVED_REPORT_GO", "SAVED_REPORT_GO_TIMEOUT_MS", "OTIMIZAR_SLOW_MO_BROWSER",
    "SLOW_MO_BROWSER_MS", "OTIMIZAR_TIMEOUT_EDIT_EXECUCAO", "TIMEOUT_EDIT_EXECUCAO_OTIMIZADO_MS",
    "TIMEOUT_EDIT_EXECUCAO", "TIMEOUT_LINK_EDIT", "TIMEOUT_BUSCA_EDIT", "TIMEOUT_EDIT_CENARIO",
}

FLAGS_BLOCK = '# ============================================================\n# BLOCO GERENCIADO V6.1 - NAO ALTERAR MANUALMENTE\n# Padrao: env especifico com apenas 1 relatorio visivel ao motor.\n# Otimizacoes V6.1: metricas reais, sem slow_mo, overlay controlado,\n# botao Proximo curto e SEM_EDIT mais rapido.\n# ============================================================\nRELATORIOS={relatorios_line}\nRELATORIO_UNICO_INDICE=1\nRELATORIO_ORIGINAL_INDICE={idx}\nRELATORIO_ATUAL_NOME={nome}\nRELATORIO_ATUAL_LIDER={lider}\nRELATORIO_ATUAL_PRIORIDADE={prioridade}\nRELATORIO_ATUAL_SAVED_VALUE={saved}\nRELATORIO_ATUAL_QTD={total}\nRELATORIO_ATUAL_TOTAL_CENARIOS={total}\nRELATORIO_ATUAL_EDITAR_INICIO={edit_inicio}\nRELATORIO_ATUAL_EDITAR_FIM={edit_fim}\nRELATORIO_ATUAL_TR_INICIO={tr_inicio}\nRELATORIO_ATUAL_TR_FIM={tr_fim}\n\n# Metricas reais\nMEDIR_METRICAS_REAIS=S\nMETRICAS_MEDIR_PLAYWRIGHT=S\nMETRICAS_SALVAR_ETAPAS=S\nMETRICAS_EXIBIR_TELA=S\nMETRICAS_PASTA=metricas_execucao\nMETRICAS_BUFFER_MEMORIA=S\nMETRICAS_IGNORAR_ETAPAS=LOCATOR_COUNT\n\n# Otimizacoes seguras V6\nOTIMIZAR_ESPERAS_GTN=S\nOTIMIZAR_WAIT_FOR_TIMEOUT=S\nOTIMIZAR_WAIT_FOR_TIMEOUT_SOMENTE_EXECUCAO=S\nMAX_WAIT_FOR_TIMEOUT_MS=450\nOTIMIZAR_OVERLAY_APEX=S\nOVERLAY_TIMEOUT_MS=1000\nOTIMIZAR_PROXIMO=S\nPROXIMO_TIMEOUT_MS=500\nOTIMIZAR_SAVED_REPORT_GO=S\nSAVED_REPORT_GO_TIMEOUT_MS=2000\nOTIMIZAR_SLOW_MO_BROWSER=S\nSLOW_MO_BROWSER_MS=0\nOTIMIZAR_TIMEOUT_EDIT_EXECUCAO=S\nTIMEOUT_EDIT_EXECUCAO_OTIMIZADO_MS=5000\nTIMEOUT_EDIT_EXECUCAO=5000\n'


def chave_da_linha(linha: str) -> str | None:
    texto = linha.strip()
    if not texto or texto.startswith("#") or "=" not in texto:
        return None
    if texto.lower().startswith("export "):
        texto = texto[7:].strip()
    return texto.split("=", 1)[0].strip()


def bloco_gerenciado(info: dict) -> str:
    return FLAGS_BLOCK.format(**info).lstrip()


def modelo_novo(info: dict) -> str:
    return f"""# ============================================================
# ENV ESPECIFICO - {info['nome']}
# ============================================================
# Arquivo criado automaticamente porque nao existia.
# Preencha ou copie suas credenciais reais do GTN abaixo, se o motor principal exigir.
# ============================================================

# GTN_URL=
# GTN_HOME_URL=
# GTN_USER=
# GTN_PASS=
# GTN_USUARIO=
# GTN_SENHA=

{bloco_gerenciado(info)}"""


def corrigir_env(info: dict) -> None:
    PASTA_CREDENCIAIS.mkdir(exist_ok=True)
    caminho = PASTA_CREDENCIAIS / info["arquivo_env"]

    if caminho.exists():
        PASTA_BACKUP.mkdir(exist_ok=True)
        shutil.copy2(caminho, PASTA_BACKUP / caminho.name)
        linhas = caminho.read_text(encoding="utf-8-sig").splitlines()
        preservadas = []
        for linha in linhas:
            chave = chave_da_linha(linha)
            if chave and chave in CHAVES_GERENCIADAS:
                continue
            preservadas.append(linha.rstrip())
        conteudo = "\n".join(preservadas).rstrip() + "\n\n" + bloco_gerenciado(info)
        caminho.write_text(conteudo, encoding="utf-8-sig")
        print(f"[OK] Atualizado preservando credenciais: {caminho}")
    else:
        caminho.write_text(modelo_novo(info), encoding="utf-8-sig")
        print(f"[CRIADO] Env nao existia. Criado modelo: {caminho}")


def main() -> None:
    print("=" * 100)
    print("APLICACAO PADRAO V6 NOS 19 ENVS - preserva credenciais e atualiza somente bloco gerenciado")
    print(f"Pasta base: {BASE_DIR}")
    print(f"Pasta credenciais: {PASTA_CREDENCIAIS}")
    print("=" * 100)
    for info in RELATORIOS:
        corrigir_env(info)
    if PASTA_BACKUP.exists():
        print(f"\n[BACKUP] Arquivos originais salvos em: {PASTA_BACKUP}")
    print("\n[FIM] Envs atualizados para o Padrao V6. Agora rode qualquer GTN_RELATORIO_XX_*.py normalmente.")


if __name__ == "__main__":
    main()
