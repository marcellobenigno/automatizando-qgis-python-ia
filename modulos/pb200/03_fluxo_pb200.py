"""
Módulo 4 — Fluxo automatizado: áreas de influência da PB-200.

Etapas:
  1. Filtra a rodovia na malha viária
  2. Reprojeta para SIRGAS 2000 / UTM 24S (EPSG:31984)
  3. Gera os buffers ADA (1 km) e AII (3 km)
  4. Calcula a área da AII em cada município (km² e % do município)
  5. Recorta o uso e ocupação do solo pela AII e soma a área (ha) por classe
  6. Salva tudo em um GeoPackage + CSVs e faz verificações de consistência

Como usar: abra no Editor do Console Python do QGIS, ajuste as constantes
abaixo e clique em "Executar script".
"""
from pathlib import Path

import processing
from qgis.core import QgsProject, QgsVectorLayer

# --------------------------------------------------------------------------
# Parâmetros — altere aqui
# --------------------------------------------------------------------------
GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"
PASTA_SAIDA = "/caminho/para/dados_curso/pb200/resultados"
RODOVIA = "PB-200"
CRS_METRICO = "EPSG:31984"  # SIRGAS 2000 / UTM 24S: fuso em que está a PB-200
DIST_ADA = 1000  # metros
DIST_AII = 3000  # metros
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


saida = Path(PASTA_SAIDA)
saida.mkdir(parents=True, exist_ok=True)
prefixo = RODOVIA.lower().replace("-", "")  # "pb200"

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

municipios_m = rodar("native:reprojectlayer", {
    "INPUT": camada("municipios"), "TARGET_CRS": CRS_METRICO})
municipios_m = rodar("native:fieldcalculator", {
    "INPUT": municipios_m,
    "FIELD_NAME": "area_mun_km2", "FIELD_TYPE": 0, "FIELD_PRECISION": 4,
    "FORMULA": "$area / 1e6",
})
print(f"[2] Reprojetado para {CRS_METRICO}")

# 3. Buffers (dissolvidos: uma única área por faixa) -------------------------
ada = rodar("native:buffer", {
    "INPUT": rodovia_m, "DISTANCE": DIST_ADA, "DISSOLVE": True})
aii = rodar("native:buffer", {
    "INPUT": rodovia_m, "DISTANCE": DIST_AII, "DISSOLVE": True})
area_aii_km2 = next(aii.getFeatures()).geometry().area() / 1e6
print(f"[3] AII ({DIST_AII} m): {area_aii_km2:.2f} km²")

# 4. AII x municípios -------------------------------------------------------
aii_mun = rodar("native:intersection", {
    "INPUT": municipios_m, "OVERLAY": aii,
    "INPUT_FIELDS": ["nome", "cod_ibge_m", "populacao_total", "area_mun_km2"],
    "OVERLAY_FIELDS": ["rodovia_nome"],
})
aii_mun = rodar("native:fieldcalculator", {
    "INPUT": aii_mun,
    "FIELD_NAME": "area_aii_km2", "FIELD_TYPE": 0, "FIELD_PRECISION": 4,
    "FORMULA": "$area / 1e6",
})
aii_mun = rodar("native:fieldcalculator", {
    "INPUT": aii_mun,
    "FIELD_NAME": "pct_mun", "FIELD_TYPE": 0, "FIELD_PRECISION": 2,
    "FORMULA": '"area_aii_km2" / "area_mun_km2" * 100',
})
print(f"[4] Municípios afetados: {aii_mun.featureCount()}")
for f in sorted(aii_mun.getFeatures(), key=lambda f: -f["pct_mun"]):
    print(f"      {f['nome']:<25} {f['area_aii_km2']:8.2f} km²  {f['pct_mun']:5.2f} %")

# 5. Uso e ocupação do solo na AII ------------------------------------------
# A camada tem ~1 milhão de polígonos: primeiro selecionamos só os que tocam
# a AII (rápido, usa índice espacial) e só então reprojetamos e recortamos.
uso_perto = rodar("native:extractbylocation", {
    "INPUT": camada("uso_ocupacao_solo"),
    "PREDICATE": [0],  # intersecta
    "INTERSECT": aii,
})
uso_perto = rodar("native:fixgeometries", {"INPUT": uso_perto})
uso_m = rodar("native:reprojectlayer", {
    "INPUT": uso_perto, "TARGET_CRS": CRS_METRICO})
uso_aii = rodar("native:clip", {"INPUT": uso_m, "OVERLAY": aii})
# Interseção com os municípios: cada pedaço passa a saber em que município está
uso_aii = rodar("native:intersection", {
    "INPUT": uso_aii, "OVERLAY": municipios_m,
    "INPUT_FIELDS": ["val", "descricao"],
    "OVERLAY_FIELDS": ["nome", "cod_ibge_m"],
})
uso_aii = rodar("native:fieldcalculator", {
    "INPUT": uso_aii,
    "FIELD_NAME": "area_ha", "FIELD_TYPE": 0, "FIELD_PRECISION": 4,
    "FORMULA": "$area / 1e4",
})
uso_classes = rodar("qgis:statisticsbycategories", {
    "INPUT": uso_aii,
    "VALUES_FIELD_NAME": "area_ha",
    "CATEGORIES_FIELD_NAME": ["descricao"],
})
# Mesma tabela do fluxo manual: área por município x classe (formato "longo")
uso_mun_classes = rodar("qgis:statisticsbycategories", {
    "INPUT": uso_aii,
    "VALUES_FIELD_NAME": "area_ha",
    "CATEGORIES_FIELD_NAME": ["nome", "descricao"],
})
uso_mun_classes = rodar("native:retainfields", {
    "INPUT": uso_mun_classes, "FIELDS": ["nome", "descricao", "sum"]})
print(f"[5] Uso do solo na AII: {uso_aii.featureCount()} polígonos")
for f in sorted(uso_classes.getFeatures(), key=lambda f: -f["sum"]):
    print(f"      {f['descricao']:<32} {f['sum']:10.2f} ha")

# 6. Salvar resultados -------------------------------------------------------
gpkg_saida = str(saida / f"{prefixo}_resultados.gpkg")
for lyr, nome in [(rodovia_m, "rodovia"), (ada, "ada_1km"), (aii, "aii_3km"),
                  (aii_mun, "aii_municipios"), (uso_aii, "uso_solo_aii")]:
    lyr.setName(f"{prefixo}_{nome}")
processing.run("native:package", {
    "LAYERS": [rodovia_m, ada, aii, aii_mun, uso_aii],
    "OUTPUT": gpkg_saida,
    "OVERWRITE": True,
})
processing.run("native:savefeatures", {
    "INPUT": aii_mun, "OUTPUT": str(saida / f"{prefixo}_aii_municipios.csv")})
processing.run("native:savefeatures", {
    "INPUT": uso_classes, "OUTPUT": str(saida / f"{prefixo}_uso_solo_classes.csv")})
processing.run("native:savefeatures", {
    "INPUT": uso_mun_classes,
    "OUTPUT": str(saida / f"{prefixo}_uso_solo_municipio_classe.csv")})
print(f"[6] Resultados salvos em {saida}")

# 7. Verificações de consistência -------------------------------------------
soma_mun = sum(f["area_aii_km2"] for f in aii_mun.getFeatures())
soma_uso = sum(f["sum"] for f in uso_classes.getFeatures()) / 100  # ha -> km²
print("[7] Verificações")
print(f"      CRS da AII: {aii.crs().authid()} (esperado {CRS_METRICO})")
print(f"      Soma AII nos municípios: {soma_mun:.2f} km² "
      f"({soma_mun / area_aii_km2:.1%} da AII)")
print(f"      Soma do uso do solo:     {soma_uso:.2f} km² "
      f"({soma_uso / area_aii_km2:.1%} da AII)")
# Diferenças grandes indicam AII saindo do estado, falhas no mapeamento
# ou geometrias inválidas — investigue antes de usar os números!

if CARREGAR_NO_MAPA:
    for nome in ["uso_solo_aii", "aii_municipios", "aii_3km", "ada_1km", "rodovia"]:
        QgsProject.instance().addMapLayer(
            QgsVectorLayer(f"{gpkg_saida}|layername={prefixo}_{nome}",
                           f"{prefixo}_{nome}", "ogr"))
