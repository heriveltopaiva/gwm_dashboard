"""
Gera dados sintéticos de vendas GWM — 1 TSV por cidade, 12 meses/2026.

Estrutura gerada automaticamente:
    seu_projeto/
    ├── gerar_dados.py
    ├── config/
    │   └── listas_gwm.json
    ├── logs/
    │   └── geracao_YYYY-MM-DD.log
    └── saida/
        ├── UBERLANDIA.tsv
        ├── UBERABA.tsv
        ├── PASSOS.tsv
        ├── PATOS_DE_MINAS.tsv
        └── _resumo.txt
"""

import random
import csv
import os
import json
import sys
from datetime import datetime, timedelta

# ============================================================
# CONFIGURAÇÃO DE PASTAS
# ============================================================
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(BASE_DIR, "config")
SAIDA_DIR   = os.path.join(BASE_DIR, "saida")
LOGS_DIR    = os.path.join(BASE_DIR, "logs")

for pasta in (CONFIG_DIR, SAIDA_DIR, LOGS_DIR):
    os.makedirs(pasta, exist_ok=True)

# ============================================================
# SEED E LOG
# ============================================================
SEED = 42
random.seed(SEED)

LOG_PATH = os.path.join(LOGS_DIR, f"geracao_{datetime.now():%Y-%m-%d_%H%M%S}.log")

def log(msg: str) -> None:
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ============================================================
# LISTAS — devem ser IDÊNTICAS a CONFIG_GWM.listas no Apps Script
# ============================================================
LISTAS = {
    "tipo":       ["Firmorder", "Pedido", "Usado", "Emplacado"],
    "status":     ["Faturado", "Cancelada", "Devolução"],
    "vendedores": ["CAMILA", "FERNANDA", "KELBY", "LUDMILLE",
                   "MARCOS", "PATRICIA", "POLIANA", "WENDELL"],
    "cores":      ["Azul topazio", "Azul Cianita", "Azul copacabana",
                   "Cinza diamante", "Cinza Amazonita", "Prata Lunar",
                   "Preto Hematita", "Preto Khalifa", "Vermelho Granada",
                   "Grafitte Zenith", "Solar Gold", "Verde Turmalina",
                   "VerdeEsmeralda", "Branco", "Laranja", "Cinza Titanium"],
    "simNao":     ["Sim", "Não"],
}

MODELOS_GWM = [
    "ORA SKIN", "ORA SKIN 58", "ORA 5",
    "HAVAL H6 HEV ONE", "HAVAL H6 HEV 2", "HAVAL H6 PHEV 19",
    "HAVAL H6 PHEV 34", "HAVAL H6 GT", "HAVAL H9 EXCL.",
    "TANK 300", "POER P30 EXCL.", "POER P30 TRAIL", "WEY 07",
]

MODELOS_TROCA = [
    "COROLLA XEI 2.0 FLEX 16V AUT.",
    "COMPASS LONG. T270 1.3 TB 4X2 FLEX AUT.",
    "COMPASS SPORT T270 1.3 TB 4X2 FLEX AUT.",
    "COROLLA CROSS XRE 2.0 16V FLEX AUT",
    "STRADA ULTRA 1.0 FLEX TURBO CD AUT.",
    "TRACKER PREMIER 1.2 TURBO 12V FLEX AUT.",
    "HR-V EXL 1.8 FLEXONE 16V 5P AUT.",
    "HAVAL H6 GT 1.5 AWD (HIBRIDO)",
    "RENEGADE SPORT 1.3 TURBO FLEX AUT.",
    "PULSE DRIVE 1.0 TURBO FLEX AUT.",
]

PRECO_TABELA = {
    "ORA SKIN":          159000,
    "ORA SKIN 58":       169000,
    "ORA 5":             189000,
    "HAVAL H6 HEV ONE":  199000,
    "HAVAL H6 HEV 2":    220000,
    "HAVAL H6 PHEV 19":  245000,
    "HAVAL H6 PHEV 34":  288000,
    "HAVAL H6 GT":       325000,
    "HAVAL H9 EXCL.":    319000,
    "TANK 300":          339000,
    "POER P30 EXCL.":    240000,
    "POER P30 TRAIL":    220000,
    "WEY 07":            429000,
}

# Salva as listas em JSON (útil pra sincronizar com o Apps Script)
with open(os.path.join(CONFIG_DIR, "listas_gwm.json"), "w", encoding="utf-8") as f:
    json.dump({"listas": LISTAS, "modelos": MODELOS_GWM}, f,
              ensure_ascii=False, indent=2)

# ============================================================
# PERÍODO — 12 meses de 2026
# ============================================================
MESES = [(m, 2026) for m in range(1, 13)]   # 1..12

# ============================================================
# CONFIG POR CIDADE (qtd mínima, qtd máxima por mês)
# ============================================================
CIDADES_CONFIG = {
    "UBERLANDIA":     (20, 40),
    "UBERABA":        (15, 30),
    "PASSOS":       (10, 20),
    "PATOS DE MINAS": (8, 18),
}

# ============================================================
# HELPERS
# ============================================================
def data_fmt(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")

def brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

_chassis = set()
def chassi_unico() -> str:
    while True:
        c = "9BW" + "".join(random.choices("0123456789", k=14))
        if c not in _chassis:
            _chassis.add(c)
            return c

def placa() -> str:
    if random.random() < 0.5:
        return (f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}-"
                f"{random.randint(1000, 9999)}")
    return (f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}"
            f"{random.randint(0,9)}"
            f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            f"{random.randint(10,99)}")

def data_aleatoria_no_mes(ano: int, mes: int) -> datetime:
    prox = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)
    dias = (prox - datetime(ano, mes, 1)).days
    return datetime(ano, mes, 1) + timedelta(days=random.randint(0, dias - 1))

# ============================================================
# GERAÇÃO DE UMA LINHA (21 colunas, ordem do Apps Script)
# ============================================================
def gerar_linha(ano: int, mes: int, cidade: str, idx: int) -> list:
    data_pedido  = data_aleatoria_no_mes(ano, mes)
    data_fat     = data_pedido + timedelta(days=random.randint(1, 10))
    data_emissao = data_fat + timedelta(days=random.randint(150, 200))

    tipo   = random.choices(LISTAS["tipo"],   weights=[3, 5, 1, 2])[0]
    status = random.choices(LISTAS["status"], weights=[8, 1, 1])[0]

    modelo = random.choice(MODELOS_GWM)
    tabela = PRECO_TABELA[modelo]

    venda = round(tabela * (1 - random.uniform(0.03, 0.10)), 2)
    custo = round(venda * random.uniform(0.82, 0.90), 2)
    incid = round(venda * random.uniform(0.05, 0.09), 2)
    lb    = round(venda - custo - incid, 2)

    tem_troca    = random.choice(LISTAS["simNao"])
    tem_captacao = random.choice(LISTAS["simNao"])

    if tem_troca == "Sim":
        modelo_troca = random.choice(MODELOS_TROCA)
        placa_troca  = placa()
        emissao      = data_fmt(data_emissao)
    else:
        modelo_troca = placa_troca = emissao = ""

    return [
        data_fmt(data_pedido),                # A  DATA PEDIDO
        data_fmt(data_fat),                   # B  DATA FAT
        tipo,                                 # C  TIPO
        status,                               # D  STATUS
        chassi_unico(),                       # E  CHASSI
        modelo,                               # F  FAMILIA
        random.choice(LISTAS["cores"]),       # G  COR
        f"CLIENTE TESTE {idx:04d}",           # H  NOME CLIENTE
        random.choice(LISTAS["vendedores"]),  # I  VEND
        cidade,                               # J  LOCAL
        brl(venda),                           # K  VENDA
        brl(custo),                           # L  CUSTO
        brl(incid),                           # M  INCID
        brl(lb),                              # N  LB
        "",                                   # O  OBS
        "",                                   # P  OBS2
        tem_troca,                            # Q  TEST DRIVE
        tem_captacao,                         # R  CAPTAÇÃO
        modelo_troca,                         # S  MODELO
        placa_troca,                          # T  PLACA
        emissao,                              # U  EMISSÃO
    ]

# ============================================================
# LOOP PRINCIPAL — 1 TSV por cidade
# ============================================================
log("=" * 60)
log(f"GERAÇÃO DE DADOS SINTÉTICOS GWM — {datetime.now():%d/%m/%Y %H:%M:%S}")
log(f"Seed: {SEED} | Período: 01/2026 a 12/2026 | Cidades: {len(CIDADES_CONFIG)}")
log("=" * 60)

resumo_linhas = []

for cidade, (qmin, qmax) in CIDADES_CONFIG.items():
    log(f"\n=== {cidade} ===")
    linhas = []
    idx = 1
    total_por_mes = {}

    for mes, ano in MESES:
        qtd = random.randint(qmin, qmax)
        total_por_mes[f"{mes:02d}/{ano}"] = qtd
        for _ in range(qtd):
            linhas.append(gerar_linha(ano, mes, cidade, idx))
            idx += 1

    # resumo compacto por mês
    linha_resumo = "  " + " | ".join(
        f"{k}: {v}" for k, v in total_por_mes.items()
    )
    log(linha_resumo)

    # nome do arquivo: espaços viram underscore
    nome_arq = f"{cidade.replace(' ', '_')}.tsv"
    caminho = os.path.join(SAIDA_DIR, nome_arq)

    with open(caminho, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerows(linhas)

    log(f"  TOTAL: {len(linhas)} linhas -> saida/{nome_arq}")
    resumo_linhas.append((cidade, len(linhas), nome_arq))

# ============================================================
# RESUMO FINAL + ARQUIVO _resumo.txt
# ============================================================
log("\n" + "=" * 60)
log("RESUMO FINAL")
log("=" * 60)

linhas_resumo_txt = [
    f"Resumo da geração — {datetime.now():%d/%m/%Y %H:%M:%S}",
    f"Seed: {SEED}",
    f"Período: 01/2026 a 12/2026",
    "",
    f"{'CIDADE':<18} {'LINHAS':>8}   ARQUIVO",
    "-" * 50,
]

total_geral = 0
for cidade, total, arq in resumo_linhas:
    linha = f"{cidade:<18} {total:>8}   saida/{arq}"
    log(linha)
    linhas_resumo_txt.append(linha)
    total_geral += total

linha_total = f"{'TOTAL GERAL':<18} {total_geral:>8}"
log(linha_total)
linhas_resumo_txt.append("-" * 50)
linhas_resumo_txt.append(linha_total)

with open(os.path.join(SAIDA_DIR, "_resumo.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_resumo_txt))

log(f"\nLog salvo em: logs/{os.path.basename(LOG_PATH)}")
log(f"Resumo salvo em: saida/_resumo.txt")
log("\nConcluído com sucesso. ✅")