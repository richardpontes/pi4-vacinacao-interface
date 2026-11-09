import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Vacinação em Porto Alegre", layout="wide")

FAIXAS = ["0 a 4", "5 a 9", "10 a 14", "15 a 19", "20 a 24", "25 a 29",
          "30 a 39", "40 a 49", "50 a 59", "60 a 69", "70 ou mais"]


@st.cache_data
def carregar_series():
    return pd.read_csv("dados/tb_series_temporais_doses_v3.csv", parse_dates=["data_aplicacao"])


@st.cache_data
def carregar_mapa():
    with open("dados/malha_bairros_poa.geojson", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def carregar_cobertura():
    codigos = (pd.read_csv("dados/dim_populacao_bairro.csv", dtype={"cd_bairro": str})
                 [["cd_bairro", "nm_bairro"]].drop_duplicates())
    partes = []
    for vacina, arquivo in [("Influenza", "dados/tb_cobertura_influenza_v3.csv"),
                            ("Covid", "dados/tb_cobertura_covid_v3.csv")]:
        d = pd.read_csv(arquivo)
        d["vacina"] = vacina
        partes.append(d)
    cobertura = pd.concat(partes).merge(codigos, left_on="bairro", right_on="nm_bairro", how="left")
    return cobertura, codigos


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

with aba2:
    cobertura, codigos = carregar_cobertura()
    geo = carregar_mapa()

    c1, c2 = st.columns(2)
    vacina = c1.radio("Vacina", ["Influenza", "Covid"], horizontal=True)
    disponiveis = [f for f in FAIXAS
                   if ((cobertura["vacina"] == vacina) & (cobertura["faixa_etaria"] == f)).any()]
    faixa = c2.selectbox("Faixa etária (anos)", disponiveis, index=len(disponiveis) - 1)

    sel = cobertura[(cobertura["vacina"] == vacina) & (cobertura["faixa_etaria"] == faixa)]

    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=geo, featureidkey="properties.CD_BAIRRO",
        locations=codigos["cd_bairro"].tolist(), z=[0] * len(codigos),
        colorscale=[[0, "#D9D9D9"], [1, "#D9D9D9"]], showscale=False,
        marker_line_color="white", marker_line_width=0.5,
        customdata=codigos["nm_bairro"].tolist(),
        hovertemplate="<b>%{customdata}</b><br>Sem dado suficiente ou excluído<extra></extra>"))
    fig.add_trace(go.Choroplethmap(
        geojson=geo, featureidkey="properties.CD_BAIRRO",
        locations=sel["cd_bairro"].tolist(), z=sel["cobertura_pct"].tolist(),
        colorscale="Blues", marker_line_color="white", marker_line_width=0.5,
        colorbar_title="População<br>vacinada (%)",
        customdata=sel[["bairro", "pacientes_unicos", "populacao"]].values,
        hovertemplate=("<b>%{customdata[0]}</b><br>Vacinados: %{customdata[1]:,}"
                       "<br>População: %{customdata[2]:,}"
                       "<br>População vacinada: %{z:.1f}%<extra></extra>")))
    fig.update_layout(map_style="carto-positron", map_center={"lat": -30.10, "lon": -51.17},
                      map_zoom=10.0, height=650, margin=dict(l=0, r=0, t=0, b=0),
                      separators=",.")
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Bairros com dado nesta seleção: {len(sel)} de {len(codigos)}. "
               "População vacinada (%) = pessoas vacinadas ao menos uma vez de janeiro a setembro "
               "de 2026 ÷ população da faixa etária no bairro (IBGE, Censo 2022) × 100. "
               "Em cinza: bairros excluídos por distorção no registro do endereço ou com menos de "
               "30 vacinados na faixa, número insuficiente para uma estimativa confiável.")

for aba in (aba3, aba4):
    with aba:
        st.info("Em construção.")