# 07f — Mapa de pausa e minimapa do Tallon

Estado: verificada (22/10/2026: validate 33/68/0; .ips sha1 `43f480e1…270c`, igual ao reconstruir; 26/26 testes)
Esforço estimado: 1 dia (spec 1 h, código 2 h, testes 2 h, verificação e imagens 1 h)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (linha 07f; critério 6 `tallon_mapa_salvo`;
decisão 6: sem map station)

## Contexto

Na área 0 (Tallon) a pausa ainda mostra o mapa vanilla da **Crateria**: título "CRATERIA", a grade
dela, o ícone da nave na Landing Site vanilla e o ícone da map station dela. O minimapa do HUD usa
o mesmo tilemap, então também mostra a Crateria. E o save só guarda os bytes de mapa explorado que a
Crateria usava: parte do que a Samus explora no Tallon some depois de salvar e continuar. Na tela de
continue (spec 01), um save no Tallon mostraria "CRATERIA" na região acesa.

## Estado atual (verificado)

Lido nos bytes de `base/sm_fix.sfc` e da ROM atual (`build/`, sha1 do .ips
`4ad1826bda0ef2b7d4ed91dc15da4d8b1617ec77`), no código C (`vendor/sm/src`) e com scripts de leitura.

- `tools/areas.py`: `TALLON.pause_map = False`; `tools/build.py` `VANILLA_PAUSE` só tem a área 3; a
  área 0 fica com as tabelas vanilla.
- Tabelas da área 0 (todas no lugar vanilla, iguais na ROM base e na atual):

  | O quê | Endereço | Vanilla |
  |---|---|---|
  | tilemap 64×32 (pausa e minimapa) | `$82:964A` → `$B5:9000` (0x1000 bytes) | Crateria |
  | máscara da map station | `$82:9717` → `$82:9727` (0x100), só dela | Crateria |
  | nome na pausa | `$82:965F` → `$82:966F` (12 words) | "  CRATERIA  " |
  | ícones de chefe | `$82:C7CB` → `$82:C83B` | 3× `FFFE` + `FFFF` (nada desenhado) |
  | ícone de map station | `$82:C7FB` → `$82:C84D` | `(B8,40)` + `FFFF` |
  | ícones de save (n = estação n) | `$82:C80B` → `$82:C853`, 8 entradas | `(D8,28) (90,38)` + 6× `FFFE` |
  | ícones de elevador | `$82:C81B` → `$82:C873`, 8 entradas | `(1A0,58) (110,40) (B8,90) (30,48) (88,50)` + 3× `FFFE` |
  | rótulos "to <área>" | `$82:C74D` → `$82:C759` | 5 entradas de 6 bytes + `FFFF` |

- A lista de save não termina em 8 entradas: o laço (`DrawMapIconsOfType` `$82:B81C`) segue até um
  `FFFF` e usa um bit de `used_save_stations_and_elevators` por entrada; as entradas 8–15 são a lista
  de elevadores (bits altos = elevadores usados). Na tela de continue `DrawAreaSelectMapLabels`
  (C `sm_81.c:2039`) desenha o nome da área só se um bit usado cair numa entrada que não é `FFFE`
  (até 16 entradas), na ordem de áreas 0, 3, 5, 1, 4, 2 (`kFileSelectMap_AreaIndexes`).
- **Ícone da nave fixo no código, só na área 0**: `$82:B6BC` (pausa, `DrawMapIcons`) e `$82:B777`
  (mapa do continue, `DrawFileSelectMapIcons`): `AD 9F 07 D0 1A A9 00 0E 85 03 AD 55 C8 38 E5 B3 A8
  AD 53 C8 38 E5 B1 AA A9 63 00 22 1F 89 81` = se área 0, desenha a spritemap `$63` em
  (`$82:C853`, `$82:C855`), ou seja, **na entrada 0 da lista de save da área 0**, sempre (sem olhar
  explorado). Trocando a entrada 0 no lugar, a nave vai junto.
- Rótulos "to <área>" (`DisplayMapElevatorDestinations` `$82:BB30`) só aparecem com a map station da
  área usada (`$7ED908+área`): nunca no Tallon, mas são dados da Crateria.
- Limites de rolagem do mapa (`DetermineMapScrollLimits` `$82:9EC4`): sem map station vêm dos bits
  explorados, então a máscara da ROM não muda o que a pausa mostra no Tallon.
- Pausa: `LoadPauseMenuMapTilemap` (`$82:943D`) monta em **`$7E:4000`** (0x1000 bytes) o tilemap
  da pausa: tile explorado = word do tilemap sem o bit `$400`; não explorado = `$001F`. Dá para o
  teste conferir.
- Save do mapa (`tools/frigate/mapsave.py`, spec 03): lista da área 0 em `$81:8146` (cabe 80),
  contagem vanilla 74, início 0. Os 8 bytes das 5 salas do MVP são `31 35 38 39 41 42 45 46`;
  **`35 39 41 45` não estão na lista vanilla** (perdem-se no save hoje). O Tallon inteiro (44 salas)
  usa 47 bytes, e os 8 do MVP estão dentro deles.
- `mapsave.layout` põe os blocos das áreas refeitas depois dos 327 bytes vanilla **em ordem de
  número de área**: com a área 0 entrando, a fragata andaria de +327 para +374.
- Tela de continue: nome da área 0 = spritemap de menu `$39` em `$82:CC6B`, 8 peças, "CRATERIA" numa
  linha (y −4); posição da área 0 na tabela `$81:AA1C` = (`$5B`, `$32`).

## Mudança proposta

1. **`tools/areas.py`**: `TALLON.pause_map = True`. Campo novo `AreaDef.save_map_rooms`
   (padrão `None` = as salas da área) e método `map_save_bytes()` = `mapsave.needed` da máscara
   dessas salas. O Tallon usa a **tabela inteira** (`tallon_rooms.ALL_ROOMS`, 47 bytes): a lista do
   save já fica a definitiva e não muda quando as regiões 07k–07m entrarem (um save antigo continua
   lendo os mesmos bytes nos mesmos lugares). O tilemap e a máscara da ROM continuam só com as salas
   construídas (`area.rooms`): sala não construída nunca é explorada, e sem map station nada mais a
   mostraria.
2. **`tools/frigate/mapsave.py`**: `layout` põe os blocos **na ordem do dicionário** (= ordem de
   `AREAS`, que é a ordem de build), não por número de área. Assim uma área nova nunca empurra o
   bloco das anteriores: fragata continua em +327 (30 bytes), Tallon em +357 (47 bytes),
   404/1280 usados.
3. **`tools/build.py`**:
   - `VANILLA_PAUSE[0]` com os bytes vanilla acima (`tilemap` `$B5:9000`, `reveal` `$82:9727`,
     `map_station` `(B8,40)+FFFF`, `save` as 8 entradas, `elevator_icons` as 8 entradas de
     `$82:C873`, `elevators` os 30 bytes dos 5 rótulos);
   - `write_pause_map` genérica: ícones de save por **índice** de estação (entrada n = estação n;
     estações ≥ 8 não são slots de save e ficam fora; o resto `FFFE`); lista mais curta que a
     vanilla é completada com `FF` (lista vazia = `FFFF`); `elevator_icons` (se existir na área)
     vira `FFFF`, o que também fecha a lista de save em 8 entradas; rótulos "to <área>" viram `FF`.
     A fragata sai com os mesmos bytes;
   - antes de escrever a área 0, conferir os bytes de `$82:B6BC` e `$82:B777` (leitura fixa de
     `$C853/$C855` e spritemap `$63`): o ícone da nave passa a ficar na estação 0 do Tallon (em cima
     da nave da Landing Site);
   - `write_pause_map` devolve `area.map_save_bytes()` e falha se um byte das salas construídas
     ficar fora dela.
   Resultado na área 0: tilemap das 5 salas, nome "TALLON", sem ícone de map station, sem
   elevadores, sem rótulos, ícone de save/nave na estação 0; save com 47 bytes em +357.
4. **`tools/frigate/areaselect.py`**: nome da área 0 na tela de continue = **"TALLON" / "OVERWORLD"**
   em duas linhas (mesmo jeito do "FRIGATE / ORPHEON" da spec 01): spritemap nova de 15 peças no
   espaço livre do `$82` (não cabe nas 8 de `$82:CC6B`), ponteiro `$82:C569+2·$39` (`$82:C5DB`, hoje
   `$CC6B`, conferido antes). Alocada **depois** da da área 3 (endereço da fragata não muda).
   `oam_entries(área)` devolve a posição na tela para os testes; `check_rom` confere as duas.
   O título continua "TALLON IV" (um só para todas as áreas, spec 01).
5. **`tools/validate.py`**: `check_pause_maps(rom)` na ROM construída, para cada área com mapa:
   tilemap e máscara iguais a `pausemap.build`, nome igual a `area_label`, contagem/início/lista do
   save iguais a `map_save_bytes()`/`layout`, ícone de save da estação 0 no lugar, lista de map
   station só com as salas que têm map station; para a área 0, elevadores e rótulos vazios. Mais:
   os bytes das salas construídas estão dentro da lista do save.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 0 problemas (linha do Tallon e "33 salas, 68 portas"), já com
   `check_pause_maps` das áreas 3 e 0 e a lista do save da área 0. (protege = tabelas da pausa e do
   save na ROM; falha_quando = tilemap/nome/ícone/lista diferente, byte construído fora da lista;
   não_prova = o que aparece na tela, isso é dos testes 3–5)
2. `python3 -I tools/build.py` duas vezes → mesmo sha1; log com
   `mapa na SRAM: área 3 = 30 bytes em +327` e `área 0 = 47 bytes em +357 (404/1280 usados)`.
3. Teste novo **`tallon_mapa_salvo`**: chegada na Landing Site, andar pelas 5 salas do MVP até o
   elevador e voltar (como `tallon_rota_mvp`), subir na nave e salvar, morrer, continue; depois do
   continue, os bits explorados de uma tela de cada sala (a tela da porta de entrada) estão em
   `$7E07F7`; pausar: em `$7E:4000` essas telas têm a word do tilemap do Tallon (sem `$400`) e uma
   tela fora das 5 salas tem `$001F`; foto `build/tests/tallon_mapa_salvo.png`. (falha_quando =
   lista do save sem os bytes 35/39/41/45 — **falha na ROM anterior**; tilemap da Crateria;
   não_prova = o desenho do nome, ver 5)
4. Teste novo **`continue_mostra_o_tallon`**: chegada, salvar na nave, morrer; na tela de área:
   estado 5, passo 6, área 0, estação 0; 1º sprite = T de cima do título; o sprite seguinte ao título
   = 1ª letra de "TALLON" (área 0 vem primeiro na ordem do jogo); foto
   `build/tests/continue_tela_do_tallon.png`; depois a tela de salas (foto
   `build/tests/continue_mapa_do_tallon.png`) e o continue volta à Landing Site. (falha_quando =
   "CRATERIA" — **falha na ROM anterior**)
5. Fotos olhadas: pausa no Tallon só com as salas do Tallon, "TALLON" e a nave na Landing Site;
   minimapa do HUD com as salas do Tallon; tela de área com "TALLON / OVERWORLD"; mapa de salas do
   continue com o cursor na nave. Copiadas para `specs/img/07f-*.png`.
6. Fragata igual: `mapa_de_pausa` (o `map_station_e_mapa_de_pausa`) e os outros testes passam; a foto
   `build/tests/mapa_de_pausa.png` é idêntica (bytes dos pixels) à da ROM anterior.
7. `python3 -I tests/run_tests.py` → 26/26 (24 + 2 novos).

Mudança de expectativa de teste: nenhum teste existente muda. `tallon_rota_mvp` continua igual (o
comentário "ainda mostra o mapa vanilla da Crateria" é atualizado).

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_pause_maps` (áreas 3 e 0, ROM construída), bytes construídos ⊂ lista do save | +1 |
| run_tests.py | `tallon_mapa_salvo`, `continue_mostra_o_tallon` | +2 |
| imagem | pausa, minimapa, tela de área, mapa de salas do continue; pausa da fragata idêntica | 5 |
| build | sha1 igual em dois builds | 1 |

## Riscos e reversão

- **Saves feitos antes**: a lista do Tallon passa a ler de +357; um save antigo no Tallon perde o
  mapa explorado uma vez (só o mapa). A fragata não muda de lugar (+327).
- **Nave fixa no código**: o ícone da nave segue a entrada 0 da lista de save da área 0. Se um dia o
  Tallon tiver a estação 0 longe da nave, o ícone vai junto (hoje são a mesma coisa, 07e).
- A lista de elevadores da área 0 fica vazia: quando os elevadores (07j) existirem de verdade, a
  spec deles põe os ícones de volta.
- A spritemap de depuração `$82:C893` (só com `enable_debug`) fica vanilla.
- Reversão: `pause_map=False` no Tallon, tirar `VANILLA_PAUSE[0]`, a ordem do `layout` e o nome da
  área 0 do `areaselect`; ou reverter os arquivos e reconstruir.

## Fora de escopo

- Ícones de elevador e de itens (07h/07j); map station (o Tallon não tem, decisão 6).
- Redesenhar o planeta da tela de área (continua o desenho do Zebes, spec 01).
- Mover a lista do save para o espaço livre de `$81` (47 ≤ 80, não precisa).

## Desvios (preenchido na implementação)

Verificação (22/10/2026, na pasta real):

- `python3 -I tools/validate.py` → linha do Tallon (47/80) e `33 salas, 68 portas, 0 problemas`,
  saída 0, já com `check_pause_maps` nas áreas 3 e 0.
- `python3 -I tools/build.py` duas vezes → `.ips` sha1 `43f480e12ee7a3a18d5c700fcba90c2e3183270c`
  nas duas; log `mapa na SRAM: área 0 = 47 bytes em +357` e `área 3 = 30 bytes em +327
  (404/1280 usados)`; nome da área 3 continua em `$82:F75D`, o da área 0 vai para `$82:F7A5`.
- `python3 -I tests/run_tests.py` → **26/26** (2 min 14 s).
- Na ROM anterior (`pre07f.sfc`, mesmos roteiros): `tallon_mapa_salvo` falha (bits explorados dos
  bytes 39 e 41, fora da lista vanilla, somem depois do continue: `$7E081E`, `$7E0820`; VRAM do mapa com tiles da
  Crateria; nome `$3832` "C"); `continue_mostra_o_tallon` falha no 17º sprite (letra de "CRATERIA").
- Mutações na memória da ROM construída: tilemap, nome, contagem do save, ícone de elevador e ícone
  de map station voltando → cada um acusado por `check_pause_maps`; a ROM anterior inteira dá 6
  problemas; `areaselect.check_rom` na ROM anterior acusa o nome da área 0.
- Bytes que mudaram em relação à ROM anterior (comparação byte a byte): `$81:8131` (contagem e
  início da área 0), `$81:8146` (lista, 47), `$82:966F` (nome), `$82:9727` (máscara), `$82:C5DB`
  (ponteiro do nome no continue), `$82:C759` (rótulos), `$82:C84D–$82:C892` (map station, save,
  elevadores), `$82:F7A5` (spritemap nova), `$B5:9000` (tilemap). Nada da fragata.
- Fragata igual: `build/tests/mapa_de_pausa.png` e `continue_tela_de_area.png` idênticas byte a
  byte às da ROM anterior.
- Imagens: `specs/img/07f-pausa-tallon.png` (depois de explorar as 5 salas, salvar e continuar),
  `07f-minimapa-tallon.png`, `07f-continue-tela-de-area.png`, `07f-continue-mapa-de-salas.png`,
  `07f-antes-pausa-crateria.png` (ROM anterior: "CRATERIA", nave da Crateria no canto, minimapa
  vazio) e `07f-depois-pausa-tallon-rota.png` (mesmo momento do `tallon_rota_mvp`, ROM nova).

Desvios e detalhes:

- **Lista do save = tabela inteira (47 bytes), não só as 5 salas (8)**: o pedido dizia "só os bytes
  necessários". Os 47 são os necessários para o Tallon inteiro; com só 8, cada região nova (07k–07m)
  mudaria a lista e o início dos blocos, e saves antigos perderiam o mapa a cada spec. O tilemap
  continua só com as salas construídas.
- **`mapsave.layout` em ordem de build** (a spec 03 dizia "em ordem de área"): sem isso a área 0
  empurraria a fragata de +327 para +374.
- **Teste do mapa na pausa lê a VRAM** (`$3000`/`$38AA`), não `$7E:4000` como a spec dizia: o buffer
  é reaproveitado depois do DMA (no emulador ele tinha `$184E` em tudo). O teste também confere o
  nome "TALLON" na VRAM.
- `continue_mostra_o_tallon` lê o passo do menu (`peekw 7E0727`) antes da foto do mapa de salas, sem
  `expect` (o tempo da animação varia); a foto foi olhada.
- Ícone de elevador: nenhum (as salas de transporte são de enfeite; fica para a 07j).
- `save_on_tallon_ship` ganhou o nome da foto como parâmetro (testes em paralelo não escrevem o
  mesmo arquivo). Nenhuma expectativa de teste existente mudou.

