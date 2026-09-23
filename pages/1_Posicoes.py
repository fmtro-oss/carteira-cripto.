import streamlit as st
from lib import db, precos as precos_mod, calculos

st.set_page_config(page_title="Posições — Carteira Cripto", page_icon="💼", layout="wide")
st.title("💼 Posições por ativo e exchange")

lanc = db.carregar_lancamentos()
cfg = db.carregar_config()
cotacoes = precos_mod.buscar_precos_consolidados()
posicoes = calculos.calcular_posicoes(lanc, cotacoes, cfg)

if posicoes.empty:
    st.info("Nenhuma posição ainda.")
    st.stop()

col1, col2, col3 = st.columns(3)
exchanges = ["Todas"] + sorted(posicoes["exchange"].unique().tolist())
filtro_exchange = col1.selectbox("Exchange", exchanges)
filtro_status = col2.selectbox("Status", ["Todos", "Recompra", "Realizar Parcial", "Dentro do Alvo", "Zerada"])
ocultar_zeradas = col3.checkbox("Ocultar posições zeradas", value=True)

df = posicoes.copy()
if filtro_exchange != "Todas":
    df = df[df["exchange"] == filtro_exchange]
if filtro_status != "Todos":
    df = df[df["status"] == filtro_status]
if ocultar_zeradas:
    df = df[df["status"] != "Zerada"]

df_show = df.rename(columns={
    "ativo": "Ativo", "exchange": "Exchange", "qtd_atual": "Qtd Atual",
    "custo_medio": "Custo Médio (USD)", "custo_posicao": "Custo Posição (USD)",
    "preco_atual": "Preço Atual (USD)", "valor_atual": "Valor Atual (USD)",
    "pl_aberto": "P/L Aberto (USD)", "pl_aberto_pct": "P/L Aberto %",
    "pl_realizado": "P/L Realizado (USD)", "pct_carteira": "% Carteira",
    "alvo_recompra": "Alvo Recompra", "alvo_realizacao": "Alvo Realização",
    "status": "Status",
})
df_show["P/L Aberto %"] = df_show["P/L Aberto %"] * 100
df_show["% Carteira"] = df_show["% Carteira"] * 100

def cor_status(val):
    cores = {"Recompra": "background-color: #14532d; color: #bbf7d0",
             "Realizar Parcial": "background-color: #713f12; color: #fde68a",
             "Zerada": "opacity: 0.5"}
    return cores.get(val, "")

colunas = ["Ativo", "Exchange", "Qtd Atual", "Custo Médio (USD)", "Custo Posição (USD)",
           "Preço Atual (USD)", "Valor Atual (USD)", "P/L Aberto (USD)", "P/L Aberto %",
           "P/L Realizado (USD)", "% Carteira", "Alvo Recompra", "Alvo Realização", "Status"]

st.dataframe(
    df_show[colunas].style.map(cor_status, subset=["Status"]),
    width="stretch", hide_index=True, height=600,
    column_config={
        "Qtd Atual": st.column_config.NumberColumn(format="%.6f"),
        "Custo Médio (USD)": st.column_config.NumberColumn(format="$ %.4f"),
        "Custo Posição (USD)": st.column_config.NumberColumn(format="$ %.2f"),
        "Preço Atual (USD)": st.column_config.NumberColumn(format="$ %.4f"),
        "Valor Atual (USD)": st.column_config.NumberColumn(format="$ %.2f"),
        "P/L Aberto (USD)": st.column_config.NumberColumn(format="$ %.2f"),
        "P/L Aberto %": st.column_config.NumberColumn(format="%.1f%%"),
        "P/L Realizado (USD)": st.column_config.NumberColumn(format="$ %.2f"),
        "% Carteira": st.column_config.NumberColumn(format="%.1f%%"),
        "Alvo Recompra": st.column_config.NumberColumn(format="$ %.4f"),
        "Alvo Realização": st.column_config.NumberColumn(format="$ %.4f"),
    },
)

st.caption(f"{len(df_show)} posições exibidas de {len(posicoes)} no total.")
