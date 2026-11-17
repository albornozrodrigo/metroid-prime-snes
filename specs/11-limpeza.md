# 11 — Limpeza: salas vanilla órfãs

Estado: verificada (26/10/2026: validate 72/148/0 com a linha do Tallon igual e a linha nova "órfãs: …"; .ips sha1
`3919c3c73d46afc45ffd4eb51083daebbe8264ff` igual em dois builds, a ROM não mudou; 53/53 testes)
Esforço estimado: 1 dia (auditoria 0,5; checagem, teste e documentação 0,5)

## Contexto

O jogo hoje é a fragata (área 3, salas novas) e o Tallon Overworld (área 0, 44 salas, 20 itens em 7 rodadas). Todas as salas
do jogo são **cabeçalhos novos** no espaço livre do `$8F`; as 262 salas do Super Metroid continuam na ROM. Trabalhos anteriores
anotaram que a Crateria e a Wrecked Ship vanilla ficaram "sem ligação" (HANDOFF), mas ninguém tinha provado **por quais
caminhos** o jogo ainda carrega uma sala, nem o que as salas órfãs seguram de espaço e de dados que as nossas usam. A próxima
etapa provável (Chozo Ruins, 64 salas e 136 portas no Prime) precisa saber quanto espaço sobra em cada banco.

## Estado atual (verificado)

Antes desta spec, na pasta real: `python3 -I tools/validate.py` → "72 salas, 148 portas, 0 problemas"; `.ips` sha1
`3919c3c73d46afc45ffd4eb51083daebbe8264ff`; `python3 -I tests/run_tests.py` → 52/52.

Roteiros da auditoria no scratchpad da sessão (`…/scratchpad/s11/`: `crawl.py`, `audit.py`, `space.py`, `demo/`), nunca em
`build/`. Fatos lidos dos bytes (ROM base e `build/metroid_prime_snes.sfc`) ou do emulador:

### Como o jogo carrega uma sala

Uma sala só é carregada por uma **entrada de porta** (`$83`): estação de carga (`$80:C4B5`, 14 bytes, a sala carregada é o destino
da porta, `LoadDoorHeader`), demo (`$82:876C`, 18 bytes por cena, mesma regra, `LoadDemoRoomData` `$82:8679`) ou porta de sala
(lista do cabeçalho +9, índice = BTS dos blocos de porta tipo 9). Varrendo a ROM base a partir de **todas** as estações e demos,
seguindo só as portas que os blocos de porta usam: **262 salas** (área 0: 34, 1: 54, 2: 76, 3: 16, 4: 56, 5: 19, 6 Ceres: 6,
7 debug: 1), igual à contagem da `research/sm_room_format.md`. O `research/sm_rooms.json` (que o validador usava para os bits
vanilla) tem **250**: faltam `$A201`, `$A734`, `$B0B4`, `$B1BB`, `$DF1B`, as 6 de Ceres e a de debug `$E82C`.

### Entradas do jogo construído (bytes)

| Caminho | Bytes | Estação | Sala |
|---|---|---|---|
| Novo jogo | `$82:EED9` = `JMP $F70F` (pula introdução e Ceres); rotina `$82:F70F`: `LDA #3; STA $079F`, `LDA #0; STA $078B` | 3/0 | hangar |
| Fim da fragata | `$82:8032` = `STZ $079F`, `$82:8035` = `LDA #$12` | 0/$12 | Landing Site (Tallon) |
| Save da fragata | PLM `$B76F` arg 1 na Reactor Entrance | 3/1 | Reactor Entrance |
| Save do Tallon | PLM `$B76F` arg 1 na Savestation | 0/1 | Savestation |
| Nave do Tallon | `GunshipTop_12` salva na estação 0 da área atual | 0/0 | Landing Site (Tallon) |
| Game over → continue | carrega a SRAM: área e estação de um dos saves acima (o novo jogo grava na hora: `JSL $81:8000` na rotina `$82:F70F`) | — | — |
| Demos de atração | `$82:876C`, tabela igual à da ROM base | — | **19 salas vanilla** |
| Debug | estações `$08–$0F` (elevadores) e `$10+` só com `$7E05D1 ≠ 0`; o código só zera esse byte (`sm_80.c:214`) | — | nenhuma |
| Introdução / Ceres (`loading_game_state $1F`) | só no fim da introdução (`$8B:C100`), que o `JMP` acima pula | — | nenhuma |

Seguindo as portas a partir dessas 5 estações: **exatamente as 72 salas nossas**; nenhuma porta nossa leva a cabeçalho vanilla; o
número de portas usadas pelos blocos de cada sala é o do `RoomDef`. As outras estações das áreas 0 e 3: `0/2–7`, `3/2–$F` sem porta
(`$0000`); `0/$08–$0C`, `0/$10–$11`, `3/$10–$11` (debug/elevador) apontam para salas vanilla, inalcançáveis.

### As demos de atração (emulador)

ROM construída, sem tocar em nada (`demo/script.txt`, 36000 quadros): a tela-título fica parada ~2900 quadros e o jogo toca as demos
do Super Metroid (estado `$28/$2A`): conjunto 0 = Landing Site vanilla `$91F8`, `$9F11`, `$9D9C`, `$B106`, `$AFFB`, `$9D19`; volta ao
título; conjunto 1 = `$A408`, `$9C5E`, `$9E52`, `$AF14`, `$9879`, `$9CB3`; conjunto 2 = `$CC6F` (Wrecked Ship), `$91F8`, `$A56B`, `$A322`,
`$A59F`, `$A66A`; e de novo o 0 (o conjunto 3 só existe com a SRAM marcada "supermetroid", `VerifySRAM $80:8261`). Comparando
quadro a quadro com a ROM base (`demo/cmp.png`): **iguais**, menos o **minimapa do HUD**, que desenha o mapa da nossa área (o da área 0
é o do Tallon; vazio onde a Crateria vanilla tinha sala). `LoadDemoRoomData` enche os bits de item (`$7ED870`, 64 bytes: inclui os nossos
`$A0–$B3`) com `$FF` e zera portas/eventos/chefes **na WRAM**; o jogador não controla a demo, e toda saída dela passa pelo título e pela
tela de arquivos: um novo jogo logo depois começa limpo (conferido: `$7ED884–$7ED886 = 0`, `$7ED8C6 = 0`, chefes 0, hangar), um continue
recarrega tudo da SRAM. "Fim" no game over faz soft reset (zera o banco `$7E`, `sm_80.c:166`).

### Bits de item e de porta

Varrendo as 262 salas (bytes): bits de item vanilla 0–`$9A` (100 bits), bits de porta vanilla até `$A9` (114 bits); os do Tallon:
itens `$A0–$B3`, portas vermelhas `$B0–$B2` (vetores separados: item `$7ED870`, porta `$7ED8B0`). **Nenhuma sobreposição**, e as 12
salas que faltavam no `sm_rooms.json` não têm bit nenhum (mesmos conjuntos). Mas a checagem do validador (`check_gates`,
`check_tallon_items`) só via 250 salas: um bit numa das 12 passaria.

### O que as órfãs seguram (bytes)

Os dados vanilla de sala em `$8F`, `$83`, `$A1` e `$B4` estão **byte a byte iguais à ROM base** (diff por banco: o build só escreve nas
faixas livres e na entrada do tileset 4, `$8F:E6C6–E6CE`). As nossas salas usam de propósito, fora do espaço livre do build:
FX da chuva `$83:80C0` (sala de demo `$91F8`), fundo da Wrecked Ship `$8F:E117` (órfãs `$CA08` e `$E82C`), fundo das cavernas `$8F:B905`
(órfãs da Crateria de tileset 2), e do Phantoon (`$CD13`, órfã) a população `$A1:CCD4`, o set `$B4:8D1D`, o FX `$83:9C44` e o fundo
`$8F:E0FD`; população e set vazios `$A1:85D8`, `$B4:8129`. Tilesets: os nossos usam 0, 2 e 4 (4 recolorido e com tabela de metatiles
própria); 5 só a Wrecked Ship vanilla (e a demo `$CC6F`); **01 nenhuma sala**; 03, 08, 0C–0E, 0F–14 (Ceres), 16–19, 1B, 1C só órfãs.

**Órfãs: 243 salas** (área 0: 31, 1: 43, 2: 73, 3: 15, 4: 55, 5: 19, 6: 6, 7: 1) + 19 só nas demos. Bytes que só órfãs usam (estruturas
de sala, sem código): **`$8F` 20637** (66 pedaços; maiores `$8F:D4EF–DDBD` 2255, áreas 4/5; `$8F:92B3–9878` 1478, área 0; `$8F:C49B–C8C6`
1068), **`$83` 9356**, **`$A1` 24030**, **`$B4` 4017**.

### Espaço livre de hoje (varredura de `$FF` no fim de cada banco da ROM construída)

| Banco | Para quê | Livre | A partir de |
|---|---|---|---|
| `$8F` | cabeçalhos, estados, listas de porta/PLM, fundos, código de sala | **1781** | `$8F:F90B` |
| `$83` | entradas de porta, FX | 19294 | `$83:B4A2` |
| `$A1` | populações de inimigos | 3851 | `$A1:F0F5` |
| `$B4` | sets de inimigos | 2488 | `$B4:F648` |
| `$84` | PLMs (código) | 3225 | `$84:F367` |
| `$A0` | espécies de inimigo | 1985 | `$A0:F83F` |
| `$A2` / `$A6` / `$82` | nave / Ridley / menus | 2744 / 111 / 2062 | `$A2:F548` / `$A6:FF91` / `$82:F7F2` |
| `$E0–$EF` | níveis (24 bits) | 500129 | `$E0:DE5F` |
| `$F0–$FF` | gráficos, paletas (24 bits) | 500297 | `$F0:DDB7` |
| SRAM do mapa | bytes explorados | 876 de 1280 | +404 |

(O HANDOFF dizia "`$83` … (264)", "`$A1` … (236)", "`$B4` … (52)": os endereços estavam certos, os números não eram o livre.)

### Achados

| # | Achado | Risco | Decisão |
|---|--------|-------|---------|
| B1 | Nenhum caminho do jogo (novo jogo, saves, nave, fim da fragata, game over, debug) entra numa sala vanilla, mas nada no validador prova isso: uma porta, estação ou save errado levaria a Samus para a Crateria/Brinstar vanilla sem erro. | médio (futuro: Chozo mexe em estações, portas e saves) | **`check_orphans`** |
| B2 | As demos de atração tocam 19 salas vanilla (Crateria, Brinstar, Norfair, Wrecked Ship, Maridia) com o minimapa da nossa área. O jogador vê, não controla. | baixo (cosmético) | **decisão do usuário**; até lá, lista explícita `DEMO_SCENES` conferida. **Resolvido na [spec 16](16-titulo-e-demos.md)**: demos desligadas (`$8B:9F2C`), `check_orphans` sem exceção; o teste `atracao_e_novo_jogo` virou `titulo_sem_demo_e_novo_jogo` |
| B3 | A demo deixa os bits de item `$A0–$B3` = `$FF` na WRAM. | nenhum hoje (novo jogo e continue regravam) | teste `atracao_e_novo_jogo` |
| B4 | Bits vanilla do validador lidos de `research/sm_rooms.json` (250 salas, faltam 12). | baixo (hoje nenhum bit nas 12) | varredura dos bytes (`smlib/roomgraph.py`) |
| B5 | Nossas salas dependem de 8 dados vanilla (FX, fundos, populações, sets) que moram em salas órfãs ou de demo: recuperar espaço sem saber disso quebraria a fragata/o Tallon. | médio (para a Chozo) | lista explícita `VANILLA_SHARED` conferida contra a ROM base |
| B6 | `$8F` livre 1781 bytes; as 72 salas custaram ~55 bytes de `$8F` cada: as 64 salas da Chozo pedem ~3500. Órfãs seguram 20637 em `$8F`. | alto para a Chozo, nenhum agora | **só documentado** (nota abaixo); recuperar é da etapa da Chozo |
| B7 | Um save da SRAM do Super Metroid vanilla (mesmo formato) carregaria a sala vanilla dele. | baixo (exige copiar o `.srm` de outra ROM) | documentado; não conferido no emulador |

## Mudança proposta

Nenhuma mudança na ROM (o sha1 fica igual). Só validador, um teste e documentação.

1. **`tools/smlib/roomgraph.py`** (novo): o grafo de salas lido dos bytes — portas usadas pelos blocos tipo 9 de cada estado
   (`door_slots`, `room_doors`), destino de porta, estação, cenas de demo, `walk`, `vanilla_rooms` (todas as estações + demos), saves
   de uma sala, e o tamanho das estruturas presas a banco de uma sala (`structures`: cabeçalho e estados, scroll, PLMs e listas de
   scroll de PLM, raio X, fundo, lista de portas e entradas, FX, população, set com o nome).
2. **`tools/build.py`**: as quatro faixas livres viram constantes (`FREE_8F`, `FREE_83`, `FREE_A1`, `FREE_B4`), mesmos valores.
3. **`tools/validate.py`**:
   - `vanilla_door_bits` / `vanilla_item_bits` leem as 262 salas dos bytes (`vanilla_rooms`, em cache por ROM) em vez do
     `sm_rooms.json`.
   - `entry_stations(rom)`: estações do novo jogo (o `JMP` em `$82:EED9` e os `LDA #; STA $079F/$078B` da rotina) e do fim da fragata
     (`STZ $079F; LDA #imm` em `$82:8032`), lidas dos bytes.
   - **`check_orphans(rom, base, manifest)`**: a partir dessas estações, de toda estação que um PLM de save (`$B76F`) de sala alcançada
     grava e da estação 0 de toda área alcançada (a nave), pelas portas dos blocos: as salas alcançadas são **exatamente** as do
     manifest (sala vanilla alcançável = erro com o caminho; sala nossa sem caminho = erro); estação usada sem porta = erro; lista de
     portas do tamanho do `RoomDef`. **Lista explícita das salas vanilla usadas de propósito**: `DEMO_SCENES` (as 23 cenas, tabela
     igual à da ROM base, bytes das 19 salas iguais aos da base). **Lista explícita dos dados vanilla compartilhados**:
     `VANILLA_SHARED` (FX, fundo, população, set): estado nosso apontando para fora do `build.FREE_*` só nela, cada entrada usada e
     igual à base; PLMs, código, raio X, scroll e portas nossos no espaço livre. Imprime a linha "órfãs: … bytes só delas: …".
4. **`tests/run_tests.py`**: teste novo `atracao_e_novo_jogo` (título parado: as 6 salas do conjunto 0 nas horas medidas, `$7ED884 =
   $FFFF` durante a demo, volta ao título; novo jogo: hangar, bits de item `$A0–$B3` e porta `$B0–$BF` zerados, chefes da área 3 zero).

## Critérios de aceite

1. `check_orphans` sem problema na ROM construída; a linha "órfãs: 243 salas vanilla sem caminho (por área 0-7: 31 43 73 15 55 19 6 1),
   19 só nas demos; bytes só delas: $8F 20637, $83 9356, $A1 24030, $B4 4017". (validate: protege = nenhuma sala vanilla alcançável;
   falha_quando = porta, estação, save, novo jogo ou fim da fragata leva a sala vanilla, demo muda, dado compartilhado novo ou
   sobrescrito; não_prova = a SRAM de outra ROM, código que pule para sala por ponteiro fixo.)
2. Mutações (scratchpad `s11/mutate.py`, ROM em memória; `s11/proj_m`, cópia do projeto): cada uma pega pela checagem nova (abaixo).
3. `vanilla_door_bits`/`vanilla_item_bits` sobre 262 salas; mutação com porta vermelha bit `$B0` na `$A201` (fora do `sm_rooms.json`)
   pega por `check_gates`.
4. Teste `atracao_e_novo_jogo` passa; com a tabela de demo mudada (cena 1 → sala da cena 2) falha em `$7E079B`.
5. ROM igual: sha1 `3919c3c7…64ff` em dois builds; linha do Tallon igual (44 salas, 20 itens em 7 rodadas); testes todos passando.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_orphans` (entradas, salas alcançadas, demos, dados compartilhados) | +1 checagem |
| validate.py | bits vanilla pelos bytes (262 salas) | 2 funções trocadas |
| run_tests.py (emulador) | `atracao_e_novo_jogo` | +1 |
| scratchpad | 13 mutações em memória + 1 na cópia do projeto + 1 do teste | 15 |

## Riscos e reversão

Nada muda na ROM. A checagem nova pode acusar falso positivo se uma etapa futura usar de propósito um dado vanilla (pôr na
`VANILLA_SHARED` com o motivo) ou mudar as demos (decisão do usuário: atualizar `DEMO_SCENES`). Reverter: tirar `roomgraph.py`,
`check_orphans`/`entry_stations`/`DEMO_SCENES`/`VANILLA_SHARED` do validador, as constantes `FREE_*` do build e o teste.

## Fora de escopo

- Recuperar espaço das órfãs (B6): só documentado; quem precisar (Chozo) recupera com a lista e os riscos da nota abaixo.
- Apagar ou trocar as demos de atração, a tela-título "SUPER METROID" ou o texto "METROID 3" da abertura (B2: decisão do usuário).
- Recusar save de SRAM vanilla (B7).

## Precisa de decisão do usuário

1. **Demos de atração** (B2): com o título parado, o jogo mostra 3 conjuntos de demos do Super Metroid (19 salas da Crateria, Brinstar,
   Norfair, Wrecked Ship), com o minimapa da nossa área por cima. Opções: (a) deixar como está; (b) desligar as demos (o título fica
   parado ou repete a abertura); (c) gravar demos novas na fragata/Tallon (precisa gravar a entrada do controle; mais trabalho). Se mudar,
   `DEMO_SCENES` muda junto e as 19 salas viram órfãs (mais espaço livre para recuperar).
2. **Tela-título e abertura** continuam as do Super Metroid ("SUPER METROID", "METROID 3"): fora desta etapa.

## Nota para a etapa da Chozo Ruins

- **Prime**: 64 salas, 136 portas (`research/prime_worlds.json`). As 72 salas do jogo gastaram 3932 bytes de `$8F` (~55 por sala:
  cabeçalho e estado 39, listas de porta e de PLM, mais fundos e código), 12 por porta em `$83`, ~16 por inimigo em `$A1`, ~20 por set em `$B4`.
- **Cabe sem mexer em nada**: `$83` (19294 livres, ~1700 necessários), `$A1` (3851), `$B4` (2488), `$84` (3225), `$A0` (1985), níveis e
  gráficos (~500 KB em cada alocador expandido), SRAM do mapa (876 bytes livres; a lista da área no lugar vanilla aceita até 80 bytes,
  `mapsave.LIST_ROOM`).
- **Não cabe: `$8F`** (1781 livres para ~3500). Caminho sugerido, nesta ordem de segurança: (1) pôr só **estados, listas de PLM e de
  portas** (nunca cabeçalhos: o código compara `room_ptr` com `$9804`, `$96BA`, `$A66A`, `$B32E`, `$B457`, `$CEFB`, `$DD58`, `$DEDE`,
  `sm_88.c:209–354`, `sm_91.c:1203`) num pedaço órfão de área sem demo, p.ex. `$8F:D4EF–DDBD` (2255 bytes, Maridia/Tourian) — o
  `Allocator` hoje é uma faixa só: precisaria de uma segunda faixa; (2) antes, rodar `check_orphans` (as faixas recuperadas não podem
  cruzar `DEMO_SCENES` nem `VANILLA_SHARED`, que a checagem confere byte a byte) e conferir que nenhum código vanilla lê a faixa por
  endereço fixo.
- **Área da Chozo**: 1 (Brinstar), 2 (Norfair) ou 4 (Maridia) — a 5 está reservada para a Impact Crater (`mapsave.py`), 6 (Ceres) e 7
  (debug) têm código especial. Cuidados por área no código vanilla: 2 = Norfair (Ridley, projéteis e calor por área: `sm_a6.c`,
  `sm_86.c:1163`), 4 = o mapa de pausa desloca 24 px (`sm_82.c:1811`), 1 = um caso de raio X (`sm_91.c:1065`). As tabelas de mapa de
  pausa, nome, ícones e estações da área escolhida são reescritas no lugar como as das áreas 0 e 3 (`build.VANILLA_PAUSE` ganha a
  entrada dela). Estações por área: 1 = 19, 2 = 23, 4 = 20.
- **Tilesets reaproveitáveis** (nenhuma sala nossa nem demo usa): **01** (nenhuma sala vanilla usa), 03 (Old Tourian), 08, 0C (Maridia
  rochosa), 0D/0E (Tourian), 16–19 (salas de mapa/save/recarga), 1B, 1C. Para o visual Chozo, os candidatos são 06/07 (Brinstar) e
  09/0A (Norfair), usados só por órfãs e por demos: **recolorir um deles muda as demos** (B2). Recolor é global por tileset
  (`build.py`, passo 3).

## Desvios (preenchido na implementação)

- **Uma spec só, sem filhas**: a auditoria não achou risco que pedisse mudar a ROM; o trabalho coube em validador + teste + documentação.
- **Recuperação de espaço**: não feita (fora de escopo pelo pedido: documentar antes de liberar). A nota da Chozo diz quanto e onde.
- **B7 (SRAM vanilla)**: conclusão pelo código (`LoadFromSram` lê área e estação da SRAM), não rodada no emulador.
- **Contagem "órfãs" por área conta salas, os bytes por banco contam cada byte uma vez** (salas da mesma área dividem listas).
- O teste novo usa as horas medidas das demos (quadros 3600–7800); o emulador é determinístico, mas mudar a abertura ou o título muda
  as horas.
- Verificação final (26/10/2026, pasta real): `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas`, linha do Tallon
  igual ("… 44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas …") e a nova "órfãs: 243 salas vanilla sem caminho
  (por área 0-7: 31 43 73 15 55 19 6 1), 19 só nas demos; bytes só delas: $8F 20637, $83 9356, $A1 24030, $B4 4017";
  `python3 -I tools/build.py` duas vezes → sha1 `3919c3c73d46afc45ffd4eb51083daebbe8264ff` nas duas (igual ao de antes);
  `python3 -I tests/run_tests.py` → **53/53** (52 + `atracao_e_novo_jogo`; nenhuma expectativa antiga mudou).
- Mutações (`s11/mutate.out`): todas pegas — M1 porta do Tallon → `$92FD`; M2 save da Savestation → estação 2 (sem porta); M3 estação
  0/1 com porta vanilla; M4 novo jogo na estação 3/`$10`; M5 fim da fragata na 0/`$10`; M6 tabela de demo; M7 PLMs da sala de demo
  `$91F8`; M8 população vanilla fora da lista; M9 lista sem o fundo `$E117`; M10 entrada sem uso; M11 população do Phantoon
  sobrescrita; M12 sala nossa sem porta de entrada; M13 porta vermelha bit `$B0` na `$A201` (`check_gates`). Na cópia do projeto
  (`s11/proj_m`, save do Tallon +2 no `build.py`): "ERRO órfãs: área 0, estação $03 (save em tallon_savestation) sem porta". Teste com a
  demo mudada: `FAIL 7E079B = 9D9C, esperado 9F11`.
