import pdfplumber
import re

rubrica_rmc = '217'
rubrica_rcc = '268'
rubricas_sindicato = ['SINDICATO', 'CONTRIB']

def formatar_valor(valor_str):
    return float(valor_str.replace('.', '').replace(',', '.'))

def extrair_competencia(bloco):
    match = re.search(r'(\d{2})/(\d{4})', bloco)
    return f"01/{match.group(1)}/{match.group(2)}" if match else None

def somar_rubrica(bloco, rubrica):
    padrao = re.compile(rf'{rubrica} .*?R\$ ([\d.,]+)')
    return sum(formatar_valor(v) for v in padrao.findall(bloco))

def somar_texto(bloco, palavras_chave):
    padrao = re.compile(rf"({'|'.join(palavras_chave)}).*?R\$ ([\d.,]+)", re.IGNORECASE)
    return sum(formatar_valor(m[1]) for m in padrao.findall(bloco))

def processar_pdf(caminho_pdf):
    dados = {}

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            blocos = re.split(r'(?=Competência Período)', texto)

            for bloco in blocos:
                data = extrair_competencia(bloco)
                if not data:
                    continue
                if data not in dados:
                    dados[data] = {'RMC': 0.0, 'RCC': 0.0, 'SINDICATO': 0.0}

                dados[data]['RMC'] += somar_rubrica(bloco, rubrica_rmc)
                dados[data]['RCC'] += somar_rubrica(bloco, rubrica_rcc)
                dados[data]['SINDICATO'] += somar_texto(bloco, rubricas_sindicato)

    # ordenar da mais antiga pra mais recente
    return dict(sorted(dados.items(), key=lambda x: tuple(map(int, x[0].split("/")[::-1]))))
