import pdfplumber
import re
from datetime import datetime
from pdf2image import convert_from_path
import pytesseract

rubricas_alvo = {
    "RMC": "217",
    "RCC": "268",
}

rubricas_textuais = {
    "SINDICATO": [
        "CONTRIB", "CONTRIBUIÇÃO", "CONTRIB.SINDICAL", "SINDICATO", "SIND.", "SINDICAL"
    ]
}

def formatar_valor(valor_str):
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_competencia_periodo(linha):
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})\s*a\s*(\d{2})/(\d{2})/(\d{4})', linha)
    if match:
        return f"01/{match.group(2)}/{match.group(3)}"
    return None

def extrair_nome_banco(linha):
    match = re.search(r'(RMC|RCC).*?- ([A-Z0-9 ./]+)', linha)
    return match.group(2).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB\.?.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def extrair_dados_linhas(linhas):
    dados = []
    competencia_atual = None

    for linha in linhas:
        nova_data = extrair_competencia_periodo(linha)
        if nova_data:
            competencia_atual = nova_data

        if not competencia_atual:
            continue

        for chave, codigo in rubricas_alvo.items():
            if codigo in linha:
                valor = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor:
                    dados.append({
                        "Data": competencia_atual,
                        "Tipo": f"{chave} - {extrair_nome_banco(linha)}",
                        "Valor": formatar_valor(valor.group(1))
                    })

        for chave, palavras in rubricas_textuais.items():
            if any(p in linha.upper() for p in palavras):
                valor = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor:
                    dados.append({
                        "Data": competencia_atual,
                        "Tipo": f"{chave} - {extrair_nome_sindicato(linha)}",
                        "Valor": formatar_valor(valor.group(1))
                    })

    return dados

def processar_pdf(caminho_pdf, debug=False):
    dados = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if not texto:
                    continue
                linhas = texto.split("\n")
                dados.extend(extrair_dados_linhas(linhas))
    except:
        pass

    if not dados:
        imagens = convert_from_path(caminho_pdf)
        for imagem in imagens:
            texto = pytesseract.image_to_string(imagem, lang='por')
            linhas = texto.split("\n")
            dados.extend(extrair_dados_linhas(linhas))

    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
