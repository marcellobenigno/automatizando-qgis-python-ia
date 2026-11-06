# Dados do minicurso

Os dados **não ficam no git**: estão numa pasta do **Google Drive**. Baixe a pasta inteira e coloque o conteúdo aqui, em `dados_curso/`, na raiz do repositório:

> 📥 **[Pasta `dados_curso` no Google Drive](https://drive.google.com/drive/folders/1xQdt_9qNkrSeVNFKqvhs9dpuh6m28r5D?usp=sharing)**

Tudo nesta pasta, exceto este `README.md`, é ignorado pelo git (veja o `.gitignore`). Os scripts trazem caminhos de exemplo como `/caminho/para/dados_curso/...`: ajuste-os para o local onde você salvou a pasta.

## O que baixar para cada módulo

Se não quiser baixar tudo, pegue só o que o módulo usa:

| Módulo | Dados no Drive |
| --- | --- |
| [Introdução](../modulos/introducao/introducao.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1Ot_0LSC1BQBNH3qXEsKofkvD9VmXG1aj/view?usp=sharing) |
| [Geocodificação](../modulos/geocodificacao/geocodificacao.md) | [`geocodificacao/`](https://drive.google.com/drive/folders/18i4zbnI13SSQs2HGyAWLPC6wgMT_rkWu?usp=sharing) |
| [PB-200](../modulos/pb200/pb200.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1Ot_0LSC1BQBNH3qXEsKofkvD9VmXG1aj/view?usp=sharing) e, para conferir, [`pb200/resultados/`](https://drive.google.com/drive/folders/11X3sCNL6ymDI1CL7LbbbSismPx5TPXxt?usp=sharing) |
| [Grade TOPODATA](../modulos/grade_topodata/grade_topodata.md) | [`grade_topodata/`](https://drive.google.com/drive/folders/1lN2DfblMS2tecaPPsPpQB8tRMuXIdipx?usp=sharing) |
| [Perfil da PB-200](../modulos/perfil_pb200/perfil_pb200.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1Ot_0LSC1BQBNH3qXEsKofkvD9VmXG1aj/view?usp=sharing) e, para conferir, [`perfil_pb200/resultados/`](https://drive.google.com/drive/folders/1NLJYONJGQ9ubQ0QR_8fm6kmg_s5MlcnS?usp=sharing) |
| [Alcance a partir do IFPB](../modulos/alcance_ifpb/alcance_ifpb.md) | [`alcance_ifpb/`](https://drive.google.com/drive/folders/1kP42mKzmooOTogjF7fJj-33B4WBz8YCH?usp=sharing) |
| [Queimadas na Paraíba](../modulos/queimadas_pb/queimadas_pb.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1Ot_0LSC1BQBNH3qXEsKofkvD9VmXG1aj/view?usp=sharing) |
| [Composição RGB](../modulos/composicao_rgb/composicao_rgb.md) | [`composicao_rgb/`](https://drive.google.com/drive/folders/1pVUuxhQ8YzLIec0H85iM-ArlrpaV11Gi?usp=sharing) |
| [Dados vetoriais](../modulos/dados_vetoriais/dados_vetoriais.md) | [`dados_vetoriais/entrada/`](https://drive.google.com/drive/folders/1cnUG8amunnNd1k4qZn-c8ynEAWU4yG6x?usp=sharing) e [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1Ot_0LSC1BQBNH3qXEsKofkvD9VmXG1aj/view?usp=sharing) |
| Material de apoio | [`material_apoio/`](https://drive.google.com/drive/folders/1WU_JFqm8Rk0Q097rexIZ_iSRzbt2Yl_b?usp=sharing), com o [PyQGIS Developer Cookbook (PDF)](https://drive.google.com/file/d/1T2gwL05yXmM1XF83YgRJPAKo58ta2haX/view?usp=sharing) e o *Guia OSMnx + QGIS no Windows* (PDF) |

## Estrutura esperada

```
dados_curso/
├── minicurso_dados.gpkg        ← GeoPackage principal (~548 MB), usado por vários módulos
├── geocodificacao/
│   └── enderecos.csv
├── pb200/
│   └── resultados/             ← saídas do fluxo manual e dos scripts
├── grade_topodata/
│   └── grade_topodata.geojson
├── perfil_pb200/
│   └── resultados/             ← perfil pronto, para conferir
├── alcance_ifpb/
│   ├── malha_joao_pessoa_all.gpkg  ← malha do OSM baixada uma vez com o OSMnx (27 MB)
│   └── resultados/             ← alcance a pé e de carro
├── composicao_rgb/
│   ├── area_interese.geojson
│   ├── LC08_L1TP_216065_…/     ← bandas Landsat 8 recortadas
│   ├── S2A_MSIL2A_…/           ← bandas Sentinel-2 recortadas
│   └── cenas_completas/        ← cenas originais, sem recorte (1,7 GB, opcional)
├── dados_vetoriais/
│   ├── entrada/                ← os três shapefiles problemáticos
│   └── resultados/
└── material_apoio/             ← PyQGIS Developer Cookbook e Guia OSMnx + QGIS no Windows (PDFs), arquivos de teste
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
| `bdqueimadas_2026-01-01_2026-10-30` | Point | 2.445 | Focos de queimadas do BDQueimadas (INPE), satélite NOAA-20: `DataHora` (UTC), `Municipio`, `Bioma`, `FRP`, `RiscoFogo`, `DiaSemChuva`, `Precipitacao` (`-999` = sem dado) |
| `layer_styles` | tabela | — | Estilos salvos de cada camada (carregados automaticamente pelo QGIS) |

#### Classes de uso e ocupação do solo (`descricao`)

Formação Florestal, Formação Savânica, Formação Campestre, Mangue, Apicum, Campo Alagado e Área Pantanosa, Pastagem, Mosaico de Usos, Cana de Açúcar, Outras Lavouras Temporárias, Outras Lavouras Perenes, Silvicultura, Área Urbanizada, Mineração, Aquicultura, Afloramento Rochoso, Praia Duna e Areal, Outras Áreas não Vegetadas, Rio, Lago e Oceano.

### CRS para cálculos

As camadas estão em coordenadas geográficas (graus). Para buffers e áreas, reprojete para um sistema métrico:

| CRS | Uso |
| --- | --- |
| EPSG:31984 — SIRGAS 2000 / UTM 24S | Oeste e centro da Paraíba (inclui a PB-200) |
| EPSG:31985 — SIRGAS 2000 / UTM 25S | Faixa litorânea (a leste de 36° W) |

Veja a discussão sobre a Brasil Policônica (EPSG:5880) na [seção 6.4 da prática da PB-200](../modulos/pb200/pb200.md#64-validar-a-ia-não-valida-por-você).
