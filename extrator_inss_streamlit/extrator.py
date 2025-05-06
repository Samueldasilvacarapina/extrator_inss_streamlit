import pdfplumber
import re
from datetime import datetime, timedelta
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

def processar_linhas(linhas):
    dados = []
    competencia = None
    dentro_competencia = False

    for linha in linhas:
        linha_limpa = linha.strip()

        if "CRÉDITO" in linha_limpa.upper() or "CRED" in linha_limpa.upper():
            continue  # Ignora lançamentos de crédito

        nova_comp = extrair_competencia(linha_limpa)
        if nova_comp:
            competencia = nova_comp
            dentro_competencia = True
            continue  # pula para a próxima linha após atualizar competência

        # Só processa rubricas se estiver dentro de uma competência válida
        if competencia and dentro_competencia:
            # Verifica rubricas RMC/RCC por código específico
            for tipo, codigo in rubricas_alvo.items():
                if re.search(rf'\b{codigo}\b', linha_limpa):
                    valor_match = re.search(r'R\$\s*([\d.,]+)', linha_limpa)
                    if valor_match:
                        dados.append({
                            "Data": competencia,
                            "Tipo": f"{tipo} - {extrair_nome_banco(linha_limpa)}",
                            "Valor": formatar_valor(valor_match.group(1))
                        })
                        break  # evita múltiplas detecções na mesma linha

            # Verifica contribuições sindicais por palavras-chave
            for tipo, termos in rubricas_textuais.items():
                if any(p in linha_limpa.upper() for p in termos):
                    valor_match = re.search(r'R\$\s*([\d.,]+)', linha_limpa)
                    if valor_match:
                        dados.append({
                            "Data": competencia,
                            "Tipo": f"{tipo} - {extrair_nome_sindicato(linha_limpa)}",
                            "Valor": formatar_valor(valor_match.group(1))
                        })
                        break

    return dados

def preencher_meses_faltantes(dados):
    dados_reais = [d for d in dados if d["Valor"] > 0]
    if not dados_reais:
        return dados

    datas_convertidas = [datetime.strptime(d["Data"], "%d/%m/%Y") for d in dados_reais]
    data_inicial = min(datas_convertidas)
    data_final = max(datas_convertidas)

    datas_existentes = set(d["Data"] for d in dados)

    atual = data_inicial
    while atual <= data_final:
        data_str = atual.strftime("%d/%m/%Y")
        if data_str not in datas_existentes:
            dados.append({
                "Data": data_str,
                "Tipo": "SEM DADOS",
                "Valor": 0.0
            })
        atual += relativedelta(months=1)

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
    dados = preencher_meses_faltantes(dados)
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))

    return dados
