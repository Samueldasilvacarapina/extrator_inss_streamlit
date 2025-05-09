import pdfplumber
import re
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path

# Rubricas a serem buscadas
rubricas_textuais = {
    "RMC": ["RMC", "EMPRÉSTIMO SOBRE A RMC"],
    "RCC": ["CONSIGNACAO - CARTAO", "CARTAO"],
    "SINDICATO": ["CONTRIB", "CONTRIBUIÇÃO", "CONTRIB.SINDICAL", "SINDICATO", "SIND.", "SINDICAL"],
}

def formatar_valor(valor_str):
    """Converte valor string para float, no formato brasileiro."""
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_linhas(texto):
    """Divide o texto extraído do PDF em linhas."""
    return texto.split("\n")

def extrair_nome_sindicato(linha):
    """Extrai o nome do sindicato a partir da linha."""
    match = re.search(r'(CONTRIB\.?.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def processar_linhas(linhas):
    """Processa todas as linhas do texto, identificando rubricas e competências."""
    dados = []
    competencia_atual = None

    for linha in linhas:
        linha = linha.strip()

        # Detecta linha com competência no início (ex: 02/2018 R$ ...)
        if re.match(r'^\d{2}/\d{4}\s+R\$[\d.,]+', linha):
            competencia_atual = re.match(r'^(\d{2}/\d{4})', linha).group(1)
            competencia_atual = f"01/{competencia_atual}"  # sempre com dia 01

        # Verifica presença de rubricas e extrai dados
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
                        "Data": competencia_atual or "01/01/1900",
                        "Tipo": nome_final,
                        "Valor": formatar_valor(valor_match.group(1))
                    })
                break  # já encontrou a rubrica, passa pra próxima linha

    return dados

def processar_pdf(caminho_pdf):
    """Processa o PDF, extraindo dados com ou sem OCR se necessário."""
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

    # Fallback com OCR (caso pdfplumber falhe ou não encontre texto)
    if not dados:
        try:
            imagens = convert_from_path(caminho_pdf)
            for imagem in imagens:
                texto = pytesseract.image_to_string(imagem)
                linhas = extrair_linhas(texto)
                dados.extend(processar_linhas(linhas))
        except Exception:
            pass

    # Filtra e ordena os dados por data
    dados = [d for d in dados if d.get("Valor") is not None]
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
