# 07b — Alcance sem Space Jump

Estado: verificada (22/10/2026: validate 28/60/0, .ips sha1 `e9b0db22…8555` igual, 21/21 testes)
Esforço estimado: 1 dia (medição 2 h, spec 1 h, código 3 h, verificação 1 h)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md)

## Contexto

No Tallon a Samus chega só com o Power Beam (decisão 3 do épico: sem mísseis, 99 de energia, sem
Space Jump, sem Morph Ball, sem Hi-Jump). O validador de hoje diz que "ar conectado = alcançável":
isso está certo na fragata (lá ela tem Space Jump), mas aprovaria no Tallon uma plataforma alta
demais, que prende a Samus. Esta spec dá ao validador um modelo de pulo de verdade, com números
medidos no emulador, e um "equipamento" (loadout) por área. Nenhuma sala muda; a ROM sai igual.

## Estado atual (verificado)

- `tools/validate.py` (`check_area`): flood fill 4-vizinhos no ar (`tipo de bloco != 8`) a partir da
  primeira entrada; porta inalcançável = célula de dentro da porta fora do ar alcançado. O
  docstring diz que supõe Space Jump + Morph. As checagens de save station, map station e nave
  perguntam `(x, chão-1) in reached`.
- `tools/areas.py`: `AreaDef` não tem equipamento; só existe `FRIGATE` (área 3).
- Antes de mexer (22/10/2026): `validate.py` → "28 salas, 60 portas, 0 problemas";
  `build/metroid_prime_snes.ips` sha1 `e9b0db220a7f5d7540b02b2ccbbd6e3889e28555`.

### Física do pulo medida no emulador

Método: `tools/snesrun` com a ROM construída. Novo jogo, porta a porta até a `evac_area`, os 4
inimigos da sala apagados (`$0F86+$40·i` byte alto = `$02`, senão o empurrão do dano estraga a
medida), equipamento ligado `$09A2` = 0 (nada) ou `$0100` (só Hi-Jump). A Samus é posta no chão
(linha 27, topo do chão = y 432) na coluna 14, que tem ar até a linha 2. A cada quadro: x `$0AF6`,
y `$0AFA`, raio vertical `$0B00`; pé = y + raio (o raio muda quando ela gira). Resultado igual em
todas as rodadas (o emulador é determinístico).

| Pulo | Como | Subida do pé | Tempo no ar | Distância na volta ao mesmo nível |
|------|------|--------------|-------------|-----------------------------------|
| parado, sem itens | A segurado | **113 px** (432 → 319) | 93 quadros | 0 |
| parado + direção, sem itens | direita+A juntos, parada | **113 px** | 93 quadros | **115 px** |
| parado, Hi-Jump | A segurado | **169 px** (432 → 263) | — | 0 |
| andando (com embalo), sem itens | 16 quadros andando, depois +A | 120 px | ~92 quadros | ~128 px |
| correndo (B) | — | não medido com folga (bate na parede) | | |

Distância horizontal do pulo "parado + direção" quando o pé, já descendo, passa r blocos acima
do chão de onde saiu (o maior x com subida ≥ 16·r px, do quadro em que sai do chão até pousar):

| r (blocos) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|------------|---|---|---|---|---|---|---|---|
| px | 115 | 109 | 105 | 100 | 94 | 87 | 79 | 62 |

Conferência direta: na `evac_area`, a plataforma da linha 20 (colunas 6–12) fica a **7 blocos
exatos** (112 px) acima do chão. Com a Samus parada 3 blocos à direita da ponta, esquerda+A: ela
pousa em cima (pé em 320, `$0AFA` = `$012B`). 8 blocos (128 px) passam da subida medida (113 px).

Decisões:
- O modelo usa o pulo **parado + direção** (o mais simples). Embalo, corrida, wall-jump, bomb jump,
  mockball e outras técnicas **não** são supostos para caminho obrigatório. O pulo andando sobe e
  vai mais longe (120/128 px); fica como folga do jogador.
- Hi-Jump só aumenta a altura do "sobe ao lado e entra" (d = 1, abaixo); os saltos de vão usam a
  tabela sem Hi-Jump (mais curta = mais cautelosa) com a folga de teto da subida com Hi-Jump.

## Mudança proposta

### Modelo (novo `tools/smlib/reach.py`)

Grade de blocos (16×16 px). Tipo do bloco = `palavra >> 12`.

- **Corpo cabe** num bloco de tipo ar `0`, porta `9`, tampa atirável `C` e extensões `5`/`D` (as
  tampas abrem com o Power Beam). Sólido `8`, rampa `1` (casco da nave) e o resto bloqueiam.
- **Chão** = qualquer bloco que não seja ar `0` (sólido, rampa, porta, tampa).
- **Posição de pé** (x, y): chão em (x, y+1) e corpo cabe em (x, y), (x, y−1), (x, y−2) (Samus em
  pé tem 42 px = 3 blocos).
- **Cair**: `pousa(x, y)` desce enquanto não há chão embaixo e o corpo cabe; dá a posição de pé.
- Constantes: `JUMP_RISE_PX = 113`, `HIJUMP_RISE_PX = 169`, `JUMP_ARC_PX = {0: 115, …, 7: 62}`.
  Subida máxima H = subida // 16 → **7 blocos** (Hi-Jump: **10**). Alcance W(r) = `JUMP_ARC_PX[r]
  // 16` (centro a centro): r ≤ 0 → 7; 1–3 → 6; 4–5 → 5; 6 → 4; 7 → 3.
- **Transições** a partir de (x, y), lado s = ±1:
  1. **Andar/cair**: o corpo cabe na coluna x+s nas linhas y−2..y → `pousa(x+s, y)`.
  2. **Subir ao lado** (d = 1, sobe r = 1..H): alvo (x+s, y−r) de pé; coluna x livre das linhas
     y−r−3 .. y (um bloco de folga acima da cabeça no alto).
  3. **Saltar vão** (2 ≤ d ≤ W(r), r ≤ min(H, 7), alvo pode estar mais baixo): alvo (x+s·d, y2) de
     pé; teto cauteloso: em todas as colunas de x até x+s·d, livre desde a linha do alto do pulo
     inteiro (`y − 2 + piso((6 − subida)/16)`, isto é y−9 sem Hi-Jump, y−13 com) até a linha de pé
     daquela coluna (x: y; alvo: y2; entre elas: a mais baixa de y, y2). Sem pulo baixo "por baixo
     do teto": é cauteloso de propósito.
- **Entradas**: porta L/R → `pousa(2 ou wb−3, tela·16+9)`; porta T (Samus cai de cima) →
  `pousa(tela·16+7, 3)`; porta B (vem de baixo) → `pousa(tela·16+7, hb−4)`; spawn → `pousa` da
  célula do spawn. Entrada que não dá posição de pé = problema.
- **Porta alcançada**: L/R se alguma posição alcançada está na coluna 2 (wb−3) com o corpo
  encostando nas linhas 6–9 da porta; T se alguma posição alcançada numa coluna da porta tem a
  coluna livre até a linha 0 e o topo da Samus no alto do pulo entra na linha 0
  (`(y−2)·16 + 6 − subida < 16`); B se alguma posição alcançada numa coluna da porta tem y ≥ hb−4.
- **Regra da sala**: de **cada** entrada (cada porta e o spawn) todas as portas são alcançáveis
  (o caminho pode ser de mão única, como uma queda; por isso não basta olhar só a primeira entrada).
  Save station, map station e nave usam o conjunto alcançado a partir da primeira entrada (as
  posições de pé), como hoje.

### Equipamento por área

- `reach.Loadout(space_jump, hi_jump, morph)`; `SPACE_JUMP_MORPH` e `POWER_BEAM_ONLY`.
- `AreaDef.loadout` (padrão `POWER_BEAM_ONLY`, o mais estrito); `FRIGATE.loadout = SPACE_JUMP_MORPH`.
- Com Space Jump o validador faz **exatamente** o que faz hoje (ar conectado). Morph sem Space Jump
  não é modelado (passagens de 1 bloco ficam inalcançáveis: cauteloso).

### Testes do modelo (sem emulador, rodam dentro do `validate.py`)

`reach.self_test()` monta salas sintéticas em ASCII e confere o resultado esperado; qualquer
diferença vira problema do validador (assim uma mudança no modelo que o enfraqueça é pega).

### Teste de medição no emulador

`pulo_sem_space_jump_medido` em `tests/run_tests.py`: o roteiro do método acima. O
`run_tests.py` ganha um verificador por teste (função que lê a saída do `peekw`): subida parada,
subida com Hi-Jump e a tabela `JUMP_ARC_PX` recalculadas da trajetória têm que ser **iguais** às
constantes de `reach.py`; e `expect 7E0AFA 012B` depois do pulo para a plataforma de 7 blocos.

## Critérios de aceite

1. `python3 -I tools/validate.py` → "28 salas, 60 portas, 0 problemas" (fragata com Space Jump +
   Morph = comportamento de hoje). (protege=fragata; falha_quando=o caminho com Space Jump mudar)
2. `python3 -I tools/build.py` → `.ips` sha1 `e9b0db220a7f5d7540b02b2ccbbd6e3889e28555` (só
   ferramentas de checagem mudam).
3. `python3 -I tests/run_tests.py` → 21/21 (20 de antes + `pulo_sem_space_jump_medido`).
   (protege=as constantes; falha_quando=o motor/ROM mudar a física ou alguém mexer nos números;
   não_prova=pulos com embalo/corrida)
4. `reach.self_test()` sem problemas, com estes casos (cada um é uma mutação que tem que falhar):
   a. degrau de 7 blocos ao lado → alcança; 8 → não.
   b. com Hi-Jump: 10 → alcança; 11 → não.
   c. vão no mesmo nível: alvo a 7 colunas (6 de buraco) → alcança; 8 → não.
   d. vão subindo 7 blocos: 3 colunas → alcança; 4 → não.
   e. degrau de 7 com teto baixo em cima da Samus (sem espaço para subir) → não.
   f. vão de 7 colunas com teto baixo no meio → não.
   g. queda: desce um buraco de 8 blocos → alcança embaixo; de baixo não volta em cima.
   h. com Space Jump: degrau de 8 → alcança (ar conectado).
   i. porta de teto (linha 0): Samus com o pé na linha 9 alcança pulando; na linha 10 não.
5. Mutação real conferida à mão (anotada em Desvios): mudar `JUMP_RISE_PX` para 129 faz
   `self_test` acusar o caso (a) e o teste do emulador falhar.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `reach.self_test()` (casos a–i) | +1 checagem (9 casos) |
| run_tests.py (emulador) | `pulo_sem_space_jump_medido` | +1 |
| build | sha1 do .ips igual | 1 |

## Riscos e reversão

- Modelo cauteloso demais (teto de pulo inteiro nos vãos): salas do Tallon podem precisar de mais
  ar acima dos vãos. Se uma sala da 07g precisar, refina-se aqui com pulo baixo medido.
- Rampas viram degraus (bloco cheio): uma rampa de verdade é mais fácil que o modelo; cauteloso.
- A medida depende do `snesrun`/LakeSnes ser fiel; o teste da plataforma de 7 blocos confirma no
  próprio jogo.
- Reversão: `tools/smlib/reach.py`, `tools/validate.py`, `tools/areas.py`, `tests/run_tests.py`.

## Fora de escopo

- Salas do Tallon (07d/07g); nenhuma sala da fragata muda.
- Morph Ball sem Space Jump, bombas, Grapple, Speed Booster, água, inimigos como plataforma.
- Pulos com embalo/corrida, wall-jump e técnicas avançadas como caminho obrigatório.
- Progressão por itens entre salas (07h).

## Desvios (preenchido na implementação)

- **Verificação (22/10/2026):** `validate.py` → "28 salas, 60 portas, 0 problemas"; `build.py` →
  `.ips` sha1 `e9b0db220a7f5d7540b02b2ccbbd6e3889e28555` (igual); `run_tests.py` → 21/21.
- `self_test` escreve os números da spec por extenso (H = 7, Hi-Jump = 10, vão = 7, vão subindo 7
  = 3) em vez de recalcular das constantes: assim mudar uma constante também acusa no validador,
  não só no teste do emulador.
- Critério 4i reescrito em linhas (o texto antigo, "7 linhas abaixo", não batia com a conta).
- Mutações feitas à mão e desfeitas (critério 5):
  - `JUMP_RISE_PX = 129` → validate: "degrau de 8" e "porta de teto, pé na linha 10" (2 problemas);
    emulador: "pulo parado: subiu 113 px, reach.py diz 129" (e o mesmo no com_direcao).
  - `JUMP_ARC_PX[0] = 116` → emulador falha (alcance medido 115).
  - Samus posta 6 blocos mais longe da plataforma de 7 → `expect 7E0AFA 012B` falha (`018B`).
  - Na lógica: H+1 → "degrau de 8" e "Hi-Jump degrau de 11"; W+1 → "vão de 8 colunas" e
    "vão subindo 7: 4 colunas"; sem a regra de teto → "vão de 7 com teto baixo no meio".
- **A fragata no modelo sem Space Jump** (só informação; não entra no `validate`, a fragata tem
  Space Jump + Morph): 28 problemas em 16 salas. São reais, não do modelo: poços com degraus de
  8+ blocos (`mech_shaft`, `vent_*`, `elevator_*`, `cargo_lift`…) e passagens de 2 linhas que
  pedem Morph (ex.: pilar da `security_hall`, colunas 15–16, deixa só as linhas 8–9). Trocando a
  regra de teto por "só a altura do corpo" sobram 26 em 17 salas: a cautela do teto quase não pesa.
- Cuidado para a 07g: no SM bater a cabeça no teto não mata o pulo (ela só para de subir). A regra
  de "pulo inteiro livre acima do vão" é mais rígida que o jogo; se uma sala do Tallon precisar de
  vão sob teto baixo, medir o pulo com batida no teto e refinar aqui.
- A medida apaga os 4 inimigos da `evac_area` (`$0F87+$40·i = $02`); sem isso o empurrão do dano
  mudava x e a altura (visto na primeira rodada).
