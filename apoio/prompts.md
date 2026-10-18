# Biblioteca de prompts

Prompts usados no [Módulo 3](textos/03-ia-aplicada.md) e na [Parte 3 da prática](../modulos/pb200/README.md#parte-3--a-ia-na-criação-do-algoritmo). Substitua o que está entre `< >`. Funcionam em qualquer assistente (ChatGPT, Claude, Gemini, Copilot...).

> Lembre-se: **nunca** cole dados pessoais ou sigilosos. Descreva a estrutura dos dados (camadas, campos, CRS), não o conteúdo.

## 1. Gerar

### Script completo, com contexto

```text
Você é especialista em PyQGIS. Escreva um script para o Editor do Console
Python do QGIS <3.44>, usando processing.run e algoritmos "native:".

Dados: GeoPackage em GPKG = "<caminho>", camadas em <EPSG:4326>:
- <camada> (<geometria>), campos <campo1>, <campo2>
- ...

Passos:
1. <...>
2. <...>

Saída: <camadas em memória / arquivo .gpkg / CSV>; imprima o resultado de cada etapa.
Restrições: parâmetros em constantes no topo, comentários em português,
nada de APIs do QGIS 2 (processing.runalg, QgsMapLayerRegistry).
```

### Uma etapa por vez

```text
Vamos construir o script por etapas. Escreva apenas a etapa <N>: <descrição>.
A entrada é a variável <nome> criada na etapa anterior. Termine com um print
que me permita conferir o resultado.
```

### Do log do QGIS para o script

```text
Executei esta ferramenta pela interface e o Log mostrou:
<cole o conteúdo da aba Log / "Copiar como comando Python">
Transforme em uma chamada processing.run cuja saída fique em memória e seja
usada como entrada de native:buffer com 3000 m.
```

### Limpeza e importação de dados

```text
Tenho uma pasta com shapefiles com estes problemas: alguns sem arquivo .prj
(sei que estão em SIRGAS 2000 geográfico, EPSG:4674), nomes de arquivo com
espaços e acentos, e nomes de campos com espaços e acentos.
Escreva um script PyQGIS para o QGIS 3.44 que:
1. percorra todos os .shp da pasta <caminho>;
2. defina o CRS dos que não têm (native:assignprojection);
3. padronize os nomes de campos (minúsculas, sem acento, "_" no lugar de espaço);
4. importe todos para um único GeoPackage, com nomes de camada padronizados.
Imprima um relatório do que foi alterado em cada arquivo.
```

## 2. Compreender

```text
Explique este código linha a linha para um estudante de geoprocessamento.
Para cada processing.run, diga qual ferramenta da Caixa de Ferramentas é
equivalente e o que significa cada parâmetro.
<código>
```

```text
Por que o script usa native:extractbylocation antes do native:clip?
O resultado seria diferente sem ele?
```

## 3. Depurar

```text
Rodei este código no Console Python do QGIS <versão>:
<código>
Erro completo:
<traceback inteiro>
Eu esperava: <o que deveria acontecer>.
Explique a causa e proponha a correção mínima.
```

```text
O script roda sem erro, mas o buffer de 3000 m ficou do tamanho do estado.
<código>
O que pode estar errado?
```

## 4. Otimizar

```text
Este fluxo demora <N> minutos. A camada <nome> tem <N> feições.
<código>
Como deixá-lo mais rápido sem alterar o resultado? Explique o ganho esperado
de cada sugestão.
```

## 5. Validar

```text
Liste verificações que eu deveria fazer para confirmar que este script
calcula corretamente a área de cada classe de uso do solo dentro do buffer.
Inclua verificações de CRS, geometrias inválidas, somas de controle e
comparação com uma referência independente.
```

## 6. Transformar em ferramenta

```text
Transforme este script em um QgsProcessingAlgorithm para a Caixa de
Ferramentas do QGIS 3.44. Parâmetros: <lista>. Saída: <descrição>.
Use processing.run com is_child_algorithm=True, context e feedback.
```
