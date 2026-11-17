# 09e — Power Bombs e as paredes do X-Ray

Estado: verificada (23/10/2026: validate 72/148/0 com "alcançáveis agora: 44"; .ips sha1 `9bc37cab…3462` igual em dois builds; 48/48 testes)
Esforço estimado: 1–1,5 dia (modelo e validador 0,5 d; Life Grove e item 0,1 d; testes no emulador 0,5 d; verificação 0,25 d)
Épico: [09 — Itens de trava](09-itens-de-trava.md) (linha 09e; decisões 1, 3, 4 e 5)

## Contexto

Depois da 09d o Tallon inteiro é jogável a pé, mas o X-Ray Visor do Life Grove fica no chão aberto: no Prime ele fica
dentro de paredes que só a Power Bomb quebra ("Destroyable Wall" ×5 + "Power Bomb Scan Hint", dados), e a Power Bomb
(linha 19 de `items.py`, bit `$B3`) ainda não tem lugar. Esta filha põe a Power Bomb na Mines East, cerca o X-Ray com
blocos de Power Bomb e ensina esses blocos ao modelo de alcance e ao validador. A ordem fica a do épico: o X-Ray passa
da rodada 5 para a 6 (a seguinte à da Power Bomb).

## Estado atual (verificado)

Na pasta real: `python3 -I tools/validate.py` → "… 44 salas construídas, alcançáveis agora: 44" e "72 salas, 148 portas,
0 problemas"; `.ips` sha1 `ad0ef09f8a7e41b88d596947701cf844b069eec3`; 47/47 testes.

- **Rodadas hoje** (roteiro `scratchpad/s09e/rounds.py`, cópia do da 09d): 0 Power Beam → Morph; 1 → Bombas, Wave; 2 →
  Space Jump; 3 → Ice; 4 → Gravity; 5 → as 21 salas de D/E, Plasma e **X-Ray**; 6 → Arbor. Power Bomb sem lugar.
- **Life Grove** (`tools/tallon/layouts.py:757`, colisão impressa): chão do bosque na linha 30 (colunas 18–56), pilares
  Chozo nas colunas 24–25 e 50–51 (linhas 26–29), ar das linhas 1 a 29 entre eles; X-Ray em (40, 29) (`items.py`).
  Uma porta só (L0, para o Life Grove Tunnel).
- **Mines East** (`low_transport("L")`, igual à Chozo South): porta L1, corredor nas linhas 17–25, chão na linha 26,
  plataforma do elevador nas colunas 9–12; (6, 25) é ar com chão embaixo, 4 colunas da porta (a Plasma está no mesmo
  lugar da Chozo South).
- **Bloco de Power Bomb** (ROM `base/sm_fix.sfc` e C `vendor/sm/src`): tiro em bloco tipo C → PLM pela tabela
  `$94:9EA6` + 2·BTS (lida): BTS `$08` → `$D084` (setup `$CF2E`, lista `$CB94`), BTS `$09` → `$D088` (setup `$CF2E`,
  lista `$CC20`). Setup `$CF2E` = `PlmSetup_RespawningPowerBombBlock` (`sm_84.c:2250`): só Power Bomb (`$300`) quebra;
  bomba (`$500`) vai para a lista `$C91C`, outro tiro apaga o PLM (o bloco fica). Lista `$CB94` (BTS 8): quadros de
  quebrar `$53/$54/$55`, **`$0180` quadros de ar**, quadros de volta, `$8B17` (redesenha o bloco: `$057`) → **volta**;
  lista `$CC20` (BTS 9): quebrar, ar, `$86BC` (apaga) → **não volta** (bytes lidos; a medir no emulador). A vanilla usa
  só BTS 9 em bloco de PB (todas as salas de `research/sm_rooms.json`, roteiro `scratchpad/s09e/scanC.py`), sempre
  disfarçado de terreno; o metatile CRE **`$057`** é o bloco de PB visível do SM (o que o jogo redesenha ao voltar; desenho
  nos tilesets 0 e 2: esfera com gomos num quadrado, `scratchpad/s09e/mt_t0.png`).
- **Alcance da explosão** (`BlockFunc_A06A`, `sm_94.c:1567`): a cada quadro a Power Bomb testa os blocos da borda do
  retângulo (x ± R, y ± 3R/4), R crescendo até `$86` px: quebra blocos a até ~8 blocos na horizontal e ~6 na vertical.
- **Modelo** (`tools/smlib/reach.py`): `BODY_TYPES` inclui o tipo C (tampas de porta), então um bloco C seria ar para o
  corpo; `with_bombs` só conhece o tipo F; `Loadout` não tem Power Bomb. `validate.foot_grid` e o flood não recebem o BTS.
  `items_loadout` ignora `POWER_BOMB` (está em `GEOMETRY` e em `TIERS[5]`, sem efeito).

## Mudança proposta

### 1. Item (`tools/tallon/items.py`)

| # | Item | Bit | Sala | Lugar | Fase |
|---|------|-----|------|-------|------|
| 19 | Power Bomb `$EEE3` | `$B3` | Transport to Phazon Mines East | (6, 25), no chão | 0 |

`Item` ganha `needs` (itens de geometria a pé atrás dos quais o lugar fica): X-Ray = `{MORPH, POWER_BOMB}`.

### 2. Life Grove: cabana de blocos de Power Bomb em volta do X-Ray (`layouts.py`)

- **15 blocos de PB**: paredes nas colunas 37 e 43 (linhas 26–29) e teto na linha 25 (colunas 37–43). Dentro, colunas
  38–42, linhas 26–29 (4 linhas: ela fica de pé). O teto fecha a cabana (sem ele a Samus subiria a parede de 4 e cairia
  dentro). Por cima da cabana ela passa para o leste (degrau de 5).
- Bloco de PB = **tipo C, metatile CRE `$057`, BTS `$09`** (a que não volta, se o emulador confirmar; senão a outra,
  anotado), em `Shape.blocks` como os blocos de bomba (`layouts.power_bomb_block`). Desvio da instrução da tarefa ("tipo
  F com o BTS de PB"): o tipo F é o bloco de bomba (bomba e PB quebram); o bloco só de Power Bomb do SM é o tipo C com BTS
  8/9 (épico, decisão 1; bytes acima).

### 3. Modelo (`tools/smlib/reach.py`)

- `Loadout.power_bomb`. Bloco de PB = tipo `SHOT_BLOCK` (`$C`) com BTS em `POWER_BOMB_BTS = {$08, $09}`.
- `with_bombs(types, loadout)` vira **`with_breakables(types, bts, loadout)`**: bloco F → ar com as Bombas (como antes;
  a PB também quebra bloco F no jogo, o modelo não conta: conservador, nenhuma trava depende disso); bloco de PB → **ar
  com Morph e Power Bomb** (a PB se põe em bola), **sólido** sem eles (não o tipo C das tampas).
- `self_test` +3: bloco de PB no túnel: só a bola não passa; bola com Power Bomb passa; Bombas sem Power Bomb não passam.

### 4. Validador (`tools/validate.py`)

- `foot_grid(r, l1, bts, …)` e o flood (`tallon_room_reach`) com o BTS; `check_room` (`passable`) com os blocos de PB
  sólidos. `items_loadout`/`loadout_items` com `power_bomb`; `FOOT_GEOMETRY` + `POWER_BOMB` (a regra "cada item a pé
  necessário sozinho" e a água usam o mapa item → campo do `Loadout`).
- `check_room`: sala com blocos de PB é andada também com Morph + Bombas + Power Bomb (portas, sem lugar sem volta: a
  cabana aberta deixa sair).
- **`check_breakables`** cobre os blocos de PB: metatile/BTS do projeto (`$057`/`$09`); sala com algum item que pede
  Power Bomb (`Item.needs`); **quebrável**: com Morph e Bombas (os blocos de PB todos inteiros), de alguma porta, a bola
  chega a ≤ 2 blocos (Chebyshev) dele (a explosão real chega a ~8×6: regra conservadora do épico).
- **`check_item_geometry`** (novo): todo item com `needs`, de toda porta da sala, com Morph + Bombas + Power Bomb (e a água
  da sala) é pego; sem qualquer um dos itens de `needs` (os outros com ele), não é.
- O passeio por fases/rodadas já usa `GRANTS[POWER_BOMB_ITEM]`; com `items_loadout` certo, o X-Ray passa a pedir a PB.
  Esperado (roteiro `rounds.py`): rodada 5 pega a **Power Bomb** (Mines East); **rodada 6: X-Ray** e Arbor. `FIRST_TIER` e
  `Item.tier` continuam 0 (a fase 0 anda até nada mudar); "alcançáveis agora: 44"; 20 itens com lugar.

### 5. Testes no emulador (`tests/run_tests.py`)

- Novo **`tallon_power_bomb`** (atalhos anotados): da estação 1 (Savestation), teleporte de porta pela cadeia da fragata
  afundada até a Hydro Access, GTH → Tunnel E → Mines East (atrás de portas de gelo); **pega a Power Bomb andando para
  dentro dela** (fecha a caixa com A) → bit `$B3`, munição `$09CE/$09D0`; Morph por RAM (pega e testada na 09d);
  teleporte GTH → Life Grove Tunnel → Life Grove; Samus posta no chão a oeste da cabana: em pé para na parede, tiro do
  Power Beam não quebra, X-Ray não pego; bola, SELECT até a Power Bomb (`$09D2 = 3`), X: a PB explode, **os 15 blocos =
  ar na WRAM**; 600 quadros depois continuam ar; desfaz a bola, **anda para dentro do X-Ray** → bit `$AC`, `$09A4` com o
  X-Ray. Fotos `specs/img/09e-*.png`.
- **`tallon_grande_arvore` muda**: na Mines East pega a Power Bomb; no Life Grove, em vez de pegar o X-Ray, anda até a
  cabana e para na parede (X-Ray não pego). O X-Ray passa a ser pego no `tallon_power_bomb`.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 72 salas, 148 portas, **0 problemas**, "alcançáveis agora: 44". (protege = a cabana
   segura sem PB, abre com ela, nada prende; falha_quando = mutações do 2; não_prova = técnicas que o modelo não supõe)
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) blocos de PB viram ar → X-Ray sem PB
   (`check_item_geometry`); (b) Power Bomb sem lugar → X-Ray fora da fase 0; (c) bloco de PB enterrado na rocha →
   `check_breakables`; (d) BTS `$08` (volta) → `check_breakables`; (e) cabana sem teto → X-Ray sem PB; (f) `self_test`
   com o bloco de PB quebrando sem a Power Bomb → falha; (g) bloco de PB numa sala sem item que peça PB → `check_breakables`.
3. Rodadas (roteiro): X-Ray na rodada 6, Power Bomb na 5; as outras como na 09d.
4. `python3 -I tools/build.py` duas vezes, mesmo sha1; espaço anotado (`$8F`: PLM da PB; nível do Life Grove).
5. `python3 -I tests/run_tests.py` → 48/48 (os 47, com `tallon_grande_arvore` mudado, + `tallon_power_bomb`).
6. Fotos `specs/img/09e-*.png` olhadas: a PB no lugar e a mensagem, a cabana (desenho `$057`, sem lixo), a explosão, a
   cabana aberta, o X-Ray pego.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| reach.self_test | bloco de PB por equipamento | +3 |
| validate.py | `check_breakables` com PB; `check_item_geometry`; walk com PB nas salas com blocos de PB | +1, 2 alteradas |
| mutação à mão | (a)–(g) | 7 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `tallon_power_bomb`; `tallon_grande_arvore` alterado | +1 |
| imagem | item, mensagem, cabana antes/depois, X-Ray | ~6 |

## Riscos e reversão

- A explosão da PB também quebra blocos de bomba e abre portas azuis por perto; no Life Grove não há nenhum.
- Teleporte de porta e o deslocamento do BG1 (armadilha da 09d): se os blocos quebrados continuarem desenhados, repor os
  valores de uma entrada a pé (anotado).
- Reversão: `layouts.py` (Life Grove), `items.py`, `reach.py`, `validate.py`, `tests/run_tests.py`; reconstruir.

## Fora de escopo

- Rodadas declaradas (`FIRST_ROUND`/`Item.round`), `stuck` por rodada, `tallon_cadeia_completa` (09f).
- Expansões de Power Bomb; PB abrindo porta amarela; "Power Bomb Scan Hint".

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → linha do Tallon `… 44 salas construídas, alcançáveis agora: 44 …` e `72 salas, 148 portas,
  0 problemas` (~7,5 s; era ~6,3 s: o Life Grove andado também com a PB, `check_item_geometry`).
- Rodadas (roteiro `scratchpad/s09e/rounds.py`): 0 Power Beam → míssil da Landing Site, Morph; 1 → Bombas, Wave, mísseis da Crash
  Site e do Tunnel B; 2 → Space Jump; 3 → Ice, míssil da Root Cave; 4 → Gravity, míssil da Overgrown; 5 (21 salas de D/E) → E-tanks
  da Cargo Lift e da Hydro, mísseis da Biohazard, GTC e LGT, Plasma, **Power Bomb**; **6 (+ Power Bomb, plasma) → X-Ray** e o míssil
  da Arbor (Arbor Chamber). **44 salas, 20 itens**: igual à tabela da decisão 3 do épico. O passeio dá ainda uma volta 7 vazia
  (nenhuma sala, nenhum item): o X-Ray dá `xray` (`GRANTS`), que nenhuma trava usa; a 09f decide se a rodada conta assim.
- `python3 -I tools/build.py` duas vezes (e uma terceira depois dos testes) → `build/metroid_prime_snes.ips` sha1
  `9bc37cab4865b96ea4be265812fad89d3e253462` em todas (logs iguais). Espaço: `$8F` livre a partir de `$8F:F90B` (era `$8F:F905`: +6
  bytes, o PLM da Power Bomb na lista da Mines East); nível do Life Grove 751 → 784 bytes, alocador de nível 24126 → 24159 bytes,
  livres 500129 (nenhum nível cruza banco); `$84`, `$83`, `$A1`, `$B4`, fixo: iguais.
- `python3 -I tests/run_tests.py` → **48/48** (os 47 + `tallon_power_bomb`).
- Experimentos no emulador (cópia da ROM em `scratchpad/s09e/`, `exp_pb.py`, `pb.out`, `pb8.out`): a Power Bomb pega dá 5/5
  (`$09CE/$09D0`) e o bit `$B3` (`$7ED886 = $08`); um SELECT põe `$09D2 = 3` (o segundo volta a 0); o tiro do Power Beam não quebra
  (o PLM se apaga); posta em bola ao lado da parede oeste, a PB quebra **os 15 blocos** (nível na WRAM `$C057` → `$0054` → `$00FF`,
  ~75 quadros depois do X); **BTS `$09` não volta** (600 quadros depois, ar); **BTS `$08` volta** como `$C057` ~450 quadros depois
  de quebrar (BTS posto por RAM num bloco); de pé dentro da cabana aberta, andar para o X-Ray o pega (`$09A4 = $8024`, bit `$AC`).
- Mutações do validador (na memória, `scratchpad/s09e/mut_validate.py`, saída em `mut_validate.out`; sem mutação e depois de
  desfazer: 0 problemas), todas acusadas: (a) paredes de PB viram ar → `check_item_geometry` "pega-se pela porta 0 sem power_bomb"
  (e sem morph); (b) Power Bomb sem lugar → "X-Ray fica alcançável na fase 5 (+ Power Bombs), declarado 0" (e o PLM na ROM sobra);
  (c) bloco de PB numa bolsa 10 linhas abaixo do chão → "a bola não chega a 2 blocos dele"; (d) BTS `$08` → "esperado $057/$09";
  (e) cabana sem teto → X-Ray sem PB; (f) modelo quebrando bloco de PB só com a Morph → `self_test` ("bloco de PB só com a Morph",
  "com as Bombas") e `check_breakables`; (g) bloco de PB no chão da Chozo South → "numa sala sem item que peça a Power Bomb"; (h)
  `needs` do X-Ray esquecido → o mesmo, no Life Grove; (i) bloco de PB tratado como o tipo C das tampas (ar para o corpo) →
  `self_test` e X-Ray sem PB.
- Imagens olhadas (`specs/img/09e-*.png`): a Power Bomb no chão da Mines East (`09e-power-bomb-na-mines-east.png`) e a mensagem
  POWER BOMB; a cabana de 15 blocos (o desenho `$057` do SM: esfera com gomos, sem lixo; zoom em `09e-cabana-do-xray-zoom.png`) com o
  X-Ray dentro e a Samus parada na parede (também sem a PB, `09e-cabana-sem-power-bomb.png`, do `tallon_grande_arvore`); a bola com a
  PB começando a explodir e a parede quebrando; a cabana aberta; a mensagem X-RAY SCOPE e a Samus com o ícone do X-Ray no HUD.

Mudanças de expectativa dos testes existentes:

- `tallon_grande_arvore`: na Mines East pega a Power Bomb andando para dentro dela (bit `$B3`, `$09CE = $09D0 = 5`) (novo).
- `tallon_grande_arvore`: no Life Grove não pega mais o X-Ray (antes: `pick_up` no chão aberto e `$09A5` com o X-Ray); repõe o
  deslocamento do BG1 e uma pausa redesenha, anda da porta até a cabana (`LIFE_GROVE_TO_HUT`) e para na parede oeste (x `$24B`), o
  X-Ray continua lá (`$7ED885` = só o míssil da GTC, `$7ED886` = só a PB). A foto final é `tallon_e_cabana_do_xray.png` (era
  `tallon_e_depois_do_xray.png`).

Desvios e detalhes:

- **Tipo C, não F**: a instrução da tarefa dizia "bloco tipo F com o BTS de PB"; o tipo F é o bloco de bomba (bomba e PB quebram,
  `PlmSetup_RespawningBombBlock2`); o bloco que só a PB quebra é o tipo C com BTS 8/9 (`PlmSetup_RespawningPowerBombBlock`),
  como o épico já dizia. Ficou o tipo C, BTS `$09`, metatile `$057`.
- **Cabana com teto**: o épico falava em "paredes"; sem teto a Samus sobe a parede de 4 e cai dentro (mutação (e)). 15 blocos.
- **`Item.needs` + `check_item_geometry`** (não previstos): o X-Ray não é porta, então a regra da borda não o via; sem uma checagem
  do item, as paredes virando ar (mutação (a)) só apareciam nas rodadas, que são da 09f.
- **Modelo conservador**: a PB também quebra blocos de bomba no jogo; `with_breakables` não conta (nenhuma trava depende disso).
  A regra de alcance da PB (≤ 2 blocos da bola, Chebyshev) é mais estreita que a explosão real (~8 × 6 blocos, `sm_94.c:1567`).
- **Testes e o deslocamento do BG1**: a cadeia de `door_teleport` desde a Savestation deixa `$091F` fora de uma tela inteira (o
  primeiro teleporte, pela porta de chão da Savestation, dá `$00E1`; descer andando por ela dá `$0100`, medido): o item e os blocos
  quebrados se desenhavam 4 linhas abaixo (buracos no chão, X-Ray dentro da rocha; colisão certa). O `tallon_power_bomb` e o
  `tallon_grande_arvore` repõem `$091D/$091F` (`LIFE_GROVE_BG1_OFFSETS = $FC00/$0200`, `MINES_EAST_BG1_OFFSETS = $FC00/$0100`) e
  pausam para redesenhar. No jogo normal não acontece (a transição de porta andando alinha a câmera). Pôr a câmera por RAM
  (`tallon_look`) também desalinhava o redesenho dos blocos quebrados: o teste chega à cabana andando da porta.
- Atalhos do `tallon_power_bomb` (anotados no teste): salas por teleporte de porta desde a Savestation, Gravity Suit e Morph por
  RAM; o resto (pegar a PB, andar até a cabana, bola, SELECT, X, desfazer a bola, pegar o X-Ray) é jogado.
