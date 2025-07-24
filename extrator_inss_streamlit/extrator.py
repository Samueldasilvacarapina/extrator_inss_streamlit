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

def extrair_competencia(texto):
    # 1. MM/AAAA
    match = re.search(r"\b(\d{2}/\d{4})\b", texto)
    if match:
        return f"01/{match.group(1)}"

    # 2. MM-AAAA
    match = re.search(r"\b(\d{2})-(\d{4})\b", texto)
    if match:
        return f"01/{match.group(1)}/{match.group(2)}"

    # 3. DD/MM/AAAA (pega mês e ano)
    match = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", texto)
    if match:
        return f"01/{match.group(2)}/{match.group(3)}"

    # 4. Mês por extenso ou abreviado + ano (ex: JAN/2023)
    meses = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
        "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
        "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
    }
    match = re.search(r"\b(" + "|".join(meses.keys()) + r")[^\d]{0,2}(\d{4})\b", texto.upper())
    if match:
        mes = meses[match.group(1)]
        ano = match.group(2)
        return f"01/{mes}/{ano}"

    return None

def processar_linhas(linhas):
    dados = []
    competencia_atual = None

    for i, linha in enumerate(linhas):
        linha = linha.strip()
        nova_comp = extrair_competencia(linha)
        if nova_comp:
            competencia_atual = nova_comp

        # Detecta rubrica e valor
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
                        "Data": competencia_atual if competencia_atual else "SEM DATA",
                        "Tipo": nome_final,
                        "Valor": formatar_valor(valor_match.group(1)),
                        "Origem": linha  # opcional para depuração
                    })
                break  # achou rubrica, não precisa continuar

    return dados

def processar_pdf(caminho_pdf):
    dados = []

    try:
        # Tenta extrair com texto
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = extrair_linhas(texto)
                    dados.extend(processar_linhas(linhas))
    except Exception as e:
        print("Erro ao ler com pdfplumber:", e)

    # Se não achou nada, tenta OCR
    if not dados:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem)
                linhas = extrair_linhas(texto)
                dados.extend(processar_linhas(linhas))
        except Exception as e:
            print("Erro ao ler com OCR:", e)

    # Filtra apenas os que têm valor
    dados = [d for d in dados if d.get("Valor") is not None]

    # Ordena por data (ignora os com 'SEM DATA')
    dados_validos = [d for d in dados if d["Data"] != "SEM DATA"]
    dados_invalidos = [d for d in dados if d["Data"] == "SEM DATA"]

    dados_validos.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))

    return dados_validos + dados_invalidos
