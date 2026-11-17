# 07h — Itens do Tallon

Estado: verificada (23/10/2026: validate 48/98/0 com "alcançáveis agora: 15"; .ips sha1 `c1d5735a…e147` igual em dois builds; 29/29 testes)
Esforço estimado: 1,5 dia (pesquisa 0,25 d; tabela + build 0,25 d; validador 0,25 d; testes no emulador 0,5 d; verificação 0,25 d)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (linha 07h; seção "Itens (proposta, 07h)")

## Contexto

Desde a 07k o Tallon tem 20 salas com as travas fiéis do Prime: portas vermelhas (míssil), cinza
"nunca abre" (gelo/plasma) e bordas de Space Jump. A Samus chega só com o Power Beam e 0 mísseis, e
nenhum item existe no jogo: as três portas vermelhas (Temple Security, Waterfall Cavern, Root Tunnel)
são um beco sem saída. Esta spec põe os itens das salas que já estão na ROM e resolve esse impasse.

## Estado atual (verificado)

- Itens do Prime no Tallon (épico, tabela "Itens"): 9 Missile Expansions, 2 Energy Tanks, Space
  Jump, X-Ray e 2 artefatos. Posições lidas nesta pesquisa dos objetos `Pickup` crus de
  `research/prime_fs` (retro-data-structures não lê o `Pickup` do Prime: nome e posição saem dos
  bytes; posição local = posição − translação da sala em `prime_worlds.json`):

  | P# | Sala | Item | Altura no Prime (m, local) | Referência |
  |----|------|------|---------------------------|------------|
  | 0 | Landing Site | Missile Expansion | 0,9 | portas oeste 7,5–15; Waterfall −9,5 |
  | 4 | Alcove | Space Jump | 1,8 | porta 8,6 |
  | 8 | Frigate Crash Site | Missile Expansion | 9,5 | entrada (Waterfall) 23,8 |
  | 13 | Overgrown Cavern | Missile Expansion | 1,4 | portas 0 e 4 |
  | 15 | Root Cave | Missile Expansion | 84,1 | porta da Arbor 85, do Root Tunnel 36,9 |
  | 16 | Artifact Temple | Artifact of Truth | — | — |
  | 19 | Transport Tunnel B | Missile Expansion | 5,7 | portas 0 e 12 |
  | 20 | Arbor Chamber | Missile Expansion | 2,7 | porta 0 |
  | 27, 30, 35 | Cargo Lift, Biohazard, Hydro Access (D) | E-tank, míssil, E-tank | — | região D |
  | 37, 39, 42 | Great Tree Chamber, Life Grove Tunnel, Life Grove (E) | míssil, míssil, X-Ray (+ Artifact of Chozo) | — | região E |

- PLMs de item visível (`research/sm_room_format.md` §5, base `$EED7` + 4·n): E-tank `$EED7`, míssil
  `$EEDB`, X-Ray `$EF0F`, Space Jump `$EF1B` (setup lido na ROM: `$EE4D`, `$EE52`, `$EE64`, `$EE64`).
  O setup escreve BTS `$45` no bloco (tipo ar) e conta o item (`$84:EE64`); o argumento é o bit do
  item (`$7ED870`, 512 bits).
- Bits de item vanilla (todos os PLMs `$EED7–$EFD2` das 250 salas da ROM base, lidos nesta
  pesquisa): 100 itens, bits 0–154. Livres a partir de 155.
- Coleta (C `PlmInstr_CollectAmmoMissileTank`, `$84:89A9`): `$09C8` (máximo) e `$09C6` (atual) +5,
  caixa de mensagem 2 ("MISSILE"), que só fecha com A. O bit do item fica em `$7ED870`, dentro do
  bloco salvo na SRAM (`SaveToSram` `$81:8000` copia `$7ED7C0`…).
- A fragata não tem itens (nenhum PLM de item no `build.py`).
- `validate.check_tallon_tiers` anda as salas por fase com o equipamento fixo da fase; não conhece itens.

## Mudança proposta

### 1. Tabela de itens (`tools/tallon/items.py`, novo)

Uma linha por item do SM do Tallon inteiro (13: os 15 do Prime menos os 2 artefatos), na ordem do
Prime; bit = `$A0` + índice da linha (160–172), fixo mesmo quando as regiões D/E entrarem. Cada linha:
sala, P#, PLM, lugar `(x, y)` (bloco de ar onde passa o corpo da Samus) e fase declarada; sem lugar
enquanto a sala não está construída.

| # | Sala | Item | Bit | Lugar (bloco) | Fase | Por quê |
|---|------|------|-----|---------------|------|---------|
| 0 | Landing Site | Missile Expansion | `$A0` | (21, 43), no fundo do lago | **0** | **desvio**: no Prime fica atrás de um túnel de Morph Ball, que não existe aqui; fica no chão, baixo e a oeste como no Prime, no caminho da nave à porta da Canyon Cavern |
| 1 | Alcove | Space Jump | `$A1` | — | — | Alcove não construída (pede Morph + Bombas no Prime, ver 07k) |
| 2 | Frigate Crash Site | Missile Expansion | `$A2` | (25, 59), no fundo do lago sob o nariz do destroço | 0 | baixo como no Prime; sem água (07k), a pé |
| 3 | Overgrown Cavern | Missile Expansion | `$A3` | (16, 9), no chão | 3 | atrás das portas de gelo |
| 4 | Root Cave | Missile Expansion | `$A4` | (6, 9), na borda da porta da Arbor Chamber | 2 | no Prime está na altura da porta da Arbor (84 m): só com Space Jump |
| 5 | Transport Tunnel B | Missile Expansion | `$A5` | (23, 7), no degrau do meio | 0 | baixo, no meio do túnel |
| 6 | Arbor Chamber | Missile Expansion | `$A6` | (20, 9), no chão | 4 | atrás da trava de plasma/grapple/X-Ray |
| 7–9 | Cargo Lift, Biohazard, Hydro Access | E-tank, míssil, E-tank | `$A7–$A9` | — | — | região D (07l) |
| 10–12 | Great Tree Chamber, Life Grove Tunnel, Life Grove | míssil, míssil, X-Ray | `$AA–$AC` | — | — | região E (07m) |

Artefatos (P16, P42): **fora** (o SM não tem item equivalente; spec própria dos artefatos).

### 2. O impasse dos mísseis

Sem um míssil na fase 0 as portas vermelhas não abrem nunca. Decisão: o míssil da Landing Site
fica onde a Samus anda (desvio documentado: não existe Morph Ball). Ele dá 5 mísseis, exatamente o
que uma porta vermelha do SM pede; a nave da Landing Site recarrega os mísseis (refil vanilla ao
salvar: C `GunshipTop_12`, `Samus_RestoreMissiles`, antes da pergunta do save), e o míssil da Crash Site e o do Transport Tunnel B (atrás das portas vermelhas) sobem o
máximo para 15. Não há beco: o bit da porta aberta fica salvo.

### 3. Fases

`validate.tallon_tiers` passa a **pegar itens**: em cada fase começa com os itens da fase, anda as
salas, e todo item em que o corpo da Samus chega (a pé: as 3 linhas de pé de cada lugar alcançado;
com Space Jump: o flood fill) acrescenta o que dá (`items.GRANTS`: míssil → `missile`, Space Jump →
`space_jump`, X-Ray → `xray`, E-tank → nada); repete até não pegar nada novo. `FIRST_TIER` muda: as 6
salas atrás das portas vermelhas (Temple Lobby, Artifact Temple, Frigate Crash Site, Root Cave,
Transport Tunnel B, Transport to Magmoor East) passam da fase 1 para a **0**. Alcançáveis agora: 15.

### 4. Build (`tools/build.py`)

Na lista de PLMs de cada estado da sala, um PLM por item com lugar: `PLM, x, y, bit` (6 bytes). Sem
código novo. Espaço: `$8F` +42 bytes (6 itens + 3 listas de PLM novas), livre a partir de `$8F:F419`.

### 5. Validador (`tools/validate.py`)

- `check_tallon_tiers`: cada item com lugar está num bloco de ar, fora das portas, e fica alcançável
  primeiro na fase declarada; lugar e fase vêm juntos; item em sala fora do build é erro.
- `check_tallon_items` (ROM construída): bits únicos, dentro do vetor e fora dos bits vanilla (ROM
  base); em cada estado de cada sala do Tallon, os PLMs de item são exatamente os da tabela.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 0 problemas, linha do Tallon com `alcançáveis agora: 15`.
   (protege = lugar e fase de cada item, bits, PLMs na ROM, as salas que o primeiro míssil abre;
   falha_quando = item na parede, item fora do alcance da fase, bit repetido/vanilla, PLM faltando;
   não_prova = a coleta no jogo, isso é o critério 4)
2. Mutações (na memória, desfeitas; sem mutação 0 problemas): (a) míssil da Landing Site dentro do
   chão → "não está num bloco de ar" + "inalcançável" + as 6 salas voltam para a fase 1; (b) no alto
   do céu → "fica alcançável na fase 2 (+ Space Jump), declarado 0" + as 6 salas na fase 1; (c) sem o
   míssil → as 6 salas na fase 1 (o impasse aparece); (d) míssil do Tunnel B na parede → falha.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds.
4. `python3 -I tests/run_tests.py` → 29/29: os 27 de antes + `tallon_missil_abre_porta_vermelha`
   (pouso → lago → `$09C6`/`$09C8` = 5 e bit `$A0` → sobre a nave e os terraços até a porta vermelha
   da Waterfall Cavern → SELECT (`$09D2` = 1) → mísseis na porta → bit da porta ligado, `$09C6` = 0 →
   entra na Frigate Crash Site) e `tallon_missil_salvo` (pega, salva na nave, game over, continue:
   bit e 5/5 voltam; andar de novo pelo lago não dá mais nada).
5. Imagens `specs/img/07h-emulador-*.png` olhadas.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | itens nas fases (`check_tallon_tiers`), `check_tallon_items` | +2 checagens |
| mutação à mão | 4 (acima) | 4 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `tallon_missil_abre_porta_vermelha`, `tallon_missil_salvo` (novos); `tallon_rota_bc` (expectativa) | +2 (1 alterado) |
| imagem | lago com o míssil, mensagem, porta aberta, Crash Site com o míssil, lago vazio depois do save | 5 |

## Riscos e reversão

- Os testes de rota andam "às cegas" e passam pelo lago: a rota B/C pega o míssil (só a expectativa
  final muda). Mexer no lugar do míssil pode pedir novo ajuste dos trechos medidos.
- Itens das fases 2–4 estão na ROM mas só o validador prova o alcance (no jogo ainda não há Space
  Jump, gelo nem plasma).
- Reversão: tirar `tools/tallon/items.py` e o laço de PLMs do `build.py`, voltar `FIRST_TIER` e
  reconstruir.

## Fora de escopo

- Space Jump (Alcove), E-tanks e X-Ray (regiões D/E), artefatos, mapa de pausa com pontos de item,
  inimigos que soltam mísseis (07i), túnel de Morph Ball.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (… 20 salas construídas, 2 desenhadas fora do build,
  alcançáveis agora: 15) …` e `48 salas, 98 portas, 0 problemas`.
- Mutações: as 4 do critério 2 deram exatamente as falhas descritas (10, 9, 8 e 2 problemas); sem
  mutação, 0.
- `python3 -I tools/build.py` duas vezes → sha1 `c1d5735abfe5b1f33e7c10faa76412df79b4e147` nas duas.
  `$8F` livre a partir de `$8F:F419` (3047 bytes; eram 3089).
- `python3 -I tests/run_tests.py` → **29/29**.

Mudanças de expectativa dos testes existentes:
- `tallon_rota_bc`: no trecho para oeste (`bc_oeste`) a Samus passa pelo fundo do lago e pega o
  míssil; a expectativa final `$09C8 = 0000` virou `$09C8 = 0005` + bit `$A0` ligado. A sequência de
  salas e as três portas vermelhas fechadas (o beam continua selecionado) não mudaram.

Desvios e detalhes:

- **Câmera das estações do Tallon (bug da 07g achado aqui)**: a estação 0 e a `$12` começavam a câmera
  em x = 576 (Samus no meio da tela). `LoadFromLoadStation` (`$80:C437`) copia isso para
  `bg1_x_offset`, e o desenho de PLM na VRAM (`CalculatePlmDrawTilemapVramDst`, `$84:91DC`) só olha o
  bit `$100` dele: todo PLM animado (o item, e a tampa de porta quando abre) aparecia também 64 px
  (576 mod 256) à esquerda do lugar certo — um "míssil fantasma" no chão, 4 blocos antes do
  verdadeiro, nesta sala e em todas depois de portas. As estações vanilla sempre começam em telas
  inteiras: `write_load_station` agora arredonda o x da câmera para múltiplo de 256 (512 na Landing
  Site; a Samus começa em x 192 da tela). A fragata não muda (câmera 0).
- **Lugar do míssil da Landing Site**: a rota medida dos testes passa por todo o chão da sala (mapa de
  onde a Samus esteve, tirado de uma cópia com leitura de posição a cada ciclo); não há lugar a pé
  fora dela sem uma escalada que os andadores cegos também fariam. Ficou no lago, no caminho.
- **Teste**: a caixa "MISSILE" só aceita A depois de ~240 quadros; o teste espera antes de fechar.
  Para salvar na nave, a posição posta por RAM mantém a corrida da Samus (tipo de movimento 1, ela
  escorrega para fora do centro); a nave só aceita a Samus parada a até 8 px do centro (`$A2:A9BD`):
  o teste aperta UP, espera e põe a Samus no centro de novo.
- Root Cave: o míssil ficou na borda da porta da Arbor (fase 2) e não num lugar à parte: o alto da
  sala no Prime é justamente essa borda.
