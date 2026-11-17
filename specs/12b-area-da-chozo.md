# 12b — Lugar da Chozo na área 1

Estado: verificada (26/10/2026: validate 72/148/0 com a linha nova "chozo (specs/12b): área 1 …"; .ips sha1
`3919c3c73d46afc45ffd4eb51083daebbe8264ff` igual em dois builds; 53/53 testes)
Esforço estimado: 0,5 dia
Épico: [12 — Chozo Ruins](12-chozo-ruins.md) (decisão 1; não depende da decisão dos itens)

## Contexto

A Chozo Ruins vai precisar de uma área do SM própria (mapa de pausa, minimapa, mapa salvo, load stations, nome). O build já faz isso
para qualquer área (spec 07a): basta uma `AreaDef` com o número e, em `build.VANILLA_PAUSE`, os bytes vanilla das tabelas que ele
reescreve no lugar (o build confere esses bytes antes de escrever). Esta filha reserva o lugar — a área 1 — e confere os bytes dela
**antes** de existir sala, para que a primeira filha com salas (12f) não descubra um erro de tabela no meio do caminho. A ROM não muda.

## Estado atual (verificado)

- Áreas usadas: 0 (Tallon), 3 (fragata). `VANILLA_PAUSE` só tinha 0 e 3 (`tools/build.py`), conferidas pelo build ao escrever.
- Código vanilla que muda por área (C `vendor/sm/src`, `grep area_index`): 1 = um caso do raio X (`sm_91.c:1065`, `$91:CF3E`);
  2 = projéteis inimigos por área (`sm_86.c:1163`) e congelamento de 300 quadros em vez de 400 (`sm_a0.c:2751`, `2789`) e o Ridley
  (`sm_a6.c`); 4 = mapa de pausa rola 24 px (`sm_82.c:1811`); 5 reservada à Impact Crater (`tools/frigate/mapsave.py`), 6 Ceres, 7 debug.
- Tabelas da área 1 na ROM base (bytes, lidos pelos ponteiros de `build.PAUSE_TILEMAPS`, `PAUSE_MAP_REVEAL`, `MAP_ICONS`,
  `MAP_ELEVATOR_LABELS`): tilemap `$B5:8000`, máscara `$82:9827`, nome `$82:9687`; chefe `$82:C89D` = (`$1BC`, `$9C`) `FFFF`; map station
  `$82:C8B7` = (`$28`, `$28`) `FFFF`; save `$82:C8BD` = 5 ícones + 3 `FFFE` (8 entradas, como a área 0); elevador `$82:C8DD` = 4 ícones +
  4 `FFFE`; rótulos "to <área>" `$82:C779` = 5 rótulos de 6 bytes (`48 00 08 00 59 00` …) e `FFFF`.
- SRAM do mapa: 404 de 1280 bytes usados (vanilla 327 + fragata 30 + Tallon 47); a lista da área 1 no lugar vanilla aceita até 80 bytes
  (`mapsave.LIST_ROOM`). Load stations da área 1: 19 (`roomgraph.STATION_COUNTS`).

## Mudança proposta

1. `tools/areas.py`: `CHOZO_AREA = 1`, com o porquê (menos código vanilla por área entre 1, 2 e 4). Nenhuma `AreaDef` nova.
2. `tools/build.py`: `VANILLA_PAUSE[1]` com os bytes acima (mesmo formato das áreas 0 e 3). Sem uso no build até haver uma `AreaDef`
   da área 1.
3. `tools/validate.py`:
   - `check_vanilla_pause(base)`: toda entrada de `VANILLA_PAUSE` (0, 1, 3) igual à ROM base — ponteiros de tilemap e máscara, e cada
     lista de ícones/rótulos começa com os bytes da entrada. (O build só conferia a área que escreve.)
   - `check_chozo_slot()`: a área `CHOZO_AREA` não é de outra `AreaDef`, está em 0–4, tem `VANILLA_PAUSE`, e a lista máxima no lugar vanilla
     cabe no que sobra do buffer de SRAM depois das áreas construídas. Imprime a linha "chozo (specs/12b): …".

## Critérios de aceite

1. validate 0 problemas com a linha "chozo (specs/12b): área 1, sem sala ainda; tabelas vanilla do mapa de pausa conferidas; lista do
   mapa salvo até 80 bytes no lugar vanilla; SRAM do mapa livre: 876 de 1280". (protege = os bytes que o build vai reescrever na área 1 e
   o lugar livre; falha_quando = byte de lista errado, área ocupada/reservada/sem tabela; não_prova = o mapa da Chozo de verdade, da 12c/12f)
2. Mutações (scratchpad `s12/mutate_b.py`), cada uma pega; ensaio: `build.write_pause_map` numa área 1 falsa de uma sala, numa ROM base
   em memória, passa por todas as `replace_checked` da área 1.
3. ROM igual: sha1 `3919c3c7…64ff` em dois builds; 53/53.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_vanilla_pause`, `check_chozo_slot` | +2 |
| scratchpad | 7 mutações + 1 ensaio do `write_pause_map` | 8 |
| run_tests.py | nenhum (ROM igual) | 0 |

## Riscos e reversão

- Se o usuário preferir a área 4 (ou 2): trocar `CHOZO_AREA` e pôr a entrada dela em `VANILLA_PAUSE` (os bytes saem do mesmo roteiro); a
  checagem acusa se faltar.
- Reverter: tirar `CHOZO_AREA`, `VANILLA_PAUSE[1]` e as duas checagens.

## Fora de escopo

- `AreaDef` da Chozo, salas, mapa de pausa escrito, nome "CHOZO" no mapa e na tela de continue (12f), estações (12e/12f).

## Desvios (preenchido na implementação)

- **Área escolhida antes da confirmação do usuário**: a 1 é a recomendação do épico; é uma constante e uma entrada de tabela, sem efeito na
  ROM até a 12f. Fica na lista de perguntas do épico.
- A checagem de `VANILLA_PAUSE` cobre também as áreas 0 e 3 (antes conferidas só pelo build ao escrever).
- Mutações (`s12/mutate_b.out`), todas pegas: B1 ícone de chefe da área 1 errado; B2 tilemap da área 1 errado; B3 lista de save da área 0
  errada; B4 rótulos de elevador da área 1 errados; B5 Chozo na área 3 ("já usada por ['frigate']"); B6 na área 5; B7 na área 2 (sem
  `VANILLA_PAUSE`). Sem mutação: limpo. Ensaio D1: `write_pause_map` na área 1 (sala falsa copiada da Chozo West) aceita as listas vanilla.
- Verificação final: ver a linha de verificação no fim da 12a (as duas foram verificadas juntas, na pasta real).
