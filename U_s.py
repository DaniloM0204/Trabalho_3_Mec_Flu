import os
import subprocess
import numpy as np
from GCI import criar_caso, rodar_caso, ler_resultados, ja_rodou, gci

Base = os.getcwd() # Caminho do diretorio
Pasta = os.path.join(Base,"Velocidades") # Criacao das malhas
DX = [0.035, 0.05, 0.07] # Tamanho da celula: fina, media, grossa (ordem exigida pela gci)
AREA = 0.541869/0.05 # Area do dominio 2D (volume / espessura do extrude) [m^2]
T_ENTRADA = 288.15 # Temperatura do ar na entrada [K]
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

def gci_conservador(N, phi, p=1):
    """GCI da malha fina [%] com a ordem p fixada.
    N e phi na ordem [fina, media, grossa]."""
    r21 = (N[0] / N[1])**0.5
    e_a21 = abs((phi[0] - phi[1]) / phi[0])
    return 1.25 * e_a21 / (r21**p - 1) * 100


if __name__ == "__main__":
    resultados = []
    cabecalho = ("U,Ri,N_fina,Q_fina,dT_fina,"
                 "Q_media,Q_grossa,dT_media,dT_grossa,"
                 "Q_s,Q_p,Q_ext,Q_GCI21,Q_GCI21_p1,Q_Rassint,"
                 "dT_s,dT_p,dT_ext,dT_GCI21,dT_GCI21_p1,dT_Rassint")

    for U in U_variacao:
        N_l, Q_l, dT_l = [], [], []   #* Zera as listas para cada velocidade

        #~ Roda (ou reaproveita) as 3 malhas desta velocidade
        for dx in DX:
            caminho = os.path.join(Pasta, f"U_{U}", f"dx_{dx}") #* Ex.: Velocidades/U_0.1/dx_0.035
            if not ja_rodou(caminho):
                criar_caso(dx, caminho)
                ajusta_velocidade(caminho, U)
                rodar_caso(caminho)
            N, Q, T = ler_resultados(caminho)
            N_l.append(N); Q_l.append(Q); dT_l.append(T - T_ENTRADA)

        #~ GCI desta velocidade
        gQ  = gci(N_l, Q_l, AREA)
        gdT = gci(N_l, dT_l, AREA)
        sQ  = np.sign((Q_l[2] - Q_l[1]) / (Q_l[1] - Q_l[0]))      #* +1 monotona, -1 oscilatoria
        sdT = np.sign((dT_l[2] - dT_l[1]) / (dT_l[1] - dT_l[0]))

        Ri = 9.81 * (1/T_ENTRADA) * 15 * 1.4 / U**2

        resultados.append((U, Ri, N_l[0], Q_l[0], dT_l[0],
                           Q_l[1], Q_l[2], dT_l[1], dT_l[2],
                           sQ, gQ["p"], gQ["phi_ext"], gQ["GCI_21"],
                           gci_conservador(N_l, Q_l), gQ["Rassint"],
                           sdT, gdT["p"], gdT["phi_ext"], gdT["GCI_21"],
                           gci_conservador(N_l, dT_l), gdT["Rassint"]))

        print(f"U = {U} m/s (Ri = {Ri:.2f}): "
              f"Q = {[round(float(x), 3) for x in Q_l]} W, GCI21 = {gQ['GCI_21']:.2f}% (p=1: {gci_conservador(N_l, Q_l):.2f}%) | "
              f"dT = {[round(float(x), 3) for x in dT_l]} K, GCI21 = {gdT['GCI_21']:.2f}% (p=1: {gci_conservador(N_l, dT_l):.2f}%)")

        #* Salva a cada velocidade: se algo falhar no meio, o que ja rodou fica gravado
        np.savetxt("resultados_velocidades.csv", np.array(resultados, dtype=float),
                   delimiter=",", header=cabecalho, comments="")