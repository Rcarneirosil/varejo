import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.linear_model import LinearRegression

# Expandir a tela para largura total
st.set_page_config(layout="wide")

# Configuração do fundo escuro
plt.rcParams["figure.facecolor"] = "#0E1117"
plt.rcParams["axes.facecolor"] = "#0E1117"
plt.rcParams["axes.edgecolor"] = "white"
plt.rcParams["axes.labelcolor"] = "white"
plt.rcParams["xtick.color"] = "white"
plt.rcParams["ytick.color"] = "white"
plt.rcParams["text.color"] = "white"
plt.rcParams["legend.edgecolor"] = "white"
plt.rcParams["grid.color"] = "#444444"
plt.rcParams["savefig.facecolor"] = "#0E1117"

# Título do aplicativo
st.title("📊 Análise de Vendas")

# URL do arquivo CSV no GitHub
csv_url = "https://raw.githubusercontent.com/Rcarneirosil/varejo/main/entrada.csv"

# Tentar carregar o arquivo CSV diretamente do GitHub
try:
    entrada = pd.read_csv(csv_url, sep=",", encoding="utf-8")
    entrada.columns = entrada.columns.str.strip()
    st.success("✅ Dados carregados com sucesso!")

    # Criar colunas para organizar o layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Top 3 Produtos Mais Vendidos por UF")

        # Selecionar os 3 produtos mais vendidos
        top_3_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().nlargest(3).index

        # Filtrar apenas esses produtos no dataset
        df_top = entrada[entrada["Aparelho"].isin(top_3_produtos)]

        # Criar gráfico empilhado de vendas por UF
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=df_top,
            x="SaleQt",
            y="Aparelho",
            hue="UF",
            palette="coolwarm",
            estimator=sum,
            ci=None,
            dodge=False,  # 🔥 Deixa as barras empilhadas
            ax=ax
        )

        ax.set_title("Top 3 Produtos Mais Vendidos por UF", fontsize=14, color="white")
        ax.set_xlabel("Quantidade Vendida", fontsize=12, color="white")
        ax.set_ylabel("Aparelho", fontsize=12, color="white")
        plt.legend(title="UF", loc="upper right", fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("📋 Tabela de Produtos por UF")
        produto_selecionado = st.selectbox(
            "Selecione um produto:",
            entrada["Aparelho"].unique()
        )

        df_produto = entrada[entrada['Aparelho'] == produto_selecionado]

        preco_medio_produto = df_produto['Price'].mean()
        custo_medio_produto = df_produto['Cost'].mean()

        st.write(f"💰 **Preço Médio:** R$ {preco_medio_produto:.2f}")
        st.write(f"📉 **Custo Médio:** R$ {custo_medio_produto:.2f}")

        tabela_completa = (
            df_produto.groupby('UF').agg(
                Price=("Price", "mean"),
                Cost=("Cost", "mean"),
                Qty=("SaleQt", "sum")
            )
        ).reset_index()

        tabela_completa['SMS%'] = 1 - (tabela_completa['Cost'] / tabela_completa['Price'])
        tabela_completa = tabela_completa.round(2)

        st.write(f"📊 Dados por UF para **{produto_selecionado}**")
        st.dataframe(tabela_completa, height=400)

    # Criar uma nova linha de colunas para incluir o gráfico de bolhas na col4
    col3, col4 = st.columns([2, 1])

    with col3:
        st.subheader("🔍 Análise Completa por UF")
        uf_selecionada = st.selectbox("Escolha uma UF para análise:", sorted(entrada["UF"].unique()))

        df_uf = entrada[entrada["UF"] == uf_selecionada]

        tabela_otimizada = df_uf.groupby("Aparelho").agg(
            Price=("Price", "mean"),
            Cost=("Cost", "mean"),
            Qty=("SaleQt", "sum"),
            Faturamento_Total=("SaleAmt", "sum"),
            Custo_Total=("SaleCostAmt", "sum")
        ).reset_index()

        tabela_otimizada["Margem"] = 1 - (tabela_otimizada["Custo_Total"] / tabela_otimizada["Faturamento_Total"])

        st.write(f"📊 Análise de Precificação Ótima, Margem e Faturamento para Produtos na UF **{uf_selecionada}**")
        st.dataframe(tabela_otimizada, height=400)

    with col4:
        st.subheader("📈 Margem por UF")

        df_bolhas = entrada.groupby("UF").agg(
            Faturamento_Total=("SaleAmt", "sum"),
            Volume_Vendas=("SaleQt", "sum"),
            Custo_Total=("SaleCostAmt", "sum")
        ).reset_index()

        df_bolhas["Margem_Total"] = 1 - (df_bolhas["Custo_Total"] / df_bolhas["Faturamento_Total"])

        def top_produtos_margem(uf):
            df_uf = entrada[entrada["UF"] == uf]
            top_prod = (
                df_uf.groupby("Aparelho").agg(
                    Faturamento=("SaleAmt", "sum"),
                    Margem=("SaleCostAmt", "sum")
                )
            )
            top_prod["Margem"] = 1 - (top_prod["Margem"] / df_uf.groupby("Aparelho")["SaleAmt"].sum())

            ## **Critério Melhorado**: Ordenamos por impacto total (Margem * Faturamento)
            top_prod["Impacto_Margem"] = top_prod["Margem"] * top_prod["Faturamento"]
            top_prod = top_prod.sort_values("Impacto_Margem", ascending=False).head(3)

            return "<br>".join([f"{prod}: {margem:.2%}" for prod, margem in zip(top_prod.index, top_prod["Margem"])])

        df_bolhas["Produtos"] = df_bolhas["UF"].apply(top_produtos_margem)

        fig = px.scatter(
            df_bolhas,
            x="Volume_Vendas",
            y="Faturamento_Total",
            size="Margem_Total",
            text="UF",
            hover_data={"Produtos": True, "Margem_Total": ":.2%"},
            title="Faturamento x Volume de Vendas",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {e}")
