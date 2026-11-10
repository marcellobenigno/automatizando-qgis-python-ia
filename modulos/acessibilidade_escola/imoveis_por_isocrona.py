# ============================================================
# IMÓVEIS (POLÍGONOS OSM) POR ISÓCRONA A PÉ — SEM INTERNET
# QGIS 3.44.x + plugin "OSMnx Routing & Isochrones"
#
# 1. Cria o ponto da escola.
# 2. Gera as isócronas de 5, 10, 15 e 20 min (osmnx_routing:isochrones),
#    a partir de uma malha já baixada (GeoPackage) — roda offline.
# 3. Atribui cada polígono à MENOR isócrona que ele intersecta
#    (as isócronas do plugin são cumulativas: a de 20 contém a de 15...).
#    Assim nenhum polígono aparece em duas camadas.
# 4. Salva num único GeoPackage: o ponto da análise (escola), as isócronas
#    geradas pelo plugin (isocronas) e os polígonos 5_min, 10_min, 15_min
#    e 20_min; imprime a contagem por faixa e acumulada.
#
# Uso: Plugins > Console Python > Mostrar Editor > abrir > Executar.
# ============================================================

import os

import processing
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsVectorFileWriter,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingUtils,
)
from qgis.core import (
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
)
from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface


# ============================================================
# 1. PARÂMETROS
# ============================================================

PASTA = "/caminho/para/dados_curso/acessibilidade_escola"

# Malhas baixadas antes (uma vez, com internet) pelo osmnx_routing:download_network
REDE_A_PE = os.path.join(PASTA, "malha_joao_pessoa_all.gpkg")    # TYPE = all (camadas arcos, nos...)
REDE_CARRO = os.path.join(PASTA, "malha_joao_pessoa_drive.gpkg")  # TYPE = drive

PERFIL = "a_pe"          # "a_pe" (PROFILE 1, malha all) ou "carro" (PROFILE 0, malha drive)

# Imóveis: camada imoveis_jp dentro do GPKG da malha (EPSG:4326, igual aos arcos)
POLIGONOS = os.path.join(PASTA, "malha_joao_pessoa_all.gpkg") + \
    "|layername=imoveis_jp"

# Escola (EPSG:4326: X = longitude, Y = latitude)
ESCOLA_X = -34.832828172
ESCOLA_Y = -7.106927411
ESCOLA_NOME = "Escola"

MINUTOS = [5, 10, 15, 20]
VELOCIDADE_KMH = 4.8     # usada se o algoritmo tiver parâmetro de velocidade

# Filtro opcional sobre os polígonos. Vazio = todos os polígonos.
# Ex.: só edificações -> '"building" IS NOT NULL'
FILTRO = ""

ARQ_ISOCRONAS = os.path.join(PASTA, "isocronas_escola.gpkg")
GPKG_SAIDA = os.path.join(PASTA, "imoveis_por_isocrona.gpkg")
NOME_GRUPO = "Imóveis por isócrona"

ALG_ID = "osmnx_routing:isochrones"

# Cores por classe (mesma cor para a isócrona e para os imóveis da faixa)
CORES = {5: "#ffffb2", 10: "#fecc5c", 15: "#fd8d3c", 20: "#e31a1c"}
OPACIDADE_ISOCRONA = 0.45   # preenchimento das isócronas (0 a 1)
SALVAR_ESTILO_NO_GPKG = True  # grava os estilos como padrão dentro do GPKG


# ============================================================
# FUNÇÕES
# ============================================================

def soltar_arquivo(caminho):
    """Remove do projeto camadas que usam o arquivo (evita arquivo travado)."""
    proj = QgsProject.instance()
    for lyr in list(proj.mapLayers().values()):
        if os.path.abspath(lyr.source().split("|")[0]) == os.path.abspath(caminho):
            proj.removeMapLayer(lyr.id())


def camada_escola():
    lyr = QgsVectorLayer("Point?crs=EPSG:4326&field=nome:string(80)",
                         "escola", "memory")
    f = QgsFeature(lyr.fields())
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(ESCOLA_X, ESCOLA_Y)))
    f["nome"] = ESCOLA_NOME
    lyr.dataProvider().addFeature(f)
    lyr.updateExtents()
    return lyr


def gerar_isocronas(pontos, context, feedback):
    alg = QgsApplication.processingRegistry().algorithmById(ALG_ID)
    if alg is None:
        raise Exception("Algoritmo osmnx_routing:isochrones não encontrado. "
                        "O plugin está instalado e ativo?")

    rede = REDE_A_PE if PERFIL == "a_pe" else REDE_CARRO
    if not os.path.exists(rede):
        raise Exception(f"Malha não encontrada: {rede}\n"
                        "Baixe uma vez com osmnx_routing:download_network "
                        "(TYPE all para a pé, drive para carro).")

    params = {
        "NETWORK": rede,
        "PROFILE": 1 if PERFIL == "a_pe" else 0,   # 1 = pedestre, 0 = carro
        "POINTS": pontos,
        "ID_FIELD": "nome",
        "SEPARATE": True,
        "MINUTES": ", ".join(str(m) for m in MINUTOS),
        "OUTPUT": ARQ_ISOCRONAS,
        "ROADS": "TEMPORARY_OUTPUT",
    }

    # O nome do parâmetro de velocidade não está documentado para isócronas:
    # procura pelo nome/descrição e só envia se existir.
    achou_vel = False
    if PERFIL == "a_pe":
        for d in alg.parameterDefinitions():
            txt = f"{d.name()} {d.description()}".lower()
            if "km/h" in txt or "speed" in txt or "veloc" in txt:
                params[d.name()] = VELOCIDADE_KMH
                achou_vel = True
                print(f"   velocidade: {d.name()} = {VELOCIDADE_KMH} km/h")
        if not achou_vel:
            print("   aviso: algoritmo sem parâmetro de velocidade; "
                  "vale o padrão do plugin (4,8 km/h na documentação).")

    soltar_arquivo(ARQ_ISOCRONAS)
    if os.path.exists(ARQ_ISOCRONAS):
        os.remove(ARQ_ISOCRONAS)

    try:
        res = processing.run(ALG_ID, params, context=context, feedback=feedback)
    except Exception:
        print(processing.algorithmHelp(ALG_ID))
        raise

    iso = QgsProcessingUtils.mapLayerFromString(res["OUTPUT"], context)
    if iso is None:
        iso = QgsVectorLayer(res["OUTPUT"], "isocronas", "ogr")
    if iso is None or not iso.isValid():
        raise Exception("Não foi possível abrir a camada de isócronas.")
    return iso


def geometrias_por_minuto(iso, crs_destino):
    """{minutos: geometria} no CRS dos polígonos (une se houver várias)."""
    xf = QgsCoordinateTransform(iso.crs(), crs_destino, QgsProject.instance())
    geoms = {}
    for ft in iso.getFeatures():
        m = int(round(float(ft["minutes"])))
        g = QgsGeometry(ft.geometry())
        g.transform(xf)
        if not g.isGeosValid():
            g = g.makeValid()
        geoms[m] = g if m not in geoms else geoms[m].combine(g)
    faltando = [m for m in MINUTOS if m not in geoms]
    if faltando:
        raise Exception(f"Isócronas ausentes na saída: {faltando}")
    return geoms


def classificar(poligonos, geoms):
    """Cada polígono vai para a menor isócrona que ele intersecta."""
    ordem = sorted(MINUTOS)
    engines = {}
    for m in ordem:
        eng = QgsGeometry.createGeometryEngine(geoms[m].constGet())
        eng.prepareGeometry()
        engines[m] = eng

    req = QgsFeatureRequest().setFilterRect(geoms[ordem[-1]].boundingBox())
    if FILTRO:
        req.setFilterExpression(FILTRO)

    grupos = {m: [] for m in ordem}
    invalidos = 0
    for f in poligonos.getFeatures(req):
        g = f.geometry()
        if g.isEmpty():
            continue
        if not g.isGeosValid():
            g = g.makeValid()
            invalidos += 1
        for m in ordem:
            if engines[m].intersects(g.constGet()):
                grupos[m].append((f, g))
                break
    if invalidos:
        print(f"   {invalidos} geometrias inválidas corrigidas em memória.")
    return grupos


def gravar(grupos, poligonos):
    soltar_arquivo(GPKG_SAIDA)
    if os.path.exists(GPKG_SAIDA):
        os.remove(GPKG_SAIDA)

    # 'fid' do GPKG de origem vira 'fid_origem' (evita conflito de chave).
    campos = QgsFields()
    campos.append(QgsField("fid_origem", QMetaType.Type.LongLong))
    nomes_origem = [c.name() for c in poligonos.fields() if c.name().lower() != "fid"]
    for c in poligonos.fields():
        if c.name().lower() != "fid":
            campos.append(c)
    campos.append(QgsField("isocrona_min", QMetaType.Type.Int))

    ctx = QgsProject.instance().transformContext()
    camadas = []
    primeira = True
    for m, itens in grupos.items():
        nome = f"{m}_min"
        opt = QgsVectorFileWriter.SaveVectorOptions()
        opt.driverName = "GPKG"
        opt.layerName = nome
        opt.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteFile if primeira
            else QgsVectorFileWriter.CreateOrOverwriteLayer)
        primeira = False

        w = QgsVectorFileWriter.create(GPKG_SAIDA, campos, poligonos.wkbType(),
                                       poligonos.crs(), ctx, opt)
        if w.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(f"Erro ao criar {nome}: {w.errorMessage()}")
        for f, g in itens:
            nf = QgsFeature(campos)
            nf.setGeometry(g)
            nf.setAttributes([f.id()] + [f[n] for n in nomes_origem] + [m])
            w.addFeature(nf)
        del w  # fecha e grava
        camadas.append(nome)
    return camadas


def gravar_camada(lyr, nome):
    """Copia uma camada (ponto ou isócronas) para o GPKG de saída."""
    opt = QgsVectorFileWriter.SaveVectorOptions()
    opt.driverName = "GPKG"
    opt.layerName = nome
    opt.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    erro, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
        lyr, GPKG_SAIDA, QgsProject.instance().transformContext(), opt)
    if erro != QgsVectorFileWriter.NoError:
        raise Exception(f"Erro ao gravar {nome}: {msg}")


def simbolo_poligono(cor_hex, opacidade=1.0):
    cor = QColor(cor_hex)
    cor.setAlphaF(opacidade)
    sym = QgsFillSymbol.createSimple({
        "outline_color": QColor(cor_hex).darker(160).name(),
        "outline_width": "0.26",
    })
    sym.symbolLayer(0).setFillColor(cor)
    return sym


def estilo_isocronas(lyr):
    cats = []
    for m in sorted(CORES):
        cats.append(QgsRendererCategory(
            m, simbolo_poligono(CORES[m], OPACIDADE_ISOCRONA), f"{m} min"))
    # 'minutes' é double no plugin -> classifica pelo inteiro
    rend = QgsCategorizedSymbolRenderer('to_int("minutes")', cats)
    # isócronas são cumulativas: desenha 20 min primeiro e 5 min por cima
    rend.setOrderBy(QgsFeatureRequest.OrderBy(
        [QgsFeatureRequest.OrderByClause('"minutes"', False)]))
    rend.setOrderByEnabled(True)
    lyr.setRenderer(rend)


def estilo_imoveis(lyr, minutos):
    lyr.setRenderer(QgsSingleSymbolRenderer(simbolo_poligono(CORES[minutos])))


def estilo_ponto(lyr):
    sym = QgsMarkerSymbol.createSimple({
        "name": "star", "color": "#2c7fb8", "outline_color": "#000000",
        "outline_width": "0.3", "size": "6",
    })
    lyr.setRenderer(QgsSingleSymbolRenderer(sym))


def aplicar_estilo(lyr, nome):
    if nome == "escola":
        estilo_ponto(lyr)
    elif nome == "isocronas":
        estilo_isocronas(lyr)
    else:
        estilo_imoveis(lyr, int(nome.split("_")[0]))
    lyr.triggerRepaint()
    if SALVAR_ESTILO_NO_GPKG:
        try:
            lyr.saveStyleToDatabase(nome, f"Estilo {nome}", True, "")
        except Exception as e:
            print(f"   aviso: estilo de {nome} não salvo no GPKG ({e})")


def carregar(camadas):
    proj = QgsProject.instance()
    raiz = proj.layerTreeRoot()
    antigo = raiz.findGroup(NOME_GRUPO)
    if antigo:
        raiz.removeChildNode(antigo)
    grupo = raiz.insertGroup(0, NOME_GRUPO)

    # ordem no painel: ponto, polígonos 5 -> 20 min, isócronas por último
    rotulos = {"escola": "Ponto da análise", "isocronas": "Isócronas (plugin)"}
    for nome in ["escola"] + camadas + ["isocronas"]:
        lyr = QgsVectorLayer(f"{GPKG_SAIDA}|layername={nome}",
                             rotulos.get(nome, nome), "ogr")
        if not lyr.isValid():
            print(f"   aviso: não foi possível carregar {nome}")
            continue
        aplicar_estilo(lyr, nome)
        proj.addMapLayer(lyr, False)
        grupo.addLayer(lyr)
        if nome == "isocronas":
            iface.setActiveLayer(lyr)
    iface.zoomToActiveLayer()


# ============================================================
# EXECUÇÃO
# ============================================================

def main():
    context = QgsProcessingContext()
    context.setProject(QgsProject.instance())
    feedback = QgsProcessingFeedback()

    print("\n1/4 - Abrindo polígonos...")
    poligonos = QgsVectorLayer(POLIGONOS, "poligonos_osm", "ogr")
    if not poligonos.isValid():
        raise Exception(f"Camada de polígonos inválida: {POLIGONOS}")

    print(f"2/4 - Gerando isócronas ({PERFIL}) {MINUTOS} min...")
    escola = camada_escola()
    iso = gerar_isocronas(escola, context, feedback)

    print("3/4 - Classificando polígonos pela menor isócrona...")
    geoms = geometrias_por_minuto(iso, poligonos.crs())
    grupos = classificar(poligonos, geoms)

    print("4/4 - Gravando camadas...")
    camadas = gravar(grupos, poligonos)
    gravar_camada(escola, "escola")        # ponto da análise
    gravar_camada(iso, "isocronas")        # isócronas como saíram do plugin
    carregar(camadas)

    print("\n" + "=" * 52)
    print(f"{'Isócrona':<10}{'Só nesta faixa':>16}{'Acumulado':>14}")
    print("-" * 52)
    acumulado = 0
    for m in sorted(grupos):
        n = len(grupos[m])
        acumulado += n
        print(f"{str(m) + ' min':<10}{n:>16}{acumulado:>14}")
    print("=" * 52)
    print("Arquivo:", GPKG_SAIDA)
    print("Camadas: escola, isocronas, " + ", ".join(camadas))
    if FILTRO:
        print("Filtro :", FILTRO)


main()
