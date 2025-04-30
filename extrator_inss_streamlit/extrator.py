import pdfplumber
import re
from collections import defaultdict

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
    dados = defaultdict(lambda: {"RMC": 0.0, "RCC": 0.0, "SINDICATO": 0.0})

    with pdfplumber.open(caminho_pdf) as pdf:
        texto_total = ""
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_total += texto + "\n"

    blocos = re.split(r"(?=\d{2}/\d{4})", texto_total)

    for bloco in blocos:
        match_data = re.search(r"(\d{2})/(\d{4})", bloco)
        if not match_data:
            continue
        competencia = f"01/{match_data.group(1)}/{match_data.group(2)}"

        if debug:
            print(f"📅 {competencia}\n---\n{bloco}\n---\n")

        # RMC e RCC (numéricos)
        for chave, codigo in rubricas_alvo.items():
            padrao = re.compile(rf"{codigo}[\s\S]*?R\$\s*([\d.,]+)", re.IGNORECASE)
            valores = padrao.findall(bloco)
            for v in valores:
                dados[competencia][chave] += formatar_valor(v)

        # SINDICATO e variações (palavras)
        for chave, palavras in rubricas_textuais.items():
            for palavra in palavras:
                padrao = re.compile(rf"{palavra}[\s\S]*?R\$\s*([\d.,]+)", re.IGNORECASE)
                valores = padrao.findall(bloco)
                for v in valores:
                    dados[competencia][chave] += formatar_valor(v)

    dados_ordenados = dict(sorted(dados.items(), key=lambda x: (int(x[0][6:]), int(x[0][3:5]))))
    return dados_ordenados
