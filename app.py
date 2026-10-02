"""Controle GWM — Dashboard (somente leitura). Rodar: streamlit run app.py"""
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import dados

st.set_page_config(page_title="Controle GWM", page_icon="📊", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")
AZUL, CINZA = "#1C5075", "#9AA5AD"

COMO_USAR = """
### Como usar este painel

**1. Escolha o período** na barra da esquerda. Ele vale para a *data de faturamento*
(coluna **DATA FAT**). Por padrão mostra do dia 1º do mês até hoje.

**2. Filtre por loja ou vendedor** (opcional). Deixe vazio para ver todos.

**3. Veja as abas:** Resumo (números gerais), Lojas (faturamento × meta),
Vendedores (ranking), Modelos (o que mais vende) e Dados (lista de veículos, com download).

**4. Os números não atualizam?** Clique em **🔄 Atualizar dados agora**.
O painel também busca dados novos sozinho a cada 5 minutos.

---

### Para os números ficarem certos, a planilha precisa estar preenchida assim

| Regra | Por quê |
|---|---|
| **STATUS** escrito como na lista (Aguardando faturamento, Faturado, Cancelado, Devolução) | O painel conta cada status separadamente |
| **DATA FAT** preenchida quando o status for *Faturado* ou *Devolução* | Sem a data, a venda não entra em nenhum período |
| **DATA PEDIDO** preenchida em todo pedido | Usada para contar cancelamentos e pedidos do período |
| **VENDA, CUSTO e INCID** só com números | O lucro bruto é calculado por eles: VENDA − CUSTO − INCID |
| **VEND** escolhido na lista | Nome diferente vira outro vendedor no ranking |
| **Metas**: aba *Metas*, mês sempre no 1º dia (ex.: 01/10/2026) e loja com o mesmo nome da aba | Senão a meta não é encontrada |

### Como cada número é calculado
- **Faturamento / Quantidade:** pedidos *Faturado* com DATA FAT dentro do período.
- **Lucro bruto:** lucro dos faturados menos o das devoluções do período.
- **Margem:** lucro bruto ÷ faturamento.
- **Meta:** soma das metas dos meses que o período toca (período de 01/10 a 15/10 usa a meta de outubro inteira).
- **Aguardando faturamento:** todos os pedidos nesse status hoje, sem filtro de data.
- **Cancelados:** status *Cancelado* com DATA PEDIDO dentro do período.

> Este painel **só lê** a planilha. Nada que você fizer aqui altera os dados.
"""


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
    st.title("📊 Controle GWM")
    digitada = st.text_input("Digite a senha de acesso", type="password")
    if digitada:
        if digitada == senha:
            st.session_state["liberado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()


@st.cache_data(ttl=300, show_spinner="Lendo a planilha...")
def carregar():
    conta, pid = segredo("gcp_service_account"), segredo("planilha_id")
    if not conta or not pid:
        raise ValueError("Faltam as configurações de acesso (secrets). Veja o passo 6 do manual.")
    blocos = dados.ler_planilha(dict(conta), pid)
    vendas, metas = dados.preparar(blocos)
    return vendas, metas, dt.datetime.now(FUSO)


# ---------------------------------------------------------------- início
checar_senha()
st.title("📊 Controle GWM — Dashboard")

try:
    vendas, metas, lido_em = carregar()
except Exception as erro:
    st.error("Não consegui ler a planilha.")
    st.write(f"Detalhe técnico: `{erro}`")
    st.info("Confira o manual, seção **Problemas comuns**. Se for a primeira vez, "
            "veja se a planilha foi compartilhada com o e-mail da conta de serviço.")
    st.stop()

if vendas.empty:
    st.warning("Não encontrei lançamentos nas abas Loja 01 a Loja 04.")
    st.stop()

hoje = dt.datetime.now(FUSO).date()
with st.sidebar:
    st.header("Filtros")
    periodo = st.date_input("Período (data de faturamento)", value=(hoje.replace(day=1), hoje),
                            format="DD/MM/YYYY")
    lojas_sel = st.multiselect("Lojas", dados.LOJAS, default=dados.LOJAS)
    vend_opcoes = sorted(v for v in vendas["VEND"].unique() if v)
    vend_sel = st.multiselect("Vendedores (vazio = todos)", vend_opcoes)
    if st.button("🔄 Atualizar dados agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Dados lidos às {lido_em:%H:%M} · atualiza sozinho a cada 5 min")

if not isinstance(periodo, (tuple, list)) or len(periodo) != 2:
    st.info("Escolha a data inicial **e** a data final no calendário da esquerda.")
    st.stop()
if not lojas_sel:
    st.warning("Marque pelo menos uma loja.")
    st.stop()

ini, fim = periodo
base = vendas[vendas["LOJA"].isin(lojas_sel)]
if vend_sel:
    base = base[base["VEND"].isin(vend_sel)]

r = dados.indicadores(base, ini, fim)
meta = dados.meta_periodo(metas, lojas_sel, ini, fim)
meta_valida = not vend_sel  # meta é por loja, não por vendedor
ticket = r["valor"] / r["qtd"] if r["qtd"] else 0
margem = r["lb"] / r["valor"] if r["valor"] else 0
st.caption(f"Período: {ini:%d/%m/%Y} a {fim:%d/%m/%Y} · Lojas: {', '.join(lojas_sel)}"
           + (f" · Vendedores: {', '.join(vend_sel)}" if vend_sel else ""))

aba_resumo, aba_lojas, aba_vend, aba_modelos, aba_dados, aba_ajuda = st.tabs(
    ["📊 Resumo", "🏪 Lojas", "👤 Vendedores", "🚗 Modelos", "📋 Dados", "❓ Como usar"])

# ---------------------------------------------------------------- Resumo
with aba_resumo:
    c = st.columns(4)
    c[0].metric("Faturamento", moeda(r["valor"]))
    c[1].metric("Quantidade faturada", r["qtd"])
    c[2].metric("Ticket médio", moeda(ticket))
    c[3].metric("Lucro bruto", moeda(r["lb"]), help="Lucro dos faturados menos o das devoluções")
    c = st.columns(4)
    c[0].metric("Margem bruta", pct(margem))
    c[1].metric("Meta de faturamento", moeda(meta) if meta_valida else "—")
    c[2].metric("% da meta", pct(r["valor"] / meta) if meta_valida and meta else "—")
    c[3].metric("Aguardando faturamento", r["aguard_n"])
    c = st.columns(4)
    c[0].metric("Cancelados no período", r["canc_n"])
    c[1].metric("Devoluções no período", r["dev_n"])
    if meta_valida and meta:
        st.progress(min(r["valor"] / meta, 1.0), text=f"{pct(r['valor'] / meta)} da meta")
    elif vend_sel:
        st.caption("A meta é por loja, por isso não aparece quando há vendedor filtrado.")

    fat = r["fat"]
    if fat.empty:
        st.info("Nenhum veículo faturado neste período. Confira se DATA FAT e STATUS estão preenchidos.")
    else:
        if (fim - ini).days <= 62:
            serie = fat.groupby(fat["DATA FAT"].dt.date)["VENDA"].sum().reset_index()
            serie.columns = ["Data", "Faturamento"]
            titulo = "Faturamento por dia"
        else:
            serie = fat.groupby(fat["DATA FAT"].dt.to_period("M").dt.to_timestamp())["VENDA"].sum().reset_index()
            serie.columns = ["Data", "Faturamento"]
            titulo = "Faturamento por mês"
        fig = px.bar(serie, x="Data", y="Faturamento", title=titulo, color_discrete_sequence=[AZUL])
        fig.update_layout(yaxis_tickprefix="R$ ", margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    ped = base[base["DATA PEDIDO"].between(pd.Timestamp(ini), pd.Timestamp(fim))]
    if not ped.empty:
        por_status = ped.groupby("STATUS").size().reset_index(name="Pedidos")
        fig = px.bar(por_status, x="STATUS", y="Pedidos", title="Pedidos do período por status",
                     color_discrete_sequence=[AZUL], text="Pedidos")
        fig.update_layout(xaxis_title=None, margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- Lojas
with aba_lojas:
    linhas = []
    for loja in lojas_sel:
        rl = dados.indicadores(base[base["LOJA"] == loja], ini, fim)
        m = dados.meta_periodo(metas, [loja], ini, fim)
        linhas.append({"Loja": loja, "Qtd": rl["qtd"], "Faturamento": rl["valor"], "Lucro bruto": rl["lb"],
                       "Meta": m, "% Meta": rl["valor"] / m if m else 0})
    lojas_df = pd.DataFrame(linhas)
    fig = go.Figure()
    fig.add_bar(x=lojas_df["Loja"], y=lojas_df["Faturamento"], name="Faturamento", marker_color=AZUL)
    if meta_valida:
        fig.add_bar(x=lojas_df["Loja"], y=lojas_df["Meta"], name="Meta", marker_color=CINZA)
    fig.update_layout(barmode="group", title="Faturamento × Meta por loja",
                      yaxis_tickprefix="R$ ", margin=dict(t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)
    mostra = lojas_df.copy()
    for col in ["Faturamento", "Lucro bruto", "Meta"]:
        mostra[col] = mostra[col].map(moeda)
    mostra["% Meta"] = lojas_df["% Meta"].map(pct)
    st.dataframe(mostra, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- Vendedores
with aba_vend:
    fat = r["fat"]
    if fat.empty:
        st.info("Sem vendas faturadas neste período.")
    else:
        rank = (fat.groupby("VEND").agg(Qtd=("VENDA", "size"), Faturamento=("VENDA", "sum"), LB=("LB", "sum"))
                .reset_index().sort_values("Faturamento", ascending=False))
        rank["VEND"] = rank["VEND"].replace("", "(sem vendedor)")
        top = rank.head(15).sort_values("Faturamento")
        fig = px.bar(top, x="Faturamento", y="VEND", orientation="h", title="Ranking de vendedores (top 15)",
                     color_discrete_sequence=[AZUL], text="Qtd")
        fig.update_layout(yaxis_title=None, xaxis_tickprefix="R$ ", margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
        mostra = rank.rename(columns={"VEND": "Vendedor", "LB": "Lucro bruto"})
        mostra["Faturamento"] = mostra["Faturamento"].map(moeda)
        mostra["Lucro bruto"] = mostra["Lucro bruto"].map(moeda)
        st.dataframe(mostra, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- Modelos
with aba_modelos:
    fat = r["fat"]
    if fat.empty:
        st.info("Sem vendas faturadas neste período.")
    else:
        mod = (fat.groupby("FAMILIA").agg(Qtd=("VENDA", "size"), Faturamento=("VENDA", "sum"))
               .reset_index().sort_values("Qtd", ascending=False))
        mod["FAMILIA"] = mod["FAMILIA"].replace("", "(sem modelo)")
        fig = px.bar(mod.sort_values("Qtd"), x="Qtd", y="FAMILIA", orientation="h",
                     title="Veículos faturados por modelo", color_discrete_sequence=[AZUL], text="Qtd")
        fig.update_layout(yaxis_title=None, margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
        mostra = mod.rename(columns={"FAMILIA": "Modelo"})
        mostra["Faturamento"] = mostra["Faturamento"].map(moeda)
        st.dataframe(mostra, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- Dados
with aba_dados:
    opcoes = {"Faturados no período": "fat", "Aguardando faturamento": "aguard",
              "Cancelados no período": "canc", "Devoluções no período": "dev"}
    escolha = st.radio("Mostrar", list(opcoes), horizontal=True)
    lista = r[opcoes[escolha]]
    cols = ["LOJA", "DATA PEDIDO", "DATA FAT", "STATUS", "CHASSI", "FAMILIA", "COR",
            "NOME CLIENTE", "VEND", "VENDA", "CUSTO", "INCID", "LB"]
    tabela = lista[cols].copy()
    for col in ["DATA PEDIDO", "DATA FAT"]:
        tabela[col] = tabela[col].dt.strftime("%d/%m/%Y").fillna("")
    st.write(f"{len(tabela)} veículo(s)")
    st.dataframe(tabela, hide_index=True, use_container_width=True)
    st.download_button("⬇️ Baixar esta lista (Excel/CSV)",
                       tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="controle_gwm.csv", mime="text/csv")

with aba_ajuda:
    st.markdown(COMO_USAR)
