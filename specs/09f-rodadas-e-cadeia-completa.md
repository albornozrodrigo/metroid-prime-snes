# 09f — Rodadas declaradas e a cadeia completa

Estado: verificada (23/10/2026: validate 72/148/0 com "alcançáveis agora: 44, 20 itens em 7 rodadas" (~3,3 s); .ips sha1 `9bc37cab…3462` igual em dois builds e igual ao de antes; 49/49 testes)
Esforço estimado: 1,5–2 dias (validador e mutações 0,5 d; teste ponta a ponta no emulador 1 d; épicos e docs 0,25 d)
Épico: [09 — Itens de trava](09-itens-de-trava.md) (linha 09f; decisões 4 e 5; definição de pronto). Fecha também o
[07 — Tallon Overworld](07-tallon-overworld.md) se a definição de pronto dele estiver cumprida.

## Contexto

Depois da 09e, da nave, só com o Power Beam, a pé, chegam-se às 44 salas e aos 20 itens. Mas o validador ainda fala em
**fases hipotéticas** (`TIERS`: "+ mísseis, Morph, Bombas", "+ Space Jump"…) que não existem mais no jogo: todas as salas e
itens estão declarados na fase 0 (`FIRST_TIER`, `Item.tier`), e a ordem real (as rodadas do épico) só aparece num roteiro
de rascunho. Esta filha troca as fases pelas **rodadas** declaradas, prova que nenhum lugar prende a Samus com o equipamento
de cada rodada e mostra no emulador a cadeia inteira, item por item, na ordem.

## Estado atual (verificado)

Na pasta real: `python3 -I tools/validate.py` → "… 44 salas construídas, alcançáveis agora: 44" e "72 salas, 148 portas, 0
problemas" (~7,9 s); `.ips` sha1 `9bc37cab4865b96ea4be265812fad89d3e253462`; 48/48 testes.

- `tools/tallon/rooms.py`: `TIERS` (7 fases com itens supostos) e `FIRST_TIER` (44 salas, todas 0). `tools/tallon/items.py`:
  `Item.tier` (20 itens, todos 0).
- `tools/validate.py`: `tallon_tiers` anda as 7 fases (cada uma começa com os itens da fase e repete passes até nada novo)
  e devolve a fase de cada sala/item e o que a Samus tem ao chegar a cada sala (`arrival`); `check_tallon_tiers` compara com
  as declarações. `tallon_rounds` (09d) anda os passes da fase 0 (= as rodadas) para `check_tallon_return`. Usam o `arrival`:
  `check_tallon_water`, `check_tallon_enemies`. `tallon_report` conta "alcançáveis agora" = salas da fase 0.
- Lugares sem volta (`reach.stuck`): `check_room` anda cada sala a pé com o equipamento da chegada, com Morph + Bombas e,
  na sala com blocos de PB, com a PB; `check_tallon_water` anda a Vent C sem a suit. A rodada 1 (mísseis + Morph, **sem**
  Bombas) não é andada por ninguém.
- Rodadas medidas (roteiro `scratchpad/s09e/rounds.py`, rodado agora): 0 → 9 salas, míssil da Landing Site e Morph; 1 → 6
  salas, Bombas, Wave, mísseis da Crash Site e do Tunnel B; 2 → Gully, Alcove, Space Jump; 3 → nenhuma sala, Ice, míssil da
  Root Cave; 4 → 5 salas, Gravity, míssil da Overgrown; 5 → 21 salas, 2 E-tanks, 3 mísseis, Plasma, Power Bomb; 6 → Arbor,
  X-Ray, míssil da Arbor; **7 → nada** (o X-Ray dá `xray`, que nenhuma trava usa). 44 salas, 20 itens: a tabela do épico.

## Mudança proposta

### 1. Rodadas declaradas (`rooms.py`, `items.py`)

- Saem `TIERS` e `FIRST_TIER`. Entra **`FIRST_ROUND`** (sala → rodada em que fica alcançável pela primeira vez), escrito
  por rodada, igual à tabela da decisão 3 do épico (0: 9 salas; 1: 6; 2: 2; 3: nenhuma; 4: 5; 5: 21; 6: Arbor).
- `Item.tier` vira **`Item.round`**: 0 míssil da Landing Site, Morph; 1 Bombas, Wave, mísseis da Crash Site e do Tunnel B; 2
  Space Jump; 3 Ice, míssil da Root Cave; 4 Gravity, míssil da Overgrown; 5 Plasma, Power Bomb, E-tanks da Cargo Lift e da
  Hydro, mísseis da Biohazard, GTC e LGT; 6 X-Ray, míssil da Arbor.

### 2. Passeio por rodadas (`validate.py`)

- **Rodada k** = um passeio da nave com o equipamento de todos os itens pegos nas rodadas anteriores (rodada 0: só o Power
  Beam). O passeio anda sala a sala (`tallon_room_reach`), passa uma porta só com os itens não-geometria da trava (como hoje)
  e junta os itens que o corpo alcança; os itens pegos na rodada k só valem a partir da k+1.
- **Regra de parada (decisão aberta do épico, decidida aqui)**: o passeio para quando uma volta **não acrescenta nenhuma sala
  e nenhum item**; essa volta vazia **não é rodada** e **não é erro**. Por quê: é a regra mais simples que fecha certo — se a
  volta k não pegou item novo, o equipamento da k+1 é o mesmo da k (os itens pegos já estavam pegos antes), então nada mais
  muda: é o ponto fixo. A outra regra possível ("para quando nenhum item dá habilidade nova") contaria uma rodada a menos
  só quando o último item não dá nada, e trataria diferente um E-tank e o X-Ray; a regra escolhida não olha o que cada item
  dá. Com ela o Tallon tem **7 rodadas (0–6)**; a volta com o `xray` anda e é descartada.
- `tallon_progress_built()` (cache por `check()`, no lugar de `tallon_tiers_built`): as rodadas (equipamento, estados
  (sala, entrada) alcançados), a primeira rodada de cada sala e de cada item, e o que a Samus tem ao chegar a cada sala
  (`arrival` = equipamento da primeira rodada da sala; quem usa: água e justiça dos inimigos, sem mudança de regra).
- **`check_tallon_rounds`** (no lugar de `check_tallon_tiers`): cada sala construída alcançada na rodada `FIRST_ROUND`;
  cada item com lugar alcançado na rodada `Item.round` (e lugar de ar fora das portas, como antes); diferença = problema
  com a sala/item, a rodada achada (com o equipamento dela) e a declarada; sala ou item nunca alcançado = problema;
  `FIRST_ROUND` com sala fora do build = problema; lugar sem rodada (ou o contrário) = problema.
- O caminhamento de sala fica memorizado por (sala, entrada, itens de geometria) num cache só por `check()`, usado pelas
  rodadas, pela volta à nave (`check_tallon_return`) e pelo `stuck` por rodada.

### 3. `stuck` por rodada (`validate.py`, `check_tallon_round_stuck`)

Em cada rodada k, para todo estado (sala, entrada) que o passeio alcança, a sala é andada daquela entrada com o equipamento
da rodada k (`items_loadout`, com a água da sala) e nenhum lugar alcançado pode ficar sem volta a uma porta **que a Samus
possa usar** nessa rodada (porta sem trava, ou cujos itens não-geometria ela tem). Com Space Jump (seco, ou na água com a
suit) o modelo é o flood fill (ar ligado vale nos dois sentidos): nada a andar. Na prática: rodadas 0–2 a pé (nada; mísseis
+ Morph; + Bombas e Wave) e a Vent C sem a suit na rodada 4. A rodada 1 (Morph sem Bombas) passa a ser andada.

### 4. Linha do Tallon

`tallon_report`: "alcançáveis agora: 44, 20 itens em 7 rodadas" (salas e itens alcançados pelas rodadas; número de rodadas).

### 5. Teste ponta a ponta `tallon_cadeia_completa` (`tests/run_tests.py`)

Da nave (chegada normal), na ordem das rodadas, os 20 itens, cada um **pego andando para dentro dele** (`pick_up`, caixa
fechada com A), e a trava de cada rodada aberta pelo meio certo:

| Rodada | Itens | Trava aberta de verdade no teste |
|--------|-------|----------------------------------|
| 0 | míssil da Landing Site (andando da nave, como `tallon_first_missile`), Morph | — (só Power Beam) |
| 1 | Bombas, Wave, mísseis da Crash Site e do Tunnel B | as 3 portas vermelhas com mísseis (Temple Security, Root Tunnel, Waterfall) |
| 2 | Space Jump | os 2 blocos de bomba da Tallon Canyon, bola, sobe à Gully |
| 3 | Ice, míssil da Root Cave | borda de Space Jump: sobe a Root Cave até a prateleira com o Space Jump |
| 4 | míssil da Overgrown, Gravity | portas de gelo (Crash Site → Overgrown → Tunnel C → Chozo East), tiro do gelo |
| 5 | E-tanks, 3 mísseis, Plasma, Power Bomb | anteparo da Vent C com a Gravity Suit (água); uma porta de onda com o Wave |
| 6 | X-Ray, míssil da Arbor | cabana de Power Bomb; porta de plasma da Root Cave |

Atalhos permitidos, cada um anotado no teste (como nos testes anteriores): **teleporte de porta** (`door_teleport`) entre
trechos, só por portas sem trava ou já abertas (vermelha com o bit ligado; de feixe só depois de a Samus ter o feixe e já ter
aberto uma porta daquele feixe no teste; borda de Space Jump só depois de ter subido uma); **Samus posta por RAM** perto de
uma porta, de um item (no chão dele, `pick_up`) ou na ponta da plataforma da Canyon; **munição e energia repostas por RAM**
antes de uma porta vermelha (5 mísseis por porta; na rodada 1 só há 5–15) e entre trechos; volta à nave por RAM (estação 0)
no fim. O deslocamento do BG1 (`$091D/$091F`) é reposto numa tela inteira (`whole_screen_bg1`) onde um PLM se redesenha
(blocos que quebram, itens nas fotos). Nada de equipamento por RAM.

No fim: os **20 bits de item**; `$09A4` com Morph, Bombas, Gravity, Space Jump e X-Ray; `$09A8` = Wave + Ice + Plasma
(`$000B`); mísseis máximos 45, Power Bombs 5, energia máxima 299 (`$012B`). Salva na nave, game over, continue: os 20 bits e
o equipamento voltam. Fotos `specs/img/09f-*.png`.

### 6. Épicos e docs

- Épico 07: conferir a definição de pronto ("pega os 13 itens do SM … sem softlock (validador + rota no emulador)") contra o
  validador e o `tallon_cadeia_completa`; se cumprida, `verificada`.
- Épico 09: as 6 filhas verificadas e a definição de pronto cumprida → `verificada`.
- `specs/README.md`, tabelas de filhas dos épicos, `HANDOFF.md`, `README.md`.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 72 salas, 148 portas, **0 problemas**, linha do Tallon "alcançáveis agora: 44, 20 itens
   em 7 rodadas". (protege = ordem declarada, sem armadilha em nenhuma rodada; falha_quando = mutações do 2; não_prova =
   técnicas fora do modelo, armadilha só com Space Jump, que o flood fill não vê)
2. Mutações na memória (roteiro `scratchpad/s09f/mut_validate.py`; desfeitas, depois 0 problemas), cada uma acusada:
   (a) `FIRST_ROUND` de uma sala errado; (b) `Item.round` de um item errado; (c) item movido para antes (Ice no lugar do
   míssil do Tunnel B) → rodadas acusadas; (d) item movido para depois (Wave no lugar do míssil da Overgrown); (e) armadilha
   só numa rodada do meio (bolsa de bola com chão de bloco de bomba na Tallon Canyon: prende com Morph sem Bombas, rodada 1)
   → só o `stuck` por rodada acusa (`check_room` não); (f) o X-Ray sem nada a dar (`GRANTS`) → as mesmas 7 rodadas, 0
   problemas (a volta vazia não é erro nem rodada).
3. `python3 -I tools/build.py` duas vezes, mesmo sha1; mudança só do validador (e dos testes): sha1 esperado igual ao de
   antes (`9bc37cab…3462`).
4. `python3 -I tests/run_tests.py` → 49/49 (os 48 + `tallon_cadeia_completa`); nenhuma expectativa antiga muda.
5. Fotos `specs/img/09f-*.png` olhadas (uma por rodada, no mínimo: trava aberta e item pego; o fim).
6. Épicos 07 e 09 com estado conferido e anotado.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `check_tallon_rounds` (no lugar de `check_tallon_tiers`); `check_tallon_round_stuck` | +1, 1 trocada, 3 usam o passeio novo |
| mutação à mão | (a)–(f) | 6 |
| build | sha1 igual (dois builds) | 1 |
| run_tests.py | `tallon_cadeia_completa` | +1 |
| imagem | rodadas, travas, fim | ~10 |

## Riscos e reversão

- Teste longo (todo o Tallon): o mais lento da bateria; os testes rodam em paralelo, então o tempo total sobe para o dele.
- Subir a Root Cave com o Space Jump no emulador pede ritmo de botões medido; se não fechar, a Samus é posta por RAM na
  prateleira e a "borda de Space Jump" é provada noutra borda (anotado em Desvios).
- Reversão: `tools/validate.py`, `tools/tallon/rooms.py`, `tools/tallon/items.py`, `tests/run_tests.py`.

## Fora de escopo

- Space Jump no modelo a pé (o flood fill continua o modelo com Space Jump); técnicas (bomb jump, wall-jump).
- Mudar lugar de item, sala ou trava.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → linha do Tallon `… 44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas …` e
  `72 salas, 148 portas, 0 problemas`, **~3,3 s** (era ~7,9 s: sai o passeio das 7 fases hipotéticas, que repetia os passes com
  itens supostos, e o caminhamento de sala fica memorizado por `check()`; o `stuck` por rodada custa pouco porque a partir da
  rodada 3 o modelo é o flood fill).
- Rodadas (as do passeio, iguais à tabela do épico): 0 → 9 salas, 2 itens; 1 → 6, 4; 2 → 2, 1; 3 → 0, 2; 4 → 5, 2; 5 → 21, 7;
  6 → 1, 2. A volta 7 (com o `xray`) não acrescenta nada e é descartada: não é rodada nem erro.
- `python3 -I tools/build.py` duas vezes → sha1 `9bc37cab4865b96ea4be265812fad89d3e253462` nas duas, **igual ao da 09e** (mudança
  só de validador e testes; logs iguais).
- `python3 -I tests/run_tests.py` → **49/49** (os 48 + `tallon_cadeia_completa`, ~200 s sozinho: o mais longo da bateria).
- Mutações (na memória, `scratchpad/s09f/mut_validate.py`, saída em `mut_validate.out`; sem mutação e depois de desfazer: 0
  problemas), todas acusadas:
  (a) `FIRST_ROUND` da Gully 2 → 3: "tallon_gully fica alcançável na rodada 2 (com [bombs, missile, morph, wave]), FIRST_ROUND
  diz 3"; (b) `Item.round` do X-Ray 6 → 5: "é pego na rodada 6 (…), declarado na rodada 5"; (c) Ice trocado de lugar com o míssil
  do Tunnel B (antes): 42 problemas (gelo na rodada 1, Frigate Access/Vent C na 2, Overgrown/Tunnel C/Chozo East na 3, Arbor na
  5…; rodadas 0–5 em vez de 0–6); (d) Wave trocado com o míssil da Overgrown (depois): "Wave Beam … é pego na rodada 4, declarado
  na rodada 1" e o míssil na 1 (declarado 4), mais os PLMs da ROM (não reconstruída); (e) armadilha só na rodada 1 (Tallon Canyon:
  túnel de bola no terraço, linha 21, x 40–43, que acaba numa bolsa de 1 linha em x 43–44; bloco de bomba no chão do túnel em
  (41, 22) que, com as Bombas, derruba a bola por um poço até um túnel na linha 25 que sai no penhasco): `check_room` sozinho (a pé
  e com Morph + Bombas) **0 problemas**; com o `stuck` por rodada, 3: "rodada 1 ([missile, morph]): em tallon_canyon pela entrada
  1/2/3, 2 lugares sem volta a uma porta que ela possa usar (ex.: coluna 43, pé na linha 22)"; (f) o X-Ray sem nada a dar
  (`GRANTS` vazio): 0 problemas, as mesmas 7 rodadas.
- Fotos olhadas (`specs/img/09f-*.png`, cópias das de `build/tests/cadeia_*.png`): o Morph pego; a porta vermelha da Temple Security
  fechada e abrindo com mísseis; o Wave; os blocos de bomba da Canyon e a Gully; o Space Jump; a Samus na prateleira da Root Cave
  depois da subida (caixa MISSILE) e o Ice; a porta de gelo da Crash Site fechada e abrindo (verde); a Gravity Suit; a Vent B (passou o
  anteparo); a porta de onda aberta; o Plasma; a Power Bomb; a cabana de PB inteira, aberta e o X-Ray; a porta de plasma (laranja)
  fechada; o míssil da Arbor; a tela de equipamento no fim (Ice, Wave, Plasma; Gravity; Morph, Bombas; Space Jump).

Mudanças de expectativa dos testes existentes: **nenhuma**. Mudanças em ajudantes de teste, sem efeito nos testes antigos:
- `pick_up`: o "ainda não pego" lê 16 bits (o byte do item e o seguinte) e agora conta os itens já pegos dos dois bytes (como
  `item_not_taken_with`); antes só os do mesmo byte (nenhum teste antigo passava item do byte seguinte). O lugar ao lado do item
  saiu para `near_item`.
- `tallon_first_missile(name)` e `save_on_tallon_ship(shot, energy)`: parâmetros novos com o padrão de antes (nomes das fotos;
  energia depois do refil da nave: 299 com os 2 E-tanks).

Desvios e detalhes:

- **Regra de parada**: decidida como recomendada (volta sem sala nova e sem item novo = ponto fixo, descartada, sem erro); justificativa
  na seção 2.
- **`stuck` por rodada só vê as rodadas a pé**: com Space Jump o modelo é o flood fill, que não tem armadilha por construção. Na
  prática anda as rodadas 0–2 (e a Vent C sem a suit na 4). Uma armadilha que só exista com o Space Jump (cair num poço de onde
  nem o Space Jump sai) o modelo não vê: limite do modelo (já era assim na fragata).
- **Porta "que ela possa usar"**: o `stuck` por rodada só conta as portas cuja trava (fora a geometria) a Samus tem naquela rodada
  (uma porta vermelha na rodada 0 não serve de saída); o `check_room` continua contando todas.
- **Teleporte para cima não pega**: `door_teleport` pela porta de teto do Artifact Temple deixa a Samus no próprio templo (estado
  `$0B`, depois 8 no alto da sala; medido). O teste volta à nave por RAM (estação 0) e segue de lá.
- **A primeira caixa de mensagem**: o A do `tallon_first_missile` chega antes de a caixa aceitar (nos testes antigos o andador a
  fecha com o pulo seguinte); a cadeia dá um segundo A depois.
- **Gravity Suit**: entrando andando pela porta, ela desce os degraus correndo e passa pela suit; posta por RAM 1 bloco a oeste dela
  (o chão do poço tem 4 blocos), anda para dentro.
- **Subida da Root Cave com o Space Jump** (medida, `ROOT_CAVE_CLIMB`): pulo em parafuso só correndo (parada, o pulo é o normal);
  A segurado 30 quadros, solto 12 (o próximo pulo só pega caindo; com 5 de folga não pega); sem direção ela desliza para oeste até a
  parede sob a prateleira, depois segurando → encostada na raiz (x 11) sobe além da prateleira e um último pulo ← pousa nela; anda
  para oeste e pega o míssil e o Ice. Na rodada 6 a mesma subida leva até a porta de plasma. A Samus leva dois toques de inimigo na
  subida (99 → 59) e chega mesmo assim.
- Atalhos do `tallon_cadeia_completa` (anotados no teste, `tallon_full_chain` e ajudantes `chain_*`): salas por `door_teleport` só por
  portas sem trava ou já abertas no teste (vermelha com o bit; de feixe depois de abrir uma daquele feixe; borda de Space Jump — Great
  Tree Hall → Chamber — depois de subir a da Root Cave; na Crash Site ela é posta por RAM na borda da porta de gelo da Overgrown); Samus posta por RAM diante das portas
  (`stand_before_door`, com a câmera na tela da porta e uma pausa para redesenhar), perto dos itens (`pick_up`) e na ponta da
  plataforma da Canyon; mísseis repostos por RAM a 5 antes da porta vermelha do Root Tunnel (a da Temple Security gastou os 5
  da Landing Site); energia reposta por RAM (até o máximo que ela tem); volta à nave por RAM três vezes (depois das Bombas, antes da
  Arbor e no fim). Nenhum item nem feixe por RAM: os 20 pegos andando, cada caixa fechada com A.
- No fim: `$7ED884 = $FFFF`, `$7ED886 = $000F` (os 20 bits), `$09A4 = $9224` (Morph, Bombas, Gravity, Space Jump, X-Ray), `$09A6/$09A8 =
  $000B`, mísseis 45, Power Bombs 5, energia máxima 299; salva na nave, game over, continue: tudo igual.
- Épicos: 07 e 09 fechados (`verificada`), conferidos contra as definições de pronto (anotado em cada um).
