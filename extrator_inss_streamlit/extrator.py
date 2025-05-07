import pdfplumber
import re
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path
import pandas as pd

rubricas_alvo = {
    "RMC": "217",
    "RCC": "268",
}

rubricas_textuais = {
    "Contribuição": [
        "CONTRIB", "CONTRIBUIÇÃO", "CONTRIB.SINDICAL", "SINDICATO", "SIND.", "SINDICAL"
    ]
}

def formatar_valor(valor_str):
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_competencia_periodo(linhas):
    for linha in linhas:
        match = re.search(r'(\d{2})/(\d{4})\s*a\s*(\d{2})/(\d{4})', linha)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None

def extrair_linhas(texto):
    return texto.split("\n")

def processar_linhas(linhas):
    dados = []
    competencia = extrair_competencia_periodo(linhas)

    for linha in linhas:
        for tipo, codigo in rubricas_alvo.items():
            if re.search(rf'\b{codigo}\b', linha):
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor_match and competencia:
                    dados.append({
                        "Data": competencia,
                        "Tipo": tipo,
                        "Valor": formatar_valor(valor_match.group(1))
                    })

        for tipo, termos in rubricas_textuais.items():
            if any(term in linha.upper() for term in termos):
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor_match and competencia:
                    dados.append({
                        "Data": competencia,
                        "Tipo": tipo,
                        "Valor": formatar_valor(valor_match.group(1))
                    })

    return dados

def processar_pdf(caminho_pdf):
    dados_extraidos = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = extrair_linhas(texto)
                    dados_extraidos.extend(processar_linhas(linhas))
    except Exception:
        pass

    if not dados_extraidos:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem, lang='por')
                linhas = extrair_linhas(texto)
                dados_extraidos.extend(processar_linhas(linhas))
        except Exception:
            pass

    # Organizar os dados em colunas: Data | RMC | RCC | Contribuição
    df = pd.DataFrame(dados_extraidos)
    tabela_pivotada = df.pivot_table(
        index="Data",
        columns="Tipo",
        values="Valor",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    # Ordena as datas corretamente no formato mês/ano
    tabela_pivotada["Data"] = pd.to_datetime(tabela_pivotada["Data"], format="%m/%Y")
    tabela_pivotada = tabela_pivotada.sort_values("Data")
    tabela_pivotada["Data"] = tabela_pivotada["Data"].dt.strftime("%m/%Y")

    return tabela_pivotada
