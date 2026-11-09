import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Vacinação em Porto Alegre", layout="wide")


@st.cache_data
def carregar_series():
    return pd.read_csv("dados/tb_series_temporais_doses_v3.csv", parse_dates=["data_aplicacao"])


def fmt(n):
    return f"{n:,.0f}".replace(",", ".")


st.title("Vacinação dos moradores de Porto Alegre — 2026")
st.caption("Fonte: Programa Nacional de Imunizações (PNI), Ministério da Saúde. "
           "Dados extraídos do Portal de Dados Abertos do SUS em 02/10/2026.")

aba1, aba2, aba3, aba4 = st.tabs(["Visão geral", "Vacinação por bairro",
                                  "Níveis de adesão", "Séries temporais"])

with aba1:
    df = carregar_series()

    c1, c2, c3 = st.columns(3)
    c1.metric("Doses aplicadas", fmt(df["total_doses_aplicadas"].sum()))
    c2.metric("Período", f"{df['data_aplicacao'].min():%d/%m} a {df['data_aplicacao'].max():%d/%m/%Y}")
    c3.metric("Vacinas diferentes", df["sg_imunobiologico"].nunique())

    NOMES_VACINAS = {
        "INF3": "Influenza trivalente",
        "COV-19 PFIZER-COMIRN": "Covid-19 (Pfizer)",
        "INF4": "Influenza quadrivalente",
        "dT": "Dupla adulto (difteria e tétano)",
        "HB": "Hepatite B",
        "VIP": "Poliomielite inativada (VIP)",
        "DNG": "Dengue",
        "MenACWY": "Meningocócica ACWY",
        "VFA": "Febre amarela",
        "SCR": "Tríplice viral (sarampo, caxumba e rubéola)",
    }
    top = (df.groupby("sg_imunobiologico")["total_doses_aplicadas"].sum()
             .nlargest(10).sort_values().reset_index())
    top["vacina"] = top["sg_imunobiologico"].map(NOMES_VACINAS).fillna(top["sg_imunobiologico"])
    fig = px.bar(top, x="total_doses_aplicadas", y="vacina", orientation="h",
                 labels={"total_doses_aplicadas": "Doses aplicadas", "vacina": ""})
    fig.update_layout(separators=",.")
    fig.update_xaxes(tickformat=",d")
    st.subheader("As 10 vacinas mais aplicadas")
    st.plotly_chart(fig, use_container_width=True)

for aba in (aba2, aba3, aba4):
    with aba:
        st.info("Em construção.")