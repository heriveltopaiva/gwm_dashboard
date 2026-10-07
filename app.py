"""CLAYTON GWM — Dashboard visual.
Mantém a lógica de dados existente e reorganiza somente a apresentação visual.
Rodar: streamlit run app.py

Correções aplicadas:
  1. Meta da loja não some mais ao filtrar por vendedor.
  2. Cache recebe só o planilha_id (credenciais lidas dentro da função).
  3. Período personalizado usa session_state (sem st.stop() no meio).
  4. base renomeada para base_loja_vendedor (clareza).
  6. chart_layout aceita overrides (evita update_layout duplicado).
"""
import datetime as dt
import re
import warnings
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import dados

# ============================================================
# CONFIGURAÇÃO
# ============================================================
st.set_page_config(
    page_title="CLAYTON GWM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

FUSO = ZoneInfo("America/Sao_Paulo")

# Paleta do layout aprovado
BG = "#071521"
BG_2 = "#0A1D2D"
PANEL = "#0B2235"
PANEL_2 = "#0D2940"
CYAN = "#16C8FF"
CYAN_2 = "#38D7FF"
BLUE = "#1596D1"
YELLOW = "#FFC400"
GREEN = "#22D39A"
RED = "#FF5A5F"
TEXT = "#F4F8FB"
MUTED = "#8FA6B8"
BORDER = "#124866"

# ============================================================
# CSS — somente apresentação
# ============================================================
st.markdown(
    f"""
<style>
    /* ---------- base ---------- */
    .stApp {{
        background:
            radial-gradient(circle at 85% 5%, rgba(22,200,255,.09), transparent 28%),
            linear-gradient(180deg, {BG_2} 0%, {BG} 100%);
        color: {TEXT};
    }}

    /* Remove a faixa fixa do Streamlit que estava passando por cima
       do cabeçalho personalizado. */
    [data-testid="stHeader"],
    [data-testid="stAppHeader"] {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
    }}

    [data-testid="stToolbar"] {{
        visibility: hidden;
        height: 0;
    }}

    .block-container {{
        max-width: 1700px;
        padding: 1.4rem 1.35rem .75rem !important;
    }}

    /* ---------- top header ---------- */
    .gwm-header {{
        position: relative;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        min-height: 72px;
        box-sizing: border-box;
        padding: 14px 4px 16px;
        border-bottom: 1px solid rgba(22,200,255,.22);
        margin-top: 12px;
        margin-bottom: 14px;
        isolation: isolate;
    }}

    .gwm-brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 240px;
    }}

    .gwm-logo {{
        width: 42px;
        height: 42px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(145deg, #0D3853, #071A29);
        border: 1px solid rgba(22,200,255,.45);
        box-shadow: 0 0 20px rgba(22,200,255,.08);
        font-size: 23px;
    }}

    .gwm-name {{
        font-size: 20px;
        font-weight: 800;
        letter-spacing: .4px;
        color: {TEXT};
    }}

    .gwm-name span {{
        color: {CYAN};
        font-weight: 500;
    }}

    .gwm-title {{
        flex: 1;
        text-align: center;
        font-size: 25px;
        font-weight: 800;
        letter-spacing: .3px;
    }}

    .gwm-update {{
        text-align: right;
        color: {MUTED};
        font-size: 12px;
        min-width: 170px;
    }}

    .gwm-update strong {{
        color: {TEXT};
        font-size: 13px;
    }}

    /* ---------- section labels ---------- */
    .section-title {{
        font-size: 14px;
        font-weight: 800;
        color: {TEXT};
        letter-spacing: .35px;
        margin: 8px 0 7px;
        text-transform: uppercase;
    }}

    /* ---------- filter panels ---------- */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
        min-width: 0;
    }}

    .filter-caption {{
        color: {MUTED};
        font-size: 11px;
        margin-bottom: 3px;
    }}

    .filter-strip {{
        background: linear-gradient(180deg, rgba(13,41,64,.86), rgba(8,28,44,.92));
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px 10px 2px;
        margin-bottom: 10px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
    }}

    /* ---------- buttons ---------- */
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid {BORDER};
        background: linear-gradient(180deg, #0E3A57, #09263B);
        color: {TEXT};
        font-weight: 700;
        min-height: 38px;
    }}

    .stButton > button:hover {{
        border-color: {CYAN};
        color: white;
        box-shadow: 0 0 14px rgba(22,200,255,.12);
    }}

    /* ---------- select/date inputs ---------- */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {{
        background: #071A29 !important;
        border-color: #154A68 !important;
        border-radius: 7px !important;
    }}

    div[data-baseweb="select"] span,
    div[data-baseweb="input"] input {{
        color: {TEXT} !important;
    }}

    /* ---------- KPI cards ---------- */
    .kpi-card {{
        background:
            linear-gradient(145deg, rgba(13,45,69,.97), rgba(6,25,39,.98));
        border: 1px solid {BORDER};
        border-radius: 11px;
        padding: 13px 14px 11px;
        min-height: 112px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
    }}

    .kpi-label {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 600;
    }}

    .kpi-value {{
        color: {TEXT};
        font-size: 23px;
        font-weight: 850;
        margin-top: 5px;
        white-space: nowrap;
    }}

    .kpi-money {{
        color: {YELLOW};
    }}

    .kpi-delta {{
        font-size: 11px;
        font-weight: 700;
        margin-top: 5px;
    }}

    .positive {{ color: {GREEN}; }}
    .negative {{ color: {RED}; }}
    .neutral {{ color: {MUTED}; }}

    /* ---------- chart cards ---------- */
    .chart-card {{
        background: linear-gradient(145deg, rgba(10,38,59,.94), rgba(5,24,38,.96));
        border: 1px solid {BORDER};
        border-radius: 11px;
        padding: 5px 8px 0;
        overflow: hidden;
    }}

    /* ---------- tables ---------- */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    /* ---------- tabs ---------- */
    button[data-baseweb="tab"] {{
        color: {MUTED};
        font-weight: 750;
        border-bottom: 2px solid transparent;
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {CYAN};
    }}

    div[data-baseweb="tab-highlight"] {{
        background-color: {CYAN} !important;
    }}

    /* ---------- progress ---------- */
    div[data-testid="stProgressBar"] > div > div {{
        background: linear-gradient(90deg, {BLUE}, {CYAN});
    }}

    /* ---------- hide sidebar ---------- */
    section[data-testid="stSidebar"] {{
        display: none;
    }}

    /* ---------- small screens ---------- */
    @media (max-width: 1100px) {{
        .gwm-title {{ font-size: 20px; }}
        .gwm-update {{ min-width: 125px; }}
        .kpi-value {{ font-size: 19px; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def segredo(chave, padrao=None):
    try:
        return st.secrets[chave]
    except Exception:
        return padrao


def moeda(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    return f"{v * 100:.1f}%".replace(".", ",")


def checar_senha():
    senha = segredo("senha")
    if not senha or st.session_state.get("liberado"):
        return
    st.title("📊 CLAYTON GWM")
    digitada = st.text_input("Digite a senha de acesso", type="password")
    if digitada:
        if digitada == senha:
            st.session_state["liberado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()


# ------------------------------------------------------------
# CORREÇÃO 2: cache recebe SÓ o planilha_id.
# As credenciais são lidas dentro da função, fora do hash do cache.
# ------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner="Lendo as planilhas das lojas...")
def carregar(ids_planilhas: dict):
    conta = segredo("gcp_service_account")
    if not conta:
        raise ValueError(
            "Faltam as configurações de acesso (secrets). "
            "Configure gcp_service_account no ambiente do Streamlit."
        )
    blocos, avisos, unidades_lidas, orcamentos = dados.ler_planilhas(dict(conta), ids_planilhas)
    vendas, metas = dados.preparar(blocos, orcamentos)
    return vendas, metas, avisos, unidades_lidas, dt.datetime.now(FUSO)


# ------------------------------------------------------------
# CORREÇÃO 6: chart_layout aceita overrides.
# Evita chamar update_layout() de novo depois.
# ------------------------------------------------------------
def fonte(cor="#FFFFFF", tamanho=13):
    """Fonte em NEGRITO para os gráficos.

    Usa weight="bold" (plotly >= 5.24). Se a versão instalada for mais antiga,
    cai para a fonte Arial Black, que também é pesada.
    """
    try:
        f = go.layout.Font(color=cor, size=tamanho, weight="bold").to_plotly_json()
        f.setdefault("family", "Arial")
    except Exception:
        f = dict(color=cor, size=tamanho, family="Arial Black, Arial, sans-serif")
    return f


TEXTO_GRAFICO = "#FFFFFF"   # contraste máximo sobre o fundo escuro dos cards
TEXTO_EIXO = "#DCE7F0"      # números e nomes dos eixos (bem mais claro que o MUTED anterior)


def legenda(**extra):
    """Legenda em negrito, branca, sobre um painel escuro para destacar das barras."""
    d = dict(
        bgcolor="rgba(7,26,41,.90)",
        bordercolor=BORDER,
        borderwidth=1,
        font=fonte(TEXTO_GRAFICO, 13),
    )
    d.update(extra)
    return d


def chart_layout(fig, height=300, **overrides):
    """Aplica o layout padrão do dashboard e sobrescreve com 'overrides'.

    Ex.: chart_layout(fig, 310, title=dict(text="X", font=dict(size=14)))
    Todos os textos do gráfico (título, legenda, eixos e rótulos) saem em negrito
    e com alto contraste.
    """
    base = dict(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=fonte(TEXTO_GRAFICO, 13),
        margin=dict(l=20, r=18, t=45, b=35),
        legend=legenda(),
        xaxis=eixo_x(),
        yaxis=eixo_y(),
    )
    base.update(overrides)
    fig.update_layout(**base)
    fig.update_layout(title_font=fonte(TEXTO_GRAFICO, 15))
    # rótulos de dados: brancos e em negrito, fora das barras/fatias (nunca sobre a cor da barra)
    fig.update_traces(textfont=fonte(TEXTO_GRAFICO, 13), selector=dict(type="pie"))
    fig.update_traces(
        textfont=fonte(TEXTO_GRAFICO, 13),
        textposition="outside",
        cliponaxis=False,
        selector=lambda t: t.type == "bar" and t.text is not None,
    )
    return fig


def _eixo(**extra):
    d = dict(
        color=TEXTO_EIXO,
        tickfont=fonte(TEXTO_EIXO, 12),
        gridcolor="rgba(120,170,200,.28)",
        zerolinecolor="rgba(120,170,200,.35)",
    )
    d.update(extra)
    return d


def eixo_x(**extra):
    """Dict de eixo X padrão + extras (ex.: tickprefix='R$ ')."""
    return _eixo(**extra)


def eixo_y(**extra):
    """Dict de eixo Y padrão + extras (ex.: tickprefix='R$ ')."""
    return _eixo(**extra)


def kpi_html(label, value, delta="", money=False, positive=None):
    if positive is True:
        cls = "positive"
        arrow = "↑ "
    elif positive is False:
        cls = "negative"
        arrow = "↓ "
    else:
        cls = "neutral"
        arrow = ""
    money_cls = "kpi-money" if money else ""
    delta_html = f'<div class="kpi-delta {cls}">{arrow}{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {money_cls}">{value}</div>
        {delta_html}
    </div>
    """


# ============================================================
# INÍCIO
# ============================================================
checar_senha()

try:
    # IDs separados por unidade. Para facilitar a migração, o antigo
    # planilha_id é aceito como Uberlândia enquanto os secrets são atualizados.
    config_planilhas = segredo("planilhas", {})
    ids_planilhas = {
        unidade["chave"]: str(config_planilhas.get(unidade["chave"], "") or "").strip()
        for unidade in dados.UNIDADES
    }
    if not any(ids_planilhas.values()):
        legado = segredo("planilha_id", "")
        if legado:
            ids_planilhas["uberlandia"] = str(legado).strip()
    if not any(ids_planilhas.values()):
        raise ValueError(
            "Nenhuma planilha foi configurada. Preencha ao menos "
            "[planilhas].uberlandia no secrets.toml."
        )
    vendas, metas, avisos_leitura, unidades_lidas, lido_em = carregar(ids_planilhas)

    # Compatibilidade com diferentes nomes de coluna vindos da planilha.
    # O restante do dashboard utiliza o nome interno "VEND".
    if "VEND" not in vendas.columns:
        aliases_vendedor = {
            "VENDEDOR", "VENDEDORES", "NOME VENDEDOR", "NOME DO VENDEDOR",
            "VENDEDOR(A)", "CONSULTOR", "CONSULTOR DE VENDAS",
            "CONSULTOR(A)", "RESPONSAVEL", "RESPONSÁVEL",
        }
        normalizar = lambda valor: re.sub(r"\s+", " ", str(valor).strip()).upper()
        coluna_vendedor = next(
            (col for col in vendas.columns if normalizar(col) in aliases_vendedor),
            None,
        )
        if coluna_vendedor is not None:
            vendas = vendas.rename(columns={coluna_vendedor: "VEND"})
        else:
            st.warning(
                "A coluna de vendedor não foi identificada na base. "
                f"Colunas disponíveis: {', '.join(map(str, vendas.columns))}"
            )
            vendas["VEND"] = ""

except Exception as erro:
    st.error("Não consegui ler a planilha.")
    st.write(f"Detalhe técnico: `{erro}`")
    st.info(
        "Confira o manual, seção **Problemas comuns**. Se for a primeira vez, "
        "veja se a planilha foi compartilhada com o e-mail da conta de serviço."
    )
    st.stop()

for aviso in avisos_leitura:
    st.warning(aviso)

if vendas.empty:
    st.warning("Não encontrei lançamentos nas abas mensais das planilhas configuradas.")
    st.stop()

hoje = dt.datetime.now(FUSO).date()

# ============================================================
# HEADER
# ============================================================
st.markdown(
    f"""
    <div class="gwm-header">
        <div class="gwm-brand">
            <div class="gwm-logo">📊</div>
            <div class="gwm-name">CLAYTON GWM <span>— Dashboard</span></div>
        </div>
        <div class="gwm-title">DASHBOARD DE LUCRATIVIDADE DE VENDAS</div>
        <div class="gwm-update">
            Atualizado em:<br>
            <strong>{lido_em:%d/%m/%Y %H:%M}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# NAVEGAÇÃO PRINCIPAL
# ============================================================
aba_dashboard, aba_ranking, aba_parametros = st.tabs(
    ["📊  DASHBOARD", "🏆  RANKING", "⚙️  PARÂMETROS"]
)

# ============================================================
# FILTROS — compartilhados visualmente
# ============================================================
st.markdown('<div class="section-title">Filtros</div>', unsafe_allow_html=True)

f1, f2, f3, f4, f5, f6 = st.columns([1.05, 1.05, 1.0, 1.0, 1.15, 1.15])

datas_disponiveis = pd.concat([vendas["DATA FAT"], vendas["DATA PEDIDO"]]).dropna()
if datas_disponiveis.empty:
    st.warning("Há registros, mas nenhuma data válida foi encontrada nas colunas DATA PEDIDO e DATA FAT.")
    st.stop()

with f1:
    anos_disponiveis = sorted(datas_disponiveis.dt.year.unique(), reverse=True)
    ano_sel = st.selectbox("Ano", anos_disponiveis)

with f2:
    nomes_meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    # datas_disponiveis é uma Series, portanto o filtro é feito diretamente nela.
    # Considera também datas de pedido quando não há data de faturamento.
    datas_ano = datas_disponiveis[datas_disponiveis.dt.year == ano_sel]
    meses_disponiveis = sorted(datas_ano.dt.month.unique())
    opcoes_meses = [nomes_meses[m] for m in meses_disponiveis]
    mes_padrao = hoje.month if hoje.month in meses_disponiveis else meses_disponiveis[-1]
    if "filtro_meses" not in st.session_state:
        st.session_state["filtro_meses"] = [nomes_meses[mes_padrao]]
    st.session_state["filtro_meses"] = [
        m for m in st.session_state["filtro_meses"] if m in opcoes_meses
    ]
    meses_nome_sel = st.multiselect(
        "Mês",
        options=opcoes_meses,
        key="filtro_meses",
        placeholder="Selecione meses",
    )
    meses_sel = [m for m in meses_disponiveis if nomes_meses[m] in meses_nome_sel]


def ao_alterar_lojas():
    # Limpa vendedores selecionados anteriormente ao mudar o conjunto de lojas.
    st.session_state["filtro_vendedores"] = []


with f3:
    opcoes_lojas = ["Todas as lojas", *sorted(vendas["LOJA"].dropna().unique().tolist())]
    if "filtro_lojas_ui" not in st.session_state:
        st.session_state["filtro_lojas_ui"] = ["Todas as lojas"]

    lojas_ui = st.multiselect(
        "Lojas",
        options=opcoes_lojas,
        key="filtro_lojas_ui",
        on_change=ao_alterar_lojas,
        placeholder="Selecione lojas",
    )

    # A opção especial representa todas as lojas e não é passada aos cálculos.
    if "Todas as lojas" in lojas_ui:
        lojas_sel = sorted(vendas["LOJA"].dropna().unique().tolist())
    else:
        lojas_sel = lojas_ui

with f4:
    if lojas_sel:
        vendedores_lojas = vendas.loc[
            vendas["LOJA"].isin(lojas_sel), "VEND"
        ].dropna()
        vend_opcoes = sorted(
            str(v).strip() for v in vendedores_lojas.unique() if str(v).strip()
        )
        vend_sel = st.multiselect(
            "Vendedores",
            options=vend_opcoes,
            key="filtro_vendedores",
            placeholder="Todos os vendedores",
        )
    else:
        st.markdown(
            '<div style="color:#8FA6B8;font-size:14px;margin-bottom:8px;">'
            'Vendedores</div>',
            unsafe_allow_html=True,
        )
        st.caption("Selecione uma loja para visualizar os vendedores.")
        vend_sel = []

with f5:
    periodo_tipo = st.selectbox("Período", ["Mês selecionado", "Personalizado"])

# ------------------------------------------------------------
# CORREÇÃO 3: período personalizado com session_state.
# Sem st.stop() no meio — usa o último período válido enquanto
# o usuário escolhe a 2ª data.
# ------------------------------------------------------------
with f6:
    if periodo_tipo == "Mês selecionado":
        if not meses_sel:
            ini = dt.date(ano_sel, 1, 1)
            fim = dt.date(ano_sel, 12, 31)
            periodo_label = "Nenhum mês selecionado"
        else:
            ini = dt.date(ano_sel, min(meses_sel), 1)
            ultimo_mes = max(meses_sel)
            fim = (pd.Timestamp(dt.date(ano_sel, ultimo_mes, 1)) + pd.offsets.MonthEnd(1)).date()
            periodo_label = ", ".join(nomes_meses[m] for m in meses_sel)
        st.text_input("Período ativo", periodo_label, disabled=True)
    else:
        periodo = st.date_input(
            "Período",
            value=st.session_state.get(
                "periodo_custom", (hoje.replace(day=1), hoje)
            ),
            format="DD/MM/YYYY",
        )
        # Só aceita quando o usuário confirmou as DUAS datas.
        if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
            st.session_state["periodo_custom"] = periodo
            ini, fim = periodo
            periodo_label = f"{ini:%d/%m/%Y} → {fim:%d/%m/%Y}"
        else:
            # Ainda escolhendo: usa o último período válido guardado.
            ini, fim = st.session_state.get(
                "periodo_custom", (hoje.replace(day=1), hoje)
            )
            periodo_label = (
                f"{ini:%d/%m/%Y} → {fim:%d/%m/%Y} "
                "(aguardando confirmação da 2ª data)"
            )

col_refresh, col_info = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_info:
    st.caption(
        f"Período: {periodo_label} · "
        f"Lojas: {', '.join(lojas_sel) if lojas_sel else 'nenhuma'} · "
        f"Dados atualizados automaticamente a cada 5 minutos"
    )

if not lojas_sel:
    st.warning("Marque pelo menos uma loja.")
    st.stop()

# ------------------------------------------------------------
# BASE PARA OS CÁLCULOS
# Filtra APENAS por loja e vendedor.
# A regra de data é aplicada dentro de dados.indicadores(),
# porque cada indicador usa a data correta (DATA PEDIDO ou DATA FAT).
# ------------------------------------------------------------
base_loja_vendedor = vendas[vendas["LOJA"].isin(lojas_sel)]
if vend_sel:
    base_loja_vendedor = base_loja_vendedor[
        base_loja_vendedor["VEND"].isin(vend_sel)
    ]

r = dados.indicadores(base_loja_vendedor, ini, fim)
st.write("DEBUG USADOS:", len(r["fat_usado"]))
st.dataframe(
    r["fat_usado"][
        ["DATA PEDIDO", "DATA FAT", "TIPO", "STATUS", "CAPTAÇÃO", "MODELO"]
    ]
)
meta = dados.meta_periodo(metas, lojas_sel, ini, fim)

# ------------------------------------------------------------
# CORREÇÃO 1: meta é sempre da LOJA/MÊS — nunca invalidada por
# filtro de vendedor. Só fica indisponível se a planilha de Metas
# estiver vazia.
# ------------------------------------------------------------
meta_disponivel = meta > 0
meta_label = "META DA LOJA" if vend_sel else "META DE FATURAMENTO"
meta_delta = "loja no período" if vend_sel else "% da meta disponível"

ticket = r["valor"] / r["qtd"] if r["qtd"] else 0
margem = r["lb"] / r["valor"] if r["valor"] else 0

# ============================================================
# DASHBOARD
# ============================================================
with aba_dashboard:
    st.markdown('<div class="section-title">Visão geral</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.markdown(
            kpi_html(
                "VEÍCULOS 0 KM VENDIDOS",
                f"{r['qtd_0km']:,}".replace(",", "."),
                "período atual",
            ),
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(kpi_html("FATURAMENTO", moeda(r["valor"]), "vendas faturadas", True), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_html("LUCRO TOTAL", moeda(r["lb"]), "lucro bruto", True), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_html("MARGEM MÉDIA", pct(margem), "lucro / faturamento"), unsafe_allow_html=True)
    with k5:
        st.markdown(kpi_html("TICKET MÉDIO", moeda(ticket), "por veículo", True), unsafe_allow_html=True)
    with k6:
        st.markdown(
            kpi_html(
                meta_label,
                moeda(meta) if meta_disponivel else "—",
                meta_delta,
                True,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ---- Indicadores comerciais relacionados aos pedidos do período ----
    ex = dados.indicadores_extras(base_loja_vendedor, ini, fim)
    e1, e2, e3, e4, e5 = st.columns(5)
    with e1:
        st.markdown(
            kpi_html("PEDIDOS DO PERÍODO", f"{ex['pedidos']}", "todos os pedidos"),
            unsafe_allow_html=True,
        )
    with e2:
        st.markdown(
            kpi_html(
                "USADOS VENDIDOS",
                f"{r['qtd_usado']:,}".replace(",", "."),
                "vendas faturadas",
            ),
            unsafe_allow_html=True,
        )
    with e3:
        st.markdown(
            kpi_html(
                "TEST DRIVE",
                f"{ex['td_n']}",
                f"{pct(ex['td_pct'])} dos pedidos",
                True,
            ),
            unsafe_allow_html=True,
        )
    with e4:
        st.markdown(
            kpi_html(
                "EMPLACADOS",
                f"{ex['emp_n']}",
                f"{pct(ex['emp_pct'])} dos pedidos",
                True,
            ),
            unsafe_allow_html=True,
        )
    with e5:
        st.markdown(
            kpi_html(
                "USADO NA TROCA",
                f"{ex['cap_n']}",
                f"{pct(ex['cap_pct'])} dos pedidos",
                True,
            ),
            unsafe_allow_html=True,
        )
    if ex["pedidos"] and not (ex["td_n"] or ex["cap_n"] or ex["emp_n"]):
        st.caption(
            "Ainda não há registros de TEST DRIVE, CAPTAÇÃO ou TIPO = Emplacado nos pedidos deste período. "
            "Preencha essas colunas na planilha."
        )

    st.markdown("")

    c1, c2, c3 = st.columns([1.05, 1.0, 1.05])

    fat = r["fat"]

    # Gráfico 1 — distribuição por loja
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if fat.empty:
            st.info("Sem vendas faturadas no período.")
        else:
            loja_g = fat.groupby("LOJA")["VENDA"].sum().reset_index()
            fig = px.pie(
                loja_g,
                names="LOJA",
                values="VENDA",
                hole=.58,
                title="Faturamento por Loja (R$)",
            )
            fig.update_traces(
                textposition="outside",
                textinfo="label+percent",
                marker=dict(line=dict(color=BG, width=2)),
            )
            chart_layout(
                fig,
                310,
                title=dict(font=dict(size=14, color=TEXT)),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Gráfico 2 — faturamento por período
    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if fat.empty:
            st.info("Sem vendas faturadas no período.")
        else:
            if (fim - ini).days <= 62:
                serie = fat.groupby(fat["DATA FAT"].dt.date)["VENDA"].sum().reset_index()
                serie.columns = ["Data", "Faturamento"]
                x_col = "Data"
            else:
                serie = (
                    fat.groupby(fat["DATA FAT"].dt.to_period("M").dt.to_timestamp())["VENDA"]
                    .sum()
                    .reset_index()
                )
                serie.columns = ["Data", "Faturamento"]
                x_col = "Data"

            fig = px.bar(serie, x=x_col, y="Faturamento", title="Faturamento no Período")
            fig.update_traces(marker_color=CYAN)
            chart_layout(
                fig,
                310,
                title=dict(font=dict(size=14, color=TEXT)),
                yaxis=eixo_y(tickprefix="R$ "),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        # Legenda do período selecionado, logo abaixo do gráfico
        st.markdown(
            f'<div style="text-align:center; color:#8FA8B8; '
            f'font-size:12px; margin-top:-8px; padding-bottom:6px;">'
            f'Período: {periodo_label}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Gráfico 3 — vendedores
    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if fat.empty:
            st.info("Sem vendas faturadas no período.")
        else:
            rank = (
                fat.groupby("VEND")
                .agg(Qtd=("VENDA", "size"), Faturamento=("VENDA", "sum"))
                .reset_index()
                .sort_values("Faturamento", ascending=False)
            )
            rank["VEND"] = rank["VEND"].replace("", "(sem vendedor)")
            top = rank.head(8).sort_values("Faturamento")
            fig = px.bar(
                top,
                x="Faturamento",
                y="VEND",
                orientation="h",
                title="Faturamento por Vendedor (R$)",
            )
            fig.update_traces(marker_color=CYAN_2)
            chart_layout(
                fig,
                310,
                title=dict(font=dict(size=14, color=TEXT)),
                xaxis=eixo_x(tickprefix="R$ "),
                yaxis=eixo_y(title=None),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    # Segunda linha de gráficos
    c4, c5 = st.columns([1.0, 1.0])

    with c4:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if fat.empty:
            st.info("Sem vendas faturadas no período.")
        else:
            mod = (
                fat.groupby("FAMILIA")
                .agg(Qtd=("VENDA", "size"), Faturamento=("VENDA", "sum"))
                .reset_index()
                .sort_values("Qtd", ascending=False)
            )
            mod["FAMILIA"] = mod["FAMILIA"].replace("", "(sem modelo)")
            top_mod = mod.head(8).sort_values("Qtd")
            fig = px.bar(
                top_mod,
                x="Qtd",
                y="FAMILIA",
                orientation="h",
                title="Veículos Faturados por Família",
                text="Qtd",
            )
            fig.update_traces(marker_color=BLUE)
            chart_layout(
                fig,
                300,
                title=dict(font=dict(size=14, color=TEXT)),
                xaxis=eixo_x(title=None),
                yaxis=eixo_y(title=None),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        ped = base_loja_vendedor[
            base_loja_vendedor["DATA PEDIDO"].between(pd.Timestamp(ini), pd.Timestamp(fim))
        ]
        if ped.empty:
            st.info("Sem pedidos no período.")
        else:
            por_status = ped.groupby("STATUS").size().reset_index(name="Pedidos")
            fig = px.bar(
                por_status,
                x="STATUS",
                y="Pedidos",
                title="Pedidos do Período por Status",
                text="Pedidos",
            )
            fig.update_traces(marker_color=CYAN)
            chart_layout(
                fig,
                300,
                title=dict(font=dict(size=14, color=TEXT)),
                xaxis=eixo_x(title=None),
                yaxis=eixo_y(title=None),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">Test drive, emplacamento e troca por vendedor</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    por_vend = dados.extras_por_vendedor(ex["ped"])
    if por_vend.empty:
        st.info("Sem pedidos no período.")
    else:
        por_vend = por_vend.sort_values("Pedidos", ascending=False).head(10)
        fig = go.Figure()
        for nome_serie, cor_serie in [("Test drive", CYAN), ("Emplacados", YELLOW), ("Usado na troca", GREEN)]:
            fig.add_bar(x=por_vend["VEND"], y=por_vend[nome_serie], name=nome_serie, marker_color=cor_serie)
        chart_layout(
            fig,
            320,
            title=dict(text="Pedidos do período por vendedor", font=dict(size=14, color=TEXT)),
            barmode="group",
            legend=legenda(orientation="h", x=1, xanchor="right", y=1.14, yanchor="bottom"),
            margin=dict(l=20, r=18, t=70, b=35),
            xaxis=eixo_x(title=None),
            yaxis=eixo_y(title=None),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">Detalhamento das vendas</div>', unsafe_allow_html=True)

    opcoes = {
        "Faturados": "fat",
        "Aguardando (sem status)": "aguard",
        "Cancelados": "canc",
        "Devoluções": "dev",
    }
    escolha = st.radio("Visualização", list(opcoes), horizontal=True, label_visibility="collapsed")
    lista = r[opcoes[escolha]]

    cols = [
        "LOJA", "DATA PEDIDO", "DATA FAT", "STATUS", "CHASSI",
        "FAMILIA", "COR", "NOME CLIENTE", "VEND", "VENDA",
        "CUSTO", "INCID", "LB", "TIPO", "TEST DRIVE", "CAPTAÇÃO",
    ]
    tabela = lista[cols].copy()
    for col in ["DATA PEDIDO", "DATA FAT"]:
        tabela[col] = tabela[col].dt.strftime("%d/%m/%Y").fillna("")

    st.dataframe(tabela, hide_index=True, use_container_width=True, height=270)

    dl_col, _ = st.columns([1, 5])
    with dl_col:
        st.download_button(
            "⬇ Exportar CSV",
            tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name="controle_gwm.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ============================================================
# RANKING
# ============================================================
with aba_ranking:
    st.markdown('<div class="section-title">Performance comercial</div>', unsafe_allow_html=True)

    fat = r["fat"]

    if fat.empty:
        st.info("Sem vendas faturadas no período.")
    else:
        rank = (
            fat.groupby("VEND")
            .agg(
                Vendas=("VENDA", "size"),
                Faturamento=("VENDA", "sum"),
                Lucro=("LB", "sum"),
            )
            .reset_index()
            .sort_values("Faturamento", ascending=False)
        )
        rank["VEND"] = rank["VEND"].replace("", "(sem vendedor)")
        rank["% Meta"] = (rank["Faturamento"] / meta) if meta_disponivel else 0
        extras_rank = dados.extras_por_vendedor(
            dados.indicadores_extras(base_loja_vendedor, ini, fim)["ped"]
        )[["VEND", "Test drive", "Emplacados", "Usado na troca"]]
        rank = rank.merge(extras_rank, on="VEND", how="left")
        for col_extra in ["Test drive", "Emplacados", "Usado na troca"]:
            rank[col_extra] = rank[col_extra].fillna(0).astype(int)

        rk1, rk2, rk3, rk4, rk5 = st.columns(5)
        rk1.markdown(
            kpi_html(
                "META TOTAL",
                moeda(meta) if meta_disponivel else "—",
                "período",
                True,
            ),
            unsafe_allow_html=True,
        )
        rk2.markdown(kpi_html("FATURAMENTO", moeda(rank["Faturamento"].sum()), "realizado", True), unsafe_allow_html=True)
        rk3.markdown(kpi_html("VEÍCULOS", f"{int(rank['Vendas'].sum())}", "faturados"), unsafe_allow_html=True)
        rk4.markdown(
            kpi_html(
                "% DA META",
                pct(rank["Faturamento"].sum() / meta) if meta_disponivel else "—",
                "realizado",
            ),
            unsafe_allow_html=True,
        )
        falta = max(meta - rank["Faturamento"].sum(), 0) if meta_disponivel else 0
        rk5.markdown(
            kpi_html(
                "FALTA PARA META",
                moeda(falta) if meta_disponivel else "—",
                "saldo",
                True,
            ),
            unsafe_allow_html=True,
        )

        st.markdown("")

        rc1, rc2 = st.columns([1.05, 1.0])

        with rc1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            mostra = rank.copy()
            mostra.insert(0, "#", range(1, len(mostra) + 1))
            mostra["Faturamento"] = mostra["Faturamento"].map(moeda)
            mostra["Lucro"] = mostra["Lucro"].map(moeda)
            mostra["% Meta"] = (rank["% Meta"] * 100).map(lambda x: f"{x:.1f}%".replace(".", ","))
            mostra = mostra.rename(columns={"VEND": "Vendedor"})
            st.dataframe(
                mostra[["#", "Vendedor", "Vendas", "Faturamento", "Lucro", "% Meta", "Test drive", "Emplacados", "Usado na troca"]],
                hide_index=True,
                use_container_width=True,
                height=430,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with rc2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            top = rank.head(10).sort_values("Faturamento")
            fig = go.Figure()
            fig.add_bar(
                y=top["VEND"],
                x=top["Faturamento"],
                orientation="h",
                name="Realizado",
                marker_color=CYAN,
            )
            if meta_disponivel:
                fig.add_vline(x=meta, line_dash="dash", line_color=YELLOW)
            chart_layout(
                fig,
                430,
                title=dict(text="Ranking de Faturamento", font=dict(size=14, color=TEXT)),
                xaxis=eixo_x(tickprefix="R$ "),
                yaxis=eixo_y(title=None),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PARÂMETROS
# ============================================================
with aba_parametros:
    st.markdown('<div class="section-title">Configurações e referências do painel</div>', unsafe_allow_html=True)

    p1, p2, p3, p4 = st.tabs(
        ["🚗 Famílias e Modelos", "🎨 Cores", "👤 Vendedores", "🎯 Metas"]
    )

    with p1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Famílias de veículos")
            familias = sorted(v for v in vendas["FAMILIA"].dropna().unique() if v)
            fam_df = pd.DataFrame({
                "Código": [f"F{i:02d}" for i in range(1, len(familias) + 1)],
                "Família": familias,
                "Status": ["Ativa"] * len(familias),
            })
            st.dataframe(fam_df, hide_index=True, use_container_width=True, height=360)

        with col_b:
            st.markdown("#### Modelos / famílias")
            modelo_df = pd.DataFrame({
                "Modelo": familias,
                "Família": familias,
            })
            st.dataframe(modelo_df, hide_index=True, use_container_width=True, height=360)

    with p2:
        st.markdown("#### Cores cadastradas")
        if "COR" in vendas.columns:
            cores = sorted(v for v in vendas["COR"].dropna().unique() if v)
        else:
            cores = []
        cor_df = pd.DataFrame({
            "Código": [f"C{i:02d}" for i in range(1, len(cores) + 1)],
            "Cor": cores,
        })
        st.dataframe(cor_df, hide_index=True, use_container_width=True, height=400)

    with p3:
        st.markdown("#### Vendedores")
        vendedores = sorted(v for v in vendas["VEND"].dropna().unique() if v)
        vend_df = pd.DataFrame({
            "Código": [f"V{i:02d}" for i in range(1, len(vendedores) + 1)],
            "Vendedor": vendedores,
            "Status": ["Ativo"] * len(vendedores),
        })
        st.dataframe(vend_df, hide_index=True, use_container_width=True, height=400)

    with p4:
        st.markdown("#### Metas por período / loja")
        if isinstance(metas, pd.DataFrame) and not metas.empty:
            metas_vis = metas[metas["LOJA"].isin(lojas_sel)].copy()
            metas_vis = metas_vis[
                metas_vis["MES"].dt.year == ano_sel
            ].sort_values(["MES", "LOJA"])
            metas_vis["Mês"] = metas_vis["MES"].dt.strftime("%m/%Y")
            metas_vis["Qtd"] = metas_vis["META_QTD"].round().astype(int)
            metas_vis["Faturamento"] = metas_vis["META_FAT"].map(moeda)
            metas_vis["Lucro bruto"] = metas_vis["META_LB"].map(moeda)
            st.caption("Metas lidas da aba Orçamento de cada loja. Faturamento = quantidade × valor unitário.")
            st.dataframe(
                metas_vis.rename(columns={"LOJA": "Loja"})[["Mês", "Loja", "Qtd", "Faturamento", "Lucro bruto"]],
                hide_index=True, use_container_width=True, height=400,
            )
        else:
            st.info("Nenhuma meta disponível na fonte atual.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("""
<style>
/* Contêiner das etiquetas do multiselect */
div[data-testid="stMultiSelectTagsContainer"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    scrollbar-width: thin !important;
}

/* Evita que as etiquetas sejam comprimidas */
div[data-testid="stMultiSelectTagsContainer"] > span {
    flex-shrink: 0 !important;
}

/* Barra de rolagem */
div[data-testid="stMultiSelectTagsContainer"]::-webkit-scrollbar {
    height: 6px !important;
}

div[data-testid="stMultiSelectTagsContainer"]::-webkit-scrollbar-thumb {
    background: #9CAAB5 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)
