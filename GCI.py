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

def ler_resultados(caminho, n_media=500):
    """Retorna (N, Q_boneco, T_media), com Q e T = média das últimas n_media iterações."""

    #* Ler o número de células do log.checkMesh
    with open(os.path.join(caminho, "Logs", "log.checkMesh")) as f:
        for l in f:
            if l.strip().startswith("cells:"):
                N = int(l.split()[1])
                break

    #* Ler o fluxo de calor no boneco: colunas = Time, patch, area, normalVector, wallHeatFlux
    arq = os.path.join(caminho, "postProcessing", "wallHeatFlux", "0", "wallHeatFlux.dat")
    with open(arq) as f:
        dados = [l.split() for l in f if not l.startswith("#") and l.strip()]
    q = [(float(d[0]), float(d[4])) for d in dados if d[1] == "boneco"]
    t_final = q[-1][0]
    Q = [v for t, v in q if t > t_final - n_media]


    #* Ler a temperatura média: colunas = Time, volAverage(T)
    arq = os.path.join(caminho, "postProcessing", "volAverage(T)", "0", "volFieldValue.dat")
    with open(arq) as f:
        dados = [l.split() for l in f if not l.startswith("#") and l.strip()]
    t = [(float(d[0]), float(d[1])) for d in dados]
    T = [v for tempo, v in t if tempo > t_final - n_media]

    return N, np.mean(Q), np.mean(T)


def gci(N, phi, A):
    """Celik et al. (2008). N e phi na ordem [fina, média, grossa]."""
    # TODO: h_i, r21, r32, eps21, eps32, s, p (iterativo), phi_ext, e_a21, GCI_fina
    N = np.array(N,float)
    phi = np.array(phi,float)
    
    h_i = (A/N)**0.5
    r21 = h_i[1]/h_i[0]
    r32 = h_i[2]/h_i[1]
    eps21 = (phi[1] - phi[0])
    eps32 = (phi[2] - phi[1])
    s = np.sign(eps32/eps21)

    p = 1.0                                      # chute inicial
    for _ in range(100):
        q = np.log((r21**p - s) / (r32**p - s))
        p_novo = abs(np.log(abs(eps32 / eps21)) + q) / np.log(r21)
        if abs(p_novo - p) < 1e-8:
            break
        p = p_novo

    phi_ext = phi[0] + (phi[0] - phi[1]) / (r21**p - 1)
    e_a21 = abs((phi[0] - phi[1]) / phi[0])
    e_a32 = abs((phi[1] - phi[2]) / phi[1])


    GCI_21 = (1.25 * e_a21 / (r21**p - 1)) * 100
    GCI_32 = (1.25 * e_a32 / (r32**p - 1)) * 100
    
    Rassint = GCI_32 / (r21**p * GCI_21)


    return {
        "p": p,
        "phi_ext": phi_ext,
        "e_a21": e_a21,
        "GCI_21": GCI_21,
        "GCI_32": GCI_32,
        "Rassint": Rassint
    }


def ja_rodou(caminho):
    """True se o foamRun desse caso já terminou."""
    log = os.path.join(caminho, "Logs", "log.foamRun")
    if not os.path.exists(log):
        return False
    with open(log) as f:
        return "End" in f.read().split()[-3:]


if __name__ == "__main__":
    N_lista, Q_lista, T_lista = [], [], []
    for dx in DX:                          
        caminho = os.path.join(PASTA, f"dx_{dx}")
        if not ja_rodou(caminho):
            caminho = criar_caso(dx)
            rodar_caso(caminho)
        N, Q, T = ler_resultados(caminho)
        N_lista.append(N); Q_lista.append(Q); T_lista.append(T)
    
    T_lista = [T-288.15 for T in T_lista]
    area  =  0.541869/0.05
    res   =  gci(N_lista, Q_lista, area)            # GCI do calor no boneco
    res_t =  gci(N_lista, T_lista, area)            # GCI da temperatura média
    print("GCI do calor no boneco:", res)
    print("GCI da temperatura média:", res_t)
    pass
