# Dados do minicurso

Os dados **não ficam no git**: estão no **Google Drive**. Baixe tudo de uma vez, descompacte e coloque o conteúdo aqui, em `dados_curso/`, na raiz do repositório:

> 📦 **[`dados_curso-ia.zip`: todos os dados num arquivo só (217 MB)](https://drive.google.com/file/d/1r99KsFYZnMR3KYoU4EH4_qw_IqPgI0Xs/view?usp=sharing)**
>
> 📥 [Pasta `dados_curso` no Google Drive](https://drive.google.com/drive/folders/1rqgB9Fe6D7ApSjebBoSYNgK5c1ZJoipq?usp=sharing), para baixar só uma parte

Tudo nesta pasta, exceto este `README.md`, é ignorado pelo git (veja o `.gitignore`). Os scripts trazem caminhos de exemplo como `/caminho/para/dados_curso/...`: ajuste-os para o local onde você salvou a pasta.

## O que baixar para cada módulo

Se não quiser baixar tudo, pegue só o que o módulo usa:

| Módulo | Dados no Drive |
| --- | --- |
| [Introdução](../modulos/introducao/introducao.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1-V3TuUkvq82hJhzAR0swleoTV5NxNqA8/view?usp=sharing) |
| [Geocodificação](../modulos/geocodificacao/geocodificacao.md) | [`geocodificacao/`](https://drive.google.com/drive/folders/14GFuZCBRNZdKZZ2wXu1tSmewwH_QoTHK?usp=sharing) |
| [PB-200](../modulos/pb200/pb200.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1-V3TuUkvq82hJhzAR0swleoTV5NxNqA8/view?usp=sharing) e, para conferir, [`pb200/resultados/`](https://drive.google.com/drive/folders/1UdU-RlLDg6WNzSVlISo5S0fqhAxp3CwN?usp=sharing) |
| [Grade TOPODATA](../modulos/grade_topodata/grade_topodata.md) | [`grade_topodata/`](https://drive.google.com/drive/folders/12hXG-S2Ym_UGycpbwzryD1s08LkMGTym?usp=sharing), com a folha [`07S375ZN.tif`](https://drive.google.com/file/d/12B5p5EBSmvvN1QbqdFhzvqBNZGvcwv5b/view?usp=sharing) |
| [Perfil da PB-200](../modulos/perfil_pb200/perfil_pb200.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1-V3TuUkvq82hJhzAR0swleoTV5NxNqA8/view?usp=sharing) e, para conferir, [`perfil_pb200/resultados/`](https://drive.google.com/drive/folders/10nChUkuWfTP3IuMDqhtikrnxqeWbyV8M?usp=sharing); a folha [`07S375ZN.tif`](https://drive.google.com/file/d/12B5p5EBSmvvN1QbqdFhzvqBNZGvcwv5b/view?usp=sharing) é o MDE |
| [Acessibilidade a pé à escola](../modulos/acessibilidade_escola/acessibilidade_escola.md) | [`acessibilidade_escola/`](https://drive.google.com/drive/folders/1nLdnMuQQkE2FB9WV3GAf5mBgK3kZnLep?usp=sharing) |
| [Queimadas na Paraíba](../modulos/queimadas_pb/queimadas_pb.md) | [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1-V3TuUkvq82hJhzAR0swleoTV5NxNqA8/view?usp=sharing) |
| [Composição RGB](../modulos/composicao_rgb/composicao_rgb.md) | [`composicao_rgb/`](https://drive.google.com/drive/folders/1_ogFrju31UT5nTKDPsn4z2Ca9ycJuNjS?usp=sharing) |
| [Dados vetoriais](../modulos/dados_vetoriais/dados_vetoriais.md) | [`dados_vetoriais/entrada/`](https://drive.google.com/drive/folders/1Ns_koQT9KXnFHzRcGthi_UMx4-eBi4jk?usp=sharing) e [`minicurso_dados.gpkg`](https://drive.google.com/file/d/1-V3TuUkvq82hJhzAR0swleoTV5NxNqA8/view?usp=sharing) |
| Material de apoio | [`material_apoio/`](https://drive.google.com/drive/folders/10eWQKFH2ejOHlSgyjFZw347EzZQsn_t1?usp=sharing), com o [PyQGIS Developer Cookbook (PDF)](https://drive.google.com/file/d/1AL1bHiJekqPYNMzvHrU6o1qXhqYbUmsZ/view?usp=sharing) e o [Guia OSMnx + QGIS no Windows (PDF)](https://drive.google.com/file/d/1oqxWvQPgbtTPc1CFdSGqSav6C5DlCbWl/view?usp=sharing) |

## Estrutura esperada

```
dados_curso/
├── minicurso_dados.gpkg        ← GeoPackage principal (~544 MB), usado por vários módulos
├── geocodificacao/
│   └── enderecos.csv
├── pb200/
│   └── resultados/             ← saídas do fluxo manual e dos scripts
├── grade_topodata/
│   ├── grade_topodata.geojson
│   └── 07S375ZN.tif            ← folha da PB-200 (67 MB), usada na grade e no perfil
├── perfil_pb200/
│   └── resultados/             ← perfil pronto, para conferir
├── acessibilidade_escola/
│   ├── malha_joao_pessoa_all.gpkg    ← malha a pé (arcos, nodes), os imóveis (imoveis_jp) e o ponto da escola
│   ├── malha_joao_pessoa_drive.gpkg  ← vias de carro, para o desafio de carro (20 MB)
│   └── isocronas_escola.gpkg, imoveis_por_isocrona.gpkg, layout_imoveis_isocronas.pdf ← saídas dos scripts, para conferir
├── composicao_rgb/
│   ├── area_interese.geojson
│   ├── LC08_L1TP_216065_…/     ← bandas Landsat 8 recortadas
│   └── S2A_MSIL2A_…/           ← bandas Sentinel-2 recortadas
├── dados_vetoriais/
│   ├── entrada/                ← os três shapefiles problemáticos
│   └── resultados/             ← criada ao fazer o exercício; não vem no download
└── material_apoio/             ← PyQGIS Developer Cookbook e Guia OSMnx + QGIS no Windows (PDFs)
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

Veja a discussão sobre a Brasil Policônica (EPSG:5880) na [seção 5.3 da prática da PB-200](../modulos/pb200/pb200.md#53-validar-a-ia-não-valida-por-você).
