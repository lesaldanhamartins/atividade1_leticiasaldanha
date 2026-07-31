# ==========================
# IMPORTS
# ==========================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from snowflake.snowpark import Session
import datetime


# ==========================
# CONFIGURAÇÃO DA PÁGINA
# ==========================

st.set_page_config(
    page_title="Atividade 1 - Leticia Saldanha Martins",
    layout="wide"
)

# ==========================
# CONEXÃO SNOWFLAKE
# ==========================

connection_parameters = {
    "account": st.secrets["snowflake"]["account"],
    "user": st.secrets["snowflake"]["user"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": "TEST_DB",
    "schema": "PUBLIC",
    "role": st.secrets["snowflake"]["role"],
    "authenticator": "externalbrowser"
}

# ==========================
# DATASET
# ==========================

url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"

# ==========================
# SIDEBAR
# ==========================

st.sidebar.header("Ações")

# --------------------------
# Carregar dados no Snowflake
# --------------------------

if st.sidebar.button("■ Carregar Dados no Snowflake"):

    df = pd.read_csv(url)

    continentes = ["Asia", "Africa", "South America"]

    df_filtrado = df[df["continent"].isin(continentes)]

    session = Session.builder.configs(connection_parameters).create()

    sp_df = session.create_dataframe(df_filtrado)

    sp_df.write.mode("overwrite").save_as_table("DADOS_COVID_FILTRADOS")

    st.success("Dados carregados com sucesso!")

# --------------------------
# Carregar Dashboard
# --------------------------

if st.sidebar.button("■ Carregar Dashboard"):

    session = Session.builder.configs(connection_parameters).create()

    df = session.table("DADOS_COVID_FILTRADOS").to_pandas()

    st.session_state.df = df

# --------------------------
# Verifica se os dados existem
# --------------------------

if "df" not in st.session_state:

    st.info("Clique em 'Carregar Dashboard' para visualizar os dados.")

    st.stop()

df = st.session_state.df

# ==========================
# FILTROS
# ==========================

st.sidebar.header("Filtros")

lista_paises = sorted(df["location"].dropna().unique())

paises = st.sidebar.multiselect(
    "Selecione os países",
    lista_paises,
    default=lista_paises
)

df_filtrado = df[df["location"].isin(paises)]

# ==========================
# KPIs
# ==========================

st.title("Dashboard COVID-19")

col1, col2, col3 = st.columns(3)

total_casos = int(df_filtrado["new_cases"].fillna(0).sum())

total_obitos = int(df_filtrado["total_deaths"].fillna(0).max())

numero_paises = df_filtrado["location"].nunique()

col1.metric("Total de Casos", f"{total_casos:,}")

col2.metric("Total de Óbitos", f"{total_obitos:,}")

col3.metric("Países Analisados", numero_paises)

# ==========================
# ABAS
# ==========================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Evolução de novos casos",
        "Total de óbitos",
        "% Pessoas vacinadas",
        "% Casos",
        "Dados Brutos",
        "Query SQL"
    ]
)

# ==========================
# TAB 1
# ==========================

with tab1:

    fig = px.line(
        df_filtrado,
        x="date",
        y="new_cases_smoothed",
        color="location",
        title="Evolução de novos casos"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================
# TAB 2
# ==========================

with tab2:

    fig = px.bar(
        df_filtrado,
        x="date",
        y="total_deaths",
        color="location",
        title="Total de Óbitos"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================
# TAB 3
# ==========================

with tab3:

    continentes = ["Asia", "Africa", "South America"]

    for continente in continentes:

        df_cont = df_filtrado[df_filtrado["continent"] == continente]

        vacinados = df_cont["people_fully_vaccinated_per_hundred"].mean()

        if pd.isna(vacinados):
            vacinados = 0

        nao_vacinados = max(0, 100 - vacinados)

        df_pizza = pd.DataFrame({
            "Status": ["Vacinados", "Não vacinados"],
            "Percentual": [vacinados, nao_vacinados]
        })

        fig = px.pie(
            df_pizza,
            names="Status",
            values="Percentual",
            title=f"{continente} - Vacinação"
        )

        fig.update_traces(
            textinfo="label+percent",
            marker=dict(colors=["green", "red"])
        )

        st.plotly_chart(fig, use_container_width=True)

# ==========================
# TAB 4
# ==========================

with tab4:

    fig = px.scatter(
        df_filtrado,
        x="date",
        y=df_filtrado["new_cases_smoothed_per_million"] / 10000,
        color="location",
        title="% Casos"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================
# TAB 5
# ==========================

with tab5:

    st.subheader("Dados Brutos")

    st.dataframe(df_filtrado, use_container_width=True)

    csv = df_filtrado.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Exportar CSV",
        data=csv,
        file_name="dados_covid.csv",
        mime="text/csv"
    )

# ==========================
# TAB 6
# ==========================

with tab6:

    st.subheader("Executar Consulta SQL")

    consulta = st.text_area(
        "Digite sua consulta SQL:",
        "SELECT * FROM DADOS_COVID_FILTRADOS LIMIT 10;"
    )

    if st.button("Executar SQL"):

        try:

            session = Session.builder.configs(connection_parameters).create()

            resultado = session.sql(consulta).to_pandas()

            st.success("Consulta executada com sucesso!")

            st.dataframe(resultado, use_container_width=True)

        except Exception as e:

            st.error(f"Erro ao executar consulta:\n\n{e}")
