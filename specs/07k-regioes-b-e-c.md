# 07k — Regiões B e C do Tallon (templo, cachoeira, crash site, raízes)

Estado: verificada (23/10/2026: validate 48/98/0 com "alcançáveis agora: 9"; .ips sha1 `4fb3e227…c30b` igual em dois builds; 27/27 testes)
Esforço estimado: 3 dias (spec + pesquisa das travas 0,5 d; desenhos 1 d; validador por fases 0,5 d;
build/portas 0,25 d; teste de rota 0,5 d; verificação 0,25 d)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (linha 07k; decisões 4, 5, 7 e 8)

## Contexto

Até a 07j o Tallon tinha 5 salas na ROM (o caminho do Prime sem itens). As regiões B (templo) e C
(cachoeira, Crash Site, raízes) são 15 salas, 6 delas já desenhadas ou com desenho da 07j
(Artifact Temple, Chozo East, Magmoor East). O problema de projeto é a **progressão**: no Prime,
depois do pouso, a Samus só tem o Power Beam, e boa parte dessas salas fica atrás de travas
(escudo de míssil, portas de gelo/plasma, bordas que pedem Space Jump) cujos itens ainda não
existem no demake.

Decisão: **travas fiéis** (sem acesso provisório). As salas atrás de uma trava ficam construídas,
inalcançáveis até o item existir. O validador passa a saber **em que fase** (equipamento) cada sala
fica alcançável e confere isso contra uma tabela declarada.

## Estado atual (verificado)

- `tools/tallon/rooms.py`: `ACTIVE_REGIONS = {"A"}`, `ACTIVE_ROOMS` = as 5 salas do MVP. Tabela,
  tamanhos e `LINKS` da 07d (B: 4 salas, C: 11). Desenhos em `tools/tallon/layouts.py`: as 5 do MVP
  e, da 07j, Artifact Temple, Chozo East, Magmoor East (B/C) e Chozo South, Mines East (E).
- Portas das salas de A para B/C hoje são parede: Landing Site R1 (Waterfall Cavern) e R2 (Temple
  Hall), Tallon Canyon L0 (Root Tunnel). O desenho delas (07g) fecha essas saídas com rocha.
- `tools/validate.py`: alcance a pé (07b) de **toda** entrada para **toda** porta e `reach.stuck`
  (07j). Não há fases: com uma porta de míssil, "toda porta de toda entrada" continua valendo (a
  Samus anda até a porta; só não abre), mas uma borda que pede Space Jump quebraria a regra.
- `tools/build.py`: portas cinza só da fragata (`DoorLink.locked`, PLM `$C842…`, tipo 0 = chefe
  morto). PLMs de porta (`research/sm_room_format.md` §5): vermelha (míssil) `$C88A/$C890/$C896/$C89C`
  (parede direita/esquerda/chão/teto), argumento = bit da porta (`$7ED8B0`); cinza tipo 4 = nunca abre.
- Bits de porta usados pelo SM vanilla (todos os PLMs de porta das 250 salas da ROM base, lidos
  nesta pesquisa): 0–172. Livres a partir de 173.
- `$8F` livre: 3824 bytes (a partir de `$8F:F110`, 07g/07j). `.ips` sha1 `43f480e1…270c`; 26/26 testes.

### As travas no Prime (dados)

Lidos de `research/prime_fs` (objetos crus de cada sala, com um leitor à parte: o
retro-data-structures 0.44.1 não lê `DamageableTrigger`/`Door`; nome e posição saem dos bytes, e a
porta é a doca mais perto, a ≤ 2 m). Uma porta comum tem `Trigger_DoorUnlock` + `Actor_DoorShield`.
Uma porta com trava tem também `Trigger_DoorKey`: com o objeto `Actor Missile Lock` (o escudo que se
escaneia como "Missile Lock") é **escudo de míssil**; sem ele é **porta de cor** (a cor não sai dos
nomes: vem do conhecimento do Prime, marcado como tal). Alturas = z das docas (m).

| Ligação | Trava no Prime | Fonte | SM agora |
|---------|----------------|-------|----------|
| Landing Site ↔ Temple Hall | nenhuma (porta 12 m acima da nave) | dados | porta azul |
| Temple Hall ↔ Temple Security Station | nenhuma | dados | porta azul |
| Temple Security Station ↔ Temple Lobby | **míssil** (escudo do lado da Security) | dados | **vermelha** do lado da Security |
| Temple Lobby ↔ Artifact Temple | nenhuma (porta de chão) | dados | porta de chão |
| Landing Site ↔ Waterfall Cavern | nenhuma (porta 13 m abaixo da nave) | dados | porta azul |
| Waterfall Cavern ↔ Frigate Crash Site | **míssil** (escudo do lado da Waterfall) | dados | **vermelha** do lado da Waterfall |
| (dentro da Waterfall Cavern) | túnel de Morph Ball | **incerto** (não está nos dados) | não construído: o escudo já fecha |
| Crash Site ↔ Overgrown Cavern | porta de cor (**gelo**) dos dois lados + porta 37 m acima da entrada (**Space Jump**) | trava: dados; cor e Space Jump: conhecimento | **cinza que nunca abre** + borda alta (só com Space Jump) |
| Crash Site ↔ Frigate Access Tunnel | porta de cor (**gelo**) dos dois lados | trava: dados; cor: conhecimento | **cinza** dos dois lados |
| Overgrown Cavern ↔ Transport Tunnel C | porta de cor (**gelo**) dos dois lados | idem | **cinza** dos dois lados |
| Transport Tunnel C ↔ Transport to Chozo Ruins East | porta de cor (**gelo**) dos dois lados | idem | **cinza** dos dois lados |
| (dentro do Transport Tunnel C) | trecho de Morph Ball | dados (`Trigger_morphball_camera`) | não construído (sem Morph no modelo a pé; depois da trava de gelo) |
| Tallon Canyon ↔ Root Tunnel | nenhuma na porta; porta 11,5 m acima da do Transport Tunnel A | dados; "sem item" é **incerto** | porta azul no alto (degraus de 4) |
| Root Tunnel ↔ Root Cave | **míssil** (escudo do lado do Root Tunnel) | dados | **vermelha** do lado do Root Tunnel |
| Root Cave ↔ Transport Tunnel B | nenhuma (porta embaixo, 34 m abaixo da do Root Tunnel) | dados | porta azul |
| Transport Tunnel B ↔ Transport to Magmoor East | nenhuma | dados | porta azul |
| Root Cave ↔ Arbor Chamber | porta de cor (**plasma**) do lado da Root Cave, 48 m acima; **grapple** e plataforma **invisível** (X-Ray) | trava, grapple e plataforma: dados; plasma e Space Jump: conhecimento | **cinza** do lado da Root Cave + borda alta (só com Space Jump) |
| Crash Site ↔ Frigate Access ↔ fragata afundada | (região D) | — | parede (região D desligada) |

Gully e Alcove (região A, fora do MVP): no Prime pedem Morph Ball + Bombas (o "bomb slot" da
Tallon Canyon: `RumbleEffect_bomb_walls`, `Breakable Block`) e Space Jump (a Alcove guarda o próprio
Space Jump). Nenhum desses itens existe nem existe modelo de Bomba: **ficam fora** desta spec
(entram com os itens, 07h). Continuam parede.

## Mudança proposta

### 1. Travas como dados (`tools/tallon/rooms.py`)

- `GATES`: por ligação (par de salas), os itens que ela pede (`missile`, `ice`, `plasma`,
  `space_jump`, `grapple`, `xray`) e de que lado(s) fica a tampa. Tampa por item: `missile` →
  porta vermelha (PLM de míssil, um bit de porta por ligação, a partir de `$B0` = 176, fora dos
  0–172 do vanilla); `ice`/`plasma` → **cinza tipo 4 (nunca abre)** até a spec do item trocar pela
  porta certa. `space_jump`/`grapple`/`xray` não têm tampa: são a geometria (borda alta).
- `DoorLink` (`tools/frigate/rooms.py`) ganha `gate` (itens da ligação, dos dois lados) e `lock`
  (`"missile"`/`"grey"`/`None`, só no lado da tampa). Porta com `lock` se comporta como a cinza da
  fragata: blocos de tampa azul no level, PLM por cima, sem a tampa que fecha atrás.
- `TIERS` (fases, na ordem do Prime): 0 chegada (só Power Beam) · 1 + mísseis · 2 + Space Jump ·
  3 + gelo · 4 + grapple, X-Ray e plasma. Movimento: a pé (07b) sem Space Jump; com ele, o flood
  fill da fragata.
- `FIRST_TIER`: a fase em que cada sala construída fica alcançável (declarada; o validador confere):

  | Fase | Salas |
  |------|-------|
  | 0 (agora) | Landing Site, Canyon Cavern, Tallon Canyon, Transport Tunnel A, Chozo West, **Temple Hall, Temple Security Station, Waterfall Cavern, Root Tunnel** |
  | 1 (+mísseis) | Temple Lobby, Artifact Temple, Frigate Crash Site, Root Cave, Transport Tunnel B, Transport to Magmoor East |
  | 2 (+Space Jump) | — |
  | 3 (+gelo) | Overgrown Cavern, Frigate Access Tunnel, Transport Tunnel C, Transport to Chozo Ruins East |
  | 4 (+grapple, X-Ray, plasma) | Arbor Chamber |

  **Alcançáveis agora da Landing Site só com o Power Beam, de B/C: Temple Hall, Temple Security
  Station, Waterfall Cavern e Root Tunnel** (cada uma até a porta vermelha).

### 2. Ativação

`ACTIVE_REGIONS = {"A", "B", "C"}`; `ACTIVE_ROOMS` = as 5 do MVP + as 15 de B/C (Gully e Alcove
ficam fora). 20 salas na área 0. As portas para Gully, Alcove e região D continuam parede.

### 3. Desenhos (`tools/tallon/layouts.py`)

Regras da 07g para todo caminho a pé: degraus de no máximo 4 blocos, nenhum buraco sem saída,
toda porta sem trava de movimento alcançável de toda entrada (a pé, mesmo nas salas de fase com
Space Jump: mais rígido, mais seguro). Bordas de Space Jump: mais de 7 blocos acima de qualquer
lugar alcançável a pé. Visual pela tabela (superfície/caverna; chuva nas salas do Prime com chuva:
Temple Security Station, Root Cave, Arbor Chamber).

- **Landing Site** (muda o lado leste): sob os terraços, um corredor no nível do chão (3 linhas)
  vai da nave até a porta R2 (Temple Hall); os terraços saem do topo da nave e sobem em degraus de
  4 até a borda da porta R1 (Waterfall Cavern). Oeste e nave iguais.
- **Tallon Canyon** (muda o lado oeste): borda da porta L1 mais larga; três plataformas sobem para a
  direita (degraus de 4) e um salto para a esquerda leva à ponte de pedra da porta L0 (Root Tunnel),
  no alto da parede oeste.
- Novas: Temple Hall, Temple Security Station (pilares Chozo, chuva), Temple Lobby (corredor e poço
  até a porta de chão), Waterfall Cavern, Root Tunnel, Frigate Crash Site (destroço da fragata no
  meio, chão andável entre L3 e R3, borda alta da R2), Frigate Access Tunnel (beco até a região D),
  Overgrown Cavern, Transport Tunnel C (degraus de 4 até a R2), Root Cave (chão entre R3 e L3,
  caverna alta com raízes, borda da L0 só com Space Jump), Transport Tunnel B, Arbor Chamber.
- Água: **sem FX de água** (a água do SM muda o pulo e o modelo da 07b foi medido no seco). Fica
  para a spec da região D/itens.

### 4. Build (`tools/build.py`)

PLM da tampa no lado com `lock`: vermelha `$C88A/$C890/$C896/$C89C` + bit; cinza
`$C842/$C848/$C84E/$C854` com argumento `$9000` (tipo 4, sem bit salvo). Lista de PLMs em `$8F`
(como a cinza da fragata). Mapa de pausa: as 20 salas construídas; lista da SRAM igual (47 bytes,
tabela inteira).

### 5. Validador (`tools/validate.py`)

- `check_room` (a pé): porta com `space_jump` na trava sai da regra "alcançável de toda entrada" e
  entra na regra contrária: **inalcançável a pé** de toda outra entrada (a trava segura).
- `check_tallon_tiers`: para cada fase, busca pelas salas a partir da nave (estação 0), andando de
  verdade em cada sala (a pé ou flood fill) e só passando por uma porta se a fase tem os itens da
  trava. A fase em que cada sala aparece tem que ser a de `FIRST_TIER`; na última fase todas as
  salas construídas são alcançáveis.
- `check_gates` (ROM construída): cada lado com `lock` tem o PLM certo no lugar da tampa (vermelha
  com o bit, cinza tipo 4); bits únicos e fora dos usados pelo vanilla (ROM base).
- Linha do Tallon: `regiões ativas: ABC, 20 salas construídas, 2 desenhadas fora do build` e
  `alcançáveis agora: 9`.

### 6. Teste novo (`tests/run_tests.py`, `tallon_rota_bc`)

Do pouso, só com o Power Beam, andando (direção + tiro + pulo, sem teleporte; trechos com/sem pulo
e com nº de ciclos fixo, o emulador é determinístico): nave → terraços → Waterfall Cavern (a porta
vermelha não abre com o Power Beam) → volta → Canyon Cavern → Tallon Canyon → Transport Tunnel A →
Chozo West → volta à Tallon Canyon, sobe as plataformas → Root Tunnel (porta vermelha) → volta →
Canyon Cavern → Landing Site → corredor sob a nave → Temple Hall → Temple Security Station (porta
vermelha) → volta à Landing Site. A sequência de salas lida a cada ciclo tem que ser exatamente
essa; o equipamento continua zerado; bit da porta vermelha desligado; foto do meio de cada sala nova.

## Critérios de aceite

1. `python3 -I tools/validate.py` → **0 problemas**, com a linha do Tallon
   `regiões ativas: ABC, 20 salas construídas, 2 desenhadas fora do build … alcançáveis agora: 9`.
   (protege = alcance por fase, travas, mapa; falha_quando = degrau alto, sala alcançável antes/depois
   da fase declarada, borda de Space Jump alcançável a pé, tampa errada; não_prova = o jogo real,
   isso é o teste 4)
2. Mutações (na memória, desfeitas): (a) tirar um degrau a pé de uma sala alcançável agora
   (plataforma da Tallon Canyon) → falha (porta inalcançável / lugar sem volta); (b) tirar a trava de
   míssil da Temple Security → falha (Temple Lobby e Artifact Temple na fase 0, declaradas na 1);
   (c) baixar a borda da Overgrown na Crash Site para alcance a pé → falha (trava de Space Jump não
   segura). Sem mutação: 0 problemas.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds; `$8F` livre anotado.
4. `python3 -I tests/run_tests.py` → **27/27**: os 26 de antes + `tallon_rota_bc`.
   (falha_quando = porta que não passa, porta vermelha que abre com o Power Beam, sala trocada)
5. Mudanças de expectativa dos testes existentes (cada uma anotada à parte): a volta da rota do MVP
   (`tallon_rota_mvp`, `tallon_mapa_salvo`) para de andar depois de entrar na Landing Site (antes a
   parede leste a segurava; agora há saídas para Waterfall/Temple Hall); as portas conferidas no
   mapa são só as do caminho do MVP; o quadrado "vazio" do mapa de pausa sai de (30,8), que agora é
   a Temple Hall.
6. Imagens `specs/img/07k-sala-*.png` de cada sala nova ou mudada (sala inteira, tileset da ROM) e
   `specs/img/07k-emulador-*.png` das 4 salas alcançáveis agora (com a porta vermelha), olhadas uma a
   uma.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | fases (`check_tallon_tiers`), trava de Space Jump em `check_room`, `check_gates` | +3 checagens |
| mutação à mão | degrau tirado, trava tirada, borda baixada | 3 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `tallon_rota_bc` (novo); 2 do MVP com a volta encurtada | +1 (2 alterados) |
| imagem | 17 salas inteiras + 4 do emulador | 21 |

## Riscos e reversão

- Cores das portas (gelo/plasma) e o Space Jump da Overgrown/Arbor vêm do conhecimento do Prime, não
  dos dados: se estiverem erradas, muda só `GATES`/`FIRST_TIER` (e a borda). Ficam marcadas acima.
- Cinza "nunca abre" é provisória: a spec do gelo/plasma precisa trocar por uma porta que abra com o
  feixe (o SM não tem porta de gelo).
- A porta vermelha do SM pede 5 mísseis (o escudo do Prime, 1): diferença aceita.
- O teste de rota depende de nº de ciclos por trecho: qualquer mudança nas salas do caminho pode pedir
  novo ajuste (o verificador mostra a sequência de salas obtida).
- Reversão: `ACTIVE_REGIONS = {"A"}` e `ACTIVE_ROOMS` do MVP voltam a ROM ao mesmo conteúdo de antes
  menos os desenhos novos de Landing Site/Tallon Canyon; ou reverter os arquivos e reconstruir.

## Fora de escopo

- Itens (07h: os mísseis/E-tank destas salas, o Space Jump da Alcove), inimigos (07i), Gully e
  Alcove, Morph Ball/Bombas, túneis de Morph, água.
- Porta de gelo/plasma que abre, grapple, plataforma invisível (X-Ray).
- Região D (Frigate Access continua beco), região E, Meta Ridley/artefatos no Artifact Temple.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (tabela inteira, regiões ativas: ABC, 20 salas construídas,
  2 desenhadas fora do build, alcançáveis agora: 9): 44 salas, 44 ligações, 251 telas, mapa 47/80 …`
  e `48 salas, 98 portas, 0 problemas`.
- Mutações (na memória, `LAYOUTS`/`GATES` trocados e desfeitos; sem mutação: 0 problemas):
  (a) sem a plataforma P2 da Tallon Canyon → "porta 2 (L0 -> tallon_root_tunnel) inalcançável a partir
  da entrada porta 0 (R0)" e "tallon_root_tunnel fica alcançável na fase 2 (+ Space Jump), a tabela
  FIRST_TIER diz 0"; (b) sem a trava de míssil Temple Security–Lobby → "tallon_temple_lobby fica
  alcançável na fase 0 …, a tabela FIRST_TIER diz 1" (e o Artifact Temple); (c) degraus de 4 até a
  borda da R2 da Crash Site → "porta 2 (R2 -> tallon_overgrown_cavern) tem trava ['space_jump'] mas é
  alcançável a pé a partir da entrada porta 0 (L3)" (os degraus também fecharam o chão até a R3, o que
  dá mais 3 avisos).
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `4fb3e22745f7a44a909cb4b747e3c109891bc30b` nas duas. `$8F` livre a partir de `$8F:F3EF`:
  **3089 bytes** (735 usados: 15 salas, listas de portas e de PLMs). `$83` até `$83:B22E`, expandido até
  PC `$30B1D2`.
- `python3 -I tests/run_tests.py` → **27/27** (os 26 de antes + `tallon_rota_bc`). A rota B/C sai
  exatamente LS → Temple Hall → Temple Security → Temple Hall → LS → Canyon Cavern → Tallon Canyon →
  Tunnel A → Chozo West → Tunnel A → Tallon Canyon → Root Tunnel → Tallon Canyon → Canyon Cavern →
  LS → Waterfall Cavern → LS; nas três portas vermelhas a Samus fica parada atirando, e a palavra dos
  bits delas (`$7ED8C6`) continua 0; equipamento e mísseis continuam 0.
- Imagens olhadas: `specs/img/07k-sala-*.png` (17: as 15 de B/C + Landing Site e Tallon Canyon,
  tileset da ROM base) e `specs/img/07k-emulador-*.png` (Temple Hall, Temple Security com a porta
  vermelha e chuva, Waterfall Cavern e Root Tunnel com a porta vermelha, Landing Site com a Samus no
  corredor sob a nave).

Mudanças de expectativa dos testes existentes:
- `tallon_rota_mvp` e `tallon_mapa_salvo`: a volta (direita) anda 56 ciclos (era 70, o mesmo da ida):
  ela entra na Landing Site no ciclo 50 e, com mais ciclos, seguia pelos terraços novos até a Waterfall
  Cavern (ciclo 68). A ida e a sequência de salas esperada não mudaram.
- `tallon_door_screens` (usado em `tallon_mapa_salvo`): só as portas entre salas do caminho do MVP
  (as portas novas da Landing Site e da Tallon Canyon não são atravessadas nesse teste).
- `tallon_pause_shows`: o quadrado que tem que ficar vazio no mapa de pausa passou de (30,8), agora
  parte da Temple Hall, para (30,20), fora de toda sala do Tallon.

Desvios e detalhes:

- **Samus presa em cima da tampa vermelha** (emulador, Root Tunnel): o `hall()` deixava 3 linhas de ar
  sobre a porta; ela pulou para cima da tampa fechada e ficou entalada sob o teto baixo. O modelo a pé
  não viu porque (1) tratava os blocos de tampa como passáveis e (2) pede um bloco livre sobre a cabeça
  para subir, mais rígido que o pulo real. Correções: `validate.foot_grid` trata como sólidos os blocos
  de tampa das portas com `lock` (fechadas na chegada), e `hall()` põe rocha sobre as portas laterais.
  Risco que fica: um lugar que o jogo alcança e o modelo não continua invisível ao `reach.stuck`
  (só o teste no emulador pega).
- **Landing Site**: a pedra com musgo foi para x 30–35 (era 31–37) para abrir 2 colunas de descida ao
  chão sob a nave; sem isso o corredor da R2 era só de ida. O terraço de cima começa colado no topo da
  nave (linha 34).
- **Tallon Canyon**: a borda da L1 ficou com 8 blocos (x 0–7): pulando de cima da porta a Samus batia
  na rocha sobre ela. Plataformas P1 (x 10–12, linha 22), P2 (14–17, 18), P3 (18–20, 14), ponte x 0–16
  na linha 10. O andador cego da rota do MVP não sobe as plataformas (cai no cânion), então a ida/volta
  do MVP não muda de sala.
- **Teste B/C**: trechos medidos no emulador (determinístico): descer da nave pela esquerda (70
  quadros), direita sem pulo 9 ciclos (corredor → Temple Hall), direita 20, esquerda 100 (até a Chozo
  West), espera de 60 quadros (sem ela a posição na parede variava), direita 21 e a subida com
  comandos simples (virar para a esquerda antes do último pulo: virar no ar não dava tempo), esquerda
  20, direita 75, esquerda 16.
- **Crash Site**: o destroço é desenhado com a rocha do estilo da superfície (sem peças da fragata):
  degraus de rocha soltos no alto, fora do alcance a pé.
- `vanilla_door_bits` lê também as portas cinza (o bit "aberta" delas fica no mesmo vetor): o maior bit
  vanilla é 172; os do Tallon são `$B0–$B2` (176–178).
- Gully e Alcove continuam fora (ver "Estado atual"); Temple Lobby, Artifact Temple e as 9 salas de C
  além das 2 de agora estão na ROM, atrás das travas.

