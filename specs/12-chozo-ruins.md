# 12 — Chozo Ruins (épico)

Estado: **verificada** (28/10/2026: as 13 filhas, 12a–12m e 12g2, `verificada`; definição de pronto conferida abaixo,
"Verificação do épico"; validate 136/284/0, sha1 `0bcb610a…dcaf0` em dois builds, 76/76). Antes: 26/10/2026 pesquisa e decisões
do usuário (opção B, área 1, as duas travas novas, chefes depois, as 64 salas por região).
Esforço estimado: 30–40 dias no total, em ~13 filhas de 0,5–3 dias (a Chozo tem 64 salas; o Tallon, 44, levou 13 filhas + o épico 09).
MVP (12a–12f): 8–10 dias.

## Contexto

O Tallon Overworld está pronto (épicos 07, 09, 10, 11): 44 salas e 20 itens a pé da nave, em 7 rodadas. No Prime, o primeiro
elevador que a Samus usa (Transport to Chozo Ruins West) leva à Chozo Ruins, o segundo mundo. Hoje esse elevador é **de enfeite**
(spec 07j): a sala existe, a plataforma existe, nada acontece.

O épico 09 resolveu "o Tallon inteiro jogável a pé" pondo no próprio Tallon itens que, no Prime, são de outros mundos — e três
deles são **da Chozo** no Prime (Morph Ball, Bombas, Ice Beam). Por isso a Chozo não pode simplesmente copiar a lista de itens do
Prime. Este épico levanta os fatos, propõe opções para essa tensão (sem decidir: é do usuário), divide o trabalho em filhas e
implementa só as filhas de toolchain que servem a qualquer opção.

## Estado atual (verificado)

Antes desta etapa, na pasta real: `python3 -I tools/validate.py` → "72 salas, 148 portas, 0 problemas" (linha do Tallon "44 salas
construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"); `.ips` sha1 `3919c3c73d46afc45ffd4eb51083daebbe8264ff`; testes 53/53.
Roteiros desta pesquisa no scratchpad da sessão (`…/scratchpad/s12/`), nunca em `build/`: `chozo_pick.py` (itens e contagens de
objetos do Prime), `tele.py` (destino dos elevadores), `regions.py` (regiões e tamanhos), `tilesets.py` (uso de tileset e prévias),
`roomcmp.py` (comparações com o ponteiro da sala), `block.py` (dono de cada byte de um pedaço do `$8F`).

### A Chozo Ruins no Prime (dados)

Fonte: `research/prime_worlds.json` (MLVL "Chozo Ruins") e os objetos de `research/prime_fs` (retro-data-structures 0.44.1;
nome do `Pickup` pelos bytes crus, como na 07h; item = 1ª palavra depois do nome + 60 bytes, enum de itens do Prime: conhecimento,
conferido pelos 2 artefatos do Tallon, Truth = 29 no Artifact Temple e Chozo = 35 no Life Grove, como o Prime tem).

- **64 salas** (índices 0–63), **136 entradas de dock = 68 ligações** (todas com volta). O grafo tem ciclos (68 ligações em 64 salas).
- **3 salas de save** (Save Station 1, 2, 3: P22, P39, P59) e **1 map station** (P34 "Map Station", na Ruined Gallery).
- **4 elevadores** (`WorldTeleporter`, destino lido pelo id de MREA nos bytes de cada um, `tele.py`):

| P# Chozo | Sala | Vai para | Do lado do Tallon (nossa chave) |
|---|---|---|---|
| 0 | Transport to Tallon Overworld North | Tallon P14 Transport to Chozo Ruins West | `tallon_transport_chozo_west` (região A, rodada 0) |
| 62 | Transport to Tallon Overworld East | Tallon P22 Transport to Chozo Ruins East | `tallon_transport_chozo_east` (região C, rodada 4: gelo) |
| 63 | Transport to Tallon Overworld South | Tallon P41 Transport to Chozo Ruins South | `tallon_transport_chozo_south` (região E, rodada 5) |
| 24 | Transport to Magmoor Caverns North | Magmoor P0 | — (Magmoor não existe: fica de enfeite) |

- **Itens** (35 `Pickup` de verdade; os outros são sobras de inimigo "Pickup - …"):

| P# | Sala | Item (enum do Prime) | Existe no SM? |
|---|---|---|---|
| 9 | Ruined Shrine | **Morph Ball** (16) | sim — **já está no Tallon** (Chozo West, 09d) |
| 48 | Burn Dome | **Bombas** (6) | sim — **já está no Tallon** (Artifact Temple, 09d) |
| 61 | Antechamber | **Ice Beam** (1) | sim — **já está no Tallon** (Root Cave, 09b) |
| 36 | Hive Totem | Missile Launcher (4, 5/5; nome `P_Missile_Launcher` sem "-component") | não: no SM a 1ª expansão já libera mísseis (épico 07) |
| 41 | Watery Hall | **Charge Beam** (10) | sim (PLM `$EEEB` = `$EED7` + 4·5, research §5) — não está no jogo |
| 37 | Sunchamber | **Varia Suit** (22) | sim (`$EF07` = `$EED7` + 4·12) — não está no jogo |
| 21 | Tower of Light | Wavebuster (28, combo do Charge) | não |
| 20 | Magma Pool | expansão de Power Bomb (7) | sim (o "Power Bomb" do SM já é expansão de +5) |
| 2 (×3), 8, 9 (×2), 11, 16, 18, 28 (×2), 32, 38, 41, 45 (×2), 48, 49, 53 | Main Plaza, Ruined Fountain, Ruined Shrine, Vault, Ruined Nursery, Training Chamber Access, Ruined Gallery, Gathering Hall, Watery Hall Access, Watery Hall, Dynamo, Burn Dome, Furnace, Crossway | 19 Missile Expansions | sim |
| 2, 12, 30, 49, 52 | Main Plaza, Training Chamber, Transport Access North, Furnace, Hall of the Elders | 5 Energy Tanks | sim |
| 27, 37, 57 | Tower Chamber, Sunchamber, Elder Chamber | 3 artefatos (Lifegiver 33, Wild 32, World 38) | não (fora desde o épico 07) |

  **Correção de uma premissa do pedido**: Wave Beam, Boost Ball e Spider Ball **não** são da Chozo no Prime — são de Phendrana
  (Chapel of the Elders, Phendrana Canyon, Quarantine Cave: tabela da spec 09, dados). A Chozo tem Morph, Bombas, **Ice**, Missile
  Launcher, Charge, Varia, Wavebuster, 1 expansão de PB, 19 mísseis, 5 E-tanks e 3 artefatos. **Conflito com o Tallon: Morph, Bombas e
  Ice.** Ainda não postos em lugar nenhum do jogo: Charge, Varia, os mísseis/E-tanks/PB da Chozo e os artefatos.
- **Inimigos** (todas as camadas somadas, `chozo_objs.txt`): AmbientAI 40, Beetle 31, SnakeWeedSwarm 24, ChozoGhost 20, WarWasp 15,
  Eyeball (Eyon) 14, Oculus 14, WallCrawlerSwarm 13, SpankWeed 12, Puffer 12, FishCloud 8 (enfeite), Parasite 8, PuddleToadGamma (Stone
  Toad) 6, PuddleSpore 2, AtomicAlpha 1, ActorContraption 1; **chefes**: Flaahgra (+ 4 FlaahgraTentacle, Sunchamber), Hive Mecha (Hive
  Totem) e Incinerator Drone (Burn Dome) — os nomes dos dois últimos são conhecimento (o tipo nos dados é genérico).
- **Água** (objeto `Water`, 42 objetos em **16 salas**): Ruined Fountain, Meditation Fountain, Arboretum, Magma Pool (lava no Prime:
  conhecimento), Tower of Light, Ruined Gallery, Gathering Hall, Totem Access, Sun Tower Access, Hive Totem, Sunchamber, Watery Hall
  Access, Watery Hall, Energy Core, Burn Dome, Reflecting Pool.

### Regiões (agrupamento pelo grafo de portas, como na 07)

Tamanho SM = estimativa pela regra que a tabela do Tallon segue (largura ≈ maior lado horizontal ÷ 30 m, altura ≈ altura ÷ 30 m,
largura 1–6, altura 1–4; conferida contra as 44 salas do Tallon em `regions.py`); a filha 12c desenha a tabela de verdade.

**A — Entrada, Main Plaza e Torre da Luz** (12 salas, ~45 telas): 0 Transport to Tallon North, 1 Ruins Entrance, 2 Main Plaza
(6 portas: o eixo), 3 Ruined Fountain Access, 4 Ruined Shrine Access, 5 Nursery Access, 6 Plaza Access, 7 Piston Tunnel, 9 Ruined
Shrine, 15 Tower of Light Access, 21 Tower of Light, 27 Tower Chamber.

**B — Ala norte: Nursery, Gallery, Hive Totem e Vault** (12 salas, ~27 telas): 10 Eyon Tunnel, 16 Ruined Nursery, 22 Save Station 1,
23 North Atrium, 28 Ruined Gallery, 33 Totem Access, 34 Map Station, 36 Hive Totem, 30 Transport Access North, 24 Transport to
Magmoor North, 17 Vault Access, 11 Vault.

**C — Fonte, Arboreto, Sunchamber (Flaahgra) e Sun Tower** (15 salas, ~62 telas): 8 Ruined Fountain, 13 Arboretum Access,
14 Meditation Fountain, 18 Training Chamber Access, 12 Training Chamber, 20 Magma Pool, 19 Arboretum, 25 Sunchamber Lobby,
31 Sunchamber Access, 37 Sunchamber, 26 Gathering Hall Access, 32 Gathering Hall, 39 Save Station 2, 29 Sun Tower, 35 Sun Tower Access.

**D — Watery Hall, Energy Core e Burn Dome** (11 salas, ~35 telas): 38 Watery Hall Access, 40 East Atrium, 41 Watery Hall,
42 Energy Core Access, 43 Dynamo Access, 44 Energy Core, 45 Dynamo, 46 Burn Dome Access, 48 Burn Dome, 47 West Furnace Access, 49 Furnace.

**E — Elders, Reflecting Pool e as saídas para o Tallon** (14 salas, ~33 telas): 50 East Furnace Access, 51 Crossway Access West,
52 Hall of the Elders, 53 Crossway, 54 Reflecting Pool Access, 55 Elder Hall Access, 56 Crossway Access South, 57 Elder Chamber,
58 Reflecting Pool, 59 Save Station 3, 60 Transport Access South, 61 Antechamber, 62 Transport to Tallon East, 63 Transport to Tallon South.

Ligações entre regiões (9): A–C (3–8, 7–12), A–B (5–10, 6–11), B–C (24–29), C–D (32–38, 32–40), D–E (49–50, 49–51).
**Total: 64 salas, ~202 telas** (o Tallon tem 251; a estimativa é solta).

### Ponto de ligação com o Tallon

`tallon_transport_chozo_west` (P14, região A do Tallon, alcançável na rodada 0): 2×2 telas, elevador de enfeite desenhado por
`tools/tallon/layouts.py elevator()` (spec 07j), com a **Morph Ball** em cima da plataforma (09d). Os outros dois (Chozo East na
rodada 4, com a Gravity Suit na plataforma; Chozo South na rodada 5, com o Plasma) seguem o mesmo desenho. No SM um elevador entre
áreas é uma porta com a flag `$80` (elevador) e `$40` (troca de área: salva/carrega o mapa explorado) na entrada de porta em `$83`
(research §3, conferido pelo C `LoadDoorHeader`); a plataforma que desce é um inimigo próprio nas salas de elevador vanilla
(conhecimento: espécie e PLMs a conferir na filha 12e). Nada disso existe ainda no projeto: as nossas portas usam `$00`.

### A área do SM

Livres: 1 (Brinstar), 2 (Norfair), 4 (Maridia) — 0 é o Tallon, 3 a fragata, 5 reservada à Impact Crater (`mapsave.py`), 6 Ceres e 7
debug com código próprio. Código vanilla que muda por área (C `vendor/sm/src`, `grep area_index`):

| Área | Diferenças | Peso |
|---|---|---|
| 1 | um caso do raio X que só desenha um bloco especial na área 1 (`sm_91.c:1065`, `$91:CF3E`); ladrão do Torizo dourado (`sm_aa.c:150`: área ≠ 0) | quase nada |
| 2 | propriedades dos projéteis inimigos por área (`sm_86.c:1163`); congelar com o gelo dura 300 quadros em vez de 400 (`sm_a0.c:2751`, `2789`); o Ridley (`sm_a6.c`) | **muda o jogo** (o gelo do Tallon congelaria menos na Chozo) |
| 4 | o mapa de pausa rola 24 px a mais à esquerda (`sm_82.c:1811`) | cosmético |

**Recomendação: área 1.** Implementado como `areas.CHOZO_AREA = 1` na filha 12b (a confirmar: trocar custa uma linha e uma
entrada de `VANILLA_PAUSE`). A área 1 tem 19 load stations vanilla (`roomgraph.STATION_COUNTS`) e lista do mapa salvo de até 80
bytes no lugar vanilla (`mapsave.LIST_ROOM`).

### Visual (tilesets, inimigos, FX)

Uso de cada tileset (bytes de todas as salas vanilla e das nossas, `tilesets.py`; demos = `DEMO_SCENES`):

| Tileset | Salas vanilla | Nas demos | Nossas | Para a Chozo |
|---|---|---|---|---|
| 0C Maridia rochosa | 27 | — | — | **melhor candidato**: tijolos e colunas com chão de areia (prévia `s12/ts/ts0C_D5A7.png`); recolorir para arenito não muda nada que o jogador veja hoje |
| 0B Maridia arenosa | 22 | `$D0B9` (conjunto 3, só com SRAM "supermetroid") | — | cavernas de areia e plantas (Arboretum, fontes); recolorir muda essa demo |
| 08 corredor das estátuas | 1 | — | — | metal azul, poucas peças |
| 06 / 07 Brinstar | 26 / 17 | 7 / 3 salas | — | recolorir muda as demos (spec 11, B2) |
| 09 / 0A Norfair | 52 / 14 | 2 / 1 | — | ruínas de Lower Norfair; idem |
| 03, 0D, 1A, 1B, 1C | 2, 15, 1, 1, 1 | 1A: `$A59F` | — | salas especiais (Old Tourian, Tourian, chefes) |

Recolor é global por tileset (`build.py` passo 3): 0C não é usado por nenhuma sala nossa nem demo. Prévia das salas vanilla maiores de
cada candidato em `…/scratchpad/s12/ts/montage.png`.

Inimigos (nomes de debug lidos em `$B4` pelo ponteiro `+$3E` de cada espécie em `$A0`; a escolha é conhecimento, a filha confere):
Beetle → SSIDE `$D93F` (já usado); Parasite → ZEELA `$DC7F` (já usado); Wall Crawler → HZOOMER `$DC3F` (já usado); Spank Weed →
SABOTEN `$CFFF` (já usado); **War Wasp → HACHI1 `$EABF`** (Kihunter; "hachi" = vespa); Puffer → PUYO `$CFBF` ou PUU `$E8BF`; Oculus →
VIOLA `$DABF`; Eyon → EYE `$E6BF`; Chozo Ghost → ATOMIC `$E9FF` (flutua e atravessa); Stone Toad, Snake Weed, AmbientAI, FishCloud
fora (como no Tallon). Chefes: Flaahgra ↔ Spore Spawn (planta-chefe; é da área 1), Hive Mecha e Incinerator Drone sem par claro.

FX: água em sala inteira (`build.WATER_FX`, precedente da fragata afundada 07l: água parcial mudaria o pulo medido); lava (FX tipo 2,
research §7) para a Magma Pool; chuva não (a Chozo não tem `Rain Simulator` nos dados).

### Mapa e SRAM

- Mapa de pausa 64×32 em área própria: ~202 telas cabem (o Tallon ocupa 251). Map station na P34 (o build já faz map station: Map
  Facility da fragata).
- SRAM do mapa (`mapsave`): hoje 404 de 1280 bytes (vanilla 327 + fragata 30 + Tallon 47); **livres 876**. A lista da área 1 no lugar
  vanilla aceita até 80 bytes (o Tallon, 251 telas, usa 47): cabe com folga. Passando de 80, a lista vai para `$81:EF1A–FEFF`
  (4070 bytes de `$FF`, nota de `mapsave.py`).
- Load stations da área 1: 0 = chegada (Transport to Tallon North); 1–3 = Save Stations 1–3 (os ícones de save da área); chegadas
  pelos elevadores East/South = estações ≥ 8 (fora dos slots de save, como a `$12` do Tallon).
- Bits: itens vanilla 0–`$9A`, Tallon `$A0–$B3` → Chozo a partir de `$B4` (o vetor `$7ED870` tem 512 bits); portas vanilla até `$A9`,
  Tallon `$B0–$B2` → Chozo a partir de `$B3`.

### Espaço por banco (números da spec 11; custo pelas 72 salas de hoje)

| Banco | Livre hoje | A Chozo pede (64 salas, 68 ligações) | Cabe? |
|---|---|---|---|
| `$8F` | 1781 (`$8F:F90B`) | ~3500 (≈ 55 por sala: cabeçalho + estado 39, listas) | **não sozinho**; com a 12a (+2254 do bloco órfão `$8F:D4EF–DDBD`) = 4035: **cabe com ~500 de folga** |
| `$83` | 19294 | ~1700 (12 por porta, 136 + estações) | sim |
| `$A1` / `$B4` | 3851 / 2488 | ~16 por inimigo, ~20 por set | sim |
| `$84` | 3225 | porta de Charge (se houver) ~100 | sim |
| `$A0` | 1985 | só se um chefe pedir espécie própria | sim |
| nível / fixo | 500129 / 500297 | ~25 KB / paleta e tabela do tileset recolorido | sim |
| SRAM do mapa | 876 | ≤ 80 | sim |

Mais `$8F` se faltar (pela linha "órfãs" da spec 11): `$8F:92B3–9878` (1478 bytes, só órfãs da Crateria; contém `$96BA` e `$9804`,
que o código compara: entram partidos em volta deles) e `$8F:C49B–C8C6` (1068, só órfãs de Maridia). A checagem da 12a
(`check_reclaimed`) prova cada faixa nova antes de usar.

## Mudança proposta

### A tensão dos itens: opções (decisão do usuário)

**(A) Fiel: devolver Morph, Bombas e Ice à Chozo e refazer a rota do Tallon.**
Morph na Ruined Shrine, Bombas na Burn Dome, Ice na Antechamber, Charge na Watery Hall, Varia na Sunchamber. No Tallon, os três
lugares (plataforma da Chozo West, chão do Artifact Temple, prateleira da Root Cave) ficam com míssil/E-tank ou vazios.
- Prós: a ordem do Prime (o Morph na Ruined Shrine é o momento mais lembrado da Chozo); o elevador vira caminho obrigatório, como no Prime.
- Contras: **reescreve o épico 09** (verificado): rodadas, `FIRST_ROUND`, `Item.round`, o passeio passa a cruzar áreas antes de o Tallon
  andar; os testes `tallon_cadeia_completa`, `tallon_morph_e_bombas`, `tallon_gelo` e as 3 rotas cegas que pegam o Morph mudam; a
  tabela de rodadas do Tallon (44 salas, 20 itens em 7 rodadas) deixa de valer. E fica fiel só pela metade: Wave, Gravity, Plasma e
  Power Bomb continuam no Tallon. +4–6 dias.

**(B) Tallon intacto; a Chozo leva o que ainda não tem lugar, e travas novas que usam isso.**
A Chozo ganha Charge (Watery Hall), Varia (Sunchamber), os 19 mísseis + o "launcher" como míssil, 5 E-tanks, a expansão de PB
(Magma Pool) e, se o usuário quiser, os artefatos. Nos lugares do Prime de Morph/Bombas/Ice (Ruined Shrine, Burn Dome, Antechamber)
vai um míssil ou E-tank (a Ruined Shrine já tem 2 mísseis nos dados). Travas da Chozo: as do Prime que usam o que o Tallon já dá (túnel de
Morph, blocos de bomba, portas de gelo/onda, bordas de Space Jump) **mais travas novas** de Charge (porta de feixe do 09a com o bit
de tiro carregado — a conferir no emulador) e de Varia (salas quentes — mecanismo do SM a conferir).
- Prós: os épicos 07/09/10 continuam verificados e a tabela de rodadas do Tallon não muda (nada da Chozo abre trava do Tallon);
  menos risco; as filhas de toolchain servem do mesmo jeito; a Chozo dá habilidades **novas** (Charge, Varia) com uso.
- Contras: menos fiel (o Morph não está na Ruined Shrine); como a Chozo West está na rodada 0, a Chozo inteira se mistura às rodadas do
  Tallon (o validador passa a andar as duas áreas juntas: filha 12m); as travas de Charge/Varia são invenção do demake.

**(C) Híbrido: B + o Morph na Ruined Shrine.**
Tudo como B, mas o Morph sai da plataforma da Chozo West (que ganha um míssil) e vai para a Ruined Shrine (4 salas depois do elevador:
Transport North → Ruins Entrance → Main Plaza → Ruined Shrine Access → Ruined Shrine), alcançável só com o Power Beam.
- Prós: o momento do Prime volta; Bombas e Ice ficam onde estão, então as rodadas do Tallon quase não mudam (o Morph continua na
  rodada 0, só que noutra área).
- Contras: muda o épico 09 num ponto (o Morph): a tabela do Tallon passa a ter 19 itens na área 0 e precisa do elevador funcionando
  **antes** de o Tallon passar da rodada 0; mudam `tallon_morph_e_bombas`, `tallon_cadeia_completa` e as 3 rotas cegas que pegam o Morph.

**Recomendação: (B).** Os três itens em conflito sustentam as rodadas 0–3 do Tallon, que foi provado inteiro (validador e cadeia no
emulador); mexer neles reabre dois épicos verificados para ganhar fidelidade parcial. B deixa o Tallon como está, dá à Chozo duas
habilidades que o jogo ainda não tem, e não fecha a porta para C depois (C é B + mover um PLM e refazer 3 rotas).

### Decisões do épico que não dependem dos itens

1. **Área 1** (12b; confirmada pelo usuário).
2. **Uma sala do Prime = uma sala do SM**, ligações iguais ao grafo do Prime; chaves com prefixo `chozo_` (regra da 07a).
3. **Regiões ligadas aos poucos** (`ACTIVE_REGIONS`, como o Tallon).
4. **Elevadores Tallon ↔ Chozo funcionando** (os 3, feitos na 12e); o da Magmoor North fica de enfeite.
5. **Visual**: tileset 0C recolorido para arenito (sem demo), água de sala inteira, lava na Magma Pool.
6. **`$8F`**: estruturas de sala podem ir ao bloco órfão recuperado (12a); nenhum cabeçalho num endereço que o código compara.

### Filhas (rápido → complexo; toolchain primeiro)

| # | Spec | Entrega | Esforço | Depende da decisão dos itens? |
|---|---|---|---|---|
| 12a | [Segundo espaço do `$8F`](12a-espaco-8f-recuperado.md) (**verificada**) | faixa `RECLAIMED_8F` no alocador, `check_reclaimed`, mutações; ROM igual | 0,5 d | **não** |
| 12b | [Lugar da Chozo na área 1](12b-area-da-chozo.md) (**verificada**) | `CHOZO_AREA`, `VANILLA_PAUSE[1]` lido dos bytes, `check_vanilla_pause`, `check_chozo_slot`; ROM igual | 0,5 d | **não** (só a confirmação da área) |
| 12c | [Grafo, mapa e travas do Prime](12c-grafo-e-mapa-chozo.md) (**verificada**) | tabela das 64 salas (tamanho, posição no mapa 64×32, `LINKS`, regiões); travas do Prime lidas dos dados por dock (portas de cor, blocos, túneis), sem decidir o mecanismo SM; mapa ≤ 80 bytes de SRAM | 2–3 d | **não** (a tabela; o mecanismo SM de cada trava vem na 12g) |
| 12d | [Estilo das ruínas](12d-estilo-das-ruinas.md) (**verificada**) | `Style` do tileset 0C (peças tiradas das salas vanilla, colisão igual), recolor arenito, FX de água/lava, música; prévia | 2 d | **não** |
| 12e | [Elevadores de verdade](12e-elevadores-de-verdade.md) (**verificada**) | as 3 salas de elevador do Tallon levam às 3 da Chozo (becos em arenito, área 1) e voltam (flags `$C0`, plataforma `$D73F`, blocos `$88FC`), Morph e Gravity ao lado das plataformas, mapa/minimapa/SRAM da área 1; testes `elevador_chozo_ida_e_volta`, `elevador_chozo_east_e_south` | 2–3 d | **não** (todas as opções precisam) |
| 12f | [Região A](12f-regiao-a-chozo.md) (**verificada**) | as 12 salas da região A em arenito (a North abre para a Ruins Entrance), travas do Prime com itens do Tallon (vermelha `$B3`, túnel de Morph, portas de onda roxas no 0C, mão única cinza), 7 itens (6 mísseis + 1 E-tank, bits `$B4–$BA`), fundo `$E25A` e música `$1B/$05`; 4 portas para B/C = parede; o validador anda Tallon + Chozo juntos; save/map station ficam com a região B (12i) | 2–3 d | pouco: só o item da Ruined Shrine (B, decidida: míssil) |
| 12g | [Itens e travas novas](12g-itens-e-travas-novas.md) (**verificada**) | Charge Beam `$EEEB` e Varia Suit `$EF07` (bits `$BB`/`$BC`, sem lugar até as regiões D/C), porta de charge (porta de feixe com `AND #$0F10`, PLMs `$F3F5`/`$F3FB`, amarela), calor do SM (objeto `$F761` na lista de FX de paleta da área 1, `HEAT_FX`, `HOT_ROOMS`; modelo: sem a Varia não entra), cena da Varia no lugar; provado numa ROM de teste (`build.py --teste-12g`); antes, a spec 13 corrigiu o item varrido por Power Bomb no motor | 1,5–2,5 d | **sim** |
| 12g2 | [Ajustes da 12g](12g2-ajustes-calor-e-cor.md) (**verificada**) | só a Varia protege do calor (`$8D:E37D`), porta de charge branca (linha 4 e metatiles `$3E8–$3EF` do `$0C`), a ordem da 12f sai, o tiro em porta de cor com a correção da spec 13 (`$84:FFBB`) | 0,5–1 d | decisões do usuário |
| 12h | [Inimigos da Chozo](12h-inimigos-chozo.md) (**verificada**) | camada 0 do Prime nas 12 salas da região A (30 inimigos em 8 salas: Beetle → Sidehopper pequeno, Wall Crawler → HZOOMER, Oculus → Viola, Puffer → Mella), ≤ 1 por tela, justos na chegada; tabela do Prime das regiões B–E só registrada; `check_chozo_enemies`; teste `chozo_inimigos_vivos` | 1–2 d | parcial (a justiça usa as rodadas) |
| 12i | [Região B](12i-regiao-b-chozo.md) (**verificada**) | as 12 salas da região B em arenito (Nursery Access L0 e Plaza Access R0 abertas; a Plaza Access alcançável), 2 portas vermelhas (bits `$B4`, `$B5`: a do Hive Totem ↔ Transport Access North dos dois lados), 6 itens (5 mísseis, o Missile Launcher como expansão, 1 E-tank; bits `$BD–$C2`), o E-tank da praça rodada 3 → 1; **Save Station 1** (estação 1 da área 1, "CHOZO / RUINS" no continue) e **Map Station**; inimigos (Eyon → olho `$E6BF` inofensivo, War Wasp → Mella, Fire Flea → Fireflea); elevador da Magmoor de enfeite | 2 d | sim |
| 12j | [Região C](12j-regiao-c-chozo.md) (**verificada**) | as 15 salas da região C (as paredes da Ruined Fountain Access, do Piston Tunnel e da Magmoor North abertas), 4 portas vermelhas (bits `$B6–$B9`), portas de onda da Training Chamber (cor lida dos dados: só Wave), túneis de Morph com bloco de bomba (copa do Arboretum, pistão), a Sun Tower com o poço de Space Jump (Spider Ball), a **Magma Pool quente** (o único "Area Damage" da Chozo), 6 itens (a **Varia** no pedestal da Sunchamber, 3 mísseis, 1 E-tank, a expansão de PB; bits `$C3–$C7`), **Save Station 2** (estação 2), Metaree → Skree; `check_chozo_locks_mapped`; o alocador do `$8F` corrigido e a faixa recuperada da 12a em uso | 2–3 d | sim |
| 12k | [Região D](12k-regiao-d-chozo.md) (**verificada**) | as 11 salas da região D (as paredes R0/R1 da Gathering Hall abertas; as da Furnace para E ficam), 3 portas vermelhas (bits `$BA–$BC`), túneis com bloco de bomba (o bloco quebrável da Watery Hall na frente da Dynamo Access, os bomb slots do Energy Core na frente da West Furnace Access), o túnel de Morph da Burn Dome Access, 9 itens (o **Charge Beam** no pedestal da Watery Hall, 7 mísseis com o das Bombas do Burn Dome, 1 E-tank; bits `$C8–$CF`), nenhuma porta de charge nem sala quente (dados: nenhuma porta de cor, nenhum `Area Damage`), Parasite → Zeela; altura de corpo no enchimento do Space Jump (`flood_touch`), `EVENT_LOCKS` | 2 d | sim |
| 12l | [Região E](12l-regiao-e-chozo.md) (**verificada**) | as 12 salas que faltavam (as 64 construídas): as paredes da Furnace (B3 de gelo, de chão; R0 de Morph) e das salas de elevador East/South abertas; portas de gelo de chão/teto (PLMs novos `$F4EF`/`$F4F5`), 3 vermelhas (bits `$BD–$BF`), a onda da Crossway Access West, tampas diferentes por lado (`SIDE_CAPS`: a Antechamber), a cor de toda porta "key" conferida com o Prime (`KEY_BEAM`); a **Reflecting Pool inundada** (as portas dela atrás da Gravity Suit: mantém as rodadas do Tallon); 3 itens (E-tank da Hall, míssil da Crossway na cabana de PB, míssil da Antechamber no lugar do Ice Beam; bits `$D0–$D2`); **Save Station 3**; nenhum inimigo (camada 0 vazia) | 2 d | sim |
| 12m | [Rodadas das duas áreas e a cadeia completa](12m-rodadas-e-cadeia-completa.md) (**verificada**) | o passeio anda Tallon + Chozo (desde a 12f); `check_world_rounds` (51 itens em 7 rodadas, cada um na declarada; porcentagem do fim 51%); a tabela do Tallon igual (B); teste `cadeia_completa_tallon_chozo`: do pouso aos 51 itens na ordem das rodadas, pelos 3 elevadores, as subidas em zigue-zague com botões (nenhuma correção de layout); emulador de teste 2,4× mais rápido | 2 d | **sim** |

Chefes (Flaahgra, Hive Mecha, Incinerator Drone) e artefatos: fora, até o usuário decidir.

```
12a ─┐
12b ─┼─> 12c ─┬─> 12f ─> 12g ─> 12h ─> 12i ─> 12j ─> 12k ─> 12l ─> 12m
     │        │    ^
     └─> 12d ─┘    │
     12e ──────────┘
```

### Testes das filhas (ideias)

- 12c: validador com a tabela inteira (mapa sem sobreposição, portas encostadas, ligações que voltam, SRAM ≤ 80); mutação de porta
  sem volta.
- 12d: `crateria.check`-like para o 0C (peça no tileset, colisão vanilla igual); prévia olhada; mutação de peça de outro tileset.
- 12e: teste no emulador: entrar no elevador da Chozo West, chegar na área 1 (`$079F = 1`), voltar, mapa explorado das duas áreas preservado;
  `check_orphans` com as estações novas.
- 12f: `check_orphans` (salas alcançadas = manifest com a área 1); alcance a pé de cada sala; teste de rota cega da chegada à Main Plaza;
  save na Save Station 1 e continue.
- 12g/12m: as mutações do épico 09 adaptadas (item atrás da própria trava, rodada declarada errada), teste por mecanismo novo (Charge na porta,
  Varia na sala quente), cadeia completa das duas áreas.

## Critérios de aceite (do épico)

1. 12a e 12b `verificada` sem mudar a ROM (sha1 `3919c3c7…64ff` em dois builds; linha do Tallon igual; 53/53).
2. Depois da decisão do usuário: cada filha `verificada` com validate + build + testes; `check_orphans` prova que nenhum caminho entra em
   sala vanilla também pela área 1; `check_reclaimed` prova o uso do bloco recuperado.
3. Definição de pronto (a refinar com a decisão): as 64 salas ligadas como no Prime, os 3 elevadores funcionando, a Chozo jogável a pé com
   os itens da opção escolhida, sem softlock (validador nas duas áreas + cadeia no emulador), mapa de pausa e minimapa "CHOZO" salvos.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` (12a), `check_vanilla_pause` e `check_chozo_slot` (12b); depois: tabela, estilo, alcance, rodadas | +3 agora |
| scratchpad | mutações 12a (13 + 5 do alocador) e 12b (7 + ensaio do mapa de pausa); build da cópia com o `$8F` forçado ao bloco recuperado + testes | 26 + 1 |
| run_tests.py | nenhum novo agora (a ROM não muda); elevador, chegada, rotas e cadeia nas filhas | 0 |

## Riscos e reversão

- **`$8F` apertado mesmo com a 12a** (~500 bytes de folga para 64 salas): há mais 2 pedaços órfãos medidos; a checagem prova cada um.
- **Save de SRAM do Super Metroid vanilla** (spec 11, B7): quando o bloco recuperado for usado, carregar um save vanilla da Maridia/Tourian
  cairia em cabeçalho sobrescrito. Exige copiar o `.srm` de outra ROM; documentado.
- **Demos** (spec 11, B2): o 0C não aparece nelas; escolher 06/07/09/0A/0B mudaria a cor das demos.
- **Elevador do SM** nunca foi usado no projeto: a 12e mede antes de as salas da Chozo dependerem dele.
- Reversão: tudo vem de `tools/`; 12a e 12b não mudam a ROM (tirar as faixas/constantes e as checagens basta).

## Fora de escopo (até decisão)

- Chefes (Flaahgra, Hive Mecha, Incinerator Drone), artefatos, Chozo Ghosts, Wavebuster, scan, camadas de evento.
- Magmoor, Phendrana, Mines; o elevador da Magmoor North funcionando.
- Mudar as demos de atração.

## Decisões do usuário (26/10/2026, finais)

1. **Itens e progressão: opção B.** O Tallon fica intacto (44 salas, 20 itens em 7 rodadas). A Chozo leva Charge Beam, Varia Suit,
   os mísseis dela, os E-tanks e a expansão de Power Bomb. **Artefatos fora.** As travas da Chozo usam os itens do Tallon e os novos.
2. **Travas novas: as duas** — portas que só abrem com tiro carregado (Charge) e salas quentes que machucam sem a Varia (12g).
3. **Chefes: depois**, numa etapa própria no fim.
4. **Tamanho: as 64 salas**, por região, a A primeiro, cada região verificada antes da próxima.
5. **Área 1** confirmada.
6. **Elevadores: os três agora** (Tallon Chozo West, East e South, 12e); o da Magmoor North fica de enfeite.
7. **Morph Ball (Chozo West) e Gravity Suit (Chozo East)**, que estavam nas plataformas de enfeite, vão para o lado da plataforma, na
   mesma sala; a tabela de rodadas do Tallon não muda (12e: Morph em (12, 25), Gravity em (10, 21)).

8. **27/10/2026 (respostas da 12g e da spec 13; spec [12g2](12g2-ajustes-calor-e-cor.md))**: **só a Varia protege do calor**
   (patch de 1 byte em `$8D:E37D`; a Gravity só reduz o dano a ¼, regra geral do SM); **a porta de charge tem cor própria**
   (branca, só no tileset `$0C`); **a ordem da 12f sai** (a spec 13 a substitui); **o tiro em porta de cor ganha a mesma
   correção** da spec 13.

9. **27/10/2026, padrão aceito (decisões pequenas do orquestrador na 12i)**: a porta de charge **fica branca**; a redução de ¼ do
   calor com a Gravity Suit **fica** (é a regra geral do SM para dano periódico, que cobre também lava e ácido); **Puffer → Mella**;
   os inimigos da Tower of Light **ficam 6 + 6**; **Eyon → EYE** aceito na 12i se for justo (é: inofensivo, sem colisão, nunca
   bloqueia porta; ver a 12i).

10. **28/10/2026 (respostas da 12l)**: a **Reflecting Pool fica inundada** (a Gravity Suit guarda a Save Station 3, a Antechamber e a
    Transport Access South; mantém a tabela do Tallon): fecha a **pergunta 7** (água: só sala inteira, e só onde a progressão
    pede — a fragata afundada do Tallon e a Reflecting Pool; o resto seco). **A porta de charge branca fica para uma área futura**:
    a Chozo não tem nenhuma (fiel ao Prime: nenhuma porta de cor da Chozo é só de tiro carregado). **As paredes de míssil
    continuam blocos de bomba.**

Ainda abertas: confirmação final da cor (8: na 12e a linha 7 numa sala da Chozo é exatamente `SANDSTONE`, sem o tom
oliva da foto da 12d), demos (10); e as da 12i (Missile Wall → bloco de bomba; War Wasp → Mella; o elevador da Magmoor sem arte).
E as da 12k: Charge Beam como item comum (portão de runas aberto); Bombas do Burn Dome → míssil; paredes de míssil →
bloco de bomba (também quebram com tiro carregado no Prime); Watery Hall → Dynamo Access atrás do bloco quebrável; Parasite → Zeela.
E as da 12l (a da piscina inundada respondida na decisão 10): a estátua da Hall of the
Elders sem as membranas coloridas (E-tank e Reflecting Pool Access com bloco de bomba); o míssil da Crossway numa cabana de
Power Bomb no chão; Antechamber → míssil.

E as da 12m: o emulador de teste que desenha só o último quadro de cada comando (saída idêntica, 2,4× mais rápido), uma
cadeia só (~270 s) e os atalhos que ficam nela (ver a 12m).

## Verificação do épico (28/10/2026, 12m)

Definição de pronto (critério 3), conferida:
- **As 64 salas ligadas como no Prime**: `check_chozo` (tabela, 68 ligações = as do Prime, mapa) e as 64 construídas (12l); 0
  problemas.
- **Os 3 elevadores funcionando**: `check_elevators(_in_rom)`; no emulador `elevador_chozo_ida_e_volta`,
  `elevador_chozo_east_e_south` e a cadeia da 12m (9 viagens, a Samus andando até a plataforma).
- **A Chozo jogável a pé com os itens da opção B, sem softlock**: o validador anda Tallon + Chozo juntos (as 64 salas e os 31
  itens alcançáveis da nave, cada um na rodada declarada; volta à nave e nenhum lugar sem volta em cada rodada); a cadeia
  `cadeia_completa_tallon_chozo` pega os 51 itens das duas áreas na ROM, na ordem, pelos elevadores.
- **Mapa de pausa e minimapa "CHOZO" salvos**: `check_pause_maps`; `chozo_map_station`, `chozo_save_*`; a cadeia confere os bits
  de explorado das duas áreas depois de salvar, game over e continue, e o mapa de pausa de cada área.
- Critérios 1 e 2: 12a/12b sem mudar a ROM (na época); cada filha verificada; `check_orphans` e `check_reclaimed` com a área 1.

Pendências do usuário que não bloqueiam o épico: cor final (8), demos de atração (10), os padrões a confirmar das filhas (acima),
e a próxima etapa (chefes) só com aprovação.

## Precisa de decisão do usuário (perguntas originais; respondidas acima, menos 8 e 10)

1. **Itens e progressão**: (A) fiel, refaz o Tallon; (B) Tallon intacto, Chozo com Charge/Varia/mísseis/E-tanks e travas novas
   (**recomendado**); (C) B + o Morph na Ruined Shrine.
2. **Área 1** para a Chozo (recomendado; 2 muda o gelo e os projéteis, 4 rola o mapa 24 px). Já implementado como constante (12b).
3. **Travas novas** (se B ou C): porta que só abre com tiro carregado (Charge)? Salas quentes que pedem a Varia? As duas?
4. **Elevadores**: os 3 do Tallon para a Chozo funcionando (proposto); o da Magmoor North na Chozo continua de enfeite?
5. **Chefes**: Flaahgra (com Spore Spawn por baixo?), Hive Mecha, Incinerator Drone — entram ou ficam fora, como o Ridley do Tallon?
6. **Artefatos** (3 na Chozo, 2 no Tallon): continuam fora?
7. **Água**: só sala inteira (como no Tallon; 16 salas da Chozo têm água no Prime) ou seca onde for poça? (**respondida em
   28/10/2026, decisão 10**: a Reflecting Pool inundada, o resto seco.)
8. **Visual**: tileset 0C recolorido para arenito (proposto, não aparece nas demos)?
9. **Tamanho**: as 64 salas (como o Tallon) ou um corte (p.ex. A + B + C primeiro)?
10. Pendente da spec 11: **demos de atração** (deixar, desligar, gravar novas) — só pesa se o visual usar um tileset das demos.

## Desvios (preenchido na implementação)

- 26/10/2026: só as filhas de toolchain independentes da decisão (12a, 12b) foram implementadas; nenhuma sala da Chozo, nenhum item, nada
  do Tallon mudou. ROM igual (sha1 `3919c3c73d46afc45ffd4eb51083daebbe8264ff`).
- Verificação final: ver as Desvios da 12a e da 12b.
- 26/10/2026 (segunda leva, ainda sem a decisão dos itens): **12c** (tabela das 64 salas, 68 ligações, mapa de 41/80 bytes, 15 portas de
  chão/teto; travas do Prime por doca lidas dos objetos, `research/prime_chozo_locks.json`; ROM igual) e **12d** (estilo `ruinas` do 0C e
  a paleta em arenito numa cópia no alocador fixo; nenhuma sala nossa nem demo usa o 0C; sha1 novo
  `04dc19affd46326b94602f19eefcf2ea8fe3d9dc`) verificadas, 53/53. **12e** parou depois da medição do elevador do SM (bytes e emulador:
  ida e volta área 0 ↔ 1 funcionam) porque pede decisões: confirmar a área 1, o que fazer com a Morph e a Gravity Suit que estão nas
  plataformas de enfeite, e se East/South entram agora (ver a spec).
- 26/10/2026 (decisões do usuário, acima): **12e** verificada: os 3 elevadores funcionam (Tallon ↔ Chozo, área 0 ↔ 1), as 3 salas de
  elevador da Chozo construídas como becos em arenito (fora das rodadas do Tallon, linha própria no validador), Morph e Gravity ao lado
  das plataformas (rodadas do Tallon iguais), mapa/minimapa "CHOZO" e lista de 41 bytes na SRAM (+404); validate 75/148/0, sha1
  `d90984d0f621c88f8e5e2bac77ddb1a2e88026e6` (dois builds), **55/55** (2 testes novos; expectativas mudadas anotadas na 12e).
- 26/10/2026: **12f** verificada (região A: 12 salas, 7 itens, o passeio do validador anda Tallon + Chozo pelos elevadores; linha do
  Tallon igual); validate 86/170/0, sha1 `e22a2f9f78f4fb2b2d2ac49ab281be5b0fb4572c` (dois builds), **57/57**. Achado do motor: item
  varrido por Power Bomb pode ficar impegável (ver a 12f); o X-Ray do Tallon tem o mesmo risco latente.
- 26/10/2026: **spec 13** verificada (problema achado na 12f): a busca do toque no item (`$84:EEAB`) passa a pular slots de PLM
  mortos (rotina em `$84:FFDF`); o X-Ray do Tallon é o único PLM do Life Grove (slot 39) e não era afetado (medido); teste
  `power_bomb_nao_apaga_item`; sha1 `425f0796…981f`, 58/58. **12g** verificada: Charge Beam e Varia Suit como itens (sem lugar), porta
  de charge e salas quentes como mecanismos, provados numa ROM de teste separada; o SM deixa a **Gravity Suit proteger do calor**
  (decisão aberta na 12g); validate 86/170/0, sha1 `3fb636cf46244959557e8855b0fc526196a9691c` (dois builds), **60/60**.
- 27/10/2026: **12g2** verificada (decisões do usuário sobre a 12g e a spec 13: só a Varia protege do calor, porta de charge branca,
  a ordem da 12f sai, o tiro em porta de cor corrigido); sha1 `8371049f04df077c09df8a56aeafe8f1bba314d3`, 60/60. **12h** verificada
  (inimigos da região A: 30 em 8 salas; Puffer = Mella, desvio da tabela acima); validate 86/170/0, sha1
  `9a632d29fa3b6e80ac9bc2663d45a6d4a5785971` (dois builds), **61/61**.
- 27/10/2026: **12i** verificada (região B: 12 salas, 6 itens, Save Station 1 e Map Station na área 1, "CHOZO / RUINS" no continue,
  10 inimigos em 5 salas). Padrão aceito (decisão 9): porta de charge branca, a Gravity reduz o calor a ¼ (regra geral do SM),
  Puffer → Mella, torre 6 + 6, Eyon → EYE (inofensivo). Desvios da tabela acima: **War Wasp = Mella** (o HACHI1 morre com 6 tiros;
  o Rio mergulha longe demais para a Ruined Nursery), **Eyon = 1 olho** (o facho de dois sai errado), **Missile Wall = bloco de
  bomba** (o SM não tem bloco só de míssil), o **Missile Launcher = Missile Expansion** no totem; nenhuma porta de charge nem sala
  quente na região B (o Prime não tem trava de cor ali; o "Check Varia Suit" da galeria é da poça). Portas para a região C
  (Magmoor North R0 → Sun Tower) = parede; o elevador da Magmoor fica de enfeite. validate 98/196/0, sha1
  `8bd21bf1644bffe3befe1038e59d13991ec983a9` (dois builds), **65/65**.
- 27/10/2026: **12j** verificada (região C: 15 salas, 6 itens com a **Varia Suit** no pedestal da Sunchamber (o Flaahgra depois),
  a Magma Pool quente, Save Station 2 = estação 2 da área 1, 4 portas vermelhas `$B6–$B9`, portas de onda na Training Chamber, 13
  inimigos em 4 salas (Metaree → Skree)). Fatos novos dos dados: a cor das portas "key" pela vulnerabilidade do `Trigger_DoorKey`
  (as da região C são só Wave, como a Tower of Light) e a função 18 (`Area Damage`) só na Magma Pool. O `$8F` livre acabou: 288
  bytes na faixa recuperada da 12a (o alocador comparava só 16 bits: corrigido). O nível da Sunchamber cruza o banco `$E0`.
  Validador: `check_chozo_locks_mapped` (toda trava do Prime numa ligação construída tem o seu mecanismo). validate 113/230/0,
  sha1 `3df756e39c5098c35e911073f4a39e97b2bde840` (dois builds), **70/70**.
- 27/10/2026: **12k** verificada (região D: 11 salas, 9 itens com o **Charge Beam** como item comum no pedestal da Watery Hall
  (o portão de runas do Scan Visor aberto), as Bombas do Burn Dome = míssil, 3 portas vermelhas `$BA–$BC`, 16 inimigos em 8 salas
  (Parasite → Zeela)). Fatos dos dados: nenhuma porta de cor na região (logo **nenhuma porta de charge**: o Prime não tem porta só de
  tiro carregado; a Furnace → East Furnace Access, da região E, é só Ice), nenhum `Area Damage` (a Furnace é fria e seca). O "event"
  do Energy Core é o quebra-cabeça dos bomb slots (mapeado: `EVENT_LOCKS`). Validador: a lacuna da 12j fechada (`flood_touch`: item
  de borda de Space Jump só com lugar de pé). `$8F` recuperado: 846 de 2254 usados (1408 livres para a região E). validate
  124/252/0, sha1 `ebad8fa673c701847863a1ff8a16ae0a04f07093` (dois builds), **72/72**.
- 27/10/2026: **12l** verificada (região E: as 12 salas que faltavam, **as 64 construídas**; as paredes da Furnace e das salas de
  elevador East/South abertas; portas de gelo de chão/teto novas, 3 vermelhas `$BD–$BF`, a onda da Crossway Access West, tampas
  por lado (`SIDE_CAPS`) e a cor de toda porta key conferida com o Prime (`KEY_BEAM`); 3 itens `$D0–$D2`; Save Station 3 =
  estação 3; nenhum inimigo: a camada 0 da região é vazia). Conflito achado: o caminho do Prime (Crossway, estátua) levaria aos
  elevadores East/South uma rodada antes do lado do Tallon e mudaria a tabela do Tallon; a **Reflecting Pool inundada** (Gravity
  Suit nas portas dela) mantém a linha do Tallon igual (decisão a confirmar, pergunta 7). Validador: água da Chozo, cor das
  portas key, túnel de Morph em borda de Space Jump (`check_ball_ledges`). validate 136/284/0, sha1
  `0bcb610afa5639eb2cadc657ac9f357a1a8dcaf0` (dois builds), **75/75**.
- 28/10/2026: **12m** verificada (as rodadas das duas áreas e a cadeia completa: `check_world_rounds`, 51 itens em 7 rodadas, a
  porcentagem do fim 51%; o teste `cadeia_completa_tallon_chozo` do pouso aos 51 itens, pelos 3 elevadores, com as subidas em
  zigue-zague das 12i–12l feitas com botões, nenhuma correção de layout; o emulador de teste desenha só o último quadro de cada
  comando). Decisões do usuário de 28/10 registradas (decisão 10: piscina inundada, sem porta de charge na Chozo, paredes de
  míssil = blocos de bomba). Linha do Tallon igual; validate 136/284/0, sha1 `0bcb610afa5639eb2cadc657ac9f357a1a8dcaf0` (dois
  builds, igual), **76/76**. **Épico 12 `verificada`.**
