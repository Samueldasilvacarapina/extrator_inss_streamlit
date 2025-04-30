import pdfplumber
import re
from collections import defaultdict
from datetime import datetime
import pandas as pd

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

def extrair_competencia_linha(linha):
    match = re.search(r'(\d{2})/(\d{4})', linha)
    if match:
        return f"01/{match.group(1)}/{match.group(2)}"
    return None

def processar_pdf(caminho_pdf, debug=False):
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
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            nome = linha.split(codigo)[-1].strip()
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {nome}",
                                "Valor": formatar_valor(valor.group(1))
                            })

                for chave, palavras in rubricas_textuais.items():
                    if any(p in linha.upper() for p in palavras):
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {linha.strip()}",
                                "Valor": formatar_valor(valor.group(1))
                            })

    if not dados:
        return []

    df = pd.DataFrame(dados)
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)

    # Gera todos os meses entre a menor e a maior data
    todas_datas = pd.date_range(df["Data"].min(), df["Data"].max(), freq="MS")

    tipos_unicos = df["Tipo"].unique()
    linhas_completas = []

    for data in todas_datas:
        for tipo in tipos_unicos:
            filtro = (df["Data"] == data) & (df["Tipo"] == tipo)
            if filtro.any():
                total = df.loc[filtro, "Valor"].sum()
            else:
                total = 0.0
            linhas_completas.append({
                "Data": data.strftime("%d/%m/%Y"),
                "Tipo": tipo,
                "Valor": total
            })

    return linhas_completas
