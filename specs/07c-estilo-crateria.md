# 07c — Estilo da Crateria

Estado: verificada (22/10/2026: validate igual, 28/60/0; .ips sha1 `e9b0db22…8555` igual; 21/21 testes)
Esforço estimado: 1 dia (pesquisa 3 h, spec 1 h, código 2 h, verificação 2 h)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (decisão 5 "Visual", linha 07c)

## Contexto

As salas do Tallon (07d/07g) vão ser desenhadas em ASCII como as da fragata, e um "estilo" troca
cada bloco de parede pelo pedaço certo do tileset (chão, parede, canto, teto). O único estilo que
existe é o da fragata (Wrecked Ship, tileset 4). Esta spec cria os estilos da Crateria para a
superfície e para as cavernas/túneis, com a chuva e a música da Landing Site, **sem construir
nenhuma sala do Tallon** (isso é da 07d/07g). A ROM da fragata sai igual.

## Estado atual (verificado)

Tudo lido de `base/sm_fix.sfc` com `tools/smlib/room_reader.py` (`read_room`, `read_level_data`),
percorrendo as 34 salas da área 0 de `research/sm_rooms.json` e todos os estados de cada uma.

### Tilesets da Crateria

- Tileset **0** (Crateria de cima): Landing Site `$91F8`, `$92FD`, `$93FE`, `$94FD`, `$957D`,
  `$948C`, `$9552`, `$9461`, `$95FF` … Rocha verde com borda de pedra azul, grama no chão.
- Tileset **2** (Crateria de baixo): dois visuais no mesmo tileset: metal (`$96BA`, `$99F9`,
  `$975C`) e **tijolos de pedra** (`$99BD`, `$9A44`, `$9879`, `$98E2`). A rocha orgânica roxa de
  `$990D`/`$9969` só existe em rampas (tipo 1) com recheio preto `$081`/`$3FF`: não serve para
  desenho em ASCII (sem rampas).
- Para cavernas/túneis do Tallon a escolha é o **tijolo de pedra do tileset 2**: é todo em blocos
  retos (cabe no ASCII), parece ruína Chozo (túneis de transporte do Prime) e cumpre a decisão 5
  do épico. A rocha de caverna do tileset 0 também existe (`$957D`), então uma caverna natural pode
  usar o estilo da superfície se a 07g preferir.

### Como as peças foram escolhidas

Para cada bloco sólido (tipo 8) das salas de origem, contei qual metatile (com os bits de
espelho) aparece para cada combinação de lados que tocam ar (N/L/S/O; e, com os 4 lados sólidos,
qual diagonal toca ar). A tabela usa a peça mais comum de cada caso. Bits: `H` = `$400`
(espelho horizontal), `V` = `$800` (vertical).

**Superfície — tileset 0** (salas `$91F8 $957D $92FD $948C $9552 $9461 $95FF`):

| Caso | Peça | Contagem no vanilla |
|------|------|---------------------|
| recheio (4 lados sólidos) | `$111`, `$111\|H`, `$111\|V`, `$111\|H\|V` | 4448 + 676 + 240 + 307 |
| chão (ar em cima) | `$10C $118 $10F $101` (e espelhos) | 49, 41, 41, 26 (+39 `$50C`, 19 `$501`) |
| teto (ar embaixo) | `$10F\|V $118\|V $10F\|H\|V` | 47, 19, 24 |
| parede, ar à esquerda | `$110` (`$110\|V`) | 176 (+20) |
| parede, ar à direita | `$110\|H` (`$110\|H\|V`) | 183 (+18) |
| canto de fora NO / NE | `$100` / `$100\|H` | 27 / 19 |
| canto de fora SO / SE | `$10D\|V` / `$10D\|H\|V` | 19 / 24 |
| canto de dentro NO/NE/SO/SE | `$114`, `$114\|H`, `$114\|V`, `$114\|H\|V` | 90, 96, 156, 148 |
| saliência fina (ar em cima e embaixo) | meio `$11B`/`$11B\|H`, pontas `$11A`/`$11A\|H` | 10+2, 12/13 |
| coluna de 1 bloco (ar dos 2 lados) | `$110` | 5 (caso raro; vanilla não tem peça própria) |
| grama (ar, em cima do chão) | `$12E $12F $130 $12D` | tipo 0 em 73, 115, 98, 51 blocos |

**Caverna — tileset 2** (salas `$99BD $9A44 $9879 $98E2`; plantas também de `$9969`):

| Caso | Peça | De onde |
|------|------|---------|
| recheio, paredes, cantos, coluna, saliência | `$2B6`/`$2B8` em xadrez pela paridade de x+y | `$99BD` linhas 62–68: `82B6 82B8…` alternando por linha (aparelho de tijolo); `...O` 38× `$2B6`, `.L..` 43× `$2B8`, `N.S.` 20+20 |
| chão | `$2AF`/`$2AD` pela paridade de x | `$9879` linha 13: `82AF 82AD …`; 33+33 |
| teto | `$2AF\|V`/`$2AD\|V` | `$9879` linha 2: `8AAF 8AAD …`; 44+44 |
| planta (ar, em cima do chão) | `$36F`, `$36D` | tipo 0 em `$99BD` (linhas 71–78), `$990D`, `$9969` |

No vanilla as paredes de tijolo não têm peça de borda: o próprio tijolo é a borda. Por isso, na
caverna, cantos, coluna e pontas de saliência continuam o xadrez (ou a fileira de chão/teto), em
vez de uma peça fixa que quebraria o aparelho.

### Chuva e música (Landing Site `$8F:91F8`)

Estados da sala (lidos): `E612`/`E669`/`E612` e o padrão `E5E6`. O **padrão**: tileset 0, música
**`$06/$05`** (song set / faixa), FX **`$83:80C0`**, BG2 scroll `$0181`, fundo `$8F:B76A`.

FX `$83:80C0` = `00 00 FF FF FF FF 00 00 00 0A 02 0E 00 01 00 22`: entrada padrão (palavra 0 =
`$0000`), **tipo `$0A` = chuva**, blend `$02`/`$0E`, bitset de FX de paleta `$01`, blend de
paleta `$22` (formato em `research/sm_room_format.md` §7). O FX de paleta é escolhido pela lista
da área (`$83:AC46`), então na área 0 ele é o da Crateria.

O fundo da Landing Site (`$B76A`) só tem comandos "se entrou pela porta X" (`0E`) e o BG2 dela não
vem do level: não serve para sala nova. Fundos simples da Crateria: `$8F:B8B4` (Parlor `$92FD`,
BG2 scroll `$C1C1`: descomprime `$BA:8437` e copia para o BG2). A escolha do fundo fica para a 07g.

### Paletas

O recolor da fragata é só do tileset 4 (`AreaDef.palette_rows` da fragata; `build.py` recolore
por tileset das áreas com `palette_rows`). Conferido na ROM construída: entradas da tabela de
tilesets (`$8F:E7A7`), paleta e gráficos descomprimidos dos tilesets 0 e 2 **iguais** aos da ROM
base (o 4 muda, o 5 fica igual).

## Mudança proposta

1. `tools/smlib/style.py`: nova classe `EdgeStyle` (a `Style` da fragata fica intocada). Recebe as
   peças de cada caso (tabela acima) e o `tileset`. `apply()` troca só blocos tipo 8 (portas e
   tampas ficam); com ar em cima e embaixo usa as peças de saliência; põe a grama/planta como ar
   (tipo 0) no bloco vazio em cima de um chão, 1 a cada `grass_every` (3) blocos, por posição
   (o resultado é sempre o mesmo). Peças únicas (cantos, coluna, pontas) podem ser `None`:
   canto de fora segue a fileira de chão/teto, as outras seguem o recheio.
2. `tools/smlib/crateria.py` (novo): `SURFACE` (tileset 0), `CAVE` (tileset 2),
   `SURFACE_TILESET = 0`, `CAVE_TILESET = 2`, `RAIN_FX = 0x80C0`, `LANDING_SITE_MUSIC = (0x06,
   0x05)`, `SOURCE_ROOMS` e `check(rom)` (ver critérios).
3. Ligação nas salas: `RoomDef` ganha `fx: int = 0x0000`; `style` aceita `Style | EdgeStyle`.
   `build.state_bytes` usa `room.fx` quando não recebe `fx` (fragata: 0, igual a hoje). Uma sala do
   Tallon fica assim (07g):
   `RoomDef(..., style=crateria.SURFACE, fx=crateria.RAIN_FX)` com a `AreaDef` do Tallon em
   `tileset=crateria.SURFACE_TILESET, music=crateria.LANDING_SITE_MUSIC`; caverna:
   `style=crateria.CAVE, tileset=crateria.CAVE_TILESET`. O `Palette()` padrão serve (todo `#` e
   `=` é trocado pelo estilo).
4. `tools/validate.py`: chama `crateria.check()` (silencioso quando passa: saída igual) e acusa
   sala cujo `EdgeStyle` é de outro tileset que o da sala.
5. `tools/preview_rooms.py --estilos`: além das salas de cada área (como hoje), desenha uma sala de
   teste sintética 3×2 por estilo (chão, degraus, buraco, teto com saliência, coluna de 1 bloco,
   saliência fina, plataformas `=`, portas) em `specs/img/07c-<estilo>.png` (com contorno do tipo
   de bloco) e `07c-<estilo>-limpo.png` (como no jogo).

## Critérios de aceite

1. `python3 -I tools/build.py` → `.ips` sha1 `e9b0db220a7f5d7540b02b2ccbbd6e3889e28555` (nenhuma
   sala do Tallon é construída). Checagem: `shasum`.
2. `python3 -I tools/validate.py` → saída igual à de antes ("28 salas, 60 portas, 0 problemas").
   Checagem: `diff`.
3. `python3 -I tests/run_tests.py` → 21/21.
4. `crateria.check(rom)` (rodado pelo validate): cada peça está na tabela do tileset dela, aparece
   nas salas de origem e o tipo de bloco mais comum dela no vanilla é o que o estilo usa (sólido 8
   para as peças de parede; ar 0 para grama/planta); tileset/FX/música da Landing Site vanilla
   iguais às constantes; `$83:80C0` é entrada padrão do tipo `$0A`. Protege: peça trocada por uma
   de ar, de outro tileset ou inexistente; falha_quando: (conferido à mão) grama `$12E` como chão
   → "tipo 0 no vanilla"; chão `$10C` como grama → "tipo 8"; `$111` na caverna → "não aparece";
   `RAIN_FX = $80D0` → 2 problemas. Não prova: que a peça fica bonita (isso é o critério 5).
5. Imagens `specs/img/07c-superficie(-limpo).png` e `07c-caverna(-limpo).png`: bordas e cantos
   certos, sem peça trocada (conferido olhando, também ampliado).
6. Tilesets 0 e 2 da ROM construída iguais aos da base (entrada, paleta, gráficos). Checagem:
   script de comparação (resultado na seção Estado atual).
7. (Experimento, cópia descartável) uma sala da fragata com `SURFACE` + `RAIN_FX` no emulador:
   `$196E` (tipo de FX) = `$000A`, música `$07F3/$07F5` = `0006/0005`; imagem
   `specs/img/07c-emulador-superficie-chuva.png`.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `crateria.check` (peças × tileset × colisão, FX, música); estilo × tileset da sala | +2 |
| run_tests.py (emulador) | nenhum novo (não há sala do Tallon) | 0 |
| imagem | 2 salas sintéticas (com e sem contorno) + 1 foto do emulador (experimento) | +5 |
| build | sha1 igual | 1 |

## Riscos e reversão

- A grama/planta ocupa o bloco de ar em cima do chão (continua tipo 0, sem mudar colisão).
  `decor` e `overlay` de `Level` são desenhados depois e cobrem a grama; `backdrop` só pinta bloco
  de ar puro (`$00FF`), então pula esse bloco. Se atrapalhar, a sala usa `grass_every=0`
  (`dataclasses.replace`).
- Rampas não existem no ASCII: o visual fica mais "quadrado" que a Crateria vanilla.
- Reversão: apagar `smlib/crateria.py`, a classe `EdgeStyle`, `RoomDef.fx` e as linhas do
  validate/preview; nada da ROM muda.

## Fora de escopo

- Salas do Tallon, `AreaDef` do Tallon, mapa de pausa da área 0 (07d/07f/07g).
- Fundo (BG2) das salas do Tallon e rampas.
- Recolorir os tilesets 0/2 (o épico pede para não recolorir: é global por tileset).
- Água da fragata afundada (07l).

## Desvios (preenchido na implementação)

- Caverna: o tijolo do tileset 2 não tem peças de borda/canto no vanilla; o estilo usa o próprio
  tijolo nesses casos (campos `None`), em vez de peças inventadas.
- `preview_rooms.py` já desenhava por área desde a 07a; aqui ganhou só `--estilos`.
- Experimento no emulador (cópia em `scratchpad/07c/proj`, descartada): Air Lock da fragata
  com `SURFACE`, tileset 0, `RAIN_FX`, música `$06/$05`, fundo `$B8B4` e BG2 `$C1C1`. Entrou pela
  porta do hangar: `$196E = $000A`, `$07F3 = $0006`, `$07F5 = $0005`; entre dois quadros (37
  quadros de distância) 576 pixels do fundo vazio mudam (gotas de chuva caindo). Bordas iguais à
  prévia. A sala estava na área 3, então o FX de paleta foi o da lista da área 3; na área 0 será o
  da Crateria (não testado: não há sala da área 0 ainda).
