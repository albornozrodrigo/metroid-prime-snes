# 07a — Toolchain para várias áreas

Estado: verificada (22/10/2026: .ips sha1 `e9b0db22…8555` igual, validate igual, 20/20 testes)
Esforço estimado: 1 dia (spec 1 h, código 4 h, verificação 1 h)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md)

## Contexto

Hoje o build, o validador, o mapa de pausa, a lista do mapa na SRAM, o manifest e os testes só
conhecem uma área: a fragata (área 3 do SM). O Tallon (área 0) vai precisar de tudo isso de novo.
Esta spec cria a ideia de **área** (`AreaDef`) e faz as ferramentas percorrerem uma lista de áreas,
sem acrescentar nenhuma sala nova. O jogador não vê diferença nenhuma: a ROM tem que sair igual.

## Estado atual (verificado)

Conferido lendo o código em 22/10/2026 (depois das specs 01–06; os números de linha do épico estão
velhos). Antes de mexer: `build/metroid_prime_snes.ips` sha1
`e9b0db220a7f5d7540b02b2ccbbd6e3889e28555`, `validate.py` → "28 salas, 60 portas, 0 problemas",
`build/manifest.json` guardado para comparar.

### Inventário: o que supõe "área 3 / fragata"

| Onde | O quê | Como fica |
|------|-------|-----------|
| `tools/build.py:24-27` | importa `ROOMS`, `ENEMIES`, `BACKDROPS` direto de `frigate.*` | salas e inimigos vêm de `areas.AREAS` |
| `tools/build.py:36-37` | `FRIGATE_AREA = 3`, `FRIGATE_TILESET = 4` | `AreaDef.number`, `AreaDef.tileset` (e `RoomDef.tileset` por sala) |
| `tools/build.py:40-42`, `131-146` | `state_bytes` põe tileset 4, BG/scroll e música da Wrecked Ship em toda sala | `state_bytes(level_ptr, area, ...)`: padrões de `AreaDef.tileset/music/layer2/library_bg` |
| `tools/build.py:45-47` | `BOSS_ROOM`, `HANGAR_ROOM`, `RIDLEY_ROOM` por chave | ficam (são da fragata de propósito); `BOSS_ROOM` lê `FRIGATE.boss_room`; `"hangar"` solto em `build.py:412` passa a usar `HANGAR_ROOM` |
| `tools/build.py:64-66`, `453-461` | estação 0 = sala com `spawn`; estação 1 = única save station (`assert len(save_rooms) == 1`), índice fixo `SAVE_STATION_INDEX` | `AreaDef.load_stations: list[LoadStation]`; o build escreve todas; o PLM de save recebe o índice da estação daquela sala |
| `tools/build.py:79` | `SAVE_SAMUS_ABOVE_FLOOR` (posição da Samus na save station) | vai para `tools/areas.py`, usada ao montar as `LoadStation` |
| `tools/build.py:175` | timer de fuga lê `$7ED82B` (boss bits da área 3) | `escape_timer_routine(area)` lê `$7ED828 + área` (mesmos bytes para a área 3) |
| `tools/build.py:238-246` | `write_load_station` sempre na tabela da área 3 | recebe o número da área |
| `tools/build.py:263-289` | lista do mapa na SRAM só para uma área (`custom = {area: offs}`) | `write_map_save_lists(rom, {área: offs, ...})` com todas as áreas de uma vez (`mapsave.layout` já ordena por área) |
| `tools/build.py:292-329` | mapa de pausa: `assert` dos endereços vanilla da área 3, ícones trocados com as coordenadas vanilla da Wrecked Ship, nome `AREA_NAME = "FRIGATE"`, lista de elevadores esvaziada | `write_pause_map(rom, area, placed)` genérico; os bytes vanilla esperados de cada área ficam numa tabela `VANILLA_PAUSE[área]` (só a 3 por enquanto; outra área sem entrada para o build com mensagem clara); nome = `AreaDef.name` |
| `tools/build.py:376` | cabeçalho da sala com área fixa (índice de sala 0) | byte de área = `area.number`; índice de sala segue 0 (igual hoje) |
| `tools/build.py:344`, `497-513` | `rooms = {r.key: ...}` e `manifest.json` por chave de sala | percorre todas as áreas; chave repetida entre áreas **para o build** (ver Modelo); manifest continua igual |
| `tools/build.py:438-451` | recolore a paleta do tileset 4 e checa estrelas/fundo do hangar | recolor por área com `AreaDef.palette_rows` (cada tileset uma vez); as checagens do hangar ficam da fragata |
| `tools/build.py:462-471` | novo jogo: área 3, estação 0, itens da intro do Prime | área de `areas.START_AREA`; itens ficam (loadout por área é da 07b) |
| `tools/build.py:506` | print do tileset da Queen | `FRIGATE.tileset` |
| `tools/frigate/rooms.py:18`, `67` | `style=FRIGATE` fixo e `Palette` padrão em `RoomDef.level()` | campos `RoomDef.style` (padrão `FRIGATE`), `RoomDef.palette` (padrão `Palette()`), `RoomDef.tileset` (padrão `None` = o da área) |
| `tools/frigate/pausemap.py:1` | docstring "frigate (area 3)" | o código já é genérico (recebe salas); só o texto muda |
| `tools/frigate/mapsave.py` | já genérico (dict por área) | sem mudança |
| `tools/validate.py:35-37`, `43` | importa `ROOMS`/`ENEMIES`/`PROPS` da fragata, `FRIGATE_AREA = 3` | percorre `areas.AREAS`; inimigos/objetos de `AreaDef.enemies/props` |
| `tools/validate.py:58`, `77` | `by_key` global; porta para sala desconhecida dá `KeyError` | `by_key` por área; porta para sala fora da área vira problema |
| `tools/validate.py:125` | `mapsave.check` só da área 3 | `mapsave.check` com todas as áreas juntas |
| `tools/validate.py:194-196` | "objetos em salas que não existem" só quando `r is ROOMS[0]` | checado uma vez por área |
| `tools/validate.py:277-312` | progressão da fragata (chefe, rota de fuga, hangar) | fica da fragata de propósito, ligada por `PROGRESSION["frigate"]`; `START_ROOM`/`BOSS_ROOM` lidos da `AreaDef` |
| `tools/validate.py:319` | contagem de salas/portas de `ROOMS` | soma de todas as áreas (mesmo texto) |
| `tools/preview_rooms.py:6`, `13-16`, `20` | só salas da fragata, `load_tileset(rom, 4, 3)`, recolor `FRIGATE_ROWS`, arquivo `frigate_<sala>.png` | percorre áreas; tileset por sala, área = `area.number`, linhas = `area.palette_rows`, arquivo `<área.key>_<sala>.png` (mesmos nomes) |
| `tests/run_tests.py:17` | `from frigate.rooms import ROOMS` | `ROOMS = FRIGATE.rooms` (de `areas`) |
| `tests/run_tests.py:38`, `97-98`, `131` | `$7ED82B`, `$7ED8FE`, `$7ED90B` e estação de save 1 escritos à mão | derivados de `FRIGATE.number` e de `FRIGATE.load_stations` (mesmos valores) |

Fica preso à área 3 **de propósito** (é a fragata, não a toolchain): `tools/frigate/ending.py`
(patches da nave e Ridley só na área 3), `areaselect.py` (nome da área 3 na seleção), `bosses.py`,
`queen_art.py` e `space.py` (tileset 4/5, Phantoon, estrelas do hangar), as salas especiais
`BOSS_ROOM`/`RIDLEY_ROOM`/`HANGAR_ROOM` no build, a progressão da fragata no validador, o nome de
debug "FRIGATE" do enemy set (`enemies.py:96`, sem efeito no jogo), o `Palette` padrão de
`smlib/level.py:26` e `FRIGATE` de `smlib/style.py:139` (continuam sendo o padrão; a 07c cria os
da Crateria), o loadout da intro e o alcance com Space Jump (07b). Os testes do emulador seguem
sendo roteiros da fragata.

## Mudança proposta

### Modelo (novo arquivo `tools/areas.py`)

```python
@dataclass(frozen=True)
class LoadStation:
    index: int   # estação da área (0 = chegada / novo jogo; 0-7 são as do save)
    room: str    # chave da sala
    x: int       # pixel da Samus na sala
    y: int

@dataclass
class AreaDef:
    key: str                     # "frigate": nome curto (arquivos de prévia <key>_<sala>.png)
    number: int                  # byte de área do SM (fragata = 3)
    name: str                    # nome no mapa de pausa ("FRIGATE"), até 12 letras A-Z
    rooms: list[RoomDef]
    tileset: int                 # tileset padrão das salas (RoomDef.tileset sobrepõe)
    music: tuple[int, int]       # (song set, faixa) padrão dos estados
    layer2: int                  # scroll do BG2 padrão
    library_bg: int              # lista de comandos do fundo padrão ($8F)
    load_stations: list[LoadStation]
    enemies: dict[str, list[Spawn]] = {}
    props: dict[str, list[Prop]] = {}
    palette_rows: tuple[int, ...] = ()   # linhas da paleta do tileset recoloridas (vazio = nenhuma)
    boss_room: str | None = None         # sala do ícone de chefe no mapa de pausa

    def by_key(self) -> dict[str, RoomDef]
    def tileset_of(self, room: RoomDef) -> int     # room.tileset ou self.tileset
    def station_in(self, room_key: str) -> int     # índice da estação daquela sala

def stations_from_rooms(rooms) -> list[LoadStation]:
    """0 = sala com spawn; 1, 2… = salas com save station, na ordem das salas."""

FRIGATE = AreaDef("frigate", 3, "FRIGATE", ROOMS, tileset=4, music=(0x30, 0x05),
                  layer2=0xC1C1, library_bg=0xE117, load_stations=stations_from_rooms(ROOMS),
                  enemies=ENEMIES, props=PROPS, palette_rows=FRIGATE_ROWS, boss_room="reactor_core")
AREAS = [FRIGATE]          # ordem do build = ordem de alocação na ROM
START_AREA = FRIGATE       # novo jogo começa na estação 0 desta área
```

`all_rooms()` devolve `(área, sala)` de todas as áreas e para com erro se uma chave de sala
aparecer em duas áreas. **Regra de chaves:** a chave de sala é global (o manifest e os testes usam
a chave sozinha); salas de áreas novas usam o prefixo da área (`tallon_landing_site`), então as
11 salas da fragata afundada com nome repetido não colidem. Assim o `manifest.json` não muda de
formato.

`RoomDef` (em `tools/frigate/rooms.py`, onde está) ganha `style: Style = FRIGATE`,
`palette: Palette = Palette()` e `tileset: int | None = None`; `level()` passa `style` e
`palette` ao `Level` (os valores padrão são os de hoje).

### Build (`tools/build.py`)

- `rooms` = `Placed` de todas as salas de `all_rooms()`, cada um com a sua `area`.
- `state_bytes(level_ptr, area, *, tileset/music/layer2/bg=None, ...)`: `None` = padrão da área.
- Cabeçalho com `area.number`; PLM de save com `area.station_in(sala)`.
- Passo 4: para cada área, `write_load_station(rom, bank83, area.number, st.index, …)` na ordem
  dos índices (mesma ordem de alocação em `$83` de hoje); depois o novo jogo com `START_AREA`.
- `write_pause_map(rom, area, placed)` por área (tilemap, máscara, nome, ícones de chefe/map
  station/save/elevadores comparados com `VANILLA_PAUSE[area.number]`); as listas de SRAM de todas
  as áreas vão juntas num `write_map_save_lists` no fim.
- Recolor: um por tileset de área com `palette_rows`; checagens do hangar continuam logo depois.
- Prints mantêm o mesmo texto para a fragata.

### Validador, prévia e testes

- `validate.py`: `check()` percorre `AREAS`; cada área faz as checagens de sala, mapa e progressão
  (`PROGRESSION = {"frigate": check_progression}`); `mapsave.check` com todas as áreas; a saída
  final soma salas e portas.
- `preview_rooms.py`: percorre áreas (mesmos nomes de arquivo).
- `tests/run_tests.py`: salas de `FRIGATE.rooms`; endereços de RAM da área 3 e estação de save
  derivados da `AreaDef`. Nenhum roteiro muda.

## Critérios de aceite

1. `python3 -I tools/build.py` gera `build/metroid_prime_snes.ips` com sha1
   `e9b0db220a7f5d7540b02b2ccbbd6e3889e28555`, igual ao de antes, e igual de novo ao reconstruir
   (checagem: `shasum`).
2. `python3 -I tools/validate.py` → saída completa igual à de antes ("28 salas, 60 portas, 0
   problemas") (checagem: `diff` com a saída guardada).
3. `python3 -I tests/run_tests.py` → 20/20.
4. `build/manifest.json` byte a byte igual ao de antes (checagem: `cmp`).
5. `python3 -I tools/preview_rooms.py` gera os mesmos 28 PNGs (checagem: sha1 dos arquivos).
6. Nenhum `FRIGATE_AREA`/`FRIGATE_TILESET`/`from frigate.rooms import ROOMS` sobra em `build.py`,
   `validate.py`, `preview_rooms.py` e `run_tests.py` (checagem: `grep`).
7. Chave de sala repetida entre áreas para o build e o validador com mensagem (checagem: teste
   manual com uma `AreaDef` falsa numa cópia; não fica no código).

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| build | sha1 do .ips igual, duas vezes | 1 |
| validate.py | saída igual; percorre áreas | 0 novas |
| run_tests.py | os 20 de hoje | 0 novos |
| prévia | 28 PNGs iguais | 1 |

Não entram testes novos: uma refatoração pura se prova pela ROM igual.

## Riscos e reversão

- Mudar a ordem de alocação em `$8F`/`$83`/`$E0+` muda a ROM; o sha1 pega isso na hora.
- `mapsave.layout` põe áreas novas antes da 3 se o número for menor (o Tallon = 0 empurra o bloco
  da fragata). É a regra já escrita em `mapsave.py`; muda a ROM só quando a 07f ligar a área 0.
- Reversão: tudo está em `tools/` e `tests/`; reverter o código e reconstruir basta.

## Fora de escopo

- Salas do Tallon (07d/07g) e qualquer `AreaDef` nova.
- Física de pulo / alcance sem Space Jump e loadout por área (07b).
- Estilo, metatiles, FX e música da Crateria (07c).
- Mapa de pausa da área 0 e os bytes vanilla dela em `VANILLA_PAUSE` (07f).
- Mover os módulos `tools/frigate/*` de lugar.

## Desvios (preenchido na implementação)

Verificação (22/10/2026, na pasta real):

- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `e9b0db220a7f5d7540b02b2ccbbd6e3889e28555` nas duas; a saída do build (endereços de cada sala,
  estações, espaço livre) é idêntica à de antes (`diff`).
- `python3 -I tools/validate.py` → "28 salas, 60 portas, 0 problemas"; saída completa igual (`diff`).
- `python3 -I tests/run_tests.py` → 20/20 passaram.
- `build/manifest.json` byte a byte igual (`cmp`); formato não mudou, os testes não precisaram mudar
  de leitura.
- `python3 -I tools/preview_rooms.py` → os mesmos 28 PNGs (sha1 iguais) e a mesma saída.
- Critério 7: com uma `AreaDef` falsa repetindo a fragata (só na memória), `all_rooms()` e
  `validate.check()` param com "sala 'hangar' existe nas áreas frigate e fake"; o build usa
  `all_rooms()`, então para também.

Desvios e detalhes que a spec não dizia:

- `write_pause_map` confere também que cada lista de ícones nova tem o tamanho da vanilla (ela é
  escrita no lugar); com tamanho diferente o build para com mensagem, em vez de passar por cima do
  que vem depois. Para a fragata o tamanho é o mesmo.
- O recolor para com erro se duas áreas pedirem linhas diferentes para o mesmo tileset (o recolor é
  global por tileset, risco já citado no épico).
- `tests/run_tests.py`: `step_on_save_station` usa a posição da `LoadStation` (mesmos 48/136 px
  que a conta escrita à mão dava). Os outros `0003` literais dos roteiros ficaram: são roteiros da
  fragata.
- O critério 1 do épico cita o sha1 `85d9…8921`, de antes das specs 01–06; o certo agora é
  `e9b0…8555`.
