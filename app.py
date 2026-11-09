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

EXCLUIDOS = ["Farroupilha", "Praia de Belas", "Vila Conceição", "Pedra Redonda",
             "Navegantes", "Agronomia"]
CORES_NIVEL = {"Baixa": "#C0392B", "Intermediária": "#E0A526", "Alta": "#1E8C6E",
               "Excluído": "#9E9E9E", "Dados insuficientes": "#E0E0E0"}


@st.cache_data
def carregar_clustering():
    return pd.read_csv("dados/tb_clustering_cobertura_v3.csv")

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
        # colorbar_title="População<br>vacinada (%)",
        colorbar=dict(title="População<br>vacinada (%)", x=0.01, xanchor="left",
                      y=0.02, yanchor="bottom", len=0.45, bgcolor="rgba(255,255,255,0.85)"),
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

with aba3:
    clus = carregar_clustering()
    _, codigos = carregar_cobertura()
    geo = carregar_mapa()

    mapa = codigos.merge(clus, left_on="nm_bairro", right_on="bairro", how="left")
    mapa["categoria"] = mapa["nivel_adesao"]
    mapa.loc[mapa["nm_bairro"].isin(EXCLUIDOS), "categoria"] = "Excluído"
    mapa["categoria"] = mapa["categoria"].fillna("Dados insuficientes")
    n = mapa["categoria"].value_counts()
    mapa["legenda"] = mapa["categoria"].map(lambda c: f"{c} ({n[c]} bairros)")

    fig = px.choropleth_map(
        mapa, geojson=geo, featureidkey="properties.CD_BAIRRO", locations="cd_bairro",
        color="legenda",
        color_discrete_map={f"{c} ({n[c]} bairros)": cor for c, cor in CORES_NIVEL.items() if c in n},
        category_orders={"legenda": [f"{c} ({n[c]} bairros)" for c in CORES_NIVEL if c in n]},
        hover_name="nm_bairro", hover_data={"cd_bairro": False, "legenda": False, "categoria": True},
        labels={"categoria": "Nível"},
        map_style="carto-positron", center={"lat": -30.12, "lon": -51.17}, zoom=10.0, height=750)
    fig.update_traces(marker_line_color="white", marker_line_width=0.5)
    # fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Nível de adesão")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Nível de adesão",
                      legend=dict(x=0.01, xanchor="left", y=0.02, yanchor="bottom",
                                  bgcolor="rgba(255,255,255,0.85)"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Perfil médio de cada nível")
    indicadores = {"inf_0a4": "Influenza<br>0 a 4 anos", "inf_60a69": "Influenza<br>60 a 69 anos",
                   "inf_70mais": "Influenza<br>70 anos ou mais", "cov_60a69": "Covid<br>60 a 69 anos",
                   "cov_70mais": "Covid<br>70 anos ou mais"}
    perfil = (clus.groupby("nivel_adesao")[list(indicadores)].mean()
                  .reindex(["Baixa", "Intermediária", "Alta"]).rename(columns=indicadores)
                  .reset_index()
                  .melt(id_vars="nivel_adesao", var_name="indicador", value_name="valor"))
    fig2 = px.bar(perfil, x="indicador", y="valor", color="nivel_adesao", barmode="group",
                  color_discrete_map=CORES_NIVEL, text_auto=".1f",
                  labels={"indicador": "", "valor": "População vacinada, média dos bairros (%)",
                          "nivel_adesao": "Nível de adesão"})
    fig2.update_layout(separators=",.")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Bairros de cada nível")
    colunas = st.columns(3)
    for coluna, nivel in zip(colunas, ["Baixa", "Intermediária", "Alta"]):
        lista = sorted(clus.loc[clus["nivel_adesao"] == nivel, "bairro"])
        coluna.markdown(f"**{nivel} ({len(lista)} bairros)**")
        coluna.markdown("\n".join(f"- {b}" for b in lista))

    st.caption("Os níveis foram obtidos por agrupamento K-Means (K = 3) a partir de cinco indicadores "
               "de população vacinada por bairro: influenza em 0 a 4, 60 a 69 e 70 anos ou mais, e "
               "covid em 60 a 69 e 70 anos ou mais. Os grupos representam faixas de um gradiente "
               "contínuo de vacinação, e não tipos de bairro distintos. Excluído: bairros com "
               "distorção no registro do endereço. Dados insuficientes: bairros com menos de 30 "
               "vacinados em algum dos cinco indicadores.")

with aba4:
    st.info("Em construção.")