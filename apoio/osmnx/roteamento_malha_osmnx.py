# -*- coding: utf-8 -*-
"""
Roteamento sobre a malha OSMnx em GeoPackage  —  v2 (arcos direcionados)

Rodar no Editor de Scripts do Console Python do QGIS (botão Executar).

O que mudou em relação à v1 (e em relação ao guia "OSMnx + QGIS no Windows"):
  * Grafo DIRIGIDO por padrão: mão única só é percorrida no sentido permitido.
    Fonte do sentido, em ordem de confiabilidade:
      1) camada 'arcos' (gravada pelo malha_urbana_osmnx.py novo: 1 feição por sentido)
      2) camada 'edges' exportada com directed=False, reconstruída a partir de
         'from'/'to' + 'oneway' (o OSMnx guarda esses campos justamente para isso)
      3) camada 'edges' exportada com directed=True (u, v, key)
    Quando 'arcos' e 'edges' existem, o script compara os dois (validação cruzada).
  * Perfis: Carro (respeita mão/contramão; menor distância e mais rápida) e
    Pedestre (ignora o sentido). No perfil Carro, uma rota de comparação
    "ignorando mão única" mostra quantos metros seriam feitos na contramão.
  * Pontos clicados são ligados só a nós da maior componente fortemente conexa
    (evita "não existe caminho" por ilhas e becos sem saída de mão única).
  * Validação de campos obrigatórios, camadas de rota tipadas, auditoria de
    sentido por trecho, zoom no resultado, resumo em janela e gravação opcional
    das rotas em <arquivo>_rotas.gpkg.

Uso: escolha o GPKG -> confira a inspeção no console -> escolha o perfil ->
clique ORIGEM e DESTINO no mapa (botão direito ou Esc cancela).
Para outra rota sem recarregar nada: nova_rota()
"""

import os
import ast
import site
from collections import Counter
from datetime import datetime

import numpy as np

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from qgis.core import (QgsVectorLayer, QgsProject, QgsSettings, QgsWkbTypes,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsFeatureRequest, QgsFeature, QgsGeometry, QgsPointXY,
                       QgsRectangle, NULL)
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker
from qgis.utils import iface

# --- ambiente (mesmos ajustes do startup.py) ---------------------------------
site.addsitedir(site.getusersitepackages())
os.environ["PROJ_LIB"] = os.environ.get("PROJ_DATA", os.environ.get("PROJ_LIB", ""))

import shapely
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point

_base = os.path.join(os.path.expanduser("~"), "osmnx")
ox.settings.cache_folder = os.path.join(_base, "cache")
ox.settings.data_folder = os.path.join(_base, "data")
ox.settings.logs_folder = os.path.join(_base, "logs")

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================
COMPARAR_IGNORANDO_SENTIDO = True   # perfil Carro: rota extra sem respeitar mão única
COMPARAR_COM_QGIS = False           # também roda o algoritmo nativo do QGIS
SALVAR_ROTAS = True                 # grava cada rota em <gpkg>_rotas.gpkg (camada 'rotas')
N_AMOSTRA = 3                       # feições na amostra da inspeção
SNAP_MAX_M = 150                    # alerta se o clique estiver longe da malha

VEL_PADRAO_KMH = {                  # vias sem maxspeed (referência urbana no Brasil)
    "motorway": 100, "motorway_link": 60, "trunk": 80, "trunk_link": 50,
    "primary": 60, "primary_link": 40, "secondary": 50, "secondary_link": 40,
    "tertiary": 40, "tertiary_link": 30, "unclassified": 30, "residential": 30,
    "living_street": 10, "service": 20, "road": 30,
}
VEL_FALLBACK_KMH = 30

PERFIS = {
    "Carro — respeita mão e contramão (distância e tempo)": "carro",
    "Pedestre — ignora o sentido das vias (distância)": "pedestre",
}

CAMPOS_OBRIGATORIOS = {"nodes": ["osmid", "x", "y"],
                       "edges": ["u", "v", "length"],
                       "arcos": ["u", "v", "length"]}
CAMPOS_CUSTO = ["length", "maxspeed", "oneway", "highway", "lanes", "speed_kph",
                "travel_time", "from", "to", "u", "v", "key", "reversed", "mao"]
CAMPOS_LISTA = ("highway", "maxspeed", "lanes", "name", "ref", "access", "width", "osmid")

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


# =============================================================================
# UTILITÁRIOS
# =============================================================================
def _nulo(v):
    return v is None or v == NULL or (isinstance(v, str) and v.strip() == "")


def _lista(v):
    """O GPKG guarda listas do OSM como texto: "['40', '60']" -> ['40', '60']."""
    if isinstance(v, str) and v.startswith("["):
        try:
            return ast.literal_eval(v)
        except (ValueError, SyntaxError):
            return v
    return v


def _bool(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return False
    return str(v).strip().lower() in ("true", "1", "yes", "-1")


def _txt(v):
    if isinstance(v, (list, tuple, set)):
        return " / ".join(str(x) for x in v)
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    return str(v)


def listar_camadas(gpkg):
    from osgeo import ogr
    ds = ogr.Open(gpkg)
    return [ds.GetLayer(i).GetName() for i in range(ds.GetLayerCount())]


# =============================================================================
# ETAPA 1 - INSPEÇÃO DE METADADOS (PyQGIS)
# =============================================================================
def inspecionar_camada(gpkg, nome):
    lyr = QgsVectorLayer(f"{gpkg}|layername={nome}", nome, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"Camada '{nome}' inválida em {gpkg}")

    crs = lyr.crs()
    ext = lyr.extent()
    ext_wgs = QgsCoordinateTransform(crs, WGS84, QgsProject.instance()).transformBoundingBox(ext)
    print("\n" + "=" * 78)
    print(f" CAMADA: {nome}")
    print("=" * 78)
    print(f"  SRC ............: {crs.authid()} - {crs.description()}")
    print(f"  Geográfico? ....: {'sim (graus)' if crs.isGeographic() else 'não (metros)'}")
    print(f"  Geometria ......: {QgsWkbTypes.displayString(lyr.wkbType())}")
    print(f"  Nº de feições ..: {lyr.featureCount():,}")
    print(f"  Extensão WGS84 .: lon {ext_wgs.xMinimum():.5f} a {ext_wgs.xMaximum():.5f} | "
          f"lat {ext_wgs.yMinimum():.5f} a {ext_wgs.yMaximum():.5f}")

    nomes = lyr.fields().names()
    faltando = [c for c in CAMPOS_OBRIGATORIOS.get(nome, []) if c not in nomes]
    if faltando:
        raise RuntimeError(f"Camada '{nome}': campos obrigatórios ausentes: {faltando}")

    preenchidos, oneway, highway, total = Counter(), Counter(), Counter(), 0
    for f in lyr.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)):
        total += 1
        for n in nomes:
            if not _nulo(f[n]):
                preenchidos[n] += 1
        if "oneway" in nomes:
            oneway[str(f["oneway"])] += 1
        if "highway" in nomes:
            highway[str(f["highway"])] += 1

    print(f"\n  {'campo':<16}{'tipo':<14}{'preenchido':>12}   custo?")
    print("  " + "-" * 52)
    for c in lyr.fields():
        pct = 100 * preenchidos[c.name()] / total if total else 0
        print(f"  {c.name():<16}{c.typeName():<14}{pct:>11.1f}%"
              f"{'  <==' if c.name() in CAMPOS_CUSTO else ''}")
    if oneway:
        print("\n  Valores de 'oneway':", dict(oneway.most_common()))
    if highway and nome == "edges":
        print("  'highway' (10 mais comuns):")
        for k, n in highway.most_common(10):
            print(f"     {k:<35}{n:>8,}")

    amostra = list(lyr.getFeatures(QgsFeatureRequest().setLimit(N_AMOSTRA)))
    if amostra:
        print(f"\n  Amostra ({len(amostra)} feições):")
        for n in nomes:
            print(f"     {n:<16}" + " | ".join(str(f[n])[:22] for f in amostra))
    return {"preenchidos": preenchidos, "total": total, "campos": nomes}


def etapa1(gpkg):
    print(f"\nGeoPackage: {gpkg}")
    camadas = listar_camadas(gpkg)
    print("Camadas:", ", ".join(camadas))
    for obrig in ("nodes", "edges"):
        if obrig not in camadas:
            raise RuntimeError(f"O GeoPackage não tem a camada '{obrig}'.")
    infos = {n: inspecionar_camada(gpkg, n) for n in camadas}

    e = infos["edges"]
    pct = lambda c: 100 * e["preenchidos"][c] / e["total"] if c in e["campos"] else 0
    print("\n" + "#" * 78)
    print(" DIAGNÓSTICO PARA ROTEAMENTO")
    print("#" * 78)
    print(f"  Distância (length)   : {pct('length'):5.1f}%  (metros)")
    print(f"  Velocidade (maxspeed): {pct('maxspeed'):5.1f}%  -> o restante é imputado por 'highway'")
    print(f"  Sentido (oneway)     : {pct('oneway'):5.1f}%")
    if "arcos" in camadas:
        print("  Fonte do sentido     : camada 'arcos' (grafo dirigido gravado no download) [melhor]")
    elif {"from", "to"}.issubset(e["campos"]):
        print("  Fonte do sentido     : 'edges' não dirigida -> reconstrução por from/to + oneway")
    else:
        print("  Fonte do sentido     : 'edges' dirigida (u, v, key)")
    return camadas


# =============================================================================
# ETAPA 2 - GRAFO DIRIGIDO
# =============================================================================
def _preparar(gdf):
    for c in CAMPOS_LISTA:
        if c in gdf.columns:
            gdf[c] = gdf[c].map(_lista)
    gdf["oneway"] = gdf["oneway"].map(_bool) if "oneway" in gdf.columns else False
    return gdf


def _ler_nodes(gpkg):
    nodes = gpd.read_file(gpkg, layer="nodes")
    nodes["osmid"] = nodes["osmid"].astype("int64")
    return nodes.set_index("osmid")


def _arcos_de_camada_dirigida(gdf, nodes):
    e = gdf.copy()
    e[["u", "v"]] = e[["u", "v"]].astype("int64")
    return e[e["u"].isin(nodes.index) & e["v"].isin(nodes.index)]


def _arcos_reconstruidos(edges, nodes):
    """
    Exportação não dirigida -> arcos dirigidos.
    'from'/'to' = sentido original do arco no grafo dirigido do OSMnx; numa via de
    mão única esse é o único sentido permitido. Regras:
      - todo trecho gera o arco from->to (geometria orientada de 'from' para 'to')
      - trecho com oneway=False gera também to->from (geometria invertida)
    """
    crs = edges.crs
    e = edges.drop(columns=[c for c in ("u", "v", "key", "reversed") if c in edges.columns])
    e = e.rename(columns={"from": "u", "to": "v"})
    e[["u", "v"]] = e[["u", "v"]].astype("int64")
    e = e[e["u"].isin(nodes.index) & e["v"].isin(nodes.index)].copy()

    geoms = e.geometry.to_numpy()
    p0 = shapely.get_point(geoms, 0)
    x0, y0 = shapely.get_x(p0), shapely.get_y(p0)
    ux, uy = nodes.loc[e["u"], "x"].to_numpy(), nodes.loc[e["u"], "y"].to_numpy()
    vx, vy = nodes.loc[e["v"], "x"].to_numpy(), nodes.loc[e["v"], "y"].to_numpy()
    inv = (x0 - ux) ** 2 + (y0 - uy) ** 2 > (x0 - vx) ** 2 + (y0 - vy) ** 2
    geoms[inv] = shapely.reverse(geoms[inv])
    e["geometry"] = gpd.GeoSeries(geoms, index=e.index, crs=crs)

    volta = e[~e["oneway"]].copy()
    volta[["u", "v"]] = volta[["v", "u"]].to_numpy()
    volta["geometry"] = gpd.GeoSeries(shapely.reverse(volta.geometry.to_numpy()),
                                      index=volta.index, crs=crs)
    arcos = gpd.GeoDataFrame(pd.concat([e, volta], ignore_index=True),
                             geometry="geometry", crs=crs)
    return arcos, int(inv.sum())


def carregar_grafo(gpkg, camadas):
    nodes = _ler_nodes(gpkg)
    edges = _preparar(gpd.read_file(gpkg, layer="edges"))
    nao_dirigida = {"from", "to"}.issubset(edges.columns)

    if "arcos" in camadas:
        arcos = _arcos_de_camada_dirigida(_preparar(gpd.read_file(gpkg, layer="arcos")), nodes)
        fonte = "camada 'arcos' (dirigida)"
        if nao_dirigida:   # validação cruzada: reconstrução x arcos gravados
            rec, _ = _arcos_reconstruidos(edges, nodes)
            par = lambda df: set(zip(df["u"], df["v"]))
            a, r = par(arcos), par(rec)
            print(f"\n[validação] arcos gravados: {len(arcos):,} | reconstruídos: {len(rec):,} | "
                  f"pares u->v em comum: {100 * len(a & r) / max(len(a), 1):.2f}%")
    elif nao_dirigida:
        arcos, n_inv = _arcos_reconstruidos(edges, nodes)
        fonte = f"reconstrução de 'edges' (from/to + oneway; {n_inv:,} geometrias reorientadas)"
    else:
        arcos = _arcos_de_camada_dirigida(edges, nodes)
        fonte = "camada 'edges' dirigida"

    arcos["contramao"] = False
    arcos["key"] = arcos.groupby(["u", "v"]).cumcount()
    arcos = arcos.drop(columns=[c for c in ("speed_kph", "travel_time") if c in arcos.columns])
    G = ox.graph_from_gdfs(nodes, arcos.set_index(["u", "v", "key"]))
    G = ox.routing.add_edge_speeds(G, hwy_speeds=VEL_PADRAO_KMH, fallback=VEL_FALLBACK_KMH)
    G = ox.routing.add_edge_travel_times(G)

    n_unica = sum(1 for *_, d in G.edges(data=True) if d.get("oneway"))
    print(f"\n[grafo] fonte do sentido: {fonte}")
    print(f"[grafo] {G.number_of_nodes():,} nós | {G.number_of_edges():,} arcos dirigidos "
          f"({n_unica:,} em vias de mão única)")
    return G


def grafo_sem_sentido(G):
    """Cópia em que toda mão única ganha o arco inverso, marcado contramao=True."""
    H = G.copy()
    for u, v, d in list(G.edges(data=True)):
        if d.get("oneway"):
            r = dict(d)
            r["geometry"] = shapely.reverse(d["geometry"])
            r["contramao"] = True
            H.add_edge(v, u, **r)
    return H


def _nos_conectados(G, fortemente):
    comps = nx.strongly_connected_components(G) if fortemente else nx.weakly_connected_components(G)
    return max(comps, key=len)


def _crs_metrico(gdf):
    try:
        return gdf.estimate_utm_crs(datum_name="SIRGAS 2000")   # EPSG:31985 em João Pessoa
    except Exception:
        return gdf.estimate_utm_crs()


def no_mais_proximo(nodes_m, lat, lon):
    """Índice espacial do GeoPandas (rápido; dispensa scikit-learn)."""
    pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(nodes_m.crs)
    idx, dist = nodes_m.sindex.nearest(pt, return_all=False, return_distance=True)
    return int(nodes_m.index[idx[1][0]]), float(dist[0])


def calcular_rota(G, o, d, peso):
    rota = ox.routing.shortest_path(G, o, d, weight=peso)
    if rota is None:
        return None
    return ox.routing.route_to_gdf(G, rota, weight=peso)   # pega o arco paralelo de menor peso


def resumir(gdf):
    contra = gdf["contramao"].fillna(False).astype(bool)
    unica = gdf["oneway"].map(_bool) & ~contra
    return {"km": gdf["length"].sum() / 1000, "min": gdf["travel_time"].sum() / 60,
            "trechos": len(gdf), "unica": int(unica.sum()),
            "contra": int(contra.sum()), "contra_m": float(gdf.loc[contra, "length"].sum())}


# =============================================================================
# SAÍDA NO QGIS
# =============================================================================
def camada_rota(gdf, nome, cor, largura=1.2, tracejada=False):
    uri = ("LineString?crs=EPSG:4326&field=ordem:integer&field=nome:string(150)"
           "&field=tipo_via:string(60)&field=maxspeed:string(30)&field=mao:string(10)"
           "&field=contramao:string(3)&field=dist_m:double&field=vel_kmh:double&field=tempo_s:double")
    lyr = QgsVectorLayer(uri, nome, "memory")
    feats = []
    for i, (_, r) in enumerate(gdf.iterrows(), start=1):
        f = QgsFeature(lyr.fields())
        f.setGeometry(QgsGeometry.fromWkt(r.geometry.wkt))
        f.setAttributes([i, _txt(r.get("name")), _txt(r.get("highway")), _txt(r.get("maxspeed")),
                         "única" if _bool(r.get("oneway")) else "dupla",
                         "sim" if bool(r.get("contramao")) else "não",
                         round(float(r["length"]), 1), round(float(r["speed_kph"]), 1),
                         round(float(r["travel_time"]), 1)])
        feats.append(f)
    lyr.dataProvider().addFeatures(feats)
    lyr.updateExtents()
    sl = lyr.renderer().symbol().symbolLayer(0)
    sl.setColor(QColor(cor))
    sl.setWidth(largura)
    if tracejada:
        sl.setPenStyle(Qt.DashLine)
    QgsProject.instance().addMapLayer(lyr)
    return lyr


def camada_pontos(orig, dest, info):
    lyr = QgsVectorLayer("Point?crs=EPSG:4326&field=tipo:string(10)&field=no_osm:string(20)"
                         "&field=snap_m:double", "Origem/Destino", "memory")
    feats = []
    for tipo, (lat, lon), (no, dist) in (("origem", orig, info[0]), ("destino", dest, info[1])):
        f = QgsFeature(lyr.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        f.setAttributes([tipo, str(no), round(dist, 1)])
        feats.append(f)
    lyr.dataProvider().addFeatures(feats)
    lyr.renderer().symbol().setSize(3)
    QgsProject.instance().addMapLayer(lyr)
    return lyr


def enquadrar(camadas):
    ext = QgsRectangle()
    for lyr in camadas:
        ext.combineExtentWith(lyr.extent())
    if ext.isEmpty():
        return
    canvas = iface.mapCanvas()
    tr = QgsCoordinateTransform(WGS84, canvas.mapSettings().destinationCrs(), QgsProject.instance())
    ext = tr.transformBoundingBox(ext)
    ext.scale(1.25)
    canvas.setExtent(ext)
    canvas.refresh()


def salvar_rotas(registros, orig, dest):
    destino = os.path.splitext(_estado["gpkg"])[0] + "_rotas.gpkg"
    linhas = []
    for rotulo, gdf, r in registros:
        geom = shapely.line_merge(shapely.union_all(gdf.geometry.to_numpy()))
        linhas.append({"data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "perfil": _estado["perfil"], "rota": rotulo,
                       "km": round(r["km"], 3), "minutos": round(r["min"], 1),
                       "contramao_m": round(r["contra_m"], 1),
                       "orig_lat": orig[0], "orig_lon": orig[1],
                       "dest_lat": dest[0], "dest_lon": dest[1], "geometry": geom})
    modo = "a" if os.path.exists(destino) else "w"
    gpd.GeoDataFrame(linhas, crs="EPSG:4326").to_file(destino, layer="rotas",
                                                     driver="GPKG", mode=modo)
    print(f"  rotas gravadas em {destino}")


# =============================================================================
# ROTEAMENTO NATIVO DO QGIS (comparação opcional)
# =============================================================================
EXPR_VELOCIDADE = (
    r"coalesce(to_real(regexp_substr(to_string(\"maxspeed\"), '(\\d+)')), "
    "CASE " + " ".join(f"WHEN \"highway\" LIKE '%{k}%' THEN {v}" for k, v in
                       sorted(VEL_PADRAO_KMH.items(), key=lambda kv: -kv[1]))
    + f" ELSE {VEL_FALLBACK_KMH} END)")
EXPR_SENTIDO = "CASE WHEN lower(to_string(\"oneway\")) IN ('1','true','yes') THEN 'F' ELSE 'A' END"


def rota_qgis(orig, dest):
    """Usa 'arcos' (cada arco já digitalizado no sentido do tráfego -> tudo 'só ida')
    ou, sem ela, 'edges' com campo de sentido derivado de oneway."""
    import processing
    gpkg, camadas = _estado["gpkg"], _estado["camadas"]
    tem_arcos = "arcos" in camadas
    r = processing.run("native:reprojectlayer", {
        "INPUT": f"{gpkg}|layername={'arcos' if tem_arcos else 'edges'}",
        "TARGET_CRS": QgsCoordinateReferenceSystem(_estado["crs_m"].to_wkt()),
        "OUTPUT": "memory:"})["OUTPUT"]
    r = processing.run("native:fieldcalculator", {
        "INPUT": r, "FIELD_NAME": "vel_kmh", "FIELD_TYPE": 0, "FIELD_LENGTH": 6,
        "FIELD_PRECISION": 1, "FORMULA": EXPR_VELOCIDADE, "OUTPUT": "memory:"})["OUTPUT"]
    sentido = {"DEFAULT_DIRECTION": 0}                         # 0 = só no sentido da linha
    if not tem_arcos:
        r = processing.run("native:fieldcalculator", {
            "INPUT": r, "FIELD_NAME": "sentido", "FIELD_TYPE": 2, "FIELD_LENGTH": 1,
            "FORMULA": EXPR_SENTIDO, "OUTPUT": "memory:"})["OUTPUT"]
        sentido = {"DIRECTION_FIELD": "sentido", "VALUE_FORWARD": "F", "VALUE_BACKWARD": "R",
                   "VALUE_BOTH": "A", "DEFAULT_DIRECTION": 2}
    for estrategia, rotulo in ((0, "menor distância"), (1, "mais rápida")):
        out = processing.run("native:shortestpathpointtopoint", {
            "INPUT": r, "STRATEGY": estrategia, **sentido,
            "SPEED_FIELD": "vel_kmh", "DEFAULT_SPEED": VEL_FALLBACK_KMH, "TOLERANCE": 1.0,
            "START_POINT": f"{orig[1]},{orig[0]} [EPSG:4326]",
            "END_POINT": f"{dest[1]},{dest[0]} [EPSG:4326]", "OUTPUT": "memory:"})["OUTPUT"]
        f = next(out.getFeatures(), None)
        if f:
            c = f["cost"]
            print(f"  QGIS   {rotulo:<28}: " +
                  (f"{c / 1000:6.2f} km" if estrategia == 0 else f"{c * 60:6.1f} min"))
        out.setName(f"Rota QGIS - {rotulo}")
        QgsProject.instance().addMapLayer(out)


# =============================================================================
# ORQUESTRAÇÃO
# =============================================================================
_estado = {}


def rotear(orig, dest):
    perfil = _estado["perfil"]
    G = _estado["G"]
    print("\n" + "#" * 78)
    print(f" ROTA ({perfil})  origem {orig[0]:.5f},{orig[1]:.5f}  ->  "
          f"destino {dest[0]:.5f},{dest[1]:.5f}")
    print("#" * 78)

    # carro: liga cliques só à maior componente FORTEMENTE conexa do grafo dirigido
    nos_m = _estado["nodes_carro"] if perfil == "carro" else _estado["nodes_pe"]
    info = [no_mais_proximo(nos_m, *orig), no_mais_proximo(nos_m, *dest)]
    for nome, (_, dist) in zip(("origem", "destino"), info):
        if dist > SNAP_MAX_M:
            print(f"  ! {nome} a {dist:.0f} m do nó mais próximo — clique mais perto de uma via")
    o, d = info[0][0], info[1][0]

    if perfil == "carro":
        pedidos = [(G, "length", "Carro - menor distância", "#1f77b4", False),
                   (G, "travel_time", "Carro - mais rápida", "#d62728", False)]
        if COMPARAR_IGNORANDO_SENTIDO:
            pedidos.append((_estado["G_livre"], "length",
                            "Comparação - ignorando mão única", "#7f7f7f", True))
    else:
        pedidos = [(_estado["G_livre"], "length", "Pedestre - menor distância", "#2ca02c", False)]

    camadas, registros, linhas_resumo = [], [], []
    for grafo, peso, rotulo, cor, tracejada in pedidos:
        gdf = calcular_rota(grafo, o, d, peso)
        if gdf is None:
            msg = f"{rotulo}: sem caminho entre os nós escolhidos"
            print("  ! " + msg)
            linhas_resumo.append(msg)
            continue
        r = resumir(gdf)
        txt = (f"{rotulo}: {r['km']:.2f} km | {r['min']:.1f} min | {r['trechos']} trechos | "
               f"{r['unica']} em mão única (sentido permitido)")
        if r["contra"]:
            txt += f" | {r['contra']} na CONTRAMÃO ({r['contra_m']:.0f} m)"
        print("  " + txt)
        linhas_resumo.append(txt)
        camadas.append(camada_rota(gdf, rotulo, cor, 0.8 if tracejada else 1.2, tracejada))
        registros.append((rotulo, gdf, r))

    camadas.append(camada_pontos(orig, dest, info))
    enquadrar(camadas)
    if COMPARAR_COM_QGIS and perfil == "carro":
        rota_qgis(orig, dest)
    if SALVAR_ROTAS and registros:
        salvar_rotas(registros, orig, dest)

    QMessageBox.information(iface.mainWindow(), "Rota concluída", "\n\n".join(linhas_resumo) +
                            "\n\nCamadas temporárias adicionadas. Outra rota: nova_rota()")


class DoisCliques(QgsMapToolEmitPoint):
    """1º clique = origem, 2º = destino. Botão direito ou Esc cancela."""

    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas, self.callback = canvas, callback
        self.pontos, self.marcas = [], []
        self.anterior = canvas.mapTool()

    def _encerrar(self):
        for m in self.marcas:
            self.canvas.scene().removeItem(m)
        self.marcas = []
        if self.anterior:
            self.canvas.setMapTool(self.anterior)
        else:
            self.canvas.unsetMapTool(self)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._encerrar()
            iface.messageBar().pushInfo("Roteamento", "Cancelado.")

    def canvasReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self._encerrar()
            iface.messageBar().pushInfo("Roteamento", "Cancelado.")
            return
        p_mapa = self.toMapCoordinates(e.pos())
        m = QgsVertexMarker(self.canvas)
        m.setCenter(p_mapa)
        m.setColor(QColor("#2ca02c" if not self.pontos else "#d62728"))
        m.setIconSize(14)
        m.setPenWidth(3)
        self.marcas.append(m)
        tr = QgsCoordinateTransform(self.canvas.mapSettings().destinationCrs(),
                                    WGS84, QgsProject.instance())
        p = tr.transform(p_mapa)
        self.pontos.append((p.y(), p.x()))
        if len(self.pontos) == 1:
            iface.messageBar().pushInfo("Roteamento", "Origem marcada. Clique no DESTINO.")
            return
        self._encerrar()
        self.callback(*self.pontos)


def nova_rota():
    global _ferramenta
    _ferramenta = DoisCliques(iface.mapCanvas(), rotear)
    iface.mapCanvas().setMapTool(_ferramenta)
    iface.messageBar().pushInfo("Roteamento",
                                "Clique a ORIGEM no mapa (botão direito/Esc cancela).")


def principal():
    gpkg, _ = QFileDialog.getOpenFileName(
        iface.mainWindow(), "GeoPackage da malha (OSMnx)",
        QgsSettings().value("malha_osmnx/ultima_pasta", os.path.expanduser("~")),
        "GeoPackage (*.gpkg)")
    if not gpkg:
        return
    try:
        camadas = etapa1(gpkg)
    except RuntimeError as erro:
        QMessageBox.critical(iface.mainWindow(), "Inspeção", str(erro))
        return

    rotulos = list(PERFIS)
    escolha, ok = QInputDialog.getItem(iface.mainWindow(), "Roteamento", "Perfil:",
                                       rotulos, 0, False)
    if not ok:
        return

    if _estado.get("gpkg") != gpkg:             # carrega uma vez por arquivo
        G = carregar_grafo(gpkg, camadas)
        G_livre = grafo_sem_sentido(G)
        nodes = ox.graph_to_gdfs(G, edges=False)
        crs_m = _crs_metrico(nodes)
        nodes_m = nodes.to_crs(crs_m)
        scc = _nos_conectados(G, fortemente=True)
        wcc = _nos_conectados(G_livre, fortemente=False)
        print(f"[grafo] maior componente fortemente conexa: {len(scc):,} nós "
              f"({100 * len(scc) / len(nodes):.1f}%) | SRC métrico: {crs_m.to_string()}")
        _estado.update(gpkg=gpkg, camadas=camadas, G=G, G_livre=G_livre, crs_m=crs_m,
                       nodes_carro=nodes_m.loc[list(scc)], nodes_pe=nodes_m.loc[list(wcc)])
    _estado["perfil"] = PERFIS[escolha]
    nova_rota()


principal()
