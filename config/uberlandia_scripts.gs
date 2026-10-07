/****************************************************
 * GWM UBERLÂNDIA — CONTROLE DE VENDAS E ORÇAMENTO
 * Versão consolidada
 *
 * IMPORTANTE:
 * 1. A criação não limpa abas existentes.
 * 2. A atualização altera somente as fórmulas previstas.
 * 3. Teste primeiro em uma cópia da planilha.
 ****************************************************/

const CONFIG_GWM = {
  loja: "GWM Uberlândia",
  cnpj: "48.337.247/0003-96",

  meses: [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
  ],

  modelos: [
    "ORA SKIN",
    "ORA SKIN 58",
    "ORA 5",
    "HAVAL H6 HEV ONE",
    "HAVAL H6 HEV 2",
    "HAVAL H6 PHEV 19",
    "HAVAL H6 PHEV 34",
    "HAVAL H6 GT",
    "HAVAL H9 EXCL.",
    "TANK 300",
    "POER P30 EXCL.",
    "POER P30 TRAIL",
    "WEY 07"
  ],

  colunas: [
    "DATA PEDIDO", "DATA FAT", "TIPO", "STATUS",
    "CHASSI", "FAMILIA", "COR", "NOME CLIENTE",
    "VEND", "LOCAL", "VENDA", "CUSTO",
    "INCID", "LB", "OBS", "OBS2",
    "TEST DRIVE", "CAPTAÇÃO", "MODELO", "PLACA", "EMISSÃO"
  ],

  // Listas fixas dos menus suspensos (para mudar um nome, edite aqui e rode
  // "Adicionar colunas e listas" no menu 📊 GWM).
  listas: {
    tipo: ["Firmorder", "Pedido", "Usado", "Emplacado"],
    status: ["Faturado", "Cancelada", "Devolução"],
    vendedores: [
      "CAMILA", "FERNANDA", "KELBY", "LUDMILLE",
      "MARCOS", "PATRICIA", "POLIANA", "WENDELL"
    ],
    cores: [
      "Azul topazio", "Azul Cianita", "Azul copacabana", "Cinza diamante",
      "Cinza Amazonita", "Prata Lunar", "Preto Hematita", "Preto Khalifa",
      "Vermelho Granada", "Grafitte Zenith", "Solar Gold", "Verde Turmalina",
      "VerdeEsmeralda", "Branco", "Laranja", "Cinza Titanium"
    ],
    simNao: ["Sim", "Não"]
  },

  cores: {
    escuro: "#17365D",
    claro: "#D9EAF7",
    total: "#F3F6FA",
    branco: "#FFFFFF"
  }
};


/****************************************************
 * FUNÇÕES AUXILIARES
 ****************************************************/

function obterAbaGwm(nome) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let aba = ss.getSheetByName(nome);

  if (!aba) {
    aba = ss.insertSheet(nome);
  }

  aba.setHiddenGridlines(true);
  return aba;
}


function letraColunaGwm(coluna) {
  let letra = "";

  while (coluna > 0) {
    const resto = (coluna - 1) % 26;
    letra = String.fromCharCode(65 + resto) + letra;
    coluna = Math.floor((coluna - 1) / 26);
  }

  return letra;
}


/****************************************************
 * CRIAÇÃO DAS ABAS MENSAIS
 ****************************************************/

function configurarAbasMensaisGwm() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = CONFIG_GWM;

  const larguras = [
    110, 110, 100, 110, 150, 130, 100, 220,
    140, 120, 120, 120, 120, 120, 200, 200,
    120, 120
  ];

  config.meses.forEach(mes => {
    const aba = obterAbaGwm(mes);

    // Só insere cabeçalhos se a primeira linha estiver vazia.
    const cabecalhoAtual = aba
      .getRange(1, 1, 1, config.colunas.length)
      .getDisplayValues()[0];

    const linhaVazia = cabecalhoAtual.every(valor => valor === "");

    if (linhaVazia) {
      aba.getRange(1, 1, 1, config.colunas.length)
        .setValues([config.colunas]);
    }

    aba.getRange(1, 1, 1, config.colunas.length)
      .setBackground(config.cores.escuro)
      .setFontColor(config.cores.branco)
      .setFontWeight("bold")
      .setHorizontalAlignment("center")
      .setWrap(true);

    aba.setFrozenRows(1);
    aba.setRowHeight(1, 42);

    aba.getRange("A2:B1000")
      .setNumberFormat("dd/MM/yyyy");

    aba.getRange("K2:N1000")
      .setNumberFormat('"R$" #,##0.00');

    larguras.forEach((largura, i) => {
      aba.setColumnWidth(i + 1, largura);
    });

    aba.getRange(1, 1, 1000, config.colunas.length)
      .setVerticalAlignment("middle");

    // Evita tentar criar um segundo filtro.
    if (!aba.getFilter()) {
      aba.getRange(1, 1, 1000, config.colunas.length)
        .createFilter();
    }
  });

  aplicarListasEColunasGwm();
}


/****************************************************
 * CRIAÇÃO INICIAL DO ORÇAMENTO
 ****************************************************/

function criarEstruturaOrcamentoGwm() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = CONFIG_GWM;
  const cores = config.cores;

  let aba = ss.getSheetByName("Orçamento 2026");

  if (aba) {
    const conteudo = aba.getDataRange().getDisplayValues();
    const possuiConteudo = conteudo.some(linha =>
      linha.some(valor => valor !== "")
    );

    if (possuiConteudo) {
      SpreadsheetApp.getUi().alert(
        "A aba Orçamento 2026 já contém dados. " +
        "A estrutura não foi recriada para evitar perda de informações. " +
        "Use a função atualizarFormulasOrcamentoUberlandia() " +
        "para atualizar as fórmulas."
      );
      return;
    }
  } else {
    aba = ss.insertSheet("Orçamento 2026");
  }

  aba.setHiddenGridlines(true);

  // Identificação
  aba.getRange("A1:N1").merge();
  aba.getRange("A1")
    .setValue("ORÇAMENTO 2026 — GWM UBERLÂNDIA");

  aba.getRange("A2").setValue("Unidade:");
  aba.getRange("B2").setValue(config.loja);
  aba.getRange("A3").setValue("CNPJ:");
  aba.getRange("B3").setValue(config.cnpj);

  const blocos = [
    {
      titulo: "QUANTIDADE DE VEÍCULOS",
      linhaTitulo: 5,
      linhaCabecalho: 6,
      tipo: "quantidade"
    },
    {
      titulo: "VALOR UNITÁRIO (R$)",
      linhaTitulo: 22,
      linhaCabecalho: 23,
      tipo: "valor"
    },
    {
      titulo: "LUCRO BRUTO ORÇADO (R$)",
      linhaTitulo: 40,
      linhaCabecalho: 41,
      tipo: "lucro"
    },
    {
      titulo: "% MARGEM DE VENDA",
      linhaTitulo: 58,
      linhaCabecalho: 59,
      tipo: "margem"
    }
  ];

  const mesesMaiusculos = config.meses.map(m =>
    m.toUpperCase()
  );

  blocos.forEach(bloco => {
    const linhaTitulo = bloco.linhaTitulo;
    const linhaCabecalho = bloco.linhaCabecalho;
    const tipo = bloco.tipo;

    const primeiraLinha = linhaCabecalho + 1;
    const ultimaLinha = primeiraLinha + config.modelos.length - 1;
    const linhaTotal = ultimaLinha + 1;

    // Título do bloco
    aba.getRange(linhaTitulo, 1, 1, 14).merge();
    aba.getRange(linhaTitulo, 1).setValue(bloco.titulo);

    // Cabeçalho
    aba.getRange(linhaCabecalho, 1, 1, 14)
      .setValues([[
        "MODELO",
        ...mesesMaiusculos,
        (tipo === "margem" || tipo === "valor") ? "MÉDIA" : "TOTAL"
      ]]);

    // Modelos
    aba.getRange(primeiraLinha, 1, config.modelos.length, 1)
      .setValues(config.modelos.map(modelo => [modelo]));

    // Linha de total
    aba.getRange(linhaTotal, 1)
      .setValue(
        tipo === "margem" ? "MÉDIA" :
        tipo === "valor" ? "FATURAMENTO ORÇADO" : "TOTAL"
      );

    // Formatação do bloco
    aba.getRange(linhaTitulo, 1, 1, 14)
      .setBackground(cores.escuro)
      .setFontColor(cores.branco)
      .setFontWeight("bold");

    aba.getRange(linhaCabecalho, 1, 1, 14)
      .setBackground(cores.claro)
      .setFontWeight("bold")
      .setWrap(true);

    aba.getRange(linhaTotal, 1, 1, 14)
      .setBackground(cores.total)
      .setFontWeight("bold");

    // Formatos numéricos
    if (tipo === "quantidade") {
      aba.getRange(primeiraLinha, 2, config.modelos.length + 1, 13)
        .setNumberFormat("0");
    }

    if (tipo === "valor" || tipo === "lucro") {
      aba.getRange(primeiraLinha, 2, config.modelos.length + 1, 13)
        .setNumberFormat('"R$" #,##0.00');
    }

    if (tipo === "margem") {
      aba.getRange(primeiraLinha, 2, config.modelos.length + 1, 13)
        .setNumberFormat("0.00%");
    }
  });

  // Aparência geral
  aba.getRange("A1:N1")
    .setBackground(cores.escuro)
    .setFontColor(cores.branco)
    .setFontWeight("bold")
    .setFontSize(16);

  aba.getRange("A2:B3").setFontWeight("bold");

  aba.setColumnWidth(1, 230);

  for (let col = 2; col <= 14; col++) {
    aba.setColumnWidth(col, 115);
  }

  aba.setFrozenRows(6);
  aba.getRange("A1:N73").setVerticalAlignment("middle");
  aba.getRange("B6:N73").setHorizontalAlignment("center");
}


/****************************************************
 * ATUALIZAÇÃO DAS FÓRMULAS DO ORÇAMENTO
 *
 * Não limpa abas nem recria a estrutura.
 ****************************************************/

function atualizarFormulasOrcamentoUberlandia() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const aba = ss.getSheetByName("Orçamento 2026");

  if (!aba) {
    SpreadsheetApp.getUi().alert(
      "A aba Orçamento 2026 não foi encontrada."
    );
    return;
  }

  const primeiraColunaMes = 2;
  const ultimaColunaMes = 13;
  const colunaTotal = 14;
  const quantidadeModelos = CONFIG_GWM.modelos.length;

  // Separador de argumentos que ESTA planilha aceita (vírgula ou ponto e vírgula)
  const S = separadorArgumentos();

  // Fórmulas por modelo
  for (let i = 0; i < quantidadeModelos; i++) {
    const linhaQtd = 7 + i;
    const linhaValor = 24 + i;
    const linhaLucro = 42 + i;
    const linhaMargem = 60 + i;

    // Total anual de quantidade
    aba.getRange(linhaQtd, colunaTotal)
      .setFormula(`=SUM(B${linhaQtd}:M${linhaQtd})`);

    // Média anual do valor unitário
    aba.getRange(linhaValor, colunaTotal)
      .setFormula(
        `=IFERROR(AVERAGE(B${linhaValor}:M${linhaValor})${S}0)`
      );

    // Lucro bruto mensal
    const formulasLucro = [];

    for (
      let col = primeiraColunaMes;
      col <= ultimaColunaMes;
      col++
    ) {
      const letra = letraColunaGwm(col);

      formulasLucro.push(
        `=${letra}${linhaQtd}*${letra}${linhaValor}*${letra}${linhaMargem}`
      );
    }

    aba.getRange(linhaLucro, primeiraColunaMes, 1, 12)
      .setFormulas([formulasLucro]);

    // Total anual do lucro
    aba.getRange(linhaLucro, colunaTotal)
      .setFormula(`=SUM(B${linhaLucro}:M${linhaLucro})`);

    // Média anual da margem
    aba.getRange(linhaMargem, colunaTotal)
      .setFormula(
        `=IFERROR(AVERAGE(B${linhaMargem}:M${linhaMargem})${S}0)`
      );
  }

  // Totais dos blocos
  const blocos = [
    { inicio: 7, total: 20 },
    { inicio: 42, total: 55 }
  ];

  blocos.forEach(bloco => {
    for (
      let col = primeiraColunaMes;
      col <= ultimaColunaMes;
      col++
    ) {
      const letra = letraColunaGwm(col);

      aba.getRange(bloco.total, col)
        .setFormula(
          `=SUM(${letra}${bloco.inicio}:${letra}${bloco.total - 1})`
        );
    }

    aba.getRange(bloco.total, colunaTotal)
      .setFormula(
        `=SUM(N${bloco.inicio}:N${bloco.total - 1})`
      );
  });

  // Linha 37 — FATURAMENTO ORÇADO = quantidade x valor unitário de cada modelo.
  // (Antes somava os preços unitários, o que não tem sentido de negócio.)
  const primeiraQtd = 7;
  const ultimaQtd = primeiraQtd + quantidadeModelos - 1;      // 19
  const primeiroValor = 24;
  const ultimoValor = primeiroValor + quantidadeModelos - 1;  // 36
  const linhaFaturamento = ultimoValor + 1;                   // 37

  aba.getRange(linhaFaturamento, 1).setValue("FATURAMENTO ORÇADO");
  aba.getRange(linhaFaturamento - quantidadeModelos - 1, colunaTotal).setValue("MÉDIA"); // cabeçalho N23

  const formulasFaturamento = [];
  for (let col = primeiraColunaMes; col <= ultimaColunaMes; col++) {
    const letra = letraColunaGwm(col);
    // Um único argumento: não depende do separador da planilha.
    formulasFaturamento.push(
      `=SUMPRODUCT(${letra}${primeiraQtd}:${letra}${ultimaQtd}*${letra}${primeiroValor}:${letra}${ultimoValor})`
    );
  }
  aba.getRange(linhaFaturamento, primeiraColunaMes, 1, 12).setFormulas([formulasFaturamento]);
  aba.getRange(linhaFaturamento, colunaTotal).setFormula(`=SUM(B${linhaFaturamento}:M${linhaFaturamento})`);

  // Médias mensais da margem
  const formulasMargem = [];

  for (
    let col = primeiraColunaMes;
    col <= ultimaColunaMes;
    col++
  ) {
    const letra = letraColunaGwm(col);

    formulasMargem.push(
      `=IFERROR(AVERAGE(${letra}60:${letra}72)${S}0)`
    );
  }

  aba.getRange(73, primeiraColunaMes, 1, 12)
    .setFormulas([formulasMargem]);

  // Média anual da margem
  aba.getRange(73, colunaTotal)
    .setFormula(`=IFERROR(AVERAGE(N60:N72)${S}0)`);

  SpreadsheetApp.flush();

  SpreadsheetApp.getUi().alert(
    "Fórmulas do orçamento atualizadas."
  );
}


/****************************************************
 * CONFIGURAÇÃO GERAL
 *
 * Executa a configuração inicial somente quando
 * a estrutura do orçamento ainda não existe.
 ****************************************************/

function configurarPlanilhaGwmUberlandia() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const abaOrcamento = ss.getSheetByName("Orçamento 2026");

  if (abaOrcamento) {
    const dados = abaOrcamento.getDataRange().getDisplayValues();
    const possuiConteudo = dados.some(linha =>
      linha.some(valor => valor !== "")
    );

    if (possuiConteudo) {
      SpreadsheetApp.getUi().alert(
        "A planilha já possui orçamento. " +
        "A configuração inicial foi interrompida para preservar os dados. " +
        "Se deseja atualizar as fórmulas, execute " +
        "atualizarFormulasOrcamentoUberlandia()."
      );
      return;
    }
  }

  configurarAbasMensaisGwm();
  criarEstruturaOrcamentoGwm();

  SpreadsheetApp.flush();

  SpreadsheetApp.getUi().alert(
    "Estrutura inicial configurada."
  );
}


/****************************************************
 * DETECTA O SEPARADOR DE ARGUMENTOS DA PLANILHA
 *
 * Planilhas em português (Brasil) podem exigir ";"
 * mesmo dentro do script. Testamos numa aba temporária
 * e descobrimos qual funciona, sem depender de idioma.
 ****************************************************/

function separadorArgumentos() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const temp = ss.insertSheet("tmp_teste_separador");

  try {
    const cel = temp.getRange("A1");
    // MAX(1,3): com vírgula como separador dá 3; se a vírgula for decimal (pt-BR) vira 1,3
    cel.setFormula("=MAX(1,3)");
    SpreadsheetApp.flush();
    return cel.getDisplayValue() === "3" ? "," : ";";
  } finally {
    ss.deleteSheet(temp);
  }
}


/****************************************************
 * COLUNAS NOVAS (TEST DRIVE, CAPTAÇÃO) + MENUS SUSPENSOS
 *
 * Seguro para planilhas que já têm dados: não apaga nem move
 * nada. Só preenche os cabeçalhos novos (colunas Q e R) se
 * estiverem vazios, aplica as listas e estende o filtro.
 * Pode rodar quantas vezes quiser.
 ****************************************************/

function aplicarListasEColunasGwm() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = CONFIG_GWM;
  const cores = config.cores;
  const listas = config.listas;
  const total = config.colunas.length;   // 18
  const ultimaLinha = 1000;

  // coluna -> lista (C = TIPO, D = STATUS, G = COR, I = VEND, Q = TEST DRIVE, R = CAPTAÇÃO)
  const menus = [
    { coluna: 3,  lista: listas.tipo },
    { coluna: 4,  lista: listas.status },
    { coluna: 7,  lista: listas.cores },
    { coluna: 9,  lista: listas.vendedores },
    { coluna: 17, lista: listas.simNao },
    { coluna: 18, lista: listas.simNao }
  ];

  let abasAtualizadas = 0;

  config.meses.forEach(mes => {
    const aba = ss.getSheetByName(mes);
    if (!aba) return;

    // Cabeçalhos novos: só escreve onde estiver vazio
    for (let c = 17; c <= total; c++) {
      const cel = aba.getRange(1, c);
      if (cel.isBlank()) cel.setValue(config.colunas[c - 1]);
      aba.setColumnWidth(c, 120);
    }

    aba.getRange(1, 1, 1, total)
      .setBackground(cores.escuro)
      .setFontColor(cores.branco)
      .setFontWeight("bold")
      .setHorizontalAlignment("center")
      .setWrap(true);

    aba.getRange(2, 17, ultimaLinha - 1, 2).setHorizontalAlignment("center");

    // Menus suspensos fixos (não aceita nome fora da lista)
    menus.forEach(m => {
      const regra = SpreadsheetApp.newDataValidation()
        .requireValueInList(m.lista, true)
        .setAllowInvalid(false)
        .build();
      aba.getRange(2, m.coluna, ultimaLinha - 1, 1).setDataValidation(regra);
    });

    // O filtro precisa cobrir as colunas novas
    const filtro = aba.getFilter();
    if (!filtro || filtro.getRange().getLastColumn() < total) {
      if (filtro) filtro.remove();
      aba.getRange(1, 1, ultimaLinha, total).createFilter();
    }

    abasAtualizadas++;
  });

  SpreadsheetApp.flush();
  SpreadsheetApp.getUi().alert(
    "Colunas e listas aplicadas em " + abasAtualizadas + " aba(s) mensal(is)."
  );
}


/****************************************************
 * MENU
 ****************************************************/

function onOpen() {
  SpreadsheetApp.getUi().createMenu("📊 GWM")
    .addItem("Adicionar colunas e listas (meses)", "aplicarListasEColunasGwm")
    .addItem("Atualizar fórmulas do orçamento", "atualizarFormulasOrcamentoUberlandia")
    .addToUi();
}