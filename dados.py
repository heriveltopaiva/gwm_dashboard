"""Leitura e cálculo dos dados do Controle GWM (nada de tela aqui)."""
import unicodedata

import gspread
import pandas as pd

LOJAS = ["Loja 01", "Loja 02", "Loja 03", "Loja 04"]
ABA_METAS = "Metas"


def norm(texto):
    """Minúsculo e sem acento: 'Devolução ' -> 'devolucao'."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return t.strip().lower()


def ler_planilha(info_conta, planilha_id):
    """Lê as 4 lojas + Metas em UMA chamada. Só leitura: nunca escreve na planilha."""
    gc = gspread.service_account_from_dict(info_conta)
    planilha = gc.open_by_key(planilha_id)
    intervalos = [f"'{loja}'!A:Q" for loja in LOJAS] + [f"'{ABA_METAS}'!A:F"]
    resp = planilha.values_batch_get(intervalos, params={"valueRenderOption": "UNFORMATTED_VALUE"})
    return [b.get("values", []) for b in resp["valueRanges"]]


def _bloco_para_df(valores):
    if len(valores) < 2:
        return pd.DataFrame()
    cab = [str(c).strip().upper() for c in valores[0]]
    n = len(cab)
    linhas = [(list(l) + [""] * n)[:n] for l in valores[1:]]
    return pd.DataFrame(linhas, columns=cab)


def _datas(serie):
    """Aceita número de data do Sheets (ex.: 46296) ou texto 'dd/mm/aaaa'."""
    def conv(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(v))
        if isinstance(v, str) and v.strip():
            return pd.to_datetime(v, dayfirst=True, errors="coerce")
        return pd.NaT
    return pd.to_datetime(serie.map(conv), errors="coerce").dt.normalize()


def _numero(serie):
    return pd.to_numeric(serie, errors="coerce").fillna(0.0)


def _preparar_metas(valores):
    vazio = pd.DataFrame(columns=["MES", "LOJA", "META_FAT", "META_LB"])
    df = _bloco_para_df(valores)
    if df.empty or df.shape[1] < 4:
        return vazio
    out = pd.DataFrame({
        "MES": _datas(df.iloc[:, 0]).dt.to_period("M"),
        "LOJA": df.iloc[:, 1].astype(str).str.strip(),
        "META_FAT": _numero(df.iloc[:, 2]),
        "META_LB": _numero(df.iloc[:, 3]),
    })
    return out[out["MES"].notna()].reset_index(drop=True)


def preparar(blocos):
    """Transforma o que veio da planilha em duas tabelas limpas: vendas e metas."""
    quadros = []
    for loja, valores in zip(LOJAS, blocos[:len(LOJAS)]):
        df = _bloco_para_df(valores)
        if not df.empty:
            df["LOJA"] = loja
            quadros.append(df)
    cols_texto = ["TIPO", "STATUS", "CHASSI", "FAMILIA", "COR", "NOME CLIENTE", "VEND"]
    cols_num = ["VENDA", "CUSTO", "INCID"]
    cols_data = ["DATA PEDIDO", "DATA FAT"]
    metas = _preparar_metas(blocos[len(LOJAS)] if len(blocos) > len(LOJAS) else [])
    if not quadros:
        return pd.DataFrame(columns=cols_texto + cols_num + cols_data + ["LOJA", "STATUS_N", "LB"]), metas

    v = pd.concat(quadros, ignore_index=True)
    for c in cols_texto + cols_num + cols_data:
        if c not in v.columns:
            v[c] = ""
    for c in cols_data:
        v[c] = _datas(v[c])
    for c in cols_texto:
        v[c] = v[c].astype(str).str.strip()
    for c in cols_num:
        v[c] = _numero(v[c])
    # linha só existe se tiver data do pedido ou chassi
    v = v[v["DATA PEDIDO"].notna() | (v["CHASSI"] != "")].copy()
    v["STATUS_N"] = v["STATUS"].map(norm)
    v["LB"] = v["VENDA"] - v["CUSTO"] - v["INCID"]
    dev = v["STATUS_N"] == "devolucao"
    v.loc[dev, "LB"] = -v.loc[dev, "LB"].abs()
    return v.reset_index(drop=True), metas


def indicadores(base, ini, fim):
    """Calcula os números do período. ini/fim são datas (inclusive)."""
    ini, fim = pd.Timestamp(ini), pd.Timestamp(fim)
    no_fat = base["DATA FAT"].between(ini, fim)
    no_ped = base["DATA PEDIDO"].between(ini, fim)
    fat = base[(base["STATUS_N"] == "faturado") & no_fat]
    dev = base[(base["STATUS_N"] == "devolucao") & no_fat]
    canc = base[(base["STATUS_N"] == "cancelado") & no_ped]
    aguard = base[base["STATUS_N"] == "aguardando faturamento"]
    return {
        "valor": float(fat["VENDA"].sum()), "qtd": len(fat),
        "lb": float(fat["LB"].sum() + dev["LB"].sum()),
        "dev_n": len(dev), "canc_n": len(canc), "aguard_n": len(aguard),
        "fat": fat, "dev": dev, "canc": canc, "aguard": aguard,
    }


def meta_periodo(metas, lojas, ini, fim):
    """Soma as metas de faturamento dos meses que o período toca."""
    if metas.empty:
        return 0.0
    meses = pd.period_range(pd.Timestamp(ini), pd.Timestamp(fim), freq="M")
    m = metas[metas["MES"].isin(meses) & metas["LOJA"].isin(lojas)]
    return float(m["META_FAT"].sum())
