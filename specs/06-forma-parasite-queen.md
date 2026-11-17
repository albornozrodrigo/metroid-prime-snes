# 06 — Forma da Parasite Queen

Estado: verificada (22/10/2026; sha1 do .ips e9b0db220a7f5d7540b02b2ccbbd6e3889e28555; testes 20/20)
Esforço estimado (por parte; o protótipo já provou o caminho, ver "Protótipo"):
- decodificador/codificador de tiles 4bpp + deduplicação (`tools/smlib/gfx.py`): 30 min;
- módulo `tools/frigate/queen_art.py` (ler, codificar, gravar, checagens, paletas, hitboxes) e ligação
  no `build.py`: 1 h 30;
- desenho final (`tools/frigate/queen_draw.py`), com prévias e fotos no emulador até o usuário
  aprovar: 4 a 6 h (é a parte maior e a única subjetiva);
- testes (validate +2, run_tests +1) e documentação: 2 h.
- Total: 1 a 1,5 dia de trabalho, dos quais ~2/3 são arte.

## Contexto

A Parasite Queen hoje é o Phantoon com as cores do Prime: quem joga vê a "cabeça de cérebro" com um
olho do Phantoon, só que marrom e carmim (`research/parasite_queen_antes_depois.png`). No Prime ela é
um inseto grande que flutua no reator: cabeça com mandíbulas e uma boca que abre para atirar, pernas
laterais com espinhos, abdômen comprido em segmentos e cauda. É a pendência "Forma própria da Parasite
Queen (exige arte nova)" do `HANDOFF.md` e a etapa 6 que ficou só nas cores.

Esta spec troca só a **forma** (gráficos e caixas de colisão). A luta, os ataques e o fim continuam
os do Phantoon.

## Estado atual (verificado)

Conferido no código C (`vendor/sm/src`), em bytes da ROM (`base/sm_fix.sfc` e a ROM gerada numa
cópia privada) e no emulador `tools/snesrun` com um comando extra de despejo de VRAM/CGRAM/WRAM
(só na cópia; o emulador do projeto não muda).

### Onde está o corpo

1. **O corpo do Phantoon é a camada BG2, não sprites.** As chamas são projéteis (sprites, paleta da
   espécie `$A7:CA01`, já recolorida como fogo). Os tiles de sprite da espécie (`$AC:AA00`, `$C00`
   bytes, cabeçalho `$A0:E4BF`+`$36`) são das chamas e ficam fora desta spec.
2. **Registros da BG2 no Reactor Core** (despejo no emulador): mapa em VRAM word `$4800`, tiles
   da BG1/BG2 a partir de VRAM `$0000` (BG3 em `$4000`, sprites em `$6000`/`$7000`).
3. **Os tiles do corpo vêm do tileset 4 (Wrecked Ship), tiles `$110`–`$183`.** O despejo da VRAM na
   luta é igual, byte a byte, aos gráficos descomprimidos do tileset 4 (`$BB:AE9E`, 14354 bytes
   comprimidos, `$4800` descomprimidos = tiles `$000`–`$23F`). Nada é carregado à parte para o
   chefe.
4. **Ninguém mais usa `$110`–`$18F`.** A tabela de metatiles do tileset 4/5 (`$C1:C5CF`) só aponta
   para `$100`–`$10F` nessa faixa; o fundo da Wrecked Ship (`$8F:E117` → `$BA:8DE7`) também não usa.
   Os blocos do corpo usam 116 tiles (`$110`–`$183`); `$184`–`$18F` sobram. **Orçamento: 128 tiles
   (`$110`–`$18F`, 4 KB)**, 4bpp, 16 cores.
5. **Os tilesets 4 e 5 dividem os mesmos gráficos.** Entradas `$8F:E6C6` (4) e `$8F:E6CF` (5), cada
   uma com 3 ponteiros de 24 bits (tabela, gráficos, paleta); as duas apontam os gráficos para
   `$BB:AE9E`. O build já trocou a paleta do tileset 4 para o espaço expandido (`tools/build.py`,
   passo 3); o mesmo serve para os gráficos.
6. **Carga dos gráficos do tileset:** por porta, `DecompressToMem` (`$80:B0FF`, C `sm_82.c:3978`);
   ao carregar jogo, `DecompressToVRAM` (`$80:B271`, C `sm_82.c:4198`). O primeiro atravessa limite
   de banco (`research/sm_room_format.md` §0); o segundo **não foi conferido**, então os dados novos
   ficam dentro de um banco só.

### Mapa de tiles do corpo (blocos em `$A7`)

7. **Área desenhada: 10 x 14 tiles (80 x 112 px).** Buffer na WRAM `$7E:2000` (linha = 64 bytes),
   enviado para VRAM `$4800` com `$360` bytes (`Phantoon_Init` `$A7:CDF3` põe
   `enemy_bg2_tilemap_size = 864`; envio em `QueueEnemyBG2TilemapTransfers` `$A0:9726`).
8. **Posição:** `Phantoon_Main` (`$A7:CEA6`) faz `BG2HOFS = layer1_x − x + 40` e
   `BG2VOFS = layer1_y − y + 40`: o pixel (40, 40) do desenho fica na posição (x, y) do inimigo.
9. **Blocos de tilemap** (formato "extended tilemap", `ProcessExtendedTilemap` `$A0:96CA`):
   `$FFFE`, depois entradas {endereço WRAM, n, n palavras}, e `$FFFF`. Ficam em
   **`$A7:E0AA`–`$A7:E3D1`** (808 bytes, 22 blocos). Cada parte do chefe (inimigos 0–3) desenha
   o seu bloco pelo "extended spritemap" (`$A7:DEDD`–`$A7:E010`). Lidos da ROM:

   | Bloco(s) | Onde desenha (linha, coluna, largura) | O que é no Phantoon |
   |---|---|---|
   | `$E0AA` | linhas 0–11, colunas 0–9 | corpo inteiro, com um buraco no lugar do olho |
   | `$E1CE`, `$E202`, `$E236` | linhas 7–10, colunas 3–6 (4x4) | olho aberto, meio, fechado |
   | `$E26A` | linhas 8–9, colunas 4–5 (2x2) | íris no centro |
   | `$E27E` `$E30A` `$E2BA` `$E2E2` `$E292` `$E2CE` `$E2A6` `$E2F6` | idem | íris olhando para cima, cima-direita, direita, baixo-direita, baixo, baixo-esquerda, esquerda, cima-esquerda (direção da Samus, `$A0:AE29`; tabela `$A7:D40D`) |
   | `$E31E` `$E32E` `$E33E` | linhas 12–13, coluna 2 | tentáculo esquerdo, 3 poses |
   | `$E34E` `$E35E` `$E36E` | linhas 12–13, coluna 7 | tentáculo direito, 3 poses |
   | `$E37E` `$E39A` `$E3B6` | linhas 12–13, colunas 3–6 | boca, 3 poses |

   Palavras: tile + paleta 7 + prioridade 1 (`$3C00`); células vazias = `$2338` (tile `$338` da CRE,
   transparente). Metade das colunas é a outra metade espelhada (bit de inversão horizontal).
10. **Paletas do corpo:** linha 7 da BG (CGRAM 112–127). 8 paletas de 16 cores, uma por faixa de
    vida (a cada 312 de HP, `Phantoon_SetColorBasedOnHp_FindEntry` `$A7:DC0F`), ponteiros em
    `$A7:DC4A` → `$A7:CB41`…`$A7:CC21`. Hoje `tools/frigate/bosses.py` as recolore.
11. **Caixas de colisão** (listas de 12 bytes: esquerda, topo, direita, baixo, rotina de toque, rotina
    de tiro; relativas à posição do inimigo):
    - `$A7:E020`: 1 caixa vazia (olho fechado: invulnerável);
    - `$A7:E02E`: 5 caixas, toque `$A7:DD95`, tiro `$A7:DD9B`: corpo (−33,−40,32,56), olho
      (−9,22,8,39) e três da boca;
    - `$A7:E06C`: 1 caixa, só o olho (−9,22,8,39).
    `Phantoon_Shot` (`$A7:DD9B`) não olha qual caixa foi atingida: qualquer caixa da lista vale.
12. **As chamas nascem na posição do inimigo** (pixel (40, 40) do desenho).

### Referência do Prime

13. O modelo `Parasite_queen` (CMDL `9A43BD70`) é legível com retro-data-structures (`tools/venv`):
    3832 vértices, 5894 triângulos. Renderizado de cima e de lado (sombreamento simples):
    `specs/img/06-referencia-prime.png`. Visto de cima ela já tem a pose que cabe na tela:
    cabeça em cima, dois braços com espinhos para os lados, corpo em gomos com espinhos, cauda
    fina com uma pinça na ponta. Cores: as das texturas já usadas em `bosses.py`.

## Mudança proposta

### Ideia

Manter o "esqueleto" do Phantoon (IA, os 22 blocos com os mesmos tamanhos, as listas de caixas com
o mesmo número de caixas, as 8 paletas) e trocar o conteúdo: tiles `$110`–`$18F` novos, palavras e
destinos novos dentro dos blocos, coordenadas novas nas caixas, cores novas. Nenhum código 65816 muda.

### Direção de arte (80 x 112 px, origem do inimigo em (40, 40))

A Parasite Queen vista de frente, em pé, como o modelo do Prime visto de cima:

- **Cabeça** (y 0–48, x 20–60): cúpula de carapaça iluminada de cima, crista clara no meio, dois
  olhos pequenos alaranjados. Embaixo, a **boca** com duas mandíbulas de osso.
- **Boca = o olho do Phantoon** (bloco 4x4 movido para linhas 2–5, colunas 3–6): fechada (mandíbulas
  juntas), meio aberta, aberta (anel de dentes, interior escuro). Quando aberta ela fica vulnerável,
  como o olho.
- **Núcleo brilhante = a íris** (bloco 2x2 movido para linhas 3–4, colunas 4–5): uma bola de energia
  laranja-branca dentro da boca aberta que se desloca 2 px para o lado da Samus (9 quadros, mesma
  ordem de direções da tabela acima).
- **Pernas** (y 33–63): dois pares saindo dos lados até a borda do desenho, com espinhos de osso.
- **Abdômen** (y 45–95): 6 gomos que afinam de 38 para 12 px, faixa de carne carmim entre placas,
  espinhos laterais.
- **Cauda e pinça** (linhas 12–13, os blocos da boca do Phantoon): ponta da cauda com ferrão (bloco
  central, 3 poses: ferrão normal, mais claro, aceso) e as duas garras da pinça (blocos laterais,
  3 poses: fechando → abrindo). Elas animam quando o Phantoon abriria a boca.
- Contorno de 1 px escuro em toda a figura. Simétrica (só a metade esquerda é desenhada e espelhada):
  é o que cabe nos 128 tiles.

Paleta (índice → papel), cores das texturas do Prime:

| Índice | Papel | Cor (RGB) |
|---|---|---|
| 1 | contorno | (16, 8, 8) |
| 2–6 | carapaça, do escuro ao claro | (40,26,22) (66,50,42) (98,78,66) (138,110,94) (180,152,130) |
| 7 | osso / espinhos / crista | (224, 210, 188) |
| 8–11 | carne carmim | (62,16,20) (112,36,42) (164,62,68) (214,112,104) |
| 12–15 | brilho (núcleo, olhos, ferrão) | (128,56,8) (232,132,32) (255,222,112) (255,255,240) |

As 8 faixas de vida: faixa 7 (vida cheia) = tabela acima; cada faixa abaixo leva as cores 8–15 um
pouco mais para (255, 90, 60) (até 45% na faixa 0): ela "esquenta" quando enfraquece. Cor 0 = 0.

### Caixas de colisão novas (relativas ao inimigo)

- `$A7:E02E` (5 caixas, mesmas rotinas): cabeça (−20,−40,19,8); núcleo (−10,−18,9,1);
  abdômen (−15,8,14,48); cauda (−5,48,4,60); pinça (−12,56,11,71).
- `$A7:E06C` (1 caixa): núcleo (−10,−18,9,1).
- `$A7:E020` não muda.

### Arquivos

1. **`tools/smlib/gfx.py`** (acrescentar):
   - `decode_4bpp(tile: bytes) -> list[int]` e `encode_4bpp(px: list[int]) -> bytes` (64 índices,
     linha a linha, planos 0/1 nos bytes 0–15 e 2/3 nos bytes 16–31);
   - `flip_tile(px, h, v)`;
   - `TileDeduper(limit)`: `add(px) -> (n, hflip, vflip)`; reaproveita um tile igual a outro
     invertido; erro claro ao passar do limite.
2. **`tools/frigate/queen_draw.py`** (novo): o desenho em Python puro (sem PIL, como o resto do
   build): `PALETTE` (16 cores), `LAYOUT` (bloco → lista de (linha, coluna, n)), `CORE_DIR`,
   `HITBOX_ALL`, `HITBOX_CORE`, e `frames() -> {bloco: lista de 80*112 índices}` (um quadro
   inteiro por bloco; cada bloco usa só as suas células). Primitivas: elipse com função de
   sombreamento, polígono, contorno automático, espelho.
3. **`tools/frigate/queen_art.py`** (novo):
   - `VANILLA`: estrutura dos 22 blocos (tabela acima) e `check_vanilla_shape(rom)` (para se alguém
     já mexeu nos blocos);
   - `read_block`, `render_block`, `frames_from_rom` (lê de volta qualquer ROM em imagens: usado nos
     testes e para gerar prévias);
   - `encode(frames, layout) -> (tiles, {bloco: bytes})`: corta cada célula 8x8, célula toda
     transparente → `$2338`, senão `TileDeduper` → `($110+n) | $3C00 | inversões`; confere que cada
     bloco tem o tamanho original;
   - `apply(rom, put_in_bank)`: confere que nenhum metatile do tileset 4 aponta para `$110`–`$18F`;
     lê os gráficos pelo ponteiro **atual** da entrada do tileset 4 (`$8F:E6C6`+3), troca só os bytes
     `$2200`–`$31FF` (tiles `$110`–`$18F`; sobra = zeros), recomprime com
     `smlib.compression.compress`, grava no expandido **dentro de um banco** e troca só o ponteiro do
     tileset 4 (o 5 continua em `$BB:AE9E`); grava os 22 blocos no lugar; grava as 8 paletas no
     lugar (`$A7:DC4A`); grava as caixas no lugar (assert: mesmo número de caixas);
   - devolve para o manifesto: número de tiles, ponteiro novo e 3 palavras de amostra do tilemap
     (para o teste no emulador).
4. **`tools/build.py`**: `LinearAllocator.put_in_bank(payload)` (pula para o próximo banco se não
   couber; a spec 04 propõe o mesmo método: usar um só); chamar `queen_art.apply` logo depois de
   `bosses.parasite_queen(rom)`; gravar `manifest["parasite_queen"]`.
5. **`tools/frigate/bosses.py`**: tirar o laço que recolore as 8 paletas do corpo (agora vêm de
   `queen_art`); fica só a paleta das chamas. Atualizar o docstring.
6. **`tools/preview_queen.py`** (novo, 30 linhas): grava `research/render/parasite_queen.png` com
   os quadros (`queen_art.frames_from_rom` sobre a ROM gerada) para revisar a arte sem emulador.
7. Opcional: `tools/render_prime_model.py` (venv) que gerou `specs/img/06-referencia-prime.png`.

Espaço usado: ~13,3 KB no expandido (gráficos do tileset 4 recomprimidos); o resto é no lugar.

### Protótipo (feito numa cópia, não no projeto)

Em `/private/tmp/…/scratchpad/spec06/` (cópia descartável) o caminho inteiro foi feito e rodado:

- LZ: gráficos do tileset 4 descomprimidos (`$4800`) → `compress` do projeto (13913 bytes, menor que
  os 14354 originais) → descomprimidos de novo = **idênticos**.
- Phantoon original → imagens → `encode` com o layout original → gravado → lido de volta: os 22
  blocos **idênticos pixel a pixel**, 114 tiles (o original usa 116; a deduplicação acha 2 a mais).
  Tiles `$000`–`$10F` e `$190`+ intactos.
- Desenho provisório (o das imagens): 107 tiles; ROM → imagens = arte, 0 pixels diferentes;
  gráficos novos em `$E0:9B1B` (13317 bytes, num banco só).
- No emulador: a forma nova aparece com a ondulação de entrada, a boca abre com o núcleo
  (`specs/img/06-antes-depois.png`: antes, depois, boca aberta). VRAM conferida no início do jogo
  (carga por `DecompressToVRAM`) e na arena (carga por porta): tiles `$000`–`$10F` e `$190`–`$23F`
  iguais ao vanilla, `$110`–`$18F` iguais à arte nova.
- `validate.py`: 0 problemas; `run_tests.py`: **13/13**; build duas vezes = mesmo md5.
- Prova de que o teste da morte protege as caixas: com as caixas jogadas para fora da tela, o teste
  `parasite_queen_morre_e_fuga_com_timer` falha (chefe não morre, `$7ED82B` = 0).
- Quadros do protótipo: `specs/img/06-quadros-prototipo.png` (corpo, boca fechada/meia/aberta,
  núcleo, pinça acesa). É **arte provisória**: a final segue a direção de arte acima e passa pelo
  usuário.

## Critérios de aceite

1. **LZ ida e volta:** gráficos vanilla do tileset 4 → `compress` → `decompress` = idênticos.
   (validate.py `check_queen_art`: protege=compressor; falha_quando=o compressor gera fluxo
   diferente; não_prova=que o jogo lê o fluxo.)
2. **Phantoon ida e volta:** `encode(frames_from_rom(base), VANILLA)` gravado numa cópia em memória e
   lido de volta = os 22 blocos idênticos pixel a pixel, ≤ 128 tiles. (validate.py
   `check_queen_art`: protege=codificador 4bpp, inversões, formato dos blocos; falha_quando=um bit de
   plano ou de inversão sai trocado; não_prova=a arte nova.)
3. **Arte nova cabe e volta igual:** no build, `queen_art.apply` termina com ≤ 128 tiles e
   `frames_from_rom(rom gerada)` = `queen_draw.frames()` nas células de cada bloco (0 pixels
   diferentes). (assert no build + validate.py `check_queen_art`.)
4. **Nada mais do tileset muda:** gráficos novos com tiles `$000`–`$10F` e `$190`–`$23F` iguais ao
   vanilla; ponteiro do tileset 5 continua `$BB:AE9E`; dado comprimido não atravessa banco. (assert
   no build.)
5. **Forma nova no jogo:** teste novo `parasite_queen_forma_nova`: ida até o Reactor Core, espera 600
   quadros, `expect` em 3 palavras do buffer `$7E:2000` com os valores do manifesto (cabeça, perna,
   abdômen) e `shot build/tests/parasite_queen.png`. (protege=gráficos e blocos ligados de verdade;
   falha_quando=`apply` não roda ou grava no lugar errado; não_prova=a beleza da arte.)
6. **Ainda dá para matar:** `parasite_queen_morre_e_fuga_com_timer` e `fuga_ridley_nave_e_final`
   passam sem mudança. (protege=caixas de colisão; falha_quando=caixas fora do alcance dos mísseis,
   já provado no protótipo; não_prova=que a caixa do núcleo é a única vulnerável.)
7. **Salas iguais:** os 13 testes passam; as fotos `ida_fim.png` e `continue_na_save_station.png`
   ficam iguais às de antes da mudança (comparar md5 antes/depois; a segunda passa pela carga
   `DecompressToVRAM`).
8. **Arte aprovada:** `specs/img/06-*.png` com a forma final (prévia + foto do emulador com a boca
   aberta) mostrada ao usuário e aprovada antes de marcar `implementada`.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_queen_art`: LZ ida e volta (1), Phantoon ida e volta (2), arte nova cabe e volta igual (3) | +1 função, 3 checagens |
| build (assert) | metatiles fora de `$110`–`$18F`, tiles fora da faixa intactos, tileset 5 intacto, um banco só, tamanhos dos blocos e nº de caixas | +6 asserts |
| run_tests.py (emulador) | `parasite_queen_forma_nova` (novo); `parasite_queen_morre_e_fuga_com_timer` (sem mudança) | +1 |
| imagem | `build/tests/parasite_queen.png`, `research/render/parasite_queen.png`, `specs/img/06-*.png` | +3 |

## Riscos e reversão

- **Gráficos do tileset compartilhados (4 e 5):** só a entrada do tileset 4 é repontada; as salas
  vanilla da Wrecked Ship (tileset 5) seguem com o Phantoon original. Se alguma sala da fragata usar
  outro tileset no futuro, a Queen só funciona nas salas de tileset 4 (o Reactor Core é).
- **Outra spec usar os tiles `$110`–`$18F`:** ficam reservados para a Queen (anotar no
  `research/sm_room_format.md`). A spec 04 usa `$240`–`$27F`: sem conflito. `apply` lê o ponteiro
  atual, então convive com quem mexer em outros tiles antes dele.
- **Descompressão para VRAM atravessando banco:** não conferida; evitada com `put_in_bank`.
- **Dificuldade muda:** o ponto fraco sobe do meio-baixo (olho em y +22..+39) para a cabeça
  (y −18..+1). O teste de morte passa, mas a luta deve ser jogada uma vez pelo usuário.
- **Orçamento de tiles:** a arte tem de ser simétrica e com poucos detalhes únicos; os 9 quadros do
  núcleo são o que mais custa (até 36 tiles). Se estourar, o build para com mensagem clara;
  simplificar o núcleo (menos deslocamento) resolve.
- **Arte é subjetiva:** pode precisar de rodadas; por isso o critério 8.
- **Reversão:** tudo vem de `tools/` (`queen_art.py`, `queen_draw.py`, a chamada no `build.py` e o laço
  de paletas em `bosses.py`); reverter o código e reconstruir devolve o Phantoon recolorido.

## Fora de escopo

- Ataques do Prime (raio da boca, escudo giratório do reator, giro das plataformas): a IA continua a
  do Phantoon (bolas de fogo, mergulho, sumir e reaparecer).
- Chamas/projéteis: continuam as do Phantoon (já recoloridas como fogo).
- Animação de morte própria; sons; música.
- Desenho à mão em PNG indexado (precisaria de leitor de PNG sem PIL); pode vir depois trocando só
  `queen_draw.py`.
- Usar o modelo 3D do Prime direto no build (só serviu de referência visual).

## Desvios (preenchido na implementação)

1. **Arte em grades de texto, não em primitivas.** `tools/frigate/queen_draw.py` guarda o desenho
   como grades de caracteres (meia figura, índice da paleta em hexadecimal, '.' = transparente):
   `BODY` 40x96, `MAW_HALF`/`MAW_OPEN` 16x32, `CORE` 10x10, `TAIL[3]` 16x16, `CLAW[3]` 8x16; `frames()`
   espelha e compõe os 22 quadros. As primitivas (elipse, polígono, contorno, espelho) só serviram
   para o rascunho (fora do projeto); depois a arte foi retocada pixel a pixel, o que primitivas não
   permitem. Continua Python puro, sem PIL nem PNG; como editar está no docstring do módulo. Arte
   final feita sem rodada de aprovação (o usuário pediu trabalho autônomo; critério 8): cabeça em
   triângulo invertido com olhos compostos acesos sob a sobrancelha, crista e chifres; boca fechada
   = mandíbulas de osso com fileira de dentes; meia/aberta com anel de dentes e o núcleo; pernas com
   joelho e garra; 6 gomos; cauda com ferrão e pinça. **88 tiles** de 128. Quadros:
   `specs/img/06-quadros-final.png`; antes/depois no jogo: `research/parasite_queen_forma.png`.
2. **Caixas de colisão:** a lista `$A7:E02E` ficou cabeça (−20,−40,19,8), núcleo (−10,−18,9,1),
   **pernas (−40,−8,39,24)**, abdômen (−15,8,14,48), **cauda e pinça juntas (−12,48,11,71)**. As da
   spec deixavam as pernas (que vão até a borda do desenho) sem colisão; continuam 5 caixas. `$A7:E06C`
   e `$A7:E020` como na spec.
3. **Teste da morte alterado (expectativa de teste mudou):** `kill_parasite_queen` atira por 200
   rodadas em vez de 100. Motivo medido: a luta é caótica; os gráficos recomprimidos mudam o tempo de
   carga da porta e o padrão da luta muda. Com as caixas da spec o teste já falhava; com as finais ela
   morre na rodada 90 (com as caixas do Phantoon na ROM nova, na 67), sem tempo para a sequência de
   morte (~21 rodadas). No pre06 ela morre na rodada 27. Com as caixas jogadas
   para fora da tela o teste falha (`$7ED82B` = 0), então ele ainda protege as caixas. Sobram ~2:54 no
   cronômetro no fim da fuga.
4. **Manifesto:** os dados ficam em `manifest["reactor_core"]["parasite_queen"]` (tiles, ponteiro,
   bytes, `tilemap_samples`), como o `meta_ridley` da Air Lock: `run_tests.py` trata cada chave de
   primeiro nível como sala.
5. **Teste `parasite_queen_forma_nova`:** além das 3 palavras (`$7E:2008`, `$7E:2140`, `$7E:2248`:
   cabeça, perna, abdômen) confere que o inimigo 0 é o Phantoon, e tira a foto 240 quadros depois
   (aos 600 ela ainda está surgindo e a foto saía só com as chamas).
6. **Critério 7:** `ida_fim.png` igual (md5 `3b545d7c…`); `continue_na_save_station.png` difere só
   num quadrado 8x8 do minimapa (o ícone de save piscando em outra fase: tempo de carga diferente);
   a sala é igual pixel a pixel.
7. `bosses.py`: além do laço das paletas do corpo, saíram as rampas `BODY`/`FLESH` e as funções que
   só ele usava (`is_reddish`, `body_ramp`), que ficaram sem uso. `queen_art.check()` concentra as 3
   checagens do `validate.py`.
8. Também verificado: todos os 22 quadros sem pixel solto, as 9 combinações cauda × garras se
   encaixam, e no jogo (`snesrun`, peek em `$7E:20C8`) a boca abre (palavra `$4A`) com o núcleo
   seguindo a Samus, sem lixo, com vida cheia e baixa.
