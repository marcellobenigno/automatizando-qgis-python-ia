# Exercício extra: a mesma análise com GeoPandas (fora do QGIS)

> Versão alternativa do [exercício principal](README.md), para fazer em Python puro (Colab/Jupyter). Atenção: aqui se sugere EPSG:5880; na prática do QGIS mostramos que, na Paraíba, ela superestima áreas em alguns por cento — compare os resultados usando EPSG:31984.

## Estudo de Caso: Licenciamento Ambiental da Duplicação da Rodovia PB-200 (PB)

### **Contexto**

A rodovia estadual **PB-200** passará por um processo de duplicação. Como analista geospacial responsável pelo Estudo de Impacto Ambiental (EIA/RIMA), sua missão é utilizar a biblioteca **GeoPandas** para processar os dados vetoriais do estado da Paraíba, delimitar as áreas de influência do empreendimento, avaliar o uso do solo impactado e gerar relatórios, mapas e gráficos explicativos.

### **Fonte de Dados**

Todos os dados estão consolidados no arquivo GeoPackage: `/content/drive/MyDrive/pb.gpkg`.

| Camada | Tipo Geométrico | Descrição | 
| ----- | ----- | ----- | 
| `limite_pb` | MultiPolygon | Limite estadual da Paraíba | 
| `municipios` | MultiPolygon | Limites dos 223 municípios paraibanos com dados populacionais | 
| `malha_viaria` | MultiLineString | Rodovias do estado (coluna `rodovia_nome` ou `codigo`) | 
| `uso_ocupacao_2023` | MultiPolygon | Mapeamento de uso e cobertura do solo (`val`, `descricao`, `cor`) | 
| `outorgas` / `pocos` | Point / MultiPoint | Pontos de captação e usos d'água na região | 

> **Atenção quanto ao CRS (Sistema de Referência de Coordenadas):**
>
> 1. Todas as camadas do GeoPackage estão originalmente em coordenadas geográficas **WGS 84 (EPSG:4326)**, cujas unidades são graus decimais. Para realizar cálculos de distância (buffers) e área ($m^2$ ou $km^2$), os dados precisam obrigatoriamente estar em um sistema projetado métrico.
> 2. **Por que não usar UTM?** O estado da Paraíba abrange dois fusos UTM diferentes (**Zone 24S / EPSG:31984** e **Zone 25S / EPSG:31985**). Adoções de fusos UTM isolados em áreas que cruzam zonas geram distorções de escala e descontinuidade espacial.
> 3. **Solução:** Reprojete todos os dados para o sistema plano métrico de abrangência nacional: **SIRGAS 2000 / Brasil Policônica (EPSG:5880)**.

---

### **Roteiro do Exercício**

#### **Etapa 1: Leitura e Preparação dos Dados**

1. Carregue as camadas `municipios`, `malha_viaria` e `uso_ocupacao_2023` contidas em `pb.gpkg`.
2. Filtre o GeoDataFrame da malha viária para obter apenas a rodovia **PB-200**.
3. Reprojete todas as camadas para o CRS **EPSG:5880** (`.to_crs(epsg=5880)`).

#### **Etapa 2: Identificação dos Municípios Afetados**

1. Identifique quais municípios são cortados pela PB-200 (utilize intersecção espacial via `gpd.sjoin` ou `.intersects()`).
2. Exporte a lista dos municípios afetados com suas respectivas populações para um arquivo Excel chamado `municipios_afetados_pb200.xlsx`.

#### **Etapa 3: Delimitação das Áreas de Influência (Buffers)**

1. **Área Diretamente Afetada (ADA):** Crie um buffer de **1.000 metros** (1 km) ao redor da PB-200.
2. **Área de Influência Indireta (AII):** Crie um buffer de **3.000 metros** (3 km) ao redor da PB-200.

#### **Etapa 4: Análise do Impacto Territorial nos Municípios**

1. Realize a interseção espacial (`gpd.overlay`) entre o buffer de **3 km (AII)** e a camada de `municipios`.
2. Calcule a área em $km^2$ da AII que incide sobre cada município afetado.
3. Calcule o **percentual (%) da área total de cada município** contido dentro da faixa do buffer de 3 km.

#### **Etapa 5: Análise do Uso e Ocupação do Solo**

1. Realize o recorte / interseção (`gpd.overlay`) entre a camada `uso_ocupacao_2023` e o buffer de **3 km (AII)**.
2. Calcule a área total (em $km^2$ ou hectares) de cada classe de uso do solo (`descricao`) dentro da AII.

#### **Etapa 6: Elaboração de Mapas Temáticos (Matplotlib)**

Gere três mapas explicativos utilizando a biblioteca `matplotlib`:

* **Mapa 6.1 — Visão Geral dos Municípios Afetados:**
  * Apresente a malha completa dos municípios da Paraíba em tom neutro.
  * Destaque os municípios cortados pela PB-200 em uma cor diferenciada.
  * Plote o traçado da PB-200 em destaque.

* **Mapa 6.2 — Delimitação das Áreas de Influência:**
  * Destaque o trecho da PB-200.
  * Sobreponha a **ADA (Buffer 1 km)** e a **AII (Buffer 3 km)** utilizando cores distintas e transparência (`alpha`).
  * Mantenha os limites dos municípios afetados em segundo plano.

* **Mapa 6.3 — Recorte do Uso e Ocupação do Solo na AII:**
  * Plote o recorte do uso do solo restrito ao buffer de 3 km.
  * Mapeie cada classe de uso utilizando as cores da coluna `cor` (ou uma paleta adequada).
  * Inclua legenda, título e elementos cartográficos básicos.

#### **Etapa 7: Elaboração de Gráficos (Visualização Estatística)**

Crie os seguintes gráficos para integrar o parecer técnico:

* **Gráfico 7.1 — Percentual de Área do Município Afetada pela AII (Gráfico de Barras Horizontais):**
  * **Eixo Y:** Nome dos municípios afetados.
  * **Eixo X:** Porcentagem (%) do território municipal ocupado pelo buffer de 3 km.
  * **Objetivo:** Identificar quais municípios têm a maior proporção de seu território impactado.

* **Gráfico 7.2 — Distribuição do Uso e Ocupação do Solo na AII (Gráfico de Rosca ou Barras):**
  * **Categorias:** Classes de uso do solo (`descricao`).
  * **Valores:** Área em $km^2$ (ou % do total da AII).
  * **Objetivo:** Mostrar quais tipos de cobertura (ex: vegetação nativa, área agrícola, corpo d'água) serão mais impactados.

* **Gráfico 7.3 \[Bônus\] — Uso do Solo por Município (Gráfico de Barras Empilhadas):**
  * **Eixo X:** Municípios afetados.
  * **Eixo Y:** Área ($km^2$) decomposta pelas classes de uso do solo.

---

### **Código de Referência de Suporte (GeoPandas / Python)**

```python
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# 1. Caminho do arquivo e leitura das camadas
gpkg_path = "/content/drive/MyDrive/pb.gpkg"
municipios = gpd.read_file(gpkg_path, layer="municipios")
malha = gpd.read_file(gpkg_path, layer="malha_viaria")
uso_solo = gpd.read_file(gpkg_path, layer="uso_ocupacao_2023")

# 2. Filtro da rodovia PB-200
pb200 = malha[malha['rodovia_nome'] == 'PB-200']

# 3. Reprojeção para SIRGAS 2000 / Brasil Policônica (EPSG:5880)
# Necessário pois a Paraíba cruza os fusos UTM 24S e 25S
pb200_poly = pb200.to_crs(epsg=5880)
municipios_poly = municipios.to_crs(epsg=5880)
uso_solo_poly = uso_solo.to_crs(epsg=5880)

# 4. Criação das Áreas de Influência (Buffers em metros)
ada_1km = pb200_poly.buffer(1000)
aii_3km = pb200_poly.buffer(3000)

# 5. Cálculo de áreas (Lembrete: área calculada em m², divida por 1_000_000 para km²)
# Exemplo de conversão:
# aii_df['area_km2'] = aii_df.geometry.area / 1000000
```