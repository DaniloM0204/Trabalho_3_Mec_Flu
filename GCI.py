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
    #* Montagem do caminho do caso
    caminho = os.path.join(PASTA, f"dx_{dx}")

    if os.path.exists(caminho):
        shutil.rmtree(caminho)
    
    os.makedirs(caminho, exist_ok=True)

    #* Copia das pastas 0,system e constant
    pastas   = ["0", "system", "constant"]
    arquivos = ["runAll.sh"]

    for p in pastas:
        if p == "constant":
            shutil.copytree(os.path.join(BASE, p), os.path.join(caminho, p),
                            ignore=shutil.ignore_patterns("polyMesh", "extendedFeatureEdgeMesh"))
        else:
            shutil.copytree(os.path.join(BASE, p), os.path.join(caminho, p))

    #* Copia dos arquivos
    for a in arquivos:
        shutil.copy(os.path.join(BASE, a), os.path.join(caminho, a))

    #* Ler e substituir o template do blockMeshDict
    with open(os.path.join(BASE, "system", "blockMeshDict_template"), "r") as f:
        blockMeshDict = f.read()
    blockMeshDict = blockMeshDict.replace("@DX@", str(dx))

    #* Escrever o blockMeshDict final
    with open(os.path.join(caminho, "system", "blockMeshDict"), "w") as f:
        f.write(blockMeshDict)

    os.makedirs(os.path.join(caminho, "Logs"), exist_ok=True)

    return caminho

def rodar_caso(caminho):
    """Executa o runAll.sh dentro da pasta do caso."""
    subprocess.run(["bash", "runAll.sh"], cwd=caminho, check=True)

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


if __name__ == "__main__":
    for i in range(len(DX)):
        caminho = criar_caso(DX[i])
        rodar_caso(caminho)

    # TODO: chamar gci() para Q_boneco e para T_media e imprimir os resultados
    pass
