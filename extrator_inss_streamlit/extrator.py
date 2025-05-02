import pdfplumber
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
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
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_competencia(linha):
    match = re.search(r'(\d{2})/(\d{4})', linha)
    return f"01/{match.group(1)}/{match.group(2)}" if match else None

def extrair_nome_banco(linha):
    match = re.search(r'(RMC|RCC).*?- ([A-Z0-9 ./]+)', linha)
    return match.group(2).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB\.?.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def extrair_linhas(texto):
    return texto.split("\n")

def preencher_meses(dados):
    if not dados:
        return dados

    datas = sorted(set(datetime.strptime(d["Data"], "%d/%m/%Y") for d in dados))
    inicio = datas[0]
    fim = datas[-1]

    meses_completos = []
    atual = inicio
    while atual <= fim:
        meses_completos.append(atual.strftime("%d/%m/%Y"))
        atual += relativedelta(months=1)

    dados_por_data = {(d["Data"], d["Tipo"]): d for d in dados}
    tipos = set(d["Tipo"] for d in dados)

    dados_preenchidos = []
    for data in meses_completos:
        for tipo in tipos:
            chave = (data, tipo)
            if chave in dados_por_data:
                dados_preenchidos.append(dados_por_data[chave])
            else:
                dados_preenchidos.append({
                    "Data": data,
                    "Tipo": tipo,
                    "Valor": 0.0
                })

    return dados_preenchidos

def processar_linhas(linhas):
    dados = []
    competencia = None

    for linha in linhas:
        if not competencia:
            competencia = extrair_competencia(linha)

        for tipo, codigo in rubricas_alvo.items():
            if codigo in linha:
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor_match:
                    dados.append({
                        "Data": competencia or "01/01/1900",
                        "Tipo": f"{tipo} - {extrair_nome_banco(linha)}",
                        "Valor": formatar_valor(valor_match.group(1))
                    })

        for tipo, termos in rubricas_textuais.items():
            if any(p in linha.upper() for p in termos):
                valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                if valor_match:
                    dados.append({
                        "Data": competencia or "01/01/1900",
                        "Tipo": f"{tipo} - {extrair_nome_sindicato(linha)}",
                        "Valor": formatar_valor(valor_match.group(1))
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

    dados = [d for d in dados if d.get("Valor") is not None]
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    dados = preencher_meses(dados)
    return dados
