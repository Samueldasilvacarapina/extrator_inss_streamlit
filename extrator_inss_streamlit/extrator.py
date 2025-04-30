import pdfplumber
import re
from collections import defaultdict

rubricas_alvo = {
    "RMC": "217",
    "RCC": "268",
}
rubricas_textuais = {
    "SINDICATO": ["CONTRIB", "SINDICATO"]
}

def formatar_valor(valor_str):
    return float(valor_str.replace(".", "").replace(",", "."))

def extrair_competencia_linha(linha):
    match = re.search(r'(\d{2})/(\d{4})', linha)
    if match:
        return f"01/{match.group(1)}/{match.group(2)}"
    return None

def processar_pdf(caminho_pdf):
    dados = defaultdict(lambda: {"RMC": 0.0, "RCC": 0.0, "SINDICATO": 0.0})

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
            linhas = texto.split("\n")
            competencia_atual = None

            for linha in linhas:
                nova_data = extrair_competencia_linha(linha)
                if nova_data:
                    competencia_atual = nova_data

                if competencia_atual:
                    for chave, codigo in rubricas_alvo.items():
                        if codigo in linha:
                            valor = re.search(r'R\$ ([\d.,]+)', linha)
                            if valor:
                                dados[competencia_atual][chave] += formatar_valor(valor.group(1))

                    for chave, palavras in rubricas_textuais.items():
                        if any(p in linha.upper() for p in palavras):
                            valor = re.search(r'R\$ ([\d.,]+)', linha)
                            if valor:
                                dados[competencia_atual][chave] += formatar_valor(valor.group(1))

    dados_ordenados = dict(sorted(dados.items(), key=lambda x: (int(x[0][6:]), int(x[0][3:5]))))
    return dados_ordenados

