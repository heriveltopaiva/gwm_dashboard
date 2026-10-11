"""
Envia os TSVs para o Google Sheets usando credenciais do
.streamlit/secrets.toml — versão anti-429 com retry e pausas.

Uso:
    python3 enviar_sheets.py                          # todas as cidades
    python3 enviar_sheets.py --cidade UBERLANDIA      # só uma cidade
    python3 enviar_sheets.py --limpar                 # limpa antes de enviar
    python3 enviar_sheets.py --dry-run                # simula, não envia
    python3 enviar_sheets.py --sujo                   # usa *_suja.tsv
    python3 enviar_sheets.py --pausa 8                # pausa maior entre cidades
"""

import os
import time
import toml
import argparse
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# ARGS
# ============================================================
parser = argparse.ArgumentParser()
parser.add_argument("--sujo",    action="store_true",
                    help="Usa arquivos com sufixo _suja")
parser.add_argument("--dry-run", action="store_true",
                    help="Simula sem enviar")
parser.add_argument("--limpar",  action="store_true",
                    help="Limpa as abas antes de inserir")
parser.add_argument("--cidade",  type=str, default=None,
                    help="Envia só uma cidade (ex: UBERLANDIA)")
parser.add_argument("--pausa",   type=float, default=5.0,
                    help="Segundos entre cidades (default: 5)")
args = parser.parse_args()

# ============================================================
# PASTAS
# ============================================================
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
SAIDA_DIR    = os.path.join(BASE_DIR, "saida")
LOGS_DIR     = os.path.join(BASE_DIR, "logs")
SECRETS_PATH = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")

os.makedirs(LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOGS_DIR, f"envio_{datetime.now():%Y-%m-%d_%H%M%S}.log")


def log(msg=""):
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# ============================================================
# RETRY — trata erro 429 (quota) com espera exponencial
# ============================================================
def retry(fn, tentativas=5, espera=15):
    """Executa fn() com retry exponencial em erro 429."""
    for t in range(tentativas):
        try:
            return fn()
        except gspread.exceptions.APIError as e:
            msg = str(e)
            if "429" in msg or "Quota exceeded" in msg:
                log(f"  ⏳ Cota atingida. Aguardando {espera}s "
                    f"(tentativa {t+1}/{tentativas})...")
                time.sleep(espera)
                espera = int(espera * 1.5)
            else:
                raise
    raise RuntimeError("Retries esgotados")


# ============================================================
# AUTENTICAÇÃO
# ============================================================
if not os.path.exists(SECRETS_PATH):
    log(f"❌ Arquivo não encontrado: {SECRETS_PATH}")
    raise SystemExit(1)

with open(SECRETS_PATH, encoding="utf-8") as f:
    secrets = toml.load(f)

# tenta achar a seção de credenciais
info = (secrets.get("gcp_service_account")
        or secrets.get("google_service_account")
        or secrets)

if "client_email" not in info:
    log("❌ secrets.toml não contém credenciais de service account.")
    log("   Chaves disponíveis: " + ", ".join(secrets.keys()))
    raise SystemExit(1)

log(f"🔑 Autenticando como: {info['client_email']}")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(info, scopes=SCOPES)
gc = gspread.authorize(creds)


# ============================================================
# PLANILHAS — nome do arquivo TSV  ->  nome no Google Drive
#
# A chave precisa ser IGUAL ao nome do arquivo .tsv
# (sem extensão, com "_" trocado por espaço).
# ============================================================
PLANILHAS = {
    "UBERLANDIA":     "GWM Uberlândia - Vendas 2026",
    "UBERABA":        "GWM Uberaba - Vendas 2026",
    "PASSOS":         "GWM Passos - Vendas 2026",
    "PATOS DE MINAS": "GWM Patos de Minas - Vendas 2026",
}

MESES_NOMES = ["Janeiro", "Fevereiro", "Março", "Abril",
               "Maio", "Junho", "Julho", "Agosto",
               "Setembro", "Outubro", "Novembro", "Dezembro"]


# ============================================================
# ENVIO
# ============================================================
sufixo = "_suja" if args.sujo else ""
arquivos = [f for f in os.listdir(SAIDA_DIR)
            if f.endswith(f"{sufixo}.tsv") and not f.startswith("_")]

if not arquivos:
    log(f"❌ Nenhum TSV em {SAIDA_DIR}")
    raise SystemExit(1)

log("=" * 60)
log(f"ENVIO PARA GOOGLE SHEETS — {datetime.now():%d/%m/%Y %H:%M:%S}")
log(f"Dry-run: {args.dry_run} | Limpar: {args.limpar} | "
    f"Cidade: {args.cidade or 'todas'} | Pausa: {args.pausa}s")
log("=" * 60)

LOTE = 500
total_geral = 0

for arq in sorted(arquivos):
    nome_cidade = arq.replace(sufixo + ".tsv", "").replace("_", " ").strip()

    if nome_cidade not in PLANILHAS:
        log(f"⚠️  Cidade '{nome_cidade}' não cadastrada em PLANILHAS — pulando")
        continue

    if args.cidade and nome_cidade != args.cidade:
        continue

    log(f"\n=== {nome_cidade} ===")

    with open(os.path.join(SAIDA_DIR, arq), encoding="utf-8") as f:
        linhas = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]

    log(f"  Arquivo: {arq} ({len(linhas)} linhas)")

    if args.dry_run:
        log("  [dry-run] nada enviado")
        total_geral += len(linhas)
        continue

    # ---------------------------------------------------------
    # Abre a planilha (com retry)
    # ---------------------------------------------------------
    try:
        sh = retry(lambda: gc.open(PLANILHAS[nome_cidade]))
    except gspread.SpreadsheetNotFound:
        log(f"  ❌ Planilha '{PLANILHAS[nome_cidade]}' não encontrada")
        log(f"     Compartilhe com: {info['client_email']}")
        continue
    except Exception as e:
        log(f"  ❌ Erro ao abrir planilha: {e}")
        continue

    # ---------------------------------------------------------
    # 1 read pega o metadado de TODAS as abas (economiza cota)
    # ---------------------------------------------------------
    try:
        meta = retry(lambda: sh.fetch_sheet_metadata())
        abas_existentes = {
            s["properties"]["title"]
            for s in meta.get("sheets", [])
        }
    except Exception as e:
        log(f"  ❌ Erro ao listar abas: {e}")
        continue

    # ---------------------------------------------------------
    # Agrupa as linhas por mês (coluna A = "dd/mm/yyyy")
    # ---------------------------------------------------------
    por_mes = {m: [] for m in MESES_NOMES}
    invalidas = 0
    for ln in linhas:
        try:
            mes_num = int(ln[0].split("/")[1])
            if 1 <= mes_num <= 12:
                por_mes[MESES_NOMES[mes_num - 1]].append(ln)
            else:
                invalidas += 1
        except Exception:
            invalidas += 1

    if invalidas:
        log(f"  ⚠️  {invalidas} linha(s) com data inválida — ignoradas")

    # ---------------------------------------------------------
    # Envia mês a mês
    # ---------------------------------------------------------
    for nome_mes, linhas_mes in por_mes.items():
        if not linhas_mes:
            continue

        if nome_mes not in abas_existentes:
            log(f"  ⚠️  Aba '{nome_mes}' não existe — pulando")
            continue

        try:
            ws = retry(lambda m=nome_mes: sh.worksheet(m))
        except Exception as e:
            log(f"  ❌ Erro ao abrir aba {nome_mes}: {e}")
            continue

        # descobre a próxima linha vazia
        if args.limpar:
            try:
                retry(lambda w=ws: w.batch_clear([f"A2:U{w.row_count}"]))
                proxima = 2
            except Exception as e:
                log(f"  ❌ Erro ao limpar {nome_mes}: {e}")
                continue
        else:
            try:
                # lê apenas A1:A2000 (bem mais leve que col_values)
                col_a = retry(lambda w=ws: w.get(
                    "A1:A2000",
                    value_render_option="UNFORMATTED_VALUE"
                ))
                n = sum(1 for r in col_a if r and r[0] != "")
                proxima = max(n + 1, 2)
            except Exception:
                proxima = 2  # fallback: assume cabeçalho

        # envia em lotes
        for i in range(0, len(linhas_mes), LOTE):
            pedaco = linhas_mes[i:i+LOTE]
            try:
                retry(lambda p=pedaco, r=proxima + i, w=ws: w.update(
                    range_name=f"A{r}",
                    values=p,
                    value_input_option="USER_ENTERED"
                ))
            except Exception as e:
                log(f"  ❌ Erro em {nome_mes} lote {i}: {e}")

        log(f"  {nome_mes:<10} +{len(linhas_mes):>4} linhas")
        total_geral += len(linhas_mes)

        # pausa curta entre abas (evita rajada de writes)
        time.sleep(1.5)

    # pausa entre cidades
    log(f"  ⏸  pausa {args.pausa}s antes da próxima cidade...")
    time.sleep(args.pausa)


# ============================================================
# RESUMO
# ============================================================
log("\n" + "=" * 60)
log(f"TOTAL ENVIADO: {total_geral} linhas")
log(f"Log salvo em: logs/{os.path.basename(LOG_PATH)}")
log("Concluído. ✅")