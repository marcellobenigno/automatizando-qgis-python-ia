"""
Módulo 4 — Automação em lote: buffer de 3 km para várias rodovias.

O mesmo fluxo que seria repetido N vezes na interface vira um laço `for`.
"""
from pathlib import Path

import processing
from qgis.core import QgsVectorLayer

GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"
PASTA_SAIDA = "/caminho/para/dados_curso/pb200/resultados"
RODOVIAS = ["PB-200", "PB-228", "PB-238", "PB-250"]
DISTANCIA = 3000  # metros


def crs_utm(camada):
    """CRS SIRGAS 2000 / UTM (hemisfério sul) do fuso onde está o centro da camada.

    A camada precisa estar em graus (EPSG:4326). Fuso 24 -> EPSG:31984,
    fuso 25 -> EPSG:31985 (a Paraíba tem municípios nos dois).
    """
    longitude = camada.extent().center().x()
    fuso = int((longitude + 180) // 6) + 1
    return f"EPSG:{31960 + fuso}"


malha = QgsVectorLayer(f"{GPKG}|layername=malha_viaria", "malha_viaria", "ogr")
saida = Path(PASTA_SAIDA)
saida.mkdir(parents=True, exist_ok=True)

resumo = []
for rodovia in RODOVIAS:
    trechos = processing.run("native:extractbyattribute", {
        "INPUT": malha, "FIELD": "rodovia_nome", "OPERATOR": 0,
        "VALUE": rodovia, "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
    if trechos.featureCount() == 0:
        print(f"{rodovia}: não encontrada, pulando")
        continue

    crs = crs_utm(trechos)
    trechos_m = processing.run("native:reprojectlayer", {
        "INPUT": trechos, "TARGET_CRS": crs,
        "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]

    arquivo = saida / f"{rodovia.lower().replace('-', '')}_buffer_{DISTANCIA // 1000}km.gpkg"
    buffer = processing.run("native:buffer", {
        "INPUT": trechos_m, "DISTANCE": DISTANCIA, "DISSOLVE": True,
        "OUTPUT": str(arquivo)})["OUTPUT"]

    area_km2 = sum(f.geometry().area() for f in
                   QgsVectorLayer(buffer, "", "ogr").getFeatures()) / 1e6
    resumo.append((rodovia, trechos.featureCount(), crs, area_km2))
    print(f"{rodovia}: {trechos.featureCount()} trechos, {crs}, buffer = {area_km2:.1f} km²")

print("\nRodovia   Trechos  CRS         Área do buffer (km²)")
for rodovia, n, crs, area in resumo:
    print(f"{rodovia:<9} {n:>7}  {crs:<10}  {area:>20.1f}")
