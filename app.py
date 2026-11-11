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
.cartao .linha {font-size: 0.85rem; color: #374151; margin: 0.35rem 0 0 0;}
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

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(["📊 Visão geral", "🗺️ Vacinação por bairro",
                                              "🧭 Níveis de adesão", "📈 Séries temporais",
                                              "🔎 Explorador de dados", "📚 Metodologia"])

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

    def pct(x):
        return f"{x:.1f}".replace(".", ",") + "%"

    medias = clus.groupby("nivel_adesao")[["inf_0a4", "inf_60a69", "inf_70mais",
                                            "cov_60a69", "cov_70mais"]].mean()
    leitura = {"Baixa": "Menores proporções de vacinados nos cinco indicadores",
               "Intermediária": "Proporções intermediárias nos cinco indicadores",
               "Alta": "Maiores proporções de vacinados nos cinco indicadores"}
    colunas_cartao = st.columns(3)
    for coluna, nivel in zip(colunas_cartao, ["Baixa", "Intermediária", "Alta"]):
        m = medias.loc[nivel]
        n_b = (clus["nivel_adesao"] == nivel).sum()
        coluna.markdown(
            f'<div class="cartao" style="--cor:{CORES_NIVEL[nivel]}">'
            f'<p class="rotulo">{n_b} bairros</p>'
            f'<p class="valor">Adesão {nivel.lower()}</p>'
            f'<p class="detalhe">{leitura[nivel]}</p>'
            f'<p class="linha"><b>Influenza:</b> {pct(m.inf_0a4)} (0 a 4 anos) · '
            f'{pct(m.inf_60a69)} (60 a 69) · {pct(m.inf_70mais)} (70 ou mais)</p>'
            f'<p class="linha"><b>Covid:</b> {pct(m.cov_60a69)} (60 a 69 anos) · '
            f'{pct(m.cov_70mais)} (70 ou mais)</p></div>',
            unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

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
    fig2.update_traces(
    hovertemplate="<b>%{x}</b><br>"
                  "Nível de adesão: %{fullData.name}<br>"
                  "População vacinada (média dos bairros): %{y:.1f}%"
                  "<extra></extra>"
    )
    fig2.update_layout(separators=",.")



    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Valores mínimos e máximos de cada nível")
    st.markdown("Não há limites fixos entre os níveis: o K-Means classifica cada bairro pelo "
                "conjunto dos 5 indicadores, e não por um valor isolado. Por isso, os intervalos "
                "de níveis vizinhos podem se sobrepor.")
    nomes_ind = {"inf_0a4": "Influenza 0 a 4 anos", "inf_60a69": "Influenza 60 a 69 anos",
                 "inf_70mais": "Influenza 70 anos ou mais", "cov_60a69": "Covid 60 a 69 anos",
                 "cov_70mais": "Covid 70 anos ou mais"}
    faixas_niv = pd.DataFrame({"Indicador": list(nomes_ind.values())})
    for nivel in ["Baixa", "Intermediária", "Alta"]:
        sub = clus.loc[clus["nivel_adesao"] == nivel, list(nomes_ind)]
        faixas_niv[f"Adesão {nivel.lower()}"] = [
            f"{pct(sub[c].min())} a {pct(sub[c].max())}" for c in nomes_ind]
    st.dataframe(faixas_niv, hide_index=True, use_container_width=True)
    
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

with aba5:
    cobertura, codigos = carregar_cobertura()
    clus = carregar_clustering()
    pop = pd.read_csv("dados/dim_populacao_bairro.csv").groupby("nm_bairro")["populacao"].sum()

    indicadores_tab = {("Influenza", "0 a 4"): "Influenza 0 a 4 anos (%)",
                       ("Influenza", "60 a 69"): "Influenza 60 a 69 anos (%)",
                       ("Influenza", "70 ou mais"): "Influenza 70 anos ou mais (%)",
                       ("Covid", "60 a 69"): "Covid 60 a 69 anos (%)",
                       ("Covid", "70 ou mais"): "Covid 70 anos ou mais (%)"}

    tab = codigos[["nm_bairro"]].rename(columns={"nm_bairro": "Bairro"})
    tab["População (Censo 2022)"] = tab["Bairro"].map(pop)
    tab["Nível de adesão"] = tab["Bairro"].map(clus.set_index("bairro")["nivel_adesao"])
    tab.loc[tab["Bairro"].isin(EXCLUIDOS), "Nível de adesão"] = "Excluído"
    tab["Nível de adesão"] = tab["Nível de adesão"].fillna("Dados insuficientes")
    for (vac, faixa_i), nome in indicadores_tab.items():
        s = cobertura[(cobertura["vacina"] == vac) &
                      (cobertura["faixa_etaria"] == faixa_i)].set_index("bairro")["cobertura_pct"]
        tab[nome] = tab["Bairro"].map(s)
    tab = tab.sort_values("Bairro")

    colunas_pct = list(indicadores_tab.values())

    c1, c2, c3 = st.columns([2, 2, 1])
    busca = c1.text_input("Buscar bairro")
    niveis = c2.multiselect("Nível de adesão", list(CORES_NIVEL), default=list(CORES_NIVEL))
    ordem = c3.selectbox("Ordenar por", ["Bairro", "População (Censo 2022)"] + colunas_pct)

    filtrada = tab[tab["Nível de adesão"].isin(niveis)]
    if busca:
        filtrada = filtrada[filtrada["Bairro"].str.contains(busca, case=False, na=False)]
    if ordem == "Bairro":
        filtrada = filtrada.sort_values("Bairro")
    else:
        filtrada = filtrada.sort_values(ordem, ascending=False, na_position="last")

    exibir = filtrada.copy()
    exibir["População (Censo 2022)"] = exibir["População (Censo 2022)"].map(
        lambda v: f"{v:,.0f}".replace(",", "."))
    for col in colunas_pct:
        exibir[col] = exibir[col].map(lambda v: "—" if pd.isna(v) else f"{v:.1f}".replace(".", ","))
    st.dataframe(exibir, hide_index=True, use_container_width=True, height=560)

    st.caption(f"{len(filtrada)} de {len(tab)} bairros. —: sem dado, por ter menos de 30 vacinados "
               "na faixa ou por ser bairro excluído por distorção no registro do endereço.")

    st.download_button("Baixar tabela (CSV)",
                       filtrada.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="vacinacao_por_bairro.csv", mime="text/csv")

with aba6:
    esq, dir_ = st.columns(2, gap="large")

    with esq:
        st.subheader("Arquitetura dos dados (camadas Bronze, Silver e Gold)")
        st.markdown("""
- **Bronze:** arquivos mensais brutos do PNI (janeiro a setembro de 2026), processados no Google Colab em partes e filtrados pelo **município de residência** do paciente (Porto Alegre), resultando em 1.156.680 registros.
- **Silver** (`tb_vacinacao_poa_v3`): verificação de duplicidade por documento (nenhuma duplicata encontrada), padronização de tipos, datas e CEPs.
- **Gold:** tabelas agregadas para as análises e para esta interface: série diária de doses, população vacinada por bairro e faixa etária (influenza e covid), indicadores e resultado do agrupamento.
- **Dimensões:** `dim_cep_bairro`, com 10.116 CEPs de Porto Alegre e o bairro de cada um, e `dim_populacao_bairro`, com a população por bairro e faixa etária (IBGE, Censo 2022).

O processamento foi feito no Google BigQuery e no Google Colab. Esta interface lê arquivos exportados das tabelas Gold.
""")

        st.subheader("Ciclo CRISP-DM")
        st.markdown("""
1. **Entendimento do problema:** reunião com a chefia da Unidade de Vigilância Epidemiológica de Porto Alegre, entidade parceira do projeto.
2. **Entendimento e preparação dos dados:** processamento dos arquivos mensais do PNI em partes, filtro por município de residência e atribuição do bairro pelo CEP completo (8 dígitos), disponível em 73% dos registros, com correspondência de 98,9%.
3. **Modelagem:** agrupamento K-Means (K = 3) dos bairros e modelos de séries temporais (modelos de referência, SARIMA e Prophet).
4. **Avaliação:** coeficiente de silhueta e inércia no agrupamento; MAE, RMSE e sMAPE nas séries temporais, em 4 semanas de teste.
5. **Implantação:** esta interface, publicada no Streamlit Community Cloud.
""")

    with dir_:
        st.subheader("Indicadores e critérios")
        st.markdown("""
- **População vacinada (%)** = pessoas vacinadas ao menos uma vez no período ÷ população da faixa etária no bairro (Censo 2022) × 100.
- **Confiabilidade:** só são exibidas estimativas com pelo menos 30 vacinados, critério da Rede Interagencial de Informações para a Saúde (RIPSA).
- **Bairros excluídos (6):** Farroupilha, Praia de Belas, Vila Conceição, Pedra Redonda e Navegantes, onde o CEP da unidade de saúde aparece registrado como residência de muitos pacientes, e Agronomia, onde predomina um CEP geral de avenida que atravessa vários bairros.
- **Agrupamento:** 81 bairros com os 5 indicadores completos (influenza em 0 a 4, 60 a 69 e 70 anos ou mais; covid em 60 a 69 e 70 anos ou mais).
- **Séries temporais:** 7 modelos comparados; o SARIMA(0,1,1)(0,1,1)₇ em escala logarítmica teve o menor erro em 5 das 6 séries.
""")

        st.subheader("Ética e LGPD")
        st.markdown("""
- Uso exclusivo de dados abertos do Ministério da Saúde, publicados conforme a Lei de Acesso à Informação (Lei 12.527/2011).
- Os microdados não identificam os pacientes: o código do paciente é anonimizado na origem.
- Os resultados são apresentados apenas de forma agregada por bairro, e grupos com menos de 30 pessoas não são exibidos, em conformidade com a Lei Geral de Proteção de Dados (Lei 13.709/2018).
""")

        st.subheader("Limitações")
        st.markdown("""
- Dados extraídos em 02/10/2026. O Ministério da Saúde atualiza os arquivos semanalmente, e os valores podem mudar em versões posteriores, sobretudo nas últimas semanas do período.
- O indicador mede a vacinação no período de janeiro a setembro de 2026, e não a cobertura vacinal oficial do calendário.
- A população de referência é a do Censo 2022.
- A atribuição do bairro depende do CEP informado no registro de vacinação.
""")

        st.subheader("Equipe (UNIVESP · PI IV · 2026)")
        st.markdown("""
- Antonio Alexandre Martincues
- Cleber Rodrigues Pereira
- Gabriel Lima de Almeida
- Igor dos Santos Gomes
- Karen Kuniyoshi Nakaoka
- Nina Maria Irma Soares Pinheiro Machado Rodrigues dos Santos
- Patrick Lucas Almeida
- Richard Miranda Pontes

**Tutor:** Henrique Rodrigues Souza Silva
""")