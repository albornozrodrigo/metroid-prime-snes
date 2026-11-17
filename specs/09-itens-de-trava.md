# 09 — Itens de trava: o Tallon inteiro jogável (épico)

Estado: verificada (23/10/2026: as 6 filhas verificadas; definição de pronto cumprida, ver Desvios)
Filhas: 09a–09f verificadas (23/10/2026: as 44 salas e os 20 itens a pé da nave, em 7 rodadas declaradas e provadas pelo validador; `tallon_cadeia_completa` no emulador).
Esforço estimado: 8–9,5 dias no total, em 6 filhas de 0,5–2,5 dias. MVP (09a–09d): 5–6 dias.
Épico anterior: [07 — Tallon Overworld](07-tallon-overworld.md) (falta da definição de pronto: "pega os 13 itens")

## Contexto

Depois da 07m as 44 salas do Tallon estão na ROM, ligadas como no Prime, com as **travas fiéis** do Prime:
portas vermelhas (míssil), portas cinza "nunca abre" (gelo, plasma, condutores Wave+Thermal, paredes de
Bombas da Gully), bordas de Space Jump e o anteparo da Gravity Suit. No Prime, os itens que abrem essas
travas vêm de outros mundos (Chozo Ruins, Phendrana, Magmoor, Phazon Mines), que não existem no demake.
Resultado hoje: do pouso, a pé, só 15 salas e 4 itens (os mísseis da Landing Site, Crash Site, Tunnel B e,
com eles, as salas atrás das portas vermelhas) são alcançáveis; o resto espera.

Esta etapa põe no próprio Tallon os **itens de trava** e o mecanismo que falta a cada trava, para que um
jogador saia da Landing Site só com o Power Beam e, andando, pegue os 13 itens do Tallon e chegue às 44
salas, sem softlock. O épico decide quais itens, o equivalente no SM de cada habilidade do Prime, como
fazer portas que só abrem com um feixe, onde cada item fica e em que ordem, o que o validador tem de
provar e como testar. As filhas (09a–09f) só implementam.

## Estado atual (verificado)

Conferido nesta pesquisa na pasta real (só leitura): `python3 -I tools/validate.py` → "regiões ativas: ABCDE,
44 salas construídas, alcançáveis agora: 15" e "72 salas, 148 portas, 0 problemas"; `build/metroid_prime_snes.ips`
sha1 `27828fae3277b076cc5611dbdaf56f5cdb3bebe3`; HANDOFF: 39/39 testes.

### As travas de hoje (`tools/tallon/rooms.py`, `GATES`, `TIERS`, `FIRST_TIER`)

| Ligação | Itens da trava hoje | Mecanismo hoje | Fonte (07k/07l/07m) |
|---------|---------------------|----------------|---------------------|
| Temple Security ↔ Temple Lobby | míssil | vermelha (lado da Security) | dados |
| Waterfall Cavern ↔ Frigate Crash Site | míssil | vermelha (lado da Waterfall) | dados |
| Root Tunnel ↔ Root Cave | míssil | vermelha (lado do Root Tunnel) | dados |
| Crash Site ↔ Overgrown Cavern | gelo + Space Jump | cinza dos dois lados + borda (Crash) | trava: dados; gelo/SJ: conhecimento |
| Crash Site ↔ Frigate Access, Overgrown ↔ Tunnel C, Tunnel C ↔ Chozo East | gelo | cinza dos dois lados | idem |
| Root Cave ↔ Arbor Chamber | plasma + Space Jump + grapple + X-Ray | cinza (Root Cave) + borda | trava/grapple/plataforma invisível: dados; plasma/SJ: conhecimento |
| Vent C ↔ Vent B | Gravity Suit | anteparo de 4 blocos (geometria, água) | conhecimento |
| Reactor Core ↔ Reactor Access, Reactor Access ↔ Cargo Lift | Wave + Thermal | cinza dos dois lados | painéis: dados; itens: conhecimento |
| Cargo Lift ↔ Transit Hall, Biohazard ↔ Security Hall, Biotech 1 ↔ Conduit Hall | Wave + Thermal | cinza de um lado | idem |
| Tallon Canyon ↔ Gully | Bombas | cinza na porta de teto T3 da Canyon | blocos quebráveis: dados; Bombas: conhecimento |
| Landing Site ↔ Gully, Landing Site ↔ Alcove | Space Jump | borda (câmara no penhasco) | conhecimento (incerto) |
| GTH ↔ Tunnel D, GTH ↔ Tunnel E, Tunnel D ↔ Chozo South, Tunnel E ↔ Mines East | gelo | cinza dos dois lados | Key: dados; gelo: conhecimento |
| GTH ↔ Great Tree Chamber | Space Jump | borda (GTH) | conhecimento (incerto) |
| GTH ↔ Life Grove Tunnel | gelo + Spider + Boost + Power Bombs | cinza dos dois lados | Key/trilha/pedra/paredes: dados; itens: conhecimento |

`TIERS` = 7 fases **hipotéticas** (0 chegada; 1 + mísseis, Morph, Bombas; 2 + Space Jump; 3 + gelo; 4 +
Gravity, Wave, Thermal; 5 + Spider, Boost, Power Bombs; 6 + grapple, X-Ray, plasma). O passeio por fases
(`validate.tallon_tiers`) começa cada fase com os itens dela e pega os itens reais que alcança
(`items.GRANTS`); `FIRST_TIER` declara a fase de cada sala. Itens reais hoje: 9 mísseis, 2 E-tanks, Space
Jump (Alcove, `$A1`), X-Ray (Life Grove, `$AC`) — bits `$A0–$AC` (`tools/tallon/items.py`).

Regras do validador que dependem da fase declarada (vão mudar, ver decisão 5): `check_tallon_water` (salas
inundadas cuja fase não tem a Gravity Suit são andadas sem ela), `check_tallon_enemies` (justiça da fase 0:
todo inimigo de sala `FIRST_TIER` 0 morre com ≤ 5 tiros do Power Beam e toca ≤ 20).

Modelo de alcance (`tools/smlib/reach.py`): a pé (degrau 7, vão 7, medidos), água com/sem Gravity; com Space
Jump, flood fill de células abertas (o flood trata como sólido só o tipo `$8`, `validate.SOLID_TYPES`). **Morph
Ball não é modelada a pé** (`Loadout.morph`: "only meaningful with space_jump").

### Onde ficam esses itens no Prime (dados)

Lido nesta pesquisa: os objetos `Pickup` de todos os mundos (`research/prime_fs`, retro-data-structures, nome =
1º texto das propriedades; roteiro fora do projeto, `scratchpad/s09/pick.py`):

| Item do Prime | Mundo / sala (dados) |
|---------------|----------------------|
| Morph Ball (`p_morphball_01`) | Chozo Ruins / Ruined Shrine |
| Morph Ball Bombs (`P_Bomb`) | Chozo Ruins / Burn Dome (os outros `P_Bomb` são expansões de Power Bomb — conhecimento) |
| Ice Beam (`P_IceBeam_01`) | Chozo Ruins / Antechamber |
| Varia (`P_VariaSuit`), Charge (`P_Chargebeam_01`) | Chozo Ruins / Sunchamber, Watery Hall |
| Wave Beam (`P_Wavebeam_01`) | Phendrana / Chapel of the Elders |
| Gravity Suit (`P_GravitySuit`) | Phendrana / Gravity Chamber |
| Thermal (`P_Thermal_01`), Boost (`P_boostball_01`), Spider (`Spiderball`) | Phendrana / Research Core, Phendrana Canyon, Quarantine Cave |
| Grapple (`P_Grapple_01`) | Phazon Mines / Storage Depot B |
| Power Bombs (`P_Bomb`) | Phazon Mines / Central Dynamo (que é o principal: conhecimento) |
| Plasma (`P_Plasmabeam_01`) | Magmoor / Plasma Processing |
| Space Jump (`p_DoublejumpBoots_01`), X-Ray (`P_XRay_01`) | Tallon / Alcove, Life Grove (já na ROM) |

Phendrana não tem elevador para o Tallon (chega-se pela Magmoor: épico 07).

### Portas no SM (ROM `base/sm_fix.sfc` e C `vendor/sm/src`)

- Cabeçalho de PLM de porta = 3 palavras (setup, lista de instruções, lista de fechar): vermelha (parede
  direita) `$84:C88A` = `$C7B1, $C318, $C301`; setup `$C7B1` = `PlmSetup_Door_Colored` (`sm_84.c:2112`:
  escreve bloco `$C044`, tipo C BTS `$44`). Amarela `$C85A` → lista `$C014`, verde `$C872` → `$C19C`, cinza
  `$C842` → `$BE70` (bytes lidos).
- Lista da vermelha `$C318`: `8A72 C4B1` (GotoIfDoorBitSet, `sm_84.c:536`), `8A24 C32A` (SetLinkReg),
  `86C1 BD50` (SetPreInstr = `PlmPreInstr_GoToLinkInstrIfShotWithAnyMissile`, `sm_84.c:1838`), `0001 A8E7`
  (desenho fechado), `86B4` (Sleep); em `$C32A`: `8A91 05 C34E` (IncrementDoorHitCounterAndJGE: 5 acertos,
  `sm_84.c:547`), piscar, e a abertura em `$C34E`. Amarela/verde: a mesma forma, contagem 1 (`$C02A`:
  `8A91 01 C04B`; `$C1AE`: `8A91 01 C1CF`).
- O tiro chega à porta assim: bloco C BTS `$44` → PLM `$C83E` (tabela `$94:9EA6` + 2·`$44`, lida) =
  `PlmSetup_Door_Strange` (`sm_84.c:2129`), que põe no timer do PLM da porta
  `projectile_type & $1FFF | $8000` (`sm_84.c:2139`). O pré-instrução da porta só compara esse número:
  míssil `$100`, super `$200`, Power Bomb `$300`, bomba `$500` (`ida_types.h:700-703`); tiro de feixe =
  `equipped_beams | $8000` (`sm_90.c:3413`; carregado `& $100F | $8010`, `sm_90.c:3490`): os bits baixos são
  os feixes (Wave `$1`, Ice `$2`, Spazer `$4`, Plasma `$8`: Wave e Ice medidos abaixo, Plasma conhecimento).
- `$84:BD88` (`PlmPreInstr_GoToLinkInstrIfShotWithSuperMissile`, `sm_84.c:1861`) tem 42 bytes:
  `LDA $1D77,x; BEQ fim; AND #$0F00; CMP #$0200; BNE som; …(vai para o link)…; RTS; som: LDA #$57; JSL
  $8090CB; fim: STZ $1D77,x; RTS`. Trocando só os dois imediatos (`AND #$0F02 / CMP #$0002`) vira "abre só
  com tiro de feixe que tenha o gelo"; qualquer míssil/bomba (nibble alto ≠ 0) ou feixe sem o bit dá o som
  "dud" e não abre.
- Argumento da porta com bit 15 = **não lembra**: `GotoIfDoorBitSet` e `IncrementDoorHitCounterAndJGE`
  pulam o bit salvo quando o argumento é negativo (`sm_84.c:536-560`): a porta volta fechada a cada visita.
- Cores: o desenho de cada tampa usa metatiles CRE com a mesma figura (tiles `$300/$310`, cores 1–3) em 4
  linhas de paleta: `$00` p0 = **amarelo/laranja** (`ffb500 bd7300 632900`), `$04` p1 = **verde**, `$08` p2 =
  **vermelho**, `$0C` p3 = **azul** (CRE `$B9:A09D`, lido; cores iguais nos tilesets 0, 2 e 4). O azul (p3) é
  **a porta azul comum** (`tools/smlib/level.py:145`: tampas azuis = metatiles `$00C/$02C`) e o "piscar" das
  portas coloridas (`$A9B3`). A cinza usa `$0AE/$0CE` (p1, cores 5–7, malva escuro). Não sobra metatile CRE
  de porta numa 5ª cor.
- **Experimento no emulador** (cópia da ROM construída em `scratchpad/s09/`, roteiro `beamdoor_exp.py`): a
  lista `$C318` com o pré-instrução trocado por uma cópia de `$BD88` com os imediatos do gelo em `$84:F10F` e
  contagem 1; da rota `tallon_missil_abre_porta_vermelha` até a porta vermelha da Waterfall Cavern, 6 tiros:
  Power Beam → fechada (`$7ED8C6 = 0000`); mísseis → fechada; Wave só (`$09A6 = 1`) → fechada; **Ice
  (`$09A6 = 2`) → abre e a Samus entra na Crash Site** (`$079B = F139`); Ice+Wave (`= 3`) → abre. Fotos
  das 4 cores no mesmo lugar (`looks.png`): rosa-vermelho, azul (igual à porta comum), laranja, verde; a
  cinza aparece pouco contrastada no tileset 2.

### Blocos de Bomba e de Power Bomb (ROM e C)

- Tipo F (bloco de bomba): tiro, bomba e grapple caem em `BlockReact_BombableBlock` (`sm_94.c:1535`), PLM
  pela tabela `$94:A012` + 2·BTS (lida): BTS 0–3 → `$D0B8–$D0C4`, 4–7 → `$D0C8–$D0D4`, todos com setup
  `$CEDA` = `PlmSetup_RespawningBombBlock2` (`sm_84.c:2227`): quebra com bomba (`$500`) ou Power Bomb
  (`$300`); feixe e míssil não. Tocar correndo/Screw Attack: `PlmSetup_RespawningBombBlock`. Qual faixa
  de BTS volta a se fechar: conhecimento (0–3 voltam, 4–7 não), a filha confere no emulador.
- Tipo C BTS `$08/$09` → `$D084/$D088`, setup `$CF2E` = `PlmSetup_RespawningPowerBombBlock`
  (`sm_84.c:2250`): só Power Bomb quebra.
- PLMs de item visível = `$EED7 + 4·n` (`research/sm_room_format.md` §5): Power Bomb `$EEE3`, Bombas `$EEE7`,
  Ice `$EEEF`, Wave `$EEFB`, Gravity `$EF0B`, Plasma `$EF13`, Morph `$EF23` (o Morph em `$9E9F` conferido lá).

### Espaço (ROM construída, cauda de `$FF` por banco, lido)

`$84` livre a partir de `$84:F10F`: **3825 bytes** (o build não usa o `$84`). `$8F` 1821 (de `$8F:F8E3`),
`$83` 19294, `$A1` 3851, `$B4` 2490. Nível das salas no `$E0` até `$E0:FFA0`: **96 bytes**; a Parasite Queen
fica em `$E1:8000` posta por `put_in_bank` **depois** do nível (`tools/build.py:635`), e as estrelas do
hangar também por `put_in_bank` no meio do nível (`build.py:496`): se o nível crescer, a Queen muda de banco
sozinha, nunca testado.

## Mudança proposta

### Decisão 1 — Quais itens de trava (Prime → SM)

Regra: item nativo do SM quando existe e a trava faz sentido com a física do SM; sem equivalente, a trava
sai (fica só a que o SM sabe fazer), em vez de inventar item. Menos itens = menos mecanismos.

| Habilidade do Prime | No SM | Decisão | Por quê |
|---------------------|-------|---------|---------|
| Morph Ball | Morph Ball (`$EF23`) | **entra** | Bombas e Power Bombs só existem em bola; túnel de 1 bloco |
| Morph Ball Bombs | Bombs (`$EEE7`) | **entra**: trava da Gully = **blocos de bomba** (tipo F) num túnel de Morph, no lugar da cinza | os "Breakable Block" do Prime (dados) |
| Ice Beam | Ice Beam (`$EEEF`) | **entra**: 9 ligações com **porta de gelo** (decisão 2) | |
| Wave Beam | Wave Beam (`$EEFB`) | **entra**: 5 ligações de condutor viram **porta de onda** | o Wave carrega o condutor no Prime |
| Thermal Visor | — | **sai**: os condutores pedem só o Wave | o SM não tem visor térmico; o Thermal só mostrava o painel |
| Gravity Suit | Gravity Suit (`$EF0B`) | **entra**: o anteparo da Vent C (já medido na água, 07l) | |
| Plasma Beam | Plasma Beam (`$EF13`) | **entra**: porta da Arbor (Root Cave L0) vira **porta de plasma** | |
| Grapple Beam | Grapple (existe) | **sai** da trava da Arbor | com Space Jump, no SM nada exige o grapple pela geometria (o flood fill já passa); seria item sem uso |
| X-Ray Visor | X-Ray (já no Life Grove) | fica como **prêmio**, sem trava | a plataforma invisível da Arbor não tem equivalente (o X-Ray do SM mostra blocos especiais, não torna bloco sólido visível); a borda de Space Jump já segura |
| Spider Ball | — | **sai** | a porta do Life Grove Tunnel fica embaixo no GTH (desvio da 07m): não há trilha a subir |
| Boost Ball | — (Speed Booster custaria pista e modelo de corrida) | **sai** | |
| Power Bomb | Power Bomb (`$EEE3`) | **entra**: as **paredes de Power Bomb** em volta do X-Ray no Life Grove (tipo C BTS `$08/$09`, a que não volta, conferida no emulador na 09e) | dados: 5 "Destroyable Wall" + "Power Bomb Scan Hint" em volta do X-Ray |
| Space Jump | Space Jump (`$EF1B`) | já está (Alcove) | |
| Missile | Missile Expansion | já está | |
| Charge, Varia, Super Missile, Phazon Suit, combos, Scan | — | fora | nenhuma trava do Tallon pede |

**Itens de trava novos: 7** — Morph Ball, Bombas, Ice, Wave, Gravity Suit, Power Bomb, Plasma. Com os 13 do
Tallon: 20 itens.

Travas depois da etapa (substitui a tabela de hoje):

| Ligação | Itens | Mecanismo |
|---------|-------|-----------|
| 3 portas vermelhas | míssil | igual |
| Crash ↔ Overgrown | gelo + Space Jump | **porta de gelo** dos dois lados + borda (igual) |
| Crash ↔ Frigate Access, Overgrown ↔ Tunnel C, Tunnel C ↔ Chozo East, GTH ↔ Tunnel D/E, Tunnel D ↔ Chozo South, Tunnel E ↔ Mines East | gelo | **porta de gelo** dos dois lados |
| GTH ↔ Life Grove Tunnel | gelo | **porta de gelo** dos dois lados (sem Spider/Boost/PB) |
| Root Cave ↔ Arbor | plasma + Space Jump | **porta de plasma** (Root Cave) + borda (igual) |
| as 5 de condutor | Wave | **porta de onda** nos mesmos lados das cinza de hoje |
| Vent C ↔ Vent B | Gravity | igual (geometria) |
| Tallon Canyon ↔ Gully | Morph + Bombas | **sem tampa** (porta azul); túnel de Morph com 2 blocos de bomba na Canyon, antes da plataforma sob a T3 |
| LS ↔ Gully/Alcove, GTH ↔ GTC | Space Jump | igual |
| (Life Grove, item) | Power Bomb | blocos de Power Bomb em volta do X-Ray (não é porta) |

Nenhuma porta "nunca abre" fica no Tallon (`LOCK_OF` sem `grey`; o validador passa a recusar cinza no Tallon).

### Decisão 2 — Portas de feixe: PLM próprio em `$84` (não remapear)

Remapear para as portas do SM não serve: verde abre com super míssil, amarela com Power Bomb, cinza nunca —
o jogo não tem super míssil, e Power Bomb chega quase no fim; nenhuma abre com um feixe. A porta de feixe é
barata (a ROM já tem tudo menos uma comparação):

- **Código** (`$84`, a partir de `$84:F10F`): 3 pré-instruções, cópias dos 42 bytes de `$84:BD88` com os
  imediatos `AND #$0F00|m` / `CMP #m`: gelo m = `$0002`, onda `$0001`, plasma `$0008`.
- **Listas de instruções** (só paredes laterais: as 26 tampas de feixe do Tallon são todas L/R — 18 de gelo,
  7 de onda, 1 de plasma, conferido em `LINKS`): por feixe e lado, `8A72 C4B1` · `8A24 L` · `86C1 <pré>` ·
  `0001 <desenho fechado da cor>` · `86B4` · `8724 <o Sleep>` · L: `8A91 01 <abertura vanilla da cor>`
  (27 bytes). Cabeçalho de 6 bytes = setup `$C7B1` + a lista nova + a lista de fechar vanilla da cor.
  Porta de chão/teto de feixe: erro no build (não existe; se um dia existir, nova spec).
- **Cores** (só as que existem; o azul p3 é a porta comum e não pode): **gelo = verde** (desenho e abertura
  da verde `$C872/$C878`), **plasma = laranja** (da amarela `$C85A/$C860`; o plasma do Prime é laranja-vermelho),
  **onda = cinza** (da cinza `$C842/$C848`: na fragata afundada, tileset 4, é a "porta sem energia" que o Wave
  carrega — o papel do condutor). Desvio do Prime anotado: gelo branco e onda roxa no Prime. A vermelha
  (míssil) não muda. Cor nova (paleta própria) fica fora (ver Fora de escopo).
- **Argumento `$8000`** (não lembra, nenhum bit de porta): fecha de novo a cada visita, como as portas de
  cor do Prime; os escudos de míssil continuam lembrados (como no Prime). Sem softlock: um feixe nunca se
  perde, e entrando por uma porta de feixe a Samus já tem o feixe dela.
- **Custo**: ~126 + 6×27 + 6×6 ≈ **330 bytes no `$84`** (3825 livres); `$8F`: 0 (as 26 entradas de PLM cinza
  só trocam de id); nível: 0 (as tampas já são blocos de tampa azul sob o PLM, como a cinza); `$83`: 0.
- Evidência: o experimento acima (gelo abre só com gelo; Power Beam, míssil e Wave não; combinação com gelo
  abre).

### Decisão 3 — Lugar de cada item e ordem

Regra de lugar: **cada elevador de enfeite guarda o item "que viria de lá"** (o mundo do Prime onde o item
está, dados acima); as Bombas, item Chozo, ficam no templo Chozo; o gelo, que no Prime vem depois do Space
Jump, numa borda de Space Jump. Todos num **lugar já existente** (só PLM de item: nenhum nível muda por item).

| # (linha de `items.py`) | Item | Bit | Sala | Lugar (bloco) | Porquê |
|---|------|-----|------|---------------|--------|
| 13 | Ice Beam | `$AD` | Root Cave | (4, 9), na prateleira da porta da Arbor, ao lado do míssil (6, 9) | só com Space Jump; o jogador vê ali a porta laranja que pede outro feixe |
| 14 | Wave Beam | `$AE` | Transport to Magmoor East | (9, 25), no chão | Phendrana se chega pela Magmoor |
| 15 | Gravity Suit | `$AF` | Transport to Chozo Ruins East | (12, 25), sobre a plataforma do elevador | beco no fim do ramo de gelo de C, antes da água da região D |
| 16 | Plasma Beam | `$B0` | Transport to Chozo Ruins South | (6, 25), no chão | beco da região E (o Magmoor East já tem o Wave) |
| 17 | Morph Ball | `$B1` | Transport to Chozo Ruins West | (8, 25), sobre a plataforma do elevador | primeiro elevador do Prime, rumo à Chozo Ruins; Morph cedo, como no Prime |
| 18 | Bombas | `$B2` | Artifact Temple | (13, 53), no chão entre os totens | templo Chozo, atrás da porta vermelha da Temple Security |
| 19 | Power Bomb | `$B3` | Transport to Phazon Mines East | (6, 25), no chão | Mines |

Lugares conferidos nesta pesquisa (bloco de ar, chão embaixo, 2 blocos livres em cima; distância às portas ≥ 2).
Bits = `$A0` + linha, fixos; as 7 linhas entram juntas na 09b (as ainda sem lugar com `spot=None`, como a
tabela já permite), para nenhum bit mudar entre filhas. Os itens de trava usam o vetor de itens `$7ED870`
(não confundir com os bits de porta vermelha `$B0–$B2` do vetor `$7ED8B0`).

**Ordem (rodadas)** — rodada k = o que se alcança com os itens pegos nas rodadas anteriores (decisão 4):

| Rodada | Itens que a Samus tem | Salas novas | Itens pegos |
|--------|-----------------------|-------------|-------------|
| 0 | Power Beam | Landing Site, Canyon Cavern, Tallon Canyon, Tunnel A, Chozo West, Temple Hall, Temple Security, Waterfall Cavern, Root Tunnel (9) | míssil da Landing Site, **Morph Ball** |
| 1 | + mísseis, Morph | Temple Lobby, Artifact Temple, Crash Site, Root Cave, Tunnel B, Magmoor East (6) | **Bombas**, **Wave**, mísseis da Crash Site e do Tunnel B |
| 2 | + Bombas, Wave | Gully, Alcove (2) | Space Jump |
| 3 | + Space Jump | — | **Ice**, míssil da Root Cave |
| 4 | + gelo | Overgrown, Tunnel C, Chozo East, Frigate Access, Vent C (5) | **Gravity Suit**, míssil da Overgrown |
| 5 | + Gravity Suit | as outras 13 de D, GTH, GTC, Tunnel D, Tunnel E, Chozo South, Mines East, LGT, Life Grove (21) | E-tanks da Cargo Lift e da Hydro, mísseis da Biohazard, GTC e LGT, **Power Bomb**, **Plasma** |
| 6 | + Power Bomb, plasma | Arbor Chamber (1) | X-Ray, míssil da Arbor |

44 salas, 20 itens. Sequência que o jogador sente: Morph → mísseis → Bombas (e o Wave, que só serve na
fragata) → Space Jump → gelo → Gravity → Power Bombs e plasma → X-Ray (a do Prime: mísseis, Morph, Bombas,
Space Jump, Wave, gelo, Gravity, Power Bombs, plasma, X-Ray).

O míssil da Landing Site **continua no lago, a pé** (desvio da 07h): pô-lo atrás de um túnel de Morph, como no
Prime, mudaria a Landing Site e as rotas cegas de 5 testes sem abrir nada novo (o Morph já tem uso nas Bombas).

### Decisão 4 — Modelo de alcance e validador

`tools/smlib/reach.py`:
- `Loadout` ganha `morph`, `bombs`, `power_bomb` a pé. **Bola**: estado (x, y) com 1 bloco de corpo livre e
  chão embaixo; rola ±1, cai; vira bola no lugar de pé; desfaz a bola só com 3 linhas livres. **Sem** pulo em
  bola, bomb jump (IBJ), wall-jump, corrida: o caminho obrigatório nunca pede técnica (como 07b). Item pego
  pela célula do corpo da bola também.
- Grade por equipamento (`foot_grid(r, l1, loadout)` e o `passable` do flood): bloco F → ar com `bombs` ou
  `power_bomb`; C BTS `$08/$09` → ar com `power_bomb`; sem o item, sólidos (hoje o flood os deixa passar).
  Flood fill (Space Jump) só com `morph` (erro senão: célula de 1 bloco pressupõe a bola).
- `self_test` +: túnel de 1 linha passa só com Morph; bola não sobe degrau de 1; desfazer a bola num vão de
  2 linhas não dá; bloco de bomba sólido sem Bombas, ar com elas; bloco de PB idem.

`tools/validate.py` e `tools/tallon/rooms.py`:
- `MOVEMENT` vira `GEOMETRY = {space_jump, gravity, morph, bombs, power_bomb}`: itens que a geometria da
  sala decide (o passeio não os pede na porta); `Gate.ledge` passa a significar "lado atrás de geometria".
  A regra da borda generaliza: sem os itens de geometria da trava, a porta é inalcançável de toda entrada que
  não esteja atrás da mesma geometria; com eles, alcançável. `LOCK_OF = {missile, ice, wave, plasma}`.
- `check_breakables` (novo): todo bloco de bomba toca (vizinho de 4) uma célula de bola alcançável com as
  Bombas; todo bloco de PB fica a ≤ 2 blocos de uma; nenhum fora disso (quebraria sem querer ou nunca).
- **Rodadas** (09f): `TIERS` (fases hipotéticas) sai; o passeio começa só com o Power Beam, anda tudo, junta
  os itens alcançados e só os usa na rodada seguinte, até nada mudar. Declarado: `FIRST_ROUND` por sala e
  `Item.round` (no lugar de `FIRST_TIER`/`Item.tier`); o validador compara com a tabela acima.
- **Prova final** (09f): (1) da nave, as 44 salas e os 20 itens alcançados; (2) **sem ponto sem volta**: em
  cada rodada, de todo estado (sala, entrada) alcançado, com os itens daquela rodada, a nave é alcançável
  (busca a partir de cada estado); (3) `reach.stuck` de cada sala com o equipamento de cada rodada em que ela
  é visitada (hoje só com o da chegada).
- Regras que usavam a fase declarada passam a usar **o que a Samus tem quando chega à sala pela primeira vez**
  (o passeio registra): `check_tallon_water` (anda sem a suit as salas inundadas alcançadas antes da Gravity:
  só a Vent C) desde a 09b; justiça dos inimigos (07i) para as salas alcançadas só com Power Beam, mísseis e
  Morph (rodadas 0–1) desde a 09d.
- `check_gates` (ROM): cada tampa de feixe tem o PLM certo (id do lado e da cor, argumento `$8000`); nenhuma
  cinza no Tallon. `check_tallon_items`: os 7 PLMs novos e os bits `$AD–$B3`.

### Decisão 5 — Testes

- Um teste de emulador **por mecanismo**, que **pega o item andando para dentro dele** (`pick_up`) e **usa-o
  na trava** dele (chegando à sala do item por teleporte de porta quando a rota a pé é longa, documentado):
  porta de gelo, de onda, de plasma (com feixe errado antes: continua fechada), Gravity (passa o anteparo da
  Vent C), Morph + Bombas (rola, bomba os blocos da Canyon, sobe para a Gully), Power Bomb (quebra as paredes
  e pega o X-Ray).
- **Ponta a ponta** (09f, `tallon_cadeia_completa`): da nave, na ordem das rodadas, pega os 20 itens andando
  para dentro de cada um e passa cada trava pelo mecanismo real (mísseis na porta vermelha, bombas, tiro de
  cada feixe, pulo debaixo d'água com a suit, Power Bomb); entre trechos, teleporte de porta (`door_teleport`)
  só por portas já abertas ou sem trava, cada um anotado. No fim: os 20 bits de item, `$09A4`/`$09A8` com os 7
  itens + Space Jump + X-Ray, 45 mísseis, 299 de energia; salva na nave, game over, continue: tudo volta.

### Decisão 6 — Banco do nível antes de mexer em nível

Só duas salas mudam de nível nesta etapa (Tallon Canyon na 09d, Life Grove na 09e) e o `$E0` tem 96 bytes.
Antes delas (09c): o que vai por DMA (estrelas do hangar, arte da Parasite Queen) passa a um alocador próprio
num banco fixo (`$F0:8000`), fora do fluxo do nível; o nível (com o texto e as paletas) segue linear a partir
de `$E0:8000` e pode cruzar de banco (o descompressor cruza: `research/sm_room_format.md` §0, sala vanilla
`$ADAD`). Assim o crescimento do nível nunca move a Queen.

### Filhas (rápido → complexo)

| # | Spec | Entrega | Esforço | Depende de |
|---|------|---------|---------|------------|
| 09a | [Portas de feixe](09a-portas-de-feixe.md) (**verificada**; desvio: lista de fechar própria, 462 bytes) | 3 pré-instruções + 6 listas + 6 cabeçalhos em `$84` (`tools/tallon/beamdoors.py` ou no build); `LOCK_OF` ice/wave/plasma; Thermal, Spider, Boost, grapple e X-Ray saem de `GATES`/`TIERS` (Life Grove Tunnel, Life Grove e os 2 itens deles: fase 5 → 4); `check_gates` com as cores e `$8000`, sem cinza no Tallon. Testes com o feixe posto por RAM: `porta_de_gelo` (Crash Site → Frigate Access: Power Beam e míssil não abrem, gelo abre, passa; volta pelo outro lado), `porta_de_onda` (Reactor Core → Reactor Access), `porta_de_plasma` (Root Cave → Arbor); foto das 3 cores | 1,5 d | — |
| 09b | [Itens de feixe e Gravity Suit](09b-itens-de-feixe-e-gravity.md) (**verificada**; desvio: a cena da Gravity Suit deixa a Samus onde pegou, `$91:D64E`: a vanilla a punha dentro da parede da Chozo East) | as 7 linhas novas em `items.py` (bits `$AD–$B3`), lugar das 4: Ice, Wave, Gravity, Plasma; `GRANTS`; `check_tallon_water` pelo "primeiro a chegar"; `FIRST_TIER` refeito (o que fica real cai de fase). Testes: `tallon_gelo` (pega o gelo na Root Cave, com Space Jump por RAM, e abre a porta de gelo), `tallon_onda`, `tallon_gravity` (pega na Chozo East e passa o anteparo da Vent C), `tallon_plasma` (pega na Chozo South e abre a porta da Arbor) | 1 d | 09a |
| 09c | [Segurança do banco de dados de sala](09c-banco-de-salas.md) (**verificada**; desvio: paletas e TALLON IV também no fixo; nível `$E0–$EF`, 500169 livres; fixo `$F0–$FF`, 502980 livres; teste `nivel_cruza_banco_<sala>`, experimento `--cruzar-banco hangar` 47/47) | alocador DMA em `$F0:8000` (Queen, estrelas); validador: nenhum asset de DMA no fluxo do nível, nenhum cruza banco, aviso de qual sala cruza `$E0/$E1`; experimento único com enchimento forçando uma sala a cruzar banco (os 39 testes passam; anotado em Desvios); teste `tallon_sala_cruza_banco` gerado do manifest sempre que alguma sala cruzar | 0,5–1 d | — |
| 09d | [Morph Ball e Bombas](09d-morph-e-bombas.md) (**verificada**; desvios: bloco de bomba = metatile `$058`, BTS 4; T3 passagem aberta; cada item de geometria necessário sozinho; volta à nave por rodada já aqui) | bola e blocos de bomba no `reach.py` (+ `self_test`); `GEOMETRY` e a regra de borda generalizada; `check_breakables`; Tallon Canyon: túnel de Morph com 2 blocos de bomba (F, BTS que não volta, conferido no emulador) antes da plataforma da T3, T3 vira porta azul; Morph e Bombas nos lugares; justiça dos inimigos pelas rodadas 0–1. Testes: `tallon_morph_e_bombas` (pega o Morph na Chozo West andando, as Bombas no Artifact Temple, bomba os blocos, sobe pela T3 à Gully); mudanças de expectativa das rotas cegas que passam pela Chozo West (`tallon_rota_mvp`, `tallon_mapa_salvo`, `tallon_rota_bc` pegam o Morph: `$09A4` = `$0004`, trechos remedidos) | 2–2,5 d | 09c (nível da Canyon), 09b |
| 09e | [Power Bombs e as paredes do X-Ray](09e-power-bombs-e-xray.md) (**verificada**; desvios: cabana de 15 blocos de PB com teto, tipo C metatile `$057` BTS `$09` medido; `Item.needs` + `check_item_geometry`; X-Ray só no `tallon_power_bomb`) | bloco de PB no modelo; Life Grove: paredes de PB (C BTS `$09`) em volta do X-Ray; Power Bomb na Mines East. Testes: `tallon_power_bomb` (pega na Mines East, põe a PB no Life Grove, pega o X-Ray); `tallon_grande_arvore` muda (pega a PB na Mines East antes do X-Ray) | 1–1,5 d | 09c, 09d |
| 09f | [Rodadas declaradas e a cadeia completa](09f-rodadas-e-cadeia-completa.md) (**verificada**; desvios: volta vazia descartada (não é rodada nem erro); `stuck` por rodada só a pé (com Space Jump, flood fill); volta à nave por RAM no teste; subida real da Root Cave com o Space Jump) | rodadas (`FIRST_ROUND`, `Item.round`; `TIERS` sai), volta à nave por rodada, `stuck` por rodada, linha do Tallon "alcançáveis agora: 44, 20 itens em 7 rodadas"; teste `tallon_cadeia_completa`; README, HANDOFF, épico 07 (definição de pronto cumprida → `verificada`) | 1,5–2 d | 09a–09e |

**MVP = 09a + 09b + 09c + 09d**: com elas o Tallon inteiro é jogável a pé — as 44 salas e os 13 itens do Tallon
alcançáveis da nave (o passeio por fases dá `FIRST_TIER` 0 a todas as salas: prova de alcance sem itens
hipotéticos). 09e acrescenta a trava de Power Bomb do Prime (o X-Ray, até lá, fica no chão aberto); 09f faz a
prova forte (ordem, nenhum ponto sem volta) e o teste ponta a ponta, e fecha o épico 07.

```
09a ──> 09b ──┐
09c ──────────┼──> 09d ──> 09e ──> 09f
              └────────────────────^ (09f depende de todas)
```

Por que nesta ordem: 09a é código pequeno e isolado com experimento já feito, e sozinha não muda nada
jogável (as portas trocam de cinza para feixe, ainda sem o feixe). 09b só põe PLMs de item (nenhum nível muda).
09c prepara o banco antes da primeira mudança de nível. 09d é a maior (modelo de bola + geometria + testes
cegos remedidos). 09e repete o mecanismo de 09d para a PB. 09f prova tudo junto e muda o validador de fases
para rodadas quando não há mais item hipotético.

## Critérios de aceite (do épico; cada filha detalha os seus)

1. `python3 -I tools/validate.py` → 0 problemas; linha do Tallon com "alcançáveis agora: 44" e os 20 itens em
   7 rodadas iguais às da decisão 3. (protege = ordem, alcance, travas, volta à nave; falha_quando = mutações do
   critério 2; não_prova = técnicas que o modelo não supõe)
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) sem o Morph → Bombas,
   Gully e tudo depois inalcançáveis; (b) gelo dentro da Overgrown (atrás de porta de gelo) → círculo, salas
   inalcançáveis; (c) blocos de bomba da Canyon viram ar → Gully na rodada 1 (a trava não segura); (d) bloco de
   bomba sem vizinho de bola → `check_breakables`; (e) sem as paredes de PB → X-Ray na rodada 5; (f) porta de
   gelo com o PLM de onda (ROM) → `check_gates`; (g) uma queda sem volta numa sala alcançável → volta à nave;
   (h) saída de túnel de Morph num vão de 2 linhas → `stuck`; (i) rodada declarada errada → aviso; (j) Gravity
   na Vent B (atrás do anteparo) → região D inalcançável; (k) `self_test` com a bola subindo degrau → falha;
   (l) flood fill sem Morph → erro.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds; espaço por banco anotado (`$84`
   ~330 bytes; `$8F` ~60).
4. `python3 -I tests/run_tests.py` → os 39 de antes (com as mudanças de expectativa anotadas nas filhas) + os
   novos: 3 portas (09a), 4 itens (09b), sala que cruza banco (09c, se houver), Morph+Bombas (09d), Power Bomb
   (09e), cadeia completa (09f).
5. Fotos olhadas: as 3 portas de feixe fechadas e abrindo, os blocos de bomba e de PB antes/depois, cada item
   no lugar, a mensagem de cada item novo.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| reach.self_test | bola, desfazer a bola, blocos de bomba/PB por equipamento | +8 casos |
| validate.py | `check_breakables`, rodadas, volta à nave, `stuck` por rodada; `check_gates`/`check_tallon_items` estendidos; regra de geometria | +3 checagens, 4 alteradas |
| mutação à mão | (a)–(l) do critério 2, mais as de cada filha | ≥ 12 |
| build | sha1 igual em dois builds | 1 por filha |
| run_tests.py (emulador) | portas de gelo/onda/plasma, gelo/onda/gravity/plasma pegos e usados, Morph+Bombas, Power Bomb, cadeia completa, sala que cruza banco | +11 (≈3 com expectativa alterada) |
| imagem | portas, blocos, itens | ~20 |

## Riscos e reversão

- **Código novo no `$84`** (pré-instrução da porta): é uma cópia de 42 bytes vanilla com dois imediatos
  trocados, provada no emulador (experimento acima). O Plasma (`$8`) não foi medido: o teste da 09a mede.
- **Cores fora do Prime**: gelo verde e onda cinza (no Prime, branco e roxo); o jogador do SM pode achar que a
  verde pede super míssil. Fica anotado; uma cor nova pediria metatiles e linha de paleta própria nos tilesets
  0/2 (as cores 1–3 da linha 7 parecem livres, `c6c6c6`, não conferido): fora de escopo.
- **Rotas cegas dos testes**: o Morph na Chozo West entra no caminho de 3 testes (mensagem de item, ciclos
  medidos). Se o remedir não fechar, o Morph vai para o alto do poço do elevador (mesma sala), ainda a pé.
- **Banco `$E0`**: o nível vai cruzar para o `$E1`; o descompressor cruza (vanilla), mas no projeto nunca foi
  exercitado: a 09c isola a Queen e força um cruzamento uma vez antes das salas mudarem.
- **Modelo sem técnicas**: wall-jump, bomb jump (IBJ) e gelo nos inimigos deixam pular a ordem (quebra de
  sequência). Não prendem: toda volta é pelo mesmo caminho com o que já se tem, e o validador prova a volta à
  nave só para o caminho sem técnica.
- **Combinação de feixes do SM**: com gelo+onda+plasma ligados, um tiro abre qualquer porta de feixe (o Prime
  troca de feixe). Aceito (é o SM).
- **Prime incerto** (herdado de 07k/07m): cores das portas "Key", a necessidade de Space Jump nas bordas.
- Reversão: tudo vem de `tools/`; cada filha reverte os arquivos dela e reconstrói. A 09a sozinha volta às
  cinza trocando `LOCK_OF`.

## Fora de escopo

- Charge, Varia, Super Missile, Grapple, Spider, Boost, Thermal, Scan, Hi-Jump, Speed Booster, Spring Ball,
  Screw Attack, Spazer, Reserve; Phazon Suit e combos.
- Cor nova para as portas de gelo/onda (paleta própria); porta de feixe de chão/teto.
- Míssil da Landing Site atrás de túnel de Morph; labirinto de Morph da Hydro Access; túnel de Morph da
  Waterfall Cavern (incerto); plataforma invisível e grapple da Arbor.
- Água das poças de A–C e E; camadas de evento; artefatos; elevadores funcionando; outros mundos.
- Mostrar itens no mapa de pausa.

## Definição de pronto do épico

- As 6 filhas `verificada`, com validate + build + testes rodados por quem revisa.
- Da nave, só com o Power Beam, a pé: as 44 salas e os 20 itens (13 do Tallon + 7 de trava), na ordem das
  rodadas, sem ponto sem volta (validador) e no emulador (`tallon_cadeia_completa`).
- Nenhuma porta "nunca abre" no Tallon.
- Épico 07: o ponto "pega os 13 itens" cumprido, estado `verificada`; README e HANDOFF atualizados.

## Desvios (preenchido na implementação)

- Fechamento (09f, 23/10/2026), conferido contra a definição de pronto: (1) as 6 filhas `verificada`; (2) da nave, só com o Power
  Beam, a pé: as 44 salas e os 20 itens nas 7 rodadas da decisão 3, declaradas (`FIRST_ROUND`, `Item.round`) e conferidas pelo
  validador, com volta à nave e `stuck` em cada rodada (0 problemas), e no emulador (`tallon_cadeia_completa`: os 20 itens pegos
  andando, a trava de cada rodada aberta pelo meio certo, salvo e continuado); (3) nenhuma porta "nunca abre" no Tallon
  (`check_gates`); (4) épico 07 fechado; README e HANDOFF atualizados. Estado → `verificada`.
- Decisão aberta da 09f: o passeio para na primeira volta sem sala nova e sem item novo; essa volta não é rodada nem erro (o
  X-Ray dá `xray`, que nenhuma trava usa).
- Critério 4 do épico: a bateria tem 49 testes (os 39 de antes + 3 portas, 4 itens, Morph+Bombas, Power Bomb, cadeia completa;
  o de banco cruzado só existe quando um nível cruza banco, nenhum no build normal).
