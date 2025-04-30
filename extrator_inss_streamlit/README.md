
# Extrator de Histórico de Créditos - INSS

Este é um aplicativo em Python usando Streamlit que permite enviar um PDF do INSS e gerar uma planilha completa com:

- Valores por competência (RMC, RCC, SINDICATO)
- Salário Bruto (rubrica 101)
- Descontos (201, 216, 104, etc.)
- Salário líquido
- Totais simples, valores em dobro e valor da causa

## Como usar localmente

1. Clone o repositório:

```
git clone https://github.com/seuusuario/projeto-inss-extrator.git
cd projeto-inss-extrator
```

2. Instale as dependências:

```
pip install -r requirements.txt
```

3. Rode o app:

```
streamlit run app.py
```

4. Abra o link que aparecer no navegador, envie o PDF e baixe a planilha gerada.
