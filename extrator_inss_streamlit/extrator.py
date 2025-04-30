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

def processar_pdf(caminho_pdf, debug=False):
    dados = []
    competencia_atual = None

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
            linhas = texto.split("\n")

            for i, linha in enumerate(linhas):
                # Detecta bloco de data: linha com data, seguida por 'a', depois outra data
                if i + 2 < len(linhas):
                    match1 = re.match(r'(\d{2}/\d{2}/\d{4})', linhas[i].strip())
                    match2 = linhas[i+1].strip().lower() == 'a'
                    match3 = re.match(r'(\d{2}/\d{2}/\d{4})', linhas[i+2].strip())
                    if match1 and match2 and match3:
                        competencia_atual = '01/' + linhas[i].strip()[3:]  # usa apenas mês/ano da 1ª data

                if not competencia_atual:
                    continue

                linha_upper = linha.upper()

                for chave, codigo in rubricas_alvo.items():
                    if codigo in linha:
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {linha.strip()}",
                                "Valor": formatar_valor(valor.group(1))
                            })

                for chave, palavras in rubricas_textuais.items():
                    if any(p in linha_upper for p in palavras):
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {linha.strip()}",
                                "Valor": formatar_valor(valor.group(1))
                            })

    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
