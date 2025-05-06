import streamlit as st
import pandas as pd
from extrator import processar_pdf
from fpdf import FPDF
from io import BytesIO
import tempfile
import os
from datetime import datetime

st.set_page_config(page_title="Extrator INSS", layout="wide")
st.title("📄 Extrator de Histórico de Créditos - INSS")
st.markdown("Envie o PDF e veja os valores reais por competência, mês a mês.")

uploaded_file = st.file_uploader("Envie o arquivo PDF do histórico de créditos", type="pdf")

def gerar_pdf(df, resumo, anotacao):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, "Extrato de Créditos INSS", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", 'B', size=10)
    pdf.cell(40, 8, "Data", border=1)
    pdf.cell(90, 8, "Tipo", border=1)
    pdf.cell(40, 8, "Valor", border=1, ln=True)
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(40, 8, row["Data"], border=1)
        pdf.cell(90, 8, row["Tipo"][:40], border=1)
        pdf.cell(40, 8, row["Valor Formatado"], border=1, ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, "Totais por Tipo", ln=True)

    for tipo, total in resumo.items():
        if "SEM DADOS" in tipo:
            continue
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Total {tipo}: R$ {total:,.2f}", ln=True)
        pdf.cell(0, 8, f"Em Dobro: R$ {total * 2:,.2f}", ln=True)
        pdf.cell(0, 8, f"Com Indenização: R$ {total * 2 + 10000:,.2f}", ln=True)
        pdf.ln(2)

    valor_total = sum(valor for tipo, valor in resumo.items() if "SEM DADOS" not in tipo)
    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(0, 10, f"VALOR DA CAUSA (total x2 + R$10.000): R$ {valor_total * 2 + 10000:,.2f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', size=11)
    pdf.cell(0, 10, "Anotações:", ln=True)
    pdf.set_font("Arial", size=10)
    for linha in anotacao.split("\n"):
        pdf.multi_cell(0, 8, linha)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

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
        df["DataRaw"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
        df = df.dropna(subset=["DataRaw"]).drop_duplicates()

        # Filtra apenas entre a menor e maior data com VALOR > 0
        datas_validas = df[df["Valor"] > 0]["DataRaw"]
        data_ini, data_fim = datas_validas.min(), datas_validas.max()
        df = df[(df["DataRaw"] >= data_ini) & (df["DataRaw"] <= data_fim)]

        df["Data"] = df["DataRaw"].dt.strftime("%m/%Y")
        df["Valor Formatado"] = df["Valor"].map(lambda x: f"R$ {x:,.2f}")
        df = df[["Data", "Tipo", "Valor", "Valor Formatado"]]

        st.success("✅ Dados extraídos com sucesso!")
        st.dataframe(df[["Data", "Tipo", "Valor Formatado"]], use_container_width=True)

        totais = df.groupby("Tipo")["Valor"].sum()
        st.subheader("Totais por Tipo")

        for tipo, total in totais.items():
            if "SEM DADOS" in tipo:
                continue
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Total {tipo}", f"R$ {total:,.2f}")
            with col2:
                st.metric("Em Dobro", f"R$ {total * 2:,.2f}")
            with col3:
                st.metric("Com Indenização", f"R$ {total * 2 + 10000:,.2f}")

        valor_total = sum(valor for tipo, valor in totais.items() if "SEM DADOS" not in tipo)
        st.divider()
        st.metric("VALOR DA CAUSA (total x2 + R$10.000)", f"R$ {valor_total * 2 + 10000:,.2f}")

        anotacao = st.text_area("Anotações Finais", height=150)

        pdf_bytes = gerar_pdf(df[["Data", "Tipo", "Valor Formatado"]], totais, anotacao)

        st.download_button(
            "📅 Baixar Relatório PDF",
            data=pdf_bytes.getvalue(),
            file_name="relatorio_inss.pdf",
            mime="application/pdf"
        )

        os.remove(caminho)
