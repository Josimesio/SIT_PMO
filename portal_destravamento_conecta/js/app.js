const DATA_URL = 'data/conecta_dashboard.json';

const state = {
  raw: [],
  filtered: [],
  resumo: {},
  filters: {
    responsavel: 'TODOS',
    frente: 'TODOS',
    status: 'TODOS',
    somenteAcao: false,
  },
};

const normalize = (value) => String(value ?? '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .trim()
  .toUpperCase();

const formatNumber = (n) => Number(n || 0).toLocaleString('pt-BR');

function getAtencao(indice) {
  if (indice >= 100) return { label: 'Atenção Crítica', cls: 'danger' };
  if (indice >= 50) return { label: 'Atenção Alta', cls: 'danger' };
  if (indice >= 20) return { label: 'Atenção Média', cls: 'warning' };
  return { label: 'Controlado', cls: 'success' };
}

function badge(text, cls = '') {
  return `<span class="badge ${cls}">${escapeHtml(text || '-')}</span>`;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function classifyStatus(item) {
  if (item.bloqueado) return { label: 'Bloqueado', cls: 'danger' };
  if (item.nao_iniciado) return { label: 'Não iniciado', cls: 'warning' };
  if (item.ocorrencia_aberta) return { label: 'Ocorrência aberta', cls: 'danger' };
  const status = normalize(item.status);
  if (status.includes('CONCLUID') || status.includes('FINALIZ') || status === 'OK') return { label: 'Concluído', cls: 'success' };
  if (status.includes('EXEC') || status.includes('ANDAMENTO')) return { label: 'Em execução', cls: 'info' };
  return { label: item.status || 'Não classificado', cls: '' };
}

function sugerirAcao(item) {
  if (item.bloqueado) return 'Escalar impedimento e definir ação de destravamento';
  if (item.ocorrencia_aberta) return 'Priorizar tratativa da ocorrência aberta';
  if (item.nao_iniciado) return 'Confirmar plano de início e pré-requisitos';
  if (!item.responsavel || normalize(item.responsavel) === 'SEM RESPONSAVEL') return 'Definir responsável de tratativa';
  if (item.indice_apoio >= 20) return 'Acompanhar em reunião de gestão';
  return 'Monitorar evolução';
}

async function loadData() {
  try {
    const response = await fetch(`${DATA_URL}?v=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    state.raw = Array.isArray(payload.itens) ? payload.itens : [];
    state.resumo = payload.resumo || {};
    applyFilters();
    setupFilters();
    renderAll();
  } catch (error) {
    console.error(error);
    showLoadError(error);
  }
}

function showLoadError(error) {
  document.getElementById('ultimaAtualizacao').textContent = 'Dados não encontrados';
  document.getElementById('tempoGeracao').textContent = 'Gere o JSON com atualizar_site_do_consolidado.py';
  const alertas = document.getElementById('alertasGestao');
  alertas.innerHTML = `
    <div class="alert-item danger">
      <strong>Não consegui carregar o arquivo data/conecta_dashboard.json</strong>
      <span>Rode o conversor Python apontando para o consolidado do GTN. Detalhe técnico: ${escapeHtml(error.message)}</span>
    </div>`;
}

function setupFilters() {
  fillSelect('filtroResponsavel', ['TODOS', ...unique(state.raw.map(x => x.responsavel || 'Sem responsável'))]);
  fillSelect('filtroFrente', ['TODOS', ...unique(state.raw.map(x => x.frente || 'Sem frente'))]);
  fillSelect('filtroStatus', ['TODOS', ...unique(state.raw.map(x => classifyStatus(x).label))]);

  document.getElementById('filtroResponsavel').value = state.filters.responsavel;
  document.getElementById('filtroFrente').value = state.filters.frente;
  document.getElementById('filtroStatus').value = state.filters.status;

  document.getElementById('filtroResponsavel').addEventListener('change', (e) => {
    state.filters.responsavel = e.target.value;
    applyFilters();
    renderAll();
  });
  document.getElementById('filtroFrente').addEventListener('change', (e) => {
    state.filters.frente = e.target.value;
    applyFilters();
    renderAll();
  });
  document.getElementById('filtroStatus').addEventListener('change', (e) => {
    state.filters.status = e.target.value;
    applyFilters();
    renderAll();
  });
  document.getElementById('btnSomenteAcao').addEventListener('click', () => {
    state.filters.somenteAcao = !state.filters.somenteAcao;
    document.getElementById('btnSomenteAcao').classList.toggle('active', state.filters.somenteAcao);
    applyFilters();
    renderAll();
  });
  document.getElementById('btnLimparFiltros').addEventListener('click', () => {
    state.filters = { responsavel: 'TODOS', frente: 'TODOS', status: 'TODOS', somenteAcao: false };
    document.getElementById('btnSomenteAcao').classList.remove('active');
    setupFilters();
    applyFilters();
    renderAll();
  });
}

function fillSelect(id, values) {
  const select = document.getElementById(id);
  const current = select.value || 'TODOS';
  select.innerHTML = values.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('');
  if (values.includes(current)) select.value = current;
}

function unique(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), 'pt-BR'));
}

function applyFilters() {
  state.filtered = state.raw.filter(item => {
    const statusLabel = classifyStatus(item).label;
    if (state.filters.responsavel !== 'TODOS' && item.responsavel !== state.filters.responsavel) return false;
    if (state.filters.frente !== 'TODOS' && item.frente !== state.filters.frente) return false;
    if (state.filters.status !== 'TODOS' && statusLabel !== state.filters.status) return false;
    if (state.filters.somenteAcao && !(item.bloqueado || item.ocorrencia_aberta || item.nao_iniciado || item.indice_apoio >= 20)) return false;
    return true;
  });
}

function renderAll() {
  renderHeader();
  renderKPIs();
  renderChartStatus();
  renderAlertas();
  renderMapaApoio();
  renderFila();
  renderOcorrencias();
  renderNaoIniciados();
  renderDetalhe();
}

function renderHeader() {
  document.getElementById('ultimaAtualizacao').textContent = state.resumo.ultima_atualizacao || '-';
  document.getElementById('tempoGeracao').textContent = `Tempo de geração: ${state.resumo.tempo_geracao || '-'}`;
}

function calcMetrics(items) {
  return items.reduce((acc, item) => {
    acc.total += 1;
    if (item.nao_iniciado) acc.naoIniciados += 1;
    if (item.bloqueado) acc.bloqueados += 1;
    if (item.ocorrencia_aberta) acc.ocorrencias += 1;
    if (!item.nao_iniciado && !item.bloqueado && normalize(item.status).includes('EXEC')) acc.execucao += 1;
    acc.indice += Number(item.indice_apoio || 0);
    return acc;
  }, { total: 0, execucao: 0, naoIniciados: 0, bloqueados: 0, ocorrencias: 0, indice: 0 });
}

function renderKPIs() {
  const m = calcMetrics(state.filtered);
  document.getElementById('kpiTotal').textContent = formatNumber(m.total);
  document.getElementById('kpiExecucao').textContent = formatNumber(m.execucao);
  document.getElementById('kpiNaoIniciados').textContent = formatNumber(m.naoIniciados);
  document.getElementById('kpiBloqueados').textContent = formatNumber(m.bloqueados);
  document.getElementById('kpiOcorrencias').textContent = formatNumber(m.ocorrencias);
  document.getElementById('kpiIndiceApoio').textContent = formatNumber(m.indice);
}

function renderChartStatus() {
  const canvas = document.getElementById('chartStatus');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const groups = groupBy(state.filtered, item => classifyStatus(item).label);
  const data = Object.entries(groups).map(([label, list]) => ({ label, value: list.length }))
    .sort((a,b) => b.value - a.value);

  if (!data.length) {
    drawEmptyChart(ctx, canvas, 'Sem dados para os filtros atuais');
    return;
  }

  const max = Math.max(...data.map(d => d.value), 1);
  const barHeight = 28;
  const gap = 14;
  const startY = 28;
  const labelX = 12;
  const barX = 170;
  const maxBarWidth = canvas.width - barX - 60;

  ctx.font = '13px Segoe UI, Arial';
  ctx.textBaseline = 'middle';

  data.slice(0, 7).forEach((d, i) => {
    const y = startY + i * (barHeight + gap);
    const width = Math.max(3, (d.value / max) * maxBarWidth);
    ctx.fillStyle = '#334155';
    ctx.fillText(d.label, labelX, y + barHeight / 2);
    ctx.fillStyle = pickColor(d.label);
    roundRect(ctx, barX, y, width, barHeight, 8);
    ctx.fill();
    ctx.fillStyle = '#0f172a';
    ctx.fillText(formatNumber(d.value), barX + width + 10, y + barHeight / 2);
  });
}

function drawEmptyChart(ctx, canvas, text) {
  ctx.fillStyle = '#64748b';
  ctx.font = '16px Segoe UI, Arial';
  ctx.textAlign = 'center';
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);
  ctx.textAlign = 'start';
}

function pickColor(label) {
  const s = normalize(label);
  if (s.includes('BLOQUE') || s.includes('OCORR')) return '#dc2626';
  if (s.includes('NAO INICI')) return '#f59e0b';
  if (s.includes('CONCL')) return '#16a34a';
  if (s.includes('EXEC')) return '#2563eb';
  return '#64748b';
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  ctx.closePath();
}

function renderAlertas() {
  const m = calcMetrics(state.filtered);
  const alertas = [];
  if (m.bloqueados > 0) alertas.push({ cls: 'danger', title: `${m.bloqueados} cenário(s) bloqueado(s)`, text: 'Prioridade máxima: impedimento ativo precisa de dono, prazo e decisão.' });
  if (m.ocorrencias > 0) alertas.push({ cls: 'danger', title: `${m.ocorrencias} ocorrência(s) aberta(s)`, text: 'Concentrar tratativa onde existe problema ativo.' });
  if (m.naoIniciados > 0) alertas.push({ cls: 'warning', title: `${m.naoIniciados} cenário(s) não iniciado(s)`, text: 'Validar se é fila natural, falta de acesso, dependência ou ausência de plano.' });
  if (m.total > 0) {
    const taxa = Math.round((m.naoIniciados / m.total) * 100);
    if (taxa >= 20) alertas.push({ cls: 'warning', title: `${taxa}% da base filtrada não iniciou`, text: 'Pode indicar gargalo de agenda, ambiente, dados ou direcionamento.' });
  }
  if (!alertas.length) alertas.push({ cls: 'success', title: 'Sem alertas críticos nos filtros atuais', text: 'Manter acompanhamento e histórico de evolução.' });

  document.getElementById('alertasGestao').innerHTML = alertas.map(a => `
    <div class="alert-item ${a.cls}">
      <strong>${escapeHtml(a.title)}</strong>
      <span>${escapeHtml(a.text)}</span>
    </div>
  `).join('');
}

function renderMapaApoio() {
  const groups = groupBy(state.filtered, item => item.frente || 'Sem frente');
  const rows = Object.entries(groups).map(([frente, items]) => {
    const m = calcMetrics(items);
    const at = getAtencao(m.indice);
    return { frente, ...m, at };
  }).sort((a, b) => b.indice - a.indice);

  setTableRows('tabelaMapaApoio', rows, row => `
    <td>${escapeHtml(row.frente)}</td>
    <td>${formatNumber(row.total)}</td>
    <td>${formatNumber(row.naoIniciados)}</td>
    <td>${formatNumber(row.bloqueados)}</td>
    <td>${formatNumber(row.ocorrencias)}</td>
    <td><strong>${formatNumber(row.indice)}</strong></td>
    <td>${badge(row.at.label, row.at.cls)}</td>
  `);
}

function renderFila() {
  const rows = [...state.filtered]
    .filter(item => item.indice_apoio > 0 || item.nao_iniciado || item.bloqueado || item.ocorrencia_aberta)
    .sort((a, b) => Number(b.indice_apoio || 0) - Number(a.indice_apoio || 0))
    .slice(0, 20);

  setTableRows('tabelaFila', rows, (item, idx) => {
    const st = classifyStatus(item);
    return `
      <td><strong>${idx + 1}</strong></td>
      <td>${escapeHtml(item.responsavel || '-')}</td>
      <td>${escapeHtml(item.frente || '-')}</td>
      <td>${escapeHtml(item.cenario || item.arquivo_origem || '-')}</td>
      <td>${badge(st.label, st.cls)}</td>
      <td>${item.ocorrencia_aberta ? badge('Aberta', 'danger') : '<span class="muted">-</span>'}</td>
      <td><strong>${formatNumber(item.indice_apoio)}</strong></td>
      <td>${escapeHtml(sugerirAcao(item))}</td>
    `;
  });
}

function renderOcorrencias() {
  const rows = state.filtered.filter(item => item.ocorrencia_aberta || item.bloqueado);
  setTableRows('tabelaOcorrencias', rows, item => {
    const st = classifyStatus(item);
    return `
      <td>${escapeHtml(item.responsavel || '-')}</td>
      <td>${escapeHtml(item.frente || '-')}</td>
      <td>${escapeHtml(item.cenario || item.arquivo_origem || '-')}</td>
      <td>${badge(st.label, st.cls)}</td>
      <td>${escapeHtml(item.ocorrencia || (item.ocorrencia_aberta ? 'Ocorrência aberta' : '-'))}</td>
      <td>${escapeHtml(sugerirAcao(item))}</td>
    `;
  });
}

function renderNaoIniciados() {
  const rows = state.filtered.filter(item => item.nao_iniciado);
  setTableRows('tabelaNaoIniciados', rows, item => `
    <td>${escapeHtml(item.responsavel || '-')}</td>
    <td>${escapeHtml(item.relatorio_origem || '-')}</td>
    <td>${escapeHtml(item.frente || '-')}</td>
    <td>${escapeHtml(item.cenario || '-')}</td>
    <td>${escapeHtml(item.arquivo_origem || '-')}</td>
    <td>${escapeHtml(sugerirAcao(item))}</td>
  `);
}

function renderDetalhe() {
  const rows = state.filtered.slice(0, 500);
  setTableRows('tabelaDetalhe', rows, item => {
    const st = classifyStatus(item);
    return `
      <td>${escapeHtml(item.responsavel || '-')}</td>
      <td>${escapeHtml(item.frente || '-')}</td>
      <td>${escapeHtml(item.relatorio_origem || '-')}</td>
      <td>${escapeHtml(item.cenario || '-')}</td>
      <td>${badge(st.label, st.cls)}</td>
      <td>${item.ocorrencia_aberta ? badge('Aberta', 'danger') : '<span class="muted">-</span>'}</td>
      <td>${escapeHtml(item.arquivo_origem || '-')}</td>
      <td>${escapeHtml(sugerirAcao(item))}</td>
    `;
  });
}

function setTableRows(tableId, rows, renderer) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="99" class="empty-state">Sem dados para os filtros atuais.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((row, idx) => `<tr>${renderer(row, idx)}</tr>`).join('');
}

function groupBy(items, keyFn) {
  return items.reduce((acc, item) => {
    const key = keyFn(item) || 'Não informado';
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});
}

function setupNavigation() {
  document.querySelectorAll('.menu-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.menu-item').forEach(x => x.classList.remove('active'));
      document.querySelectorAll('.view').forEach(x => x.classList.remove('active-view'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.target).classList.add('active-view');
    });
  });
}

setupNavigation();
loadData();
