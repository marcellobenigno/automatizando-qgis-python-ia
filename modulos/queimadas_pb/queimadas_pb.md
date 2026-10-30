<!-- navegação -->
[⬅️ 🚶 Alcance a partir do IFPB](../alcance_ifpb/alcance_ifpb.md) · [🏠 Início](../../README.md)

# Do QGIS ao WebGIS: explorando os focos de queimadas na Paraíba

> **Roteiro de aula:** prático, guiado e com aprofundamento técnico
> **Público:** estudantes de geotecnologias, meio ambiente e ciências da terra · **Nível:** 🔴 Avançado
> **Duração:** 35 minutos de aula prática (seções 1 a 5) + aprofundamento técnico para estudo posterior (seções 6 e 7)
> **Tema:** análise temporal de focos de calor e comunicação de dados cartográficos na web
> **Tecnologias:** QGIS 3.44 e PyQGIS; Leaflet (TimeDimension, heat, markercluster), Vue.js 3, Tom Select, Highcharts e Tailwind CSS; GitHub Pages; IA generativa
> **Dashboard publicado:** 🌐 [marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/](https://marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/)

---

## 🧭 1. A proposta da aula

Nesta aula, investigamos **quando e onde o satélite registrou focos de calor na Paraíba em 2026** e comparamos duas formas de apresentar esses dados:

1. **No QGIS**, com uma animação feita no **Controlador Temporal** (*Temporal Controller*).
2. **No WebGIS**, com um **dashboard** que qualquer pessoa abre no navegador ou no celular.

A pergunta que guia a atividade:

> **Como o padrão espacial dos focos muda ao longo do ano, e como comunicar essa dinâmica com clareza para quem não trabalha com SIG?**

O QGIS responde à primeira metade muito bem, **para quem tem o QGIS instalado e sabe configurá-lo**. O gestor da Defesa Civil, o jornalista ou o secretário de meio ambiente não vão abrir um GeoPackage. A segunda metade da pergunta é a razão de existir do dashboard.

### 🎯 Objetivos de aprendizagem

Ao final da aula, a turma será capaz de:

1. **diferenciar** um *foco de calor* de uma *área queimada*;
2. **configurar e executar** a animação temporal de uma camada vetorial no QGIS;
3. **navegar e interpretar** quatro representações cartográficas num WebGIS: agrupamento, densidade, intensidade e coroplético;
4. **reconhecer e tratar** duas armadilhas comuns em dados ambientais: o fuso horário (UTC × horário local) e o valor sentinela `-999`;
5. **validar** que o dashboard mostra os mesmos números calculados no QGIS.

---

## 📋 2. Preparação e roteiro de tempo

### 🛠️ Antes da aula, o(a) professor(a) confere

- [ ] **QGIS** 3.34 LTR ou mais recente (material testado no 3.44) em todos os computadores.
- [ ] **Dados:** o `minicurso_dados.gpkg`, com a camada `bdqueimadas_2026-01-01_2026-10-30`, na pasta `dados_curso/` (veja [`dados_curso/`](../../dados_curso/README.md)).
- [ ] **Dashboard:** abre no [GitHub Pages](https://marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/). Sem internet, rode-o localmente (seção 6.6).
- [ ] **Rede da sala:** carrega os mapas de fundo e as bibliotecas da CDN (`cdn.jsdelivr.net`, `server.arcgisonline.com`). Se a rede bloquear algum desses endereços, o painel avisa o que faltou.

> 💡 **Dica para quem conduz a aula:** montar o dashboard e programar em PyQGIS não cabem em 35 minutos. Use o painel já publicado para a exploração da turma e reserve o código (seção 6) para uma demonstração guiada ou para estudo posterior.

### ⏱️ Planejamento minuto a minuto (35 min)

| Intervalo | Etapa | Foco da turma |
| :--- | :--- | :--- |
| **0–5 min** | Pergunta e contexto | O que é um foco de calor? Os dados da Paraíba em 2026. |
| **5–13 min** | Atividade 1: QGIS | Ligar o tempo na camada e animar os focos semana a semana. |
| **13–25 min** | Atividade 2: WebGIS | Trocar as visualizações do mapa, filtrar um município, mudar o período. |
| **25–32 min** | Atividade 3: validação | Conferir os focos de outubro no QGIS e no dashboard. |
| **32–35 min** | Síntese e fechamento | Check-out oral e reflexão sobre comunicar mapas ao público. |

---

## 💡 3. Fundamentação

### 3.1 Foco de calor **não é** área queimada

O **Programa Queimadas** do INPE processa imagens de satélite e marca um **foco** em cada pixel com temperatura bem acima da vizinhança. Nesta camada, o sensor é o **VIIRS**, a bordo do satélite **NOAA-20**, com pixel de **~375 m**.

```
   incêndio grande e contínuo   ──>  vários focos vizinhos na mesma passagem
   queimada pequena e rápida    ──>  um foco, ou nenhum se acabar entre duas passagens
   fogo sob nuvens espessas     ──>  nenhum foco
   fogo entre duas passagens    ──>  nenhum foco naquele dia
```

> 🗣️ **Como explicar para a turma:**
> *"Pensem no foco de calor como uma foto tirada pelo satélite ao passar lá no alto. Ela mostra que havia uma fonte de calor forte naquele pixel de 375 metros, mas não desenha o contorno do que queimou."*

Por isso, a contagem de focos é uma **amostra comparável**: ótima para comparar meses e regiões com o mesmo satélite, mas não é um inventário de incêndios.

### 3.2 O satélite de referência (NOAA-20)

Vários satélites detectam o mesmo fogo, e somar todos contaria o mesmo incêndio várias vezes. Por isso o INPE usa um **satélite de referência**, que forma a série comparável ano a ano. Os **2.445 focos** desta aula são todos do **NOAA-20** (confira no campo `Satelite`).

Em órbita polar, o satélite passa sobre a Paraíba **duas vezes por dia**. Nos dados, as detecções se concentram em duas janelas (horário da Paraíba):

- **à tarde, entre 15h e 16h:** 9 em cada 10 focos;
- **de madrugada, entre 2h e 4h:** o restante.

> ⚠️ **Atenção:** não há foco às 10h da manhã. Não é que não haja fogo: é que o satélite não estava passando. O gráfico *Hora da detecção* do dashboard mostra isso.

### 3.3 Os campos, o fuso e a armadilha do `-999`

| Campo | O que é | Cuidado |
| :--- | :--- | :--- |
| `DataHora` | instante da passagem do satélite | está em **UTC** (o `Z` no fim); a Paraíba fica em **UTC−3**, então subtraia 3 horas |
| `Municipio` | município do foco | em maiúsculas (`CAJAZEIRAS`) |
| `Bioma` | bioma do foco | na Paraíba: Caatinga (84% dos focos) e Mata Atlântica (16%) |
| `FRP` | *Fire Radiative Power*, potência radiativa do fogo, em **MW** | indica a **intensidade**, não a área queimada; vai de 0,3 a 204,5 MW |
| `RiscoFogo` | risco de fogo calculado pelo INPE, de 0 a 1 | **`-999` ou vazio = sem dado** |
| `DiaSemChuva` | dias seguidos sem chuva | **`-999` ou vazio = sem dado** |
| `Precipitacao` | chuva no dia, em mm | vazio = sem dado |

> 🚨 **O perigo do valor sentinela `-999`:**
> em bases ambientais, `-999` quer dizer "não calculado". Calcule a média de `RiscoFogo` sem tirá-lo e o resultado sai **negativo**. Antes de qualquer estatística, o `-999` vira "sem dado".

### 3.4 A sazonalidade dos focos em 2026

| Mês | jan | fev | mar | abr | mai | jun | jul | ago | set | out |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Focos** | **572** | 240 | 68 | 10 | 22 | 29 | 64 | 178 | 391 | **871** |

A série tem **dois picos** e um vale:

- **pico de janeiro:** fim da estação seca no Sertão;
- **pico de setembro a outubro:** a seca volta ao interior e a cana-de-açúcar é colhida na Zona da Mata;
- **vale de abril a junho:** a quadra chuvosa, quando os focos quase desaparecem.

---

## 🛠️ 4. Trilha prática guiada

### 📍 Atividade 1: a animação temporal no QGIS (8 min)

**Objetivo:** fazer os focos aparecerem no mapa conforme a data.

1. Arraste a camada `bdqueimadas_2026-01-01_2026-10-30` do `minicurso_dados.gpkg` para o mapa.
2. **Propriedades da camada → Temporal:**
   - marque **Temporal dinâmico** (*Dynamic Temporal Control*);
   - **Configuração:** **Campo único com data/hora** (*Single Field with Date/Time*);
   - **Campo:** `DataHora`. Deixe a **Duração do evento** em 0.
   Um relógio aparece ao lado do nome da camada: ela agora responde ao tempo.
3. Abra o **Controlador Temporal** (*Exibir → Painéis → Controlador Temporal*, ou o ícone de relógio).
4. Clique em ▶ **Navegação animada** e em ↻ (*Set to full range*) para usar do primeiro ao último foco.
5. **Passo:** `1 semana`. Aperte ▶ e observe os pontos surgindo.
6. *(Opcional)* Nas opções (⚙), marque **Intervalo cumulativo** para os focos se acumularem desde janeiro.

> 💡 **Para mostrar a data no mapa:** *Exibir → Decorações → Rótulo de título*, com o texto `[% format_date(@map_start_time, 'dd/MM/yyyy') %]`. E **Exportar animação** (🎞 no painel) grava um PNG por quadro, que vira GIF ou vídeo.

> 💬 **Pausa para reflexão com a turma:**
> - *O que acontece com a quantidade de pontos quando a animação passa por abril, maio e junho?*
> - *Para alguém da Defesa Civil ver esta animação, o que precisaria estar instalado no computador dela?*

<details>
<summary>Respostas esperadas</summary>

- Os pontos quase somem: é a quadra chuvosa (10 focos em abril, 22 em maio, 29 em junho).
- O QGIS, os dados (um GeoPackage de 548 MB) e alguém que saiba configurar as propriedades temporais. É exatamente o que o dashboard dispensa:

| Para ver a animação, a pessoa precisa… | No QGIS | No dashboard web |
| --- | :---: | :---: |
| instalar um programa | ✅ QGIS (~1 GB) | ❌ só o navegador |
| receber os dados | ✅ GeoPackage de 548 MB | ❌ já estão na página (~900 KB) |
| saber configurar propriedades temporais | ✅ | ❌ |
| abrir no celular | ❌ | ✅ |
| ver gráficos ligados ao mapa | ❌ (precisa montar à parte) | ✅ |
| achar um município | ❌ (expressão ou seleção) | ✅ digitando o nome |

</details>

---

### 📍 Atividade 2: explorando o WebGIS (12 min)

Abra o [dashboard publicado](https://marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/). Ele segue um princípio cartográfico simples: **uma pergunta, uma representação**. O mapa tem quatro visualizações, e só uma fica ligada de cada vez:

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │  [Agrupados]    responde: onde estão os focos?                         │
  │  [Densidade]    responde: onde eles se concentram?                     │
  │  [Intensidade]  responde: quais fogos são mais fortes (FRP)?           │
  │  [Municípios]   responde: quais municípios tiveram mais focos?         │
  └────────────────────────────────────────────────────────────────────────┘
```

**Roteiro de exploração:**

1. **Leia o período.** A etiqueta ao lado do título do mapa diz o que está na tela: o painel abre em **"Outubro de 2026 · só este mês"**.
2. **Troque as visualizações:**
   - **Agrupados:** círculos com a contagem dos focos próximos; aproxime o mapa para separá-los.
   - **Densidade:** o mapa de calor mostra as manchas de concentração no Sertão e na Zona da Mata.
   - **Intensidade (FRP):** um círculo por foco, com cor e tamanho pela potência do fogo.
   - **Municípios:** o mapa coroplético, com os municípios coloridos em 5 classes de contagem.
3. **Filtre um município.** Digite `cajaz` na busca de **Município** (acentos não importam) e escolha **CAJAZEIRAS**. Os indicadores, os gráficos e o mapa se atualizam juntos; uma etiqueta "Município: CAJAZEIRAS ✕" mostra o filtro ativo. O botão 🏠, entre o + e o − do zoom, volta à Paraíba inteira.
4. **Mude o período.** Na faixa abaixo do mapa, aperte ◀ para ir a setembro, ou ▶ para animar. Na série temporal, as colunas escuras mostram o período que está no mapa.

> 💡 **Por que o painel abre no mês atual, e não no acumulado de dez meses?**
> Sobrepor dez meses de focos polui o mapa e sugere que tudo aconteceu ao mesmo tempo: um foco de janeiro e um de outubro no mesmo lugar parecem um fogo contínuo que não existiu. Começar por um mês ajuda o leitor a entender o padrão antes de ver o todo. O modo **Acumulado** continua a um clique.

> 💬 **Pausa para reflexão:** *em qual das quatro visualizações Cajazeiras se destaca mais? Por que o mesmo município pode parecer mais ou menos importante conforme a representação?*

<details>
<summary>Resposta esperada</summary>

No coroplético e no gráfico de municípios, Cajazeiras lidera em número de focos. Na densidade, o destaque depende de quantos focos estão próximos uns dos outros, não do limite municipal. Na intensidade, o que pesa é a potência de cada fogo. Cada representação responde a uma pergunta diferente; escolher a representação é escolher a pergunta.

</details>

---

### 📍 Atividade 3: validação cruzada (7 min)

Uma página bonita com números errados é pior que nenhuma página. Confira se o dashboard mostra **os mesmos números** que o QGIS.

1. **No QGIS:** *Selecionar por expressão*, com o ajuste do fuso para UTC−3:
   ```text
   month("DataHora" - make_interval(hours:=3)) = 10
   ```
   Resultado esperado: **871 feições selecionadas**.
2. **No dashboard:** o painel já abre em outubro, só o mês atual. Leia o cartão **Focos**: **871**.
3. **Setembro:** troque `10` por `9` na expressão; no dashboard, aperte ◀ uma vez.
4. **Cajazeiras no ano todo:** no QGIS, `"Municipio" = 'CAJAZEIRAS'`; no dashboard, filtre Cajazeiras e escolha **Acumulado** (a etiqueta passa a dizer "Período todo").

| Conferência | QGIS | Script Python | Dashboard | |
| :--- | :---: | :---: | :---: | :---: |
| focos em outubro | 871 | 871 | 871 | ✅ |
| focos em setembro | 391 | 391 | 391 | ✅ |
| focos em Cajazeiras (ano todo) | 155 | 155 | 155 | ✅ |

> 💡 **O fuso importa?** Tire o `- 3 hours` e conte de novo: dá o mesmo 871. As passagens do satélite acontecem entre 5h e 7h e entre 18h e 20h UTC, e nenhuma cruza a meia-noite ao voltar 3 horas. Mas a **hora** muda: sem o ajuste, o pico de detecções iria para as 18h–19h. Com outro satélite ou com dados horários, o dia e o mês também podem mudar: ajuste sempre.

---

## 🎓 5. Fechamento: checagem de aprendizagem

### 💬 Check-out oral

Peça que a turma complete as frases:

1. *"Um foco de calor indica temperatura elevada no pixel, mas **não** significa que…"*
2. *"Para mostrar onde o fogo foi mais forte, a melhor visualização do dashboard é a de…, porque…"*
3. *"Se não ajustarmos o fuso de UTC para UTC−3, o pico de detecções parece acontecer às…"*

<details>
<summary>Respostas esperadas</summary>

1. … aquela área queimou, nem que houve um incêndio por foco: o foco é um pixel quente no instante da passagem.
2. … **Intensidade (FRP)**, porque cor e tamanho de cada círculo seguem a potência radiativa do fogo.
3. … 18h–19h, horário em que o satélite não está sobre a Paraíba.

</details>

### 🏁 Mensagem final

> *"O QGIS é o lugar da análise espacial e do tratamento rigoroso dos dados. O WebGIS é a janela para comunicar esses resultados à sociedade, de forma clara e interativa. Os dois se completam. E, na web, há um cuidado a mais: o leitor não tem você do lado para explicar; o painel tem de dizer sozinho o que está mostrando."*

---

## 💻 6. Aprofundamento técnico: automação e arquitetura

### 6.1 O fluxo dos dados: do GeoPackage ao WebGIS

```
┌────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│ 1. GeoPackage          │ ──> │ 2. Script PyQGIS       │ ──> │ 3. Dashboard WebGIS    │
│ • 2.445 focos          │     │ • liga o tempo e o     │     │ • 3 GeoJSON leves      │
│ • todas as camadas     │     │   Controlador Temporal │     │ • HTML + Vue.js +      │
│   do curso             │     │ • limpa os -999        │     │   Leaflet + Highcharts │
│ • 548 MB               │     │ • simplifica limites   │     │ • GitHub Pages         │
└────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

**Por que não publicar o GeoPackage?** Ele tem **548 MB** porque guarda todas as camadas do curso. O script [`queimadas_pb.py`](queimadas_pb.py) extrai só o que o painel usa:

| Arquivo | Conteúdo | Tamanho |
| --- | --- | ---: |
| `queimadas_pb_2026.geojson` | os 2.445 focos, coordenadas com 5 casas (~1 m), sem os `-999` | ~585 KB |
| `municipios_pb.geojson` | os 223 municípios, simplificados com tolerância de 0,001° (~110 m) | ~285 KB |
| `limite_pb.geojson` | o contorno do estado | ~34 KB |

Sem simplificar, os municípios teriam 13 MB. Para o coroplético e os contornos, o script usa as camadas `municipios` e `limite_pb` do mesmo GeoPackage.

### 6.2 O script de automação (`queimadas_pb.py`)

Os trechos centrais, copiados do script:

**Ligar o tempo na camada** (o mesmo que a Atividade 1, passo 2):

```python
tp = lyr.temporalProperties()
tp.setIsActive(True)
tp.setMode(Qgis.VectorTemporalMode.FeatureDateTimeInstantFromField)
tp.setStartField("DataHora")
```

**Configurar o Controlador Temporal** (passos 3 a 5):

```python
nav = iface.mapCanvas().temporalController()
nav.setNavigationMode(Qgis.TemporalNavigationMode.Animated)
nav.setTemporalExtents(QgsDateTimeRange(inicio, fim))
nav.setFrameDuration(QgsInterval(1, Qgis.TemporalUnit.Weeks))
nav.setTemporalRangeCumulative(False)  # True = acumula desde o início
```

**Limpar o `-999`:** um valor só entra se existir e não for o sentinela.

```python
def valor(f, campo):
    """Valor numérico do campo, ou None quando vazio ou -999."""
    v = f[campo]
    if v is None or v == SEM_DADO or str(v) == "NULL":
        return None
    return v
```

**Só os focos do ano**, contados no horário da Paraíba. Nesta camada não há nenhum fora de 2026, mas um novo download do BDQueimadas pode trazer a virada do ano:

```python
quando = f["DataHora"].toPyDateTime().replace(tzinfo=timezone.utc)
if quando.astimezone(FUSO_PB).year != ANO:
    fora_do_ano += 1
    continue
```

**Simplificar os municípios** e gravar o nome em maiúsculas, para casar com o campo `Municipio` dos focos:

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
> | `ensure_ascii=False` | mantém `SÃO JOSÉ DE PRINCESA` e `Mata Atlântica` legíveis no arquivo |
> | `try: from qgis.utils import iface` | o mesmo script roda no Console (com mapa) e fora dele (só exporta) |

**Rodar o script:** abra `queimadas_pb.py` no **Editor do Console Python** do QGIS, ajuste `GPKG` e `PASTA_DASHBOARD` (a pasta `docs/queimadas_pb/` do seu clone do repositório) e clique em **Executar script**. Saída esperada:

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

### 6.3 As peças do dashboard

O painel é uma página estática com cinco arquivos em [`docs/queimadas_pb/`](../../docs/queimadas_pb/): `index.html` (a estrutura), `app.js` (a lógica) e os três GeoJSON. Não há servidor nem banco de dados; as bibliotecas vêm de uma CDN.

| Biblioteca | Papel no dashboard |
| --- | --- |
| **Leaflet 1.9** | o mapa: mapas base, zoom, popups, contornos e coroplético (`L.geoJSON`) |
| **Leaflet.TimeDimension** | o "Controlador Temporal" da web: ▶, ⏸, avançar, voltar, velocidade e barra de tempo |
| **Leaflet.heat** | a visualização de densidade (mapa de calor) |
| **Leaflet.markercluster** | a visualização de agrupamentos: círculos com a contagem, que se abrem com o zoom |
| **Tom Select** | a busca de município: filtra a lista enquanto se digita, sem diferenciar acentos |
| **Vue.js 3** | guarda o estado (filtros, visualização, passo, modo, instante) e atualiza tudo quando ele muda |
| **Highcharts** | os gráficos: série temporal, municípios, bioma e hora da detecção |
| **Tailwind CSS** | o visual, com classes direto no HTML |

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

> **Por que Vue e não jQuery?** Com jQuery, cada filtro precisaria de código para atualizar à mão o mapa, os 4 gráficos, os 5 indicadores, a tabela e as etiquetas, e é fácil esquecer um. No Vue, você declara *o que* cada parte mostra a partir do estado (`computed`), e ele refaz só o que mudou.

> ⚠️ **Leaflet 1.9, não 2.0.** Os três plugins foram escritos para o Leaflet 1.x. A série 2.0 mudou a API e os quebra.

### 6.4 Um estado, várias vistas

Todo o dashboard deriva de seis valores:

```
   município ──┐
   bioma ──────┤                    ┌──> mapa (a visualização escolhida)
   visualização┤                    ├──> indicadores e tabela
   passo ──────┼──> focos filtrados ┼──> gráficos de municípios e de bioma
   modo ───────┤                    └──> faixa destacada na série temporal
   instante ───┘
```

**O instante vem do TimeDimension.** A lista de instantes é o início de cada passo (dia, semana ou mês, à meia-noite da Paraíba). A cada quadro, o plugin dispara `timeload`, o Vue recebe o novo instante e o resto se atualiza sozinho. O controle do plugin nasce no mapa e é levado para a faixa abaixo dele, para não cobrir os dados:

```javascript
dimensao = new L.TimeDimension({ times: instantes, currentTime: tempo.value });
dimensao.on("timeload", (e) => { tempo.value = e.time; });
tempoEl.value.appendChild(controle.getContainer());
```

**A janela de tempo** depende do modo: *só o passo atual* ou *acumulado* (de janeiro até o fim do passo), o mesmo que o **Intervalo cumulativo** do QGIS:

```javascript
const janela = computed(() => ({
  inicio: modo.value === "acumulado" ? limites.value.inicio : tempo.value,
  fim: proximoPasso(tempo.value, passo.value),
}));
```

**Uma visualização por vez.** Só a camada escolhida fica no mapa, e só ela é atualizada a cada quadro:

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

**Gráficos ligados entre si.** Clicar numa barra de município filtra o painel inteiro; clicar numa coluna da série temporal leva a animação até aquele período. O gráfico de municípios **ignora o próprio filtro** e destaca o escolhido: assim você vê o município no meio dos outros, em vez de uma barra solitária. O coroplético faz o mesmo.

**Componentes de fora do Vue precisam de ponte nos dois sentidos.** O município pode mudar por quatro caminhos: a busca, uma barra do gráfico, o coroplético ou a etiqueta ✕. O `true` em `setValue` evita um vai e volta infinito:

```javascript
onChange: (valor) => { municipio.value = valor || ""; },           // Tom Select → Vue
watch(municipio, (valor) => {                                       // Vue → Tom Select
  if (buscaMunicipio.getValue() !== valor) buscaMunicipio.setValue(valor, true);
});
```

### 6.5 Como o painel chegou aqui: quatro rodadas de revisão com a IA

| Rodada | O que estava errado | O que mudou |
| --- | --- | --- |
| **1. Primeira versão** | funcionava, com números certos, mas o mapa ficou **poluído**: calor, agrupamentos e cores de FRP ligados ao mesmo tempo, duas legendas, abrindo no acumulado de dez meses | — |
| **2. Revisão cartográfica** | não havia hierarquia visual | uma visualização por vez, legenda que muda com ela, abrir no mês atual, agrupamentos em 4 faixas, contornos discretos, coroplético, controle de tempo abaixo do mapa, popups em cartão |
| **3. Revisão de uso** | o leitor não sabia que período via, nem o que cada filtro afetava; teclado, erros de rede e celular esquecidos | etiqueta do período, filtros ativos removíveis, indicadores com contexto, `aria-pressed`, estados de carregamento e erro, layout de celular |
| **4. Detalhes** | 203 municípios numa lista; sem atalho para voltar ao estado | busca com autocomplete e botão 🏠 |

Em todas as rodadas, a IA escreveu o código **e** sugeriu melhorias, mas quem decidiu o que adotar, e quem conferiu no navegador se ficou certo, foi uma pessoa. Duas sugestões foram recusadas, com justificativa: uma grade hexagonal H3 (virou desafio) e um botão "minha localização", sem uso nesta análise.

### 6.6 Rodar localmente e publicar

**Rodar localmente.** O navegador **não deixa** uma página aberta direto do disco (`file://`) ler os GeoJSON. Sirva a pasta `docs/`:

```bash
cd docs
python -m http.server 8000
```

e abra `http://localhost:8000/queimadas_pb/`. Gerou os GeoJSON de novo e nada mudou? Recarregue ignorando o cache: **Ctrl+Shift+R** (Windows/Linux) ou **Cmd+Shift+R** (macOS).

**Publicar no GitHub Pages:**

1. Faça *commit* e *push* da pasta `docs/` para a branch `main`.
2. No GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**; **Branch: `main`**, pasta **`/docs`**; **Save**.
3. Em um ou dois minutos, o painel estará em `https://<seu-usuario>.github.io/<repositorio>/queimadas_pb/`. O deste curso está em [marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/](https://marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/).

O arquivo vazio `docs/.nojekyll` diz ao GitHub para servir os arquivos como estão, sem passar pelo Jekyll.

> ⚠️ **Tudo em `docs/` fica público**, mesmo o que a página não usa. Antes do *push*, confira com `git status` se não entrou nenhum arquivo de trabalho (um `.zip`, um rascunho, uma planilha).

### 6.7 Os prompts usados com a IA

#### 🤖 Prompt do script PyQGIS

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

#### 🌐 Prompt do dashboard

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

> 💡 O prompt do dashboard é o **resultado** das quatro rodadas da seção 6.5, não o ponto de partida. Ninguém escreve um prompt assim de primeira: ele cresce a cada vez que você olha o painel e encontra o que não funciona.

---

## 🛡️ 7. Resolução de problemas e dicionário

### ⚠️ Armadilhas comuns

| Sintoma | Causa | Como corrigir |
| :--- | :--- | :--- |
| **média do risco de fogo negativa** | o `-999` entrou na conta | tratar `-999` como "sem dado" antes de exportar |
| **pico de detecções às 18h–19h** | a hora foi lida em UTC | agrupar e mostrar em UTC−3 (`America/Fortaleza`) |
| **página sem dados; erro de CORS no console** | o HTML foi aberto com duplo clique (`file://`) | `python -m http.server` ou GitHub Pages |
| **GeoJSON novo, painel com os números antigos** | o navegador reaproveitou o arquivo do cache | recarregar com Ctrl/Cmd+Shift+R |
| **controles quebrados, erros no console** | Leaflet 2.0 com plugins da série 1.x | fixar `leaflet@1.9.4` |
| **mosaicos com "API key required"** | o provedor do mapa base exige chave (ex.: CARTO) | usar mapas base sem chave (OSM, Esri) ou cadastrar a chave |
| **animação travando** | 2.445 marcadores recriados a cada quadro | criar uma vez e reaproveitar |
| **mapa poluído, duas legendas** | calor, agrupamentos e cores de FRP ligados juntos | uma visualização por vez, com a legenda dela |
| **dez meses de focos sobrepostos ao abrir** | o painel abria no acumulado | abrir no último mês, só o passo atual |
| **a busca mostra um município e o painel filtra outro** | o filtro mudou por outro caminho e ninguém avisou o Tom Select | sincronizar nos dois sentidos (seção 6.4) |
| **o ✕ do popup fica fora da caixa** | o `padding` do popup foi zerado e a margem do conteúdo "vazou" (colapso de margens do CSS) | manter o `padding` do `.leaflet-popup-content-wrapper` |
| **1ª semana "29/12/2025 a 04/01/2026"** | as semanas vão de segunda a domingo, e 1º/01/2026 foi uma quinta | cortar os passos em 1º de janeiro |

> **Licenças.** Leaflet, plugins, Vue e Tailwind são livres (MIT/BSD); o Tom Select também (Apache 2.0). O **Highcharts** é gratuito para uso **pessoal, educacional e sem fins lucrativos**; para uso comercial, exige licença (alternativas livres: Apache ECharts, Chart.js). O mapa base OpenStreetMap segue a [política de uso dos mosaicos](https://operations.osmfoundation.org/policies/tiles/).

### 📖 Dicionário para estudantes

- **Foco de calor:** pixel com temperatura bem acima da vizinhança, no instante da passagem do satélite.
- **FRP (*Fire Radiative Power*):** potência radiativa do fogo, em megawatts; mede a intensidade, não a área.
- **UTC:** o horário de referência mundial; a Paraíba fica 3 horas atrás (UTC−3).
- **Valor sentinela:** um número "impossível", como `-999`, usado para dizer "sem dado".
- **GeoJSON:** formato de texto, leve, para guardar geometrias e atributos na web.
- **WebGIS:** um SIG que roda no navegador, sem instalar programas.
- **Coroplético:** mapa em que cada área (aqui, o município) é colorida conforme um valor.
- **CDN (*Content Delivery Network*):** rede que entrega bibliotecas prontas (Leaflet, Vue…) para o navegador.
- **Estado (*state*):** as escolhas ativas na página: município filtrado, mês, visualização.
- **Simplificação de geometria:** remover vértices dispensáveis de um polígono para deixá-lo mais leve, sem perder a forma.

---

## 🚀 8. Desafios para depois da aula

1. **Vídeo no QGIS.** Use **Exportar animação** do Controlador Temporal, com o rótulo de data da Atividade 1, e transforme os quadros num GIF. Compare o esforço com o de mandar o link do dashboard.
2. **Focos por 1.000 km².** Cajazeiras lidera em número de focos, mas é também um município grande? Calcule a área de cada município num SRC métrico (ver [`dados_curso/`](../../dados_curso/README.md)), grave-a em `municipios_pb.geojson` e faça o coroplético por densidade. O ranking muda?
3. **Grade hexagonal.** Em vez dos limites municipais, gere no QGIS uma grade de hexágonos de 10 km (*Criar grade*, num SRC métrico), conte os focos em cada um (*Contar pontos em polígono*) e acrescente ao dashboard uma quinta visualização. O padrão muda?
4. **Só com o teclado.** Use o painel sem o mouse: Tab, Enter, Espaço e setas. Consegue filtrar um município, trocar a visualização, animar o tempo e abrir um foco da tabela no mapa? Anote onde travou e peça à IA a correção.
5. **Sem internet na sala.** Baixe as bibliotecas para `docs/queimadas_pb/vendor/`, troque os endereços no `index.html` e teste com o Wi-Fi desligado. O que continua dependendo da internet? (Dica: o mapa base.)
6. **Atualização automática.** Como atualizar o dashboard toda semana com novos dados do BDQueimadas, sem abrir o QGIS? O script já roda fora da interface; pesquise *GitHub Actions*.

---

<!-- navegação -->
[⬅️ 🚶 Alcance a partir do IFPB](../alcance_ifpb/alcance_ifpb.md) · [🏠 Início](../../README.md)
