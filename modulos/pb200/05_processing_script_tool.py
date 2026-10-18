"""
Módulo 5 — Transformando o fluxo em uma ferramenta da Caixa de Ferramentas.

Como instalar:
  Caixa de Ferramentas > ícone Python > "Adicionar script à Caixa de
  Ferramentas..." e escolha este arquivo. Ele aparecerá em
  Scripts > Minicurso > "Uso do solo na área de influência".

A ferramenta recebe qualquer camada de linhas e qualquer camada de uso do solo,
então serve para outras rodovias, dutos, linhas de transmissão...
"""
import processing
from qgis.core import (QgsCoordinateReferenceSystem, QgsProcessing,
                       QgsProcessingAlgorithm, QgsProcessingParameterCrs,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField)


class UsoSoloAreaInfluencia(QgsProcessingAlgorithm):
    LINHAS = "LINHAS"
    USO = "USO"
    CAMPO_CLASSE = "CAMPO_CLASSE"
    DISTANCIA = "DISTANCIA"
    CRS = "CRS"
    SAIDA = "SAIDA"

    def name(self):
        return "uso_solo_area_influencia"

    def displayName(self):
        return "Uso do solo na área de influência"

    def group(self):
        return "Minicurso"

    def groupId(self):
        return "minicurso"

    def shortHelpString(self):
        return ("Gera um buffer dissolvido ao redor das linhas, recorta a camada de "
                "uso do solo e calcula a área (ha) de cada polígono no CRS métrico "
                "escolhido.")

    def createInstance(self):
        return UsoSoloAreaInfluencia()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.LINHAS, "Camada de linhas (ex.: rodovia filtrada)",
            [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.USO, "Uso e ocupação do solo", [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(
            self.CAMPO_CLASSE, "Campo com a classe de uso", parentLayerParameterName=self.USO,
            defaultValue="descricao"))
        self.addParameter(QgsProcessingParameterCrs(
            self.CRS, "CRS métrico para os cálculos",
            defaultValue=QgsCoordinateReferenceSystem("EPSG:31984")))
        self.addParameter(QgsProcessingParameterDistance(
            self.DISTANCIA, "Distância do buffer (m)", defaultValue=3000,
            parentParameterName=self.LINHAS, minValue=0))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.SAIDA, "Uso do solo na área de influência"))

    def processAlgorithm(self, parameters, context, feedback):
        crs = self.parameterAsCrs(parameters, self.CRS, context)
        distancia = self.parameterAsDouble(parameters, self.DISTANCIA, context)
        campo = self.parameterAsString(parameters, self.CAMPO_CLASSE, context)

        def rodar(alg, params):
            # is_child_algorithm=True integra a barra de progresso e o cancelamento
            params.setdefault("OUTPUT", "TEMPORARY_OUTPUT")
            if feedback.isCanceled():
                return None
            return processing.run(alg, params, context=context, feedback=feedback,
                                  is_child_algorithm=True)["OUTPUT"]

        feedback.pushInfo("Reprojetando e gerando o buffer...")
        linhas = rodar("native:reprojectlayer", {
            "INPUT": parameters[self.LINHAS], "TARGET_CRS": crs})
        buffer = rodar("native:buffer", {
            "INPUT": linhas, "DISTANCE": distancia, "DISSOLVE": True})

        feedback.pushInfo("Selecionando e recortando o uso do solo...")
        uso = rodar("native:extractbylocation", {
            "INPUT": parameters[self.USO], "PREDICATE": [0], "INTERSECT": buffer})
        uso = rodar("native:fixgeometries", {"INPUT": uso})
        uso = rodar("native:reprojectlayer", {"INPUT": uso, "TARGET_CRS": crs})
        uso = rodar("native:clip", {"INPUT": uso, "OVERLAY": buffer})

        feedback.pushInfo("Calculando áreas...")
        uso = rodar("native:retainfields", {"INPUT": uso, "FIELDS": [campo]})
        resultado = rodar("native:fieldcalculator", {
            "INPUT": uso, "FIELD_NAME": "area_ha", "FIELD_TYPE": 0,
            "FIELD_PRECISION": 4, "FORMULA": "$area / 1e4",
            "OUTPUT": parameters[self.SAIDA]})
        return {self.SAIDA: resultado}
