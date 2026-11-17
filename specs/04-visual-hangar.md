# 04 — Hangar com cara de hangar

Estado: verificada (22/10/2026; sha1 be42c9446b4280f35625c37c2e5a142cc35d4927; testes 17/17)
Esforço estimado: céu estrelado 1–2 h; parede do fundo + garras + plataforma de pouso 1–2 h;
testes novos e ajuste visual 1–2 h. Total: meio dia (o protótipo abaixo já funciona).

## Contexto
O jogo começa no Exterior Docking Hangar (Prime P0), onde a nave da Samus está estacionada. No
Prime é uma baía aberta para o espaço, do lado de fora da fragata. Hoje o fundo da sala é o mesmo
fundo de parede do Wrecked Ship de todas as outras salas (canos e faixa de tijolo rosado,
`specs/img/04-antes-inicio.png`, `04-antes-nave.png`): parece uma sala interna qualquer.

Dados do Prime (`research/frigate_objects.json`, índice 0): 14 `Platform`, 1 `Dock`, 3 `Door`,
42 `Effect`, 2 `VisorFlare` (luzes). Os nomes dos objetos não puderam ser lidos; não há mais
detalhe útil ali.

## Estado atual (verificado)
- Todas as salas da fragata usam o mesmo estado: camada 2 `layer2 = $C1C1` (fundo vem da
  biblioteca, paralaxe 0,75) e fundo de biblioteca `$8F:E117` (`tools/build.py:39-40`,
  `state_bytes`, `tools/build.py:129`). O hangar é montado no laço `tools/build.py:344-382`
  (estado simples `header + E6E5 + normal`).
- `$8F:E117` (lido na ROM): `0004 $BA:8DE7 → $7E:4000` (descomprime o mapa),
  `0002 $7E:4000 → VRAM $4800, $800 bytes` e `0002 $7E:4000 → VRAM $4C00, $800 bytes`, `0000`.
  Ou seja: só o mapa de tiles da BG2 (64x32) muda; os tiles vêm do tileset.
- Tileset 4 (Wrecked Ship): gráficos `$BB:AE9E` descomprimem para **$4800 bytes = tiles
  $000–$23F**. CRE começa no tile $280 (`research/sm_room_format.md` §8). Logo os tiles
  **$240–$27F (VRAM palavra $2400–$27FF, 64 tiles)** não são usados por nenhuma sala da fragata.
  Conferido no emulador (comando `dumpvram` acrescentado só na cópia do `snesrun`): nessa faixa há
  lixo da tela de título e a pausa escreve nela sem restaurar; nenhum mapa de tiles aponta para ela.
- Cor 0 da CGRAM (fundo atrás de tudo) = preto ($0000). Linha de paleta 4 do BG (já recolorida
  pela fragata): cores 1/2/3 = cinzas, 13 = azul claro (144,184,248), 14 = branco.
- Metatiles escuros de "parede de fundo" do Wrecked Ship ($2D0/$2D1 faixa com luzes azuis,
  $2EF/$2F0 painel escuro, $2DB trilho vertical) **não têm o bit de prioridade** nos tiles
  (varredura da tabela `$C1:C5CF`). Já $11F (escora das plataformas) tem prioridade: a Samus passa
  por trás dela. Usar $11F embaixo da nave escondia a Samus (visto no emulador); por isso $2DB.
- Colisão da nave: blocos invisíveis `$x0FF` nas linhas 18–22 (`tools/frigate/ending.py:186`);
  chão do hangar na linha 26; a Samus anda por baixo da nave nas linhas 23–25.
- Teto: não dá para "abrir" o teto de verdade. Sem blocos sólidos na linha 0–1 a Samus (com Space
  Jump) sairia pelo topo da sala sem porta. O espaço tem de aparecer **atrás** (BG2), não em cima.

## Causa (problemas)
O hangar herda o fundo de biblioteca do Wrecked Ship e não tem nenhuma peça própria de hangar.

## Mudança proposta
Três partes, todas só no hangar (`r.key == "hangar"`); nenhuma outra sala muda.

1. **Céu estrelado na BG2** — módulo novo `tools/frigate/space.py`:
   - `star_tiles()`: 8 tiles 4bpp (vazio + estrelas de 1 pixel em cinza/azul/branco + uma
     estrela grande em cruz), `$100` bytes. Cor 0 = transparente (aparece o preto do fundo).
   - `star_tilemap(seed=4)`: mapa 64x32 (`$1000` bytes), 72% vazio, resto estrelas sorteadas
     com espelhamentos; tiles `$240+n`, paleta 4, sem prioridade. Determinístico (mesma ROM sempre).
   - `library_bg(tiles, n, mapa)`: lista de comandos `0002 tiles → VRAM $2400 (n bytes)`,
     `0002 mapa → VRAM $4800 ($1000 bytes)`, `0000` (16 bytes em $8F).
   - `tools/build.py`: tiles e mapa no espaço expandido com `LinearAllocator.put_in_bank` (novo:
     nunca cruza banco, porque a fonte do DMA dá a volta dentro do banco); lista no `bank8f`;
     estado do hangar com `layer2 = $2121` (fundo da biblioteca + paralaxe lenta $20/256) e
     `bg = lista nova`.
   - No protótipo: lista em `$8F:EA7D` = `0200 8981E0 0024 0001 | 0200 8982E0 0048 0010 | 0000`,
     estado do hangar em `$8F:EA9E` (endereços mudam conforme a ordem do build). Custo: 20 bytes
     a mais de $8F (livre até `$8F:F029` no lugar de `$8F:F015`), `$1100` bytes no expandido.
2. **Baía de atracação (parede do fundo)** — `tools/smlib/level.py` ganha dois campos:
   `backdrop` (metatile desenhado depois do estilo, só em células de ar puro `$00FF`, então não
   apaga escoras, portas nem decoração) e `skin` (troca o desenho de um bloco sólido mantendo a
   colisão; erro se o bloco não for sólido). `tools/frigate/props.py` ganha `BACKDROPS`/`SKINS`
   e `rooms.py` os passa ao `Level`:
   - faixa de luzes $2D0/$2D1 na linha 21 e painéis escuros $2EF/$2F0 nas linhas 22–25, colunas
     15–60 (do pé do deck alto até antes da porta da Air Lock). Acima disso: estrelas.
   - garras de atracação: colunas $2DB nas linhas 23–25, x = 50 e 57 (pontas do casco da nave).
3. **Plataforma de pouso** — `skin` na linha 26, x = 48–60: peças de luz $115/$116/$117 com
   espelho vertical (v-flip) embutidas no chão sob a nave. Só o desenho muda; a colisão não.

Diff completo do protótipo (feito na cópia, não no projeto):

```diff
--- a/tools/build.py	2026-10-22 19:18:27
+++ b/tools/build.py	2026-10-22 19:18:27
@@ -21,7 +21,7 @@
 ROOT = Path(__file__).resolve().parent.parent
 sys.path.insert(0, str(ROOT / "tools"))
 
-from frigate import bosses, ending, pausemap, timer  # noqa: E402
+from frigate import bosses, ending, pausemap, space, timer  # noqa: E402
 from frigate.enemies import ENEMIES, enemy_set, population  # noqa: E402
 from frigate.rooms import ROOMS, RoomDef  # noqa: E402
 from smlib.compression import compress, decompress  # noqa: E402
@@ -42,6 +42,7 @@
 
 # Parasite Queen = Phantoon. Fight state copied from the vanilla Phantoon room ($8F:CD13).
 BOSS_ROOM = "reactor_core"
+HANGAR_ROOM = "hangar"         # starfield background (tools/frigate/space.py)
 RIDLEY_ROOM = "airlock"       # Meta Ridley flies off here during the escape (tools/frigate/ending.py)
 PHANTOON_MUSIC = (0x27, 0x06)
 PHANTOON_FX = 0x9C44
@@ -116,6 +117,12 @@
         self.rom.data[start:start + len(payload)] = payload
         self.pc += len(payload)
         return 0x800000 | ((start // 0x8000) << 16) | (0x8000 + start % 0x8000)
+
+    def put_in_bank(self, payload: bytes) -> int:
+        """Like put, but never crossing a bank: DMA sources wrap inside their bank."""
+        if self.pc // 0x8000 != (self.pc + len(payload) - 1) // 0x8000:
+            self.pc = (self.pc // 0x8000 + 1) * 0x8000
+        return self.put(payload)
 
 
 @dataclass
@@ -354,7 +361,16 @@
             set_ptr = (bank_b4.put(ending.gunship_enemy_set()) + 7) & 0xFFFF
         else:
             pop, set_ptr = EMPTY_ENEMY_POP, EMPTY_ENEMY_SET
-        normal = state_bytes(level_ptr, enemy_pop=pop, enemy_set_ptr=set_ptr)
+        if r.key == HANGAR_ROOM:
+            # Prime's hangar is open to space: a starfield on BG2 instead of the WS wall pattern
+            tiles = space.star_tiles()
+            tiles_at = expanded.put_in_bank(tiles)
+            map_at = expanded.put_in_bank(space.star_tilemap())
+            bg = bank8f.put(space.library_bg(tiles_at, len(tiles), map_at)) & 0xFFFF
+            normal = state_bytes(level_ptr, enemy_pop=pop, enemy_set_ptr=set_ptr,
+                                 layer2=space.LAYER2_SCROLL, bg=bg)
+        else:
+            normal = state_bytes(level_ptr, enemy_pop=pop, enemy_set_ptr=set_ptr)
         header = bytes([0, FRIGATE_AREA, r.map_x, r.map_y, r.width, r.height, 0x70, 0xA0, 0x00]) + b"\x00\x00"
         if r.key == BOSS_ROOM:
             # default state = boss alive (Phantoon); E629 #1 selects the boss-dead state
--- a/tools/smlib/level.py	2026-10-22 19:22:08
+++ b/tools/smlib/level.py	2026-10-22 19:22:08
@@ -55,6 +55,10 @@
     decor: list[tuple[int, int, int]] = field(default_factory=list)   # (x, y, metatile) drawn as air
     # (x, y, block word, BTS) written last, as is: collision that the level art doesn't draw
     overlay: list[tuple[int, int, int, int]] = field(default_factory=list)
+    # (x, y, metatile) drawn after the style: on plain air cells only (background, e.g. a back
+    # wall), or on solid cells keeping their collision (`skin`, e.g. a landing pad)
+    backdrop: list[tuple[int, int, int]] = field(default_factory=list)
+    skin: list[tuple[int, int, int]] = field(default_factory=list)
 
     @property
     def wb(self) -> int:
@@ -102,6 +106,13 @@
             self._stamp_door(l1, bts, door)
         if self.style:
             l1 = self.style.apply(l1, wb, hb)
+        for x, y, mt in self.backdrop:
+            if l1[y * wb + x] == AIR:
+                l1[y * wb + x] = word(0, mt & 0x3FF, bool(mt & 0x400), bool(mt & 0x800))
+        for x, y, mt in self.skin:
+            if l1[y * wb + x] >> 12 != 8:
+                raise ValueError(f"acabamento em ({x},{y}) cai num bloco que não é sólido")
+            l1[y * wb + x] = word(8, mt & 0x3FF, bool(mt & 0x400), bool(mt & 0x800))
         for x, y, mt in self.decor:
             if l1[y * wb + x] >> 12 != 0:
                 raise ValueError(f"decoração em ({x},{y}) cai num bloco que não é ar")
--- a/tools/frigate/rooms.py	2026-10-22 19:22:08
+++ b/tools/frigate/rooms.py	2026-10-22 19:22:08
@@ -18,7 +18,7 @@
 from smlib.style import FRIGATE
 
 from .ending import ship_blocks
-from .props import PROPS
+from .props import BACKDROPS, PROPS, SKINS
 
 OPPOSITE = {"L": "R", "R": "L", "T": "B", "B": "T"}
 
@@ -65,7 +65,7 @@
         decor = [cell for prop in PROPS.get(self.key, []) for cell in prop.cells()]
         overlay = ship_blocks(*self.ship) if self.ship else []
         return Level(self.width, self.height, self.canvas.rows(), doors=doors, style=FRIGATE, decor=decor,
-                     overlay=overlay)
+                     overlay=overlay, backdrop=BACKDROPS.get(self.key, []), skin=SKINS.get(self.key, []))
 
 
 # --- generic shapes -----------------------------------------------------------------------------
--- a/tools/frigate/props.py	2026-10-22 19:22:08
+++ b/tools/frigate/props.py	2026-10-22 19:26:00
@@ -64,3 +64,39 @@
     "security_hall": consoles([7, 24], 10),
     "reactor_entrance": consoles([8], 10),
 }
+
+
+# --- Exterior Docking Hangar (Prime P0): open to space above, docking bay below -----------------
+# Background pieces are the dark Wrecked Ship back-wall metatiles ($2xx), drawn as air: they read
+# as far away, so nothing that looks solid is passable (same rule as tools/smlib/style.py).
+V = 0x800  # v-flip
+
+HANGAR_SHIP_X = 54            # tools/frigate/rooms.py: hangar ship=(54, 26)
+HANGAR_FLOOR = 26
+
+
+def hangar_backdrop() -> list[tuple[int, int, int]]:
+    cells = []
+    # docking clamps: columns from the deck up to the ship's belly, at both ends of the hull
+    for x in (HANGAR_SHIP_X - 4, HANGAR_SHIP_X + 3):
+        cells += [(x, y, 0x2DB) for y in range(HANGAR_FLOOR - 3, HANGAR_FLOOR)]
+    # back wall of the bay: 5 rows over the deck, a light band on top, starfield above it
+    top = HANGAR_FLOOR - 5
+    for x in range(15, 61):
+        cells.append((x, top, (0x2D0, 0x2D1)[x % 2]))
+        for y in range(top + 1, HANGAR_FLOOR):
+            cells.append((x, y, (0x2EF, 0x2F0)[(x + y) % 2]))
+    return cells
+
+
+def hangar_pad() -> list[tuple[int, int, int]]:
+    """Landing pad: the deck under the ship gets a lit strip (ceiling light pieces, v-flipped)."""
+    x0 = HANGAR_SHIP_X - 6
+    out = []
+    for i, x in enumerate(range(x0, x0 + 13)):
+        out.append((x, HANGAR_FLOOR, (0x115, 0x116, 0x117)[i % 3] | V))
+    return out
+
+
+BACKDROPS: dict[str, list[tuple[int, int, int]]] = {"hangar": hangar_backdrop()}
+SKINS: dict[str, list[tuple[int, int, int]]] = {"hangar": hangar_pad()}
```

`tools/frigate/space.py` (arquivo novo, completo):

```python
"""Starfield behind the Exterior Docking Hangar (Prime P0 is open to space).

The hangar gets its own library background ($8F command list, research/sm_room_format.md §1):
  - DMA a few star tiles to VRAM word $2400 (BG tiles $240-$27F). The Wrecked Ship SCE graphics
    are $4800 bytes (tiles $000-$23F) and the CRE starts at tile $280, so these 64 tiles are not
    used by any frigate room.
  - DMA a 64x32 BG2 tilemap of those tiles to $4800 (the same place the vanilla WS background
    $8F:E117 writes its two 32x32 screens).
Pixels use colour 0 (transparent: the black backdrop shows) and BG palette line 4, whose colours
1/2/3/13/14 are greys, a pale blue and white in the recoloured frigate palette.
"""
from __future__ import annotations

import random
import struct

STAR_VRAM = 0x2400           # VRAM word address; tile number = STAR_VRAM // 16
STAR_TILE0 = STAR_VRAM // 16
BG2_TILEMAP_VRAM = 0x4800
PALETTE_LINE = 4
LAYER2_SCROLL = 0x2121       # library BG (bit 0) + slow parallax $20/256 on both axes

# 8x8 tiles as {(x, y): colour}
TILES: list[dict[tuple[int, int], int]] = [
    {},                                                     # 0 empty space
    {(2, 5): 3},                                            # dim
    {(6, 1): 2},
    {(4, 3): 1},
    {(1, 6): 14},                                           # bright
    {(5, 2): 13},                                           # blue
    {(3, 3): 14, (2, 3): 13, (4, 3): 13, (3, 2): 13, (3, 4): 13},   # big star
    {(1, 1): 3, (6, 5): 2},
]
WEIGHTS = [72, 7, 6, 5, 3, 3, 1, 3]


def tile_bytes(pixels: dict[tuple[int, int], int]) -> bytes:
    """One 4bpp SNES tile (planes 0/1 interleaved in the first 16 bytes, 2/3 in the last 16)."""
    out = bytearray(32)
    for (x, y), c in pixels.items():
        bit = 0x80 >> x
        for plane in range(4):
            if c >> plane & 1:
                out[(plane >> 1) * 16 + y * 2 + (plane & 1)] |= bit
    return bytes(out)


def star_tiles() -> bytes:
    return b"".join(tile_bytes(t) for t in TILES)


def star_tilemap(seed: int = 4) -> bytes:
    """64x32 BG2 tilemap (two 32x32 screens, $1000 bytes); random flips vary the star positions."""
    rng = random.Random(seed)
    words = []
    for _ in range(64 * 32):
        t = rng.choices(range(len(TILES)), WEIGHTS)[0]
        w = (STAR_TILE0 + t) | (PALETTE_LINE << 10)
        if t:
            w |= rng.choice((0, 0x4000, 0x8000, 0xC000))
        words.append(w)
    return struct.pack(f"<{len(words)}H", *words)


def library_bg(tiles_at: int, n_tile_bytes: int, map_at: int) -> bytes:
    """Library-BG command list: op 2 = DMA (src24, VRAM word dst, size in bytes); 0 = end."""
    def dma(src: int, dst: int, size: int) -> bytes:
        return struct.pack("<H", 2) + struct.pack("<I", src)[:3] + struct.pack("<HH", dst, size)
    return dma(tiles_at, STAR_VRAM, n_tile_bytes) + dma(map_at, BG2_TILEMAP_VRAM, 0x1000) + b"\x00\x00"
```

## Critérios de aceite
1. `python3 -I tools/validate.py` → 28 salas, 60 portas, 0 problemas (no protótipo: passou).
2. `python3 -I tools/build.py` termina sem erro; `put_in_bank` garante que tiles e mapa das
   estrelas não cruzam banco (assert/verificação no próprio build).
3. `python3 -I tests/run_tests.py` → todos os testes atuais passam, inclusive
   `nave_fechada_antes_do_chefe` e `fuga_ridley_nave_e_final` (no protótipo: 13/13).
4. Colisão da nave inalterada: os blocos de `ship_blocks(54, 26)` no `l1`/BTS do hangar são
   idênticos antes e depois (teste novo em validate.py: `hangar_colisao_nave_igual`;
   protege=colisão/embarque; falha_quando=backdrop/skin tocar bloco da nave; não_prova=visual).
5. Teste novo `hangar_ceu_estrelado` (run_tests.py) — exige um comando `peekvram`/`expectvram`
   no `snesrun` (o protótipo usou `dumpvram`): após NEW_GAME, VRAM palavra $2400 = tiles de
   `space.star_tiles()` e $4800 = `space.star_tilemap()`; repete depois de pausar e despausar,
   depois de usar o X-ray e depois de ir à Air Lock e voltar. Grava
   `build/tests/hangar_ceu.png`. protege=fundo recarregado em toda entrada/retorno;
   falha_quando=DMA não roda ou é sobrescrito; não_prova=que a imagem fica bonita.
6. Mesmo teste: na Air Lock, VRAM $4800 volta a ser o mapa do Wrecked Ship (o fundo das outras
   salas não muda).
7. Imagem: `build/tests/hangar_ceu.png` mostra estrelas em fundo preto acima da parede escura
   do fundo, e na foto ao lado da nave a Samus aparece inteira passando por baixo dela
   (referência: `specs/img/04-depois-inicio.png`, `04-depois-nave.png`).

## Plano de testes
| Camada | O quê | Qtde |
|---|---|---|
| validate.py | colisão da nave igual; `skin` só em blocos sólidos; `backdrop` só em ar | +2 |
| run_tests.py (emulador) | `hangar_ceu_estrelado` (início, pausa, X-ray, ida e volta à Air Lock) | +1 |
| snesrun.c | comando `expectvram ADDR HEXBYTES` ou `dumpvram FILE` (recompilar) | +1 |
| imagem | `hangar_ceu.png` e foto sob a nave | +2 |

Já conferido no protótipo (cópia em scratchpad): estrelas presentes após pausa (estado $0F → $08)
e após X-ray (VRAM igual aos dados gerados); Air Lock e Evacuation Area com o fundo normal
(`ida_fim.png`); `volta_evacuacao_ate_hangar` volta ao hangar com estrelas.

Imagens: `specs/img/04-antes-inicio.png`, `04-depois-inicio.png`, `04-antes-nave.png`,
`04-depois-nave.png`, `04-depois-sala-inteira.png` (render da sala inteira sem a nave, que é
sprite), `04-depois-xray-desligado.png`.

## Riscos e reversão
- Tiles $240–$27F: livres hoje com o tileset 4. Se um dia o tileset da fragata crescer além de
  $4800 bytes, as estrelas ficam por cima dos tiles novos. O build deve checar (assert) o tamanho
  descomprimido dos gráficos do tileset 4 ≤ $4800.
- O teste `nave_fechada_antes_do_chefe` teleporta a câmera; a foto `nave_no_hangar.png` mostra
  restos do mapa de tiles antigo (já era assim antes) — não usar essa foto como critério visual.
- Peças com prioridade de BG cobrem a Samus; só usar no `backdrop` metatiles sem o bit de
  prioridade (a checagem pode virar um assert em `props.py`).
- Paralaxe $2121 é escolha visual; `$0101` (fundo parado) também funciona.
- A plataforma de pouso com luz de teto invertida é discreta; pode-se trocar as peças sem mudar
  nada mais.
- Reversão: desfazer as mudanças em `tools/` e reconstruir.

## Fora de escopo
- Abrir o teto ou as paredes de verdade (a Samus sairia da sala).
- Arte nova de garras/portas da baía (só peças do tileset 4).
- Fundo do Ceres/Crateria (tileset e modo de vídeo diferentes; não precisou).
- Animação de estrelas, FX, luzes piscando.
- Mudar o fundo de outras salas.

## Desvios (preenchido na implementação)
- `snesrun`: o comando novo é `expectvram ADDR FILE` (palavra de VRAM em hex + arquivo com os bytes
  esperados), não `expectvram ADDR HEXBYTES`: o mapa tem $1000 bytes e não cabe numa linha do roteiro.
  `tests/run_tests.py` grava os arquivos de referência em `build/tests/vram_*.bin` (estrelas e mapa de
  `space.py`; mapa do Wrecked Ship descomprimido de `$BA:8DE7`, conferindo antes os bytes de `$8F:E117`).
- `put_in_bank` entrou no `LinearAllocator` (o alocador de `$82` das specs 01–03 é o `Allocator` por banco,
  que não serve ao espaço expandido) e ganhou um assert de que o dado não cruza o banco.
- Os dois asserts sugeridos em "Riscos" viraram checagens do build (`RuntimeError`): gráficos do
  tileset 4 > $4800 bytes, e metatile de `props.BACKDROPS` com bit de prioridade (ou < $100).
- validate.py: uma checagem só (`check_backdrop`, comentário `hangar_colisao_nave_igual`) compara a
  sala com e sem `backdrop`/`skin`: blocos da nave idênticos (palavra e BTS) e tipo de bloco + BTS
  iguais em todas as outras células. Cobre "backdrop só em ar" e "skin só em sólido"; `skin` em bloco
  não sólido continua sendo erro do `Level` (que o validate já relata). Conferido com mutação (skin
  gravando tipo 0 → 14 problemas).
- X-ray no teste: selecionado com 3 toques de SELECT (HUD item 5) e acionado segurando B depois de a
  Samus virar de lado (na pose de frente o X-ray não abre); o teste confere `$0A78` = 1 durante o feixe.
- Fotos: `build/tests/hangar_ceu.png` (início), `hangar_sob_a_nave.png` (tirada depois de pausar e
  despausar, porque o teleporte da câmera deixa restos do mapa antigo na tela), `hangar_depois_do_xray.png`,
  `air_lock_fundo.png`.
- Endereços iguais aos do protótipo: lista em `$8F:EA7D`, estado do hangar em `$8F:EA9E`, estrelas em
  `$E1:8189`/`$E1:8289`; `$8F` livre a partir de `$8F:F029`.
- Contagem de testes: eram 16 (não 13) antes desta spec; agora 17/17.
