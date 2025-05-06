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
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_competencia(linha):
    match = re.search(r'(\d{2})/(\d{4})', linha)
    if match:
        return f"01/{match.group(1)}/{match.group(2)}"
    return None

def extrair_nome_banco(linha):
    match = re.search(r'(RMC|RCC).*?- ([A-Z0-9 ./]+)', linha)
    return match.group(2).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB\.?.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def extrair_linhas(texto):
    return texto.split("\n")

def processar_pdf(caminho_pdf):
    dados = []
    competencia_atual = None
    dentro_bloco = False
    buffer_linhas = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = extrair_linhas(texto)
                    for linha in linhas:
                        nova_comp = extrair_competencia(linha)
                        if nova_comp:
                            competencia_atual = nova_comp
                            dentro_bloco = True
                            buffer_linhas = []
                        if dentro_bloco:
                            buffer_linhas.append(linha)
                            if "Rubrica" in linha and "Descrição" in linha and "Valor" in linha:
                                continue  # ignora o cabeçalho da tabela
                            # RMC ou RCC
                            for tipo, cod in rubricas_alvo.items():
                                if cod in linha:
                                    valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                                    if valor_match:
                                        dados.append({
                                            "Data": competencia_atual,
                                            "Tipo": f"{tipo} - {extrair_nome_banco(linha)}",
                                            "Valor": formatar_valor(valor_match.group(1))
                                        })
                            # Sindicato
                            for tipo, termos in rubricas_textuais.items():
                                if any(t in linha.upper() for t in termos):
                                    valor_match = re.search(r'R\$\s*([\d.,]+)', linha)
                                    if valor_match:
                                        dados.append({
                                            "Data": competencia_atual,
                                            "Tipo": f"{tipo} - {extrair_nome_sindicato(linha)}",
                                            "Valor": formatar_valor(valor_match.group(1))
                                        })
    except Exception as e:
        print("Erro ao processar PDF:", e)

    # Ordenar por data
    dados = [d for d in dados if d.get("Valor") is not None]
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
