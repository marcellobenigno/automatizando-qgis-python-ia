# -*- coding: utf-8 -*-
"""
Alcance a partir do IFPB Campus João Pessoa com o plugin OSMnx Routing & Isochrones.

Até onde se chega em 10 minutos, a pé e de carro, pelas ruas?

O script faz pelo Python o mesmo que os painéis do plugin fazem com cliques:
  1. Isócronas a pé de 5, 10 e 15 minutos (malha "all") e a comparação da
     de 10 minutos com o círculo de 800 m
  2. Isócronas de carro de 5 e 10 minutos (malha "drive"), saindo do campus
     e chegando a ele: a diferença entre as duas é a mão única
  3. A rota de carro campus → orla de Tambaú e a volta, respeitando e
     ignorando a mão única
  4. A conferência das vias alcançadas a pé com a "Área de serviço" nativa
     do QGIS

As malhas NÃO são baixadas aqui: vêm dos GeoPackages salvos uma única vez
(a "all" com o OSMnx; a "drive" com o algoritmo "1. Baixar malha viária"
do plugin). Daqui em diante, tudo roda sem internet.

Requisitos: o plugin OSMnx Routing & Isochrones instalado e ativo
(https://marcellobenigno.github.io/osmnx-routing-isochrones/pt-br/).

Como usar: abra no Editor do Console Python do QGIS, ajuste PASTA e clique
em "Executar script".
"""
import math

import processing
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
)

# --------------------------------------------------------------------------
# Parâmetros: altere aqui
# --------------------------------------------------------------------------
PASTA = "/caminho/para/dados_curso/alcance_ifpb/"
MALHA_ALL = PASTA + "malha_joao_pessoa_all.gpkg"      # todas as vias: para andar
MALHA_DRIVE = PASTA + "malha_joao_pessoa_drive.gpkg"  # só vias de carro

CAMPUS = "-34.87354,-7.13574 [EPSG:4326]"  # centro do terreno do campus no OSM
PRAIA = "-34.8237,-7.1154 [EPSG:4326]"     # orla de Tambaú
CRS_METRICO = QgsCoordinateReferenceSystem("EPSG:31985")  # SIRGAS 2000 / UTM 25S

# Os parâmetros de lista do plugin recebem a posição da opção (0, 1, …)
CARRO, A_PE = 0, 1
SAINDO, CHEGANDO = 0, 1
VELOCIDADE_A_PE = 4.8  # km/h: 10 minutos = 800 m


def isocronas(malha, perfil, minutos, nome, sentido=SAINDO):
    """Roda o algoritmo de isócronas do plugin e carrega o resultado no mapa."""
    res = processing.runAndLoadResults("osmnx_routing:isochrones", {
        "NETWORK": malha, "PROFILE": perfil, "POINT": CAMPUS,
        "DIRECTION": sentido, "MINUTES": minutos,
        "WALK_SPEED": VELOCIDADE_A_PE,
        "OUTPUT": "TEMPORARY_OUTPUT", "ROADS": "TEMPORARY_OUTPUT"})
    poligonos = QgsProject.instance().mapLayer(res["OUTPUT"])
    vias = QgsProject.instance().mapLayer(res["ROADS"])
    poligonos.setName(nome)
    vias.setName(nome + " (vias)")
    faixas = sorted(([f["minutes"], f["area_km2"], f["roads_km"]]
                     for f in poligonos.getFeatures()))
    return faixas, vias


def rota(origem, destino, ignorar_mao_unica):
    """Menor caminho de carro pela distância; devolve km, minutos e contramão."""
    res = processing.run("osmnx_routing:shortest_path", {
        "NETWORK": MALHA_DRIVE, "PROFILE": CARRO, "CRITERION": 0,
        "ORIGIN": origem, "DESTINATION": destino,
        "IGNORE_ONEWAY": ignorar_mao_unica, "OUTPUT": "TEMPORARY_OUTPUT"})
    return res["DISTANCE_KM"], res["TIME_MIN"], res["WRONG_WAY_M"]


def km_de_vias(camada):
    """
    Comprimento das vias, contando cada rua uma vez só.

    Mede a área de uma faixa de 1 m em volta das linhas (em metros, no SRC
    métrico) e divide pela largura: ida e volta de uma rua de mão dupla,
    sobrepostas, ocupam a mesma faixa.
    """
    para_utm = QgsCoordinateTransform(camada.crs(), CRS_METRICO,
                                      QgsProject.instance())
    faixas = []
    for f in camada.getFeatures():
        g = QgsGeometry(f.geometry())
        g.transform(para_utm)
        faixas.append(g.buffer(0.5, 4))
    return QgsGeometry.unaryUnion(faixas).area() / 1000


# --------------------------------------------------------------------------
# 1. A pé: 5, 10 e 15 minutos
# --------------------------------------------------------------------------
print("\n[1] A pé, malha 'all', saindo do campus")
a_pe, _ = isocronas(MALHA_ALL, A_PE, "5, 10, 15", "A pé: 5, 10 e 15 min")
for minutos, area, km in a_pe:
    print(f"      {minutos:4.0f} min: {area:5.2f} km² | {km:5.1f} km de vias")

raio_km = VELOCIDADE_A_PE * 10 / 60
circulo = math.pi * raio_km ** 2
area_10 = next(area for minutos, area, _ in a_pe if minutos == 10)
print(f"      10 min a {VELOCIDADE_A_PE} km/h = {raio_km * 1000:.0f} m: "
      f"isócrona {area_10:.2f} km² = {100 * area_10 / circulo:.0f}% "
      f"do círculo de {raio_km * 1000:.0f} m ({circulo:.2f} km²)")

# --------------------------------------------------------------------------
# 2. De carro: saindo × chegando
# --------------------------------------------------------------------------
print("\n[2] De carro, malha 'drive'")
saindo, _ = isocronas(MALHA_DRIVE, CARRO, "5, 10", "Carro: saindo", SAINDO)
chegando, _ = isocronas(MALHA_DRIVE, CARRO, "5, 10", "Carro: chegando",
                        CHEGANDO)
for (minutos, a_s, _), (_, a_c, _) in zip(saindo, chegando):
    print(f"      {minutos:4.0f} min: saindo {a_s:5.1f} km² | "
          f"chegando {a_c:5.1f} km² ({100 * (a_c - a_s) / a_s:+.0f}%)")

# --------------------------------------------------------------------------
# 3. Rota até a praia, ida e volta, com e sem a mão única
# --------------------------------------------------------------------------
print("\n[3] Rota de carro: campus ↔ orla de Tambaú (menor distância)")
for trecho, origem, destino in (("ida  ", CAMPUS, PRAIA),
                                ("volta", PRAIA, CAMPUS)):
    km, minutos, _ = rota(origem, destino, False)
    km_livre, _, contramao = rota(origem, destino, True)
    print(f"      {trecho}: {km:.2f} km, {minutos:.1f} min | ignorando a mão "
          f"única: {km_livre:.2f} km, com {contramao / 1000:.2f} km na contramão")

# --------------------------------------------------------------------------
# 4. Conferência com a Área de serviço nativa do QGIS (800 m a pé)
# --------------------------------------------------------------------------
print("\n[4] Conferência: plugin × Área de serviço do QGIS (a pé, 800 m)")
_, vias_plugin = isocronas(MALHA_ALL, A_PE, "10", "A pé: 10 min")
arcos = QgsVectorLayer(MALHA_ALL + "|layername=arcos", "arcos", "ogr")
arcos_utm = processing.run("native:reprojectlayer", {
    "INPUT": arcos, "TARGET_CRS": CRS_METRICO,
    "OUTPUT": "TEMPORARY_OUTPUT"})["OUTPUT"]
nativo = processing.run("native:serviceareafrompoint", {
    "INPUT": arcos_utm, "STRATEGY": 0,      # 0 = mais curto (distância)
    "DEFAULT_DIRECTION": 2,                 # 2 = ambas as direções (a pé)
    "START_POINT": CAMPUS, "TRAVEL_COST2": 800,
    "OUTPUT_LINES": "TEMPORARY_OUTPUT"})["OUTPUT_LINES"]
km_plugin, km_nativo = km_de_vias(vias_plugin), km_de_vias(nativo)
roads_km = next(km for minutos, _, km in a_pe if minutos == 10)
print(f"      plugin: {km_plugin:.1f} km × QGIS nativo: {km_nativo:.1f} km "
      f"({100 * (km_plugin - km_nativo) / km_nativo:+.1f}%)")
print(f"      campo roads_km do plugin: {roads_km:.1f} km "
      f"({100 * (roads_km - km_plugin) / km_plugin:+.0f}% sobre a faixa de 1 m)")
