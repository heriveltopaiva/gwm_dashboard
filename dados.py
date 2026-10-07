"""Leitura e cálculo dos dados do Dashboard CLAYTON GWM."""
import re
import unicodedata

import gspread
import pandas as pd

# Cadastro técnico das quatro unidades. Os IDs são preenchidos em secrets.toml.
UNIDADES = [
    {"chave": "uberlandia", "cnpj": "48.337.247/0003-96", "nome": "GWM Uberlândia", "responsavel": "Poliana"},
    {"chave": "uberaba", "cnpj": "48.337.247/0008-09", "nome": "GWM Uberaba", "responsavel": "Fernanda"},
    {"chave": "passos", "cnpj": "48.337.247/0009-81", "nome": "GWM Passos", "responsavel": "Gerente 02"},
    {"chave": "patos_de_minas", "cnpj": "48.337.247/0010-15", "nome": "GWM Patos de Minas", "responsavel": "Gerente 01"},
]
MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
ABA_ORCAMENTO = "Orçamento 2026"
ANO_ORCAMENTO = int(re.search(r"\d{4}", ABA_ORCAMENTO).group())
COLUNAS_OPERACIONAIS = [
    "DATA PEDIDO", "DATA FAT", "TIPO", "STATUS", "CHASSI", "FAMILIA",
    "COR", "NOME CLIENTE", "VEND", "LOCAL", "VENDA", "CUSTO", "INCID",
    "LB", "OBS", "OBS2", "TEST DRIVE", "CAPTAÇÃO", "MODELO", "PLACA", "EMISSÃO",
]


def norm(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return t.strip().lower()


def _normalizar_cabecalho(valores):
    if not valores:
        return []
    return [str(c).strip().upper() for c in valores[0]]


def _bloco_para_df(valores):
    if len(valores) < 2:
        return pd.DataFrame()
    cab = _normalizar_cabecalho(valores)
    if not cab or not any(cab):
        return pd.DataFrame()
    n = len(cab)
    linhas = [(list(l) + [""] * n)[:n] for l in valores[1:]]
    return pd.DataFrame(linhas, columns=cab)


def ler_planilhas(info_conta, ids_planilhas):
    """Lê as abas mensais de cada unidade configurada; nunca escreve nas fontes.

    ids_planilhas é um dicionário chave_da_unidade -> ID do Google Sheets.
    IDs vazios são ignorados. Devolve também o texto bruto da aba Orçamento de cada
    unidade (usado para montar as metas). Erros/abas ausentes viram avisos
    para que o dashboard não esconda problemas de origem.
    """
    gc = gspread.service_account_from_dict(info_conta)
    blocos, avisos, unidades_lidas, orcamentos = [], [], [], []
    for unidade in UNIDADES:
        planilha_id = str(ids_planilhas.get(unidade["chave"], "") or "").strip()
        if not planilha_id:
            continue
        try:
            planilha = gc.open_by_key(planilha_id)
            abas_existentes = {aba.title for aba in planilha.worksheets()}
            intervalos = []
            meses_presentes = []
            for mes in MESES:
                if mes in abas_existentes:
                    intervalos.append(f"'{mes}'!A:R")
                    meses_presentes.append(mes)
                else:
                    avisos.append(f"{unidade['nome']}: aba mensal '{mes}' não encontrada.")
            if not meses_presentes:
                avisos.append(f"{unidade['nome']}: nenhuma aba mensal foi encontrada.")
                continue
            tem_orcamento = ABA_ORCAMENTO in abas_existentes
            busca = intervalos + ([f"'{ABA_ORCAMENTO}'!A:N"] if tem_orcamento else [])
            resposta = planilha.values_batch_get(
                busca,
                params={"valueRenderOption": "UNFORMATTED_VALUE"},
            )
            faixas = resposta.get("valueRanges", [])
            if tem_orcamento and len(faixas) > len(intervalos):
                orcamentos.append({
                    "loja": unidade["nome"],
                    "valores": faixas[len(intervalos)].get("values", []),
                })
            for mes, intervalo, retorno in zip(meses_presentes, intervalos, faixas):
                valores = retorno.get("values", [])
                df = _bloco_para_df(valores)
                if df.empty:
                    continue
                # Colunas operacionais são padronizadas pela arquitetura. Mantemos
                # colunas extras apenas se vierem na fonte, sem exigir que existam.
                df["LOJA"] = unidade["nome"]
                df["CNPJ"] = unidade["cnpj"]
                df["RESPONSAVEL"] = unidade["responsavel"]
                df["MES_ORIGEM"] = mes
                blocos.append(df)
            unidades_lidas.append(unidade["nome"])
            if not tem_orcamento:
                avisos.append(f"{unidade['nome']}: aba '{ABA_ORCAMENTO}' não encontrada (sem metas).")
        except Exception as exc:
            avisos.append(f"{unidade['nome']}: falha na leitura ({exc}).")
    return blocos, avisos, unidades_lidas, orcamentos


def _datas(serie):
    """Aceita serial do Google Sheets ou texto de data."""
    def conv(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(v))
        if isinstance(v, str) and v.strip():
            return pd.to_datetime(v, dayfirst=True, errors="coerce")
        return pd.NaT
    return pd.to_datetime(serie.map(conv), errors="coerce").dt.normalize()


def _para_float(v):
    """Número de uma célula do Sheets (int/float) ou texto brasileiro ("R$ 1.234,56")."""
    if isinstance(v, bool):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace("R$", "").replace(" ", "")
    if not t:
        return 0.0
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def _numero(serie):
    """Converte para número célula a célula.

    O Sheets entrega números já tipados (int/float); texto só aparece se alguém
    digitar "R$ 1.234,56". Só tratamos separador brasileiro quando há vírgula,
    para nunca estragar um valor como 140000.5.
    """
    return serie.map(_para_float).astype(float)


COLUNAS_METAS = ["MES", "LOJA", "META_FAT", "META_LB", "META_QTD"]


def _metas_do_orcamento(valores, loja, ano=ANO_ORCAMENTO):
    """Lê a aba Orçamento (uma unidade) e devolve uma linha de meta por mês.

    Não depende de número de linha: localiza os blocos pelos títulos
    (QUANTIDADE, VALOR UNITÁRIO, LUCRO BRUTO) e cada modelo pelo nome.
      META_QTD = soma da quantidade orçada
      META_FAT = soma de quantidade x valor unitário (faturamento orçado)
      META_LB  = soma do lucro bruto orçado
    """
    blocos = {"qtd": {}, "valor": {}, "lucro": {}}
    atual = None
    ignorar = {"", "modelo", "total", "media", "faturamento orcado"}
    for linha in valores:
        if not linha:
            continue
        rotulo = norm(linha[0])
        if rotulo.startswith("quantidade de veiculos"):
            atual = "qtd"
        elif rotulo.startswith("valor unitario"):
            atual = "valor"
        elif rotulo.startswith("lucro bruto"):
            atual = "lucro"
        elif rotulo.startswith("% margem"):
            atual = None
        elif atual and rotulo not in ignorar:
            cel = (list(linha[1:13]) + [""] * 12)[:12]
            blocos[atual][rotulo] = [_para_float(c) for c in cel]
    if not blocos["qtd"]:
        return pd.DataFrame(columns=COLUNAS_METAS)
    linhas = []
    for i in range(12):
        qtd = sum(v[i] for v in blocos["qtd"].values())
        fat = sum(q[i] * blocos["valor"].get(m, [0.0] * 12)[i] for m, q in blocos["qtd"].items())
        lucro = sum(v[i] for v in blocos["lucro"].values())
        linhas.append({"MES": pd.Period(f"{ano}-{i + 1:02d}", freq="M"), "LOJA": loja,
                       "META_FAT": fat, "META_LB": lucro, "META_QTD": qtd})
    return pd.DataFrame(linhas, columns=COLUNAS_METAS)


def preparar(blocos, orcamentos=None):
    """Consolida os blocos mensais em uma base operacional única."""
    colunas_vazias = COLUNAS_OPERACIONAIS + ["LOJA", "CNPJ", "RESPONSAVEL", "MES_ORIGEM", "STATUS_N"]
    quadros_meta = [_metas_do_orcamento(o["valores"], o["loja"]) for o in (orcamentos or [])]
    quadros_meta = [q for q in quadros_meta if not q.empty]
    metas = pd.concat(quadros_meta, ignore_index=True) if quadros_meta else pd.DataFrame(columns=COLUNAS_METAS)
    if not blocos:
        return pd.DataFrame(columns=colunas_vazias), metas
    v = pd.concat(blocos, ignore_index=True, sort=False)
    # Aceita variações de escrita no cabeçalho (ex.: CAPTACAO, Test Drive).
    apelidos = {"test drive": "TEST DRIVE", "captacao": "CAPTAÇÃO"}
    v = v.rename(columns={c: apelidos[norm(c)] for c in v.columns if norm(c) in apelidos})
    for c in COLUNAS_OPERACIONAIS:
        if c not in v.columns:
            v[c] = ""
    for c in ["DATA PEDIDO", "DATA FAT"]:
        v[c] = _datas(v[c])
    for c in ["TIPO", "STATUS", "CHASSI", "FAMILIA", "COR", "NOME CLIENTE", "VEND", "LOCAL", "OBS", "OBS2", "TEST DRIVE", "CAPTAÇÃO"]:
        v[c] = v[c].fillna("").astype(str).str.strip()
    for c in ["VENDA", "CUSTO", "INCID"]:
        v[c] = _numero(v[c])
    # Usa a LB da fonte quando numérica e preenchida; caso contrário, calcula.
    lb_fonte = _numero(v["LB"])
    lb_preenchida = v["LB"].notna() & v["LB"].astype(str).str.strip().ne("")
    v["LB"] = lb_fonte.where(lb_preenchida, v["VENDA"] - v["CUSTO"] - v["INCID"])
    v = v[v["DATA PEDIDO"].notna() | v["DATA FAT"].notna() | v["CHASSI"].ne("")].copy()
    v["STATUS_N"] = v["STATUS"].map(norm).replace({"cancelada": "cancelado"})  # aceita as duas grafias
    devolucao = v["STATUS_N"].eq("devolucao")
    v.loc[devolucao, "LB"] = -v.loc[devolucao, "LB"].abs()
    return v.reset_index(drop=True), metas


def indicadores(base, ini, fim):
    """Calcula indicadores do período (datas inclusivas)."""

    ini, fim = pd.Timestamp(ini), pd.Timestamp(fim)

    no_fat = base["DATA FAT"].between(ini, fim)
    no_ped = base["DATA PEDIDO"].between(ini, fim)

    status = base["STATUS_N"].map(norm)
    tipo = base["TIPO"].map(norm)

    # =========================
    # VENDAS FATURADAS
    # =========================
    fat = base[
        (status == "faturado") &
        no_fat
    ].copy()

    # =========================
    # VENDAS 0 KM
    # =========================
    tipos_0km = {
        "pedido",
        "firmorder",
        "emplacado",
    }

    fat_0km = fat[
        fat["TIPO"].map(norm).isin(tipos_0km)
    ].copy()

    # =========================
    # VENDAS DE USADOS
    # =========================
    fat_usado = fat[
        fat["TIPO"].map(norm) == "usado"
    ].copy()

    # =========================
    # DEVOLUÇÕES
    # =========================
    dev = base[
        (status == "devolucao") &
        no_fat
    ]

    # =========================
    # CANCELAMENTOS
    # =========================
    canc = base[
        (status == "cancelado") &
        no_ped
    ]

    # =========================
    # AGUARDANDO FATURAMENTO
    # =========================
    aguard = base[
        (status == "aguardando faturamento") |
        (
            (status == "") &
            base["DATA PEDIDO"].notna()
        )
    ]

    return {
        # Faturamento TOTAL
        "valor": float(fat["VENDA"].sum()),

        # Quantidade TOTAL faturada
        "qtd": len(fat),

        # NOVOS INDICADORES
        "qtd_0km": len(fat_0km),
        "qtd_usado": len(fat_usado),

        "valor_0km": float(fat_0km["VENDA"].sum()),
        "valor_usado": float(fat_usado["VENDA"].sum()),

        # Lucro
        "lb": float(
            fat["LB"].sum() +
            dev["LB"].sum()
        ),

        "dev_n": len(dev),
        "canc_n": len(canc),
        "aguard_n": len(aguard),

        # Bases
        "fat": fat,
        "fat_0km": fat_0km,
        "fat_usado": fat_usado,
        "dev": dev,
        "canc": canc,
        "aguard": aguard,
    }

def indicadores_extras(base, ini, fim):
    """
    Indicadores comerciais do período.

    Pedidos:
        Todas as linhas cuja DATA PEDIDO esteja no período.

    Test Drive:
        TEST DRIVE = Sim.

    Emplacados:
        TIPO = Emplacado
        e STATUS = Faturado.

    Usado na troca:
        CAPTAÇÃO = Sim
        e STATUS = Faturado.

    Os percentuais são sobre todos os pedidos do período.
    """

    ini, fim = pd.Timestamp(ini), pd.Timestamp(fim)

    # ==========================================
    # PEDIDOS DO PERÍODO
    # ==========================================
    ped = base[
        base["DATA PEDIDO"].between(ini, fim)
    ].copy()

    n = len(ped)

    status = ped["STATUS_N"].map(norm)
    tipo = ped["TIPO"].map(norm)

    # ==========================================
    # TEST DRIVE
    # ==========================================
    td = int(
        (ped["TEST DRIVE"].map(norm) == "sim").sum()
    )

    # ==========================================
    # EMPLACADOS
    # ==========================================
    emp = int(
        (
            (tipo == "emplacado") &
            (status == "faturado")
        ).sum()
    )

    # ==========================================
    # USADO NA TROCA
    # ==========================================
    cap = int(
        (
            (ped["CAPTAÇÃO"].map(norm) == "sim") &
            (status == "faturado")
        ).sum()
    )

    return {
        "pedidos": n,

        "td_n": td,
        "emp_n": emp,
        "cap_n": cap,

        "td_pct": td / n if n else 0.0,
        "emp_pct": emp / n if n else 0.0,
        "cap_pct": cap / n if n else 0.0,

        "ped": ped,
    }

def extras_por_vendedor(ped):
    """Quantidade de pedidos, test drives, emplacados e usados na troca por vendedor."""
    if ped.empty:
        return pd.DataFrame(columns=["VEND", "Pedidos", "Test drive", "Emplacados", "Usado na troca"])
    g = pd.DataFrame({
        "VEND": ped["VEND"].replace("", "(sem vendedor)"),
        "Pedidos": 1,
        "Test drive": (ped["TEST DRIVE"].map(norm) == "sim").astype(int),
        "Emplacados": (ped["TIPO"].map(norm) == "emplacado").astype(int),
        "Usado na troca": (ped["CAPTAÇÃO"].map(norm) == "sim").astype(int),
    })
    return g.groupby("VEND", as_index=False).sum()