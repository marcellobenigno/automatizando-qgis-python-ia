"""
Desafio — Tabela dinâmica (pivot table): municípios x classes de uso do solo.

Lê o CSV "longo" gerado por 03_fluxo_pb200.py (uma linha por município e
classe) e o transforma em uma tabela "larga": uma linha por município,
uma coluna por classe, com a área em hectares.
"""
from pathlib import Path

import pandas as pd

PASTA_SAIDA = "/caminho/para/dados_curso/pb200/resultados"
PREFIXO = "pb200"

pasta = Path(PASTA_SAIDA)
longo = pd.read_csv(pasta / f"{PREFIXO}_uso_solo_municipio_classe.csv")

pivot = longo.pivot_table(index="nome", columns="descricao", values="sum",
                          aggfunc="sum", fill_value=0, margins=True,
                          margins_name="Total").round(2)
print(pivot)

# Percentual de cada classe dentro de cada município
pct = pivot.div(pivot["Total"], axis=0).mul(100).round(1)
print(pct)

# sep=";" e decimal="," abrem direto no Excel em português; utf-8-sig mantém os acentos
pivot.to_csv(pasta / f"{PREFIXO}_pivot_ha.csv", sep=";", decimal=",", encoding="utf-8-sig")
pct.to_csv(pasta / f"{PREFIXO}_pivot_pct.csv", sep=";", decimal=",", encoding="utf-8-sig")
# Para gerar .xlsx: pivot.to_excel(...) — requer o pacote openpyxl
print("Tabelas salvas em", pasta)
