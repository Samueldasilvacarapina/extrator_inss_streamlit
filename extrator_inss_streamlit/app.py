
import streamlit as st
import pandas as pd
from extrator import processar_pdf, indenizacao_fixa
import tempfile
import os

st.set_page_config(page_title="Extrator INSS", layout="wide")
st.title("📄 Extrator de Histórico de Créditos - INSS")
st.markdown("Faça upload do PDF do INSS e gere uma planilha completa com RMC, RCC, SINDICATO, salário bruto, descontos, e cálculo do valor da causa.")

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
        total_rmc = total_rcc = total_sind = total_bruto = total_desc = total_liq = 0.0

        for data in sorted(dados):
            linha = dados[data]
            rmc = linha['RMC']
            rcc = linha['RCC']
            sind = linha['SINDICATO']
            bruto = linha['SALARIO_BRUTO']
            descontos = linha['DESCONTOS']
            liquido = linha['LIQUIDO']

            total_rmc += rmc
            total_rcc += rcc
            total_sind += sind
            total_bruto += bruto
            total_desc += descontos
            total_liq += liquido

            linhas.append([data, rmc, rcc, sind, bruto, descontos, liquido])

        df = pd.DataFrame(linhas, columns=[
            "Data", "RMC (217)", "RCC (268)", "SINDICATO", "Bruto (101)", "Descontos", "Líquido"
        ])
        st.dataframe(df.style.format({col: "R$ {:,.2f}" for col in df.columns[1:]}), use_container_width=True)


        st.subheader("Totais e Cálculo Final")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total RMC", f"R$ {total_rmc:,.2f}")
            st.metric("Em Dobro", f"R$ {total_rmc * 2:,.2f}")
            st.metric("Valor da Causa", f"R$ {total_rmc * 2 + indenizacao_fixa:,.2f}")
        with col2:
            st.metric("Total RCC", f"R$ {total_rcc:,.2f}")
            st.metric("Em Dobro", f"R$ {total_rcc * 2:,.2f}")
            st.metric("Valor da Causa", f"R$ {total_rcc * 2 + indenizacao_fixa:,.2f}")
        with col3:
            st.metric("Total SINDICATO", f"R$ {total_sind:,.2f}")
            st.metric("Em Dobro", f"R$ {total_sind * 2:,.2f}")
            st.metric("Valor da Causa", f"R$ {total_sind * 2 + indenizacao_fixa:,.2f}")

        st.divider()
        st.metric("TOTAL BRUTO", f"R$ {total_bruto:,.2f}")
        st.metric("TOTAL DESCONTOS", f"R$ {total_desc:,.2f}")
        st.metric("SALÁRIO LÍQUIDO", f"R$ {total_liq:,.2f}")

        st.download_button(
            "📥 Baixar Planilha Excel",
            data=df.to_excel(index=False, engine='openpyxl'),
            file_name="planilha_inss.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        os.remove(caminho)
