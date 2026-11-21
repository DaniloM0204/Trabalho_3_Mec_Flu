#! /bin/bash

#* Limpa o caso
foamCleanCase

#! Rodas as malhas

#~ Malha principal
blockMesh > Logs/log.blockMesh 2>&1

#~ Malha com boneco e refinamento
snappyHexMesh > Logs/log.snappyHexMesh 2>&1

#~ Malha extrudada para 2D
extrudeMesh > Logs/log.extrudeMesh 2>&1

#* Checa a malha e manda pra um log
checkMesh > Logs/log.checkMesh 2>&1

#* Roda o solver
foamRun > Logs/log.foamRun 2>&1