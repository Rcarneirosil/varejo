import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
st.title("📊 Análise de Vendas de Produtos")

# Carregar o arquivo CSV
uploaded_file = st.file_uploader("Carregue o arquivo 'entrada.csv'", type="csv")

if uploaded_file is not None:
    entrada = pd.read_csv(uploaded_file)

    #%% TOP SELLING PRODUCTS BASED ON TOTAL SALES QUANTITY
    st.header("Top 10 Produtos Mais Vendidos")

    # Somar a quantidade total vendida por produto
    top_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().sort_values(ascending=False)

    # Criar colunas para dividir a visualização
    col1, col2 = st.columns([2, 1])  # Mais espaço para o gráfico

    with col1:
        st.subheader("📊 Gráfico de Produtos Mais Vendidos")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=top_produtos.head(10).index, y=top_produtos.head(10).values, palette="coolwarm", ax=ax)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10)
        ax.set_title("Top 10 Produtos Mais Vendidos", fontsize=14, color="white")
        ax.set_xlabel("Aparelho", fontsize=12, color="white")
        ax.set_ylabel("Quantidade Vendida", fontsize=12, color="white")
        plt.tight_layout()
        st.pyplot(fig)

    #%% Análise de um produto específico
    st.header("🔍 Análise de um Produto Específico")

    # Criar colunas para dispor o gráfico ao lado da tabela do produto selecionado
    col3, col4 = st.columns([1.5, 1])  # Mais espaço para o gráfico

    with col3:
        # Selecionar o produto desejado
        produto_selecionado = st.selectbox(
            "Selecione um produto:",
            entrada["Aparelho"].unique()
        )

        # Filtrar o DataFrame para o produto selecionado
        df_produto = entrada[entrada['Aparelho'] == produto_selecionado]

        # Criar gráfico de vendas do produto por UF
        vendas_por_uf = df_produto.groupby("UF")["SaleQt"].sum().reset_index()

        st.subheader(f"📊 Vendas do Produto '{produto_selecionado}' por Estado")
        fig_prod, ax_prod = plt.subplots(figsize=(8, 5))
        sns.barplot(x=vendas_por_uf["UF"], y=vendas_por_uf["SaleQt"], palette="coolwarm", ax=ax_prod)
        ax_prod.set_title(f"Vendas por Estado - {produto_selecionado}", fontsize=14, color="white")
        ax_prod.set_xlabel("Estado", fontsize=12, color="white")
        ax_prod.set_ylabel("Quantidade Vendida", fontsize=12, color="white")
        plt.tight_layout()
        st.pyplot(fig_prod)

    with col4:
        # Calcular o preço médio e o custo médio do produto
        preco_medio_produto = df_produto['Price'].mean()
        custo_medio_produto = df_produto['Cost'].mean()

        st.subheader(f"📋 Dados de {produto_selecionado}")
        st.write(f"💰 **Preço Médio:** R$ {preco_medio_produto:.2f}")
        st.write(f"📉 **Custo Médio:** R$ {custo_medio_produto:.2f}")

        # Calcular o preço médio, custo médio e quantidade vendida por UF
        preco_medio_por_uf = df_produto.groupby('UF')['Price'].mean().reset_index()
        custo_medio_por_uf = df_produto.groupby('UF')['Cost'].mean().reset_index()
        qtd_por_uf = df_produto.groupby('UF')['SaleQt'].sum().reset_index()

        # Combinar os DataFrames de preço, custo e quantidade por UF
        tabela_completa = (
            preco_medio_por_uf
            .merge(custo_medio_por_uf, on='UF', suffixes=('_Preço', '_Custo'))
            .merge(qtd_por_uf, on='UF')
        )

        # Renomear coluna SaleQt para Qty
        tabela_completa = tabela_completa.rename(columns={'SaleQt': 'Qty'})

        # Calcular a margem de estoque SMS%
        tabela_completa['SMS%'] = 1 - (tabela_completa['Cost'] / tabela_completa['Price'])

        # Formatar a tabela para exibir valores com duas casas decimais
        tabela_completa = tabela_completa.round(2)

        # Exibir a tabela completa
        st.write(f"📊 Dados por UF para **{produto_selecionado}**")
        st.dataframe(tabela_completa, height=400)

else:
    st.warning("🚨 Por favor, carregue o arquivo 'entrada.csv' para continuar.")
