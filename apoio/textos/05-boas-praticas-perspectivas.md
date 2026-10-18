# Módulo 5 — Boas práticas e perspectivas

⏱ 15 min · [← Prática](../../modulos/pb200/README.md) · [Início](../../README.md)

## Reutilização de scripts

- **Parâmetros no topo.** Caminhos, nomes, CRS e distâncias em constantes (`GPKG`, `RODOVIA`, `CRS_METRICO`...). Ninguém deveria precisar ler o script inteiro para trocar a rodovia.
- **Funções para o que se repete.** Se o mesmo bloco aparece duas vezes, vire função (`def camada(nome): ...`).
- **Saídas intermediárias em memória**, finais em arquivo — de preferência um único GeoPackage.
- **Nomes de arquivos sem espaço e sem acento** (`pb200_uso_solo.gpkg`, e não `Uso do Solo PB 200.shp`).
- **Prints e verificações** ao fim de cada etapa: contagem de feições, CRS, somas de controle.

## Reprodutibilidade

Um resultado é reprodutível quando outra pessoa (ou você daqui a seis meses) consegue obtê-lo de novo. Para isso:

- registre a **versão do QGIS** e a **fonte/data dos dados**;
- deixe o **CRS explícito** em cada etapa, nunca dependa do CRS do projeto;
- versione os scripts com **git** (como neste repositório);
- prefira **GeoPackage** a Shapefile (nomes de campo longos, acentos, um arquivo só);
- salve **estilos** junto com os dados: *Propriedades → Estilo → Salvar como padrão no banco de dados* grava na tabela `layer_styles` do GeoPackage, e por código: `layer.saveStyleToDatabase(...)` / `layer.loadNamedStyle("estilo.qml")`.

## Limitações e uso responsável da IA

- **Alucinação:** a IA inventa métodos, parâmetros e até IDs de algoritmos com total confiança.
- **Versões:** muito código público ainda é do QGIS 2; peça explicitamente QGIS 3.
- **Dados sensíveis:** não cole dados pessoais (CAR com CPF, cadastros) nem informações sigilosas em serviços externos.
- **Autoria e entendimento:** você responde pelo laudo, não a IA. Não entregue código que você não sabe explicar.
- **Dependência:** use a IA para aprender mais rápido, não para deixar de aprender.

## Criando ferramentas personalizadas

Um script pode virar uma ferramenta da Caixa de Ferramentas, com janela, parâmetros, barra de progresso e suporte a lote, herdando de `QgsProcessingAlgorithm`. Exemplo completo: [`05_processing_script_tool.py`](../../modulos/pb200/05_processing_script_tool.py).

```python
class UsoSoloAreaInfluencia(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):      # declara os parâmetros (a "janela")
        self.addParameter(QgsProcessingParameterFeatureSource("LINHAS", "Camada de linhas", ...))
        self.addParameter(QgsProcessingParameterDistance("DISTANCIA", "Distância", defaultValue=3000, ...))
        ...
    def processAlgorithm(self, parameters, context, feedback):   # o fluxo em si
        ...
```

Instalação: Caixa de Ferramentas → ícone Python → **Adicionar script à Caixa de Ferramentas...**

Outros caminhos:

| Caminho | Quando usar |
| --- | --- |
| **Modelador Gráfico** | Fluxos lineares, sem código; pode ser exportado para Python |
| **Script de processamento** | Fluxo reutilizável com parâmetros e interface automática |
| **Plugin** | Interface própria, menus, barras de ferramentas, distribuição no repositório oficial |
| **`qgis_process`** | Rodar algoritmos/modelos em servidores, agendadores, pipelines |

## Ideias para continuar

- **Aptidão agrícola × CAR:** cruzar a camada `aptidao_agricola_pb` (Embrapa) com imóveis do CAR para estimar a área de cada classe por imóvel e discutir precificação/valorização.
- **MDE × sub-bacias (ANA):** unir sub-bacias pelo código, recortar o MDE por bacia e calcular estatísticas zonais (altitude, declividade) em lote.
- **Rasters de cobertura:** repetir a análise de uso do solo com o raster do MapBiomas (`gdal:cliprasterbymasklayer` + `native:rasterlayerzonalstats`).
- **Limpeza de dados com IA:** dados sem projeção, nomes de arquivos e de campos com espaços e acentos → peça à IA um script que padronize nomes e importe tudo para um GeoPackage.
- **Layouts automáticos:** gerar um mapa em PDF por rodovia com `QgsPrintLayout` / Atlas.

## Referências

- [PyQGIS Developer Cookbook — Writing new Processing algorithms](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/processing.html)
- [QGIS User Guide — Processing](https://docs.qgis.org/latest/pt_BR/docs/user_manual/processing/index.html)
- [CSC Training — PyQGIS](https://github.com/csc-training/pyqgis)
