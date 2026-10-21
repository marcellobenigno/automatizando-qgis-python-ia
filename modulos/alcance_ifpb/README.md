# Alcance a partir do IFPB: 800 m a pé e 4 km de carro

> Exercício do minicurso **Automatizando o QGIS com Python e IA**.
> Até onde se chega, **pelas ruas**, a partir do **IFPB Campus João Pessoa**: andando 800 m e dirigindo 4 km? A malha viária de João Pessoa é baixada **uma única vez** do OpenStreetMap com o OSMnx e guardada num GeoPackage. Daí em diante, as duas análises rodam **offline**, no QGIS, com **PyQGIS e NetworkX**: em segundos, sem internet e com o mesmo resultado para toda a turma.

![Alcance a pé e de carro a partir do campus](../../imgs/alcance_ifpb/1-alcance-ifpb.png)

## Contexto

Um círculo de 800 m em volta do campus **não** é o que se alcança andando 800 m. Quem anda segue as ruas: contorna quarteirões, muros e áreas sem passagem. O conjunto de ruas alcançáveis até uma certa distância **pela rede** chama-se **área de serviço** (ou isodistância). Ela responde a perguntas como:

- Quais ruas ficam a até **10 minutos a pé** do campus (~800 m, a 4,8 km/h)? É a distância usada em planejamento urbano para medir o que é "caminhável" em volta de uma escola ou estação.
- Até onde se chega com **4 km de carro**, respeitando a **mão única** das vias?

Para responder, precisamos de uma **rede**: nós (cruzamentos) e arcos (trechos de rua com comprimento e sentido). Ela vem do OpenStreetMap, por meio do **OSMnx**.

### Por que trabalhar offline

![Online × offline](../../imgs/alcance_ifpb/2-online-offline.png)

O OSMnx consulta o **Overpass**, um servidor público e gratuito. Na preparação deste exercício, em 21/10/2026, **várias tentativas seguidas** de baixar a malha de João Pessoa receberam `502 Bad Gateway … server is currently at capacity`, no QGIS e fora dele. Agora imagine 30 alunos consultando ao mesmo tempo.

A saída é separar as duas etapas:

| | Baixar a malha (online) | Analisar (offline) |
| --- | --- | --- |
| **Quem** | o professor, uma vez | cada aluno, quantas vezes quiser |
| **Ferramenta** | OSMnx, num Python separado | QGIS: PyQGIS + NetworkX |
| **Depende da internet?** | sim | **não** |
| **Tempo** | minutos (quando o servidor responde) | **~1 s** para ler a malha, **< 0,5 s** por análise |
| **Resultado** | `malha_joao_pessoa_all.gpkg` (27 MB) | alcance, mapas e verificações |

Além da velocidade e da independência da rede, trabalhar sobre um arquivo traz **reprodutibilidade**: o OpenStreetMap muda todo dia, mas o GeoPackage não. Toda a turma analisa a mesma malha e chega aos mesmos números.

## Dados

| Dado | Origem | Observação |
| --- | --- | --- |
| `malha_joao_pessoa_all.gpkg` | gerado com [`malha_urbana_osmnx.py`](../../apoio/osmnx/malha_urbana_osmnx.py) (rede `all`) e distribuído em `dados_curso/alcance_ifpb/` ([Google Drive](../../dados_curso/README.md)) | camadas `nodes` (22.647), `arcos` (59.603), `edges` e `limite`, em EPSG:4326. © colaboradores do OpenStreetMap, licença [ODbL](https://www.openstreetmap.org/copyright) |
| campus | centro do terreno do IFPB Campus João Pessoa no OSM | (−34,87354; −7,13574) |

> **Pré-requisito:** o NetworkX no Python do QGIS. Confira no Console Python com `import networkx`. Se der erro, veja a seção 6.1 do *Guia OSMnx + QGIS no Windows* (PDF no [Google Drive do curso](../../dados_curso/README.md)). O OSMnx **não** precisa estar instalado no QGIS: ele só é usado para baixar a malha.

## O que deve ser entregue

1. `alcance_ifpb.gpkg`, com as camadas `alcance_faixas` (um anel por faixa de distância, com os km de vias), `alcance_poligonos` (polígono do alcance e círculo de cada análise) e `campus`.
2. `alcance_ifpb.png`, os dois mapas lado a lado.
3. A conferência com a ferramenta nativa **Área de serviço (Service area)** do QGIS.

Tudo em `dados_curso/alcance_ifpb/resultados/`.

## Roteiro

| Parte | O que fazemos | Tempo |
| --- | --- | --- |
| [1 — Baixar a malha, uma vez](#parte-1--baixar-a-malha-uma-vez) | OSMnx → GeoPackage (feito pelo professor) | 5 min |
| [2 — Conhecer a malha](#parte-2--conhecer-a-malha) | Camadas, campos e duas redes num arquivo só | 10 min |
| [3 — Do GeoPackage ao grafo](#parte-3--do-geopackage-ao-grafo) | PyQGIS lê, NetworkX monta o grafo | 15 min |
| [4 — Distância pela rede e faixas](#parte-4--distância-pela-rede-e-faixas) | Dijkstra com limite e o corte dos trechos | 15 min |
| [5 — Rodar e ler os resultados](#parte-5--rodar-e-ler-os-resultados) | Mapas, linha reta × rede e mão única | 15 min |
| [6 — Conferir com o QGIS](#parte-6--conferir-com-a-área-de-serviço-do-qgis) | A mesma análise com o algoritmo nativo | 10 min |

> No texto, os nomes de menus e algoritmos aparecem em português e, entre parênteses, em inglês.

---

## Parte 1 — Baixar a malha, uma vez

O script [`apoio/osmnx/malha_urbana_osmnx.py`](../../apoio/osmnx/malha_urbana_osmnx.py) pede o nome da cidade, o tipo de rede e a pasta de saída. Ele baixa em segundo plano (o QGIS não trava) e grava quatro camadas:

| Camada | Conteúdo | Para quê |
| --- | --- | --- |
| `nodes` | cruzamentos e pontas de rua (`osmid`, `x`, `y`) | os nós do grafo |
| `edges` | uma linha por trecho de rua | para o mapa |
| `arcos` | **uma linha por sentido de circulação**: mão dupla = 2 arcos (ida e volta), mão única = 1 arco, desenhado no sentido do tráfego | para o roteamento |
| `limite` | polígono do município | recorte e conferência |

Usamos a rede **`all`**, que traz todas as vias: ruas, calçadões, escadarias, trilhas e vias de serviço. Assim, **um arquivo serve às duas análises**. A rede de pedestres e a de carros são filtradas dele na Parte 2.

> **Por que a camada `arcos`?** O *Guia OSMnx + QGIS no Windows* (PDF no [Google Drive do curso](../../dados_curso/README.md)) avisa (seção 8.1): gravado com `directed=False`, o grafo perde o sentido das vias, e uma rota pode entrar na contramão. A camada `arcos` guarda o grafo **dirigido**. Para o carro, é ela que garante a mão única.

**Na aula, os alunos recebem o GeoPackage pronto** e pulam esta parte. Ela é mostrada para que saibam de onde vêm os dados e como refazer para outra cidade.

---

## Parte 2 — Conhecer a malha

Abra `malha_joao_pessoa_all.gpkg` no QGIS (arraste o arquivo para o mapa) e a tabela de atributos de `arcos`. Os campos que importam:

| Campo | O que é | Cuidado |
| --- | --- | --- |
| `u`, `v` | nó de início e de fim do arco | o arco vai **de `u` para `v`** |
| `length` | comprimento em metros (geodésico, calculado pelo OSMnx) | não use `$length` em EPSG:4326: daria graus |
| `highway` | tipo de via (`residential`, `footway`, `primary`…) | trechos unidos pelo OSMnx guardam **listas como texto**: `['service', 'residential']` |
| `oneway` | 1 = mão única | a pé, não vale |
| `access` | restrição de acesso | `private` (2.315 arcos) e `no` (151) ficam de fora |

Os tipos mais comuns na malha de João Pessoa:

| `highway` | arcos | km | entra a pé? | entra de carro? |
| --- | ---: | ---: | :---: | :---: |
| `residential` | 35.364 | 3.074 | sim | sim |
| `service` | 7.498 | 508 | sim | não (estacionamentos, entradas de garagem) |
| `tertiary` | 4.867 | 349 | sim | sim |
| `footway` | 2.954 | 112 | sim | não |
| `secondary` / `primary` | 5.140 | 381 | sim | sim |
| `path` / `track` / `steps` | 1.408 | 219 | sim | não |
| `cycleway` | 331 | 60 | não | não |
| `trunk` (BR-230) | 143 | 44 | sim | sim |

Duas regras definem as redes:

- **A pé:** basta **um** dos tipos do trecho ser de pedestre. Um trecho `['footway', 'residential']` entra.
- **De carro:** **todos** os tipos do trecho têm de ser de automóvel. O mesmo trecho fica de fora, porque parte dele é calçada.

### O prompt

```text
Tenho um GeoPackage gerado pelo OSMnx (rede "all") com as camadas nodes
(osmid, x, y) e arcos (u, v, length, highway, oneway, access), em EPSG:4326.
Na camada arcos, cada feição é um sentido de circulação, já desenhada de u
para v. O campo highway pode ser uma lista gravada como texto.

Escreva um script PyQGIS para o QGIS 3.44 que, SEM internet e SEM OSMnx:
- leia as camadas com QgsVectorLayer e monte dois grafos nx.MultiDiGraph:
  a pé (vias de pedestre; a mão única não vale) e de carro (só vias de
  automóvel; respeita a mão única);
- ligue o IFPB Campus João Pessoa (-34.87354, -7.13574) ao nó mais próximo
  da maior componente fortemente conexa;
- calcule as vias alcançáveis até 800 m a pé e até 4 km de carro, em faixas
  (200/400/600/800 m e 1/2/3/4 km), cortando os trechos no limite exato;
- compare o resultado com native:serviceareafrompoint.
Distâncias em EPSG:31985. Comentários em português.
```

A versão revisada é [`alcance_ifpb.py`](alcance_ifpb.py). As Partes 3 e 4 explicam o que conferir nela.

---

## Parte 3 — Do GeoPackage ao grafo

### 3.1 Ler com PyQGIS

```python
nodes_lyr, arcos_lyr = camada("nodes"), camada("arcos")
para_m = QgsCoordinateTransform(arcos_lyr.crs(), METRICO, QgsProject.instance())
for f in arcos_lyr.getFeatures(pedido):   # pedido: só os 6 campos usados
    g = f.geometry()
    g.transform(para_m)                   # geometria em UTM 25S (metros)
    ...
```

Os 59.603 arcos são lidos em **0,9 s**. Nenhum pacote além do QGIS é necessário para isso.

### 3.2 Montar o grafo com NetworkX

```python
grafo.add_edge(a["u"], a["v"], key=i, length=a["length"], arco=i)
if a["oneway"] and not mao_unica:
    # a pé: a mão única ganha o arco de volta (geometria invertida)
    grafo.add_edge(a["v"], a["u"], key=-i - 1, length=a["length"], arco=-i - 1)
```

- A mão dupla já tem os dois arcos na camada. Só a mão única precisa do arco de volta, e só a pé.
- O grafo a pé fica com 21.713 nós e 64.134 arcos; o de carro, com 18.173 nós e 46.262 arcos.

### 3.3 Onde começa: o nó de partida

O campus é um ponto; o grafo só tem nós. O script usa um índice espacial (`QgsSpatialIndex`) para achar o nó mais próximo, mas **só entre os nós da maior componente fortemente conexa**: de lá se chega a toda a rede e se volta dela. Sem isso, o nó escolhido pode ser uma rua sem saída de mão única, e o alcance sai quase vazio.

```text
[2] Partida no nó 4666479308, a 35 m do campus      (a pé)
[2] Partida no nó 799966499, a 80 m do campus       (de carro)
```

> **Nota: o que conferir no código**
>
> | Trecho | Por que é assim |
> | --- | --- |
> | `nx.MultiDiGraph()` | **Multi**: pode haver duas ruas diferentes entre os mesmos nós. **Di**: o sentido importa |
> | `a["tipos"] <= analise["vias"]` (carro) × `a["tipos"] & analise["vias"]` (a pé) | todos os tipos × pelo menos um tipo |
> | `max(nx.strongly_connected_components(grafo), key=len)` | o mesmo cuidado do `roteamento_malha_osmnx.py` |
> | `ponto` em EPSG:31985 | a distância do campus ao nó sai em metros |

---

## Parte 4 — Distância pela rede e faixas

### 4.1 Dijkstra com limite

```python
distancias = nx.single_source_dijkstra_path_length(
    grafo, origem, cutoff=raio, weight="length")
```

Devolve a distância pela rede, do nó de partida a **cada nó** alcançável até `raio` metros. É o mesmo cálculo do `nx.ego_graph(..., distance="length")`, mas guardando as distâncias, que são usadas para cortar as ruas. Leva 0,1 s para 4 km de carro.

### 4.2 Cortar os trechos no limite

Um nó a 700 m do campus "sobra" 100 m para os 800 m a pé. A rua que sai dele é percorrida só até 100 m. Um ponto a `s` metros do início do arco `u → v` está a `dist[u] + s` do campus. Então o pedaço alcançado na faixa `b` vai de 0 até `b − dist[u]`.

Na mão dupla, a mesma rua pode ser alcançada **pelas duas pontas**. O script trabalha por **trecho físico**: junta a ida e a volta, soma o que se alcança por cada lado e nunca conta a rua duas vezes.

> **A IA não valida por você.** A primeira versão deste script unia as geometrias de todos os pedaços e media o comprimento da união. O resultado parecia plausível (17,5 km a pé), mas a soma das faixas dava 18,9 km. Os pedaços de ida e de volta da mesma rua se sobrepunham, e a união não os fundia por diferenças mínimas de arredondamento. Contando por trecho físico, o valor certo é **16,2 km**: a versão anterior errava em +8%. A pista veio de uma conferência simples, **a soma das partes tem de dar o todo**.

### 4.3 As faixas

| A pé | km de vias | De carro | km de vias |
| --- | ---: | --- | ---: |
| até 200 m | 0,4 | até 1 km | 17,8 |
| 200 a 400 m | 2,2 | 1 a 2 km | 51,9 |
| 400 a 600 m | 6,6 | 2 a 3 km | 113,2 |
| 600 a 800 m | 7,0 | 3 a 4 km | 156,5 |
| **total** | **16,2** | **total** | **339,4** |

Cada faixa traz mais vias que a anterior: o anel cresce com a distância, como a área de um círculo.

---

## Parte 5 — Rodar e ler os resultados

Abra [`alcance_ifpb.py`](alcance_ifpb.py) no Editor do Console Python, ajuste `MALHA` e `PASTA_SAIDA` e execute. Saída esperada:

```text
[1] 22647 nós e 59603 arcos lidos de malha_joao_pessoa_all.gpkg em 0.9 s, sem internet

[1] A pé: grafo com 21713 nós e 64134 arcos
[2] Partida no nó 4666479308, a 35 m do campus
[3] 137 nós a até 800 m pela rede (0.0 s)
[4] 16.2 km de vias alcançadas; ponto mais distante a 747 m em linha reta
      polígono do alcance: 0.81 km² = 40% do círculo de 800 m (2.01 km²)
[5] QGIS (Área de serviço): 16.1 km × NetworkX 16.2 km (-0.2%)

[1] De carro: grafo com 18173 nós e 46262 arcos
[2] Partida no nó 799966499, a 80 m do campus
[3] 2953 nós a até 4000 m pela rede (0.1 s)
[4] 339.4 km de vias alcançadas; ponto mais distante a 3520 m em linha reta
      polígono do alcance: 20.92 km² = 42% do círculo de 4000 m (50.25 km²)
      ignorando a mão única: 388.3 km (+49.0 km, 14% a mais)
[5] QGIS (Área de serviço): 339.1 km × NetworkX 339.4 km (-0.1%)

[6] Resultados em …/alcance_ifpb/resultados/alcance_ifpb.gpkg
      Mapas: …/alcance_ifpb/resultados/alcance_ifpb.png
```

### 5.1 O polígono do alcance

O **polígono do alcance** envolve as vias alcançadas (envoltória côncava, `concaveHull`). Comparado com o círculo do mesmo raio, ele mede a eficiência da rede:

| | Círculo | Polígono do alcance | Polígono ÷ círculo |
| --- | ---: | ---: | ---: |
| A pé, 800 m | 2,01 km² | 0,81 km² | **40%** |
| De carro, 4 km | 50,25 km² | 20,92 km² | **42%** |

Uma malha em grade perfeita chegaria a ~64% (um losango dentro do círculo). Quanto menor a proporção, mais a rede obriga a desvios. Em volta do campus, pesam os quarteirões longos, o próprio terreno do campus e, de carro, a **Mata do Buraquinho**, o vazio a sudeste no mapa.

### 5.2 Linha reta × rede

![Dentro do círculo não quer dizer dentro do alcance](../../imgs/alcance_ifpb/3-reta-x-rede.png)

- **A pé:** um ponto a **337 m** ao sul do campus, em linha reta, está a **812 m** pela rede, fora do alcance de 800 m. Não há passagem direta pelo lado sul do terreno, e é preciso dar a volta pelo oeste.
- **De carro:** um ponto a **2,4 km** a leste, do outro lado da Mata do Buraquinho, está a **6,3 km** pela rede. O caminho contorna a mata pelo norte e ainda passa do ponto, desce e volta para chegar até ele.

Nenhum ponto alcançado fica além do raio em linha reta (747 m < 800 m; 3520 m < 4000 m): **a rede nunca é mais curta que a reta**. É a verificação mais simples de que o cálculo está coerente.

### 5.3 O que a mão única tira

![O que a mão única tira do alcance](../../imgs/alcance_ifpb/4-mao-unica.png)

Ignorando a mão única, o carro alcançaria **388 km** de vias: **49 km (14%) a mais**. Os trechos em vermelho só seriam alcançados andando na contramão. Eles se concentram nas bordas do alcance, onde o caminho certo é mais longo.

---

## Parte 6 — Conferir com a Área de serviço do QGIS

O QGIS tem a mesma análise pronta: **Caixa de Ferramentas de Processamento → Análise de redes → Área de serviço (a partir de ponto)** (*Processing Toolbox → Network analysis → Service area (from point)*). Para conferir à mão:

1. Carregue a camada `arcos` e reprojete para **EPSG:31985** (*Reprojetar camada*).
2. Abra a **Área de serviço (a partir de ponto)**: camada de rede = `arcos` reprojetada; tipo de caminho = **Mais curto**; ponto inicial = clique no campus; custo = **800** (a pé) ou **4000** (carro).
3. Em **Avançado**, a **Direção padrão** decide o sentido:
   - **carro: Direção para frente (Forward direction)**. Cada arco já está desenhado no sentido do tráfego, então "para frente" é exatamente a mão única;
   - **a pé: Ambas as direções (Both directions)**.

O script faz isso automaticamente (`COMPARAR_COM_QGIS = True`), sobre os **mesmos arcos** usados no grafo:

![NetworkX × QGIS](../../imgs/alcance_ifpb/5-networkx-x-qgis.png)

| | NetworkX | QGIS | Diferença |
| --- | ---: | ---: | ---: |
| A pé, 800 m | 16,2 km | 16,1 km | −0,2% |
| De carro, 4 km | 339,4 km | 339,1 km | −0,1% |

Duas ferramentas diferentes, a mesma resposta. A pequena diferença vem do **ponto de partida**: o QGIS parte do ponto da rua mais próximo do campus, e o NetworkX, do **nó** mais próximo (a 35 m a pé e a 80 m de carro).

> **Como o QGIS foi medido.** A Área de serviço devolve a ida e a volta de uma rua de mão dupla como **duas linhas sobrepostas**. Somar o comprimento delas contaria a rua duas vezes (o mesmo problema da Parte 4.2). O script mede pela área de uma faixa de 1 m em volta das linhas, que conta cada rua uma vez só.

> **Se o QGIS já faz, por que o NetworkX?** Porque, com o grafo na mão, o resto é Python: mudar o peso para tempo (`travel_time` já está na malha), calcular a partir de vários pontos de uma vez, fazer a comparação "ignorando a mão única", ou somar quantas escolas e paradas de ônibus cada faixa alcança. E o mesmo grafo serve para o roteamento por clique de [`roteamento_malha_osmnx.py`](../../apoio/osmnx/roteamento_malha_osmnx.py).

---

## Desafios

1. **Em minutos.** A camada `arcos` já tem `travel_time` (segundos, calculado pelo OSMnx a partir da velocidade de cada tipo de via). Troque o peso para `travel_time` e calcule o alcance de **10 minutos de carro**. A pé, use 4,8 km/h: 5, 10 e 15 minutos.
2. **Outro ponto de partida.** Troque `CENTRO` por outro lugar de João Pessoa (a Reitoria do IFPB, uma estação, sua casa) e compare a proporção polígono ÷ círculo. Onde a rede é mais "caminhável"?
3. **O que está a até 10 minutos?** Some, por faixa, quantos pontos de interesse ficam a até 800 m pela rede (por exemplo, paradas de ônibus). Dica: ligue cada ponto ao nó mais próximo e leia a distância em `distancias`.
4. **Outra cidade, uma vez.** Baixe com `malha_urbana_osmnx.py` a malha de Cabedelo e calcule o alcance do IFPB Campus Cabedelo. Se o alcance de 4 km sair do município, o script avisa: o que fazer?
