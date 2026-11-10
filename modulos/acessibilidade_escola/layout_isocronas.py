# ============================================================
# LAYOUT DE IMPRESSÃO — IMÓVEIS POR ISÓCRONA A PÉ
# QGIS 3.44.x
#
# Lê o resultado de imoveis_por_isocrona.py (imoveis_por_isocrona.gpkg),
# monta um layout A4 paisagem com OSM de fundo e exporta PDF e PNG:
#   - mapa em SIRGAS 2000 / UTM 25S, com grade de coordenadas geográficas
#   - título, subtítulo, legenda, tabela de contagens com as cores das classes
#   - seta de norte, escala gráfica, fonte dos dados e data
#
# Atenção: o fundo OSM precisa de internet para baixar as tiles.
# Sem conexão, o layout sai com o fundo em branco.
#
# Uso: Plugins > Console Python > Mostrar Editor > abrir > Executar.
# ============================================================

import os
from datetime import date

from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeatureRequest,
    QgsPrintLayout,
    QgsLayoutItemPage,
    QgsLayoutItemMap,
    QgsLayoutItemMapGrid,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemScaleBar,
    QgsLayoutItemPicture,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLayoutExporter,
    QgsTextFormat,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsLegendStyle,
    QgsMapLayerLegendUtils,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont
from qgis.utils import iface


# ============================================================
# 1. PARÂMETROS
# ============================================================

PASTA = "/caminho/para/dados_curso/acessibilidade_escola"
GPKG = os.path.join(PASTA, "imoveis_por_isocrona.gpkg")

MINUTOS = [5, 10, 15, 20]
CORES = {5: "#ffffb2", 10: "#fecc5c", 15: "#fd8d3c", 20: "#e31a1c"}
OPACIDADE_ISOCRONA = 0.45
VELOCIDADE_KMH = 4.8

OSM_FONTE = ("type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png"
             "&zmax=19&zmin=0")

NOME_LAYOUT = "Imóveis por isócrona - Escola"
TITULO = "Acessibilidade a pé à escola"
SUBTITULO = (f"Imóveis alcançados em 5, 10, 15 e 20 minutos de caminhada "
             f"({str(VELOCIDADE_KMH).replace('.', ',')} km/h) — João Pessoa/PB")
AUTOR = ""               # ex.: "Elaboração: Fulano de Tal"

CRS_MAPA = "EPSG:31985"  # SIRGAS 2000 / UTM 25S (escala gráfica correta em metros)
INTERVALO_GRADE = 0.01   # graus
MARGEM_MAPA = 1.12       # folga em torno da isócrona de 20 min

PDF_SAIDA = os.path.join(PASTA, "layout_imoveis_isocronas.pdf")
PNG_SAIDA = os.path.join(PASTA, "layout_imoveis_isocronas.png")
DPI_PDF = 300
DPI_PNG = 200            # tiles OSM: evite DPI muito alto (política de uso)
ABRIR_DESIGNER = True

NOME_GRUPO = "Layout - isócronas"
FONTE = "Arial"
MM = Qgis.LayoutUnit.Millimeters


# ============================================================
# 2. ESTILOS (mesmas cores do script de análise)
# ============================================================

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
    cats = [QgsRendererCategory(m, simbolo_poligono(CORES[m], OPACIDADE_ISOCRONA),
                                f"{m} min") for m in MINUTOS]
    rend = QgsCategorizedSymbolRenderer('to_int("minutes")', cats)
    rend.setOrderBy(QgsFeatureRequest.OrderBy(
        [QgsFeatureRequest.OrderByClause('"minutes"', False)]))
    rend.setOrderByEnabled(True)
    lyr.setRenderer(rend)


def estilo_ponto(lyr):
    lyr.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({
        "name": "star", "color": "#2c7fb8", "outline_color": "#000000",
        "outline_width": "0.3", "size": "6"})))


# ============================================================
# 3. CAMADAS
# ============================================================

def grupo_layout():
    raiz = QgsProject.instance().layerTreeRoot()
    g = raiz.findGroup(NOME_GRUPO)
    return g if g else raiz.insertGroup(0, NOME_GRUPO)


def obter_camada(nome, rotulo):
    """Reaproveita a camada se já estiver no projeto; senão carrega do GPKG."""
    alvo = os.path.abspath(GPKG)
    for lyr in QgsProject.instance().mapLayers().values():
        partes = lyr.source().split("|")
        if os.path.abspath(partes[0]) == alvo and f"layername={nome}" in partes:
            return lyr
    lyr = QgsVectorLayer(f"{GPKG}|layername={nome}", rotulo, "ogr")
    if not lyr.isValid():
        raise Exception(f"Camada '{nome}' não encontrada em {GPKG}. "
                        "Rode antes o imoveis_por_isocrona.py.")
    QgsProject.instance().addMapLayer(lyr, False)
    grupo_layout().addLayer(lyr)
    return lyr


def obter_osm():
    for lyr in QgsProject.instance().mapLayers().values():
        if "tile.openstreetmap.org" in lyr.source():
            return lyr
    osm = QgsRasterLayer(OSM_FONTE, "OpenStreetMap", "wms")
    if not osm.isValid():
        raise Exception("Não foi possível criar a camada OpenStreetMap.")
    QgsProject.instance().addMapLayer(osm, False)
    QgsProject.instance().layerTreeRoot().addLayer(osm)   # vai para o fundo
    return osm


# ============================================================
# 4. ELEMENTOS DO LAYOUT
# ============================================================

def formato(tamanho, negrito=False, cor="#222222"):
    fonte = QFont(FONTE)
    fonte.setBold(negrito)
    fmt = QgsTextFormat()
    fmt.setFont(fonte)
    fmt.setSize(tamanho)
    fmt.setColor(QColor(cor))
    return fmt


def posicionar(item, x, y, w=None, h=None):
    item.attemptMove(QgsLayoutPoint(x, y, MM))
    if w is not None and h is not None:
        item.attemptResize(QgsLayoutSize(w, h, MM))


def rotulo(layout, texto, x, y, w, h, fmt, alinhamento=Qt.AlignLeft):
    lbl = QgsLayoutItemLabel(layout)
    lbl.setText(texto)
    lbl.setTextFormat(fmt)
    lbl.setHAlign(alinhamento)
    lbl.setVAlign(Qt.AlignVCenter)
    layout.addLayoutItem(lbl)
    posicionar(lbl, x, y, w, h)
    return lbl


def milhar(n):
    """1234 -> '1.234' (padrão brasileiro)."""
    return f"{n:,}".replace(",", ".")


def tabela_html(contagens, areas):
    linhas = []
    acum = 0
    for m in MINUTOS:
        n = contagens[m]
        acum += n
        area = areas.get(m)
        area_txt = f"{area:.2f}".replace(".", ",") if area is not None else "—"
        linhas.append(
            f"<tr><td><span style='background:{CORES[m]};border:1px solid #777;'>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;</span>&nbsp;{m} min</td>"
            f"<td align='right'>{area_txt}</td>"
            f"<td align='right'>{milhar(n)}</td>"
            f"<td align='right'>{milhar(acum)}</td></tr>")
    return f"""
<div style="font-family:{FONTE}; font-size:7.5pt; color:#222;">
<b>Imóveis alcançados por faixa de tempo</b>
<table style="border-collapse:collapse; width:100%; margin-top:3px;"
       cellpadding="2">
<tr style="border-bottom:1px solid #444;">
  <th align="left">Tempo</th><th align="right">Área (km²)</th>
  <th align="right">Na faixa</th><th align="right">Acumulado</th>
</tr>
{''.join(linhas)}
<tr style="border-top:1px solid #444;">
  <td><b>Total</b></td><td></td><td></td><td align="right"><b>{milhar(acum)}</b></td>
</tr>
</table>
<span style="font-size:6.5pt; color:#555;">Cada imóvel é contado só na menor
faixa que ele intersecta.</span>
</div>"""


def montar_layout():
    proj = QgsProject.instance()

    ponto = obter_camada("escola", "Ponto da análise")
    iso = obter_camada("isocronas", "Isócronas (plugin)")
    imoveis = {m: obter_camada(f"{m}_min", f"{m}_min") for m in MINUTOS}
    osm = obter_osm()

    estilo_ponto(ponto)
    estilo_isocronas(iso)
    for m, lyr in imoveis.items():
        lyr.setRenderer(QgsSingleSymbolRenderer(simbolo_poligono(CORES[m])))
    for lyr in [ponto, iso] + list(imoveis.values()):
        lyr.triggerRepaint()

    contagens = {m: imoveis[m].featureCount() for m in MINUTOS}
    areas = {}
    for f in iso.getFeatures():
        areas[int(round(float(f["minutes"])))] = float(f["area_km2"])

    # ---- layout A4 paisagem ----
    mgr = proj.layoutManager()
    antigo = mgr.layoutByName(NOME_LAYOUT)
    if antigo:
        mgr.removeLayout(antigo)
    layout = QgsPrintLayout(proj)
    layout.initializeDefaults()
    layout.setName(NOME_LAYOUT)
    layout.pageCollection().page(0).setPageSize("A4", QgsLayoutItemPage.Landscape)
    mgr.addLayout(layout)

    # ---- título ----
    rotulo(layout, TITULO, 10, 7, 277, 11, formato(18, True))
    rotulo(layout, SUBTITULO, 10, 17, 277, 7, formato(10, cor="#444444"))

    # ---- mapa ----
    mapa = QgsLayoutItemMap(layout)
    mapa.setCrs(QgsCoordinateReferenceSystem(CRS_MAPA))
    layout.addLayoutItem(mapa)
    posicionar(mapa, 18, 28, 186, 165)
    mapa.setFrameEnabled(True)
    mapa.setLayers([ponto] + [imoveis[m] for m in MINUTOS] + [iso, osm])
    mapa.setKeepLayerSet(True)

    xf = QgsCoordinateTransform(iso.crs(), mapa.crs(), proj)
    ext = xf.transformBoundingBox(iso.extent())
    ext.scale(MARGEM_MAPA)
    mapa.zoomToExtent(ext)

    # grade geográfica: rótulos à esquerda e embaixo
    grade = QgsLayoutItemMapGrid("Coordenadas", mapa)
    mapa.grids().addGrid(grade)
    grade.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    grade.setIntervalX(INTERVALO_GRADE)
    grade.setIntervalY(INTERVALO_GRADE)
    grade.setStyle(QgsLayoutItemMapGrid.FrameAnnotationsOnly)
    grade.setFrameStyle(QgsLayoutItemMapGrid.Zebra)
    grade.setFrameWidth(1.5)
    grade.setAnnotationEnabled(True)
    grade.setAnnotationFormat(QgsLayoutItemMapGrid.DecimalWithSuffix)
    grade.setAnnotationPrecision(2)
    grade.setAnnotationTextFormat(formato(6.5))
    for lado in (QgsLayoutItemMapGrid.Top, QgsLayoutItemMapGrid.Right):
        grade.setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, lado)
    grade.setAnnotationDirection(QgsLayoutItemMapGrid.Vertical,
                                 QgsLayoutItemMapGrid.Left)
    grade.setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal,
                                 QgsLayoutItemMapGrid.Bottom)
    mapa.updateBoundingRect()

    # ---- coluna da direita ----
    X, W = 211, 76

    legenda = QgsLayoutItemLegend(layout)
    legenda.setTitle("Legenda")
    legenda.setLinkedMap(mapa)
    legenda.setAutoUpdateModel(False)
    raiz = legenda.model().rootGroup()
    raiz.removeAllChildren()

    def item_legenda(grupo, lyr, texto):
        n = grupo.addLayer(lyr)
        n.setUseLayerName(False)
        n.setName(texto)
        if isinstance(lyr.renderer(), QgsSingleSymbolRenderer):
            # símbolo único: a legenda mostra o rótulo do símbolo, não o do nó
            QgsMapLayerLegendUtils.setLegendNodeUserLabel(n, 0, texto)
            legenda.model().refreshLayerLegend(n)

    item_legenda(raiz, ponto, "Escola (ponto da análise)")
    item_legenda(raiz, iso, "Isócronas a pé")
    g = raiz.addGroup("Imóveis por faixa")
    for m in MINUTOS:
        item_legenda(g, imoveis[m], f"{m} min")

    # fontes menores: com o padrão, a legenda invade a tabela (y = 108 mm)
    for estilo, tam, negrito in ((QgsLegendStyle.Title, 11, True),
                                 (QgsLegendStyle.Group, 8.5, True),
                                 (QgsLegendStyle.Subgroup, 8.5, True),
                                 (QgsLegendStyle.SymbolLabel, 7.5, False)):
        legenda.rstyle(estilo).setTextFormat(formato(tam, negrito))
    legenda.setSymbolHeight(3.5)
    legenda.setSymbolWidth(6)
    legenda.setFrameEnabled(False)
    layout.addLayoutItem(legenda)
    posicionar(legenda, X, 27)
    legenda.adjustBoxSize()

    tab = QgsLayoutItemLabel(layout)
    tab.setMode(QgsLayoutItemLabel.ModeHtml)
    tab.setText(tabela_html(contagens, areas))
    layout.addLayoutItem(tab)
    posicionar(tab, X, 108, W, 44)

    norte = QgsLayoutItemPicture(layout)
    norte.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
    norte.setLinkedMap(mapa)
    layout.addLayoutItem(norte)
    posicionar(norte, X, 154, 13, 17)

    escala = QgsLayoutItemScaleBar(layout)
    escala.setStyle("Single Box")
    escala.setLinkedMap(mapa)
    escala.applyDefaultSize(Qgis.DistanceUnit.Kilometers)
    escala.setNumberOfSegmentsLeft(0)
    escala.setUnitLabel("km")
    escala.setTextFormat(formato(7))
    layout.addLayoutItem(escala)
    posicionar(escala, X + 18, 157)
    escala.update()

    creditos = (
        "Fontes: © colaboradores do OpenStreetMap (ODbL); isócronas geradas "
        "com o plugin OSMnx Routing & Isochrones (malha 'all', perfil "
        f"pedestre, {str(VELOCIDADE_KMH).replace('.', ',')} km/h).\n"
        "Projeção: SIRGAS 2000 / UTM zona 25S (EPSG:31985). "
        "Grade em coordenadas geográficas (WGS 84).\n"
        f"{AUTOR + ' | ' if AUTOR else ''}Data: {date.today():%d/%m/%Y}"
    )
    rotulo(layout, creditos, X, 175, W, 18, formato(6.5, cor="#555555"))

    return layout


# ============================================================
# 5. EXPORTAÇÃO
# ============================================================

def exportar(layout):
    exp = QgsLayoutExporter(layout)

    pdf = QgsLayoutExporter.PdfExportSettings()
    pdf.dpi = DPI_PDF
    r = exp.exportToPdf(PDF_SAIDA, pdf)
    print("PDF:", PDF_SAIDA if r == QgsLayoutExporter.Success else f"erro ({r})")

    img = QgsLayoutExporter.ImageExportSettings()
    img.dpi = DPI_PNG
    r = exp.exportToImage(PNG_SAIDA, img)
    print("PNG:", PNG_SAIDA if r == QgsLayoutExporter.Success else f"erro ({r})")


def main():
    print("\nMontando layout...")
    layout = montar_layout()
    print("Exportando (as tiles do OSM podem demorar)...")
    exportar(layout)
    if ABRIR_DESIGNER:
        iface.openLayoutDesigner(layout)
    print("Layout:", NOME_LAYOUT)


main()
