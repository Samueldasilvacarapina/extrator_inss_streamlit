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

def extrair_competencia_linha(linha):
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', linha)
    if match:
        return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
    return None

def processar_pdf(caminho_pdf, debug=False):
    dados = []
    competencia_atual = None

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
            linhas = texto.split("\n")

            for linha in linhas:
                nova_data = extrair_competencia_linha(linha)
                if nova_data:
                    competencia_atual = nova_data

                if not competencia_atual:
                    continue

                linha_upper = linha.upper()

                # RMC e RCC por código (217, 268)
                for chave, codigo in rubricas_alvo.items():
                    if codigo in linha:
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            entidade_match = re.search(rf'{codigo}[^\d\n\r]*? -?\s*([^R$\n\r]+)', linha)
                            entidade = entidade_match.group(1).strip() if entidade_match else ""
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {entidade}" if entidade else chave,
                                "Valor": formatar_valor(valor.group(1))
                            })

                # SINDICATO (CONTRIBUIÇÕES)
                for chave, palavras in rubricas_textuais.items():
                    if any(p in linha_upper for p in palavras):
                        valor = re.search(r'R\$\s*([\d.,]+)', linha)
                        if valor:
                            entidade_match = re.search(r'(CONTRIB\.?\s*[^R$\n]*)', linha_upper)
                            entidade = entidade_match.group(1).strip() if entidade_match else ""
                            dados.append({
                                "Data": competencia_atual,
                                "Tipo": f"{chave} - {entidade}" if entidade else chave,
                                "Valor": formatar_valor(valor.group(1))
                            })

    dados.sort(key=lambda x: datetime.strptime(x["Data"], "%d/%m/%Y"))
    return dados
