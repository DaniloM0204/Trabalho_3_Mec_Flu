import os
import shutil
import subprocess
import numpy as np

BASE   = os.getcwd()                       # pasta T3
PASTA  = os.path.join(BASE, "GCI")         # Criacao das malhas
DX     = [0.035, 0.05, 0.07]               # 1 = fina, 2 = média, 3 = grossa


def criar_caso(dx):
    """Copia 0/, system/, constant/ (sem polyMesh) e runAll.sh para GCI/dx_<valor>
    e grava o blockMeshDict a partir do template. Retorna o caminho do caso."""
    # TODO 1: montar o caminho, ex.: os.path.join(PASTA, f"dx_{dx}")
    caminho = os.path.join(PASTA, f"dx_{dx}")
    # TODO 2: shutil.copytree(...) para 0, system e constant
    shutil.copytree(os.path.join(BASE, "0"), os.path.join(PASTA, f"dx_{dx}", "0"))
    shutil.copytree(os.path.join(BASE, "system"), os.path.join(PASTA, f"dx_{dx}", "system"))
    shutil.copytree(os.path.join(BASE, "constant"), os.path.join(PASTA, f"dx_{dx}", "constant"), ignore=shutil.ignore_patterns("polyMesh", "extendedFeatureEdgeMesh"))
    # TODO 3: ler system/blockMeshDict_template, trocar "@DX@" e gravar system/blockMeshDict
    with open(os.path.join(BASE, "system", "blockMeshDict_template"), "r") as f:
        blockMeshDict = f.read().replace("@DX@", str(dx))
    with open(os.path.join(PASTA, f"dx_{dx}", "system", "blockMeshDict"), "w") as f:
        f.write(blockMeshDict)
    # TODO 4: criar a pasta Logs dentro do caso
    os.makedirs(os.path.join(PASTA, f"dx_{dx}", "Logs"), exist_ok=True)


def rodar_caso(caminho):
    """Executa o runAll.sh dentro da pasta do caso."""
    # TODO: subprocess.run(["bash", "runAll.sh"], cwd=caminho, check=True)
    pass


def ler_resultados(caminho):
    """Retorna (N_celulas, Q_boneco, T_media) do caso."""
    # TODO 1: N  -> linha "cells:" de Logs/log.checkMesh
    # TODO 2: Q  -> última linha do patch "boneco" em postProcessing/wallHeatFlux/0/wallHeatFlux.dat (coluna Q [W])
    # TODO 3: T  -> última linha de postProcessing/volAverage(T)/0/volFieldValue.dat
    pass


def gci(N, phi, A):
    """Celik et al. (2008). N e phi na ordem [fina, média, grossa]."""
    # TODO: h_i, r21, r32, eps21, eps32, s, p (iterativo), phi_ext, e_a21, GCI_fina
    pass

for i in range(len(DX)):
    criar_caso(DX[i])


if __name__ == "__main__":
    # TODO: para cada dx -> criar_caso, rodar_caso, ler_resultados
    # TODO: chamar gci() para Q_boneco e para T_media e imprimir os resultados
    pass
