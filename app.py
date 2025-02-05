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
        st.subheader("📊 Gráfico de Produtos Mais Vendidos por UF")

        # 1️⃣ - Calcular o total de vendas por produto (independente da UF)
        total_vendas_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().reset_index()

        # 2️⃣ - Selecionar os Top 10 produtos mais vendidos (ordenados corretamente)
        top_10_produtos = (
            total_vendas_produtos
            .nlargest(10, "SaleQt")  # Pega os 10 maiores
            .sort_values("SaleQt", ascending=True)  # 🔥 Inverter a ordem para gráfico horizontal correto
            ["Aparelho"]
            .tolist()
        )

        # 3️⃣ - Filtrar apenas esses produtos no dataset original
        df_top = entrada[entrada["Aparelho"].isin(top_10_produtos)]

        # 4️⃣ - Criar tabela pivotada para organizar os dados corretamente
        df_pivot = df_top.pivot_table(index="Aparelho", columns="UF", values="SaleQt", aggfunc="sum").fillna(0)

        # 5️⃣ - Garantir que os produtos estejam ordenados corretamente no gráfico
        df_pivot = df_pivot.loc[top_10_produtos]

        # 6️⃣ - Ordenar as UFs da maior para a menor para que a maior fique na BASE das barras
        ufs_ordenadas = df_pivot.sum(axis=0).sort_values(ascending=False).index  # 🔥 UFs com mais vendas primeiro

        # 7️⃣ - Reorganizar a pivot_table para seguir essa ordem de UFs
        df_pivot = df_pivot[ufs_ordenadas]

        # 8️⃣ - Criar gráfico de barras empilhadas
        fig, ax = plt.subplots(figsize=(10, 6))
        df_pivot.plot(kind="barh", stacked=True, colormap="coolwarm", ax=ax)

        # 9️⃣ - Ajustar título e rótulos
        ax.set_title("Top 10 Produtos Mais Vendidos por UF", fontsize=14, color="black")
        ax.set_xlabel("Quantidade Vendida", fontsize=12, color="black")
        ax.set_ylabel("Aparelho", fontsize=12, color="black")

        # 🔟 - Ajustar a legenda dentro do gráfico
        plt.legend(title="UF", loc="lower right", fontsize=10, bbox_to_anchor=(1.0, 0.0))

        # 🔥 Ajustar layout para evitar cortes
        plt.tight_layout()

        # 🔥 Exibir o gráfico no Streamlit
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
    col3, col4 = st.columns([2, 1])  # Mantém proporção equilibrada

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

        tabela_otimizada["Price Optimal"] = np.nan
        tabela_otimizada["New Qty"] = np.nan
        tabela_otimizada["New Revenue"] = np.nan
        tabela_otimizada["Elasticity"] = np.nan

        for i, row in tabela_otimizada.iterrows():
            data_produto = df_uf[df_uf["Aparelho"] == row["Aparelho"]]

            if len(data_produto) > 2:
                X = data_produto["Price"].values.reshape(-1, 1)
                y = data_produto["SaleQt"].values.reshape(-1, 1)

                model = LinearRegression()
                model.fit(X, y)

                intercept = model.intercept_[0]
                slope = model.coef_[0][0]

                mean_price = data_produto["Price"].mean()
                mean_quantity = data_produto["SaleQt"].mean()
                elasticity = (slope * mean_price) / mean_quantity
                price_optimal = -intercept / (2 * slope)

                new_qty = intercept + slope * price_optimal
                new_revenue = new_qty * price_optimal

                tabela_otimizada.at[i, "Price Optimal"] = round(price_optimal, 2)
                tabela_otimizada.at[i, "New Qty"] = round(new_qty, 0)
                tabela_otimizada.at[i, "New Revenue"] = round(new_revenue, 2)
                tabela_otimizada.at[i, "Elasticity"] = round(elasticity, 2)

        st.write(f"📊 Análise de Precificação Ótima, Margem e Faturamento para Produtos na UF **{uf_selecionada}**")
        st.dataframe(tabela_otimizada, height=400)

    # Criar a tabela agregada com faturamento total e custo total por UF
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
            top_prod = top_prod.sort_values("Faturamento", ascending=False).head(3)

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
            height=600  # 🔥 **Ajuste na altura do gráfico**
        )

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {e}")
