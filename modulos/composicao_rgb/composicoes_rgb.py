# -*- coding: utf-8 -*-

# Composições RGB (cor natural e falsa-cor NIR) para todas as cenas
# Landsat 8/9 e Sentinel-2 de uma pasta, como rasters virtuais (.vrt).
# Rode no Editor do Console Python do QGIS.

from pathlib import Path

import processing
from qgis.core import (
    QgsContrastEnhancement,
    QgsMultiBandColorRenderer,
    QgsProject,
    QgsRasterLayer,
    QgsRasterMinMaxOrigin,
)

# 1. Configuração dos caminhos e parâmetros espectrais
PASTA_DADOS = Path(r"C:\minicurso\dados_curso\composicao_rgb")  # ajuste para sua pasta

CONFIG_SENSORES = {
    "Landsat": {
        "prefixos": ("LC08", "LC09"),
        "composicoes": {
            "cor_natural": ["B04.tif", "B03.tif", "B02.tif"],
            "falsa_cor_nir": ["B05.tif", "B04.tif", "B03.tif"],  # NIR = B05
        },
    },
    "Sentinel2": {
        "prefixos": ("S2A", "S2B", "S2C"),
        "composicoes": {
            "cor_natural": ["B04.tif", "B03.tif", "B02.tif"],
            "falsa_cor_nir": ["B08.tif", "B04.tif", "B03.tif"],  # NIR = B08
        },
    },
}


def data_da_cena(nome_cena, sensor_id):
    """Extrai a data AAAAMMDD do nome da cena."""
    partes = nome_cena.split("_")
    return partes[3] if sensor_id == "Landsat" else partes[2][:8]


def aplicar_corte_cumulativo(layer):
    """Cor multibanda (R=1, G=2, B=3) com corte cumulativo 2–98%."""
    layer.setRenderer(
        QgsMultiBandColorRenderer(layer.dataProvider(), 1, 2, 3)
    )
    # CumulativeCut usa os percentis do histograma (padrão do QGIS: 2–98%).
    layer.setContrastEnhancement(
        QgsContrastEnhancement.StretchToMinimumMaximum,
        QgsRasterMinMaxOrigin.CumulativeCut,
    )


# 2. Iteração sobre as pastas de cenas orbitais
print("Iniciando o processamento de composições RGB...")
projeto = QgsProject.instance()

for subpasta in sorted(PASTA_DADOS.iterdir()):
    if not subpasta.is_dir():
        continue

    nome_cena = subpasta.name
    sensor_id = None

    # Identifica o sensor orbital pelo nome da pasta
    for sensor, cfg in CONFIG_SENSORES.items():
        if nome_cena.startswith(cfg["prefixos"]):
            sensor_id = sensor
            break

    if not sensor_id:
        continue

    data = data_da_cena(nome_cena, sensor_id)
    print(f"\nProcessando cena: {nome_cena} ({sensor_id}, {data})")
    grupo = projeto.layerTreeRoot().insertGroup(0, f"{sensor_id} {data}")

    # Gera cada composição definida para o sensor
    for nome_comp, bandas in CONFIG_SENSORES[sensor_id]["composicoes"].items():
        caminhos_bandas = [subpasta / b for b in bandas]
        faltantes = [c.name for c in caminhos_bandas if not c.exists()]

        if faltantes:
            print(f"  [AVISO] Faltam {faltantes}. Pulando {nome_comp}.")
            continue

        caminho_vrt = str(subpasta / f"{nome_comp}.vrt")

        processing.run("gdal:buildvirtualraster", {
            "INPUT": [str(c) for c in caminhos_bandas],
            "RESOLUTION": 1,   # 0 = média, 1 = mais alta, 2 = mais baixa
            "SEPARATE": True,  # cada arquivo vira uma banda, na ordem da lista
            "OUTPUT": caminho_vrt,
        })

        # Carrega o VRT no grupo da cena: sensor_data_composicao
        nome_camada = f"{sensor_id}_{data}_{nome_comp}"
        camada = QgsRasterLayer(caminho_vrt, nome_camada)

        if camada.isValid():
            aplicar_corte_cumulativo(camada)
            projeto.addMapLayer(camada, False)
            grupo.addLayer(camada)
            print(f"  [SUCESSO] {nome_camada} ({'-'.join(b[:-4] for b in bandas)})")
        else:
            print(f"  [ERRO] Falha ao carregar o VRT: {caminho_vrt}")

print("\nProcessamento concluído.")
