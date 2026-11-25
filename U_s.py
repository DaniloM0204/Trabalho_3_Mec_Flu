import os
import subprocess
import numpy as np
from GCI import criar_caso, rodar_caso, ler_resultados, ja_rodou

Base = os.getcwd() # Caminho do diretorio
Pasta = os.path.join(Base,"Velocidades") # Criacao das malhas
DX = [0.035, 0.05, 0.07] # Tamanho da celula da malha
U_variacao = [0.1,0.5,0.75,1.5,2.5,5.0] # Velocidades a serem testadas



def turbulencia(U):
    """Calcula o I,k, e omega a partir 
    da velocidade média U (m/s)"""
    mi = 1.8*10**-5
    rho_0 = 1.225
    D_h = 1
    l = 0.07
    Cmi = 0.09


    nu = mi/rho_0
    Re = (U*D_h)/nu
    I = 0.16*Re**(-1/8)
    k = 1.5*(U*I)**2
    epsilon = (Cmi**0.75 * k**1.5)/l
    omega = epsilon/(Cmi*k)

    return {
        "I": I,
        "k": k,
        "omega": omega
    }

def ajusta_velocidade(caminho,U):
    """Calcula os valores de k,I,omega 
    e ajusta no arquivo 0/k e 0/omega 
    Ajusta a velocidade U(m/s) no arquivo 0/U
    """
    #~ Calcula os valores de k,I,omega
    t = turbulencia(U)
    subprocess.run(["foamDictionary",
                "-entry", "internalField",
                "-set", f"uniform {t['k']}", "0/k"],
               cwd=caminho, check=True)

    subprocess.run(["foamDictionary",
                "-entry", "boundaryField/dutoDireito/intensity",
                "-set", f"{t['I']}", "0/k"],
               cwd=caminho, check=True)

    subprocess.run(["foamDictionary",
                "-entry", "internalField",
                "-set", f"uniform {t['omega']}", "0/omega"],
               cwd=caminho, check=True)

    #~ Ajusta o valor de velocidade no arquivo 0/U
    subprocess.run(["foamDictionary",
                    "-entry","boundaryField/dutoDireito/value",
                    "-set",f"uniform ({-U} 0 0)", "0/U"]
                    ,cwd=caminho, check=True)

if __name__ == "__main__":
    resultados = []
    for U in U_variacao:
        caminho = os.path.join(Pasta, f"U_{U}") #* Montagem do caminho do caso
        if not ja_rodou(caminho):
            criar_caso(DX,caminho)
            ajusta_velocidade(caminho,U)
            rodar_caso(caminho)
        N, Q, T = ler_resultados(caminho)
        Ri = 9.81 * (1/288.15) * 15 * 1.4 / U**2
        dT = T - 288.15
        resultados.append((U,Ri,N,Q,dT))
    np.savetxt("resultados_velocidades.csv", np.array(resultados), delimiter=",",
            header="U,Ri,N,Q_boneco,dT", comments="")