"""
Exercício 1 — Diagnóstico: inventário de todos os shapefiles de uma pasta.

Para cada arquivo, mostra CRS, número de feições, campos (com tipo) e o nome
padronizado sugerido (minúsculo, sem acento, separado por underline). Serve
para enxergar o problema antes de corrigir — e para colar no prompt da IA.

Rode no Editor do Console Python do QGIS. Ajuste PASTA antes de executar.
"""

import re
import unicodedata
from pathlib import Path

from qgis.core import QgsVectorLayer

PASTA = Path("/caminho/para/dados_curso/dados_vetoriais/entrada")


def snake_case(nome):
    """'ÁREA (ha)' → 'area_ha';  'Município' → 'municipio'."""
    sem_acento = (unicodedata.normalize("NFKD", nome)
                  .encode("ascii", "ignore").decode("ascii"))
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")


for shp in sorted(PASTA.glob("*.shp")):
    camada = QgsVectorLayer(str(shp), shp.stem, "ogr")
    crs = camada.crs().authid() if camada.crs().isValid() else "?? SEM CRS"
    print(f"\n=== {shp.name}  →  sugestão: {snake_case(shp.stem)}.shp")
    print(f"    CRS: {crs} | feições: {camada.featureCount()} | "
          f"extensão: {camada.extent().toString(2)}")
    for fld in camada.fields():
        valores = camada.uniqueValues(camada.fields().indexOf(fld.name()))
        preenchidos = [v for v in valores if v not in (None, "") and v == v]
        print(f"    {fld.name():<12} {fld.typeName():<8} → "
              f"{snake_case(fld.name()):<12} valores: {preenchidos or 'VAZIO'}")
