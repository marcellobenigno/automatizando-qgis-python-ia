"""
Módulo 2 — Fundamentos de PyQGIS: camadas, feições e processing.run.

Rode pelo Editor do Console Python do QGIS depois de ajustar GPKG.
"""
import processing
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeatureRequest,
                       QgsProject, QgsVectorLayer)

GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"

# 1. Abrir uma camada de um GeoPackage --------------------------------------
municipios = QgsVectorLayer(f"{GPKG}|layername=municipios", "municipios", "ogr")
print("Válida?", municipios.isValid())
print("CRS:", municipios.crs().authid(), "-", municipios.crs().description())
print("Feições:", municipios.featureCount())
print("Campos:", [campo.name() for campo in municipios.fields()])

# 2. Percorrer feições -------------------------------------------------------
for f in municipios.getFeatures(QgsFeatureRequest().setLimit(5)):
    print(f["nome"], f["populacao_total"])

# 3. Filtrar com expressão (igual à "Seleção por expressão" da interface) ------
pedido = QgsFeatureRequest().setFilterExpression('"populacao_total" > 100000')
grandes = [f["nome"] for f in municipios.getFeatures(pedido)]
print("Municípios com mais de 100 mil hab.:", grandes)

# 4. Executar um algoritmo ---------------------------------------------------
malha = QgsVectorLayer(f"{GPKG}|layername=malha_viaria", "malha_viaria", "ogr")
resultado = processing.run("native:extractbyexpression", {
    "INPUT": malha,
    "EXPRESSION": "\"rodovia_nome\" = 'PB-200'",
    "OUTPUT": "TEMPORARY_OUTPUT",
})
pb200 = resultado["OUTPUT"]  # processing.run devolve um dicionário
print("Trechos da PB-200:", pb200.featureCount())

# 5. Encadear algoritmos: a saída de um é a entrada do próximo ----------------
pb200_m = processing.run("native:reprojectlayer", {
    "INPUT": pb200,
    "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:31984"),
    "OUTPUT": "TEMPORARY_OUTPUT",
})["OUTPUT"]
extensao_km = sum(f.geometry().length() for f in pb200_m.getFeatures()) / 1000
print(f"Extensão da PB-200: {extensao_km:.1f} km")

# 6. Adicionar ao mapa --------------------------------------------------------
pb200_m.setName("pb200_utm24s")
QgsProject.instance().addMapLayer(pb200_m)
# Atalho: processing.runAndLoadResults(...) executa e já carrega a saída.
