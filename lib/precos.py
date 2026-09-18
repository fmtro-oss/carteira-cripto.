"""Cotações ao vivo — substitui o Power Query da planilha.

Mesma regra de antes: Binance manda, KuCoin cobre o que a Binance não tem.
Cacheado por 5 minutos para não bater na API a cada clique do usuário.
"""
import requests
import pandas as pd
import streamlit as st


@st.cache_data(ttl=300, show_spinner=False)
def buscar_precos_binance() -> pd.DataFrame:
    r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=10)
    r.raise_for_status()
    dados = r.json()
    df = pd.DataFrame(dados)
    df = df[df["symbol"].str.endswith("USDT")].copy()
    df["ativo"] = df["symbol"].str[:-4]
    df["preco_usd"] = pd.to_numeric(df["price"])
    df["fonte"] = "Binance"
    return df[["ativo", "preco_usd", "fonte"]]


@st.cache_data(ttl=300, show_spinner=False)
def buscar_precos_kucoin() -> pd.DataFrame:
    r = requests.get("https://api.kucoin.com/api/v1/market/allTickers", timeout=10)
    r.raise_for_status()
    dados = r.json()["data"]["ticker"]
    df = pd.DataFrame(dados)
    df = df[df["symbol"].str.endswith("-USDT")].copy()
    df["ativo"] = df["symbol"].str.replace("-USDT", "", regex=False)
    df["preco_usd"] = pd.to_numeric(df["last"])
    df["fonte"] = "KuCoin"
    return df[["ativo", "preco_usd", "fonte"]]


@st.cache_data(ttl=300, show_spinner="Atualizando cotações...")
def buscar_precos_consolidados() -> pd.DataFrame:
    """Uma linha por ativo. Binance tem prioridade; KuCoin cobre o resto."""
    try:
        binance = buscar_precos_binance()
    except Exception:
        binance = pd.DataFrame(columns=["ativo", "preco_usd", "fonte"])
    try:
        kucoin = buscar_precos_kucoin()
    except Exception:
        kucoin = pd.DataFrame(columns=["ativo", "preco_usd", "fonte"])

    kucoin_exclusivo = kucoin[~kucoin["ativo"].isin(binance["ativo"])]
    consolidado = pd.concat([binance, kucoin_exclusivo], ignore_index=True)
    consolidado["preco_usd"] = consolidado["preco_usd"].replace(0, pd.NA)
    return consolidado.drop_duplicates(subset="ativo").sort_values("ativo").reset_index(drop=True)


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_cambio_usd_brl() -> float:
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=10)
        r.raise_for_status()
        return float(r.json()["USDBRL"]["bid"])
    except Exception:
        return None
