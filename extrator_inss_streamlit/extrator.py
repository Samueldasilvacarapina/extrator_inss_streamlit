import pdfplumber
import re
from collections import defaultdict
from datetime import datetime

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

def extrair_competencia_periodo(trecho):
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})\s*a\s*(\d{2})/(\d{2})/(\d{4})', trecho)
    if match:
        return f"01/{match.group(2)}/{match.group(3)}"
    return None

def extrair_nome_banco(linha):
    match = re.search(r'RMC.*?- ([A-Z ]+)', linha)
    if not match:
        match = re.search(r'RCC.*?- ([A-Z ]+)', linha)
    return match.group(1).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB\.?.*?)\s*R\$?', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def processar_pdf(caminho_pdf, debug=False):
    dados = []
    competencia_atual = None
    linhas_acumuladas = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue

            linhas = texto.split("\n")

            for linha in linhas:
                linha = linha.strip()
                if not linha:
                    continue

                linhas_acumuladas.append(linha)

                if len(linhas_acumuladas) >= 3:
                    trecho = " ".join(linhas_acumuladas[-3:])
                    nova_data = extrair_competencia_periodo(trecho)
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

    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
