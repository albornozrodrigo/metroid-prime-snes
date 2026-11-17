# 18b — Lugar de Phendrana na área 4 (e o plano das áreas)

Estado: verificada (03/11/2026: validate 165/342/0 com a linha nova "phendrana (specs/18b): área 4 …"; .ips sha1
`15d37c8ace02ff12e8c0907cd085febe3eca65cd` igual em dois builds; grupo A 34/34, grupo B 64/64)
Esforço estimado: 0,5 dia
Épico: [18 — Phendrana Drifts](18-phendrana-drifts.md) (decisão 2, opção (a): **padrão aceito, a confirmar**; toolchain, ROM igual)

## Contexto

Como a 12b (Chozo) e a 17b (Magmoor), esta filha reserva a área do SM de Phendrana — a 4, da Maridia — e confere os bytes vanilla das
tabelas que o build vai reescrever **antes** de existir sala. Fecha também a pendência do épico 17 (aviso de capacidade): o plano das
áreas para os três mundos que faltam — **Phendrana na 4, Phazon Mines na 5, Impact Crater dentro da 0** —, escrito no código. A área 4
tem código vanilla próprio: o mapa de pausa rola 24 px a mais para a esquerda (`sm_82.c:1811`, inofensivo), e as listas de FX de paleta
e de tiles animados da área são da Maridia: nenhuma sala nossa pode ligá-las por engano. A ROM não muda.

## Estado atual (verificado)

- `tools/areas.py`: `CHOZO_AREA = 1`, `MAGMOOR_AREA = 2`; áreas em uso 0, 1, 2, 3 (e a 6 pela cena da fuga). `build.VANILLA_PAUSE` com
  0, 1, 2 e 3.
- Tabelas da área 4 na ROM base (roteiro `s18a/area4.py`, pelos ponteiros de `build.PAUSE_TILEMAPS`, `PAUSE_MAP_REVEAL`, `MAP_ICONS`,
  `MAP_ELEVATOR_LABELS`; nenhum ponteiro dividido com outra área): tilemap `$B5:C000`, máscara `$82:9B27`; chefe `$82:C9DB` = (`$13C`,
  `$54`) `FFFF`; map station `$82:C9ED` = (`$88`, `$90`) `FFFF`; save `$82:C9F3` = 4 ícones + 4 `FFFE` (8 entradas, até `$CA13`);
  elevador `$82:CA13` = 1 ícone + 7 `FFFE`; rótulos "to <área>" `$82:C7AF` = 3 rótulos (`0801 0800 5900`, `3000 A000 5A00`, `7800 A000
  5A00`) e `FFFF` em `$C7C1` (`$C7C3` é a lista da área 5).
- Lista de FX de paleta da área 4 (`$83:AC46 + 4·2` → `$83:ACE6`): `F795 F799 F79D F745 F745 F745 F745 F745` (3 objetos da Maridia);
  lista de tiles animados (`$83:AC56 + 4·2` → `$83:ACF6`): `8257 8251 8287 828D 824B 824B 824B 824B`. As entradas iguais nas 8 áreas
  (bits `$E3`: 0, 1, 5, 6, 7) são comuns; as 2 e 3 são da Maridia. A chuva/lava/água que o projeto usa: a água (`build.WATER_FX`) tem
  os dois bytes 0; a lava liga o bit 1 dos tiles animados (comum).
- Load stations vanilla da área 4: 20 (`roomgraph.STATION_COUNTS`); Phendrana pede 5 (0 = chegada pelo elevador norte, 1–4 = as Save
  Stations; épico). SRAM do mapa: livre **805** de 1280 depois das áreas construídas (vanilla 327 + fragata + Tallon 47 + Chozo 41 +
  Magmoor 30); a lista da área 4 cabe no lugar vanilla até 80 bytes (`mapsave.LIST_ROOM[4]`): **a lista da área 5 não precisa mudar de
  lugar agora** (fica para o épico da Mines).
- `validate.check_slot` só aceita as áreas 0–4 e dizia "5 = Impact Crater" (o plano antigo).

## Mudança proposta

1. `tools/areas.py`: `PHENDRANA_AREA = 4`, `MINES_AREA = 5`, `IMPACT_CRATER_AREA = 0`, com o porquê (o plano). Nenhuma `AreaDef` nova (18e).
2. `tools/build.py`: `VANILLA_PAUSE[4]` com os bytes acima (formato das áreas 1 e 2).
3. `tools/frigate/mapsave.py`: a regra das áreas diz o plano (Phendrana 4 no lugar vanilla, Mines 5 com a lista no `$81`, Impact Crater
   na 0).
4. `tools/validate.py`:
   - **`check_phendrana_slot(base, built)`**: `check_slot("phendrana", 4, 5)` (área livre, 0–4, `VANILLA_PAUSE`, lista ≤ o que sobra da
     SRAM, 5 estações ≤ as 20 vanilla e ≤ 8); não é a área da Chozo nem da Magmoor; o plano (`MINES_AREA` livre e com mapa salvo,
     `IMPACT_CRATER_AREA` = a do Tallon); a área 4 fora de `heat.HEAT_BITS`/`GLOWS` (sem calor nem frio, decisão 5); as duas listas de FX
     da área 4 iguais a `PHENDRANA_PALFX`/`PHENDRANA_ANIMTILES` na ROM base e na construída; toda sala nossa da área 4 (o FX dela: o do
     build, a água ou um vanilla de `RoomDef.fx`) com o byte de FX de paleta 0 e só bits comuns de tiles animados. Linha nova
     "phendrana (specs/18b): …".
   - `check_vanilla_pause` já cobre a área 4 (lê todas as entradas); `check_slot` diz "5 = Phazon Mines, com a lista do mapa no $81".

## Critérios de aceite

1. validate "165 salas, 342 portas, 0 problemas" com a linha "phendrana (specs/18b): área 4, 0 salas construídas; tabelas vanilla do
   mapa de pausa conferidas; lista do mapa salvo até 80 bytes no lugar vanilla; estações 5 de 20 (save até 8); SRAM do mapa livre: 805
   de 1280; sem calor; listas de FX da área (paleta $83ACE6, tiles animados $83ACF6) iguais à ROM base, nenhum bit da Maridia (tiles
   animados comuns: $E3); plano: Mines na área 5, Impact Crater na 0", e as outras linhas iguais. (protege = os bytes que o build vai
   reescrever na área 4, o lugar livre, nenhum efeito da Maridia nas salas; falha_quando = mutações abaixo; não_prova = o mapa e as salas
   de Phendrana, 18c/18e)
2. Mutações (`s18a/mutate_b.py`, em memória), cada uma pega; ensaio: `build.write_pause_map` numa área 4 falsa de uma sala, numa ROM
   base em memória, passa por todas as `replace_checked` da área 4.
3. ROM igual: sha1 `15d37c8a…65cd` em dois builds; A 34/34, B 64/64.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_phendrana_slot`; `check_vanilla_pause` com a área 4 | +1 |
| scratchpad | 21 mutações (2 controles) + 1 ensaio do `write_pause_map` | 22 |
| run_tests.py | nenhum (ROM igual) | 0 |

## Riscos e reversão

- O mapa de pausa da área 4 rola 24 px a mais para a esquerda (`sm_82.c:1811`): a 18e confere no emulador que o mapa de Phendrana
  aparece inteiro.
- O Botwoon lê o byte de chefe da área 4: nenhum Botwoon nas nossas salas.
- Reverter: tirar as 3 constantes, `VANILLA_PAUSE[4]`, `check_phendrana_slot` e as frases do plano.

## Fora de escopo

- `AreaDef` de Phendrana, salas, mapa de pausa escrito, nome no mapa e no continue, estações (18e).
- Mover a lista do mapa salvo da área 5 para o `$81` (épico da Mines).

## Desvios (preenchido na implementação)

- **Listas de FX conferidas também na ROM construída** e a regra por sala (byte de paleta 0, tiles animados só nos bits comuns, lidos
  das 8 listas): o épico pedia "conferidas, nada de Maridia nas nossas salas"; a regra precisa de sala para morder, então as mutações
  B17–B21 usam uma área 4 falsa com uma sala da Magmoor copiada.
- **O plano das áreas virou checagem** (Mines livre e com mapa salvo, Impact Crater na área do Tallon), além do comentário.
- SRAM livre: 805 (o épico dizia 835, de antes da Magmoor ser construída; os 30 da Magmoor já estão no save).
- Mutações (`s18a/mutate_b.out`), todas pegas: B1 ícone de chefe; B2 tilemap; B3 rótulo de elevador; B4 lista de save; B5 sem
  `VANILLA_PAUSE[4]`; B6–B9 Phendrana na área 1, 2, 3 e 5; B10 9 estações; B11 Mines na 4; B12 Mines na 6; B13 Impact Crater na 5; B14
  área 4 em `HEAT_BITS`; B15 calor na entrada 3 da lista de paleta na ROM construída; B16 entrada 2 dos tiles animados mexida na ROM base;
  B18 sala inundada da área 4 com o bit 0 de paleta; B19 com o bit 2 de tiles animados (Maridia); B21 sala quente na área 4. Controles
  limpos: B0 sem mutação, B17 sala sem FX, B20 o bit 1 de tiles animados (comum). Ensaio D1: `write_pause_map` numa área 4 falsa (uma
  sala, estação 1) aceita as listas vanilla; o ícone de save 1 escrito, os rótulos viram `FF…` com o `FFFF` vanilla depois.
- Verificação (03/11/2026, pasta real): `python3 -I tools/build.py` duas vezes → sha1 `15d37c8ace02ff12e8c0907cd085febe3eca65cd` nas
  duas; `python3 -I tools/validate.py` → "165 salas, 342 portas, 0 problemas", só a linha nova "phendrana (specs/18b)"; grupo A
  **34/34**, grupo B **64/64**.
