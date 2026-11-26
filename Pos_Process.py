import os
import glob
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from GCI import ja_rodou

Base    = os.getcwd()
Pasta   = os.path.join(Base, "Velocidades")
Figs    = os.path.join(Base, "Figuras")
CSV     = os.path.join(Base, "resultados_velocidades.csv")

DX      = [0.035, 0.05, 0.07]
Nome_malha    = {0.035: "fina", 0.05: "média", 0.07: "grossa"}
T_Ein   = 288.15
Z       = 0.05   # z dentro da camada 2D 

os.makedirs(Figs, exist_ok=True)

def caminho_caso(U, dx):
    return os.path.join(Pasta, f"U_{U}", f"dx_{dx}")


def ler_dat(arquivo):
    """Lê um .dat do postProcessing: devolve as linhas (sem comentários) já separadas."""
    with open(arquivo) as f:
        return [l.split() for l in f if not l.startswith("#") and l.strip()]


def historico_Q(caminho, patch="boneco"):
    """Calor no patch ao longo das iterações: (iteracoes, Q [W])."""
    dados = ler_dat(os.path.join(caminho, "postProcessing", "wallHeatFlux", "0", "wallHeatFlux.dat"))
    d = [(float(x[0]), float(x[4])) for x in dados if x[1] == patch]
    return np.array(d).T


def historico_T(caminho):
    """Temperatura média do domínio ao longo das iterações: (iteracoes, T [K])."""
    dados = ler_dat(os.path.join(caminho, "postProcessing", "volAverage(T)", "0", "volFieldValue.dat"))
    return np.array([(float(x[0]), float(x[1])) for x in dados]).T


def residuos(caminho):
    """Resíduos iniciais: dicionário {campo: (iteracoes, residuo)}."""
    arquivo = glob.glob(os.path.join(caminho, "postProcessing", "residuals*", "0", "residuals.dat"))[0]
    with open(arquivo) as f:
        cabecalho = [l for l in f if l.startswith("#")][-1].split()[2:]   # tira "#" e "Time"
    dados = [x for x in ler_dat(arquivo) if "N/A" not in x]
    it = np.array([float(x[0]) for x in dados])
    return {campo: (it, np.array([float(x[i + 1]) for x in dados]))
            for i, campo in enumerate(cabecalho)}


def perfil(caminho, Nome_malha, inicio, fim, n_pontos=150):
    """Perfil de T e U ao longo de uma linha (função graphUniform do OpenFOAM).
    Roda o foamPostProcess só na primeira vez; depois apenas lê o arquivo.
    Devolve um dicionário com as colunas: distance, T, U_x, U_y, U_z."""
    saida = glob.glob(os.path.join(caminho, "postProcessing", Nome_malha, "*", "line.xy"))
    if not saida:
        func = (f"graphUniform(name={Nome_malha}, start=({inicio[0]} {inicio[1]} {Z}), "
                f"end=({fim[0]} {fim[1]} {Z}), nPoints={n_pontos}, fields=(T U))")
        subprocess.run(["foamPostProcess", "-solver", "fluid", "-latestTime", "-func", func],
                       cwd=caminho, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        saida = glob.glob(os.path.join(caminho, "postProcessing", Nome_malha, "*", "line.xy"))
    arquivo = sorted(saida, key=lambda p: float(p.split(os.sep)[-2]))[-1]
    with open(arquivo) as f:
        colunas = f.readline().split()[1:]
    dados = np.loadtxt(arquivo)
    return {c: dados[:, i] for i, c in enumerate(colunas)}


def ler_csv():
    """Resultados da varredura: dicionário {coluna: array}, uma linha por velocidade."""
    dados = np.genfromtxt(CSV, delimiter=",", names=True)
    return {Nome_malha: dados[Nome_malha] for Nome_malha in dados.dtype.names}


#* Figura 1 do calor sob o boneco

def fig_convergencia_Q(U):
    """Q no boneco x iteração para as 3 malhas de uma velocidade.
    Mostra (a) a convergência (patamar) e (b) a diferença entre malhas."""
    casos = [dx for dx in DX if ja_rodou(caminho_caso(U, dx))]
    if not casos:
        print(f"  [pulando] U = {U} m/s: nenhum caso terminou ainda")
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    for dx in casos:
        it, Q = historico_Q(caminho_caso(U, dx))
        ax.plot(it[1:], Q[1:], label=f"malha {Nome_malha[dx]} (dx = {dx} m)")   #* [1:] tira a iteração 0 (campo inicial)

    ax.set_xlabel("Iteração")
    ax.set_ylabel("Q no boneco [W]")
    ax.set_title(f"Convergência do calor no boneco, U = {U} m/s")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(Figs, f"convergencia_Q_U{U}.png"), dpi=200)
    plt.close(fig)


def fig_residuos(U, dx=0.035):
    """Resíduo inicial de cada campo x iteração, para uma malha (padrão: fina)."""
    caminho = caminho_caso(U, dx)
    if not ja_rodou(caminho):
        print(f"  [pulando] U = {U} m/s, malha {Nome_malha[dx]}: caso não terminou ainda")
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    for campo, (it, res) in residuos(caminho).items():    #* p_rgh, Ux, Uy, h, k, omega
        ax.plot(it, res, label=campo, linewidth=0.8)

    ax.set_xlabel("Iteração")
    ax.set_ylabel("Resíduo inicial")
    ax.set_yscale("log")
    ax.set_title(f"Resíduos, U = {U} m/s, malha {Nome_malha[dx]} (dx = {dx} m)")
    ax.grid(alpha=0.3, which="both")
    ax.legend(ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(Figs, f"residuos_U{U}.png"), dpi=200)
    plt.close(fig)



def fig_perfis_malhas(U, x_linha):
    fig, (ax_T, ax_U) = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    for dx in DX:
        caminho = caminho_caso(U, dx)
        dados = perfil(caminho, f"linha_x{x_linha}", (x_linha, 0), (x_linha, 3))
        T = dados["T"]
        U_mod = np.sqrt(dados["U_x"]**2 + dados["U_y"]**2)
        y = dados["distance"]

        ax_T.plot(T, y, label=f"malha {Nome_malha[dx]} (dx = {dx} m)")
        ax_U.plot(U_mod, y, label=f"malha {Nome_malha[dx]} (dx = {dx} m)",
                  linestyle="--")

    #~ Temperatura
    ax_T.set_xlabel("Temperatura [K]")
    ax_T.set_ylabel("Altura [m]")
    ax_T.set_title("Perfil de temperatura")
    ax_T.set_ylim(0,3)
    ax_T.grid(alpha=0.3)
    ax_T.legend()

    #~ Velocidade
    ax_U.set_xlabel("|U| [m/s]")
    ax_U.set_title("Perfil de velocidade")
    ax_U.set_ylim(0,3)
    ax_U.grid(alpha=0.3)
    ax_U.legend()

    fig.suptitle(f"Perfis de temperatura e velocidade, U = {U} m/s")
    fig.savefig(os.path.join(Figs, f"perfis_U{U}_{x_linha}.png"), dpi=200)
    plt.close(fig)


def fig_gci_resumo():
    d = ler_csv()
    grandezas = ["Q", "dT_sala", "dT_saida"]
    rotulo = ["Calor no boneco [W]", "dT da sala [K]", "dT da saída [K]"]

    perm = d["U"] > 0.3   #* Regime permanente (U > 0.3 m/s)

    fig, eixos = plt.subplots(3,1,sharex=True, figsize=(7, 8))
    for ax, g, rotulo in zip(eixos, grandezas, rotulo):
        erro = d[f"{g}_GCI21_p1"] / 100 * d[f"{g}_fina"]

        x = d["U"][perm]
        y = d[f"{g}_fina"][perm]
        ax.errorbar(x, y, yerr=erro[perm], fmt="o-", label="Regime permanente", capsize=4)
        ax.plot(d["U"][~perm], d[f"{g}_fina"][~perm],"o",mfc="none")
        ax.set_xscale("log")
        ax.set_ylabel(f"{rotulo}")
        ax.grid(alpha=0.3)

    eixos[-1].set_xlabel("U [m/s]")
    fig.suptitle("GCI conservador p=1 malha fina")
    eixos[-1].legend(labels=["Reg N Perm U=0.25 m/s"], loc="best")
    fig.tight_layout()
    fig.savefig(os.path.join(Figs, f"GCI_resumo.png"), dpi=200)
    plt.close(fig)



def fig_varredura():
    d = ler_csv()
    grandezas = ["Q_fina", "dT_sala_fina", "dT_saida_fina",]
    rotulo = ["Calor no boneco [W]", "dT da sala [K]", "dT da saída [K]"]
    perm = d["U"] > 0.3

    fig, eixos = plt.subplots(3,1,sharex=True, figsize=(7, 8))
    for ax, g, rotulo in zip(eixos, grandezas, rotulo):
        ax.plot(d["Ri"][perm], d[g][perm],"o-")
        ax.plot(d["Ri"][~perm], d[g][~perm],"o",mfc="none")
        ax.set_xscale("log")
        ax.axvline(x=1, color="black", linestyle="--", alpha=0.5)
        ax.set_ylabel(f"{rotulo}")
        ax.grid(alpha=0.3)

    eixos[-1].set_xlabel("(Ri)")
    fig.suptitle("Efeito da velocidade (malha dx=0.035)")
    eixos[-1].legend(labels=["Reg Perm", "Reg N Perm (U=0.25 m/s)"], loc="best")
    fig.tight_layout()
    fig.savefig(os.path.join(Figs, f"varredura.png"), dpi=200)
    plt.close(fig)


def fig_perfis_velocidades(x_linha, dx=0.035):
    #TODO: perfis de T na linha x = x_linha para todas as velocidades (malha fina)."""
    pass



if __name__ == "__main__":
    U_var = [0.25, 0.5, 0.75, 1.5, 2.5, 5.0]

    for U in U_var:
        fig_convergencia_Q(U)
        fig_perfis_malhas(U, 0.6)
        fig_perfis_malhas(U, 2.4)
        fig_residuos(U)

    fig_varredura()
    fig_gci_resumo()

    print(f"Figuras salvas em {Figs}")
