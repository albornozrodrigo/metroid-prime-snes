# 13 — Item varrido por Power Bomb fica impegável

Estado: **verificada** (26/10/2026: validate "86 salas, 170 portas, 0 problemas", linha do Tallon igual; `.ips` sha1
`425f07969592da8b6b8ac8124a431981f01e219b` igual em dois builds; **58/58** testes)
Esforço estimado: 0,5 dia (pesquisa e reprodução 0,25 d; correção, teste e mutações 0,25 d)

## Contexto

A 12f achou no emulador: quando uma Power Bomb varre o bloco de um item, fica um PLM morto na lista; se a sala tiver um
slot de PLM livre mais alto, a Samus anda para dentro do item e não o pega até sair e voltar. A 12f contornou na Chozo (o
item da Power Bomb da Main Plaza vai primeiro na lista de PLMs, fora da explosão) e apontou o mesmo risco no X-Ray do Life
Grove do Tallon (dentro da cabana de Power Bomb, 09e).

## Estado atual (verificado)

Antes desta spec, na pasta real: validate "86 salas, 170 portas, 0 problemas"; `.ips` sha1
`e22a2f9f78f4fb2b2d2ac49ab281be5b0fb4572c`; 57/57 testes.

### O código (bytes da `base/sm_fix.sfc` e C `vendor/sm/src`)

- **Toque no item**: o bloco do item é tipo B, BTS `$45`; a colisão da Samus gera um PLM cujo setup é **`$84:EEAB`**
  (`sub_84EEAB`, `sm_84.c:2882`). Bytes `$84:EEAB–EED2`:
  `AD 78 0A  D0 1C  BB  BD 87 1C  9E 87 1C  A2 4E 00  DD 87 1C  F0 05  CA CA  10 F7  00  A9 FF 00  9D 77 1D  18  60 …`
  = pega o índice de bloco do próprio slot (`$1C87,X`), zera-o, e procura **do slot 39 para baixo o primeiro slot com o
  mesmo índice** (`CMP $1C87,X`), sem olhar o cabeçalho (`$1C37,X`); marca esse slot como tocado (`plm_timers` `$1D77,X` =
  `$FF`). Sem nenhum slot, `BRK` (`$84:EEC3`).
- **PLM que termina**: `PlmInstr_Delete` (`$84:86BC`) zera só o cabeçalho; o índice de bloco fica no slot.
- **Bomba/Power Bomb no bloco do item**: `BlockBombedReact_Special` (`$94:9D71`) → `kBlockBombedReact_Special_Plm[$45]` em
  `$94:9E2E` = **`$B62F`**: setup `$84:B3CF` (`nullsub_290`), lista `$84:AAE3` = `$86BC` (Delete). Cria um slot morto com o
  índice do bloco do item.
- **`SpawnPLM`** (`$84:84E7`) e **`SpawnRoomPLM`** (`$84:846A`) usam o slot livre mais alto (de 39 para baixo): o primeiro
  PLM da lista da sala fica no slot 39.
- **Alcance da varredura** (`BlockFunc_A06A`, `$94:A06A`): a caixa usa `HIBYTE($0CEA)`, que passa da fase branca (`$86`,
  `sm_88.c:1154`) e cresce até **`$FA`** (250 px na horizontal, 187 na vertical; medido no emulador, trace abaixo). A
  `power_bomb_box` da 12f (`$86`) cobre só a primeira fase.

### No emulador (roteiros no scratchpad, `s13/`)

- **X-Ray do Life Grove (ROM atual)**: `xray/repro.py` (o `tallon_power_bomb` com a tabela de PLMs despejada). O Life Grove
  só tem um PLM (o X-Ray; a porta L0 é azul): **o X-Ray fica no slot 39**. Depois da Power Bomb, os slots 28–38 guardam
  índices mortos dos blocos da cabana; o X-Ray continua no 39 e é o primeiro que a busca acha: **pegou** (`$7ED885` bit
  `$10`). **Não reproduz no X-Ray hoje**: o risco só existe se a sala ganhar um PLM antes dele na lista.
- **O defeito, na ROM atual, noutra sala**: Overgrown Cavern (slots: 39 tampa de gelo oeste, 38 tampa de gelo leste, 37 o
  míssil em (16, 9)). Abrir a porta leste (slot 38 livre), Power Bomb na bola 4 blocos a leste do míssil: no quadro 7678 o
  slot 38 fica com cabeçalho 0 e **índice `$0260` = o bloco do míssil** (o morto). Com a varredura alcançando a tampa oeste,
  o PLM de "tiro na porta" cai no slot 38 e apaga o índice (quadro 7702): nesse roteiro o míssil foi pego. Na Ruined Shrine
  (`shrine/repro.py`: pega os 2 mísseis de cima, Power Bomb no bloco de bomba do túnel) o morto do míssil do túnel aparece no
  slot 38 (quadro 13225) e some 12 quadros depois do mesmo jeito. **Natural, o defeito pede**: o morto acima do item e, depois,
  um slot ainda mais alto que fique livre **sem** que antes nasça um PLM no slot do morto (os PLMs dos blocos de Power Bomb da
  Main Plaza fazem isso: nascem acima do morto e terminam sozinhos; a 12f viu). Abrir porta ou pegar item nasce primeiro no
  slot livre mais alto, que é o do morto, e o apaga.
- **Teste que falha antes**: `power_bomb_nao_apaga_item` (abaixo) na ROM `e22a…` → `FAIL 7ED884 = 00, bit 08 desligado`: a
  Samus atravessa o míssil e ele fica (`s13/t13/before.out`, foto `s13/t13/13_missil_mensagem.png`).

## Causa

A busca do toque (`$84:EEAB`) compara só o índice de bloco: um slot morto (cabeçalho 0) com o índice do item, acima do slot
do item, é escolhido no lugar dele; o tique de "tocado" vai para um PLM que não roda, e o item fica.

## Mudança proposta

**Correção geral no motor** (`tools/smlib/itemtouch.py`, `tools/build.py`): a busca de `$84:EEB7` (13 bytes) vira
`JSR $FFDF` + `BRA $EEC4` (5 bytes; os outros 8 ficam como estavam, inalcançáveis); a rotina em **`$84:FFDF–FFFF`** (33 bytes,
fim do banco, livre `$FF` na base) procura primeiro **um slot vivo** (cabeçalho ≠ 0) com o índice; se não houver, faz a busca
vanilla (o primeiro com o índice, morto ou não; `BRK` sem nenhum, como antes). Y preservado (`PHY`/`PLY`).

Por que não a regra da 12f no X-Ray: o X-Ray já é o primeiro PLM (nada a mudar), e a regra não cobre o caso geral — uma Power
Bomb (ou bomba) posta em qualquer lugar perto de qualquer item cria o morto, e a caixa da 12f (`$86`) é menor que a varredura
real (`$FA`). A correção no motor vale para toda sala, de toda área, sem regra de layout.

O que fica: a ordem da 12f (item da PB primeiro na Main Plaza) e `check_bombed_items(_in_rom)` continuam (redundantes agora;
nota no código). Tirar é decisão do usuário (abaixo).

## Critérios de aceite

1. Teste `power_bomb_nao_apaga_item` falha na ROM antes (`e22a…`) e passa depois. (protege = o item é pego com um morto
   acima dele; falha_quando = a busca volta a ser a vanilla; não_prova = a sequência natural da 12f, que pede os blocos de PB)
2. `itemtouch.check` no validador (bytes do patch a partir da ROM base, resto de `$84:EEAB` vanilla); mutações pegas.
3. Tabela de rodadas do Tallon igual (44 salas, 20 itens em 7 rodadas); validate 0 problemas.
4. Dois builds com o mesmo sha1; 58/58.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `itemtouch.check` | +1 |
| run_tests.py | `power_bomb_nao_apaga_item` | +1 |
| scratchpad | `xray/repro.py`, `og/repro.py`, `shrine/repro.py` (reprodução), `t13/before.*` (o teste na ROM antiga), `mutate_13.py` | 6 mutações |

## Riscos e reversão

- A busca nova só difere da vanilla quando há um slot morto com o mesmo índice acima do vivo: aí ela pega o vivo. Sem vivo,
  é a vanilla. Reversão: tirar a chamada `itemtouch.apply` do build.
- O mesmo padrão (procurar por índice sem olhar o cabeçalho) existe no tiro em porta de cor (`PlmSetup_Door_Strange`,
  `$84:C7E2`): um morto acima da tampa faria um tiro se perder (o seguinte acerta). Fora do escopo; anotado.

## Fora de escopo

- Tirar a ordem da 12f e `check_bombed_items`; corrigir `$84:C7E2`.

## Resultado

- **Teste novo `power_bomb_nao_apaga_item`** (Overgrown Cavern): gelo, Morph e 5 PBs por RAM, salas por `door_teleport`; abre a
  porta leste com o gelo (slot 38 livre); Power Bomb 4 blocos a leste do míssil (a varredura não chega à tampa oeste); confere o
  morto (slot 38: cabeçalho 0, índice `$0260` = o do míssil; o míssil vivo no 37, não pego); **atalho**: o PLM do slot 39 (tampa
  oeste) termina por RAM, como terminam os PLMs dos blocos de Power Bomb; anda para dentro do míssil → pego. Antes: não pego.
  Fotos `build/tests/13_power_bomb.png`, `13_missil_mensagem.png`, `13_missil_pego.png` (olhadas: a explosão; a caixa
  "MISSILE"; e, na ROM antiga, a Samus do outro lado do míssil, que continua no chão).
- **Mutações** (`s13/mutate_13.py` → `mutate_13.out`), todas pegas: M1 patch ausente (busca vanilla), M2 rotina sem olhar o
  cabeçalho, M3 `BRA` errado, M4 resto vanilla mexido, M5 espaço do `$84` ocupado (o build para), M6 ROM base diferente (o build
  para).
- **Espaço**: `$84` +38 bytes (5 em `$84:EEB7`, 33 em `$84:FFDF–FFFF`); nada mais.

## Desvios

- **Não reproduz no X-Ray**: medido, o X-Ray é o único PLM do Life Grove (slot 39). A reprodução e o teste usam a Overgrown
  Cavern, com o morto criado pela Power Bomb de verdade e um atalho por RAM (o slot de cima terminando), porque a sequência
  natural depende de PLMs que terminam sozinhos acima do morto (os dos blocos de PB), que só existem perto do X-Ray (slot 39) e
  do míssil da árvore (que a 12f já pôs no slot 39).
- **A caixa da 12f** (`validate.POWER_BOMB_BOX_X = $86`) é só a primeira fase da explosão; a varredura vai até `$FA`. Com a
  correção no motor isso deixa de importar; a regra fica (nota no código).

## Decisões para o usuário

1. Tirar a ordem da 12f (item da PB primeiro) e `check_bombed_items`/`check_bombed_items_in_rom`, agora redundantes? (Hoje:
   mantidas.)
2. Corrigir também o tiro em porta de cor (`$84:C7E2`), que tem a mesma busca?

**Respondidas em 27/10/2026 (spec [12g2](12g2-ajustes-calor-e-cor.md))**: (1) a ordem da 12f e `check_bombed_items(_in_rom)`
**saíram**; antes, no emulador: o teste da 12f sem a ordem e sem esta correção passava (o toque nascia no próprio morto), e com
um slot acima do morto livre (atalho por RAM) o míssil da árvore não era pego sem esta correção e era com ela; o teste ganhou esse
atalho. (2) o tiro em porta de cor (`$84:C7E2`) foi corrigido do mesmo jeito (rotina em `$84:FFBB`); o tiro cria dois PLMs por
quadro, então o defeito só apareceria com dois mortos acima de uma porta no slot 36 ou abaixo (nenhuma sala tem).
