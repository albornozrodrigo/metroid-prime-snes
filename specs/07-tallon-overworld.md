# 07 — Tallon Overworld (épico)

Estado: verificada (23/10/2026, fechado na 09f: definição de pronto cumprida, ver Desvios)
Esforço estimado: 24–30 dias no total, em 13 specs filhas de 1–3 dias. MVP (07a–07g): 12–15 dias.

## Contexto

A fragata está pronta (28 salas, área 3 do SM). No Prime, quando a fragata cai, a Samus segue o Meta
Ridley até Tallon IV, perde o equipamento e pousa a nave na Landing Site do Tallon Overworld. Daí ela
vai às outras regiões pelos elevadores. O Tallon é o "centro" do Prime: sem ele não dá para ligar
nenhum outro mundo. `research/frigate_design.md` já reserva a área 0 do SM (Crateria) para ele:
superfície com chuva e com a nave da Samus, como a Crateria.

Este épico diz o tamanho do trabalho, como ele se divide e qual é o menor pedaço jogável (MVP).
Cada spec filha vai ter o próprio arquivo (`specs/07x-*.md`) com o modelo completo antes de começar.

## Estado atual (verificado)

### O Tallon no Prime (dados)

Fonte: `research/prime_worlds.json` (MLVL "Tallon Overworld", `Metroid4.pak`). Objetos extraídos
nesta pesquisa com `tools/dump_prime_area_objects.py research/prime_fs "Tallon Overworld"` e com um
leitor de `Pickup` feito à parte (o dump atual mostra os nomes dos Pickups como "nome ilegível": o
retro-data-structures 0.44.1 lê errado esse objeto; o nome e o item saem certos procurando
`00 00 00 12 <nome> 00` nos bytes crus e lendo 3 palavras (item, capacidade, quantidade) 60 bytes
depois do nome).

- **44 salas** (índices 0–43) e **44 ligações** de porta (88 entradas de dock, todas com volta).
- **2 pontos de save**: a nave na Landing Site (P0, `SpecialFunction Save Station`) e a sala
  `Savestation` (P28, dentro da fragata afundada).
- **Nenhuma map station** (nenhuma sala com estação de mapa; a fragata tinha a Map Facility).
- **Elevadores** (`WorldTeleporter`): 5 salas de transporte e o Artifact Temple:

| P# | Sala | Vai para |
|----|------|----------|
| 14 | Transport to Chozo Ruins West | Chozo Ruins |
| 22 | Transport to Chozo Ruins East | Chozo Ruins |
| 41 | Transport to Chozo Ruins South | Chozo Ruins |
| 23 | Transport to Magmoor Caverns East | Magmoor Caverns |
| 43 | Transport to Phazon Mines East | Phazon Mines |
| 16 | Artifact Temple (2 teleportes) | Impact Crater (depois dos 12 artefatos) |

  Não há elevador direto do Tallon para Phendrana (só pela Magmoor).
- **Itens** (225 objetos `Pickup`: 210 são sobras de inimigo, 5 tipos × 42; os 15 de verdade):

| P# | Sala | Item | Obs. |
|----|------|------|------|
| 0 | Landing Site | Missile Expansion (+5) | no Prime precisa de Morph Ball |
| 4 | Alcove | Space Jump Boots | |
| 8 | Frigate Crash Site | Missile Expansion | |
| 13 | Overgrown Cavern | Missile Expansion | |
| 15 | Root Cave | Missile Expansion | |
| 16 | Artifact Temple | Artifact of Truth | |
| 19 | Transport Tunnel B | Missile Expansion | |
| 20 | Arbor Chamber | Missile Expansion | |
| 27 | Cargo Freight Lift to Deck Gamma | Energy Tank | fragata afundada |
| 30 | Biohazard Containment | Missile Expansion | fragata afundada |
| 35 | Hydro Access Tunnel | Energy Tank | |
| 37 | Great Tree Chamber | Missile Expansion | |
| 39 | Life Grove Tunnel | Missile Expansion | |
| 42 | Life Grove | X-Ray Visor | |
| 42 | Life Grove | Artifact of Chozo | |

  Total: **9 Missile Expansions, 2 Energy Tanks, Space Jump, X-Ray, 2 artefatos = 15 itens.**
  (Os Pickups de míssil se chamam `P_Missile_Launcher` no script, mas têm capacidade 5 e
  quantidade 5: são expansões. O Missile Launcher do Prime fica na Chozo Ruins.)
- **Inimigos** (todas as camadas somadas): Parasite ("Platform Zoomer") 18, Beetle 14, Geemer 5,
  Seedling 13, Metaree Alpha 4, Blood Flower 4, AmbientAI ("Chubb Weed", explode ao tocar) 24,
  SnakeWeedSwarm 8, Space Pirate 13, Flying Pirate 9, Drone 4, Gun Turret 8, Jelly Zap 11,
  Spank Weed 29, Wall Crawler Swarm 1, Chozo Ghost 3, Ridley 1 (Artifact Temple, chefe final).
  FishCloud (57) são peixes/pássaros de enfeite.
- **Chuva** (`SpecialFunction - Rain Simulator`): Landing Site, Tallon Canyon, Temple Security
  Station, Root Cave, Arbor Chamber, Life Grove.
- **Água** (objeto `Water`): 13 das 14 salas da fragata afundada (só a P29 não tem) e mais 11:
  Landing Site, Gully, Alcove, Waterfall Cavern, Tallon Canyon, Frigate Crash Site, Root Tunnel,
  Root Cave, Transport to Magmoor Caverns East, Great Tree Hall, Life Grove. Fora da fragata
  afundada costuma ser poça ou lago raso; o tamanho de cada uma fica para as specs das regiões.

### Regiões (agrupamento pelo grafo de portas)

Tamanho do Prime = caixa (x, y, z) em metros, de `aabb`. Tamanho SM = proposta (telas L×A),
na mesma escala solta da fragata (sala longa → corredor, sala alta → poço; ≤ 50 telas).

**A — Superfície (início)**, 7 salas, 48 telas:

| P# | Sala | Prime (m) | SM | Portas para |
|----|------|-----------|----|-------------|
| 0 | Landing Site | 135×135×94 | 6×3 | 1, 2, 3, 4, 5 |
| 1 | Gully | 79×52×31 | 3×2 | 6, 0 |
| 2 | Canyon Cavern | 56×70×23 | 2×1 | 6, 0 |
| 4 | Alcove | 134×146×55 | 3×2 | 0 |
| 6 | Tallon Canyon | 125×112×79 | 4×3 | 2, 9, 1, 10 |
| 9 | Transport Tunnel A | 17×52×11 | 2×1 | 14, 6 |
| 14 | Transport to Chozo Ruins West | 36×46×51 | 1×2 | 9 |

**B — Templo**, 4 salas, 26 telas: 3 Temple Hall (3×1), 7 Temple Security Station (3×1),
11 Temple Lobby (2×1), 16 Artifact Temple (6×3). Cadeia 0 → 3 → 7 → 11 → 16.

**C — Cachoeira, Crash Site e Raízes**, 11 salas, 69 telas: 5 Waterfall Cavern (2×2),
8 Frigate Crash Site (8×4, a maior: 315×353×222 m), 12 Frigate Access Tunnel (2×1),
13 Overgrown Cavern (2×1), 18 Transport Tunnel C (3×3), 22 Transport to Chozo Ruins East (1×2),
10 Root Tunnel (3×1), 15 Root Cave (2×4), 19 Transport Tunnel B (3×1), 20 Arbor Chamber (2×1),
23 Transport to Magmoor Caverns East (1×2).

**D — Fragata afundada** (subaquática; no Prime precisa da Gravity Suit), 14 salas, 56 telas:
17/21/24 Main Ventilation Shaft C/B/A, 25 Reactor Core, 26 Reactor Access, 27 Cargo Freight Lift,
28 Savestation, 29 Deck Beta Transit Hall, 30 Biohazard Containment, 31 Deck Beta Security Hall,
32 Biotech Research Area 1, 33 Deck Beta Conduit Hall, 34 Connection Elevator to Deck Beta,
35 Hydro Access Tunnel. Cadeia 12 → 17 → 21 → 24 → 25 → 26 → (27, 28); 27 → 29 → … → 35 → 36.
Onze nomes repetem salas da fragata (ex.: "Reactor Core"): as chaves das salas precisam de prefixo.

**E — Grande Árvore**, 8 salas, 50 telas: 36 Great Tree Hall (3×6), 37 Great Tree Chamber,
38 Transport Tunnel D, 39 Life Grove Tunnel, 40 Transport Tunnel E, 41 Transport to Chozo Ruins
South, 42 Life Grove (4×4), 43 Transport to Phazon Mines East.

Total proposto: **44 salas, 249 telas.**

### A área 0 do SM hoje (ROM `base/sm_fix.sfc`, lida com `tools/smlib/room_reader.py`)

- Crateria vanilla: 34 salas, 320 telas, 310 tiles no mapa, caixa x 6–56 / y 1–19 na grade 64×32,
  **70 bytes** de mapa explorado. A cota de SRAM da área 0 é **74 bytes** (`$81:8131`,
  `tools/build.py:268`). 249 telas cabem na grade; caber em 74 bytes depende da disposição
  (cada byte = 8 tiles de uma linha). A spec 03 (cota de SRAM) cuida do total entre as áreas.
- Landing Site vanilla `$8F:91F8`: estado padrão com tileset 0, música `$06/$05`, FX `$83:80C0`
  (tipo `$0A` = chuva). Tilesets da Crateria: 0 (Crateria de cima, 21 estados) e 2 (Crateria de
  baixo/cavernas, 23 estados). O tileset 1 ("Red Crateria") não é usado por nenhum estado.
- Load stations da área 0: 19 entradas; a 0 = Landing Site na nave (sala `$91F8`, porta `$896A`).
- A nave do SM na área 0 já faz o que o Tallon precisa: os patches de `$A2` só mudam a área 3
  (`tools/frigate/ending.py:218-266`); fora dela a nave recarrega e oferece salvar na **load station 0
  da área 0** (`research/sm_room_format.md` §13) e só decola com o evento `$0E`, que nunca é ligado.
- Espaço livre no banco `$8F` depois da fragata (build numa cópia do projeto, nesta pesquisa):
  ocupado até `$8F:F015`, sobram **4075 bytes**. A fragata gastou 1638 bytes (~58 por sala, com
  rotinas). 44 salas ≈ 2,6 KB: cabe, mas sobra pouco para os próximos mundos (ver Riscos).
  `$83` usou só 744 de 21146 bytes; `$A1` 503 de 5167; `$B4` 181 de 2888.
- Inimigos que a Crateria vanilla usa (nome de debug lido em `$B4` pelo ponteiro `+$3E` do
  cabeçalho da espécie em `$A0`): ZOOMER `$DCFF`, MZOOMER `$DD3F`, SKREE `$DB7F`, WAVER `$D63F`,
  RIPPER `$D47F`, KAGO `$E7FF`, BOYON `$CEBF`, piratas BATTA `$F353`/`$F653`… Outros úteis em
  outras áreas: SABOTEN `$CFFF` (cacto que atira espinhos), SIDE `$D9BF` (sidehopper), ZEELA `$DC7F`.

### O que é preso à fragata no código (precisa generalizar)

| Onde | O quê |
|------|-------|
| `tools/build.py:24-26` | importa só `frigate.*` (`ROOMS`, `ENEMIES`, `pausemap`, `ending`…) |
| `tools/build.py:35-36` | `FRIGATE_AREA = 3`, `FRIGATE_TILESET = 4` |
| `tools/build.py:39-41`, `129-144` | `state_bytes` usa tileset 4, fundo/scroll e música da Wrecked Ship para toda sala |
| `tools/build.py:44-52`, `359-374` | sala do chefe e do Ridley fixas por chave (`reactor_core`, `airlock`) |
| `tools/build.py:64`, `429-434` | uma única save station (índice 1, `assert len(save_rooms) == 1`) |
| `tools/build.py:173` | timer lê `$7ED82B` (boss bits da área 3) |
| `tools/build.py:204-206`, `435-456` | novo jogo: área 3, itens da intro do Prime |
| `tools/build.py:236-244` | `write_load_station` sempre na tabela da área 3 |
| `tools/build.py:261-281` | lista de bytes de mapa só da área 3; `assert` com as contagens vanilla e com o espaço de 32 bytes da área 3; doadora fixa = área 5 |
| `tools/build.py:284-321` | mapa de pausa: `assert` do endereço vanilla da área 3, ícones trocados por `replace_checked` com as coordenadas vanilla da Wrecked Ship, nome "FRIGATE" |
| `tools/build.py:358` | cabeçalho com área fixa e índice de sala 0 |
| `tools/build.py:394-397` | door ASM do timer por chave de sala |
| `tools/build.py:421-424` | recolore a paleta do tileset 4 |
| `tools/build.py:476-480` | `manifest.json` por chave de sala (chaves repetidas entre mundos colidem) |
| `tools/frigate/rooms.py:6`, `18`, `67` | supõe Space Jump; estilo `FRIGATE` fixo em `RoomDef.level()` |
| `tools/frigate/ending.py:218-248` | patches da nave só para a área 3 (está certo; não mexer) |
| `tools/frigate/enemies.py:30-34`, `96` | só 2 espécies; nome do enemy set "FRIGATE" |
| `tools/smlib/level.py:26` | `Palette` padrão = metatiles da Wrecked Ship |
| `tools/smlib/style.py:139` | `FRIGATE = Style()`: metatiles do tileset 4 |
| `tools/smlib/palette.py:7` | `FRIGATE_ROWS` (recolor da Wrecked Ship) |
| `tools/validate.py:11`, `23-26`, `235-266` | alcance supõe Space Jump + Morph; progressão só "chefe vivo/morto" |
| `tools/preview_rooms.py:13` | `load_tileset(rom, 4, 3)` |
| `tests/run_tests.py:15-16`, `35`, `94`, `110`, `198` | importa `frigate.rooms`; endereços de RAM da área 3 fixos |

O que já é genérico e se reaproveita: `tools/frigate/pausemap.py` (recebe uma lista de salas),
`tools/smlib/canvas.py`, `level.py` (portas usam metatiles CRE `$0xx`, comuns a todos os
tilesets), `compression.py`, `room_reader.py`, a forma de declarar salas e `LINKS` de
`rooms.py`, as checagens de portas/mapa do `validate.py`, o `Allocator`.

## Mudança proposta

### Decisões do épico

1. **Área 0 = Tallon.** Salas novas em `$8F` com byte de área 0; as salas vanilla da Crateria ficam
   na ROM, sem ligação (como as da Wrecked Ship hoje).
2. **Chegada:** load station 0 da área 0 aponta para a Landing Site do Tallon, ao lado da nave.
   A nave vanilla já salva nessa estação (ver acima). A sala `Savestation` (P28) vira load
   station 1 da área 0 (região D, fora do MVP).
3. **Perda de itens:** ao chegar, a Samus fica só com o Power Beam (sem mísseis, 99 de energia),
   como no Prime (só sobram Power Beam, visores e Power Suit). Quem zera é a transição da spec 05.
   **Contrato com a spec 05:** o final da fragata termina com área = 0, load station = 0,
   `$09A2/$09A4/$09A6/$09A8 = 0`, mísseis 0/0, energia 99/99, e grava o save. Enquanto a 05 não
   existir, a 07e entrega um caminho de teste que faz isso por RAM (sem mexer no final atual).
4. **Uma sala do Prime = uma sala do SM**, ligações iguais ao grafo do Prime (como na fragata).
5. **Visual:** superfície com tileset 0 + FX de chuva `$83:80C0` nas 6 salas com chuva do Prime;
   cavernas e túneis com tileset 2; fragata afundada com o tileset 4 já recolorido (o recolor da
   fragata é global e combina) + FX de água. Música da Landing Site vanilla (`$06/$05`), lida da ROM.
6. **Sem map station** no Tallon (fiel ao Prime). O mapa só mostra o que foi explorado.
7. **Elevadores para outros mundos:** salas de transporte construídas, com o elevador como
   cenário que não funciona (beco sem saída, igual ao Prime antes de existirem os outros mundos).
   Artifact Temple sem teleporte e sem Meta Ridley.
8. **Regiões ligadas aos poucos:** a tabela tem as 44 salas, mas o build só monta as regiões
   ativadas. Uma porta para uma região desligada vira parede (sem porta no level), e o validador
   ignora a ligação. Assim cada filha entrega algo jogável.

### Inimigos (proposta, refinada na 07i)

| Prime | SM (debug name, `$A0`) | Por quê |
|-------|------------------------|---------|
| Parasite "Platform Zoomer" | ZEELA `$DC7F` | anda nas plataformas e paredes |
| Geemer | ZOOMER `$DCFF` | é o mesmo bicho (Geemer) |
| Beetle (Alpha Beetle) | SIDE `$D9BF` (sidehopper) | inimigo de chão que avança na Samus |
| Seedling | SABOTEN `$CFFF` | atira espinhos como o Seedling |
| Metaree Alpha | SKREE `$DB7F` | o Metaree é o Skree do Prime |
| Space Pirate / Flying Pirate | pirata `$F653` (já usado na fragata) | |
| Wall Crawler Swarm | HZOOMER `$DC3F` (já usado na fragata) | |
| Blood Flower, Jelly Zap, Spank Weed, Drone, Gun Turret | a escolher na 07i | |
| AmbientAI (Chubb Weed), SnakeWeedSwarm, FishCloud | não entram (enfeite/armadilha) | |
| Chozo Ghost, Ridley | fora deste épico | |

No máximo 4 espécies por sala e `$2000` bytes de VRAM de inimigos; a nave ocupa `$1200`, então a
Landing Site fica sem inimigos (no Prime ela também não tem inimigos que atacam).

### Itens (proposta, 07h)

PLMs de item do SM (`research/sm_room_format.md` §5): Missile Expansion → míssil, Energy Tank → E-tank,
Space Jump → Space Jump, X-Ray → X-Ray. Os 2 artefatos não têm item no SM: ficam fora (spec própria
dos artefatos). Índices de bit de item (`$7ED870`) numa tabela única do projeto, sem repetir.
No SM não existe "Missile Launcher": a primeira expansão já libera mísseis (diferença aceita).

### Specs filhas

| # | Spec | Entrega | Esforço | Depende de |
|---|------|---------|---------|------------|
| 07a | Toolchain para várias áreas | `AreaDef` (área, nome, salas, load stations, estilo por sala); `build.py`, `validate.py`, `pausemap`, `manifest` e testes percorrem áreas; chaves com prefixo. **A ROM da fragata sai byte a byte igual** (sha1 do .ips igual ao de antes) | 2–3 d | — |
| 07b | Alcance sem Space Jump | validador com pulo normal (altura medida no emulador e escrita como constante com teste), loadout por área | 1–2 d | 07a |
| 07c | Estilo da Crateria | `Style` para os tilesets 0 e 2 (metatiles tirados das salas vanilla), FX de chuva, música; `preview_rooms.py` por área | 2 d | 07a |
| 07d | Grafo e mapa do Tallon | 44 salas com tamanho, posição no mapa e `LINKS`; regiões ligáveis; mapa ≤ 64×32 sem sobreposição e portas encostadas | 2 d | 07a |
| 07e | Chegada na Landing Site | load station 0 da área 0, nave na Landing Site salvando, perda de itens (contrato com a 05), caminho de teste | 2 d | 07d, 05 (contrato) |
| 07f | Mapa de pausa e minimapa da área 0 | tilemap, nome "TALLON", ícone da nave, lista de elevadores, lista de bytes da SRAM | 1–2 d | 07d, 03 |
| 07g | Salas da região A (MVP) | layouts jogáveis sem Space Jump das 5 salas do MVP e portas fechadas para o resto | 2 d | 07b, 07c, 07d |
| 07h | Itens | PLMs dos 9 mísseis, 2 E-tanks, Space Jump, X-Ray, conforme as regiões existirem | 1–2 d | 07g |
| 07i | Inimigos | tabela acima, quantidades da camada 0 do Prime | 2–3 d | 07g |
| 07j | Elevadores de mentira | 5 salas de transporte + Artifact Temple sem teleporte | 1 d | 07d, 07c |
| 07k | Regiões B e C | templo, cachoeira, crash site, raízes (15 salas) | 3 d | 07g, 07j |
| 07l | Região D (fragata afundada) | 14 salas, água, save station P28 = load station 1 | 3 d | 07k |
| 07m | Região E (Grande Árvore) | 8 salas | 2–3 d | 07l |

### Grafo de dependências

```
05 (contrato) ─────────────┐
                           v
07a ─┬─> 07b ──────┐      07e ──┐
     ├─> 07c ──────┼─> 07g ─┬──> 07h
     └─> 07d ──┬───┘   │    └──> 07i
               ├─> 07e │
               ├─> 07f <── 03
               └─> 07j ┴─> 07k ──> 07l ──> 07m
```

### Por que nesta ordem

- 07a primeiro e sozinha: mexe em tudo e tem um teste perfeito (ROM igual). Depois dela, cada filha
  só acrescenta dados de uma área nova.
- 07b antes de qualquer sala: sem Space Jump, o validador atual ("ar conectado = alcançável")
  aprovaria salas impossíveis. É o maior risco de softlock.
- 07c e 07d podem correr em paralelo (estilo vs. dados), mas os builds não: um item por vez.
- 07e e 07f fecham o ciclo jogável (chegar, salvar, ver o mapa) antes de crescer o mundo.
- Itens e inimigos depois das salas do MVP, regiões maiores no fim (mais telas, mais risco de cota).

### MVP (menor Tallon jogável ligado à fragata)

07a + 07b + 07c + 07d + 07e + 07f + 07g:

- Landing Site (com a nave, salva na load station 0) → Canyon Cavern → Tallon Canyon → Transport
  Tunnel A → Transport to Chozo Ruins West (elevador de enfeite). 5 salas, 36 telas. É o caminho que
  o Prime permite sem nenhum item.
- Saídas para Gully, Alcove, Temple Hall, Waterfall Cavern e Root Tunnel fechadas (parede).
- Sem itens e sem inimigos (entram na 07h/07i). Chuva na Landing Site e na Tallon Canyon.
- Mapa de pausa "TALLON" com as 5 salas; o explorado sobrevive ao save.

## Critérios de aceite (do épico; cada filha detalha os seus)

1. Depois da 07a, `build/metroid_prime_snes.ips` tem o mesmo sha1 de antes
   (`e9b0db220a7f5d7540b02b2ccbbd6e3889e28555 (ROM depois das specs 01–06)`) e os 20 testes passam.
2. `python3 -I tools/validate.py` checa as duas áreas, com o loadout de cada uma (fragata: Space Jump
   + Morph; Tallon: só pulo normal), e dá 0 problemas.
3. Teste `tallon_chegada`: depois da fragata (ou do caminho de teste), área 0, sala Landing Site,
   itens zerados, jogo em estado 8.
4. Teste `tallon_nave_salva`: agachar na nave → refil + "save?" → sim → load station 0 da área 0;
   o continue volta à Landing Site do Tallon (não à Crateria vanilla).
5. Teste `tallon_rota_mvp`: a Samus atravessa as 5 salas do MVP pelas portas, ida e volta.
6. Teste `tallon_mapa_salvo`: salas exploradas continuam no mapa depois de salvar e carregar.
7. Imagens em `build/tests/`: Landing Site com a nave e chuva, Tallon Canyon, mapa de pausa.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | checagens por área; alcance sem Space Jump; mapa da área 0; bytes de SRAM ≤ cota | +4 |
| run_tests.py | chegada, nave salva/continue, rota MVP, mapa salvo (MVP); itens, inimigos, elevadores (depois) | +4 (+3) |
| imagem | Landing Site, Tallon Canyon, mapa de pausa | +3 |
| build | ROM da fragata igual depois da 07a | 1 |

## Riscos e reversão

- **Pulo sem Space Jump:** a fragata nunca precisou disso. Salas desenhadas "no olho" podem prender a
  Samus. Mitigação: 07b antes das salas, e teste de rota no emulador.
- **Cota de SRAM do mapa (74 bytes na área 0):** a disposição das 44 salas pode passar disso. A
  fragata já pegou 12 bytes da Tourian. Depende da spec 03; a 07d mede os bytes no validador.
- **Espaço no banco `$8F`:** sobram 4075 bytes; o Tallon deve gastar ~2,6 KB. Chozo (64 salas) não
  cabe no que sobrar. Fica para uma spec própria (reaproveitar o espaço das salas vanilla da Crateria
  em `$8F`, depois de checar quem ainda aponta para elas: Ceres → `$91F8`, load stations, elevadores).
- **Tela de continue/seleção de área** ainda mostra os nomes do SM (spec 01).
- **Recolor de paleta é global por tileset:** se o Tallon recolorir o tileset 0 ou 2, muda também
  qualquer outra área que usar o mesmo tileset (Chozo e Phazon Mines no futuro).
- **Nave na área 0:** ela salva na estação 0 da área 0 em qualquer sala; se um dia houver uma
  segunda nave, isso quebra. Hoje só existe uma por área.
- Reversão: tudo vem de `tools/`; reverter o código e reconstruir basta.

## Fora de escopo

- Final da fragata e a viagem até Tallon IV (spec 05; aqui só o contrato de chegada).
- Elevadores funcionando, Chozo Ruins e demais mundos, Impact Crater.
- Meta Ridley no Artifact Temple, artefatos e o templo funcionando.
- Scan visor, logbook, dicas (HUDMemo) e cenas de câmera do Prime.
- Map station no Tallon (o Prime não tem).
- Recuperar o espaço das salas vanilla da Crateria em `$8F`.

## Definição de pronto do épico

- As 13 filhas em estado `verificada`, com validate + build + testes rodados por quem revisa.
- As 44 salas do Tallon existem e ligam como no Prime; as 6 saídas para outros mundos estão
  construídas como becos sem saída.
- A Samus chega do fim da fragata à Landing Site sem itens, salva na nave, continua de lá, pega os
  13 itens do SM (9 mísseis, 2 E-tanks, Space Jump, X-Ray) e chega às regiões que o equipamento dela
  permite, sem softlock (validador + rota no emulador).
- Mapa de pausa e minimapa "TALLON" corretos e preservados no save.
- README e HANDOFF atualizados.

## Desvios (preenchido na implementação)

- Depois da 07m (23/10/2026): as 13 filhas verificadas, as 44 salas na ROM e ligadas como no Prime, as 6
  saídas para outros mundos construídas como becos. Da definição de pronto falta "pega os 13 itens": desde a
  07k as travas são as do Prime, então os itens estão na ROM nos lugares e fases do Prime (validador), mas
  no jogo só o míssil da Landing Site se pega a pé — os outros esperam Bombas, gelo, Gravity Suit, Wave/
  Thermal, Spider/Boost/Power Bombs, grapple, plasma (outros mundos). Por isso o épico continua "aprovada".
- 07m: no Great Tree Hall a ordem das portas segue o mapa da 07d (Hydro no teto), não as alturas do Prime.
- Fechamento (09f, 23/10/2026), conferido item a item contra a definição de pronto: as 13 filhas `verificada`; as 44 salas na ROM,
  ligadas como no Prime, e as 6 saídas para outros mundos como becos (07j/07k/07m); a Samus chega do fim da fragata sem itens à
  Landing Site, salva na nave e continua de lá (07e, `tallon_chegada`, `tallon_nave_salva`); **pega os 13 itens do SM** (9 mísseis,
  2 E-tanks, Space Jump, X-Ray) e chega a todas as regiões sem softlock: validador (rodadas declaradas, volta à nave e `stuck` em
  cada rodada, 0 problemas) e rota no emulador (`tallon_cadeia_completa`: do fim da fragata, os 13 + os 7 itens de trava pegos
  andando, salvo e continuado); mapa de pausa e minimapa no save (07f); README e HANDOFF atualizados. Desvio do Prime: os itens
  que abrem as travas não vêm dos outros mundos, ficam no próprio Tallon (épico 09, decisão 3). Estado → `verificada`.
