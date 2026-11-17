# 09d — Morph Ball e Bombas

Estado: verificada (23/10/2026: validate 72/148/0 com "alcançáveis agora: 44"; .ips sha1 `ad0ef09f…eec3` igual em dois builds; 47/47 testes)
Esforço estimado: 2–2,5 dias (modelo da bola 0,5 d; validador e mutações 0,5 d; Canyon e itens 0,25 d; testes no
emulador e rotas cegas 0,75 d; verificação 0,25 d)
Épico: [09 — Itens de trava](09-itens-de-trava.md) (linha 09d; decisões 1, 3, 4 e 5; riscos "Rotas cegas" e
"Modelo sem técnicas")

## Contexto

Depois da 09a–09c o gelo, a onda, o plasma e a Gravity Suit existem como item, mas o caminho para eles começa no
Space Jump da Alcove, que fica atrás da Gully, e a Gully atrás da tampa cinza "nunca abre" da T3 da Tallon Canyon
(as paredes de Bombas do Prime). Do pouso, a pé, só 15 salas. Esta filha fecha o MVP do épico: põe a Morph Ball e
as Bombas no Tallon, troca a cinza da Gully por um túnel de Morph com 2 blocos de bomba (os 2 "Breakable Block" do
Prime) e ensina a bola e os blocos ao modelo de alcance. Com isso, só com o Power Beam, a pé: as 44 salas e os 13
itens do Tallon + Morph, Bombas, Ice, Wave, Gravity, Plasma (a Power Bomb é da 09e; o X-Ray fica no chão aberto até lá).

## Estado atual (verificado)

Na pasta real: `python3 -I tools/validate.py` → "… 44 salas construídas, alcançáveis agora: 15" e "72 salas, 148
portas, 0 problemas"; `.ips` sha1 `11071b4656e2f548e832492fe9bc7cb8e64d94bd`; 46/46 testes.

- **Tallon Canyon** (`tools/tallon/layouts.py:121`, colisão impressa do build): a T3 (porta de teto da Gully, colunas
  54–57) tem a tampa cinza `GREY_DOOR_NEVER` (`build.py:617`, `LOCK_OF[BOMBS] = "grey"`); `Canvas.door_gap` põe a
  plataforma na linha 6, colunas 52–59; a Samus sobe nela pulando da ponta oeste da prateleira (coluna 51, pé na
  linha 9: colunas 51 livre das linhas 2 a 9) para (52, 5); em cima, linhas 3–5 livres nas colunas 52–57 (rocha a
  partir da 58). Embaixo da plataforma (linhas 7–9) passa a prateleira da porta R0.
- **Chozo West** (`layouts.py:200`): chão na linha 26, plataforma do elevador nas colunas 7–10; (8, 25) é ar com o
  poço do elevador em cima (as rotas cegas passam por ele indo até a parede oeste). **Artifact Temple**
  (`layouts.py:262`): chão na linha 54, totens nas colunas 10–11 e 16–17 (linhas 50–53); (13, 53) é ar entre eles.
- **Blocos de bomba** (C `vendor/sm/src`): tipo F → `BlockReact_BombableBlock` (`sm_94.c:1535`) → PLM pela tabela
  `$94:A012` + 2·BTS, setup `PlmSetup_RespawningBombBlock2` (`sm_84.c:2227`): bomba (`$500`) ou Power Bomb (`$300`)
  quebram, outro tiro apaga o PLM (o bloco fica). A explosão da bomba testa o bloco dela e os vizinhos
  (`BlockColl_BombExplosion`, `sm_94.c:1449`). **Vanilla** (todas as salas de `research/sm_rooms.json`, roteiro
  `scratchpad/s09d/scanF.py`): o metatile CRE `$05F` é o único CRE usado em bloco F e aparece nos tilesets 0, 6 e 10
  com BTS 0, 4 e 5 (salas `$95FF`, `$965B` no tileset 0); os outros blocos F vanilla são disfarçados de terreno.
  Desenho de `$05F` nos tilesets 0 e 2 (CRE, igual nos dois): quadrado de metal com frisos (`scratchpad/s09d/mt_t0.png`).
  BTS 0–3 / 4–7: qual volta a se fechar → medir no emulador (decisão abaixo).
- **Modelo** (`tools/smlib/reach.py`): a pé só a Samus em pé (3 linhas); `Loadout.morph` "só com Space Jump";
  o flood fill do Space Jump trata como sólido só o tipo 8 (`validate.SOLID_TYPES`), então um bloco F seria ar.
  `validate.foot_grid` não conhece itens. `MOVEMENT = {space_jump, gravity}` decide as bordas; a regra da borda em
  `reach_on_foot` só vale para o Space Jump.
- `tallon_tiers` já registra o que a Samus tem ao chegar em cada sala (09b); `check_tallon_enemies` usa
  `FIRST_TIER == 0` para a justiça dos inimigos.

## Mudança proposta

### 1. Tallon Canyon: túnel de Morph com 2 blocos de bomba (`layouts.py`, `rooms.py`)

- A Samus continua subindo da prateleira (51, 9) para a ponta oeste da plataforma (52, 5) (geometria do caminho das
  rotas cegas igual). A leste dela, **túnel de 1 linha**: rocha em (53, 3), (53, 4) e (54, 4) (teto), **blocos de
  bomba** em (53, 5) e (54, 5) (chão = a plataforma). Depois do túnel, a câmara sob a T3 (colunas 55–57, linhas 3–5
  livres, 3 linhas: a bola se desfaz) de onde o pulo entra na porta.
- Bloco de bomba = bloco tipo F, metatile CRE `$05F` (o que a vanilla mostra), BTS da faixa que **não volta**
  (4, se o emulador confirmar; senão a outra, anotado). Entra no nível como `overlay` (blocos crus, como a
  colisão da nave): `Shape.blocks` → `RoomDef.blocks`.
- `GATES`: Canyon ↔ Gully = `Gate({MORPH, BOMBS}, (), ("tallon_canyon",))`: sem tampa (`LOCK_OF` sem `BOMBS`: a T3
  vira passagem aberta, como as outras portas de teto do Tallon), o lado da Canyon fica "atrás de geometria".

### 2. Itens (`items.py`)

| # | Item | Bit | Sala | Lugar | Fase |
|---|------|-----|------|-------|------|
| 17 | Morph Ball `$EF23` | `$B1` | Transport to Chozo Ruins West | (8, 25), sobre a plataforma do elevador | 0 |
| 18 | Bombas `$EEE7` | `$B2` | Artifact Temple | (13, 53), no chão entre os totens | 0 |

`GRANTS[MORPH_BALL] = {morph}`. Se as rotas cegas não fecharem com o Morph no caminho, o fallback do épico (alto do
poço do elevador, mesma sala) entra e fica anotado.

### 3. Modelo (`tools/smlib/reach.py`)

- `Loadout` ganha `bombs`; `morph` passa a valer a pé. Estado de **bola** `(x, y, BALL)`: 1 bloco de corpo livre;
  rola ±1 para uma célula livre e cai até ter chão; vira bola em todo lugar de pé (mesma célula do pé); **desfaz a
  bola só com 3 linhas livres** (o lugar de pé). Sem pulo em bola, sem bomb jump, sem wall-jump (o caminho
  obrigatório nunca pede técnica). Porta lateral e de chão: a bola entra; de teto: só de pé (pulo).
- `moves(g, estado, loadout)`, `reach`, `stuck` e `door_reached` aceitam os dois estados.
- `flood(passable, start, loadout)`: erro se `loadout.morph` for falso (a célula de 1 bloco pressupõe a bola).
- Bloco de bomba por equipamento: quem monta a grade (`validate.foot_grid(r, l1, wb, hb, loadout)` e o `passable` do
  flood) troca o tipo F por ar com `bombs`; sem elas é sólido (o flood também).
- `self_test` +6: túnel de 1 linha passa só com a Morph; a bola não sobe degrau de 1; desfazer a bola num vão de 2
  linhas não dá (sai do outro lado sem ficar de pé); bloco de bomba sólido sem as Bombas e ar com elas; flood sem
  Morph = erro.

### 4. Validador (`tools/validate.py`, `rooms.py`)

- `MOVEMENT` vira **`GEOMETRY = {space_jump, gravity, morph, bombs, power_bomb}`**: itens que a geometria decide.
  `TIERS`: a fase 1 vira "+ mísseis, Morph Ball, Bombas" de fato (`MORPH` entra no conjunto).
- **Regra da borda generalizada** (`reach_on_foot`): cada entrada anda com o equipamento da área + a geometria da
  própria porta, se ela está atrás de geometria (a T3 da Canyon anda com Morph e Bombas; a câmara da Landing Site
  continua a pé); uma porta atrás de geometria cujos itens a caminhada não tem fica inalcançável de toda entrada que
  não esteja atrás da mesma geometria; e, **com** os itens dela (Morph/Bombas: modelados a pé), alcançável de toda
  entrada. Gravity: como antes (a sala inundada anda com a suit; `check_tallon_water` anda sem).
- **Volta garantida com Morph e Bombas** (o pedaço barato da prova da 09f): toda sala andada a pé é andada também
  com Morph + Bombas, de toda entrada: portas fora de borda alcançadas, bordas de Space Jump não, nenhum lugar sem
  volta (`reach.stuck`).
- **`check_breakables`** (novo): todo bloco F do Tallon é o bloco de bomba do projeto (metatile/BTS); fica numa sala
  com porta atrás de uma trava de Bombas; e é **quebrável de verdade**: com Morph e Bombas, de alguma entrada, a bola
  chega a uma célula vizinha (4 lados) dele com ele ainda inteiro (os outros blocos de bomba já quebrados).
- `tallon_room_reach(r, entrada, itens)`: monta o `Loadout` dos itens (Space Jump, Gravity, Morph, Bombas); o corpo
  da bola pega item. `tallon_tiers`: a porta pede `gate - GEOMETRY`.
- **Justiça dos inimigos** (`check_tallon_enemies`): para as salas a que a Samus chega pela primeira vez só com Power
  Beam, mísseis e Morph (o passeio registra; rodadas 0–1 do épico), não mais `FIRST_TIER == 0`.
- `check_gates`: nenhuma cinza no Tallon (qualquer tampa que não seja vermelha ou de feixe é erro).
- `FIRST_TIER` e `Item.tier`: tudo na fase 0 (esperado: o passeio chega às 44 salas e aos 19 itens com lugar).

### 5. Testes no emulador (`tests/run_tests.py`)

- Novo **`tallon_morph_e_bombas`** (atalhos anotados no teste): teleporte de porta Tunnel A → Chozo West (a rota a pé
  até ali é a da `tallon_rota_mvp`); **pega o Morph andando para dentro dele** → bit `$B1`, `$09A2`/`$09A4` com `$0004`;
  teleporte Temple Lobby → Artifact Temple (atrás da porta vermelha), Samus posta no chão perto dos totens por RAM,
  **pega as Bombas andando** → bit `$B2`, `$1000`; teleporte Canyon Cavern → Tallon Canyon; posta na ponta da
  plataforma (52, 5) por RAM: em pé não passa (encostada no bloco); vira bola, **bomba os 2 blocos**, rola; dentro do
  túnel apertar ↑ não desfaz a bola (raio vertical da bola); na câmara desfaz; pula e entra na Gully. Fotos dos blocos
  antes, quebrando e depois.
- Respawn: no mesmo teste, depois de quebrar, esperar ~600 quadros na câmara e conferir que os blocos continuam
  quebrados (nível na WRAM = ar), se a faixa de BTS escolhida for a que não volta.
- **Rotas cegas** que passam pela Chozo West (`tallon_rota_mvp`, `tallon_mapa_salvo`, `tallon_rota_bc`): pegam o
  Morph (a caixa de mensagem fecha com o A do pulo do andador); no fim `$09A2 = $09A4 = $0004` em vez de 0; ciclos
  remedidos se precisar (cada mudança anotada).
- `tallon_gully_alcove`: a T3 não tem mais tampa: na plataforma, andando para oeste a Samus para nos blocos de bomba
  (só tem o Space Jump), e o pulo a leva de volta à Gully.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 72 salas, 148 portas, **0 problemas**, "alcançáveis agora: 44".
   (protege = lugar/fase dos itens, a trava da Gully, a bola no modelo, a volta com Morph/Bombas; falha_quando =
   mutações do 2; não_prova = técnicas que o modelo não supõe: bomb jump, wall-jump)
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) sem o Morph (linha sem lugar) →
   Bombas, Gully e o resto na fase 1; (b) blocos de bomba viram ar → a T3 alcançável sem Morph/Bombas; (c) bloco de
   bomba enterrado na rocha → `check_breakables`; (d) câmara da T3 com 2 linhas (não desfaz a bola) → T3 inalcançável
   mesmo com Morph e Bombas; (e) Bombas na Gully (atrás dos blocos) → fases erradas; (f) T3 de volta à cinza →
   `check_gates`; (g) `self_test` com a bola subindo degrau de 1 → falha; (h) flood sem Morph → erro; (i) bloco de bomba
   com BTS que volta → `check_breakables`; (j) poço sem volta alcançável só em bola → `stuck` com Morph; (k) justiça
   pela fase declarada (regra antiga) → inimigos da região D/E acusados.
3. `python3 -I tools/build.py` duas vezes, mesmo sha1; espaço anotado (`$8F`: 2 PLMs de item; nível da Canyon).
4. `python3 -I tests/run_tests.py` → 47/47 (os 46, com as mudanças de expectativa anotadas, + `tallon_morph_e_bombas`).
5. Fotos `specs/img/09d-*.png` olhadas: Morph e Bombas no lugar, mensagens, blocos de bomba (desenho certo, sem lixo)
   antes/depois, a Samus em bola no túnel, a Gully.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| reach.self_test | bola, desfazer, bloco de bomba, flood sem Morph | +6 |
| validate.py | `check_breakables`; regra da borda geral; volta com Morph/Bombas; justiça pelo primeiro a chegar; `check_gates` sem cinza | +2, 3 alteradas |
| mutação à mão | (a)–(k) | 11 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `tallon_morph_e_bombas`; 4 com expectativa alterada | +1 |
| imagem | itens, mensagens, blocos, túnel | ~10 |

## Riscos e reversão

- Rotas cegas: a caixa da Morph e o novo teto podem mudar os ciclos; remedir (épico). O andador que pula para a
  direita na prateleira poderia subir na ponta da plataforma (já era possível antes, colunas 51→52).
- Tudo que a bola abre fica alcançável no modelo: o validador anda toda sala também com Morph e Bombas.
- Modelo sem técnicas: bomb jump deixa subir por poços (quebra de sequência, sem prender).
- Reversão: `layouts.py` (Canyon), `rooms.py` (gate/`GEOMETRY`/fases), `items.py`, `reach.py`, `validate.py`,
  `frigate/rooms.py` (`blocks`), `tests/run_tests.py`; reconstruir.

## Fora de escopo

- Power Bomb e as paredes do X-Ray (09e); rodadas, volta à nave por rodada e `tallon_cadeia_completa` (09f).
- Míssil da Landing Site atrás de túnel de Morph; outros túneis de Morph do Prime (Hydro Access, Waterfall).
- Spring Ball, bomb jump no modelo.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → linha do Tallon `… 44 salas construídas, alcançáveis agora: 44 …` e `72 salas, 148
  portas, 0 problemas` (~6,3 s). **Alcançáveis agora: 15 → 44 salas.** Itens com lugar: 19 (os 13 do Tallon + Morph,
  Bombas, Ice, Wave, Gravity, Plasma), todos na fase 0; `FIRST_TIER` = 0 nas 44 salas.
- Ordem que o passeio acha (as voltas do passeio da fase 0 = as rodadas do épico; roteiro `scratchpad/s09d/rounds.py`):
  rodada 0 (Power Beam): 9 salas (Landing Site, Canyon Cavern, Tallon Canyon, Tunnel A, Chozo West, Temple Hall, Temple
  Security, Waterfall Cavern, Root Tunnel), míssil da Landing Site e **Morph**; 1 (+ mísseis, Morph): Temple Lobby, Artifact
  Temple, Crash Site, Root Cave, Tunnel B, Magmoor East, **Bombas**, Wave, mísseis da Crash Site e do Tunnel B; 2 (+ Bombas,
  Wave): Gully, Alcove, Space Jump; 3 (+ Space Jump): nenhuma sala, Ice e o míssil da Root Cave; 4 (+ gelo): Overgrown, Tunnel
  C, Chozo East, Frigate Access, Vent C, Gravity, míssil da Overgrown; 5 (+ Gravity): as 21 de D e E, os 2 E-tanks, mísseis
  da Biohazard, GTC e LGT, Plasma, **X-Ray** (no chão aberto até a 09e); 6 (+ plasma): Arbor Chamber e o míssil dela. Igual à
  tabela da decisão 3 do épico, menos a Power Bomb (09e) e o X-Ray, que cai da rodada 6 para a 5 até as paredes existirem.
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1 `ad0ef09f8a7e41b88d596947701cf844b069eec3` nas
  duas (logs iguais). Espaço: `$8F` livre a partir de `$8F:F905` (era `$8F:F8FD`: +8 bytes; 2 PLMs de item e as listas de
  PLM novas da Chozo West e do Artifact Temple, menos o PLM cinza da T3); nível da Tallon Canyon 977 → 984 bytes, alocador
  de nível 24126 bytes, livres 500162 a partir de `$E0:DE3E` (nenhum nível cruza banco); `$84`, `$83`, `$A1`, `$B4`, fixo:
  iguais.
- `python3 -I tests/run_tests.py` → **47/47** (os 46 + `tallon_morph_e_bombas`).
- Experimentos no emulador (cópia da ROM em `scratchpad/s09d/`, `exp_bomb.py`, `exp_mb.py`, `bts_*.txt`): bomba ao lado do
  bloco o quebra (nível na WRAM `$F058` → `$00FF`); feixe não; **BTS 4 não volta** (600 quadros depois, ar); **BTS 0 volta**
  depois de ~380 quadros (PLM `$D0B8`, lista `$84:CC3C` com espera `$0180`) e volta desenhado como `$058`; em bola, ↑ sob o teto
  do túnel não desfaz a bola (pose `$1D`); na câmara, ↑ agacha (`$27`) e ↑ de novo fica de pé (`$01`); a primeira bomba
  levanta a bola (pose `$31`: o bomb jump existe no jogo, o modelo não o usa).
- Mutações do validador (na memória, `scratchpad/s09d/mut_validate.py`, saída em `mut_validate.out`; sem mutação e depois de
  desfazer: 0 problemas), todas acusadas: (a) sem o lugar do Morph → 43 (Gully, Alcove e tudo depois na fase 1); (b) blocos
  de bomba viram ar → 3 ("tem trava ['bombs', 'morph'] mas é alcançável sem bombs" de R0, L1, L0); (c) bloco de bomba numa
  bolsa na rocha → "a bola não chega a nenhum bloco vizinho"; (d) câmara da T3 sem 3 linhas (rocha na linha 4) → 51 (a T3 não
  volta a nenhuma porta nem com Morph/Bombas); (e) Bombas na Gully → 45 (fases); (f) T3 cinza de novo → "com tampa 'grey' …:
  no Tallon só portas vermelhas e de feixe"; (g) bola subindo degrau de 1 → `self_test` "bola num degrau de 1"; (h) flood fill
  aceitando sem Morph → `self_test` "flood fill sem Morph Ball: esperado erro"; (i) bloco com BTS 0 → "esperado $058/$04"; (j)
  túnel de bola no chão da Chozo West caindo num vão de 1 linha → "3 lugares sem volta … (com Morph Ball e Bombas)" (a pé
  nada muda); (k) justiça pela fase 0 declarada (regra antiga) → Biohazard (turret tira 40); (l) regra da borda só para
  Space Jump/Gravity → 6 (T3 exigida a pé); (m) Gully sem saída → `check_tallon_return` "rodada 2 … de tallon_gully não há volta
  à nave"; (n) câmara da Landing Site fechada → `check_tallon_return` "a nave fica fora de alcance" (rodadas 2–6).
- Imagens olhadas (`specs/img/09d-*.png`): o Morph na plataforma do elevador e a mensagem MORPHING BALL; as Bombas entre os
  totens do Artifact Temple e a mensagem BOMB; os 2 blocos de bomba (quadrado de pedra roxa, o desenho `$058` do SM, sem lixo;
  zoom em `09d-blocos-de-bomba-zoom.png`), a bola encostada, a bomba, o primeiro bloco quebrado, a bola no túnel sob o teto
  (`09d-bola-no-tunel-zoom.png`), a Samus de pé na câmara, a Gully; sem Morph (só Space Jump) a Samus para nos blocos.

Mudanças de expectativa dos testes existentes:

- `tallon_rota_mvp`: volta com **65** ciclos em vez de 56 (`TALLON_CYCLES_BACK`; a Landing Site chega no ciclo 59, a Waterfall no 78).
- `tallon_rota_mvp`: no fim `$09A2 = $09A4 = $0004` (Morph) e o bit `$B1`, em vez de `$09A2–$09A8 = 0`.
- `tallon_mapa_salvo`: a mesma volta de 65 ciclos (usa os mesmos números).
- `tallon_mapa_salvo`: antes de salvar na nave, UP e a Samus reposta no centro da nave (a volta mais longa termina com ela correndo, como no `tallon_missil_salvo`).
- `tallon_mapa_salvo`: depois do continue, `$09A4 = $0004` e o bit do Morph (novo: o Morph sobrevive ao save).
- `tallon_rota_bc`: trecho `bc_sobe` com **28** ciclos em vez de 21 (a Tallon Canyon chega no ciclo 27).
- `tallon_rota_bc`: no fim `$09A2 = $09A4 = $0004` e o bit `$B1`, em vez de `$09A2–$09A8 = 0`.
- `tallon_gully_alcove`: no fim, em vez de 4 pulos contra a tampa cinza (fica na Canyon), andando para oeste a Samus para nos blocos de bomba (x `$375`, na Canyon) e o pulo guiado para a esquerda a leva de volta à Gully.

Desvios e detalhes:

- **Metatile `$058`, não `$05F`**: `$05F` era o único CRE que a vanilla põe em bloco F, mas o código do próprio jogo redesenha o
  bloco de bomba que volta como `$058` (`PlmSetup_RespawningBombBlock2`, visto no emulador); `$058` é o bloco de bomba do SM.
- **A T3 vira passagem aberta**, não "porta azul": porta de teto/chão sem trava não tem tampa neste projeto (`DoorLink.has_cap`),
  como as outras portas de teto do Tallon.
- **Cada item de geometria a pé tem de ser necessário sozinho** (regra nova, não prevista): a mutação (b) mostrou que, sem os
  blocos, o teto do túnel ainda pedia a Morph e o validador não dizia nada; agora, da entrada que não está atrás da trava, com
  só a Morph (ou só as Bombas) a T3 continua fora de alcance.
- **Volta à nave por rodada** (`check_tallon_return`) entrou já aqui (pedido: "se for barato"): as voltas do passeio da fase 0
  (`tallon_rounds`) com as caminhadas de sala memorizadas; de todo (sala, entrada) alcançado, com os itens da rodada, chega-se
  à Landing Site, e nela à nave de toda entrada. Faltam da prova da 09f: `FIRST_ROUND`/`Item.round` no lugar das fases e o
  `stuck` de cada sala com o equipamento de cada rodada (aqui: a pé e com Morph + Bombas, de toda entrada).
- **O passeio por fases é cacheado por `check()`** (`tallon_tiers_built`): validate de ~10,7 s para ~6,3 s.
- **Rotas cegas**: indo para oeste o andador pula por cima do Morph; pega-o na volta (a caixa de mensagem fecha com o A do pulo,
  ~5–7 ciclos). Não precisou do lugar de reserva (alto do poço).
- **Teste por teleporte e o deslocamento do BG1**: `door_teleport` encadeado de salas com a câmera mexida por RAM deixou o
  deslocamento vertical do BG1 (`$091F`) fora de uma tela inteira (`$0281`); os PLMs que redesenham o bloco quebrado
  escreviam nas linhas erradas e o bloco continuava desenhado (colisão certa: ar). Entrando a pé pela porta da Canyon Cavern os
  valores são `$FC00/$0200` (medido); o `tallon_morph_e_bombas` os põe depois do teleporte (anotado no teste). No jogo normal
  não acontece (a transição de porta alinha a câmera).
- Atalhos do `tallon_morph_e_bombas` (anotados no teste): salas por teleporte de porta, a Samus posta por RAM perto de cada item
  e na ponta oeste da plataforma da Canyon; o resto (pegar os itens, virar bola, bombas, rolar, desfazer, subir) é jogado.
- Justiça dos inimigos pela chegada (Power Beam, mísseis, Morph): as mesmas 6 salas com inimigos de antes (Canyon Cavern,
  Tallon Canyon, Tunnel A, Root Tunnel, Root Cave, Tunnel B).
