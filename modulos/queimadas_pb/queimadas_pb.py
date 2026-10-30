# -*- coding: utf-8 -*-
"""
Focos de queimadas na Paraíba, jan.–out. de 2026 (QGIS 3.44).

Do Controlador Temporal do QGIS para um dashboard na web.

Os focos vêm do BDQueimadas (INPE), camada
'bdqueimadas_2026-01-01_2026-10-30' do minicurso_dados.gpkg: um ponto por
foco detectado pelo satélite de referência (NOAA-20), com data e hora em
UTC, município, bioma, dias sem chuva, precipitação, risco de fogo e FRP.

Etapas:
  1. Abre a camada de focos e confere os campos
  2. Liga as propriedades temporais da camada (campo 'DataHora')
  3. Configura o Controlador Temporal: animação de semana em semana
  4. Limpa os dados (-999 vira "sem dado") e resume: focos por mês e
     municípios com mais focos, os números que o dashboard deve repetir
  5. Exporta um GeoJSON leve para o dashboard (docs/queimadas_pb/)
  6. Exporta os limites dos municípios e do estado, simplificados, para o
     mapa coroplético e para o contorno do mapa

Como usar: abra no Editor do Console Python do QGIS, ajuste as constantes
abaixo e clique em "Executar script". Fora do QGIS (sem iface), as etapas
2 e 3 são puladas e o GeoJSON é gerado do mesmo jeito.
"""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsDateTimeRange,
    QgsInterval,
    QgsMarkerSymbol,
    QgsProject,
    QgsSingleSymbolRenderer,
    QgsVectorLayer,
)

# --------------------------------------------------------------------------
# Parâmetros — altere aqui
# --------------------------------------------------------------------------
GPKG = "/caminho/para/dados_curso/minicurso_dados.gpkg"
CAMADA = "bdqueimadas_2026-01-01_2026-10-30"
# Pasta do dashboard no repositório (publicada pelo GitHub Pages)
PASTA_DASHBOARD = "/caminho/para/automatizando-qgis-python-ia/docs/queimadas_pb"
ARQUIVO_GEOJSON = "queimadas_pb_2026.geojson"
# Limites para o mapa web: (camada no GeoPackage, arquivo de saída)
LIMITES = [("municipios", "municipios_pb.geojson"), ("limite_pb", "limite_pb.geojson")]
# Tolerância da simplificação, em graus (0,001° ≈ 110 m): 13 MB → ~300 KB
TOLERANCIA = 0.001

# A Paraíba fica em UTC−3 o ano todo (sem horário de verão)
FUSO_PB = timezone(timedelta(hours=-3))
ANO = 2026  # só os focos deste ano, no horário da Paraíba
SEM_DADO = -999  # o BDQueimadas usa -999 quando não há valor
PASSO_ANIMACAO = QgsInterval(1, Qgis.TemporalUnit.Weeks)
QUADROS_POR_SEGUNDO = 4
CARREGAR_NO_MAPA = True

CAMPOS = ["DataHora", "Satelite", "Municipio", "Bioma", "DiaSemChuva",
          "Precipitacao", "RiscoFogo", "FRP"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

try:  # só existe dentro do QGIS
    from qgis.utils import iface
except ImportError:
    iface = None


def abrir_camada():
    """Abre a camada de focos e verifica se os campos esperados existem."""
    lyr = QgsVectorLayer(f"{GPKG}|layername={CAMADA}", "Focos de queimadas 2026", "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"Não foi possível abrir '{CAMADA}' em {GPKG}")
    faltando = [c for c in CAMPOS if lyr.fields().indexOf(c) < 0]
    if faltando:
        raise RuntimeError(f"Campos ausentes na camada: {faltando}")
    print(f"[1] {lyr.featureCount()} focos lidos, SRC {lyr.crs().authid()}")
    return lyr


def ligar_tempo(lyr):
    """Propriedades da camada → Temporal: cada foco é um instante."""
    tp = lyr.temporalProperties()
    tp.setIsActive(True)
    tp.setMode(Qgis.VectorTemporalMode.FeatureDateTimeInstantFromField)
    tp.setStartField("DataHora")
    tp.setAccumulateFeatures(False)  # quem acumula é o Controlador Temporal
    print("[2] Temporal ligado na camada: instante = campo 'DataHora'")


def configurar_controlador(inicio, fim):
    """Painel do Controlador Temporal: modo animado, passo de 1 semana."""
    nav = iface.mapCanvas().temporalController()
    nav.setNavigationMode(Qgis.TemporalNavigationMode.Animated)
    nav.setTemporalExtents(QgsDateTimeRange(inicio, fim))
    nav.setFrameDuration(PASSO_ANIMACAO)
    nav.setFramesPerSecond(QUADROS_POR_SEGUNDO)
    nav.setTemporalRangeCumulative(False)  # True = acumula desde o início
    nav.setLooping(True)
    nav.rewindToStart()
    print(f"[3] Controlador Temporal: {nav.totalFrameCount()} quadros de "
          f"{PASSO_ANIMACAO.weeks():.0f} semana; aperte ▶ no painel")


def estilizar(lyr):
    """Um círculo laranja por foco, com borda clara para separar os vizinhos."""
    simbolo = QgsMarkerSymbol.createSimple({
        "name": "circle", "color": "#eb6834", "size": "2.4",
        "outline_color": "#ffffff", "outline_width": "0.2"})
    lyr.setRenderer(QgsSingleSymbolRenderer(simbolo))


def valor(f, campo):
    """Valor numérico do campo, ou None quando vazio ou -999."""
    v = f[campo]
    if v is None or v == SEM_DADO or str(v) == "NULL":
        return None
    return v


def ler_focos(lyr):
    """Um dicionário por foco, já limpo e com a data em UTC."""
    focos, ignorados, fora_do_ano = [], Counter(), 0
    for f in lyr.getFeatures():
        quando = f["DataHora"].toPyDateTime().replace(tzinfo=timezone.utc)
        if quando.astimezone(FUSO_PB).year != ANO:
            fora_do_ano += 1
            continue
        for campo in ("DiaSemChuva", "RiscoFogo", "Precipitacao", "FRP"):
            if valor(f, campo) is None:
                ignorados[campo] += 1
        p = f.geometry().asPoint()
        focos.append({
            "quando": quando,
            "lon": round(p.x(), 5), "lat": round(p.y(), 5),
            "municipio": f["Municipio"], "bioma": f["Bioma"],
            "satelite": f["Satelite"],
            "frp": valor(f, "FRP"), "risco_fogo": valor(f, "RiscoFogo"),
            "dias_sem_chuva": valor(f, "DiaSemChuva"),
            "precipitacao": valor(f, "Precipitacao"),
        })
    print(f"[4] Focos fora de {ANO} descartados: {fora_do_ano}")
    print("      sem dado (vazio ou -999): "
          + ", ".join(f"{c} {n}" for c, n in ignorados.items()))
    return focos


def resumir(focos):
    """Os números que o dashboard tem de mostrar, para conferir depois."""
    local = [f["quando"].astimezone(FUSO_PB) for f in focos]
    por_mes = Counter(d.month for d in local)
    print("      focos por mês (horário da Paraíba):")
    print("      " + "  ".join(f"{MESES[m - 1]} {por_mes[m]}" for m in sorted(por_mes)))
    municipios = Counter(f["municipio"] for f in focos)
    print(f"      {len(municipios)} municípios com focos; os 5 primeiros:")
    for nome, n in municipios.most_common(5):
        print(f"        {nome:<24} {n:>4}")
    biomas = Counter(f["bioma"] for f in focos)
    print("      " + "  ".join(f"{b} {n} ({n / len(focos):.0%})" for b, n in biomas.items()))
    satelites = sorted({f["satelite"] for f in focos})
    print(f"      satélite(s): {', '.join(satelites)}")


def exportar(focos):
    """GeoJSON compacto: coordenadas com 5 casas (~1 m) e só o necessário."""
    pasta = Path(PASTA_DASHBOARD)
    pasta.mkdir(parents=True, exist_ok=True)
    feicoes = []
    for f in sorted(focos, key=lambda f: f["quando"]):
        props = {k: v for k, v in f.items() if k not in ("quando", "lon", "lat", "satelite")}
        props["data_hora"] = f["quando"].strftime("%Y-%m-%dT%H:%M:%SZ")
        feicoes.append({"type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [f["lon"], f["lat"]]},
                        "properties": props})
    datas = [f["quando"] for f in focos]
    geojson = {
        "type": "FeatureCollection",
        # membros extras: o dashboard lê a fonte e o período daqui
        "metadados": {
            "fonte": "INPE — Programa Queimadas (BDQueimadas)",
            "satelite": ", ".join(sorted({f["satelite"] for f in focos})),
            "inicio": min(datas).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fim": max(datas).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "features": feicoes,
    }
    saida = pasta / ARQUIVO_GEOJSON
    with open(saida, "w", encoding="utf-8") as arq:
        json.dump(geojson, arq, ensure_ascii=False, separators=(",", ":"))
    print(f"[5] {len(feicoes)} focos em {saida} ({saida.stat().st_size / 1024:.0f} KB)")


def exportar_limites():
    """Municípios e estado simplificados, com o nome no padrão do BDQueimadas."""
    for nome, arquivo in LIMITES:
        lim = QgsVectorLayer(f"{GPKG}|layername={nome}", nome, "ogr")
        if not lim.isValid():
            raise RuntimeError(f"Não foi possível abrir '{nome}' em {GPKG}")
        feicoes = []
        for f in lim.getFeatures():
            props = {}
            if nome == "municipios":
                # 'Cajazeiras' → 'CAJAZEIRAS', como no campo Municipio dos focos
                props = {"municipio": f["nome"].upper(), "nome": f["nome"]}
            geometria = json.loads(f.geometry().simplify(TOLERANCIA).asJson(4))
            feicoes.append({"type": "Feature", "geometry": geometria, "properties": props})
        saida = Path(PASTA_DASHBOARD) / arquivo
        with open(saida, "w", encoding="utf-8") as arq:
            json.dump({"type": "FeatureCollection", "features": feicoes}, arq,
                      ensure_ascii=False, separators=(",", ":"))
        print(f"[6] {len(feicoes)} feições de '{nome}' em {saida.name} "
              f"({saida.stat().st_size / 1024:.0f} KB)")


lyr = abrir_camada()
if iface is not None:
    ligar_tempo(lyr)
    estilizar(lyr)
    if CARREGAR_NO_MAPA:
        QgsProject.instance().addMapLayer(lyr)
    # extensão temporal: do primeiro ao último foco
    campo = lyr.fields().indexOf("DataHora")
    configurar_controlador(lyr.minimumValue(campo), lyr.maximumValue(campo))
else:
    print("[2-3] Fora do QGIS: Controlador Temporal não configurado")

focos = ler_focos(lyr)
resumir(focos)
exportar(focos)
exportar_limites()
