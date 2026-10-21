# -*- coding: utf-8 -*-
"""
Alcance a partir do IFPB Campus João Pessoa (QGIS 3.44 + NetworkX), offline.

Até onde se chega andando 800 m e dirigindo 4 km pelas ruas?

A malha viária NÃO é baixada aqui. Ela vem do GeoPackage gerado uma única
vez com o OSMnx (apoio/osmnx/malha_urbana_osmnx.py, rede "all"): camadas
'nodes', 'arcos' e 'limite'. Daqui em diante, tudo roda sem internet, só
com PyQGIS e NetworkX.

Etapas:
  1. Lê 'nodes' e 'arcos' e monta dois grafos: a pé (todas as vias por
     onde se anda, nos dois sentidos) e de carro (vias de automóvel; cada
     arco já está no sentido do tráfego, então a mão única é respeitada)
  2. Liga o campus ao nó mais próximo de cada rede
  3. Calcula a distância pela rede do campus a cada nó (Dijkstra com
     limite) e corta cada arco nas faixas de distância
  4. Mede o alcance: km de vias, ponto mais distante, polígono do alcance
     × círculo e, para o carro, o efeito da mão única
  5. Confere o resultado com a "Área de serviço" nativa do QGIS
  6. Salva o GeoPackage, desenha os mapas e carrega as camadas no QGIS

Como usar: abra no Editor do Console Python do QGIS, ajuste as constantes
abaixo e clique em "Executar script".
"""
import ast
import time
from pathlib import Path

import networkx as nx

import processing
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFillSymbol,
    QgsGeometry,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPointXY,
    QgsProject,
    QgsRendererCategory,
    QgsSpatialIndex,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

# --------------------------------------------------------------------------
# Parâmetros — altere aqui
# --------------------------------------------------------------------------
MALHA = "/caminho/para/dados_curso/alcance_ifpb/malha_joao_pessoa_all.gpkg"
PASTA_SAIDA = "/caminho/para/dados_curso/alcance_ifpb/resultados"
# Centro do terreno do campus no OpenStreetMap (lon, lat em WGS 84)
CENTRO = ("IFPB Campus João Pessoa", -34.87354, -7.13574)
CRS_METRICO = "EPSG:31985"  # SIRGAS 2000 / UTM 25S: faixa litorânea

# Cada análise: tipos de via (campo 'highway'), se respeita a mão única e
# as faixas de distância (m) pela rede; a última faixa é o alcance
ANALISES = {
    "pe": {
        "titulo": "A pé",
        "vias": {"trunk", "primary", "secondary", "tertiary", "unclassified",
                 "residential", "living_street", "service", "pedestrian",
                 "footway", "path", "steps", "track", "corridor"},
        "mao_unica": False,  # quem anda não respeita mão única
        "faixas": [200, 400, 600, 800],  # 800 m ≈ 10 min a 4,8 km/h
    },
    "carro": {
        "titulo": "De carro",
        "vias": {"motorway", "trunk", "primary", "secondary", "tertiary",
                 "unclassified", "residential", "living_street"},
        "mao_unica": True,
        "faixas": [1000, 2000, 3000, 4000],
    },
}
ACESSO_PROIBIDO = {"private", "no"}  # campo 'access'
COMPARAR_COM_QGIS = True  # confere cada alcance com native:serviceareafrompoint
CARREGAR_NO_MAPA = True

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
METRICO = QgsCoordinateReferenceSystem(CRS_METRICO)
# Uma cor por faixa: da mais perto (escura) à mais longe (clara)
CORES = ["#253494", "#2c7fb8", "#41b6c4", "#a1dab4"]


def tipos(valor):
    """O OSMnx grava listas como texto: "['service', 'residential']"."""
    valor = str(valor)
    if valor.startswith("["):
        return {t.removesuffix("_link") for t in ast.literal_eval(valor)}
    return {valor.removesuffix("_link")}


def camada(nome):
    """Abre uma camada da malha e verifica se ela é válida."""
    lyr = QgsVectorLayer(f"{MALHA}|layername={nome}", nome, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"Não foi possível abrir a camada '{nome}' em {MALHA}")
    return lyr


def ler_malha():
    """Nós (osmid → ponto em UTM) e arcos (u, v, comprimento, geometria em UTM)."""
    nodes_lyr, arcos_lyr = camada("nodes"), camada("arcos")
    para_m = QgsCoordinateTransform(arcos_lyr.crs(), METRICO, QgsProject.instance())
    nos = {}
    for f in nodes_lyr.getFeatures():
        nos[int(f["osmid"])] = para_m.transform(QgsPointXY(f["x"], f["y"]))
    arcos = []
    campos = ["u", "v", "length", "highway", "oneway", "access"]
    pedido = QgsFeatureRequest().setSubsetOfAttributes(campos, arcos_lyr.fields())
    for f in arcos_lyr.getFeatures(pedido):
        g = f.geometry()
        g.transform(para_m)
        u, v = int(f["u"]), int(f["v"])
        arcos.append({"u": u, "v": v, "length": f["length"],
                      # ida e volta da mesma rua: mesmos nós e comprimento
                      "fisico": (min(u, v), max(u, v), round(f["length"], 1)),
                      "tipos": tipos(f["highway"]), "oneway": bool(f["oneway"]),
                      "access": f["access"], "geom": g})
    return nos, arcos


def montar_grafo(arcos, analise, mao_unica):
    """Grafo da análise: só os arcos dos tipos de via permitidos.

    Na camada 'arcos', a mão dupla já tem os dois sentidos (2 arcos). Sem
    mão única, cada trecho de mão única ganha também o arco de volta.
    """
    grafo = nx.MultiDiGraph()
    usados = []
    for i, a in enumerate(arcos):
        if a["access"] in ACESSO_PROIBIDO:
            continue
        if analise["mao_unica"]:
            # carro: todos os tipos do trecho têm de ser de automóvel
            if not a["tipos"] <= analise["vias"]:
                continue
        elif not a["tipos"] & analise["vias"]:
            continue  # a pé: basta um tipo por onde se anda
        grafo.add_edge(a["u"], a["v"], key=i, length=a["length"], arco=i)
        if a["oneway"] and not mao_unica:
            # a volta usa a geometria invertida (índice negativo)
            grafo.add_edge(a["v"], a["u"], key=-i - 1, length=a["length"], arco=-i - 1)
        usados.append(i)
    return grafo, usados


def geometria(arcos, arco):
    """Geometria do arco no sentido do percurso (índice negativo = volta)."""
    if arco >= 0:
        return arcos[arco]["geom"]
    return QgsGeometry(arcos[-arco - 1]["geom"].constGet().reversed())


def no_mais_proximo(nos, candidatos, ponto):
    """Nó mais próximo do ponto, entre os candidatos (índice espacial)."""
    indice = QgsSpatialIndex()
    ids = list(candidatos)
    for i, osmid in enumerate(ids):
        f = QgsFeature(i)
        f.setGeometry(QgsGeometry.fromPointXY(nos[osmid]))
        indice.addFeature(f)
    perto = ids[indice.nearestNeighbor(ponto, 1)[0]]
    return perto, nos[perto].distance(ponto)


def intervalos(trecho, b):
    """Partes de um trecho físico (em m, a partir do início) alcançadas até b.

    Chega-se a um ponto a s metros do início pelo início (dist + s) ou
    pelo fim (dist + comprimento - s), se o sentido permitir.
    """
    comprimento = trecho["length"]
    partes = []
    if trecho["inicio"] in trecho["lados"]:
        a = min(comprimento, b - trecho["lados"][trecho["inicio"]])
        if a > 0:
            partes.append((0, a))
    if trecho["fim"] in trecho["lados"]:
        c = min(comprimento, b - trecho["lados"][trecho["fim"]])
        if c > 0:
            partes.append((comprimento - c, comprimento))
    if len(partes) == 2 and partes[0][1] >= partes[1][0]:
        partes = [(0, comprimento)]  # as duas pontas se encontram
    return partes


def menos(partes, anteriores):
    """Intervalos de 'partes' que não estão em 'anteriores'."""
    resto = []
    for ini, fim in partes:
        for a_ini, a_fim in anteriores:
            if a_fim <= ini or a_ini >= fim:
                continue
            if a_ini > ini:
                resto.append((ini, a_ini))
            ini = max(ini, a_fim)
        if fim > ini:
            resto.append((ini, fim))
    return resto


def faixas_de_alcance(grafo, arcos, distancias, faixas):
    """Corta as vias nas faixas de distância.

    Trabalha por trecho físico de rua: na mão dupla, os dois arcos (ida e
    volta) são a mesma rua e não podem ser contados duas vezes. Devolve,
    por faixa, a geometria e os km do "anel" (o que entrou nessa faixa e
    não estava na anterior), e a geometria do alcance total.
    """
    trechos = {}
    for u, _, dados in grafo.edges(data=True):
        if u not in distancias:
            continue  # o início do arco não foi alcançado
        indice = dados["arco"] if dados["arco"] >= 0 else -dados["arco"] - 1
        a = arcos[indice]
        t = trechos.setdefault(a["fisico"], {
            "geom": a["geom"], "inicio": a["u"], "fim": a["v"],
            "length": a["length"], "lados": {}})
        t["lados"][u] = min(distancias[u], t["lados"].get(u, float("inf")))
    aneis, km = {}, {}
    anteriores = {chave: [] for chave in trechos}
    pedacos_total = []
    for b in faixas:
        pedacos, metros = [], 0.0
        for chave, t in trechos.items():
            partes = intervalos(t, b)
            novas = menos(partes, anteriores[chave])
            anteriores[chave] = partes
            # 'length' do OSMnx é geodésico; a geometria está em UTM
            fator = t["geom"].length() / t["length"] if t["length"] else 1
            for ini, fim in novas:
                metros += fim - ini
                pedacos.append(QgsGeometry(
                    t["geom"].constGet().curveSubstring(ini * fator, fim * fator)))
        aneis[b] = QgsGeometry.collectGeometry(pedacos)
        km[b] = metros / 1000
        pedacos_total += pedacos
    return aneis, km, QgsGeometry.collectGeometry(pedacos_total)


def alcance_qgis(arcos, usados, analise, ponto, distancia):
    """Mesmo alcance com o algoritmo nativo do QGIS, sobre os mesmos arcos.

    Carro: cada arco está no sentido do tráfego, então vale só "para frente".
    """
    rede = QgsVectorLayer(f"LineString?crs={CRS_METRICO}", "rede", "memory")
    feicoes = []
    for i in usados:
        f = QgsFeature()
        f.setGeometry(arcos[i]["geom"])
        feicoes.append(f)
    rede.dataProvider().addFeatures(feicoes)
    linhas = processing.run("native:serviceareafrompoint", {
        "INPUT": rede, "STRATEGY": 0, "TOLERANCE": 0,
        "DEFAULT_DIRECTION": 0 if analise["mao_unica"] else 2,
        "START_POINT": f"{ponto.x()},{ponto.y()} [{CRS_METRICO}]",
        "TRAVEL_COST2": distancia, "OUTPUT_LINES": "TEMPORARY_OUTPUT"})["OUTPUT_LINES"]
    return QgsGeometry.unaryUnion([f.geometry() for f in linhas.getFeatures()])


def camada_memoria(tipo, nome, campos):
    """Camada em memória em EPSG:31985 com os campos [(nome, tipo)]."""
    lyr = QgsVectorLayer(f"{tipo}?crs={CRS_METRICO}", nome, "memory")
    lyr.dataProvider().addAttributes([QgsField(n, t) for n, t in campos])
    lyr.updateFields()
    return lyr


saida = Path(PASTA_SAIDA)
saida.mkdir(parents=True, exist_ok=True)
nome_centro, lon, lat = CENTRO
ponto = QgsCoordinateTransform(WGS84, METRICO, QgsProject.instance()) \
    .transform(QgsPointXY(lon, lat))
ponto_geom = QgsGeometry.fromPointXY(ponto)

# 1. Malha do GeoPackage (offline) ------------------------------------------
inicio = time.time()
nos, arcos = ler_malha()
print(f"[1] {len(nos)} nós e {len(arcos)} arcos lidos de {Path(MALHA).name} "
      f"em {time.time() - inicio:.1f} s, sem internet")
limite_lyr = camada("limite")
limite = next(limite_lyr.getFeatures()).geometry()
limite.transform(QgsCoordinateTransform(limite_lyr.crs(), METRICO, QgsProject.instance()))

faixas_lyr = camada_memoria("MultiLineString", "alcance_faixas", [
    ("modo", QMetaType.Type.QString), ("faixa_m", QMetaType.Type.Int),
    ("km", QMetaType.Type.Double)])
poligonos_lyr = camada_memoria("Polygon", "alcance_poligonos", [
    ("modo", QMetaType.Type.QString), ("tipo", QMetaType.Type.QString),
    ("area_km2", QMetaType.Type.Double)])
resultados = {}
for modo, analise in ANALISES.items():
    titulo, faixas = analise["titulo"], analise["faixas"]
    raio = faixas[-1]
    grafo, usados = montar_grafo(arcos, analise, analise["mao_unica"])
    print(f"\n[1] {titulo}: grafo com {grafo.number_of_nodes()} nós e "
          f"{grafo.number_of_edges()} arcos")

    # 2. Campus → nó mais próximo, de onde se chega a toda a rede ------------
    principal = max(nx.strongly_connected_components(grafo), key=len)
    origem, snap = no_mais_proximo(nos, principal, ponto)
    print(f"[2] Partida no nó {origem}, a {snap:.0f} m do campus")

    # 3. Distância pela rede até cada nó e faixas de alcance ----------------
    inicio = time.time()
    distancias = nx.single_source_dijkstra_path_length(
        grafo, origem, cutoff=raio, weight="length")
    aneis, km, total = faixas_de_alcance(grafo, arcos, distancias, faixas)
    print(f"[3] {len(distancias)} nós a até {raio} m pela rede "
          f"({time.time() - inicio:.1f} s)")

    # 4. Medidas do alcance -------------------------------------------------
    vias_km = sum(km.values())  # soma dos anéis
    longe = max(QgsGeometry.fromPointXY(QgsPointXY(v)).distance(ponto_geom)
                for v in total.vertices())
    poligono = total.concaveHull(0.3)
    circulo = ponto_geom.buffer(raio, 32)
    indice = poligono.area() / circulo.area()
    resultados[modo] = {"vias_km": vias_km, "longe": longe, "indice": indice,
                        "aneis": aneis, "poligono": poligono, "circulo": circulo,
                        "usados": usados, "origem": origem}
    print(f"[4] {vias_km:.1f} km de vias alcançadas; ponto mais distante a "
          f"{longe:.0f} m em linha reta")
    print(f"      polígono do alcance: {poligono.area() / 1e6:.2f} km² = {indice:.0%} "
          f"do círculo de {raio} m ({circulo.area() / 1e6:.2f} km²)")
    if not limite.contains(total):
        print("      ATENÇÃO: o alcance sai do limite da malha; ela é pequena "
              "demais para esta distância")
    if analise["mao_unica"]:
        livre, _ = montar_grafo(arcos, analise, mao_unica=False)
        d_livre = nx.single_source_dijkstra_path_length(
            livre, origem, cutoff=raio, weight="length")
        _, km_livre, total_livre = faixas_de_alcance(livre, arcos, d_livre, [raio])
        extra = km_livre[raio] - vias_km
        resultados[modo].update(sem_mao_unica=total_livre, livre_km=km_livre[raio])
        print(f"      ignorando a mão única: {km_livre[raio]:.1f} km "
              f"(+{extra:.1f} km, {extra / vias_km:.0%} a mais)")

    # 5. Conferência com o QGIS ---------------------------------------------
    if COMPARAR_COM_QGIS:
        qgis = alcance_qgis(arcos, usados, analise, ponto, raio)
        # O QGIS devolve ida e volta da mesma rua como linhas sobrepostas:
        # a área de uma faixa de 1 m em volta mede cada rua uma vez só
        km_qgis = qgis.buffer(0.5, 2).area() / 1000
        resultados[modo]["qgis"] = qgis
        print(f"[5] QGIS (Área de serviço): {km_qgis:.1f} km × NetworkX "
              f"{vias_km:.1f} km ({km_qgis / vias_km - 1:+.1%})")

    for b in faixas:
        f = QgsFeature(faixas_lyr.fields())
        f.setGeometry(aneis[b])
        f.setAttributes([modo, b, round(km[b], 2)])
        faixas_lyr.dataProvider().addFeature(f)
    for tipo, geom in [("alcance", poligono), ("circulo", circulo)]:
        f = QgsFeature(poligonos_lyr.fields())
        f.setGeometry(geom)
        f.setAttributes([modo, tipo, round(geom.area() / 1e6, 3)])
        poligonos_lyr.dataProvider().addFeature(f)

# 6. Salvar, desenhar e carregar --------------------------------------------
campus_lyr = camada_memoria("Point", "campus", [("nome", QMetaType.Type.QString)])
f = QgsFeature(campus_lyr.fields())
f.setGeometry(ponto_geom)
f.setAttributes([nome_centro])
campus_lyr.dataProvider().addFeature(f)

gpkg_saida = str(saida / "alcance_ifpb.gpkg")
processing.run("native:package", {
    "LAYERS": [faixas_lyr, poligonos_lyr, campus_lyr],
    "OUTPUT": gpkg_saida, "OVERWRITE": True})
print(f"\n[6] Resultados em {gpkg_saida}")

try:
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
except ImportError:
    plt = None
    print("      matplotlib não instalado: os mapas não foram gerados.")


def linhas_km(geom):
    """Coordenadas em km a partir do campus, para o matplotlib."""
    partes = geom.asMultiPolyline() if geom.isMultipart() else [geom.asPolyline()]
    return [[((p.x() - ponto.x()) / 1000, (p.y() - ponto.y()) / 1000) for p in parte]
            for parte in partes if parte]


if plt:
    fig, eixos = plt.subplots(1, len(ANALISES), figsize=(15, 8.6))
    for ax, (modo, analise) in zip(eixos, ANALISES.items()):
        r = resultados[modo]
        raio = analise["faixas"][-1]
        fina = raio > 1000  # escala da cidade: linhas mais finas
        lim = raio * 1.15
        janela = QgsGeometry.fromRect(ponto_geom.buffer(lim, 4).boundingBox())
        fundo = [s for i in r["usados"] if arcos[i]["geom"].intersects(janela)
                 for s in linhas_km(arcos[i]["geom"])]
        ax.add_collection(LineCollection(fundo, colors="#e3e3e3",
                                         linewidths=0.4 if fina else 0.9))
        for (b, anel), cor in zip(r["aneis"].items(), CORES):
            rotulo = f"até {b} m" if b < 1000 else f"até {b / 1000:g} km"
            ax.add_collection(LineCollection(linhas_km(anel), colors=cor,
                                             linewidths=0.9 if fina else 2.2,
                                             label=rotulo))
        for geom, estilo in [
                (r["circulo"], {"color": "black", "linestyle": "--", "linewidth": 1.2,
                                "label": f"círculo de {raio} m"}),
                (r["poligono"], {"color": "#e6550d", "linewidth": 1.6,
                                 "label": f"polígono do alcance ({r['indice']:.0%} do círculo)"})]:
            anel = linhas_km(QgsGeometry.fromPolylineXY(geom.asPolygon()[0]))[0]
            ax.plot(*zip(*anel), **estilo)
        ax.plot(0, 0, "o", color="#e6550d", markersize=9, markeredgecolor="white",
                zorder=5, label=nome_centro)
        ax.set_xlim(-lim / 1000, lim / 1000)
        ax.set_ylim(-lim / 1000, lim / 1000)
        ax.set_aspect("equal")
        distancia = f"{raio} m" if raio < 1000 else f"{raio / 1000:g} km"
        ax.set_title(f"{analise['titulo']}: {distancia} pela rede",
                     fontsize=14, fontweight="bold")
        ax.set_xlabel("km a leste do campus")
        ax.set_ylabel("km ao norte do campus")
        ax.grid(alpha=0.25)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=9.5,
                  frameon=False)
    fig.suptitle(f"Alcance a partir do {nome_centro}", fontsize=15)
    fig.text(0.5, 0.01, "Malha viária: © colaboradores do OpenStreetMap (ODbL), via OSMnx",
             ha="center", fontsize=8, color="#666")
    fig.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.2, wspace=0.15)
    png_saida = saida / "alcance_ifpb.png"
    fig.savefig(png_saida, dpi=150)
    print(f"      Mapas: {png_saida}")
    plt.show()

if CARREGAR_NO_MAPA:
    projeto = QgsProject.instance()
    for nome in ["alcance_poligonos", "alcance_faixas", "campus"]:
        lyr = QgsVectorLayer(f"{gpkg_saida}|layername={nome}", nome, "ogr")
        if nome == "alcance_faixas":
            # Uma cor por faixa, nas duas análises
            categorias = []
            for analise in ANALISES.values():
                for b, cor in zip(analise["faixas"], CORES):
                    simbolo = QgsLineSymbol.createSimple({"color": cor, "width": "0.8"})
                    categorias.append(QgsRendererCategory(b, simbolo, f"até {b} m"))
            lyr.setRenderer(QgsCategorizedSymbolRenderer("faixa_m", categorias))
        elif nome == "alcance_poligonos":
            lyr.renderer().setSymbol(QgsFillSymbol.createSimple({
                "color": "0,0,0,0", "outline_color": "#e6550d", "outline_width": "0.6"}))
        else:
            lyr.renderer().setSymbol(QgsMarkerSymbol.createSimple(
                {"color": "#e6550d", "size": "4"}))
        projeto.addMapLayer(lyr)
