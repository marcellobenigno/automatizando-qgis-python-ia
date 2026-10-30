<!-- navegação -->
[🏠 Início](../../README.md) · [📍 Geocodificação urbana ➡️](../geocodificacao/geocodificacao.md)

# Automatizando o QGIS com Python e IA

Pense na última vez que você repetiu a mesma sequência de ferramentas no QGIS: abrir a camada, reprojetar, gerar um buffer, recortar, calcular a área, exportar… e depois fazer tudo de novo para o próximo arquivo, o próximo município, a próxima rodovia.

Este curso parte de uma ideia simples: **se você sabe fazer à mão, você pode ensinar o computador a fazer por você.** A linguagem **Python** pode ser utilizada dentro do **QGIS** para automatizar tarefas; a Inteligência Artificial (IA) generativa é uma intérprete que ajuda a escrever nessa linguagem. Mas quem decide *o que* fazer, e quem confere se ficou certo, continua sendo você.


## 1. O que é automatizar?

Automatizar é **transformar uma sequência de operações em instruções que o computador executa**, sem que você precise repetir cada clique.

> 💡 Um script pode executar *perfeitamente* uma análise *conceitualmente errada*. Automação aumenta a velocidade — inclusive a velocidade de errar. Por isso, **só automatiza bem quem sabe fazer à mão**.

---

## 2. As peças do quebra-cabeça

Antes de escrever qualquer linha de código, vale organizar o vocabulário. São cinco peças, cada uma com um papel:

![Fluxo QGIS + Python + IA](../../imgs/introducao/01_fluxo_qgis_python_ia.png)

| Recurso | O que é | Analogia |
| --- | --- | --- |
| **QGIS** | O ambiente: camadas, mapas, algoritmos, layouts | A oficina |
| **Python** | A linguagem: variáveis, repetições (`for`), condições (`if`) | O idioma |
| **PyQGIS** | A biblioteca que dá ao Python acesso aos objetos do QGIS (projeto, camadas, feições, atributos) | As mãos dentro da oficina |
| **Processing** | A estrutura que organiza **todas** as ferramentas de análise como algoritmos com parâmetros | A caixa de ferramentas |
| **IA generativa** | Assistente que ajuda a planejar, escrever, explicar e depurar o código | Um colega experiente, mas que precisa ser supervisionado |

### Onde o Python entra no QGIS

![Onde o Python entra no QGIS](../../imgs/introducao/02_python_no_qgis.png)

O Python alcança praticamente tudo no QGIS. Para este curso, o que importa é saber **qual porta usar para cada situação**:

| Recurso | Quando usar | No curso |
| --- | --- | --- |
| **Console Python** | Testar comandos, inspecionar camadas, desenvolver um script passo a passo | ✅ Ponto de partida |
| **Processing via código** (`processing.run`) | Executar e encadear algoritmos que já existem na Caixa de Ferramentas | ✅ **Foco principal** |
| **PyQGIS** | Ler e alterar camadas, feições e atributos quando nenhum algoritmo pronto resolve | ✅ Quando necessário |
| **Processamento em lote** | Rodar *uma* ferramenta em vários arquivos, pela interface | ✅ Como comparação |
| **Modelador Gráfico** | Montar um fluxo visualmente e exportá-lo como script Python | ✅ Como ponte entre clique e código |
| **Layouts e exportação** | Gerar séries de mapas padronizados | ➖ Mencionado |
| **Plugins** | Criar extensões com interface própria | ❌ **Fora do escopo** |

> **Dentro ou fora do QGIS?** Todos os scripts do curso rodam **dentro** do QGIS, no Editor do Console Python. Lá, o projeto aberto, as camadas e o objeto `iface` (a interface gráfica) já estão disponíveis. Scripts *fora* do QGIS (no terminal, agendados) também são possíveis, mas exigem configurar o ambiente — e o `iface` não existe neles. Guarde essa diferença: ela vai aparecer quando você pedir código à IA.

---

## 3. A ideia central: todo clique tem um código

Esta é a ponte que sustenta o curso inteiro. Quando você executa uma ferramenta da Caixa de Ferramentas de Processamento, o QGIS registra, na aba **Log**, o nome do algoritmo e **todos** os parâmetros usados:

![Do clique ao código](../../imgs/introducao/08_do_clique_ao_codigo.png)

Compare o Log acima com o código abaixo. É a mesma coisa:

```python
process = processing.run("native:buffer", {
    "INPUT": camada_pb200_utm,
    "DISTANCE": 3000,           # unidades do SRC da camada (aqui, metros)
    "SEGMENTS": 5,
    "END_CAP_STYLE": 0,         # 0 = arredondado
    "JOIN_STYLE": 0,
    "MITER_LIMIT": 2,
    "DISSOLVE": True,
    "OUTPUT": "TEMPORARY_OUTPUT",   # camada temporária, em memória
})
buffer_utm_3km = process["OUTPUT"]

# Adiciona a nova camada gerada diretamente à tela do QGIS
QgsProject.instance().addMapLayer(buffer_utm_3km)
```

Três coisas a observar:

1. **`"native:buffer"`** é o identificador do algoritmo. Cada ferramenta da Caixa tem o seu (`native:clip`, `native:reprojectlayer`, `native:intersection`…).
2. **Os parâmetros são um dicionário** — pares `"NOME": valor`, exatamente os campos do formulário da ferramenta.
3. **O resultado também é um dicionário**; a camada gerada está em `process["OUTPUT"]` e pode virar a entrada do próximo algoritmo. É assim que se *encadeia* um fluxo.

Você não precisa decorar nada disso. O próprio QGIS entrega o código:

- **Avançado → Copiar como comando Python**, no rodapé de qualquer ferramenta;
- **Processamento → Histórico**, que guarda tudo o que você executou;
- `processing.algorithmHelp("native:buffer")`, que lista todos os parâmetros aceitos pela **sua** versão do QGIS — a fonte da verdade quando a IA sugerir um parâmetro estranho.

> 💡 Portanto, o caminho do curso é sempre o mesmo: **fazer à mão → copiar o código → juntar os passos em um script → generalizar.**

---

## 4. Primeiro contato: o Console Python

![Console Python do QGIS](../../imgs/introducao/07_console_python.png)

Abra o Console em **Complementos → Console Python** (`Ctrl+Alt+P`). Com a camada `municipios` selecionada no painel Camadas, digite uma linha de cada vez:

```python
camada = iface.activeLayer()                  # a camada selecionada no painel
camada.name(), camada.featureCount()          # ('municipios', 223)
camada.crs().authid()                         # 'EPSG:4326'
[campo.name() for campo in camada.fields()]   # nomes dos campos
```

> **O que é `iface`?** É a abreviação de *interface*: um objeto que o QGIS deixa pronto no Console e que representa a **janela do QGIS** — painel de camadas, mapa, menus e barras de ferramentas. Por meio dele, o código faz o que você faria com o mouse: `iface.activeLayer()` devolve a camada selecionada no painel Camadas, `iface.mapCanvas()` dá acesso ao mapa e `iface.addVectorLayer(...)` adiciona uma camada ao projeto. Como representa a janela, o `iface` **só existe dentro do QGIS**: num script executado fora dele, a linha acima falharia com `NameError: name 'iface' is not defined`.

Em quatro linhas você respondeu a três perguntas que todo analista faz antes de qualquer análise: *quantas feições?*, *em que SRC?*, *quais campos?* Repare na terceira: **EPSG:4326 é um SRC geográfico, em graus.** Guarde isso para a seção 6.

Para comandos maiores, use o **Editor** do Console (ícone *Mostrar editor*): ali você escreve, salva e executa scripts inteiros. É onde todos os exercícios do curso acontecem.

> ⚠️ **Aviso de segurança:** o Console executa comandos de verdade. Se o código mandar apagar, sobrescrever ou editar, ele vai executar imediatamente. **Leia e entenda o código antes de clicar em Executar** — principalmente trechos gerados por Inteligência Artificial.

---

## 5. A IA como copiloto: escrevendo bons prompts

![Estrutura de Prompt GIS](../../imgs/introducao/03_prompt_gis.png)

Um **prompt** é a instrução que você envia à IA. A IA não vê seu projeto, não conhece seus dados e não sabe qual versão do QGIS você usa. Tudo o que você não disser, ela vai **supor** — e suposições viram código errado.

| Elemento | ❌ Prompt fraco | ✅ Prompt melhorado | Por que melhora |
| --- | --- | --- | --- |
| **Contexto** | "Faça um código para o QGIS." | "QGIS 3.44, Console Python. Camada de linhas `malha_viaria` (EPSG:4326), campo `rodovia_nome`." | Evita API antiga (QGIS 2) e código para o ambiente errado |
| **Instruções** | "Faça a análise e salve." | "1) extraia a PB-200; 2) reprojete para EPSG:31984; 3) buffer de 3 000 m dissolvido; 4) salve em GeoPackage." | O fluxo fica explícito e verificável |
| **Exemplos** | "Quero um código organizado." | "Parâmetros em constantes no topo; um bloco comentado por etapa; imprima o nº de feições ao final." | Define uma forma concreta, que você pode conferir |
| **Clareza** | "Selecione áreas perto da estrada." | "Considere *próxima* a feição a até 3 000 m da rodovia." | "Perto", "grande", "otimizado" não são critérios |

### Um prompt completo

```text
Atue como especialista em PyQGIS. Escreva um script para o Editor do Console
Python do QGIS 3.44, usando processing.run e algoritmos "native:".

Dados (já carregados no projeto, em EPSG:4326):
- malha_viaria (linhas), campo rodovia_nome (ex.: 'PB-200')
- municipios (polígonos), campos nome e cod_ibge_m

Passos:
1. extrair a rodovia 'PB-200';
2. reprojetar para EPSG:31984 (SIRGAS 2000 / UTM 24S);
3. gerar um buffer de 3000 m, dissolvido;
4. listar os municípios que intersectam o buffer.

Regras:
- verifique se as camadas existem antes de começar e mostre mensagens claras;
- não altere as camadas originais; saídas intermediárias em memória;
- parâmetros em constantes no topo; comentários em português;
- não use APIs do QGIS 2 (processing.runalg, QgsMapLayerRegistry);
- se faltar alguma informação, pergunte em vez de supor.
```

### Três hábitos que fazem diferença

1. **Peça por etapas.** Uma etapa por vez, rodando cada uma antes de pedir a próxima. Se algo der errado no passo 2, você descobre no passo 2 — e não depois de 150 linhas.
2. **Peça explicações.** "Explique linha a linha" e "quais parâmetros ficaram no padrão?" são perguntas que ensinam e, de quebra, revelam erros.
3. **Depure com contexto.** Ao surgir um erro, envie **a mensagem completa**, o trecho de código, a versão do QGIS e a etapa em que falhou. "Não funcionou, corrige" é o pior prompt possível.

> 🔒 **Compartilhe a estrutura, não os dados.** Para obter ajuda com código, basta enviar nomes de camadas, campos, tipos e SRC — não o arquivo. Dados pessoais, sigilosos ou de clientes não devem ir para serviços externos sem autorização.

---

## 6. Rodou sem erro ≠ está certo

![Buffer em graus vs metros](../../imgs/introducao/06_buffer_graus_vs_metros.png)

![Validação de SRC/CRS](../../imgs/introducao/04_validacao_crs.png)

Os dois códigos rodaram **sem nenhuma mensagem de erro**. À esquerda, a camada está em UTM: `DISTANCE: 3000` significa 3 000 **metros**, e o resultado é a faixa de 3 km esperada. À direita, alguém escreveu `DISTANCE: 3` "pensando em quilômetros" numa camada em WGS 84, cuja unidade é o **grau**: o buffer tem raio de ~330 km e engole a Paraíba inteira.

O QGIS fez exatamente o que foi pedido. O erro estava na **interpretação das unidades** — e nenhum interpretador Python, nenhuma IA, vai avisar você disso. É um erro clássico, inclusive em código gerado por IA.

> 💡 **Atribuir não é reprojetar:**
>
> - **Atribuir projeção (`Set CRS`):** apenas troca a "etiqueta" do arquivo. As coordenadas internas dos pontos continuam exatamente as mesmas.
> - **Reprojetar (`Reproject layer`):** recalcula matematicamente todas as coordenadas X e Y para o novo sistema.
>
> Trocar a etiqueta de uma camada em graus para UTM sem recalcular as coordenadas faz os dados "desaparecerem" ou irem parar no meio do oceano, sem nenhum aviso de erro do software.

### O ciclo de validação

Trate todo código — seu ou da IA — como uma **proposta** a ser testada. A lista abaixo resume os cuidados em três momentos:

#### Antes de pedir o código

☐ Defina o objetivo da análise e os critérios (distâncias, unidades, campos).  
☐ Confira os nomes **exatos** das camadas e dos campos (maiúsculas e acentos contam).  
☐ Informe o SRC de cada camada — graus ou metros.  
☐ Verifique a versão do QGIS e onde o código vai rodar.  

#### Antes de executar

☐ Leia o código e entenda o que cada bloco faz (caso não saiba Python, peça à IA para explicar e comentar o código).  
☐ Confirme se os algoritmos e parâmetros existem (`processing.algorithmHelp`).  
☐ Verifique se o script apaga, sobrescreve ou edita algo, e trabalhe em uma **cópia**.  
☐ Teste primeiro em uma área pequena.  

#### Depois de executar

☐ Confira se o resultado aparece **no lugar certo** do mapa.  
☐ Avalie se o número de feições faz sentido.  
☐ Meça uma amostra com a ferramenta de medição (a faixa tem mesmo 3 km?).  
☐ Verifique se a tabela de atributos está preenchida, sem nulos inesperados.  
☐ Compare o resultado com uma execução manual do mesmo fluxo.  

---

## 7. O método de trabalho: do problema ao script reutilizável

Integrando todos os conceitos apresentados, este é o fluxo de trabalho prático que orientará cada exercício e desafio ao longo da sua jornada de automação:

![Método de trabalho: definir objetivo, execução manual, tradução para código, apoio com IA, validação e reaproveitamento](../../imgs/introducao/09_metodo_de_trabalho.svg)

| Etapa | Foco da etapa | Pergunta-chave que ela responde |
| :--- | :--- | :--- |
| **1. Objetivo** | Diagnóstico do problema | *Qual é o desafio geoespacial e qual resultado exato preciso obter?* |
| **2. Fluxo manual** | Mapeamento no QGIS | *Quais ferramentas nativas utilizarei, em qual sequência e com quais parâmetros?* |
| **3. Código (Processing)** | Tradução para PyQGIS | *Como converter cada clique da interface no algoritmo correspondente em `processing.run(...)`?* |
| **4. Apoio com IA** | Aceleração e escrita | *Como construir o prompt ideal para gerar, compreender ou depurar o script rapidamente?* |
| **5. Validação** | Auditoria geoespacial | *O resultado reflete corretamente a realidade do terreno, com SRC e unidades exatas?* |
| **6. Reaproveitamento** | Escala e automação | *Como estruturar este código para processar novas bases ou rotinas em lote de forma autônoma?* |

### Aplicação prática no mundo real

Nos exercícios seguintes, este fluxo será aplicado a cenários reais de análise territorial no estado da **Paraíba**, organizados em uma **trilha de aprendizagem progressiva**, em ordem crescente de complexidade:

#### 📍 Exercício 1 — Geocodificação urbana em João Pessoa

- **Nível:** 🟢 Iniciante
- **O desafio:** você recebe uma planilha com nomes e endereços de João Pessoa (PB), mas sem coordenadas. A tarefa é transformá-la em uma camada de pontos no mapa. Você descreve o que quer, a IA escreve o script e você confere o resultado.
- **O que você irá aprender:**
  - ler uma tabela (CSV) com Python;
  - consultar um serviço web de geocodificação (Nominatim / OpenStreetMap), respeitando limites de requisições;
  - tratar endereços não encontrados sem perder linhas da tabela;
  - criar uma camada temporária de pontos no QGIS;
  - desconfiar de um ponto "encontrado": verificar se ele caiu na rua correta.

👉 [Abrir o exercício](../geocodificacao/geocodificacao.md)

#### 🛣️ Exercício 2 — Impacto ambiental da duplicação da PB-200

- **Nível:** 🟡 Intermediário
- **O desafio:** delimitar a área de influência da duplicação da rodovia PB-200 (buffer de 3 km) e cruzá-la com os municípios atingidos e com o mapeamento de uso do solo, para responder: *quanto de cada classe de uso, em hectares, há dentro da faixa, em cada município?*
- **O que você irá aprender:**
  - fazer a análise primeiro à mão e depois traduzir cada clique em `processing.run(...)`;
  - encadear algoritmos (reprojetar, buffer, recortar, interseção), usando a saída de um como entrada do próximo;
  - calcular áreas em hectares num SRC métrico adequado (UTM / SIRGAS 2000);
  - comparar o resultado do script com o do fluxo manual.

👉 [Abrir o exercício](../pb200/pb200.md)

#### 🗺️ Exercício 3 — Grade interativa SRTM/TOPODATA

- **Nível:** 🟡 Intermediário
- **O desafio:** partir de um mapa índice na web e criar uma grade no QGIS em que basta **clicar numa célula** para baixar e carregar automaticamente o Modelo Digital de Elevação (MDE) TOPODATA daquela região.
- **O que você irá aprender:**
  - usar a IA para investigar a estrutura de dados de uma página web;
  - converter os dados em uma camada vetorial (GeoJSON);
  - descobrir a regra de formação dos links de download de cada quadrícula;
  - criar **ações personalizadas** em Python no QGIS para baixar arquivos sob demanda, com barra de progresso.

👉 [Abrir o exercício](../grade_topodata/grade_topodata.md)

#### ⛰️ Exercício 4 — Perfil topográfico da PB-200

- **Nível:** 🟡 Intermediário
- **O desafio:** juntar os dois exercícios anteriores e traçar o perfil topográfico da PB-200 inteira, do km 0 ao km 104, com o MDE TOPODATA baixado pela ação de clique. O ponto de partida é um tutorial da web escrito para uma versão antiga do QGIS.
- **O que você irá aprender:**
  - usar a IA para atualizar código antigo e conferir o que ela trocou (GRASS e SAGA por algoritmos nativos);
  - descobrir por que a solução "óbvia" para unir trechos falha (trechos invertidos e com falhas) e costurá-los pela ordem do km;
  - gerar pontos ao longo de uma linha e ler a altitude de cada um no raster;
  - desenhar o perfil com matplotlib e conferir com a ferramenta nativa Perfil de Elevação;
  - interpretar o resultado: exagero vertical, ruído do SRTM e o que o dado permite (ou não) afirmar.

👉 [Abrir o exercício](../perfil_pb200/perfil_pb200.md)

#### 🚶 Exercício 5 — Alcance a partir do IFPB

- **Nível:** 🔴 Avançado
- **O desafio:** descobrir até onde se chega, pelas ruas, a partir do IFPB Campus João Pessoa: andando 800 m e dirigindo 4 km. A malha viária é baixada uma única vez do OpenStreetMap, e as análises rodam offline.
- **O que você irá aprender:**
  - separar o download (OSMnx, uma vez) da análise (PyQGIS + NetworkX, sem internet), ganhando velocidade e independência de servidores públicos;
  - montar um grafo dirigido a partir de um GeoPackage e tirar dele duas redes: a pé e de carro, com mão única;
  - calcular a distância pela rede (Dijkstra) e cortar as ruas em faixas de distância;
  - comparar o alcance pela rede com o círculo em linha reta;
  - conferir o resultado com a Área de serviço nativa do QGIS e desconfiar de números que não fecham.

👉 [Abrir o exercício](../alcance_ifpb/alcance_ifpb.md)

#### 🔥 Exercício 6 — Focos de queimadas na Paraíba

- **Nível:** 🔴 Avançado
- **O desafio:** mostrar *quando* e *onde* o fogo apareceu na Paraíba em 2026, a partir dos 2.445 focos do BDQueimadas (INPE). Primeiro, com o Controlador Temporal do QGIS; depois, num dashboard publicado no GitHub Pages, que qualquer pessoa abre no navegador ou no celular, sem instalar o QGIS.
- **O que você irá aprender:**
  - configurar as propriedades temporais de uma camada e animar o mapa, à mão e com PyQGIS;
  - limpar dados para a web: valores `-999`, fuso horário (UTC × horário da Paraíba) e tamanho dos arquivos;
  - montar um dashboard com Leaflet (TimeDimension, heat e markercluster), Vue.js e Highcharts, com uma representação cartográfica por vez;
  - revisar o painel como um leitor: o que ele mostra, quais filtros valem, acessibilidade e falhas de rede;
  - conferir que o dashboard mostra os mesmos números do QGIS.

👉 [Abrir o exercício](../queimadas_pb/queimadas_pb.md) · 🌐 [Abrir o dashboard publicado](https://marcellobenigno.github.io/automatizando-qgis-python-ia/queimadas_pb/)

#### 🚧 Próximos exercícios

Em produção.

> 💡 **Para levar:** a Inteligência Artificial pode gerar o código e o *Processing Framework* do QGIS pode executar os cálculos. No entanto, a **responsabilidade técnica** sobre o resultado final — a escolha do SRC correto, a precisão das unidades de medida e a rigorosa interpretação do fenômeno geográfico — é exclusivamente de quem assina o projeto. **É sua.**

---

## Glossário rápido

| Termo | Significado |
| --- | --- |
| **Algoritmo** | Ferramenta do Processing que recebe parâmetros e produz resultados (ex.: `native:buffer`) |
| **Feição** | Uma entidade da camada (ponto, linha ou polígono) com seus atributos |
| **`iface`** | Objeto que dá acesso à interface gráfica do QGIS; existe só dentro do QGIS |
| **Prompt** | Instrução enviada a uma ferramenta de IA |
| **Reprojetar** | Recalcular as coordenadas de um SRC para outro |
| **SRC / CRS** | Sistema de Referência de Coordenadas; define se as coordenadas estão em graus ou metros, e em relação a quê |
| **`TEMPORARY_OUTPUT`** | Saída em memória, sem gravar arquivo em disco |
| **Validação** | Verificar se o resultado atende aos requisitos e representa corretamente a análise |

## Para consultar

- [PyQGIS Developer Cookbook](https://docs.qgis.org/latest/pt_BR/docs/pyqgis_developer_cookbook/) — o manual de referência do PyQGIS
- [Usando os algoritmos de processamento a partir do console](https://docs.qgis.org/latest/pt_BR/docs/user_manual/processing/console.html)
- [Documentação da API do QGIS para Python](https://qgis.org/pyqgis/)

Consulte sempre a documentação da **versão instalada**: classes, métodos e parâmetros mudam entre versões.

---

<!-- navegação -->
[🏠 Início](../../README.md) · [📍 Geocodificação urbana ➡️](../geocodificacao/geocodificacao.md)
