# -*- coding: utf-8 -*-

# Geocodifica uma LISTA de endereços de um CSV com o Nominatim
# (OpenStreetMap) e cria uma camada de pontos com todos os registros,
# inclusive os não encontrados. Rode no Editor do Console Python do QGIS.

import csv
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface


# --------------------------------------------------
# 1. Configurações (ajuste aqui)
# --------------------------------------------------

ARQUIVO_CSV = Path("/caminho/para/dados_curso/geocodificacao/enderecos.csv")  # caminho completo do CSV
CAMPO_ENDERECO = "endereco"                   # coluna com o endereço
SEPARADOR = ";"                               # ";" ou ","
PAUSA_SEGUNDOS = 1.1                          # política: no máximo 1 consulta/s


def geocodificar(endereco):
    """Devolve (lat, lon, descrição, status) para um endereço."""
    url = "https://nominatim.openstreetmap.org/search?" + urlencode({
        "q": endereco,
        "format": "jsonv2",
        "limit": 1,
    })
    requisicao = Request(
        url,
        headers={"User-Agent": "minicurso-qgis-python-ia/1.0"}
    )
    try:
        with urlopen(requisicao, timeout=30) as resposta:
            resultados = json.loads(resposta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as erro:
        return None, None, "", f"erro: {erro}"

    if not resultados:
        return None, None, "", "não encontrado"

    r = resultados[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"], "ok"


# --------------------------------------------------
# 2. Leitura do CSV
# --------------------------------------------------

with open(ARQUIVO_CSV, encoding="utf-8-sig", newline="") as arquivo:
    linhas = list(csv.DictReader(arquivo, delimiter=SEPARADOR))

if not linhas or CAMPO_ENDERECO not in linhas[0]:
    raise ValueError(
        f"O CSV precisa ter a coluna '{CAMPO_ENDERECO}'. "
        f"Colunas encontradas: {list(linhas[0]) if linhas else 'nenhuma'}"
    )


# --------------------------------------------------
# 3. Camada: colunas do CSV + resultado da geocodificação
# --------------------------------------------------

camada = QgsVectorLayer(
    "Point?crs=EPSG:4326", "enderecos_geocodificados", "memory"
)
campos_csv = list(linhas[0])
camada.dataProvider().addAttributes(
    [QgsField(nome, QVariant.String) for nome in campos_csv]
    + [
        QgsField("local_encontrado", QVariant.String),
        QgsField("latitude", QVariant.Double),
        QgsField("longitude", QVariant.Double),
        QgsField("status", QVariant.String),
    ]
)
camada.updateFields()


# --------------------------------------------------
# 4. Geocodifica linha a linha
# --------------------------------------------------

cache = {}       # evita consultar duas vezes o mesmo endereço
feicoes = []

for indice, linha in enumerate(linhas, start=1):
    endereco = (linha[CAMPO_ENDERECO] or "").strip()

    if endereco not in cache:
        cache[endereco] = geocodificar(endereco)
        time.sleep(PAUSA_SEGUNDOS)

    lat, lon, descricao, status = cache[endereco]
    print(f"{indice}/{len(linhas)}  {status:15}  {endereco}")

    feicao = QgsFeature(camada.fields())

    # Sem resultado, a linha entra na camada SEM geometria:
    # nada é descartado e nada é inventado.
    if status == "ok":
        feicao.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))

    feicao.setAttributes(
        [linha[nome] for nome in campos_csv]
        + [descricao, lat, lon, status]
    )
    feicoes.append(feicao)

camada.dataProvider().addFeatures(feicoes)
camada.updateExtents()


# --------------------------------------------------
# 5. Adiciona ao projeto e resume
# --------------------------------------------------

QgsProject.instance().addMapLayer(camada)
iface.setActiveLayer(camada)
iface.zoomToActiveLayer()

encontrados = sum(1 for f in feicoes if f["status"] == "ok")
print(
    f"\n{encontrados} de {len(feicoes)} endereços geocodificados. "
    "Confira os demais na tabela de atributos (campo status)."
)
