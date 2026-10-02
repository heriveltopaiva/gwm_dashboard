// ============================================================
//  CONTROLE GWM — versão simples (sem ID, sem Loja 00, sem dashboard)
//  O dashboard agora é feito em Python e só LÊ esta planilha.
//  Este script cuida de: listas suspensas, cores, cálculo do LB e metas.
// ============================================================

const CONFIG = {
  LOJAS: ["Loja 01", "Loja 02", "Loja 03", "Loja 04"],
  CONFIG: "Configurações",
  METAS: "Metas",
  COLUNAS: [
    "DATA PEDIDO", "DATA FAT", "TIPO", "STATUS", "CHASSI",
    "FAMILIA", "COR", "NOME CLIENTE", "VEND", "LOCAL", "VENDA",
    "CUSTO", "INCID", "LB", "OBS", "OBS2"
  ],
  AZUL: "#DDEBF7",
  VERMELHO: "#F4CCCC",
  CABECALHO: "#222324",
  BRANCO: "#F8F9F9"
};

// Número de cada coluna nas abas das lojas (A = 1)
const COL = {
  PEDIDO: 1, FAT: 2, TIPO: 3, STATUS: 4, CHASSI: 5, FAMILIA: 6, COR: 7,
  CLIENTE: 8, VEND: 9, LOCAL: 10, VENDA: 11, CUSTO: 12, INCID: 13, LB: 14
};

// ============================================================
//  MENU
// ============================================================
function onOpen() {
  SpreadsheetApp.getUi().createMenu("📊 Controle GWM")
    .addItem("Recalcular LB de todas as lojas", "recalcularLBTodasLojas")
    .addItem("Reaplicar listas e cores", "reaplicarListasECores")
    .addToUi();
}

// ============================================================
//  CONFIGURAÇÃO INICIAL (rode uma vez)
// ============================================================
function configurarSistema() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  [...CONFIG.LOJAS, CONFIG.CONFIG, CONFIG.METAS].forEach(nome => {
    let sh = ss.getSheetByName(nome);
    if (!sh) sh = ss.insertSheet(nome);
    if (CONFIG.LOJAS.includes(nome)) configurarAbaOperacional(sh);
  });
  configurarListas(ss);
  configurarMetas(ss);
  aplicarMenusTodasAbas();
  aplicarCoresTodasAbas();
  removerGatilhosAntigos();
  ss.toast("Estrutura configurada.", "Controle GWM", 5);
}

function reaplicarListasECores() {
  aplicarMenusTodasAbas();
  aplicarCoresTodasAbas();
  SpreadsheetApp.getActiveSpreadsheet().toast("Listas e cores reaplicadas.", "Controle GWM", 4);
}

function configurarAbaOperacional(sh) {
  const n = CONFIG.COLUNAS.length;
  sh.getRange(1, 1, 1, n).setValues([CONFIG.COLUNAS])
    .setFontWeight("bold").setBackground(CONFIG.CABECALHO)
    .setFontColor(CONFIG.BRANCO).setHorizontalAlignment("center");
  sh.setFrozenRows(1);
  sh.setRowHeight(1, 32);
  sh.setColumnWidths(1, n, 120);
  sh.setColumnWidth(COL.CLIENTE, 220);
  sh.setColumnWidth(15, 220);
  sh.setColumnWidth(16, 220);
  sh.getRange("A:B").setNumberFormat("dd/MM/yyyy");
  sh.getRange("K:N").setNumberFormat('"R$" #,##0.00;[Red]-"R$" #,##0.00');
}

// ============================================================
//  LISTAS (aba Configurações)
// ============================================================
function configurarListas(ss) {
  const sh = ss.getSheetByName(CONFIG.CONFIG);
  const listas = [
    ["TIPOS", "STATUS", "FAMILIA", "COR", "LOJA 01", "LOJA 02", "LOJA 03", "LOJA 04"],
    ["FIRMORDER", "Aguardando faturamento", "HAVAL H6 GT", "Azul topazio", "CAMILA", "VENDEDOR UBERBA", "VENDEDOR LOJA3", "VENDEDOR LOJA4"],
    ["PEDIDO", "Faturado", "HAVAL H6 HEV ONE", "Azul Cianita", "FERNANDA", "VENDEDOR UBERBA1", "VENDEDOR2 LOJA3", "VENDEDOR2 LOJA4"],
    ["USADO", "Cancelado", "HAVAL H6 HEV2", "Azul copacabana", "KELBY", "VENDEDOR UBERBA2", "VENDEDOR3 LOJA3", "VENDEDOR3 LOJA4"],
    ["EMPLACADO", "Devolução", "HAVAL H6 PHEV19", "Cinza diamante", "LUCAS"],
    ["", "", "HAVAL H9 EXCL.", "Cinza Amazonita", "LUDMILLE"],
    ["", "", "ORA 5", "Prata Lunar", "MARCOS"],
    ["", "", "POER P30 EXCL.", "Preto Hematita", "PATRICIA"],
    ["", "", "POER P30 TRAIL", "Preto Khalifa", "POLIANA"],
    ["", "", "SEMINOVO", "Vermelho Granada", "WENDELL"],
    ["", "", "", "Grafitte Zenith"],
    ["", "", "", "Solar Gold"],
    ["", "", "", "Verde Turmalina"],
    ["", "", "", "VerdeEsmeralda"],
    ["", "", "", "Branco"],
    ["", "", "", "Laranja"],
    ["", "", "", "Cinza Titanium"]
  ];
  // Só preenche se estiver vazia: nunca apaga nomes editados pelo usuário.
  if (sh.getLastRow() === 0 || sh.getRange("A1").isBlank()) {
    sh.getRange(1, 1, listas.length, 8).setValues(
      listas.map(r => Array.from({length: 8}, (_, i) => r[i] || ""))
    );
    sh.getRange("A1:H1").setFontWeight("bold").setBackground("#1C5075").setFontColor(CONFIG.BRANCO);
  }
  sh.setFrozenRows(1);
  sh.autoResizeColumns(1, 8);
}

function contarItens(sh, col) {
  if (!sh || sh.getLastRow() < 2) return 0;
  return sh.getRange(2, col, sh.getLastRow() - 1, 1)
    .getDisplayValues().filter(r => r[0].trim() !== "").length;
}

function criarRegra(sh, col) {
  if (!contarItens(sh, col)) return null;
  return SpreadsheetApp.newDataValidation()
    .requireValueInRange(sh.getRange(2, col, sh.getLastRow() - 1, 1), true)
    .setAllowInvalid(false).build();
}

function aplicarRegra(sh, col, linhas, regra) {
  if (linhas < 1) return;
  const rg = sh.getRange(2, col, linhas, 1);
  if (regra) rg.setDataValidation(regra);
  else rg.clearDataValidations();
}

function aplicarMenusTodasAbas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const cfg = ss.getSheetByName(CONFIG.CONFIG);
  const tipo = criarRegra(cfg, 1), status = criarRegra(cfg, 2);
  const familia = criarRegra(cfg, 3), cor = criarRegra(cfg, 4);
  CONFIG.LOJAS.forEach((nome, i) => {
    const sh = ss.getSheetByName(nome);
    if (!sh) return;
    const rows = Math.max(sh.getMaxRows() - 1, 1);
    aplicarRegra(sh, COL.TIPO, rows, tipo);
    aplicarRegra(sh, COL.STATUS, rows, status);
    aplicarRegra(sh, COL.FAMILIA, rows, familia);
    aplicarRegra(sh, COL.COR, rows, cor);
    aplicarRegra(sh, COL.VEND, rows, criarRegra(cfg, 5 + i)); // colunas E..H da Configurações
  });
}

function aplicarCoresTodasAbas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  CONFIG.LOJAS.forEach(nome => {
    const sh = ss.getSheetByName(nome);
    if (!sh) return;
    const rg = sh.getRange(2, 1, Math.max(sh.getMaxRows() - 1, 1), CONFIG.COLUNAS.length);
    sh.setConditionalFormatRules([
      SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=$D2="Cancelado"')
        .setBackground(CONFIG.VERMELHO).setRanges([rg]).build(),
      SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=AND($A2<>"",$D2<>"Cancelado")')
        .setBackground(CONFIG.AZUL).setRanges([rg]).build()
    ]);
  });
}

// ============================================================
//  EDIÇÃO — só recalcula o LB das linhas editadas (rápido, aceita colar vários)
// ============================================================
function onEdit(e) {
  if (!e || !e.range) return;
  const sh = e.range.getSheet();
  if (!CONFIG.LOJAS.includes(sh.getName())) return;

  const r1 = Math.max(e.range.getRow(), 2), r2 = e.range.getLastRow();
  if (r2 < r1) return;
  const c1 = e.range.getColumn(), c2 = e.range.getLastColumn();
  const afetaLB = [COL.STATUS, COL.VENDA, COL.CUSTO, COL.INCID].some(c => c >= c1 && c <= c2);
  if (!afetaLB) return;

  recalcularLB(sh, r1, r2 - r1 + 1);
}

/** Recalcula a coluna LB de um bloco de linhas, gravando tudo de uma vez. */
function recalcularLB(sh, linhaInicial, qtd) {
  const largura = COL.INCID - COL.STATUS + 1;
  const v = sh.getRange(linhaInicial, COL.STATUS, qtd, largura).getValues();
  const lbs = v.map(l => {
    const status = String(l[0]).trim();
    const venda = Number(l[COL.VENDA - COL.STATUS]) || 0;
    const custo = Number(l[COL.CUSTO - COL.STATUS]) || 0;
    const incid = Number(l[COL.INCID - COL.STATUS]) || 0;
    if (!status && !venda && !custo && !incid) return [""];
    let lb = venda - custo - incid;
    if (status === "Devolução") lb = -Math.abs(lb);
    return [lb];
  });
  sh.getRange(linhaInicial, COL.LB, qtd, 1).setValues(lbs);
}

/** Use pelo menu depois de mexer na estrutura ou colar dados por fora. */
function recalcularLBTodasLojas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  CONFIG.LOJAS.forEach(nome => {
    const sh = ss.getSheetByName(nome);
    if (sh && sh.getLastRow() > 1) recalcularLB(sh, 2, sh.getLastRow() - 1);
  });
  ss.toast("LB recalculado em todas as lojas.", "Controle GWM", 4);
}

// ============================================================
//  METAS (uma linha por loja e mês — o dashboard lê esta aba)
// ============================================================
function configurarMetas(ss) {
  const sh = ss.getSheetByName(CONFIG.METAS);
  const headers = ["MÊS (1º DIA)", "LOJA", "META FATURAMENTO", "META LB", "ALTERADA EM", "OBSERVAÇÃO"];
  if (sh.getRange("A1").isBlank()) {
    sh.getRange(1, 1, 1, headers.length).setValues([headers])
      .setFontWeight("bold").setBackground("#1C5075").setFontColor(CONFIG.BRANCO);
    sh.setFrozenRows(1);
    sh.getRange("A:A").setNumberFormat("MM/yyyy");
    sh.getRange("C:D").setNumberFormat('"R$" #,##0.00');
    sh.setColumnWidths(1, 6, 160);
  }
  let hist = ss.getSheetByName("Histórico Metas");
  if (!hist) hist = ss.insertSheet("Histórico Metas");
  if (hist.getRange("A1").isBlank()) {
    hist.getRange("A1:F1").setValues([["DATA ALTERAÇÃO", "MÊS", "LOJA", "META FATURAMENTO", "META LB", "OBSERVAÇÃO"]])
      .setFontWeight("bold").setBackground("#536B78").setFontColor(CONFIG.BRANCO);
  }
  const rule = SpreadsheetApp.newDataValidation().requireValueInList(CONFIG.LOJAS, true).setAllowInvalid(false).build();
  sh.getRange(2, 2, Math.max(sh.getMaxRows() - 1, 1), 1).setDataValidation(rule);
}

/** Opcional: registra o histórico de metas. Instale antes com instalarGatilhoMetas(). */
function onEditMetas(e) {
  if (!e || !e.range) return;
  const sh = e.range.getSheet();
  if (sh.getName() !== CONFIG.METAS || e.range.getRow() < 2) return;
  const row = e.range.getRow();
  sh.getRange(row, 5).setValue(new Date());
  const hist = e.source.getSheetByName("Histórico Metas");
  hist.appendRow([new Date(), sh.getRange(row, 1).getValue(), sh.getRange(row, 2).getValue(),
    sh.getRange(row, 3).getValue(), sh.getRange(row, 4).getValue(), sh.getRange(row, 6).getValue()]);
}

/** Rode uma vez se quiser o histórico de metas. */
function instalarGatilhoMetas() {
  ScriptApp.newTrigger("onEditMetas")
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet()).onEdit().create();
}

// ============================================================
//  LIMPEZA — remove os gatilhos horários da versão antiga
// ============================================================
function removerGatilhosAntigos() {
  ScriptApp.getProjectTriggers()
    .filter(t => ["sincronizarMaster", "atualizarDashboard"].includes(t.getHandlerFunction()))
    .forEach(t => ScriptApp.deleteTrigger(t));
}