# 10c — Mapa de pausa com a forma da sala

Estado: verificada (26/10/2026: validate 72/148/0; .ips sha1 `2eb8a710b1166045f650265d47ff6c763a96bd9f` igual em dois builds; 52/52 testes)
Esforço estimado: 0,25 dia
Épico: [10 — Polimento do Tallon](10-polimento-tallon.md) (achado A5)

## Contexto

O mapa de pausa desenha cada sala como a caixa dela (largura × altura em telas, parede só na borda da caixa). Várias salas do
Tallon têm telas inteiras de rocha (a caixa do Prime é maior que a parte andável); a Samus nunca entra nelas, então nunca
ficam exploradas: no mapa a sala aparece recortada e **aberta** do lado da rocha (Tallon Canyon em L sem parede, Artifact Temple
com degraus abertos). Foto: `specs/img/10c-mapa-antes.png` (todas as telas não maciças exploradas por RAM).

## Estado atual (verificado)

- `tools/frigate/pausemap.py:63` (`room_tile`): parede nos lados em que a tela está na borda da caixa; `build()` põe esse tile em
  toda tela da caixa e a máscara de revelação (map station) cobre a caixa inteira; a lista do save sai da máscara
  (`mapsave.needed`): área 0 = 47 bytes em +357, área 3 = 30 em +327 (log do build).
- Telas inteiras de bloco tipo `$8` (sólido), contadas no nível de cada sala: Tallon 16 — Canyon (3,1) (2,2) (3,2), Artifact Temple
  (3,1) (3,2) (2,3) (3,3) (4,3), Life Grove (0,2) (1,2) (2,2), Vent C (0,1) (1,1), Tunnel C (3,3), Reactor Core (0,2), Elevator Beta
  (0,2); fragata 1 — Vent A (1,0). (Contar também os tipos A–D dá a mesma lista.)
- `check_pause_maps` (`tools/validate.py:298`) compara o tilemap da ROM com `pausemap.build` (não com a forma da sala).

## Mudança proposta

- `pausemap.solid_screens(room)`: telas em que os 256 blocos são tipo `$8`.
- `pausemap.room_tile(room, sx, sy, solid=None)`: tela maciça → `BLANK`; nas outras, parede em cada lado cujo vizinho está fora da
  caixa **ou é maciço**.
- `pausemap.build`: usa isso no tilemap; a **máscara de revelação continua a caixa inteira** (a lista do save e o lugar dela na
  SRAM não mudam; o tile `BLANK` revelado não mostra nada).
- Vale para todas as áreas (é a mesma função): na fragata muda só a Vent A.
- Validador: `check_map_shapes` (novo) lê o tilemap **da ROM** e confere cada tela de cada sala contra o nível da sala (maciça →
  vazia; as outras com parede exatamente nos lados de fora/maciços).

## Critérios de aceite

1. `check_map_shapes`: 0 problemas na ROM nova; na ROM de antes (mutação) acusa as salas com telas maciças.
2. Teste novo `mapa_com_a_forma_da_sala`: telas não maciças da Tallon Canyon e do Artifact Temple marcadas exploradas por RAM,
   pausa: cada uma mostra (VRAM) o tile com as paredes voltadas para a rocha. (falha_quando = mapa antigo: mutação)
3. Lista do save igual (log: área 0 = 47 bytes em +357, área 3 = 30 em +327); `tallon_mapa_salvo`, `map_station_e_mapa_de_pausa`,
   `continue_mostra_o_tallon` passam.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `check_map_shapes` | +1 |
| run_tests.py | `mapa_com_a_forma_da_sala` | +1 |
| imagem | mapa inteiro antes/depois; Canyon e Artifact Temple no teste | 3 |

## Riscos e reversão

Tile `BLANK` dentro da caixa de uma sala: o jogo só desenha telas exploradas e a Samus não entra em rocha; a map station da
fragata revela a Vent A (1,0) como vazia. Reversão: `tools/frigate/pausemap.py`, `tools/validate.py`, o teste.

## Fora de escopo

- Telas só parcialmente de rocha (continuam tela da sala).
- Ícones, nomes, minimapa do HUD (o minimapa lê o mesmo tilemap: herda a mudança).

## Desvios (preenchido na implementação)

Verificação (26/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas` (~3,9 s; linha do Tallon igual).
- `python3 -I tools/build.py` duas vezes → sha1 `2eb8a710b1166045f650265d47ff6c763a96bd9f` nas duas (antes, depois da 10b,
  `ed565db6…336c`); log "mapa na SRAM: área 0 = 47 bytes em +357", "área 3 = 30 bytes em +327" (iguais). Diferença da ROM: 72 bytes,
  todos nos tilemaps de pausa (`$B5:926A`–`$B5:B34D`).
- `python3 -I tests/run_tests.py` → **52/52** (os 51 + `mapa_com_a_forma_da_sala`).
- Mutações: `check_map_shapes` na ROM de antes → 40 problemas ("vent_a tela (1,0) é rocha maciça e o mapa a desenha ($4C25)",
  "tallon_canyon tela (2,1): paredes [], a forma da sala pede ['B', 'R']", …); o teste novo numa cópia com a ROM de antes e o
  `pausemap` novo → falha ("vram 3584 = 081B, esperado 8825").
- Fotos olhadas: `specs/img/10c-mapa-antes.png` e `10c-mapa-depois.png` (todas as telas não maciças exploradas por RAM: a Canyon e o
  Artifact Temple fechados com parede do lado da rocha; nas outras salas com rocha, idem), `10c-teste-canyon-e-templo.png` (a foto
  do teste, ampliada).

Mudanças de expectativa dos testes existentes: **nenhuma** (`tallon_pause_shows` já usava `pausemap.room_tile`: as telas de porta
que ele confere não mudam).
