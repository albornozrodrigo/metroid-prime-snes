# 18 — Phendrana Drifts (épico)

Estado: **verificada** (04/11/2026, fechado na 18n: as 14 filhas 18a–18n verificadas; critérios conferidos em "Verificação do épico", no fim). Aprovada em 03/11/2026: decisões do usuário 1, 3, 4 e 5 respondidas; 2, 6 e 7 = padrão aceito, a confirmar; ver "Respostas" no fim. 18a, 18b e 18c verificadas em 03/11/2026, ROM igual; 18d e 18e verificadas em 03/11/2026; 18f e 18g verificadas em 03/11/2026; 18h verificada em 03/11/2026; 18i verificada em 03/11/2026; 18j verificada em 03/11/2026; 18k verificada em 03/11/2026; 18l verificada em 03/11/2026; 18m verificada em 04/11/2026: as 56 salas e os 17 itens; 18n verificada em 04/11/2026: as rodadas das quatro áreas (75 itens, 75%) e a cadeia completa com os dois chefes vencidos de verdade
Esforço estimado: 29–33 dias no total, em 14 filhas de 0,5–3 dias (a Magmoor, 29 salas e ~156 telas, levou 10 filhas; Phendrana tem
**56 salas e ~302 telas**, a maior área até agora, mais 2 chefes, 3 estilos novos e o terceiro grupo de testes). MVP (18a–18g: a
região norte jogável vinda da Magmoor, com os inimigos): 11–13 dias. Com a opção (b) da decisão 3 (Speed Booster e Grapple): +4–6 dias.

## Contexto

Tallon (44 salas), Chozo (64) e Magmoor (29) estão prontos e andados juntos: **58 itens em 7 rodadas, 58%**, a cadeia completa no
emulador em 3 testes ligados por estado salvo (17j), os 4 chefes da Chozo (épico 14). O usuário aprovou a próxima etapa: **Phendrana
Drifts**, o mundo de gelo que no Prime se liga só à Magmoor, por dois elevadores. Hoje os dois lados da Magmoor são **de enfeite**:
`magmoor_transport_phendrana_north` (P13, região B, rodada 3) e `magmoor_transport_phendrana_south` (P27, região C, rodada 3)
(`tools/magmoor/rooms.py:56` `DECORATIVE_ELEVATORS`, linhas 92 e 107).

Este épico segue o molde do 17 (e do 12): levanta os fatos (Prime e ROM), decide o que é técnico, deixa ao usuário o que é de gosto ou
de escopo, e divide o trabalho em filhas — toolchain e dados primeiro (ROM igual), regiões por último, as rodadas e a cadeia no fim.
Também fecha a pendência do épico 17 (decisão 6, "aviso de capacidade"): **o plano das áreas do SM para Phendrana, Mines e Impact Crater**.

## Estado atual (verificado)

Na pasta real, antes desta etapa (leitura só): `python3 -I tools/validate.py` → "165 salas, 342 portas, 0 problemas" (17 s); linha
"rodadas (specs/12m, 17j): Tallon + Chozo + Magmoor andados juntos, 58 itens em 7 rodadas … porcentagem do fim ($8B:E627) com
todos: 58% (energia 999, mísseis 180, power bombs 15)". Nenhum teste rodado, nenhum build (só leitura de `build/metroid_prime_snes.sfc`
e `build/manifest.json`). Roteiros desta pesquisa no scratchpad da sessão (`…/scratchpad/s18/scripts/`): `phen_objs.py` (itens, cor das
portas, funções especiais, inimigos por camada, destino dos elevadores; o `magmoor_objs.py` da 17 com o nome do mundo trocado),
`phen_named.py` (água, gatilhos de dano com a vulnerabilidade, objetos de trava por nome), `phen_envfx.py` (o `AreaAttributes`: neve),
`summary.py`/`table.py`/`regions.py` (tamanho pela regra do Tallon, travas por doca, regiões), `tileset_survey.py` (tilesets, FX e
música das salas vanilla). Saídas: `s18/phendrana_locks.json` (o `tools/dump_prime_locks.py` rodado para Phendrana: "56 salas"),
`s18/phen_objs.out`, `s18/named.out`, `s18/envfx.out`, `s18/summary.out`, `s18/table.md`, `s18/tilesets.out`, `s18/free.out`,
`s18/orphans.out` (os `free.py`/`orphan_runs.py` da 17, rodados de novo), `s18/validate.out`.

### Phendrana no Prime (dados)

Fonte: `research/prime_worlds.json` (MLVL "Phendrana Drifts") e os objetos de `research/prime_fs` (retro-data-structures 0.44.1, venv
`tools/venv`; mesmos métodos da 17: item = 1ª palavra depois do nome + 60 bytes; cor de porta = `DamageVulnerability` do
`Trigger_DoorKey`, ordem power, ice, wave, plasma, 1 = dano, 2 = imune; neve = `AreaAttributes.fx_type_` 1). "Conhecimento" = o que
eu sei do jogo e os dados não mostram; marcado *(incerto)* quando não tenho certeza.

- **56 salas** (índices 0–55), **118 docks = 59 ligações**, todas com volta; **4 ciclos** (Shorelines ↔ Ice Ruins East pelos dois
  acessos; o grande anel Ruined Courtyard → laboratórios → torres → Research Core → Frozen Pike → Transport Access → elevador sul →
  Quarantine Cave → Ruined Courtyard; dois anéis no sul: Frost Cave/Hunter Cave/Phendrana's Edge e Hunter Cave/Gravity Chamber).
- **4 save stations** (P4 Save Station B, P17 A, P33 D, P45 C) e **1 map station** (P22).
- **2 elevadores** (`WorldTeleporter`, destino pelo id de MREA nos bytes): P0 Transport to Magmoor Caverns West → **Magmoor P13**
  Transport to Phendrana Drifts North; P29 Transport to Magmoor Caverns South → **Magmoor P27** Transport to Phendrana Drifts South.
  Nenhum para outro mundo.
- **Itens** (23 `Pickup` de verdade; os outros 300+ `Pickup - …` são recargas soltas por inimigo):

| P# | Sala | Item do Prime (enum) | Existe no SM? |
|---|---|---|---|
| 2 | Phendrana Shorelines | Missile Expansion (4) ×2 (uma no alto da torre com trilho de Spider) | sim |
| 10 | Ice Ruins East | Missile Expansion (4) ×2 (uma num trilho de Spider, outra num bloco de gelo) | sim |
| 25 | Research Lab Hydra | Missile Expansion (4) | sim |
| 27 | Quarantine Monitor | Missile Expansion (4) | sim |
| 41 | Frost Cave | Missile Expansion (4) | sim |
| 51 | Research Lab Aether | Missile Expansion (4) + Energy Tank (24) | sim |
| 53 | Gravity Chamber | Missile Expansion (4) + **Gravity Suit** (21) | sim (a Gravity **já está no Tallon**, 09b) |
| 15 | Ruined Courtyard | Energy Tank (24) | sim |
| 31 | Transport Access | Energy Tank (24) (num bloco de gelo que só o Plasma derrete: `DamageableTrigger_ice01` `2 2 2 1`) | sim |
| 9 | Ice Ruins West | Power Bomb Expansion (7) (num bloco de gelo de Plasma: `Actor _Iceblockpickup`, `2 2 2 1`) | sim (liga as PBs no SM) |
| 55 | Security Cave | Power Bomb Expansion (7) | sim |
| 14 | Chapel of the Elders | **Wave Beam** (2) (depois do Sheegoth) | sim (o Wave **já está no Tallon**, Magmoor East, 09b) |
| 16 | Phendrana Canyon | **Boost Ball** (18) | **não** |
| 24 | Quarantine Cave | **Spider Ball** (19) (depois do Thardus) | **não** |
| 30 | Observatory | **Super Missile** (11, `P_Power_Combo`) | **sim: o Super Missile do SM** (PLM `$84:EEDF`, conferido: setup `$EE57`) |
| 40 | Research Core | **Thermal Visor** (9) (camada 1) | **não** |
| 8 | Chozo Ice Temple | artefato (37) | não (artefatos fora desde o épico 07) |
| 39 | Control Tower | artefato (31) | não |
| 54 | Storage Cave | artefato (39) | não |

  **Correções de premissas**: o **Ice Beam não é de Phendrana** (é da Chozo, Antechamber; o épico 09 o pôs no Tallon, Root Cave); o
  **Space Jump** é do Tallon (Alcove); o **Grapple** é da Phazon Mines. As habilidades de Phendrana são **Wave, Boost, Spider, Super
  Missile, Thermal e Gravity**. São 9 mísseis, 3 E-tanks, 2 expansões de PB — e 6 habilidades e 3 artefatos.
- **Frio: nenhum.** Nenhuma das 56 salas tem `SpecialFunction` 18 (`Area Damage`): `area_damage` 0 em todas
  (`s18/phendrana_locks.json`). O Prime não machuca no frio.
- **Neve** (`AreaAttributes`, `fx_type_` 1): **23 salas** — 0, 1, 2, 5, 8, 9, 10, 14, 15, 16, 17, 21, 24, 26, 27, 31, 34, 37, 39, 45,
  52, 54, 55 (densidade 0,3–0,5 nas Ice Ruins e no Ice Temple, 1,0 no resto). As salas com `AreaAttributes` (céu à vista) são 28; os
  laboratórios e as cavernas fundas não têm.
- **Água** (objeto `Water`, todos "ice water"): Phendrana Shorelines (1), Ruined Courtyard (2: "DOWN"/"UP position", a água que sobe no
  quebra-cabeça), Frozen Pike, Hunter Cave Access, Frost Cave, Hunter Cave, Lower Edge Tunnel, Lake Tunnel, Phendrana's Edge (1 cada) e
  **Gravity Chamber (4: a sala funda)**. 10 salas.
- **Travas nas portas** (`s18/phendrana_locks.json` + cor lida das vulnerabilidades): **71 docas key** — **65 de onda** (`2 2 1 2`:
  praticamente todas do Ruined Courtyard para o sul, e a saída da Chapel of the Elders), **4 de gelo** (`2 1 2 2`: Transport to Magmoor
  South ↔ Transport Access, Pike Access ↔ Research Core), **2 de plasma** (`2 2 2 1`: Phendrana's Edge ↔ Storage Cave); **5 escudos
  de míssil** (`Actor Missile Lock`: Ice Ruins West → Canyon Entryway, Ruined Courtyard → Save Station A, Observatory → Save Station D,
  West Tower Entrance ↔ West Tower); **4 docas de Morph** (`Door_Area Morphball`: Quarantine Cave ↔ Quarantine Monitor, Phendrana's
  Edge ↔ Security Cave). Nenhuma porta de charge (como na Chozo e na Magmoor).
- **Travas dentro das salas** (dados; o uso no caminho é conhecimento):
  - trilhos de Spider (`spider`): Shorelines (9, a torre do míssil), Ice Ruins East (18, um míssil), Ruined Courtyard (30), **Quarantine
    Cave (113: a arena do Thardus e a saída para a Quarantine Monitor)**, Transport to Magmoor South (34);
  - bomb slots: Chozo Ice Temple (9: a estátua; "Make Head Explode"), Ruined Courtyard (9: sobe a água), Observatory (6: liga o projetor);
  - meio-tubo de Boost: Phendrana Canyon (5, as plataformas que flutuam: a Boost Ball no alto *(incerto)*);
  - `GrapplePoint`: Quarantine Cave (2), Hunter Cave (1), Phendrana's Edge (2), Gravity Chamber (1) — no Prime o Grapple vem da Mines;
  - gelo de Plasma (`2 2 2 1`): Chozo Ice Temple (6 gatilhos: o artefato), Ice Ruins West (a expansão de PB), Transport Access (o E-tank);
  - painéis de Wave ("Hit Detection" `2 2 1 2` com "Thermal Wire"): Ruined Courtyard e Research Core — o Thermal mostra o fio, o Wave
    liga (conhecimento);
  - estalactites que caem ("Cracked Stalactite"): Ice Ruins West, Frost Cave (3, quebram o gelo do lago do míssil), Hunter Cave (3);
  - vidro dos tubos (`Actor Glass Break`, `1 1 1 1`): Research Lab Hydra (5) e Aether (3+): os Metroids presos.
- **Inimigos** (camada 0, a regra de 07i/12h/17g; nomes dos tipos dos dados): Shorelines Parasite 4; Ice Ruins Access AtomicBeta 2;
  Courtyard Entryway AtomicAlpha 1 + WallCrawlerSwarm 2; Canyon Entryway AtomicBeta 2; **Chapel of the Elders Babygoth 4 + IceSheegoth 1**;
  Phendrana Canyon Babygoth 1 + Parasite 7; North Quarantine Tunnel AtomicAlpha 2; Hydra Lab Entryway AtomicBeta 2; South Quarantine
  Tunnel AtomicAlpha 2; Transport Access AtomicAlpha 1; Frozen Pike JellyZap 1; Frost Cave Access Beetle 2 + WallCrawlerSwarm 1; Hunter
  Cave Access JellyZap 3; **Research Core MetroidAlpha 3**; Frost Cave Ripper 1; Lower Edge Tunnel AtomicBeta 2; Chamber Access Drone 1;
  Lake Tunnel AtomicBeta 1; Aether Lab Entryway AtomicBeta 3; **Research Lab Aether MetroidAlpha 1**; Phendrana's Edge FlyingPirate 2 +
  JellyZap 2 + Ripper 1; Gravity Chamber JellyZap 2 + SpankWeed 6. Nas outras camadas (passes e eventos): Ice Troopers e Space Pirates
  dos laboratórios (até 8 por sala), **3 Elite Pirates** (Research Entrance L5, Research Lab Hydra L4, Control Tower L3), Metroids dos
  tubos, Ice Sheegoths do 2º passe (Ruins Entryway, Ice Ruins West/East, Quarantine Cave), Babygoths, Flying Pirates, Shriekbats
  (FlickerBat), o voo do Ridley (Shorelines/Canyon/Control Tower).
- **Chefes**: **Sheegoth** (Chapel of the Elders, camada 0, com 4 Babygoths; guarda o Wave) e **Thardus** (Quarantine Cave, camada 3
  "Thardus", com `DamageableTrigger (Kills Thardus)`; guarda a Spider Ball). Não há Flaahgra nem chefe Chozo; as Elite Pirates são
  camada de evento (fora, como os Flying Pirates da Magmoor).

Tamanho SM pela regra do Tallon (`tools/tallon/rooms.py:57` `screens`, 30 m por tela, no máximo 6×4; `s18/table.md`). "Neve" =
`fx_type_` 1; "Água" = objeto `Water`; travas pelo lado da sala da linha (o outro lado, na linha da outra sala):

| P# | Sala | Telas | Liga a (trava deste lado) | Região | Neve | Água | Travas na sala |
|---|---|---|---|---|---|---|---|
| 0 | Transport to Magmoor Caverns West | 2×2 | 1 | A | sim | | elevador (Magmoor P13) |
| 1 | Shoreline Entrance | 4×1 | 0, 2 | A | sim | | |
| 2 | Phendrana Shorelines | 6×2 | 1, 3, 4, 5, 6, 7 | A | sim | sim | spider 9 |
| 3 | Temple Entryway | 3×1 | 8, 2 | A | | | |
| 4 | Save Station B | 1×1 | 2 | A | | | |
| 5 | Ruins Entryway | 3×2 | 9, 2 | A | sim | | |
| 6 | Plaza Walkway | 4×1 | 2, 10 | A | | | |
| 7 | Ice Ruins Access | 3×1 | 10, 2 | A | | | |
| 8 | Chozo Ice Temple | 5×2 | 3, 11 | A | sim | | bomb slot 9, gelo de plasma (artefato) |
| 9 | Ice Ruins West | 4×2 | 5, 12 (onda), 13 (míssil) | B | sim | | gelo de plasma (PB) |
| 10 | Ice Ruins East | 3×2 | 7, 6 | A | sim | | spider 18 |
| 11 | Chapel Tunnel | 2×1 | 14, 8 | A | | | blocos (qualquer tiro) |
| 12 | Courtyard Entryway | 3×1 | 15, 9 | B | | | |
| 13 | Canyon Entryway | 3×1 | 16, 9 | B | | | |
| 14 | Chapel of the Elders | 4×1 | 11 (onda) | A | sim | | **Sheegoth** |
| 15 | Ruined Courtyard | 5×2 | 12, 17 (míssil), 18 (onda), 19 | B | sim | sim | bomb slot 9, spider 30, painel de Wave |
| 16 | Phendrana Canyon | 6×3 | 13 | B | sim | | meio-tubo 5 |
| 17 | Save Station A | 1×1 | 15 | B | sim | | |
| 18 | Specimen Storage | 2×1 | 20 (onda), 15 (onda) | B | | | |
| 19 | Quarantine Access | 2×1 | 21, 15 | B | | | |
| 20 | Research Entrance | 3×1 | 18 (onda), 22, 23 (onda) | B | | | |
| 21 | North Quarantine Tunnel | 6×4 | 24 (onda), 19 (onda) | C | sim | | |
| 22 | Map Station | 1×1 | 20 | B | | | |
| 23 | Hydra Lab Entryway | 3×1 | 20 (onda), 25 (onda) | B | | | |
| 24 | Quarantine Cave | 6×2 | 21 (onda), 26 (onda), 27 (morph) | C | sim | | **Thardus**; spider 113, grapple 2 |
| 25 | Research Lab Hydra | 2×2 | 23 (onda), 28 (onda) | B | | | vidro dos tubos |
| 26 | South Quarantine Tunnel | 6×4 | 24 (onda), 29 (onda) | C | sim | | |
| 27 | Quarantine Monitor | 3×1 | 24 (morph) | C | sim | | |
| 28 | Observatory Access | 3×1 | 30 (onda), 25 (onda) | D | | | |
| 29 | Transport to Magmoor Caverns South | 2×2 | 31 (gelo), 26 (onda) | C | | | elevador (Magmoor P27); spider 34 |
| 30 | Observatory | 3×2 | 28 (onda), 32 (onda), 33 (míssil) | D | | | bomb slot 6 |
| 31 | Transport Access | 2×1 | 29 (gelo), 34 (onda) | C | sim | | gelo de plasma (E-tank) |
| 32 | West Tower Entrance | 1×1 | 35 (míssil), 30 (onda) | D | | | |
| 33 | Save Station D | 1×1 | 30 | D | | | |
| 34 | Frozen Pike | 3×4 | 36 (onda), 31 (onda), 37 (onda), 38 (onda) | E | sim | sim | |
| 35 | West Tower | 2×2 | 32 (míssil), 39 (onda) | D | | | |
| 36 | Pike Access | 2×1 | 34 (onda), 40 (gelo) | D | | | |
| 37 | Frost Cave Access | 6×2 | 34 (onda), 41 (onda) | E | sim | | |
| 38 | Hunter Cave Access | 6×1 | 34 (onda), 42 (onda) | E | | sim | |
| 39 | Control Tower | 4×2 | 43 (onda), 35 (onda) | D | sim | | |
| 40 | Research Core | 2×2 | 36 (gelo), 44 (onda) | D | | | painel de Wave |
| 41 | Frost Cave | 3×3 | 45 (onda), 37 (onda), 46 (onda) | E | | sim | estalactites |
| 42 | Hunter Cave | 3×2 | 38, 47, 48, 49 (onda) | E | | sim | grapple 1, estalactites |
| 43 | East Tower | 2×2 | 50 (onda), 39 (onda) | D | | | |
| 44 | Research Core Access | 2×1 | 40 (onda), 51 (onda) | D | | | |
| 45 | Save Station C | 2×1 | 41 (onda) | E | sim | | |
| 46 | Upper Edge Tunnel | 3×1 | 52 (onda), 41 (onda) | E | | | |
| 47 | Lower Edge Tunnel | 3×1 | 52 (onda), 42 (onda) | E | | sim | |
| 48 | Chamber Access | 2×1 | 42 (onda), 53 (onda) | E | | | |
| 49 | Lake Tunnel | 2×1 | 42 (onda), 53 (onda) | E | | sim | |
| 50 | Aether Lab Entryway | 1×1 | 43 (onda), 51 (onda) | D | | | |
| 51 | Research Lab Aether | 3×2 | 50 (onda), 44 (onda) | D | | | vidro dos tubos |
| 52 | Phendrana's Edge | 2×4 | 47 (onda), 46 (onda), 54 (plasma), 55 (morph) | E | sim | sim | grapple 2 |
| 53 | Gravity Chamber | 3×2 | 49 (onda), 48 (onda) | E | | sim (funda) | grapple 1 |
| 54 | Storage Cave | 1×1 | 52 (plasma) | E | sim | | só o artefato |
| 55 | Security Cave | 2×1 | 52 (morph) | E | sim | | |

**Total ~302 telas** (Tallon 251, Chozo 202, Magmoor 156). As duas Quarantine Tunnels dão 6×4 pela regra (caixas de 173×232 e
235×167 m: túneis que serpenteiam em 3D); a 18c pode limitá-las se o mapa 64×32 não fechar (ver Riscos).

### Regiões (pelo grafo, como 07, 12 e 17; `s18/scripts/regions.py`)

- **A — Norte: Shorelines, Ice Temple, Chapel** (12 salas, ~59 telas): 0, 1, 2, 3, 4 Save B, 5, 6, 7, 8 Chozo Ice Temple, 10 Ice
  Ruins East, 11, 14 Chapel of the Elders (Sheegoth). Itens: os 2 mísseis da Shorelines, os 2 da Ice Ruins East, o lugar do Wave.
- **B — Ice Ruins West, Ruined Courtyard e o primeiro laboratório** (12 salas, ~58 telas): 9 Ice Ruins West, 12, 13, 16 Phendrana
  Canyon, 15 Ruined Courtyard, 17 Save A, 18, 19, 20 Research Entrance, 22 Map Station, 23, 25 Research Lab Hydra. Itens: PB da Ice
  Ruins West (gelo de plasma), E-tank do Courtyard, o lugar da Boost, o míssil da Hydra.
- **C — Quarentena e o elevador sul** (6 salas, ~69 telas): 21 North Quarantine Tunnel, 24 Quarantine Cave (Thardus), 26 South
  Quarantine Tunnel, 27 Quarantine Monitor, 29 Transport to Magmoor South, 31 Transport Access. Itens: o lugar da Spider, o míssil da
  Monitor, o E-tank da Transport Access (gelo de plasma).
- **D — Observatório, torres e laboratórios** (12 salas, ~42 telas): 28, 30 Observatory, 32, 33 Save D, 35 West Tower, 39 Control
  Tower, 43 East Tower, 50, 51 Research Lab Aether, 44, 40 Research Core, 36 Pike Access. Itens: o Super Missile, o E-tank e o míssil
  da Aether, o lugar do Thermal.
- **E — Sul fundo: Frozen Pike, cavernas, Phendrana's Edge, Gravity Chamber** (14 salas, ~74 telas): 34, 37, 38, 41 Frost Cave, 45
  Save C, 42 Hunter Cave, 46, 47, 48, 49, 52 Phendrana's Edge, 53 Gravity Chamber, 54 Storage Cave, 55 Security Cave. Itens: o míssil
  da Frost Cave, o míssil e o lugar da Gravity, a PB da Security Cave.

Ligações entre regiões: A–B (5–9), B–C (19–21), B–D (25–28), C–E (31–34), E–D (34–36).

### Como Phendrana encaixa no nosso mundo (verificado no código)

- **Pares de elevador**: `tools/areas.py:238` `ELEVATORS` tem 5 pares; os dois lados da Magmoor que levam a Phendrana são de enfeite
  e ficam na **rodada 3** (linha "magmoor (specs/17e, 17f)" do validador: rodada 3 = as 23 salas quentes e o sul, onde estão a P13 e a
  P27). Phendrana acrescenta 2 pares: Magmoor P13 ↔ Phendrana P0 e Magmoor P27 ↔ Phendrana P29 (7 no total).
- **Itens que o Tallon já tem** (`tools/tallon/items.py:99–110`, épico 09): Ice (Root Cave, rodada 3), **Wave** (Transport to Magmoor
  East, rodada 1), **Gravity** (Transport to Chozo East, rodada 4), Plasma (Transport to Chozo South, rodada 5), Morph, Bombas, Power
  Bomb (Mines East, rodada 5), X-Ray, Space Jump; a Chozo deu Charge e Varia (`tools/chozo/items.py:49, 52`). **Nenhum item de
  Phendrana do Prime que existe no SM está faltando, exceto o Super Missile.**
- **Regra dos itens** (épicos 12 e 17, aceita duas vezes): item do Prime que já está no jogo → **míssil** no lugar (Morph, Bombas e Ice
  da Chozo; Plasma da Magmoor); item que não existe no SM → **nada** (Wavebuster, Ice Spreader, artefatos); Missile/E-tank/expansão de
  PB → o mesmo do SM. Aplicada a Phendrana: Wave e Gravity → míssil; Boost, Spider, Thermal e os 3 artefatos → nada; **Super Missile →
  Super Missile do SM** (o item existe: PLM `$84:EEDF`, base `$EED7` + 4·2, cabeçalho lido na ROM base: setup `$EE57`, instruções
  `$E0E3`). O Super Missile não tem trava no Phendrana do Prime (nenhum `Cordite` nos dados); no Prime ele serve na Mines.
- **Quando a Samus tem cada coisa** (rodada em que é pega → usada a partir da seguinte): mísseis 0, Morph 0, Bombas 1, Wave 1, Charge 1,
  Varia 2, Space Jump 2, Ice 3, Gravity 4, Power Bomb 5, Plasma 5. Phendrana só se alcança pelos elevadores da Magmoor (rodada 3), e é
  fria: tudo nela fica da **rodada 3** em diante. Pelas travas: as portas de onda (rodada 2+) não atrasam nada; as de gelo seguram a
  Transport Access, o Research Core e a região E até a **rodada 4**; a de plasma (Storage Cave) e os gelos de plasma, a **rodada 6**.
- **As rodadas declaradas do Tallon, da Chozo e da Magmoor não mudam**, se três regras forem seguidas: (1) Phendrana não dá atalho que
  chegue antes a sala de outra área — os dois elevadores chegam a salas da Magmoor que já são rodada 3, e Phendrana só se entra por
  eles; (2) as **2 expansões de PB** (no SM pegar uma liga as Power Bombs) nunca antes da rodada 6 — no Prime as duas já estão atrás
  de gelo de Plasma (Ice Ruins West) e de um túnel de Morph (Security Cave): plasma = rodada 6, e o túnel com bloco de Power Bomb
  (o jeito da Magma Pool e da Fiery Shores); (3) o **Super Missile** não abre nada nas outras áreas (nenhuma porta verde nem bloco de
  super no jogo: a 18c confere por varredura) — ele só soma munição e dano.
- **Rodadas previstas dos 17 itens** (decisão 3a; a filha de cada região confirma): rodada 3 — Shorelines 2, Ice Ruins East 2, Chapel 1
  (prêmio do Sheegoth), Courtyard E-tank 1, Hydra 1, Quarantine Monitor 1, Super Missile 1, Aether 2 (11); rodada 4 — Frost Cave 1,
  Gravity Chamber 2 (3); rodada 6 — PB da Ice Ruins West, E-tank da Transport Access, PB da Security Cave (3). **Nenhuma rodada nova**
  (as 7 de hoje bastam) e nenhuma rodada só de Phendrana (a guarda da 17f vale).
- Bits livres: itens a partir de `$DA` (Tallon `$A0–$B3`, Chozo `$B4–$D2`, Magmoor `$D3–$D9`, `tools/magmoor/items.py:17`; vetor
  `$7ED870`, 512 bits): Phendrana `$DA–$EA` (17). Portas vermelhas a partir de `$C2` (Magmoor `$C0`, `$C1`, `tools/magmoor/rooms.py:243`):
  Phendrana 5 (`$C2–$C6`). Bits de chefe da área nova: `$08` e `$10` (o SM usa 1, 2 e 4; a regra da 14b).
- **Porcentagem do fim** com Phendrana (decisão 3a, a fórmula de `$8B:E627`, `tools/validate.py:1194` `item_percentage`: 1 por item):
  **75%** (energia 1299, mísseis 235, power bombs 25, supers 5).

### As áreas do SM (o plano pedido pelo épico 17)

Usadas hoje: **0 Tallon, 1 Chozo, 2 Magmoor, 3 fragata** (`tools/areas.py:159, 165`; `AREAS` em `tools/areas.py:253`). A 6 (Ceres) é
usada pela cena da fuga (spec 05). Conferido agora no código vanilla (C `vendor/sm/src`):

| Área | Mapa salvo | Tela de continue | Código próprio da área | Serve a um mundo? |
|---|---|---|---|---|
| 4 (Maridia) | sim (lista até **80** bytes no lugar vanilla: `tools/frigate/mapsave.py:32` `LIST_ROOM`) | sim | o mapa de pausa rola 24 px (`sm_82.c:1811`); a lista de FX de paleta e a de tiles animados da área (`sm_89.c:99, 107`); o Botwoon lê o byte de chefe da área 4 | **sim** |
| 5 (Tourian) | sim, mas a lista vanilla cabe só **21** bytes: maior que isso vai para o `$81` livre (`$81:EF1A–FEFF`, 4070 bytes, todos `FF` na ROM construída; a regra já escrita em `mapsave.py`) | sim | a bola de fogo do Ridley (`sm_86.c:1165`): nada para nós | **sim** (com a lista no `$81`) |
| 6 (Ceres) | **não** (o save só guarda 0–5) | **não** (`kFileSelectMap_AreaIndexes = {0, 3, 5, 1, 4, 2}`, `sm_81.c:34`) | um tratador de movimento próprio da Samus (`sm_91.c:1853`), som dos PLMs em 32 quadros (`sm_84.c:1575`), o Ridley de Ceres (`sm_a6.c:2808`) | não |
| 7 (debug) | não | não | sem mapa de pausa (`sm_82.c:1556`: área ≥ 7) | não |

Sobram **duas áreas (4 e 5) para três mundos** (Phendrana 56 salas, Mines ~41 *(incerto, contar no épico dela)*, Impact Crater ~12).
A Impact Crater do Prime não tem save station nem map station e se entra pelo Artifact Temple do **Tallon**. **Recomendação técnica:
Phendrana na área 4, Mines na 5, Impact Crater dentro da área 0** (decisão 2). Lugar do mapa no 64×32: o Tallon usa 251 telas (47
bytes de lista); com a Impact Crater (~40 telas, estimativa) cabe nos 80. **Aviso**: a lista da área 0 crescer muda o lugar dos blocos
das áreas construídas depois dela no buffer do save (`mapsave.layout`: blocos em ordem de construção) — saves antigos perdem o mapa
explorado; a filha da Impact Crater precisa de um bloco extra da área 0 no fim (não pesa agora).

Cota da SRAM do mapa (`mapsave.py`: buffer de 1280 bytes, 327 vanilla): livre hoje **835**; Phendrana ~55–65 bytes (estimativa pelas
telas: Tallon 251 → 47, Chozo 202 → 41, Magmoor 156 → 30; a 18c mede, limite 80 no lugar vanilla da área 4); Mines ~40; folga grande.
Estações: a área 4 tem **20** entradas de load station (`tools/smlib/roomgraph.py:22` `STATION_COUNTS`); Phendrana usa ~5 (0 = chegada
pelo elevador norte, 1–4 = as Save Stations; a map station não precisa de estação).

### Visual: tileset, neve, água, música

- **Tilesets livres** (tabela `$8F:E7A7`, lida dos bytes; uso vanilla por `s18/scripts/tileset_survey.py`): nós usamos 00, 02 (Tallon),
  04 (fragata), 0C (Chozo), 09/0A (Magmoor). Pares que dividem metatiles e gráficos e só trocam a paleta (o truque da 09/0A na 17d):
  **00/01** (`$C1:B6F6`, `$BA:C629`; o **01 não tem nenhum estado vanilla**), 02/03 (o 03 só em 2 estados de salas órfãs), **04/05**
  (`$C1:C5CF`, `$BB:AE9E`; o 05 só em 14 estados de salas órfãs da Wrecked Ship), 0D/0E (Tourian), 07/08. Tilesets inteiros livres: 06
  (Brinstar), 07 (Brinstar vermelho), 0B (Maridia de fora), 0D/0E (Tourian). As entradas 1A, 1B e 1C (salas do Kraid, Crocomire e
  Draygon, todas órfãs desde a spec 16) podem ser reapontadas para um gráfico nosso com paleta nova.
- **Três caras** (proposta técnica, decisão 6): exterior com neve no **01** (as peças da superfície do Tallon, pintadas de branco e
  azul: as 28 salas com céu do Prime); ruínas de gelo com **os gráficos do 0C da Chozo e paleta de gelo numa entrada livre** (Ice Temple,
  Ice Ruins, Chapel, Ruined Courtyard); laboratórios dos piratas no **05** (as peças da fragata com paleta fria: Research Entrance, os
  dois Research Labs, Observatory, as torres, o Research Core). As portas de onda roxas (10d, 12f, 17d) pintadas em cada uma.
- **Neve**: o SM não tem FX de neve. Candidatos medidos numa ROM de teste na 18d (como a lava na 17d): o FX de chuva `$0A` (2 estados
  vanilla na área 0; o Tallon já usa) com o BG3 em branco, ou os esporos `$08` (4 estados vanilla na área 1), que caem devagar. Nas 23
  salas com neve no Prime.
- **Água**: o projeto só tem salas **inteiras** inundadas (fragata afundada, 07l; Reflecting Pool, `tools/chozo/rooms.py:514`
  `FLOODED`), "andadas sem a Gravity" (linha "água (specs/07l, 12l)" do validador); lagos secos (pergunta 7 do épico 12). Água parcial
  do SM (FX `$06`, 49 estados vanilla na área 4) muda a física e nunca foi medida (decisão 5).
- **Música**: as do SM ainda livres — Brinstar verde `0F/05`, Brinstar vermelho `12/05`, Tourian `1E/05`, Crateria `09/05` (usadas hoje:
  fragata `30/05`, Tallon a da Landing Site, Chozo Maridia `1B/05`, Magmoor Norfair `15/05`). A 18d escolhe pelas prévias, como a 12f e a 17d.

### Chefes (Prime → SM, regras do épico 14)

Regras que valem (épico 14, decisões 3, 7, 10–13): arena pela rotina comum em **`$84:F500`** (`tools/chozo/bosses.py:134` `ROUTINE`,
condições `KILLS`, `SLOT`, `BOSS_BIT`, `ITEM`); o prêmio aparece na hora da morte; chefe morto nunca volta (bit nosso salvo); justiça =
vence só com o Power Beam em **≤ 20 tiros** (somados numa arena) e tira **≤ 40 por toque** com o equipamento da rodada de chegada, ou a
regra 13 (mísseis da capacidade da rodada, ou ≤ 20 tiros carregados) se o Power Beam não fere; cópia de espécie em `$A0` (64 bytes,
`SpeciesCopy`); música de mini-chefe só durante a luta.

| Prime | Onde | Rodada de chegada | Dublê SM proposto | Por quê |
|---|---|---|---|---|
| **Sheegoth** + 4 Babygoths | Chapel of the Elders (P14), camada 0 | 3 (Wave, Varia, Space Jump, Charge, ~180 mísseis) | **DESSGEEGA grande** (`$DA3F`: 800 de vida, toque 160) **copiado** com toque 40 e vida para ≤ 20 tiros, cores de gelo das texturas do Prime; os Babygoths = **Sidehopper pequeno** `$D93F` (60/20), 2–3; arena com cota de mortes, o prêmio (míssil, decisão 3a) aparece | o "Sidehopper grande e duro" do SM, diferente da cópia do SIDE do Plated Beetle (14a); só sprites, cabe em qualquer tileset |
| **Thardus** | Quarantine Cave (P24), camada 3 | 3 | **Bomb Torizo** (`$A0:EEFF`, 800 de vida) **copiado** (vida e toque pela regra, cores de pedra e gelo): a estátua que acorda, como o Thardus que se monta de pedras; a porta tranca até a vitória | o único chefe do SM que "nasce" de uma estátua; custa os **7 pontos do código que leem a área** (`$AA:C895` e mais 6, épico 14 "Torizo fora da área 0") e a VRAM inteira de inimigos da sala (`$2000`: só ele na arena) |
| Elite Pirates, Ice Sheegoths do 2º passe, Metroids dos tubos, Ridley | camadas de evento | — | **fora** (regra da camada 0) | como os Flying Pirates da Magmoor e os Chozo Ghosts |

Alternativa barata ao Torizo para o Thardus (decisão 4b): arena de colmeias/rochas com a rotina da 14b (o jeito do Incinerator Drone).
Os **Metroids da camada 0** (Research Core 3, Aether 1) são inimigos comuns, não chefes: a 18g propõe uma cópia do METROID (`$DD7F`:
500/120, prende e suga) com toque ≤ 20 ou nenhum (decisão 7).

### Espaço por banco (medido agora)

Livres na ROM construída (`s18/free.out`, maior faixa de `$FF`; `$8F` recuperado pela linha do validador):

| Banco | Livre hoje | Phendrana pede (56 salas, 59 ligações) | Cabe? |
|---|---|---|---|
| `$8F` (cabeçalhos, estados, listas) | **1** na faixa principal; **695** nas recuperadas (3122 de 3817 usados) | ~3000 (≈ 53 por sala: a região C da Magmoor usou 640 para 12) + ~60 por arena | **não**: precisa da faixa das demos (18a) |
| `$83` (portas, FX) | 16 606 (`$83:BB96` em diante) | ~1700 (118 entradas de porta + FX de 56 salas) | sim |
| `$A1` (populações) | 1765 | ~1000 (~45 inimigos + 2 arenas) | sim, mas deixa ~750 para a Mines: recuperar `$A1` órfão no épico dela (27 363 bytes só de órfãs; a maior faixa `$A1:AD09–CCD3`, 8139) |
| `$B4` (enemy sets) | 1990 | ~800 | sim |
| `$84` (PLMs) | 2672 em pedaços (`$84:F000–FFFF`; a faixa do fim acabou) | entradas novas da tabela das arenas e pintura das portas nos tilesets novos (~200) | sim |
| `$A0` (espécies) | 1857 | 4–5 cópias (Sheegoth, Babygoth?, Torizo, Atomic com toque menor, Metroid?) ≈ 320 | sim |
| nível / fixo | 477 711 / 477 501 | ~20 KB de nível; 3 paletas e tabelas de metatiles pintadas (~8 KB) | sim |
| `$81` | 4070 (`$81:EF1A–FEFF`) | nada (a lista da área 4 cabe no lugar vanilla) | — (a Mines vai usar) |
| SRAM do mapa | 835 de 1280 | ~55–65 | sim |

**Faixas órfãs do `$8F`** fora do `RECLAIMED_8F` (`s18/orphans.out`; 19 519 bytes em 32 faixas), as maiores sem cabeçalho comparado
pelo código (`build.py:159` `ROOM_PTR_COMPARED`):

| Faixa | Bytes | Donas | Demo? |
|---|---|---|---|
| `$8F:8000–8ED3` | **3796** | 149 salas das áreas 0–2 (scroll e PLMs) | sim (17 salas das demos) |
| `$8F:C215–C8C6` | 1714 | 97 salas das áreas 3–6 | sim |
| `$8F:AD5C–B218` | 1213 | 26 da Norfair | sim |
| `$8F:A6A1–A97A` | 730 | | — |
| `$8F:CAAE–CCC7` | 538 | | — |

**Avaliação**: com 695 + **3796** (`$8F:8000–8ED3`, a faixa que a 17a guardou para Phendrana/Mines) ficam **4491 para ~3100**: folga de
~1400. As demos estão **desligadas desde a spec 16** (`$8B:9F2C`, `tools/frigate/title.py:318` `check_demos_off`, decisão do usuário):
usar dados de demo é seguro enquanto elas ficarem desligadas; a 18a troca a regra "nada de demo" do `check_reclaimed`
(`tools/validate.py:2463`) por "demos desligadas, provado por `check_demos_off`". Para a Mines sobram `$8F:C215–C8C6`, `$8F:AD5C–B218`,
`$8F:A6A1–A97A` (3657, todas sem cabeçalho comparado).

### Testes: tempo por comando

Hoje a bateria roda em dois comandos (`tests/run_tests.py:6575` `TEST_GROUP_B`, `:6578` `CHAIN_GROUP`): **grupo A ~3 min 20 s** (com a
parte 1 da cadeia, o piso dele) e **grupo B ~4 min 43 s** (as partes 2 e 3, que carregam o estado salvo pela 1), perto do limite de
~6 min de uma execução da ferramenta. Phendrana acrescenta ~10–14 testes no emulador (rota/itens/save por região, inimigos, 2 chefes,
2 elevadores) e ~2–3 min de cadeia. **Não cabem no grupo B.** Plano: um **grupo C** (prefixo `phendrana_`, os elevadores novos e as
partes novas da cadeia), criado na 18e (a primeira filha com teste de Phendrana no emulador); a cadeia (`CHAIN_PARTS`,
`tests/run_tests.py:5910`) em 4–5 partes ligadas por estado salvo, rodadas na ordem A → B → C; se o C passar de ~5 min medido, um
grupo D pela mesma regra. Cada grupo ≤ ~5 min sozinho.

## Mudança proposta

### Decisões técnicas deste épico (minhas, justificadas acima; o usuário pode vetar)

1. **Uma sala do Prime = uma sala do SM**, as 59 ligações; chaves com prefixo `phendrana_`; `tools/phendrana/` no molde de
   `tools/magmoor/` (`rooms.py`, `layouts.py`, `items.py`, `enemies.py`, `bosses` dentro de `tools/chozo/bosses.py` como as arenas).
2. **Sem frio** (fiel: nenhuma `Area Damage` em Phendrana), sem patch de calor; `HEAT_BITS` da área 4 vazio.
3. **Travas do Prime → mecanismos que já existem**: escudo de míssil → porta vermelha; onda/gelo/plasma → portas de feixe (a de plasma
   da Storage Cave é de plasma de verdade: a Samus entra e sai com o Plasma); **gelo que só o Plasma derrete** (o item da Ice Ruins West
   e o da Transport Access) → nicho fechado por **porta de plasma**; Spider/Boost/Grapple → borda de Space Jump; bomb slot → túnel com
   bloco de bomba; túnel de Morph → túnel de Morph (com bloco de Power Bomb onde guarda a expansão de PB: Security Cave); painéis de
   Wave, estalactites, vidro dos tubos → enfeite (as portas já pedem o Wave).
4. **Elevadores de verdade**: Magmoor P13 ↔ Phendrana P0 e Magmoor P27 ↔ Phendrana P29 (`ELEVATORS` +2; os lados da Magmoor ganham
   `ride=True`, como a 17e fez com a Chozo P24 e o Tallon P23); a Mines West continua de enfeite.
5. **Inimigos da camada 0** (07i/12h/17g), ≤ 1 por tela, justos em toda rodada: Parasite → Zeela (padrão aceito); AtomicAlpha/Beta → o
   **ATOMIC** do SM (`$E9FF`, 250/40: cópia com toque 20); Ripper → **RIPPER** (`$D47F`, 200/5); Babygoth → Sidehopper pequeno
   (`$D93F`); Beetle → o da Chozo (12h); JellyZap, Drone, WallCrawlerSwarm, SpankWeed e as camadas de evento fora ou escolhidos na 18g;
   Metroids pela decisão 7.
6. **Rodadas**: o passeio anda as quatro áreas pelos elevadores (`validate.world_rounds`); critério duro: **as rodadas declaradas de cada
   item e sala do Tallon, da Chozo e da Magmoor não mudam**.
7. **`$8F`**: a faixa das demos `$8F:8000–8ED3` (18a).
8. **Testes**: grupo C (18e) e a cadeia em mais partes (18n).

### Filhas (toolchain e dados primeiro, regiões por último)

| # | Spec | Entrega | Esforço | Testes |
|---|---|---|---|---|
| 18a | Espaço do `$8F` para Phendrana (a faixa das demos) | `build.RECLAIMED_8F` ganha `$8F:8000–8ED3` (3796 bytes, só salas órfãs, nenhum cabeçalho comparado); `check_reclaimed` aceita dado de demo **só** com `check_demos_off` passando; ROM igual | 0,5 d | validate: `check_reclaimed` com a faixa nova; mutações no scratchpad (demos religadas → erro; estrutura nossa num cabeçalho comparado; faixa sobreposta) |
| 18b | Lugar de Phendrana na área 4 | `areas.PHENDRANA_AREA = 4`, `VANILLA_PAUSE[4]` lido dos bytes, `check_vanilla_pause` cobre a 4, `check_phendrana_slot` (área livre, SRAM, lista ≤ 80, estações ≤ 20), a lista de FX de paleta e a de tiles animados da área 4 conferidas (nada de Maridia nas nossas salas), `HEAT_BITS` da 4 vazio; o plano das áreas (decisão 2) escrito em `mapsave.py`/`areas.py` (5 = Mines, a Impact Crater na 0); ROM igual | 0,5–1 d | validate: linha "phendrana (specs/18b)"; mutações (área ocupada, byte vanilla errado, FX de Maridia ligado) |
| 18c | Grafo, mapa e travas do Prime | `tools/phendrana/rooms.py`: `TABLE` (56, tamanho pela regra), `LINKS` (59), `REGIONS` A–E, `DOCK_LOCKS` (key 71 com a cor, missile 5, morph 4), `KEY_BEAM`, `FEATURES`, `SNOW_ROOMS` (23), `WATER_ROOMS` (10), `PLASMA_ICE`; `research/prime_phendrana_locks.json` pelo `dump_prime_locks.py` (com o campo novo `env_fx`); disposição no 64×32 por busca; `check_phendrana`; varredura "nenhuma porta verde / bloco de super no jogo"; prévia `--mapa-phendrana`; nenhuma sala na ROM | 2 d | validate: tabela × Prime, mapa sem sobreposição, portas encostadas, ligação sem volta = erro (mutação), SRAM ≤ 80; prévia olhada |
| 18d | Estilo do gelo (3 caras), neve e cor das portas | `tools/smlib/ice.py`: neve no 01, ruínas de gelo (gráficos do 0C, paleta nova numa entrada livre), laboratório no 05; portas de onda/gelo/plasma pintadas; **neve medida numa ROM de teste** (`build.py --teste-18d`: FX `$0A`/`$08` com o BG3 branco); fundo e música pelas prévias | 2,5–3 d | validate: `ice.check`, cores/metatiles na ROM, nenhuma sala fora de Phendrana usa as entradas novas; emulador: `neve_medida`, `porta_de_onda_gelo`; prévias |
| 18e | Elevadores de verdade (Magmoor ↔ Phendrana) e o grupo C | as salas P0 e P29 (becos), os lados P13 e P27 da Magmoor com `ride=True`, `ELEVATORS` +2, `AreaDef PHENDRANA`, mapa/minimapa "PHENDRANA", "PHENDRANA / DRIFTS" no continue; `TEST_GROUP_C` | 2 d | validate: `check_elevators(_in_rom)` com 7 pares, rodadas dos lados (3 e 3); emulador: `elevador_phendrana_norte`, `elevador_phendrana_sul` (ida e volta, `$079F` = 4); save/game over/continue com as quatro áreas |
| 18f | Região A (norte) | as 12 salas; Save Station B = estação 1 da área 4; 4 mísseis (Shorelines, Ice Ruins East; as bordas de Space Jump no lugar dos trilhos de Spider) e o lugar do Wave (míssil, aparece na 18h); o bomb slot do Ice Temple = túnel com bloco de bomba; neve nas 8 salas do Prime | 2,5 d | validate: alcance a pé, rodadas (as das outras áreas iguais); emulador: `phendrana_regiao_a_rota`, `phendrana_regiao_a_itens`, `phendrana_save_station_b` |
| 18g | Inimigos | camada 0 do Prime na região A (e a tabela das regiões B–E registrada, como a 12h e a 17g), as espécies da decisão técnica 5, cópias em `$A0`, justiça em toda sala | 1,5–2 d | validate: `check_layer0_enemies` de Phendrana; emulador: `phendrana_inimigos_vivos`, auditoria de entrada (spec 15) nas salas novas |
| 18h | Sheegoth (arena da Chapel of the Elders) | cópia do DESSGEEGA grande + Sidehoppers pequenos, cota de mortes, bit `$08` da área 4, o míssil aparece; justiça medida | 2 d | validate: `check_bosses`/`check_arenas` com a arena nova; emulador: `phendrana_sheegoth` (a luta de verdade, rodada 3) |
| 18i | Região B (Ice Ruins West, Courtyard, Hydra) | as 12 salas; Save Station A (estação 2), as portas vermelhas da Ice Ruins West → Canyon Entryway (`$C2`) e da Save Station A (`$C3`), Map Station; **a PB da Ice Ruins West num nicho de porta de plasma** (rodada 6), o E-tank do Courtyard (bomb slot → túnel), o míssil da Hydra; o lugar da Boost (decisão 3) | 3 d | validate: rodadas, `check_bombed_items`, porta de plasma do nicho; emulador: `phendrana_regiao_b_rota`, `_itens`, `phendrana_save_station_a`, `phendrana_map_station` |
| 18j | Região C (quarentena e o elevador sul) | as 6 salas (as duas Quarantine Tunnels grandes); a P29 abre (porta de gelo para a Transport Access); o míssil da Monitor (túnel de Morph); **o E-tank da Transport Access num nicho de porta de plasma** (rodada 6); o lugar da Spider | 2,5–3 d | validate: `check_phendrana_locks_mapped` (toda trava do Prime na sua ligação com o seu mecanismo, como 12j/17i), rodadas; emulador: `phendrana_regiao_c_rota`, `_itens` |
| 18k | Thardus (arena da Quarantine Cave) | cópia do Bomb Torizo (os 7 pontos por área, a VRAM da sala), a porta tranca, bit `$10`; o prêmio pela decisão 3 | 2–3 d | validate: `check_arenas` com o Torizo; emulador: `phendrana_thardus` |
| 18l | Região D (observatório, torres, laboratórios) | as 12 salas; **o Super Missile** no Observatory (item novo: `GRANTS`, a munição na porcentagem, a varredura de portas verdes); Save Station D (estação 3, porta vermelha `$C4`), as portas vermelhas da West Tower Entrance ↔ West Tower (`$C5`, `$C6`); E-tank e míssil da Aether; o lugar do Thermal; a porta de gelo do Research Core | 3 d | validate: rodadas, item novo; emulador: `phendrana_regiao_d_rota`, `_itens` (o Super Missile pego, munição 5), `phendrana_save_station_d` |
| 18m | Região E (sul fundo, a água) | as 14 salas; Save Station C (estação 4); Gravity Chamber (água pela decisão 5; o míssil e o lugar da Gravity); o míssil da Frost Cave; a Storage Cave atrás da porta de plasma (vazia); a PB da Security Cave atrás de bloco de Power Bomb (rodada 6) | 3 d | validate: rodadas, regra da água, `check_breakables`; emulador: `phendrana_regiao_e_rota`, `_itens`, `phendrana_save_station_c`, `phendrana_agua` |
| 18n | Rodadas das quatro áreas e a cadeia completa | `check_world_rounds` com Phendrana (75 itens; as rodadas das outras áreas iguais; 75%), linha "elevadores a partir da rodada" com os 2 novos, `check_epic_phendrana`; a cadeia estendida pelos 2 elevadores (os chefes de Phendrana mortos de verdade ou por atalho anotado, decisão 9 do épico 14), em 4–5 partes A → B → C | 2,5 d | validate: linha "rodadas (specs/18n)"; emulador: a cadeia inteira, cada grupo ≤ ~5 min; verificação inteira |

```
18a ─┐
18b ─┼─> 18c ─┬─> 18e ─> 18f ─> 18g ─> 18h ─> 18i ─> 18j ─> 18k ─> 18l ─> 18m ─> 18n
     └─> 18d ─┘
```

18a, 18b e 18c não mudam a ROM e servem a qualquer resposta do usuário. A 18d só muda a ROM de teste. Da 18e em diante, cada filha
`verificada` antes da próxima. Os chefes vêm logo depois da região deles (o Sheegoth na região A, o Thardus na C), não num épico à parte
como na Chozo: a arena já existe (14b) e a luta é testada com a sala pronta.

## Critérios de aceite (do épico)

1. 18a, 18b e 18c `verificada` com a ROM igual (sha1 do `.ips` igual ao de antes, dois builds; linhas do Tallon, da Chozo, da Magmoor e
   das rodadas iguais; testes iguais).
2. Cada filha `verificada` com validate + build + testes (cada grupo ≤ ~6 min por comando); `check_orphans` prova que nenhum caminho
   entra em sala vanilla também pela área 4; `check_reclaimed` prova o uso da faixa nova com as demos desligadas.
3. **As rodadas declaradas do Tallon, da Chozo e da Magmoor iguais** em toda filha (salas e itens; o validador compara; desvio = parar e
   perguntar).
4. Definição de pronto: as salas da decisão 1 ligadas como no Prime, os 2 elevadores nos dois sentidos, Phendrana jogável a pé com os
   itens da decisão 3, os chefes da decisão 4 com a luta de verdade, sem softlock (validador nas quatro áreas + cadeia no emulador),
   mapa de pausa/minimapa "PHENDRANA" salvos, as 4 save stations e a map station, "PHENDRANA / DRIFTS" no continue.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` (18a), `check_phendrana_slot` + `check_vanilla_pause` (18b), `check_phendrana` (18c), `ice.check` (18d), elevadores (18e), alcance/rodadas/neve/água por região (18f, 18i, 18j, 18l, 18m), inimigos (18g), arenas (18h, 18k), `check_phendrana_locks_mapped` (18j), `check_world_rounds` + `check_epic_phendrana` (18n) | +10–12 checagens |
| scratchpad | mutações de cada checagem nova (como 17a/17b/17c) | ~30 |
| run_tests.py (grupo C) | `neve_medida`, `porta_de_onda_gelo` (18d); 2 de elevador (18e); rota/itens/save por região (18f, 18i, 18j, 18l, 18m: ~14); inimigos e entradas (18g); 2 chefes (18h, 18k); `phendrana_agua` (18m); as partes novas da cadeia (18n) | +20–24 |
| imagem | prévias do estilo, da neve e do mapa; fotos do emulador das cinco regiões e dos dois chefes | — |

## Riscos e reversão

- **Tamanho**: 302 telas no mapa 64×32 da área 4 (o Tallon cabe com 251). Se a busca da 18c não fechar, as duas Quarantine Tunnels
  (24 telas cada pela regra) ficam limitadas a 6×2, anotado como desvio.
- **`$8F`**: 4491 para ~3100 (folga ~1400). Religar as demos depois quebraria (o validador pega: `check_reclaimed` pede
  `check_demos_off`).
- **Rodadas das outras áreas** podem mudar por um atalho não previsto (as expansões de PB, o Super Missile, um elevador): o validador
  pega; a regra é mudar Phendrana, não as outras.
- **Torizo fora da área 0** (18k): 7 pontos de código por área e a VRAM inteira; se não fechar, a alternativa da decisão 4b (arena de
  colmeias, sem código novo).
- **Neve**: se nenhum FX recolorido parecer neve, as salas ficam só com a cor (sem partículas).
- **Tempo dos testes**: grupo C novo desde a 18e; se a cadeia passar de ~5 min num grupo, mais uma parte (grupo D).
- **Super Missile**: item novo no jogo; a munição e o HUD de supers aparecem pela primeira vez (conferir na 18l que o HUD tem lugar e que
  nenhum inimigo/chefe já feito muda de comportamento com supers).
- **Save de SRAM** (spec 11, B7): um save vanilla de Maridia cairia em dado sobrescrito; documentado, como na 12a/17a.
- Reversão: tudo vem de `tools/`; 18a–18c não mudam a ROM (tirar as faixas, constantes e checagens basta).

## Fora de escopo

- Phazon Mines e Impact Crater (só o plano das áreas, decisão 2); o elevador da Mines West continua de enfeite.
- Speed Booster, Grapple Beam e outras habilidades novas do SM — só se o usuário escolher (decisão 3b).
- Artefatos, Thermal Visor, Scan Visor, combos (o Super Missile do SM entra como item do SM, não como combo do charge), camadas de evento
  (Elite Pirates, Ice Troopers, Metroids dos tubos, o voo do Ridley, o 2º passe), estalactites e painéis de Wave como travas.
- Mexer no Tallon, na Chozo e na Magmoor além dos dois lados dos elevadores (`ride=True` nas salas P13 e P27 da Magmoor).

## Decisões do usuário (perguntas)

1. **Tamanho**: (a) **as 56 salas**, por região (A norte, B ruínas e o primeiro laboratório, C quarentena, D torres, E sul fundo)
   (**recomendado**: é o tamanho do Prime, e as regiões C–E ligam os dois elevadores); (b) só A + B (24 salas, ~117 telas: o norte
   jogável com o Sheegoth; o resto noutra etapa, o elevador sul continua de enfeite).
2. **Plano das áreas do SM** (sobram a 4 e a 5 para três mundos; a 6 e a 7 não servem: sem mapa salvo nem tela de continue):
   (a) **Phendrana na área 4, Phazon Mines na 5 (a lista do mapa vai para o `$81`), Impact Crater dentro da área 0 com o Tallon**
   (**recomendado**: no Prime a Impact Crater se entra pelo Artifact Temple do Tallon e não tem save nem mapa; é pequena);
   (b) Phendrana na 4, Impact Crater na 5, Mines dividindo a área 2 com a Magmoor (a Mines é grande, ~41 salas: o mapa da Norfair
   ficaria cheio); (c) Phendrana na 5 e Mines na 4 (Phendrana precisaria da lista no `$81` desde já).
3. **Itens**: (a) **como na Chozo e na Magmoor** — 9 mísseis, 3 E-tanks, 2 expansões de PB (rodada 6), **míssil no lugar do Wave e da
   Gravity** (já estão no Tallon), **o Super Missile do SM no Observatory** (é o mesmo item), nada no lugar da Boost, da Spider, do
   Thermal e dos artefatos: **17 itens, 75% no fim** (**recomendado**: segue a regra das duas áreas anteriores e não mexe nas rodadas
   delas); (b) a + **Speed Booster no lugar da Boost Ball** e **Grapple Beam no lugar da Spider Ball** (o prêmio do Thardus; os 6 pontos
   de gancho do Prime viram blocos de gancho de verdade) — Phendrana ganha habilidades novas, mas +4–6 dias e física nova no modelo de
   alcance; (c) a, mas um míssil no lugar do Super Missile (nada novo no jogo).
4. **Chefes**: (a) **os dois** — Sheegoth = Sidehopper grande do tipo Dessgeega (cores de gelo) com 2–3 Sidehoppers pequenos na Chapel,
   o prêmio aparece quando morrem; Thardus = Bomb Torizo (a estátua que acorda, cores de pedra) na Quarantine Cave, a porta tranca até a
   vitória (**recomendado**); (b) os dois, mas o Thardus como arena de colmeias/rochas (mais barato, menos parecido); (c) nenhum agora
   (um épico de chefes depois, como o 14).
5. **Água e frio**: (a) **sem frio** (o Prime não machuca no frio) e água só onde a sala é funda — a **Gravity Chamber inteira inundada**
   (como a Reflecting Pool); os lagos das outras 9 salas secos (**recomendado**: fiel no que pesa e sem física nova); (b) a + água
   parcial de verdade do SM nos lagos (Frost Cave, Hunter Cave…), medida no emulador como a lava (+2 d); (c) frio que machuca sem a
   Varia (não é do Prime).
6. **Visual**: (a) **três caras** — exterior com neve, ruínas Chozo de gelo, laboratórios dos piratas — e neve caindo nas 23 salas onde
   neva no Prime (**recomendado**); (b) uma cara só para tudo (mais rápido, ~1 dia a menos).
7. **Metroids** (4 na camada 0 do Prime, Research Core e Aether): (a) **o Metroid do SM enfraquecido** (cópia com vida e toque pela regra
   de justiça; o gelo congela) (**recomendado**: são a marca dos laboratórios de Phendrana); (b) fora (como as camadas de evento).

### Respostas (03/11/2026)

1. **(a) as 56 salas**, região por região (A–E).
2. *Padrão aceito, a confirmar*: **(a)** Phendrana na área 4, Phazon Mines na 5, Impact Crater dentro da área 0 com o Tallon.
3. **(a) com o Super Missile de verdade do SM**: 9 mísseis, 3 E-tanks, 2 expansões de PB (nunca antes da rodada 6), **o Super Missile
   do SM no lugar do Super Missile do Prime** (Observatory), míssil no lugar do Wave e da Gravity, nada no lugar da Boost, da Spider, do
   Thermal e dos artefatos. **17 itens, 75% no fim.**
4. **(a) os dois chefes**: Sheegoth = cópia **mais dura** do Dessgeega grande, em cores de gelo, com 2–3 Sidehoppers pequenos, arena na
   Chapel of the Elders; Thardus = cópia do Bomb Torizo em cores de pedra na Quarantine Cave, portas trancadas até ele morrer; os tetos
   de justiça do épico 14 valem (≤ 20 tiros do Power Beam somados na arena, ≤ 40 por toque com o equipamento da rodada de chegada, ou a
   regra 13).
5. **(a)**: sem frio; só a **Gravity Chamber** inundada (sala inteira, como a Reflecting Pool); os outros lagos secos.
6. *Padrão aceito, a confirmar*: **(a)** três caras (exterior com neve, ruínas Chozo de gelo, laboratórios dos piratas) e neve caindo
   nas salas onde neva no Prime.
7. *Padrão aceito, a confirmar*: **(a)** o Metroid do SM enfraquecido nos laboratórios, justo pelas regras de sempre.

## Desvios (preenchido na implementação)

- 18a–18c: ver os Desvios de cada filha. Achado da 18c: os dados têm **20 travas de evento** e **72 docas key** (uma delas,
  Canyon Entryway → Ice Ruins West, abre com qualquer feixe), não 71; a tabela do épico acima não listava as de evento.
- 18d: os laboratórios ficam na entrada `$1B` (não no `$05`: uma sala de demo usa o `$05`); a neve = os esporos do SM; a ROM de teste da
  18d teve uma área 4 própria, que a 18e pendurou na área de Phendrana. 18e: os elevadores **descem** em Phendrana (a Magmoor já tinha o
  poço saindo pelo teto); regra nova `PHENDRANA_MIN_MAP_X` (a rolagem do mapa da área 4, medida). Ver os Desvios das filhas.
- 18f: região A com **11 salas novas** (a tabela do épico conta 12 com a P0, já da 18e); neve em **7** salas da região (a linha da
  18f do épico dizia 8: a Ice Ruins West, que neva, é da região B); **3 testes** (`phendrana_regiao_a_rota` com os 4 mísseis,
  `phendrana_regiao_a_templo`, `phendrana_save_station_b`) em vez de `_rota`/`_itens`/`_save_station_b`; o míssil da Chapel (lugar do
  Wave) fica para a 18h (prêmio da arena), como o épico já dizia; a linha das rodadas (12m, 17j) continua das três áreas até a 18n.
  Ver os Desvios da filha.
- 18g: a cópia do ATOMIC (`$A0:F8BF`, vida 100, toque 20) vai até a Samus atravessando paredes (o orbe vanilla): regra nova de deriva
  longe das portas no validador; a **Ice Ruins East tem 4 Parasites na camada 0** (a lista "Inimigos" acima não a tinha); contas abaixo
  do Prime (Shorelines 3 de 4, Ice Ruins East 2 de 4); a Chapel fica vazia até a arena da 18h (`ARENA_LATER`); o Metroid, o Ripper e os
  outros tipos de B–E ficam como propostas (`PROPOSED_LATER`) para as filhas das regiões. Ver os Desvios da filha.
- 18h: o Sheegoth é o **Dessgeega inteiro** (vida 800 e as vulnerabilidades dele: o feixe sem carga não fere), toque 40, cores de gelo das
  texturas do Prime: a "cópia mais dura" da decisão 4 vencida pela regra 13 do épico 14 (10 mísseis para a arena, capacidade 85 na rodada
  3; ou 16 tiros carregados), não por "vida para ≤ 20 tiros" do Power Beam (a linha da tabela de chefes acima); **2 Babygoths** (Prime 4)
  marcados como da arena (somem no estado morto); a porta da Chapel tranca (o `Actor Door Lock` do Prime: porta cinza de cota de mortes
  no estado vivo, a de onda no morto: `DoorLink.dead_lock`); o míssil no meio do altar (bit `$DE`, rodada 3); bit `$08` da área 4; as
  arenas, os bits e a linha do épico no validador valem para qualquer área (`epic_area_bosses`, linha "chefes de Phendrana (specs/18h)");
  `Allocator.next_at` (o cabeçalho condicional na faixa das demos); `phendrana_regiao_a_templo` entra na Chapel morta por atalho anotado.
  Ver os Desvios da filha.
- 18i: a expansão de PB da Ice Ruins West num nicho fechado por uma **tampa de plasma dentro da sala** (`RoomDef.caps`: mecanismo novo;
  o nível precisa dos blocos de tampa de porta, medido); a ligação Research Entrance ↔ Hydra Lab Entryway pediu uma **porta de onda
  vertical** nova (roxa, só na tabela do tileset 4, em `$84:FE00`: as regiões C e E têm mais 3 ligações assim e precisam pintá-la nas
  outras caras); contas abaixo do Prime (Courtyard Entryway 1 zoomer de 2, Canyon 2 Zeelas de 7); o E-tank do Courtyard pelo bomb slot
  (túnel com bloco de bomba); `$8F`: 3194 bytes livres na faixa das demos depois da região B. Ver os Desvios da filha.
- 18j: região C com **5 salas novas** e a P29 aberta (o caminho até a R0 no alto); a porta de Morph Quarantine Cave ↔ Monitor = túnel
  de Morph dos dois lados, **sem a borda de Space Jump do gancho** do Prime (a L1 da caverna fica no chão da tela de baixo pelo mapa da
  18c); a porta de onda vertical da North Quarantine Tunnel pedia a **pintura na tabela da neve** (feita: `VERTICAL_WAVE_TILESETS`; as
  ruínas de gelo ainda sem ela, a região E decide); regra a mais no validador: a porta de Morph do Prime fecha algo na própria sala
  (a mutação V7 mostrou o buraco); a NQT desce pelo meio e os 2 orbes dela ficam fora da câmera; a Quarantine Cave fica vazia e plana
  para o Thardus (18k); `$8F`: **2892 bytes livres** na faixa das demos depois da região C (+303). Ver os Desvios da filha.
- 18k: o Thardus = cópia do Bomb Torizo (`$A0:F93F`) com **vida 400** (20 tiros do Power Beam: o Torizo é ferido pelo feixe) e o toque
  dele (8); o código dos Torizos **corrigido no lugar** (as 7 leituras da área viram 0, a bruma da sala vanilla tirada, a posição da
  tabela, as paletas e o pulso do peito em cores de pedra e neve das texturas do Prime); acorda quando a sala carrega (sem o PLM da
  estátua); a condição é o bit `$04` que a morte do Torizo liga (a morte não conta na cota de mortes, medido), as portas L0/R0 cinza de
  **tipo 2** só no estado vivo e de onda no morto (`build.arena_door_alive_cap`); bit da arena `$10`; **sem prêmio** (decisão 3: nada no
  lugar da Spider Ball); a música da sala vanilla do Torizo (`24/03`), não a `2A/05`; `PRIME_BOSS_LAYERS` (o Thardus é da camada 3);
  `phendrana_regiao_c_rota` cruza a caverna morta por atalho anotado; `$8F`: **2846 bytes livres** na faixa das demos (+46). Ver os
  Desvios da filha.
- 18l: região D com **12 salas novas** e a R0 da Hydra aberta; o **Super Missile do SM** na câmara do projetor do Observatory atrás de
  bloco de bomba (bit `$E4`, `needs` Morph + Bombas, rodada 3; `GRANTS` = `SUPER`, que nenhuma trava pede); a porta vermelha WTE ↔ West
  Tower com **um bit para os dois lados** (`$C5`, a regra da 12i que `check_gates` exige): os escudos do épico ficam em `$C2–$C5` e o
  `$C6` livre; os **Metroids** = cópia do Metroid do SM com vida 100, **a IA de toque comum** (20 por toque, sem agarrar nem drenar: o
  agarrar do Prime/SM não cabe no teto de 20 por toque), uma IA de tiro própria (6 bytes no `$A3`: o ramo "congelado" do Metroid_Shot
  para todo tiro) e uma tabela própria (os feixes ×1, o gelo só congela); `SpeciesCopy` ganha `touch`/`shot`/`vulnerability`; regra
  nova de validador para o Metroid (voa a 3 px por quadro só na câmera: fora da câmera de toda porta, `chaser_problems`); contas abaixo
  do Prime na Aether Lab Entryway (1 orbe de 3: a sala tem 1 tela); a Control Tower na cara de neve, a Pike Access na cara de neve sem
  neve caindo; `$8F`: **2146 bytes livres** na faixa das demos depois da região D (+700). Ver os Desvios da filha.
- 18m: região E com **14 salas novas** (Phendrana inteira: 56 salas, 17 itens = 11 mísseis (os 9 Missile Expansions + os lugares do
  Wave e da Gravity), 3 E-tanks, 2 expansões de PB, o Super Missile); a **Gravity Chamber inundada** (`rooms.FLOODED`, a regra
  `EPIC_PHENDRANA_FLOODED` no validador) andada sem a Gravity por uma escada de rocha de degraus de 3 linhas (um zigue-zague de 3 linhas
  não deixa espaço para o pulo debaixo d'água); o míssil do lugar da Gravity no fundo na **rodada 4** e o da borda (o gancho do Prime =
  borda de Space Jump, que debaixo d'água pede a Gravity) na **rodada 5**, não os "2 na rodada 4" das rodadas previstas; a porta de Morph
  Edge ↔ Security Cave com **bloco de Power Bomb dos dois lados** (a Warrior Shrine); tudo na cara de neve (a porta de onda vertical
  nas ruínas não foi necessária); o **Ripper fora** (imune a todo feixe, como o do Prime), as Jelly Zaps, o Drone, os Flying Pirates e as
  Spank Weeds fora (`PROPOSED_LATER` vazio); regra nova (mutação V11): a porta de Morph do Prime fecha algo na sala sem cada item da
  trava; testes `phendrana_regiao_e_rota` e `phendrana_regiao_e_agua` (a caminhada dividida em duas) e `phendrana_save_station_c`;
  `$8F`: **1282 bytes livres** na faixa das demos (+864). Ver os Desvios da filha.
- 18n: `check_world_rounds` com as quatro áreas ("75 itens em 7 rodadas … 75%"), `check_epic_phendrana` (a linha do épico inteiro);
  a cadeia completa em **4 partes** (1 no grupo A, 2 no B, 3 e 4 no C; o épico previa 4–5 e um grupo D se o C passasse de ~5 min: o C
  ficou em 5 min 30 s, abaixo dos ~6 min, e o grupo D fica como decisão do usuário); os dois chefes **vencidos de verdade** na cadeia
  (lutas buscadas da entrada da própria cadeia), não por atalho; uma visita a Phendrana por rodada (3, 4, 5, 6), a rodada 3 do Tallon (o
  Ice) depois de Phendrana; a **tela do fim do SM** com "YOUR RATE FOR COLLECTING ITEMS IS 75%" (o evento `$0E` por RAM, o único
  atalho novo; pedido do orquestrador, fora do plano). Ver os Desvios da filha.

## Verificação do épico (04/11/2026, 18n)

Conferido no fim da 18n, contra os critérios de aceite do épico e as decisões do usuário:

| Critério | Onde | Resultado |
|---|---|---|
| 1. 18a, 18b, 18c com a ROM igual | [18a](18a-espaco-8f-das-demos.md), [18b](18b-area-da-phendrana.md), [18c](18c-grafo-e-mapa-phendrana.md) | sim (ROM igual, linhas e testes iguais nas três) |
| 2. Cada filha verificada (validate + build + testes, cada grupo ≤ ~6 min); nenhum caminho entra em sala vanilla pela área 4; a faixa das demos só com elas desligadas | as 14 filhas; `check_orphans`, `check_reclaimed` | sim (validate 0 problemas em todas; 262 órfãs; na 18n A 3 min 0 s, B 3 min 20 s, C 5 min 30 s) |
| 3. Rodadas declaradas do Tallon, da Chozo e da Magmoor iguais em toda filha | linha "tallon (…)" e linha "rodadas (specs/12m, 17j, 18n)" | sim: "44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"; itens por rodada Tallon + Chozo + Magmoor 0: 2 + 1 + 0; 1: 4 + 7 + 0; 2: 1 + 11 + 0; 3: 2 + 8 + 4; 4: 2 + 1 + 1; 5: 7 + 0 + 0; 6: 2 + 3 + 2 (iguais à 17j); elevadores chozo_west 0, chozo_east 4, chozo_south 5, magmoor_north 1, magmoor_east 1 |
| 4a. As 56 salas ligadas como no Prime | `check_phendrana` (tabela, 59 ligações), `check_epic_phendrana` | sim |
| 4b. Os 2 elevadores nos dois sentidos | `check_elevators(_in_rom)`; `elevador_phendrana_norte`, `elevador_phendrana_sul`; a cadeia (P13 ↑ 2, P27 ↑ 2, P29 ↓ 4) | sim |
| 4c. Phendrana a pé com os itens da decisão 3 | `check_phendrana_rounds`, `check_world_rounds`, `check_epic_phendrana`; as caminhadas das regiões (18f–18m) e a cadeia (os 17 itens nas rodadas, nenhum por RAM) | sim: 11 mísseis, 3 E-tanks, 2 expansões de PB (rodada 6), o Super Missile; **75 itens, 75%** (a tela do fim do SM mostra 75%) |
| 4d. Os chefes da decisão 4 com a luta de verdade | `check_epic_bosses`, `check_arenas`; `phendrana_sheegoth`, `phendrana_thardus`; a cadeia (as duas lutas buscadas da entrada dela) | sim |
| 4e. Sem softlock | `check_tallon_return` e `check_tallon_round_stuck` nas quatro áreas, a água (`check_tallon_water`); a cadeia inteira | sim |
| 4f. Mapa/minimapa "PHENDRANA" salvos, 4 save stations e a map station, "PHENDRANA / DRIFTS" no continue | `check_pause_maps`; `phendrana_save_station_a/b/c/d`, `phendrana_map_station`, `elevador_phendrana_norte`; o fim da cadeia (as telas de Phendrana na cópia salva da área 4 depois do continue) | sim |
| Decisão 1: as 56 salas, região por região | 18f, 18i, 18j, 18l, 18m | sim |
| Decisão 2: área 4 (Mines na 5, Impact Crater na 0) | `check_phendrana_slot` | sim (padrão aceito, a confirmar) |
| Decisão 3: itens (o Super Missile do SM) | `EPIC_PHENDRANA_ITEMS`, `EPIC_PHENDRANA_NO_ITEM` | sim |
| Decisão 4: os dois chefes | `EPIC_PHENDRANA_BOSS_ROOMS`, `check_epic_phendrana` | sim |
| Decisão 5: sem frio, só a Gravity Chamber inundada | `check_epic_phendrana`, `EPIC_PHENDRANA_FLOODED` | sim |
| Decisão 6: três caras, neve onde neva no Prime | `ice.check`, `check_epic_phendrana` (23 salas) | sim (padrão aceito, a confirmar) |
| Decisão 7: Metroid do SM enfraquecido | `check_phendrana_enemies` (`chaser_problems`) | sim (padrão aceito, a confirmar) |

Decisões das filhas a confirmar pelo usuário (escolhidas as recomendadas): as cores das três caras, a neve = esporos, a música (18d); a
cara das salas de elevador e o elevador que desce em Phendrana (18e); as formas das salas e os mísseis "sem trava" (18f); o orbe =
cópia do ATOMIC que deriva até ela, as contas e as cores (18g); o Sheegoth imune ao feixe sem carga, 2 Babygoths, a porta trancada (18h);
o gelo de plasma = nicho com tampa laranja (18i); Quarantine Cave ↔ Monitor = túnel dos dois lados (18j); o Thardus sem prêmio, vida
400, acorda na entrada, a música do Torizo (18k); o Metroid sem agarrar (18l); o Ripper fora, a borda da Gravity Chamber na rodada 5, o
bloco de PB dos dois lados (18m); o grupo C em 5 min 30 s ou um grupo D, a tela do fim do SM pelo evento `$0E`, a rodada 3 subindo pela
Shore Tunnel (18n). Fica em aberto: as Phazon Mines e a Impact Crater (o plano das áreas, decisão 2).
