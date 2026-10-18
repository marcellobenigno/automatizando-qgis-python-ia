
# -*- coding: utf-8 -*-

import re
from pathlib import Path
from urllib.request import Request, urlopen

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QProgressDialog,
    QApplication,
    QFileDialog,
)
from qgis.utils import iface


# --------------------------------------------------
# 1. Configurações e validações
# --------------------------------------------------

# Como ação, o QGIS troca [% @layer_id %] pelo id da camada da ação.
# No Console Python a expressão não é substituída, mapLayer() devolve
# None e usamos a camada ativa.
layer = (
    QgsProject.instance().mapLayer('[% @layer_id %]')
    or iface.activeLayer()
)

if not isinstance(layer, QgsVectorLayer):
    QMessageBox.warning(
        iface.mainWindow(),
        "TOPODATA",
        "Ative a camada da grade TOPODATA (vetorial)."
    )

elif layer.selectedFeatureCount() == 0:
    QMessageBox.warning(
        iface.mainWindow(),
        "TOPODATA",
        "Selecione uma ou mais células da grade antes de executar."
    )

elif "scene" not in layer.fields().names():
    QMessageBox.warning(
        iface.mainWindow(),
        "TOPODATA",
        "A camada ativa não possui o campo 'scene'."
    )

else:

    # --------------------------------------------------
    # 2. Escolha do diretório de download
    # --------------------------------------------------

    diretorio_inicial = str(Path.home() / "TOPODATA")

    diretorio_escolhido = QFileDialog.getExistingDirectory(
        iface.mainWindow(),
        "Escolha a pasta para salvar os rasters TOPODATA",
        diretorio_inicial,
        QFileDialog.ShowDirsOnly
    )

    if not diretorio_escolhido:
        QMessageBox.information(
            iface.mainWindow(),
            "TOPODATA",
            "Operação cancelada. Nenhum download foi iniciado."
        )

    else:
        diretorio = Path(diretorio_escolhido)
        diretorio.mkdir(parents=True, exist_ok=True)

        feicoes = list(layer.selectedFeatures())

        progresso = QProgressDialog(
            "Preparando downloads...",
            "Cancelar",
            0,
            len(feicoes),
            iface.mainWindow()
        )
        progresso.setWindowTitle("Download TOPODATA")
        progresso.setWindowModality(Qt.WindowModal)
        progresso.setMinimumDuration(0)
        progresso.show()

        baixados = 0
        reutilizados = 0
        adicionados = 0
        erros = []
        cancelado = False

        try:
            # ------------------------------------------
            # 3. Processa as células selecionadas
            # ------------------------------------------

            for indice, feicao in enumerate(feicoes, start=1):

                if progresso.wasCanceled():
                    cancelado = True
                    break

                scene = (
                    str(feicao["scene"]).strip()
                    if feicao["scene"] is not None
                    else ""
                )

                progresso.setLabelText(
                    "Processando {} ({}/{})".format(
                        scene, indice, len(feicoes)
                    )
                )
                progresso.setValue(indice - 1)
                QApplication.processEvents()

                # Valida identificadores como 07S375 e 05S42_.
                if not re.fullmatch(r"\d{2}[NS]\d{2,3}_?", scene):
                    erros.append(
                        "{}: identificador de célula inválido".format(
                            scene or feicao.id()
                        )
                    )
                    progresso.setValue(indice)
                    continue

                # --------------------------------------
                # 4. Monta a URL correta
                # --------------------------------------

                pasta_grade = scene[:3]
                folha = scene[3:]

                url = (
                    "https://data.inpe.br/bdc/data/topodata/v001/"
                    f"{pasta_grade}/{folha}/{scene}ZN.tif"
                )

                nome_arquivo = f"{scene}ZN.tif"
                arquivo = diretorio / nome_arquivo
                temporario = diretorio / (nome_arquivo + ".part")

                try:
                    # ----------------------------------
                    # 5. Verifica arquivo existente
                    # ----------------------------------

                    raster_existente = None

                    if (
                        arquivo.is_file()
                        and arquivo.stat().st_size > 0
                    ):
                        raster_existente = QgsRasterLayer(
                            str(arquivo.resolve()),
                            scene,
                            "gdal"
                        )

                    if (
                        raster_existente is not None
                        and raster_existente.isValid()
                    ):
                        reutilizados += 1

                    else:
                        if arquivo.exists():
                            arquivo.unlink()

                        # ------------------------------
                        # 6. Download do raster
                        # ------------------------------

                        requisicao = Request(
                            url,
                            headers={
                                "User-Agent": "Mozilla/5.0 QGIS TOPODATA"
                            }
                        )

                        with urlopen(
                            requisicao, timeout=120
                        ) as resposta:

                            tamanho_total = int(
                                resposta.headers.get(
                                    "Content-Length", 0
                                )
                            )
                            tamanho_baixado = 0

                            with open(temporario, "wb") as destino:
                                while True:
                                    if progresso.wasCanceled():
                                        cancelado = True
                                        raise InterruptedError(
                                            "Download cancelado pelo usuário."
                                        )

                                    bloco = resposta.read(1024 * 256)

                                    if not bloco:
                                        break

                                    destino.write(bloco)
                                    tamanho_baixado += len(bloco)

                                    progresso.setLabelText(
                                        "Baixando {}: {:.1f} MB".format(
                                            scene,
                                            tamanho_baixado / (1024 * 1024)
                                        )
                                    )
                                    QApplication.processEvents()

                            if (
                                tamanho_total > 0
                                and tamanho_baixado != tamanho_total
                            ):
                                raise IOError("Download incompleto.")

                        if tamanho_baixado == 0:
                            raise IOError(
                                "O arquivo baixado está vazio."
                            )

                        temporario.replace(arquivo)
                        baixados += 1

                    # ----------------------------------
                    # 7. Adiciona ao projeto QGIS
                    # ----------------------------------

                    caminho = str(arquivo.resolve())
                    ja_carregado = False

                    for camada_projeto in (
                        QgsProject.instance().mapLayers().values()
                    ):
                        if not isinstance(
                            camada_projeto, QgsRasterLayer
                        ):
                            continue

                        fonte = camada_projeto.source().split("|")[0]

                        try:
                            if str(Path(fonte).resolve()) == caminho:
                                ja_carregado = True
                                break
                        except (OSError, ValueError):
                            continue

                    if not ja_carregado:
                        raster = QgsRasterLayer(
                            caminho,
                            scene,
                            "gdal"
                        )

                        if not raster.isValid():
                            arquivo.unlink(missing_ok=True)
                            raise RuntimeError(
                                "O arquivo baixado não é um raster válido."
                            )

                        QgsProject.instance().addMapLayer(raster)
                        adicionados += 1

                except InterruptedError:
                    cancelado = True
                    break

                except Exception as erro:
                    erros.append(
                        "{}: {}\nURL: {}".format(
                            scene, erro, url
                        )
                    )

                finally:
                    if temporario.exists():
                        temporario.unlink()

                progresso.setValue(indice)
                QApplication.processEvents()

        finally:
            progresso.close()

        # ----------------------------------------------
        # 8. Relatório final
        # ----------------------------------------------

        resumo = (
            "Diretório de destino:\n{}\n\n"
            "Células selecionadas: {}\n"
            "Rasters baixados: {}\n"
            "Arquivos existentes reutilizados: {}\n"
            "Novas camadas adicionadas: {}\n"
            "Erros: {}"
        ).format(
            diretorio,
            len(feicoes),
            baixados,
            reutilizados,
            adicionados,
            len(erros)
        )

        if cancelado:
            resumo += "\n\nOperação cancelada pelo usuário."

        if erros:
            resumo += (
                "\n\nDetalhes dos erros:\n"
                + "\n\n".join(erros[:10])
            )

            if len(erros) > 10:
                resumo += "\n\n... e mais {} erro(s).".format(
                    len(erros) - 10
                )

        QMessageBox.information(
            iface.mainWindow(),
            "Resultado — TOPODATA",
            resumo
        )
