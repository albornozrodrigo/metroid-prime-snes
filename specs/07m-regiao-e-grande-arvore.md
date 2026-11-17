# 07m — Região E do Tallon (Grande Árvore), com Gully e Alcove

Estado: verificada (23/10/2026: validate 72/148/0 com "ABCDE, 44 salas construídas … alcançáveis agora: 15"; .ips sha1 `27828fae…bebe3` igual em dois builds; 39/39 testes)
Esforço estimado: 2,5 dias (pesquisa Prime + decisões 0,5 d; desenhos 0,75 d; validador + mutações 0,5 d;
testes no emulador 0,5 d; verificação/documentos 0,25 d)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (linha 07m: "Região E (Grande Árvore), 8 salas";
decisões 4, 5, 7 e 8; definição de pronto: "As 44 salas do Tallon existem")

## Contexto

Depois da 07l o Tallon tem 34 salas na ROM (regiões A–D). Faltam a região E — Great Tree Hall, Great Tree
Chamber, Transport Tunnel D e E, Life Grove Tunnel, Life Grove e as duas salas de transporte (Chozo Ruins
South e Phazon Mines East, desenhadas na 07j) — e, na região A, Gully e Alcove, que a 07k deixou de fora
por pedirem Bombas e Space Jump. Esta spec fecha o épico: **as 44 salas na ROM**, com as travas fiéis do
Prime mapeadas nos mecanismos que já existem (porta vermelha, cinza "nunca abre", borda de Space Jump,
geometria), o X-Ray, os dois mísseis da região E e o Space Jump da Alcove nos lugares do Prime, e os
inimigos da camada 0. Como na 07l, quase nada disso é alcançável a pé agora (fiel): os testes entram por
teleporte de porta.

## Estado atual (verificado)

- `tools/tallon/rooms.py`: `ACTIVE_REGIONS = {A, B, C, D}`; `ACTIVE_ROOMS` lista 34 salas (sem Gully e
  Alcove). Tabela da 07d: tamanhos pelo `screens()` — Great Tree Hall 3x4, Great Tree Chamber 3x1, Tunnel D
  2x1, Life Grove Tunnel 2x1, Tunnel E 3x1, Life Grove 5x3, transportes 1x2; Gully 3x1, Alcove 5x2. `LINKS`:
  Hydro Access B2 ↔ Great Tree Hall T0; GTH R0 Tunnel D, R1 Great Tree Chamber, R2 Tunnel E, R3 Life Grove
  Tunnel; Tunnel D R0 ↔ Chozo South L1; LGT R0 ↔ Life Grove L0; Tunnel E R0 ↔ Mines East L1; Landing Site L0
  ↔ Alcove R1, L1 ↔ Gully R0; Gully B0 ↔ Tallon Canyon T3. `TIERS` 0–5 (5 = grapple, X-Ray, plasma:
  Arbor Chamber).
- `tools/tallon/layouts.py`: Chozo South e Mines East desenhadas (`low_transport`, 07j); a B2 da Hydro
  Access "é rocha até a 07m" (os degraus da R0 descem por cima dela, `floor_from` até o fundo); a parede
  oeste da Landing Site é rocha maciça atrás das L0/L1; a T3 da Tallon Canyon fica sob rocha.
- `tools/tallon/items.py`: linhas sem lugar: 1 Alcove (Space Jump, bit `$A1`), 10 Great Tree Chamber
  (míssil, `$AA`), 11 Life Grove Tunnel (míssil, `$AB`), 12 Life Grove (X-Ray, `$AC`).
- `tools/tallon/enemies.py` (07i): "Seedling = Cacatac **andando**… decidir os números na 07m".
- Antes de mexer: `validate` 62 salas/126 portas/0 problemas ("ABCD, 34 salas construídas, 2 desenhadas
  fora do build, alcançáveis agora: 15"); `.ips` sha1 `8edc24a4…6a73`; 37/37 testes. Espaço livre: `$8F`
  a partir de `$8F:F6C3` (2365), `$83` de `$83:B39A`, `$A1` de `$A1:F009`, `$B4` de `$B4:F614`; nível das
  salas no banco `$E0` até `$E0:EE0E` (4594 bytes antes da Parasite Queen, posta em `$E1:8000` com
  `put_in_bank`).

### A região E, Gully e Alcove no Prime (dados de `research/prime_fs`)

Lidos nesta pesquisa com o retro-data-structures (`tools/venv`), como na 07k/07l: tipos por camada; nome e
posição dos objetos que a biblioteca não lê saem dos bytes crus (nome = 1º texto, posição = 3 floats depois
dele, posição local pela transformação inversa da sala); porta = doca mais perto (≤ 1 m para os escudos).
Escudo comum = `Actor_DoorShield`; **porta de cor** = tem também `Actor_DoorShield_Key` (a cor não sai dos
nomes: conhecimento). Alturas = z das docas (m).

| Sala | Docas (z) | Travas nas portas (dados) | Água | Inimigos camada 0 | Item (posição local) |
|------|-----------|---------------------------|------|-------------------|----------------------|
| P36 Great Tree Hall | Hydro 3,4; Tunnel E 22,6; Tunnel D 57,5; GTC 73,2; LGT 90,4 | **Key** nas docas de Tunnel D, Tunnel E e LGT; comuns na Hydro e na GTC. Dentro: 57 `SpiderBallWaypoint`, "POI_Spiderball Track"/"Ice Spidertrack" junto da doca do LGT, `BallTrigger`, camadas "Gate Solved/Unsolved" | "Crashed Water" no fundo (z ~7) | Seedling 4, Blood Flower 2, Jelly Zap 2 | — |
| P37 Great Tree Chamber | GTH 4,6 | comum | — | — | míssil (0,3; 1,2; 2,2): no chão, no meio |
| P38 Transport Tunnel D | 2,5 / 2,5 | **Key** nas duas | — | Seedling 2 | — |
| P39 Life Grove Tunnel | GTH 1,4; Life Grove 1,5 | **Key** na do GTH; a do Life Grove sem escudo. Camada "remove this boulder when destroyed", "Player Hint_wallpuzzle" | — | — | míssil (−0,9; −5,5; 1,6): no meio, na altura das portas |
| P40 Transport Tunnel E | 9,0 / 14,5 | **Key** nas duas | — | Seedling 3 | — |
| P41 Chozo Ruins South, P43 Phazon Mines East | — | **Key** | — | — | — |
| P42 Life Grove | LGT 21,6 | (uma porta) | "normal water" no fundo (z ~0) | — (camada 1 "1st Pass": Chozo Ghost 3, Seedling 1; camada 2: Spank Weed 8) | X-Ray (18,3; −0,4; 8,7): 13 m abaixo e 54 m da porta, **dentro de 5 "Platform - Destroyable Wall"** com "Power Bomb Scan Hint"; Artifact of Chozo (fora) |
| P1 Gully | Canyon 9,2; Landing Site 2,5 | comuns. Na **Tallon Canyon**, junto da doca do Gully: 2 "Breakable Block" + "RumbleEffect_bomb_walls" | sim (poça) | **Parasite 3** | — |
| P4 Alcove | Landing Site 11,1 | comum | sim (poça) | — | Space Jump (−1,1; 0,2; 1,8): no chão, 9 m abaixo e 37 m da porta |

Landing Site: docas do Gully e da Alcove a z 17,5, a do Canyon Cavern a 10,0, a nave a ~8–9,5. Nenhum
`Metaree` na região E (os 4 Metaree Alpha do épico são da camada 1 da Temple Lobby).

Conhecimento do Prime (não sai dos dados, marcado como tal): as portas "Key" da região E são de **gelo**
(a da Life Grove Tunnel, **incerto**); a Gully se abre com **Bombas** (os blocos quebráveis); da Landing
Site, a borda das portas do Gully e da Alcove **não se alcança do chão sem Space Jump** (o caminho do Prime
é subir pela Gully; **incerto**); a porta da Great Tree Chamber, 70 m acima da Hydro, pede **Space Jump**
(**incerto**); o caminho até o Life Grove pede **Spider Ball** (a trilha da árvore), **Boost Ball** e
**Power Bombs** (a pedra e o quebra-cabeça do túnel, as paredes do X-Ray). No Prime a região E se chega
pelos elevadores (Chozo South/Mines, que aqui não funcionam) ou pela Hydro Access (Gravity Suit).

## Mudança proposta

### 1. Travas e fases (`tools/tallon/rooms.py`)

- Itens novos de trava: `bombs` (tampa **cinza** "nunca abre", como gelo/plasma), `spider`, `boost`,
  `power_bomb` (sem tampa nem borda: só o passeio por fases os pede, como grapple/X-Ray na Arbor).
- `GATES` novos:

  | Ligação | Itens | Fonte | SM |
  |---------|-------|-------|----|
  | Tallon Canyon ↔ Gully | Bombas | blocos quebráveis: dados; Bombas: conhecimento | **cinza** do lado da Canyon (porta de teto T3) |
  | Landing Site ↔ Gully, Landing Site ↔ Alcove | Space Jump | altura das docas: dados; "sem SJ do chão": conhecimento (incerto) | **borda** do lado da Landing Site: câmara no alto do penhasco oeste, que une L0 e L1 |
  | Hydro Access ↔ Great Tree Hall | — | dados | porta de chão/teto comum (era rocha) |
  | GTH ↔ Tunnel D, GTH ↔ Tunnel E, Tunnel D ↔ Chozo South, Tunnel E ↔ Mines East | gelo | Key nas duas docas: dados; cor: conhecimento | **cinza** dos dois lados |
  | GTH ↔ Great Tree Chamber | Space Jump | altura: dados; SJ: conhecimento (incerto) | **borda** do lado do GTH |
  | GTH ↔ Life Grove Tunnel | gelo, Spider Ball, Boost Ball, Power Bombs | Key, trilha, pedra, paredes: dados; itens: conhecimento | **cinza** dos dois lados |

- **Passeio por fases**: os itens de movimento de uma trava (Space Jump, Gravity Suit) passam a ser
  decididos só pela geometria (o passeio da sala já anda com o pulo da fase); os outros itens continuam
  pedidos nos dois sentidos. Antes a ligação pedia o Space Jump dos dois lados, e a Alcove — que guarda o
  Space Jump e se alcança pela borda vindo da Gully — só ficaria alcançável depois do próprio Space Jump.
  Nenhuma fase das salas de A–D muda com isso (conferido pelo validador).
- `TIERS`: a fase 1 vira **"+ mísseis, Morph Ball, Bombas"** (no Prime Morph Ball e Bombas vêm das Chozo
  Ruins junto dos mísseis, antes do Space Jump); entra a fase **5 "+ Spider Ball, Boost Ball, Power
  Bombs"**; a antiga 5 vira **6** (Arbor Chamber e o míssil dela: 5 → 6).
- `FIRST_TIER`: Gully **1**, Alcove **1**; Great Tree Hall, Great Tree Chamber, Tunnel D, Tunnel E,
  Chozo South, Mines East **4** (pela Hydro Access; gelo e Space Jump já existem nessa fase); Life Grove
  Tunnel e Life Grove **5**; Arbor **6**. **Alcançáveis agora: 15** (não muda).
- Ativação: `ACTIVE_REGIONS = {A, B, C, D, E}`, `ACTIVE_ROOMS = None` (todas): **44 salas na área 0**.
- Visual pela tabela (07d): GTH, GTC, Life Grove (chuva), Gully, Alcove = superfície; túneis e transportes
  = caverna. **Água: nenhuma** (o lago do fundo do GTH, o do Life Grove e as poças de Gully/Alcove ficam
  secos, como as poças de A–C: água parcial mudaria o pulo e não está no modelo).

### 2. Desenhos (`tools/tallon/layouts.py`)

Regras de sempre (degraus de até 4, nada sem volta, toda porta de toda entrada a pé menos as bordas de
Space Jump, que ficam a mais de 7 blocos de altura ou de distância de todo lugar alcançável a pé).

- **Landing Site** (muda o penhasco oeste): câmara no alto do penhasco: a borda da L0 vai até a coluna 9,
  três degraus de 4 sobem até ela a partir do chão da L1 (linha 26), que sai por uma boca no penhasco até
  um ressalto 15 blocos acima do chão (a Samus cai para a bacia, só de ida). O resto da sala não muda.
- **Tallon Canyon** (muda o teto leste): o poço da T3 (Gully, cinza) aberto até a plataforma que
  `Canvas.door_gap` põe sob a porta de teto; a Samus sobe nela pela ponta oeste da prateleira.
- **Hydro Access** (muda o fundo leste): os degraus da R0 viram plataformas de 1 bloco, o túnel continua
  por baixo deles até um poço de 3 sobre as bordas da porta de chão B2.
- **Gully** (3x1): leito de riacho da porta de chão B0 à margem da R0 (3 acima), pedras no leito.
- **Alcove** (5x2): bacia entre penhascos; a R1 numa prateleira 2 acima do chão; o Space Jump no chão.
- **Great Tree Hall** (3x4): a Samus cai da Hydro na plataforma da T0; um piso na linha 10 vai até a R0
  (Tunnel D), com um buraco junto do tronco (a rocha a oeste); galhos em dois lances: da borda da R2
  (Tunnel E) sobem para a esquerda até o buraco; do chão do fundo (R3, Life Grove Tunnel) sobem para a
  direita até a borda da R2. A R1 (Great Tree Chamber) fica no ar livre entre o piso e a borda da R2, a
  ≥ 9 colunas de todo galho, com o piso por cima (ninguém cai nela): borda de Space Jump. No Prime a
  porta da Hydro fica no fundo, debaixo d'água; aqui o mapa da 07d a põe no teto (desvio do épico).
- **Great Tree Chamber** (3x1): beco com raízes; o míssil no chão no meio.
- **Transport Tunnel D** (2x1) e **E** (3x1): corredores de chão plano (os Seedlings andam).
- **Life Grove Tunnel** (2x1): corredor com duas pedras baixas; o míssil no meio.
- **Life Grove** (5x3, chuva): terraços de 4 descem da L0 ao chão do bosque (linha 30), dois pilares Chozo;
  a leste o leito seco do lago, dois degraus abaixo.

### 3. Itens (`tools/tallon/items.py`)

| # | Sala | Item | Bit | Lugar | Fase | Por quê |
|---|------|------|-----|-------|------|---------|
| 1 | Alcove | Space Jump | `$A1` | (40, 27), no chão | 1 | Prime: no chão, no meio |
| 10 | Great Tree Chamber | Missile Expansion | `$AA` | (24, 9), no chão no meio | 4 | Prime: idem |
| 11 | Life Grove Tunnel | Missile Expansion | `$AB` | (16, 9), no meio | 5 | Prime: no meio, na altura das portas |
| 12 | Life Grove | X-Ray Scope (`$EF0F`) | `$AC` | (40, 29), no chão do bosque | 5 | Prime: 13 m abaixo e 54 m da porta; as paredes de Power Bomb à volta dele ficam na trava do caminho |
| 4 | Root Cave (07h) | Missile Expansion | `$A4` | igual | **2 → 1** | o Space Jump da Alcove vem na fase 1 |
| 6 | Arbor (07h) | Missile Expansion | `$A6` | igual | **5 → 6** | a fase nova 5 |

Artefato de Chozo: fora (07h). Com isso os 13 itens SM do Tallon estão na ROM.

### 4. Inimigos (`tools/tallon/enemies.py`, `tools/frigate/enemies.py`)

- **Seedling → Cacatac andando** (espécie nova `seedling`: `$A0:CFFF`, parâmetros das colocações vanilla
  da Maridia `$8F:9FBA`: p2 = `$0301` = velocidade 3 (3/16 px por quadro), alcance 64 px para cada lado
  (`$A2:9F36`); p1 = 0 = em pé, como a Blood Flower). Mesma espécie da Blood Flower: **uma entrada só no
  enemy set** (paleta 7 das duas). `Species.patrol` = 64.
- Por sala (camada 0; no máximo 1 por tela):

  | Sala | Fase | Inimigos | Onde |
  |------|------|----------|------|
  | Gully | 1 | 3 Parasite (Zeela) | no leito (12,13), (25,13), (36,13) |
  | Great Tree Hall | 4 | 4 Seedling, 2 Blood Flower | Seedlings andando no chão do fundo (8,62), (18,62), (33,62) e no piso de cima (28,10); Blood Flowers nas pontas do piso (2,10), (38,10) |
  | Transport Tunnel D | 4 | 2 Seedling | (11,10), (20,10) |
  | Transport Tunnel E | 4 | 3 Seedling | (11,10), (23,10), (36,10) |

- Jelly Zap (2 no GTH): **fora** — vivem no lago do fundo do GTH, que fica seco. Chozo Ghosts, o Seedling
  e os Spank Weeds do Life Grove: camadas de evento, fora. Fase 4+: a regra de justiça da fase 0 não vale
  (a Gully é fase 1; o Zeela morre com 2 tiros de qualquer jeito).

### 5. Validador (`tools/validate.py`)

- `tallon_tiers`: o passeio pede os itens da trava **menos os de movimento** (geometria).
- Regra da borda de Space Jump: inalcançável a pé de toda entrada que **não esteja numa borda** (antes:
  de toda entrada menos a da própria porta) — a câmara da Landing Site tem duas portas na mesma borda.
- `foot_grid`: a tampa de porta de **teto** não vira sólida (a Samus chega a ela pulando contra a tampa;
  a de porta lateral/de chão continua sólida).
- `check_enemies`: inimigo que anda (`Species.patrol`) tem ar para a caixa inteira e chão sob o centro
  **em todo o caminho**, e o caminho todo longe das portas.
- `check_enemy_sets` / `enemy_set`: espécies agrupadas pelo ponteiro (`set_species`); duas espécies do
  projeto com o mesmo ponteiro têm de ter a mesma paleta; VRAM contada uma vez.
- Os existentes cobrem o resto: `check_tallon_tiers` (fases das 44 salas e dos 13 itens), `check_gates`
  (as tampas cinza, a de teto incluída), `check_tallon_items` (X-Ray `$EF0F`, Space Jump `$EF1B` na ROM),
  `check_tallon_enemies` (contas da camada 0), `check_door_push`, `check_pause_maps`.

### 6. Testes no emulador (`tests/run_tests.py`)

- `tallon_grande_arvore`: estação 1 (Savestation), com a Gravity Suit; por teleporte de porta a 1ª cadeia
  da fragata afundada até a Hydro Access, depois Hydro → GTH (cai na plataforma sob a T0: y `$004B`) → GTC
  (pega o míssil: 0 → 5) → GTH → Tunnel D → Chozo South → Tunnel D → GTH → Tunnel E → Mines East → Tunnel E
  → GTH → Life Grove Tunnel → Life Grove: cada sala carrega, seca (FX 0, ou chuva `$0A` no Life Grove),
  inimigos vivos na tabela da WRAM; **pega o X-Ray** (bit `$AC`, `$09A4` bit `$8000`).
- `tallon_gully_alcove`: da nave, teleporte para a Alcove, **pega o Space Jump** (bit `$A1`, `$09A4` bit
  `$0200`); volta à borda da Landing Site; Gully (3 Zeelas vivos); desce pela porta de chão para a Tallon
  Canyon (cai na plataforma sob a T3) e pula 4 vezes contra a tampa cinza: continua na Canyon.
- Fotos: `specs/img/07m-sala-*.png` (prévia, `preview_rooms.py --salas-07m`) e `specs/img/07m-emulador-*.png`.

### 7. Espaço

Medir no build (critério 3). Estimativa: `$8F` ~550 bytes (10 salas + listas de PLM), `$83` ~260 (24
entradas de porta), `$A1` ~240, `$B4` ~50; nível ~4,5 KB comprimidos no `$E0` — cabe nos 4594 bytes antes
da Parasite Queen, com pouca folga. Se não couber, o `LinearAllocator` atravessa para o `$E1` (nível pode
cruzar banco) e a Parasite Queen (`put_in_bank`) vai para o banco seguinte: anotar.

## Critérios de aceite

1. `python3 -I tools/validate.py` → **0 problemas**, "regiões ativas: ABCDE, 44 salas construídas,
   alcançáveis agora: 15" (sem "desenhadas fora do build") e **"72 salas, 148 portas"**. (protege = travas,
   bordas, fases, itens, inimigos andando, sets; falha_quando = mutações do critério 2; não_prova = o jogo)
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) degraus do chão até o
   ressalto da Landing Site; (b) Gully sem a trava das Bombas; (c) galho a 6 colunas da borda da GTC;
   (d) Seedling andando sobre o buraco do piso; (e) Seedling com paleta diferente da Blood Flower; (f) Life
   Grove Tunnel sem Spider/Boost/Power Bomb; (g) X-Ray dentro do pilar; (h) sem o poço da B2 da Hydro;
   (i) GTC sem a trava de Space Jump; (j) Space Jump declarado na fase 2; (k) passeio pedindo os itens de
   movimento (regra antiga); (l) regra antiga da borda; (m) tampa de porta de teto sólida.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds; espaço por banco anotado.
4. `tallon_grande_arvore` passa (protege = as 8 salas de E carregam pelas portas, secas, inimigos vivos,
   míssil e X-Ray pegos; não_prova = chegar a pé, que o jogo não permite ainda).
5. `tallon_gully_alcove` passa (protege = Alcove, borda da Landing Site, Gully, tampa cinza da Gully na
   Canyon, Space Jump pego).
6. `python3 -I tests/run_tests.py` → **39/39** (os 37 de antes, sem mudar expectativa, + 2).
7. Fotos `specs/img/07m-*.png` olhadas: tileset, paletas, portas e inimigos sem lixo.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | inimigo andando; espécie repetida no set; regra da borda; passeio por geometria; tampa de teto | +2 checagens, 3 regras alteradas |
| mutação à mão | (a)–(m) | 13 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `tallon_grande_arvore`, `tallon_gully_alcove` | +2 |
| imagem | 13 prévias + fotos do emulador | ~25 |

## Riscos e reversão

- Bordas de Space Jump (câmara da Landing Site, R1 do GTH) e a borda da Gravity Suit são geometria: o
  modelo só supõe o pulo parado (sem wall-jump, sem desvio no ar). No GTH o piso sobre a R1 impede cair
  nela; na Landing Site o ressalto fica 15 blocos acima do chão.
- Cores das portas (gelo) e a necessidade do Space Jump nas bordas são conhecimento do Prime (incertos
  marcados na tabela).
- A ordem das portas no GTH segue o mapa da 07d, não as alturas do Prime (a Hydro em cima, o LGT embaixo).
- Banco `$E0` quase cheio depois desta spec (ver Desvios): a próxima sala nova cruza para o `$E1` e empurra
  a Parasite Queen um banco (automático).
- Reversão: `ACTIVE_REGIONS`/`ACTIVE_ROOMS` como antes, `GATES`/`TIERS`/`FIRST_TIER`/itens/inimigos como
  antes, desenhos de Landing Site/Canyon/Hydro como antes, reconstruir.

## Fora de escopo

- Bombas, Spider/Boost Ball, Power Bombs, gelo como itens; portas cinza que abrem; elevadores funcionando.
- Água parcial (lagos do GTH e do Life Grove, poças de Gully/Alcove); Jelly Zaps; camadas de evento (Chozo
  Ghosts, Spank Weeds); o Artifact of Chozo; reordenar o mapa da 07d.
- Rota a pé do jogo até a região E ou até a Gully (o jogo não permite: travas fiéis).

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (tabela inteira, regiões ativas: ABCDE, 44 salas construídas,
  alcançáveis agora: 15): 44 salas, 44 ligações, 251 telas, mapa 47/80 bytes de SRAM …` e `72 salas, 148
  portas, 0 problemas`.
- Mutações (na memória, `LAYOUTS`/`GATES`/`ITEMS`/`ENEMIES`/`SPECIES` e o próprio `validate.py` trocados e
  desfeitos; sem mutação: 0 problemas): (a) degraus do chão até o ressalto → 10 ("porta 0 (L1 -> tallon_gully)
  tem trava ['space_jump'] mas é alcançável a pé a partir da entrada porta 2 (R2)", e a L0); (b) Gully sem a
  trava das Bombas → 4 (Gully, Alcove, Space Jump e o míssil da Root Cave na fase 0); (c) galho a 6 colunas da
  borda da GTC → 4 (portas inalcançáveis: o galho corta o lance de cima); (d) Seedling sobre o buraco → 2
  ("não tem chão embaixo em todo o caminho (colunas 15-23)" + ROM); (e) Seedling com paleta 3 → 3 ("espécie
  $CFFF com duas paletas no mesmo enemy set" + ROM); (f) Life Grove Tunnel só com gelo → 4 (LGT, Life Grove e
  os 2 itens na fase 4); (g) X-Ray no pilar → 3; (h) sem o poço da B2 → 13; (i) GTC sem a trava de Space Jump
  → 4 (R1 inalcançável de toda entrada); (j) Space Jump declarado na fase 2 → 1; (k) passeio pedindo os itens
  de movimento (regra da 07k) → 3 (Alcove, Space Jump e o míssil da Root Cave na fase 2); (l) regra da borda
  da 07k → 2 (L0 e L1 alcançáveis uma da outra); (m) tampa de porta de teto sólida → 8 (T3 da Canyon
  inalcançável). Roteiro: `scratchpad/s07m/bin/mutations.py` (fora do projeto).
- `python3 -I tools/build.py` duas vezes → sha1 `27828fae3277b076cc5611dbdaf56f5cdb3bebe3` nas duas. Espaço
  usado: `$8F` 544 bytes (`$8F:F6C3` → `$8F:F8E3`; sobram 1821), `$83` 264 (→ `$83:B4A2`), `$A1` 236
  (→ `$A1:F0F5`), `$B4` 52 (→ `$B4:F648`); nível das 10 salas novas + Landing Site/Canyon/Hydro refeitas:
  4498 bytes no `$E0` (`$E0:EE0E` → `$E0:FFA0`): **sobram 96 bytes** antes de `$E1:8000`, onde a Parasite
  Queen continua (não precisou mover nada). A próxima sala nova cruza para o `$E1` (o `LinearAllocator`
  deixa o nível cruzar banco) e a Parasite Queen vai para o `$E2:8000` (`put_in_bank`): automático, mas não
  testado nesta spec. `$A0`, `$A2`, `$A6`, `$82` iguais; lista do mapa na SRAM igual (47 bytes, área 0).
- `python3 -I tests/run_tests.py` → **39/39** (os 37 de antes + `tallon_grande_arvore` e `tallon_gully_alcove`).
- Imagens olhadas: `specs/img/07m-sala-*.png` (13 prévias) e `specs/img/07m-emulador-*.png` (16: as 8 salas de
  E, o míssil e o X-Ray pegos, o HUD com o X-Ray, Alcove e o Space Jump, a câmara da Landing Site, a Gully com
  os Zeelas e a tampa cinza da Gully vista da plataforma da Canyon). Tileset, paletas, portas cinza, Seedlings
  (Cacatac verde atirando agulhas) sem lixo.

Mudanças de expectativa dos testes existentes: **nenhuma** (os 37 passam sem mudança; as rotas cegas pela
Tallon Canyon não sentiram o teto novo da T3).

Desvios e detalhes:

- **Ordem das portas do Great Tree Hall**: segue o mapa da 07d (Hydro no teto, Life Grove Tunnel embaixo),
  não as alturas do Prime (Hydro no fundo debaixo d'água, Life Grove Tunnel no alto). Reordenar o mapa mexeria
  na lista do mapa na SRAM e no layout de E inteiro: fora de escopo.
- **Hydro Access**: os degraus da R0 viraram plataformas de 1 bloco para o túnel passar por baixo até a B2
  (era rocha maciça). O E-tank e a prateleira não mudaram; `tallon_fragata_afundada` passa igual.
- **Teste por teleporte** (como a 07l): nenhuma rota a pé chega à região E nem à Gully. A chegada pela porta
  de teto (Hydro → GTH, Gully → Canyon) foi conferida: a Samus pousa na plataforma sob a porta (y `$004B`).
- **Inimigos andando**: o Cacatac anda ±64 px a 3/16 px por quadro (devagar); o validador confere o chão do
  caminho inteiro. Jelly Zaps fora (o lago do GTH fica seco).
- **Prévias**: `preview_rooms.py --rascunhos-tallon` não desenha mais nada (não há sala desenhada fora do build).
