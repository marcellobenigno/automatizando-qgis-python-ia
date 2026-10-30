<!-- navegação -->
[⬅️ 🛣️ Duplicação da PB-200](../pb200/pb200.md) · [🏠 Início](../../README.md) · [⛰️ Perfil da PB-200 ➡️](../perfil_pb200/perfil_pb200.md)

# Grade interativa SRTM/TOPODATA: de um mapa na web a um clique no QGIS

> **Roteiro de aula:** prático, guiado e com aprofundamento técnico
> **Público:** estudantes de geotecnologias e ciências da terra · **Nível:** 🟡 Intermediário
> **Duração:** 35 minutos de aula prática (seções 1 a 5) + aprofundamento técnico para estudo posterior (seções 6 e 7)
> **Tema:** extrair dados de uma página web com IA e criar ações em Python no QGIS para baixar o MDE de cada célula
> **Tecnologias:** QGIS 3.44 (Ações de camada), PyQGIS, GDAL; navegador (código-fonte da página); IA generativa

---

## 🧭 1. A proposta da aula

O [TOPODATA](http://www.dsr.inpe.br/topodata/) (INPE) oferece dados geomorfométricos de todo o Brasil (altitude, declividade, orientação, curvaturas…) derivados do SRTM, com resolução de 1″ (~30 m). Os dados são divididos em **556 folhas** de 1° de latitude × 1,5° de longitude.

O problema prático: para baixar uma folha, é preciso **saber o código dela** (`07S375`, `05S42_`…), montar a URL, baixar, salvar numa pasta e carregar no QGIS. Para uma folha, tudo bem. Para vinte, é uma tarde perdida.

Nesta aula, partimos **apenas de um link**, o mapa índice **https://map4s3.com.br/maps/topodata/**, e, conversando com uma IA, chegamos a uma grade no QGIS em que **basta clicar numa célula para baixar e abrir o modelo de elevação** daquela região.

A pergunta que guia a atividade:

> **Como transformar um mapa que só existe numa página web numa ferramenta do QGIS, em que um clique faz o trabalho de uma tarde?**

![A grade TOPODATA no QGIS](../../imgs/grade_topodata/1-apresentacao.png)

### 🎯 Objetivos de aprendizagem

Ao final da aula, a turma será capaz de:

1. **investigar** de onde um mapa web carrega os seus dados, com o código-fonte da página;
2. **converter** um arquivo de dados JavaScript em GeoJSON, preservando os atributos e as coordenadas;
3. **descobrir e testar** a regra que liga o código de uma folha à URL de download;
4. **criar e usar** uma ação Python numa camada do QGIS;
5. **reconhecer** o que torna um download robusto: reaproveitar o que já existe e nunca deixar arquivo pela metade.

---

## 📋 2. Preparação e roteiro de tempo

### 🛠️ Antes da aula, o(a) professor(a) confere

- [ ] **QGIS** 3.34 LTR ou mais recente (material testado no 3.44).
- [ ] **Rede da sala:** acesso a `map4s3.com.br`, `cdn.map4s3.com.br` e `data.inpe.br`.
- [ ] **A folha `07S375ZN.tif` já copiada** numa pasta `TOPODATA` em cada computador (é a folha da PB-200, usada também no [perfil topográfico](../perfil_pb200/perfil_pb200.md)). Na Atividade 3, a ação vai **reaproveitá-la** em vez de baixar de novo.
- [ ] **Espaço em disco:** ~70 MB por folha de altitude (até ~105 MB).
- [ ] **Assistente de IA** aberto no navegador.

> 💡 **Dica para quem conduz a aula:** com uma turma inteira baixando folhas de 70 MB ao mesmo tempo, a rede da sala pode travar. Por isso a folha `07S375` fica pré-copiada: a turma vê a ação funcionando (e reaproveitando o arquivo) sem depender da rede. Se a rede aguentar, cada um baixa mais **uma** célula, de preferência a da própria cidade.

> As capturas de tela estão com o QGIS 3.44 em inglês; no texto aparecem os nomes em português e, entre parênteses, em inglês.

### ⏱️ Planejamento minuto a minuto (35 min)

| Intervalo | Etapa | Foco da turma |
| :--- | :--- | :--- |
| **0–5 min** | Pergunta e contexto | O TOPODATA, as 556 folhas e o problema de achar o código de cada uma. |
| **5–13 min** | Atividade 1: de onde vem a grade? | Ler o código-fonte da página, achar o arquivo de dados e carregar a grade no QGIS. |
| **13–20 min** | Atividade 2: a regra do endereço | Montar a URL de uma folha a partir do código e testar no navegador. |
| **20–32 min** | Atividade 3: a ação de clique | Criar a ação na camada e clicar numa célula. |
| **32–35 min** | Síntese e fechamento | Check-out oral e mensagem final. |

---

## 💡 3. Fundamentação

### 3.1 Todo mapa web carrega os dados de algum lugar

Um mapa web (Leaflet, OpenLayers…) precisa receber a geometria de algum lugar: um arquivo `.geojson`, um serviço WFS, uma API, ou um **arquivo JavaScript com os dados embutidos**. O mapa índice do Map4s3 mostra a grade, mas não oferece um arquivo para baixar: a grade está **dentro do código da página**.

> 🗣️ **Como explicar para a turma:**
> *"O mapa no navegador é a vitrine de uma loja. O que está na vitrine veio do estoque, e o código-fonte da página é a nota fiscal: lá está escrito de onde cada coisa veio."*

![O mapa índice TOPODATA no Map4s3](../../imgs/grade_topodata/2-site-topodata.png)

### 3.2 O que é uma ação de camada

Uma **ação** é um comando guardado na própria camada do QGIS, que roda quando você clica numa feição. Uma ação do tipo **Python** pode baixar arquivos, abrir janelas e carregar camadas. Antes de executá-la, o QGIS **substitui** cada expressão `[% … %]` pelo valor da feição clicada. Para a célula `07S375`:

```python
scene = '[% "scene" %]'.strip()   # o QGIS executa: scene = '07S375'.strip()
```

> ⚠️ **Por isso o script da ação não roda no Console Python:** lá não há substituição, e `scene` seria literalmente `[% "scene" %]`.

---

## 🛠️ 4. Trilha prática guiada

### 📍 Atividade 1: de onde vem a grade? (8 min)

**Objetivo:** achar o arquivo de dados por trás do mapa e transformá-lo numa camada do QGIS.

1. **Peça à IA o caminho mais curto:**
   ```text
   Leia o código-fonte da página https://map4s3.com.br/maps/topodata/
   e extraia a grade GeoJSON do mapa índice TOPODATA.
   ```
   Na conversa que originou este exercício, a IA **não conseguiu**: as ferramentas de navegação dos chatbots costumam receber só o HTML "cru", não executam o JavaScript e às vezes recusam arquivos `.js`. Em vez de inventar uma resposta, ela pediu ajuda, e esse é o comportamento que queremos.
2. **Ajude a IA:** no navegador, abra a página, clique com o botão direito → **Exibir código-fonte da página** (`Ctrl+U`), copie tudo e mande para a IA (o prompt completo está na seção 6.2). Ela aponta o suspeito, carregado por uma tag `<script>`:
   ```html
   <script type="text/javascript"
           src="https://cdn.map4s3.com.br/js/maps/topodata/topodata-dataset.js"></script>
   ```
3. **Confirme com os próprios olhos:** abra esse endereço numa aba. O conteúdo é um GeoJSON **atribuído a uma variável JavaScript**:

![O conteúdo do topodata-dataset.js](../../imgs/grade_topodata/3-pagina-codigo-grade-geojson-js.png)

```text
var pol_topodata = {"type": "FeatureCollection","features":[{"type":"Feature","properties":{"scene":"00S465"},"geometry":{"type":"Polygon", ...
```

4. **Carregue a grade:** rode no Editor do Console Python o script da seção 6.3, que baixa o arquivo, tira a variável JavaScript, salva o GeoJSON e carrega a grade no mapa. Confira: **556 feições**, EPSG:4326, campo `scene` preenchido em todas as linhas, e a grade sem deslocamento em relação ao litoral.

> 💬 **Pausa para reflexão com a turma:**
> - *Por que foi bom a IA dizer "não consigo ler a página", em vez de responder qualquer coisa?*
> - *O arquivo tem duas variáveis, `pol_topodata` e `pt_topodata`. Qual delas queremos, e por quê?*

<details>
<summary>Respostas esperadas</summary>

- Porque uma resposta inventada (uma URL que "parece" certa, uma grade "aproximada") passaria por verdadeira. Quando a IA admite o limite, você sabe o que fazer: mandar o código-fonte para ela.
- `pol_topodata`, com os **556 polígonos** da grade. A `pt_topodata` tem 556 **pontos**, usados só para os rótulos no mapa web. Sem dizer qual você quer, a IA pode juntar as duas numa camada de geometria mista, ou pegar a errada.

</details>

---

### 📍 Atividade 2: a regra do endereço de download (7 min)

**Objetivo:** transformar o código da folha (`scene`) na URL do arquivo.

Os arquivos estão no servidor do INPE / Brazil Data Cube:

```text
https://data.inpe.br/bdc/data/topodata/v001/{pasta}/{folha}/{scene}ZN.tif
```

| scene | pasta (`scene[:3]`) | folha (`scene[3:]`) | URL |
| --- | --- | --- | --- |
| `07S375` | `07S` | `375` | `…/v001/07S/375/07S375ZN.tif` |
| `05S42_` | `05S` | `42_` | `…/v001/05S/42_/05S42_ZN.tif` |

1. Monte com a turma a URL da folha `07S375` e cole no navegador: o download começa (pode cancelar, a folha já está na máquina).
2. Escolha uma célula da grade perto da sua cidade, leia o `scene` na tabela de atributos e monte a URL dela.

Três detalhes que importam:

- **`ZN` é a altimetria:** o MDE refinado, em metros, referenciado ao geoide EGM96. Os outros planos de informação (declividade, orientação, curvaturas…) seguem o mesmo padrão, trocando só o sufixo (seção 6.4).
- **O `_` faz parte do código:** quando a longitude tem só dois dígitos (`42` → 42°), o código é completado com `_` para ter sempre 6 caracteres.
- **Não há separador antes de `ZN`:** `07S375ZN.tif`, e não `07S375_ZN.tif`.

> 💬 **Pausa para reflexão:** *se o script esquecesse do `_` e montasse a URL só com `05S42`, quantas células da grade dariam erro?*

<details>
<summary>Resposta esperada</summary>

**Metade:** 276 das 556 células têm o `_`. É o tipo de regra que só se descobre testando com mais de um exemplo, e que a IA pode "corrigir" sem avisar se você não disser que o `_` faz parte do código.

</details>

---

### 📍 Atividade 3: a ação de clique (12 min)

**Objetivo:** dar à grade um botão: clicou numa célula, o modelo de elevação aparece no mapa.

1. Clique com o botão direito em **`grade_topodata`** → **Propriedades (Properties)** → **Ações (Actions)** → **+** (Adicionar nova ação).
2. Preencha:
   - **Tipo (Type):** Python;
   - **Descrição (Description):** `Baixar TOPODATA (altitude)`;
   - **Nome curto (Short name):** `TOPODATA`;
   - **Escopos (Action scopes):** **Tela (Canvas)** e **Feição (Feature)**;
   - **Texto da ação (Action text):** o conteúdo de [`acao_baixar_celula.py`](acao_baixar_celula.py), a versão revisada do script que a IA gerou (o prompt está na seção 6.5).
3. **OK** e **OK**.

![Editando a ação Python](../../imgs/grade_topodata/5-editar-acao-python.png)

A ação aparece na lista da camada:

![Ações da camada grade_topodata](../../imgs/grade_topodata/4-propriedades-acoes.png)

4. Na barra **Atributos (Attributes)**, abra o menu da ferramenta **Executar ação da feição (Run Feature Action)** (engrenagem com uma seta) e escolha **`Baixar TOPODATA (altitude)`**.
5. Clique na célula **`07S375`** e escolha a pasta `TOPODATA` onde a folha já está: a ação **reaproveita** o arquivo e o carrega no mapa, sem baixar nada.
6. Se a rede permitir, clique em **mais uma** célula: agora a ação baixa, com barra de progresso.

![Baixando a célula 07S375](../../imgs/grade_topodata/6-baixando-uma-celula.png)

Ao terminar, o raster aparece no mapa e no painel **Camadas**, com o nome da célula:

![Raster 07S375 carregado](../../imgs/grade_topodata/7-raster-carregado.png)

7. Salve o projeto (`Ctrl+S`): a ação fica gravada no `.qgz`.

> 💬 **Pausa para reflexão:** *a ação baixa primeiro para `07S375ZN.tif.part` e só no fim renomeia para `07S375ZN.tif`. Por quê?*

<details>
<summary>Resposta esperada</summary>

Para que um download interrompido (internet que cai, Cancelar, servidor que fecha a conexão) **nunca deixe um arquivo pela metade com o nome final**. Se deixasse, na próxima vez a ação acharia o arquivo, pensaria que ele está pronto e tentaria carregar um raster quebrado. O `.part` só vira `.tif` depois de conferir o tamanho e abrir o arquivo como raster.

</details>

---

## 🎓 5. Fechamento: checagem de aprendizagem

### 💬 Check-out oral

Peça que a turma complete as frases:

1. *"Para descobrir de onde um mapa web tira os dados, eu abro…"*
2. *"A IA precisa preservar o campo `scene` sem renomear porque…"*
3. *"Quando a folha já está na pasta, a ação não baixa de novo porque…"*

<details>
<summary>Respostas esperadas</summary>

1. … o código-fonte da página (`Ctrl+U`) e procuro de onde vêm os dados: um `.geojson`, um serviço, uma API ou um script com os dados embutidos. Se não estiver ali, a aba **Network** das ferramentas do desenvolvedor (`F12`).
2. … a ação lê `[% "scene" %]` para montar a URL. Se a IA "melhorar" o nome para `codigo` ou `folha`, a ação quebra.
3. … ela confere se o arquivo já existe e se abre como raster válido; se sim, só carrega. Na Atividade 3, foi o que aconteceu com a `07S375`.

</details>

### 🏁 Mensagem final

> *"Partimos de um link e chegamos a uma ferramenta. A IA não leu a página sozinha, e foi bom ela admitir isso; com o código-fonte em mãos, achou o arquivo, converteu e escreveu a ação. Mas foram as nossas instruções que fizeram tudo funcionar: preservar o `scene`, não mexer nas coordenadas, testar a regra da URL com o `_` e nunca deixar um arquivo pela metade."*

---

## 💻 6. Aprofundamento técnico: os prompts e as ações

### 6.1 O que deve ser entregue

1. `dados_curso/grade_topodata/grade_topodata.geojson`: a grade com as 556 células, em **EPSG:4326**, com o atributo `scene` (código da folha).
2. Uma **ação de clique** na camada: clicou numa célula → escolhe a pasta → baixa (ou reaproveita) o GeoTIFF → carrega no projeto.
3. Uma **ação para várias células selecionadas**, com barra de progresso e relatório final (seção 6.6).

Requisitos das duas ações:

- o usuário **escolhe a pasta de destino**;
- se o arquivo **já existir** na pasta e for um raster válido, ele é **reaproveitado** (não baixa de novo);
- se o raster **já estiver no projeto**, não é adicionado duas vezes;
- download incompleto ou cancelado **não deixa arquivo quebrado** na pasta.

### 6.2 Os prompts para achar e converter a grade

**Mandar o código-fonte** (Atividade 1, passo 2):

```text
Este é o código-fonte HTML da página https://map4s3.com.br/maps/topodata/
(um mapa Leaflet com a grade de articulação do TOPODATA).

<cole aqui o HTML>

Identifique de onde o mapa carrega os polígonos da grade: arquivo
.geojson, serviço WFS, API ou dados embutidos em algum script.
Liste os endereços completos dos candidatos e justifique.
Não invente URLs: use apenas o que está no código.
```

> **Plano B: o DevTools.** Se o dado não estivesse no HTML, a pista estaria na aba **Network (Rede)** das ferramentas do desenvolvedor (`F12`): recarregue a página, filtre por **Fetch/XHR** e por **JS**, e procure respostas com `FeatureCollection`. Peça à IA um trecho de código para o **Console** do navegador que liste os recursos carregados; foi o que ela sugeriu na conversa original.

**Converter o `.js` em GeoJSON.** Abra o endereço do arquivo no navegador, salve com **Salvar como…** (`Ctrl+S`) e anexe ao chat:

```text
Anexei o arquivo topodata-dataset.js, que alimenta o mapa índice do TOPODATA.

Converta os POLÍGONOS da grade em um arquivo GeoJSON:
- nome: grade_topodata.geojson
- CRS: WGS 84 (EPSG:4326)
- preserve TODOS os atributos originais, sem renomear; em especial o campo
  "scene" (código da folha, ex.: 07S375), que será usado por uma ação no
  QGIS para montar a URL de download de cada célula
- não altere, arredonde nem reconstrua as coordenadas
- confira e me informe: quantidade de feições, tipos de geometria,
  extensão (min/max de lon e lat) e se há códigos "scene" repetidos
```

**Por que tanto detalhe?**

- **"Os polígonos":** o arquivo tem **duas** variáveis, `pol_topodata` (556 polígonos) e `pt_topodata` (556 pontos, para os rótulos).
- **"Preserve o `scene`":** é o requisito que faz o resto funcionar; a ação lê `[% "scene" %]`.
- **"Não altere as coordenadas":** os vértices são `-46.500138914…`, e não `-46.5`. É meio pixel de 1″ (0,000139°): a grade acompanha a **borda externa dos pixels** do raster. Uma IA "caprichosa" arredondaria isso sem avisar.
- **"Confira e informe":** números que você consegue checar no QGIS.

Saída esperada: **556 polígonos**, extensão de **−75° a −34,5°** de longitude e **−34° a 6°** de latitude, nenhum `scene` repetido.

### 6.3 Você nem precisava da IA para a conversão (mas precisava saber disso)

O conteúdo depois do `=` **já é GeoJSON**. Toda a conversão cabe em poucas linhas, e é um ótimo exercício pedir à IA para explicar este código. Ajuste `SAIDA` e rode no Editor do Console Python do QGIS: o script salva o GeoJSON e já carrega a grade no mapa.

```python
import json, re
from pathlib import Path
from urllib.request import urlopen

from qgis.core import QgsProject, QgsVectorLayer

URL = "https://cdn.map4s3.com.br/js/maps/topodata/topodata-dataset.js"
SAIDA = Path.home() / "grade_topodata.geojson"   # ajuste o caminho
texto = urlopen(URL).read().decode("utf-8")

# Cada "var nome = {...};" vira um objeto Python
decoder = json.JSONDecoder()
dados = {m.group(1): decoder.raw_decode(texto, m.end())[0]
         for m in re.finditer(r"var\s*(\w+)\s*=\s*", texto)}

print({nome: len(d["features"]) for nome, d in dados.items()})
# {'pol_topodata': 556, 'pt_topodata': 556}

with open(SAIDA, "w", encoding="utf-8") as f:
    json.dump(dados["pol_topodata"], f)
print("Salvo em", SAIDA)

# Carrega a grade no projeto
grade = QgsVectorLayer(str(SAIDA), "grade_topodata", "ogr")
if grade.isValid():
    QgsProject.instance().addMapLayer(grade)
    iface.setActiveLayer(grade)
    iface.zoomToActiveLayer()
    print("Camada carregada:", grade.featureCount(), "feições,", grade.crs().authid())
else:
    print("Não foi possível carregar", SAIDA)
```

> ⚠️ **Use sempre caminho completo.** No QGIS, a "pasta atual" do Python não é a pasta do projeto. No Windows ela costuma ser a pasta de instalação do QGIS (`C:\Program Files\QGIS …`), onde não se pode gravar. Um `open("grade_topodata.geojson", "w")` falha com `PermissionError` (ou, no macOS, `Read-only file system`).

### 6.4 Os planos de informação do TOPODATA

| Sufixo | Plano de informação | Unidade / classes |
| --- | --- | --- |
| `ZN` | Altimetria numérica (MDE): dado primário, do qual os demais derivam | metros (EGM96) |
| `SN` | Declividade numérica | % |
| `SA` · `SB` · `SC` | Declividade em classes | 4 classes (Marques 1971/Lepsch 1991) · 7 classes A–G (Lepsch 1991) · 6 classes (EMBRAPA 1999) |
| `ON` | Orientação de vertentes numérica | graus (0°–360°) |
| `OC` | Orientação de vertentes em octantes | N, NE, E, SE, S, SW, W, NW |
| `VN` | Curvatura vertical numérica (perfil: côncavo/convexo) | °/m |
| `V3` · `V5` | Curvatura vertical em classes | 3 ou 5 classes |
| `HN` | Curvatura horizontal numérica (convergente/divergente) | °/m |
| `H3` · `H5` | Curvatura horizontal em classes | 3 ou 5 classes |
| `FT` | Forma do terreno (curvatura vertical × horizontal) | 9 classes |
| `DD` | Delineamento de microbacias (talvegues e divisores) | apoio à digitalização da drenagem |

### 6.5 A ação de clique: o prompt e o que conferir

Na mesma conversa das etapas anteriores:

```text
Escreva o código de uma AÇÃO do tipo Python para o QGIS 3.44
(Propriedades da camada → Ações), na camada "grade_topodata".

Ao clicar numa célula:
1. Leia o código da folha com '[% "scene" %]' e valide com a regex
   r"\d{2}[NS]\d{2,3}_?" (há códigos como 07S375 e 05S42_).
2. Monte a URL:
   https://data.inpe.br/bdc/data/topodata/v001/{scene[:3]}/{scene[3:]}/{scene}ZN.tif
   Nome do arquivo: {scene}ZN.tif
3. Peça a pasta de destino com QFileDialog (padrão: ~/TOPODATA) e lembre
   a última pasta escolhida com QgsSettings.
4. Se o raster já estiver carregado no projeto (mesmo caminho), apenas
   ative a camada e avise.
5. Se o arquivo já existir na pasta e for um raster válido (gdal.Open,
   fechando o dataset em seguida), carregue sem baixar.
6. Senão, baixe com urllib para um arquivo temporário ".part", com
   QProgressDialog e botão Cancelar; confira se o tamanho baixado bate com
   o Content-Length; valide como raster com gdal.Open, feche o dataset
   (ds = None) e só então renomeie para o nome final.
7. Carregue no projeto com o nome da célula.
8. Em qualquer saída (erro, cancelamento), apague o ".part". Mostre erros
   com QMessageBox, incluindo a URL usada.

Use apenas a biblioteca padrão e a API do QGIS (nada de requests).
Comentários em português.
```

> **Nota: o que conferir no código** ([`acao_baixar_celula.py`](acao_baixar_celula.py))
>
> | Trecho | Por que é assim |
> | --- | --- |
> | download em `arquivo.tif.part` e `temporario.replace(arquivo)` no fim | se a internet cair no meio, o arquivo final nunca fica pela metade |
> | `tamanho_baixado != tamanho_total` | o servidor pode fechar a conexão sem erro; só o tamanho denuncia |
> | `raster_valido()` (`gdal.Open`) **antes** de renomear | um 404 pode vir como página HTML salva com extensão `.tif` |
> | `ds = None` em `raster_valido()` | fecha o arquivo: no Windows, um arquivo aberto não pode ser renomeado nem apagado (`PermissionError: [WinError 32]`). Um `QgsRasterLayer` de teste deixaria o `.part` aberto |
> | `finally: apagar_seguro(temporario)` | limpa o `.part` mesmo se der erro ou cancelamento, sem que uma falha ao apagar esconda o erro real |
> | `renomear_com_tentativas()` | no Windows, antivírus e pastas de rede podem segurar o arquivo por um instante: tenta de novo antes de desistir |
> | comparação por `Path(fonte).resolve()` | evita carregar duas vezes o mesmo arquivo escrito com caminhos diferentes |

**Levar a ação para outros projetos:** **Propriedades** → **Estilo (Style)** → **Salvar estilo (Save Style)**, com a categoria **Ações (Actions)** marcada. O estilo salvo (`.qml`) leva junto a simbologia e as ações: ao carregar a grade em outro projeto, carregue o estilo e a ação já vem pronta.

### 6.6 A ação para várias células selecionadas

Na mesma conversa, com o script da ação de clique como referência:

```text
Agora crie uma segunda versão que trabalhe com VÁRIAS células:
- use as feições SELECIONADAS da camada ativa (iface.activeLayer());
- valide: há camada ativa? há seleção? existe o campo "scene"?
- peça a pasta de destino UMA vez só;
- para cada célula, as mesmas regras de antes: reaproveitar arquivo válido,
  não duplicar camada já carregada, baixar via ".part";
- uma QProgressDialog para o conjunto (célula i de n, MB baixados) com
  Cancelar que interrompe o download em andamento;
- um erro numa célula NÃO pode interromper as outras: guarde e continue;
- no fim, um relatório em QMessageBox: selecionadas, baixadas, reaproveitadas,
  camadas adicionadas e os erros (no máximo 10, com a URL).
```

O resultado está em [`acao_baixar_selecionadas.py`](acao_baixar_selecionadas.py). Repare na diferença de estrutura: o `try/except` está **dentro** do laço. Na ação de clique, um erro encerra a ação; aqui, um erro vira **uma linha no relatório**, e o laço segue para a próxima célula.

**Duas formas de rodar:**

- **a) Editor do Console Python.** Selecione algumas células, abra o editor (`Ctrl+Alt+P` → *Mostrar editor*), abra o arquivo e execute. Bom para testar.
- **b) Como ação de camada.** Crie uma nova ação Python como na Atividade 3, com **Descrição** `Baixar TOPODATA das células selecionadas`, **Escopo** apenas **Camada (Layer)** e o conteúdo de `acao_baixar_selecionadas.py`. Ações de escopo *Camada* aparecem no botão **Ações (Actions)** da barra da **Tabela de atributos** (ícone de engrenagem, perto do fim da barra). Abra a tabela, selecione as células e execute.

![Tabela de atributos com as quatro células selecionadas](../../imgs/grade_topodata/8-tabela-celulas-selecionadas.png)

Durante o download, a janela mostra a célula e os MB já baixados:

![Baixando as células selecionadas](../../imgs/grade_topodata/9-baixando-selecionadas.png)

**Conferir:** selecione 4 células vizinhas (por exemplo, em volta da sua cidade) e rode **duas vezes**:

| Execução | Baixados | Reaproveitados | Camadas adicionadas |
| --- | --- | --- | --- |
| 1ª | 4 | 0 | 4 |
| 2ª (camadas ainda no projeto) | 0 | 4 | 0 |

Se a 2ª execução baixar tudo de novo, a verificação de "arquivo existente" não está funcionando.

Nas capturas abaixo, a célula `07S375` já tinha sido baixada pela ação de clique. Por isso a 1ª execução mostra **3 baixados e 1 reaproveitado**:

![Relatório da 1ª execução](../../imgs/grade_topodata/10-relatorio-final.png)

![As quatro folhas carregadas](../../imgs/grade_topodata/11-mosaico-carregado.png)

Na 2ª execução, nada é baixado. Repare que ela rodou com um **raster como camada ativa** (o último baixado), e mesmo assim funcionou, graças ao `[% @layer_id %]`:

![Relatório da 2ª execução](../../imgs/grade_topodata/12-relatorio-segunda-execucao.png)

> **Cuidado com o tamanho:** cada folha de altitude tem ~70 MB em média. As 556 folhas do Brasil somam **~40 GB**.

---

## 🛡️ 7. Resolução de problemas e dicionário

### ⚠️ Armadilhas comuns

| Sintoma | Causa | Como corrigir |
| :--- | :--- | :--- |
| **a IA diz que não consegue ler a página** | o chat recebe só o HTML "cru", sem executar o JavaScript | mandar o código-fonte (`Ctrl+U`) e depois o arquivo `.js` |
| **a camada tem pontos e polígonos misturados** | a conversão juntou `pol_topodata` e `pt_topodata` | pedir só os **polígonos** (`pol_topodata`) |
| **a ação não encontra o campo** | a IA renomeou `scene` para `codigo` ou `folha` | exigir no prompt: "preserve os atributos, sem renomear" |
| **a grade não encaixa nos pixels do raster** | as coordenadas foram arredondadas (`-46.5` em vez de `-46.500138914…`) | "não altere, arredonde nem reconstrua as coordenadas" |
| **`PermissionError` ou `Read-only file system` ao salvar** | caminho relativo: a "pasta atual" do Python é a de instalação do QGIS | usar caminho completo |
| **`[% "scene" %]` literal, ou erro no Console** | o script da ação foi rodado no Console, onde não há substituição | rodar como ação da camada |
| **404 nas células com `_`** | a URL foi montada sem o `_` (`05S42` em vez de `05S42_`) | o `_` faz parte do código: use o `scene` inteiro |
| **raster quebrado na pasta** | download interrompido salvo com o nome final | baixar para `.part`, conferir tamanho e `gdal.Open`, só então renomear |
| **`PermissionError: [WinError 32]` ao renomear** | o arquivo ficou aberto (dataset GDAL ou `QgsRasterLayer` de teste) | fechar com `ds = None` antes de renomear |
| **a 2ª execução baixa tudo de novo** | a verificação de arquivo existente não funciona | conferir o caminho e o teste de raster válido |
| **a rede da sala trava na aula** | a turma inteira baixando folhas de 70 MB | pré-copiar a `07S375` e baixar no máximo uma célula por pessoa |

### 📖 Dicionário para estudantes

- **TOPODATA:** o banco de dados geomorfométricos do INPE, derivado do SRTM, com pixel de ~30 m.
- **MDE (Modelo Digital de Elevação):** raster em que cada pixel guarda uma altitude.
- **Folha / célula:** um recorte de 1° × 1,5° do TOPODATA, identificado por um código (`scene`).
- **Código-fonte da página:** o HTML que o navegador recebe, visto com `Ctrl+U`.
- **GeoJSON:** formato de texto para geometrias e atributos, muito usado em mapas web.
- **Ação de camada:** um comando guardado na camada, que roda ao clicar numa feição ou na camada.
- **`[% … %]`:** expressão que o QGIS troca pelo valor da feição antes de executar a ação.
- **Arquivo `.part`:** o arquivo temporário de um download em andamento; só vira o arquivo final quando termina e é conferido.
- **GDAL:** a biblioteca que o QGIS usa para ler e gravar rasters.

---

## 🚀 8. Desafios para depois da aula

1. **Outro plano de informação.** Crie uma segunda ação que baixe a **declividade** (`SN`) em vez da altitude. O que muda no script? (Dica: o sufixo `ZN` aparece em dois lugares, na URL e no nome do arquivo.)
2. **Várias células.** Configure a ação da seção 6.6 e baixe as 4 células em volta da sua cidade. Rode duas vezes e confira o relatório.
3. **O mosaico.** Com as 4 folhas carregadas, crie um mosaico virtual (`gdal:buildvirtualraster`) e use-o no [perfil topográfico](../perfil_pb200/perfil_pb200.md) de uma rodovia que cruze mais de uma folha.
4. **Outro mapa índice.** Escolha outro mapa web que mostre uma grade ou camada sem oferecer download, e repita a investigação da Atividade 1. Onde estavam os dados?

---

<!-- navegação -->
[⬅️ 🛣️ Duplicação da PB-200](../pb200/pb200.md) · [🏠 Início](../../README.md) · [⛰️ Perfil da PB-200 ➡️](../perfil_pb200/perfil_pb200.md)
