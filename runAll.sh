#! /bin/bash

#* Limpa o caso
foamCleanCase

#! Rodas as malhas

#~ Malha principal
blockMesh > Logs/log.blockMesh 2>&1
set -e

#~ Malha com boneco e refinamento
surfaceFeatureExtract > Logs/log.surfaceFeatureExtract 2>&1
set -e

snappyHexMesh > Logs/log.snappyHexMesh 2>&1
set -e

#~ Malha extrudada para 2D
extrudeMesh > Logs/log.extrudeMesh 2>&1
set -e

#* Checa a malha e manda pra um log
checkMesh > Logs/log.checkMesh 2>&1
set -e

#* Roda o solver
foamRun > Logs/log.foamRun 2>&1
set -e