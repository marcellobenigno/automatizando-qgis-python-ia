# Dados do minicurso

Os dados **não ficam no git**: estão numa pasta do **Google Drive**. Baixe a pasta inteira e coloque o conteúdo aqui, em `dados_curso/`, na raiz do repositório:

> 📥 **<link do Google Drive — a definir>**

Tudo nesta pasta, exceto este `README.md`, é ignorado pelo git (veja o `.gitignore`). Os scripts trazem caminhos de exemplo como `/caminho/para/dados_curso/...`: ajuste-os para o local onde você salvou a pasta.

## Estrutura esperada

```
dados_curso/
├── minicurso_dados.gpkg        ← GeoPackage principal (~570 MB), usado por vários módulos
├── geocodificacao/
│   └── enderecos.csv
├── pb200/
│   └── resultados/             ← saídas do fluxo manual e dos scripts
├── grade_topodata/
│   └── grade_topodata.geojson
├── composicao_rgb/
│   ├── area_interese.geojson
│   ├── LC08_L1TP_216065_…/     ← bandas Landsat 8 recortadas
│   ├── S2A_MSIL2A_…/           ← bandas Sentinel-2 recortadas
│   └── cenas_completas/        ← cenas originais, sem recorte (1,7 GB, opcional)
├── dados_vetoriais/
│   ├── entrada/                ← os três shapefiles problemáticos
│   └── resultados/
└── material_apoio/             ← PyQGIS Developer Cookbook (PDF) e arquivos de teste
```

## O GeoPackage `minicurso_dados.gpkg`

### Camadas

Todas em **WGS 84 (EPSG:4326)**.

| Camada | Geometria | Feições | Campos principais |
| --- | --- | --- | --- |
| `limite_pb` | MultiPolygon | 1 | Limite estadual da Paraíba |
| `estados_ne` | MultiPolygon | 9 | Estados do Nordeste |
| `municipios` | MultiPolygon | 223 | `nome`, `cod_ibge_m`, `microregiao`, `mesoregiao`, `populacao_rural`, `populacao_urbana`, `populacao_total` |
| `malha_viaria` | MultiLineString | 674 | `rodovia_nome` (ex.: `PB-200`), `codigo`, `descricao`, `jurisdicao`, `extensao`, `km_inicial`, `km_final`, `sit_fisica` |
| `uso_ocupacao_solo` | MultiPolygon | ~1,06 milhão | `val`, `descricao` (classe), `cor` |
| `aptidao_agricola_pb` | MultiPolygon | 3.789 | `descricao`, `val`, `cod_ibge_m` |
| `layer_styles` | tabela | — | Estilos salvos de cada camada (carregados automaticamente pelo QGIS) |

#### Classes de uso e ocupação do solo (`descricao`)

Formação Florestal, Formação Savânica, Formação Campestre, Mangue, Apicum, Campo Alagado e Área Pantanosa, Pastagem, Mosaico de Usos, Cana de Açúcar, Outras Lavouras Temporárias, Outras Lavouras Perenes, Silvicultura, Área Urbanizada, Mineração, Aquicultura, Afloramento Rochoso, Praia Duna e Areal, Outras Áreas não Vegetadas, Rio, Lago e Oceano.

### CRS para cálculos

As camadas estão em coordenadas geográficas (graus). Para buffers e áreas, reprojete para um sistema métrico:

| CRS | Uso |
| --- | --- |
| EPSG:31984 — SIRGAS 2000 / UTM 24S | Oeste e centro da Paraíba (inclui a PB-200) |
| EPSG:31985 — SIRGAS 2000 / UTM 25S | Faixa litorânea (a leste de 36° W) |

Veja a discussão sobre a Brasil Policônica (EPSG:5880) na [Parte 3 da prática](../modulos/pb200/README.md#35-validar--a-ia-não-valida-por-você).
