PORTAL DE DESTRAVAMENTO — PROGRAMA CONECTA
==========================================

OBJETIVO
--------
Usar o arquivo consolidado gerado pelo script GTN para atualizar um dashboard HTML/CSS/JavaScript.
O portal mostra gargalos, necessidade de apoio, ocorrências, não iniciados e fila de destravamento.
A ideia não é apontar culpados. É mostrar onde o PMO deve agir para destravar o projeto.


ESTRUTURA
---------
index.html                         -> página principal do dashboard
css/style.css                      -> visual do portal
js/app.js                          -> regras, filtros, KPIs, tabelas e gráfico em JavaScript puro
data/conecta_dashboard.json        -> dados consumidos pelo site
tools/atualizar_site_do_consolidado.py -> conversor do consolidado Excel para JSON
requirements_portal.txt            -> dependência para o conversor
atualizar_site.bat                 -> atalho Windows para atualizar o JSON
rodar_site_local.bat                -> abre servidor local para testar o site


PASSO 1 — INSTALAR DEPENDÊNCIA
------------------------------
Abra o PowerShell/CMD dentro da pasta portal_destravamento_conecta e rode:

pip install -r requirements_portal.txt


PASSO 2 — GERAR O CONSOLIDADO NO SCRIPT GTN
-------------------------------------------
Execute seu script GTN atualizado.
Ele deve gerar algo parecido com:

F:\REPOSITORIOS\SIT_PMO\downloads_gtn\consolidado_22-54-16.xlsx


PASSO 3 — ATUALIZAR O SITE COM O CONSOLIDADO
--------------------------------------------
Opção A — pelo .bat:

atualizar_site.bat "F:\REPOSITORIOS\SIT_PMO\downloads_gtn\consolidado_22-54-16.xlsx"

Opção B — direto no Python:

python tools\atualizar_site_do_consolidado.py "F:\REPOSITORIOS\SIT_PMO\downloads_gtn\consolidado_22-54-16.xlsx"

Isso atualiza o arquivo:

data/conecta_dashboard.json


PASSO 4 — ABRIR O DASHBOARD
---------------------------
Para testar localmente, rode:

rodar_site_local.bat

Depois abra:

http://localhost:8000

Também dá para abrir o index.html direto, mas alguns navegadores bloqueiam fetch local.
Por isso o servidor local é mais confiável.


PUBLICAR ONLINE
---------------
Publique a pasta inteira em:

- GitHub Pages
- SharePoint
- IIS
- Nginx
- servidor interno

Sempre que gerar um novo consolidado, rode o conversor e suba o JSON atualizado.


ABAS ESPERADAS NO CONSOLIDADO
-----------------------------
O conversor procura estas abas:

WALCERI
WALCEIR
CAMILA
LUCASRAMOS
LUCAS RAMOS

A aba RESUMO_EXECUCAO é usada para capturar data/hora e tempo de geração quando existir.


REGRA DO ÍNDICE DE APOIO
------------------------
Índice de Apoio = Bloqueado * 5 + Ocorrência Aberta * 3 + Não Iniciado * 1

Interpretação:
- Bloqueado: impedimento ativo, prioridade alta.
- Ocorrência aberta: problema em tratamento, precisa de acompanhamento.
- Não iniciado: fila, dependência ou cenário ainda sem execução.


IMPORTANTE
----------
O painel não é ranking de pessoas.
A visão por responsável mostra concentração de trabalho e necessidade de apoio, não desempenho individual.
