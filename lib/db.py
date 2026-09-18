"""Conexão com o Supabase e funções de leitura/escrita da tabela lancamentos e config.

Todas as funções devolvem/recebem pandas DataFrames — o resto do app nunca
fala com o Supabase diretamente, só com estas funções.
"""
import pandas as pd
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def carregar_lancamentos() -> pd.DataFrame:
    """Lê todos os lançamentos, mais recentes primeiro."""
    sb = get_client()
    resultado = sb.table("lancamentos").select("*").order("data", desc=True).execute()
    df = pd.DataFrame(resultado.data)
    if df.empty:
        return pd.DataFrame(columns=[
            "id", "data", "exchange", "ativo", "tipo",
            "quantidade", "preco_usd", "taxa_usd", "observacao",
        ])
    df["data"] = pd.to_datetime(df["data"]).dt.date
    for col in ("quantidade", "preco_usd", "taxa_usd"):
        df[col] = pd.to_numeric(df[col])
    return df


def inserir_lancamento(data, exchange, ativo, tipo, quantidade, preco_usd, taxa_usd, observacao):
    sb = get_client()
    sb.table("lancamentos").insert({
        "data": str(data),
        "exchange": exchange,
        "ativo": ativo.upper().strip(),
        "tipo": tipo,
        "quantidade": float(quantidade),
        "preco_usd": float(preco_usd),
        "taxa_usd": float(taxa_usd or 0),
        "observacao": observacao or "",
    }).execute()


def excluir_lancamento(id_lancamento: int):
    sb = get_client()
    sb.table("lancamentos").delete().eq("id", id_lancamento).execute()


def carregar_config() -> dict:
    sb = get_client()
    resultado = sb.table("config").select("*").execute()
    return {row["chave"]: row["valor"] for row in resultado.data}


def salvar_config(chave: str, valor: float):
    sb = get_client()
    sb.table("config").upsert({"chave": chave, "valor": float(valor)}).execute()
