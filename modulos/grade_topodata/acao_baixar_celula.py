# -*- coding: utf-8 -*-

# Ação Python da camada grade_topodata (escopos: Feição e Tela).
# O QGIS substitui [% "scene" %] pelo valor da célula clicada
# antes de executar o código — por isso este arquivo NÃO roda
# no Console Python: cole o conteúdo em
# Propriedades da camada → Ações.

import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

from osgeo import gdal
from qgis.core import QgsProject, QgsRasterLayer, QgsSettings
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QProgressDialog,
    QApplication,
    QFileDialog,
)
from qgis.utils import iface


CHAVE_PASTA = "topodata/ultima_pasta"


def raster_valido(caminho):
    """Valida o raster com o GDAL e fecha o arquivo em seguida."""
    ds = gdal.Open(str(caminho))
    ok = ds is not None
    ds = None  # fecha o dataset (libera o arquivo no Windows)
    return ok


def apagar_seguro(caminho):
    """Apaga o arquivo sem deixar a falha mascarar o erro real."""
    try:
        if caminho.exists():
            caminho.unlink()
    except OSError:
        pass


def renomear_com_tentativas(origem, destino, tentativas=5):
    """Renomeia com repetição (antivírus/rede podem segurar o arquivo)."""
    for i in range(tentativas):
        try:
            origem.replace(destino)
            return
        except PermissionError:
            if i == tentativas - 1:
                raise
            time.sleep(0.5)


# --------------------------------------------------
# 1. Atributos da célula clicada
# --------------------------------------------------

scene = '[% "scene" %]'.strip()


# --------------------------------------------------
# 2. Validação do identificador
# --------------------------------------------------

if not re.fullmatch(r"\d{2}[NS]\d{2,3}_?", scene):

    QMessageBox.warning(
        iface.mainWindow(),
        "TOPODATA",
        "O identificador da célula é inválido: " + scene
    )

else:

    # --------------------------------------------------
    # 3. Monta a URL correta
    # --------------------------------------------------

    pasta_grade = scene[:3]
    folha = scene[3:]

    url = (
        "https://data.inpe.br/bdc/data/topodata/v001/"
        f"{pasta_grade}/{folha}/{scene}ZN.tif"
    )

    nome_arquivo = f"{scene}ZN.tif"

    # --------------------------------------------------
    # 4. Escolhe a pasta de destino (lembra a última)
    # --------------------------------------------------

    config = QgsSettings()
    diretorio_inicial = config.value(
        CHAVE_PASTA,
        str(Path.home() / "TOPODATA")
    )

    diretorio_escolhido = QFileDialog.getExistingDirectory(
        iface.mainWindow(),
        "Escolha a pasta para salvar o raster TOPODATA",
        diretorio_inicial,
        QFileDialog.Option.ShowDirsOnly
    )

    if not diretorio_escolhido:

        iface.messageBar().pushInfo(
            "TOPODATA",
            "Operação cancelada."
        )

    else:

        config.setValue(CHAVE_PASTA, diretorio_escolhido)

        diretorio = Path(diretorio_escolhido)
        diretorio.mkdir(parents=True, exist_ok=True)

        arquivo = diretorio / nome_arquivo
        temporario = diretorio / (nome_arquivo + ".part")
        progresso = None

        try:

            # ------------------------------------------
            # 5. Verifica se o raster já está no projeto
            # ------------------------------------------

            caminho_raster = str(arquivo.resolve())
            raster_carregado = None

            for camada in QgsProject.instance().mapLayers().values():

                if not isinstance(camada, QgsRasterLayer):
                    continue

                fonte = camada.source().split("|")[0]

                try:
                    if str(Path(fonte).resolve()) == caminho_raster:
                        raster_carregado = camada
                        break
                except (OSError, ValueError):
                    continue

            if raster_carregado is not None:

                iface.setActiveLayer(raster_carregado)

                iface.messageBar().pushInfo(
                    "TOPODATA",
                    f"O raster {scene} já está carregado."
                )

            else:

                # --------------------------------------
                # 6. Reutiliza arquivo local válido
                # --------------------------------------

                if (
                    arquivo.is_file()
                    and arquivo.stat().st_size > 0
                    and raster_valido(arquivo)
                ):

                    raster_local = QgsRasterLayer(
                        str(arquivo.resolve()),
                        scene,
                        "gdal"
                    )

                    QgsProject.instance().addMapLayer(raster_local)
                    iface.setActiveLayer(raster_local)

                    iface.messageBar().pushSuccess(
                        "TOPODATA",
                        f"Raster {scene} carregado do disco."
                    )

                else:

                    # Remove arquivo inválido, se existir.
                    apagar_seguro(arquivo)

                    # ----------------------------------
                    # 7. Baixa o raster
                    # ----------------------------------

                    requisicao = Request(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 QGIS TOPODATA"
                        }
                    )

                    with urlopen(requisicao, timeout=120) as resposta:

                        tamanho_total = int(
                            resposta.headers.get("Content-Length", 0)
                        )
                        tamanho_baixado = 0

                        progresso = QProgressDialog(
                            f"Baixando {scene}...",
                            "Cancelar",
                            0,
                            100,
                            iface.mainWindow()
                        )

                        progresso.setWindowTitle("Download TOPODATA")
                        progresso.setWindowModality(
                            Qt.WindowModality.WindowModal
                        )
                        progresso.setMinimumDuration(0)

                        # Sem Content-Length: barra indeterminada
                        if tamanho_total == 0:
                            progresso.setRange(0, 0)

                        progresso.show()

                        with open(temporario, "wb") as destino:

                            while True:

                                if progresso.wasCanceled():
                                    raise InterruptedError(
                                        "Download cancelado pelo usuário."
                                    )

                                bloco = resposta.read(1024 * 256)

                                if not bloco:
                                    break

                                destino.write(bloco)
                                tamanho_baixado += len(bloco)

                                if tamanho_total > 0:
                                    percentual = min(
                                        100,
                                        int(
                                            tamanho_baixado
                                            * 100
                                            / tamanho_total
                                        )
                                    )
                                    progresso.setValue(percentual)

                                QApplication.processEvents()

                    if tamanho_baixado == 0:
                        raise IOError("O arquivo baixado está vazio.")

                    if (
                        tamanho_total > 0
                        and tamanho_baixado != tamanho_total
                    ):
                        raise IOError("O download terminou incompleto.")

                    # Valida com o GDAL (fecha o arquivo logo depois)
                    if not raster_valido(temporario):
                        raise RuntimeError(
                            "O arquivo recebido não é um raster válido."
                        )

                    renomear_com_tentativas(temporario, arquivo)

                    # ----------------------------------
                    # 8. Carrega no projeto QGIS
                    # ----------------------------------

                    raster = QgsRasterLayer(
                        str(arquivo.resolve()),
                        scene,
                        "gdal"
                    )

                    if not raster.isValid():
                        raise RuntimeError(
                            "Não foi possível carregar o raster no QGIS."
                        )

                    QgsProject.instance().addMapLayer(raster)
                    iface.setActiveLayer(raster)

                    iface.messageBar().pushSuccess(
                        "TOPODATA",
                        f"Raster {scene} baixado e carregado."
                    )

        except InterruptedError:

            QMessageBox.information(
                iface.mainWindow(),
                "TOPODATA",
                "Download cancelado pelo usuário."
            )

        except Exception as erro:

            QMessageBox.critical(
                iface.mainWindow(),
                "Erro ao carregar TOPODATA",
                f"{erro}\n\nURL utilizada:\n{url}"
            )

        finally:

            if progresso is not None:
                progresso.close()

            apagar_seguro(temporario)
