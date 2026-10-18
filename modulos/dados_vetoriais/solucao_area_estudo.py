"""
Exercício 1 — Arrumando a casa: consolida e padroniza as áreas de estudo.

Junta os três shapefiles de dados_curso/dados_vetoriais/entrada/ em uma única camada "area_estudo",
no GeoPackage areas_especies_sertao.gpkg, com:
    descricao   texto padronizado ("Área prioritária 1")
    area_ha     área da geometria em hectares (EPSG:31984)
    municipios  municípios intersectados, separados por vírgula

Rode no Editor do Console Python do QGIS (Ctrl+Alt+P → Mostrar editor).
Ajuste PASTA e GPKG_DADOS antes de executar.
"""

from pathlib import Path

import processing
from qgis.core import QgsProject, QgsVectorLayer

# ---------------------------------------------------------------------------
# Parâmetros
# ---------------------------------------------------------------------------
PASTA = Path("/caminho/para/dados_curso/dados_vetoriais")
GPKG_DADOS = "/caminho/para/dados_curso/minicurso_dados.gpkg"   # camada municipios (IBGE)

ENTRADA = PASTA / "entrada"
GPKG_SAIDA = PASTA / "resultados" / "areas_especies_sertao.gpkg"
CAMADA_SAIDA = "area_estudo"
CRS_DESTINO = "EPSG:31984"   # SIRGAS 2000 / UTM 24S

# De-para: para cada arquivo, o campo que vira "descricao" e o CRS a assumir
# quando o arquivo chega sem .prj. O CRS ausente NÃO é adivinhado: foi
# deduzido das coordenadas (E ≈ 640 000 m, N ≈ 9 220 000 m → UTM 24S).
CAMADAS = {
    "ÁREAS DE ESTUDO.shp":     {"descricao": "descriçã", "crs_se_ausente": None},
    "ÁREAS DE ESTUDO (2).shp": {"descricao": "descriçã", "crs_se_ausente": None},
    "area_estuto_josé.shp":    {"descricao": "desc",     "crs_se_ausente": "EPSG:31984"},
}

# Expressões do esquema final (dicionário de dados)
EXP_AREA_HA = "round(area($geometry) / 10000, 2)"   # área plana, em UTM
EXP_MUNICIPIOS = (
    "array_to_string(array_sort("
    "overlay_intersects('municipios', \"nome\")), ', ')"
)


def capitalizar(campo):
    """Expressão QGIS: ' ÁREA 3 ' → 'Área 3'."""
    texto = f'trim("{campo}")'
    return f"upper(left({texto}, 1)) || lower(substr({texto}, 2))"


def campo(nome, tipo, tamanho, precisao, expressao):
    """Uma linha do mapeamento do native:refactorfields."""
    return {"name": nome, "type": tipo, "length": tamanho,
            "precision": precisao, "expression": expressao}


TEXTO, DECIMAL = 10, 6   # QVariant.String, QVariant.Double

# ---------------------------------------------------------------------------
# 1. Municípios (precisam estar no projeto para o overlay_intersects)
# ---------------------------------------------------------------------------
projeto = QgsProject.instance()
if not projeto.mapLayersByName("municipios"):
    municipios = QgsVectorLayer(f"{GPKG_DADOS}|layername=municipios",
                                "municipios", "ogr")
    projeto.addMapLayer(municipios)

# ---------------------------------------------------------------------------
# 2. Cada camada: CRS correto → só o campo descricao, já padronizado
# ---------------------------------------------------------------------------
padronizadas = []
for arquivo, cfg in CAMADAS.items():
    camada = QgsVectorLayer(str(ENTRADA / arquivo), arquivo, "ogr")
    assert camada.isValid(), f"Não abriu: {arquivo}"

    if not camada.crs().isValid():
        print(f"[CRS] {arquivo}: sem .prj → atribuindo {cfg['crs_se_ausente']}")
        camada = processing.run("native:assignprojection", {
            "INPUT": camada, "CRS": cfg["crs_se_ausente"],
            "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

    camada = processing.run("native:reprojectlayer", {
        "INPUT": camada, "TARGET_CRS": CRS_DESTINO,
        "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

    camada = processing.run("native:refactorfields", {
        "INPUT": camada,
        "FIELDS_MAPPING": [
            campo("descricao", TEXTO, 100, 0, capitalizar(cfg["descricao"])),
        ],
        "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

    print(f"[OK]  {arquivo}: {camada.featureCount()} feições")
    padronizadas.append(camada)

# ---------------------------------------------------------------------------
# 3. Juntar, corrigir geometrias e descartar duplicatas
# ---------------------------------------------------------------------------
unidas = processing.run("native:mergevectorlayers", {
    "LAYERS": padronizadas, "CRS": CRS_DESTINO,
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

unidas = processing.run("native:fixgeometries", {
    "INPUT": unidas, "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

res = processing.run("native:deleteduplicategeometries", {
    "INPUT": unidas, "OUTPUT": "TEMPORARY_OUTPUT"})
print(f"[DUP] {res['DUPLICATE_COUNT']} duplicata(s) removida(s), "
      f"{res['RETAINED_COUNT']} feição(ões) mantida(s)")

# ---------------------------------------------------------------------------
# 4. Esquema final: só os 3 campos, com área e municípios calculados
# ---------------------------------------------------------------------------
GPKG_SAIDA.parent.mkdir(parents=True, exist_ok=True)
final = processing.run("native:refactorfields", {
    "INPUT": res["OUTPUT"],
    "FIELDS_MAPPING": [
        campo("descricao", TEXTO, 100, 0, '"descricao"'),
        campo("area_ha", DECIMAL, 12, 2, EXP_AREA_HA),
        campo("municipios", TEXTO, 254, 0, EXP_MUNICIPIOS),
    ],
    "OUTPUT": f"ogr:dbname='{GPKG_SAIDA}' table=\"{CAMADA_SAIDA}\" (geom)",
})["OUTPUT"]

# ---------------------------------------------------------------------------
# 5. Conferir
# ---------------------------------------------------------------------------
area_estudo = QgsVectorLayer(final, CAMADA_SAIDA, "ogr")
print(f"\n{CAMADA_SAIDA}: {area_estudo.featureCount()} feições, "
      f"{area_estudo.crs().authid()}, campos "
      f"{[f.name() for f in area_estudo.fields()]}")
for f in area_estudo.getFeatures():
    print(f"  {f['descricao']:<20} {f['area_ha']:>9.2f} ha  {f['municipios']}")
projeto.addMapLayer(area_estudo)
