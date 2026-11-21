# Trabalho 3: escoamento e transferência de calor em uma sala climatizada

Simulação 2D do escoamento de ar e da troca de calor em uma sala com ar-condicionado e uma pessoa (o "boneco") no centro. O ar frio entra por um duto no alto da parede direita e sai por um duto junto ao chão da parede esquerda. Feito no OpenFOAM 14 (Foundation).

## Objetivos

1. Resolver o escoamento e a transferência de calor com a aproximação de Boussinesq, em regime permanente.
2. Gerar a malha com `snappyHexMesh`.
3. Verificar a independência de malha com o GCI (*Grid Convergence Index*).
4. Redigir um relatório explicando como o caso foi montado: geração de malha, configuração do solver, análise de resíduos e verificação de convergência.

> No OpenFOAM 14, o antigo `buoyantBoussinesqSimpleFoam` foi substituído por `foamRun` com `solver fluid`, `equationOfState Boussinesq` e `ddtSchemes` em `steadyState`. O tutorial de referência é `$FOAM_TUTORIALS/fluid/hotRoomBoussinesqSteady`.

## Geometria

| Item | Valor |
|---|---|
| Sala | 3 × 3 m, caso 2D (frente e fundo `empty`) |
| Duto de entrada (direita) | 0,5 m de altura, encostado no teto (y de 2,5 a 3,0 m), estendido 2,5 m para fora (x de 3 a 5,5 m) |
| Duto de saída (esquerda) | 0,5 m de altura, encostado no chão (y de 0 a 0,5 m), estendido 2,5 m para fora (x de −2,5 a 0 m) |
| Boneco | 0,8 × 1,4 m, centralizado em x = 1,5 m e apoiado no chão |

O STL original (`constant/geometry/boneco.STL`) está em mm e é binário com cabeçalho `solid`. Por isso, ele precisa ser convertido para metros e posicionado com `surfaceTransformPoints` antes de gerar a malha.

Os dutos foram estendidos por 5 alturas (L = 5 × 0,5 = 2,5 m) para afastar as condições de contorno de entrada e saída da sala. Suas paredes são adiabáticas, para não alterarem a temperatura do ar que entra ou sai.

## Malha

O `system/blockMeshDict` é parametrizado: a geometria e o número de células saem das variáveis no início do arquivo. Para mudar o refinamento, basta alterar `dx`, que é o tamanho da célula de fundo. Junto ao boneco, o `snappyHexMesh` refina 2 níveis, o que dá dx/4. O `GCI.py` gera as malhas a partir do `system/blockMeshDict_template`, trocando o marcador `@DX@`.

O boneco recebe **8 camadas prismáticas** (`addLayers`), com primeira camada de 1 mm e razão de crescimento de 1,2. Em média, o `snappyHexMesh` insere cerca de 6,8 camadas, com cerca de 90% da espessura pretendida.

| dx [m] | Células (após `snappyHexMesh` com camadas + `extrudeMesh`) | y⁺ médio no boneco |
|---|---|---|
| 0,07 | 4.267 | 1,56 |
| 0,05 | 7.518 | 1,25 |
| 0,035 | 13.442 | 1,09 |

A espessura da primeira camada vem de y⁺ = 1. Na rodada com `kEpsilon`, o boneco tinha y⁺ ≈ 9,5 com a primeira célula a cerca de 6,25 mm da parede, o que dá u_τ = y⁺·ν/y ≈ 0,022 m/s. Para y⁺ = 1, o centro da primeira célula fica a y = ν/u_τ ≈ 0,67 mm, ou seja, uma camada de cerca de 1,3 mm. Foi adotado 1 mm, com margem.

Sequência: `surfaceFeatures`, `blockMesh`, `snappyHexMesh`, `extrudeMesh` e `checkMesh` (script `runAll.sh`).

## Condições de contorno

| Contorno | T | U | p_rgh |
|---|---|---|---|
| `dutoDireito` (entrada) | `fixedValue` 288,15 K (15 °C) | `fixedValue` (−U 0 0) | `fixedFluxPressure` |
| `dutoEsquerdo` (saída) | `zeroGradient` | `pressureInletOutletVelocity` | `fixedValue` 0 |
| `boneco` | `fixedValue` 303,15 K (30 °C) | `noSlip` | `fixedFluxPressure` |
| `paredes` (sala) | `fixedValue` 298,15 K (25 °C, isotérmica) | `noSlip` | `fixedFluxPressure` |
| `paredesDuto` | `zeroGradient` (adiabática) | `noSlip` | `fixedFluxPressure` |
| `front` / `back` | `empty` | `empty` | `empty` |

Turbulência (`kOmegaSST`, parede resolvida até y⁺ ≈ 1):

- **Entrada:** `turbulentKineticEnergy` com I = 0,16·Re^(−1/8) e `turbulentOmega` com ℓ = 0,07·D_h, sendo D_h = 1 m.
- **Saída:** `inletOutlet` em k e ω.
- **Paredes:** `kqRWallFunction` (k), `omegaWallFunction` (ω), `nutUWallFunction` (ν_t) e `compressible::alphatWallFunction` com Pr_t = 0,85 (α_t), como no tutorial `buoyantCavity`.
- **Valor inicial de ω:** ω = ε/(C_μ·k), com C_μ = 0,09.

Para o SST, o `fvSchemes` também precisa do bloco `wallDist { method meshWave; }`. As camadas geram células com não-ortogonalidade de até cerca de 63°. Por isso, os esquemas laplaciano e snGrad usam `limited corrected 0.5`, e o `fvSolution` usa `nNonOrthogonalCorrectors 1`.

**Fluido:** ar (ρ₀ = 1,225 kg/m³, T₀ = 288,15 K, β = 1/T₀ = 3,47×10⁻³ K⁻¹, μ = 1,8×10⁻⁵ Pa·s, c_p = 1005 J/(kg·K), Pr = 0,7).

## Condições alteradas

| Arquivo | Patch | Antes | Depois |
|---|---|---|---|
| `0/p_rgh` | `dutoEsquerdo` | `prghPressure` (p uniforme) | `fixedValue`, `uniform 0` |
| `constant/momentumTransport` | — | `kEpsilon` com funções de parede | `kOmegaSST` com 8 camadas no boneco (y⁺ ≈ 1) |

### Pressão na saída

A saída é uma abertura vertical (0,5 m). Fixar p uniforme impõe um desequilíbrio hidrostático de ρ·g·Δy ≈ 6 Pa, cerca de 18 vezes a pressão dinâmica (½ρU² ≈ 0,34 Pa), o que criava refluxo pela parte de cima da saída. Com p_rgh uniforme, o ambiente externo fica em equilíbrio hidrostático, e o refluxo desapareceu.

### De `kEpsilon` para `kOmegaSST`

Com `kEpsilon` e funções de parede, o calor trocado pelo boneco **não convergia com a malha**:

| dx [m] | Q no boneco [W] | y⁺ médio no boneco |
|---|---|---|
| 0,07 | 7,60 | 12,4 |
| 0,05 | 8,70 | 9,5 |
| 0,035 | 10,14 | 6,4 |

O calor aumentava 14–17% a cada refinamento, e o GCI da malha fina chegava a **64%**. A causa é o y⁺: as funções de parede supõem a primeira célula na camada logarítmica (y⁺ de cerca de 30 a 300). No boneco, o y⁺ ficava entre 6 e 12, na camada de amortecimento (*buffer layer*), e caía a cada refinamento. Nessa faixa, a função de parede térmica (`alphatJayatillekeWallFunction`) dá um fluxo de calor que depende do tamanho da célula, então refinar a malha mudava o próprio modelo de parede. Trocar só a função de parede de ν_t por `nutUSpaldingWallFunction` não resolveu (7,16 → 8,58 → 10,32 W).

A solução foi **resolver a camada limite** em vez de modelá-la: o `kOmegaSST` funciona até a parede, e as camadas prismáticas mantêm y⁺ ≈ 1 nas três malhas. Com isso, o calor passa a ser calculado pelo gradiente de temperatura junto à parede, e a diferença entre as malhas média e fina caiu de 17% para 0,46% (ver GCI).

## Estudo de velocidade

O enunciado não fixa a velocidade de entrada, então ela será variada para observar o efeito no campo térmico. A escolha usa o número de Richardson, que compara empuxo e inércia:

$$Ri = \frac{g\,\beta\,\Delta T\,L}{U^2}$$

Com β = 1/288 K⁻¹, ΔT = 15 K e L = 1,4 m (altura do boneco), Ri = 1 corresponde a U ≈ 0,85 m/s.

| U [m/s] | Re (D_h = 1 m) | I | k [m²/s²] | ε [m²/s³] | ω [1/s] |
|---|---|---|---|---|---|
| 0,1 | 6.806 | 5,31% | 4,23×10⁻⁵ | 6,45×10⁻⁷ | 0,169 |
| 0,5 | 34.028 | 4,34% | 7,07×10⁻⁴ | 4,41×10⁻⁵ | 0,693 |
| 0,75 | 51.042 | 4,13% | 1,44×10⁻³ | 1,28×10⁻⁴ | 0,988 |
| 1,0 | 68.056 | 3,98% | 2,38×10⁻³ | 2,72×10⁻⁴ | 1,270 |
| 1,5 | 102.083 | 3,78% | 4,83×10⁻³ | 7,89×10⁻⁴ | 1,815 |
| 2,0 | 136.111 | 3,65% | 8,00×10⁻³ | 1,68×10⁻³ | 2,333 |
| 3,0 | 204.167 | 3,47% | 1,63×10⁻² | 4,87×10⁻³ | 3,320 |

Em cada caso mudam: U no `dutoDireito`, a `intensity` em `0/k` e os `internalField` de k e ω.

## Independência de malha (GCI)

Método de Celik et al. (2008), em U = 0,75 m/s, calculado pelo `GCI.py`. Q e T são as médias das últimas 500 iterações (de 4.000), e h = (A/N)^½ com A = 10,84 m².

| φ | Fina (13.442) | Média (7.518) | Grossa (4.267) | s | p aparente | φ_ext | GCI₂₁ | GCI₃₂ | Razão assintótica |
|---|---|---|---|---|---|---|---|---|---|
| Q no boneco [W] | 7,424 | 7,390 | 7,670 | −1 | 7,40 | 7,429 | 0,08% | 0,66% | 1,02 |
| ΔT da sala [K] | 2,020 | 1,877 | 1,898 | −1 | 6,46 | 2,045 | 1,59% | 0,27% | 0,03 |

Estimativa conservadora, com p limitado à ordem formal dos esquemas:

| φ | GCI₂₁ com p = 1 | GCI₂₁ com p = 2 |
|---|---|---|
| Q no boneco | 1,7% | 0,7% |
| ΔT da sala | 26% | 11% |

- **Calor no boneco:** independente da malha. A diferença entre as malhas média e fina é de 0,46%, menor que o ruído iterativo (±0,8%), e a razão assintótica é 1,02.
- **Temperatura média:** fora da faixa assintótica (razão de 0,03). Ela depende da mistura do jato e da pluma na sala inteira, e a média inclui os 2,5 m de cada duto.
- **p aparente de 6 a 7 e s = −1 (convergência oscilatória):** a diferença entre as malhas é da ordem do ruído iterativo. Por isso, os GCI com o p aparente são otimistas, e a estimativa conservadora (p = 1 ou 2) deve ser a reportada.
- **Malha escolhida para a varredura:** a fina (dx = 0,035), por cerca de 2 minutos por caso.

## Andamento

- [x] Malha de fundo (`blockMesh`) parametrizada, com dutos estendidos
- [x] STL em metros e posicionado: x de 1,100 a 1,900, y de 0 a 1,399 e z de 0 a 0,2, superfície fechada
- [x] `surfaceFeatures`, `snappyHexMesh` e `extrudeMesh` (malha 2D)
- [x] Velocidades do estudo: 0,1, 0,5, 0,75, 1, 1,5, 2 e 3 m/s (Ri de cerca de 72 até 0,08)
- [x] Campos em `0/` e arquivos em `constant/`
- [x] Primeira rodada válida (U = 0,75 m/s): sem refluxo, balanço de massa exato e monitores estáveis
- [x] Condição de pressão na saída corrigida (`p_rgh` `fixedValue`), eliminando o refluxo
- [x] Modelo de turbulência: troca de `kEpsilon` (funções de parede) para `kOmegaSST` com camadas no boneco (y⁺ ≈ 1)
- [x] `GCI.py`: gera, roda e lê as três malhas automaticamente (`criar_caso`, `rodar_caso`, `ja_rodou`, `ler_resultados` e `gci`)
- [x] GCI com três malhas (dx = 0,07, 0,05 e 0,035 m) em U = 0,75 m/s: Q no boneco independente da malha; malha fina escolhida
- [ ] Script da varredura de velocidades (reaproveitando as funções do `GCI.py`)
- [ ] Rodar as 7 velocidades na malha fina (dx = 0,035)
- [ ] Verificar cada caso: monitores estáveis, ausência de refluxo, balanços de massa e de energia e y⁺ do boneco
- [ ] Pós-processamento: campos de T e U no ParaView e gráficos de Q e ΔT em função de U e de Ri
- [ ] Gráficos de convergência (resíduos e monitores) para o relatório
- [ ] Escrever o relatório
