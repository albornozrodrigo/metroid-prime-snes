# 19b — Lugar da Mines na área 5 (e a lista do mapa no `$81`)

Estado: verificada (05/11/2026: validate 221/460/0 com a linha nova "mines (specs/19b): área 5 …"; .ips sha1
`8e5d377133b668151f4a558ebbb192d1bff0f01a` igual em dois builds; os grupos A, B e C rodados no fim da 19c, com a ROM igual)
Esforço estimado: 0,5–1 dia
Épico: [19 — Phazon Mines](19-phazon-mines.md) (decisão 2, opção (a): **padrão aceito, confirmado pelo usuário em 09/11/2026**; toolchain, ROM igual)

## Contexto

Como a 12b, a 17b e a 18b, esta filha reserva a área do SM da Mines — a 5, da Tourian — e confere os bytes vanilla das tabelas que o
build vai reescrever **antes** de existir sala. A área 5 é a primeira que nunca usamos e tem três coisas novas: a lista do mapa salvo
não cabe no lugar vanilla (21 bytes; a Mines pede ~45), a Tourian não tem map station (a Mines tem uma), e a lista de FX de paleta da
área começa com o objeto de **calor** (como a da Norfair). A ROM não muda.

## Estado atual (verificado)

- `tools/areas.py:178` `MINES_AREA = 5` (plano da 18b). `build.VANILLA_PAUSE` com 0–4; `validate.check_slot` só aceitava 0–4.
- Tabelas da área 5 na ROM base (lidas pelos ponteiros de `build.PAUSE_TILEMAPS`, `PAUSE_MAP_REVEAL`, `MAP_ICONS`,
  `MAP_ELEVATOR_LABELS`): tilemap `$B5:D000`; máscara `$82:9C27` — **o mesmo ponteiro da área 7** (debug; a sala dela é órfã, spec 11);
  **lista de chefe: ponteiro 0** (o `DrawBossMapIcons`, `$82:B892`, pula); map station `$82:CA4F` = **só `FFFF`** (2 bytes: a Tourian
  vanilla não tem map station); save `$82:CA51` = 2 ícones + 6 `FFFE` (8 entradas); elevador `$82:CA71` = 1 ícone + 7 `FFFE`; rótulo
  "to <área>" `$82:C7C3` = 1 (`980048005900`) e `FFFF` em `$C7C9`.
- Lista de FX de paleta da área 5 (`$83:AC46 + 5·2` → `$83:AD06`): `F761 F7A1 F7A5 FFC9 FFCD FFD1 FFD5 F745` — a entrada 0 é o
  **calor** `$F761` (`heat.HEAT_OBJECT`, o mesmo da entrada 0 da Norfair): uma sala nossa na área 5 que ligasse o bit 0 de paleta
  esquentaria. Tiles animados (`$83:AD16`): `8257 8251` (as 2 comuns) e `824B` (sem uso) no resto.
- Bits de chefe vanilla da área 5 (`vanilla_boss_bits`): só `$04`, das portas cinza de tipo 2 das salas órfãs `$DC65` e `$DCB1`.
  Nenhum código lê o byte de chefe da área 5 fora de dado de sala (`vendor/sm/src`: só `boss_bits_for_area[area_index]`, a tabela
  de tiles animados de `sm_87.c:215` e o `[4]` da Maridia).
- Código vanilla próprio da área 5: só a bola de fogo do Ridley (`sm_86.c:1165`). A map station é genérica:
  `PlmInstr_ActivateMapStation` (`$84:8C8F`) e o salvamento (`sm_80.c:235, 247`) usam `map_station_byte_array[area_index]`. O
  `RoomCode_SetCollectedMap` (`$8F:C90A`, a Tourian dá o mapa ao entrar) é código de estado de sala vanilla: nenhuma sala nossa o usa
  (`check_orphans`: código de sala só no espaço do build).
- Mapa salvo: `PackMapToSave`/`UnpackMapFromSave` (`$81:834B`/`$81:82E4`) leem a lista pelo ponteiro `$81:82D6 + 2·área`, no banco
  `$81` (`RomPtr_81`). `$81:EF1A–FEFF` (4070 bytes) é todo `FF` na ROM base e na construída (o `$81:FF00` em diante é texto).
- Load stations vanilla da área 5: 18 (`roomgraph.STATION_COUNTS`); a Mines pede 4 (0 = chegada pelo elevador do Tallon, 1–3 = as
  Save Stations A, B, C). SRAM do mapa livre: **748** de 1280 depois das cinco áreas construídas (o épico dizia 805: era a conta da
  linha de Phendrana, que deixa a própria Phendrana de fora).

## Mudança proposta

1. `tools/frigate/mapsave.py`: `FREE_81 = ($81:EF1A, $81:FEFF)`, `MOVES_TO_81 = (5,)`, `list_room(area)` e `list_at(area, size)`: a
   lista fica no lugar vanilla enquanto cabe; a da área 5 maior que 21 vai para o começo do `FREE_81`; a de qualquer outra área que não
   cabe para o build. A regra do arquivo diz isso.
2. `tools/build.py`:
   - `write_map_save_lists` usa `mapsave.list_at`: se a lista vai para o `$81`, confere que os bytes lá são `FF` e aponta
     `$81:82D6 + 2·área` para ela. Só roda quando a área 5 tiver sala (19e): hoje nada muda;
   - `VANILLA_PAUSE[5]` com os bytes acima (sem `"boss"`; `"map_station"` = `FFFF`);
   - `DEBUG_AREA = 7`; a trava do `write_pause_map` "máscara só desta área" aceita a área 7 dividindo a da área 5.
3. `tools/validate.py`:
   - `check_slot` aceita a área 5 (a da lista no `$81`); `own_fx_bits(base, área, região)` (o laço da 18b, igual para Phendrana);
   - **`check_mines_slot(base, built)`**: `check_slot("mines", 5, 4)`; não é a área de outro mundo; a área 5 em `MOVES_TO_81` e o `$81`
     livre todo `FF` na ROM base e, na construída, `FF` menos a lista da área 5 quando ela foi para lá (o ponteiro aponta para ela; sem
     sala da Mines, o vanilla); sem calor (`HEAT_BITS`, `GLOWS`); as duas listas de FX da área iguais a `MINES_PALFX`/`MINES_ANIMTILES`
     na ROM base e na construída; nenhuma sala nossa da área 5 liga bit de paleta (o calor `$F761`) nem de tiles animados da Tourian;
     bits de chefe vanilla = `MINES_VANILLA_BOSS_BITS` (`$04`) e as arenas planejadas (`$08`, `$10`) fora deles e distintas; ícones: sem
     lista de chefe, save ≥ 4, elevador ≥ 2, a map station contada (0 de 1: a 19e dá uma lista nova); máscara dividida só com a área 7;
     sem sala da Mines, os ponteiros e as listas da área 5 na ROM construída iguais aos da ROM base. Linha nova "mines (specs/19b)".

## Critérios de aceite

1. validate "221 salas, 460 portas, 0 problemas" com a linha "mines (specs/19b): área 5, 0 salas construídas; tabelas vanilla do mapa
   de pausa conferidas (ícones: save 8, elevador 8, map station 0 de 1: a lista vanilla é só FFFF, a 19e dá uma nova; sem lista de
   chefe); lista do mapa salvo até 21 bytes no lugar vanilla, maior no $81 livre ($81EF1A-$81FEFF, 4070 bytes $FF; usa 0); estações 4
   de 18 (save até 8); máscara da map station $829C27 dividida só com a área 7 (debug); SRAM do mapa livre: 748 de 1280; sem calor (a
   entrada 0 da lista de paleta da área é o calor $F761, nenhuma sala nossa a liga); listas de FX da área (paleta $83AD06, tiles
   animados $83AD16) iguais à ROM base, nenhum bit da Tourian (tiles animados comuns: $E3); bits de chefe vanilla da área: $04 (salas
   órfãs); arenas planejadas: $08, $10", e as outras linhas iguais. (protege = os bytes que o build vai reescrever na área 5, o lugar
   livre, a lista no `$81`, nenhum calor nem efeito da Tourian; falha_quando = mutações abaixo; não_prova = o mapa e as salas da Mines,
   19c/19e; a map station funcionando no emulador, 19e)
2. Mutações (`s19a/mutate_b.py`, em memória), cada uma pega; ensaios do `write_map_save_lists` e do `write_pause_map` numa área 5
   falsa, numa ROM base em memória.
3. ROM igual: sha1 `8e5d3771…f01a` em dois builds.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_mines_slot`; `check_vanilla_pause` com a área 5 | +1 |
| scratchpad | 23 mutações + 2 controles; 5 ensaios | 30 |
| run_tests.py | nenhum (ROM igual) | 0 |

## Riscos e reversão

- **Map station da área 5**: a lista vanilla de ícones é só `FFFF`; a 19e precisa de uma lista nova (ponteiro `$82:C7FB + 2·5` para
  o `$82` livre) e de conferir a máquina no emulador. Se não funcionar, a sala fica sem a máquina (só anotado, como diz o épico).
- **Ícone de chefe**: a área 5 não tem lista; se a 19h/19k quiserem o ícone, é uma lista nova também.
- **Calor nativo**: a entrada 0 da lista de paleta da área 5 é o calor; o validador recusa sala nossa da área 5 com bit de paleta.
- **A área 7 divide a máscara da 5**: escrever a máscara da Mines muda a da área 7 (debug, nada a carrega).
- Reverter: tirar `VANILLA_PAUSE[5]`, `DEBUG_AREA`, `list_at`/`list_room`/`FREE_81`/`MOVES_TO_81`, o uso no `write_map_save_lists`,
  `check_mines_slot`, `own_fx_bits` (o laço volta para o `check_phendrana_slot`) e a área 5 do `check_slot`.

## Fora de escopo

- `AreaDef` da Mines, salas, mapa de pausa escrito, lista da map station, nome no mapa e no continue, estações (19e).
- O mapa da Mines e o tamanho da lista (19c).

## Desvios (preenchido na implementação)

- **A lista do mapa no `$81` já está no build** (o épico pedia o mecanismo "preparado no `mapsave.py`"): `list_at` decide o lugar e o
  `write_map_save_lists` o usa; nada muda na ROM enquanto a área 5 não tiver sala. Ensaios D1–D3 provam o caminho.
- **A máscara da área 5 é dividida com a área 7** (achado; o épico não sabia): a trava do `write_pause_map` que exigia máscara só da
  área recusaria a Mines na 19e. Ela agora aceita só esse caso (`DEBUG_AREA`).
- **A lista de map station da área 5 é vazia**: o `write_pause_map` recusa uma map station na área 5 (ensaio D5). Fica para a 19e (a
  lista nova); a linha diz "map station 0 de 1".
- **Calor nativo na área 5** (achado): a entrada 0 da lista de paleta é o `$F761`. Coberto pela regra por sala (`own_fx_bits`).
- SRAM livre: 748 (o épico dizia 805, a conta da linha de Phendrana).
- Mutações (`s19a/mutate_b.out`), todas pegas: B1 Mines na área 4 (a de Phendrana); B2 na 6 (sem mapa salvo); B3 na 0 (a do Tallon);
  B4 área 5 fora de `MOVES_TO_81`; B5 byte não `FF` no `$81` livre da ROM base; B6 ponteiro da lista da área 5 movido sem sala da Mines;
  B7 byte escrito no `$81` livre da ROM construída; B8 área 5 em `HEAT_BITS`; B9 entrada 1 da lista de paleta mexida na ROM construída;
  B10 entrada 2 dos tiles animados mexida na ROM base; B11 sala da área 5 com o bit 0 de paleta (o calor); B12 com o bit 2 de tiles
  animados (da Tourian); B14 bits de chefe vanilla errados; B15 arena com o bit vanilla `$04`; B16 duas arenas com o mesmo bit; B17
  lista de ícone de chefe na área 5; B18 9 estações; B19 sem `VANILLA_PAUSE[5]`; B20 um ícone de save errado em `VANILLA_PAUSE[5]`
  (`check_vanilla_pause`); B21 máscara da área 5 dividida com a área 4; B22 ponteiro do tilemap da área 5 mexido sem sala da Mines; B23
  lista de save da área 5 mexida sem sala da Mines; B24 só 1 ícone de elevador. Controles limpos: B0 sem mutação, B13 sala da área 5
  com o bit 1 (comum) de tiles animados. Ensaios: D1 lista de 45 bytes da área 5 → ponteiro `$81:EF1A`, contagem 45, início +327, o
  lugar vanilla intacto; D2 lista de 21 bytes fica no lugar vanilla (`$81:82A6`); D3 lista de 81 bytes da área 0 → o build para; D4
  `write_pause_map` numa área 5 falsa (uma sala de Phendrana com save, estação 1) passa, ícone de save 1 escrito; D5 a mesma com uma
  map station → o build para (a lista vanilla é vazia).
- Verificação (05/11/2026, pasta real): `python3 -I tools/build.py` duas vezes → sha1 `8e5d377133b668151f4a558ebbb192d1bff0f01a` nas
  duas; `python3 -I tools/validate.py` → "221 salas, 460 portas, 0 problemas", só a linha nova "mines (specs/19b)" (diff com a saída
  da 19a). Os grupos A, B e C rodaram no fim da 19c (a ROM não mudou): ver a 19c.
