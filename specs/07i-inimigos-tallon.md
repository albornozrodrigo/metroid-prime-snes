# 07i — Inimigos do Tallon

Estado: verificada (23/10/2026: validate 48/98/0; .ips sha1 `17b959e1…fcc1` igual em dois builds; 32/32 testes)
Esforço estimado: 2 dias (pesquisa Prime + ROM 0,5 d; tabela + build 0,25 d; validador + mutações 0,5 d;
testes no emulador e ajuste das rotas 0,5 d; verificação 0,25 d)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (linha 07i: "tabela acima, quantidades da camada 0
do Prime"; seção "Inimigos (proposta, refinada na 07i)")

## Contexto

O Tallon tem 20 salas na ROM (regiões A, B e C; 07g, 07k) e 6 mísseis (07h), mas nenhum inimigo: a
Samus anda sozinha. Esta spec põe os inimigos das salas **construídas** (as das regiões D e E entram com
elas, 07l/07m), com as quantidades da camada 0 do Prime, cada inimigo do Prime trocado por uma espécie
que o SM já tem. A Samus chega com 99 de energia, só o Power Beam e no máximo 5–15 mísseis: o caminho
da chegada (fase 0) tem de continuar justo.

## Estado atual (verificado)

### Inimigos do Prime por sala e por camada (dados)

Lidos nesta pesquisa de `research/prime_fs` com o retro-data-structures (`tools/venv`), contando os
objetos de cada camada do script de cada sala (MREA). O tipo do objeto sai certo; o nome e a posição
não (a biblioteca não lê as propriedades desses objetos: `ValueError`), então **as posições não vêm do
Prime**: foram escolhidas pelo desenho de cada sala (abaixo). Camada 0 = "Default" (a que está ligada ao
entrar); as outras são ligadas por eventos.

| Sala (construída) | Camada 0 | Outras camadas (fora desta spec) |
|-------------------|----------|-----------------------------------|
| Landing Site | Snake Weed 2 | — |
| Canyon Cavern | **Beetle 3** | — |
| Temple Hall | Snake Weed 2 | camada 2 "2nd pass": Seedling 3 |
| Waterfall Cavern | Chubb Weed (AmbientAI) 7 | — |
| Tallon Canyon | **Parasite 4, Geemer 1, Beetle 2**, Chubb Weed 10 | — |
| Temple Security Station | — | — |
| Frigate Crash Site | — | 1 "Beetles": Beetle 3, Jelly Zap 2; 2 "Space Pirate": 3 piratas + 2 voadores; 3 "Don't load": 3 piratas; 4: 2 piratas voadores |
| Transport Tunnel A | **Parasite 2** | — |
| Root Tunnel | **Blood Flower 1**, Snake Weed 1 | — |
| Temple Lobby | — | — |
| Frigate Access Tunnel | Snake Weed 1 | — |
| Overgrown Cavern | Snake Weed 1 | — |
| Transport to Chozo Ruins West | — | — |
| Root Cave | **Blood Flower 1, Geemer 2, Parasite 3** | 1 "1st Pass Alpha Beetles": Beetle 6 |
| Artifact Temple | — | 1: Ridley |
| Transport Tunnel C | **Geemer 2, Parasite 2**, Chubb Weed 7 | — |
| Transport Tunnel B | **Parasite 4** | — |
| Arbor Chamber, Chozo East, Magmoor East | — | — |

(FishCloud, peixes/pássaros de enfeite, fora da contagem.) O dump por tipo não acha objetos dos tipos
`Metaree` nem `Turret` em nenhuma sala do Tallon (o épico listou "Metaree Alpha 4" e "Gun Turret 8"
contando por nome): fica para as specs de D/E conferirem.

### O SM (ROM `base/sm_fix.sfc`, C em `vendor/sm`)

- População (`$A1`, 16 bytes por inimigo) e enemy set (`$B4`, `{espécie, paleta}`, até 4 espécies):
  `research/sm_room_format.md` §6. O build já monta os dois a partir de `AreaDef.enemies`
  (`tools/build.py`, passo 1; `tools/frigate/enemies.py`), com o nome de 7 bytes "FRIGATE".
- VRAM de inimigos: `LoadEnemyGfxToVram` (`$82:DFD1`) e `ProcessEnemyTilesets` (`$A0:8D64`) põem os
  tiles das espécies um depois do outro a partir da palavra `$7000` (pela WRAM `$7E:7800–$97FF`):
  cabem **`$2000` bytes**; espécie com o bit 15 do tamanho vai para um lugar fixo. Na fragata os números
  do cronômetro de fuga ficam em `$7E00` (§13): lá cabem **`$1C00`**. A nave da Landing Site ocupa
  `$1200` (`$1000 + $200`): a sala dela fica sem inimigos (o build já recusa).
- Paleta: o 2º word da entrada do set escolhe a linha de sprite (`linha = valor + 8`); os sets vanilla
  usam só **1, 2, 3 e 7** (tabela de todos os estados das 250 salas vanilla, nesta pesquisa).
- Tabela de inimigos na WRAM: inimigo n em `$7E0F78 + $40·n` (espécie; `+$14` = vida; `+$0E`
  propriedades), `vendor/sm/src/enemy_types.h:3952` e `ida_types.h:111`; um inimigo morto/apagado tem a
  espécie zerada (`DetermineWhichEnemiesToProcess` `$A0:8EB6`: propriedade `$0200` → espécie = 0).
- Dano: o tiro do Power Beam tira `(20 >> 1) × (vulnerabilidade & $7F)` (C `vendor/sm/src/sm_a0.c:2771`
  e `2720`; `$FF` só congela, sem dano); a vulnerabilidade ao Power Beam é o 1º byte da tabela da espécie
  (`$B4`, cabeçalho `+$3C`; 0 = tabela padrão `$B4:EC1C`). Conferido no emulador: o Cacatac vai de 60
  para 40 com um tiro.

Espécies candidatas (cabeçalho `$A0`, lido da ROM; tiros = tiros do Power Beam para matar):

| Espécie (nome de debug) | Vida | Toque | Raio x×y | Tiles | Tiros | Usada no vanilla |
|-------------------------|------|-------|----------|-------|-------|------------------|
| ZOOMER `$DCFF` (Geemer) | 15 | 5 | 8×8 | `$600` | 1 | Crateria/Brinstar, chão: init 3, prop. `$2001`, p1 2 |
| ZEELA `$DC7F` (Zeela) | 30 | 10 | 8×8 | `$600` | 2 | Brinstar `$8F:9FBA`, chão: init 3, p2 = 2 |
| SSIDE `$D93F` (Sidehopper pequeno) | 60 | 20 | 16×13 | `$400` | 3 | Brinstar `$8F:9E52`, chão: tudo 0 |
| SIDE `$D9BF` (Sidehopper grande) | 320 | 80 | 24×20 | `$600` | 16 | Brinstar |
| SABOTEN `$CFFF` (Cacatac) | 60 | 20 | 8×8 | `$400` | 3 | Maridia; p1/p2 = 0: parado, em pé; p2 = alcance/velocidade da andada |
| SKREE `$DB7F` | 15 | 10 | 8×12 | `$400` | 1 | Crateria/Brinstar |
| MZOOMER `$DD3F` | 15 | 5 | 8×8 | `$600` | — (imune ao beam) | Wrecked Ship |
| HZOOMER `$DC3F` (Parasite da fragata) | 15 | 5 | 8×8 | `$600` | 1 | |

## Mudança proposta

### 1. Prime → SM (todas as decisões)

| Prime | SM | Por quê |
|-------|----|---------|
| Beetle | **SSIDE `$D93F`** (Sidehopper pequeno) | inimigo de chão que salta na Samus; 3 tiros, 20 por toque. **Desvio do épico** (SIDE `$D9BF`): o grande tem 320 de vida (16 tiros) e tira 80 por toque — dois toques matam a Samus de 99; injusto na chegada |
| Geemer | **ZOOMER `$DCFF`** (Geemer) | é o mesmo bicho; 1 tiro |
| Parasite ("Platform Zoomer", o Zoomer do Tallon) | **ZEELA `$DC7F`** | anda nas paredes como o do Prime; parece diferente do Geemer (os dois dividem 3 salas); 2 tiros. A fragata usa o HZOOMER para os Parasites dela: aqui não, porque o HZOOMER tem os mesmos tiles do Geemer (só muda a cor) |
| Blood Flower | **SABOTEN `$CFFF`** (Cacatac) parado | planta que fica no lugar e atira espinhos; 3 tiros |
| Seedling (fora: só camada 2 da Temple Hall; região E) | Cacatac **andando** (p2 ≠ 0) | planta que anda e atira agulhas; mesma espécie da Blood Flower, então cabe no mesmo set (Great Tree Hall tem os dois). Decidir os números na 07m |
| Metaree Alpha (não achado por tipo) | SKREE `$DB7F` | o Metaree é o Skree do Prime |
| Space Pirate, Flying Pirate (Crash Site camadas 2–4; região D) | pirata `$F653` (o da fragata) | já usado e testado |
| Wall Crawler Swarm (região D) | HZOOMER `$DC3F` (como na fragata) | |
| Jelly Zap, Drone, Gun Turret (região D/E; Crash Site camada 1) | a decidir na 07l/07m | pedem água/inimigos voadores; nenhum na camada 0 das salas construídas |
| Chubb Weed (AmbientAI), Snake Weed, Spank Weed | **fora** | são armadilhas/plantas de enfeite no Prime (explodem ou mordem ao tocar), não inimigos que se mata; o SM não tem nada parecido sem virar inimigo de verdade |
| FishCloud | fora | enfeite |
| Chozo Ghost, Ridley | fora do épico | |

Regras de quantidade: a da camada 0 do Prime, cortada para **no máximo 1 inimigo por tela** da sala do SM
(o Prime põe mais numa sala 3D; mesma ideia da fragata). Corte em 2 salas: Canyon Cavern 3 → 2 Beetles,
Transport Tunnel B 4 → 3 Parasites. Camadas de evento (1st pass, 2nd pass) ficam fora: pedem estados de
sala por evento (spec própria).

### 2. Espécies (`tools/frigate/enemies.py`, `SPECIES`)

Quatro entradas novas, com os parâmetros copiados de colocações vanilla no chão (a tabela acima):
`geemer` (`$DCFF`, init 3, prop. `$2001`, p1 2, paleta **1**), `zoomer` (`$DC7F`, init 3, `$2001`, p1 1,
p2 2, paleta **2**), `beetle` (`$D93F`, tudo 0, altura 13, paleta **3**), `blood_flower` (`$CFFF`, tudo 0,
paleta **7**). Cada espécie tem a sua linha de paleta: qualquer mistura cabe numa sala. `enemy_set` ganha
o nome de 7 bytes como argumento (`build.enemy_set_name`: "FRIGATE", "TALLON "); a fragata sai igual.

### 3. Por sala (`tools/tallon/enemies.py`, novo; `areas.TALLON.enemies`)

Posição = (coluna, linha do bloco sólido em que pisa).

| Sala | Fase | Inimigos (SM) | Onde | VRAM |
|------|------|---------------|------|------|
| Canyon Cavern | 0 | 2 Beetle | no rebaixo do meio do chão (13,12), (19,12) | `$400` |
| Tallon Canyon | 0 | 4 Parasite, 1 Geemer, 2 Beetle | Parasites na prateleira de musgo solta (23,20) e nos terraços (47,14), (37,22), (29,30); Geemer num terraço (42,18), longe da subida das plataformas da porta do Root Tunnel; Beetles no fundo do cânion (20,38), (24,34) | `$1000` |
| Transport Tunnel A | 0 | 2 Parasite | no bloco do meio (14,8) e no chão (9,10) | `$600` |
| Root Tunnel | 0 | 1 Blood Flower | no chão, no meio (20,10) | `$400` |
| Root Cave | 0 | 1 Blood Flower, 2 Geemer, 3 Parasite | Blood Flower no fosso (22,60); no chão de baixo: Geemers (9,58), (35,58), Parasites (16,58), (30,58), (40,58) | `$1000` |
| Transport Tunnel B | 0 | 3 Parasite | (8,10), (27,8), (38,10) | `$600` |
| Transport Tunnel C | 3 | 2 Parasite, 2 Geemer | Parasites nas ilhas soltas (15,30), (31,22); Geemers no chão (14,58), (41,50) | `$C00` |
| as outras 13 | — | nenhum (o Prime não tem na camada 0, ou só armadilhas) | | |

Total: 27 inimigos em 7 salas. Landing Site sem inimigos (a nave usa a VRAM; o Prime só tem Snake Weed).

### 4. Build

Nada novo além do nome do set: o passo 1 do `build.py` já põe população em `$A1` e set em `$B4` para
toda sala com `area.enemies`. Espaço: `$A1` +421 bytes (`$A1:EDFB–$A1:EF9F`), `$B4` +111 bytes
(`$B4:F57E–$B4:F5EC`); `$8F` e os outros bancos não mudam.

### 5. Validador (`tools/validate.py`)

- `check_enemies` (toda área): a **caixa inteira** do inimigo (raios lidos do cabeçalho da espécie na
  ROM, não só a coluna do meio) fica dentro da sala ("fica fora da sala") e no ar ("nasce dentro da
  parede"); chão embaixo; longe das portas (como antes).
- `check_enemy_sets` (toda área): no máximo 4 espécies; uma paleta por espécie, entre 1, 2, 3, 7; tiles
  sem lugar fixo e somados ≤ `$2000` (≤ `$1C00` na área do cronômetro, a fragata); a altura de
  `Species` = raio y do cabeçalho; nenhum inimigo na sala da nave.
- `check_enemies_in_rom` (ROM construída): todo estado de toda sala com inimigos aponta para a população
  e o set da tabela (pega ROM velha e build quebrado).
- `check_tallon_enemies`: contra `PRIME_LAYER0` — cada inimigo do Prime com substituto está lá (≥ 1,
  ≤ a conta do Prime), nada que o Prime não tenha, ≤ 1 por tela, todo tipo da camada 0 tem decisão em
  `STAND_IN`; e **nas salas da fase 0** (`FIRST_TIER` 0) toda espécie morre com até 5 tiros do Power Beam
  e tira no máximo 20 por toque (lido da ROM). "Prender a Samus" não tem checagem geral: as espécies
  escolhidas não agarram nem fecham passagem (nenhum Beetom/Kago/Ripper), e ficam a ≥ 5 blocos das portas.

### 6. Testes no emulador (`tests/run_tests.py`)

- `tallon_inimigos_vivos`: pouso; na Landing Site o inimigo 0 é a nave; atravessa as portas (como o
  `inimigos_nascem_nas_salas` da fragata: teleporte na frente da porta) Canyon Cavern → Tallon Canyon →
  Transport Tunnel A → Tallon Canyon → Root Tunnel; em cada sala, cada inimigo da tabela no seu lugar da
  tabela da WRAM com a vida cheia da espécie e nada depois; fotos (Beetle, Parasite, Geemer, Blood Flower).
- `tallon_inimigos_atras_da_porta_vermelha`: pega o míssil do lago, abre a porta vermelha do Root Tunnel
  com mísseis, confere Root Cave (as 3 espécies juntas, paletas 7/1/2) e Transport Tunnel B; fotos.
- `tallon_power_beam_mata_inimigo`: no Root Tunnel, agachada a 5 blocos, o Power Beam tira 20 do
  Cacatac (60 → 40) e o 3º tiro o mata (espécie zerada); a Samus continua só com o Power Beam.
- Rotas cegas (`tallon_walk`): a energia volta a 99 no começo de cada ciclo (ver Desvios).

## Critérios de aceite

1. `python3 -I tools/validate.py` → 0 problemas (protege = lugar, set, VRAM, paleta, contas do Prime e
   justiça da fase 0 de cada inimigo, e a ROM igual à tabela; falha_quando = qualquer das mutações do
   critério 2; não_prova = o comportamento no jogo, critérios 4–6).
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) Parasite dentro do
   bloco do Tunnel A; (b) Beetle saindo pela borda da sala; (c) Parasite sem chão; (d) 5 espécies numa
   sala; (e) set de `$2200` bytes no Tallon; (f) set de `$2200` na fragata (limite `$1C00`); (g) espécie
   imune ao beam (MZOOMER) numa sala da fase 0; (h) o Sidehopper grande (proposta do épico) na fase 0;
   (i) duas espécies na mesma paleta; (j) 3 Parasites no Tunnel A (Prime 2, 2 telas); (k) a Blood Flower
   do Root Tunnel faltando; (l) inimigo na Temple Hall (o Prime não tem); (m) inimigo na sala da nave;
   (n) tabela mudada sem reconstruir a ROM.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds.
4. `tallon_inimigos_vivos` e `tallon_inimigos_atras_da_porta_vermelha` passam (protege = cada inimigo
   nasce vivo, na sala certa, na ordem da tabela; falha_quando = set/população errados, inimigo apagado ao
   nascer; não_prova = a aparência, critério 6).
5. `tallon_power_beam_mata_inimigo` passa (protege = dá para matar com o equipamento da chegada).
6. Fotos `specs/img/07i-*.png` olhadas: cada espécie aparece com os tiles e a cor certos.
7. `python3 -I tests/run_tests.py` → 32/32 (os 29 de antes + 3).

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `check_enemies` (caixa inteira), `check_enemy_sets`, `check_enemies_in_rom`, `check_tallon_enemies` | 1 alterada + 3 novas |
| mutação à mão | (a)–(n) | 14 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | 3 novos; `tallon_walk` e a subida da `tallon_rota_bc` alterados | +3 (2 alterações) |
| imagem | 9 fotos `specs/img/07i-*` | 9 |

## Riscos e reversão

- Rotas cegas: inimigos empurram a Samus; trechos medidos podem mudar se as salas ou os inimigos mudarem
  (a subida da Tallon Canyon agora começa de um ponto fixo).
- Dificuldade real só se mede jogando: o validador garante tiros e dano por toque, não a habilidade.
- Reversão: tirar `tools/tallon/enemies.py` (e `enemies=` do `TALLON` em `tools/areas.py`) e reconstruir;
  as checagens novas continuam valendo para a fragata.

## Fora de escopo

- Inimigos das regiões D e E (07l, 07m), das salas Gully/Alcove, e das camadas de evento do Prime
  (Beetles do 1st pass da Root Cave e da Crash Site, Seedlings da Temple Hall, piratas da Crash Site).
- Armadilhas (Chubb Weed, Snake Weed, Spank Weed), Jelly Zap, Drone, Gun Turret.
- Mudar vida/dano das espécies vanilla (seria uma espécie nova em `$A0`).

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `48 salas, 98 portas, 0 problemas` (com a ROM velha, antes de
  reconstruir: 7 problemas, todos "estado … sem a população/enemy set da tabela" — a checagem nova pegou a
  ROM sem inimigos).
- Mutações (a)–(n): todas acusadas; sem mutação, 0. Cada mutação de inimigo também acusa a linha
  "estado … sem a população/enemy set" (a ROM construída não tem a mutação).
- `python3 -I tools/build.py` duas vezes → sha1 `17b959e1c162d816060b49962e781dbaf7b9fcc1` nas duas.
- `python3 -I tests/run_tests.py` → **32/32**.

Mudanças de expectativa dos testes existentes:
- `tallon_walk` (usado por `tallon_rota_mvp`, `tallon_mapa_salvo`, `tallon_rota_bc`,
  `tallon_missil_abre_porta_vermelha`, `tallon_missil_salvo`): **a energia volta a 99 (`poke $09C2`) no
  começo de cada ciclo.** Sem isso o andador cego, que atira uma vez por ciclo e não desvia, morre na volta
  da rota do MVP (medido: 99 → 0 na Tallon Canyon, 20 por salto de Beetle) e o continue o leva para outra
  sala. Os inimigos continuam lá e empurram a Samus; essas rotas testam o caminho, não a luta. Quem prova
  que os inimigos existem e morrem são os 3 testes novos.
- `tallon_rota_bc`, subida da Tallon Canyon (`TALLON_CLIMB`): o trecho medido de 21 ciclos terminava num
  ponto que agora depende dos empurrões (Parasite do Tunnel A: a Samus chega 1 ciclo depois e 24 px à
  direita, e erra a 1ª plataforma). Agora, antes das entradas medidas da subida, ela anda para a esquerda
  até a tampa fechada da porta L1 e vira para a direita (`hold LEFT 40`, `hold RIGHT 2`): fica em x `$27`,
  em pé, virada para a direita, exatamente onde o trecho terminava antes (conferido nas duas ROMs, com e
  sem inimigos). A sequência de salas esperada não mudou.

Desvios e detalhes:

- **Beetle = Sidehopper pequeno** (`$D93F`), não o grande do épico (`$D9BF`): ver a tabela de decisões; a
  mutação (h) mostra o validador recusando o grande na fase 0.
- **Parasite = Zeela** (como o épico), não o HZOOMER que a fragata usa para os Parasites dela.
- **Quantidades**: Canyon Cavern 2 Beetles (Prime 3) e Transport Tunnel B 3 Parasites (Prime 4), pela regra
  de 1 por tela. Na 1ª tentativa o Geemer da Tallon Canyon ficava no caminho a oeste (34ª linha, coluna
  11) e desmanchava a subida da `tallon_rota_bc`; foi para um terraço do leste (42,18).
- **Posições**: escolhidas pelo desenho (as do Prime não saem da biblioteca).
- O tiro em pé passa por cima do Cacatac (16 px de altura): o teste atira agachado.
- As fotos são tiradas depois de pausar e despausar (a câmera posta por RAM deixa o fundo sem redesenhar,
  como no `hangar_ceu_estrelado`). Em algumas a Samus não aparece: está piscando depois de um toque.
