# 07l — Região D do Tallon (fragata afundada)

Estado: verificada (23/10/2026: validate 62/126/0 com "ABCD, 34 salas … alcançáveis agora: 15"; .ips sha1 `706ba8c7…f498` igual em dois builds; 36/36 testes)
Esforço estimado: 3 dias (pesquisa Prime + ROM 0,5 d; medição do pulo na água 0,5 d; desenhos 0,75 d;
validador + mutações 0,5 d; build/estação de save 0,25 d; testes no emulador 0,5 d)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (linha 07l: "14 salas, água, save station P28 =
load station 1"; decisões 2, 5 e 8)

## Contexto

Depois da 07k/07h/07i o Tallon tem as regiões A, B e C (20 salas) com as travas fiéis do Prime. A
região D é a Frigate Orpheon no fundo do lago: 14 salas debaixo d'água, com o segundo ponto de save
do Tallon (P28 `Savestation`). No Prime ela fica atrás da porta de gelo da Frigate Access Tunnel e
pede a Gravity Suit; lá dentro, portas que só abrem carregando condutores de energia (Thermal Visor +
Wave Beam). Nada disso existe no demake ainda: a região entra **construída e fiel, inalcançável a pé
agora**, como Temple Lobby/Overgrown/Arbor na 07k. Os testes chegam nela pela estação de save nova.

O problema técnico é a **água**: o FX de água do SM muda o pulo da Samus, e o modelo de alcance
(`tools/smlib/reach.py`, 07b) foi medido no seco. Esta spec mede o pulo debaixo d'água no emulador,
com e sem a Gravity Suit, e o validador passa a usar o pulo certo em cada sala.

## Estado atual (verificado)

- `tools/tallon/rooms.py`: `ACTIVE_REGIONS = {A, B, C}`; a tabela já tem as 14 salas de D (07d:
  visual `FRI` = estilo e tileset 4 da fragata; Hydro Access `CAV`), tamanhos (60 telas) e `LINKS`.
  Portas para D são parede (Frigate Access R0). `TIERS` 0–4, `GATES` da 07k.
- `tools/tallon/items.py`: linhas reservadas sem lugar: 7 Cargo Lift (E-tank, bit `$A7`), 8 Biohazard
  (míssil, `$A8`), 9 Hydro Access (E-tank, `$A9`). As três ficam na região D (épico, tabela "Itens").
- `tools/areas.py`: estações do Tallon = 0 (nave) e `$12` (chegada da fragata). A lista de save da
  área 0 (`$82:C853`) tem 8 entradas; a do mapa na SRAM já guarda os 47 bytes da tabela inteira (07f).
- `tools/build.py`: a única save station (fragata) usa estado condicional ao chefe ("Save Disabled"
  do Prime). FX das salas = `RoomDef.fx` (só chuva). Bancos livres antes desta spec: `$8F` a partir de
  `$8F:F419` (3047 bytes), `$A1` de `$A1:EFA0`, `$B4` de `$B4:F5ED`, `$83` de `$83:B22E`.
- Antes de mexer: `validate` 48 salas/98 portas/0 problemas; `.ips` sha1 `17b959e1…fcc1`; 32/32 testes.

### A região D no Prime (dados de `research/prime_fs`, lidos nesta pesquisa)

Objetos por camada de cada sala (retro-data-structures; nome e posição dos objetos que a biblioteca
não lê saem dos bytes crus: nome = 1º texto das propriedades, posição = 3 floats depois dele, posição
local = transformação inversa da sala em `prime_worlds.json`; porta = doca mais perto, ≤ 1,6 m).

| Sala | Água | Travas nas portas (dados) | Inimigos camada 0 | Item |
|------|------|---------------------------|-------------------|------|
| P12 Frigate Access Tunnel | não | `Trigger_DoorKey` + `Actor_DoorShield_Key` na doca da Crash Site (gelo, 07k); doca da Vent C comum | Snake Weed 1 | — |
| P17 Main Vent. Shaft C | sim | comuns | — | — |
| P21 Main Vent. Shaft B | sim | comuns (uma porta interna com "Thermal Door Scan") | — (4 Gun Turret na camada 1) | — |
| P24 Main Vent. Shaft A | sim | comuns | Wall Crawler Swarm 1 | — |
| P25 Reactor Core | sim | doca do Reactor Access: "Thermal Door Scan Hi" + 4 "Thermal Panel" | — (Jelly Zap/Spank Weed na camada 2, pirata voador na 1) | — |
| P26 Reactor Access | sim | doca da Cargo Lift: "Thermal Door Scan"; doca do Reactor Core: "Reactor Door" sem `DoorUnlock`; doca da Savestation comum | — | — |
| P27 Cargo Freight Lift | sim | doca da Transit Hall: "Thermal Door Scan" + "Door Activate"; doca do Reactor Access sem `DoorUnlock` | Spank Weed 2 | E-tank, z −38,7 m (porta do Reactor Access −37,3) |
| P28 Savestation | sim | comum | — | — (estação de save) |
| P29 Deck Beta Transit Hall | **não** | comuns | — | — |
| P30 Biohazard Containment | sim | doca da Security Hall: "Thermal Door Scan" + "Door Activate" | **Gun Turret 4** | míssil, z −12,9 (porta da Security −11,4), oeste |
| P31 Deck Beta Security Hall | sim | comuns | Spank Weed 5 | — |
| P32 Biotech Research Area 1 | sim | doca da Conduit Hall: "Thermal Door Scan" + "Door Activate" | — (piratas voadores/Jelly Zap/Drone em camadas de evento) | — |
| P33 Deck Beta Conduit Hall | sim | comuns | Spank Weed 6 | — |
| P34 Connection Elevator to Deck Beta | sim | comuns | **Space Pirate 1** | — |
| P35 Hydro Access Tunnel | sim | comuns (túnel de Morph Ball: "Puzzle/Force Trigger") | — | E-tank, z 27,0 (portas 2,5 e 20,5), no meio |

Conhecimento do Prime (não sai dos dados, marcado como tal): a fragata afundada pede a **Gravity
Suit**; os condutores ("Thermal Panel") se veem com o **Thermal Visor** e se carregam com o **Wave
Beam**. Os três vêm antes da fragata no Prime (Wave e Gravity/Thermal na Phendrana).

### O pulo debaixo d'água (medido no emulador)

FX de água = entrada da sala vanilla inundada da Wrecked Ship `$8F:CD5C` (`$83:9B64`: tipo 6, blend
`$02/$18`, opções 3, paleta `$48`, sem listas de área) com a superfície em y `$10` (o valor das salas
inundadas da Maridia, `$83:9D64`…): a sala inteira fica debaixo d'água. Método igual ao da 07b
(`pulo_sem_space_jump_medido`): Samus parada no chão da Savestation (linha 13, coluna 2, ar até a
linha 3), virada para a direita, equipamento por RAM, `x`, `y`, raio a cada quadro.

| Pulo | Subida | Alcance (px) quando o pé passa r blocos acima (r = 0…) |
|------|--------|--------------------------------------------------------|
| seco (07b), referência | 113 | 115, 109, 105, 100, 94, 87, 79, 62 |
| água **com** Gravity Suit | **113** | **112, 108, 105, 100, 93, 87, 78, 62** |
| água **sem** Gravity Suit | **51** | **144, 131, 116, 91** (pulo baixo e longo, cai devagar) |

Em blocos: com a Gravity Suit dá exatamente o modelo do seco (degrau 7, vão 7); sem ela, degrau **3**
e vão de **9** colunas. Os alcances mudam 1–2 px com o estado inicial (virada para a esquerda, a
1ª medida dava 130 px): as constantes valem para o roteiro do teste, como na 07b. Space Jump debaixo
d'água sem a Gravity Suit não funciona: C `vendor/sm/src/sm_90.c:1915-1930` (com a Samus no líquido e
sem o bit de paleta da Gravity, o pulo no ar não é chamado); os meus toques de A por quadro também não
dispararam o Space Jump no seco, então isso fica provado pelo código, não pelo emulador.

### Outros fatos verificados no emulador nesta pesquisa

- **Carregar a estação 1 por RAM**: área `$079F` = 0, estação `$078B` = 1, `$7ED914` = 5, estado
  `$0998` = 6 (o mesmo que a rotina de jogo novo faz) → a Savestation carrega com a Samus no pedestal;
  ela só aceita comando ~550 quadros depois (pose `0` de frente).
- **Estação recém-carregada não salva** até a Samus sair da sala (`save_station_lockout_flag`, ligado
  em `LoadFromLoadStation` `$80:C437`, desligado só na troca de sala `$82:E1B7`): comportamento
  vanilla, o teste sai e volta.
- **Descer por porta de chão afunda a Samus na borda de baixo**: o padrão `$8000` (distância 384) da
  transição para baixo termina com o pé 7 px dentro da borda que `Canvas.door_gap` põe na linha 6 sob
  toda porta de teto; ela fica presa (anda 0 px). Com `$0140` (valor vanilla) para em cima da borda.
- **Subir por porta de chão numa sala inundada**: com `$0240` (o da fragata) a Samus sai dentro da porta
  e cai de volta (debaixo d'água ela não continua subindo); com `$0340` sai 2 linhas acima das bordas e,
  segurando a direção, pousa ao lado da porta.
- **Teleporte por porta (só teste)**: pôr a Samus parada na frente da porta, `$099C` = `$E17D`
  (`DoorTransitionFunction_HandleElevator`, o que a colisão com bloco de porta põe, `$94:938B`), `$078D` =
  entrada da porta, `$0998` = 9 → a transição acontece como se ela tocasse a porta. Passa por portas
  cinza (que o jogo não abre ainda).

## Mudança proposta

### 1. Travas, fases e alcance (`tools/tallon/rooms.py`)

- Itens novos de trava: `gravity`, `wave`, `thermal`. `wave`/`thermal` têm tampa **cinza que nunca
  abre** (como gelo/plasma, provisória até os itens existirem). `gravity` é de **movimento** (borda,
  como o Space Jump), mas no sentido contrário do Space Jump: a borda tem de ser alcançável a pé **com**
  a suit e inalcançável debaixo d'água **sem** ela.
- `GATES` novos:

  | Ligação | Trava | Fonte | SM |
  |---------|-------|-------|----|
  | Frigate Access ↔ Vent C | nenhuma | dados | porta azul (era parede) |
  | Vent C ↔ Vent B | **Gravity Suit** | conhecimento | borda: um anteparo de 4 blocos na Vent C (sem a suit o pulo sobe 3) |
  | Reactor Core ↔ Reactor Access | Thermal + Wave | dados (painéis, sem `DoorUnlock` dos dois lados) + conhecimento (feixe/visor) | **cinza** dos dois lados |
  | Reactor Access ↔ Cargo Lift | Thermal + Wave | idem | **cinza** dos dois lados |
  | Cargo Lift ↔ Transit Hall | Thermal + Wave | idem (escudo comum do lado da Transit) | **cinza** do lado da Cargo Lift |
  | Biohazard ↔ Security Hall | Thermal + Wave | idem | **cinza** do lado da Biohazard |
  | Biotech 1 ↔ Conduit Hall | Thermal + Wave | idem | **cinza** do lado da Biotech |

- `TIERS`: entra uma fase nova **4 = "+ Gravity Suit, Wave Beam, Thermal Visor"** (o que a fragata
  afundada pede; os três vêm antes dela no Prime); a antiga 4 (grapple, X-Ray, plasma) vira **5** (Arbor
  Chamber e o míssil dela: 4 → 5).
- `FIRST_TIER`: Vent C = **3** (depois da porta de gelo, sem a suit; Prime deixa nadar até o anteparo);
  as outras 13 salas de D = **4**. **Nenhuma sala de D é alcançável agora** (fiel, como a 07k pede).
- `FLOODED`: as 13 salas com objeto `Water` no Prime (todas de D menos a Transit Hall) ficam inundadas
  até o teto (`RoomDef.water`). As poças de A–C continuam secas (fora de escopo).
- Região D ativa: `ACTIVE_REGIONS = {A, B, C, D}`; `ACTIVE_ROOMS` + as 14 salas → 34 salas na área 0.
  Visual da fragata: estilo/tileset 4 (o recolor da fragata é global e serve) e o fundo dela (lista
  vanilla `$8F:E117`, BG2 `$C1C1`), no lugar do céu do Tallon. Música: a da área (sem música própria).

### 2. Pulo na água (`tools/smlib/reach.py`)

`Loadout` ganha `gravity` e `water`; `rise_px`/`arc_px` escolhem a tabela medida (seco, água com a
suit, água sem); `flies` = Space Jump que funciona (no seco, ou na água com a suit); Hi-Jump na água
não foi medido (erro). `self_test` ganha os casos da água: com a suit degrau 7/8 e vão 7/8 como no seco;
sem ela degrau **3** alcança / **4** não, vão de **9** alcança / **10** não; sem Space Jump na água sem a suit.

### 3. Desenhos (`tools/tallon/layouts.py`)

Mesmas regras da 07g/07k (degraus de até 4, nada sem volta, toda porta de toda entrada, a pé, com a
suit). Peças da fragata (casco, nervuras, plataformas finas). `steps()` = subida de plataformas de 1
bloco, 4 acima e 3 colunas ao lado da anterior (nada pendurado sobre a coluna do salto).

- **Frigate Access** (C): o paredão de entulho que fechava a R0 virou um monte (2 blocos) e um resto
  pendurado longe da porta.
- **Vent C** (2x2): duto no alto da tela de cima; o **anteparo** de 4 blocos (colunas 12–13) é a trava
  da Gravity Suit; depois dele o duto afunda numa calha de 4. A tela de baixo é casco.
- **Vent B** (2x2): degraus de 4 descem da L0 até o fundo da tela de baixo e sobem até a R0.
- **Vent A** (2x1): duto com nervuras e um pedaço de duto caído.
- **Reactor Core** (4x3): passarela da L1 (linha 26), degraus de 4 até o chão (linha 42) sob o reator
  pendurado no meio; R2 (cinza) na ponta leste do chão.
- **Reactor Access** (1x1): corredor; L0 e R0 cinza; a borda da porta de teto (T0) a 4 do chão.
- **Savestation** (1x1): chão na linha 13 dos dois lados da porta de chão (B0), teto na linha 2 (o
  pulo inteiro cabe: é onde se mede); **pedestal da estação em (11, 13)**, à direita da porta.
- **Cargo Lift** (4x3): deque de cima (linhas 26–27) da L1 até a coluna 40; deque de baixo da L2 até o
  poço; 3 plataformas sobem do deque de baixo ao de cima; trilhos do elevador no poço.
- **Transit Hall** (2x1, seca): corredor com nervuras.
- **Biohazard** (2x2): degraus de 4 da R0 até o chão da tela de baixo; dois tanques de contenção de 4
  blocos; a L1 (cinza) no chão.
- **Security Hall** (1x1), **Conduit Hall** (2x1): corredores.
- **Biotech 1** (2x3): portas no chão da tela de baixo; plataformas sobem às galerias.
- **Elevator Beta** (1x3): a cabine parada (linha 26) entre as portas do meio; trilhos acima.
- **Hydro Access** (3x2, caverna inundada): degraus de 4 da R0 até o chão do túnel; prateleira a 4 do
  chão. A porta B2 (Great Tree Hall, região E) é rocha até a 07m.

### 4. Estação de save P28 = load station 1 da área 0

- `areas.gunship_stations`: estação 0 e `$12` na nave e, como `stations_from_rooms`, 1, 2… nas salas
  com save station → **estação 1 = Savestation** (Samus em x 192, y 184 = pedestal − 24).
- Build: o PLM de save (`$B76F`, argumento 1) no pedestal; **estado único** (o "Save Disabled" depois do
  chefe é só da fragata: estado condicional agora só quando a área tem `boss_room`).
- Mapa de pausa: a sala 1x1 com save usa o tile `$4D` (pausemap); a entrada 1 da lista de ícones de save
  da área 0 (`$82:C853` + 4) passa a ser a da Savestation (era `$FFFE`); `check_pause_maps` confere. A
  lista da SRAM não muda (47 bytes, tabela inteira).

### 5. Água e portas (`tools/build.py`)

- `WATER_FX` (16 bytes em `$83`, um só para todas as salas inundadas) e `RoomDef.water` → FX dos estados.
- `TALLON_DOWN_PUSH = $0140` nas portas do Tallon que descem (lado B) e `TALLON_UP_PUSH_WATER = $0340`
  nas que sobem (lado T) para uma sala inundada (ver "Outros fatos"). A fragata não muda.
- `manifest.json` ganha `doors` (endereços das entradas de porta de cada sala), para o teleporte dos
  testes.

### 6. Itens (`tools/tallon/items.py`) — todos na fase 4

| # | Sala | Item | Bit | Lugar | Por quê |
|---|------|------|-----|-------|---------|
| 7 | Cargo Lift | Energy Tank | `$A7` | (38, 25), no deque de cima sobre o poço | no Prime na altura da porta do Reactor Access |
| 8 | Biohazard | Missile Expansion | `$A8` | (11, 25), entre os tanques | no Prime baixo, a oeste, na altura da porta da Security Hall |
| 9 | Hydro Access | Energy Tank | `$A9` | (22, 21), na prateleira | no Prime alto no meio do labirinto de Morph Ball; sem Morph Ball, numa prateleira (desvio) |

### 7. Inimigos (`tools/tallon/enemies.py`, `PRIME_LAYER0`, `STAND_IN`)

| Prime (camada 0) | SM | Onde |
|------------------|----|------|
| Wall Crawler Swarm 1 (Vent A) | HZOOMER `$DC3F` (o "parasite" da fragata), paleta 1 | no chão do duto (22, 10) |
| Space Pirate 1 (Elevator Beta) | pirata `$F653` (o da fragata), paleta 2 | na cabine (8, 26) |
| **Gun Turret 4** (Biohazard) | **Rinka `$D23F`**, paleta 3 (espécie nova `turret`) | nos degraus (24, 14), (21, 18) e em cima dos tanques (8, 22), (14, 22) |
| Spank Weed (Cargo 2, Security 5, Conduit 6) | fora | planta-armadilha, como o Snake Weed (07i) |
| Jelly Zap, Drone | fora | só em camadas de evento (1st/2nd pass) na região D |

Rinka: o "anel" da Tourian é um emissor parado que atira um anel na Samus de novo e de novo — o papel
de uma torreta; valores das colocações vanilla `$8F:DAE1` (init 0, propriedades `$6000`, parâmetros 0 =
o Rinka comum, não o do Mother Brain). Vida 10 (1 tiro do Power Beam), toque 40. Fase 4: a regra de
justiça da fase 0 (07i) não se aplica. Cada sala com ≤ 1 inimigo por tela e set ≤ 4 espécies/`$2000`.

### 8. Validador (`tools/validate.py`)

- `room_loadout`: sala inundada é checada com a Gravity Suit e o pulo da água (a região assume a suit);
  `check_room` usa o flood fill só quando o Space Jump funciona (`Loadout.flies`).
- Regra da borda: a de **Space Jump** continua "inalcançável a pé"; a de **Gravity Suit** é alcançável
  a pé com a suit (regra normal).
- `tallon_room_reach`/`tallon_tiers`: o passeio por fases usa o pulo da água sem a suit nas fases sem
  ela (sem Space Jump), e o flood fill com ela.
- **`check_tallon_water`** (novo): as salas inundadas que a Samus pode alcançar sem a suit (FIRST_TIER
  sem `gravity`: a Vent C) são andadas com o pulo de 51 px: de cada porta fora da borda da suit, a porta
  atrás da trava fica inalcançável, as outras alcançáveis, nenhum lugar sem volta.
- **`check_water_in_rom`** (novo, ROM construída): todo estado de sala inundada aponta para `WATER_FX`
  (tipo 6, superfície `$10`); nenhuma outra sala tem água.
- Os existentes cobrem o resto: `check_tallon_tiers` (fases, itens), `check_gates` (cinza nas 5 ligações
  de condutor), `check_tallon_items`, `check_enemies`/`check_enemy_sets`/`check_tallon_enemies`,
  `check_arrival` (estação 1 na ROM), `check_pause_maps` (ícone de save da estação 1).

### 9. Testes no emulador (`tests/run_tests.py`)

- `pulo_na_agua_medido`: carrega a estação 1, mede os 4 pulos da tabela acima; as constantes
  `WATER_*` de `reach.py` têm de sair **iguais** (verificador `check_water_jumps`).
- `tallon_rota_d`: da estação 1, com a Gravity Suit, andando: pela porta de chão até o Reactor Access,
  à porta do Reactor Core e à da Cargo Lift (cinza: os tiros do Power Beam não abrem, a Samus fica na
  sala), de volta à borda e pela porta de teto à Savestation; a sequência de salas tem de ser essa.
- `tallon_save_fragata`: estação 1 → sai e volta (a rota acima) → pedestal → salva (marca em `$09E0`)
  → `$078B` = 1, bit 1 de `$7ED8F8` → pausa (foto do mapa com o ícone) → morre → tela de área
  (Tallon, estação 1) → continue: Savestation, estação 1, a marca, na água.
- `tallon_fragata_afundada`: as 13 outras salas por teleporte de porta (duas cadeias a partir da
  estação 1): cada sala carrega, água em todas menos a Transit Hall, inimigos vivos na tabela da WRAM
  (Vent A, Biohazard, Elevator Beta), e o **E-tank da Cargo Lift é pego** (máximo 99 → 199, bit `$A7`).
- Fotos: `specs/img/07l-sala-*.png` (15 salas, prévia sem a água) e `specs/img/07l-emulador-*.png`.

## Critérios de aceite

1. `python3 -I tools/validate.py` → **0 problemas**, linha do Tallon "regiões ativas: ABCD, 34 salas
   construídas … alcançáveis agora: 15" e "62 salas, 126 portas". (protege = alcance com o pulo certo na
   água, a trava da suit, fases, travas cinza, itens, inimigos, água e estação na ROM; falha_quando =
   mutações do critério 2; não_prova = o jogo real, critérios 4–7)
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) anteparo da Vent C
   com 3 blocos; (b) anteparo até o teto; (c) poço de 4 antes do anteparo; (d) sem a trava da Gravity
   Suit; (e) fase 4 sem o Wave Beam; (f) Savestation sem água (ROM com); (g) Transit Hall com água (ROM
   sem); (h) pulo sem a suit de 67 px; (i) E-tank da Cargo Lift dentro do deque; (j) 5 torretas na
   Biohazard.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds; espaço por banco anotado.
4. `pulo_na_agua_medido` passa (protege = as constantes da água; falha_quando = a física mudar ou alguém
   mexer nos números).
5. `tallon_rota_d` e `tallon_save_fragata` passam (protege = descer/subir pelas portas de chão na água,
   portas cinza fechadas, salvar e continuar na estação 1).
6. `tallon_fragata_afundada` passa (protege = toda sala de D carrega com água certa, inimigos vivos,
   coleta do E-tank; não_prova = chegar a pé, que o jogo não permite ainda).
7. `python3 -I tests/run_tests.py` → **36/36** (os 32 de antes + 4).
8. Fotos `specs/img/07l-*.png` olhadas: tileset, paletas e água sem lixo.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| reach.self_test | casos da água (com e sem a suit, Space Jump) | +9 |
| validate.py | `check_tallon_water`, `check_water_in_rom`; regra da borda da suit; fases com a água | +2 checagens (3 alteradas) |
| mutação à mão | (a)–(j) | 10 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `pulo_na_agua_medido`, `tallon_rota_d`, `tallon_save_fragata`, `tallon_fragata_afundada` | +4 |
| imagem | 15 salas + fotos do emulador | ~20 |

## Riscos e reversão

- A trava da Gravity Suit é geometria: um wall-jump na água sem a suit poderia passar o anteparo (o
  modelo só supõe o pulo parado, como na 07b/07k). Mesmo risco das bordas de Space Jump.
- Os alcances medidos variam 1–2 px com o estado da Samus; o modelo usa o roteiro do teste. Em blocos,
  só o vão sem a suit (144 px = 9 colunas) está na borda de um bloco.
- Portas de condutor (Thermal + Wave) são cinza "nunca abre" (provisório, como gelo/plasma); a cor/item
  vem de conhecimento do Prime (os painéis vêm dos dados).
- A região só é testada no emulador a partir da estação 1 e por teleporte de porta: nenhuma rota a pé
  da nave chega lá (porta de gelo).
- Reversão: `ACTIVE_REGIONS`/`ACTIVE_ROOMS` sem D, `TIERS`/`FIRST_TIER`/itens como antes, reconstruir.

## Fora de escopo

- Gravity Suit, Wave Beam, Thermal Visor como itens; portas de condutor que abrem; gelo.
- Água das poças das regiões A–C; música própria da fragata afundada; objetos de cena (tanques de
  estase) nas salas de D.
- Camadas de evento (Jelly Zap, Drone, piratas voadores, torretas da Vent B, piratas da Biohazard).
- Morph Ball (o labirinto da Hydro Access), região E (a porta B2 da Hydro Access é rocha).
- O problema da porta de chão na fragata (ver Desvios): só anotado.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (tabela inteira, regiões ativas: ABCD, 34 salas construídas, 2
  desenhadas fora do build, alcançáveis agora: 15): 44 salas, 44 ligações, 251 telas, mapa 47/80 bytes de
  SRAM …` e `62 salas, 126 portas, 0 problemas`.
- Mutações (na memória, `LAYOUTS`/`GATES`/`TIERS`/`FLOODED`/`reach`/`ITEMS`/`enemies` trocados e desfeitos;
  sem mutação: 0 problemas): (a) anteparo de 3 → 2 problemas ("sem a Gravity Suit … alcança a porta 1 (R0)",
  e a calha vira lugar sem volta); (b) anteparo até o teto → 18 (portas inalcançáveis, D inteira
  inalcançável); (c) poço de 4 antes do anteparo → 1 ("4 lugares sem volta" sem a suit); (d) sem a trava da
  suit → 3; (e) fase 4 sem o Wave Beam → 13 (as salas atrás dos condutores na fase 5); (f) Savestation sem
  água → 1 (ROM com água); (g) Transit Hall com água → 1; (h) pulo sem a suit de 67 px → 2 (`self_test` e a
  trava); (i) E-tank dentro do deque → 3; (j) 5 torretas → 4. Mutação no emulador (cópia do projeto):
  `TALLON_DOWN_PUSH = $8000` → `tallon_rota_d` falha (`7E0AF6 = 0088, esperado 0025`: presa na borda);
  `TALLON_UP_PUSH_WATER = $0240` → falha (a Samus volta ao Reactor Access).
- `python3 -I tools/build.py` duas vezes → sha1 `706ba8c7f2ffe7f17e6920daae7caf78a496f498` nas duas.
  Espaço usado: `$8F` 682 bytes (`$8F:F419` → `$8F:F6C3`; sobram 2365), `$83` 364 (`$83:B22E` → `$83:B39A`:
  entradas de porta + 16 da água), `$A1` 105 (→ `$A1:F009`), `$B4` 39 (→ `$B4:F614`); nível das 14 salas
  3603 bytes comprimidos no banco `$E0` (até `$E0:EE0E`, 4594 antes do banco da Parasite Queen, que não
  muda de lugar); `$A0`, `$A2`, `$A6`, `$82` iguais.
- `python3 -I tests/run_tests.py` → **36/36** (os 32 de antes + `tallon_save_fragata`, `pulo_na_agua_medido`,
  `tallon_rota_d`, `tallon_fragata_afundada`).
- Imagens olhadas: `specs/img/07l-sala-*.png` (15, prévia sem a água; tampas cinza não aparecem, são PLMs)
  e `specs/img/07l-emulador-*.png` (as 14 salas com a água azul e a malha do BG3 da água, sem lixo; portas
  cinza do Reactor Access e da Cargo Lift; o E-tank pego; mapa de pausa com o "S" e o ícone de save na
  Savestation; tela de área "TALLON / OVERWORLD"; continue no pedestal).

Mudanças de expectativa dos testes existentes: **nenhuma** (os 32 passam sem mudança; `tallon_pause_shows`
continua com o quadrado vazio em (30,20), fora de toda sala, D incluída).

Desvios e detalhes:

- **Portas de chão do Tallon** (achado no emulador, não previsto): descer pela porta de chão da Savestation
  deixava a Samus 7 px dentro da borda da linha 6 do Reactor Access (anda 0 px; um pulo solta) e subir de
  volta a fazia cair de novo na porta. Correção só no Tallon: `TALLON_DOWN_PUSH = $0140` (descer) e
  `TALLON_UP_PUSH_WATER = $0340` (subir para sala inundada); a Temple Lobby → Artifact Temple (07k) também
  desce com `$0140` agora. **A fragata tem o mesmo afundamento** (conferido: Map Facility → Connection
  Elevator to Deck Beta, y `$51`, anda 0 px até pular), no caminho principal; não mexi (mudaria a ROM da
  fragata e os testes dela atravessam por teleporte): fica anotado no HANDOFF para decisão.
- **Pulo na água**: medido primeiro numa cópia (evac_area com água), depois no lugar definitivo (Savestation):
  as constantes são as da Savestation (o roteiro do teste). Virada para a esquerda o alcance dava 130 px
  (virar gasta quadros): o teste vira a Samus para a direita antes de cada pulo.
- **Space Jump sem a Gravity Suit na água**: o modelo diz "não funciona" pelo código C (`sm_90.c:1915-1930`);
  não consegui fazer o Space Jump disparar no emulador nem no seco com toques de A por quadro, então não há
  medida dele.
- **Estação recém-carregada não salva** (vanilla): o teste de save sai pela porta de chão e volta antes.
- **Teleporte de porta** só nos testes (`door_teleport`), para as salas atrás das portas de condutor; o
  `manifest.json` ganhou `doors` para isso.
- Gun Turret = Rinka: decidido aqui (07i deixou em aberto). O Rinka morto volta (como na Tourian); a torreta do
  Prime fica destruída — diferença aceita. Testado vivo nos 4 lugares (`tallon_fragata_afundada`).
- Vent C: a tela de baixo é casco (a sala do Prime é um duto inclinado de 49 m); o caminho fica na de cima.
- `tools/preview_rooms.py`: o recolor da paleta passou a ser por tileset (o da área que recolore o tileset 4),
  então as salas do Tallon no tileset 4 saem com as cores da fragata, como na ROM; as da fragata não mudam.
