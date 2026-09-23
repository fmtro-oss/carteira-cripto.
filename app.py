import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib import db, precos as precos_mod, calculos

st.set_page_config(page_title="Carteira Cripto", page_icon="💠", layout="wide")

# ---------------------------------------------------------------- estilo
st.markdown("""
<style>
[data-testid="stMetric"] {
    background: #0c0c0c;
    border: 1px solid #262626;
    border-left: 3px solid #39D98A;
    border-radius: 10px;
    padding: 18px 20px 10px 20px;
}
[data-testid="stMetricLabel"] p { color: #b3b3b3 !important; }
[data-testid="stMetricValue"] { color: #FAFAFA; }
.bloco-alerta {
    background: #0c0c0c;
    border: 1px solid #262626;
    border-left: 3px solid #39D98A;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.bloco-alerta .num { font-size: 28px; font-weight: 700; color: #39D98A; }
.bloco-alerta .lbl { font-size: 12px; color: #b3b3b3; }
</style>
""", unsafe_allow_html=True)

st.title("💠 Carteira Cripto")

col_a, col_b = st.columns([5, 1])
with col_b:
    if st.button("🔄 Atualizar cotações", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------------- dados
lanc = db.carregar_lancamentos()
cfg = db.carregar_config()
cotacoes = precos_mod.buscar_precos_consolidados()

posicoes = calculos.calcular_posicoes(lanc, cotacoes, cfg)
consolidado = calculos.calcular_consolidado(posicoes, cfg)
painel = calculos.calcular_painel(posicoes, cfg)
alertas = calculos.alertas(posicoes, consolidado)

if lanc.empty:
    st.info("Nenhum lançamento ainda. Use a página **Lançamentos** no menu à esquerda para começar, ou rode a migração inicial a partir da sua planilha.")
    st.stop()

cambio = cfg.get("cambio_usd_brl", 0)

# ---------------------------------------------------------------- KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total investido (custo)", f"$ {painel['total_investido']:,.2f}")
c2.metric("Patrimônio atual", f"$ {painel['patrimonio_atual']:,.2f}",
          f"{painel['resultado_aberto_pct']*100:,.1f}%")
c3.metric("Resultado já realizado", f"$ {painel['resultado_realizado']:,.2f}")
c4.metric("Resultado total", f"$ {painel['resultado_total']:,.2f}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Caixa em USDT", f"$ {painel['caixa_usdt']:,.2f}")
c6.metric("Exposição em cripto", f"$ {painel['exposicao_cripto']:,.2f}")
c7.metric("Capital aportado", f"$ {painel['capital_aportado']:,.2f}")
c8.metric("Resultado sobre o aporte", f"$ {painel['resultado_sobre_aporte']:,.2f}",
          f"{painel['resultado_sobre_aporte_pct']*100:,.1f}%")

st.caption(f"Câmbio USD/BRL: {cambio:,.4f} · Patrimônio em BRL: R$ {painel['patrimonio_atual']*cambio:,.2f}")

st.divider()

# ---------------------------------------------------------------- alertas
st.subheader("Alertas")
a1, a2, a3, a4 = st.columns(4)
for col, num, lbl in [
    (a1, alertas["recompra"], "posições em zona de recompra"),
    (a2, alertas["realizacao"], "posições em zona de realização"),
    (a3, alertas["concentrados"], "ativos acima da alocação máxima"),
    (a4, alertas["sem_preco"], "ativos sem preço atualizado"),
]:
    col.markdown(f'<div class="bloco-alerta"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>',
                  unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------- gráficos por exchange
st.subheader("Por exchange")
por_exchange = posicoes.groupby("exchange", as_index=False).agg(
    custo=("custo_posicao", "sum"), atual=("valor_atual", "sum"))
por_exchange["pl_pct"] = (por_exchange["atual"] / por_exchange["custo"] - 1).where(por_exchange["custo"] > 0, 0) * 100

g1, g2 = st.columns(2)
with g1:
    fig = go.Figure()
    fig.add_bar(name="Custo", x=por_exchange["exchange"], y=por_exchange["custo"], marker_color="#3a3a3a")
    fig.add_bar(name="Valor atual", x=por_exchange["exchange"], y=por_exchange["atual"], marker_color="#39D98A")
    fig.update_layout(barmode="group", template="plotly_dark", height=340,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                       title="Custo vs. valor atual")
    st.plotly_chart(fig, width="stretch")
with g2:
    cores = ["#f87171" if v < 0 else "#39D98A" for v in por_exchange["pl_pct"]]
    fig2 = go.Figure(go.Bar(x=por_exchange["exchange"], y=por_exchange["pl_pct"], marker_color=cores))
    fig2.update_layout(template="plotly_dark", height=340,
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        title="P/L % por exchange", yaxis_ticksuffix="%")
    st.plotly_chart(fig2, width="stretch")

st.divider()

# ---------------------------------------------------------------- consolidado por ativo
st.subheader("Consolidado por ativo")
tabela = consolidado.copy()
tabela["pl_pct"] = tabela["pl_pct"] * 100
tabela["pct_carteira"] = tabela["pct_carteira"] * 100
tabela = tabela.rename(columns={
    "ativo": "Ativo", "qtd_atual": "Qtd", "custo_medio": "Custo médio (USD)",
    "custo_posicao": "Custo total (USD)", "valor_atual": "Valor atual (USD)",
    "pl_pct": "P/L %", "pct_carteira": "% carteira", "concentrado": "Concentrado?",
})
st.dataframe(
    tabela[["Ativo", "Qtd", "Custo médio (USD)", "Custo total (USD)", "Valor atual (USD)", "P/L %", "% carteira", "Concentrado?"]],
    width="stretch", hide_index=True,
    column_config={
        "Qtd": st.column_config.NumberColumn(format="%.6f"),
        "Custo médio (USD)": st.column_config.NumberColumn(format="$ %.4f"),
        "Custo total (USD)": st.column_config.NumberColumn(format="$ %.2f"),
        "Valor atual (USD)": st.column_config.NumberColumn(format="$ %.2f"),
        "P/L %": st.column_config.NumberColumn(format="%.1f%%"),
        "% carteira": st.column_config.NumberColumn(format="%.1f%%"),
    },
)
