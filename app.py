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


ESTILO = """
<style>
.block-container {padding-top: 2rem;}
.faixa {background: #1B2A41; color: white; border-radius: 12px; padding: 1.4rem 1.8rem;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;}
.faixa h1 {color: white; font-size: 1.7rem; margin: 0; padding: 0;}
.faixa p {color: #C9D3E0; margin: 0.3rem 0 0 0; font-size: 0.95rem;}
.selo {background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.3);
       border-radius: 20px; padding: 0.35rem 0.9rem; font-size: 0.85rem; color: #E6ECF3;
       white-space: nowrap;}
.cartao {background: white; border: 1px solid #E3E8EF; border-top: 5px solid var(--cor);
         border-radius: 10px; padding: 1rem 1.2rem; height: 100%;}
.cartao .rotulo {font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em;
                 color: #5B6675; margin: 0;}
.cartao .valor {font-size: 1.9rem; font-weight: 700; color: #1F2937; margin: 0.2rem 0;}
.cartao .detalhe {font-size: 0.85rem; color: var(--cor); margin: 0;}
button[data-baseweb="tab"] p {font-size: 1rem;}
</style>
"""
st.markdown(ESTILO, unsafe_allow_html=True)

st.markdown("""
<div class="faixa">
  <div>
    <h1>Vacinação dos moradores de Porto Alegre — 2026</h1>
    <p>Projeto Integrador em Computação IV · UNIVESP · Entidade parceira: Vigilância Epidemiológica de Porto Alegre</p>
  </div>
  <div class="selo">Dados: PNI · extraídos em 02/10/2026</div>
</div>
""", unsafe_allow_html=True)

aba1, aba2, aba3, aba4 = st.tabs(["📊 Visão geral", "🗺️ Vacinação por bairro",
                                  "🧭 Níveis de adesão", "📈 Séries temporais"])

def cartao(rotulo, valor, detalhe, cor):
    return (f'<div class="cartao" style="--cor:{cor}"><p class="rotulo">{rotulo}</p>'
            f'<p class="valor">{valor}</p><p class="detalhe">{detalhe}</p></div>')


MESES = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

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

with aba1:
    df = carregar_series()
    diario = df.groupby("data_aplicacao")["total_doses_aplicadas"].sum()
    dia_max = diario.idxmax()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(cartao("Doses aplicadas", fmt(df["total_doses_aplicadas"].sum()),
                       "Em moradores de Porto Alegre", "#1F4E79"), unsafe_allow_html=True)
    c2.markdown(cartao("Período", f"{diario.index.min():%d/%m} a {diario.index.max():%d/%m/%Y}",
                       "Último dia com registro parcial", "#5B7DB1"), unsafe_allow_html=True)
    c3.markdown(cartao("Vacinas diferentes", df["sg_imunobiologico"].nunique(),
                       "Imunobiológicos registrados no PNI", "#1E8C6E"), unsafe_allow_html=True)
    c4.markdown(cartao("Dia com mais doses", fmt(diario.max()),
                       f"{dia_max:%d/%m} · Dia D contra a gripe", "#E0A526"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Doses aplicadas por mês")
    mensal = diario.groupby(diario.index.month).sum()
    mensal_df = pd.DataFrame({"mes": [MESES[m] for m in mensal.index], "doses": mensal.values})
    fig = px.line(mensal_df, x="mes", y="doses", markers=True,
                  labels={"mes": "", "doses": "Doses aplicadas"})
    fig.update_traces(line_color="#1F4E79", fill="tozeroy", fillcolor="rgba(31,78,121,0.12)",
                      hovertemplate="%{x}<br>%{y:,.0f} doses<extra></extra>")
    eventos = {"Abr": "Campanha contra a gripe<br>(Dia D em 11/04)",
               "Jun": "Vacina da gripe liberada<br>para toda a população",
               "Ago": "Dia D da<br>Multivacinação (22/08)"}
    for mes, texto in eventos.items():
        y = mensal_df.loc[mensal_df["mes"] == mes, "doses"].iloc[0]
        fig.add_annotation(x=mes, y=y, text=texto, showarrow=True, arrowhead=2, ay=-50,
                           font=dict(size=11, color="#1F2937"), bgcolor="white",
                           bordercolor="#C9D3E0", borderpad=4)
    fig.update_layout(separators=",.", height=430, margin=dict(t=30))
    fig.update_yaxes(tickformat=",d", range=[0, mensal_df["doses"].max() * 1.3])
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Setembro inclui os registros até 26/09/2026.")

    st.subheader("As 10 vacinas mais aplicadas")
    top = (df.groupby("sg_imunobiologico")["total_doses_aplicadas"].sum()
             .nlargest(10).sort_values().reset_index())
    top["vacina"] = top["sg_imunobiologico"].map(NOMES_VACINAS).fillna(top["sg_imunobiologico"])
    fig = px.bar(top, x="total_doses_aplicadas", y="vacina", orientation="h",
                 labels={"total_doses_aplicadas": "Doses aplicadas", "vacina": ""},
                 color_discrete_sequence=["#1F4E79"])
    fig.update_traces(hovertemplate="%{y}<br>%{x:,.0f} doses<extra></extra>")
    fig.update_layout(separators=",.", height=430)
    fig.update_xaxes(tickformat=",d")
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

@st.cache_data
def carregar_previsao():
    return pd.read_csv("dados/previsao_series_temporais.csv", parse_dates=["data"])


@st.cache_data
def carregar_comparacao():
    return pd.read_csv("dados/comparacao_modelos.csv")


NOMES_MODELOS = {
    "Naive": "Ingênuo",
    "Sazonal ingênuo (7d)": "Sazonal ingênuo (7 dias)",
    "Média dia-semana 4sem": "Média por dia da semana (4 semanas)",
    "SARIMA (busca)": "SARIMA (busca em grade)",
    "SARIMA(0,1,1)(0,1,1)7": "SARIMA(0,1,1)(0,1,1)₇",
    "SARIMA log": "SARIMA(0,1,1)(0,1,1)₇ em log",
    "Prophet": "Prophet",
}

with aba4:
    serie_df = carregar_series()
    prev = carregar_previsao()
    comp = carregar_comparacao()

    opcoes = {"Total de doses": "TOTAL"}
    for cod in ["INF3", "COV-19 PFIZER-COMIRN", "INF4", "dT", "HB"]:
        opcoes[NOMES_VACINAS.get(cod, cod)] = cod
    escolha = st.selectbox("Série", list(opcoes))
    cod = opcoes[escolha]

    base = serie_df if cod == "TOTAL" else serie_df[serie_df["sg_imunobiologico"] == cod]
    hist = (base[base["data_aplicacao"] <= "2026-09-25"]
              .groupby("data_aplicacao")["total_doses_aplicadas"].sum()
              .asfreq("D", fill_value=0).iloc[-90:])

    comp_s = comp[comp["serie"] == cod].sort_values("RMSE")
    melhor = comp_s.iloc[0]["modelo"]
    st.markdown(f"**Modelo usado na previsão:** {NOMES_MODELOS.get(melhor, melhor)} "
                "(menor RMSE no período de teste)")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Real (últimos 90 dias)",
                             line=dict(color="gray"),
                             hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} doses<extra></extra>"))
    fig.add_trace(go.Scatter(x=prev["data"], y=prev[cod], name="Previsão (próximas 4 semanas)",
                             line=dict(color="#1E8C6E", dash="dash"),
                             hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f} doses<extra></extra>"))
    fig.update_layout(height=450, separators=",.", yaxis_title="Doses aplicadas por dia",
                      legend=dict(orientation="h", y=-0.15), margin=dict(t=20))
    fig.update_yaxes(tickformat=",d")
    fig.update_xaxes(tickformat="%d/%m")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Comparação dos modelos no período de teste (29/08 a 25/09)")
    tabela = (comp_s.assign(Modelo=comp_s["modelo"].map(NOMES_MODELOS))
                    [["Modelo", "MAE", "RMSE", "sMAPE_%"]]
                    .rename(columns={"sMAPE_%": "sMAPE (%)"}))
    estilo = (tabela.style
                    .format(precision=1, decimal=",", thousands=".",
                            subset=["MAE", "RMSE", "sMAPE (%)"])
                    .apply(lambda linha: ["background-color: #D5EFE6" if linha.name == tabela.index[0]
                                          else "" for _ in linha], axis=1))
    st.dataframe(estilo, hide_index=True, use_container_width=True)

    st.caption("Os modelos foram treinados com os dados de 01/01 a 28/08/2026 e avaliados nas 4 "
               "semanas seguintes. MAE: erro médio, em doses por dia. RMSE: raiz do erro quadrático "
               "médio, que pesa mais os erros grandes. sMAPE: erro percentual. A previsão foi feita "
               "com o modelo de menor RMSE, reajustado com toda a série até 25/09. O Dia D da "
               "Multivacinação (22/08) foi substituído por um sábado típico, para não distorcer os "
               "modelos. As previsões não consideram campanhas futuras nem feriados, como o de 12/10.")