# 08 — Samus presa ao descer por porta de chão na fragata

Estado: verificada (23/10/2026: validate 62/126/0; .ips sha1 `8edc24a4…6a73` igual em dois builds; 37/37 testes)
Esforço estimado: 0,5 dia (reproduzir e varrer as portas 0,25 d; regra + checagem + teste 0,25 d)

Histórico: rascunho → aprovada (pedido do usuário, escopo "bug-fix pequeno") → implementada → verificada.

## Contexto

Achado na 07l (`specs/07l-regiao-d-fragata-afundada.md`, Desvios): no Tallon, descer pela porta de
chão da Savestation deixava a Samus afundada na borda debaixo da porta de teto do Reactor Access; ela
não andava até pular. A 07l corrigiu **só nas portas do Tallon** e anotou no `HANDOFF.md` que a
fragata (área 3) tem o mesmo problema no caminho principal (Map Facility → Connection Elevator to
Deck Beta). Os testes da fragata atravessam as portas com `go_through` (põe a Samus na frente da porta
e a cada sala a reposiciona), então nunca pegaram. Um jogador de verdade pega: cai na sala de baixo e
fica parado até apertar pulo.

## Estado atual (verificado)

- Entrada de porta (banco `$83`), bytes 8–9 = "distância da porta" (`research/sm_room_format.md`,
  seção 3; `LoadDoorHeader $82:DE12`): `$8000` = padrão (384/256 px por quadro na vertical).
- `tools/build.py` (antes): `door_push(side)` = `$0240` para porta de teto (subir), `$8000` nas outras;
  e, só quando `p.area is TALLON`, `TALLON_DOWN_PUSH = $0140` para descer e `TALLON_UP_PUSH_WATER =
  $0340` para subir para sala inundada. Fragata: 14 portas de chão (descer) com `$8000`, 14 de teto
  (subir) com `$0240`. Nenhuma sala da fragata é inundada.
- `Canvas.door_gap` (`tools/smlib/canvas.py:69`) põe uma borda na linha 6 (`TOP_DOOR_LEDGE_ROW`, topo
  em y 96) debaixo de toda porta de teto; é onde a Samus cai ao descer.
- Emulador, ROM de antes (sha1 `706ba8c7…f498`), **andando** (sem teleporte): da borda da porta oeste da
  Map Facility, pulo em parafuso até a plataforma, anda até o fim dela e cai na porta de chão. Na
  Connection Elevator to Deck Beta ela para em **y `$0052`** (pés em 103 = **7 px dentro da borda**),
  x `$007A`; segurando direita 30 quadros: x continua `$007A` (**anda 0 px**). Roteiro em
  `tests/run_tests.py` `walk_down_floor_door`.
- Varredura de **todas** as portas verticais da fragata (script de experimento, ROM antiga): cada porta
  de chão atravessada (as 3 cinza com o chefe morto), depois 60 quadros para a direita e 120 para a
  esquerda: nas **14**, y `$0051`/`$0052` e x parado nos três momentos (presa). Portas: airlock → mech_shaft,
  elevator_alpha → biotech_2, biotech_2 → vent_f, map_facility → elevator_beta, vent_f → vent_e,
  vent_e → vent_d, vent_a → vent_b, elevator_beta → conduit_hall, biotech_1 → elevator_gamma,
  biotech_1 → subvent_a, subvent_a → subvent_b, biohazard → transit_hall, transit_hall → cargo_lift,
  cargo_lift → reactor_entrance.

## Causa

O empurrão padrão da transição para baixo leva a Samus fundo demais: ela termina com os pés 6–7 px
dentro da borda da linha 6. Presa num bloco sólido, o andar não sai do lugar; o pulo a solta. `$0140`
(valor que o vanilla usa) a deixa acima da borda e ela pousa (medido no Tallon pela 07l).

## Mudança proposta

Uma regra só para todas as áreas, em `tools/build.py`:

```python
DOWN_PUSH = 0x0140; UP_PUSH = 0x0240; UP_PUSH_WATER = 0x0340; SIDE_PUSH = 0x8000
def door_push(side, into_water): B -> DOWN_PUSH; T -> UP_PUSH_WATER se a sala de destino é inundada,
                                 senão UP_PUSH; L/R -> SIDE_PUSH
```

e na montagem das entradas de porta `push = door_push(d.side, target.room.water)` (sai o `if p.area is
TALLON`). Para o Tallon nada muda (já era isso); na fragata as 14 portas de chão passam de `$8000` para
`$0140` (28 bytes no banco `$83`, mesmo tamanho: nenhum endereço muda). Subir na fragata continua `$0240`
(ver Desvios: `$0340` foi testado e quebra os poços).

## Critérios de aceite

1. Descer andando pela porta de chão da Map Facility: a Samus pousa na borda (y `$004B`) e anda para a
   direita (x `$007A` → `$00C6` em 30 quadros) (teste `fragata_desce_porta_de_chao_e_anda`:
   protege=pouso e andar depois de descer; falha_quando=empurrão padrão volta (ROM antiga: y `$0052`, x
   parado); não_prova=as outras 13 portas de chão — cobertas pela checagem 2 e pela varredura do Desvios).
2. Toda entrada de porta das áreas refeitas tem o empurrão da regra (`check_door_push` em
   `tools/validate.py`: protege=a regra nos bytes da ROM construída; falha_quando=uma porta com outro
   valor; não_prova=que o valor é bom no emulador).
3. Nenhum teste antigo muda de expectativa; validate 62/126/0; build reproduzível.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_door_push`: empurrão de cada porta = `build.door_push` | +1 checagem (126 portas) |
| run_tests.py (emulador) | `fragata_desce_porta_de_chao_e_anda` | +1 |
| experimento (fora do projeto) | varredura das 28 portas verticais da fragata, antes/depois | — |

## Riscos e reversão

Mudar o empurrão pode deixar a Samus alta demais e bater num teto; medido: nas 14 portas ela pousa na
borda e anda. Reverter = voltar `door_push` e reconstruir.

## Fora de escopo

- Mudar o empurrão de subida das salas secas (ver Desvios) ou a geometria das bordas/poços.
- Portas laterais.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (tabela inteira, regiões ativas: ABCD, 34 salas construídas, 2
  desenhadas fora do build, alcançáveis agora: 15) …` e `62 salas, 126 portas, 0 problemas`.
- `python3 -I tools/build.py` duas vezes → sha1 `8edc24a4b98c03595a6115fbba0bafae486c6a73` nas duas (antes
  `706ba8c7…f498`). Diferença para a ROM antiga: 28 bytes, todos em `$83:ADA2`–`$83:AFFB` (byte 8–9 das
  14 entradas das portas de chão da fragata). Espaço livre igual ao da 07l.
- `python3 -I tests/run_tests.py` → **37/37** (os 36 de antes + `fragata_desce_porta_de_chao_e_anda`).
- Nenhuma expectativa de teste antigo mudou. Só o comentário de `tallon_route_d` passou a citar
  `build.DOWN_PUSH` no lugar de `TALLON_DOWN_PUSH` (nome que saiu).
- O teste novo, rodado na ROM antiga (cópia guardada fora do projeto): falha com `7E0AFA = 0052, esperado
  004B` e `7E0AF6 = 007A, esperado 00C6`.
- Mutações da checagem (em memória, na ROM construída): ROM nova → 0 problemas; ROM antiga → 14 (as 14
  portas de chão da fragata, `$8000`); Map Facility → Elevator Beta = `$8000` → 1; Reactor Access → Savestation
  (Tallon, inundada) = `$0240` → 1; Elevator Beta → Map Facility (subir, seco) = `$0340` → 1; porta lateral
  Hangar → Air Lock = `$0140` → 1.

Medidas (emulador, varredura de todas as portas verticais da fragata):

- **Descer, antes** (`$8000`): as 14 portas de chão deixam a Samus em y `$0051`/`$0052` e ela anda 0 px para
  os dois lados. **Depois** (`$0140`): nas 14, y `$004B` (de pé na borda) e ela anda (ex.: Map Facility →
  Elevator Beta x `$0080` → `$00DB` → `$0025`; Biotech 1 → Subvent A `$0080` → `$00DB` → `$004F`).
- **Subir** (14 portas de teto, três jeitos: pulo parado + segurar direita, pulo parado + esquerda, pulo em
  parafuso para a direita): com `$0240` (antes e depois, igual) o pulo em parafuso passa em todas, e o pulo
  parado guiando para a **borda mais perto** (esquerda, saindo de x `$78` na tela) passa em 13; guiando para a
  borda do outro lado (direita) ela chega a x `$9B` quando já desceu abaixo da borda (que começa em `$A0`) e cai
  de volta em 11 das 14 (só as que chegam na Air Lock e na Biotech 1 passam; na Reactor Entrance → Cargo Lift cai também pela
  esquerda). Antes, a queda de volta a deixava presa na borda de baixo (y `$0052`); agora pousa nela (y `$004B`,
  conferido na Vent F: anda depois) e pode tentar de novo.
- **`$0340` para subir em toda sala** (o valor das salas inundadas) foi testado numa cópia: a varredura passa
  nos três jeitos, mas a fuga da fragata (`rota_completa_ida_e_fuga`, `parasite_queen_morre_e_fuga_com_timer`,
  `fuga_ridley_nave_e_final`) falha em Vent D → Vent E: a Samus sai 2 linhas mais alto, fica com a cabeça
  debaixo do degrau da linha 22 do poço (`shaft`: degraus até 8 linhas acima do chão) e não consegue ir para
  a direita; cai de volta. `$02A0`/`$02C0`/`$02E0` ainda deixam 8/8/1 portas falhando no pulo parado para a
  direita. Por isso subir em sala seca ficou `$0240` (com Space Jump, que a Samus sempre tem na fragata, o
  pulo em parafuso resolve). Anotado no HANDOFF como ideia (mexer na geometria: borda mais larga ou degrau
  mais alto), fora desta spec.
- Tallon: o único par vertical seco construído (Temple Lobby ↔ Artifact Temple) não muda (já era `$0140` para
  descer, `$0240` para subir).
