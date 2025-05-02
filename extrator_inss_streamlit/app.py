import streamlit as st
import pandas as pd
from extrator import processar_pdf
import tempfile
import os
from io import BytesIO

st.set_page_config(page_title="Extrator INSS", layout="wide")
st.title("📄 Extrator de Histórico de Créditos - INSS")
st.markdown("Envie o PDF e veja os valores reais por competência, mês a mês.")

uploaded_file = st.file_uploader("Envie o arquivo PDF do histórico de créditos", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        caminho = tmp_file.name

    with st.spinner("Processando PDF..."):
        dados = processar_pdf(caminho)

    if not dados:
        st.warning("O conteúdo do PDF parece estar em formato de imagem (escaneado). Use um PDF com texto real para extração correta.")
        st.error("Não foi possível extrair dados do PDF.")
    else:
        df = pd.DataFrame(dados)
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
        df = df.dropna(subset=["Data"])
        df = df.sort_values("Data")
        df["Data"] = df["Data"].dt.strftime("%m/%Y")
        df["Valor Formatado"] = df["Valor"].map(lambda x: f"R$ {x:,.2f}")
        df = df[["Data", "Tipo", "Valor Formatado"]]

        st.success("✅ Dados extraídos com sucesso!")
        st.dataframe(df, use_container_width=True)

        df_raw = pd.DataFrame(dados)
        totais = df_raw.groupby("Tipo")["Valor"].sum()

        st.subheader("Totais por Tipo")
        for tipo, total in totais.items():
            if "SEM DADOS" in tipo:
                continue  # não mostrar totais de SEM DADOS
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Total {tipo}", f"R$ {total:,.2f}")
            with col2:
                st.metric("Em Dobro", f"R$ {total * 2:,.2f}")
            with col3:
                st.metric("Com Indenização", f"R$ {total * 2 + 10000:,.2f}")

        total_geral = totais[[k for k in totais.index if "SEM DADOS" not in k]].sum()
        st.divider()
        st.metric("VALOR DA CAUSA (total x2 + R$10.000)", f"R$ {total_geral * 2 + 10000:,.2f}")

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
