# ==========================
# IMPORTS
# ==========================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

from snowflake.snowpark import Session


# ==========================
# CONFIGURAÇÃO DA PÁGINA
# ==========================

st.set_page_config(
    page_title="Atividade 1 - Leticia Saldanha Martins",
    layout="wide"
)


# ==========================
# CONSTANTES SNOWFLAKE
# ==========================

TABELA_COVID = "TEST_DB.PUBLIC.DADOS_COVID_FILTRADOS"


# ==========================
# CONEXÃO SNOWFLAKE
# ==========================

connection_parameters = {

    "account": st.secrets["snowflake"]["account"],
    "password": st.secrets["snowflake"]["password"],
    "user": st.secrets["snowflake"]["user"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": st.secrets["snowflake"]["database"],
    "schema": st.secrets["snowflake"]["schema"],
    "role": st.secrets["snowflake"]["role"]

}


def criar_sessao():

    return Session.builder.configs(
        connection_parameters
    ).create()



# ==========================
# DATASET
# ==========================

url = (
    "https://raw.githubusercontent.com/"
    "owid/covid-19-data/master/public/data/"
    "owid-covid-data.csv"
)



# ==========================
# SIDEBAR
# ==========================

st.sidebar.header("Ações")



# ==========================
# CARREGAR DADOS NO SNOWFLAKE
# ==========================

if st.sidebar.button("■ Carregar Dados no Snowflake"):

    try:

        with st.spinner(
            "Baixando e enviando dados para o Snowflake..."
        ):

            df = pd.read_csv(url)


            continentes = [
                "Asia",
                "Africa",
                "South America"
            ]


            df_filtrado = (
                df[
                    df["continent"].isin(continentes)
                ]
                .reset_index(drop=True)
            )


            session = criar_sessao()


            sp_df = session.create_dataframe(
                df_filtrado
            )

            
            sp_df.write.mode(
                "overwrite"
            ).save_as_table(
                "TEST_DB.PUBLIC.DADOS_COVID_FILTRADOS"
            )


            session.close()


        st.success(
            "Dados carregados com sucesso no Snowflake!"
        )


    except Exception as e:

        st.error(
            f"Erro ao carregar dados:\n\n{e}"
        )

# ==========================
# CARREGAR DASHBOARD
# ==========================

if st.sidebar.button("■ Carregar Dashboard"):

    try:

        session = criar_sessao()


        # Verifica se a tabela existe antes de tentar carregar

        tabelas = session.sql(
            "SHOW TABLES LIKE 'DADOS_COVID_FILTRADOS' IN SCHEMA TEST_DB.PUBLIC"
        ).collect()


        if len(tabelas) == 0:

            st.warning(
                "A tabela ainda não existe. "
                "Clique primeiro em 'Carregar Dados no Snowflake'."
            )

            session.close()

            st.stop()



        df = session.table(
            TABELA_COVID
        ).to_pandas()


        session.close()


        st.session_state.df = df


        st.success(
            "Dashboard carregado com sucesso!"
        )


    except Exception as e:

        st.error(
            f"Erro ao carregar dashboard:\n\n{e}"
        )



# ==========================
# VERIFICAÇÃO DO DATAFRAME
# ==========================

if "df" not in st.session_state:

    st.info(
        "Clique em 'Carregar Dados no Snowflake' "
        "e depois em 'Carregar Dashboard'."
    )

    st.stop()



df = st.session_state.df



# ==========================
# FILTROS
# ==========================

st.sidebar.header("Filtros")


lista_paises = sorted(
    df["location"]
    .dropna()
    .unique()
)


paises_padrao = [
    "Brazil",
    "India",
    "Japan"
]

paises = st.sidebar.multiselect(
    "Selecione os países",
    lista_paises,
    default=paises_padrao
)


df_filtrado = df[
    df["location"].isin(paises)
]



# ==========================
# KPIs
# ==========================

st.title(
    "Dashboard COVID-19"
)


col1, col2, col3 = st.columns(3)



total_casos = int(
    df_filtrado["new_cases"]
    .fillna(0)
    .sum()
)


total_obitos = int(
    df_filtrado["total_deaths"]
    .fillna(0)
    .max()
)


numero_paises = (
    df_filtrado["location"]
    .nunique()
)



col1.metric(
    "Total de Casos",
    f"{total_casos:,}"
)


col2.metric(
    "Total de Óbitos",
    f"{total_obitos:,}"
)


col3.metric(
    "Países Analisados",
    numero_paises
)



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


    st.plotly_chart(
        fig,
        use_container_width=True
    )



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


    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================
# TAB 3
# ==========================

with tab3:

    continentes = [
        "Asia",
        "Africa",
        "South America"
    ]


    for continente in continentes:


        df_cont = df_filtrado[
            df_filtrado["continent"] == continente
        ].copy()


        # Remove valores vazios
        df_cont = df_cont.dropna(
            subset=[
                "people_fully_vaccinated_per_hundred"
            ]
        )


        if len(df_cont) == 0:

            st.warning(
                f"Não existem dados de vacinação para {continente}"
            )

            continue


        # Pega o último valor disponível de cada país
        ultimo_valor = (
            df_cont
            .sort_values("date")
            .groupby("location")
            .tail(1)
        )


        vacinados = (
            ultimo_valor[
                "people_fully_vaccinated_per_hundred"
            ]
            .mean()
        )


        vacinados = round(
            vacinados,
            2
        )


        nao_vacinados = round(
            100 - vacinados,
            2
        )


        df_pizza = pd.DataFrame({

            "Status": [
                "Vacinados",
                "Não vacinados"
            ],

            "Percentual": [
                vacinados,
                nao_vacinados
            ]

        })


        fig = px.pie(

            df_pizza,

            names="Status",

            values="Percentual",

            title=f"{continente} - Vacinação"

        )


        fig.update_traces(

            textinfo="label+percent",

            marker=dict(
                colors=[
                    "green",
                    "red"
                ]
            )

        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ==========================
# TAB 4
# ==========================

with tab4:


    fig = px.scatter(

        df_filtrado,

        x="date",

        y=(
            df_filtrado[
                "new_cases_smoothed_per_million"
            ] / 10000
        ),

        color="location",

        title="% Casos"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )



# ==========================
# TAB 5
# ==========================

with tab5:


    st.subheader(
        "Dados Brutos"
    )


    st.dataframe(

        df_filtrado,

        use_container_width=True

    )


    csv = (
        df_filtrado
        .to_csv(index=False)
        .encode("utf-8")
    )


    st.download_button(

        label="📥 Exportar CSV",

        data=csv,

        file_name="dados_covid.csv",

        mime="text/csv"

    )



# ==========================
# TAB 6 - CONSULTA SQL
# ==========================

with tab6:


    st.subheader(
        "Executar Consulta SQL"
    )


    consulta = st.text_area(

        "Digite sua consulta SQL:",

        f"SELECT * FROM {TABELA_COVID} LIMIT 10;"

    )


    if st.button(
        "Executar SQL"
    ):


        try:


            session = criar_sessao()


            resultado = (
                session
                .sql(consulta)
                .to_pandas()
            )


            session.close()


            st.success(
                "Consulta executada com sucesso!"
            )


            st.dataframe(

                resultado,

                use_container_width=True

            )


        except Exception as e:


            st.error(

                f"Erro ao executar consulta SQL:\n\n{e}"

            )
