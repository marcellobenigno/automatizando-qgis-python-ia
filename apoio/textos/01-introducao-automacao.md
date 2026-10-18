# Módulo 1 — Introdução à automação no QGIS

⏱ 30 min · [← Início](../../README.md) · [Módulo 2 →](02-fundamentos-pyqgis.md)

## Por que automatizar?

Quase todo trabalho de geoprocessamento repete uma mesma sequência de ferramentas: filtrar, reprojetar, gerar buffer, recortar, calcular áreas, exportar. Fazer isso pela interface uma vez é ótimo para **aprender**; fazer dez vezes é lento e propenso a erro.

| Fluxo manual | Fluxo automatizado |
| --- | --- |
| Cada execução exige dezenas de cliques | Um clique (ou nenhum) |
| Fácil esquecer um passo ou trocar um parâmetro | Os parâmetros ficam escritos no código |
| Difícil explicar exatamente o que foi feito | O script **é** a documentação do método |
| Refazer com dados novos = recomeçar do zero | Troca-se o arquivo de entrada e roda de novo |
| Escala mal (1 rodovia ✔, 300 rodovias ✘) | Um `for` resolve |

Automação não substitui o conhecimento de geoprocessamento: **só automatiza bem quem sabe fazer à mão**. Por isso a prática começa pelo fluxo manual.

## O que dá para automatizar no QGIS

- **Processing Framework** — executar e encadear qualquer algoritmo da Caixa de Ferramentas (foco deste curso).
- **PyQGIS** — manipular camadas, feições, atributos, estilos, layouts e o próprio projeto.
- **Modelador Gráfico** — encadear algoritmos visualmente, sem código.
- **Processamento em lote** — rodar uma ferramenta para vários arquivos pela interface.
- **Plugins e scripts de processamento** — empacotar o seu fluxo como uma ferramenta nova.
- **`qgis_process`** — executar algoritmos pela linha de comando, sem abrir o QGIS.

## O Processing Framework

É a infraestrutura que padroniza **todas** as ferramentas de análise do QGIS. Cada algoritmo:

- pertence a um **provedor** (`native` — C++ do QGIS, `qgis` — Python, `gdal`, `grass`, `saga`...);
- tem um **ID único**, como `native:buffer` ou `gdal:cliprasterbymasklayer`;
- recebe **parâmetros nomeados** (`INPUT`, `DISTANCE`, `OUTPUT`...) e devolve **saídas nomeadas**.

Essa padronização é o que permite chamar qualquer ferramenta com a mesma linha de Python:

```python
processing.run("native:buffer", {"INPUT": camada, "DISTANCE": 3000, "OUTPUT": "TEMPORARY_OUTPUT"})
```

### Onde encontrar as ferramentas

- **Caixa de Ferramentas de Processamento** (`Ctrl+Alt+T`): busca por nome, agrupada por provedor.
- Menus **Vetor** e **Raster**: atalhos para os algoritmos mais comuns.
- **Processamento → Histórico**: tudo o que você executou, já em forma de código Python.

![Caixa de Ferramentas](../../imgs/pb200/7-toolbox.png)

## Demonstração: da interface ao código

1. Abra **Buffer** na Caixa de Ferramentas, preencha e execute.
2. Na aba **Log**, veja o ID do algoritmo e o dicionário de parâmetros usados.
3. Em **Avançado → Copiar como comando Python**, copie o comando.
4. Abra o **Console Python** (`Ctrl+Alt+P`), cole e execute: o mesmo resultado, agora por código.

![Buffer pela interface](../../imgs/pb200/9-buffer_3km.png)

## O Console Python

- **Console** (`Ctrl+Alt+P`): executa linha a linha — bom para testar.
- **Editor** (botão *Mostrar editor*): escreve, salva e executa scripts `.py` inteiros.
- Já vem com `iface`, `QgsProject`, `processing` e as classes `qgis.core` importadas.

Experimente [`scripts/01_listar_algoritmos.py`](../scripts/01_listar_algoritmos.py): ele lista os provedores, procura algoritmos de buffer e mostra a ajuda de `native:buffer`.

## Para fixar

1. Quantos algoritmos tem o provedor `native` na sua instalação?
2. Qual o ID do algoritmo **Recortar (Clip)**? E de **Reprojetar camada**?
3. Execute **Reprojetar camada** pela interface e encontre o comando correspondente no **Histórico**.

<details>
<summary>Respostas</summary>

1. Depende da versão (no QGIS 3.44 são 321): `len(QgsApplication.processingRegistry().providerById("native").algorithms())`.
2. `native:clip` e `native:reprojectlayer`.
3. **Processamento → Histórico**; clique duas vezes para reabrir o diálogo ou copie o código.
</details>
