# -*- coding: utf-8 -*-

# Geocodifica UM endereço com o Nominatim (OpenStreetMap) e cria uma
# camada de pontos no projeto. Rode no Editor do Console Python do QGIS.

import json
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
# 1. Endereço (altere aqui)
# --------------------------------------------------

endereco = "Universidade Federal da Paraíba, João Pessoa, Brasil"


# --------------------------------------------------
# 2. Consulta ao Nominatim
# --------------------------------------------------

url = "https://nominatim.openstreetmap.org/search?" + urlencode({
    "q": endereco,
    "format": "jsonv2",
    "limit": 1,
})

# A política do Nominatim exige identificar a aplicação.
requisicao = Request(
    url,
    headers={"User-Agent": "minicurso-qgis-python-ia/1.0"}
)

with urlopen(requisicao, timeout=30) as resposta:
    resultados = json.loads(resposta.read().decode("utf-8"))

if not resultados:
    iface.messageBar().pushWarning(
        "Geocodificação",
        f"Nenhum resultado para: {endereco}"
    )

else:
    resultado = resultados[0]
    latitude = float(resultado["lat"])
    longitude = float(resultado["lon"])

    # --------------------------------------------------
    # 3. Camada de pontos (EPSG:4326)
    # --------------------------------------------------

    camada = QgsVectorLayer(
        "Point?crs=EPSG:4326", "endereco_geocodificado", "memory"
    )
    camada.dataProvider().addAttributes([
        QgsField("endereco", QVariant.String),
        QgsField("local_encontrado", QVariant.String),
        QgsField("latitude", QVariant.Double),
        QgsField("longitude", QVariant.Double),
    ])
    camada.updateFields()

    feicao = QgsFeature(camada.fields())

    # X = longitude, Y = latitude (a ordem inversa da que o serviço exibe).
    feicao.setGeometry(
        QgsGeometry.fromPointXY(QgsPointXY(longitude, latitude))
    )
    feicao.setAttributes([
        endereco,
        resultado["display_name"],
        latitude,
        longitude,
    ])
    camada.dataProvider().addFeatures([feicao])
    camada.updateExtents()

    # --------------------------------------------------
    # 4. Adiciona ao projeto e aproxima
    # --------------------------------------------------

    QgsProject.instance().addMapLayer(camada)
    iface.setActiveLayer(camada)
    iface.zoomToActiveLayer()
    iface.mapCanvas().zoomScale(5000)

    print("Local encontrado:", resultado["display_name"])
    print("Latitude:", latitude, "| Longitude:", longitude)
