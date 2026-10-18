# Prática: licenciamento ambiental da duplicação da PB-200

> Exercício central do minicurso **Automatizando o QGIS com Python e IA**.
> Faremos a mesma análise três vezes: **à mão**, **com o Processing Framework em Python** e **com a ajuda de uma IA**. Depois, vamos melhorá-la.

## Contexto

A rodovia estadual **PB-200** (Juazeirinho → Santo André → Parari → Serra Branca → Coxixola → Congo, ~107 km) passará por um processo de duplicação. Como analista de geoprocessamento do Estudo de Impacto Ambiental, você precisa responder:

1. Quais **municípios** são atingidos pela Área de Influência Indireta (AII, faixa de **3 km**) e qual percentual do território de cada um ela ocupa?
2. Qual a **área (ha) de cada classe de uso e ocupação do solo** dentro da AII?
3. Qual a área de cada classe **em cada município**? (tabela para o relatório)

## Dados

Arquivo `minicurso_dados.gpkg` (ver [`dados_curso/README.md`](../../dados_curso/README.md)). Todas as camadas estão em **WGS 84 (EPSG:4326)**.

| Camada | Geometria | Campos usados |
| --- | --- | --- |
| `malha_viaria` | MultiLineString | `rodovia_nome` (ex.: `PB-200`) |
| `municipios` | MultiPolygon | `nome`, `cod_ibge_m`, `populacao_total` |
| `uso_ocupacao_solo` | MultiPolygon (~1 milhão de feições) | `val`, `descricao`, `cor` |

> **Sobre o CRS.** Buffer em metros e área em hectares exigem um sistema projetado. Usamos **SIRGAS 2000 / UTM 24S (EPSG:31984)**, pois a PB-200 está toda no fuso 24. A Paraíba, porém, cruza os fusos 24S e 25S: para outras rodovias, o fuso certo é escolhido automaticamente (Desafio 4.2). Evitamos a Brasil Policônica (EPSG:5880) nos cálculos: longe do seu meridiano central (−54°) ela distorce distâncias e áreas em alguns por cento — veja a validação na Parte 3.

## Roteiro

| Parte | O que fazemos | Tempo |
| --- | --- | --- |
| [1 — Fluxo manual](#parte-1--fluxo-manual-na-interface-do-qgis) | Executar cada ferramenta pela interface e entender o encadeamento | 30 min |
| [2 — Processing Framework](#parte-2--automatizando-com-o-processing-framework) | Transformar cada passo em `processing.run(...)` e juntar tudo em um script | 60 min |
| [3 — IA na criação do algoritmo](#parte-3--a-ia-na-criação-do-algoritmo) | Usar IA para gerar, explicar, depurar e validar o script | 45 min |
| [4 — Melhorias e desafios](#parte-4--melhorias-e-desafios) | Tabela dinâmica, várias rodovias, interface de seleção | 30 min |

---

## Parte 1 — Fluxo manual na interface do QGIS

**Objetivo:** executar a análise uma vez, à mão, prestando atenção em *quais ferramentas* são usadas, *em que ordem* e *quais parâmetros* são preenchidos. É exatamente isso que vamos automatizar depois.

> As capturas de tela estão com o QGIS em inglês; no texto aparecem os nomes em português e, entre parênteses, em inglês. Todas as saídas foram gravadas na pasta `dados_curso/pb200/resultados/` (abreviada como `resultados/` no texto).

### 1.0 Carregar os dados

No painel **Navegador (Browser)**, expanda `minicurso_dados.gpkg` e arraste para o mapa as camadas `malha_viaria` (com estilo separando Rodovias Federais e Estaduais), `limite_pb`, `uso_ocupacao_solo` e `estados_ne`. O CRS do projeto é **EPSG:4326** (canto inferior direito).

![Camadas carregadas](../../imgs/pb200/1-introducao.png)

### 1.1 Selecionar a PB-200

Com a camada `malha_viaria` ativa, clique no botão **Selecionar feições usando uma expressão (Select Features by Expression)**:

![Botão Selecionar por expressão](../../imgs/pb200/2-ferramenta-select-by-expression.png)

Monte a expressão abaixo. Dê duplo clique em `rodovia_nome` e use **All Unique** (com a busca `pb-200`) para conferir o valor exato. Depois clique em **Select Features**.

```
"rodovia_nome" = 'PB-200'
```

![Expressão de seleção](../../imgs/pb200/3-select-by-expression.png)

### 1.2 Exportar só a rodovia

Botão direito em `malha_viaria` → **Exportar (Export) → Salvar feições selecionadas como... (Save Selected Features As...)**:

![Exportar feições selecionadas](../../imgs/pb200/4-export-selected-features.png)

Formato **ESRI Shapefile**, arquivo `resultados/pb_200.shp`, CRS **EPSG:4326**, com **Salvar apenas as feições selecionadas (Save only selected features)** marcado:

![Configurações de exportação](../../imgs/pb200/5-export-settings.png)

A camada `pb_200` aparece sobre o uso do solo:

![PB-200 exportada](../../imgs/pb200/6-pb-200-exportada.png)

### 1.3 Abrir a Caixa de Ferramentas de Processamento

Clique no ícone de engrenagem da barra de ferramentas (destacado em vermelho), ou use **Processamento → Caixa de Ferramentas** (`Ctrl+Alt+T`). O painel **Processing Toolbox** abre à direita, com os algoritmos agrupados por categoria (*Vector general*, *Vector geometry*, *Vector overlay*...). Todas as ferramentas a seguir estão nele, e **todas podem ser chamadas por Python**.

![Caixa de Ferramentas](../../imgs/pb200/7-toolbox.png)

### 1.4 Reprojetar para UTM

**Geral para vetores (Vector general) → Reprojetar camada (Reproject Layer)**: entrada `pb_200 [EPSG:4326]`, CRS de destino **EPSG:31984 – SIRGAS 2000 / UTM zone 24S**, saída `resultados/pb_200_utm.shp`.

![Reprojetar para UTM](../../imgs/pb200/8-reproject-utm.png)

### 1.5 Buffer de 3 km (AII)

**Geometria de vetores (Vector geometry) → Buffer**: entrada `pb_200_utm [EPSG:31984]`, distância **3 quilômetros** (o QGIS converte a unidade porque a camada está em metros), segmentos `5`, extremidade e junção arredondadas, **Dissolver resultado (Dissolve result)** marcado, saída `resultados/pb_200_utm_buffer_3km.shp`.

![Buffer de 3 km](../../imgs/pb200/9-buffer_3km.png)

O resultado é uma faixa contínua ao longo da rodovia:

![Resultado do buffer](../../imgs/pb200/10-buffer_3km-resultado.png)

> Note que o seletor de unidades (*kilometers*) só aparece porque a camada de entrada está em um CRS métrico. Com a `pb_200` em EPSG:4326, a distância seria em **graus**.

### 1.6 Voltar ao CRS dos dados e recortar o uso do solo

Reprojete o buffer de volta para o CRS das demais camadas: **Reprojetar camada**, entrada `pb_200_utm_buffer_3km [EPSG:31984]`, destino **EPSG:4326 – WGS 84**, saída `resultados/pb_200_buffer_3km.shp`.

![Reprojetar o buffer para WGS 84](../../imgs/pb200/11-reproject-wgs84-latlon.png)

Depois, **Sobreposição de vetores (Vector overlay) → Recortar (Clip)**: entrada `uso_ocupacao_solo [EPSG:4326]`, sobreposição `pb_200_buffer_3km [EPSG:4326]`, saída `resultados/clip_uso_ocupacao_buffer_3km.shp`.

![Clip do uso do solo pelo buffer](../../imgs/pb200/12-clip-uso-ocupacao-buffer-3km.png)

A camada recortada aparece com um estilo genérico (marrom). Para reaproveitar as cores das classes, clique com o botão direito em `uso_ocupacao_solo` → **Estilos (Styles) → Copiar estilo (Copy Style) → Todas as categorias de estilo (All Style Categories)**:

![Copiando o estilo](../../imgs/pb200/13-copiando-o-estilo.png)

Depois, botão direito em `clip_uso_ocupacao_buffer_3km` → **Estilos → Colar estilo (Paste Style) → Todas as categorias de estilo**:

![Colando o estilo](../../imgs/pb200/14-colando-o-estilo.png)

Resultado: o uso do solo apenas dentro da AII, com a camada `municipios` ao fundo:

![Resultado do recorte](../../imgs/pb200/15-resultado-clip-uso-ocupacao-solo.png)

### 1.7 Cruzar com os municípios

Para saber **em que município** está cada pedaço de uso do solo, cruzamos o recorte com a camada `municipios`. O **Recortar (Clip)** com os municípios como sobreposição (saída `clip_uso_ocupacao_buffer_municipios.shp`) **não basta**: ele corta as geometrias, mas não traz os atributos dos municípios.

![Clip pelos municípios](../../imgs/pb200/16-clip-uso-ocupacao-municipios.png)

A ferramenta certa é a **Interseção (Intersection)**, em **Vetor (Vector) → Geoprocessamento (Geoprocessing Tools) → Interseção...**:

![Menu de geoprocessamento](../../imgs/pb200/17-overlay-menu.png)

Use como entrada `clip_uso_ocupacao_buffer_3km` e como sobreposição `municipios`. Mantenha os campos `val, descricao` da entrada e `nome, cod_ibge_m` da sobreposição, e salve em `resultados/overlay_uso_ocupacao_municipios.shp`:

![Interseção com os municípios](../../imgs/pb200/18-overlay-uso-ocupacao-municipios.png)

Por fim, use **Dissolver (Dissolve)** com os campos `val`, `descricao` e `nome` para obter uma feição por **município × classe**. A saída, `dissolve_uso_ocupacao_municipios`, tem 66 feições.

### 1.8 Calcular a área e exportar o relatório

Botão direito em `dissolve_uso_ocupacao_municipios` → **Abrir tabela de atributos (Open Attribute Table)**:

![Abrir tabela de atributos](../../imgs/pb200/19-open-attribute-table.png)

Abra a **Calculadora de campos (Field Calculator)** (ícone do ábaco, destacado em vermelho) e crie um campo novo `area_ha`, do tipo *Decimal number (real)*, com precisão 2 e a expressão `$area / 10000`. Como a camada está em EPSG:4326, o `$area` é calculado **sobre o elipsoide**, em m²:

![Cálculo de área em ha](../../imgs/pb200/20-calculo-area-ha.png)

Exporte com botão direito → **Exportar → Salvar feições como...**: formato **MS Office Open XML spreadsheet [XLSX]**, arquivo `resultados/relatorio_area_classe_municipio.xlsx`, campos `val`, `descricao`, `nome` e `area_ha` (com `cod_ibge_m` desmarcado):

![Exportar para Excel](../../imgs/pb200/21-exportar-excel.png)

O relatório final traz uma linha por município × classe:

![Relatório final no Excel](../../imgs/pb200/22-relatorio-excel-final.png)

### Resumo do fluxo manual

| # | Ferramenta na interface | Saída | ID do algoritmo (Python) |
| --- | --- | --- | --- |
| 1 | Selecionar por expressão + Salvar feições selecionadas | `pb_200.shp` | `native:extractbyattribute` / `native:extractbyexpression` |
| 2 | Reprojetar camada (→ EPSG:31984) | `pb_200_utm.shp` | `native:reprojectlayer` |
| 3 | Buffer 3 km, dissolvido | `pb_200_utm_buffer_3km.shp` | `native:buffer` |
| 4 | Reprojetar camada (→ EPSG:4326) | `pb_200_buffer_3km.shp` | `native:reprojectlayer` |
| 5 | Recortar (Clip) + copiar/colar estilo | `clip_uso_ocupacao_buffer_3km.shp` | `native:clip` |
| 6 | Interseção com municípios | `overlay_uso_ocupacao_municipios.shp` | `native:intersection` |
| 7 | Dissolver por `val`, `descricao`, `nome` | `dissolve_uso_ocupacao_municipios` | `native:dissolve` |
| 8 | Calculadora de campos (`area_ha`) | — | `native:fieldcalculator` |
| 9 | Salvar feições como... (XLSX) | `relatorio_area_classe_municipio.xlsx` | `native:savefeatures` |

> **Para discutir:** foram 9 etapas, dezenas de cliques e uma dúzia de arquivos intermediários na pasta `resultados/`. Agora imagine repetir para **todas as rodovias estaduais**, ou refazer porque o mapeamento de uso do solo foi atualizado. É aqui que entra a automação.

---

## Parte 2 — Automatizando com o Processing Framework

Nesta parte refazemos cada passo da Parte 1 como código, em tarefas curtas e progressivas. A regra de ouro é: **tudo o que você roda pela Caixa de Ferramentas tem um equivalente `processing.run("id_do_algoritmo", {parâmetros})`**, e o próprio QGIS mostra esse código para você.

### Tarefa 2.1 — Abrir as camadas pelo Console Python

- **Dados:** `minicurso_dados.gpkg`
- **Ferramentas:** Console Python (`Ctrl+Alt+P`)
- **Objetivo:** carregar camadas de um GeoPackage e inspecioná-las com PyQGIS

1. Abra o Console Python e clique em **Mostrar editor**.
2. Guarde o caminho do GeoPackage em uma variável (no Windows use `/` ou `r"C:\..."`):

   ```python
   GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"
   malha = QgsVectorLayer(f"{GPKG}|layername=malha_viaria", "malha_viaria", "ogr")
   print(malha.isValid(), malha.featureCount(), malha.crs().authid())
   ```

3. Liste os campos e veja alguns valores:

   ```python
   print([c.name() for c in malha.fields()])
   for f in malha.getFeatures(QgsFeatureRequest().setLimit(5)):
       print(f["rodovia_nome"], f["descricao"])
   ```

4. Para ver a camada no mapa: `QgsProject.instance().addMapLayer(malha)`.

### Tarefa 2.2 — Do clique ao código: filtrar a rodovia

- **Ferramentas:** Caixa de Ferramentas, aba **Log**, **Histórico de processamento (`Ctrl+Alt+H`)**
- **Objetivo:** descobrir o código Python de uma ferramenta a partir da execução manual

> ### 🎮 Cheat code: o Histórico de Processamento (`Ctrl+Alt+H`)
>
> **Este é o atalho mais importante do minicurso.** Toda ferramenta que você roda pela Caixa de Ferramentas — inclusive as da Parte 1 — fica registrada em **Processamento → Histórico** (`Ctrl+Alt+H`) **já escrita como `processing.run(...)`**, com o ID do algoritmo e todos os parâmetros preenchidos.
>
> O fluxo para quem está começando é sempre o mesmo:
>
> 1. **rode a ferramenta à mão**, pela interface, uma vez;
> 2. aperte **`Ctrl+Alt+H`** e clique na última linha do histórico;
> 3. **copie o comando**, cole no editor e troque os caminhos fixos por variáveis.
>
> Você não precisa decorar nenhum ID nem nome de parâmetro: o QGIS escreve o código para você. Na dúvida, rode à mão e consulte o Histórico.

1. Na Caixa de Ferramentas, abra **Extrair por atributo** e preencha: entrada `malha_viaria`, campo `rodovia_nome`, operador `=`, valor `PB-200`. Execute.
2. Aperte **`Ctrl+Alt+H`**: o comando está lá, pronto para copiar. Outras formas de chegar ao mesmo código: a aba **Log** da própria janela da ferramenta (mostra o ID do algoritmo e os parâmetros usados) ou o botão **Avançado → Copiar como comando Python**.
3. Cole no editor e ajuste:

   ```python
   resultado = processing.run("native:extractbyattribute", {
       "INPUT": malha,
       "FIELD": "rodovia_nome",
       "OPERATOR": 0,          # 0 = "="
       "VALUE": "PB-200",
       "OUTPUT": "TEMPORARY_OUTPUT",
   })
   pb200 = resultado["OUTPUT"]
   print(pb200.featureCount())   # 6 trechos
   ```

4. `processing.run` devolve um **dicionário**; a camada gerada está em `resultado["OUTPUT"]`. Use `processing.algorithmHelp("native:extractbyattribute")` para ver todos os parâmetros e valores aceitos.

> **Dica rápida — blinde o filtro contra erros de digitação.** O `=` exige igualdade exata: se a tabela tiver `" pb-200 "`, `"PB 200"` ou `"pb-200"`, o filtro devolve **0 feições** e o resto do script roda sobre uma camada vazia, sem erro nenhum. Normalize os dois lados da comparação:
>
> ```python
> RODOVIA = " pb 200 "                                   # digitado pelo usuário
> alvo = RODOVIA.strip().upper().replace(" ", "-")       # -> 'PB-200'
>
> # Do lado da tabela, a mesma limpeza em uma expressão do QGIS
> pb200 = processing.run("native:extractbyexpression", {
>     "INPUT": malha,
>     "EXPRESSION": f"""replace(upper(trim("rodovia_nome")), ' ', '-') = '{alvo}'""",
>     "OUTPUT": "TEMPORARY_OUTPUT",
> })["OUTPUT"]
>
> if pb200.featureCount() == 0:
>     raise ValueError(f"Rodovia {alvo} não encontrada em malha_viaria")
> ```
>
> `trim`/`upper`/`replace` nas expressões do QGIS fazem o mesmo que `.strip()`/`.upper()`/`.replace()` no Python. E o `raise` no final faz o script **parar com uma mensagem clara** em vez de seguir com uma camada vazia.

### Tarefa 2.3 — Encadear algoritmos: reprojetar e gerar o buffer

- **Objetivo:** usar a saída de um algoritmo como entrada do próximo, sem arquivos intermediários

```python
pb200_m = processing.run("native:reprojectlayer", {
    "INPUT": pb200,
    "TARGET_CRS": "EPSG:31984",
    "OUTPUT": "TEMPORARY_OUTPUT",
})["OUTPUT"]

aii = processing.run("native:buffer", {
    "INPUT": pb200_m,
    "DISTANCE": 3000,
    "DISSOLVE": True,
    "OUTPUT": "TEMPORARY_OUTPUT",
})["OUTPUT"]

print(next(aii.getFeatures()).geometry().area() / 1e6, "km²")
QgsProject.instance().addMapLayer(aii)
```

**Exercício:** gere também a ADA, com buffer de 1 km.

> **Pegadinha clássica:** rode o buffer com `"INPUT": pb200` (ainda em EPSG:4326). O que acontece com `DISTANCE: 3000`? (Dica: a unidade do CRS é grau.)

### Tarefa 2.4 — Recortar o uso do solo

- **Objetivo:** aplicar o Clip e lidar com uma camada grande

A camada `uso_ocupacao_solo` tem cerca de **1 milhão de polígonos**. Recortá-la inteira é lento; por isso, primeiro **extraímos só o que toca a AII** (usa índice espacial) e depois reprojetamos e recortamos:

```python
uso = QgsVectorLayer(f"{GPKG}|layername=uso_ocupacao_solo", "uso", "ogr")

uso_perto = processing.run("native:extractbylocation", {
    "INPUT": uso, "PREDICATE": [0],   # 0 = intersecta
    "INTERSECT": aii, "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
uso_perto = processing.run("native:fixgeometries", {
    "INPUT": uso_perto, "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
uso_m = processing.run("native:reprojectlayer", {
    "INPUT": uso_perto, "TARGET_CRS": "EPSG:31984",
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
uso_aii = processing.run("native:clip", {
    "INPUT": uso_m, "OVERLAY": aii, "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
```

> ### ⚖️ Regra de ouro do analista ambiental: `native:fixgeometries` antes de qualquer sobreposição
>
> Bases reais — **CAR, MapBiomas, IBGE**, mapeamentos de consultorias — quase sempre chegam com **topologia inválida**: polígonos que se autointersectam (“gravatinhas”), anéis mal fechados, vértices duplicados, buracos fora do polígono. Ninguém percebe isso ao olhar o mapa, mas as operações de sobreposição (Clip, Interseção, Dissolver) dependem de geometrias válidas.
>
> Rodar um Clip sobre 1 milhão de feições sem corrigir antes é pedir para o processamento **abortar no meio com `Feature has invalid geometry`** depois de vários minutos — ou, nos piores casos, **derrubar o QGIS sem aviso**, levando junto o trabalho não salvo.
>
> Por isso, no script acima o `fixgeometries` vem **logo depois do `extractbylocation`** (que reduz a camada) e **antes do `clip`**. Corrigir só as feições próximas da AII é muito mais rápido do que corrigir a camada inteira. Adote como hábito: **dados de terceiros → `fixgeometries` → sobreposição.**

### Tarefa 2.5 — Municípios, área e estatísticas

- **Objetivo:** reproduzir a interseção, a calculadora de campos e o resumo por classe

```python
municipios = QgsVectorLayer(f"{GPKG}|layername=municipios", "municipios", "ogr")
municipios_m = processing.run("native:reprojectlayer", {
    "INPUT": municipios, "TARGET_CRS": "EPSG:31984",
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

uso_mun = processing.run("native:intersection", {
    "INPUT": uso_aii, "OVERLAY": municipios_m,
    "INPUT_FIELDS": ["val", "descricao"],
    "OVERLAY_FIELDS": ["nome", "cod_ibge_m"],
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

uso_mun = processing.run("native:fieldcalculator", {
    "INPUT": uso_mun, "FIELD_NAME": "area_ha", "FIELD_TYPE": 0,  # 0 = decimal
    "FORMULA": "$area / 10000", "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

tabela = processing.run("qgis:statisticsbycategories", {
    "INPUT": uso_mun, "VALUES_FIELD_NAME": "area_ha",
    "CATEGORIES_FIELD_NAME": ["nome", "descricao"],
    "OUTPUT": "/caminho/para/dados_curso/pb200/resultados/uso_municipio_classe.csv"})
```

`qgis:statisticsbycategories` substitui o **Dissolver + Calculadora de campos** do fluxo manual: ele soma `area_ha` para cada combinação município × classe.

**Exercício:** faça o mesmo agrupando só por `descricao` e confira se a soma bate com a área da AII.

### Tarefa 2.6 — Juntar tudo em um script

- **Ferramentas:** Editor do Console Python
- **Objetivo:** ter um único arquivo, parametrizado, que refaz a análise inteira

O resultado das tarefas anteriores, organizado e comentado, está em [`03_fluxo_pb200.py`](03_fluxo_pb200.py). Abra-o no editor, ajuste `GPKG` e `PASTA_SAIDA` no topo e clique em **Executar**. Ele:

- deixa os parâmetros (rodovia, CRS, distâncias) em constantes no topo;
- grava as camadas em um único GeoPackage (`native:package`) e as tabelas em CSV;
- imprime verificações de consistência ao final.

Saída esperada (QGIS 3.44, ~3 min, quase tudo no recorte do uso do solo):

```
[3] AII (3000 m): 607.93 km²
[4] Municípios afetados: 11
      Santo André                 100.13 km²  50.60 %
      Coxixola                     85.71 km²  50.41 %
      Parari                       79.51 km²  38.25 %
      ...
[5] Uso do solo na AII
      Pastagem                           36432.56 ha
      Formação Savânica                  12913.48 ha
      Mosaico de Usos                     7444.19 ha
      ...
[7] Verificações
      Soma AII nos municípios: 607.93 km² (100.0% da AII)
      Soma do uso do solo:     607.93 km² (100.0% da AII)
```

> **Dica rápida — acalme o usuário com o `QgsMessageLog`.** Três minutos com o QGIS parado parecem uma eternidade, e a tentação é fechar o programa achando que travou. Escreva mensagens de andamento na aba **Log de mensagens** (**Exibir → Painéis → Log de mensagens**), em uma aba própria do seu script:
>
> ```python
> from qgis.core import QgsMessageLog, Qgis
> from qgis.PyQt.QtCore import QCoreApplication
>
> def avisar(msg):
>     QgsMessageLog.logMessage(msg, "PB-200", Qgis.Info)  # aba "PB-200" no painel de Log
>     QCoreApplication.processEvents()                     # deixa a interface redesenhar
>
> avisar("Etapa 4/7: recortando o uso do solo (pode levar ~3 min)...")
> ```
>
> O `processEvents()` é o que faz a mensagem aparecer **na hora**: enquanto o script roda, a interface do QGIS fica ocupada e só se atualiza quando você a deixa respirar. Uma mensagem antes de cada etapa demorada já basta para o usuário saber que o script está vivo. Use `Qgis.Warning` ou `Qgis.Critical` para destacar problemas.

Compare com a planilha do fluxo manual (`resultados/relatorio_area_classe_municipio.xlsx`):

| Município | Classe | Manual (ha) | Script (ha) |
| --- | --- | ---: | ---: |
| Juazeirinho | Pastagem | 4.139,53 | 4.143,42 |
| Serra Branca | Área Urbanizada | 258,79 | 259,01 |
| Taperoá | Formação Savânica | 128,69 | 128,80 |
| Caraúbas | Formação Savânica | 50,77 | 50,81 |

A diferença (< 0,1%) vem do cálculo de área: no fluxo manual, `$area` foi calculado na camada em EPSG:4326, sobre o elipsoide; no script, a área é plana, em UTM.

### Tarefa 2.7 (opcional) — O mesmo fluxo no Modelador Gráfico

Em **Processamento → Modelador gráfico**, monte o fluxo arrastando *Extrair por atributo → Reprojetar → Buffer → Recortar*. Depois use **Exportar → Exportar como script Python** e compare com o seu código: o modelo vira um `QgsProcessingAlgorithm`, a mesma estrutura de [`05_processing_script_tool.py`](05_processing_script_tool.py).

---

## Parte 3 — A IA na criação do algoritmo

A IA generativa (ChatGPT, Claude, Gemini, Copilot...) é ótima para **escrever o primeiro rascunho, explicar código e interpretar erros** — mas não conhece os seus dados e frequentemente mistura APIs de versões diferentes do QGIS. O jeito produtivo de usá-la é: **você define o fluxo (Parte 1), a IA ajuda a escrever o código (Parte 2), e você valida**. Mais prompts em [`prompts/prompts-exemplo.md`](../../apoio/prompts.md).

### 3.1 Engenharia de prompt para GIS: prompt falho × prompt bom

A IA não vê o seu GeoPackage, não sabe que a camada está em graus nem que tem 1 milhão de polígonos. **Tudo o que você não disser, ela vai chutar** — e o chute costuma ser o exemplo mais comum da internet, não o seu caso. Vamos ver isso na prática.

#### ❌ O prompt falho

```text
Faça um script PyQGIS para gerar um buffer de 3km na PB-200 e recortar o uso
do solo.
```

Parece razoável, mas a IA vai preencher as lacunas sozinha. O resultado típico **roda** (ou quase), mas está errado:

| O que faltou no prompt | O que a IA costuma fazer | Consequência |
| --- | --- | --- |
| CRS dos dados | `native:buffer` direto na camada em EPSG:4326, com `DISTANCE: 3000` | Buffer de 3000 **graus**: um polígono cobrindo o planeta inteiro |
| Tamanho da camada | `native:clip` direto nos ~1 milhão de polígonos | Script “travado” por muitos minutos, ou QGIS fechando |
| Versão do QGIS | Mistura `processing.runalg` e `QgsMapLayerRegistry` (QGIS 2) | `AttributeError` logo na primeira linha |
| Nome da camada e do campo | Inventa `roads.shp` e `"name" = 'PB-200'` | 0 feições, ou erro de camada inválida |
| Onde o código roda | Script standalone com `QgsApplication.initQgis()` | Não funciona colado no Console |
| Formato da saída | Só adiciona a camada ao mapa | Nada de área por classe nem tabela para o relatório |

**Exercício:** mande esse prompt para uma IA, rode o código e anote quantos destes problemas aparecem.

#### ✅ O prompt bom

Um bom prompt diz **papel, versão do QGIS, onde o código vai rodar, dados (camadas, campos, CRS, volume), passos e formato da saída**, além de **regras** que evitam os erros conhecidos. Note que os passos são exatamente a tabela-resumo da Parte 1:

```text
Você é especialista em PyQGIS. Escreva um script para o Editor do Console
Python do QGIS 3.44 (use processing.run e algoritmos "native:").

Dados: GeoPackage em GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg", todas as camadas
em EPSG:4326:
- malha_viaria (linhas), campo rodovia_nome (ex.: 'PB-200')
- municipios (polígonos), campos nome, cod_ibge_m
- uso_ocupacao_solo (polígonos, ~1 milhão de feições), campos val, descricao

Passos:
1. extrair a rodovia 'PB-200';
2. reprojetar para EPSG:31984 (SIRGAS 2000 / UTM 24S);
3. buffer de 3000 m dissolvido;
4. recortar o uso do solo pelo buffer (a camada é grande, otimize);
5. intersectar com os municípios e calcular area_ha;
6. somar area_ha por município e classe e salvar em CSV.

Regras: saídas intermediárias em memória ("TEMPORARY_OUTPUT"), parâmetros em
constantes no topo, comentários em português, print do resultado de cada etapa.
Não use APIs do QGIS 2 (processing.runalg, QgsMapLayerRegistry).
```

#### O que mudou: a anatomia de um prompt para GIS

| Ingrediente | No prompt bom | Erro que evita |
| --- | --- | --- |
| **Papel** | “Você é especialista em PyQGIS” | Respostas genéricas de Python |
| **Ambiente e versão** | “Editor do Console Python do QGIS 3.44”, “`processing.run`” | Código standalone ou de QGIS 2 |
| **Dados** | Caminho, nomes das camadas e campos, **CRS**, **~1 milhão de feições** | Nomes inventados, buffer em graus, clip lento |
| **Passos** | A sequência do fluxo manual, com o CRS métrico explícito | A IA decidir o método por você |
| **Saída** | CSV com `area_ha` por município × classe | Resultado que não serve para o relatório |
| **Regras** | Memória, constantes no topo, `print` por etapa, sem QGIS 2 | Código difícil de conferir e de reaproveitar |

> **Engenharia de prompt para GIS, em uma frase:** escreva o prompt como se fosse passar o trabalho para um estagiário competente que **nunca viu os seus dados**. A Parte 1 não foi perda de tempo: foi ela que te deu os passos, os nomes e os parâmetros para escrever esse prompt.

### 3.2 Gerar por etapas, não tudo de uma vez

Peça uma etapa por vez e **rode cada uma antes de pedir a próxima** — é o mesmo desenvolvimento incremental da Parte 2. Se a IA errar na etapa 4, você descobre na etapa 4, e não depois de 150 linhas.

```text
Agora só a etapa 1. Depois de rodar, imprima o número de feições encontradas.
```

### 3.3 Usar a IA para explicar (e documentar) o script

Código que você não entende é código que você não consegue validar nem manter. Antes de seguir, peça para a IA **explicar e documentar** o que ela gerou — e leia a explicação com o script aberto ao lado.

**Comentar linha a linha e criar a docstring:**

```text
Comente este script linha a linha, em português, explicando o que cada
processing.run faz e por que ele está nessa ordem. No topo do arquivo, crie
uma docstring que explique:
- o objetivo do script e o contexto (AII da duplicação da PB-200);
- cada constante/variável de configuração (GPKG, RODOVIA, CRS_METRICO,
  DIST_AII, PASTA_SAIDA...): o que é, unidade e valor esperado;
- as entradas, as saídas geradas e onde são gravadas.
Não altere a lógica do código: só acrescente comentários e a docstring.
```

O resultado esperado é algo assim no topo do arquivo:

```python
"""
Área de Influência Indireta (AII) da duplicação da PB-200.

Gera um buffer de DIST_AII metros ao redor da rodovia, recorta o uso do solo
e soma a área (ha) de cada classe por município.

Configuração:
    GPKG         caminho do minicurso_dados.gpkg (camadas em EPSG:4326)
    RODOVIA      valor de rodovia_nome a analisar, ex.: 'PB-200'
    CRS_METRICO  CRS projetado para buffer e áreas, ex.: 'EPSG:31984' (UTM 24S)
    DIST_AII     largura da faixa, em metros (3000)
    PASTA_SAIDA  pasta onde são gravados o GeoPackage e os CSV
"""
```

> **Atenção à última linha do prompt.** “Não altere a lógica” é essencial: sem ela, a IA às vezes “melhora” o código enquanto comenta e introduz erros novos. Compare o antes e o depois.

**Perguntar o porquê das escolhas:**

```text
Explique linha a linha o que este trecho faz e por que o extractbylocation vem
antes do clip. Quais parâmetros de native:buffer eu deixei no padrão e o que
eles controlam?
```

Confira a explicação com `processing.algorithmHelp("native:buffer")` — a ajuda oficial é a fonte da verdade.

### 3.4 Depurar com a mensagem de erro completa

Cole **o traceback inteiro + o trecho de código + o que você esperava**. Exemplos reais que aparecem neste exercício:

| Sintoma | Causa provável | O que pedir à IA / verificar |
| --- | --- | --- |
| `AttributeError: module 'processing' has no attribute 'runalg'` | Código de QGIS 2 | "Reescreva para a API do QGIS 3" |
| Buffer gigantesco cobrindo o estado todo | Buffer em EPSG:4326 (3000 **graus**) | Conferir `layer.crs().authid()` antes do buffer |
| `Lossy conversion ... field fid` ao salvar | Campo `fid` herdado na interseção conflita com a chave do GeoPackage | Limitar `INPUT_FIELDS`/`OVERLAY_FIELDS` |
| Script trava por minutos no clip | Recorte de 1 milhão de polígonos | Usar `native:extractbylocation` antes |
| `Feature has invalid geometry` | Geometria inválida na entrada | `native:fixgeometries` ou ajustar *Filtragem de feições inválidas* |
| `Algorithm native:clipvector not found` | **ID de algoritmo inventado pela IA** | Procurar o ID real no registro (abaixo) e corrigir |

> **Cuidado com IDs de algoritmo alucinados.** As IAs inventam com frequência ferramentas que *parecem* existir — `native:clipvector`, `native:bufferbydistance`, `qgis:intersectlayers` — ou trocam o prefixo (`qgis:` × `native:` × `gdal:`). O nome é plausível, então o erro só aparece na hora de rodar. Antes de pedir outra resposta à IA, confira no próprio QGIS:
>
> ```python
> registro = QgsApplication.processingRegistry()
> print(registro.algorithmById("native:clipvector"))          # None = não existe
> print([a.id() for a in registro.algorithms() if "clip" in a.id()])  # IDs reais com "clip"
> processing.algorithmHelp("native:clip")                     # parâmetros do algoritmo certo
> ```
>
> Ou volte ao cheat code da Tarefa 2.2: rode a ferramenta à mão e copie o ID do Histórico (`Ctrl+Alt+H`).

### 3.5 Validar — a IA não valida por você

Antes de usar qualquer número no relatório:

- [ ] O CRS de cada camada é o esperado? (`layer.crs().authid()`)
- [ ] A rodovia filtrada tem os 6 trechos esperados?
- [ ] A soma das áreas por município ≈ área da AII? E a soma por classe?
- [ ] Os números batem com o fluxo manual da Parte 1 (planilha `relatorio_area_classe_municipio.xlsx`)?

> **Caso real deste curso.** A primeira versão do script usava EPSG:5880 (sugestão comum, inclusive de IAs, "porque a Paraíba cruza dois fusos UTM"). Ele rodava sem erro e as somas de controle fechavam 100% — mas, comparando com a planilha manual, as áreas vinham **2 a 4,5% maiores** (Juazeirinho/Pastagem: 4.222 ha × 4.140 ha). A extensão da PB-200 também não batia: 106,9 km em EPSG:5880 contra 103,8 km em UTM 24S e 104,25 km no campo `extensao`. A causa: a Policônica distorce longe do meridiano central (−54°). Trocando para UTM 24S, os resultados voltaram a bater com o fluxo manual. **Somas de controle verificam consistência interna; só a comparação com uma referência independente revela erro de método.**
- [ ] O resultado faz sentido no mapa? Abra as camadas e olhe.

### 3.6 Da IA para uma ferramenta reutilizável

```text
Transforme este script em um QgsProcessingAlgorithm para a Caixa de Ferramentas:
entradas = camada de linhas, camada de uso do solo, campo de classe, CRS métrico
e distância; saída = uso do solo recortado com area_ha.
```

Uma versão revisada e testada está em [`05_processing_script_tool.py`](05_processing_script_tool.py). Para instalá-la: Caixa de Ferramentas → ícone Python → **Adicionar script à Caixa de Ferramentas...**.

---

## Parte 4 — Melhorias e desafios

### Desafio 4.1 — Tabela dinâmica (pivot table)

A tabela gerada na Tarefa 2.5 está no formato "longo" (uma linha por município × classe). Para o relatório, queremos o formato "largo": **uma linha por município, uma coluna por classe**, com totais e percentuais.

- Faça a tabela dinâmica no Excel/LibreOffice a partir do CSV; **depois**
- automatize com `pandas.pivot_table` no próprio Console do QGIS.

> **Posso usar `pandas` dentro do QGIS?** Pode. O QGIS usa um Python próprio, mas o `pandas` já vem com os instaladores oficiais do Windows (OSGeo4W) e do macOS: é só dar `import pandas as pd` no Console, sem instalar nada. No Linux, o QGIS usa o Python do sistema, e talvez seja preciso instalar o pacote da distribuição (ex.: `sudo apt install python3-pandas`). Para tirar a dúvida, rode no Console: `import pandas; print(pandas.__version__)`.

<details>
<summary>Uma solução</summary>

[`07_tabela_dinamica.py`](07_tabela_dinamica.py):

```python
pivot = longo.pivot_table(index="nome", columns="descricao", values="sum",
                          aggfunc="sum", fill_value=0, margins=True,
                          margins_name="Total").round(2)
pct = pivot.div(pivot["Total"], axis=0).mul(100).round(1)
```

**Variante (opcional): direto da camada ativa, sem CSV.** Depois de rodar o `03_fluxo_pb200.py`, clique em `pb200_uso_solo_aii` no painel de camadas e rode no Console. O código também funciona com a camada `uso_mun` da Tarefa 2.5, ou com qualquer camada que tenha os campos `nome`, `descricao` e `area_ha`.

```python
import pandas as pd

CAMPOS = ["nome", "descricao", "area_ha"]

camada = iface.activeLayer()   # a camada selecionada no painel de camadas
if camada is None:
    raise ValueError("Nenhuma camada ativa: clique em pb200_uso_solo_aii no painel de camadas.")
faltando = [c for c in CAMPOS if camada.fields().indexOf(c) == -1]
if faltando:
    raise ValueError(f"{camada.name()} não tem os campos {faltando}. "
                     f"Campos disponíveis: {camada.fields().names()}")

# Só os atributos necessários e nenhuma geometria: a leitura fica bem mais rápida
pedido = (QgsFeatureRequest()
          .setFlags(QgsFeatureRequest.NoGeometry)
          .setSubsetOfAttributes(CAMPOS, camada.fields()))
df = pd.DataFrame([[f[c] for c in CAMPOS] for f in camada.getFeatures(pedido)],
                  columns=CAMPOS)

pivot = df.pivot_table(index="nome", columns="descricao", values="area_ha",
                       aggfunc="sum", fill_value=0, margins=True,
                       margins_name="Total").round(2)
print(pivot)
```

Aqui o `pandas` soma o `area_ha` de cada polígono, papel que no script principal é do `qgis:statisticsbycategories`. Por isso o total precisa bater com o da versão via CSV (607,93 km² = 60.793 ha): é uma boa verificação cruzada.
</details>

### Desafio 4.2 — Outras rodovias com uma lista Python

A análise é a mesma para qualquer rodovia: só muda o nome. Coloque o fluxo dentro de um `for` sobre uma lista e gere um resumo comparativo.

```python
RODOVIAS = ["PB-200", "PB-228", "PB-238", "PB-250"]
for rodovia in RODOVIAS:
    ...
```

**Para pensar:** o que fazer se um nome não existir? E se a rodovia estiver no fuso 25S (litoral)?

<details>
<summary>Uma solução</summary>

[`04_loop_rodovias.py`](04_loop_rodovias.py) — saída:

```
Rodovia   Trechos  CRS         Área do buffer (km²)
PB-200          6  EPSG:31984                 607.9
PB-228          7  EPSG:31984                 468.9
PB-238          4  EPSG:31984                 462.0
PB-250          4  EPSG:31984                 213.8
```

O script escolhe o **fuso UTM de cada rodovia** a partir da longitude do centro dos trechos (`fuso = int((lon + 180) // 6) + 1` → `EPSG:{31960 + fuso}`), então funciona também para rodovias do litoral, no fuso 25S.

Bônus: transforme o corpo do `for` de `03_fluxo_pb200.py` em uma função `analisar(rodovia)`.
</details>

### Desafio 4.3 — Uma interface para escolher as rodovias

Em vez de editar a lista no código, deixe o usuário **escolher na tela**. Dois caminhos, do mais simples ao mais completo:

1. **Sem programar:** selecione os trechos no mapa e rode a ferramenta da Tarefa 3.6 marcando *Somente feições selecionadas*; ou use **Executar como processo em lote**.
2. **Ferramenta da Caixa:** adicione ao `QgsProcessingAlgorithm` um parâmetro `QgsProcessingParameterEnum(..., allowMultiple=True)` ou `QgsProcessingParameterString` com os nomes separados por vírgula.

### Desafio 4.4 — Automatizando a geração do mapa (layout)

O projeto já tem um **layout de impressão (`QgsPrintLayout`) pré-configurado**, com mapa, legenda, escala e título. Depois de rodar a análise, o último passo manual é abrir o layout e exportar o mapa — e é justamente isso que você vai automatizar.

**O desafio:** usando a IA, descubra como exportar esse layout para **PDF** e **PNG** com **2 ou 3 linhas de Python** no Console. Dicas para o prompt: diga a versão do QGIS, que o layout **já existe no projeto aberto** (e o nome dele, em **Projeto → Gerenciador de layouts**) e que você quer o código para o Console, não um script standalone.

Para conferir a resposta da IA: o layout é obtido pelo `layoutManager()` do projeto, e quem exporta é a classe `QgsLayoutExporter`. Se a IA sugerir `QgsComposition` ou `QgsComposerView`, é API do QGIS 2.

<details>
<summary>Uma solução</summary>

```python
layout = QgsProject.instance().layoutManager().printLayouts()[0]  # ou .layoutByName("Nome do layout")
exportador = QgsLayoutExporter(layout)
exportador.exportToPdf("/caminho/para/dados_curso/pb200/resultados/mapa_pb200.pdf", QgsLayoutExporter.PdfExportSettings())
exportador.exportToImage("/caminho/para/dados_curso/pb200/resultados/mapa_pb200.png", QgsLayoutExporter.ImageExportSettings())
```

Os dois métodos devolvem `QgsLayoutExporter.Success` (`0`) quando dá certo; teste o retorno antes de anunciar que o mapa foi gerado. Bônus: junte com o Desafio 4.2 e gere **um PDF por rodovia**, atualizando o título e a extensão do mapa dentro do `for`.
</details>

### Desafio 4.5 — O copiloto de relatório

A análise termina em números, mas o EIA/RIMA é texto. Use a IA para escrever o **primeiro rascunho** da seção de uso do solo.

1. Abra a tabela final (o CSV da Tarefa 2.5 ou a planilha do Desafio 4.1) e copie o conteúdo.
2. Cole no ChatGPT/Claude com o prompt:

   ```text
   Atue como analista ambiental. Com base nestes dados de uso do solo na Área
   de Influência da PB-200, escreva dois parágrafos para o relatório EIA/RIMA
   destacando os municípios mais afetados e se o impacto incide mais sobre
   áreas naturais ou antrópicas.

   [cole a tabela aqui]
   ```

3. **Revise como revisaria o texto de um estagiário:**
   - [ ] Cada número citado **existe na tabela**? A IA arredonda, soma errado e às vezes inventa valores.
   - [ ] A classificação natural × antrópica está certa? (Ex.: *Formação Savânica* é natural; *Pastagem*, *Mosaico de Usos* e *Área Urbanizada* são antrópicas.)
   - [ ] O texto afirma algo que os dados **não mostram** (fauna, qualidade da vegetação, impactos futuros)?

> **Para ir além:** peça à IA para incluir uma tabela-síntese com o percentual de áreas naturais e antrópicas por município, e confira o resultado com o `pandas` do Desafio 4.1. O texto final é responsabilidade técnica sua, não da IA.

### Outras ideias

- Gerar também a ADA (1 km) e calcular o uso do solo nas duas faixas.
- Aplicar automaticamente o estilo salvo no GeoPackage (`layer_styles`) às camadas de saída.
- Gerar os gráficos (barras por município, rosca por classe) e um layout de impressão por rodovia.
- Cruzar a AII com `aptidao_agricola_pb` (aptidão agrícola) no lugar do uso do solo.
- Refazer tudo fora do QGIS com GeoPandas: [`geopandas.md`](geopandas.md).
