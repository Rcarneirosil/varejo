import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import matplotlib.pyplot as plt

# Configurar fundo escuro e textos claros
plt.rcParams["figure.facecolor"] = "#0E1117"  # Fundo dos gráficos
plt.rcParams["axes.facecolor"] = "#0E1117"  # Fundo dos eixos
plt.rcParams["axes.edgecolor"] = "white"  # Cor das bordas do gráfico
plt.rcParams["axes.labelcolor"] = "white"  # Cor dos rótulos dos eixos
plt.rcParams["xtick.color"] = "white"  # Cor dos ticks do eixo X
plt.rcParams["ytick.color"] = "white"  # Cor dos ticks do eixo Y
plt.rcParams["text.color"] = "white"  # Cor do texto dentro dos gráficos
plt.rcParams["legend.edgecolor"] = "white"  # Cor da borda da legenda
plt.rcParams["grid.color"] = "#444444"  # Cor da grade (opcional, cinza escuro)
plt.rcParams["savefig.facecolor"] = "#0E1117"  # Fundo ao salvar imagens


# Título do aplicativo
st.title("Análise de Vendas de Produtos")

# Carregar o arquivo CSV
uploaded_file = st.file_uploader("Carregue o arquivo 'entrada.csv'", type="csv")
if uploaded_file is not None:
    entrada = pd.read_csv(uploaded_file)

    #%% TOP SELLING PRODUCTS BASED ON TOTAL SALES QUANTITY
    st.header("Top 10 Produtos Mais Vendidos (por quantidade total)")

    # Somar a quantidade total vendida por produto
    top_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().sort_values(ascending=False)

    # Exibir os 10 produtos mais vendidos
    st.write(top_produtos.head(10))

    # Visualização gráfica dos 10 mais vendidos
    plt.figure(figsize=(14, 8))
    sns.barplot(x=top_produtos.head(10).index, y=top_produtos.head(10).values, palette="coolwarm")
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.title("Top 10 Produtos Mais Vendidos (por Quantidade Total)", fontsize=16)
    plt.xlabel("Aparelho", fontsize=14)
    plt.ylabel("Quantidade Vendida", fontsize=14)
    plt.tight_layout()
    st.pyplot(plt)

    #%% Análise de um produto específico
    st.header("Análise de um Produto Específico")

    # Selecionar o produto desejado
    produto_selecionado = st.selectbox(
        "Selecione um produto:",
        entrada["Aparelho"].unique()
    )

    # Filtrar o DataFrame para o produto selecionado
    df_produto = entrada[entrada['Aparelho'] == produto_selecionado]

    # Calcular o preço médio e o custo médio do produto
    preco_medio_produto = df_produto['Price'].mean()
    custo_medio_produto = df_produto['Cost'].mean()

    st.write(f"Preço Médio do Produto '{produto_selecionado}': R$ {preco_medio_produto:.2f}")
    st.write(f"Custo Médio do Produto '{produto_selecionado}': R$ {custo_medio_produto:.2f}")

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
    st.write(f"Preço, Custo e Margem de Estoque (SMS%) do Produto '{produto_selecionado}' por UF:")
    st.dataframe(tabela_completa)

else:
    st.warning("Por favor, carregue o arquivo 'entrada.csv' para continuar.")
