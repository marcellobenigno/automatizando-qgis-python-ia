# Módulo 3 — Inteligência Artificial aplicada ao geoprocessamento

⏱ 30 min · [← Módulo 2](02-fundamentos-pyqgis.md) · [Prática →](../../modulos/pb200/pb200.md)

Assistentes de IA generativa (ChatGPT, Claude, Gemini, GitHub Copilot...) aceleram muito a escrita de scripts PyQGIS — desde que usados como **assistentes**, e não como oráculos. Neste módulo vemos como pedir, como entender o que veio e como verificar. A aplicação completa está na [seção 6.3 da prática da PB-200](../../modulos/pb200/pb200.md#63-a-ia-na-criação-do-algoritmo).

## O que a IA faz bem e onde ela erra

| Faz bem | Erra com frequência |
| --- | --- |
| Escrever o esqueleto de um script | **Inventar** métodos e parâmetros que não existem |
| Lembrar a sintaxe de `processing.run` | Misturar a API do **QGIS 2** (`processing.runalg`, `QgsMapLayerRegistry`) com a do QGIS 3 |
| Explicar código linha a linha | Ignorar o CRS (buffer em graus) |
| Interpretar mensagens de erro | Supor nomes de campos e camadas que não são os seus |
| Sugerir otimizações e alternativas | Garantir que o resultado está **correto** — ela não vê seus dados |

## Engenharia de prompts para PyQGIS

Um bom prompt responde a cinco perguntas:

1. **Onde o código vai rodar?** — "Editor do Console Python do QGIS 3.44", "plugin", "standalone".
2. **Quais são os dados?** — camadas, tipo de geometria, **nomes exatos dos campos**, **CRS**, tamanho.
3. **O que fazer?** — passos numerados, na ordem (use o fluxo manual como roteiro).
4. **Como entregar?** — saída em memória ou arquivo, formato, nomes, prints de conferência.
5. **Restrições** — "use `processing.run` e algoritmos `native:`", "sem bibliotecas externas", "comentários em português".

Modelo:

```text
Contexto: script para o Editor do Console Python do QGIS <versão>.
Dados: <arquivo>, camadas <nome (geometria, CRS, campos)>.
Tarefa: <passo 1>; <passo 2>; ...
Saída: <camadas/arquivos/prints esperados>.
Restrições: <API, bibliotecas, estilo>.
```

Mais exemplos em [`apoio/prompts.md`](../prompts.md).

## Quatro usos da IA no ciclo de desenvolvimento

### 1. Gerar

Peça **uma etapa por vez** e execute antes de pedir a próxima. Código longo gerado de uma vez é difícil de revisar.

### 2. Compreender

> "Explique este código linha a linha para um estudante de geoprocessamento. Para cada `processing.run`, diga qual ferramenta da Caixa de Ferramentas é equivalente."

### 3. Depurar

Envie **o código, o traceback completo e o que você esperava**. Exemplo:

```text
Rodei este trecho no QGIS 3.44:
<código>
E recebi:
Traceback (most recent call last):
  File "<input>", line 1, in <module>
AttributeError: module 'processing' has no attribute 'runalg'
O que está errado e como corrigir?
```

### 4. Otimizar

> "Este clip de uma camada com 1 milhão de polígonos demora muito. Como acelerar sem mudar o resultado?"

(Resposta esperada: filtrar antes com `native:extractbylocation`, criar índice espacial, reprojetar só o que for usado.)

## Validação: a responsabilidade é sua

Código que **roda** não é código **correto**. Para todo script gerado com IA:

- [ ] Entendo o que cada linha faz? (Se não, peça explicação.)
- [ ] Os nomes de camadas/campos são os do meu dado?
- [ ] O CRS está correto em cada etapa (`layer.crs().authid()`)?
- [ ] Os resultados conferem com uma execução manual ou com um cálculo de controle?
- [ ] O resultado faz sentido no mapa?
- [ ] Os métodos existem na documentação oficial (`processing.algorithmHelp`, [API PyQGIS](https://qgis.org/pyqgis/))?

## Para fixar

Peça a uma IA um script que "calcule a área de cada município da Paraíba em km²" **sem informar o CRS** e outro **informando** que a camada está em EPSG:4326. Compare: algum dos dois calculou área em graus²?
