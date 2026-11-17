# 14 — Chefes (épico)

Estado: **verificada** (31/10/2026: as filhas 14a, 14b, 14c, 14d e 14f verificadas, a 14e (Chozo Ghosts) **fora** por decisão
do usuário, a spec-problema 15 verificada; critérios conferidos em "Verificação do épico", no fim; validate "136 salas, 284 portas,
0 problemas", `.ips` sha1 `31218abaaf3b1cb047f1ee6684ecd82fe45aa6c5`, 82/82 testes em 5 min 55 s). Aprovada em 30/10/2026 com as
decisões do usuário registradas no fim. Pesquisa de 30/10/2026: inventário, opções e experimentos numa cópia da ROM; nada do
projeto mudou na pesquisa (validate "136 salas, 284 portas, 0 problemas", `.ips` sha1
`0bcb610afa5639eb2cadc657ac9f357a1a8dcaf0`).
Esforço estimado: 7–12 dias no total, em 5–6 filhas de 0,5–3 dias (depende das respostas: o Bomb Torizo, se escolhido, é a
mais cara).

## Contexto

O Tallon (épicos 07, 09, 10) e a Chozo (épico 12) estão prontos: 108 salas, 51 itens a pé da nave em 7 rodadas. Os chefes
ficaram de fora por decisão do usuário (épico 12, decisão 3: "chefes depois, numa etapa própria no fim"). Cada filha da Chozo
deixou anotado o que esperava por esta etapa:

- 12i: o Missile Launcher do Hive Totem virou expansão comum no topo do totem ("o Hive Mecha fica para a etapa dos chefes");
- 12j: a Varia ficou como item comum no pedestal da Sunchamber e a porta Sunchamber → Sun Tower Access sem trava ("o Flaahgra
  depois"); a trava de evento da Training Chamber (Chozo Ghosts) ficou fora;
- 12k: as Bombas do Burn Dome viraram míssil no suporte e a porta de evento do Burn Dome ficou fora ("a luta do Incinerator Drone
  fica para os chefes");
- 12l: as 4 travas de evento da Hall of the Elders (Chozo Ghosts) ficaram fora;
- 12f/12h/12m: a Ruined Shrine tem 3 Sidehoppers pequenos no lugar dos 7 Alpha Beetles; o Plated Beetle não existe.

Este épico levanta, nos dados do Prime e nos bytes da ROM, **todo chefe ou luta de chefe** das áreas construídas (fragata,
Tallon, Chozo), o que cada um trava no Prime e o que fazemos hoje; mede no emulador o que dá para reaproveitar do Super Metroid;
propõe as filhas; e deixa as perguntas para o usuário.

## Estado atual (verificado)

Roteiros e saídas desta pesquisa no scratchpad da sessão (`…/scratchpad/s14/`): `scripts/boss_layers.py` (inimigos de chefe por
camada, três mundos → `boss_layers_all.txt`), `scripts/room_objs.py` (objetos com nome das salas de chefe → `room_objs_chozo*.txt`),
`scripts/conns.py` (ligações entre objetos → `conns_chozo_{9,12,36,37,48,52}.txt`, `conns_tallon_42.txt`), `scripts/sm_bosses.py`
(salas de chefe vanilla → `sm_bosses.txt`), `scripts/species.py` (as 166 espécies de `$A0` → `species.txt`),
`scripts/grey_types.py` (todas as portas cinza vanilla por tipo → `grey_types.txt`), `scripts/find_species.py`
(`find_species.txt`), experimentos `scripts/e1_spore.py`, `e2_quota.py`, `e3_kago.py` (cópias da ROM em `rom/`, fotos em `shots/`).
Os dados do Prime são lidos com o `tools/venv` (retro-data-structures 0.44.1) sobre `research/prime_fs`, como nas filhas 12c–12l.

### Inventário: chefes e lutas nas áreas construídas

Fonte: as camadas de cada sala (nome da camada e tipo de objeto, `boss_layers_all.txt`) e as ligações (`conns_*.txt`). Nomes
"Hive Mecha" e "Incinerator Drone" são conhecimento (nos dados o tipo é genérico: `Actor - Totem` e `ActorContraption`);
"Plated Beetle" é o `GarBeetle` dos dados.

| # | Chefe (Prime) | Sala (P#) | O que os dados mostram | O que trava no Prime | Hoje no projeto |
|---|---|---|---|---|---|
| 1 | **Parasite Queen** | fragata P25 Reactor Core | `NewIntroBoss` na camada 0 | a fuga da fragata | **feito**: Phantoon com cores (etapa 6) e forma própria (spec 06); bit de chefe da área 3 liga o cronômetro (spec 05) |
| 2 | Meta Ridley (passagem) | fragata | cena | — | **feito**: Air Lock (etapa 7) |
| 3 | **Plated Beetle** | Chozo P9 Ruined Shrine | camada 1 "First Pass": `GarBeetle` + `Master Beetle Generator` (e os 7 Alpha Beetles da camada 0 com temporizadores); começa ao pegar a Morph Ball (`p_morphball` → `Relay-start of cinema`; `Timer - Start Battle Music`); **nenhum `Actor Door Lock`** na sala; mais 2 cópias em camadas posteriores (Main Plaza camada 2 "2nd_Pass GarBeetle", Shrine camada 4 "BETA BEETLE") | **nada** (só o encontro) | Morph no Tallon (opção B); no lugar dela um míssil (24, 12), rodada 1; 3 Sidehoppers pequenos `$D93F` |
| 4 | **Hive Mecha** | Chozo P36 Hive Totem | camada 0: `Actor - Totem`, 4 estágios (`Faulty Relay - Activate Stage 1–4`), 3 geradores de War Wasp, `DamageableTrigger - Target` (a boca), `Relay - Start Outro Stage`; camada 1: `Trigger_startcinema`; **nenhum `Actor Door Lock`** (o `Actor Missile Lock` é o escudo de míssil da porta para a Transport Access North) | o **Missile Launcher** (`P_Missile_Launcher`) | expansão de míssil no topo do totem (23, 8), **rodada 0**; 3 Mellas; porta vermelha `$B5` |
| 5 | **Flaahgra** | Chozo P37 Sunchamber | camada 1 "1st Pass Enemies": `Flaahgra` + 4 `FlaahgraTentacle` + 4 `Bomb Slot DamageableTrigger`; `Flaahgra Dead Faulty Relay` → `Relay Activate Suit Pickup`; `Actor Door Lock` (camadas 1 e 2) **só na doca 0 → Sun Tower Access** (`research/prime_chozo_locks.json`) | a **Varia** e a porta para a Sun Tower Access (e uma troca de camadas em 9 salas: `Relay_FLAAGHRA DEAD LAYERSWITCH`) | Varia comum no pedestal (31, 39), **rodada 2**; porta sem trava |
| 6 | **Incinerator Drone** | Chozo P48 Burn Dome | camada 0: `ActorContraption` + `Actor Contraption Eye`, 4 estágios (`Relay Stage One..Four Hit`), 7 `Actor Hive`, `g_warwasp_generator`; pegar as Bombas (`P_Bomb`) começa a cena; `Actor Door Lock` na **única porta** (→ Burn Dome Access) | a **saída** (a sala tranca depois das Bombas; ordem = conhecimento, coerente com os dados) | míssil no suporte (23, 10), **rodada 1**; 1 Mella; porta sem trava |
| 7 | Chozo Ghosts, 1ª passagem | Chozo P12 Training Chamber (2 fantasmas, camada 1; trava na porta → Training Chamber Access) e P52 Hall of the Elders (1 fantasma, camada 2; travas nas 4 docas da camada 0) | `Trigger - Activate Chozo Ghost`, `Counter_Deadghost` → `Relay Disable Lock` | portas | sem luta; a porta da Training Chamber é de onda, as da Hall são de gelo/abertas (12j, 12l) |
| 8 | Chozo Ghosts, 2ª passagem | Ruined Shrine (2), Arboretum (3), Sun Tower Access (4), Sunchamber (3), Furnace (2), Hall (3) | camadas "2nd/3rd pass", ligadas depois do Flaahgra e de outros eventos | encontros (a Sunchamber tranca de novo na 2ª) | — |
| 9 | Chozo Ghosts do Life Grove | Tallon P42 | camada 1 "1st Pass Enemy" (3); aparecem **depois de pegar o X-Ray** (`P_XRay` → `Timer - Try Creature`); mortos → `Timer - Beak Break Delay` | o **Artifact of Chozo** (fora: artefatos fora) | X-Ray na cabana de Power Bomb, rodada 6 |
| 10 | Meta Ridley | Tallon P16 Artifact Temple | camada 1 "Monoliths and Ridley" | o fim do jogo (12 artefatos) | fora (artefatos fora, épico 07) |

Fora da lista: o `AtomicAlpha` da Sun Tower Access (camada 2, um inimigo, não chefe; nome no SM incerto), os Drones da Biohazard
do Tallon (camadas de evento), os piratas da camada "QUEEN FIGHT 2nd Pass" da fragata. **O Tallon não tem chefe na rodada do
jogo**: só os fantasmas do Life Grove (que guardam um artefato) e o Ridley (final). **A fragata já está completa.** O trabalho
deste épico é a **Chozo**: 4 chefes (3, 4, 5, 6) e, se o usuário quiser, as lutas de fantasmas (7).

### O que o Super Metroid oferece (bytes da ROM base)

Salas de chefe vanilla lidas por `sm_bosses.py` (cabeçalho, estados, população, set, espécie):

| Chefe SM | Sala | Área | Tileset | Corpo | Bit de chefe | Por que serve ou não |
|---|---|---|---|---|---|---|
| **Spore Spawn** `$A0:DF3F` (960 de vida, toque 12, tiles `$E00`, IA `$A5`) | `$8F:9DC7`, 1×3 | **1** | 06 | **só sprites** | 2 (estado morto `E629 #$02`) | **planta-chefe da área 1; funciona no tileset 0C (E1)** |
| Kraid `$A0:E2BF` | `$8F:A59F`, 2×2 | 1 | **1A** | BG2 + 7 partes | 1 | corpo no BG2 com os tiles do 1A; sala própria: não dá arenito |
| Crocomire `$A0:DDBF` | `$8F:A98D`, 8×1 | 2 | **1B** | BG2 | — | sala e ponte próprias |
| Phantoon `$A0:E4BF` | `$8F:CD13`, 1×1 | 3 | 05 | BG2 (tiles `$110–$18F` do tileset 4) | 1 | já é a Parasite Queen; não existe no 0C |
| Draygon `$A0:DE3F` | `$8F:DA60`, 2×2 | 4 | **1C** | sprites + torretas | 1 | sala própria (1C), água |
| Ridley `$A0:E17F` | `$8F:B32E` | 2 | 09 | VRAM inteira (`$2000`) | 1 | já usado como Meta Ridley (etapa 7) |
| **Botwoon** `$A0:F293` (3000, tiles `$1800`) | `$8F:D95E`, 2×1 | 4 | **0C** (o nosso!) | sprites | 2 | o tileset é o nosso, mas o caminho é preso aos buracos da sala dele e o init lê **o byte da área 4** (`$B3:9583` = `LDA $7ED82C / AND #$0002`); não lembra nenhum chefe da Chozo |
| **Bomb Torizo** `$A0:EEFF` (800, tiles `$2000` = VRAM inteira) | `$8F:9804`, 1×1 | 0 | 02 | sprites | 4 (`E629 #$04`) | **acorda quando a Samus pega o item** (PLM gatilho `$D6EA` em (13, 11) ao lado do item `$EF3B`; porta especial `$BAF4` tipo 2): o mesmo momento do Incinerator Drone; mas ver "Torizo fora da área 0" |
| Golden Torizo `$A0:EF7F` (13500, toque 160) | `$8F:B283` | 2 | 09 | sprites | 4 | forte demais para a rodada 1 |

Inimigos comuns que servem de "mini-chefe" (`species.txt`, nome de depuração lido em `$B4` pelo `+$3E`):

| Espécie | Nome | Vida / toque / tiles | Onde no vanilla (`find_species.txt`) | Serve para |
|---|---|---|---|---|
| `$D9BF` | SIDE (Sidehopper grande) | 320 / 80 / `$600` | área 1, salas com porta de cota (`$8F:9E11`, `$8F:A130`) | Plated Beetle |
| `$E7FF` | **KAGO** (colmeia de insetos) | 1600 / 0 / `$800` | áreas 0 e 2, parâmetro 1 = `$000A`, propriedades `$A000` | as colmeias do Hive Mecha e do Burn Dome |
| `$E9FF` | ATOMIC (flutua, atravessa paredes) | 250 / 40 / `$400` | Wrecked Ship, **arenas de cota** (`$8F:CA52` cota 8 e 10, `$8F:CAF6` cota 3/4) | Chozo Ghosts |
| `$D13F` | MELLA | 30 / 16 / `$400` | (já nosso: War Wasp, 12i) | as vespas |

**Kago** (`Kago_Shot` `$A8:AB83`, C `sm_a8.c:1313`): cada tiro solta um inseto (projétil) e treme a tela; morre depois de
"parâmetro 1" tiros; não colide com a Samus.

### Mecanismos do SM para "chefe morto" e "matou todos" (bytes)

- **Bits de chefe**: um byte por área em `$7E:D828 + área` (`SetBossBitForCurArea` `$80:81A6` = `LDX $079F / LDA $7ED828,X /
  ORA … / STA`; `CheckBossBitForCurArea` `$80:81DC`), salvos com o jogo. O SM usa 1 (chefe da área), 2 (mini-chefe), 4 (Torizo);
  os bits `$08–$80` ficam livres para nós. Estado de sala por bit: condição `$8F:E629` (`BD 00 00 29 FF 00 22 DC 81 80`), já usada
  pela Parasite Queen e pelo Meta Ridley (`build.boss_conditional_header`). Na área 1 (a Chozo) nenhum código vanilla que rode
  nas nossas salas lê esses bits (o ícone de chefe da área 1 saiu na 12e).
- **Porta cinza por tipo** (PLMs `$C842/$C848/$C84E/$C854`, argumento `tipo << 10 | bit de porta`; tabela de pré-instruções em
  `$84:BE4B` = `BDD4 BDE3 BDF2 BE01 BE1C BE1F BE30`): tipo 0 = bit 1 do chefe, **tipo 1 = bit 2 (mini-chefe)**, tipo 2 = bit 4
  (Torizo), **tipo 3 = cota de mortes**. O tipo 3 (`$84:BE01` = `PHY PHX / LDA $0E50 / CMP $0E52 / BCC / LDA #0 / JSL $80:81FA`)
  compara as mortes da sala (`$0E50`, somadas em `EnemyDeathAnimation` `$A0:A3AF`) com o **byte depois do `FF FF` da população**
  (`$0E52`, `sm_a0.c:423`) e, quando abre, **liga o evento 0** ("Zebes acordou"). Portas tipo 3 no vanilla: 32 tampas em 19 salas, 8 delas na área 1
  (`grey_types.txt`). **A nossa população já termina com a contagem dos inimigos** (Hive Totem `$A1:F3F7` = 3, Ruined Shrine
  `$A1:F275` = 3, Burn Dome `$A1:F5C8` = 1): a cota já está lá.
- O evento 0 só é lido pela condição de estado `$8F:E612` (C `HandleRoomDefStateSelect`); nenhuma sala nossa usa `E612`.

### Experimentos (cópias da ROM no scratchpad; nada em `build/` além de uma foto, ver Desvios)

**E1 — Spore Spawn na Sunchamber** (`e1_spore.py`; fotos `shots/e1_montage.png`). Só o estado da sala mudou na cópia: população
`$A1:A0FD` (Spore Spawn em (128, 624), propriedades `$2800`), set `$B4:8663`, música `2A/05`; tileset continua o **0C** em
arenito, área 1. Medido:
- o chefe carrega e luta normalmente: caule, esporos, sobe e desce, abre o núcleo (`$7E0F78 = $DF3F`, vida `$03C0` = 960);
- o feixe comum **não fere**: `SporeSpawn_Shot` `$A5:ED5A` (`BIT #$0700 / BNE / BIT #$0010 / BNE / RTL`) só aceita míssil, super,
  bomba ou tiro carregado; mísseis no casco fechado explodem sem dano (foto `e1_tiros.png`);
- a morte (vida 0 por RAM + toque, a mesma rotina `$A5:EDF3`) **liga o bit 2 da área 1** (`$7ED829 = $02`), tira o gancho da
  câmera e deixa o casco seco no lugar (como no vanilla);
- **efeito colateral**: a morte repinta as linhas **4 e 7** da paleta do BG (`$A5:E8CA`: tabelas `$A5:E4F9` → linha 4,
  `$A5:E5D9` → linha 7, `$A5:E3F9` → sprite 9): o arenito fica marrom-escuro (fotos `e1_depois*.png`);
- coisas fixas no código: o caule ancorado em **x = 128** (`SporeSpawn_Func_5` `$A5:EC49`), a posição da morte (128, 624)
  (`$A5:E87C`), a câmera presa em **y ≥ 464** durante a luta (`Samus_ScrollFinishedHook_SporeSpawnFight` `$90:9589`), e um PLM
  fixo `$B78F` em (7, 30) na morte (`$A5:EE30`: `JSL $84:83D7 / db 07 1E / dw B78F`, 2×2 blocos que viram ar; `$B793` no mesmo
  lugar se a sala abre com o chefe já morto). Na nossa Sunchamber (7, 30)–(8, 31) é ar.
- ~840 quadros por segundo no `snesrun` (17533 quadros em 20,9 s).

**E2 — porta de cota no Hive Totem** (`e2_quota.py`; fotos `shots/e2_montage.png`). Lista de PLMs da sala copiada para
`$8F:DD59` (faixa recuperada livre) com uma porta cinza `$C848` em (1, 6), argumento `$0CC0` (tipo 3, bit de porta `$C0`).
Medido: entrando pela Totem Access a porta fica cinza e a Samus não sai (`expect` da sala depois de 90 quadros para a esquerda);
**um Mella morto a tiro conta** (`$0E50 = 1`); com a cota completa (`$0E50 = 3` por RAM) a tampa vira azul, o evento 0 liga
(`$7ED820 = $01`), um tiro abre, ela sai para a Totem Access (`$079B = $F94C`) e o bit de porta fica salvo (`$7ED8C8 = $01`).

**E3 — colmeias Kago no Hive Totem** (`e3_kago.py`; fotos `shots/e3_montage.png`). População com 2 Kagos (`$E7FF`, parâmetro 1
`$000A`, propriedades `$A000`) nos favos do teto, set Mella + Kago (`$C00` bytes de VRAM). Medido: carregam e aparecem certos no
0C (`$7E1038 = $7E1078 = $E7FF`, vida `$0640`). **A morte de um Kago a tiro não foi medida** (o roteiro não pôs a Samus embaixo
deles); fica para a filha.

**Não testados no emulador** (só código e bytes): Torizo fora da área 0, ATOMIC no 0C, Kraid/Draygon/Crocomire (descartados
pelo tileset).

### Torizo fora da área 0 (código e bytes)

O Torizo escolhe entre Bomb e Golden **pela área**: `LDY $079F` em `$AA:C895` (o init lê posição e propriedades em tabelas de
2 palavras: `$AA:C95F` x = `$00DB, $01A8`, `$AA:C963` y = `$00B3, $0090`; na área 1, Y = 1 lê palavras desalinhadas: x = `$A800`)
e mais 6 `LDA $079F` (`$AA:B25E` item que solta, `$AA:C2E0`, `$AA:C620` baba, `$AA:C907` cores douradas e um **atalho de depuração
que dá todos os itens** com o controle em `$C0C0`, `$AA:C97C` tiro dourado, `$AA:C9C2` ataque dourado). Usar o Torizo na área 1
pede trocar esses 7 pontos, a VRAM inteira de inimigos da sala (`$2000`: o Mella do Burn Dome sai) e a posição fixa (219, 179).

### Espaço (build atual)

| Banco | Livre | Uso estimado (4 chefes) |
|---|---|---|
| `$8F` | **730** (faixa recuperada da 12a: 629 + 101; a faixa principal acabou na 12j) | ~250: estado "morto" (5 + 26 bytes por sala), listas de PLM do estado morto, 5 bytes de chamada por sala |
| `$84` | 2752 (`$84:F4FB–FFBA`, conferido: só `FF`) | ~150: rotina comum "quando a condição vale, gera o PLM" (ver Mudança proposta) |
| `$A0` | 1984 (`$A0:F83F`) | cópias de espécie (64 bytes cada) para mudar vida/toque/paleta |
| `$A5` | 1702 (`$A5:F95A`) | nada novo: as tabelas de cor da morte do Spore Spawn são trocadas no lugar |
| `$A1` / `$B4` | ~2,4 KB / ~2,1 KB | populações e sets novos (~20 bytes por sala) |
| SRAM | nada | bits de chefe e de porta já são salvos |

## Mudança proposta

### Ideia geral

Nenhum chefe novo é desenhado do zero. Cada chefe do Prime vira **(a)** um chefe do SM que já funciona nas nossas salas
(Spore Spawn), ou **(b)** uma **arena**: inimigos do SM (Kago, Mella, Sidehopper grande, ATOMIC) com o mecanismo vanilla de
"matou todos" (porta cinza tipo 3 e a cota da população). Nas duas formas, o "chefe morto" fica num **bit de chefe da área 1**
e a sala ganha um **estado "morto"** (`E629`) com o prêmio no lugar, como a Parasite Queen faz na fragata.

Para o prêmio **aparecer na hora** (o Prime faz isso: a Varia surge quando o Flaahgra morre, o Missile Launcher depois do Hive
Mecha), uma rotina comum em `$84`, chamada pelo "main ASM" da sala (5 bytes no `$8F`: `JSL` + `RTS`), olha uma tabela pequena por
sala: **condição** (cota de mortes `$0E50 ≥ $0E52`, bit de chefe, ou bit de item pego), **efeito** (liga um bit de chefe nosso,
`$08–$80`, e gera um PLM da lista da sala com `SpawnRoomPLM` `$84:846A`: o item, ou uma porta cinza que tranca). É o mesmo jeito
que o vanilla usa (`SpawnHardcodedPlm` `$84:83D7` nos chefes), só que com o argumento do item (bit de item). Feita uma vez (14b),
serve a todos.

### Opções por chefe (com o veredito)

**Plated Beetle (Ruined Shrine)**
- **P1 (recomendada)**: um **Sidehopper grande** (`$D9BF`, 320 de vida = 16 tiros do feixe) com os 3 pequenos, **sem trancar
  porta** (o Prime não tranca). Cópia da espécie em `$A0` com toque 40 (o vanilla tira 80; a 07i recusou 80 para inimigo comum).
  Esforço 0,5–1 d. Fiel no "momento" (um besouro grande entre os pequenos), sem gatilho do Morph (o Morph está no Tallon, opção B).
- P2: o mesmo com o toque vanilla (80).
- P3: como hoje.

**Hive Mecha (Hive Totem)**
- **H1 (recomendada)**: **2–3 Kagos** nos favos/totem (as colmeias) + os 3 Mellas (as vespas); quando todos morrem (cota), o míssil
  do topo do totem **aparece** e o bit `$08` da área 1 liga; estado "morto" com o míssil no lugar. **Sem porta trancada** (fiel:
  o Prime não tranca). Kago carrega no 0C (E3); cota medida com Mella (E2). Esforço 1,5–2 d (inclui a rotina comum).
- H2: só os 3 Mellas com a porta cinza tipo 3 (E2 provou tudo): mais simples, mas tranca porta (o Prime não tranca).
- H3: como hoje (míssil comum, rodada 0).
- Botwoon descartado (caminho preso à sala dele; nada de totem).

**Flaahgra (Sunchamber)**
- **F1 (recomendada)**: **Spore Spawn** (E1: funciona no 0C, área 1, bit 2). A arena da Sunchamber muda para o canto de baixo à
  esquerda (o caule fica em x = 128, a morte em (128, 624)); a porta L0 → Sun Tower Access ganha **porta cinza tipo 1**
  (mini-chefe = bit 2, exatamente o bit que o Spore Spawn liga); a R2 (entrada) fica azul (fiel: o Prime só tranca a da Sun Tower
  Access; e sem mísseis a Samus pode sair). A Varia **aparece** quando ele morre (rotina comum, condição bit 2) e fica no estado
  morto. Cores: as do Flaahgra (texturas do Prime, como a Parasite Queen na etapa 6) na paleta da espécie (`$A5:E359`) e nas tabelas
  da morte; as tabelas das linhas 4 e 7 (`$A5:E4F9`, `$A5:E5D9`) trocadas para o arenito (senão a sala fica marrom, E1). Música
  `2A/05` (a de mini-chefe do SM) só no estado vivo. Esforço 2–3 d.
- F2: arena de inimigos (plantas do SM) — perde o chefe de verdade que já funciona.
- F3: como hoje.
- Kraid descartado (corpo no BG2 do tileset 1A; sala própria).

**Incinerator Drone (Burn Dome)**
- **I1 (recomendada)**: **arena que tranca ao pegar o item**: Kagos nas paredes (as 7 "Actor Hive" do Prime) + Mellas (as vespas do
  gerador); pegar o míssil do suporte (o lugar das Bombas) **gera a porta cinza tipo 3** na única porta (rotina comum, condição
  "bit do item"); todos mortos → abre; bit `$10` da área 1. Fiel à ordem do Prime (item → luta → porta abre); sem o "olho" do
  Drone. Esforço 1–1,5 d (com a rotina pronta).
- I2: **Bomb Torizo** (a estátua do SM que acorda quando se pega o item): o momento mais parecido no SM, mas pede trocar 7 leituras de
  área em `$AA`, a VRAM inteira da sala, a porta especial `$BAF4` e o gatilho `$D6EA`; risco médio (código dourado nunca rodado na
  área 1). Esforço 2,5–3,5 d, com uma medição de "vai/não vai" antes.
- I3: como hoje.

**Chozo Ghosts**
- **G1 (recomendada agora)**: **fora** nesta etapa (como o épico 12 deixou). As duas lutas da 1ª passagem caem em portas que já têm
  outra tampa (a da Training Chamber é de onda; duas da Hall são de gelo): o SM só põe uma tampa por porta.
- G2: as 2 lutas da 1ª passagem como arenas de **ATOMIC** (o vanilla já faz arenas de Atomic com cota na Wrecked Ship), a porta
  cinza só nas docas que não têm outra tampa (Hall → Elder Hall Access, Hall → Reflecting Pool Access). 1,5–2 d.
- G3: todas (inclui as da 2ª passagem e a troca de camadas do Flaahgra): fora do tamanho desta etapa.

**Fragata e Tallon**: nada a fazer (Parasite Queen feita; Ridley e fantasmas do Life Grove guardam artefatos, que estão fora).

### Efeito nas rodadas e na cadeia

- **Nenhum item muda de lugar nem de rodada** com as opções recomendadas: Plated Beetle não trava nada; Hive Mecha (rodada 0) se
  vence com o Power Beam (Mella 30 de vida; Kago morre por número de tiros); Flaahgra/Spore Spawn (rodada 2) pede **mísseis ou
  tiro carregado** — a Samus tem mísseis desde a rodada 0 e o Charge desde a 1; Burn Dome (rodada 1) se vence com o Power Beam.
  A linha do Tallon fica **igual** ("44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas") e a de
  `check_world_rounds` também (51 itens em 7 rodadas, 51%).
- **Modelo do validador** (`tools/smlib/reach.py`, `validate.tallon_rounds`/`check_world_rounds`): uma trava nova `boss` por porta
  ou item ("só depois da luta"), com a exigência de cada luta como itens (`{missiles}` ou `{charge}` para o Spore Spawn; nada para
  as arenas); `check_tallon_round_stuck` entende que, dentro da arena, a porta trancada abre se a luta é vencível com o equipamento
  daquela rodada. Novo `check_bosses`: espécie/população/set na ROM, cota = número de inimigos, tipo da porta cinza = bit que o
  chefe liga, estado "morto" com a máscara certa, bits de chefe sem colisão por área, nenhuma sala nossa com `E612`,
  VRAM ≤ `$2000` e ≤ 4 espécies (`check_enemy_sets`), justiça ("chefe" vencível com o equipamento da rodada; toque ≤ 40).
- **Cadeia** `cadeia_completa_tallon_chozo` (~270 s; verificação inteira ~6 min do limite de 10): cada luta entra na ordem das
  rodadas. Medido no E1: ~840 quadros/s. Lutas de verdade de 3000–6000 quadros ≈ 4–7 s cada; com atalho anotado (vida por RAM,
  como os inimigos apagados da 12m) ≈ 1 s. Estimativa: +15–30 s na cadeia; mais 4–5 testes curtos começando por estação (sem o
  pouso, ~10–15 s cada): **total ~7–7,5 min**. A 14f mede de novo.

### Filhas (rápido → complexo)

| # | Spec | Entrega | Esforço | Depende das decisões |
|---|---|---|---|---|
| 14a | [Plated Beetle](14a-plated-beetle.md) (**verificada**, 30/10/2026) | Sidehopper grande (cópia de espécie em `$A0`, toque 40) na Ruined Shrine com os 3 pequenos; regra "chefe" na justiça dos inimigos; nenhuma trava | 0,5–1 d | Q1, Q5 |
| 15 | [Dano cedo na entrada de porta](15-auditoria-de-entrada.md) (**verificada**, 30/10/2026; problema achado na 14a) | auditoria de entrada de verdade (andando pela porta, 600 quadros), 8 colocações mudadas, testes `entradas_de_porta_*` | 0,5 d | — |
| 14b | [Arena e Hive Mecha](14b-arena-e-hive-mecha.md) (**verificada**, 30/10/2026) | rotina comum em `$84:F500` (cota de mortes, slot vazio, bit de chefe ou item pego → bit de chefe nosso, música parada, PLM do prêmio) chamada pelo main ASM do estado vivo; estado "morto" por `E629`; 2 Kagos + 3 Mellas no Hive Totem, o míssil aparece; o Plated Beetle com música de mini-chefe e estado morto; trava `boss` no passeio; `check_arenas` | 1,5–2 d | Q1, Q3, Q4, Q7 |
| 14c | [Flaahgra = Spore Spawn](14c-flaahgra.md) (**verificada**, 31/10/2026; com a sobra da spec 15: a vespa da Ruined Nursery) | o fosso do Spore Spawn no canto de baixo a oeste da Sunchamber, porta cinza tipo 1 na L0 (`BOSS_DOORS`), a Varia aparece (condição `BOSS_BIT $02`, bit da arena `$40`), cores do Flaahgra, tabelas da morte = as linhas das ruínas, gancho de câmera desligado; trava `boss` em porta no passeio; justiça de chefe com o equipamento da rodada (mísseis pela capacidade ou tiro carregado); rodadas iguais | 2–3 d | Q1, Q2, Q3, Q7 |
| 14d | [Incinerator Drone](14d-incinerator-drone.md) (**verificada**, 31/10/2026; I1, decisão 6) | arena no Burn Dome: o míssil do suporte (bit `$CC`) começa a luta (condição `ITEM` redefinida: a tampa cinza tipo 3 gerada na única porta, 2 colmeias (cópia do Kago de 1 parte) e 2 vespas geradas por `SpawnEnemy`, a faixa 5 do set de mini-chefe); todas mortas (com a vespa de antes), a porta abre, bit `$10`; trava `boss` do item que começa a luta no passeio; morrer na luta volta ao último save | 1–1,5 d (I1) / 2,5–3,5 d (I2) | Q1, Q6 |
| 14e | Chozo Ghosts | **fora** (decisão 8 do usuário, 30/10/2026: os fantasmas ficam para depois; a linha fica como registro) | — | Q8 |
| 14f | [Rodadas e cadeia com os chefes](14f-rodadas-e-cadeia-com-chefes.md) (**verificada**, 31/10/2026) | as lutas na cadeia por atalho anotado (Hive Mecha, Incinerator Drone, Flaahgra; o besouro vivo), tempo total medido (5 min 55 s), linha "chefes (specs/14)" no validador (as travas no passeio, bits distintos e fora dos vanilla da área 1), fotos da 14a refeitas, épico `verificada` | 1 d | Q9 |

```
14a ──> 14b ──> 14c ──> 14d ──> 14f        (14e fora)
```
A 14a não depende da rotina; a 14b cria a rotina que 14c, 14d e 14e usam.

### Critérios de aceite e testes por filha

**14a — Plated Beetle**
1. `check_layer0_enemies`/`check_bosses`: a Ruined Shrine tem 1 `$D9BF`-cópia + 3 `$D93F`, cópia de espécie com toque 40 e vida 320
   na ROM; set ≤ `$2000`. (validate; mutação: toque 80 → erro.)
2. Teste `chozo_plated_beetle` (emulador): da Save Station 1 (estação por RAM) até a Shrine; o grande vivo (`$7E0F78+$40·n`), morre
   com tiros do Power Beam (contagem medida), `$0E50` sobe. (protege: a espécie e a população; falha_quando: sumir, não morrer;
   não_prova: a cadeia.)
3. Linha do Tallon e `check_world_rounds` iguais; 77/77 (+1).

**14b — Arena e Hive Mecha**
1. `check_bosses`: a tabela da rotina (sala → condição/efeito/PLM) bate com a ROM; o bit nosso não colide (`$08`); a cota = inimigos.
2. Teste `chozo_hive_mecha`: entra no Hive Totem, o míssil **não** está (PLM ausente na WRAM), mata os Kagos e os Mellas com o Power
   Beam, o míssil aparece e é pego andando, `$7ED829 & $08`; sai e volta: estado "morto" com o míssil pego (item não volta).
   (falha_quando: o item aparece antes, não aparece, ou volta.)
3. Mutação: cota maior que os inimigos → validate acusa; condição trocada → o teste falha.

**14c — Flaahgra (Spore Spawn)**
1. `check_bosses`: população do Spore Spawn em (128, 624), set, porta cinza tipo 1 na L0 da Sunchamber, estado morto `E629 #$02`
   com a Varia; tabelas `$A5:E4F9/E5D9` = arenito; nenhuma peça sólida em (7, 30)–(8, 31).
2. Teste `chozo_flaahgra`: da Save Station 2, Sunchamber: a L0 não abre; o feixe comum não fere; **mísseis no núcleo aberto**
   matam (ou atalho anotado: vida por RAM + toque, como o E1); `$7ED829 & $02`; a Varia aparece e é pega; a L0 abre; a linha 7 da
   paleta na WRAM continua `SANDSTONE` depois da morte (`expect` em `$7EC0E0…`).
3. Rodadas iguais; os testes da 12j/12m que andam na Sunchamber (`C_TO_THE_VARIA`, `chozo_varia_e_calor`) atualizados à arena nova.

**14d — Incinerator Drone (I1)**
1. `check_bosses`: Kagos + Mellas no Burn Dome, porta cinza tipo 3 gerada pela rotina (condição "item `$CC` pego").
2. Teste `chozo_incinerator`: entra, a porta está azul; pega o míssil do suporte → a porta fica cinza e não abre; mata todos → abre,
   bit `$10`; volta: sala calma (estado morto).

**14f — Rodadas e cadeia**
1. `cadeia_completa_tallon_chozo` com as lutas na ordem das rodadas; tempo total da verificação medido e anotado (≤ 8 min).
2. Linha nova "chefes (specs/14): …" no validate; Tallon e `check_world_rounds` iguais.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_bosses` (espécie, população, set, cota, tipo de porta, estado morto, bits, `E612`), trava `boss` no passeio das rodadas, justiça de chefe | +2 checagens |
| scratchpad | mutações por filha (cota errada, bit trocado, toque 80, tabela de cor vanilla) | ~15 |
| run_tests.py | `chozo_plated_beetle`, `chozo_hive_mecha`, `chozo_flaahgra`, `chozo_incinerator` (+ `chozo_fantasmas` se G2); a cadeia com as lutas | +4–5 |
| imagem | fotos de cada luta (antes, durante, prêmio) em `specs/img/14*-*.png` | ~12 |

## Riscos e reversão

- **Evento 0**: a porta tipo 3 liga "Zebes acordou" (`$84:BE01`). Só a condição `E612` lê; `check_bosses` garante que nenhuma
  sala nossa a use. Se um dia uma sala usar, a rotina comum pode trocar a porta tipo 3 por uma nossa.
- **Spore Spawn preso à sala vanilla**: x = 128, (128, 624), câmera y ≥ 464, PLMs `$B78F/$B793` em (7, 30). A Sunchamber muda de
  forma (os testes que andam nela mudam); se o usuário quiser a arena em outro lugar, são 4 patches de 2 bytes (posições) — medir.
- **Cor da sala depois da morte** (E1): tabelas `$A5:E4F9/E5D9` trocadas; teste confere a linha 7.
- **Kago**: a morte a tiro na nossa sala ainda não foi medida (E3 só provou que carrega); cada tiro treme a tela 16 quadros.
- **Torizo (se I2)**: 7 leituras de área em `$AA` e o atalho de depuração `$C0C0` (dá todos os itens fora da área 0); medir antes.
- **Tempo dos testes**: estimado ~7–7,5 min de 10; a 14f mede; se passar, lutas por atalho na cadeia e a luta de verdade só no
  teste próprio de cada chefe.
- **`$8F`**: 730 livres para ~250 estimados; se faltar, os pedaços órfãos já medidos no épico 12 (`check_reclaimed`).
- Reversão: tudo vem de `tools/`; tirar a tabela de chefes e reconstruir volta à ROM `0bcb610a…`.

## Fora de escopo

- Meta Ridley e o Artifact Temple funcionando; artefatos; os fantasmas do Life Grove (guardam um artefato).
- As lutas da 2ª passagem (camadas que o Prime liga depois do Flaahgra) e a troca de camadas do Flaahgra.
- Forma própria (arte nova) dos chefes reaproveitados (só cores, como a etapa 6 começou); pode virar spec separada.
- Wavebuster, Scan Visor, cenas de câmera do Prime.
- Chefes de Magmoor, Phendrana, Mines.

## Decisões do usuário (perguntas)

1. **Quais chefes entram nesta etapa?**
   (a) os 4 da Chozo: Plated Beetle, Hive Mecha, Flaahgra, Incinerator Drone — **recomendado** (os 3 grandes guardam itens/portas no
   Prime; o besouro é o mais rápido e abre a etapa); (b) só os 3 grandes; (c) só o Flaahgra (o único com chefe do SM pronto);
   (d) nenhum agora.
2. **Flaahgra**: (a) **Spore Spawn** com as cores do Flaahgra — **recomendado** (planta-chefe da própria área 1, funciona no
   arenito: E1); (b) arena de inimigos; (c) Varia comum, como hoje.
3. **O prêmio aparece quando o chefe morre?** (a) **sim, na hora** (como no Prime; uma rotina pequena, feita uma vez) —
   **recomendado**; (b) o item fica lá desde o começo e o chefe só tranca a porta; (c) o item só aparece depois de sair e voltar
   (estado da sala, sem código novo).
4. **Hive Mecha**: (a) **colmeias (Kago) no totem + as vespas; o míssil aparece quando todas morrem; nenhuma porta tranca** —
   **recomendado** (o Prime não tranca essa sala); (b) só as 3 vespas e a porta cinza; (c) como hoje.
5. **Plated Beetle**: (a) **Sidehopper grande com o toque reduzido para 40**, com os pequenos, sem trancar — **recomendado**;
   (b) o mesmo com o toque vanilla (80: 99 de energia somem em 2 toques); (c) como hoje.
6. **Incinerator Drone**: (a) **pegar o míssil do suporte tranca a porta; colmeias + vespas; todas mortas, abre** —
   **recomendado** (mesma ordem do Prime, barato com a rotina da 14b); (b) **Bomb Torizo** (a estátua do SM que acorda ao pegar o
   item: o momento mais parecido, mas 2–3 dias a mais e risco médio); (c) como hoje.
7. **Música e cores**: (a) **música de mini-chefe do SM (`2A/05`) só durante a luta; cores dos chefes tiradas das texturas do
   Prime** — **recomendado**; (b) música das ruínas o tempo todo; (c) forma própria (arte nova) para o Flaahgra, como a spec 06
   fez com a Parasite Queen (+1–1,5 d, spec separada).
8. **Chozo Ghosts**: (a) **fora nesta etapa** — **recomendado** (as portas deles já têm tampa de onda/gelo; o SM põe uma só);
   (b) só as 2 lutas da 1ª passagem com ATOMIC, nas portas livres; (c) todas.
9. **Lutas nos testes**: (a) **a cadeia mata cada chefe por atalho anotado (vida por RAM) e cada chefe tem o seu teste curto com a
   luta de verdade** — **recomendado** (cabe no limite de 10 min); (b) luta de verdade também na cadeia (+~30 s); (c) só atalho.

### Respostas (30/10/2026)

Decisões do usuário (U) e padrões que o orquestrador aceitou em nome dele (**padrão aceito**: a recomendação do épico; mudam
se o usuário pedir):

1. (U) **Os 4 da Chozo**: Plated Beetle, Hive Mecha, Flaahgra, Incinerator Drone (Q1 = a).
2. (U) **Flaahgra = Spore Spawn** com as cores do Flaahgra (Q2 = a).
3. **padrão aceito**: o prêmio aparece **na hora** em que o chefe morre (Q3 = a).
4. **padrão aceito**: Hive Mecha = colmeias (Kago) + as vespas; o míssil aparece quando todas morrem; nenhuma porta tranca (Q4 = a).
5. **padrão aceito**: Plated Beetle = Sidehopper grande com o toque reduzido para **40**, com os pequenos, sem trancar (Q5 = a).
6. (U) **Incinerator Drone = arena**: pegar o item tranca a saída; colmeias + vespas; todas mortas, abre (Q6 = a).
7. **padrão aceito**: música de mini-chefe do SM só durante a luta; cores dos chefes tiradas das texturas do Prime (Q7 = a).
8. (U) **Chozo Ghosts fora** por enquanto (Q8 = a): a filha 14e fica "fora" na tabela (registro).
9. **padrão aceito**: cada chefe tem o seu teste curto com a luta de verdade; a cadeia completa mata cada chefe por um atalho de
   RAM anotado (Q9 = a).
10. **padrão aceito** (30/10/2026, orquestrador, depois da 14a): justiça de chefe = morre só com o Power Beam em até **20 tiros**
    (`FAIR_BOSS_SHOTS`; numa arena, somados) e tira no máximo **40 por toque** (`FAIR_BOSS_TOUCH`) quando a Samus chega com no
    máximo Power Beam, mísseis e Morph.
11. **padrão aceito** (30/10/2026, orquestrador): a cadeia completa pode deixar um chefe **vivo** quando ele não bloqueia o
    caminho (o Plated Beetle); a decisão 9 (matar por atalho de RAM) vale só para chefes no caminho (o Hive Mecha, que guarda
    o míssil do totem).
12. **padrões aceitos** (31/10/2026, orquestrador, na 14c), as "decisões a confirmar" da 14b: (a) a música **para** quando uma
    arena é vencida (não volta à da área na hora: evita o congelamento de ~38 quadros); (b) chefe morto **nunca volta**
    (estado morto pelo bit nosso, salvo com o jogo); (c) os Kagos do Hive Mecha ficam com a paleta vanilla; (d) a justiça de
    uma arena é **somada** (tiros de todos os inimigos que a condição espera); (e) os bits de chefe nossos da área 1 são os da
    14b: `$08` Hive Mecha, `$10` reservado ao Incinerator Drone, `$20` Plated Beetle (a 14c usa `$40` para a arena e o `$02`
    do próprio Spore Spawn como condição).
13. **regra de justiça de chefe adaptada** (31/10/2026, 14c; o orquestrador pediu "explícita, com o equipamento da rodada"):
    uma luta que o Power Beam comum não vence (`Arena.needs` não vazio: o Spore Spawn) é justa se, com o que a Samus tem na
    rodada em que chega à sala, ela vence com os mísseis que pode carregar então (capacidade dos itens das rodadas antes,
    cada míssil acertando) **ou** com até 20 tiros carregados (se tem o Charge Beam); o `needs` declarado tem que ser, sozinho,
    um desses jeitos; o toque e os projéteis até 40.

## Desvios (preenchido na implementação)

- 31/10/2026 (14d): o Incinerator Drone é a arena I1 com os inimigos **gerados** quando o míssil é pego (`SpawnEnemy`
  `$A0:9275`): a condição `ITEM` da rotina foi redefinida (a luta começa no item e termina na cota; a 14b a deixara como "item
  pego → venceu", sem uso). Achados no emulador: o Kago diz 9 partes no cabeçalho e o `SpawnEnemy` gera tantas (o jogo travava):
  as colmeias das duas arenas usam uma cópia de 1 parte (`$A0:F87F`); a Mella afunda um passo por mergulho quando está abaixo da
  Samus e, fora da câmera, para: a vespa da camada 0 do Burn Dome subiu para o bloco leste, as da luta nascem no ar e a rotina
  liga "processar fora da câmera" (`$0800`) em todos os inimigos quando a luta começa. Antes do item a sala toca a faixa 3 do
  set de mini-chefe (como o Bomb Torizo vanilla). Decisões a confirmar na [14d](14d-incinerator-drone.md).
- 31/10/2026 (14f): linha "chefes (specs/14)" (`check_epic_bosses`); as fotos da 14a refeitas.

- 31/10/2026 (14c): a Sunchamber mudou de forma em volta do Spore Spawn (o fosso no canto de baixo a oeste, como a sala
  vanilla), a Varia aparece no chão do fosso sob a casca (sem pedestal) e o **gancho de câmera do Spore Spawn foi desligado**
  (com ele, a Samus subindo o zigue-zague durante a luta saía da tela): decisões a confirmar na [14c](14c-flaahgra.md). O bit
  `$40` da área 1 é da arena da Sunchamber; o `$02` é o do Spore Spawn (condição). A cadeia mata o Flaahgra por atalho de
  RAM (vida 0; ele morre no primeiro toque, pelo próprio código).

- 30/10/2026 (14b): no fim de uma arena a música de mini-chefe **para** (a das ruínas só volta na próxima sala): pôr o song set
  da área de volta na hora congela o jogo ~38 quadros (medido). O Plated Beetle (14a) ganhou a música e o estado morto pela
  mesma rotina (bit `$20`); bits nossos da área 1: `$08` Hive Mecha, `$10` reservado ao Incinerator Drone, `$20` Plated Beetle.
- 30/10/2026 (14b): Hive Mecha = **2** Kagos com 5 golpes cada (parâmetro 4; o vanilla `$0A` dá 11 e a arena passaria de 20
  tiros); as cores das colmeias ficaram as do Kago (decisão a confirmar).
- 30/10/2026 (spec 15): a auditoria de entrada da 12h (transição por RAM, 180 quadros) não via toques cedo em 9 salas; a spec
  15 refez a auditoria com entradas de verdade e mudou 8 colocações (inclusive os pequenos da Shrine, o que pediu procurar de
  novo a luta do besouro).

- 30/10/2026 (pesquisa): o roteiro do E1 usou `chozo_down` do `tests/run_tests.py`, que grava uma foto num caminho relativo; numa
  das rodadas, com o diretório do projeto como cwd, ele gravou **`build/tests/12j_e1_descendo.png`** (foto a mais, inofensiva:
  `build/` é saída; não apagada). As outras rodadas usaram o scratchpad como cwd. Nada em `tools/`, `tests/` ou na ROM mudou.

## Verificação do épico (31/10/2026)

Conferido no fim da 14f, contra as decisões do usuário, os padrões aceitos e os critérios por filha (acima):

| Critério | Onde | Resultado |
|---|---|---|
| Decisão 1: os 4 da Chozo | `bosses.ARENAS`, linha "chefes (specs/14)" | Plated Beetle, Hive Mecha, Flaahgra, Incinerator Drone, cada um uma arena |
| Decisão 2: Flaahgra = Spore Spawn com as cores do Flaahgra | [14c](14c-flaahgra.md), `chozo_flaahgra` | sim (decisões a confirmar da 14c) |
| Decisão 6: Incinerator Drone = arena (o item tranca a porta; colmeias + vespas; todas mortas, abre) | [14d](14d-incinerator-drone.md), `chozo_incinerator_drone` | sim (gerados no item; decisões a confirmar da 14d) |
| Decisão 8: Chozo Ghosts fora | linha 14e | fora |
| Padrão 3: o prêmio aparece na hora | Hive Mecha (o míssil), Flaahgra (a Varia) | sim (testes) |
| Padrão 4: Hive Mecha sem porta trancada | 14b | sim |
| Padrão 5: Plated Beetle toque 40 | 14a, `check_bosses` | sim |
| Padrão 7: música de mini-chefe só na luta | as 4 arenas: vivo `2A`, a vitória para a música, o morto toca a da área | sim (no Burn Dome a faixa 5 só depois do item) |
| Padrão 9: cada chefe com a sua luta de verdade; a cadeia por atalho anotado | `chozo_plated_beetle`, `chozo_hive_mecha`, `chozo_flaahgra`, `chozo_incinerator_drone`; `full_chain` (docstring e `FullChain.note`) | sim |
| Padrões 10 e 13: justiça de chefe | linha "arenas (specs/14b)" | 16 / 16 / 10 mísseis ou 8 carregados / 16 tiros; até 40 por golpe |
| Padrão 11: o besouro vivo na cadeia | `full_chain` | sim |
| Padrão 12: bits `$08` Hive, `$10` Drone, `$20` besouro, `$40` Sunchamber; chefe morto nunca volta | linha "chefes (specs/14)", estados mortos por `E629` testados com save/continue | sim; distintos, fora dos vanilla da área 1 (`$01`, `$02`, lidos da ROM base) |
| Rodadas iguais | Tallon "44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"; "51 itens em 7 rodadas … 51%" | iguais desde antes do épico |
| Toda trava de chefe no passeio | `boss_locks` (prêmio, item que começa), `door_open` (porta de chefe), `check_epic_bosses` | sim |
| Tempo dos testes ≤ 8 min | bateria inteira | 5 min 55 s (82 testes) |
| Mutações por filha | specs 14a–14d, 14f | pegas (as que o validador não vê, pelo emulador) |

Pendências do épico (para o usuário, nenhuma bloqueia): as decisões a confirmar das filhas (14b: silêncio depois da luta, cores
das colmeias; 14c: gancho de câmera, a Varia no fosso, a casca, as cores por rampa; 14d: a faixa 3 antes do item, a vespa no
bloco leste, colmeias geradas, a vespa de antes contada, o continue que refaz a luta); os Chozo Ghosts (14e).

