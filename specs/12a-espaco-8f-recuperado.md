# 12a — Segundo espaço do `$8F` (bloco órfão recuperado)

Estado: verificada (26/10/2026: validate 72/148/0 com a linha nova "$8F recuperado: 2254 bytes …"; .ips sha1
`3919c3c73d46afc45ffd4eb51083daebbe8264ff` igual em dois builds; 53/53 testes)
Esforço estimado: 0,5 dia
Épico: [12 — Chozo Ruins](12-chozo-ruins.md) (não depende da decisão dos itens)

## Contexto

Cabeçalhos de sala, estados, listas de portas e de PLMs têm de morar no banco `$8F` (research §0). Sobram 1781 bytes ali
(`$8F:F90B–FFFF`); as 72 salas de hoje gastaram ~55 bytes cada, então as 64 da Chozo pedem ~3500 (spec 11, achado B6). A spec 11
mediu 20637 bytes do `$8F` que só salas vanilla órfãs usam e sugeriu, como passo mais seguro, o pedaço `$8F:D4EF–DDBD` (2255
bytes), com uma condição: nunca um cabeçalho nosso num endereço que o código vanilla compara. Esta filha dá esse pedaço ao alocador
e põe no validador a prova de que ele é mesmo só de salas órfãs. Hoje nada é posto lá (o espaço livre ainda basta): a ROM não muda.

## Estado atual (verificado)

- `tools/build.py`: `Allocator` = uma faixa só, só escreve sobre `$FF`; `bank8f = Allocator(rom, *FREE_8F, "$8F")`, `FREE_8F =
  ($8F:E9AF, $8F:FFFF)`. Três salas (Reactor Core, Air Lock, a sala de save da fragata) montam o cabeçalho com estados condicionais
  calculando os ponteiros para `bank8f.ptr` antes do `put`.
- `tools/validate.py check_orphans` aceita ponteiro nosso de `$8F` (PLMs, código, raio X, scroll, fundo, código de porta) só a partir de
  `FREE_8F[0]`.
- **Quem compara o ponteiro da sala** (`$079B`), lido nos bytes da ROM base (`s12/roomcmp.py`: todo `LDA $079B` seguido de `CMP #`; também
  `LDX/LDY/CPX/CPY $079B`, que só leem o cabeçalho): `$88:81CC` `$CEFB`; `$88:8200` `$A66A`; `$88:82CA` `$9804 $96BA $B32E $B457
  $DD58 $DEDE` (salas de terremoto); `$91:D143` `$A66A $CEFB`. Igual ao C (`sm_88.c:209`, `319`, `349–354`; `sm_91.c:1203`).
- **Dono de cada byte de `$8F:D4EF–DDBD`** na ROM base (`s12/block.py`, `roomgraph.structures` das 262 salas): 2255 de 2255 bytes são
  estruturas de 38 salas órfãs (27 da área 4, 11 da área 5: cabeçalhos 1546, estados 338, scroll 154, listas de porta 162, scroll de PLM
  55); nenhum de sala das demos; nenhum dado da `VANILLA_SHARED`; igual à ROM base na construída. **`$DD58`** (cabeçalho da sala do Mother
  Brain, comparado) está dentro do pedaço. No C, nenhuma constante cai nos 38 cabeçalhos além de `$DD58` (`$DCFF` aparece como máscara de
  bits em `sm_a4.c:1634`); as outras constantes da faixa são de outros bancos (`$84:D6FC` PLM, `$88:D856` HDMA, `$A6:DC90…`).

## Mudança proposta

1. `tools/build.py`:
   - `RECLAIMED_8F = (($8F:D4EF, $8F:DD57), ($8F:DD59, $8F:DDBD))`: o pedaço da spec 11 menos o byte `$DD58` (assim nenhum dado
     nosso começa ali, cabeçalho ou não; perde-se 1 byte e o alocador não precisa saber o que é cabeçalho).
   - `ROOM_PTR_COMPARED`: os 8 endereços acima, com os sites.
   - `ours_8f(addr)`: endereço no espaço que o build aloca (`FREE_8F` ou `RECLAIMED_8F`).
   - `Allocator(..., reclaimed=…)`: primeiro o espaço livre (`$FF`, como antes); o que não couber vai para a primeira faixa recuperada onde
     couber (first fit, em ordem). Numa faixa recuperada o alocador confere que nada do build escreveu ali antes (guarda os bytes que viu ao
     ser criado). Faixa de outro banco = erro. `reclaimed_used()` para o relatório.
   - `put_at(bank, data, at)`: as 3 salas de cabeçalho condicional param o build se o cabeçalho for parar fora do `at` calculado (em vez de
     gravar ponteiros de estado errados).
   - `bank8f` com `reclaimed=RECLAIMED_8F`; linha nova no log: "$8F recuperado (specs/12a): … bytes usados".
2. `tools/validate.py`:
   - `check_orphans`: ponteiros nossos do `$8F` valem em `ours_8f` (antes só `>= FREE_8F[0]`).
   - `room_ptr_compares(rom)`: varre a ROM inteira por `LDA $079B; CMP #…` e devolve os endereços comparados.
   - **`check_reclaimed(rom, base, manifest)`**: (a) `build.ROOM_PTR_COMPARED` = o que os bytes comparam; (b) nenhum cabeçalho nosso num
     endereço comparado e todos em `ours_8f`; (c) cada faixa no `$8F`, fora do `FREE_8F`, sem cruzar outra, sem conter endereço comparado;
     (d) na ROM base, todo byte das faixas é estrutura de sala órfã (não de sala das demos, não da `VANILLA_SHARED`, não código nem dado sem
     dono); (e) na ROM construída, todo byte das faixas diferente da base é estrutura de uma sala nossa. Imprime a linha "$8F recuperado".

## Critérios de aceite

1. validate 0 problemas e a linha "$8F recuperado: 2254 bytes em 2 faixas ($8FD4EF-$8FDD57, $8FDD59-$8FDDBD), só de salas órfãs; usados
   pelas nossas salas: 0; o código compara a sala com 8 cabeçalhos, nenhum nosso nem nas faixas". (protege = só dado de sala órfã é
   reaproveitado, nenhuma sala nossa ganha efeito de sala vanilla; falha_quando = mutações abaixo; não_prova = código vanilla que leia o
   pedaço por um ponteiro calculado em tempo de execução que não passe por cabeçalho/porta — nenhum achado no C)
2. Mutações (scratchpad `s12/mutate.py`, ROM/manifest/constantes em memória), cada uma pega; a lista de PLMs movida para o bloco vale.
3. Experimento positivo numa cópia do projeto (`s12/proj_spill`, `FREE_8F` encurtado para `$8F:E9AF–F2FF`): o build põe 1547 bytes no
   bloco (21 cabeçalhos e listas), validate 0 problemas com a linha do Tallon igual, e os 53 testes do emulador passam nessa ROM.
4. ROM igual na pasta real: sha1 `3919c3c7…64ff` em dois builds; linha do Tallon igual; 53/53.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` (+ `check_orphans` com `ours_8f`) | +1 checagem |
| scratchpad | 13 mutações do validador + 5 do alocador; build forçado ao bloco + validate + 53 testes | 19 |
| run_tests.py | nenhum novo (ROM igual) | 0 |

## Riscos e reversão

- **Save de SRAM vanilla** (spec 11, B7): com o bloco em uso, um `.srm` do SM vanilla que carregue uma sala de Maridia/Tourian cairia num
  cabeçalho sobrescrito. Exige copiar o save de outra ROM.
- **Demos**: se a lista `DEMO_SCENES` mudar (decisão pendente da spec 11), `check_reclaimed` reavalia o pedaço sozinho.
- First fit mistura as estruturas entre as faixas (o log e o manifest dizem onde ficou cada sala).
- Reverter: tirar `RECLAIMED_8F`/`ROOM_PTR_COMPARED`/`ours_8f`/`put_at` e o parâmetro `reclaimed`, `check_reclaimed` e voltar as 3 linhas
  de `check_orphans`; como nada usa o bloco hoje, a ROM não muda.

## Fora de escopo

- Os outros pedaços órfãos (`$8F:92B3–9878`, `$8F:C49B–C8C6`): entram com uma linha em `RECLAIMED_8F` quando a Chozo precisar; a checagem
  prova cada um (o primeiro contém `$96BA` e `$9804`: tem de ser partido).
- `$83`, `$A1`, `$B4` (sobra espaço).
- Apagar as salas órfãs ou encher o bloco de `$FF`.

## Desvios (preenchido na implementação)

- **Faixa partida em volta de `$DD58`** em vez de uma regra "cabeçalho nunca em endereço comparado" dentro do alocador: mais simples, o
  alocador não precisa saber o tipo do dado, e o validador ainda confere os cabeçalhos de todas as salas nossas.
- `put_at`: guarda a mais nas 3 salas de cabeçalho condicional (não estava no pedido; sem ela, um cabeçalho que caísse no bloco gravaria
  ponteiros de estado do lugar errado sem erro).
- Mutações (`s12/mutate.out`), todas pegas: M1 faixa com `$DD58`; M2 faixa sobre a sala da demo `$91F8`; M3 sobre o fundo `$E117`
  (`VANILLA_SHARED`); M4 sobre código (`$8F:E5E6`); M5 cruzando o espaço livre; M6 fora do `$8F`; M7 faixas que se cruzam; M8
  `ROOM_PTR_COMPARED` sem `$DD58`; M9 cabeçalho nosso em `$DD58`; M10 cabeçalho nosso fora do espaço do build; M11 byte escrito no bloco sem
  ser de sala nossa; M13 lista de PLMs nossa em outro dado vanilla (`$8F:C49B`). M12 (lista de PLMs nossa movida para o bloco): aceita,
  como deve. Alocador: A1 cheio → vai para `$8F:D4EF` e um pedaço pequeno depois volta ao espaço livre (first fit); A2 bloco já escrito →
  erro; A3 sem espaço → erro; A4 `put_at` com o cabeçalho caindo no bloco → erro; A5 faixa de outro banco → erro.
- Experimento positivo (`s12/proj_spill`, cópia sem `research/prime_fs`): `FREE_8F` até `$8F:F2FF` → log "$8F recuperado: $8FD4EF-$8FDD57
  1547/2153 bytes usados"; 21 cabeçalhos no bloco (de `tallon_vent_b` `$8F:D4EF` a `tallon_transport_mines_east` `$8F:D7FB`), mais listas de
  porta e de PLMs; validate "72 salas, 148 portas, 0 problemas", linha do Tallon igual, "órfãs … $8F 19090" (20637 − 1547) e "usados pelas
  nossas salas: 1547"; `python3 -I tests/run_tests.py` nessa cópia → **53/53** (inclui `tallon_cadeia_completa`, `tallon_fragata_afundada`
  e `tallon_grande_arvore`, que passam por salas com cabeçalho no bloco).
- Verificação final (26/10/2026, pasta real, 12a e 12b juntas): `python3 -I tools/validate.py` → "72 salas, 148 portas, 0 problemas", linha
  do Tallon igual ("44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"), "órfãs" igual à da spec 11, e as linhas novas
  "chozo (specs/12b): …" e "$8F recuperado: … usados pelas nossas salas: 0 …"; `python3 -I tools/build.py` duas vezes → sha1
  `3919c3c73d46afc45ffd4eb51083daebbe8264ff` nas duas (igual ao de antes); `build/manifest.json` byte a byte igual ao de antes;
  `python3 -I tests/run_tests.py` → **53/53**.
