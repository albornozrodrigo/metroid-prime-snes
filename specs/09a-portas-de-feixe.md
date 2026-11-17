# 09a — Portas de feixe (gelo, onda, plasma)

Estado: verificada (23/10/2026: validate 72/148/0 com "alcançáveis agora: 15"; .ips sha1 `3f6e03c0…f7e2` igual em dois builds; 42/42 testes)
Esforço estimado: 1,5 dia (código no `$84` 0,25 d; tabelas e validador 0,5 d; testes no emulador 0,5 d; verificação 0,25 d)
Épico: [09 — Itens de trava](09-itens-de-trava.md) (decisão 2; decisão 1 para o que sai de `GATES`/`TIERS`)

## Contexto

Hoje as 26 tampas de gelo, onda (condutor) e plasma do Tallon são a porta cinza "nunca abre" do SM. O épico
decidiu trocá-las por **portas de feixe**: um PLM próprio em `$84` que só abre com tiro de um feixe. Esta
filha põe as portas; os feixes chegam na 09b, então para o jogador nada muda ainda (as portas continuam sem
abrir sem o feixe). Os testes dão o feixe por RAM.

## Estado atual (verificado)

Lido nesta filha na ROM base (`base/sm_fix.sfc`) e no C (`vendor/sm/src`):

- Cabeçalhos das portas de cor (3 palavras: setup, lista principal, lista de fechar):
  cinza R `$C842` = `$C794 $BE70 $BE59`, L `$C848` = `$C794 $BED9 $BEC2`; amarela R `$C85A` = `$C7B1 $C014
  $BFFD`, L `$C860` = `$C7B1 $C077 $C060`; verde R `$C872` = `$C7B1 $C19C $C185`, L `$C878` = `$C7B1 $C1FB
  $C1E4`; vermelha R `$C88A` = `$C7B1 $C318 $C301`.
- **A lista de fechar não termina: tem 23 bytes de quadros (`0002 A677 · 0002 … · 8C19 08 · … · 0001
  <fechada>`) e cai na lista principal logo depois** (`$C185 + 23 = $C19C`, `$BE59 + 23 = $BE70`, igual nas
  oito). Ela é usada quando a Samus entra por essa porta: `CheckIfColoredDoorCapSpawned`
  (`sm_82.c:4270`) troca a lista do PLM pela de fechar se o argumento é negativo ou o bit não está ligado.
  Consequência para o desenho do épico ("a lista de fechar vanilla da cor"): usada como está, a porta de
  gelo fechada atrás da Samus viraria a verde vanilla (super míssil). **Cada porta de feixe precisa de uma
  cópia dos 23 bytes de fechar, seguida da lista nova.**
- Quadros e aberturas (bytes): fechada R/L — verde `$A827/$A857`, amarela `$A767/$A797`, cinza `$A6A7/$A6D7`;
  abertura (alvo de `8A91 01`) — verde `$C1CF/$C22E`, amarela `$C04B/$C0AE`, cinza `$BEAD/$BF16`; todas
  começam com `8C19 07` (som) e terminam em `86BC` (apaga o PLM). `GotoIfDoorBitSet` das portas R vai para
  `$C4B1`, das L para `$C4E2`.
- `$84:BD88` (42 bytes, `bd 77 1d f0 21 29 00 0f c9 00 02 d0 12 …`): `AND #$0F00` em +5, `CMP #$0200` em +8
  (épico). Desvios relativos e endereços absolutos (`$1D77,x`, `$7EDEBC,x`): o código pode ser copiado.
- `$84` da ROM construída: `$FF` de `$84:F10F` a `$84:FFFF` (3825 bytes); o build não escreve no `$84`.
- Tampas a trocar (`build_rooms`, lado com `lock = "grey"`, conferido): **gelo 18** (9 R, 9 L, as duas do
  Life Grove Tunnel incluídas), **onda 7** (2 R, 5 L), **plasma 1** (L, Root Cave). Fica cinza só a T3 da
  Tallon Canyon (Bombas, 09d).
- Baseline: validate 72 salas / 148 portas / 0 problemas (alcançáveis agora: 15); `.ips` sha1
  `27828fae3277b076cc5611dbdaf56f5cdb3bebe3`; 39/39 testes.

## Mudança proposta

### 1. Código em `$84` (`tools/tallon/beamdoors.py`, chamado pelo build)

Endereços fixos a partir de `$84:F10F` (layout calculado na importação, para o validador e os testes):

- 3 pré-instruções (42 bytes cada): cópia de `$84:BD88` com `AND #($0F00|m)` / `CMP #m`; gelo m = `$0002`,
  onda `$0001`, plasma `$0008`. Gelo `$F10F`, onda `$F139`, plasma `$F163`.
- 6 blocos de 50 bytes (feixe × lado R/L, a partir de `$F18D`): 23 bytes de fechar copiados da cor + lista
  principal de 27 bytes: `8A72 <C4B1|C4E2>` · `8A24 L` · `86C1 <pré>` · `0001 <fechada>` · `86B4` (Sleep) ·
  `8724 <o Sleep>` · L: `8A91 01 <abertura vanilla>`.
- 6 cabeçalhos (6 bytes): `$C7B1` (setup das portas de cor: bloco C BTS `$44`), lista principal, bloco
  (lista de fechar). **Os ids de PLM das portas de feixe são esses cabeçalhos.**
- Cores: gelo = verde, onda = cinza, plasma = amarela/laranja (épico). Total: 126 + 300 + 36 = **462 bytes**
  (o épico estimou ~330 sem as cópias de fechar).
- O build confere os bytes vanilla que copia (cabeçalho, fechar caindo na lista, `0001 <fechada>`, `8A91 01`,
  imediatos de `$BD88`) e que o espaço está livre; erro se algo diferir.

### 2. Travas (`tools/tallon/rooms.py`)

- `LOCK_OF = {missile: "missile", ice: "ice", wave: "wave", plasma: "plasma", bombs: "grey"}`.
- Saem de `GATES` (decisão 1 do épico): Thermal (as 5 de condutor pedem só o Wave), grapple e X-Ray (Arbor:
  plasma + Space Jump), Spider/Boost/Power Bomb (Life Grove Tunnel: só gelo). Constantes `THERMAL`,
  `GRAPPLE`, `SPIDER`, `BOOST` saem (o `XRAY` fica: é o que o X-Ray dá).
- `TIERS` (números mantidos até as rodadas da 09f): 4 "+ Gravity Suit, Wave Beam"; 5 "+ Power Bombs" (o
  que as paredes do X-Ray pedirão na 09e; nenhuma trava pede ainda); 6 "+ plasma".
- `FIRST_TIER`: Life Grove Tunnel e Life Grove 5 → 4; `items.py`: míssil do Life Grove Tunnel e X-Ray 5 → 4.
  Arbor e o míssil dela continuam 6.

### 3. Build (`tools/build.py`)

Tampa com `lock` de feixe: PLM `beamdoors.PLM[(feixe, lado)]`, argumento `$8000` (não lembra: fecha a cada
visita). Porta de feixe de chão/teto: erro no build.

### 4. Validador (`tools/validate.py`)

- `check_gates` (ROM): cada tampa de feixe com o PLM do feixe e do lado e argumento `$8000`; cinza no Tallon
  só na trava de Bombas; os 462 bytes do `$84` iguais aos que `beamdoors` gera da ROM base (pré-instrução,
  listas, cabeçalhos).
- Linha do Tallon e o resto: iguais (alcançáveis agora: 15; as travas de feixe pedem os feixes, que ainda
  não existem como item).

### 5. Testes no emulador (`tests/run_tests.py`)

Preparação (documentada no teste): nave → pouso; estação 1 por RAM; feixe e mísseis postos por RAM
(`$09A6/$09A8`, `$09C6/$09C8`; os itens chegam na 09b); a sala da porta pelo teleporte de porta, entrando
**por ela** (ela fecha atrás da Samus: a lista de fechar nova). Em cada teste: andar contra a tampa → x da
Samus encostada (`$25` na L, `(largura − 2)·16 − 5` na R); Power Beam, mísseis e o feixe errado → mesma x;
feixe certo → abre, ela passa (sala do outro lado); volta andando pela porta e ela está fechada de novo.

- `porta_de_gelo`: Frigate Access L0 ↔ Crash Site R3 (gelo dos dois lados: L e R). Errado: Wave.
- `porta_de_onda`: Reactor Access L0 ↔ Reactor Core R2 (onda dos dois lados; com a Gravity Suit). Errado: gelo.
- `porta_de_plasma`: Root Cave L0 ↔ Arbor Chamber. Errado: gelo + Wave (`$3`). Mede o bit `$8` do plasma.

Fotos `build/tests/porta_de_*`, copiadas para `specs/img/09a-*.png` (cada cor fechada e aberta).

## Critérios de aceite

1. `python3 -I tools/validate.py` → 72 salas, 148 portas, **0 problemas**, alcançáveis agora: 15.
   (protege = tabelas de travas/fases coerentes e a ROM; falha_quando = mutações do 2; não_prova = o jogo)
2. Mutações na memória (desfeitas; sem mutação 0 problemas): (a) porta de gelo com o PLM de onda →
   `check_gates`; (b) argumento `$0000` numa porta de feixe → `check_gates`; (c) imediato da pré-instrução do
   gelo trocado na ROM → `check_gates`; (d) uma porta de gelo de volta à cinza → `check_gates`; (e)
   `FIRST_TIER` do Life Grove volta a 5 → `check_tallon_tiers`.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds; `$84` usado anotado.
4. `python3 -I tests/run_tests.py` → **42/42** (os 39 + `porta_de_gelo`, `porta_de_onda`, `porta_de_plasma`).
   (falha_quando = feixe errado/míssil/Power Beam abre, feixe certo não abre, porta não fecha atrás ou não
   volta fechada)
5. Fotos `specs/img/09a-*.png` olhadas: verde, cinza e laranja, sem tile quebrado.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `check_gates`: PLM/argumento das 26 portas de feixe, cinza só na de Bombas, bytes do `$84` | 1 alterada |
| mutação à mão | (a)–(e) | 5 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `porta_de_gelo`, `porta_de_onda`, `porta_de_plasma` | +3 |
| imagem | 3 cores fechadas + abertas | 6 |

## Riscos e reversão

- O Wave atravessa parede: se o tiro não chegar ao bloco da porta como tiro, a porta de onda não abre (o
  teste mede). O plasma `$8` não foi medido (o teste mede).
- Testes antigos que encostam nas cinza (`tallon_rota_d`: as portas do Reactor Access, agora de onda) atiram
  com o Power Beam: continua fechada (o som "dud" muda, a posição não).
- Reversão: `LOCK_OF` de volta a "grey" e as travas antigas; o `$84` volta a ficar livre.

## Fora de escopo

- Itens de feixe (09b), blocos de bomba e a T3 da Canyon (09d), Power Bomb (09e), rodadas (09f).
- Porta de feixe de chão/teto; cor nova.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → linha do Tallon igual (`… 44 salas construídas, alcançáveis agora: 15`) e
  `72 salas, 148 portas, 0 problemas`.
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `3f6e03c080428f7a12a6bb069920ba587ca0f7e2` nas duas. Log: `portas de feixe: 462 bytes no $84 a partir de
  $84F10F (PLMs ice R $F2B9, ice L $F2BF, wave R $F2C5, wave L $F2CB, plasma R $F2D1, plasma L $F2D7)`;
  `$84` livre a partir de `$84:F2DD` (3363 bytes). `$8F`, `$83` e o nível iguais (só os ids de PLM mudam).
- `python3 -I tests/run_tests.py` → **42/42** (os 39 + `porta_de_gelo`, `porta_de_onda`, `porta_de_plasma`).
  Nos três: fechada atrás da Samus ao entrar por ela; Power Beam, 3 mísseis (sobram 2: os tiros saíram) e o
  feixe errado deixam a Samus encostada na tampa (x `$25` na L; `$05DB` na Crash Site, `$03DB` na Reactor Core);
  o feixe certo abre com 1 tiro e ela passa; de volta, fechada de novo. **Plasma `$8` medido: abre.** **Wave
  abre** (o tiro que atravessa parede chega à porta como tiro).
- Mutações do validador (na memória, `scratchpad/s09a/mut_validate.py`; sem mutação 0 problemas): (a) gelo com
  o PLM de onda → "sem a tampa ice (PLM $F2BF em (1,6), argumento $8000)"; (b) argumento `$0000` → idem; (c)
  imediato do gelo → "`$84F118` na ROM é `$01`, beamdoors gera `$02`"; (d) gelo de volta à cinza → "cinza (nunca
  abre) na trava ['ice']: só a de Bombas fica cinza"; (e) `FIRST_TIER` do Life Grove 5 → "fica alcançável na fase
  4"; (f) lista de fechar vanilla no cabeçalho → bytes do `$84` diferentes.
- Mutações dos testes (cópias da ROM no scratchpad, `scratchpad/s09a/mut_tests.py`): pré-instrução que aceita
  qualquer tiro → os 3 falham (o Power Beam abre: x `$13`); pré-instrução que nunca abre → os 3 falham (não
  passa); cabeçalho com a lista de fechar vanilla → os 3 falham na volta (a porta em que ela entrou vira a verde/
  cinza/amarela vanilla e o feixe não abre): confirma o desvio abaixo.
- Imagens olhadas (`specs/img/09a-porta-de-{gelo,onda,plasma}-{fechada,abrindo,aberta,fechada-de-novo}.png`):
  verde (Frigate Access), cinza (Reactor Access, tileset 4: pouco contraste, como o épico previu) e laranja
  (Root Cave); quadros de abrir limpos, nenhum tile quebrado.

Mudanças de expectativa dos testes existentes: nenhuma (o `tallon_rota_d` encosta nas portas do Reactor
Access atirando com o Power Beam: agora são de onda e continuam fechadas, mesmas x `$25`/`$DB`).

Desvios e detalhes:

- **Lista de fechar própria** (não a vanilla da cor, como dizia o épico): a vanilla cai na lista principal
  vanilla (ver Estado atual); cada bloco leva uma cópia dos 23 bytes de fechar. Custo: 462 bytes em vez de ~330.
- As 6 listas (feixe × R/L) existem mesmo sem porta de plasma R no Tallon (56 bytes sem uso; uma regra só).
- `TIERS`: a fase 5 ficou "+ Power Bombs" sem trava que a peça (as paredes do X-Ray chegam na 09e); a 6 é
  "+ plasma". Arbor e o míssil dela continuam na 6.
- `porta_de_plasma`: a volta da Arbor Chamber é por teleporte de porta (a porta dela fica um degrau acima do chão:
  andar para a direita não a alcança).
- Teste com feixe e mísseis postos por RAM (preparação: os itens chegam na 09b) e a sala alcançada por teleporte
  de porta.
