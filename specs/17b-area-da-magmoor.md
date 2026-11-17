# 17b — Lugar da Magmoor na área 2 (e o calor por área)

Estado: verificada (01/11/2026: validate 136/284/0 com a linha nova "magmoor (specs/17b): área 2 …"; .ips sha1
`0f5cc669fc89800b65e43169c9cd5a816fde0653` igual em dois builds; manifest igual; 83/83 testes)
Esforço estimado: 0,5 dia
Épico: [17 — Magmoor Caverns](17-magmoor-caverns.md) (decisão 6: área 2, aceita pelo usuário; toolchain, ROM igual)

## Contexto

Como a 12b fez para a Chozo, esta filha reserva a área do SM da Magmoor — a 2, da Norfair — e confere os bytes vanilla das tabelas
que o build vai reescrever **antes** de existir sala, para que a 17e não descubra um erro de tabela no meio. E generaliza o calor
(12g/12g2), que hoje só sabe da área 1: na Norfair o objeto do calor já está na lista de FX de paleta (entrada 0), então a área 2 não
pede patch, e o FX das salas quentes tem de ligar o bit 0, não o 4. A ROM não muda.

## Estado atual (verificado)

- `tools/areas.py`: `CHOZO_AREA = 1`; áreas em uso 0 (Tallon), 1 (Chozo), 3 (fragata). `build.VANILLA_PAUSE` tem 0, 1 e 3.
- `tools/chozo/heat.py`: `HEAT_BIT = 4`, `HEAT_FX` com o bit 4, `patch(base, area)` escreve `$F761` na entrada 4 da lista da área (e
  falha se a entrada não for `$F745`); o build chama `patch(rom, CHOZO.number)` e põe o `HEAT_FX` uma vez; o validador (`check_heat`,
  `check_heat_in_rom`) só aceita sala quente na área 1.
- Tabelas da área 2 na ROM base (roteiro `s17a/area2.py`, pelos ponteiros de `build.PAUSE_TILEMAPS`, `PAUSE_MAP_REVEAL`, `MAP_ICONS`,
  `MAP_ELEVATOR_LABELS`; nenhum ponteiro dividido com outra área): tilemap `$B5:A000`, máscara `$82:9927`, nome `$82:969F`; chefe
  `$82:C90B` = (`$B8`, `$90`) `FFFF`; map station `$82:C91D` = (`$48`, `$28`) `FFFF`; save `$82:C923` = 6 ícones + 2 `FFFE` (8 entradas,
  até `$C943`); elevador `$82:C943` = 3 ícones + 5 `FFFE`; rótulos "to <área>" `$82:C799` = 1 rótulo (`50 00 08 00 5A 00`) e `FFFF`
  (`$C7A1` é a lista da área 3).
- Lista de FX de paleta da área 2 (`$83:AC46 + 2·2` → `$83:ACA6`): `F761 F785 F789 F78D F791 F745 F745 F745` — o calor `$F761` na entrada 0,
  4 brilhos de lava nas 1–4. Na área 1 (`$83:AC86`): `F775 F77D F781 F779 F745…` (a 12g põe o calor na 4).
- Load stations vanilla da área 2: 23 (`roomgraph.STATION_COUNTS`); a Magmoor pede 3 (0 = chegada da Chozo, 1–2 = Save Stations A e B;
  épico). SRAM do mapa: 445 de 1280 usados (vanilla 327 + fragata + Tallon 47 + Chozo 41), a lista da área 2 no lugar vanilla até 80 bytes
  (`mapsave.LIST_ROOM[2]`).
- Código vanilla da área 2 (épico, C): gelo 300 quadros em vez de 400 (`sm_a0.c:2751`, `2789`) e a bola de fogo do Ridley (`sm_86.c:1163`;
  o Ridley mora na área 3 aqui). Nada que pese na Magmoor além do gelo mais curto (aceito pelo usuário com a área).

## Mudança proposta

1. `tools/areas.py`: `MAGMOOR_AREA = 2`, com o porquê. Nenhuma `AreaDef` nova (17e).
2. `tools/build.py`: `VANILLA_PAUSE[2]` com os bytes acima (mesmo formato das áreas 0, 1 e 3). Sem uso até a `AreaDef` da área 2.
3. `tools/chozo/heat.py` por área: `HEAT_BITS = {1: 4, 2: 0}`; `heat_fx(area)` (o FX "sem líquido" com o bit da área; `HEAT_FX =
   heat_fx(1)`, bytes iguais); `native(base, area)`; `patch(base, area)` devolve `None` se a lista já tem o calor naquela entrada. O build
   aplica o patch de cada área de `HEAT_BITS` que precise (só a 1) e guarda um FX de calor por área, posto na primeira sala quente da área
   (a da Chozo continua no mesmo lugar: ROM igual).
4. `tools/validate.py`:
   - `HOT_WORLDS = {CHOZO_AREA: (tabela, HOT_ROOMS)}` (a 17c põe a Magmoor); `check_heat`: sala quente só em área de `HEAT_BITS`, na
     `HOT_ROOMS` do mundo dela, não de elevador, portas com a Varia; `check_heat_in_rom` por área: área nativa (2) com a lista inteira igual à
     da ROM base, área com patch (1) só com a entrada do calor mudada; os estados de sala quente apontam para o `heat_fx` da área; nenhuma
     sala nossa não quente liga o bit de calor da área; salas vanilla de área com patch não usam o bit (numa nativa usam: é o calor delas).
   - `check_slot(mundo, área, estações)` (o miolo da `check_chozo_slot`, que fica com a mesma linha) e **`check_magmoor_slot`**: área livre
     e não a da Chozo, 0–4, `VANILLA_PAUSE`, lista do mapa salvo ≤ o que sobra da SRAM, 3 estações ≤ as 23 vanilla e ≤ 8 de save, a área
     em `HEAT_BITS` com o calor nativo (sem patch). Linha nova "magmoor (specs/17b): …". `check_vanilla_pause` já cobre a área 2 (lê todas
     as entradas).

## Critérios de aceite

1. validate "136 salas, 284 portas, 0 problemas" com a linha "magmoor (specs/17b): área 2, 0 salas construídas; tabelas vanilla do mapa de
   pausa conferidas; lista do mapa salvo até 80 bytes no lugar vanilla; estações 3 de 23 (save até 8); SRAM do mapa livre: 835 de 1280;
   calor nativo (lista de FX de paleta $83ACA6, entrada 0 = $F761, sem patch)", e as outras linhas iguais. (protege = os bytes que o build
   vai reescrever na área 2, o lugar livre, o calor certo por área; falha_quando = mutações abaixo; não_prova = o mapa e as salas da Magmoor,
   17c/17e)
2. Mutações (`s17a/mutate_b.py`, em memória), cada uma pega; ensaio: `build.write_pause_map` numa área 2 falsa de uma sala, numa ROM base em
   memória, passa por todas as `replace_checked` da área 2.
3. ROM igual: sha1 `0f5cc669…0653` em dois builds; 83/83.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_magmoor_slot` (+ `check_slot`), `check_vanilla_pause` com a área 2, `check_heat`/`check_heat_in_rom` por área | +1 (e 2 generalizadas) |
| scratchpad | 15 mutações + 1 ensaio do `write_pause_map` | 16 |
| run_tests.py | nenhum (ROM igual; `sala_quente` continua na ROM de teste da 12g) | 0 |

## Riscos e reversão

- `heat.py` mora em `tools/chozo/` mas agora serve duas áreas; movê-lo para `smlib` é só nome (fora desta filha, para não mexer em imports).
- Reverter: tirar `MAGMOOR_AREA`, `VANILLA_PAUSE[2]`, `HEAT_BITS`/`heat_fx`/`native` (voltando `patch` e o build ao `HEAT_FX`) e as checagens.

## Fora de escopo

- `AreaDef` da Magmoor, salas, mapa de pausa escrito, nome "MAGMOOR" no mapa e no continue, estações (17e).
- FX de paleta com os brilhos da lava (bits 1–4) nas salas: escolha de estilo da 17d.

## Desvios (preenchido na implementação)

- **`check_slot`** saiu da `check_chozo_slot` (mesma lógica; a linha da Chozo igual) para a Magmoor não copiar o miolo; ganhou a checagem
  das estações (a da Chozo chama sem estações, como antes).
- **Calor por área** também no build (não só no validador): o laço aplica `heat.patch` a cada área de `HEAT_BITS` (a 2 dá `None`) e o FX de
  calor fica num dicionário por área. A ordem de alocação no `$83` da área 1 não mudou (manifest igual).
- `check_heat_in_rom` confere também que a entrada do calor da área **é** `$F761` na ROM construída (antes só que as outras não mudaram).
- Mutações (`s17a/mutate_b.out`), todas pegas: B1 ícone de chefe da área 2; B2 tilemap; B3 rótulo de elevador; B4 lista de save; B5 Magmoor
  na área 1 ("já usada por ['chozo']"); B6 na 3 (fragata); B7 na 5; B8 na 4 (sem `VANILLA_PAUSE` e sem calor); B9 bit de calor da área 2 = 1
  (a entrada 1 é um brilho, `$F785`); B10 área 2 fora de `HEAT_BITS`; B11 9 estações; B12 entrada 3 da lista da área 2 mexida na ROM; B13 o
  calor da área 2 apagado na ROM; B14 sala quente da área 2 fora da tabela; B15 o patch da área 1 apagado. Sem mutação: limpo. Ensaio D1:
  `write_pause_map` numa área 2 falsa (uma sala da Chozo) aceita as listas vanilla; ícone de save 0 escrito, o rótulo vira `FF…` com o
  `FFFF` vanilla depois.
- Verificação (01/11/2026, pasta real): `python3 -I tools/build.py` duas vezes → sha1 `0f5cc669fc89800b65e43169c9cd5a816fde0653` nas duas,
  `build/manifest.json` igual; `python3 -I tools/validate.py` → "136 salas, 284 portas, 0 problemas", só a linha nova "magmoor (specs/17b)";
  `python3 -I tests/run_tests.py` → **83/83**.
