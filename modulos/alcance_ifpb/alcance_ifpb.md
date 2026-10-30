<!-- navegação -->
[⬅️ ⛰️ Perfil da PB-200](../perfil_pb200/perfil_pb200.md) · [🏠 Início](../../README.md) · [🔥 Focos de queimadas ➡️](../queimadas_pb/queimadas_pb.md)

# Até onde se chega a partir do IFPB: análise de redes com PyQGIS e NetworkX

> **Roteiro de aula:** prático, guiado e com aprofundamento técnico
> **Público:** estudantes de geotecnologias, planejamento urbano e mobilidade · **Nível:** 🔴 Avançado
> **Duração:** 35 minutos de aula prática (seções 1 a 5) + aprofundamento técnico para estudo posterior (seções 6 e 7)
> **Tema:** análise de redes, acessibilidade urbana e área de serviço (isodistância)
> **Tecnologias:** QGIS 3.44, PyQGIS e NetworkX (análise, offline); OSMnx (download da malha, feito uma vez); matplotlib; IA generativa

---

## 🧭 1. A proposta da aula

Para avaliar o alcance de um equipamento público, como uma escola, um hospital ou um campus, é comum desenhar um **círculo em linha reta** (um buffer). Mas **pessoas e veículos não andam em linha reta**: seguem as ruas, contornam quarteirões e barreiras e, de carro, respeitam a mão única.

Nesta aula, calculamos a **área de serviço** (*service area*, ou isodistância) do **IFPB Campus João Pessoa**:

- 🚶 **a pé:** até **800 m**, cerca de 10 minutos de caminhada a 4,8 km/h;
- 🚗 **de carro:** até **4 km**, respeitando a mão única.

A pergunta que guia a atividade:

> **Até onde se chega, de verdade, a partir do campus, e quanto o círculo em linha reta engana?**

![Alcance a pé e de carro a partir do campus](../../imgs/alcance_ifpb/1-alcance-ifpb.png)

### 🎯 Objetivos de aprendizagem

Ao final da aula, a turma será capaz de:

1. **diferenciar** a distância em linha reta (buffer) da distância pela rede (área de serviço);
2. **reconhecer** uma malha viária como um **grafo dirigido**: nós, arcos e o sentido de cada arco;
3. **interpretar** o alcance a pé e de carro, e o efeito da mão única no alcance de carro;
4. **explicar** por que baixar a malha uma vez e analisar offline torna o trabalho mais rápido e reprodutível;
5. **validar** o resultado do script com a ferramenta nativa **Área de serviço** do QGIS.

---

## 📋 2. Preparação e roteiro de tempo

### 🛠️ Antes da aula, o(a) professor(a) confere

- [ ] **QGIS** 3.34 LTR ou mais recente (material testado no 3.44) em todos os computadores.
- [ ] **NetworkX** no Python do QGIS: no Console Python, `import networkx` não pode dar erro. Se der, veja a seção 6.1 do *Guia OSMnx + QGIS no Windows* (PDF no Google Drive do curso). O OSMnx **não** precisa estar instalado: ele só serviu para baixar a malha.
- [ ] **matplotlib** no Python do QGIS, para os mapas lado a lado (opcional: sem ele, o script só não desenha a figura).
- [ ] **Dados:** `malha_joao_pessoa_all.gpkg` (27 MB) em `dados_curso/alcance_ifpb/` (veja [`dados_curso/`](../../dados_curso/README.md)).
- [ ] **Rede da sala:** não é preciso internet. A análise roda inteira offline.

> 💡 **Dica para quem conduz a aula:** rode o script uma vez antes da aula e deixe o resultado (`alcance_ifpb.gpkg` e `alcance_ifpb.png`) à mão. Se algum computador não tiver o NetworkX, a turma acompanha a Atividade 2 pelo resultado pronto, e o tempo da aula não vai para instalação.

### ⏱️ Planejamento minuto a minuto (35 min)

| Intervalo | Etapa | Foco da turma |
| :--- | :--- | :--- |
| **0–5 min** | Pergunta e contexto | Linha reta × pelas ruas. Por que 800 m e 4 km? |
| **5–13 min** | Atividade 1: a malha no QGIS | Abrir os arcos, ler os campos e ver o sentido das ruas com setas. |
| **13–23 min** | Atividade 2: o alcance pela rede | Rodar o script e ler o resultado: km de vias, polígono × círculo, mão única. |
| **23–31 min** | Atividade 3: validação cruzada | Refazer o alcance a pé com a Área de serviço nativa do QGIS e comparar. |
| **31–35 min** | Síntese e fechamento | Check-out oral e mensagem final. |

---

## 💡 3. Fundamentação

### 3.1 Linha reta (buffer) × pelas ruas (área de serviço)

No planejamento urbano, a ideia de **cidade caminhável** (*walkable city*) costuma usar **~800 m**, ou 10 minutos a pé, como raio de influência em volta de escolas, estações e serviços.

```
   [ Buffer circular ]                        [ Área de serviço ]
   distância euclidiana                       distância pelas ruas
            │                                          │
            ▼                                          ▼
   supõe um plano sem obstáculos              segue a rede: quarteirões,
                                              muros, mão única e acessos
```

> 🗣️ **Como explicar para a turma:**
> *"O círculo é o alcance de um pássaro: ele voa em linha reta por cima de muros e prédios. A área de serviço é o alcance de quem anda pela calçada: precisa dar a volta no quarteirão e não atravessa a Mata do Buraquinho."*

![Dentro do círculo não quer dizer dentro do alcance](../../imgs/alcance_ifpb/3-reta-x-rede.png)

Dois exemplos reais, calculados nesta aula:

- **A pé:** um ponto a **337 m** ao sul do campus, em linha reta, está a **812 m** pela rede, fora do alcance de 800 m. Não há passagem direta pelo lado sul do terreno; é preciso dar a volta pelo oeste.
- **De carro:** um ponto a **2,4 km** a leste, do outro lado da Mata do Buraquinho, está a **6,3 km** pela rede.

### 3.2 A malha como grafo: nós e arcos com sentido

Uma malha viária é modelada como um **grafo** $G = (V, E)$:

- **nós** ($V$): cruzamentos e pontas de rua, com coordenadas e um identificador do OpenStreetMap (`osmid`);
- **arcos** ($E$): trechos de rua que ligam dois nós, **de `u` para `v`**, com o comprimento em metros (`length`), o tipo de via (`highway`) e o sentido (`oneway`).

```
    [ nó u ] ───────────── arco u → v ─────────────> [ nó v ]
  (cruzamento 1)        comprimento: 120 m        (cruzamento 2)
```

> 🗣️ **Como explicar para a turma:**
> *"Numa rua de mão dupla, a camada tem duas setas, uma para cada lado. Numa rua de mão única, só uma. Para o carro, a rua de mão única é uma porta que só abre para um lado."*

> ⚠️ **Se o cálculo de carro ignorar o sentido**, o veículo "anda na contramão", e o alcance sai maior do que o real.

### 3.3 Online × offline: por que baixar a malha uma vez só

APIs públicas como o **Overpass** (do OpenStreetMap) são recursos compartilhados, com limite de uso e sujeitos a sobrecarga. Na preparação desta aula, em 21/10/2026, várias tentativas seguidas de baixar a malha de João Pessoa receberam `502 Bad Gateway … server is currently at capacity`, no QGIS e fora dele.

![Online × offline](../../imgs/alcance_ifpb/2-online-offline.png)

| | Online (direto na API) | Offline (o que fazemos) |
| :--- | :--- | :--- |
| **Execução** | cada aluno baixa a malha na aula | o professor baixa a malha **uma vez**, com o OSMnx |
| **Conexão** | internet estável para todos, ao mesmo tempo | **0 bytes** de internet durante a aula |
| **Velocidade** | minutos, quando o servidor responde | **~0,9 s** para ler a malha e **< 0,5 s** por análise |
| **Reprodutibilidade** | o OSM muda todo dia | GeoPackage fixo: resultados iguais para toda a turma |

### 3.4 Os dados e as regras de cada modo

O `malha_joao_pessoa_all.gpkg` (27 MB, **EPSG:4326**) foi baixado com o script [`apoio/osmnx/malha_urbana_osmnx.py`](../../apoio/osmnx/malha_urbana_osmnx.py), com a rede **`all`** (todas as vias). Tem 4 camadas:

| Camada | Feições | O que é |
| --- | ---: | --- |
| `nodes` | 22.647 | cruzamentos e pontas de rua |
| `edges` | 33.577 | uma linha por trecho de rua, para o mapa |
| `arcos` | 59.603 | uma linha por **sentido de circulação**, para o roteamento |
| `limite` | 1 | o município de João Pessoa |

As contas fecham: 7.551 trechos de mão única (1 arco cada) + 26.026 de mão dupla (2 arcos cada) = 59.603 arcos.

**A pé e de carro, as regras são diferentes.** O campo `highway` diz o tipo de via; quando o OSMnx junta trechos de tipos diferentes, grava uma lista como texto, por exemplo `['footway', 'residential']`.

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                        FILTRAGEM POR MODO                              │
   ├────────────────────────────────────┬───────────────────────────────────┤
   │ 🚶 A PÉ                            │ 🚗 DE CARRO                       │
   │ • basta UM dos tipos do trecho ser │ • TODOS os tipos do trecho têm de │
   │   de pedestre (residential,        │   ser de automóvel                │
   │   footway, path, steps, primary…)  │ • ficam de fora calçadões         │
   │ • autoestradas e ciclovias ficam   │   (footway), escadarias, trilhas  │
   │   de fora                          │   e vias de serviço (service)     │
   │ • IGNORA a mão única               │ • RESPEITA a mão única (oneway=1) │
   └────────────────────────────────────┴───────────────────────────────────┘
```

Nos dois modos, os arcos com `access` = `private` (2.315) ou `no` (151) ficam de fora. Um trecho `['footway', 'residential']` entra a pé, mas não de carro.

---

## 🛠️ 4. Trilha prática guiada

### 📍 Atividade 1: a malha no QGIS (8 min)

**Objetivo:** ver com os próprios olhos o que é um arco e o sentido de uma rua.

1. Arraste a camada `arcos` do `malha_joao_pessoa_all.gpkg` para o mapa.
2. Abra a **Tabela de atributos** e localize os campos:
   - `u`, `v`: os nós de início e de fim (o arco vai de `u` para `v`);
   - `length`: o comprimento do trecho, em **metros**, calculado pelo OSMnx;
   - `highway`: o tipo de via (às vezes, uma lista);
   - `oneway`: `1` = mão única, `0` = mão dupla;
   - `access`: restrição de acesso (`private` e `no` ficam de fora).
3. Em **Propriedades da camada → Simbologia**, troque a linha simples por **Seta** (*Arrow*).
4. Aproxime o mapa do campus e compare uma rua de mão única com uma de mão dupla.

> 💬 **Pausa para reflexão com a turma:**
> - *Por que uma rua de mão dupla aparece com duas setas sobrepostas?*
> - *Se somarmos o comprimento de todos os arcos, teremos o comprimento das ruas de João Pessoa?*

<details>
<summary>Respostas esperadas</summary>

- Porque a camada `arcos` guarda **um arco por sentido**: a mão dupla tem a ida (`u → v`) e a volta (`v → u`), com a mesma geometria em sentidos opostos.
- Não: a mão dupla seria contada **duas vezes**. Para medir ruas, é preciso juntar a ida e a volta do mesmo trecho físico. É exatamente o cuidado que o script toma ao somar os km de vias alcançadas.

</details>

---

### 📍 Atividade 2: o alcance pela rede (10 min)

**Objetivo:** calcular o alcance a pé e de carro e ler o que os números dizem.

1. Abra [`alcance_ifpb.py`](alcance_ifpb.py) no **Editor do Console Python** do QGIS.
2. Ajuste `MALHA` e `PASTA_SAIDA` para a sua pasta `dados_curso/alcance_ifpb/` e clique em **Executar script**.
3. Em poucos segundos, aparecem no mapa as camadas `alcance_faixas`, `alcance_poligonos` e `campus`, e a figura com os dois mapas lado a lado.
4. Leia o resultado com a turma:

| Faixa a pé | km de vias | Faixa de carro | km de vias |
| --- | ---: | --- | ---: |
| até 200 m | 0,4 | até 1 km | 17,8 |
| 200 a 400 m | 2,2 | 1 a 2 km | 51,9 |
| 400 a 600 m | 6,6 | 2 a 3 km | 113,2 |
| 600 a 800 m | 7,0 | 3 a 4 km | 156,5 |
| **total** | **16,2** | **total** | **339,4** |

| | A pé, 800 m | De carro, 4 km |
| --- | ---: | ---: |
| círculo | 2,01 km² | 50,25 km² |
| polígono do alcance | 0,81 km² | 20,92 km² |
| **polígono ÷ círculo** | **40%** | **42%** |

> 🗣️ **Como explicar para a turma:**
> *"O círculo promete que 100% da área está a 10 minutos a pé. Pelas ruas, só 40% está. Numa malha em grade perfeita, seria uns 64%. A diferença é o preço dos quarteirões longos, do próprio terreno do campus e, de carro, da Mata do Buraquinho, o vazio a sudeste do mapa."*

5. **O efeito da mão única.** O script refaz a análise de carro **ignorando** a mão única, só para comparar:

![O que a mão única tira do alcance](../../imgs/alcance_ifpb/4-mao-unica.png)

- **respeitando a mão única:** **339,4 km** de vias;
- **ignorando a mão única:** **388,3 km**, **49 km (14%) a mais**. Os trechos em vermelho só seriam alcançados andando na contramão; eles se concentram nas bordas, onde o caminho permitido é mais longo.

> 💬 **Pausa para reflexão:** *nenhum ponto alcançado a pé fica além de 800 m em linha reta (o mais distante está a 747 m). Isso é coincidência?*

<details>
<summary>Resposta esperada</summary>

Não. A rede **nunca** é mais curta que a linha reta: se um ponto está a 800 m pela rede, está a no máximo 800 m em linha reta. Por isso o alcance pela rede cabe sempre dentro do círculo. É uma verificação de coerência simples: se o script devolvesse um ponto a 850 m em linha reta, haveria um erro.

</details>

---

### 📍 Atividade 3: validação cruzada com o QGIS (8 min)

O QGIS tem a mesma análise pronta: **Caixa de Ferramentas de Processamento → Análise de redes → Área de serviço (a partir de ponto)** (*Network analysis → Service area (from point)*, `native:serviceareafrompoint`). Duas implementações independentes devem dar a mesma resposta.

1. Reprojete a camada `arcos` para **EPSG:31985** (*Reprojetar camada*): a ferramenta precisa de metros.
2. Abra a **Área de serviço (a partir de ponto)**:
   - **Tipo de caminho:** Mais curto;
   - **Ponto inicial:** clique no campus;
   - **Custo:** **800** (a pé).
3. Em **Parâmetros avançados → Direção padrão**, escolha **Ambas as direções** (*Both directions*): a pé, a mão única não vale. Para o carro, seria **Direção para frente** (*Forward direction*): cada arco já está desenhado no sentido do tráfego.
4. Execute e compare, no mapa, a saída com a camada `alcance_faixas` do script.

O script faz essa mesma comparação sozinho (`COMPARAR_COM_QGIS = True`), sobre os mesmos arcos:

![NetworkX × QGIS](../../imgs/alcance_ifpb/5-networkx-x-qgis.png)

| Modo e distância | NetworkX (script) | QGIS nativo | Diferença | |
| :--- | :---: | :---: | :---: | :---: |
| 🚶 A pé (800 m) | **16,2 km** | **16,1 km** | −0,2% | ✅ |
| 🚗 De carro (4 km) | **339,4 km** | **339,1 km** | −0,1% | ✅ |

> 💡 **Por que não dá exatamente igual?** Por causa do **ponto de partida**: o QGIS parte do ponto da rua mais próximo do campus; o script parte do **nó** mais próximo (a 35 m a pé e a 80 m de carro). A concordância não prova que o script está certo em tudo, mas mostra que ele reproduz uma ferramenta já testada.

> ⚠️ **Não some o comprimento da saída do QGIS.** A Área de serviço devolve a ida e a volta de uma rua de mão dupla como **duas linhas sobrepostas**: somar o `$length` contaria a rua duas vezes (a mesma armadilha da Atividade 1). O script mede pela área de uma faixa de 1 m em volta das linhas, que conta cada rua uma vez só.

---

## 🎓 5. Fechamento: checagem de aprendizagem

### 💬 Check-out oral

Peça que a turma complete as frases:

1. *"Um buffer de 800 m superestima o alcance a pé porque…"*
2. *"Para o carro, a camada `arcos` e um grafo dirigido são indispensáveis porque…"*
3. *"Baixar a malha uma vez e analisar offline é melhor para a aula porque…"*

<details>
<summary>Respostas esperadas</summary>

1. … supõe que se anda em linha reta, atravessando quarteirões, muros e a Mata do Buraquinho. Pelas ruas, o alcance a pé cobre só 40% do círculo.
2. … guardam o **sentido** de cada rua: sem eles, o carro "anda na contramão" e o alcance sai 14% maior.
3. … não depende de um servidor público que pode estar fora do ar, roda em menos de um segundo e dá o mesmo resultado para toda a turma.

</details>

### 🏁 Mensagem final

> *"A IA escreve o script em minutos, e o NetworkX calcula o alcance em milissegundos. Mas são os fundamentos de geoprocessamento que garantem que o resultado está certo: a diferença entre a linha reta e a rede, um sistema de coordenadas métrico e o efeito da mão única. Conferir o resultado continua sendo responsabilidade sua."*

---

## 💻 6. Aprofundamento técnico: o script e a IA

### 6.1 O fluxo do exercício

```
┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│ 1. DADOS OFFLINE       │ ──> │ 2. ANÁLISE DE REDES    │ ──> │ 3. VALIDAÇÃO           │
│ • malha em GeoPackage  │     │ • PyQGIS + NetworkX    │     │ • linha reta × rede    │
│ • nós e arcos          │     │ • Dijkstra com limite  │     │ • efeito da mão única  │
│ • sem depender da API  │     │ • corte das ruas       │     │ • comparação com QGIS  │
└────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

**O que o script entrega**, em `dados_curso/alcance_ifpb/resultados/`:

1. `alcance_ifpb.gpkg`, com as camadas `alcance_faixas` (um anel por faixa de distância, com os km de vias), `alcance_poligonos` (o polígono do alcance e o círculo de cada análise) e `campus`;
2. `alcance_ifpb.png`, os dois mapas lado a lado;
3. a comparação com a **Área de serviço** nativa do QGIS, impressa no console.

> **Por que a camada `arcos`, e não `edges`?** O *Guia OSMnx + QGIS no Windows* avisa (seção 8.1): gravado com `directed=False`, o grafo perde o sentido das vias, e uma rota pode entrar na contramão. A camada `arcos` guarda o grafo **dirigido**. Para o carro, é ela que garante a mão única.

### 6.2 A lógica do script (`alcance_ifpb.py`)

Os trechos centrais, copiados do script:

**Montar o grafo de cada modo.** A mão dupla já tem os dois arcos na camada; a pé, só a mão única ganha o arco de volta:

```python
def montar_grafo(arcos, analise, mao_unica):
    grafo = nx.MultiDiGraph()
    usados = []
    for i, a in enumerate(arcos):
        if a["access"] in ACESSO_PROIBIDO:
            continue
        if analise["mao_unica"]:
            # carro: todos os tipos do trecho têm de ser de automóvel
            if not a["tipos"] <= analise["vias"]:
                continue
        elif not a["tipos"] & analise["vias"]:
            continue  # a pé: basta um tipo por onde se anda
        grafo.add_edge(a["u"], a["v"], key=i, length=a["length"], arco=i)
        if a["oneway"] and not mao_unica:
            # a volta usa a geometria invertida (índice negativo)
            grafo.add_edge(a["v"], a["u"], key=-i - 1, length=a["length"], arco=-i - 1)
        usados.append(i)
    return grafo, usados
```

**Partir do campus e calcular as distâncias.** O nó de partida sai da **maior componente fortemente conexa**: de lá se chega a toda a rede. O Dijkstra devolve a distância pela rede até cada nó alcançável (o mesmo cálculo do `nx.ego_graph(..., distance="length")`):

```python
principal = max(nx.strongly_connected_components(grafo), key=len)
origem, snap = no_mais_proximo(nos, principal, ponto)
distancias = nx.single_source_dijkstra_path_length(
    grafo, origem, cutoff=raio, weight="length")
aneis, km, total = faixas_de_alcance(grafo, arcos, distancias, faixas)
```

**Cortar as ruas nas faixas.** Um ponto a `s` metros do início do arco `u → v` está a `dist[u] + s` do campus. Um nó a 700 m "sobra" 100 m para os 800 m a pé: a rua que sai dele é percorrida só até 100 m. A função `faixas_de_alcance()` faz esse corte **por trecho físico**: junta a ida e a volta da mesma rua, soma o que se alcança por cada ponta e nunca conta a rua duas vezes.

> **Nota: o que conferir no código**
>
> | Trecho | Por que é assim |
> | --- | --- |
> | `nx.MultiDiGraph()` | **Multi**: pode haver duas ruas diferentes entre os mesmos nós. **Di**: o sentido importa |
> | `a["tipos"] <= analise["vias"]` (carro) × `a["tipos"] & analise["vias"]` (a pé) | todos os tipos × pelo menos um tipo |
> | geometrias em EPSG:31985 | o corte das ruas e o polígono saem em metros |
> | `strongly_connected_components` | evita partir de uma rua sem saída de mão única |
> | contagem por trecho físico | ida e volta da mesma rua não somam duas vezes |

**Saída esperada no console:**

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

### 6.3 A IA não valida por você

A primeira versão deste script unia as geometrias de todos os pedaços alcançados e media o comprimento da união. Deu **17,5 km** a pé: um número plausível, que passaria despercebido. Mas a soma das faixas dava **18,9 km**. A pista veio de uma conferência simples: **a soma das partes tem de dar o todo**. Contando por trecho físico, o valor certo é **16,2 km**, e as duas contas passaram a fechar.

### 6.4 O prompt usado com a IA

```text
Atue como especialista em PyQGIS e análise de redes.
Escreva um script Python para o Console do QGIS 3.44 que calcule a área de
serviço (isodistância) a partir do IFPB Campus João Pessoa
(-34.87354, -7.13574), sem usar internet e sem OSMnx.

1. Entrada: GeoPackage 'malha_joao_pessoa_all.gpkg', gerado pelo OSMnx, com
   as camadas 'nodes' (osmid, x, y) e 'arcos' (u, v, length, highway, oneway,
   access) em EPSG:4326. Na camada 'arcos', cada feição é um sentido de
   circulação, desenhada de u para v. 'highway' pode ser uma lista gravada
   como texto, por exemplo "['footway', 'residential']".
2. Grafo (NetworkX): leia as camadas com QgsVectorLayer, reprojete as
   geometrias para EPSG:31985 (SIRGAS 2000 / UTM 25S) e monte dois
   nx.MultiDiGraph():
   a) a pé: basta um dos tipos do trecho ser de pedestre; a mão única não
      vale (acrescente o arco de volta só nos trechos de mão única);
   b) de carro: todos os tipos do trecho têm de ser de automóvel; respeite
      a mão única.
   Nos dois, exclua access = 'private' ou 'no'.
3. Partida: ligue o campus ao nó mais próximo dentro da maior componente
   fortemente conexa (strongly connected component).
4. Isodistância: use nx.single_source_dijkstra_path_length com cutoff:
   a pé, faixas de 200, 400, 600 e 800 m; de carro, 1, 2, 3 e 4 km.
   Corte as ruas no limite exato de cada faixa e conte cada rua uma vez só
   (na mão dupla, a ida e a volta são a mesma rua).
5. Saída: km de vias por faixa, polígono do alcance (concaveHull) comparado
   com o círculo de mesmo raio, e comparação com native:serviceareafrompoint.
Comentários em português.
```

> 💡 O item 4 termina com "conte cada rua uma vez só": é a lição da seção 6.3 virando instrução. Quando a conferência acha um erro, o prompt seguinte deve dizer como evitá-lo.

---

## 🛡️ 7. Resolução de problemas e dicionário

### ⚠️ Armadilhas comuns

| Sintoma | Causa | Como corrigir |
| :--- | :--- | :--- |
| **comprimentos minúsculos, em "graus"** | `$length` ou `.length()` medidos em EPSG:4326 | usar o `length` do OSMnx ou reprojetar para um SRC métrico (EPSG:31985) |
| **alcance quase vazio a partir do campus** | o nó de partida está numa rua sem saída de mão única | partir do nó mais próximo dentro da **maior componente fortemente conexa** |
| **km de vias inflados (de 1% a 19%, conforme a faixa)** | as geometrias de ida e de volta, sobrepostas, foram somadas | contar por **trecho físico**, juntando ida e volta |
| **alcance de carro 14% maior** | a rede foi tratada como não dirigida (`directed=False`) | usar a camada `arcos` e um `MultiDiGraph` |
| **carro passando por calçadões, ou pedestre sem as escadarias** | o mesmo filtro de `highway` para os dois modos | regras separadas: "algum tipo" a pé, "todos os tipos" de carro |
| **`ModuleNotFoundError: networkx`** | o NetworkX não está no Python do QGIS | seção 6.1 do *Guia OSMnx + QGIS no Windows* (PDF no Google Drive do curso) |
| **`502 Bad Gateway … at capacity`** ao baixar a malha | o servidor Overpass está sobrecarregado | baixar uma vez, fora da aula, e trabalhar offline (seção 3.3) |
| **"o alcance sai do limite da malha"** no console | a malha é pequena demais para a distância pedida | baixar uma malha maior, que cubra todo o alcance |

### 📖 Dicionário para estudantes

- **Buffer:** área a uma distância fixa em linha reta de um objeto; aqui, o círculo em volta do campus.
- **Área de serviço (isodistância):** tudo o que se alcança até uma distância **pela rede**.
- **Grafo:** um conjunto de **nós** ligados por **arcos**; o modelo matemático da malha viária.
- **Grafo dirigido:** cada arco tem um sentido (de `u` para `v`); é o que representa a mão única.
- **Dijkstra:** o algoritmo clássico que acha o menor caminho de um nó até todos os outros.
- **Componente fortemente conexa:** um pedaço do grafo em que se vai de qualquer nó a qualquer outro, respeitando os sentidos.
- **OSMnx:** biblioteca Python que baixa a malha viária do OpenStreetMap já como grafo.
- **NetworkX:** biblioteca Python para criar e analisar grafos.
- **Overpass:** a API pública que entrega os dados do OpenStreetMap; compartilhada e sujeita a sobrecarga.

---

## 🚀 8. Desafios para depois da aula

1. **Em minutos.** A camada `arcos` já tem `travel_time` (segundos, calculado pelo OSMnx a partir da velocidade de cada tipo de via). Troque o peso para `travel_time` e calcule o alcance de **10 minutos de carro**. A pé, use 4,8 km/h: 5, 10 e 15 minutos.
2. **Outro ponto de partida.** Troque `CENTRO` por outro lugar de João Pessoa (a Reitoria do IFPB, uma estação, sua casa) e compare a proporção polígono ÷ círculo. Onde a rede é mais "caminhável"?
3. **O que está a até 10 minutos?** Conte quantas paradas de ônibus ficam a até 800 m pela rede. Dica: ligue cada parada ao nó mais próximo e leia a distância em `distancias`.
4. **Outra cidade, uma vez.** Baixe com `malha_urbana_osmnx.py` a malha de Cabedelo e calcule o alcance do IFPB Campus Cabedelo. Se o alcance de 4 km sair do município, o script avisa: o que fazer?

---

<!-- navegação -->
[⬅️ ⛰️ Perfil da PB-200](../perfil_pb200/perfil_pb200.md) · [🏠 Início](../../README.md) · [🔥 Focos de queimadas ➡️](../queimadas_pb/queimadas_pb.md)
