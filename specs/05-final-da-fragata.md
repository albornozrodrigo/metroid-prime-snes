# 05 — Final próprio da fragata

Estado: verificada (22/10/2026; sha1 `ac6e738c8af0916f9761ea6284dddd4ae59e0ba8`; testes 19/19)
Esforço estimado: parte 1 (troca do final pela cena de Ceres) ~1–2 h; parte 2 (texto "TALLON IV")
~2–3 h. Total ~4–5 h com testes.

## Contexto

Hoje, quando a Samus decola do hangar da fragata, o jogo toca o **final do Super Metroid**: Zebes
explodindo, "The operation has completed successfully" e créditos. Ou seja, o jogo **acaba**. No
Prime não é assim: a fragata explode, a Samus foge na nave, segue o Meta Ridley até Tallon IV e o jogo
continua. Quem termina a fragata hoje vê os créditos de um jogo que ainda nem começou.

## Estado atual (verificado)

- Decolagem: `GunshipTop_20` ($A2:AD0E), quando a nave passa da altura final, faz
  `LDA #$0026; STA $0998` em **$A2:AD20** (bytes `A9 26 00 8D 98 09`, conferidos na ROM). Estado
  $26 ($82:84BD, `GameState_38_SamusEscapesFromZebes`) escurece a tela e passa para **$27** (final
  e créditos, cena `$8B:D480`). O teste `fuga_ridley_nave_e_final` (`tests/run_tests.py:270-287`)
  espera `$0998 = 0027`. Os patches da nave estão em `tools/frigate/ending.py:251` (`gunship`).
- **A cena de fuga de Ceres já existe na ROM e faz exatamente o que o Prime pede** (lido no código C
  `vendor/sm/src` e conferido no emulador):
  1. Estado **$21** ($82:8388, `GameState_33_BlackoutFromCeres`): roda a jogabilidade normal
     enquanto escurece; quando a tela fica preta grava `loading_game_state $7ED914 = $22`,
     `$0998 = $22`, **salva na SRAM** (`JSL $81:8000`), põe a cena `$1F51 = $C11B`, zera o
     cronômetro ($0943) e o status de Ceres ($093F) e troca a música. Bytes conferidos em $82:8388.
  2. Estado **$22** (cena `$8B:C11B` `CinematicFunctionBlackoutFromCeres`): estação espacial em modo 7
     explodindo com a nave fugindo entre asteroides; depois (`$8B:C699`) um planeta com o texto
     **"PLANET ZEBES"**, a nave voa até ele e desce (`$8B:CADF` → estado 6).
  3. Estado 6 com `loading_game_state = $22` ($82:8000): força **área 0, load station $12**
     (entrada em $80:C5C1 = sala $91F8 Landing Site, porta $88FE, conferido na ROM) e toca a música
     de chegada.
  4. A nave da Landing Site, com `loading_game_state = $22` (`GunshipTop_Init` $A2:A644), desce do
     céu, abre e solta a Samus; em `GunshipTop_7` ($A2:A987) grava `loading_game_state = 5`,
     load station 0, marca a estação 0 de Crateria como usada e **salva**.
  - Na cena de Ceres **não aparece a palavra "Ceres"**; o único texto é "PLANET ZEBES" (sprite,
    spritemap $8C:9654, 11 letras com os tiles $8F,$97–$9E do gráfico comprimido $96:EC76). O
    gráfico tem só as letras P L A N E T Z B S; não tem O, I nem V. O texto japonês (só com a
    opção japonês ligada) é outro objeto ($8B:CEB5).
  - $96:EC76 só é lido por `$8B:C699` (ponteiro em $8B:C6BE `A9 00 96` = banco e $8B:C6C3
    `A9 76 EC` = endereço); o código C só tem essa referência. Como o hack pula intro e Ceres,
    essa cena só toca no nosso final.

### Protótipo (cópia do projeto em scratchpad, nada no projeto real)

Patch de 3 bytes em $A2:AD20 → `JSR` para uma rotina nova em $A2 que devolve A = $21 na área 3 e
A = $26 nas outras. Resultado no emulador (novo jogo, chefe morto por `poke`, embarcar):

| Quadro (desde apertar ↓ na nave) | `$0998` | Observação |
|---|---|---|
| +500 | 0008 | nave subindo no hangar |
| +516…+528 | **0021** | escurecendo |
| +532…+2400 | **0022** | estação explodindo, planeta, nave descendo; `$7ED914 = 0022`, `$1F51 = C2E4` |
| +2420 | 0006 | carregando |
| +2660 em diante | 0008 | Landing Site |
| +3980 | 0008 | `$079F = 0000`, `$079B = 91F8`, `$7ED914 = 0005`, `$078B = 0000`, `$7ED8F8 = 01`, energia 99 |

- Equipamento **continua** igual ao da fragata (`$09A2/$09A4 = D205`, raios `100B`, 30 mísseis).
- Game over depois do pouso → continue volta para a **Landing Site** (área 0, sala $91F8).
- Com o patch, 13 dos 14 testes passam; só falha `fuga_ridley_nave_e_final`, que espera `0027`
  (esperado: é o teste que esta spec muda).
- Parte 2 também prototipada: letras O, I, V desenhadas nos tiles vazios $AC/$AD/$AE, gráfico
  recomprimido (4017 bytes) no espaço expandido, ponteiro em $8B:C6BE/C6C3 trocado, spritemap
  $8C:9654 reescrita no lugar com 8 letras. A tela mostra **"TALLON IV"**.

Imagens (do protótipo):
- `specs/img/05-estacao-explodindo.png` — a estação (fica sendo a fragata) explodindo.
- `specs/img/05-texto-planet-zebes.png` — texto vanilla (o que a parte 2 troca).
- `specs/img/05-texto-tallon-iv.png` — com a parte 2.
- `specs/img/05-nave-a-caminho.png` — a nave indo para o planeta.
- `specs/img/05-pouso-landing-site.png` — a Samus sai da nave na Landing Site.
- `specs/img/05-continue-landing-site.png` — continue depois de game over.

## Opções comparadas

| | Opção | O que o jogador vê | Custo | Bate com o Prime? | Problemas |
|---|---|---|---|---|---|
| A | Pular o final: decolou → carregar direto a Landing Site (estado 6 com `loading_game_state = $22`) | tela preta, nave pousa em Crateria | ~1 h | médio: sem a fragata explodindo | perde a cena; mesmo trabalho que C |
| A' | Tela "TO BE CONTINUED" e voltar ao título | texto e título | 4 h+ | não | não existe essa tela no SM: arte e rotina novas; o jogador perde o progresso |
| B | Reusar o final do SM trocando Zebes pela fragata e o texto | planeta explodindo, créditos | 8 h+ | não | é o **fim do jogo**; trocar o planeta em modo 7 e o texto "operation completed" é arte nova; os créditos falam do SM |
| **C** | **Reusar a fuga de Ceres** (estado $21 → $22 → Landing Site) | estação explodindo com a nave fugindo, planeta, nave pousando | **~1–2 h** (+2–3 h para o texto) | **sim**: estação explode, Samus voa ao planeta e pousa | texto "PLANET ZEBES" (parte 2 resolve); planeta laranja; chega na Crateria vanilla até a spec 07 |

**Escolha: C**, com a parte 2 (texto "TALLON IV"). O motor já faz tudo: escurecer, salvar, cena,
carregar a Landing Site, pouso e novo save. Chegar na Crateria vanilla é aceitável agora porque a
área 0 é exatamente onde a Tallon Overworld vai ficar (spec 07); o pouso é na Landing Site, que é
a sala de pouso do Prime também.

## Mudança proposta

### Parte 1 — decolagem na fragata leva à fuga de Ceres (`tools/frigate/ending.py`)

Em `gunship()`, depois dos patches atuais:

1. Conferir que $A2:AD20 tem `A9 26 00` (senão `RuntimeError("bytes inesperados em $A2AD20")`,
   como os outros patches).
2. Pôr em `bank_a2` (espaço livre $A2:F498+, o protótipo usou 14 bytes):
   ```
   AD 9F 07     LDA $079F        ; área
   C9 03 00     CMP #$0003
   D0 04        BNE vanilla
   A9 21 00     LDA #$0021       ; fragata: escurecer como na fuga de Ceres
   60           RTS
   vanilla:
   A9 26 00     LDA #$0026       ; outras áreas: final do SM, como antes
   60           RTS
   ```
3. Trocar $A2:AD20 `A9 26 00` por `20 lo hi` (`JSR` para a rotina). O `STA $0998` seguinte fica
   igual. Constantes novas: `ENDING_STATE_SITE = 0xA2AD20`, `ENDING_STATE_VANILLA = bytes.fromhex("a92600")`,
   `GAME_STATE_CERES_BLACKOUT = 0x21`.
4. Atualizar a docstring de `ending.py` (linha 23: "It ends in SM's ending and credits") e o README
   (seção "Fim da fragata"): a decolagem agora toca a fuga (estação explodindo, nave até Tallon IV)
   e a Samus pousa na Landing Site.

Não mexer em nada do estado $21/$22: o salvamento no meio (estado $21) grava `area = 3` e
`loading_game_state = $22`; carregar esse save repete a cena e pousa na Landing Site (código C
`GameOptionsMenu_4_StartGame` $82:EEB4 e `InitAndLoadGameData` $82:8000). O save final do pouso
(`GunshipTop_7`) grava área 0 e estação 0. O patch de início de jogo em $82:EED9 não é afetado
(só o ramo de jogo novo).

### Parte 2 — texto "TALLON IV" no lugar de "PLANET ZEBES" (`tools/frigate/ending.py`, função nova `tallon_text(rom, expanded)` chamada de `tools/build.py` logo depois de `ending.gunship`)

1. Descomprimir $96:EC76 (`smlib.compression.decompress`, 16384 bytes = 512 tiles 4bpp).
2. Conferir que os tiles $AC, $AD, $AE estão zerados (são vazios; `RuntimeError` se não).
3. Desenhar neles O, I e V no estilo das letras existentes (cor 3 = contorno, cor 1 = miolo). O
   protótipo usou:
   ```
   O: .333333. 33111133 31133113 31133113 31133113 31133113 33111133 .333333.
   I: .333333. .311113. ..3113.. ..3113.. ..3113.. ..3113.. .311113. .333333.
   V: 333..333 313..313 313..313 3133.313 .31313.. .31113.. ..313... ..333...
   ```
4. Recomprimir (`compress`, conferir que `decompress(compress(x)) == x`), gravar com `expanded.put`
   e apontar para lá: banco em $8B:C6C0 (byte alto do `LDA #$9600`, que o `STA $48` põe em $49) e
   endereço em $8B:C6C4/C6C5 (o `LDA #$EC76; STA $47`). Conferir antes que os
   bytes são `A9 00 96` em $8B:C6BE e `A9 76 EC` em $8B:C6C3.
5. Reescrever a spritemap $8C:9654 **no lugar** (a nova é menor: 2 + 5·8 = 42 bytes contra 57):
   contagem 8; cada entrada `x (word, 9 bits) | y = -8 | tile` com x = -36, -28, -20, -12, -4, 4,
   20, 28 e tiles T $9B, A $98, L $97, L $97, O $AC, N $99, I $AD, V $AE (atributo 0, como as
   vanilla). Conferir antes que o primeiro word é `000B`. Os 15 bytes que sobram ficam como estão
   (não são lidos: a contagem é 8).

## Critérios de aceite

1. Decolar na fragata não leva mais aos créditos: teste `fuga_ridley_nave_e_final` (alterado) — depois
   de `board_ship()` e 600 quadros, `$0998 = 0022` e `$7ED914 = 0022`. protege = a troca $26→$21
   na área 3; falha_quando = o patch em $A2:AD20 some (fica `0027`/`0026`); não_prova = a cena em si.
2. A Samus pousa na Landing Site com o jogo rodando: mesmo teste, +3500 quadros: `$0998 = 0008`,
   `$079F = 0000`, `$079B = 91F8`, `$7ED914 = 0005`, `$078B = 0000`, `expectbit 7ED8F8 01`,
   foto `build/tests/fuga_pouso_landing_site.png`. protege = toda a cadeia $21→$22→6→8;
   falha_quando = a cena trava ou cai em outro estado; não_prova = o visual da cena.
3. O equipamento da fragata continua depois do pouso: mesmo teste, `$09A4` igual ao valor lido antes
   de embarcar e `$09C8 = 001E`. protege = nada é zerado no caminho.
4. Continue depois do pouso volta à Landing Site: teste novo `final_continue_na_landing_site`
   (chefe morto por `poke 7ED82B 01`, embarcar, esperar o pouso, zerar a energia, `GAME_OVER_CONTINUE`):
   `$0998 = 0008`, `$079F = 0000`, `$079B = 91F8`. protege = o save do pouso; falha_quando = o
   save fica na fragata; não_prova = carregar o save do meio da cena (ver Riscos).
5. Outras áreas não mudam: `validate.py` confere que a rotina em $A2 compara a área com 3 e devolve
   `$26` no outro caminho, e que $A2:AD20 tem `20 xx xx` apontando para ela. falha_quando = alguém
   troca o final de todas as áreas.
6. Texto "TALLON IV": `validate.py` lê a spritemap $8C:9654 (contagem 8, tiles na ordem T A L L O N
   I V) e descomprime o gráfico apontado por $8B:C6BE/C6C3, conferindo que os tiles $AC–$AE não
   estão vazios e que os tiles $8F e $97–$9E são iguais aos vanilla. Foto
   `build/tests/fuga_tallon_iv.png` no teste do critério 1, ~1580 quadros depois de embarcar
   (conferida a olho na revisão). falha_quando = texto volta a ser "PLANET ZEBES" ou fica com
   letras faltando.
7. Os 13 testes atuais seguem passando; validate e build sem erro.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | rotina $A2 (área 3 → $21, outras → $26); spritemap TALLON IV; tiles O/I/V no gráfico | +2 |
| run_tests.py (emulador) | `fuga_ridley_nave_e_final` alterado (estado $22, pouso, equipamento); `final_continue_na_landing_site` novo | +1 (1 alterado) |
| imagem | `fuga_tallon_iv.png`, `fuga_pouso_landing_site.png` | +2 |

Em `tests/run_tests.py`: trocar `GAME_STATE_ENDING = "0027"` por `GAME_STATE_ESCAPE_CUTSCENE = "0022"`
e as constantes da Landing Site (`LANDING_SITE = "91F8"`, `LOADING_GAME_STATE = "7ED914"`).

## Riscos e reversão

- **Save no meio da cena** (estado $21 grava `loading_game_state = $22`): se o jogador desligar
  durante a cena, carregar o save repete a cena de Ceres e pousa na Landing Site (comportamento
  vanilla de Ceres). Lido no código C, **não testado no emulador** (o `snesrun` não tem reset).
  A tela de seleção de arquivo desse save mostra a área 3. Aceitável.
- A cena chama o planeta de Tallon IV, mas ele continua **laranja** (é o Zebes). Ver fora de escopo.
- Com o idioma japonês ligado, aparece também o texto japonês de Zebes ($8B:CEB5). O jogo vem em
  inglês; fica como está.
- Depois do pouso o jogador está na **Crateria vanilla** com os itens da fragata, até a spec 07.
  A nave da Landing Site volta a salvar normalmente (os patches de $A2 só mudam a área 3).
- Tiles $AC–$AE: estão zerados no gráfico e nenhum objeto da cena aparece usando-os nas fotos, mas
  não se conferiu todas as spritemaps da cena; se aparecer lixo, trocar por outros tiles zerados
  (há 342).
- Reverter: desfazer as mudanças em `tools/frigate/ending.py`, `tools/build.py` e nos testes e
  reconstruir.

## Fora de escopo

- **Tirar os itens da Samus** (no Prime ela perde quase tudo numa explosão durante a fuga da
  fragata e chega a Tallon só com o Power Beam). Daria para zerar $09A2/$09A4 (itens), $09A6/$09A8
  (raios → Power Beam), $09C6–$09D0 (mísseis, supers, power bombs) na mesma rotina de $A2 antes
  de devolver $21 (o save do estado $21 já gravaria assim). Fica para a spec 07, que decide a
  progressão da Tallon; não foi prototipado.
- Recolorir o planeta para parecer Tallon IV (paleta `$8C:E5E9`, que também colore a estação;
  falta descobrir quais cores são do planeta).
- Trocar a forma da estação em modo 7 ($95:A82F) pela da fragata ou mostrar o Meta Ridley na cena.
- Tallon Overworld de verdade e a Landing Site com cara do Prime (spec 07).
- Mudar o final do Super Metroid em outras áreas (estado $26/$27 continua como está).

## Desvios (preenchido na implementação)

- **Endereços**: a rotina de `$A2` tem 16 bytes (não 14) e ficou em `$A2:F502` (o `$A2:F498+` já
  tinha os patches anteriores da nave). Constante extra `GAME_STATE_ENDING = 0x26` em `ending.py`.
- **Gráfico em `$E0:8000`**: `tallon_text` roda logo depois de `ending.gunship`, como pedido, então o
  gráfico (4017 bytes) é o primeiro dado do espaço expandido e tudo que vem depois andou; as
  estrelas do hangar passaram de `$E1:8189/8289` para `$E0:913A/923A` (atualizado em
  `research/sm_room_format.md` §15; a spec 04 fica como registro).
- **Equipamento (critério 3)**: o `snesrun` não guarda valores entre linhas; o teste confere
  `$09A4 = START_ITEMS` (`D205`, importado de `tools/build.py`) antes de embarcar e depois do pouso,
  e `$09C8 = START_MISSILES` (`001E`).
- **Pouso (critérios 2 e 4)**: as checagens do pouso viraram `lands_on_landing_site()` em
  `tests/run_tests.py`, usada pelos três testes do final; ela também confere `$078B = 0000` no
  teste do continue.
- **validate (critérios 5 e 6)**: `ending.check_rom` (chamada como `areaselect.check_rom`) compara a
  rotina inteira, a spritemap byte a byte, os tiles `$8F`/`$97–$9E` com o gráfico vanilla de
  `$96:EC76` (que continua intacto na ROM) e os tiles `$AC–$AE` com as letras desenhadas.
- **Save no meio da cena (Riscos) — agora testado**: `tools/snesrun` ganhou `reset` (desliga e liga:
  WRAM zerada, SRAM mantida). Teste novo `final_reset_no_meio_da_cena`: 1000 quadros depois de
  embarcar (estado `$22`), reset, carregar o slot A → o jogo vai direto ao estado `$22` (sem tela de
  área; `$079F = 3`), a cena toca de novo e a Samus pousa na Landing Site com o save feito lá.
  Conferido também à mão (fora dos testes): reset **depois** do pouso e carregar → tela de área na
  Crateria ("TALLON IV" / "CRATERIA") → Landing Site.
- **Testes**: 17 → 19 (critério 7 falava em 13; specs 01–04 acrescentaram 4). Os três testes do final
  e o validate (5 problemas) falham na ROM anterior a esta spec (conferido com a ROM pré-05 em
  `build/`); depois reconstruído e 19/19.
- **Imagens conferidas**: estação explodindo (+500…+800 quadros), "TALLON IV" sob o planeta
  (`build/tests/fuga_tallon_iv.png`), Samus em cima da nave na Landing Site
  (`build/tests/fuga_pouso_landing_site.png`), continue (`final_continue_landing_site.png`), cena
  depois do reset (`final_reset_cena.png`).
- **Depois do pouso** (lido na RAM, não alterado): eventos `$7ED820` zerados (Crateria "dormindo",
  como no começo do SM), boss bits da área 3 = `01`/`03` (Parasite Queen, Meta Ridley), cronômetro
  `$0943 = 0`, energia cheia. Não conferido no emulador: as salas vanilla da Wrecked Ship continuam
  ligadas à Crateria; com o boss bit da área 3 elas abririam no estado "Phantoon morto", com o mapa
  de pausa da fragata, e a save station delas usa as load stations da área 3 (que apontam para a
  fragata). Fica para a spec 07.
