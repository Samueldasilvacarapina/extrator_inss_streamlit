for linha in linhas:
    nova_data = extrair_competencia_linha(linha)
    if nova_data:
        competencia_atual = nova_data

    if not competencia_atual:
        continue

    # Captura nome de banco ou sindicato se estiver na linha
    nome_entidade = ""
    if "CONTRIB" in linha.upper() or "SIND" in linha.upper():
        nome_match = re.search(r"(CONTRIB[^\dR$]*)", linha.upper())
        if nome_match:
            nome_entidade = nome_match.group(1).strip()

    for chave, codigo in rubricas_alvo.items():
        if codigo in linha:
            valor = re.search(r'R\$\s*([\d.,]+)', linha)
            if valor:
                entidade = nome_entidade if nome_entidade else "BANCO"
                dados.append({
                    "Data": competencia_atual,
                    "Tipo": f"{chave} - {entidade}",
                    "Valor": formatar_valor(valor.group(1))
                })


