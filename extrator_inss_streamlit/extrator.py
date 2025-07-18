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

        # ✅ Agora detecta qualquer competência MM/AAAA mesmo dentro de frases como "01/2021 a 31/01/2021"
        comp_match = re.search(r"\b(\d{2}/\d{4})\b", linha)
        if comp_match:
            competencia_atual = f"01/{comp_match.group(1)}"  # sempre adiciona dia 01

        # ✅ Detecta rubrica e valor na linha
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
                        "Data": competencia_atual or "01/01/1900",  # se não achou, marca default
                        "Tipo": nome_final,
                        "Valor": formatar_valor(valor_match.group(1))
                    })
                break  # já achou rubrica, não precisa checar as outras

    return dados

def processar_pdf(caminho_pdf):
    dados = []

    try:
        # ✅ Primeiro tenta extrair como texto
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = extrair_linhas(texto)
                    dados.extend(processar_linhas(linhas))
    except Exception as e:
        print("Erro ao ler com pdfplumber:", e)

    # ✅ Se não achou nada (PDF escaneado), usa OCR
    if not dados:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem)
                linhas = extrair_linhas(texto)
                dados.extend(processar_linhas(linhas))
        except Exception as e:
            print("Erro ao ler com OCR:", e)

    # ✅ Filtra só os dados válidos
    dados = [d for d in dados if d.get("Valor") is not None]

    # ✅ Ordena por data
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))

    return dados
