import pdfplumber
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
    match = re.search(r'PER[ÍI]ODO.*?(\d{2})/(\d{2})/(\d{4})\s*[aáà-]+\s*(\d{2})/(\d{2})/(\d{4})', linha, re.IGNORECASE)
    if match:
        return f"01/{match.group(2)}/{match.group(3)}"
    match2 = re.search(r'(\d{2})/(\d{4})', linha)
    if match2:
        return f"01/{match2.group(1)}/{match2.group(2)}"
    return None

def extrair_nome_banco(linha):
    match = re.search(r'(RMC|RCC).*?- ([A-Z0-9 ./]+)', linha)
    return match.group(2).strip() if match else "BANCO"

def extrair_nome_sindicato(linha):
    match = re.search(r'(CONTRIB\.?.*?)\s+R\$', linha, re.IGNORECASE)
    return match.group(1).strip() if match else "SINDICATO"

def preencher_datas_continuas(dados):
    if not dados:
        return dados

    datas_existentes = set(item["Data"] for item in dados)
    primeira_data = min(datetime.strptime(d, "%d/%m/%Y") for d in datas_existentes)
    ultima_data = max(datetime.strptime(d, "%d/%m/%Y") for d in datas_existentes)

    data_atual = primeira_data.replace(day=1)
    datas_completas = []

    while data_atual <= ultima_data:
        data_str = data_atual.strftime("%d/%m/%Y")
        linhas_mes = [d for d in dados if d["Data"] == data_str]
        if linhas_mes:
            datas_completas.extend(linhas_mes)
        else:
            datas_completas.append({"Data": data_str, "Tipo": "SEM DADOS", "Valor": 0.0})
        data_atual += relativedelta(months=1)

    return datas_completas

def processar_pdf(caminho_pdf):
    dados = []
    competencia = None

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
            linhas = texto.split("\n")
            for linha in linhas:
                nova_data = extrair_competencia(linha)
                if nova_data:
                    competencia = nova_data

                for tipo, codigo in rubricas_alvo.items():
                    if codigo in linha:
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            dados.append({
                                "Data": competencia or "01/01/1900",
                                "Tipo": f"{tipo} - {extrair_nome_banco(linha)}",
                                "Valor": formatar_valor(valor.group(1))
                            })

                for tipo, termos in rubricas_textuais.items():
                    if any(t in linha.upper() for t in termos):
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            dados.append({
                                "Data": competencia or "01/01/1900",
                                "Tipo": f"{tipo} - {extrair_nome_sindicato(linha)}",
                                "Valor": formatar_valor(valor.group(1))
                            })

    dados = [d for d in dados if d["Valor"] is not None]
    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))

    return preencher_datas_continuas(dados)
