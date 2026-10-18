"""
Módulo 1 — Explorando o Processing Framework pelo Console Python.

Lista os provedores e algoritmos disponíveis e mostra a ajuda de um algoritmo.
Cole linha a linha no Console Python (Ctrl+Alt+P) ou rode pelo Editor.
"""
import processing
from qgis.core import QgsApplication

registro = QgsApplication.processingRegistry()

# Provedores: native (C++), qgis (Python), gdal, grass, saga...
for prov in registro.providers():
    print(f"{prov.id():<10} {prov.name():<30} {len(prov.algorithms())} algoritmos")

# Algoritmos cujo nome contém "buffer"
for alg in registro.algorithms():
    if "buffer" in alg.id().lower():
        print(alg.id(), "->", alg.displayName())

# Parâmetros, valores aceitos e saídas de um algoritmo
processing.algorithmHelp("native:buffer")
