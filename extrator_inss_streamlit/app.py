import streamlit as st
import pandas as pd
from extrator import processar_pdf
import tempfile
import os
from io import BytesIO
from fpdf import FPDF

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
        st.warning("O conteúdo do PDF parece estar em formato de imagem (escaneado). Use um PDF com texto real.")
        st.error("Não foi possível extrair dados do PDF.")
    else:
        df = pd.DataFrame(dados)
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
        df = df.dropna(subset=["Data"])
        df = df.drop_duplicates()
        df["Data"] = df["Data"].dt.strftime("%m/%Y")
        df["Valor Formatado"] = df["Valor"].map(lambda x: f"R$ {x:,.2f}")
        df = df[["Data", "Tipo", "Valor Formatado"]]

        st.success("✅ Dados extraídos com sucesso!")
        st.dataframe(df, use_container_width=True)

        # TOTAIS
        df_raw = pd.DataFrame(dados)
        totais = df_raw.groupby("Tipo")["Valor"].sum()

        st.subheader("Totais por Tipo")
        totais_filtrados = totais[totais > 0]  # remove totais zerados
        resumo = []

        for tipo, total in totais_filtrados.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Total {tipo}", f"R$ {total:,.2f}")
            with col2:
                st.metric("Em Dobro", f"R$ {total * 2:,.2f}")
            with col3:
                st.metric("Com Indenização", f"R$ {total * 2 + 10000:,.2f}")
            resumo.append((tipo, total))

        valor_total = sum([t for _, t in resumo])
        st.divider()
        st.metric("VALOR DA CAUSA (total x2 + R$10.000)", f"R$ {valor_total * 2 + 10000:,.2f}")

        # ANOTAÇÃO
        st.subheader("📝 Anotações Finais")
        anotacao = st.text_area("Escreva anotações que serão incluídas no PDF gerado:", height=150)

        # GERA PDF
        def gerar_pdf(df, resumo, anotacao):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Relatório de Histórico de Créditos - INSS", ln=True, align="C")
            pdf.ln(10)

            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Tabela de Competências:", ln=True)
            pdf.set_font("Arial", "", 10)

            for i, row in df.iterrows():
                linha = f"{row['Data']} - {row['Tipo']} - {row['Valor Formatado']}"
                pdf.cell(0, 8, linha, ln=True)

            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Totais por Tipo:", ln=True)
            pdf.set_font("Arial", "", 10)
            for tipo, total in resumo:
                em_dobro = total * 2
                com_indenizacao = em_dobro + 10000
                linha = f"{tipo}: Total = R$ {total:,.2f} | Em Dobro = R$ {em_dobro:,.2f} | Com Indenização = R$ {com_indenizacao:,.2f}"
                pdf.multi_cell(0, 8, linha)

            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Valor da Causa: R$ {valor_total * 2 + 10000:,.2f}", ln=True)

            if anotacao.strip():
                pdf.ln(10)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Anotações:", ln=True)
                pdf.set_font("Arial", "", 10)
                for linha in anotacao.strip().split("\n"):
                    pdf.multi_cell(0, 8, linha)

            output = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
return BytesIO(pdf_bytes)

            return output.getvalue()

        pdf_bytes = gerar_pdf(df, resumo, anotacao)

        st.download_button(
            label="📄 Baixar Relatório em PDF",
            data=pdf_bytes,
            file_name="relatorio_inss.pdf",
            mime="application/pdf"
        )

        os.remove(caminho)
