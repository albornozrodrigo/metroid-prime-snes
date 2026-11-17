# 10d — Porta de onda roxa

Estado: verificada (26/10/2026: validate 72/148/0; .ips sha1 `3919c3c73d46afc45ffd4eb51083daebbe8264ff` igual em dois builds; 52/52 testes)
Esforço estimado: 1–1,5 dia
Épico: [10 — Polimento do Tallon](10-polimento-tallon.md) (achado A6)

## Contexto

As 7 portas de onda (as de condutor da fragata afundada, spec 09a) usam a tampa **cinza** do SM: cinza-rosada sobre o fundo
azul-acinzentado da fragata, mal se vê (`specs/img/10-auditoria-porta-de-onda.png`). Pedido: uma cor que se leia bem e não se
confunda com a de gelo (verde) nem com a de plasma (laranja). No Prime a porta da onda é **roxa**.

## Estado atual (verificado)

- `tools/tallon/beamdoors.py` (09a): onda = cópia da porta cinza vanilla (`$C842/$C848`: quadros `$A6A7…`, metatiles `$0AE/$0CE…`).
  As 7 portas de onda ficam em salas do tileset 4 (região D): Reactor Core R, Reactor Access L e R, Cargo Lift L ×2, Biohazard L,
  Biotech 1 L.
- Cor das tampas (ROM, tabela CRE `$B9:A09D` e tileset 4): a tampa verde/amarela usa os tiles `$300…` e as **cores 1–3 da linha** do
  metatile — verde = linha 1 (`$004/$024…`), laranja = mesmos tiles na linha 0; a cinza usa outros tiles (`$398–$39B`) só com as
  cores 4–7 da linha 1. Nas linhas do tileset 4 (com o recolor da fragata, linhas 4, 5, 7): 0 laranja, 1 verde, 2 rosa (míssil), 3
  azul (comum), 4/5 cinza-azulado, **6 = cinza de enchimento (`$6318`) em quase tudo** (`capsheet.png`).
- **Nenhum metatile do tileset 4 (CRE + SCE) usa a linha 6** (varredura das 1024 entradas); a Parasite Queen usa a 7
  (`queen_art.TILE_ATTRS`), as estrelas do hangar a 4 (`space.PALETTE_LINE`). No emulador, a linha 6 na RAM de paleta (`$7EC0C0`)
  numa sala da região D é `$6318` (lida no teste com a ROM de antes).
- Metatiles SCE `$3E0–$3FE` do tileset 4 = enchimento `$03FF ×4`; nenhuma sala vanilla de tileset 4/5 (28 estados) nem nossa os usa.
  Os tilesets 4 e 5 têm entradas próprias em `$8F:E7A7` (`$E6C6`, `$E6CF`), apontando para a mesma tabela `$C1:C5CF`.
- `$84` livre a partir de `$84:F2DD` (3363 bytes).

## Mudança proposta

1. **Cor**: roxo na linha 6 do tileset 4, cores 1–3 = `$7DB5`, `$64CE`, `$3847` (RGB 168,104,248 / 112,48,200 / 56,16,112, do claro
   ao escuro); as cores da moldura (4–7, 12, 15) copiadas da linha 1. Escolhido entre 4 roxos lado a lado com as tampas verde,
   laranja, rosa e azul (`specs/img/10d-cores-das-portas.png`): o 2º (mais azulado que o rosa do míssil, mais vermelho que o azul).
2. **Metatiles**: `$3F0–$3F7` do tileset 4 = cópias dos metatiles CRE da tampa verde (`$004 $024 $005 $025 $006 $026 $007 $027`) com
   a linha 6 no lugar da 1 (o tile `$338` da última moldura fica na linha 0, como no vanilla). O build escreve uma **cópia própria da
   tabela do tileset 4** no alocador fixo e aponta só a entrada do tileset 4 para ela (o 5 continua na vanilla); erro se os 8
   lugares não forem enchimento.
3. **Quadros e listas** (`beamdoors.py`): a onda passa a copiar a porta **verde** (não a cinza). Depois dos cabeçalhos (os ids de
   PLM não mudam), por lado: os 4 quadros da verde (fechada `$A827/$A857` e os 3 da abertura) com os metatiles trocados (12 bytes
   cada) e a lista de abertura (21 bytes: som, 4 quadros, apaga) apontando para eles; a lista de fechar copiada aponta para eles e a
   principal termina na abertura nova. `$84` passa de 462 para 600 bytes (até `$84:F366`).
4. **Paleta**: no passo de recolor do build, a paleta do tileset 4 ganha a linha 6 (`beamdoors.paint_palette`).
5. **Validador**: `fixed_blobs` confere a paleta do tileset 4 = recolor + linha 6 e a tabela de metatiles do tileset 4 = vanilla +
   os 8; `check_gates` já confere os bytes do `$84` contra `beamdoors.code`; novo `check_wave_paint_free`: nenhuma sala do
   tileset 4 usa `$3F0–$3F7` no nível.

## Critérios de aceite

1. `porta_de_onda` (09a) passa também: com a porta fechada, o bloco de cima da tampa no nível da WRAM é `$C3F0` (lado R; `$C7F0` no
   L) e as cores 1–3 da linha 6 na paleta da WRAM são as roxas. (falha_quando = ROM de antes: `$6318`)
2. Validador: 0 problemas; na ROM de antes acusa a paleta, a tabela e os bytes do `$84`; com um metatile usado por uma sala no lugar
   de `$3F0`, `check_wave_paint_free` acusa.
3. Fotos: a porta de onda roxa fechada, abrindo e aberta; a da cadeia (rodada 5).
4. Todos os testes antigos passam (as portas de gelo/plasma, a fragata com o tileset 4, a Parasite Queen).

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | paleta e tabela do tileset 4 (`fixed_blobs`), `check_wave_paint_free`; `$84` (`check_gates`) | +2 |
| run_tests.py | `porta_de_onda` com `wave_door_purple` (bloco no nível, cores na paleta) | 0 novos, +4 expects |
| imagem | cores lado a lado; porta fechada/abrindo/aberta; cadeia | 5 |

## Riscos e reversão

Algo que use a linha 6 do tileset 4 em tempo de jogo (nada encontrado: metatiles, Queen, estrelas; a fragata nas fotos dos testes
está igual). Reversão: `tools/tallon/beamdoors.py`, o passo de recolor em `tools/build.py`, `tools/validate.py`, o teste.

## Fora de escopo

- Mudar a cor das portas de gelo e plasma; a tampa cinza das portas de chefe da fragata (continua a vanilla).

## Desvios (preenchido na implementação)

Verificação (26/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas` (linha do Tallon igual); "alocador fixo: 6 blobs, 23991
  bytes" (era 5, 21321: a tabela do tileset 4 tem 2670 bytes comprimida).
- `python3 -I tools/build.py` duas vezes → sha1 `3919c3c73d46afc45ffd4eb51083daebbe8264ff` nas duas (antes, depois da 10c,
  `2eb8a710…bd9f`). Log: "portas de feixe: 600 bytes no $84 a partir de $84F10F" (ids de PLM iguais: onda R `$F2C5`, L `$F2CB`).
- `python3 -I tests/run_tests.py` → **52/52** (nenhum teste novo; `porta_de_onda` com 4 expects a mais).
- Mutações: na ROM de antes (com o código novo) `check_gates` → 4 problemas ("$84F2DD na ROM é $FF, beamdoors gera $04", …) e
  `fixed_blobs` → "paleta do tileset 4 … não é a recolorida com a linha da porta de onda", "metatiles do tileset 4 em $C1C5CF
  diferentes dos vanilla + os da porta de onda"; `porta_de_onda` numa cópia com a ROM de antes → falha (`7EC0C2… = 6318`, esperado
  as roxas); `PAINT_METATILES[$004] = $2F0` (usado pelo hangar) → `check_wave_paint_free`: "hangar: o nível usa os metatiles da porta
  de onda ['$2F0']".
- Fotos olhadas: `specs/img/10d-porta-de-onda-fechada.png` (+ `-zoom`: as duas tampas da Reactor Access roxas, nítidas no fundo),
  `10d-porta-de-onda-abrindo.png`, `10d-porta-de-onda-aberta.png`, `10d-cadeia-porta-de-onda.png` (rodada 5 da cadeia),
  `10d-cores-das-portas.png` (verde, laranja, rosa, azul e os 4 roxos testados). A fragata (Parasite Queen, save station, porta de
  chão) igual a antes.

Desvios:

- A onda passou a copiar a porta **verde** (tiles `$300…`, cores 1–3), não a cinza: a cinza não tem as cores 1–3, então não dava para
  pintá-la mudando só a linha.
- O metatile `$027` da verde tem um tile (`$338`) na linha 0; ele fica na linha 0 (como no vanilla da verde): só os tiles da linha 1
  passam para a 6.

Mudanças de expectativa dos testes existentes: `porta_de_onda` ganha a checagem da cor (4 expects); nenhuma expectativa antiga mudou.
