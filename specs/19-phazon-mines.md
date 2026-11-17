# 19 — Phazon Mines (épico)

Estado: **verificada** (10/11/2026, **fechado na 19m**: as 13 filhas 19a–19m verificadas; critérios conferidos em "Verificação do épico", no fim; sha1 `f5b0f58b…0dac`; A 34/34, B 64/64, C 22/22, D 18/18; **as 42 salas, os 13 itens e os 2 chefes na ROM; 88 itens, 88% na tela do fim**). Decisões do usuário 1, 3, 4 e 6 respondidas; 2, 5, 7 e 8 = padrão aceito, **confirmado em 09/11/2026**; ver "Respostas" e "Confirmação" no fim. Rascunho de 05/11/2026 feito só com leitura.
Esforço estimado: 25–30 dias no total, em 13 filhas de 0,5–3 dias (Phendrana, 56 salas e ~302 telas, levou 14 filhas; a Mines tem
**42 salas e ~205 telas**, 2 chefes, 2 caras novas e o quarto grupo de testes). MVP (19a–19g: o nível de cima jogável vindo do
Tallon, com os inimigos): 11,5–13,5 dias. Com a opção (b) da decisão 3 (gancho de verdade): +4–6 dias; (c) da decisão 4 (Golden
Torizo de verdade): +2–3 dias; (b) da decisão 6 (phazon que machuca): +1,5–2 dias; (b) da decisão 5 (uma Elite Pirate): +1 dia.

## Contexto

Tallon (44 salas), Chozo (64), Magmoor (29) e Phendrana (56) estão prontos e andados juntos: **75 itens em 7 rodadas, 75%** na tela
do fim, a cadeia completa no emulador em 4 partes ligadas por estado salvo (18n), 6 chefes (os 4 da Chozo, o Sheegoth e o Thardus).
A próxima etapa é a **Phazon Mines**, o mundo dos piratas debaixo do Tallon, que no Prime se liga a dois mundos por dois elevadores.
Hoje os dois lados são **de enfeite**: `tallon_transport_mines_east` (Tallon P43, região E, rodada 5, onde está a Power Bomb do jogo:
`tools/tallon/items.py:114`) e `magmoor_transport_mines_west` (Magmoor P26, região C, rodada 4: `tools/magmoor/rooms.py:58`
`DECORATIVE_ELEVATORS`, linha 109).

Este épico segue o molde do 18 (e do 17 e do 12): levanta os fatos (Prime e ROM), decide o que é técnico, deixa ao usuário o que é de
gosto ou de escopo, e divide o trabalho em filhas — toolchain e dados primeiro (ROM igual), regiões depois, as rodadas e a cadeia no
fim. O lugar da Mines no SM já foi planejado no épico 18 (decisão 2, "padrão aceito, a confirmar"): **área 5** (a da Tourian),
`tools/areas.py:178` `MINES_AREA = 5`, com a lista do mapa salvo no `$81` livre (`tools/frigate/mapsave.py:13`).

## Estado atual (verificado)

Na pasta real, antes desta etapa (leitura só): `python3 -I tools/validate.py` → "221 salas, 460 portas, 0 problemas" (20 s); linha
"rodadas (specs/12m, 17j, 18n): Tallon + Chozo + Magmoor + Phendrana andados juntos, 75 itens em 7 rodadas … elevadores a partir da
rodada: chozo_west 0, chozo_east 4, chozo_south 5, magmoor_north 1, magmoor_east 1, phendrana_north 3, phendrana_south 3; porcentagem
do fim ($8B:E627) com todos: 75% (energia 1299, mísseis 235, super mísseis 5, power bombs 25)". Nenhum teste rodado, nenhum build (só
leitura de `build/metroid_prime_snes.sfc` e `build/manifest.json`, de 04/11 02:50). Roteiros desta pesquisa no scratchpad da sessão
(`…/scratchpad/s19/scripts/`), os da 18 com o nome do mundo trocado: `mines_objs.py` (itens, funções especiais, inimigos por camada,
destino dos elevadores), `mines_named.py` (objetos de trava por nome, com a vulnerabilidade dos `DamageableTrigger`), `mines_envfx.py`
(o `AreaAttributes`), `mines_allpick.py` (todos os `Pickup`), e dois novos: `mines_kw.py` (nomes com phazon, dano, raio-X, térmico,
cordite) e `mines_rocks.py` (a vulnerabilidade das `Platform` que quebram, lida dos bytes: o retro-data-structures 0.44.1 falha
nelas); `summary.py`/`table.py`/`regions.py` (tamanho pela regra do Tallon, travas por doca, regiões), `tileset_survey.py`, `free.py`,
`orphan_runs.py`. Saídas: `s19/mines_locks.json` (o `tools/dump_prime_locks.py` rodado para a Mines: "42 salas"), `s19/mines_objs.out`,
`s19/compact.out`, `s19/named.out`, `s19/kw.out`, `s19/rocks.out`, `s19/envfx.out`, `s19/allpick.out`, `s19/summary.out`,
`s19/table.md`, `s19/regions.out`, `s19/tilesets.out`, `s19/free.out`, `s19/orphans.out`, `s19/validate.out`.

### Phazon Mines no Prime (dados)

Fonte: `research/prime_worlds.json` (MLVL "Phazon Mines") e os objetos de `research/prime_fs` (retro-data-structures 0.44.1, venv
`tools/venv`; mesmos métodos da 17 e da 18: item = 1ª palavra depois do nome + 60 bytes; cor de porta = `DamageVulnerability` do
`Trigger_DoorKey`, ordem power, ice, wave, plasma, bomb, power bomb, missile, boost…, 1 = fere, 2 = rebate, 3 = imune, 0 = dobro).
"Conhecimento" = o que eu sei do jogo e os dados não mostram; marcado *(incerto)* quando não tenho certeza.

- **42 salas** (índices 0–41), **86 docks = 43 ligações**, todas com volta; **2 ciclos**: o anel do nível de cima (Main Quarry →
  Security Access A → Mine Security Station → Security Access B → Elite Research → Research Access → Ore Processing → Waste Disposal →
  Main Quarry) e o grande anel dos níveis de baixo (Elite Control → Maintenance Tunnel → Phazon Processing Center → Processing Center
  Access → Elite Quarters → Elite Quarters Access → Metroid Quarantine B → Quarantine Access B → Fungal Hall B → Phazon Mining Tunnel
  → Fungal Hall A → Fungal Hall Access → Elevator B → Elevator Access B → Metroid Quarantine A → Quarantine Access A → Central Dynamo
  → Dynamo Access → Omega Research → Ventilation Shaft → Elite Control).
- **3 save stations** (P4 Save Station Mines A, P30 B, P34 C), **1 map station** (P23) e **1 missile station** (P38, a recarga de
  mísseis: `SpecialFunction Missile Station`).
- **2 elevadores para outros mundos** (`WorldTeleporter`, destino pelo id de MREA nos bytes): P0 Transport to Tallon Overworld South →
  **Tallon P43** Transport to Phazon Mines East; P25 Transport to Magmoor Caverns South → **Magmoor P26** Transport to Phazon Mines
  West. E **3 elevadores internos** (plataformas que sobem e descem dentro de uma sala, sem `WorldTeleporter`): P14 Elevator A (nível de
  cima ↔ do meio), P37 Elevator B (do meio ↔ de baixo) e o da Elite Quarters (a saída depois do Omega Pirate).
- **Itens** (18 `Pickup` de verdade em 17 lugares — o Phazon Suit tem um em cada camada, no mesmo ponto; os outros ~250 `Pickup - …`
  são recargas soltas por inimigo):

| P# | Sala | Item do Prime (enum) | Existe no SM? |
|---|---|---|---|
| 2 | Main Quarry | Missile Expansion (4) | sim |
| 5 | Security Access A | Missile Expansion (4) | sim |
| 13 | Elite Research | Missile Expansion (4) + artefato (34, Warrior) | míssil sim; artefato não |
| 15 | Elite Control Access | Missile Expansion (4) | sim |
| 19 | Phazon Processing Center | Missile Expansion (4) | sim |
| 31 | Metroid Quarantine B | Missile Expansion (4) | sim |
| 32 | Metroid Quarantine A | Missile Expansion (4) | sim |
| 36 | Fungal Hall B | Missile Expansion (4) | sim |
| 40 | Fungal Hall Access | Missile Expansion (4) | sim |
| 18 | Ventilation Shaft | Energy Tank (24) | sim |
| 22 | Processing Center Access | Energy Tank (24) | sim |
| 27 | Central Dynamo | **Power Bomb** (7, o item principal: `P_Bomb`) | sim (a Power Bomb **já está no Tallon**, Mines East, 09e) |
| 9 | Storage Depot B | **Grapple Beam** (12) | **sim: o Grapple Beam do SM** (PLM `$84:EF17`, lido na ROM base: setup `$EE64`, instruções `$E366`) |
| 12 | Storage Depot A | **Flamethrower** (8, `P_Plasma_Combo`, atrás de porta de plasma) | não |
| 26 | Elite Quarters | **Phazon Suit** (23; o prêmio do Omega Pirate) | não |
| 39 | Phazon Mining Tunnel | artefato (40, Newborn) | não |

  **Correções de premissas**: a Mines **não tem expansão de Power Bomb** (as 4 do Prime estão na Magmoor e em Phendrana, já feitas); o
  **X-Ray** e o **Ice Spreader** não são da Mines (o X-Ray está no Tallon desde a 09e; o Ice Spreader é da Magmoor, "nada" na 17). São
  **9 mísseis, 2 E-tanks, a Power Bomb, o Grapple, o Flamethrower, o Phazon Suit e 2 artefatos**. Nenhum objeto com "Cordite" no nome
  (o Super Missile não aparece como trava nos dados; nos 12 primeiros valores da vulnerabilidade nenhum gatilho é só de míssil; o
  Super do Prime fica no grupo dos combos, que os roteiros não leem *(incerto: a 19c lê o vetor inteiro)*).
- **Calor, frio, água, neve: nenhum.** `area_damage` 0 nas 42 salas (`SpecialFunction` 18), nenhum objeto `Water`, `AreaAttributes` com
  `fx_type_` 0 nas 15 que têm (céu à vista só em 3: Main Quarry, Phazon Processing Center, Fungal Hall A).
- **Phazon** (`s19/kw.out`): o dano do phazon azul no chão **não aparece nos objetos** — no Prime ele vem do material da colisão da sala
  (conhecimento *(incerto)*; os roteiros não leem a colisão). Nos objetos há só: `Trigger_Phazon Radioactivity` (Security Access A),
  `Trigger - Area Gas Damage` (Ventilation Shaft: o gás dos Puffers), 34 `Trigger Barrier Damage` (Central Dynamo: as barreiras
  elétricas do labirinto de Morph Ball) e as poças de phazon da luta do Omega Pirate (Elite Quarters, camadas 1 e 5).
- **Travas nas portas** (`s19/mines_locks.json` + cor lida das vulnerabilidades): **86 docas key, todas coloridas** — **48 de gelo**
  (`2 1 2 2`), **26 de plasma** (`2 2 2 1`), **12 de onda** (`2 2 1 2`); nenhuma porta de qualquer feixe, de charge ou de míssil.
  Ligações: 23 gelo–gelo, 12 plasma–plasma, 6 onda–onda e 2 plasma–gelo (Fungal Hall A: gelo por dentro, plasma do outro lado). **4
  docas de Morph** (`Door_Area Morphball`: as 2 portas da Waste Disposal, um túnel). **Travas de evento** (`Actor Door Lock` fora da
  camada 0, as portas que trancam numa luta): Security Access A (2, camada 3: piratas), Elite Research (1, camada 1: o Phazon Elite),
  Elite Control (1, camada 1: a primeira Elite Pirate), Omega Research (3, camada 2: Elite Pirate), Central Dynamo (2, camada 1: os
  Drones); e as 2 da Elite Quarters (camada 0: a arena do Omega Pirate).
- **Travas dentro das salas** (dados; o uso no caminho é conhecimento):
  - **o que só a Power Bomb quebra** (rocha "Bendezium", lido dos bytes): `DamageableTrigger` imunes a tudo menos a PB (`3 3 3 3 3 1` ou
    `7 7 7 7 7 0`) na Security Access A (a parede que liga a Main Quarry à Mine Security Station), Mine Security Station, Phazon
    Processing Center e Phazon Mining Tunnel; `Platform - destructible rock` só de PB (`2 2 2 2 2 1`, `s19/rocks.out`) na
    **Maintenance Tunnel**, Omega Research e Central Dynamo; uma das duas grades da Ventilation Shaft; e os "Powerbomb Wall" das
    leituras (scan) da Metroid Quarantine A (2) e da Omega Research;
  - trilhos de Spider (`spider`): Main Quarry (24), Ore Processing (90), Research Access (22), Elevator Access A (24), **Phazon
    Processing Center (132)**, Metroid Quarantine B (24), Metroid Quarantine A (22);
  - `GrapplePoint`: Main Quarry (1), Ore Processing (2), **Transport Access (2: `SpecialFunction - check for grapple beam`, o caminho
    do elevador da Magmoor)**, Metroid Quarantine B (1);
  - meio-tubo de Boost: Ventilation Shaft (3);
  - o que bomba quebra/liga: o pilar da Ore Processing (`Hit Detection`, só bomba e PB), o canhão da Elite Research (`Release Ball`),
    a Quarantine Access A, o labirinto da Central Dynamo (`DamageableTrigger Bomb`), 17 blocos da Phazon Mining Tunnel;
  - X-Ray: Metroid Quarantine A (`check for Xray visor`: plataformas invisíveis) e Fungal Hall B (`Actor False XRay Floor`);
  - Thermal: o painel da Main Quarry (`Thermal Hit Trigger`, só o Wave fere: `2 2 1 2`) e a parede fraca da Elite Research (scan);
  - caixas que explodem e canos (`Platform … Crate`, `Destructible Pipe`, 28 canos na Mine Security Station): qualquer tiro, enfeite.
- **Inimigos** (camada 0, a regra de 07i/12h/17g/18g; nomes dos tipos dos dados): Main Quarry SpacePirate 4; Elevator Access A
  AtomicBeta 4; Elite Control Access SpacePirate 2; Ventilation Shaft Puffer 8; **Metroid Quarantine A MetroidAlpha 5**; Quarantine
  Access B AtomicAlpha 3 (invisíveis); Elevator Access B Burrower 3; **Fungal Hall B MetroidAlpha 6** + Ripper 1; Fungal Hall Access
  AtomicAlpha 3 + SpacePirate 1; **Fungal Hall A MetroidBeta 4** (os Hunter Metroids) + Ripper 1. Nas outras camadas (passes e eventos):
  Space Pirates em quase toda sala grande (até 15 na Mine Security Station, os "Shadow Pirates" invisíveis), MetroidAlpha/Beta dos
  tanques, Drones (Central Dynamo, Security Access A), Puffers, **Elite Pirates** (Elite Control camada 1, Omega Research camada 2,
  Dynamo Access camada 3), os 8 piratas e 9 nódulos de cura da luta do Omega.
- **Chefes**: **Omega Pirate** (Elite Quarters P26, camada 5 com `DamageableTrigger - Kills Omega Pirate` na 4; guarda o Phazon Suit;
  as 2 portas trancam: `Actor Door Lock` da camada 0) e **Phazon Elite** (`ElitePirate` da camada 1 da Elite Research P13, que sai do
  tanque (`Platform_holding Tank`); guarda o artefato Warrior; a porta para a Security Access B tranca) — o nome "Phazon Elite" é
  conhecimento *(incerto: nos dados é um `ElitePirate` comum)*. As outras 3 Elite Pirates são mini-chefes de camada de evento.

Tamanho SM pela regra do Tallon (`tools/tallon/rooms.py:57` `screens`, 30 m por tela, no máximo 6×4; `s19/table.md`). Travas pelo lado
da sala da linha (o outro lado, na linha da outra sala); "Inimigos" = camada 0:

| P# | Sala | Telas | Liga a (trava deste lado) | Região | Travas e coisas na sala | Inimigos |
|---|---|---|---|---|---|---|
| 0 | Transport to Tallon Overworld South | 1×2 | 1 (onda) | A | elevador (Tallon P43) | |
| 1 | Quarry Access | 2×2 | 2 (onda), 0 (onda) | A | | |
| 2 | Main Quarry | 5×3 | 3 (gelo), 1 (onda), 4 (onda), 5 (gelo) | A | gancho 1; spider 24; painel de Wave/Thermal | SpacePirate 4 |
| 3 | Waste Disposal | 1×1 | 2 (gelo), 6 (gelo) | A | túnel de Morph (4 docas) | |
| 4 | Save Station Mines A | 1×1 | 2 (onda) | A | save | |
| 5 | Security Access A | 3×1 | 2 (gelo), 7 (gelo) | A | parede de PB | |
| 6 | Ore Processing | 3×2 | 8 (gelo), 9 (gelo), 3 (gelo), 10 (gelo) | A | gancho 2; spider 90; bomb slot (o pilar) | |
| 7 | Mine Security Station | 3×1 | 5 (gelo), 11 (onda), 12 (plasma) | A | parede de PB | |
| 8 | Research Access | 2×2 | 6 (gelo), 13 (gelo) | A | spider 22 | |
| 9 | Storage Depot B | 1×1 | 6 (gelo) | A | (o Grapple) | |
| 10 | Elevator Access A | 1×2 | 6 (gelo), 14 (gelo) | A | spider 24 | AtomicBeta 4 |
| 11 | Security Access B | 3×1 | 13 (gelo), 7 (onda) | A | | |
| 12 | Storage Depot A | 1×1 | 7 (plasma) | A | (o Flamethrower) | |
| 13 | Elite Research | 4×2 | 8 (gelo), 11 (gelo) | A | bomb slot (canhão); **Phazon Elite** (camada 1) | |
| 14 | Elevator A | 1×3 | 10 (gelo), 15 (gelo) | B | elevador interno | |
| 15 | Elite Control Access | 2×1 | 14 (gelo), 16 (onda) | B | | SpacePirate 2 |
| 16 | Elite Control | 4×2 | 17 (gelo), 15 (onda), 18 (gelo) | B | (Elite Pirate, camada 1) | |
| 17 | Maintenance Tunnel | 3×1 | 16 (gelo), 19 (gelo) | B | **rocha de PB** | |
| 18 | Ventilation Shaft | 2×1 | 20 (gelo), 16 (gelo) | B | meio-tubo 3; grade de PB; gás | Puffer 8 |
| 19 | Phazon Processing Center | 4×3 | 21 (gelo), 17 (gelo), 22 (plasma) | C | spider 132; parede de PB | |
| 20 | Omega Research | 4×3 | 23 (gelo), 18 (gelo), 24 (gelo) | B | rocha de PB; (Elite Pirate, camada 2) | |
| 21 | Transport Access | 2×1 | 19 (gelo), 25 (gelo) | C | gancho 2 | |
| 22 | Processing Center Access | 2×1 | 19 (plasma), 26 (plasma) | C | | |
| 23 | Map Station Mines | 1×1 | 20 (gelo) | B | map station | |
| 24 | Dynamo Access | 2×1 | 27 (gelo), 20 (gelo) | B | | |
| 25 | Transport to Magmoor Caverns South | 1×3 | 21 (gelo) | C | elevador (Magmoor P26) | |
| 26 | Elite Quarters | 5×2 | 28 (plasma), 22 (plasma) | C | **Omega Pirate** (camada 5); elevador interno | |
| 27 | Central Dynamo | 5×2 | 24 (gelo), 29 (gelo), 30 (gelo) | B | rocha de PB; labirinto de Morph | |
| 28 | Elite Quarters Access | 2×1 | 31 (plasma), 26 (plasma) | C | | |
| 29 | Quarantine Access A | 2×1 | 27 (gelo), 32 (onda) | B | bloco de bomba | |
| 30 | Save Station Mines B | 1×1 | 27 (gelo) | B | save | |
| 31 | Metroid Quarantine B | 6×3 | 33 (plasma), 28 (plasma), 34 (plasma) | D | gancho 1; spider 24 | |
| 32 | Metroid Quarantine A | 6×2 | 29 (onda), 35 (gelo) | B | spider 22; parede de PB (2); X-Ray | MetroidAlpha 5 |
| 33 | Quarantine Access B | 2×1 | 31 (plasma), 36 (plasma) | D | | AtomicAlpha 3 |
| 34 | Save Station Mines C | 1×1 | 31 (plasma) | D | save | |
| 35 | Elevator Access B | 2×2 | 32 (gelo), 37 (plasma) | D | | Burrower 3 |
| 36 | Fungal Hall B | 6×2 | 38 (plasma), 33 (plasma), 39 (plasma) | D | X-Ray (chão falso) | MetroidAlpha 6, Ripper 1 |
| 37 | Elevator B | 1×3 | 35 (plasma), 40 (plasma) | D | elevador interno | |
| 38 | Missile Station Mines | 2×1 | 36 (plasma) | D | missile station | |
| 39 | Phazon Mining Tunnel | 2×1 | 36 (plasma), 41 (plasma) | D | parede de PB; blocos de bomba (17) | |
| 40 | Fungal Hall Access | 2×3 | 41 (plasma), 37 (plasma) | D | | AtomicAlpha 3, SpacePirate 1 |
| 41 | Fungal Hall A | 6×2 | 39 (gelo), 40 (gelo) | D | | MetroidBeta 4, Ripper 1 |

**Total ~205 telas** (Tallon 251, Chozo 202, Magmoor 156, Phendrana 302).

### Regiões (pelo grafo e pelos três níveis da mina; `s19/scripts/regions.py`)

- **A — Nível de cima: a pedreira e a segurança** (14 salas, ~54 telas): 0, 1, 2 Main Quarry, 3, 4 Save A, 5, 6 Ore Processing, 7 Mine
  Security Station, 8, 9 Storage Depot B, 10, 11, 12 Storage Depot A, 13 Elite Research (Phazon Elite). Itens: os mísseis da Main
  Quarry, da Security Access A e da Elite Research, o Grapple; o lugar do Flamethrower e do artefato.
- **B — Nível do meio: Elite Control, Omega Research, Central Dynamo** (12 salas, ~58 telas): 14 Elevator A, 15, 16 Elite Control, 17
  Maintenance Tunnel, 18 Ventilation Shaft, 20 Omega Research, 23 Map Station, 24, 27 Central Dynamo, 29, 30 Save B, 32 Metroid
  Quarantine A. Itens: o míssil da Elite Control Access, o E-tank da Ventilation Shaft, o lugar da Power Bomb, o míssil da MQ A.
- **C — Oeste: o elevador da Magmoor, o processamento e o Omega Pirate** (6 salas, ~31 telas): 19 Phazon Processing Center, 21
  Transport Access, 22 Processing Center Access, 25 Transport to Magmoor South, 26 Elite Quarters (Omega), 28. Itens: o míssil do PPC,
  o E-tank da Processing Center Access; o lugar do Phazon Suit.
- **D — Nível de baixo: os fungos e a quarentena B** (10 salas, ~62 telas): 31 Metroid Quarantine B, 33, 34 Save C, 35, 36 Fungal Hall
  B, 37 Elevator B, 38 Missile Station, 39 Phazon Mining Tunnel, 40 Fungal Hall Access, 41 Fungal Hall A. Itens: os mísseis da MQ B, da
  Fungal Hall B e da Fungal Hall Access; o lugar do artefato.

Ligações entre regiões: A–B (10–14, gelo), B–C (17–19, gelo + a rocha de PB), C–D (28–31, plasma), B–D (32–35, gelo).

### Como a Mines encaixa no nosso mundo (verificado no código)

- **Pares de elevador**: `tools/areas.py:283` `ELEVATORS` tem 7 pares; os dois lados de enfeite são `tallon_transport_mines_east`
  (Tallon P43, **rodada 5**: `tools/tallon/rooms.py:329`, a lista da rodada 5 de `FIRST_ROUND`) e `magmoor_transport_mines_west`
  (Magmoor P26, **rodada 4**: atrás das portas de gelo da Workstation Tunnel, `tools/magmoor/rooms.py:282`). A Mines acrescenta 2 pares:
  Tallon P43 ↔ Mines P0 e Magmoor P26 ↔ Mines P25 (9 no total; nenhum lado de enfeite sobra). Quem fica em cima em cada par é decisão
  da 19e pela geometria (a Mines é funda; a 18e fez os elevadores descerem em Phendrana) *(incerto o sentido do lado da Magmoor)*.
- **A Power Bomb do jogo está na sala do Tallon P43** (`tools/tallon/items.py:114`, rodada 5, desde a 09e: "a Power Bomb vem da
  Mines"): com o elevador de verdade ela fica na sala, no chão ao lado da plataforma (o jeito da Morph na Chozo West, 12e) — a rodada
  dela não muda.
- **A ROM de teste da 17d/17i está pendurada na Magmoor P26** (`tools/magmoor/testrooms.py:28` `HOST = "magmoor_transport_mines_west"`,
  `HOST_DOOR = ("R", 1)`): a porta R1 da sala só existe na ROM de teste; a 19e confere que o elevador de verdade não precisa dela, ou
  muda o `HOST` (só as ROMs de teste mudam).
- **Itens que o jogo já tem** (épicos 09–18): Morph, Bombas, **Power Bomb** (Tallon P43), Ice, Wave, Plasma, Gravity, X-Ray, Space Jump
  (Tallon); Charge e Varia (Chozo); **Super Missile** (Phendrana). O **Grapple Beam não está em nenhuma área** (só na fragata, que
  começa com tudo: `tools/build.py:545` `START_ITEMS`, e a Samus o perde na chegada ao Tallon, 07e).
- **Regra dos itens** (épicos 12, 17 e 18, aceita três vezes): item do Prime que já está no jogo → **míssil** no lugar (Morph, Bombas e
  Ice da Chozo; Plasma da Magmoor; Wave e Gravity de Phendrana); item que não existe no SM → **nada** (Wavebuster, Ice Spreader, Boost,
  Spider, Thermal, artefatos); Missile/E-tank/expansão de PB → o mesmo do SM; **item que existe no SM e ainda não está no jogo → o item
  do SM** (o Super Missile de Phendrana, 18l). Aplicada à Mines: **Power Bomb → míssil**; **Grapple Beam → o Grapple do SM**;
  Flamethrower, Phazon Suit e os 2 artefatos → nada.
- **Quando a Samus tem cada coisa** (rodada em que é pega → usada a partir da seguinte): mísseis 0, Morph 0, Bombas 1, Wave 1, Charge 1,
  Varia 2, Space Jump 2, Ice 3, Super Missile 3, Gravity 4, Power Bomb 5, Plasma 5, X-Ray 6 (nunca usado: nenhuma trava pede). A Mines
  se alcança **pela Magmoor na rodada 4** (P26) e **pelo Tallon na rodada 5** (P43). Pelas travas: as portas de gelo e de onda não
  atrasam nada (gelo 4+); **as rochas, paredes e a grade de PB e as 26 portas de plasma seguram metade da mina até a rodada 6**.
- **As rodadas declaradas das outras quatro áreas não mudam**, se três regras forem seguidas: (1) a Mines não dá atalho entre o Tallon e
  a Magmoor antes da rodada 6 — o caminho P25 → P0 passa pela rocha de PB da **Maintenance Tunnel** (P17) ou pela porta de plasma da
  **Processing Center Access** (P22): os dois só abrem na rodada 6, e os dois lados (rodadas 4 e 5) já são alcançados antes; (2) o
  **míssil no lugar da Power Bomb** (Central Dynamo) não é Power Bomb (a PB do jogo continua a do Tallon, rodada 5); (3) o **Grapple**
  não abre nada em lugar nenhum (nenhum bloco de gancho no jogo, e nenhum inimigo nosso agarrável mudando o alcance: a 19c confere por
  varredura, como `check_no_super_locks` fez para o Super) — ele só soma à porcentagem e ao HUD.
- **Rodadas previstas dos 13 itens** (decisão 3a; a filha de cada região confirma; previsão pelas travas acima): rodada 4 — o míssil do
  PPC *(se o trilho de Spider não passar pela parede de PB: senão rodada 6)*; rodada 5 — Main Quarry, Elite Research, Elite Control
  Access, o míssil no lugar da Power Bomb (Central Dynamo, labirinto de Morph = Bombas), o Grapple (5); rodada 6 — Security Access A
  (parede de PB *(incerto)*), Ventilation Shaft (grade de PB *(incerto)*), Metroid Quarantine A, Processing Center Access (plasma),
  Metroid Quarantine B, Fungal Hall B, Fungal Hall Access (7). **Nenhuma rodada nova** (as 7 de hoje bastam; a mina inteira cabe nas
  rodadas 4–6) e nenhuma rodada só da Mines (a guarda da 17f/18e vale).
- Bits livres: itens a partir de `$EB` (Tallon `$A0–$B3`, Chozo `$B4–$D2`, Magmoor `$D3–$D9`, Phendrana `$DA–$EA`,
  `tools/phendrana/items.py:22`; vetor `$7ED870`, 512 bits): Mines `$EB–$F7` (13). Portas vermelhas: nenhuma (a Mines não tem escudo de
  míssil; o `$C6` continua livre). Bits de chefe da área 5: `$08` e `$10` para as arenas (o Torizo liga o `$04` da área atual sozinho,
  18k); os bits vanilla da Tourian lidos da ROM base na 19b, como a 18b fez para a área 4.
- **Porcentagem do fim** com a Mines (decisão 3a, a fórmula de `$8B:E627`, 1 por item; a 19m confere): **88%** (energia 1499, mísseis 285,
  super mísseis 5, power bombs 25; o Grapple conta 1).

### A área 5 do SM (o plano do épico 18)

`tools/areas.py:174–179`: Phendrana na 4, **Mines na 5**, Impact Crater dentro da 0. Conferido agora:

- **Mapa salvo**: a lista vanilla da área 5 cabe só **21 bytes** (`tools/frigate/mapsave.py:32` `LIST_ROOM`); a Mines precisa de ~40
  (estimativa pelas telas: Chozo 202 → 41, Tallon 251 → 47, Phendrana 302 → 57). A regra já escrita em `mapsave.py:25–27`: a lista vai
  para o **`$81` livre** (`$81:EF1A–FEFF`, **4070 bytes, todos `FF` na ROM construída**, `s19/free.out`) e o ponteiro `$81:82D6 + 2·5`
  aponta para ela. SRAM do mapa: **805 livres de 1280** (linha "phendrana (specs/18b)" do validador); a Mines ~40.
- **Código próprio da área 5** (C `vendor/sm/src`, busca por `area_index`): só `SetAreaDependentEprojPropertiesEx` (`sm_86.c:1165`), que
  muda as propriedades **da bola de fogo do Ridley** nas áreas 2 e 5 (o único chamador: `sm_86.c:1217, 1221`) — nada para nós. Sem
  rolagem extra do mapa de pausa (só a área 4 tem, `sm_82.c:1811`). As tabelas indexadas pela área que a 19b confere, como a 18b: o
  mapa de pausa (`kPauseMenuMapData`, rótulo `kPauseAreaLabelTilemap`, ícones de save/elevador/map station `kMapIconDataPointers`), a
  lista de FX de paleta e a de tiles animados da área (`sm_89.c:99, 107`: as da Tourian), o byte de chefe da área 5 e o ícone de chefe
  da Tourian no mapa (a Chozo tirou o dela na 12e). **A Tourian vanilla não tem map station**: a 19b confere que a máquina e o
  `map_station_byte_array[5]` (`sm_80.c:235, 247`) funcionam na área 5 *(incerto: não medido)*.
- **Estações**: a área 5 tem **18** entradas de load station (`tools/smlib/roomgraph.py:22` `STATION_COUNTS`); a Mines usa 4 (0 = a
  chegada pelo elevador do Tallon, P0, a entrada do Prime; 1–3 = as Save Stations A, B, C; até 8 no save).
- **Tela de continue**: a 5 está no mapa da seleção de arquivo (`kFileSelectMap_AreaIndexes = {0, 3, 5, 1, 4, 2}`, `sm_81.c:34`):
  "PHAZON / MINES" como "PHENDRANA / DRIFTS".

### Visual: tileset, phazon, música

- **Tilesets** (tabela `$8F:E7A7`; uso vanilla por `s19/scripts/tileset_survey.py`, `s19/tilesets.out`): nós usamos 00 e 01 (Tallon e a
  neve), 02 (Tallon), 04 (fragata), 09/0A (Magmoor), 0C (Chozo), 1B (laboratórios de Phendrana), 1C (ruínas de gelo). **Livres**: 06
  (Brinstar verde, 30 estados vanilla, todos órfãos), 07 (Brinstar vermelho, 18), 0B (Maridia de fora, 22), **0D/0E (Tourian: 22 + 3
  estados, todos órfãos; o 0E só na sala da Mother Brain)**, 1A (a sala do Kraid, órfã), 03/05/08 (pouco usados; o 05 numa sala de demo,
  18d). Nenhuma sala vanilla é alcançável (spec 11), e as demos estão desligadas (spec 16): repintar uma entrada livre é seguro, como a
  18d fez com 01, 1B e 1C.
- **Duas caras** (proposta técnica, decisão 7): **base pirata** (metal, canos e telas: Elite Research, Elite Control, Omega Research,
  Central Dynamo, as Quarantines, as salas de elevador e de save) com os gráficos da **Tourian (0D)** e uma paleta escura com o azul do
  phazon numa entrada livre (0E); **mina de rocha e fungos** (Main Quarry, Ore Processing, os túneis, as Fungal Halls, a Phazon Mining
  Tunnel) com os gráficos do **Brinstar (06)** e paleta de rocha cinza e fungo azul numa entrada livre (07 ou 1A). As cores tiradas das
  texturas do Prime (`tools/dump_prime_textures.py`, como o Thardus). As portas de gelo/onda/plasma pintadas em cada cara (10d, 12f,
  17d, 18d, 18i).
- **Phazon**: só cor (o azul que brilha nas paredes e poças), sem FX nem dano (decisão 6). Se o usuário quiser dano: o FX de ácido do SM
  (`$04`, 8 estados vanilla na área 5: a Tourian) pintado de azul, medido numa ROM de teste como a lava (17d).
- **Música**: livres a da Tourian `1E/05`, Brinstar verde `0F/05`, Brinstar vermelho `12/05`, Crateria `09/05` (usadas hoje: fragata
  `30/05`, Tallon a da Landing Site, Chozo `1B/05`, Magmoor `15/05`, Phendrana `1B/06`). Proposta: **Tourian `1E/05`** (baixa e
  metálica, como a da Mines); a 19d escolhe pelas prévias.

### Chefes (Prime → SM, regras do épico 14)

Regras que valem (épico 14, decisões 3, 7, 10–13; 18h, 18k): arena pela rotina comum em **`$84:F500`** (`tools/chozo/bosses.py:134`
`ROUTINE`); o prêmio aparece na hora da morte; chefe morto nunca volta (bit nosso salvo); justiça = vence só com o Power Beam em
**≤ 20 tiros** (somados numa arena) e tira **≤ 40 por toque** com o equipamento da rodada de chegada, ou a regra 13 (mísseis da
capacidade da rodada, ou ≤ 20 tiros carregados) se o Power Beam não fere; cópia de espécie em `$A0` (`SpeciesCopy`, com
`touch`/`shot`/`vulnerability` desde a 18l); porta trancada até a vitória (`Actor Door Lock` do Prime: cinza de cota de mortes, ou a
de tipo 2 do Torizo, 18k).

Espécies do SM lidas na ROM base (cabeçalho `$A0`, nome no `$B4` pelo `+$3E`): os piratas são 18 (`BATTA1/2/3` × 6 cores, `$A0:F353–F793`,
código no `$B2` **sem nenhuma leitura da área**): o andante cinza `$F653` (20 de vida, toque 15: já é o nosso `pirate`,
`tools/frigate/enemies.py:72`) e o **ninja dourado `BATTA2Na` `$F593`** (1800 de vida, toque 100, tiles `$1800`: os piratas-chefe da
Norfair de baixo, que pulam e jogam garras). O Torizo: Bomb `$EEFF` (800/8), Golden `$EF7F` (13 500/160).

| Prime | Onde | Rodada de chegada | Dublê SM proposto | Por quê |
|---|---|---|---|---|
| **Phazon Elite** | Elite Research (P13), camada 1 | 5 (Ice, Wave, Charge, Varia, Space Jump, Gravity, Bombas) | **ninja dourado `$F593` copiado** com vida pela regra (≤ 20 tiros do Power Beam) e toque ≤ 40, cores de phazon das texturas do Prime; a porta para a Security Access B tranca (cota de mortes) até a vitória; prêmio: nada (o artefato) | é um pirata grande que luta como chefe; código sem área; só sprites, cabe em qualquer tileset |
| **Omega Pirate** | Elite Quarters (P26), camada 5 | 6 (+ Power Bomb, Plasma) | **Bomb Torizo `$EEFF` copiado** (o código já corrigido na 18k: as 7 leituras da área = 0), cores de phazon (azul e o cinza da armadura), **imune ao feixe sem carga** (a armadura do Omega: só PB e míssil no Prime) e vida pela regra 13; as 2 portas trancam (tipo 2, o bit `$04` da área 5) até a vitória; prêmio: nada (o Phazon Suit não existe) | o maior humanoide do SM; o trabalho da 18k serve de novo; custa a VRAM inteira de inimigos da sala (`$2000`) e o ponto fixo do Torizo (`TORIZO_SPOT`, `tools/chozo/bosses.py`: o mesmo do Thardus) |
| Elite Pirates (3), Shadow Pirates, Drones, Metroids dos tanques, os piratas e nódulos da luta do Omega | camadas de evento | — | **fora** (regra da camada 0; decisão 5) | como os Flying Pirates da Magmoor e as Elite Pirates de Phendrana |

Alternativas (decisão 4): o Omega também como **ninja dourado** (maior vida; sem repetir o Torizo, mas do tamanho de um pirata comum);
ou o **Golden Torizo de verdade** — hoje o código dos Torizos joga sempre como o Bomb e o validador recusa o `$EF7F` em sala nossa
(`tools/validate.py:4305`, 18k): seria desfazer as 7 leituras por espécie (+2–3 d). Kraid, Draygon e Crocomire ficam fora (corpo no BG2
com tileset e sala próprios, épico 14; as entradas 1B e 1C já são de Phendrana).

**Inimigos comuns da camada 0** (proposta da 19g, as espécies que já existem): SpacePirate → o **pirata andante** `$F653` (fragata,
Tallon); AtomicAlpha/Beta → a cópia justa do ATOMIC de Phendrana (`$A0:F8BF`, vida 100, toque 20, 18g); Puffer → **Mella** (Chozo, 12h);
MetroidAlpha → a cópia justa do Metroid de Phendrana (18l: vida 100, toque comum 20, sem agarrar); MetroidBeta (Hunter Metroid) → a mesma
cópia com mais vida; Ripper → **fora** (imune como no Prime, 18m); Burrower (verme que sai do chão) → o "PIPE" `$A0:E97F` (os insetos que
saem de canos) ou fora *(a 19g mede)*. ≤ 1 por tela, justos em toda rodada (5 tiros, 20 por toque), a regra da deriva e a da câmera
(18g, 18l).

### Espaço por banco (medido agora)

Livres na ROM construída (`s19/free.out`, maior faixa de `$FF` no fim de cada região livre; `$8F` recuperado pela linha do validador:
"usados pelas nossas salas: 6330 … 2514/3796"):

| Banco | Livre hoje | A Mines pede (42 salas, 43 ligações) | Cabe? |
|---|---|---|---|
| `$8F` (cabeçalhos, estados, listas) | **1** na faixa principal; **1282** na faixa das demos (`$8F:8000–8ED3`, 2514 de 3796 usados) | ~2350 (≈ 53 por sala + ~60 por arena) | **não**: precisa de mais faixas órfãs (19a) |
| `$83` (portas, FX) | 15 066 | ~1700 (86 entradas de porta + FX de 42 salas) | sim |
| `$A1` (populações) | **1053** (1286 no total) | ~600–800 (~25 inimigos + 2 arenas) | sim, mas sobram ~300 para a Impact Crater: recuperar `$A1` órfão (19a) |
| `$B4` (enemy sets) | 1718 | ~300 | sim |
| `$84` (PLMs) | 2398 em pedaços | arenas e pintura das portas nas 2 caras (~300) | sim |
| `$A0` (espécies) | 1601 | 3–4 cópias (Phazon Elite, Omega, Hunter Metroid, talvez o Burrower) ≈ 256 | sim |
| nível / fixo | 459 361 / 474 623 | ~15 KB de nível; 2 paletas e tabelas pintadas (~6 KB) | sim |
| `$81` | 4070 (`$81:EF1A–FEFF`) | a lista do mapa da área 5 (~40) | sim |
| SRAM do mapa | 805 de 1280 | ~40 | sim |

**Faixas órfãs do `$8F`** fora do `RECLAIMED_8F` (`tools/build.py:165`; `s19/orphans.out`: 15 723 bytes em 31 faixas), as que nenhum
cabeçalho comparado pelo código usa (`build.py` `ROOM_PTR_COMPARED`; o 18 já as listou para a Mines): `$8F:C215–C8C6` (**1714**, salas
das áreas 3–6, com dados de demo), `$8F:AD5C–B218` (**1213**, Norfair, com demo), `$8F:A6A1–A97A` (730), `$8F:CAAE–CCC7` (538),
`$8F:BEAB–BF9D` (243), `$8F:BA37–BB0E` (216). As quatro maiores somam **4195**: com os 1282 da faixa das demos, **5477 para ~2350** (folga
~3100, que serve também à Impact Crater, ~12 salas ≈ 650). Dado de demo só com as demos desligadas: a regra da 18a
(`check_reclaimed` pede `check_demos_off`).

**Faixas órfãs do `$A1`** (27 363 bytes, 10 faixas, nenhuma usada por sala nossa): a maior `$A1:AD09–CCD3` (**8139**). O build hoje só
aloca populações no fim do banco (`$A1:EBD1–FFFF`); a 19a dá a ele uma faixa recuperada como a do `$8F` (`RECLAIMED_A1`), provada só de
salas órfãs pelo validador.

### Testes: tempo por comando

Hoje a bateria roda em três comandos (`tests/run_tests.py:8477` `TEST_GROUP_B`, `:8482` `TEST_GROUP_C`, `:8485` `CHAIN_GROUP`), medidos
na 18n: **grupo A ~3 min 0 s**, **B ~3 min 20 s**, **C ~5 min 29 s** (329 s: as partes 3 e 4 da cadeia somam 325 s de CPU; `cadeia_completa_parte_4`
216 s), perto do limite de ~6 min de uma execução da ferramenta. A Mines acrescenta ~10–14 testes no emulador (rota/save por região, 2
elevadores, inimigos e entradas, 2 chefes, a map station) e ~2–3 min de cadeia (visitas à mina nas rodadas 4, 5 e 6). **Não cabem no
grupo C.** Plano (a regra já escrita na 18n, `run_tests.py:8481`): um **grupo D** (prefixo `mines_`, `elevador_mines_`, `entradas_de_porta_mines`
e as partes novas da cadeia), criado na 19e (a primeira filha com teste da Mines no emulador); a cadeia (`CHAIN_PARTS`,
`tests/run_tests.py:7758`) em 5–6 partes ligadas por estado salvo, rodadas na ordem A → B → C → D (a parte 4 de hoje muda: as rodadas
4–6 passam a visitar a mina); cada grupo ≤ ~5 min sozinho, medido na 19m.

## Mudança proposta

### Decisões técnicas deste épico (minhas, justificadas acima; o usuário pode vetar)

1. **Uma sala do Prime = uma sala do SM**, as 43 ligações; chaves com prefixo `mines_`; `tools/mines/` no molde de `tools/phendrana/`
   (`rooms.py`, `layouts.py`, `items.py`, `enemies.py`; as arenas em `tools/chozo/bosses.py`, como o Sheegoth e o Thardus).
2. **Sem calor, frio, água ou neve** (fiel: nada disso nos dados); `HEAT_BITS` da área 5 vazio; o phazon pela decisão 6.
3. **Travas do Prime → mecanismos que já existem**: portas de gelo/onda/plasma → portas de feixe (as de plasma de verdade: a Samus entra
   e sai com o Plasma); **rocha, parede e grade de PB** → **bloco de Power Bomb** (o jeito da Magma Pool, da Fiery Shores e da Security
   Cave); túnel de Morph (Waste Disposal) → túnel de Morph; labirinto da Central Dynamo → túnel de Morph com bloco de bomba (as barreiras
   elétricas: enfeite); bomb slot, canhão, blocos de bomba → túnel/bloco de bomba; Spider/Grapple/Boost → borda de Space Jump (como em
   toda área; o Grapple **não** trava, decisão 3a); X-Ray e Thermal → enfeite (o X-Ray é da rodada 6 e nenhuma trava o pede; as
   plataformas invisíveis viram plataformas comuns); canos e caixas → enfeite.
4. **Elevadores de verdade**: Tallon P43 ↔ Mines P0 e Magmoor P26 ↔ Mines P25 (`ELEVATORS` +2; os lados do Tallon e da Magmoor ganham
   `ride=True`, como a 12e/17e/18e fizeram; `DECORATIVE_ELEVATORS` da Magmoor fica vazio). Os **elevadores internos** (Elevator A, B e
   o da Elite Quarters) → poços que a Samus sobe com o Space Jump (rodada 2; a mina é da rodada 4+), sem máquina.
5. **Inimigos da camada 0** (07i/12h/17g/18g), ≤ 1 por tela, justos em toda rodada, as espécies da tabela acima; as camadas de evento
   fora.
6. **Missile Station** (P38): a recarga de mísseis do SM (as estações das salas de recarga vanilla) se a 19l achar o PLM e ele couber na
   cara da mina; senão a sala vazia *(incerto: PLM não lido)*.
7. **Rodadas**: o passeio anda as cinco áreas pelos elevadores (`validate.world_rounds`); critério duro: **as rodadas declaradas de cada
   item e sala do Tallon, da Chozo, da Magmoor e de Phendrana não mudam**.
8. **Espaço**: `$8F` com mais 4 faixas órfãs e `$A1` com a primeira faixa recuperada (19a), antes de qualquer sala.
9. **Testes**: grupo D (19e) e a cadeia em mais partes (19m).

### Filhas (toolchain e dados primeiro, regiões por último)

| # | Spec | Entrega | Esforço | Testes |
|---|---|---|---|---|
| 19a | Espaço no `$8F` e no `$A1` (mais faixas órfãs) | `build.RECLAIMED_8F` ganha `$8F:C215–C8C6`, `AD5C–B218`, `A6A1–A97A`, `CAAE–CCC7` (4195 bytes, só salas órfãs, nenhum cabeçalho comparado); `build.RECLAIMED_A1` novo com `$A1:AD09–CCD3` (8139) e o alocador de populações usando-o; `check_reclaimed` para os dois bancos (dado de demo só com `check_demos_off`); ROM igual | 0,5–1 d | validate: `check_reclaimed` com as faixas novas; mutações no scratchpad (demos religadas → erro; população de sala vanilla alcançável na faixa; faixa sobreposta) |
| 19b | Lugar da Mines na área 5 | `VANILLA_PAUSE[5]` lido dos bytes, `check_vanilla_pause` cobre a 5, `check_mines_slot` (área livre, SRAM, **lista do mapa > 21 → no `$81`**, estações ≤ 18, listas de FX de paleta e de tiles animados da área 5 iguais à ROM base e nenhum bit da Tourian nas nossas salas, bits de chefe vanilla da 5, ícones de save/elevador/map station da área 5, a map station na área 5), `HEAT_BITS` da 5 vazio; a mudança da lista para o `$81` no `mapsave.py` (aplicada quando a área 5 tiver sala, na 19e); ROM igual | 0,5–1 d | validate: linha "mines (specs/19b)"; mutações (área ocupada, lista grande sem o `$81`, FX da Tourian ligado, ícones a mais) |
| 19c | Grafo, mapa e travas do Prime | `tools/mines/rooms.py`: `TABLE` (42, tamanho pela regra), `LINKS` (43), `REGIONS` A–D, `DOCK_LOCKS` (key 86 com a cor, morph 4, evento 11), `KEY_BEAM`, `FEATURES`, `PB_ONLY` (as rochas/paredes/grade de PB, das vulnerabilidades); `research/prime_mines_locks.json` pelo `dump_prime_locks.py` (com o campo novo das `Platform` que só a PB quebra e o vetor inteiro de vulnerabilidade); disposição no 64×32 por busca; `check_mines`; varredura "nenhum bloco de gancho e nenhum inimigo nosso agarrável muda o alcance" (decisão 3a); prévia `--mapa-mines`; nenhuma sala na ROM | 2 d | validate: tabela × Prime, mapa sem sobreposição, portas encostadas, ligação sem volta = erro (mutação), SRAM; prévia olhada |
| 19d | Estilo da mina (2 caras), phazon e portas | `tools/smlib/mines.py` (ou no molde de `ice.py`): base pirata (gráficos do 0D, paleta na entrada livre), rocha e fungos (gráficos do 06, paleta numa entrada livre), o azul do phazon; portas de gelo/onda/plasma (e a de onda vertical, se o mapa pedir) pintadas; música e fundo pelas prévias; ROM de teste `build.py --teste-19d` | 2–2,5 d | validate: `mines.check`, cores/metatiles na ROM, nenhuma sala fora da Mines usa as entradas novas; emulador: `porta_de_plasma_mina` (a tampa abre); prévias |
| 19e | Elevadores de verdade (Tallon ↔ Mines, Magmoor ↔ Mines) e o grupo D | as salas P0 e P25 (becos), os lados P43 do Tallon e P26 da Magmoor com `ride=True` (a Power Bomb do Tallon continua na sala), `ELEVATORS` +2, `AreaDef MINES`, mapa/minimapa "MINES", "PHAZON / MINES" no continue, a lista do mapa no `$81`; o `HOST` da ROM de teste da 17d se a porta R1 da P26 sair; `TEST_GROUP_D` | 2 d | validate: `check_elevators(_in_rom)` com 9 pares, rodadas dos lados (5 e 4); emulador: `elevador_mines_leste`, `elevador_mines_oeste` (ida e volta, `$079F` = 5); save/game over/continue com as cinco áreas |
| 19f | Região A (nível de cima) | as 13 salas novas e a P0 aberta; Save Station A (estação 1 da área 5); os mísseis da Main Quarry e da Elite Research (rodada 5) e da Security Access A (atrás do bloco de PB, rodada 6); **o Grapple do SM** na Storage Depot B (item novo: `GRANTS`, a porcentagem, o HUD); a Storage Depot A vazia atrás da porta de plasma; o túnel de Morph da Waste Disposal; a Elite Research pronta para a arena (19h) | 3 d | validate: alcance a pé, rodadas (as das outras áreas iguais), item novo; emulador: `mines_regiao_a_rota` (com o Grapple pego), `mines_save_station_a` |
| 19g | Inimigos | camada 0 do Prime na região A (e a tabela das regiões B–D registrada, como 12h/17g/18g), as espécies da decisão técnica 5, cópias em `$A0`, justiça em toda sala | 1,5–2 d | validate: `check_layer0_enemies` da Mines; emulador: `mines_inimigos_vivos`, `entradas_de_porta_mines` (auditoria de entrada, spec 15) |
| 19h | Phazon Elite (arena da Elite Research) | cópia do ninja dourado (vida e toque pela regra, cores de phazon, os projéteis dele com o dano medido), cota de mortes, a porta tranca, bit `$08` da área 5; prêmio: nada (decisão 3) | 2 d | validate: `check_bosses`/`check_arenas` com a arena nova; emulador: `mines_phazon_elite` (a luta de verdade, rodada 5) |
| 19i | Região B (nível do meio) | as 12 salas; Save Station B (estação 2), Map Station; o míssil da Elite Control Access, **o míssil no lugar da Power Bomb** (Central Dynamo, labirinto de Morph), o E-tank da Ventilation Shaft (grade de PB *(incerto)*), o míssil da Metroid Quarantine A (blocos de PB); a rocha de PB da Maintenance Tunnel; os Metroids e piratas da região | 3 d | validate: rodadas, `check_bombed_items`, `check_breakables`; emulador: `mines_regiao_b_rota`, `mines_save_station_b`, `mines_map_station` |
| 19j | Região C (oeste e o elevador da Magmoor) | as 5 salas novas e a P25 aberta; o caminho de gancho da Transport Access = bordas de Space Jump; o míssil do PPC; o E-tank da Processing Center Access (portas de plasma, rodada 6); a Elite Quarters pronta para a arena (19k) | 2 d | validate: `check_mines_locks_mapped` (toda trava do Prime na sua ligação com o seu mecanismo, como 12j/17i/18j), **nenhum atalho Magmoor ↔ Tallon antes da rodada 6** (as rodadas das outras áreas iguais); emulador: `mines_regiao_c_rota` |
| 19k | Omega Pirate (arena da Elite Quarters) | cópia do Bomb Torizo (cores de phazon, imune ao feixe sem carga, vida pela regra 13), o ponto fixo do Torizo resolvido (o mesmo do Thardus, ou por área), as 2 portas trancam (tipo 2, bit `$04` da área 5), bit `$10`; prêmio: nada | 2–3 d | validate: `check_arenas` com o Torizo na área 5; emulador: `mines_omega_pirate` (a luta de verdade, rodada 6) |
| 19l | Região D (nível de baixo) | as 10 salas; Save Station C (estação 3); os mísseis da Metroid Quarantine B, da Fungal Hall B e da Fungal Hall Access; a Phazon Mining Tunnel (blocos de bomba e de PB, sem o artefato); a Missile Station (decisão técnica 6); os Hunter Metroids | 2,5–3 d | validate: rodadas, `check_breakables`; emulador: `mines_regiao_d_rota`, `mines_save_station_c` |
| 19m | Rodadas das cinco áreas e a cadeia completa | `check_world_rounds` com a Mines (88 itens; as rodadas das outras áreas iguais; 88%), linha "elevadores a partir da rodada" com os 2 novos, `check_epic_mines`; a cadeia estendida pelos 2 elevadores (os 2 chefes vencidos de verdade, como na 18n), em 5–6 partes A → B → C → D; a tela do fim com 88% | 2,5–3 d | validate: linha "rodadas (specs/19m)"; emulador: a cadeia inteira, cada grupo ≤ ~5 min; verificação inteira |

```
19a ─┐
19b ─┼─> 19c ─┬─> 19e ─> 19f ─> 19g ─> 19h ─> 19i ─> 19j ─> 19k ─> 19l ─> 19m
     └─> 19d ─┘
```

19a, 19b e 19c não mudam a ROM e servem a qualquer resposta do usuário. A 19d só muda a ROM de teste. Da 19e em diante, cada filha
`verificada` antes da próxima. Os chefes vêm logo depois da região deles (o Phazon Elite na região A, o Omega na C), como no épico 18.
A região A vem primeiro porque é a entrada do Prime (o Tallon) e o MVP jogável; a C (a entrada da Magmoor, rodada 4) quase não tem
nada antes da rodada 6.

## Critérios de aceite (do épico)

1. 19a, 19b e 19c `verificada` com a ROM igual (sha1 do `.ips` igual ao de antes, dois builds; linhas do Tallon, da Chozo, da Magmoor,
   de Phendrana e das rodadas iguais; testes iguais).
2. Cada filha `verificada` com validate + build + testes (cada grupo ≤ ~6 min por comando); `check_orphans` prova que nenhum caminho
   entra em sala vanilla também pela área 5; `check_reclaimed` prova o uso das faixas novas (`$8F` e `$A1`) com as demos desligadas.
3. **As rodadas declaradas do Tallon, da Chozo, da Magmoor e de Phendrana iguais** em toda filha (salas e itens; o validador compara;
   desvio = parar e perguntar).
4. Definição de pronto: as salas da decisão 1 ligadas como no Prime, os 2 elevadores nos dois sentidos, a Mines jogável a pé com os itens
   da decisão 3, os chefes da decisão 4 com a luta de verdade, sem softlock (validador nas cinco áreas + cadeia no emulador), mapa de
   pausa/minimapa "MINES" salvos (a lista no `$81`), as 3 save stations e a map station, "PHAZON / MINES" no continue.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` com `$8F`/`$A1` (19a), `check_mines_slot` + `check_vanilla_pause` (19b), `check_mines` e a varredura do gancho (19c), `mines.check` (19d), elevadores (19e), alcance/rodadas por região (19f, 19i, 19j, 19l), inimigos (19g), arenas (19h, 19k), `check_mines_locks_mapped` (19j), `check_world_rounds` + `check_epic_mines` (19m) | +9–11 checagens |
| scratchpad | mutações de cada checagem nova (como 18a/18b/18c) | ~30 |
| run_tests.py (grupo D) | `porta_de_plasma_mina` (19d); 2 de elevador (19e); rota/save por região (19f, 19i, 19j, 19l: ~9); inimigos e entradas (19g); 2 chefes (19h, 19k); `mines_map_station`; as partes novas da cadeia (19m) | +16–20 |
| imagem | prévias das duas caras e do mapa; fotos do emulador das quatro regiões e dos dois chefes | — |

## Riscos e reversão

- **Área 5 nunca usada por nós**: a map station (a Tourian vanilla não tem), os ícones do mapa de pausa e a lista no `$81` são
  caminhos novos; a 19b confere por bytes e a 19e no emulador. Se a map station não funcionar na 5, a sala fica sem a máquina (só
  anotado) e o mapa se revela andando.
- **`$8F`/`$A1`**: as faixas novas guardam dado de demo (as de `$8F:C215` e `$8F:AD5C`); religar as demos quebraria (o validador pega).
  O alocador de `$A1` com faixa recuperada é código novo (a 19a prova com a ROM igual e mutações).
- **Rodadas das outras áreas** podem mudar por um atalho não previsto (a rocha da Maintenance Tunnel, uma porta de plasma, um elevador):
  o validador pega; a regra é mudar a Mines, não as outras.
- **Omega = segundo Torizo**: o código dos Torizos foi mudado no lugar (18k) e o ponto fixo é o do Thardus (`TORIZO_SPOT`): a arena da
  Elite Quarters precisa ter o chão nesse ponto, ou a 19k volta a ler o ponto por área (só a tabela); a VRAM inteira da sala é dele. Se
  não fechar: a alternativa (b) da decisão 4 (ninja dourado).
- **Ninja dourado**: pula e joga garras; o dano das garras (projéteis do `$86`) entra na regra de ≤ 40 por golpe (como `TORIZO_EPROJS`).
  Não medido no emulador *(incerto)*.
- **Grapple Beam**: item novo nas áreas (já existe na fragata). Conferir na 19f que o HUD o mostra e que nenhum bloco ou inimigo das
  salas feitas vira ponto de gancho (o SM agarra blocos de gancho e alguns inimigos: a varredura da 19c).
- **Tempo dos testes**: grupo D novo desde a 19e; se a cadeia passar de ~5 min num grupo, mais uma parte.
- **Mapa 64×32**: 205 telas cabem (o Tallon tem 251); as salas de 6×3 (Metroid Quarantine B) e as de 1×3 (elevadores) são as difíceis.
- **ROM de teste da 17d na Magmoor P26**: o elevador de verdade pode tomar o lugar da porta R1 de teste (19e muda o `HOST`).
- **Save de SRAM** (spec 11, B7): um save vanilla da Tourian cairia em dado sobrescrito; documentado, como na 12a/17a/18a.
- Reversão: tudo vem de `tools/`; 19a–19c não mudam a ROM (tirar as faixas, constantes e checagens basta).

## Fora de escopo

- Impact Crater (o plano das áreas a põe na 0; épico próprio).
- Flamethrower, Phazon Suit, artefatos, Scan/Thermal/X-Ray como trava, combos do charge; as camadas de evento (Elite Pirates — salvo a
  decisão 5 —, Shadow Pirates, Drones, os Metroids dos tanques, o 2º passe, os piratas e os nódulos da luta do Omega); o labirinto
  elétrico como dano; Metroid Prime.
- Grapple como trava (só se o usuário escolher a decisão 3b); Speed Booster e outras habilidades do SM que não estão no Prime.
- Mexer no Tallon, na Chozo, na Magmoor e em Phendrana além dos lados dos elevadores (`ride=True` no Tallon P43 e na Magmoor P26) e do
  `HOST` da ROM de teste.

## Decisões do usuário (perguntas)

1. **Tamanho**: (a) **as 42 salas**, por região (A nível de cima, B nível do meio, C oeste com o elevador da Magmoor e o Omega, D nível
   de baixo) (**recomendado**: é o tamanho do Prime, e só a mina inteira liga os dois elevadores); (b) só A + B (26 salas, ~112 telas: o
   nível de cima e o do meio vindos do Tallon, com o Phazon Elite; o elevador da Magmoor continua de enfeite, o Omega fica para depois).
2. **Área do SM**: (a) **a área 5 (a da Tourian)**, com a lista do mapa salvo no `$81` livre (**recomendado**: o plano já aceito no épico
   18; a 5 tem mapa salvo e tela de continue, e o único código dela é a bola de fogo do Ridley); (b) outra divisão (a Mines dividindo
   uma área já usada: o mapa dela ficaria cheio).
3. **Itens**: (a) **a regra das três áreas anteriores** — 9 mísseis, 2 E-tanks, **míssil no lugar da Power Bomb** (já está no Tallon),
   **o Grapple Beam do SM na Storage Depot B** (é o mesmo item, como o Super Missile em Phendrana; nenhuma trava o pede), nada no lugar do
   Flamethrower, do Phazon Suit e dos 2 artefatos: **13 itens, 88% no fim** (**recomendado**: segue a regra e não mexe nas rodadas das
   outras áreas); (b) a + **gancho de verdade**: os 6 pontos de gancho do Prime viram blocos de gancho do SM e travam (Transport Access,
   Main Quarry, Ore Processing, Metroid Quarantine B) — física nova no modelo de alcance, +4–6 dias; (c) a, mas um míssil no lugar do
   Grapple (nada novo no jogo).
4. **Chefes**: (a) **os dois** — Phazon Elite = cópia do pirata ninja dourado do SM (cores de phazon) na Elite Research, a porta tranca;
   Omega Pirate = cópia do Bomb Torizo (cores de phazon, imune ao feixe sem carga como a armadura) na Elite Quarters, as portas trancam;
   sem prêmio nos dois (artefato e Phazon Suit não existem) (**recomendado**: os dois dublês já funcionam no projeto ou não têm código
   de área, e os tetos de justiça do épico 14 valem); (b) os dois, mas o Omega também como ninja dourado (mais vida; sem repetir o
   Torizo do Thardus, mas do tamanho de um pirata); (c) o Omega como o **Golden Torizo de verdade** (dourado e maior; +2–3 dias para
   desfazer a correção da 18k por espécie); (d) nenhum agora (um épico de chefes depois).
5. **Elite Pirates** (3, nas camadas de evento: Elite Control, Omega Research, Dynamo Access): (a) **fora** (regra da camada 0, como as
   Elite Pirates de Phendrana e os Flying Pirates da Magmoor) (**recomendado**); (b) só a da Elite Control como mini-chefe (o mesmo ninja
   dourado do Phazon Elite, mais fraco; a porta para a Maintenance Tunnel tranca até ela morrer), +1 dia.
6. **Phazon**: (a) **sem dano** — o phazon azul é só cor nas paredes e poças (**recomendado**: no Prime quem protege é o Phazon Suit, que
   não existe no SM; dano sem proteção seria um perigo que o Prime não tem); (b) poças de phazon = o ácido do SM (FX da Tourian) pintado
   de azul, que machuca sempre, só fora do caminho obrigatório, medido numa ROM de teste (+1,5–2 dias); (c) phazon que machuca sem a
   Gravity (a Gravity no papel do Phazon Suit, um patch como o calor da Varia) (+2–3 dias).
7. **Visual**: (a) **duas caras** — base pirata (gráficos da Tourian, escura com o azul do phazon) e mina de rocha e fungos (gráficos do
   Brinstar, rocha cinza e fungo azul), música da Tourian (**recomendado**); (b) uma cara só para tudo (mais rápido, ~1 dia a menos).
8. **Testes**: (a) **um grupo D novo** (prefixo `mines_`, os elevadores da Mines e as partes novas da cadeia) (**recomendado**: o grupo C
   já está em 5 min 29 s, perto do limite de ~6 min); (b) dividir de outro jeito (por exemplo, a cadeia inteira num grupo só dela).

### Respostas (05/11/2026)

1. **(a) as 42 salas**, região por região (A–D).
2. *Padrão aceito, confirmado em 09/11/2026*: **(a)** área 5, lista do mapa salvo no `$81`.
3. **(a) a regra de sempre + o Grapple do SM**: 9 mísseis, 2 E-tanks, míssil no lugar da Power Bomb, o Grapple Beam do SM na Storage
   Depot B (nenhuma trava o pede), nada no lugar do Flamethrower, do Phazon Suit e dos artefatos. **13 itens, 88% no fim.**
4. **(a) os dois chefes**: Phazon Elite = cópia do pirata ninja dourado em cores de phazon; Omega Pirate = cópia do Bomb Torizo em cores
   de phazon, imune ao feixe sem carga; portas trancadas até morrerem; sem prêmio; tetos de justiça do épico 14.
5. *Padrão aceito, confirmado em 09/11/2026* (veio junto da resposta 4): **(a)** os 3 Elite Pirates fora.
6. **(a)** phazon só cor, sem dano.
7. *Padrão aceito, confirmado em 09/11/2026*: **(a)** duas caras (base pirata com gráficos da Tourian, mina de rocha e fungos com gráficos do Brinstar),
   música da Tourian.
8. *Padrão aceito, confirmado em 09/11/2026*: **(a)** grupo D novo de testes.

### Confirmação (09/11/2026)

O usuário mandou seguir com as sugestões do handoff: **confirmado pelo usuário em 09/11/2026: padrão aceito** em todas as escolhas que
estavam "a confirmar". As respostas 2, 5, 7 e 8 acima ficam confirmadas (área 5; os 3 Elite Pirates fora; duas caras e a música da
Tourian; grupo D). E as das filhas, sem mudança de código:
- 19c/19d: as 3 ligações de plasma no chão/teto ficam no mapa; a porta de plasma vertical nasce na filha da região que a usa.
- 19e: a Mines embaixo dos dois elevadores; as duas salas de elevador na base pirata.
- 19f: as formas da região A; a parede de PB da Mine Security Station diante da porta de plasma; a plataforma de PB da Ore Processing
  sem trava; o míssil da Elite Research a pé; as caras por sala.
- 19g: 2 piratas fora do caminho na Main Quarry; as propostas de B–D (Puffer = Mella, Metroids = o Metroid justo da 18l, Burrower =
  Sova, Ripper fora).
- 19h: o feixe sem carga fere o Phazon Elite, vida 400 (luta curta); as cores (armadura cinza, juntas azuis); a sala sem mudança; sem prêmio.
- 19i: as rochas de PB da Omega Research e da Central Dynamo sem trava; o E-tank da Ventilation Shaft atrás de blocos de PB; 1 pirata,
  1 Mella e 2 Metroids; as formas (a passarela, o labirinto como túnel, o duto e a câmara de PB).

## Desvios (preenchido na implementação)

- **19a** ([spec](19a-espaco-8f-e-a1.md), verificada): as 4 faixas do `$8F` (+4195 bytes) e `RECLAIMED_A1 = $A1:AD09–CCD3` (8139) no
  fim, ROM igual. Achados: as faixas novas do `$8F` têm **cabeçalhos de 4 salas das demos** (`$AF14`, `$AFFB`, `$B106`, `$CC6F`), e os
  validadores do gelo e das ruínas liam essas salas na ROM construída: com o cabeçalho recuperado o validador caía (achado no
  experimento positivo, com as faixas novas primeiro). Agora leem só as salas das demos intactas (`demo_rooms_kept`). Checagem a mais no
  `$A1`: população nossa na faixa é uma que o build escreveu. O scratchpad da sessão foi apagado três vezes (outro processo do Claude
  Code; a cópia do projeto com a pasta `.claude/` era o gatilho): as saídas da pesquisa (`s19/`) se perderam; a 19c gerou de novo o que
  precisava.
- **19b** ([spec](19b-area-da-mines.md), verificada): a lista do mapa no `$81` já está no build (`mapsave.list_at`; só age com sala na
  área 5). Achados: a **máscara da map station da área 5 é a mesma da área 7** (debug): a trava do `write_pause_map` aceita só esse
  caso; a **lista de ícones de map station da área 5 é vazia** (`FFFF`): a 19e precisa de uma lista nova; a **entrada 0 da lista de FX de
  paleta da área 5 é o calor** `$F761` (como a da Norfair): nenhuma sala nossa pode ligar o bit 0 de paleta lá (o validador recusa).
  SRAM livre 748 (não 805).
- **19c** ([spec](19c-grafo-e-mapa-mines.md), verificada): os dados contra o épico — **15 travas de evento** (mais as da Mine Security
  Station e da Dynamo Access, na camada 0), **nenhuma doca de Morph** (o túnel da Waste Disposal é dentro da sala: feature), **11
  objetos só de Power Bomb em 10 salas** (mais uma `Platform` da Ore Processing), nenhum bomb slot pelo nome, **nenhuma porta que só o
  Super Missile abre** (o vetor inteiro lido). Mapa **em faixas por nível** (A em cima, B no meio à direita, C no meio à esquerda, D
  embaixo): 7 ligações de chão/teto, 39 bytes no `$81`, as portas dos dois elevadores na tela de baixo. A varredura do gancho: nenhum
  bloco de tipo `$E` e nenhuma espécie das 28 das nossas salas em que a Samus se agarra.
- **19d** ([spec](19d-estilos-da-mina.md), verificada): base pirata na entrada **`$0E`** (gráficos e tabela da Tourian `$0D`, canos no
  azul do phazon, painéis de aço escuro, fundo `$E454`) e mina de rocha na **`$08`** (não `$07`/`$1A`: as duas têm salas de demo;
  gráficos e tabela do Brinstar `$06`, rocha cinza com fungo azul, fundo `$BAF4`); música `$1E/$05`; portas de onda roxas (de lado e a
  vertical) na linha 7 das duas. Só a ROM de teste (`build.py --teste-19d`, uma área 5 própria) escreve as entradas: **a ROM do jogo
  não muda**; o validador confere as duas (a de teste feita na memória). Teste `porta_de_plasma_mina` no grupo A (o plano dizia grupo D, que só nasce na 19e: ele pode ir para lá então). **Achado: 3 ligações
  de plasma no chão/teto** no mapa da 19c e nenhuma porta de plasma vertical no projeto (só gelo e onda): fica para a região que as usa
  (C/D) ou muda o mapa. **Decidido (técnico, 05/11/2026)**: a porta de plasma vertical é feita na filha da região que a usa
  (como a porta de onda vertical na 18i), o mapa fica como está.
- **19e** ([spec](19e-elevadores-da-mines.md), verificada): Tallon P43 ↔ Mines P0 e Magmoor P26 ↔ Mines P25 de verdade (`ELEVATORS` com 9
  pares), **a Mines embaixo dos dois** (os elevadores do Tallon e da Magmoor descem; a P26 da Magmoor foi redesenhada descendo e perdeu o
  poço de enfeite que subia), as duas salas da Mines na base pirata, becos; `areas.MINES` (área 5, "MINES", a lista do mapa salvo de 39
  bytes no `$81:EF1A`), "PHAZON / MINES" no continue, as entradas `$0E/$08` agora escritas na ROM do jogo; grupo D (`--grupo D`:
  `elevador_mines_leste`, `elevador_mines_oeste`, e o `porta_de_plasma_mina` que veio do A). As rodadas dos lados: **Tallon 5, Magmoor 4,
  como o épico previa**; linhas do Tallon e das rodadas idênticas (os 2 elevadores novos ficam na linha "mines (specs/19e)" até a 19m).
  O `HOST` da ROM de teste da 17d não mudou (a porta R1 da P26 continua). A **lista de ícones de map station da área 5 fica para a 19i**
  (sem map station construída, o build escreve o `FFFF` vanilla). Dois testes antigos ajustados porque provavam o que a 19e muda de
  propósito: `magmoor_regiao_c_itens` (o elevador da P26 de enfeite → agora ele leva à P25) e `mapa_da_tourian_sobrevive_ao_save` (a
  lista vanilla da Tourian → agora a lista da Mines no `$81`).
- **19f** ([spec](19f-regiao-a-mines.md), verificada): a região A (13 salas novas e a P0 aberta), Save Station A = estação 1 da área 5,
  os mísseis da Main Quarry (topo da torre do guindaste, borda de Space Jump) e da Elite Research (rodada 5) e da Security Access A
  (nicho com blocos de PB, rodada 6), **o Grapple Beam do SM na Storage Depot B** (`GRAPPLE_BEAM = $EF17`, `GRANTS` = `grapple`, que nada
  pede; bit `$4000`, um ponto na porcentagem; o HUD com o gancho), a Storage Depot A vazia atrás da parede de PB e da porta de plasma
  (rodada 6), o túnel de Morph da Waste Disposal, a Elite Research com o chão plano da arena. **Nenhuma porta de plasma vertical**: as 3
  de chão/teto da região são de gelo e de onda. **A linha das rodadas mudou de propósito**: 75 → **79 itens**, 75% → **79%** (mísseis 235
  → 250), coluna "Mines" (3 na rodada 5, 1 na 6); a do Tallon idêntica, as rodadas das outras áreas iguais. `check_mines_locks_mapped`
  nasceu aqui (o plano o punha na 19j). Escolhas a confirmar: a parede de PB da Mine Security Station diante da porta de plasma, a
  plataforma de PB da Ore Processing sem trava (`PB_NOTHING`). Testes (grupo D): `mines_regiao_a_rota`, `mines_regiao_a_rodada_6`,
  `mines_save_station_a`; o nível da Main Quarry cruza o banco: `nivel_cruza_banco_mines_main_quarry` (grupo B). **A parte 4 da cadeia
  passou para o grupo D** (o C estava em ~6 min; agora 2 min 06 s).
- **19g** ([spec](19g-inimigos-mines.md), verificada): a camada 0 da região A — **2 piratas** na Main Quarry (Prime 4: no braço do
  guindaste e no chão a leste da torre, fora da câmera das portas à altura da Samus) e **2 orbes** (a cópia da 18g) na Elevator Access A
  (Prime 4, 2 telas); a Elite Research livre para a 19h; `tools/mines/enemies.py` com a tabela do Prime das 42 salas e as propostas de
  B–D (Puffer = Mella, MetroidAlpha/Beta = o Metroid justo da 18l, **Burrower = a Sova da Magmoor**, não o PIPE `$E97F`, que o Power Beam
  não fere; Ripper fora). **Nenhuma cópia nova em `$A0`**. Achado: **o laser do pirata atravessa paredes** e sai sempre que a Samus está
  a menos de 16 px da altura dele, na câmera: regra nova `shooter_problems` (`Species.fires`). Na rota os orbes morrem com **míssil**
  (o Ice Beam da rodada 5 congela o orbe e os tiros seguintes não tiram vida). Testes novos (grupo D): `mines_inimigos_vivos`,
  `entradas_de_porta_mines`; `mines_regiao_a_rota` medida de novo. Linhas do Tallon e das rodadas idênticas.
- **19h** ([spec](19h-phazon-elite.md), verificada): o Phazon Elite = **cópia do pirata ninja dourado** (`$F593` → `$A0:F9BF`) com vida
  **400** (20 tiros do Power Beam), toque **40**, tabela própria (o Power Beam e os feixes sem carga ferem 1×; o dourado vanilla os rebate,
  mas o rebote só vale para o ponteiro `$F593`), cores de phazon das texturas do Prime (armadura cinza, veias azuis) e também a **paleta do
  salto** (linha 7: o init lê `$B2:8727`; o operando aponta para uma cópia em `$B2`, 2 bytes no lugar); arena de cota de mortes, bit `$08`
  da área 5, a porta de teto para a Security Access B **cinza até a vitória** e de gelo depois; sem prêmio. **A sala não mudou**: o código
  do ninja não lê paredes nem área (ele salta entre dois x do parâmetro 2; a sala vanilla tem 3 telas). Garras 20 por golpe. Teste
  `mines_phazon_elite` (grupo D: a luta de verdade com o equipamento da rodada 5, 2 tiros carregados, energia 99 → 94; a porta; o estado
  morto; save, game over, continue); `mines_regiao_a_rota` cruza a sala morta por atalho anotado (`poke 7ED82D 08`); a auditoria de
  entrada cobre as 2 portas dela. Regras novas: `check_ninja`, a paleta do salto na ROM, a linha "chefes da Mines (specs/19h)". As linhas
  do Tallon e das rodadas idênticas.
- **19i** ([spec](19i-regiao-b-mines.md), verificada): a região B (12 salas; a parede R1 da Elevator Access A vira a porta para a
  Elevator A), Save Station B = estação 2 da área 5, **a Map Station** (a 1ª da área 5: **lista de ícones nova no `$82` livre**, a da
  Tourian é só `FFFF`; a máquina do SM funciona na área 5 sem mudança), os mísseis da Elite Control Access (no chão, rodada 5) e **no
  lugar da Power Bomb** (o labirinto da Central Dynamo: poço, túnel de 1 linha e bloco de bomba; rodada 5), o E-tank da Ventilation Shaft
  (duto debaixo de blocos de PB, rodada 6) e o míssil da Metroid Quarantine A (câmara atrás de parede de PB, rodada 6); a parede de PB da
  Maintenance Tunnel diante da L0 (parede até a 19j; a trava em `GATES` já espera a região C). As rochas de PB da Omega Research e da
  Central Dynamo não travam nada (`PB_NOTHING`, a confirmar); `MAZES` novo (o labirinto guarda o míssil atrás de Morph + Bombas).
  Inimigos (as propostas da 19g tomadas): 1 pirata na passarela da Elite Control Access, 1 Mella na Ventilation Shaft, 2 Metroids na
  Metroid Quarantine A; o orbe de baixo da Elevator Access A foi de x 12 para x 6 (a porta R1 nova). **Rodadas: 83 itens, 83%**
  (energia 1399, mísseis 265); a do Tallon idêntica, as colunas das outras áreas iguais. Testes novos (grupo D):
  `mines_regiao_b_rota`, `mines_regiao_b_rodada_6`, `mines_save_station_b`, `mines_map_station`.
- **19j** ([spec](19j-regiao-c-mines.md), verificada): a região C (5 salas novas; a parede R2 da P25 vira a porta de gelo para a
  Transport Access): o **Phazon Processing Center com o salão da Omega Research** (as mesmas caminhadas) e um fosso no chão coberto
  por blocos de PB com o **míssil** (a parede Bendezium *(incerto)*, rodada 6), o **E-tank da Processing Center Access** entre as
  portas de plasma (rodada 6), a **Elite Quarters com o chão plano da arena** (vazia, as portas de plasma esperando a 19k), a Elite
  Quarters Access (a porta de chão para a Metroid Quarantine B parede até a 19l). A trava da parede de PB da Maintenance Tunnel (19i)
  passa a valer: **do elevador da Magmoor até a região B e o Tallon só na rodada 6** (provado pelas rodadas: sem a Power Bomb na
  trava a região B fica na 4). **O gancho da Transport Access não trava nada** (a sala tem 1 tela de altura: não cabe um penhasco de
  Space Jump; o Space Jump é da rodada 2). A Maintenance Tunnel passa à rodada 4 (o pedaço entre a L0 e a parede, pelo PPC).
  Nenhum inimigo (a camada 0 do Prime na região não tem). **Rodadas: 85 itens, 85%** (energia 1499, mísseis 270); a do Tallon
  idêntica, as colunas das outras áreas iguais. Teste novo (grupo D): `mines_regiao_c_rota`.
- **19k** ([spec](19k-omega-pirate.md), verificada): o **Omega Pirate** = a segunda cópia do Bomb Torizo (`$A0:F9FF`, `OMEGA`), vida
  **1200**, toque 8, **imune aos 12 feixes sem carga** (`$80`), míssil 1× (12 mísseis), tiro carregado 1× (20 do Power Beam), power bomb
  1×; sozinho na Elite Quarters na **posição do Thardus** (776, 368: as tabelas do init guardam uma só; o chão da linha 26 serve);
  arena `BOSS_BIT` `$04` (a morte do Torizo liga), bit `$10`, `needs = {Missile}`, as duas portas cinza de tipo 2 até a vitória e de
  plasma depois, sem prêmio, a música do Torizo. **As cores por área**: as 6 cargas de paleta do Torizo viram `JSR` a seletores no `$AA`
  livre (`omega_patches`), que na área 5 leem cópias das tabelas nas rampas do Phazon Elite; nas outras, as do Thardus (no lugar). O
  pulso do peito fica o do Thardus (cinza claro) nas duas áreas *(desvio: um só objeto de efeito de paleta)*. Achado: com Plasma + Ice +
  Wave o tiro carregado tira 900 — **dois tiros vencem** (decisão para o usuário na spec). Teste novo (grupo D): `mines_omega_pirate` (a
  luta de verdade, só mísseis: 11, energia 95); a `mines_regiao_c_rota` atravessa a sala com a arena ganha por RAM. Rodadas iguais (85
  itens, 85%).
- **19l** ([spec](19l-regiao-d-mines.md), verificada): a região D (as 10 salas do nível de baixo; a L1 da Metroid Quarantine A e a
  B1 da Elite Quarters Access viram portas): **a porta de plasma vertical** (`beamdoors`: cópias da amarela vanilla `$C866`/`$C86C`
  em `$84:FEFA`, PLMs `$FF5E`/`$FF64`) nas 3 ligações de chão/teto; **`SIDE_CAPS` na Mines** (as duas ligações da Fungal Hall A, gelo do
  lado dela e plasma do outro); a **Phazon Mining Tunnel** com a câmara da porta de teto atrás de um túnel de Morph com um bloco de
  bomba e um de Power Bomb (`MAZES` + `PB_ONLY`); **a Missile Station** (decisão técnica 6: o PLM `$B6EB` do SM achado,
  `Canvas.refill_station`, `RoomDef.missile_station`, `check_missile_station`; sem ícone no mapa); **Save Station C** = estação 3 da
  área 5; os 3 mísseis (`$F5` no alto de uma coluna de Space Jump na Metroid Quarantine B; `$F6` e `$F7` a pé), todos na rodada 6; a
  Elevator Access B na rodada 5, o resto na 6. Inimigos (as propostas da 19g tomadas): 1 orbe na Quarantine Access B, 1 Sova na
  Elevator Access B, 2 Metroids na Fungal Hall B, 1 pirata + 1 orbe na Fungal Hall Access, 2 **Hunter Metroids** (tipo novo
  `hunter_metroid`, a mesma cópia) na Fungal Hall A; Rippers fora. Desvio na região C: o degrau da R0 da Elite Quarters Access encurtado
  (cobria a porta de chão). **Rodadas: 88 itens, 88%** (energia 1499, mísseis 285); a do Tallon idêntica, as colunas das outras
  áreas iguais. Testes novos (grupo D): `mines_regiao_d_rota`, `mines_save_station_c`.
- **19m** ([spec](19m-rodadas-e-cadeia-cinco-areas.md), verificada, ROM igual): a linha das rodadas com os 2 elevadores da Mines
  (**mines_east 5 (do Tallon), mines_west 4 (da Magmoor)**), itens por rodada e 88% iguais; `check_epic_mines` (linha "mines (specs/19,
  épico fechado na 19m)"); a cadeia em **5 partes** (a 4 = rodadas 4–5 no grupo C, a 5 = rodada 6, o fim e a tela no grupo D), os 13
  itens da Mines pegos andando nas rodadas declaradas, **o Phazon Elite e o Omega Pirate vencidos de verdade** (as lutas da 19h e da
  19k venceram também da entrada da cadeia), os 2 elevadores de verdade (o oeste andado na rodada 6), **88% na tela do fim**. Desvios:
  a Samus posta na plataforma nos 4 elevadores da Mines (atalho contado; 2 px a leste com o equipamento da cadeia); a Mines da rodada 4
  não é visitada (sem item); depois do Omega a volta à Elite Quarters Access por `door_teleport`; a recarga da nave do `fc_end` com 1700
  quadros.

## Verificação do épico (10/11/2026, 19m)

Conferido no fim da 19m, contra os critérios de aceite do épico e as decisões do usuário:

| Critério | Onde | Resultado |
|---|---|---|
| 1. 19a, 19b, 19c com a ROM igual | [19a](19a-espaco-8f-e-a1.md), [19b](19b-area-da-mines.md), [19c](19c-grafo-e-mapa-mines.md) | sim (ROM igual, linhas e testes iguais nas três; a 19d também) |
| 2. Cada filha verificada (validate + build + testes, cada grupo ≤ ~6 min); nenhum caminho entra em sala vanilla pela área 5; `$8F` e `$A1` só com as demos desligadas | as 13 filhas; `check_orphans`, `check_reclaimed` | sim (validate 0 problemas em todas; na 19m A 3 min 17 s, B 3 min 52 s, C 4 min 24 s, D 3 min 31 s; a 19h mediu 5–10× mais com a máquina carregada) |
| 3. Rodadas declaradas do Tallon, da Chozo, da Magmoor e de Phendrana iguais em toda filha | linha "tallon (…)" e linha "rodadas (specs/12m, 17j, 18n, 19m)" | sim: "44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"; itens por rodada das quatro áreas iguais aos da 18n; elevadores de antes iguais |
| 4a. As 42 salas ligadas como no Prime | `check_mines` (tabela, 43 ligações), `check_epic_mines` | sim |
| 4b. Os 2 elevadores nos dois sentidos | `check_elevators(_in_rom)`; `elevador_mines_leste`, `elevador_mines_oeste`; a cadeia (P43 ↓ 1, P0 ↑ 2, P26 ↓ 1) | sim |
| 4c. A Mines a pé com os itens da decisão 3 | `check_mines_rounds`, `check_world_rounds`, `check_epic_mines`; as caminhadas das regiões (19f–19l) e a cadeia (os 13 itens nas rodadas, andando, nenhum por RAM) | sim: 10 mísseis (um no lugar da Power Bomb), 2 E-tanks, o Grapple Beam do SM; **88 itens, 88%** (a tela do fim do SM mostra 88%) |
| 4d. Os chefes da decisão 4 com a luta de verdade | `check_epic_bosses`, `check_arenas`; `mines_phazon_elite`, `mines_omega_pirate`; a cadeia (as duas lutas da entrada dela) | sim |
| 4e. Sem softlock | `check_tallon_return` e `check_tallon_round_stuck` nas cinco áreas; a cadeia inteira | sim |
| 4f. Mapa/minimapa "MINES" salvos (a lista no `$81`), 3 save stations e a map station, "PHAZON / MINES" no continue | `check_pause_maps`, `check_mines_slot`; `mines_save_station_a/b/c`, `mines_map_station`, `elevador_mines_leste` | sim |
| Decisão 1: as 42 salas, região por região | 19f, 19i, 19j, 19l | sim |
| Decisão 2: área 5, lista do mapa no `$81` | `check_mines_slot` | sim (confirmado em 09/11/2026) |
| Decisão 3: itens (o Grapple do SM, nenhuma trava o pede) | `EPIC_MINES_ITEMS`, `EPIC_MINES_NO_ITEM`, `check_no_grapple_locks` | sim |
| Decisão 4: os dois chefes | `EPIC_MINES_BOSS_ROOMS`, `check_epic_mines` | sim |
| Decisão 5: as 3 Elite Pirates fora | `check_mines_enemies` (camada 0) | sim (confirmado em 09/11/2026) |
| Decisão 6: phazon só cor | `check_epic_mines` (sem calor, água, neve nem lava) | sim |
| Decisão 7: duas caras, música da Tourian | `mines.check`, `check_mines_in_rom` | sim (confirmado em 09/11/2026) |
| Decisão 8: grupo D | `TEST_GROUP_D`, `CHAIN_GROUP` | sim (confirmado em 09/11/2026) |

Decisões das filhas ainda a confirmar pelo usuário (padrão adotado): **19j** — o míssil do PPC atrás de PB (alternativa: borda de Space
Jump, rodada 4); o gancho da Transport Access sem trava; as formas das salas. **19k** — o tiro carregado fere o Omega (com Plasma + Ice +
Wave dois tiros vencem; alternativa: imune também ao carregado, só mísseis); vida 1200; as cores e o pulso do peito cinza. **19l** — o
míssil da Metroid Quarantine B numa coluna de Space Jump (alternativa: no chão); o túnel da Phazon Mining Tunnel com 1 bloco de bomba e
1 de PB (no Prime: 17 blocos e uma parede de PB); menos inimigos que no Prime; a Missile Station sem ícone no mapa; as formas das
salas. **19m** — os elevadores da Mines na cadeia com a Samus posta na plataforma (atalho contado). Fica em aberto: a Impact Crater
(área 0, o plano das áreas) e um fim próprio do jogo.
