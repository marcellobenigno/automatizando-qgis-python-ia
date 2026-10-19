# Perfil topográfico da PB-200

> Exercício do minicurso **Automatizando o QGIS com Python e IA**.
> Este exercício junta os dois anteriores: a **PB-200** do [exercício de licenciamento](../pb200/README.md) e o **MDE TOPODATA** da [grade interativa](../grade_topodata/README.md). O resultado é o perfil topográfico da rodovia inteira, do km 0 ao km 104. Partimos de um tutorial publicado na web, escrito para uma versão antiga do QGIS, e usamos a IA para atualizá-lo. O ponto principal do exercício é **conferir o que ela entrega**.

![Perfil topográfico da PB-200](../../imgs/perfil_pb200/1-apresentacao.png)

## Contexto

Um **perfil topográfico** mostra como a altitude varia ao longo de uma linha. Na duplicação da PB-200, ele ajuda a identificar rampas, pontos altos e baixos e os trechos que vão exigir corte ou aterro.

Para montar o perfil, precisamos de três coisas:

1. **Uma linha**, e uma só: a PB-200 inteira, orientada do km 0 (Juazeirinho) ao km 104 (Congo).
2. **Um modelo de elevação** que cubra a rodovia. A PB-200 fica inteira na folha TOPODATA **`07S375`**.
3. **Um jeito de "andar" pela linha:** pontos a intervalos regulares, cada um com a distância desde o início e a altitude lida do MDE.

A referência é o tutorial [*Python QGIS Tutorial: Create Elevation Profile*](https://www.geodose.com/2021/02/python-qgis-tutorial-create-elevation-profile.html), do Geodose. Ele usa ferramentas e APIs que mudaram desde 2021, e corrigir isso faz parte do exercício.

## Dados

| Dado | Origem | Observação |
| --- | --- | --- |
| `malha_viaria` em `minicurso_dados.gpkg` | [`dados_curso/README.md`](../../dados_curso/README.md) | campo `rodovia_nome = 'PB-200'`: **6 trechos** |
| `07S375ZN.tif` | ação de clique da [grade TOPODATA](../grade_topodata/README.md#parte-4--ação-de-clique-uma-célula) | EPSG:4326, pixel de 1″ (~30 m), altitude em metros (EGM96), NoData = −9999 |

## O que deve ser entregue

1. `pb200_perfil.gpkg`, com a camada `pb200_linha_unica` (1 feição, ~104 km, EPSG:31984) e a camada `pb200_pontos_z` (pontos a cada 30 m com `distance` e `z_1`).
2. `pb200_perfil.csv`, com as colunas `km`, `lon`, `lat` e `altitude_m`.
3. `pb200_perfil.png`, o gráfico do perfil.
4. A conferência do gráfico com a ferramenta **Perfil de Elevação (Elevation Profile)** do QGIS.

Tudo em `dados_curso/perfil_pb200/resultados/`.

## Roteiro

| Parte | O que fazemos | Tempo |
| --- | --- | --- |
| [1 — Um tutorial de 2021 no QGIS 3.44](#parte-1--um-tutorial-de-2021-no-qgis-344) | A IA atualiza o código do Geodose, e nós conferimos | 10 min |
| [2 — Uma PB-200, uma linha](#parte-2--uma-pb-200-uma-linha) | Unir os 6 trechos e descobrir por que o "óbvio" não funciona | 20 min |
| [3 — O MDE da rodovia](#parte-3--o-mde-da-rodovia) | Baixar a folha `07S375` com a ação do exercício anterior | 5 min |
| [4 — Pontos e altitudes](#parte-4--pontos-e-altitudes) | Pontos a cada 30 m e altitude de cada um | 15 min |
| [5 — O gráfico](#parte-5--o-gráfico) | Rodar o script completo, ler o perfil e entender o serrilhado | 15 min |
| [6 — Conferir com a ferramenta nativa](#parte-6--conferir-com-o-perfil-de-elevação-do-qgis) | Comparar com o Perfil de Elevação do QGIS | 10 min |

> As capturas de tela estão com o QGIS 3.44 em inglês; no texto aparecem os nomes em português e, entre parênteses, em inglês.

---

## Parte 1 — Um tutorial de 2021 no QGIS 3.44

O código do Geodose tem quatro blocos: definir entradas, gerar pontos ao longo da linha, ler a altitude de cada ponto e calcular a distância acumulada, e desenhar o gráfico. O centro dele é este trecho:

```python
raster_layer=QgsRasterLayer(elevation_data,'ogr')
interval=raster_layer.rasterUnitsPerPixelX()

processing.run("grass7:v.to.points", {'input':line,'use':1,'dmax':interval,'-i':True,'-t':False,'output':out_points})
processing.run("saga:addrastervaluestopoints", {'SHAPES':line_points,'GRIDS':[dem],'RESAMPLING':0,'RESULT':point_z})
```

### 1.1 O prompt

```text
Vou criar um perfil topográfico no QGIS 3.44 com PyQGIS. Minha referência é
este tutorial de 2021 (QGIS 3.16):

<cole aqui o código completo do tutorial>

Atualize o código para o QGIS 3.44:
- use apenas algoritmos nativos (native:...), sem GRASS e sem SAGA;
- para cada algoritmo antigo, diga qual o substitui e por quê;
- aponte os erros do código original (variáveis, unidades, CRS);
- não invente nomes de parâmetros: liste os que você usou para eu conferir
  com processing.algorithmHelp().
```

### 1.2 O que conferir na resposta

| No tutorial (QGIS 3.16) | No QGIS 3.44 |
| --- | --- |
| `grass7:v.to.points` | **`native:pointsalonglines`** (*Pontos ao longo da geometria*). Não depende do GRASS e já cria o campo `distance` (distância desde o início da linha) |
| `saga:addrastervaluestopoints` | **`native:rastersampling`** (*Amostrar valores de raster*). O SAGA saiu da instalação padrão no QGIS 3.30 e hoje é um plugin à parte |
| loop com `QgsDistanceArea` e `setEllipsoid('NAD83')` para somar distâncias | **desnecessário:** com a linha em UTM, o campo `distance` já é a distância acumulada em metros |
| `interval = rasterUnitsPerPixelX()` | **armadilha de unidade:** o TOPODATA está em EPSG:4326, e esse valor é **0,000278 grau**. Usado como distância em UTM, viraria um ponto a cada 0,3 mm. Use **30 m** |
| `out_points` × `line_points`, `dem` × `elevation_data` | o código original **nem roda**: as variáveis definidas não são as mesmas usadas |
| `f.attributes()[-1]` | leia pelo nome (`f["z_1"]`) e trate `NULL` (ponto fora do raster ou NoData) |

Confira os parâmetros reais de cada algoritmo direto no QGIS:

```python
processing.algorithmHelp("native:pointsalonglines")
processing.algorithmHelp("native:rastersampling")
```

---

## Parte 2 — Uma PB-200, uma linha

### 2.1 A solução "óbvia"

Peça à IA:

```text
Na camada malha_viaria do GeoPackage, a PB-200 está dividida em trechos
(campo rodovia_nome = 'PB-200'). Escreva um código PyQGIS que filtre os
trechos, reprojete para EPSG:31984 e una tudo em uma única linha.
```

A resposta típica é `native:extractbyattribute` → `native:reprojectlayer` → `native:dissolve` → `native:mergelines`. Rode e confira o resultado com este trecho:

```python
g = next(linha.getFeatures()).geometry()
print(g.isMultipart(), g.constGet().numGeometries(), g.length() / 1000)
```

Nos dados do curso, ele mostra:

```text
True 5 103.85
```

São **5 partes**, e não uma linha. O comprimento também não fecha, porque os trechos não se tocam. Se o perfil for gerado sobre esse resultado, os pontos de cada parte recomeçam a contagem de distância, e a ordem das partes é arbitrária. Nos dados do curso, o "km 0" cai num lugar a 472 m de altitude, e não em Juazeirinho (555 m).

![Os seis trechos da PB-200 e as falhas entre eles](../../imgs/perfil_pb200/2-trechos-pb200.png)

### 2.2 Investigando: o que há de errado com os trechos?

Abra a tabela de atributos dos trechos e troque a simbologia por **setas** (Propriedades → Simbologia → tipo de camada de símbolo **Seta (Arrow)**), para ver o sentido em que cada trecho foi digitalizado. Você vai ver dois problemas:

| Problema | Onde | Efeito |
| --- | --- | --- |
| **Sentido invertido** | os trechos `0020`, `0040` e `0050` foram digitalizados do km maior para o menor | o "fim" de um trecho não encontra o "início" do seguinte |
| **Falhas entre trechos** | ~198 m antes de `0030`, ~166 m antes de `0060`, ~57 m antes de `0040` e ~4 m antes de `0020` | o `mergelines` só junta linhas que **se tocam** |

> **A IA não valida por você.** O `dissolve` + `mergelines` está certo *em geral*: é a resposta de manual. Quem conhece os dados é você. Por isso o roteiro manda **contar as partes e medir o comprimento** antes de seguir.

### 2.3 A solução: ordenar pelo km e costurar

Os atributos `km_inicial` e `km_final` dão a ordem correta. Peça à IA:

```text
Os trechos têm km_inicial e km_final, mas alguns estão digitalizados ao
contrário e há falhas de até 200 m entre eles. Escreva uma função PyQGIS
que:
- ordene os trechos por km_inicial;
- inverta cada trecho cujo início esteja mais longe do fim do trecho
  anterior do que o seu próprio fim;
- concatene os vértices em uma única LineString (ligando as falhas em
  linha reta) e devolva também a lista de falhas, em metros;
- oriente o 1º trecho pelo 2º (o fim do 1º é o lado que encosta no 2º).
```

A versão revisada é a função `unir_trechos()` em [`perfil_pb200.py`](perfil_pb200.py).

> **Nota: o que conferir no código**
>
> | Trecho | Por que é assim |
> | --- | --- |
> | `sorted(..., key=lambda f: f["km_inicial"])` | a ordem dos trechos vem do atributo, não da geometria nem da ordem em que estão gravados |
> | `ultimo.distance(linha[-1]) < ultimo.distance(linha[0])` → `reverse()` | um trecho invertido "começa" no lado mais distante do anterior |
> | `linha[1:] if falha < 0.01 else linha` | quando os trechos se tocam, o vértice comum não é repetido |
> | as falhas são **relatadas**, não escondidas | 198 m em linha reta é aceitável num perfil de 104 km, mas a decisão é sua |

Conferência: a linha única deve ter **~104,27 km**, contra **104,25 km** da soma do campo `extensao`. Se o comprimento der muito maior (por exemplo 150 km), algum trecho foi ligado pelo lado errado e a linha "vai e volta".

---

## Parte 3 — O MDE da rodovia

1. Carregue a `grade_topodata` e a camada da PB-200 no mesmo projeto.
2. Veja que a rodovia (lat −7,07° a −7,79°) fica inteira na célula **`07S375`**, que vai de −7° a −8°.
3. Use a **ação de clique** do exercício anterior ([Parte 4 da grade TOPODATA](../grade_topodata/README.md#parte-4--ação-de-clique-uma-célula)) e clique nessa célula. Se ela já foi baixada, a ação só reaproveita o arquivo.
4. Anote o caminho do `07S375ZN.tif`: ele vai na constante `MDE` do script.

![A PB-200 sobre a célula 07S375](../../imgs/perfil_pb200/3-celula-07S375.png)

> **E se a rodovia cruzasse duas folhas?** Seria preciso juntar os MDEs antes (por exemplo, com `gdal:buildvirtualraster`, que cria um mosaico virtual). Fica como desafio no fim.

---

## Parte 4 — Pontos e altitudes

Com a linha única em UTM, os dois algoritmos da Parte 1 fazem o resto:

```python
pontos = rodar("native:pointsalonglines", {
    "INPUT": linha, "DISTANCE": INTERVALO_M})          # 30 m

pontos_mde = rodar("native:reprojectlayer", {
    "INPUT": pontos, "TARGET_CRS": mde.crs()})
pontos_z = rodar("native:rastersampling", {
    "INPUT": pontos_mde, "RASTERCOPY": mde, "COLUMN_PREFIX": "z_"})
```

- `pointsalonglines` cria os campos **`distance`** (metros desde o início) e `angle`.
- `rastersampling` cria **`z_1`**: o prefixo `z_` mais o número da banda.
- O `rastersampling` **reprojeta os pontos sozinho** quando o CRS do raster é outro. Mesmo assim, o script reprojeta antes para EPSG:4326, para o CSV sair em longitude e latitude.

Saída esperada: **3.476 pontos**, nenhum sem altitude.

> **Por que 30 m?** É aproximadamente o tamanho do pixel do TOPODATA (1″). Com pontos mais próximos, vários caem no mesmo pixel e repetem o valor. Com pontos mais distantes, o perfil perde detalhes, como o fundo de vales estreitos.

---

## Parte 5 — O gráfico

### 5.1 Rodar o script

1. Abra [`perfil_pb200.py`](perfil_pb200.py) no **Editor do Console Python**.
2. Ajuste as constantes `GPKG`, `MDE` e `PASTA_SAIDA`.
3. Clique em **Executar script**.

Saída esperada no console:

```text
[1] PB-200: 6 trechos
[2] Reprojetado para EPSG:31984
      PB-200/0010   km   0.00 a  22.54  Pavimentada
      ...
      PB-200/0060   km  83.09 a 104.25  Leito Natural
[3] Linha única: 104.27 km
      falha de    3.7 m antes de PB-200/0020 (ligada em linha reta)
      falha de  197.5 m antes de PB-200/0030 (ligada em linha reta)
      falha de   57.1 m antes de PB-200/0040 (ligada em linha reta)
      falha de  166.3 m antes de PB-200/0060 (ligada em linha reta)
[4] 3476 pontos a cada 30 m
[5] Altitude: mín. 460.6 m · máx. 601.6 m · média 513.7 m
[6] Resultados salvos em .../perfil_pb200/resultados
      Gráfico: .../perfil_pb200/resultados/pb200_perfil.png
[7] Verificações
      CRS da linha: EPSG:31984 (esperado EPSG:31984)
      Comprimento:  104.27 km × soma de 'extensao' 104.25 km (100.0%)
      Pontos sem altitude: 0 de 3476
```

![Perfil topográfico da PB-200 gerado pelo script](../../imgs/perfil_pb200/5-perfil-matplotlib.png)

### 5.2 Lendo o perfil

- O ponto mais alto (~602 m) fica nos primeiros 5 km, ainda perto de Juazeirinho, no Planalto da Borborema.
- O ponto mais baixo (~461 m) fica por volta do km 84, onde começa o trecho de **leito natural** (`PB-200/0060`).
- A amplitude total é de apenas **~140 m em 104 km**. O gráfico parece montanhoso por causa do **exagero vertical**: na figura, 1 cm no eixo Y vale cerca de 17 m, e 1 cm no eixo X vale cerca de 3,7 km. O relevo aparece ~210 vezes mais íngreme do que é.

> **Pergunte à IA:** "qual o exagero vertical deste gráfico, para `figsize=(12, 4.5)` e eixos de 0–104 km × 460–602 m? Como desenhar sem exagero?" Depois teste com `ax.set_aspect(...)` e veja por que ninguém desenha perfis de estrada sem exagero.

### 5.3 Por que o perfil é "serrilhado"?

A curva parece cheia de dentes. Antes de concluir que o script errou, meça os dentes no CSV:

| Medida | Valor |
| --- | --- |
| Variação típica entre dois pontos vizinhos (30 m) | **0,6 m** (mediana) |
| 95% das variações ficam abaixo de | **2,3 m** |
| Maior variação entre vizinhos | **7,5 m** |
| Oscilação em torno de uma média móvel de 300 m | **±1,3 m** (desvio-padrão) |

São oscilações de 1 a 2 m. Três motivos explicam por que elas parecem tão grandes:

1. **O exagero vertical (~210 vezes).** Com só 140 m no eixo Y e 104 km no eixo X, uma oscilação de 1 m, invisível no terreno, vira um dente no gráfico.
2. **O MDE é feito de degraus.** O `rastersampling` não interpola: cada ponto recebe o valor do pixel de ~30 m em que cai. A rodovia corta os pixels em diagonal, e o perfil "pula" de um valor para o seguinte. Em 10% dos passos o valor nem muda, porque o ponto caiu no mesmo pixel ou num vizinho de mesmo valor.
3. **O SRTM mede a superfície, não o chão.** O TOPODATA deriva do SRTM, um radar que registra o topo do que está no terreno: vegetação, construções, taludes de corte e aterro. Além disso, o SRTM tem um ruído próprio de alguns metros. Uma pista de ~10 m de largura também não "aparece" num pixel de 30 m, cujo valor mistura a pista com o entorno.

**Conclusão:** o ruído de ±1 a 2 m está dentro da precisão do dado. As formas grandes são relevo real: a descida do Planalto da Borborema nos primeiros 30 km, as elevações perto dos km 51 e 74 e o vale perto do km 84. Os dentes pequenos não são. Interpretar um dente de 2 m como uma "lombada" seria ler no dado mais do que ele tem.

> **Pergunte à IA:** "meu perfil topográfico feito com o SRTM a cada 30 m está serrilhado. É erro do script ou característica do dado? Que números do CSV eu posso calcular para decidir?" Compare a resposta com a tabela acima. Se a IA sugerir suavizar sem falar do custo disso, veja o Desafio 4.

---

## Parte 6 — Conferir com o Perfil de Elevação do QGIS

Desde a versão 3.26, o QGIS tem uma ferramenta nativa de perfil. Use-a para validar o script:

1. Botão direito em `07S375ZN` → **Propriedades (Properties)** → **Elevação (Elevation)** → marque **Representa superfície de elevação (Represents elevation surface)** → **OK**.
2. Menu **Exibir (View)** → **Perfil de Elevação (Elevation Profile)**.
3. Na barra do painel, clique em **Capturar curva a partir de feição (Capture Curve From Feature)** e clique na linha `pb200_linha_unica`.

![Perfil de Elevação nativo do QGIS](../../imgs/perfil_pb200/6-perfil-nativo.png)

Compare com o gráfico do script:

| | Script (pontos a cada 30 m) | Perfil de Elevação |
| --- | --- | --- |
| Comprimento | 104,27 km | **~0,94°**: o eixo X está em **graus** (veja abaixo) |
| Altitude máxima | 601,6 m (km 4,35) | pico logo acima de 600 m, perto de 0,04° (≈ 4,4 km) |
| Altitude mínima | 460,6 m (km 83,76) | vale perto de 460 m, em ~0,76° (≈ 84 km) |
| Forma da curva | — | a mesma: pico inicial, vales em 0,30°, 0,76° e 0,83° e elevação em 0,67° |

> **O eixo X em graus.** O Perfil de Elevação mede a distância no CRS do **projeto**. Com o projeto em EPSG:4326, o eixo vai de 0° a ~0,94°. A linha tem 104,27 km, então 1° ao longo dela equivale a ~110,6 km. Para ver o eixo em metros, mude o CRS do projeto para **EPSG:31984** (canto inferior direito da janela) antes de capturar a curva.

> **Cuidado ao ler valores com o mouse.** Na captura acima, passar o mouse "no ponto mais alto" e "no mais baixo" deu **587,78 m** e **488,32 m**, longe dos 601,6 e 460,6 m do script. A auditoria mostrou por quê:
>
> - **587,78 m não é o valor de nenhum pixel** ao longo da rodovia (testado a cada 5 m). É a leitura do ponto em que o cursor estava, e não o pico da curva.
> - **488,32 m existe**, mas no km ~84,9 (0,768°), na encosta logo ao lado do vale mais baixo.
>
> Num gráfico serrilhado, é muito difícil parar o cursor exatamente no extremo. Para comparar mínimo e máximo, use a forma da curva e os números do script, não uma leitura de mouse.

> **E o mínimo "verdadeiro"?** Amostrando a cada **5 m**, de modo que nenhum pixel atravessado pela rodovia fica de fora, o mínimo é **459,6 m** (km 83,74), 1 m abaixo do valor do script. Com pontos a cada 30 m, alguns pixels ficam entre dois pontos e não são lidos. O máximo é o mesmo nos dois casos (601,6 m). Diferenças de ~1 m como essa são normais entre ferramentas que amostram o raster com densidades diferentes.

> **Se a ferramenta nativa existe, por que o script?** Porque o script é **repetível** (outra rodovia é só trocar a constante `RODOVIA`), gera **dados** (o CSV vai para a planilha do projeto de engenharia) e documenta **cada decisão**: a ordem dos trechos, o intervalo de 30 m e as falhas ligadas em linha reta.

---

## Desafios

1. **Outra rodovia.** Troque `RODOVIA` por outra estadual. Se ela cruzar mais de uma folha TOPODATA, baixe as folhas com a ação de células selecionadas e crie um mosaico com `gdal:buildvirtualraster` antes de amostrar.
2. **Pavimentada × leito natural.** Pinte o gráfico com uma cor por `sit_fisica`. Dica: guarde em `unir_trechos()` a distância acumulada em que cada trecho começa.
3. **Declividade.** Calcule a rampa (%) entre pontos consecutivos e destaque os trechos acima de 6%.
4. **Suavizar o perfil.** Desenhe, por cima da curva original, uma **média móvel** de ~300 m (11 pontos de 30 m). Depois responda:
   - O que acontece com a altitude máxima e com a mínima?
   - Qual janela (5, 11, 31 pontos) tira os dentes sem apagar os vales?
   - Por que, no Desafio 3, calcular a rampa sobre a curva **original** dá valores irreais?

   <details>
   <summary>Uma solução possível</summary>

   Acrescente no script, logo depois de `ax.fill_between(...)`:

   ```python
   JANELA = 11  # pontos: 11 × 30 m ≈ 300 m
   meio = JANELA // 2
   suave = []
   for i in range(len(altitudes)):
       vizinhos = altitudes[max(0, i - meio):i + meio + 1]  # menos pontos nas pontas
       suave.append(sum(vizinhos) / len(vizinhos))
   ax.plot(km, suave, color="black", linewidth=1.5, label="Média móvel (~300 m)")
   print(f"Suavizado: mín. {min(suave):.1f} m · máx. {max(suave):.1f} m")
   ```

   Com a janela de 11 pontos, a máxima cai de **602 para 594 m** e a mínima sobe de **461 para 463 m**. Suavizar tira o ruído, mas também "achata" picos e vales reais e estreitos. Por isso o script guarda os valores originais no CSV, e a média móvel entra só no gráfico.

   </details>
