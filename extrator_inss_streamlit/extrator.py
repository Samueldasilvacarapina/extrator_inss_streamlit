import pdfplumber
from datetime import datetime
import re

def extrair_dados_linhas(linhas):
    dados_extraidos = []
    padrao_data = r"\b\d{2}/\d{2}/\d{4}\b"
    padrao_valor = r"R?\$?\s?[\d\.,]+"

    for linha in linhas:
        if any(rubrica in linha for rubrica in ["217", "268", "SIND"]):
            data_match = re.search(padrao_data, linha)
            valor_match = re.findall(padrao_valor, linha)

            if data_match and valor_match:
                data = data_match.group()
                valor = valor_match[-1]
                valor = float(valor.replace("R$", "").replace(".", "").replace(",", ".").strip())

                if "217" in linha:
                    tipo = "RMC"
                elif "268" in linha:
                    tipo = "RCC"
                elif "SIND" in linha:
                    tipo = "SINDICAL"
                else:
                    tipo = "DESCONHECIDO"

                dados_extraidos.append({
                    "Data": data,
                    "Valor": valor,
                    "Tipo": tipo
                })

    return dados_extraidos

def processar_pdf(caminho_pdf):
    dados = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if not texto:
                    continue
                linhas = texto.split("\n")
                dados.extend(extrair_dados_linhas(linhas))
    except Exception as e:
        import streamlit as st
        st.error("Erro ao ler o PDF. Verifique se o arquivo está corrompido ou é uma imagem.")
        return []

    if not dados:
        import streamlit as st
        st.warning("O conteúdo do PDF parece estar em formato de imagem (escaneado). Use um PDF com texto real para extração correta.")
        return []

    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
