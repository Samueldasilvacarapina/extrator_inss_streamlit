import streamlit as st
import pandas as pd
from extrator import processar_pdf
import tempfile
import os
from io import BytesIO

st.set_page_config(page_title="Extrator INSS", layout="wide")
st.title("📄 Extrator de Histórico de Créditos - INSS")
st.markdown("Envie o PDF e gere uma planilha limpa com RMC (217), RCC (268), SINDICATO. Ordenado por mês e ano corretamente.")

uploaded_file = st.file_uploader("Envie o arquivo PDF do histórico de créditos", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        caminho = tmp_file.name

    with st.spinner("Processando PDF..."):
        dados = processar_pdf(caminho)

    if not dados:
        st.error("Não foi possível extrair dados do PDF.")
    else:
        st.success("Dados extraídos com sucesso!")
        linhas = []
        total_rmc = total_rcc = total_sind = 0.0

        for data, valores in dados.items():
            rmc = valores["RMC"]
            rcc = valores["RCC"]
            sind = valores["SINDICATO"]
            total_rmc += rmc
            total_rcc += rcc
            total_sind += sind
            linhas.append([data, rmc, rcc, sind])

        df = pd.DataFrame(linhas, columns=["Data", "RMC (217)", "RCC (268)", "SINDICATO"])
        st.dataframe(df.style.format({col: "R$ {:,.2f}" for col in df.columns[1:]}), use_container_width=True)

        st.subheader("Totais")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total RMC", f"R$ {total_rmc:,.2f}")
            st.metric("Em Dobro", f"R$ {total_rmc * 2:,.2f}")
        with col2:
            st.metric("Total RCC", f"R$ {total_rcc:,.2f}")
            st.metric("Em Dobro", f"R$ {total_rcc * 2:,.2f}")
        with col3:
            st.metric("Total SINDICATO", f"R$ {total_sind:,.2f}")
            st.metric("Em Dobro", f"R$ {total_sind * 2:,.2f}")

        st.divider()
        st.metric("VALOR DA CAUSA (x2 + R$10.000)", f"R$ {(total_rmc + total_rcc + total_sind)*2 + 10000:,.2f}")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Créditos INSS")
        st.download_button(
            "📥 Baixar Planilha Excel",
            data=output.getvalue(),
            file_name="planilha_inss.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        os.remove(caminho)

