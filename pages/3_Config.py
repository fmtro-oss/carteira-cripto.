import streamlit as st
from lib import db, precos as precos_mod

st.set_page_config(page_title="Config — Carteira Cripto", page_icon="⚙️", layout="centered")
st.title("⚙️ Parâmetros da carteira")

cfg = db.carregar_config()

with st.form("config_form"):
    st.subheader("Câmbio e gatilhos")
    cambio = st.number_input("Câmbio USD/BRL", value=float(cfg.get("cambio_usd_brl", 5.0)), format="%.4f")
    gatilho_recompra = st.number_input(
        "Gatilho de recompra (fração; -0.10 = -10%)",
        value=float(cfg.get("gatilho_recompra", -0.10)), format="%.2f", step=0.01)
    gatilho_realizacao = st.number_input(
        "Gatilho de realização parcial (fração; 0.30 = +30%)",
        value=float(cfg.get("gatilho_realizacao", 0.30)), format="%.2f", step=0.01)
    alocacao_maxima = st.number_input(
        "Alocação máxima por ativo (fração; 0.15 = 15%)",
        value=float(cfg.get("alocacao_maxima", 0.15)), format="%.2f", step=0.01)

    st.subheader("Aportes (para separar resultado sobre custo x sobre dinheiro investido)")
    c1, c2 = st.columns(2)
    aporte_binance = c1.number_input("Aporte total Binance (BRL)", value=float(cfg.get("aporte_binance_brl", 0)))
    cambio_binance = c2.number_input("Câmbio médio do aporte (Binance)", value=float(cfg.get("cambio_medio_binance", 5.5)), format="%.4f")
    c3, c4 = st.columns(2)
    aporte_kucoin = c3.number_input("Aporte total KuCoin (BRL)", value=float(cfg.get("aporte_kucoin_brl", 0)))
    cambio_kucoin = c4.number_input("Câmbio médio do aporte (KuCoin)", value=float(cfg.get("cambio_medio_kucoin", 5.5)), format="%.4f")

    salvar = st.form_submit_button("Salvar parâmetros", type="primary", width="stretch")
    if salvar:
        db.salvar_config("cambio_usd_brl", cambio)
        db.salvar_config("gatilho_recompra", gatilho_recompra)
        db.salvar_config("gatilho_realizacao", gatilho_realizacao)
        db.salvar_config("alocacao_maxima", alocacao_maxima)
        db.salvar_config("aporte_binance_brl", aporte_binance)
        db.salvar_config("cambio_medio_binance", cambio_binance)
        db.salvar_config("aporte_kucoin_brl", aporte_kucoin)
        db.salvar_config("cambio_medio_kucoin", cambio_kucoin)
        st.cache_data.clear()
        st.success("Parâmetros salvos.")
        st.rerun()

st.divider()
st.subheader("Câmbio ao vivo (referência)")
cambio_api = precos_mod.buscar_cambio_usd_brl()
if cambio_api:
    st.metric("USD/BRL agora (AwesomeAPI)", f"{cambio_api:,.4f}")
    if st.button("Usar este câmbio"):
        db.salvar_config("cambio_usd_brl", cambio_api)
        st.cache_data.clear()
        st.success("Câmbio atualizado.")
        st.rerun()
else:
    st.warning("Não consegui buscar o câmbio agora. Tente novamente em instantes.")
