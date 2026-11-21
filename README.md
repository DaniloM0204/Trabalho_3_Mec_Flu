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

O `system/blockMeshDict` é parametrizado: a geometria e o número de células saem das variáveis no início do arquivo. Para mudar o refinamento, basta alterar `dx`, que é o tamanho da célula de fundo. Junto ao boneco, o `snappyHexMesh` refina 2 níveis, o que dá dx/4.

| dx [m] | Células (após `snappyHexMesh` + `extrudeMesh`) | Faces no `boneco` |
|---|---|---|
| 0,07 | 3.067 | 194 |
| 0,05 | 5.646 | 278 |
| 0,035 | 10.578 | 402 |

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

Turbulência (`kEpsilon`):

- **Entrada:** `turbulentKineticEnergy` com I = 0,16·Re^(−1/8) e `turbulentEpsilon` com ℓ = 0,07·D_h, sendo D_h = 1 m.
- **Saída:** `inletOutlet` em k e ε.
- **Paredes:** funções de parede (`kqRWallFunction`, `epsilonWallFunction`, `nutkWallFunction` e `compressible::alphatJayatillekeWallFunction`).

**Fluido:** ar (ρ₀ = 1,225 kg/m³, T₀ = 288,15 K, β = 1/T₀ = 3,47×10⁻³ K⁻¹, μ = 1,8×10⁻⁵ Pa·s, c_p = 1005 J/(kg·K), Pr = 0,7).

## Condições alteradas

| Arquivo | Patch | Antes | Depois | |
|---|---|---|---|---|
| `0/p_rgh` | `dutoEsquerdo` | `prghPressure` (p uniforme) | `fixedValue`, `uniform 0` | 

A saída é uma abertura vertical (0,5 m). Fixar p uniforme impõe um desequilíbrio hidrostático de ρ·g·Δy ≈ 6 Pa, cerca de 18 vezes a pressão dinâmica (½ρU² ≈ 0,34 Pa), o que criava refluxo pela parte de cima da saída. Com p_rgh uniforme, o ambiente externo fica em equilíbrio hidrostático, e o refluxo desapareceu.

## Estudo de velocidade

O enunciado não fixa a velocidade de entrada, então ela será variada para observar o efeito no campo térmico. A escolha usa o número de Richardson, que compara empuxo e inércia:

$$Ri = \frac{g\,\beta\,\Delta T\,L}{U^2}$$

Com β = 1/288 K⁻¹, ΔT = 15 K e L = 1,4 m (altura do boneco), Ri = 1 corresponde a U ≈ 0,85 m/s.

| U [m/s] | Re (D_h = 1 m) | I | k [m²/s²] | ε [m²/s³] |
|---|---|---|---|---|
| 0,1 | 6.806 | 5,31% | 4,23×10⁻⁵ | 6,45×10⁻⁷ |
| 0,5 | 34.028 | 4,34% | 7,07×10⁻⁴ | 4,41×10⁻⁵ |
| 0,75 | 51.042 | 4,13% | 1,44×10⁻³ | 1,28×10⁻⁴ |
| 1,0 | 68.056 | 3,98% | 2,38×10⁻³ | 2,72×10⁻⁴ |
| 1,5 | 102.083 | 3,78% | 4,83×10⁻³ | 7,89×10⁻⁴ |
| 2,0 | 136.111 | 3,65% | 8,00×10⁻³ | 1,68×10⁻³ |
| 3,0 | 204.167 | 3,47% | 1,63×10⁻² | 4,87×10⁻³ |

## Andamento

- [x] Malha de fundo (`blockMesh`) parametrizada, com dutos estendidos
- [x] STL em metros e posicionado: x de 1,100 a 1,900, y de 0 a 1,399 e z de 0 a 0,2, superfície fechada
- [x] `surfaceFeatures`, `snappyHexMesh` e `extrudeMesh` (malha 2D, 5.646 células em dx = 0,05)
- [x] Velocidades do estudo: 0,1, 0,5, 0,75, 1, 1,5, 2 e 3 m/s (Ri de cerca de 72 até 0,08)
- [x] Modelo de turbulência: RAS `kEpsilon`
- [x] Campos em `0/` e arquivos em `constant/`
- [x] Primeira rodada válida (U = 0,75 m/s): sem refluxo, balanço de massa exato e monitores estáveis; o `p_rgh` estabiliza em cerca de 2–3×10⁻³
- [ ] GCI com três malhas (dx = 0,07, 0,05 e 0,035 m), só em U = 0,75 m/s (Ri ≈ 1); as demais velocidades usam a malha escolhida
- [ ] Varredura de velocidades
- [ ] Pós-processamento e relatório
