"""
Perfil topográfico da PB-200 (QGIS 3.44).

Etapas:
  1. Filtra os trechos da rodovia na malha viária
  2. Reprojeta para SIRGAS 2000 / UTM 24S (EPSG:31984)
  3. Une os trechos em UMA linha, na ordem do km: inverte os trechos
     digitalizados ao contrário e relata as falhas entre eles
  4. Gera pontos a cada INTERVALO_M metros ao longo da linha
  5. Lê a altitude do MDE TOPODATA em cada ponto
  6. Salva GeoPackage + CSV e desenha o perfil (PNG) com matplotlib
  7. Faz verificações de consistência

O MDE vem do exercício da grade TOPODATA: a PB-200 inteira está na folha
07S375 (baixe com a ação de clique e informe o caminho em MDE).

Como usar: abra no Editor do Console Python do QGIS, ajuste as constantes
abaixo e clique em "Executar script".
"""
import csv
from pathlib import Path

import processing
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

# --------------------------------------------------------------------------
# Parâmetros — altere aqui
# --------------------------------------------------------------------------
GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"
MDE = "/caminho/para/TOPODATA/07S375ZN.tif"  # baixado pela ação de clique
PASTA_SAIDA = "/caminho/para/dados_curso/perfil_pb200/resultados"
RODOVIA = "PB-200"
CRS_METRICO = "EPSG:31984"  # SIRGAS 2000 / UTM 24S: fuso em que está a PB-200
INTERVALO_M = 30  # metros entre pontos (~ resolução do TOPODATA, 1″)
CARREGAR_NO_MAPA = True


def camada(nome):
    """Abre uma camada do GeoPackage e verifica se ela é válida."""
    lyr = QgsVectorLayer(f"{GPKG}|layername={nome}", nome, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"Não foi possível abrir a camada '{nome}' em {GPKG}")
    return lyr


def rodar(alg, params):
    """Executa um algoritmo em memória e devolve a camada de saída."""
    params.setdefault("OUTPUT", "TEMPORARY_OUTPUT")
    return processing.run(alg, params)["OUTPUT"]


def vertices(geom):
    """Lista de vértices (QgsPointXY) de uma linha simples ou multiparte."""
    if geom.isMultipart():
        partes = geom.asMultiPolyline()
        if len(partes) != 1:
            raise RuntimeError(f"Trecho com {len(partes)} partes: trate antes")
        return list(partes[0])
    return list(geom.asPolyline())


def unir_trechos(trechos):
    """Une trechos ordenados por km em uma linha só.

    Cada trecho é orientado para começar perto do fim do anterior.
    Devolve a geometria e a lista de falhas: (trecho, distância em m).
    """
    linhas = [vertices(f.geometry()) for f in trechos]

    # O 1º trecho é orientado pelo 2º: seu fim deve ser o lado que encosta nele
    if len(linhas) > 1:
        ini, fim = linhas[0][0], linhas[0][-1]
        prox = min(ini.distance(p) for p in (linhas[1][0], linhas[1][-1]))
        if prox < min(fim.distance(p) for p in (linhas[1][0], linhas[1][-1])):
            linhas[0].reverse()

    pontos = list(linhas[0])
    falhas = []
    for f, linha in zip(trechos[1:], linhas[1:]):
        ultimo = pontos[-1]
        if ultimo.distance(linha[-1]) < ultimo.distance(linha[0]):
            linha.reverse()  # digitalizado no sentido contrário ao km
        falha = ultimo.distance(linha[0])
        falhas.append((f["codigo"], falha))
        # Se os trechos se tocam, não repete o vértice comum
        pontos.extend(linha[1:] if falha < 0.01 else linha)
    return QgsGeometry.fromPolylineXY(pontos), falhas


saida = Path(PASTA_SAIDA)
saida.mkdir(parents=True, exist_ok=True)
prefixo = RODOVIA.lower().replace("-", "")  # "pb200"

mde = QgsRasterLayer(MDE, Path(MDE).stem)
if not mde.isValid():
    raise RuntimeError(f"MDE inválido ou não encontrado: {MDE}")

# 1. Filtrar a rodovia ------------------------------------------------------
rodovia = rodar("native:extractbyattribute", {
    "INPUT": camada("malha_viaria"),
    "FIELD": "rodovia_nome",
    "OPERATOR": 0,  # "="
    "VALUE": RODOVIA,
})
if rodovia.featureCount() == 0:
    raise RuntimeError(f"Nenhuma feição encontrada para {RODOVIA}")
print(f"[1] {RODOVIA}: {rodovia.featureCount()} trechos")

# 2. Reprojetar para um CRS métrico ----------------------------------------
rodovia_m = rodar("native:reprojectlayer", {
    "INPUT": rodovia, "TARGET_CRS": CRS_METRICO})
print(f"[2] Reprojetado para {CRS_METRICO}")

# 3. Unir os trechos em uma linha, na ordem do km ---------------------------
trechos = sorted(rodovia_m.getFeatures(), key=lambda f: f["km_inicial"])
for f in trechos:
    print(f"      {f['codigo']:<13} km {f['km_inicial']:6.2f} a {f['km_final']:6.2f}"
          f"  {f['sit_fisica']}")
linha_geom, falhas = unir_trechos(trechos)
comprimento_km = linha_geom.length() / 1000

linha = QgsVectorLayer(f"LineString?crs={CRS_METRICO}", f"{prefixo}_linha_unica", "memory")
linha.dataProvider().addAttributes([
    QgsField("rodovia_nome", QMetaType.Type.QString),
    QgsField("comprimento_km", QMetaType.Type.Double),
])
linha.updateFields()
feicao = QgsFeature(linha.fields())
feicao.setGeometry(linha_geom)
feicao.setAttributes([RODOVIA, round(comprimento_km, 3)])
linha.dataProvider().addFeature(feicao)
print(f"[3] Linha única: {comprimento_km:.2f} km")
for codigo, falha in falhas:
    if falha >= 1:
        print(f"      falha de {falha:6.1f} m antes de {codigo} (ligada em linha reta)")

# 4. Pontos ao longo da linha -----------------------------------------------
pontos = rodar("native:pointsalonglines", {
    "INPUT": linha, "DISTANCE": INTERVALO_M})
print(f"[4] {pontos.featureCount()} pontos a cada {INTERVALO_M} m")

# 5. Altitude de cada ponto -------------------------------------------------
# O rastersampling reprojeta os pontos sozinho, mas levamos os pontos para o
# CRS do MDE (EPSG:4326) para o CSV sair em longitude/latitude
pontos_mde = rodar("native:reprojectlayer", {
    "INPUT": pontos, "TARGET_CRS": mde.crs()})
pontos_z = rodar("native:rastersampling", {
    "INPUT": pontos_mde, "RASTERCOPY": mde, "COLUMN_PREFIX": "z_"})
pontos_z.setName(f"{prefixo}_pontos_z")

perfil = []  # (km, lon, lat, altitude)
sem_cota = 0
for f in sorted(pontos_z.getFeatures(), key=lambda f: f["distance"]):
    z = f["z_1"]
    if z is None or z == mde.dataProvider().sourceNoDataValue(1):
        sem_cota += 1  # NULL: fora do raster ou NoData
        continue
    p = f.geometry().asPoint()
    perfil.append((f["distance"] / 1000, p.x(), p.y(), float(z)))
if not perfil:
    raise RuntimeError("Nenhum ponto com altitude: a linha está sobre o MDE?")
altitudes = [z for *_, z in perfil]
z_min, z_max = min(altitudes), max(altitudes)
z_med = sum(altitudes) / len(altitudes)
print(f"[5] Altitude: mín. {z_min:.1f} m · máx. {z_max:.1f} m · média {z_med:.1f} m")

# 6. Salvar resultados e desenhar o perfil ----------------------------------
gpkg_saida = str(saida / f"{prefixo}_perfil.gpkg")
processing.run("native:package", {
    "LAYERS": [linha, pontos_z], "OUTPUT": gpkg_saida, "OVERWRITE": True})

csv_saida = saida / f"{prefixo}_perfil.csv"
with open(csv_saida, "w", newline="", encoding="utf-8") as arq:
    escritor = csv.writer(arq)
    escritor.writerow(["km", "lon", "lat", "altitude_m"])
    escritor.writerows((f"{km:.3f}", f"{x:.6f}", f"{y:.6f}", f"{z:.1f}")
                       for km, x, y, z in perfil)
print(f"[6] Resultados salvos em {saida}")

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    print("      matplotlib não instalado: o gráfico não foi gerado. "
          "O CSV está pronto.")

if plt:
    km = [k for k, *_ in perfil]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(km, altitudes, color="saddlebrown", linewidth=1)
    ax.fill_between(km, altitudes, z_min, color="saddlebrown", alpha=0.15)
    for valor, cor, rotulo in [(z_max, "tab:red", "Máx."),
                               (z_med, "goldenrod", "Média"),
                               (z_min, "tab:green", "Mín.")]:
        ax.axhline(valor, color=cor, linestyle="--", linewidth=1,
                   label=f"{rotulo}: {valor:.0f} m")
    ax.set_xlim(0, km[-1])
    ax.set_xlabel("Distância ao longo da rodovia (km)")
    ax.set_ylabel("Altitude (m, EGM96)")
    ax.set_title(f"Perfil topográfico da {RODOVIA} ({comprimento_km:.1f} km)"
                 f" — TOPODATA {Path(MDE).stem[:6]}")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    png_saida = saida / f"{prefixo}_perfil.png"
    fig.savefig(png_saida, dpi=150)
    print(f"      Gráfico: {png_saida}")
    plt.show()

# 7. Verificações de consistência -------------------------------------------
soma_extensao = sum(f["extensao"] for f in trechos)
print("[7] Verificações")
print(f"      CRS da linha: {linha.crs().authid()} (esperado {CRS_METRICO})")
print(f"      Comprimento:  {comprimento_km:.2f} km × soma de 'extensao' "
      f"{soma_extensao:.2f} km ({comprimento_km / soma_extensao:.1%})")
print(f"      Pontos sem altitude: {sem_cota} de {pontos_z.featureCount()}")
# Diferença grande no comprimento indica trecho invertido mal ligado
# (a linha "vai e volta") ou trecho faltando — confira no mapa!

if CARREGAR_NO_MAPA:
    projeto = QgsProject.instance()
    if not projeto.mapLayersByName(mde.name()):
        projeto.addMapLayer(mde)
    for nome in ["linha_unica", "pontos_z"]:
        projeto.addMapLayer(
            QgsVectorLayer(f"{gpkg_saida}|layername={prefixo}_{nome}",
                           f"{prefixo}_{nome}", "ogr"))
