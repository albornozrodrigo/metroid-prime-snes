# 17 — Magmoor Caverns (épico)

Estado: **verificada** (01/11/2026, fechado na 17j: as 10 filhas 17a–17j verificadas; critérios conferidos em "Verificação do épico", no fim). Aprovada em 01/11/2026 com as decisões do usuário registradas no fim; 17a, 17b e 17c verificadas com a ROM igual; 17d (estilo e lava), 17e (elevadores), 17f (região A), 17g (inimigos da região A), 17h (região B), 17i (região C: as 29 salas) e 17j (rodadas das três áreas e a cadeia completa) verificadas
Esforço estimado: 18–24 dias no total, em 10 filhas de 0,5–3 dias (a Chozo, 64 salas, levou 13 filhas + o épico dos chefes; a
Magmoor tem 29 salas e ~156 telas, mas pede estilo, lava e calor novos). MVP (17a–17f, a região norte jogável vinda da Chozo): 7–9 dias.

## Contexto

Tallon (44 salas) e Chozo (64 salas) estão prontos e andados juntos: 51 itens em 7 rodadas, a cadeia completa no emulador (12m),
os 4 chefes da Chozo (épico 14), título e demos (spec 16). O usuário aprovou a próxima etapa: **Magmoor Caverns**, o mundo de lava
que no Prime liga a Chozo, o Tallon, Phendrana e as Phazon Mines. Hoje os dois elevadores que levam à Magmoor são **de enfeite**:
`chozo_transport_magmoor_north` (Chozo P24, região B, rodada 1) e `tallon_transport_magmoor_east` (Tallon P23, região C, rodada 1,
com o Wave Beam no chão desde a 09b).

Este épico segue o molde do 12: levanta os fatos (Prime e ROM), decide o que é técnico, deixa ao usuário o que é de gosto ou de
escopo, e divide o trabalho em filhas — toolchain primeiro (ROM igual), regiões por último, as rodadas e a cadeia no fim.

## Estado atual (verificado)

Na pasta real, antes desta etapa (leitura só): `python3 -I tools/validate.py` → "136 salas, 284 portas, 0 problemas"; linha
"rodadas (specs/12m): Tallon + Chozo andados juntos, 51 itens em 7 rodadas … elevadores a partir da rodada: chozo_west 0,
chozo_east 4, chozo_south 5; porcentagem do fim ($8B:E627) com todos: 51% (energia 799, mísseis 160, power bombs 10)". Nenhum teste
rodado, nenhum build (só leitura de `build/metroid_prime_snes.sfc` e `build/manifest.json`). Roteiros desta pesquisa no scratchpad
da sessão (`…/scratchpad/s17/scripts/`): `magmoor_objs.py` (itens, cor das portas, funções especiais, inimigos por camada, destino
dos elevadores, venv do Prime), `norfair_rooms.py` (tileset, música e FX das salas vanilla da Norfair), `palfx.py` (listas de FX de
paleta por área), `free.py` (espaço livre por banco, base × construída), `orphan_runs.py` e `owners.py` (faixas de bytes só de salas
órfãs e de quem são). Saídas: `s17/magmoor_locks.json` (o `tools/dump_prime_locks.py` rodado para a Magmoor), `s17/magmoor_objs.out`,
`s17/sizes.out`, `s17/validate.out`.

### A Magmoor no Prime (dados)

Fonte: `research/prime_worlds.json` (MLVL "Magmoor Caverns", `Metroid6.pak`) e os objetos de `research/prime_fs`
(retro-data-structures 0.44.1; mesmos métodos da 12c/12j/12l: item = 1ª palavra depois do nome + 60 bytes, enum conferido pelos
artefatos; cor de porta = `DamageVulnerability` do `Trigger_DoorKey`, ordem power, ice, wave, plasma, 1 = dano, 2 = imune;
`SpecialFunction` 18 = `Area Damage`, o calor). "Conhecimento" = o que eu sei do jogo e os dados não mostram; marcado *(incerto)*
quando não tenho certeza.

- **29 salas** (índices 0–28), **58 docks = 29 ligações**, todas com volta. O grafo é quase uma linha: um só ciclo
  (Monitor Station → Warrior Shrine → Fiery Shores → Shore Tunnel → Monitor Station).
- **2 save stations** (P3 Save Station Magmoor A, P28 Save Station Magmoor B: função 7), **nenhuma map station**.
- **5 elevadores** (`WorldTeleporter`, destino pelo id de MREA nos bytes):

| P# | Sala | Vai para | Do nosso lado |
|---|---|---|---|
| 0 | Transport to Chozo Ruins North | Chozo P24 Transport to Magmoor Caverns North | `chozo_transport_magmoor_north` (região B, rodada 1, de enfeite: `tools/chozo/layouts.py:402`) |
| 16 | Transport to Tallon Overworld West | Tallon P23 Transport to Magmoor Caverns East | `tallon_transport_magmoor_east` (região C, rodada 1, de enfeite: `tools/tallon/layouts.py:288`, plataforma x 3–6; o Wave em (9, 25), fora dela) |
| 13 | Transport to Phendrana Drifts North | Phendrana P0 Transport to Magmoor Caverns West | — (Phendrana não existe) |
| 27 | Transport to Phendrana Drifts South | Phendrana P29 Transport to Magmoor Caverns South | — |
| 26 | Transport to Phazon Mines West | Phazon Mines P25 Transport to Magmoor Caverns South | — (Mines não existe) |

- **Itens** (10 `Pickup` de verdade):

| P# | Sala | Item do Prime (enum) | No nosso jogo |
|---|---|---|---|
| 6 | Triclops Pit | Missile Expansion (4) | Missile Expansion |
| 8 | Storage Cavern | Missile Expansion (4) | Missile Expansion |
| 14 | Fiery Shores | Missile Expansion (4) | Missile Expansion |
| 10 | Transport Tunnel A | Energy Tank (24) | Energy Tank |
| 23 | Magmoor Workstation | Energy Tank (24) | Energy Tank |
| 14 | Fiery Shores | Power Bomb Expansion (7, `P_Bomb`) | Power Bomb (no SM o item já é a expansão de +5) |
| 21 | Plasma Processing | **Plasma Beam** (3) | **já está no Tallon** (Chozo South, 09b) |
| 12 | Shore Tunnel | Ice Spreader (14, combo do Charge) | não existe no SM |
| 4 | Lava Lake | Artifact of Nature (36) | não (artefatos fora desde o épico 07) |
| 11 | Warrior Shrine | Artifact of Strength (30) | não |

  **Correções de premissas**: a Magmoor **não tem** Wave, Ice nem Grapple Beam (Wave e Ice são de Phendrana/Chozo; o Grapple é da
  Mines, Storage Depot B: tabela da spec 09). A única habilidade de verdade da Magmoor é o **Plasma**, que o épico 09 já pôs no Tallon.
  São 3 mísseis, 2 E-tanks, 1 expansão de PB — e o Plasma, o Ice Spreader e 2 artefatos, que não entram como estão.
- **Calor** (`Area Damage`, função 18): **12 salas superaquecidas** (13 objetos: a Lava Lake tem 2; a 12j anotou "13 salas", eram
  objetos): Lake Tunnel, Lava Lake, Pit Tunnel, Triclops Pit, Monitor Tunnel, Monitor Station, Transport Tunnel A, Warrior Shrine,
  Shore Tunnel, Fiery Shores, Transport Tunnel B, Twin Fires Tunnel. **Sem calor**: as salas de elevador e de save, a Burning Trail
  (só um "check for varia", função 5: o aviso), a Storage Cavern e todo o sul a partir da Twin Fires (Twin Fires, os Core Tunnels, a
  Geothermal Core, a Plasma Processing, a Workstation e os túneis dela). Lava (objeto `Water` com "lava" no nome) em 23 das 29 salas (todas menos as P0, P3, P5, P24, P25 e P26).
- **Travas nas portas** (`s17/magmoor_locks.json` + cor lida das vulnerabilidades):
  - escudo de míssil (`Actor Missile Lock`): Burning Trail → Save Station A; Transport to Phendrana South → Save Station B (azuis por baixo);
  - porta só Wave (`2 2 1 2`): Twin Fires → North Core Tunnel, os dois lados da North Core Tunnel, os dois da South Core Tunnel,
    Workstation → Transport Tunnel C, os dois lados da Transport Tunnel C, Transport to Phendrana South → Transport Tunnel C;
  - só Ice (`2 1 2 2`): Geothermal Core → Plasma Processing; Workstation Tunnel ↔ Transport to Mines West (os dois lados);
  - só Plasma (`2 2 2 1`): **Plasma Processing → Geothermal Core** (a porta de dentro: no Prime a Samus sai com o Plasma que pegou ali);
  - Morph Ball: Warrior Shrine → Fiery Shores (`Door_Area Morphball`, atrás de uma parede que só a Power Bomb quebra: vulnerabilidade
    `2 2 2 2 2 1 …`); do lado da Fiery Shores a doca não tem porta (só uma câmera): *mão única provável (incerto)*.
  - Nenhuma porta de charge (como na Chozo: o Prime não tem porta só de tiro carregado).
- **Travas dentro das salas** (dados; o uso no caminho é conhecimento):
  - Lava Lake: 2 rochas que só bomba/PB quebram e 2 `GrapplePoint` (o artefato no pilar; *Space Jump, incerto*);
  - Triclops Pit: um bloco de bomba (camada 3); o míssil numa cavidade da coluna (*Space Jump, talvez X-Ray: incerto*); a porta da
    Storage Cavern no alto (*Morph Ball: incerto*);
  - Monitor Station: girador de Boost Ball (`SpinnerController`, "Reset Bridges If No Boost") que levanta as pontes; jatos de fogo
    (camada 3);
  - Transport Tunnel A: o E-tank (*Morph Ball + Bombas num túnel sob o chão: incerto*);
  - Shore Tunnel: o tubo de vidro do Ice Spreader, só a PB quebra (`4 4 4 4 4 1 …`);
  - Fiery Shores: o míssil no fim do túnel que desce da Warrior Shrine (PB); a expansão de PB num trilho de bola (*Bombas: incerto*);
    2 `GrapplePoint`; 8 jatos de fogo que o gelo congela;
  - Twin Fires Tunnel: **trilho de Spider Ball** sobre a lava (92 pontos) — no Prime o caminho normal pede a Spider Ball;
  - Twin Fires e North Core Tunnel: estalactites que o tiro derruba ("target for stalactite") e viram plataforma na lava (conhecimento);
  - Geothermal Core: 7 bomb slots, trilhos de Spider (411 pontos), 1 `GrapplePoint`, 3 giradores de Boost — o quebra-cabeça que abre a
    Plasma Processing (Grapple + Spider + Boost + Bombas + Ice: conhecimento, conferido pelos objetos);
  - Magmoor Workstation: 3 painéis que só o Wave acende (`3 3 1 3 …`; o Thermal Visor os mostra: conhecimento) e sobem a plataforma do E-tank;
  - jatos de fogo congeláveis (só o Ice: `3 1 3 …`) em Lake Tunnel, Pit Tunnel, Fiery Shores, Twin Fires, South Core Tunnel, Transport
    Tunnel C e Monitor Station.
- **Inimigos** (camada 0, a regra de 07i/12h; nomes dos tipos dos dados): Burning Trail MetareeAlpha 16 + Parasite 1; Lake Tunnel
  Burrower 1 + Parasite 2; Lava Lake Puffer 6; Pit Tunnel Tryclops 3; Triclops Pit Tryclops 5; Monitor Tunnel Puffer 5; Fiery Shores
  Magdolite 1 + Tryclops 2; Transport Tunnel B Magdolite 1; Twin Fires Puffer 15; South Core Tunnel Burrower 2 + PuddleSpore 1;
  Workstation Tunnel Parasite 3. Nas outras camadas (passes/eventos): Flying Pirates (Lava Lake, Triclops Pit, Monitor Station,
  Workstation com `TeamAIMgr`), Magdolites e Puffers a mais, Parasites e PuddleSpores da Geothermal Core.
- **Chefes: nenhum.** A Magmoor do Prime não tem chefe nem mini-chefe (os piratas da Workstation são camada de evento).

Tamanho SM pela regra do Tallon (`tools/tallon/rooms.py:57` `screens`, 30 m por tela, no máximo 6×4; `s17/sizes.out`):

| P# | Sala | Telas | Liga a | Quente |
|---|---|---|---|---|
| 0 | Transport to Chozo Ruins North | 1×2 | 1 | |
| 1 | Burning Trail | 6×2 | 0, 2, 3 | |
| 2 | Lake Tunnel | 3×1 | 1, 4 | sim |
| 3 | Save Station Magmoor A | 1×1 | 1 | |
| 4 | Lava Lake | 6×1 | 2, 5 | sim |
| 5 | Pit Tunnel | 2×1 | 4, 6 | sim |
| 6 | Triclops Pit | 6×3 | 5, 7, 8 | sim |
| 7 | Monitor Tunnel | 2×1 | 6, 9 | sim |
| 8 | Storage Cavern | 2×1 | 6 | |
| 9 | Monitor Station | 6×4 | 7, 10, 11, 12 | sim |
| 10 | Transport Tunnel A | 2×1 | 9, 13 | sim |
| 11 | Warrior Shrine | 2×2 | 9, 14 | sim |
| 12 | Shore Tunnel | 3×1 | 9, 14 | sim |
| 13 | Transport to Phendrana Drifts North | 1×2 | 10 | |
| 14 | Fiery Shores | 6×2 | 11, 12, 15 | sim |
| 15 | Transport Tunnel B | 2×1 | 14, 16 | sim |
| 16 | Transport to Tallon Overworld West | 2×1 | 15, 17 | |
| 17 | Twin Fires Tunnel | 3×2 | 16, 18 | sim |
| 18 | Twin Fires | 6×1 | 17, 19 | |
| 19 | North Core Tunnel | 2×1 | 18, 20 | |
| 20 | Geothermal Core | 4×3 | 19, 21, 22 | |
| 21 | Plasma Processing | 3×1 | 20 | |
| 22 | South Core Tunnel | 3×1 | 20, 23 | |
| 23 | Magmoor Workstation | 4×3 | 22, 24, 25 | |
| 24 | Workstation Tunnel | 3×1 | 23, 26 | |
| 25 | Transport Tunnel C | 1×1 | 23, 27 | |
| 26 | Transport to Phazon Mines West | 2×2 | 24 | |
| 27 | Transport to Phendrana Drifts South | 2×2 | 25, 28 | |
| 28 | Save Station Magmoor B | 1×1 | 27 | |

**Total ~156 telas** (Chozo 202, Tallon 251). As salas de elevador seguem o desenho nosso (1×2, poço; a 17c ajusta).

### Regiões (pelo grafo, como 07 e 12)

- **A — Norte, vinda da Chozo** (9 salas, ~48 telas): 0, 1 Burning Trail, 3 Save Station A, 2 Lake Tunnel, 4 Lava Lake, 5 Pit Tunnel,
  6 Triclops Pit, 8 Storage Cavern, 7 Monitor Tunnel. Itens: os mísseis da Triclops Pit e da Storage Cavern (o artefato da Lava Lake fora).
- **B — Centro e a saída para o Tallon** (8 salas, ~51 telas): 9 Monitor Station, 10 Transport Tunnel A, 13 Transport to Phendrana North,
  11 Warrior Shrine, 12 Shore Tunnel, 14 Fiery Shores, 15 Transport Tunnel B, 16 Transport to Tallon West. Itens: E-tank do TTA, míssil e
  expansão de PB da Fiery Shores (o Ice Spreader e o artefato da Warrior Shrine não entram como estão).
- **C — Sul: Twin Fires, Geothermal Core, Workstation** (12 salas, ~57 telas): 17 Twin Fires Tunnel, 18 Twin Fires, 19 North Core Tunnel,
  20 Geothermal Core, 21 Plasma Processing, 22 South Core Tunnel, 23 Magmoor Workstation, 24 Workstation Tunnel, 26 Transport to Mines
  West, 25 Transport Tunnel C, 27 Transport to Phendrana South, 28 Save Station B. Itens: o lugar do Plasma, o E-tank da Workstation.

Ligações entre regiões: A–B (7–9), B–C (16–17).

### Como a Magmoor encaixa no nosso mundo (verificado no código)

- **Pares de elevador**: `tools/areas.py:197` `ELEVATORS` tem só os 3 da Chozo; o da Magmoor North ficou de enfeite (épico 12,
  decisão 6). Os dois lados que já existem estão na **rodada 1**: `chozo_transport_magmoor_north` (`tools/chozo/rooms.py:542`
  `_ROUNDS[1]`) e `tallon_transport_magmoor_east` (`tools/tallon/rooms.py:314` `_ROUNDS[1]`).
- **Itens do Prime → SM** (épicos 09 e 12): Missile Expansion/Launcher → Missile Expansion; Energy Tank → E-tank; expansão de PB → Power
  Bomb; Morph, Bombas, Ice, Wave, Plasma, Varia, Gravity, Charge, Space Jump, X-Ray → o mesmo item; Grapple (existe no SM) **sem uso**
  (saiu na 09a); Spider, Boost, Thermal, Scan, combos (Wavebuster, Ice Spreader…) e artefatos → **nada**. O que o Prime pede e o SM não
  tem virou geometria: Spider/Boost/meio-tubo/gancho → borda de Space Jump (Sun Tower, Main Plaza), parede de míssil → bloco de bomba,
  bomb slots → túnel com bloco de bomba (12i–12l).
- **Itens fora da ordem do Prime**: o épico 09 pôs no Tallon os itens de trava de outros mundos, cada elevador de enfeite com o item
  "que viria de lá" (Wave na Magmoor East, Plasma na Chozo South, Power Bomb na Mines East); a Chozo (opção B) recebeu só o que não
  tinha lugar (Charge, Varia, mísseis, E-tanks, a PB da Magma Pool), com **míssil** onde o Prime tem um item que já existe (Morph da
  Ruined Shrine, Bombas do Burn Dome, Ice da Antechamber) e **nada** onde o item não existe no SM (Wavebuster, artefatos).
- **Quando a Samus tem cada coisa** (rodada em que é pega → usada a partir da seguinte): mísseis 0, Morph 0, Bombas 1, Wave 1, Charge 1,
  **Varia 2**, Space Jump 2, Ice 3, Gravity 4, Power Bomb 5, Plasma 5. Com o calor "sem a Varia não entra" (12g2), tudo o que é quente
  na Magmoor fica da **rodada 3** em diante; Burning Trail, Save Station A (porta vermelha) e as salas de elevador ficam na 1.
- **As rodadas declaradas do Tallon e da Chozo não mudam** com a Magmoor, se duas regras forem seguidas: (1) a Magmoor não dá atalho
  que chegue antes a sala do Tallon/Chozo — os dois lados já são rodada 1 e todo caminho de um elevador ao outro passa por sala quente
  (rodada 3); (2) a **expansão de PB** da Magmoor (no SM, pegar uma expansão de PB **liga** as Power Bombs) não pode ser pega antes
  da rodada 6 — no Prime ela já está atrás de parede de PB (o túnel da Warrior Shrine), o mesmo jeito que a Chozo resolveu a Magma
  Pool (bloco de PB, rodada 6). O Plasma na Plasma Processing teria o mesmo problema (dá o Plasma antes da rodada 6): por isso o lugar
  dele recebe outro item (decisão 2).
- Bits livres: itens a partir de `$D3` (Tallon `$A0–$B3`, Chozo `$B4–$D2`; vetor `$7ED870`, 512 bits); portas vermelhas a partir de
  `$C0` (Tallon `$B0–$B2`, Chozo `$B3–$BF`); a Magmoor precisa de 2 (os escudos de míssil). Nenhum bit de chefe.
- Porcentagem do fim com a Magmoor (7 itens, decisão 2 recomendada): **58%** (energia 999, mísseis 180, power bombs 15).

### A área do SM

Áreas usadas: 0 Tallon, 1 Chozo, 3 fragata. Livres para mundos novos: **2 (Norfair), 4 (Maridia), 5 (Tourian, reservada à Impact Crater
em `tools/frigate/mapsave.py:12`)**. A 6 (Ceres) é usada pela cena da fuga (spec 05) e, como a 7 (debug), **não tem mapa salvo**: o save
só guarda o mapa explorado das áreas 0–5 (`mapsave.py`, `LIST_ROOM` em `mapsave.py:32`).

Código vanilla que muda por área (C `vendor/sm/src`, `grep area_index`), conferido agora:

| Área | Diferença | Peso para a Magmoor |
|---|---|---|
| 2 | o gelo congela inimigo por **300 quadros em vez de 400** (`sm_a0.c:2751`, `sm_a0.c:2789`); propriedades da bola de fogo do Ridley (`sm_86.c:1163`, `SetAreaDependentEprojPropertiesEx`: o único usuário é o `kRidleysFireball`, `sm_86.c:1217`); o código do Ridley (`sm_a6.c`) | o Meta Ridley mora na área 3: nada. Sobra o gelo 25% mais curto **só na Magmoor** (combina: lava derrete o gelo) |
| 4 | mapa de pausa rola 24 px (`sm_82.c:1811`) | cosmético |
| 5 | bola de fogo do Ridley (`sm_86.c:1165`) | nada |

**Calor na área 2 já vem pronto**: a lista de FX de paleta da Norfair (`$83:ACA6`, ponteiro em `$83:AC46 + 2·2`; bytes da ROM base:
`F761 F785 F789 F78D F791 F745 F745 F745`) tem o objeto do calor `$F761` no bit 0 e 4 objetos de brilho da lava nos bits 1–4; a Chozo
precisou pôr `$F761` no bit 4 da lista da área 1 (`tools/chozo/heat.py`, `$83:AC8E`). O patch "só a Varia protege" (`$8D:E37C`, 12g2)
vale para qualquer área.

**Recomendação técnica: área 2.** Faltam fatos da área 2 (tabelas do mapa de pausa em `build.VANILLA_PAUSE`, 23 load stations
vanilla em `roomgraph.STATION_COUNTS`, lista do mapa salvo até 80 bytes no lugar) — a filha 17b lê dos bytes, como a 12b fez para a 1.

**Aviso de capacidade** (não bloqueia a Magmoor): sobram 3 áreas com mapa salvo (2, 4, 5) para 4 mundos (Magmoor, Phendrana, Mines,
Impact Crater). Um deles vai dividir área com outro mundo (decisão 6).

### Visual: tileset, lava, música

- **Tilesets 09 e 0A da Norfair** (tabela `$8F:E7A7`; bytes): as entradas `$8F:E6F3` (09) e `$8F:E6FC` (0A) usam **os mesmos metatiles
  `$C1:E361` e os mesmos gráficos `$BD:C3F9`**, só a paleta muda (`$C2:B5E4` quente, `$C2:B6BB` fria). Salas vanilla da área 2
  (`s17/scripts/norfair_rooms.py`): 54 estados com o 09, 14 com o 0A; os estados do 09 quase todos com FX de paleta `$1F` (calor +
  brilho), os do 0A sem. **Nenhuma sala nossa usa 09/0A** (usamos 0, 2, 4, 0C) e as demos estão desligadas (spec 16): nada a recolorir.
  Escolha técnica: **salas quentes no 09, frias no 0A** — um estilo só (peças e colisão iguais), a cor diz ao jogador onde queima.
- **Lava do SM** (FX tipo 2; 39 estados vanilla da Norfair): `Samus_Animate_LavaFx` (`sm_90.c:136`): abaixo da superfície, sem a
  Gravity Suit, ½ de energia por quadro (30/s) e o corpo afunda; o `Samus_HandlePeriodicDamage` (`sm_90.c:6218`) corta pela metade com a
  Varia (15/s); **com a Gravity, nada** (e física normal). Nada disso existe no projeto ainda: a Chozo deixou a lava seca (Magma Pool,
  Meditation Fountain; pergunta 7 do épico 12).
- **Música vanilla da Norfair**: `$15/$05` (9 estados, Norfair de cima) e `$18/$05` (7, Norfair de baixo). Fundo: listas de biblioteca do
  `$8F` (`$BEC6`, `$BE5A`, `$BF68` com BG2 `$C1C1`, as mais usadas). A 17d escolhe pelas prévias, como a 12f fez para o 0C.

### Espaço por banco (medido agora)

Livres na ROM construída (`s17/scripts/free.py`, maior faixa de `$FF`; `$8F` recuperado pela linha do validador):

| Banco | Livre hoje | A Magmoor pede (29 salas, 29 ligações) | Cabe? |
|---|---|---|---|
| `$8F` (cabeçalhos, estados, listas) | **0** na faixa principal; **573** na recuperada da 12a (1681 de 2254 usados) | ~1500 (≈ 52 por sala, medido na Chozo) | **não**: precisa de mais faixa recuperada (17a) |
| `$83` (portas, FX) | 17 514 (`$83:BB96`) | ~800 (58 entradas de porta + FX de 29 salas) | sim |
| `$A1` (populações) | 2 319 (`$A1:F6F1`) | ~700 (~40 inimigos) | sim (Phendrana vai precisar de mais) |
| `$B4` (enemy sets) | 2 128 (`$B4:F7B0`) | ~600 | sim |
| `$84` (PLMs: portas de feixe) | 2 403 (`$84:F658`) | pintura das portas no 09/0A, talvez porta vertical nova (~150) | sim |
| `$A0` (espécies) | 1 857 (`$A0:F8BF`) | uma cópia de espécie se um inimigo pedir toque menor (~64) | sim |
| nível / fixo | 485 668 / 482 294 | ~12 KB de nível; paleta/tabela de metatiles do 09/0A pintadas (~5 KB) | sim |
| SRAM do mapa | 835 livres de 1280 | ≈ 30 bytes (estimativa; a 17c mede; lugar vanilla da área 2 até 80) | sim |

**Salas órfãs (pedido do relatório)**: a linha do validador "bytes só delas: `$8F` 21688, `$83` 10458, `$A1` 27363, `$B4` 4396" **não é
só das demos**: são os bytes que só as 262 salas vanilla órfãs usam (as das demos entraram na conta depois da spec 16). Faixas
contínuas de `$8F` fora do `RECLAIMED_8F` (`s17/scripts/orphan_runs.py`): 21 109 bytes em 34 faixas; as maiores:

| Faixa | Bytes | Salas donas | Cabeçalho comparado pelo código | Demo? |
|---|---|---|---|---|
| `$8F:91F8–A0FA` | 3843 | Crateria | `$96BA`, `$9804` | sim |
| `$8F:8000–8ED3` | 3796 | 149 salas (áreas 0–2: scroll e PLMs) | — | **sim** (17 salas das demos) |
| `$8F:CCCB–D48B` | 1985 | Maridia | `$CEFB` | — |
| `$8F:C215–C8C6` | 1714 | 97 salas (áreas 3–6) | — | sim (`$CC6F`, `$D0B9`) |
| `$8F:A0FD–A698` | 1436 | | `$A66A` | — |
| `$8F:AD5C–B218` | 1213 | 26 da Norfair | — | sim |
| `$8F:A9E5–AD41` | **861** | 18 da Norfair | — | **não** |
| `$8F:8ED6–9193` | **702** | 15 da Norfair | — | **não** |

`$83`: 10 458 em 55 faixas (a maior `$83:80D0–87EB`, 1820) — sem necessidade agora (17,5 KB livres). `$A1`: 27 363 em 10 faixas (a
maior `$A1:AD09–CCD3`, 8139) — guardar para Phendrana. `$B4`: 4396 em 297 pedaços de ≤ 30 bytes (pouco útil).

**Avaliação**: para a Magmoor bastam as **duas faixas da Norfair sem demo e sem cabeçalho comparado** (`$8F:8ED6–9193` e
`$8F:A9E5–AD41`, **1563 bytes**): com os 573 que sobram, 2136 para ~1500. As faixas grandes com dados das demos (`$8F:8000–8ED3`,
3796) ficam para Phendrana/Mines: usá-las prende o projeto às demos desligadas (religá-las depois quebraria) e pede tirar a regra
"nada de demo" do `check_reclaimed`. Filha 17a.

## Mudança proposta

### Decisões técnicas deste épico (minhas, justificadas acima; o usuário pode vetar)

1. **Uma sala do Prime = uma sala do SM**, as 29 ligações do grafo; chaves com prefixo `magmoor_`; `tools/magmoor/` no molde de
   `tools/chozo/` (`rooms.py`, `layouts.py`, `items.py`, `enemies.py`).
2. **Área 2** (se o usuário confirmar a decisão 6): o calor nativo no bit 0 (sem patch de lista), FX de paleta `$1F` nas salas quentes
   como as vanilla (calor + brilho), `$00` nas frias; o gelo 300 quadros na Magmoor aceito.
3. **Tilesets 09 (quentes) e 0A (frias)**, um estilo só (`tools/smlib/lava.py`, como `ruins.py`); portas de onda roxas pintadas numa
   linha livre da paleta e numa cópia da tabela de metatiles (o mesmo mecanismo da 10d e da 12f).
4. **Calor = "sem a Varia não entra"** (12g/12g2), `HOT_ROOMS` lido do `Area Damage` do Prime; `heat.py` generalizado por área.
5. **Travas do Prime → mecanismos que já existem** (sem item novo): escudo de míssil → porta vermelha; Wave/Ice → portas de feixe;
   a porta de Plasma de dentro da Plasma Processing → **gelo** (a Samus entrou por gelo; plasma ali a prenderia: `stuck` do validador);
   Spider/Boost/Grapple → borda de Space Jump; bomb slots → túnel com bloco de bomba; parede/vidro de PB → blocos de Power Bomb;
   painéis de Wave → porta de onda; estalactites e jatos de fogo → enfeite (não travam).
6. **Elevadores de verdade só para mundos que existem**: Chozo P24 ↔ Magmoor P0 e Tallon P23 ↔ Magmoor P16 (`ELEVATORS`); os três para
   Phendrana/Mines como os de enfeite da 07j (decisão 5).
7. **Inimigos da camada 0** (07i/12h), ≤ 1 por tela, justos na chegada: Puffer → Mella, Parasite → Zeela, MetareeAlpha → Skree (padrões
   aceitos); Magdolite → **LAVAMAN `$E83F`** (o Magdollite do SM, da Norfair de baixo; toque 40 > 20 da regra: cópia com toque menor,
   `SpeciesCopy` da 14a); Tryclops e Burrower → a 17g escolhe entre as espécies da Norfair (candidatos NOVA `$DCBF` = Sova, MZOOMER
   `$DD3F`, HOTARY `$D6BF`); PuddleSpore e as camadas de evento (Flying Pirates) fora.
8. **Rodadas**: o passeio anda as três áreas pelos elevadores (`validate.world_rounds`); critério duro: **as rodadas declaradas de cada
   item e sala do Tallon e da Chozo não mudam**.

### Filhas (rápido → complexo; toolchain primeiro)

| # | Spec | Entrega | Esforço | Testes |
|---|---|---|---|---|
| 17a | Mais espaço no `$8F` (segunda faixa recuperada) | `build.RECLAIMED_8F` ganha `$8F:8ED6–9193` e `$8F:A9E5–AD41` (1563 bytes, só órfãs da Norfair, nenhum dado de demo, nenhum cabeçalho comparado), `check_reclaimed` prova; ROM igual | 0,5 d | validate: `check_reclaimed` com as faixas novas; mutações no scratchpad (estrutura nossa num cabeçalho comparado, dado de demo, faixa sobreposta) falham; cópia com o `$8F` forçado à faixa nova + testes |
| 17b | Lugar da Magmoor na área 2 | `areas.MAGMOOR_AREA = 2`, `VANILLA_PAUSE[2]` lido dos bytes, `check_vanilla_pause` cobre a 2, `check_magmoor_slot` (área livre, SRAM, lista ≤ 80, estações), `heat.py` por área (`HEAT_BIT` da área: 4 na 1, 0 na 2; nenhum patch de lista na 2); ROM igual | 0,5 d | validate: linha "magmoor (specs/17b)"; mutações (área ocupada, byte vanilla errado, bit de calor errado) |
| 17c | Grafo, mapa e travas do Prime | `tools/magmoor/rooms.py`: `TABLE` (29 salas, tamanho pela regra), `LINKS` (29), `REGIONS` A–C, `DOCK_LOCKS` (missile 2, key 13 com a cor, morph 1), `FEATURES`, `HOT_ROOMS` (12), `KEY_BEAM`; `research/prime_magmoor_locks.json` por `dump_prime_locks.py`; disposição no mapa 64×32 por busca (como a 12c), poucas portas de chão/teto; `check_magmoor`; prévia `--mapa-magmoor`; nenhuma sala na ROM | 1,5–2 d | validate: tabela × Prime, mapa sem sobreposição, portas encostadas, ligação sem volta é erro (mutação), SRAM ≤ 80; prévia olhada |
| 17d | Estilo das cavernas de lava (09/0A), lava e cor das portas | `tools/smlib/lava.py` (peças das salas vanilla da Norfair, colisão igual), quente = 09 / fria = 0A, fundo e música lidos dos estados vanilla, portas de onda roxas (e as de gelo/plasma conferidas) no 09/0A; **lava medida no emulador** numa ROM de teste (`build.py --teste-17d`: dano sem suit/Varia/Gravity, altura do pulo dentro da lava) e o modelo `RoomDef.lava` em `reach.py` (decisão 4) | 2–3 d | validate: `lava.check`, cor/metatiles na ROM, nenhuma sala fora da Magmoor usa 09/0A; emulador: `lava_medida` (dano por suit, pulo), `porta_de_onda` no 09; prévias |
| 17e | Elevadores de verdade (Chozo ↔ Magmoor, Tallon ↔ Magmoor) | as salas P0 e P16 da Magmoor (becos), os lados da Chozo P24 e do Tallon P23 viram elevador (`ride=True`; o Wave fica onde está), `ELEVATORS` +2, `AreaDef MAGMOOR`, mapa/minimapa "MAGMOOR", lista do mapa salvo, "MAGMOOR / CAVERNS" na tela de continue (letras grandes existem: `areaselect.BIG`) | 2 d | validate: `check_elevators(_in_rom)` com 5 pares, linha nova com as rodadas dos dois lados (1 e 1); emulador: `elevador_magmoor_ida_e_volta` (Chozo → Magmoor → Chozo, `$079F` = 2, bits explorados das 3 áreas), `elevador_magmoor_tallon`; save/game over/continue com as três áreas |
| 17f | Região A (norte) | as 9 salas; a P0 abre para a Burning Trail; Save Station A = estação 1 da área 2 (porta vermelha, bit `$C0`); 7 salas quentes; 2 mísseis (Triclops Pit, Storage Cavern; bits `$D3`, `$D4`); a porta da Monitor Tunnel para a Monitor Station = parede | 2–3 d | validate: alcance a pé, rodadas (as da Chozo iguais), calor; emulador: `magmoor_regiao_a_rota` (do elevador à Monitor Tunnel com a Varia; sem ela o calor tira energia), `magmoor_regiao_a_itens`, `magmoor_save_station_a` |
| 17g | Inimigos | camada 0 do Prime nas salas da região A (e a tabela de B/C registrada, como a 12h), as espécies da decisão técnica 7, cópia do LAVAMAN se usado, justiça na chegada | 1–2 d | validate: `check_layer0_enemies` da Magmoor; emulador: `magmoor_inimigos_vivos`, auditoria de entrada (spec 15) nas salas novas |
| 17h | Região B (centro e Tallon West) | as 8 salas; a P16 abre (Transport Tunnel B e Twin Fires Tunnel = parede até a 17i); Transport to Phendrana North de enfeite; 5 salas quentes; E-tank do TTA, míssil e **expansão de PB da Fiery Shores atrás da parede de PB** (rodada 6); o lugar do Ice Spreader (decisão 2); o túnel de Morph da Warrior Shrine | 2–3 d | validate: rodadas (Tallon + Chozo iguais), `check_breakables` nos blocos de PB, `check_bombed_items`; emulador: `magmoor_regiao_b_rota` (Tallon West → Fiery Shores → Monitor Station → região A), `magmoor_regiao_b_itens` (a parede de PB, a expansão) |
| 17i | Região C (sul) | as 12 salas; Twin Fires Tunnel (trilho de Spider = borda de Space Jump, ou lava + Gravity: decisão 4); portas de onda (9 docas) e de gelo (3), a de dentro da Plasma Processing como gelo; quebra-cabeça da Geothermal Core → túnel com bloco de bomba + bordas de Space Jump; painéis da Workstation → porta de onda; Save Station B (estação 2, porta vermelha `$C1`); Phendrana South e Mines West de enfeite; 2 itens (o lugar do Plasma e o E-tank da Workstation) | 3 d | validate: `check_magmoor_locks_mapped` (toda trava do Prime numa ligação construída com o seu mecanismo, como a 12j), rodadas; emulador: `magmoor_regiao_c_rota`, `magmoor_regiao_c_itens`, `magmoor_save_station_b` |
| 17j | Rodadas das três áreas e a cadeia completa | `check_world_rounds` com a Magmoor (58 itens; as rodadas de Tallon/Chozo iguais; porcentagem 58%), linha "elevadores a partir da rodada" com os 2 novos; a cadeia completa estendida pelos 2 elevadores novos (todos os itens na ordem das rodadas, cada trava aberta de verdade, atalhos contados) | 2 d | validate: linha "rodadas (specs/17j)"; emulador: `cadeia_completa` com a Magmoor (~350 s); verificação inteira |

```
17a ─┐
17b ─┼─> 17c ─┬─> 17e ─> 17f ─> 17g ─> 17h ─> 17i ─> 17j
     └─> 17d ─┘
```

17a, 17b e 17c não mudam a ROM e servem a qualquer resposta do usuário (podem começar logo depois da aprovação). A 17d só muda a ROM de
teste. Da 17e em diante, cada filha `verificada` antes da próxima.

## Critérios de aceite (do épico)

1. 17a, 17b e 17c `verificada` com a ROM igual (sha1 do `.ips` igual ao de antes, dois builds; linhas do Tallon e da Chozo iguais; testes
   iguais).
2. Cada filha `verificada` com validate + build + testes; `check_orphans` prova que nenhum caminho entra em sala vanilla também pela área 2;
   `check_reclaimed` prova o uso das faixas novas.
3. **As rodadas declaradas do Tallon e da Chozo iguais** em toda filha (salas e itens; o validador compara; desvio = parar e perguntar).
4. Definição de pronto: as 29 salas ligadas como no Prime (ou o corte da decisão 1), os 2 elevadores funcionando nos dois sentidos, a Magmoor
   jogável a pé com os itens da decisão 2, as 12 salas quentes (ou o da decisão 3) só com a Varia no modelo, sem softlock (validador nas três
   áreas + cadeia no emulador), mapa de pausa/minimapa "MAGMOOR" salvos, as 2 save stations, "MAGMOOR / CAVERNS" no continue.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` (17a), `check_magmoor_slot` + `check_vanilla_pause` (17b), `check_magmoor` (17c), `lava.check` e cor no 09/0A (17d), elevadores (17e), alcance/calor/rodadas por região (17f–17i), `check_magmoor_locks_mapped` (17i), `check_world_rounds` (17j) | +8–10 checagens |
| scratchpad | mutações de cada checagem nova (como 12a/12b/12c) | ~25 |
| run_tests.py | `lava_medida`, `porta_de_onda` no 09 (17d); 2 de elevador (17e); rota/itens/save por região (17f, 17h, 17i: ~8); inimigos e entradas (17g); cadeia (17j) | +14–16 |
| imagem | prévias do estilo e do mapa; fotos do emulador das três regiões | — |

## Riscos e reversão

- **Lava** nunca foi usada no projeto: física e dano medidos na 17d antes de qualquer sala depender deles; se o modelo não fechar, a
  lava fica de enfeite (abaixo de chão sólido) ou seca, como na Chozo.
- **`$8F`**: 2136 bytes para ~1500 é folga de ~600; se a região C passar, mais faixas sem demo da Norfair (as de < 538 bytes) entram
  pela mesma checagem.
- **Rodadas do Tallon/Chozo** podem mudar por um atalho não previsto (a expansão de PB, o Plasma, um elevador): o validador pega; a
  regra é mudar a Magmoor, não as outras.
- **Gelo mais curto na área 2**: só pesa se alguma trava ou luta da Magmoor usar inimigo congelado (nenhuma proposta).
- **Cadeia mais longa** (~270 s → ~350 s): o emulador de teste já desenha só o último quadro; se passar do aceitável, a 17j propõe
  dividir por rodadas.
- **Save de SRAM vanilla** (spec 11, B7): como na 12a, um save vanilla da Norfair cairia em dado sobrescrito; documentado.
- Reversão: tudo vem de `tools/`; 17a–17c não mudam a ROM (tirar as faixas, constantes e checagens basta).

## Fora de escopo

- Phendrana Drifts, Phazon Mines, Impact Crater; os elevadores para eles funcionando.
- Habilidades novas do SM (Grapple, Speed Booster, Hi-Jump, Super Missile) — só se o usuário escolher (decisão 2).
- Artefatos, Ice Spreader, Thermal/Scan Visor, camadas de evento (Flying Pirates, segundo passe), jatos de fogo e estalactites como travas.
- Mexer no Tallon e na Chozo além dos dois lados dos elevadores (`ride=True` nas salas P24 e P23).

## Decisões do usuário (01/11/2026, respondidas)

Respostas do usuário às perguntas abaixo (as perguntas ficam como estavam, para o registro):

- **1 → (a)**: as 29 salas, região por região (norte A, centro B, sul C).
- **2 → (a)**: itens como na Chozo — 3 mísseis, 2 E-tanks, a expansão de PB (atrás da parede de PB, nunca antes da rodada 6); um
  **míssil no lugar do Plasma**; nada no lugar do Ice Spreader; nenhum artefato. Total 7 itens (4 mísseis, 2 E-tanks, 1 PB).
- **3 → (a)**: calor só nas 12 salas superaquecidas do Prime (`HOT_ROOMS`, lido do `Area Damage`).
- **4 → (b)**: lava de verdade do SM em fossos e lagos, que machuca; nunca no caminho obrigatório sem saída. **Não** (c): a lava não
  vira trava; onde o Prime pede a Spider Ball sobre a lava (Twin Fires Tunnel) vale a regra geral (borda de Space Jump), com a lava
  embaixo só como perigo com saída.
- Padrões recomendados aceitos: **5 → (a)** elevadores para Phendrana (2) e Mines (1) de enfeite e vazios; **6** a Magmoor na **área 2
  (Norfair)**; **7** nenhum chefe na Magmoor.

Incertezas do épico resolvidas agora (as que dependem de desenho ficam para a filha da região):

- Lugar da área: 2 (17b reservou e conferiu as tabelas; o calor por área, a 2 sem patch). O plano das áreas para Phendrana/Mines/Impact Crater (aviso de capacidade)
  **não** foi decidido: fica para o épico de Phendrana (não bloqueia nada da Magmoor).
- Twin Fires Tunnel: borda de Space Jump (decisão 4 sem a opção c); a lava embaixo tem saída (17i).
- Plasma Processing: a porta de dentro vira **gelo** (decisão técnica 5), o item é um míssil (decisão 2); rodada dele ≥ a do gelo.
- Espaço do `$8F`: as duas faixas sem demo da Norfair (17a) — feito, ROM igual.
- **Ficam para as regiões** (marcadas *(incerto)* acima): o sentido único Warrior Shrine → Fiery Shores e o caminho do míssil e da
  expansão de PB da Fiery Shores (17h); o míssil e a porta alta da Triclops Pit e a Lava Lake (17f); o E-tank do Transport Tunnel A
  (17h); as espécies do Tryclops e do Burrower (17g); a altura do pulo e o dano dentro da lava (medidos no emulador na 17d).

### Perguntas (como foram feitas)


1. **Tamanho**: (a) **as 29 salas**, por região, A primeiro (**recomendado**: o sul é onde Phendrana e Mines vão se ligar depois);
   (b) só A + B (17 salas; o sul fica para quando Phendrana existir).
2. **Itens**: (a) **como na Chozo** — 3 mísseis, 2 E-tanks, a expansão de PB (atrás da parede de PB, rodada 6); no lugar do Plasma
   (que já está no Tallon) um míssil; nada no lugar do Ice Spreader (como o Wavebuster); artefatos fora (**recomendado**: a Magmoor
   fica sem habilidade nova, como é no Prime, e o Tallon/Chozo não mudam); (b) a + uma habilidade nova do SM na Magmoor (p.ex. o
   Grapple Beam na Plasma Processing, com pontos de gancho de verdade na Geothermal Core e na Fiery Shores) — mais trabalho (+2–3 d) e
   mexe nas rodadas finais; (c) a, mas um E-tank em vez do míssil no lugar do Plasma.
3. **Calor**: (a) **só as 12 salas superaquecidas do Prime** (**recomendado**: fiel; o sul da Magmoor é frio no Prime); (b) a Magmoor
   inteira quente.
4. **Lava**: (a) seca, como a Chozo; (b) **lava de verdade do SM** em fossos e lagos (machuca, a Gravity Suit protege), nunca no caminho
   obrigatório sem saída — **recomendado**: sem lava a Magmoor perde a cara, e o SM já tem o efeito; (c) b + travas de lava: onde o Prime
   pede Spider Ball sobre a lava (Twin Fires Tunnel), atravessar a lava pede a **Gravity Suit** (no SM ela torna a lava inofensiva).
5. **Elevadores para Phendrana (2) e Mines (1)**: (a) **de enfeite e vazios**, como o da Magmoor na Chozo até hoje (**recomendado**);
   (b) de enfeite com o item "que viria de lá" (a regra do épico 09) — pede itens que o jogo ainda não tem.
6. **Área do SM**: confirmar a **área 2 (Norfair)** para a Magmoor (**recomendado**: calor e brilho da lava nativos, tilesets 09/0A
   livres; o gelo congela 25% menos ali). E o plano de depois: sobram 4 (Phendrana) e 5 (Mines ou Impact Crater) — um mundo vai
   dividir área; sugestão: a **Impact Crater dentro da área 0** (ela fica no Tallon, entra pelo Artifact Temple, 12 salas).
7. **Chefes**: o Prime não tem chefe na Magmoor — **nenhum** (recomendado; confirmar).

## Desvios (preenchido na implementação)

- **17a, 17b, 17c verificadas** (01/11/2026), ROM igual (sha1 `0f5cc669…0653`, manifest igual), 83/83; desvios em cada filha. Números
  medidos que mudam o texto acima: o mapa da Magmoor usa **30** bytes de SRAM (a estimativa era ≈ 30) e tem **1** porta de chão/teto; o
  `$8F` tem 3817 bytes recuperados (472 + 101 livres nas faixas da 12a, 702 + 861 nas novas: 2136 para as ~1500 da Magmoor).
- A 17c pôs a cor das portas e o calor nos **dados do dumper** (`key_vuln`, `area_damage` em `research/prime_magmoor_locks.json`), em vez de
  só no roteiro do épico.
- **17d verificada** (01/11/2026): tilesets 09/0A com as cores da Magmoor e a porta roxa (3 blobs fixos, nenhuma sala do jogo os usa ainda);
  lava medida numa ROM de teste: ½ de energia por quadro sem roupa, ¼ com a Varia, 0 com a Gravity; pulo de dentro 46/58/69 px com o pé a
  1/2/3 linhas da superfície. Regras da lava no validador (nunca no caminho; toda lava com saída em até 5 movimentos, no máximo 3 linhas de
  fundo). Desvio: a lava do SM cobre a sala inteira da superfície para baixo (BG3), as regiões põem a superfície abaixo de todo chão andável.
- **17e verificada** (01/11/2026): as salas P0 e P16 (becos, frias, secas), os elevadores Chozo P24 ↔ P0 e Tallon P23 ↔ P16, área 2 com mapa
  "MAGMOOR" e "MAGMOOR / CAVERNS" no continue; a Magmoor anda nas rodadas (rodada 1 dos dois lados); as rodadas do Tallon e da Chozo iguais.
  Desvio: nome em letras pequenas (as grandes são só do título); a caminhada cega da região B ganhou uma pausa medida.
- **17f verificada** (01/11/2026): a região A (8 salas + a P0 aberta), a Save Station A (estação 1 da área 2), os 2 mísseis (rodada 3),
  5 salas quentes, lava em 6 salas; as linhas do Tallon e das rodadas (12m) iguais (os itens da Magmoor têm a linha dela; a 17j junta
  as três áreas); 90/90 em 6 min 31 s. Desvios: o míssil da Triclops Pit numa borda de Space Jump declarada no item (`needs`); sem as
  rochas/ganchos do artefato da Lava Lake; `check_magmoor_locks_mapped` já na 17f (com "lava só onde o Prime tem").
- **17g verificada** (01/11/2026): os inimigos da camada 0 do Prime na região A (19 em 6 salas: Skree, Zeela, Mella, **Sova** no lugar
  do Burrower, **Viola parada** no do Tryclops), a tabela do Prime das regiões B/C registrada, justiça em toda sala da Magmoor (qualquer
  rodada), a auditoria de entrada (spec 15) na Magmoor, as caminhadas da 17f medidas de novo com os inimigos vivos (energia 99 do
  começo ao fim); 91/91. Desvios: os dentes do teto da Burning Trail descem até a linha 16 (os Skrees acima da câmera não acordavam); o
  Magdolite (LAVAMAN: toque 40, imune ao Power Beam) fica para a 17h decidir.
- **17h verificada** (01/11/2026): a região B (7 salas + a L0 da P16 aberta: a Magmoor liga a Chozo ao Tallon a pé, com a Varia, rodada
  3), 6 salas quentes, lava em 3, o E-tank da TTA (túnel de Morph com bloco de bomba, rodada 3), o míssil e a expansão de PB da Fiery
  Shores atrás de blocos de Power Bomb dos dois lados da porta de Morph da Warrior Shrine (rodada 6), 2 Violas na Fiery Shores; as
  linhas do Tallon e das rodadas (12m) iguais; 93/93. Desvios: **Magdolite fora** (as espécies de lava do SM são imunes ao Power Beam e
  ficam na lava: a confirmar); a porta Warrior Shrine ↔ Fiery Shores nos dois sentidos (o Prime provavelmente mão única: a confirmar);
  a Mella leste da Monitor Tunnel 24 → 12 (a porta nova, spec 15).
- **17i verificada** (01/11/2026): a região C (12 salas: as 29 da Magmoor na ROM), a Save Station B (estação 2, porta vermelha
  `$C1`), as portas key do Prime como portas de feixe (9 docas de onda, 3 de gelo; a de plasma da Plasma Processing de gelo,
  `SM_BEAM`), o míssil no lugar do Plasma (rodada 4) e o E-tank da Workstation (rodada 3), 7 inimigos (3 Mellas, 2 Sovas, 2 Zeelas);
  a ROM de teste da 17d mudou para uma porta R1 da Mines West; a bateria de testes dividida em `--grupo A|B`; as linhas do Tallon e
  das rodadas (12m) iguais. Desvios: a região C fica na rodada 3, não antes (a Twin Fires Tunnel, a porta do sul, é quente no Prime);
  bordas de Space Jump por features sem trava de porta (`FEATURE_GEOMETRY`); Puddle Spore fora; os painéis de Wave da Workstation sem
  mecanismo próprio (as portas da sala já pedem o Wave); rocha sobre portas laterais das salas altas.
- **17j verificada** (01/11/2026): as rodadas das três áreas num passeio só (`check_world_rounds`: 58 itens em 7 rodadas, os do
  Tallon e da Chozo nas rodadas de antes, os 7 da Magmoor nas declaradas, 3, 3, 3, 3, 4, 6, 6; porcentagem do fim **58%**: energia
  999, mísseis 180, power bombs 15; os elevadores da Magmoor a partir da rodada 1), a linha do épico (`check_epic_magmoor`), e a
  cadeia completa com a Magmoor no emulador, **dividida em 3 testes** ligados por estados salvos do emulador (`cadeia_completa_parte_1`
  no grupo A; `_2` e `_3` no grupo B, que carrega o estado salvo pelo A). Desvios: 2 portas de teto por `rise_through` e munição/
  energia repostas por RAM ao entrar na Magmoor (os inimigos soltam munição que a conta não prevê); tiros de feixe tirados de dois
  trechos (Wave/Plasma atravessam a parede e abrem a porta de trás); ver a [17j](17j-rodadas-e-cadeia-tres-areas.md).

## Verificação do épico (01/11/2026, 17j)

Conferido no fim da 17j, contra os critérios de aceite do épico e as decisões do usuário:

| Critério | Onde | Resultado |
|---|---|---|
| 1. 17a, 17b, 17c com a ROM igual | [17a](17a-mais-espaco-8f.md), [17b](17b-area-da-magmoor.md), [17c](17c-grafo-e-mapa-magmoor.md) | sim (sha1 `0f5cc669…0653` nas três, linhas do Tallon e da Chozo e testes iguais) |
| 2. Cada filha verificada (validate + build + testes); nenhum caminho entra em sala vanilla pela área 2; as faixas novas do `$8F` provadas | as 10 filhas; `check_orphans`, `check_reclaimed` | sim (validate 0 problemas em todas; 262 órfãs) |
| 3. Rodadas declaradas do Tallon e da Chozo iguais em toda filha | linha "tallon (…)" e linha "rodadas (specs/12m, 17j)" | sim: "44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"; itens por rodada Tallon + Chozo 0: 2 + 1; 1: 4 + 7; 2: 1 + 11; 3: 2 + 8; 4: 2 + 1; 5: 7 + 0; 6: 2 + 3 (iguais à 12m); elevadores chozo_west 0, chozo_east 4, chozo_south 5 |
| 4a. As 29 salas ligadas como no Prime | `check_magmoor` (tabela, 29 ligações), `check_epic_magmoor` | sim |
| 4b. Os 2 elevadores nos dois sentidos | `check_elevators(_in_rom)`; `elevador_magmoor_ida_e_volta`, `elevador_magmoor_tallon`; a cadeia (P24 ↓ 1 vez, P23 ↓ 2, P16 ↑ 3) | sim |
| 4c. A Magmoor a pé com os itens da decisão 2 | o passeio das três áreas (`check_magmoor_rounds`, `check_world_rounds`, `check_epic_magmoor`); as caminhadas das regiões (17f–17i) e a cadeia (os 7 itens nas rodadas, nenhum por RAM) | sim: 4 mísseis, 2 E-tanks, a expansão de PB (rodada 6); míssil no lugar do Plasma |
| 4d. As 12 salas quentes só com a Varia | `heat_gates`, `check_heat(_in_rom)`, `check_epic_magmoor`; `magmoor_calor` | sim |
| 4e. Sem softlock | `check_tallon_return` e `check_tallon_round_stuck` nas três áreas, regras da lava (`check_lava`); a cadeia inteira | sim |
| 4f. Mapa/minimapa "MAGMOOR" salvos, as 2 save stations, "MAGMOOR / CAVERNS" no continue | `check_pause_maps`; `magmoor_save_station_a`, `magmoor_save_station_b`, `elevador_magmoor_ida_e_volta`; o fim da cadeia (as telas da Magmoor na cópia salva da área 2 depois do continue) | sim |
| Decisão 1: as 29 salas, região por região | 17f, 17h, 17i | sim |
| Decisão 2: itens como na Chozo | `EPIC_MAGMOOR_ITEMS` | sim |
| Decisão 3: calor só nas 12 do Prime | `check_epic_magmoor` | sim |
| Decisão 4: lava de verdade, nunca no caminho sem saída | `check_lava`, `lava_medida` | sim (16 salas, todas com lava no Prime) |
| Decisão 5: Phendrana/Mines de enfeite e vazios | `check_epic_magmoor` (sem elevador, sem item) | sim |
| Decisão 6: área 2 | `check_magmoor_slot` | sim |
| Decisão 7: nenhum chefe | `check_epic_magmoor` | sim |

Decisões das filhas a confirmar pelo usuário (escolhidas as recomendadas): as cores e a regra da lava (17d); o míssil da Triclops
Pit numa borda de Space Jump e a Lava Lake sem as rochas do artefato (17f); Burrower = Sova, Tryclops = Viola parada, as contas
por sala, os dentes da Burning Trail (17g); Magdolite fora, a porta Warrior Shrine ↔ Fiery Shores nos dois sentidos (17h); Puddle
Spore fora, o E-tank da Workstation numa borda de Space Jump, bordas de Space Jump no lugar dos trilhos de Spider, as contas da
região C, a divisão da bateria (17i); a cadeia em 3 partes ligadas por estado salvo e os atalhos novos dela (17j). Fica em aberto
(não bloqueia nada): o plano das áreas para Phendrana, Mines e Impact Crater (aviso de capacidade, decisão 6).
