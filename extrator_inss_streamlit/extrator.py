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

def extrair_competencia(linha):
    match = re.search(r'(\d{2})/(\d{4})', linha)
    return f"01/{match.group(1)}/{match.group(2)}" if match else None

def extrair_nome_banco(linha):
    match = re.search(r'(RMC|RCC).*?- ([A-Z0-9 ./]+)', linha)
    return match.group(2).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB.*?|SIND.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def extrair_linhas(texto):
    return texto.split("\n")

def processar_linhas(linhas):
    dados = []
    competencia = None

    for linha in linhas:
        nova_comp = extrair_competencia(linha)
        if nova_comp:
            competencia = nova_comp

        for tipo, codigo in rubricas_alvo.items():
            if codigo in linha:
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor_match:
                    valor = formatar_valor(valor_match.group(1))
                    if valor:
                        dados.append({
                            "Data": competencia or "01/01/1900",
                            "Tipo": f"{tipo} - {extrair_nome_banco(linha)}",
                            "Valor": valor
                        })

        for tipo, termos in rubricas_textuais.items():
            if any(p in linha.upper() for p in termos):
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor_match:
                    valor = formatar_valor(valor_match.group(1))
                    if valor:
                        dados.append({
                            "Data": competencia or "01/01/1900",
                            "Tipo": f"{tipo} - {extrair_nome_sindicato(linha)}",
                            "Valor": valor
                        })

    return dados

def processar_pdf(caminho_pdf):
    dados = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = extrair_linhas(texto)
                    dados.extend(processar_linhas(linhas))
    except Exception:
        pass

    if not dados:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem, lang='por')
                linhas = extrair_linhas(texto)
                dados.extend(processar_linhas(linhas))
        except Exception:
            pass

    # Filtra apenas valores reais (não nulos ou zero)
    dados = [d for d in dados if d.get("Valor") not in (None, 0.0)]

    # Ordena do mais antigo pro mais recente
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))

    return dados
