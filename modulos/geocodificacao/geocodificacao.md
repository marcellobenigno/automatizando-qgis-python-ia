<!-- navegação -->
[⬅️ 📘 Introdução](../introducao/introducao.md) · [🏠 Início](../../README.md) · [🛣️ Duplicação da PB-200 ➡️](../pb200/pb200.md)

# Do endereço ao ponto: geocodificação no QGIS com IA

> **Roteiro de aula:** prático, guiado e com aprofundamento técnico
> **Público:** estudantes de geotecnologias, sem experiência em programação · **Nível:** 🟢 Iniciante
> **Duração:** 35 minutos de aula prática (seções 1 a 5) + aprofundamento técnico para estudo posterior (seções 6 e 7)
> **Tema:** geocodificação de endereços com o Nominatim (OpenStreetMap) e conferência do resultado
> **Tecnologias:** QGIS 3.44 e Console Python (PyQGIS); Nominatim; IA generativa

---

## 🧭 1. A proposta da aula

A equipe vai fazer uma saída de campo em João Pessoa e recebeu uma planilha com os locais de visita: nome e endereço, nada de coordenadas. Para planejar a rota no QGIS, cada endereço precisa virar um **ponto**.

Nesta aula, a turma vai fazer isso **sem escrever o código**: você descreve o que quer, a IA escreve o script, o QGIS executa e **você confere o resultado**.

A pergunta que guia a atividade:

> **Se o script rodou sem nenhum erro, os pontos estão no lugar certo?**

![Um endereço geocodificado no QGIS](../../imgs/geocodificacao/1-um-endereco.png)

### 🎯 Objetivos de aprendizagem

Ao final da aula, a turma será capaz de:

1. **explicar** o que é geocodificação e por que o resultado é um palpite, e não a verdade;
2. **escrever um prompt** que peça à IA um script com as regras certas (sem coordenadas inventadas, sem linhas perdidas, respeitando o serviço);
3. **rodar** um script no Editor do Console Python do QGIS;
4. **transformar** uma lista de endereços (CSV) numa camada de pontos, sem descartar nenhuma linha;
5. **conferir** o resultado no mapa e na tabela, e achar os erros que rodam sem dar erro.

---

## 📋 2. Preparação e roteiro de tempo

### 🛠️ Antes da aula, o(a) professor(a) confere

- [ ] **QGIS** 3.34 LTR ou mais recente (material testado no 3.44), com o Console Python.
- [ ] **Dados:** `dados_curso/geocodificacao/enderecos.csv`, com 5 locais de João Pessoa (veja [`dados_curso/`](../../dados_curso/README.md)).
- [ ] **Rede da sala:** acesso a `nominatim.openstreetmap.org`. O serviço é gratuito e não exige cadastro nem chave.
- [ ] **Assistente de IA** aberto no navegador (ChatGPT, Claude, Gemini, Copilot ou similar).

> 💡 **Dica para quem conduz a aula:** o Nominatim aceita **no máximo uma consulta por segundo** por aplicação. Uma turma inteira rodando ao mesmo tempo, da mesma rede, pode ser bloqueada. Se a turma for grande, faça a Atividade 2 em duplas ou rode você a lista uma vez, no projetor, e a turma confere.

### ⏱️ Planejamento minuto a minuto (35 min)

| Intervalo | Etapa | Foco da turma |
| :--- | :--- | :--- |
| **0–5 min** | Pergunta e contexto | O que é geocodificação? O que o serviço devolve, e o que ele não garante. |
| **5–15 min** | Atividade 1: um endereço | Pedir o script à IA, rodar e conferir o ponto. |
| **15–27 min** | Atividade 2: uma lista | Do CSV à camada, sem perder nenhuma linha. Achar o ponto que foi parar na Espanha. |
| **27–32 min** | Atividade 3: onde a geocodificação erra | Os cinco erros que rodam sem mensagem de erro. |
| **32–35 min** | Síntese e fechamento | Check-out oral e mensagem final. |

---

## 💡 3. Fundamentação

### 3.1 O que é geocodificação

**Geocodificação** (*geocoding*) é transformar um endereço em coordenadas. O caminho inverso, coordenadas → endereço, é a **geocodificação reversa**.

Vamos usar o **Nominatim**, o serviço de busca do **OpenStreetMap**. Ele recebe um texto e devolve a **melhor correspondência** que encontrar:

| Você pergunta | O serviço devolve |
| --- | --- |
| `Universidade Federal da Paraíba, João Pessoa, Brasil` | o campus da UFPB, em João Pessoa ✅ |
| `Avenida Epitácio Pessoa, João Pessoa` | **um ponto** da avenida, não a avenida inteira |
| `Mercado Central` | o Mercado Central de **Valência, na Espanha** ❌ |

> 🗣️ **Como explicar para a turma:**
> *"Geocodificar é como pedir informação a um desconhecido na rua. Se você diz só 'Mercado Central', ele aponta para o mais famoso que conhece, que pode estar em outro país. Quanto mais completo o endereço, melhor a resposta. E, mesmo assim, ele pode se enganar com toda a confiança."*

Três ideias para guardar:

1. **O resultado é um palpite, não a verdade.** Quanto mais completo o endereço (município, estado, país), melhor o palpite.
2. **A precisão varia:** pode ser o prédio, a rua, o bairro ou só o município.
3. **"Achou" não quer dizer "achou certo":** o terceiro exemplo foi encontrado, só que no país errado.

### 3.2 As regras do serviço

> ⚠️ **Regras do Nominatim público:** no máximo **1 consulta por segundo**, aplicação identificada no cabeçalho `User-Agent` e crédito ao OpenStreetMap ao publicar mapas. Para milhares de endereços, use outro provedor ou uma instalação própria. Política completa: <https://operations.osmfoundation.org/policies/nominatim/>

### 3.3 A ordem das coordenadas

O serviço responde "latitude, longitude", mas o QGIS pensa em **X, Y**, e X é a **longitude**:

```python
QgsPointXY(longitude, latitude)   # X = longitude, Y = latitude
```

> 🚨 **O erro clássico:** inverter a ordem. Com os números da UFPB, o ponto vai parar no meio do Atlântico Sul, e o script não dá nenhum erro.

---

## 🛠️ 4. Trilha prática guiada

### 📍 Atividade 1: um endereço (10 min)

**Objetivo:** pedir o script à IA, rodar e conferir o ponto.

1. Copie o prompt abaixo para o assistente de IA:

```text
Escreva um script para o Editor do Console Python do QGIS 3.44 que
geocodifique UM endereço com o Nominatim do OpenStreetMap.

- O endereço fica numa variável no topo do script, fácil de trocar.
- Use apenas a biblioteca padrão (urllib, json): nada de pip ou requests.
- Identifique a aplicação no User-Agent, como pede a política do Nominatim.
- Se não houver resultado, avise na barra de mensagens do QGIS e não
  crie nada. Nunca invente coordenadas.
- Se houver, crie uma camada de pontos temporária em EPSG:4326 chamada
  "endereco_geocodificado", com os campos endereco, local_encontrado
  (o display_name do serviço), latitude e longitude.
- Adicione a camada ao projeto e aproxime o mapa do ponto.
- Imprima o local encontrado e as coordenadas.
Comentários curtos, em português.
```

2. **Antes de rodar, confira a resposta da IA:**
   - monta a URL com `urlencode` (que trata espaços e acentos)?
   - tem `User-Agent` na requisição?
   - testa se a lista de resultados está **vazia** antes de usar o primeiro item?
   - cria o ponto com `QgsPointXY(longitude, latitude)`, nessa ordem?
3. Abra o **Console Python** (`Ctrl+Alt+P`), clique em **Mostrar editor (Show Editor)** e cole o script (ou abra [`geocodificar_endereco.py`](geocodificar_endereco.py), a versão revisada).
4. Clique em **Executar script (Run Script)**. Saída esperada:

```text
Local encontrado: UFPB - Universidade Federal da Paraíba, Rua Tab Estanislau Eloy, Castelo Branco, João Pessoa, ...
Latitude: -7.1383657 | Longitude: -34.846399
```

5. O ponto aparece no campus da UFPB. Agora troque o endereço por um que você conheça e rode de novo.

> 💬 **Pausa para reflexão com a turma:**
> - *Por que o prompt diz "nunca invente coordenadas"? O que a IA poderia fazer sem essa frase?*
> - *Alguém testou um endereço que caiu no lugar errado? Por quê?*

<details>
<summary>Respostas esperadas</summary>

- Sem essa regra, um script pode preencher `0, 0` quando o serviço não acha nada. O ponto vai parar no Golfo da Guiné, na costa da África, e parece um resultado como outro qualquer. Um ponto ausente é honesto; um ponto inventado engana.
- Em geral, por endereço incompleto (sem município, estado ou país) ou ambíguo. O serviço devolve o melhor palpite, não a certeza.

</details>

---

### 📍 Atividade 2: uma lista de endereços (12 min)

**Objetivo:** geocodificar o CSV inteiro, sem perder nenhuma linha.

1. Continue **na mesma conversa** com a IA, que já tem o script da Atividade 1 como base:

```text
Agora adapte o script para geocodificar uma LISTA de endereços de um CSV.

O arquivo é separado por ";", em UTF-8, com este cabeçalho e exemplo:
nome;endereco
UFPB;Universidade Federal da Paraíba, João Pessoa, Brasil

- Caminho do CSV, nome da coluna de endereço e separador em variáveis
  no topo do script.
- Espere 1 segundo entre consultas e não repita a consulta de um
  endereço que já apareceu (cache em um dicionário).
- Crie a camada "enderecos_geocodificados" (EPSG:4326) com todas as
  colunas do CSV + local_encontrado, latitude, longitude e status.
- status: "ok", "não encontrado" ou a mensagem de erro de conexão.
- Linha sem resultado entra na camada SEM geometria. Nenhuma linha
  pode ser descartada.
- No fim, imprima quantos endereços foram geocodificados.
```

> 💡 **Mande o cabeçalho e uma linha de exemplo, não a planilha inteira.** É o suficiente para a IA, e você não expõe endereços de clientes ou de pessoas a um serviço externo.

2. Abra o script no editor (ou a versão revisada, [`geocodificar_lista.py`](geocodificar_lista.py)).
3. Em `ARQUIVO_CSV`, informe o **caminho completo** de `dados_curso/geocodificacao/enderecos.csv`, por exemplo: `Path(r"C:\minicurso\dados_curso\geocodificacao\enderecos.csv")`.
4. Clique em **Executar script** e acompanhe o console, uma linha por segundo:

```text
1/5  ok               Universidade Federal da Paraíba, João Pessoa, Brasil
2/5  ok               Estação Cabo Branco, João Pessoa, Brasil
3/5  ok               Mercado Central
4/5  ok               Parque Solon de Lucena, João Pessoa, Brasil
5/5  não encontrado   Rua Inventada da Silva, 999, João Pessoa, Brasil

4 de 5 endereços geocodificados. Confira os demais na tabela de atributos (campo status).
```

5. Quatro de cinco: parece ótimo. Agora **olhe o mapa**:

![Um dos pontos foi parar na Espanha](../../imgs/geocodificacao/2-lista-mapa.png)

6. Abra a tabela de atributos de **`enderecos_geocodificados`** (`F6`) e confira linha a linha:

![Tabela de atributos da lista geocodificada](../../imgs/geocodificacao/3-lista-tabela.png)

| nome | status | Onde caiu | Veredito |
| --- | --- | --- | --- |
| UFPB | ok | João Pessoa | ✅ |
| Estação Cabo Branco | ok | João Pessoa | ✅ |
| Mercado Central | ok | **Valência, Espanha** | ❌ endereço ambíguo |
| Parque Solon de Lucena | ok | João Pessoa | ✅ |
| Escritório | não encontrado | sem ponto | ✅ registrado, nada inventado |

7. **Corrija o CSV:** troque `Mercado Central` por `Mercado Central, João Pessoa, Brasil` e rode de novo. Os quatro pontos ficam em João Pessoa, e o escritório continua como **não encontrado**, como deve ser. 🎉

> ⚠️ **`status = ok` não quer dizer "certo".** O script só sabe que o serviço respondeu. Quem sabe se a resposta faz sentido é você: **olhe o mapa** e leia a coluna `local_encontrado`.

> 💬 **Pausa para reflexão:** *o escritório não foi encontrado. É melhor que ele fique na tabela sem ponto, ou que seja apagado?*

<details>
<summary>Resposta esperada</summary>

Que fique na tabela, sem ponto. Assim a contagem fecha (5 linhas no CSV, 5 na camada) e a equipe sabe que precisa achar esse endereço de outro jeito, antes da saída de campo. Se a linha sumisse, ninguém perceberia que faltou um local de visita.

</details>

> **Nota:** a camada é **temporária** (ícone ao lado do nome). Para guardá-la, clique com o botão direito → **Exportar → Salvar feições como (Export → Save Features As)** → GeoPackage.

---

### 📍 Atividade 3: onde a geocodificação (e a IA) erra (5 min)

Todos estes erros **rodam sem mensagem de erro**. Leia a tabela com a turma e pergunte, para cada linha: *qual frase do nosso prompt evita este erro?*

| Erro típico | Como aparece | Como pegar |
| --- | --- | --- |
| **Latitude e longitude invertidas** | ponto no oceano ou em outro continente | `QgsPointXY(longitude, latitude)`; olhe o mapa |
| **Endereço ambíguo** | `status = ok`, mas o ponto está em outra cidade ou outro país | sempre inclua município, estado e país; leia o `local_encontrado` |
| **Coordenadas inventadas** | a IA preenche `0, 0` quando não acha: pontos no Golfo da Guiné | exija no prompt: "sem resultado, sem geometria" |
| **Linhas descartadas** | o CSV tem 50 linhas, a camada tem 47 | compare as contagens; peça "nenhuma linha pode ser descartada" |
| **Consultas em rajada** | erro `HTTP 429` ou bloqueio do serviço | pausa de 1 s e cache de endereços repetidos |

<details>
<summary>Respostas esperadas</summary>

- **Coordenadas inventadas:** "Nunca invente coordenadas" e "linha sem resultado entra SEM geometria".
- **Linhas descartadas:** "Nenhuma linha pode ser descartada".
- **Consultas em rajada:** "Espere 1 segundo entre consultas" e "não repita a consulta (cache)".
- **Latitude e longitude invertidas** e **endereço ambíguo:** nenhuma frase do prompt resolve. Esses dois só se pegam **olhando o mapa**.

</details>

---

## 🎓 5. Fechamento: checagem de aprendizagem

### 💬 Check-out oral

Peça que a turma complete as frases:

1. *"O script disse `status = ok` para o Mercado Central, mas o resultado estava errado porque…"*
2. *"Uma linha sem resultado deve ficar na camada, sem ponto, porque…"*
3. *"No QGIS, o ponto se cria com longitude primeiro porque…"*

<details>
<summary>Respostas esperadas</summary>

1. … o endereço era ambíguo, e o serviço achou o Mercado Central de Valência, na Espanha. `ok` só quer dizer que o serviço respondeu.
2. … assim nada é inventado nem perdido: a contagem fecha e a equipe sabe qual endereço precisa de atenção.
3. … o QGIS trabalha com X e Y, e X é a longitude. Invertida, a UFPB vai parar no Atlântico Sul.

</details>

### 🏁 Mensagem final

> *"A IA escreveu, em segundos, um script que roda sem erro. Mas rodar sem erro não é o mesmo que estar certo: um dos pontos foi parar na Espanha. Quem garante que os pontos estão no lugar certo é quem olha o mapa."*

---

## 💻 6. Aprofundamento técnico: os scripts

### 6.1 O que deve ser entregue

1. Uma camada `endereco_geocodificado` com **um** ponto (Atividade 1).
2. Uma camada `enderecos_geocodificados` com **todas** as linhas do CSV e os campos `nome`, `endereco`, `local_encontrado`, `latitude`, `longitude` e `status` (Atividade 2).

Requisitos: CRS **EPSG:4326** (latitude/longitude, como o serviço devolve); **nenhuma linha descartada**; **no máximo uma consulta por segundo**.

### 6.2 Um endereço (`geocodificar_endereco.py`)

Os trechos centrais, copiados do script:

**A consulta**, com `urlencode` para os acentos e o `User-Agent` que a política exige:

```python
url = "https://nominatim.openstreetmap.org/search?" + urlencode({
    "q": endereco,
    "format": "jsonv2",
    "limit": 1,
})

# A política do Nominatim exige identificar a aplicação.
requisicao = Request(
    url,
    headers={"User-Agent": "minicurso-qgis-python-ia/1.0"}
)
```

**Sem resultado, nada é criado:**

```python
if not resultados:
    iface.messageBar().pushWarning(
        "Geocodificação",
        f"Nenhum resultado para: {endereco}"
    )
```

**O ponto, com longitude primeiro:**

```python
# X = longitude, Y = latitude (a ordem inversa da que o serviço exibe).
feicao.setGeometry(
    QgsGeometry.fromPointXY(QgsPointXY(longitude, latitude))
)
```

### 6.3 Uma lista (`geocodificar_lista.py`)

**Pausa e cache:** cada endereço novo é consultado uma vez, com 1,1 s de pausa; os repetidos vêm do dicionário:

```python
PAUSA_SEGUNDOS = 1.1                          # política: no máximo 1 consulta/s

cache = {}       # evita consultar duas vezes o mesmo endereço

if endereco not in cache:
    cache[endereco] = geocodificar(endereco)
    time.sleep(PAUSA_SEGUNDOS)
```

**Nenhuma linha descartada, nada inventado:**

```python
# Sem resultado, a linha entra na camada SEM geometria:
# nada é descartado e nada é inventado.
if status == "ok":
    feicao.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
```

**Erros de conexão viram `status`**, em vez de interromper a lista no meio:

```python
except (HTTPError, URLError, TimeoutError) as erro:
    return None, None, "", f"erro: {erro}"
```

> **Nota: o que conferir no código**
>
> | Trecho | Por que é assim |
> | --- | --- |
> | `encoding="utf-8-sig"` ao abrir o CSV | aceita o CSV salvo pelo Excel, que grava um marcador invisível (BOM) no início |
> | a checagem de `CAMPO_ENDERECO` logo após ler o CSV | se a coluna tiver outro nome, o script avisa quais colunas encontrou, em vez de falhar no meio |
> | `PAUSA_SEGUNDOS = 1.1` | um pouco acima de 1 s, para não esbarrar no limite do serviço |
> | todas as colunas do CSV entram na camada | a camada carrega o que veio da planilha, não só o endereço |

### 6.4 Os arquivos deste exercício

```
modulos/geocodificacao/
├── geocodificacao.md                  ← este roteiro
├── geocodificar_endereco.py           ← Atividade 1: um endereço
└── geocodificar_lista.py              ← Atividade 2: lista de endereços (CSV)

imgs/geocodificacao/                   ← capturas de tela
dados_curso/geocodificacao/            ← dados (baixe do Google Drive)
└── enderecos.csv                      ← 5 locais de João Pessoa
```

---

## 🛡️ 7. Resolução de problemas e dicionário

### ⚠️ Armadilhas comuns

| Sintoma | Causa | Como corrigir |
| :--- | :--- | :--- |
| **ponto no oceano ou em outro continente** | latitude e longitude invertidas | `QgsPointXY(longitude, latitude)` |
| **`status = ok`, mas o ponto está em outro país** | endereço ambíguo ou incompleto | incluir município, estado e país; ler o `local_encontrado` |
| **pontos no Golfo da Guiné (`0, 0`)** | o script inventou coordenadas quando não achou | "sem resultado, sem geometria" |
| **a camada tem menos linhas que o CSV** | linhas sem resultado foram descartadas | manter todas as linhas, sem geometria quando preciso |
| **`HTTP 429` ou bloqueio do serviço** | consultas em rajada, ou muita gente da mesma rede ao mesmo tempo | pausa de 1 s, cache; em turma grande, rodar em duplas |
| **`FileNotFoundError` ao abrir o CSV** | caminho relativo ou errado em `ARQUIVO_CSV` | usar o caminho completo, com `r"..."` no Windows |
| **`O CSV precisa ter a coluna 'endereco'`** | a coluna tem outro nome, ou o separador não é `;` | ajustar `CAMPO_ENDERECO` e `SEPARADOR` |
| **acentos quebrados (`JoÃ£o Pessoa`)** | o CSV não está em UTF-8 | salvar o CSV como UTF-8 |

> **A IA não valida por você.** Ela escreveu um script que roda; quem garante que **os pontos estão no lugar certo** é quem confere o mapa.

### 📖 Dicionário para estudantes

- **Geocodificação:** transformar um endereço em coordenadas. A **reversa** faz o caminho contrário.
- **Nominatim:** o serviço de busca de endereços do OpenStreetMap, gratuito e sem chave.
- **OpenStreetMap (OSM):** mapa colaborativo e livre do mundo, feito por voluntários.
- **EPSG:4326 (WGS 84):** sistema de coordenadas em latitude e longitude, em graus.
- **`User-Agent`:** o "crachá" que identifica a aplicação ao fazer uma consulta na web.
- **Cache:** guardar uma resposta já obtida para não pedir de novo.
- **Camada temporária:** camada que existe só na memória do QGIS e some ao fechar o projeto, se não for salva.
- **CSV:** planilha em texto puro, com colunas separadas por `;` ou `,`.

---

## 🚀 8. Desafios para depois da aula

1. **Seus próprios endereços.** Monte um CSV com 5 lugares que você frequenta e geocodifique. Quantos caíram certo de primeira? O que você teve de acrescentar aos endereços?
2. **Geocodificação reversa.** Peça à IA um script que faça o caminho inverso: clique num ponto do mapa e receba o endereço (o Nominatim tem o serviço `reverse`). Respeite as mesmas regras do serviço.
3. **Distância do erro.** Para o Mercado Central, calcule a distância entre o ponto errado (Valência) e o certo (João Pessoa). Em que SRC essa conta faz sentido?
4. **A precisão do resultado.** O Nominatim também devolve o **tipo** do que achou (prédio, rua, bairro…). Peça à IA para gravar esse campo e use-o para marcar os pontos que caíram só no centro do bairro ou do município.

---

<!-- navegação -->
[⬅️ 📘 Introdução](../introducao/introducao.md) · [🏠 Início](../../README.md) · [🛣️ Duplicação da PB-200 ➡️](../pb200/pb200.md)
