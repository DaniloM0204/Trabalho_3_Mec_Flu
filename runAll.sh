#! /bin/bash

#* set -e indica que o script deve parar se algum comando falhar
set -e

#* Limpa o caso
foamCleanCase

mkdir -p Logs

#! Rodas as malhas

#~ Malha principal
blockMesh > Logs/log.blockMesh 2>&1

#~ Malha com boneco e refinamento
surfaceFeatures > Logs/log.surfaceFeature 2>&1

snappyHexMesh > Logs/log.snappyHexMesh 2>&1

#~ Malha extrudada para 2D
extrudeMesh > Logs/log.extrudeMesh 2>&1

#* Checa a malha e manda pra um log
checkMesh > Logs/log.checkMesh 2>&1

#* Roda o solver
foamRun > Logs/log.foamRun 2>&1