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
        st.error("Nenhum dado foi extraído do PDF.")
    else:
        df = pd.DataFrame(dados)
        df["Valor"] = df["Valor"].astype(float)
        df = df.sort_values("Data")

        # 🧩 PIVOTAR: transformar 'Tipo' em colunas
        tabela = df.pivot_table(index="Data", columns="Tipo", values="Valor", aggfunc="sum").fillna(0)
        tabela = tabela.reset_index()

        # Renomear colunas para manter padrão
        tabela = tabela.rename(columns={
            "RMC": "RMC (217)",
            "RCC": "RCC (268)",
            "SINDICATO": "SINDICATO"
        })

        # Mostrar a tabela formatada
        for col in ["RMC (217)", "RCC (268)", "SINDICATO"]:
            if col not in tabela.columns:
                tabela[col] = 0.0

        tabela = tabela[["Data", "RMC (217)", "RCC (268)", "SINDICATO"]]

        # Formatar valores com R$
        tabela_formatada = tabela.copy()
        for col in ["RMC (217)", "RCC (268)", "SINDICATO"]:
            tabela_formatada[col] = tabela_formatada[col].map(lambda x: f"R$ {x:,.2f}")

        st.success("Dados extraídos com sucesso!")
        st.dataframe(tabela_formatada, use_container_width=True)

        # 🧮 Totais
        st.subheader("Totais por Tipo")
        col1, col2, col3 = st.columns(3)
        total_rmc = tabela["RMC (217)"].sum()
        total_rcc = tabela["RCC (268)"].sum()
        total_sind = tabela["SINDICATO"].sum()

        with col1:
            st.metric("Total RMC", f"R$ {total_rmc:,.2f}")
            st.metric("Em Dobro", f"R$ {total_rmc * 2:,.2f}")
            st.metric("Valor da Causa", f"R$ {total_rmc * 2 + 10000:,.2f}")
        with col2:
            st.metric("Total RCC", f"R$ {total_rcc:,.2f}")
            st.metric("Em Dobro", f"R$ {total_rcc * 2:,.2f}")
            st.metric("Valor da Causa", f"R$ {total_rcc * 2 + 10000:,.2f}")
        with col3:
            st.metric("Total SINDICATO", f"R$ {total_sind:,.2f}")
            st.metric("Em Dobro", f"R$ {total_sind * 2:,.2f}")
            st.metric("Valor da Causa", f"R$ {total_sind * 2 + 10000:,.2f}")

        # Excel para download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            tabela.to_excel(writer, index=False, sheet_name="Créditos INSS")

        st.download_button(
            "📥 Baixar Planilha Excel",
            data=output.getvalue(),
            file_name="planilha_creditos_inss.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        os.remove(caminho)
