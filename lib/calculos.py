"""Tradução direta das fórmulas da planilha para pandas.

Referência (para quem for conferir contra o Excel um dia):
- Valor líquido de uma Compra/Saldo Inicial/Recompensa = quantidade*preço + taxa
- Valor líquido de uma Venda                            = quantidade*preço - taxa
- Custo médio (por ativo+exchange) = soma do custo de aquisição / soma da quantidade adquirida
- Vendas reduzem quantidade e realizam resultado, mas NUNCA alteram o custo médio
"""
import pandas as pd

TIPOS_AQUISICAO = ("Compra", "Saldo Inicial", "Recompensa")


def _divisao_segura(numerador: pd.Series, denominador: pd.Series, offset: float = 0.0) -> pd.Series:
    """(numerador / denominador) + offset, mas devolve 0 onde o denominador é 0
    em vez de estourar ZeroDivisionError — acontece sempre que uma posição
    está totalmente zerada (ex.: um ativo deslistado, custo_posicao = 0)."""
    resultado = pd.Series(0.0, index=numerador.index)
    mask = denominador != 0
    resultado.loc[mask] = numerador.loc[mask] / denominador.loc[mask] + offset
    return resultado


def calcular_posicoes(lanc: pd.DataFrame, precos: pd.DataFrame, config: dict) -> pd.DataFrame:
    if lanc.empty:
        return pd.DataFrame()

    df = lanc.copy()
    df["valor_liquido"] = df["quantidade"] * df["preco_usd"]
    df.loc[df["tipo"].isin(TIPOS_AQUISICAO), "valor_liquido"] += df["taxa_usd"]
    df.loc[df["tipo"] == "Venda", "valor_liquido"] -= df["taxa_usd"]

    df["qtd_aquisicao"] = df["quantidade"].where(df["tipo"].isin(TIPOS_AQUISICAO), 0)
    df["custo_aquisicao"] = df["valor_liquido"].where(df["tipo"].isin(TIPOS_AQUISICAO), 0)
    df["qtd_venda"] = df["quantidade"].where(df["tipo"] == "Venda", 0)
    df["receita_venda"] = df["valor_liquido"].where(df["tipo"] == "Venda", 0)
    df["qtd_taxa_pura"] = df["quantidade"].where(df["tipo"] == "Taxa", 0)

    g = df.groupby(["ativo", "exchange"], as_index=False).agg(
        qtd_aquisicao=("qtd_aquisicao", "sum"),
        custo_aquisicao=("custo_aquisicao", "sum"),
        qtd_venda=("qtd_venda", "sum"),
        receita_venda=("receita_venda", "sum"),
        qtd_taxa_pura=("qtd_taxa_pura", "sum"),
    )
    g["qtd_atual"] = g["qtd_aquisicao"] - g["qtd_venda"] - g["qtd_taxa_pura"]
    g["custo_medio"] = _divisao_segura(g["custo_aquisicao"], g["qtd_aquisicao"])
    g["custo_posicao"] = g["qtd_atual"] * g["custo_medio"]
    g["pl_realizado"] = g["receita_venda"] - g["qtd_venda"] * g["custo_medio"]

    g = g.merge(precos[["ativo", "preco_usd"]], on="ativo", how="left")
    g["preco_usd"] = g["preco_usd"].fillna(0)
    g = g.rename(columns={"preco_usd": "preco_atual"})

    g["valor_atual"] = g["qtd_atual"] * g["preco_atual"]
    g["pl_aberto"] = g["valor_atual"] - g["custo_posicao"]
    g["pl_aberto_pct"] = _divisao_segura(g["preco_atual"], g["custo_medio"], offset=-1.0)

    cambio = config.get("cambio_usd_brl", 0) or 0
    g["valor_atual_brl"] = g["valor_atual"] * cambio

    patrimonio_total = g["valor_atual"].sum()
    g["pct_carteira"] = g["valor_atual"] / patrimonio_total if patrimonio_total > 0 else 0

    alvo_recompra = 1 + config.get("gatilho_recompra", -0.10)
    alvo_realizacao = 1 + config.get("gatilho_realizacao", 0.30)
    g["alvo_recompra"] = g["custo_medio"] * alvo_recompra
    g["alvo_realizacao"] = g["custo_medio"] * alvo_realizacao

    def status(row):
        if row["qtd_atual"] <= 1e-9:
            return "Zerada"
        if row["preco_atual"] <= row["alvo_recompra"]:
            return "Recompra"
        if row["preco_atual"] >= row["alvo_realizacao"]:
            return "Realizar Parcial"
        return "Dentro do Alvo"

    g["status"] = g.apply(status, axis=1)
    return g.sort_values(["exchange", "ativo"]).reset_index(drop=True)


def calcular_consolidado(posicoes: pd.DataFrame, config: dict) -> pd.DataFrame:
    if posicoes.empty:
        return pd.DataFrame()
    g = posicoes.groupby("ativo", as_index=False).agg(
        qtd_atual=("qtd_atual", "sum"),
        custo_posicao=("custo_posicao", "sum"),
        valor_atual=("valor_atual", "sum"),
        pl_realizado=("pl_realizado", "sum"),
    )
    g["custo_medio"] = _divisao_segura(g["custo_posicao"], g["qtd_atual"])
    g["pl_pct"] = _divisao_segura(g["valor_atual"], g["custo_posicao"], offset=-1.0)
    patrimonio_total = posicoes["valor_atual"].sum()
    g["pct_carteira"] = g["valor_atual"] / patrimonio_total if patrimonio_total > 0 else 0
    alocacao_max = config.get("alocacao_maxima", 0.15)
    g["concentrado"] = g["pct_carteira"] > alocacao_max
    return g.sort_values("valor_atual", ascending=False).reset_index(drop=True)


def calcular_painel(posicoes: pd.DataFrame, config: dict) -> dict:
    if posicoes.empty:
        return {k: 0 for k in (
            "total_investido", "patrimonio_atual", "resultado_aberto", "resultado_aberto_pct",
            "resultado_realizado", "resultado_total", "caixa_usdt", "exposicao_cripto",
            "n_posicoes", "capital_aportado", "resultado_sobre_aporte", "resultado_sobre_aporte_pct",
        )}

    total_investido = posicoes["custo_posicao"].sum()
    patrimonio_atual = posicoes["valor_atual"].sum()
    resultado_aberto = patrimonio_atual - total_investido
    resultado_realizado = posicoes["pl_realizado"].sum()
    caixa_usdt = posicoes.loc[posicoes["ativo"] == "USDT", "valor_atual"].sum()

    aporte_binance = config.get("aporte_binance_brl", 0) / (config.get("cambio_medio_binance", 1) or 1)
    aporte_kucoin = config.get("aporte_kucoin_brl", 0) / (config.get("cambio_medio_kucoin", 1) or 1)
    capital_aportado = aporte_binance + aporte_kucoin
    resultado_sobre_aporte = patrimonio_atual - capital_aportado

    return dict(
        total_investido=total_investido,
        patrimonio_atual=patrimonio_atual,
        resultado_aberto=resultado_aberto,
        resultado_aberto_pct=(resultado_aberto / total_investido) if total_investido else 0,
        resultado_realizado=resultado_realizado,
        resultado_total=resultado_aberto + resultado_realizado,
        caixa_usdt=caixa_usdt,
        exposicao_cripto=patrimonio_atual - caixa_usdt,
        n_posicoes=int((posicoes["qtd_atual"] > 1e-9).sum()),
        capital_aportado=capital_aportado,
        resultado_sobre_aporte=resultado_sobre_aporte,
        resultado_sobre_aporte_pct=(resultado_sobre_aporte / capital_aportado) if capital_aportado else 0,
    )


def alertas(posicoes: pd.DataFrame, consolidado: pd.DataFrame) -> dict:
    if posicoes.empty:
        return dict(recompra=0, realizacao=0, concentrados=0, sem_preco=0)
    return dict(
        recompra=int((posicoes["status"] == "Recompra").sum()),
        realizacao=int((posicoes["status"] == "Realizar Parcial").sum()),
        concentrados=int(consolidado["concentrado"].sum()) if not consolidado.empty else 0,
        sem_preco=int(((posicoes["qtd_atual"] > 1e-9) & (posicoes["preco_atual"] == 0)).sum()),
    )
