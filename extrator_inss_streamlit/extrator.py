import pdfplumber
import re
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path

def formatar_valor(valor_str):
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_linhas(texto):
    return texto.split("\n")

def identificar_tipo_e_nome(linha):
    linha_upper = linha.upper()
    valor_match = re.search(r'R\$ ?([\d.,]+)', linha)
    if not valor_match:
        return None

    valor = formatar_valor(valor_match.group(1))

    # RMC
    if "RMC" in linha_upper or "EMPRESTIMO SOBRE A RMC" in linha_upper:
        return ("RMC", "EMPRÉSTIMO SOBRE A RMC", valor)

    # RCC
    if "RCC" in linha_upper or "CARTAO" in linha_upper or "CONSIGNACAO - CARTAO" in linha_upper:
        return ("RCC", "CARTÃO", valor)

    # Sindicato/Contribuição
    if any(p in linha_upper for p in ["CONTRIB", "SINDIC", "SIND." , "SINDICATO"]):
        nome_match = re.search(r'(CONTRIBUI.*?|SINDIC.*?|SIND\.?.*?)\s+R\$', linha_upper)
        nome = nome_match.group(1).strip().title() if nome_match else "SINDICATO"
        return ("SINDICATO", nome, valor)

    # Empréstimo bancário
    if "CONSIGNACAO EMPRESTIMO BANCARIO" in linha_upper:
        return ("BANCO", "EMPRÉSTIMO BANCÁRIO", valor)

    # Fallback
    return ("SEM DADOS", "SEM DADOS", valor)

def processar_linhas_por_competencia(linhas):
    dados = []
    competencia_atual = None

    for linha in linhas:
        # Detecta nova competência
        comp_match = re.match(r'^\s*(\d{2}/\d{4})\s+', linha)
        if comp_match:
            competencia_atual = f"01/{comp_match.group(1)}"
            continue

        # Tenta classificar linha
        resultado = identificar_tipo_e_nome(linha)
        if resultado and competencia_atual:
            tipo_base, tipo_nome, valor = resultado
            dados.append({
                "Data": competencia_atual,
                "Tipo": f"{tipo_base} - {tipo_nome}",
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
                    dados.extend(processar_linhas_por_competencia(linhas))
    except Exception:
        pass

    # Fallback OCR
    if not dados:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem)
                linhas = extrair_linhas(texto)
                dados.extend(processar_linhas_por_competencia(linhas))
        except Exception:
            pass

    dados = [d for d in dados if d.get("Valor") is not None]
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
