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
    col1, col2 = st.columns([2, 1])  # Mantendo layout original

    with col1:
        st.subheader("📊 Gráfico de Produtos Mais Vendidos")
        top_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(y=top_produtos.head(10).index, x=top_produtos.head(10).values, palette="coolwarm", ax=ax)
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=10)
        ax.set_title("Top 10 Produtos Mais Vendidos", fontsize=14, color="white")
        ax.set_xlabel("Quantidade Vendida", fontsize=12, color="white")
        ax.set_ylabel("Aparelho", fontsize=12, color="white")
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("📋 Tabela de Produtos por UF")
        produto_selecionado = st.selectbox(
            "Selecione um produto:",
            entrada["Aparelho"].unique()
        )

        df_produto = entrada[entrada['Aparelho'] == produto_selecionado]

        vendas_por_uf = df_produto.groupby("UF")["SaleQt"].sum().reset_index()

        preco_medio_produto = df_produto['Price'].mean()
        custo_medio_produto = df_produto['Cost'].mean()

        st.write(f"💰 **Preço Médio:** R$ {preco_medio_produto:.2f}")
        st.write(f"📉 **Custo Médio:** R$ {custo_medio_produto:.2f}")

        preco_medio_por_uf = df_produto.groupby('UF')['Price'].mean().reset_index()
        custo_medio_por_uf = df_produto.groupby('UF')['Cost'].mean().reset_index()
        qtd_por_uf = df_produto.groupby('UF')['SaleQt'].sum().reset_index()

        tabela_completa = (
            preco_medio_por_uf
            .merge(custo_medio_por_uf, on='UF', suffixes=('_Preço', '_Custo'))
            .merge(qtd_por_uf, on='UF')
        )

        tabela_completa = tabela_completa.rename(columns={'SaleQt': 'Qty'})
        tabela_completa['SMS%'] = 1 - (tabela_completa['Cost'] / tabela_completa['Price'])
        tabela_completa = tabela_completa.round(2)

        st.write(f"📊 Dados por UF para **{produto_selecionado}**")
        st.dataframe(tabela_completa, height=400)

    # Criar a terceira coluna para exibir a análise de preços ótimos + margem
    col3, _ = st.columns([2, 1])  # Ajuste para melhor distribuição do layout

    with col3:
        st.subheader("🔍 Análise Completa por UF")
        uf_selecionada = st.selectbox("Escolha uma UF para análise:", sorted(entrada["UF"].unique()))

        # Filtrar dados da UF selecionada
        df_uf = entrada[entrada["UF"] == uf_selecionada]

        # Criar tabela base (Agrupamento correto)
        tabela_otimizada = df_uf.groupby("Aparelho").agg(
            Price=("Price", "mean"),
            Cost=("Cost", "mean"),
            Qty=("SaleQt", "sum")
        ).reset_index()

        # Calcular a margem correta: SMS% = 1 - (Cost / Price)
        tabela_otimizada["Margem"] = 1 - (tabela_otimizada["Cost"] / tabela_otimizada["Price"])

        # Adicionar colunas vazias para cálculos de otimização
        tabela_otimizada["Price Optimal"] = np.nan
        tabela_otimizada["New Qty"] = np.nan
        tabela_otimizada["New Revenue"] = np.nan
        tabela_otimizada["Elasticity"] = np.nan

        # Aplicar modelo de regressão para cada produto
        for i, row in tabela_otimizada.iterrows():
            data_produto = df_uf[df_uf["Aparelho"] == row["Aparelho"]]

            if len(data_produto) > 2:
                X = data_produto["Price"].values.reshape(-1, 1)
                y = data_produto["SaleQt"].values.reshape(-1, 1)

                model = LinearRegression()
                model.fit(X, y)

                intercept = model.intercept_[0]
                slope = model.coef_[0][0]

                # Elasticidade e preço ótimo
                mean_price = data_produto["Price"].mean()
                mean_quantity = data_produto["SaleQt"].mean()
                elasticity = (slope * mean_price) / mean_quantity
                price_optimal = -intercept / (2 * slope)

                # Estimar nova quantidade e receita com o preço ótimo
                new_qty = intercept + slope * price_optimal
                new_revenue = new_qty * price_optimal

                tabela_otimizada.at[i, "Price Optimal"] = round(price_optimal, 2)
                tabela_otimizada.at[i, "New Qty"] = round(new_qty, 0)
                tabela_otimizada.at[i, "New Revenue"] = round(new_revenue, 2)
                tabela_otimizada.at[i, "Elasticity"] = round(elasticity, 2)

        st.write(f"📊 Análise de Precificação Ótima e Margem para Produtos na UF **{uf_selecionada}**")
        st.dataframe(tabela_otimizada, height=400)

        # Criar gráfico de bolhas com tooltip correto
        df_bolhas = entrada.groupby("UF").agg(
            Faturamento_Total=("SaleAmt", "sum"),
            Volume_Vendas=("SaleQt", "sum"),
            Margem_Total=("GrossProfitAmt", "sum")
        ).reset_index()

        # Criar lista dos produtos que mais impactaram a margem (ordenados)
        df_bolhas["Produtos"] = entrada.groupby("UF").apply(
            lambda x: ", ".join(
                x.groupby("Aparelho")["SaleQt"].sum().sort_values(ascending=False).head(3).index
            )
        ).reset_index(drop=True)

        fig = px.scatter(
            df_bolhas,
            x="Volume_Vendas",
            y="Faturamento_Total",
            size="Margem_Total",
            text="UF",
            hover_data={"Produtos": True, "Faturamento_Total": ":.2f"},
            title="Faturamento x Volume de Vendas (Tamanho = Margem Total)"
        )

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {e}")
