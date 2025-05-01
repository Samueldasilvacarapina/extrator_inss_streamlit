import pdfplumber
import re
from collections import defaultdict
from datetime import datetime, timedelta

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

def gerar_datas_completas(dados):
    if not dados:
        return dados
    datas_existentes = set(d["Data"] for d in dados)
    min_data = min(datetime.strptime(d["Data"], "%d/%m/%Y") for d in dados)
    max_data = max(datetime.strptime(d["Data"], "%d/%m/%Y") for d in dados)

    datas_completas = []
    atual = datetime(min_data.year, min_data.month, 1)
    fim = datetime(max_data.year, max_data.month, 1)

    while atual <= fim:
        datas_completas.append(atual.strftime("%d/%m/%Y"))
        # próximo mês
        if atual.month == 12:
            atual = datetime(atual.year + 1, 1, 1)
        else:
            atual = datetime(atual.year, atual.month + 1, 1)

    # garantir que todas as datas estejam na base, mesmo que com valor 0
    resultado = []
    for data in datas_completas:
        entradas = [d for d in dados if d["Data"] == data]
        if entradas:
            resultado.extend(entradas)
        else:
            resultado.append({
                "Data": data,
                "Tipo": "SEM LANÇAMENTO",
                "Valor": 0.0
            })
    return resultado

def extrair_competencia_linha(linha):
    match = re.search(r'(?i)compet[eê]ncia[:\s]*([0-1][0-9])/(\d{4})', linha)
    if match:
        return f"01/{match.group(1)}/{match.group(2)}"
    return None

def processar_pdf(caminho_pdf):
    dados = []

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

                if not competencia_atual:
                    continue

                for chave, codigo in rubricas_alvo.items():
                    if codigo in linha:
                        banco_match = re.search(rf'{codigo}\D+(.+)', linha)
                        banco = banco_match.group(1).strip() if banco_match else ""
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {banco}" if banco else chave,
                                "Valor": formatar_valor(valor.group(1))
                            })

                for chave, palavras in rubricas_textuais.items():
                    if any(p in linha.upper() for p in palavras):
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        sindicato = linha.strip()
                        if valor:
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {sindicato}",
                                "Valor": formatar_valor(valor.group(1))
                            })

    dados = gerar_datas_completas(dados)
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
