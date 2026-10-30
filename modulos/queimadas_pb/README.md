# Focos de queimadas na Paraíba: do Controlador Temporal do QGIS a um dashboard na web

> **Exercício prático do minicurso:** Automatizando o QGIS com Python e IA
> **Área temática:** análise espaço-temporal, monitoramento de queimadas e comunicação de dados
> **Ferramentas:** QGIS 3.44 (Controlador Temporal) e PyQGIS; Leaflet com os plugins TimeDimension, heat e markercluster; Vue.js, Tom Select, Highcharts e Tailwind CSS; GitHub Pages; IA generativa

---

### 📋 Visão geral do exercício

Entre janeiro e outubro de 2026, o satélite de referência do INPE detectou **2.445 focos de calor** na Paraíba. Cada foco tem **data e hora**, e é aí que mora a pergunta: *quando* e *onde* o fogo aparece ao longo do ano?

O QGIS responde com o **Controlador Temporal** (*Temporal Controller*): liga-se o tempo na camada, aperta-se ▶ e o mapa anima semana a semana. Funciona muito bem, **para quem tem o QGIS instalado e sabe configurá-lo**. O gestor da Defesa Civil, o jornalista ou o secretário de meio ambiente não vão abrir um GeoPackage.

Neste exercício, você faz a análise temporal no QGIS e depois leva o mesmo resultado para uma **página HTML interativa**, publicada de graça no **GitHub Pages**, que qualquer pessoa abre no navegador ou no celular.

```
┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│ 1. QGIS                │ ──> │ 2. PyQGIS              │ ──> │ 3. DASHBOARD WEB       │
│ • propriedades         │     │ • liga o tempo e o     │     │ • mapa animado, com 4  │
│   temporais            │     │   Controlador Temporal │     │   visualizações        │
│ • Controlador Temporal │     │ • limpa os -999        │     │ • gráficos e filtros   │
│ • animação semanal     │     │ • exporta os GeoJSON   │     │ • GitHub Pages         │
└────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

**Ao final deste exercício, você será capaz de:**

1. configurar as **propriedades temporais** de uma camada e animar o mapa com o **Controlador Temporal**;
2. fazer o mesmo com **PyQGIS**, sem cliques;
3. **limpar e exportar** dados para a web: valores sentinela (`-999`), fuso horário (UTC × horário local) e tamanho do arquivo;
4. montar um **dashboard** com mapa animado, quatro visualizações cartográficas (agrupamentos, densidade, intensidade e coroplético), gráficos ligados entre si e filtros;
5. **revisar** o painel com a IA como um leitor faria: hierarquia cartográfica, clareza sobre o que está sendo mostrado, acessibilidade e falhas de rede;
6. **publicar** o dashboard no GitHub Pages e **conferir** que ele mostra os mesmos números do QGIS.

### O que deve ser entregue

1. O projeto do QGIS com a camada de focos animada pelo Controlador Temporal.
2. `queimadas_pb_2026.geojson`, `municipios_pb.geojson` e `limite_pb.geojson`, gerados pelo script [`queimadas_pb.py`](queimadas_pb.py).
3. O dashboard ([`docs/queimadas_pb/`](../../docs/queimadas_pb/)) rodando localmente e publicado no GitHub Pages.
4. A tabela de conferência da seção 6: focos por mês no QGIS × no dashboard.

---

## 1. Fundamentação: o que é um foco de queimada

### 1.1 Foco de calor não é área queimada

O **Programa Queimadas** do INPE processa imagens de vários satélites e marca um **foco** em cada pixel com temperatura bem acima da vizinhança. Um foco é um **indício de fogo** num pixel de ~375 m (sensor VIIRS), não o contorno da área queimada.

```
   um incêndio grande          →   vários focos vizinhos, na mesma passagem
   uma queimada pequena        →   um foco, ou nenhum
   fogo entre duas passagens   →   nenhum foco
   fogo sob nuvens             →   nenhum foco
```

> ⚠️ **Contagem de focos é uma amostra.** Os números servem para comparar **períodos e lugares** com o mesmo satélite, não para dizer "quantos incêndios houve".

### 1.2 O satélite de referência

Vários satélites detectam o mesmo fogo, e somar todos contaria o mesmo incêndio várias vezes. Por isso o INPE usa um **satélite de referência**, cujos dados formam a série comparável ano a ano. Nesta camada, **todos os 2.445 focos são do NOAA-20**: confira no campo `Satelite`.

Um satélite de órbita polar passa sobre o mesmo lugar **duas vezes por dia**. O gráfico *Hora da detecção* do dashboard mostra isso: 9 em cada 10 focos aparecem entre **15h e 16h** (horário da Paraíba), e o restante de madrugada, entre 2h e 4h. Não existe foco às 10h: não é que não haja fogo, é que o satélite não estava lá.

### 1.3 Os outros campos

| Campo | O que é | Cuidado |
| --- | --- | --- |
| `DataHora` | data e hora da passagem do satélite | está em **UTC** (o `Z` no fim); a Paraíba fica em **UTC−3** |
| `Municipio`, `Bioma` | onde o foco caiu | nomes em maiúsculas; 2 biomas: Caatinga e Mata Atlântica |
| `FRP` | *Fire Radiative Power*, potência radiativa do fogo, em **MW** | indica a intensidade; varia de 0,3 a 204,5 MW |
| `RiscoFogo` | risco de fogo calculado pelo INPE, de 0 a 1 | **`-999` ou vazio = sem dado** |
| `DiaSemChuva` | dias seguidos sem chuva até a data | **`-999` ou vazio = sem dado** |
| `Precipitacao` | chuva no dia, em mm | vazio = sem dado |
| `lat`, `lon` | coordenadas, repetidas da geometria | — |

> 💡 **O `-999` é uma armadilha clássica.** Se você calcular a média de `RiscoFogo` sem tirá-lo, o resultado sai negativo. Ele não é um risco; é a forma de o BDQueimadas dizer "não calculado".

---

## 2. Os dados

A camada `bdqueimadas_2026-01-01_2026-10-30` está no `minicurso_dados.gpkg` (veja [`dados_curso/`](../../dados_curso/README.md)): **2.445 pontos** em **EPSG:4326**, de 01/01/2026 a 29/10/2026, em **203** dos 223 municípios da Paraíba.

| | jan | fev | mar | abr | mai | jun | jul | ago | set | out |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **focos** | 572 | 240 | 68 | 10 | 22 | 29 | 64 | 178 | 391 | **871** |

Dois picos: **janeiro**, no fim da estação seca do Sertão, e **setembro a outubro**, quando a seca volta e a cana-de-açúcar é colhida na Zona da Mata. Entre abril e junho, no período chuvoso, quase não há focos.

Para o mapa coroplético e os contornos do dashboard, o script usa também as camadas `municipios` (223 polígonos) e `limite_pb` do mesmo GeoPackage.

---

## 3. Parte A — o Controlador Temporal, à mão

### 3.1 Ligar o tempo na camada

1. Arraste a camada `bdqueimadas_2026-01-01_2026-10-30` para o mapa.
2. **Propriedades da camada → Temporal** (*Temporal*): marque **Temporal dinâmico** (*Dynamic Temporal Control*).
3. **Configuração**: **Campo único com data/hora** (*Single Field with Date/Time*); **Campo**: `DataHora`.
4. Deixe **Duração do evento** (*Event duration*) em 0 e **Acumular feições** (*Accumulate features over time*) desmarcado.

Um relógio aparece ao lado do nome da camada: ela agora responde ao tempo.

### 3.2 Animar

1. **Exibir → Painéis → Controlador Temporal** (ou o ícone de relógio na barra de navegação).
2. Clique em ▶ **Navegação animada** (*Animated temporal navigation*).
3. **Intervalo**: clique em ↻ (*Set to full range*) para usar o primeiro e o último foco.
4. **Passo**: `1 semana`. Aperte ▶.
5. Nas opções (⚙), marque **Intervalo cumulativo** (*Cumulative range*) para os focos irem se acumulando desde janeiro.

> 💡 **Para mostrar a data no mapa:** *Exibir → Decorações → Rótulo de título*, com o texto `[% format_date(@map_start_time, 'dd/MM/yyyy') %]`. E **Exportar animação** (🎞 no painel) grava um PNG por quadro, que vira GIF ou vídeo.

### 3.3 O limite do Controlador Temporal

Ele resolve a análise, mas pense em quem precisa **ver** o resultado:

| Para ver a animação, a pessoa precisa… | No QGIS | No dashboard web |
| --- | :---: | :---: |
| instalar um programa | ✅ QGIS (~1 GB) | ❌ só o navegador |
| receber os dados | ✅ GeoPackage de 548 MB | ❌ já estão na página (~900 KB) |
| saber configurar propriedades temporais | ✅ | ❌ |
| abrir no celular | ❌ | ✅ |
| ver gráficos ligados ao mapa | ❌ (precisa montar à parte) | ✅ |
| achar um município | ❌ (expressão ou seleção) | ✅ digitando o nome |

O QGIS é a **ferramenta de análise**; a página web é a **ferramenta de comunicação**. Este exercício usa as duas.

---

## 4. Parte B — automação com PyQGIS e IA

### 4.1 O prompt

```text
Atue como especialista em PyQGIS. Escreva um script para o Console Python do
QGIS 3.44 que:

1. Abra a camada 'bdqueimadas_2026-01-01_2026-10-30' do GeoPackage
   'minicurso_dados.gpkg' (pontos em EPSG:4326; campos DataHora (DateTime,
   UTC), Satelite, Municipio, Bioma, DiaSemChuva, Precipitacao, RiscoFogo,
   FRP) e confira se os campos existem.
2. Ligue as propriedades temporais da camada: um instante por feição, a
   partir do campo DataHora.
3. Configure o Controlador Temporal do mapa (iface.mapCanvas()
   .temporalController()): navegação animada, do primeiro ao último foco,
   passo de 1 semana, 4 quadros por segundo.
4. Trate -999 e valores vazios como "sem dado" (None) e imprima um resumo:
   focos por mês no horário da Paraíba (UTC-3), os 5 municípios com mais
   focos, a proporção por bioma e os satélites presentes.
5. Exporte um GeoJSON compacto para um dashboard web: coordenadas com 5
   casas decimais, data em ISO 8601 UTC, campos em minúsculas, sem os -999,
   e um bloco "metadados" com fonte, satélite e período. Só entram os focos
   de 2026 no horário da Paraíba; informe quantos ficaram de fora.
6. Exporte também as camadas 'municipios' (campo 'nome') e 'limite_pb',
   simplificadas com tolerância de 0,001° e coordenadas com 4 casas, para o
   mapa coroplético. Grave em cada município o nome em maiúsculas, para casar
   com o campo Municipio dos focos.
Se o script rodar fora do QGIS (sem iface), pule os passos 2 e 3.
Comentários em português.
```

### 4.2 A lógica do script (`queimadas_pb.py`)

A versão revisada é [`queimadas_pb.py`](queimadas_pb.py). Os trechos centrais:

**Ligar o tempo na camada** (o mesmo que a seção 3.1):

```python
tp = lyr.temporalProperties()
tp.setIsActive(True)
tp.setMode(Qgis.VectorTemporalMode.FeatureDateTimeInstantFromField)
tp.setStartField("DataHora")
```

**Configurar o Controlador Temporal** (o mesmo que a seção 3.2):

```python
nav = iface.mapCanvas().temporalController()
nav.setNavigationMode(Qgis.TemporalNavigationMode.Animated)
nav.setTemporalExtents(QgsDateTimeRange(inicio, fim))
nav.setFrameDuration(QgsInterval(1, Qgis.TemporalUnit.Weeks))
nav.setTemporalRangeCumulative(False)  # True = acumula desde o início
```

**Limpar o `-999`.** Um valor só entra se existir e não for o sentinela:

```python
def valor(f, campo):
    v = f[campo]
    if v is None or v == SEM_DADO or str(v) == "NULL":
        return None
    return v
```

**Só os focos do ano.** Antes de exportar, o script descarta os focos fora de `ANO = 2026`, contados no horário da Paraíba, e informa quantos eram. Nesta camada são zero, mas um novo download do BDQueimadas pode trazer a virada do ano.

**Exportar para a web.** O GeoPackage tem 548 MB porque guarda todas as camadas do curso; o dashboard só precisa dos focos e dos limites. Com coordenadas em 5 casas decimais (~1 m) e só os campos usados, os focos ficam com **~585 KB**. Os 223 municípios, simplificados com tolerância de 0,001° (~110 m), ficam com **~285 KB**, contra 13 MB sem simplificar:

```python
geometria = json.loads(f.geometry().simplify(TOLERANCIA).asJson(4))
props = {"municipio": f["nome"].upper(), "nome": f["nome"]}  # 'Cajazeiras' → 'CAJAZEIRAS'
```

> **Nota: o que conferir no código**
>
> | Trecho | Por que é assim |
> | --- | --- |
> | `toPyDateTime().replace(tzinfo=timezone.utc)` | o QGIS lê a data sem fuso; sem isso, o Python a trataria como hora local do seu computador |
> | resumo por mês com `astimezone(FUSO_PB)` | um foco às 01h UTC de 1º de outubro teria acontecido em 30 de setembro, na Paraíba |
> | `.upper()` no nome do município | os focos trazem `CAJAZEIRAS`; a camada `municipios`, `Cajazeiras`. Os 203 nomes casam assim |
> | `ensure_ascii=False` | mantém `CAJAZEIRINHAS`, `SÃO JOSÉ DE PRINCESA` e `Mata Atlântica` legíveis no arquivo |
> | `try: from qgis.utils import iface` | o mesmo script roda no Console (com mapa) e fora dele (só exporta) |

### 4.3 Rodar o script

Abra `queimadas_pb.py` no **Editor do Console Python** do QGIS, ajuste `GPKG` e `PASTA_DASHBOARD` (a pasta `docs/queimadas_pb/` do seu clone do repositório) e clique em **Executar script**. Saída esperada:

```text
[1] 2445 focos lidos, SRC EPSG:4326
[2] Temporal ligado na camada: instante = campo 'DataHora'
[3] Controlador Temporal: 44 quadros de 1 semana; aperte ▶ no painel
[4] Focos fora de 2026 descartados: 0
      sem dado (vazio ou -999): DiaSemChuva 503, RiscoFogo 409, Precipitacao 355
      focos por mês (horário da Paraíba):
      jan 572  fev 240  mar 68  abr 10  mai 22  jun 29  jul 64  ago 178  set 391  out 871
      203 municípios com focos; os 5 primeiros:
        CAJAZEIRAS                155
        SANTA RITA                 86
        SOUSA                      82
        LAGOA                      62
        MONTEIRO                   47
      Mata Atlântica 385 (16%)  Caatinga 2060 (84%)
      satélite(s): NOAA-20
[5] 2445 focos em …/docs/queimadas_pb/queimadas_pb_2026.geojson (584 KB)
[6] 223 feições de 'municipios' em municipios_pb.geojson (284 KB)
[6] 1 feições de 'limite_pb' em limite_pb.geojson (34 KB)
```

---

## 5. Parte C — o dashboard web

### 5.1 As peças

O dashboard é uma página estática, com cinco arquivos em [`docs/queimadas_pb/`](../../docs/queimadas_pb/): `index.html` (a estrutura), `app.js` (a lógica) e os três GeoJSON. Não há servidor nem banco de dados: as bibliotecas vêm de uma CDN.

A página, de cima para baixo:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Focos de queimadas em 2026 · satélite, período, total               │
├─────────────────────────────────────────────────────────────────────┤
│ Município [busca ▾]  Bioma [Todos|Caatinga|Mata Atl.]  etiquetas ✕  │
├─────────────────────────────────────────────────────────────────────┤
│ Focos │ Municípios │ Dia com mais focos │ Maior FRP │ Na Caatinga   │
├───────────────────────────────────────────────┬─────────────────────┤
│ ◷ Outubro de 2026 · só este mês               │ Os 15 municípios    │
│ [Agrupados|Densidade|Intensidade|Municípios]  │ com mais focos      │
│ ┌───────────────────────────────────────────┐ │ ▇▇▇▇▇▇▇▇ 96         │
│ │ + ⌂ −                          mapa       │ │ ▇▇▇▇▇ 58            │
│ └───────────────────────────────────────────┘ │ …                   │
│ ◀ ▶ ▶▶  outubro de 2026  ──────●──  1.5fps    │ ▸ Ver todos (146)   │
│ Passo [Dia|Semana|Mês]  [Só o passo|Acumulado]│                     │
│ legenda da visualização                       │                     │
├───────────────────────────────────────────────┴─────────────────────┤
│ Focos por mês (colunas escuras = o que o mapa mostra)               │
├──────────────────────┬──────────────────────┬───────────────────────┤
│ Focos por bioma      │ Hora da detecção     │ Focos mais intensos   │
├──────────────────────┴──────────────────────┴───────────────────────┤
│ Fonte, cobertura, data de geração e links para os dados             │
└─────────────────────────────────────────────────────────────────────┘
```

O painel abre em **outubro de 2026, passo mês, só o mês atual**, na visualização **Agrupados**.

| Biblioteca | Papel no dashboard |
| --- | --- |
| **Leaflet 1.9** | o mapa: mapas base, zoom, popups, contornos e coroplético (`L.geoJSON`) |
| **Leaflet.TimeDimension** | o "Controlador Temporal" da web: ▶, ⏸, avançar, voltar, velocidade e barra de tempo |
| **Leaflet.heat** | o mapa de calor (densidade de focos) |
| **Leaflet.markercluster** | agrupa os focos próximos num círculo com a contagem; abre ao dar zoom |
| **Tom Select** | a busca de município: filtra a lista enquanto se digita, sem diferenciar acentos ("sao jose" encontra "SÃO JOSÉ DE PIRANHAS") |
| **Vue.js 3** | guarda o estado (filtros, visualização, passo, modo, instante) e atualiza tudo quando ele muda |
| **Highcharts** | os gráficos: série temporal, municípios, bioma e hora da detecção |
| **Tailwind CSS** | o visual, com classes direto no HTML |

> **Por que Vue e não jQuery?** Com jQuery, cada filtro precisaria de código para atualizar à mão o mapa, os 4 gráficos, os 5 indicadores, a tabela e as etiquetas, e é fácil esquecer um. No Vue, você declara *o que* cada parte mostra a partir do estado (`computed`), e ele refaz só o que mudou. Com 6 valores de estado que se combinam, essa é a diferença entre um painel consistente e um cheio de bugs.

> ⚠️ **Leaflet 1.9, não 2.0.** Os três plugins foram escritos para o Leaflet 1.x. A série 2.0 mudou a API e os quebra.

### 5.2 Uma representação de cada vez

A primeira versão deste painel ligava o mapa de calor e os agrupamentos ao mesmo tempo, com os pontos coloridos pela FRP e as duas legendas juntas. Começava ainda no modo acumulado, com os dez meses sobrepostos. O mapa ficou poluído: três representações disputando a atenção e nenhuma hierarquia.

A regra cartográfica é simples: **cada pergunta, uma representação**. O mapa tem quatro visualizações, escolhidas num controle acima dele, e só uma fica ligada:

| Visualização | Responde | Representação | Plugin |
| --- | --- | --- | --- |
| **Agrupados** (padrão) | onde estão os focos? | círculos com a contagem, em 4 faixas (1–9, 10–49, 50–99, 100+) | Leaflet.markercluster |
| **Densidade** | onde eles se concentram? | mapa de calor, sem marcadores por cima | Leaflet.heat |
| **Intensidade (FRP)** | quais fogos são mais fortes? | um círculo por foco; cor **e** tamanho pela FRP, os mais fortes por cima | Leaflet |
| **Municípios** | qual município teve mais focos? | coroplético em 5 classes (0, 1–5, 6–20, 21–50, mais de 50) | Leaflet (`L.geoJSON`) |

A legenda, abaixo do mapa, muda com a visualização. Entre os botões + e − do zoom, um botão 🏠 (*zoom to home*) volta à Paraíba inteira; são poucas linhas com `L.DomUtil`, sem plugin, porque o Leaflet.zoomhome exige o Font Awesome. O limite do estado aparece sempre; os limites municipais, só a partir do zoom 9, em cinza claro, para não competir com os dados.

```javascript
function trocarVisual() {
  for (const nome of ["agrupados", "densidade", "intensidade", "municipios"]) {
    if (nome === visual.value) camadas[nome].addTo(mapa);
    else camadas[nome].remove();
  }
  mostrarContornos();
  atualizarMapa();
}
```

Por que abrir em **só o mês atual**? O acumulado continua disponível, mas não como ponto de partida: sobrepor um foco de janeiro e um de outubro no mesmo lugar sugere um fogo contínuo que não existiu.

### 5.3 Um estado, várias vistas

Todo o dashboard deriva de seis valores:

```
   município ──┐
   bioma ──────┤                    ┌──> mapa (a visualização escolhida)
   visualização┤                    ├──> indicadores e tabela
   passo ──────┼──> focos filtrados ┼──> gráficos de municípios e de bioma
   modo ───────┤                    └──> faixa destacada na série temporal
   instante ───┘
```

**O instante vem do TimeDimension.** A lista de instantes é o início de cada passo (dia, semana ou mês, à meia-noite da Paraíba). A cada quadro, o plugin dispara `timeload`, o Vue recebe o novo instante e o resto se atualiza sozinho. O controle do plugin nasce no mapa e é levado para uma faixa abaixo dele, junto do passo, do modo e da legenda, para não cobrir os dados:

```javascript
dimensao = new L.TimeDimension({ times: instantes, currentTime: tempo.value });
dimensao.on("timeload", (e) => { tempo.value = e.time; });
tempoEl.value.appendChild(controle.getContainer());
```

> ⚠️ **A primeira semana do ano começa em 2025.** As semanas vão de segunda a domingo, e 1º de janeiro de 2026 caiu numa quinta: sem cuidado, o primeiro passo seria "29/12/2025 a 04/01/2026", e o painel pareceria ter focos do ano passado. A função `inicioDoPasso()` corta qualquer passo em 1º de janeiro.

**A janela de tempo** depende do modo: *só o passo atual* (a semana do quadro) ou *acumulado* (de janeiro até o fim do quadro), o mesmo que a opção **Intervalo cumulativo** do QGIS.

```javascript
const janela = computed(() => ({
  inicio: modo.value === "acumulado" ? limites.value.inicio : tempo.value,
  fim: proximoPasso(tempo.value, passo.value),
}));
```

**Só a visualização ligada é atualizada** a cada quadro. Os marcadores dos agrupamentos são criados uma vez só e reaproveitados:

```javascript
if (visual.value === "agrupados") {
  camadas.agrupados.clearLayers();
  camadas.agrupados.addLayers(s.map(marcadorCluster));          // Leaflet.markercluster
} else if (visual.value === "densidade") {
  camadas.densidade.setLatLngs(s.map((f) => [f.lat, f.lon, 1])); // Leaflet.heat
}
```

**Gráficos ligados entre si.** Clicar numa barra de município filtra o painel inteiro; clicar numa coluna da série temporal leva a animação até aquele período. O gráfico de municípios **ignora o próprio filtro** e destaca o escolhido: assim você vê o município no meio dos outros, em vez de uma barra solitária. O coroplético faz o mesmo: clicar num município filtra o painel, contorna o município em preto e aproxima o mapa.

**Componentes de fora do Vue precisam de ponte nos dois sentidos.** O município pode mudar por quatro caminhos: a busca, uma barra do gráfico, o coroplético ou a etiqueta ✕. A busca do Tom Select avisa o Vue quando o usuário escolhe; o Vue avisa a busca quando o filtro muda por outro caminho. O `true` em `setValue` evita um vai e volta infinito:

```javascript
onChange: (valor) => { municipio.value = valor || ""; },           // Tom Select → Vue
watch(municipio, (valor) => {                                       // Vue → Tom Select
  if (buscaMunicipio.getValue() !== valor) buscaMunicipio.setValue(valor, true);
});
```

O TimeDimension segue a mesma ideia: `timeload` leva o instante para o Vue, e `setCurrentTime` (no clique da série temporal) o traz de volta.

### 5.4 Deixar claro o que está sendo mostrado

Um painel com filtros, animação e quatro visualizações gera dúvidas: *que período é este? quais filtros estão valendo? por que o gráfico de biomas ainda mostra os dois biomas?* As revisões do painel (seção 5.8) trataram disso:

| Dúvida ou barreira | O que o painel faz |
| --- | --- |
| que período o mapa mostra? | etiqueta junto ao título do mapa: "Outubro de 2026 · só este mês", "Acumulado de 01/01 a 31/08/2026"; na série temporal, as colunas desse período ficam escuras, com legenda |
| 203 municípios num `<select>` | busca com autocomplete (Tom Select): filtra enquanto se digita, ignora acentos e mostra o total de focos de cada município |
| como voltar ao estado inteiro? | botão 🏠 entre o + e o − do zoom |
| quais filtros estão valendo? | etiquetas removíveis ("Município: SANTA RITA ✕"), uma linha "Indicadores da seleção: …" e uma nota dizendo o que cada filtro afeta |
| de onde vem cada indicador? | o detalhe de cada cartão diz o denominador ("709 de 871 focos selecionados") ou "sem focos na seleção" |
| só 15 municípios no gráfico | o título diz "Os 15 municípios…"; "Ver todos" abre a lista completa, com um botão por município |
| teclado e leitor de tela | `aria-pressed` nos botões de opção, grupos com rótulo, a tabela com um botão por linha, nomes nos botões do TimeDimension |
| dados ou mapa base fora do ar | estado de carregamento por arquivo; erro dizendo **qual** arquivo falhou e **por quê** (404, `file://`, JSON inválido), com "Tentar novamente"; aviso quando o mapa base não carrega, enquanto os focos continuam no mapa; aviso quando uma biblioteca da CDN não carrega |
| celular | mapa mais baixo, indicadores numa faixa rolável, visualizações em 2 × 2, barra de tempo em linhas, alvos de toque de 36 px |

### 5.5 Rodar localmente

O navegador **não deixa** uma página aberta direto do disco (`file://`) ler o GeoJSON com `fetch`. Sirva a pasta `docs/`:

```bash
cd docs
python -m http.server 8000
```

e abra `http://localhost:8000/queimadas_pb/`.

> ⚠️ **Gerou os GeoJSON de novo e nada mudou?** O navegador guarda os arquivos em cache. Recarregue ignorando o cache: **Ctrl+Shift+R** (Windows/Linux) ou **Cmd+Shift+R** (macOS).

### 5.6 Publicar no GitHub Pages

1. Faça *commit* e *push* da pasta `docs/` para a branch `main` do seu repositório.
2. No GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**; **Branch: `main`**, pasta **`/docs`**; **Save**.
3. Em um ou dois minutos, o painel estará em `https://<seu-usuario>.github.io/<repositorio>/queimadas_pb/`.

O arquivo vazio `docs/.nojekyll` diz ao GitHub para servir os arquivos como estão, sem passar pelo Jekyll.

> ⚠️ **Tudo em `docs/` fica público**, mesmo o que a página não usa. Antes do *push*, confira com `git status` se não entrou nenhum arquivo de trabalho (um `.zip`, um rascunho, uma planilha).

### 5.7 O prompt do dashboard

```text
Crie um dashboard em uma página estática (index.html + app.js) para os focos
de queimadas da Paraíba em 2026, a partir do GeoJSON 'queimadas_pb_2026.geojson'
(pontos; propriedades data_hora em ISO UTC, municipio, bioma, frp, risco_fogo,
dias_sem_chuva, precipitacao; bloco "metadados" com fonte e satélite), de
'municipios_pb.geojson' (polígonos; municipio em maiúsculas, nome) e de
'limite_pb.geojson' (contorno do estado).
Bibliotecas por CDN: Leaflet 1.9.4, Leaflet.TimeDimension 1.1.1 (com
iso8601-js-period), Leaflet.heat, Leaflet.markercluster, Tom Select 2,
Vue 3 (build global), Highcharts 12 e Tailwind CSS 4 (browser).
- Filtros acima: município (busca com Tom Select, sem diferenciar acentos,
  com o total de focos de cada um) e bioma.
- Botão "zoom to home" entre o + e o − do zoom, de volta ao estado inteiro.
- Mapa com quatro visualizações exclusivas, num controle segmentado acima
  dele: agrupados (markercluster, 4 faixas de contagem), densidade (heat),
  intensidade (um círculo por foco, cor e tamanho pela FRP) e municípios
  (coroplético em 5 classes). Legenda abaixo do mapa, conforme a
  visualização. Limite do estado sempre; limites municipais só a partir do
  zoom 9. Botão de tela cheia. Popup em forma de cartão, com a FRP em destaque.
- O TimeDimension controla o instante; os passos começam à meia-noite de
  UTC-3 e nunca antes de 1º de janeiro. Leve o controle para uma faixa abaixo
  do mapa, com o passo (dia/semana/mês) e o modo (só o passo atual ×
  acumulado). Comece em outubro, passo mês, só o passo atual. A cada
  'timeload', o mapa, os indicadores e os gráficos se atualizam.
- Junto ao título do mapa, uma etiqueta com o período e o modo ("Outubro de
  2026 · só este mês"). Filtros ativos como etiquetas removíveis.
- Indicadores: focos, municípios atingidos, dia com mais focos, maior FRP,
  % na Caatinga; cada um diz a que se refere ("709 de 871 focos
  selecionados") ou "sem focos na seleção".
- Gráficos: focos por passo com a janela atual destacada (clique leva até o
  período), top 15 municípios e focos por bioma (clique filtra), hora da
  detecção em UTC-3. Tabela com os 10 maiores FRP (clique abre o foco no mapa).
- Estado de carregamento por arquivo; em caso de erro, diga qual arquivo
  falhou e por quê, com "Tentar novamente". Avise se o mapa base não carregar.
- Acessibilidade: aria-pressed nos botões de opção, rótulos nos grupos,
  tabela operável pelo teclado. No celular: mapa mais baixo, indicadores em
  faixa rolável, controles que quebram linha.
- Textos em português; datas no fuso America/Fortaleza.
```

> 💡 Este prompt é o **resultado** das revisões da seção 5.8, não o ponto de partida. Ninguém escreve um prompt assim de primeira: ele cresce a cada rodada em que você olha o painel e encontra o que não funciona.

### 5.8 Como o painel chegou aqui: quatro rodadas de revisão

| Rodada | O que estava errado | O que mudou |
| --- | --- | --- |
| **1. Primeira versão** | funcionava, com números certos, mas o mapa ficou **poluído**: calor, agrupamentos e cores de FRP ligados ao mesmo tempo, duas legendas, abrindo no acumulado de dez meses | — |
| **2. Revisão cartográfica** | não havia hierarquia visual | uma visualização por vez, legenda que muda com ela, abrir no mês atual, agrupamentos em 4 faixas, contornos discretos, coroplético por município, controle de tempo abaixo do mapa, popups em cartão |
| **3. Revisão de uso** | o leitor não sabia que período via, nem o que cada filtro afetava; teclado, erros de rede e celular esquecidos | etiqueta do período, filtros ativos removíveis, indicadores com contexto, `aria-pressed`, estados de carregamento e erro, layout de celular; correção do ✕ do popup |
| **4. Detalhes** | 203 municípios numa lista; sem atalho para voltar ao estado | busca com autocomplete e botão 🏠 |

Em todas as rodadas, a IA escreveu o código **e** sugeriu melhorias, mas quem decidiu o que adotar, e quem conferiu no navegador se ficou certo, foi uma pessoa. Duas sugestões foram recusadas com justificativa: uma grade hexagonal H3 (virou o desafio 2) e um botão "minha localização", sem uso para esta análise.

---

## 6. Validação: o dashboard mostra o mesmo que o QGIS?

Uma página bonita com números errados é pior que nenhuma página. Confira três números por três caminhos.

**1. No QGIS**, com a expressão no *Selecionar por expressão* (o `- 3 hours` passa de UTC para o horário da Paraíba):

```text
month("DataHora" - make_interval(hours:=3)) = 10
```

**2. No script**, a linha `focos por mês` da saída.

**3. No dashboard**, o painel já abre em outubro (passo **Mês**, **Só o passo atual**): leia o cartão **Focos**. Para setembro, aperte ◀ uma vez. Para Cajazeiras, digite "cajaz" na busca de município, escolha **Acumulado** e confira que a animação está no último passo, outubro: a etiqueta do mapa passa a dizer "Período todo".

| Conferência | QGIS | Script | Dashboard |
| --- | :---: | :---: | :---: |
| focos em outubro | 871 | 871 | 871 |
| focos em setembro | 391 | 391 | 391 |
| focos em Cajazeiras (período todo) | 155 | 155 | 155 |

> 💡 **O fuso importa?** Tire o `- 3 hours` e conte de novo: dá o mesmo 871. As passagens do satélite acontecem entre 5h e 7h e entre 18h e 20h UTC, e nenhuma cruza a meia-noite ao voltar 3 horas. Mas a **hora** muda: sem o ajuste, o pico de detecções iria para as 18h–19h, horário em que o satélite não está sobre a Paraíba. Com outro satélite ou com dados horários, também o dia e o mês podem mudar: ajuste sempre.

### Armadilhas comuns

| Erro comum (seu ou da IA) | Sintoma | Causa | Solução |
| :--- | :--- | :--- | :--- |
| **Ignorar o `-999`** | média de risco de fogo negativa | o sentinela entra na conta | tratar `-999` como "sem dado" antes de exportar |
| **Ignorar o fuso** | pico de detecções às 18h–19h; com outros dados, focos no dia errado | `DataHora` está em UTC | agrupar e mostrar em UTC−3 (`America/Fortaleza`) |
| **Abrir o HTML direto do disco** | página sem dados; erro de CORS no console | `fetch` bloqueado em `file://` | `python -m http.server` ou GitHub Pages |
| **Usar o Leaflet 2.0** | erros no console, controles quebrados | os plugins são da série 1.x | fixar `leaflet@1.9.4` |
| **Mapa base que pede chave** | mosaicos com a marca "API key required" | alguns provedores (ex.: CARTO) exigem chave fora do domínio autorizado | usar mapas base sem chave (OSM, Esri) ou cadastrar a chave |
| **Recriar os marcadores a cada quadro** | animação travando | 2.445 objetos novos por quadro | criar uma vez e reaproveitar |
| **Ligar todas as representações juntas** | mapa poluído, duas legendas, nada se lê | calor, agrupamentos e cores de FRP ao mesmo tempo | uma visualização por vez, com a legenda dela |
| **Começar no acumulado** | dez meses de focos sobrepostos | o padrão era "acumulado até o fim" | abrir no último mês, só o passo atual |
| **Zerar o `padding` do popup do Leaflet** | o botão ✕ fica fora da caixa | sem o `padding`, a margem do conteúdo "vaza" do invólucro (colapso de margens do CSS) e a caixa desce | manter o `padding` do `.leaflet-popup-content-wrapper` e dar espaço à direita para o ✕ |
| **Componente de fora do Vue sem ponte** | a busca mostra um município e o painel filtra outro | o filtro mudou por outro caminho (barra, mapa, etiqueta) e ninguém avisou o Tom Select | sincronizar nos dois sentidos: `onChange` → Vue e `watch` → `setValue(valor, true)` |
| **Cache do navegador** | GeoJSON novo, painel com os números antigos | o navegador reaproveitou o arquivo baixado antes | recarregar ignorando o cache (Ctrl/Cmd+Shift+R) |
| **Semanas de segunda a domingo** | 1ª semana "29/12/2025 a 04/01/2026" | 1º de janeiro de 2026 foi numa quinta | cortar os passos em 1º de janeiro |

> **Licenças.** Leaflet, plugins, Vue e Tailwind são livres (MIT/BSD); o Tom Select, também (Apache 2.0). O **Highcharts** é gratuito para uso **pessoal, educacional e sem fins lucrativos**; para uso comercial, exige licença (alternativas livres: Apache ECharts, Chart.js). O mapa base OpenStreetMap segue a [política de uso dos mosaicos](https://operations.osmfoundation.org/policies/tiles/).

---

## 7. Desafios

1. **Vídeo no QGIS.** Use **Exportar animação** do Controlador Temporal, com o rótulo de data da seção 3.2, e transforme os quadros num GIF. Compare o esforço com o de mandar o link do dashboard.
2. **Grade hexagonal.** O coroplético depende do tamanho de cada município. Gere no QGIS uma grade de hexágonos de 10 km (*Criar grade*, num SRC métrico), conte os focos em cada um (*Contar pontos em polígono*) e acrescente ao dashboard uma quinta visualização. O padrão espacial muda?
3. **Focos por 1.000 km².** Cajazeiras lidera em número de focos, mas é também um município grande? Calcule a área de cada município num SRC métrico (ver [`dados_curso/`](../../dados_curso/README.md)), grave-a em `municipios_pb.geojson` e faça o coroplético por densidade. O ranking muda?
4. **Atualização automática.** O BDQueimadas permite baixar novos períodos. Como você atualizaria o dashboard toda semana sem abrir o QGIS? Dica: o script já roda fora da interface; pesquise *GitHub Actions*.
5. **Só com o teclado.** Use o painel sem o mouse: Tab, Enter, Espaço e setas. Consegue filtrar um município, trocar a visualização, animar o tempo e abrir um foco da tabela no mapa? Anote onde travou e peça à IA a correção.
6. **Sem internet na sala.** Se a CDN cair, o painel avisa, mas não funciona. Baixe as bibliotecas para uma pasta `docs/queimadas_pb/vendor/`, troque os endereços no `index.html` e teste com o Wi-Fi desligado. O que continua dependendo da internet? (Dica: o mapa base.)

---

## 8. Para levar

> 💡 **O QGIS é onde a análise acontece; a web é onde ela é vista.** O Controlador Temporal e o dashboard mostram os mesmos 2.445 focos, mas um exige que o leitor saiba GIS e o outro só exige um link. Em qualquer dos dois, os cuidados são os mesmos: tirar o `-999`, respeitar o fuso e **conferir os números antes de publicar**. E, na web, um cuidado a mais: o leitor não tem você do lado para explicar; o painel tem de dizer sozinho o que está mostrando.
