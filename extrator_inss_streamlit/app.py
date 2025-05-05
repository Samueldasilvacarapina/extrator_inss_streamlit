import streamlit as st
import pandas as pd
from extrator import processar_pdf

st.set_page_config(page_title="Extrator de Créditos INSS", layout="wide")

st.title("📄 Extrator de Créditos do INSS")

arquivo_pdf = st.file_uploader("Faça upload do PDF do histórico de créditos", type=["pdf"])

if arquivo_pdf is not None:
    with st.spinner("Processando o PDF..."):
        dados_extraidos = processar_pdf(arquivo_pdf)

        if not dados_extraidos:
            st.error("❌ Não foi possível extrair dados do PDF.")
        else:
            # Converte os dados para DataFrame
            df = pd.DataFrame(dados_extraidos)

            # Remove linhas com valor 0 ("SEM DADOS")
            df = df[df['Valor'] > 0]

            # Garante que a coluna 'Data' está em datetime
            df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')

            # Filtra os tipos relevantes
            df = df[df['Tipo'].str.contains('RMC|RCC|SINDICATO', case=False, na=False)]

            # Agrupa por mês/ano (competência) e soma os valores
            df_grouped = df.groupby(df['Data'].dt.to_period('M')).agg({'Valor': 'sum'}).reset_index()

            # Converte para datetime e ordena
            df_grouped['Data'] = df_grouped['Data'].dt.to_timestamp()
            df_grouped = df_grouped.sort_values(by='Data')

            # Formata data para exibição
            df_grouped['Competência'] = df_grouped['Data'].dt.strftime('%m/%Y')
            df_grouped = df_grouped[['Competência', 'Valor']]

            st.success("✅ Dados extraídos com sucesso!")

            st.subheader("💰 Descontos por Competência")
            st.dataframe(df_grouped, use_container_width=True)

            # Botão para exportar
            csv = df_grouped.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar como CSV", data=csv, file_name="descontos_por_mes.csv", mime="text/csv")
