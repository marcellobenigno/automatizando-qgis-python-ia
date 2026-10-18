# Módulo 2 — Fundamentos de PyQGIS

⏱ 45 min · [← Módulo 1](01-introducao-automacao.md) · [Módulo 3 →](03-ia-aplicada.md)

PyQGIS é a API Python do QGIS. Neste módulo vemos apenas o necessário para **abrir camadas, ler atributos e executar algoritmos**. Script completo: [`scripts/02_camadas_e_parametros.py`](../scripts/02_camadas_e_parametros.py).

## Objetos principais

| Objeto | Para que serve |
| --- | --- |
| `iface` | A interface do QGIS (camada ativa, mapa, mensagens) — só existe dentro do QGIS |
| `QgsProject.instance()` | O projeto aberto: camadas carregadas, CRS do projeto |
| `QgsVectorLayer` | Uma camada vetorial (arquivo, tabela de banco, camada em memória) |
| `QgsFeature` | Uma feição: geometria + atributos |
| `QgsGeometry` | A geometria: `area()`, `length()`, `buffer()`, `intersects()`... |
| `QgsCoordinateReferenceSystem` | Um CRS, ex.: `QgsCoordinateReferenceSystem("EPSG:31984")` |
| `processing` | Módulo para executar os algoritmos da Caixa de Ferramentas |

## Acessando camadas

```python
GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"

# De um arquivo (GeoPackage: caminho|layername=nome_da_camada)
municipios = QgsVectorLayer(f"{GPKG}|layername=municipios", "municipios", "ogr")
print(municipios.isValid())            # sempre confira!
print(municipios.crs().authid())       # EPSG:4326
print(municipios.featureCount())       # 223

# De uma camada já carregada no projeto
camada = QgsProject.instance().mapLayersByName("municipios")[0]
camada = iface.activeLayer()           # a camada selecionada no painel

# Adicionar ao mapa
QgsProject.instance().addMapLayer(municipios)
```

> `isValid()` retorna `False` quando o caminho ou o nome da camada estão errados — o QGIS **não** gera erro nesse caso. Sempre teste.

## Campos e feições

```python
print([campo.name() for campo in municipios.fields()])

for f in municipios.getFeatures():
    print(f["nome"], f["populacao_total"], f.geometry().area())

# Filtrando com uma expressão (a mesma da "Seleção por expressão")
pedido = QgsFeatureRequest().setFilterExpression('"populacao_total" > 100000')
for f in municipios.getFeatures(pedido):
    print(f["nome"])

# Valores únicos de um campo
idx = municipios.fields().indexOf("mesoregiao")
print(municipios.uniqueValues(idx))
```

## Executando algoritmos

### Descobrindo os parâmetros

```python
processing.algorithmHelp("native:buffer")
```

Mostra cada parâmetro, seu tipo e os valores aceitos — por exemplo, que `END_CAP_STYLE` aceita `0` (arredondado), `1` (plano) ou `2` (quadrado).

### `processing.run`

```python
resultado = processing.run("native:buffer", {
    "INPUT": camada,               # objeto camada, ID ou caminho de arquivo
    "DISTANCE": 3000,              # na unidade do CRS da camada!
    "DISSOLVE": True,
    "OUTPUT": "TEMPORARY_OUTPUT",  # camada em memória
})
buffer = resultado["OUTPUT"]       # o retorno é um dicionário
```

| Valor de `OUTPUT` | Resultado |
| --- | --- |
| `"TEMPORARY_OUTPUT"` | Camada em memória (some ao fechar o QGIS) — ideal para etapas intermediárias |
| `"/pasta/arquivo.gpkg"` | Arquivo salvo; `resultado["OUTPUT"]` é o **caminho** (texto) |
| `"/pasta/arquivo.csv"` | Formato definido pela extensão (`.shp`, `.geojson`, `.csv`, `.xlsx`...) |

`processing.runAndLoadResults(...)` faz o mesmo e já adiciona a saída ao mapa.

### Encadeando algoritmos

A saída de um algoritmo pode ser passada diretamente como entrada do próximo:

```python
pb200 = processing.run("native:extractbyattribute", {
    "INPUT": malha, "FIELD": "rodovia_nome", "OPERATOR": 0, "VALUE": "PB-200",
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

pb200_m = processing.run("native:reprojectlayer", {
    "INPUT": pb200, "TARGET_CRS": "EPSG:31984",
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

aii = processing.run("native:buffer", {
    "INPUT": pb200_m, "DISTANCE": 3000, "DISSOLVE": True,
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
```

## CRS: o erro mais comum

Distâncias e áreas são calculadas **na unidade do CRS da camada**. Em EPSG:4326 a unidade é **grau**: um buffer de `3000` cobriria o planeta. Antes de buffers e áreas, reprojete para um CRS métrico:

- **SIRGAS 2000 / UTM** (EPSG:31984 — fuso 24S; EPSG:31985 — fuso 25S): distorção pequena dentro do fuso — é o que usamos no curso (a PB-200 está no fuso 24);
- **SIRGAS 2000 / Brasil Policônica** (EPSG:5880): um único CRS para o país todo, útil para mapas, mas **distorce distâncias e áreas** longe do meridiano central (−54°). Na Paraíba, a PB-200 mede ~106,9 km em EPSG:5880 contra ~103,8 km em UTM 24S (o campo `extensao` soma 104,25 km);
- para **áreas** de regiões que cruzam fusos, prefira uma projeção **equivalente** (Albers) ou o cálculo elipsoidal (`$area` com elipsoide definido no projeto).

## Exercícios

1. Abra a camada `malha_viaria` e imprima quantas rodovias diferentes existem em `rodovia_nome`.
2. Imprima o nome e a população dos 5 municípios mais populosos.
3. Calcule a extensão total (km) da PB-200 em EPSG:31984 e compare com a soma do campo `extensao`.

<details>
<summary>Respostas</summary>

```python
# 1
malha = QgsVectorLayer(f"{GPKG}|layername=malha_viaria", "malha", "ogr")
print(len(malha.uniqueValues(malha.fields().indexOf("rodovia_nome"))))

# 2
mun = sorted(municipios.getFeatures(), key=lambda f: f["populacao_total"], reverse=True)
for f in mun[:5]:
    print(f["nome"], f["populacao_total"])

# 3 (pb200_m do exemplo acima)
print(sum(f.geometry().length() for f in pb200_m.getFeatures()) / 1000)  # ~103,8 km (campo extensao: 104,25 km)
```
</details>
