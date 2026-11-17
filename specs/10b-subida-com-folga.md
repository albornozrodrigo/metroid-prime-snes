# 10b — Subir por porta de teto com folga

Estado: verificada (26/10/2026: validate 72/148/0; .ips sha1 `ed565db65f296c4682039d269708fb926984336c` igual em dois builds; 51/51 testes)
Esforço estimado: 0,5 dia
Épico: [10 — Polimento do Tallon](10-polimento-tallon.md) (achado A4)

## Contexto

Subindo por uma porta de teto para uma sala seca, a Samus sai pelo buraco de 4 blocos da porta de chão da sala de cima e
tem de cair numa das bordas de 3 blocos ao lado (`Canvas.door_gap`, linha h−3). A spec 08 anotou que, guiando para a borda
do **outro lado**, ela cai de volta em 11 das 14 portas da fragata; a HANDOFF repete isso para a Gully. Pedido do usuário:
uma subida normal tem de funcionar, mexendo na borda ou no empurrão da porta, pela regra única `build.door_push` e a
checagem `check_door_push`.

## Estado atual (verificado)

- `build.UP_PUSH = $0240` (`tools/build.py:316`, antes), aplicado por `door_push("T", seca)` às 16 entradas que sobem para
  sala seca (14 da fragata, Tallon Canyon → Gully, Artifact Temple → Temple Lobby); `check_door_push` (`tools/validate.py:817`)
  confere a regra em toda entrada.
- Varredura no emulador (`scratchpad/s10/upsweep.py`, as 16 portas): Samus de pé na plataforma da linha 6 sob a porta,
  virada para o lado (um toque), em 5 posições dentro das 4 colunas da porta (x +6, +16, +32, +48, +58), pulo (A) e a direção
  segurada até depois da transição. Com `$0240`: **54 de 160 subidas caem de volta**, todas guiando para a borda do outro
  lado (partindo da metade oposta da porta); para a borda do mesmo lado, nenhuma. Traço (`tr2.py`, Canyon → Gully): ela ganha o
  controle com o pé 47 px acima da borda e anda ~1,3 px por quadro; partindo da beira oeste chega ao começo da borda leste 7 px
  abaixo do topo.
- Sem direção nenhuma ela sempre cai de volta (o buraco da porta fica aberto, como no SM). Fechar a tampa atrás dela (bit
  `$04` da direção na entrada da porta, como 24 das 31 portas de subir vanilla; experimento numa cópia) **não** a segura: no
  meio da porta ela cai através da tampa que está fechando.
- Empurrões maiores (cópias, varredura e bateria): `$0280`, `$02A0`, `$02C0` passam nos testes; `$02E0`, `$0300` (e o `$0340` da
  spec 08) quebram as três fugas da fragata (`rota_completa_ida_e_fuga`, `parasite_queen_morre_e_fuga_com_timer`,
  `fuga_ridley_nave_e_final`: na Vent D → Vent E a Samus fica com a cabeça sob o degrau do poço). Quedas na varredura acima:
  `$02A0` **28**/160, `$02C0` 27/160 — todas partindo do quarto de fora da porta (x +6 ou +58) para a borda oposta.

## Causa

O empurrão de subir não dá altura para atravessar o buraco inteiro antes de a Samus descer abaixo da borda.

## Mudança proposta

- `build.UP_PUSH = $02A0` (era `$0240`): +21 px de altura ao ganhar o controle. Comentário com as medidas. `$02A0` e não `$02C0`:
  o ganho do `$02C0` é 1 subida em 160 e ele fica a um passo (`$02E0`) de quebrar a fuga.
- Nada muda na geometria. A regra continua uma só (`door_push`); `check_door_push` confere a ROM contra ela (o comentário dele
  diz o valor novo).
- Bytes: os 16 bytes baixos das entradas de subir para sala seca (`$83:ADD2` … `$83:B162`), `$40` → `$A0`.

## Critérios de aceite

1. Teste novo `sobe_porta_de_teto_pela_borda_longe`: na Tallon Canyon, de pé sob a T3 a x +12 da porta, virada para leste,
   pula, guia para leste e sobe para a Gully, de pé na borda leste (y da borda, corpo além do buraco); no Artifact Temple a x
   +52, guiando para oeste, sobe para o Temple Lobby na borda oeste. (protege = a folga; falha_quando = `$0240`: as duas caem
   de volta (mutação); não_prova = partir do quarto de fora da porta, que continua caindo)
2. `check_door_push` acusa a regra antiga (mutação em memória: `UP_PUSH = $0240` → 16 problemas).
3. Todos os testes antigos passam, inclusive as fugas da fragata.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| run_tests.py | `sobe_porta_de_teto_pela_borda_longe` (+ checagem `check_far_ledges`) | +1 |
| validate.py | `check_door_push` (já existente; mutação) | 0 |
| emulador (scratchpad) | varredura das 16 portas com `$0240`/`$02A0`/`$02C0` | 3 |
| imagem | Gully e Temple Lobby depois de subir; Gully antes (caiu) | 3 |

## Riscos e reversão

Sala com degrau baixo sobre a porta de chão (o poço da fuga) bateria a cabeça com empurrão maior: medido, `$02A0` passa.
Reversão: `UP_PUSH` em `tools/build.py` e o teste.

## Fora de escopo

- Partir do quarto de fora da porta e atravessar o buraco inteiro (28 casos na varredura): pede geometria (borda mais baixa ou
  buraco mais estreito, em toda porta de chão das duas áreas, com o modelo a pé e os testes medidos) — anotado no épico.
- Subir sem direção (cai de volta, como no SM).

## Desvios (preenchido na implementação)

Verificação (26/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas` (linha do Tallon igual).
- `python3 -I tools/build.py` duas vezes → sha1 `ed565db65f296c4682039d269708fb926984336c` nas duas (antes `9bc37cab…3462`). Diferença
  da ROM: 16 bytes em `$83:ADD2`–`$83:B162` (os bytes baixos dos 16 empurrões de subir para sala seca).
- `python3 -I tests/run_tests.py` → **51/51** (os 50 + `sobe_porta_de_teto_pela_borda_longe`).
- Mutações: teste novo numa cópia com `$0240` → falha nas duas subidas (`7E0998 = 000B`: voltou pela porta; "x 0x9b (raio 5) em
  cima do buraco da porta", "x 0x165 …"); `check_door_push` com `UP_PUSH = $0240` em memória na ROM nova → 16 problemas
  ("mech_shaft: porta 1 (T → airlock) empurra $02A0, a regra diz $0240", …).
- Varredura com a pose do teste (`climbscan.py`, a cada 4 px): com `$0240` a subida para a Gully guiando para leste pega de x +16
  em diante e a do Lobby guiando para oeste até x +48; com `$02A0`, de x +12 e até x +56. Os casos do teste (+12, +52) são os que
  mudam.
- Fotos olhadas: `specs/img/10b-subida-gully.png` (de pé na borda leste da porta de chão da Gully), `10b-subida-temple-lobby.png`
  (borda oeste do Lobby), `10b-antes-subida-gully-cai.png` (com `$0240`: voltou para a Canyon, tela da transição).

Desvios:

- O pedido era "pulo normal confiável". Com a direção segurada, a subida passa de qualquer ponto da metade da porta do lado
  para onde ela guia e, agora, de mais 1/4 da porta; **partindo do quarto de fora e atravessando o buraco inteiro ela ainda cai**
  (28/160 na varredura), e sem direção cai sempre. Empurrão maior quebra a fuga da fragata; tampa fechando atrás não segura. O
  resto pede geometria nas 18 portas de chão (fora de escopo; anotado no épico como ideia).
- A primeira varredura (sem o toque de direção antes do pulo) dava 1 queda só: a Samus posta por RAM pula mais alto parada de
  frente do que virada para um lado. A pose do teste e da varredura final é a virada (a de quem anda até a porta).

Mudanças de expectativa dos testes existentes: **nenhuma**.
