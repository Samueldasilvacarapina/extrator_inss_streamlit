import pdfplumber
import re
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path

rubricas_textuais = {
    "RMC": ["RMC", "EMPRÉSTIMO SOBRE A RMC"],
    "RCC": ["CONSIGNACAO - CARTAO", "CARTAO"],
    "SINDICATO": ["CONTRIB", "CONTRIBUIÇÃO", "CONTRIB.SINDICAL", "SINDICATO", "SIND.", "SINDICAL"],
}

def formatar_valor(valor_str):
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_linhas(texto):
    return texto.split("\n")

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB\.?.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def processar_linhas(linhas):
    dados = []
    competencia_atual = None

    for i, linha in enumerate(linhas):
        linha = linha.strip()

        # ✅ Detecta a competência (ex: "01/2021" mesmo em "01/2021 a 31/01/2021")
        comp_match = re.search(r"\b(\d{2}/\d{4})\b", linha)
        if comp_match:
            competencia_atual = f"01/{comp_match.group(1)}"
            continue  # vai pra próxima linha, pq essa é só data

        # ✅ Se não tem competência atual, não processa rubrica
        if not competencia_atual:
            continue

        # ✅ Detecta rubrica e valor
        for tipo, palavras in rubricas_textuais.items():
            if any(p in linha.upper() for p in palavras):
                valor_match = re.search(r'R\$ ?([\d.,]+)', linha)
                if valor_match:
                    if tipo == "SINDICATO":
                        nome = extrair_nome_sindicato(linha)
                        nome_final = f"{tipo} - {nome}"
                    else:
                        nome_final = f"{tipo} - BANCO"

                    dados.append({
                        "Data": competencia_atual,
                        "Tipo": nome_final,
                        "Valor": formatar_valor(valor_match.group(1))
                    })
                break  # já achou rubrica, não precisa checar as outras

    return dados
