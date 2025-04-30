import streamlit as st
import pandas as pd
from extrator import processar_pdf
import tempfile
import os
from io import BytesIO

st.set_page_config(page_title="Extrator INSS", layout="wide")
st.title("📄 Extrator de Histórico de Créditos - INSS")
st.markdown("Envie o PDF e veja os valores reais por competência sem agrupamento.")

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
        st.success("Dados extraídos com sucesso!")
        st.dataframe(df.style.format({"Valor": "R$ {:,.2f}"}), use_container_width=True)

        totais = df.groupby("Tipo")["Valor"].sum()
        st.subheader("Totais por Tipo")
        for tipo, total in totais.items():
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"Total {tipo}", f"R$ {total:,.2f}")
            with col2:
                st.metric("Em Dobro", f"R$ {total * 2:,.2f}")

        valor_total = totais.sum()
        st.divider()
        st.metric("VALOR DA CAUSA (total x2 + R$10.000)", f"R$ {valor_total * 2 + 10000:,.2f}")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Detalhado")
        st.download_button(
            "📥 Baixar Planilha Excel",
            data=output.getvalue(),
            file_name="planilha_detalhada_inss.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        os.remove(caminho)
