import datetime
import streamlit as st
from lib import db

st.set_page_config(page_title="Lançamentos — Carteira Cripto", page_icon="✍️", layout="wide")
st.title("✍️ Lançamentos")
st.caption("Toda compra, venda, taxa, recompensa ou transferência vira um lançamento aqui. É a única tela onde você digita.")

with st.form("novo_lancamento", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    data = c1.date_input("Data", value=datetime.date.today())
    exchange = c2.selectbox("Exchange", ["Binance", "KuCoin", "Outra"])
    ativo = c3.text_input("Ativo (ex: SOL, BTC)").upper().strip()
    tipo = c4.selectbox("Tipo", ["Compra", "Venda", "Saldo Inicial", "Recompensa", "Taxa", "Transferência"])

    c5, c6, c7 = st.columns(3)
    quantidade = c5.number_input("Quantidade", min_value=0.0, format="%.8f")
    preco_usd = c6.number_input("Preço USD (unitário)", min_value=0.0, format="%.6f")
    taxa_usd = c7.number_input("Taxa USD", min_value=0.0, format="%.4f", value=0.0)

    observacao = st.text_input("Observação (opcional)")

    enviado = st.form_submit_button("Adicionar lançamento", use_container_width=True, type="primary")
    if enviado:
        if not ativo or quantidade <= 0:
            st.error("Preencha ao menos o ativo e uma quantidade maior que zero.")
        else:
            db.inserir_lancamento(data, exchange, ativo, tipo, quantidade, preco_usd, taxa_usd, observacao)
            st.cache_data.clear()
            st.success(f"Lançamento de {tipo.lower()} de {ativo} adicionado.")
            st.rerun()

st.divider()
st.subheader("Histórico")

lanc = db.carregar_lancamentos()
if lanc.empty:
    st.info("Nenhum lançamento ainda.")
    st.stop()

col1, col2, col3 = st.columns(3)
ativos = ["Todos"] + sorted(lanc["ativo"].unique().tolist())
exchanges = ["Todas"] + sorted(lanc["exchange"].unique().tolist())
filtro_ativo = col1.selectbox("Filtrar por ativo", ativos)
filtro_exchange = col2.selectbox("Filtrar por exchange", exchanges)
filtro_tipo = col3.selectbox("Filtrar por tipo", ["Todos"] + sorted(lanc["tipo"].unique().tolist()))

df = lanc.copy()
if filtro_ativo != "Todos":
    df = df[df["ativo"] == filtro_ativo]
if filtro_exchange != "Todas":
    df = df[df["exchange"] == filtro_exchange]
if filtro_tipo != "Todos":
    df = df[df["tipo"] == filtro_tipo]

st.dataframe(
    df[["data", "exchange", "ativo", "tipo", "quantidade", "preco_usd", "taxa_usd", "observacao"]],
    use_container_width=True, hide_index=True, height=450,
    column_config={
        "quantidade": st.column_config.NumberColumn(format="%.8f"),
        "preco_usd": st.column_config.NumberColumn(format="$ %.6f"),
        "taxa_usd": st.column_config.NumberColumn(format="$ %.4f"),
    },
)
st.caption(f"{len(df)} lançamentos exibidos de {len(lanc)} no total.")

with st.expander("Excluir um lançamento (use com cuidado)"):
    id_excluir = st.number_input("ID do lançamento a excluir", min_value=0, step=1)
    if st.button("Excluir", type="secondary"):
        if id_excluir in lanc["id"].values:
            db.excluir_lancamento(int(id_excluir))
            st.cache_data.clear()
            st.success(f"Lançamento {id_excluir} excluído.")
            st.rerun()
        else:
            st.error("ID não encontrado na tabela acima.")
