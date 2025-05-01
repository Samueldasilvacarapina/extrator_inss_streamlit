import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import tempfile
import re

st.set_page_config(page_title="Extrator de Histórico de Créditos - INSS", layout="wide")

st.title("📄 Extrator de Histórico de Créditos - INSS")
st.write("Envie o PDF e veja os valores reais por competência, mês a mês.")

uploaded_file = st.file_uploader("Envie o arquivo PDF do histórico de créditos", type="pdf")

def extrair_texto_ocr(pdf_bytes):
    imagens = convert_from_bytes(pdf_bytes)
    texto_extraido = ""
    for imagem in imagens:
        texto_extraido += pytesseract.image_to_string(imagem, lang='por')
    return texto_extraido

def extrair_dados(texto):
    padrao = r'(\d{2}/\d{4})\s+([\d.,]+)'
    matches = re.findall(padrao, texto)
    resultados = []
    for data, valor in matches:
        valor_limpo = float(valor.replace('.', '').replace(',', '.'))
        resultados.append((data, valor_limpo))
    return resultados

if uploaded_file is not None:
    try:
        # Primeira tentativa: tentar com texto direto
        with pdfplumber.open(uploaded_file) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""

        # Se falhar, usar OCR
        if not texto.strip():
            st.warning("O conteúdo do PDF parece estar em formato de imagem (escaneado). Usando OCR...")
            texto = extrair_texto_ocr(uploaded_file.read())

        dados = extrair_dados(texto)

        if dados:
            st.success("✅ Dados extraídos com sucesso!")
            st.dataframe(dados, use_container_width=True)
        else:
            st.error("Não foi possível extrair dados do PDF.")
    except Exception as e:
        st.error(f"Erro ao processar o PDF: {e}")
