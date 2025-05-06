import pdfplumber
import re
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path

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
    try:
        return float(valor_str.replace(".", "").replace(",", "."))
    except:
        return None

def extrair_competencia_de_bloco(bloco):
    for linha in bloco:
        match = re.search(r'(\d{2})/(\d{4})', linha)
        if match:
            return f"01/{match.group(1)}/{match.group(2)}"
    return None

def extrair_nome_banco(linha):
    match = re.search(r'(RMC|RCC).*?- ([A-Z0-9 ./]+)', linha)
    return match.group(2).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB.*?|SIND.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def processar_blocos(linhas):
    dados = []
    bloco = []

    for linha in linhas:
        if re.match(r'^\d{2}/\d{4}', linha):
            if bloco:
                dados.extend(extrair_dados_de_bloco(bloco))
                bloco = []
        bloco.append(linha)

    if bloco:
        dados.extend(extrair_dados_de_bloco(bloco))

    return dados

def extrair_dados_de_bloco(bloco):
    resultados = []
    competencia = extrair_competencia_de_bloco(bloco)
    if not competencia:
        return []

    for linha in bloco:
        for tipo, codigo in rubricas_alvo.items():
            if codigo in linha:
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                valor = formatar_valor(valor_match.group(1)) if valor_match else None
                if valor:
                    resultados.append({
                        "Data": competencia,
                        "Tipo": f"{tipo} - {extrair_nome_banco(linha)}",
                        "Valor": valor
                    })

        for tipo, termos in rubricas_textuais.items():
            if any(t in linha.upper() for t in termos):
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                valor = formatar_valor(valor_match.group(1)) if valor_match else None
                if valor:
                    resultados.append({
                        "Data": competencia,
                        "Tipo": f"{tipo} - {extrair_nome_sindicato(linha)}",
                        "Valor": valor
                    })

    return resultados

def extrair_linhas(texto):
    return texto.split("\n")

def processar_pdf(caminho_pdf):
    dados = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = extrair_linhas(texto)
                    dados.extend(processar_blocos(linhas))
    except Exception:
        pass

    if not dados:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem, lang='por')
                linhas = extrair_linhas(texto)
                dados.extend(processar_blocos(linhas))
        except Exception:
            pass

    dados = [d for d in dados if d.get("Valor") not in (None, 0.0)]
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
