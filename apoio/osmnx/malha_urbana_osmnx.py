# -*- coding: utf-8 -*-
"""
Malha urbana OSM -> GeoPackage (QGIS + OSMnx)

Uso: abra no Editor de Scripts do Console Python do QGIS e clique em "Executar".
- Pede o nome da cidade (como aparece no OpenStreetMap/Nominatim)
- Pede o tipo de rede
- Pede a pasta de saída (lembra a última usada)
- Baixa em segundo plano (o QGIS não trava) e adiciona as camadas ao mapa

GeoPackage gerado com 4 camadas:
  edges  -> vias, 1 linha por trecho (para mapa); 'from'/'to' + 'oneway' guardam o sentido
  arcos  -> grafo DIRIGIDO: 1 linha por sentido de circulação (para roteamento)
            mão dupla = 2 arcos (ida e volta); mão única = 1 arco, digitalizado no sentido do tráfego
  nodes  -> cruzamentos/nós (Point)
  limite -> polígono do município usado no recorte
Arestas e arcos já saem com speed_kph (maxspeed ou padrão por tipo de via) e travel_time (s).
"""

import os
import re
import site
import unicodedata
from datetime import datetime

from qgis.PyQt.QtWidgets import QInputDialog, QFileDialog
from qgis.core import (QgsApplication, QgsTask, QgsSettings, QgsMessageLog,
                       QgsVectorLayer, QgsProject, Qgis)
from qgis.utils import iface

# --- ambiente (mesmos ajustes do startup.py; inofensivo repetir) -------------
site.addsitedir(site.getusersitepackages())
os.environ["PROJ_LIB"] = os.environ.get("PROJ_DATA", os.environ.get("PROJ_LIB", ""))

import osmnx as ox

_base = os.path.join(os.path.expanduser("~"), "osmnx")
ox.settings.cache_folder = os.path.join(_base, "cache")
ox.settings.data_folder = os.path.join(_base, "data")
ox.settings.logs_folder = os.path.join(_base, "logs")
ox.settings.requests_timeout = 600   # cidades grandes demoram no Overpass
ox.settings.log_console = False

# Velocidades (km/h) para vias sem "maxspeed" no OSM (referência urbana no Brasil)
VEL_PADRAO_KMH = {
    "motorway": 100, "motorway_link": 60, "trunk": 80, "trunk_link": 50,
    "primary": 60, "primary_link": 40, "secondary": 50, "secondary_link": 40,
    "tertiary": 40, "tertiary_link": 30, "unclassified": 30, "residential": 30,
    "living_street": 10, "service": 20, "road": 30,
}
VEL_FALLBACK_KMH = 30


def _texto_listas(gdf):
    """Listas/dicts do OSM viram texto (o GPKG não aceita listas)."""
    for c in gdf.columns:
        if c != "geometry" and gdf[c].dtype == object:
            gdf[c] = gdf[c].map(lambda x: str(x) if isinstance(x, (list, dict, set)) else x)
    return gdf

TITULO = "Malha urbana OSM"
CHAVE_PASTA = "malha_osmnx/ultima_pasta"
CHAVE_CIDADE = "malha_osmnx/ultima_cidade"

TIPOS_REDE = [
    ("all", "Todas as vias (inclui privadas)"),
    ("all_public", "Todas as vias públicas"),
    ("drive", "Veículos (vias públicas dirigíveis)"),
    ("drive_service", "Veículos + vias de serviço"),
    ("walk", "Pedestres"),
    ("bike", "Bicicletas"),
]


def _slug(texto):
    """'João Pessoa, Paraíba, Brasil' -> 'joao_pessoa'"""
    texto = texto.split(",")[0]
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def _caminho_livre(pasta, nome):
    """Evita sobrescrever (no Windows, um .gpkg aberto no QGIS fica travado)."""
    caminho = os.path.join(pasta, f"{nome}.gpkg")
    if not os.path.exists(caminho):
        return caminho
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(pasta, f"{nome}_{carimbo}.gpkg")


def _baixar(task, cidade, tipo, caminho):
    """Roda em segundo plano: nada de iface/GUI aqui dentro."""
    task.setProgress(5)
    limite = ox.geocode_to_gdf(cidade)
    poligono = limite.union_all()
    if task.isCanceled():
        return None

    task.setProgress(15)
    G = ox.graph_from_polygon(poligono, network_type=tipo, retain_all=True,
                              truncate_by_edge=True)
    if task.isCanceled():
        return None

    task.setProgress(75)
    # custos de roteamento já gravados no arquivo
    G = ox.routing.add_edge_speeds(G, hwy_speeds=VEL_PADRAO_KMH, fallback=VEL_FALLBACK_KMH)
    G = ox.routing.add_edge_travel_times(G)

    task.setProgress(80)
    # nodes + edges (não dirigida: boa para visualizar, sem linhas sobrepostas)
    ox.save_graph_geopackage(G, filepath=caminho, directed=False)

    # arcos (dirigida): cada sentido permitido é uma feição própria
    arcos = ox.graph_to_gdfs(G, nodes=False).reset_index()
    arcos["mao"] = arcos["oneway"].map(lambda x: "única" if bool(x) else "dupla")
    _texto_listas(arcos).to_file(caminho, layer="arcos", driver="GPKG")
    n_arcos = len(arcos)

    lim = limite[["geometry"]].copy()
    lim["consulta"] = cidade
    lim["nome_osm"] = limite["display_name"].values if "display_name" in limite else cidade
    lim["tipo_rede"] = tipo
    lim["baixado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    lim.to_file(caminho, layer="limite", driver="GPKG")

    task.setProgress(100)
    return {"caminho": caminho, "nos": G.number_of_nodes(),
            "arestas": n_arcos, "cidade": cidade, "tipo": tipo}


def _concluido(exception, result=None):
    """Volta para a thread principal: aqui pode mexer no mapa."""
    if exception:
        QgsMessageLog.logMessage(repr(exception), TITULO, Qgis.Critical)
        iface.messageBar().pushCritical(TITULO, f"Falhou: {exception}")
        return
    if not result:
        iface.messageBar().pushWarning(TITULO, "Cancelado.")
        return

    caminho = result["caminho"]
    nome = _slug(result["cidade"])
    grupo = QgsProject.instance().layerTreeRoot().insertGroup(
        0, f"{result['cidade'].split(',')[0]} ({result['tipo']})")
    for camada in ("limite", "edges", "nodes", "arcos"):
        lyr = QgsVectorLayer(f"{caminho}|layername={camada}", f"{nome}_{camada}", "ogr")
        if lyr.isValid():
            QgsProject.instance().addMapLayer(lyr, False)
            no = grupo.addLayer(lyr)
            if camada == "arcos":          # sobrepõe 'edges'; fica desligada no mapa
                no.setItemVisibilityChecked(False)
    iface.messageBar().pushSuccess(
        TITULO, f"{result['arestas']:,} arcos dirigidos e {result['nos']:,} nós salvos em {caminho}")


def executar():
    janela = iface.mainWindow()
    cfg = QgsSettings()

    cidade, ok = QInputDialog.getText(
        janela, TITULO, "Cidade (nome no OSM — inclua estado e país):",
        text=cfg.value(CHAVE_CIDADE, "João Pessoa, Paraíba, Brasil"))
    if not ok or not cidade.strip():
        return
    cidade = cidade.strip()

    rotulos = [f"{codigo} — {desc}" for codigo, desc in TIPOS_REDE]
    escolha, ok = QInputDialog.getItem(janela, TITULO, "Tipo de rede:", rotulos, 0, False)
    if not ok:
        return
    tipo = escolha.split(" — ")[0]

    pasta = QFileDialog.getExistingDirectory(
        janela, "Pasta para salvar o GeoPackage",
        cfg.value(CHAVE_PASTA, os.path.expanduser("~")))
    if not pasta:
        return

    cfg.setValue(CHAVE_CIDADE, cidade)
    cfg.setValue(CHAVE_PASTA, pasta)

    caminho = _caminho_livre(pasta, f"malha_{_slug(cidade)}_{tipo}")

    global _tarefa_malha   # manter referência, senão o Python descarta a tarefa
    _tarefa_malha = QgsTask.fromFunction(
        f"{TITULO}: {cidade.split(',')[0]} ({tipo})", _baixar,
        cidade=cidade, tipo=tipo, caminho=caminho, on_finished=_concluido)
    QgsApplication.taskManager().addTask(_tarefa_malha)
    iface.messageBar().pushInfo(
        TITULO, "Download iniciado — acompanhe na barra de tarefas (canto inferior).")


executar()
