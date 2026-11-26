# Trabalho 3: escoamento e transferência de calor em uma sala climatizada

Simulação 2D, no OpenFOAM 14 (Foundation), do escoamento de ar e da troca de calor numa sala de 3 × 3 m com uma pessoa (o "boneco") no centro. O ar frio entra por um duto junto ao teto, na parede direita, e sai por um duto junto ao chão, na parede esquerda.

## Objetivo

Determinar **como a velocidade de insuflamento do ar altera o campo térmico da sala e o calor perdido pelo boneco**, com uma solução numérica verificada:

1. Gerar a malha com `snappyHexMesh` a partir do STL do boneco.
2. Resolver o escoamento turbulento com empuxo (aproximação de Boussinesq) em regime permanente.
3. Verificar a convergência iterativa: resíduos, monitores e balanços de massa e energia.
4. Verificar a independência de malha com o GCI (Celik et al., 2008).
5. Variar a velocidade de entrada e analisar o resultado em função do número de Richardson.

## Caso

| Item | Valor |
|---|---|
| Sala | 3 × 3 m, 2D (`extrudeMesh`, frente e fundo `empty`) |
| Entrada (`dutoDireito`) | 0,5 m de altura, y de 2,5 a 3,0 m, T = 15 °C, U variável |
| Saída (`dutoEsquerdo`) | 0,5 m de altura, y de 0 a 0,5 m, `zeroGradient` em T e p_rgh = 0 |
| Dutos | estendidos 2,5 m (5 alturas) para fora da sala, com paredes adiabáticas |
| Boneco | 0,8 × 1,4 m, centrado em x = 1,5 m, T = 30 °C |
| Paredes da sala | isotérmicas, T = 25 °C |
| Fluido | ar, Boussinesq (ρ₀ = 1,225 kg/m³, β = 1/288,15 K⁻¹, Pr = 0,7) |
| Solver | `foamRun -solver fluid`, regime permanente (`steadyState`) |
| Turbulência | `kOmegaSST`, com 8 camadas prismáticas no boneco (y⁺ ≈ 1) |
| Malhas | dx = 0,07, 0,05 e 0,035 m, com 4.267, 7.518 e 13.442 células |

## Como reproduzir

```bash
python3 U_s.py          # gera e roda 6 velocidades × 3 malhas em Velocidades/ e grava resultados_velocidades.csv
python3 Pos_Process.py  # gera as figuras em Figuras/
```

`GCI.py` contém as funções comuns: criar e rodar um caso, ler os resultados, calcular o GCI e a temperatura de saída.

## Resultados

Os valores são da malha fina, com a média das últimas 500 iterações. Ri = gβΔT·L/U², com ΔT = 15 K e L = 1,4 m.

| U [m/s] | Ri | Q no boneco [W] | ΔT de saída [K] | ΔT médio da sala [K] | Regime |
|---|---|---|---|---|---|
| 0,25 | 11,4 | 6,63 | (2,60) | (2,21) | não permanente |
| 0,5 | 2,86 | 6,97 | 1,02 | 2,21 | permanente |
| 0,75 | 1,27 | 7,42 | 0,78 | 2,02 | permanente |
| 1,5 | 0,32 | 9,40 | 0,54 | 1,56 | permanente |
| 2,5 | 0,11 | 11,88 | 0,44 | 1,36 | permanente |
| 5,0 | 0,03 | 19,31 | 0,38 | 1,08 | permanente |

### Validação dos casos

| U [m/s] | Oscilação de Q | Balanço de energia | Balanço de massa | Refluxo na saída | y⁺ médio no boneco |
|---|---|---|---|---|---|
| 0,25 | ±5% | −30% | 0% | 11% da vazão | 1,05 |
| 0,5 | ±1,6% | +1,9% | 0% | não | 1,08 |
| 0,75 | ±0,7% | −0,1% | 0% | não | 1,10 |
| 1,5 | ±0,2% | −0,3% | 0% | não | 1,21 |
| 2,5 | ±0,2% | −1,0% | 0% | não | 1,38 |
| 5,0 | ±0,1% | −4,3%* | 0% | não | 2,02 |

\* O balanço considera só a entalpia. Em U = 5 m/s, a parcela de energia cinética (∝ U³) passa a contar.

Com U = 0,25 m/s (e com o teste anterior de 0,1 m/s), o empuxo domina. O escoamento oscila e troca ar pela saída, de modo que o modelo permanente não se aplica. Os valores desse ponto são apenas indicativos.

### Independência de malha (GCI conservador, p = 1, malha fina)

| U [m/s] | Q no boneco | ΔT de saída | ΔT médio da sala |
|---|---|---|---|
| 0,5 | 11,3% | 11,4% | 5,1% |
| 0,75 | 1,9% | 11,0% | 26% |
| 1,5 | 5,1% | 8,7% | 32% |
| 2,5 | 3,2% | 0,4% | 46% |
| 5,0 | 5,1% | 2,7% | 38% |

O calor no boneco e o ΔT de saída são independentes da malha dentro de poucos por cento. O ΔT médio da sala é sensível à malha e serve apenas como tendência.

### Conclusões

- O calor perdido pelo boneco cresce com a velocidade, de 7,0 para 19,3 W (h de cerca de 2,8 a 7,2 W/m²K). A curva achata para Ri > 1, onde a convecção natural domina.
- O aquecimento do ar cai com a vazão: o ΔT de saída vai de 1,02 para 0,38 K.
- Acima de Ri ≈ 10, a solução permanente deixa de existir.

### Figuras (`Figuras/`)

| Pasta | Conteúdo |
|---|---|
| `1_Convergencia/` | Q no boneco × iteração, para as 3 malhas |
| `2_Residuos/` | resíduos iniciais × iteração (malha fina) |
| `3_Independencia_Malha/` | perfis de T e de \|U\| em x = 0,6 e 2,4 m para as 3 malhas, e `GCI_resumo.png` |
| `4_Varredura/` | Q e ΔT × Ri |
| `5_Campos_ParaView/` | campos de T e linhas de corrente |
