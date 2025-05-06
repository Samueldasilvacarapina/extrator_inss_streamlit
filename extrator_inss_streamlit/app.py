import streamlit as st
import pandas as pd
from extrator import processar_pdf
from io import BytesIO

st.set_page_config(page_title="Extrator de Descontos", layout="centered")
st.title("📄 Extrator de Descontos em PDF")

uploaded_file = st.file_uploader("Faça upload do extrato de crédito em PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner("Processando o arquivo..."):
        dados = processar_pdf(uploaded_file)

    if dados:
        df = pd.DataFrame(dados)

        st.success("Arquivo processado com sucesso!")
        st.subheader("💳 Descontos Encontrados")
        st.dataframe(df, use_container_width=True)

        # Download do CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar como CSV",
            data=csv,
            file_name="descontos_extraidos.csv",
            mime="text/csv",
        )
    else:
        st.warning("Nenhum desconto foi encontrado no PDF enviado.")
