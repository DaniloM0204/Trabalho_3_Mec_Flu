import os
import subprocess
import numpy as np
from GCI import criar_caso, rodar_caso, ler_resultados, ja_rodou, gci, T_saida

Base            =  os.getcwd()                     # Caminho do diretorio
Pasta           = os.path.join(Base,"Velocidades") # Criacao das malhas
DX              = [0.035, 0.05, 0.07]              # Tamanho da celula: fina, media, grossa (ordem exigida pela gci)
Area            = 0.541869/0.05                    # Area do dominio 2D (volume / espessura do extrude) [m^2]
T_in            = 288.15                           # Temperatura do ar na entrada [K]
N_iter          = 10000                            # Iterações fixas
N_guarda        = 20                               # Pastas para calular a media
U_variacao      = [0.25,0.5,0.75,1.5,2.5,5.0]       # Velocidades a serem testadas



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

    #~ Remove o residualControl para o solver não parar cedo
    subprocess.run(["foamDictionary",
                    "-entry", "PIMPLE/residualControl",
                    "-remove", "system/fvSolution"],
                   cwd=caminho, check=True)
    subprocess.run(["foamDictionary",
                    "-entry", "endTime",
                    "-set", str(N_iter), "system/controlDict"],
                   cwd=caminho, check=True)

    #~ Mantém só as últimas pastas de tempo (economiza disco; bastam para a média)
    subprocess.run(["foamDictionary",
                    "-entry", "purgeWrite",
                    "-set", str(N_guarda), "system/controlDict"],
                   cwd=caminho, check=True)

def gci_conservador(N, phi, p=1):
    """GCI da malha fina [%] com a ordem p fixada.
    N e phi na ordem [fina, media, grossa]."""
    r21 = (N[0] / N[1])**0.5
    e_a21 = abs((phi[0] - phi[1]) / phi[0])
    return 1.25 * e_a21 / (r21**p - 1) * 100


if __name__ == "__main__":
    grandezas = ["Q", "dT_sala", "dT_saida"]   #* calor no boneco [W], elevação média da sala [K], elevação na saída [K]
    colunas   = ["fina", "media", "grossa", "s", "p", "ext", "GCI21", "GCI21_p1", "Rassint"]
    cabecalho = ",".join(["U", "Ri", "N_fina"] + [f"{g}_{c}" for g in grandezas for c in colunas])
    resultados = []

    for U in U_variacao:
        N_l = []
        valores = {g: [] for g in grandezas}   #* zera as listas para cada velocidade

        #~ Roda (ou reaproveita) as 3 malhas desta velocidade
        for dx in DX:
            caminho = os.path.join(Pasta, f"U_{U}", f"dx_{dx}") #* Ex.: Velocidades/U_0.1/dx_0.035
            if not ja_rodou(caminho):
                criar_caso(dx, caminho)
                ajusta_velocidade(caminho, U)
                rodar_caso(caminho)
            N, Q, T = ler_resultados(caminho)
            N_l.append(N)
            valores["Q"].append(Q)
            valores["dT_sala"].append(T - T_in)
            valores["dT_saida"].append(T_saida(caminho) - T_in)

        Ri = 9.81 * (1/T_in) * 15 * 1.4 / U**2
        linha = [U, Ri, N_l[0]]

        #~ GCI de cada grandeza desta velocidade
        resumo = []
        for g in grandezas:
            v = valores[g]
            r = gci(N_l, v, Area)
            s = np.sign((v[2] - v[1]) / (v[1] - v[0]))   #* +1 monótona, -1 oscilatória
            p1 = gci_conservador(N_l, v)
            linha += [v[0], v[1], v[2], s, r["p"], r["phi_ext"], r["GCI_21"], p1, r["Rassint"]]
            resumo.append(f"{g} = {[round(float(x), 3) for x in v]} (GCI21 p=1: {p1:.1f}%)")

        resultados.append(linha)
        print(f"U = {U} m/s (Ri = {Ri:.2f}): " + " | ".join(resumo))

        #* Salva a cada velocidade: se algo falhar no meio, o que já rodou fica gravado
        np.savetxt("resultados_velocidades.csv", np.array(resultados, dtype=float),
                   delimiter=",", header=cabecalho, comments="")
