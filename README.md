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
| Domínio | 3 × 3 m, caso 2D (frente e fundo `empty`) |
| Duto de entrada (direita) | 0,5 m de altura, encostado no teto (y de 2,5 a 3,0 m) |
| Duto de saída (esquerda) | 0,5 m de altura, encostado no chão (y de 0 a 0,5 m) |
| Boneco | 0,8 × 1,4 m, centralizado em x = 1,5 m e apoiado no chão |

O STL original (`constant/geometry/boneco.STL`) está em mm e é binário com cabeçalho `solid`. Por isso, ele precisa ser convertido para metros e posicionado com `surfaceTransformPoints` antes de gerar a malha.

## Condições de contorno

| Contorno | Temperatura | Velocidade |
|---|---|---|
| `dutoDireito` (entrada) | T = 15 °C | Velocidade de entrada, a definir (ver abaixo) |
| `dutoEsquerdo` (saída) | `zeroGradient` | A definir |
| `boneco` | T = 30 °C | Parede (sem escorregamento) |
| `paredes` | A definir (provavelmente adiabática) | Parede (sem escorregamento) |

**Fluido:** ar.

## Estudo de velocidade

O enunciado não fixa a velocidade de entrada, então ela será variada para observar o efeito no campo térmico. A escolha usa o número de Richardson, que compara empuxo e inércia:

$$Ri = \frac{g\,\beta\,\Delta T\,L}{U^2}$$

Com β = 1/288 K⁻¹, ΔT = 15 K e L = 1,4 m (altura do boneco), Ri = 1 corresponde a U ≈ 0,85 m/s.

## Andamento

- [x] Malha de fundo (`blockMesh`): 3.600 células de 0,05 m, com `Mesh OK`
- [x] STL em metros e posicionado: x de 1,100 a 1,900, y de 0 a 1,399 e z de 0 a 0,2, superfície fechada
- [ ] `surfaceFeatures`, `snappyHexMesh` e `extrudeMesh` (malha 2D)
- [x] Velocidades do estudo: 0,1, 0,5, 0,75, 1, 1,5, 2 e 3 m/s (Ri de cerca de 72 até 0,08)
- [x] Modelo de turbulência: RAS `kEpsilon`, como no tutorial `hotRoomBoussinesqSteady`
- [ ] GCI com três malhas, só em U = 0,75 m/s (Ri ≈ 1); as demais velocidades usam a malha escolhida
- [ ] Campos em `0/` e arquivos em `constant/`
- [ ] Rodar, acompanhar resíduos e verificar convergência
- [ ] Escrever o relatório
