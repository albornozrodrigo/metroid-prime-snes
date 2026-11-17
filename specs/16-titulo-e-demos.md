# 16 — Arremates: demos e tela de título

Estado: **verificada** (31/10/2026: validate "136 salas, 284 portas, 0 problemas", linhas do Tallon e das rodadas iguais;
`.ips` sha1 `0f5cc669fc89800b65e43169c9cd5a816fde0653` igual em dois builds; **83/83** testes; build×2 + validate + testes em
6 min 33 s)
Esforço estimado: 0,5 dia (demos 1 h; logo 0,5 dia) (medido: ~0,5 dia, metade dela no achado do tempo de carga, abaixo)
Itens abertos do usuário (HANDOFF): as **demos de atração** ainda mostravam salas do Super Metroid (decisão do usuário:
**desligar**, a opção recomendada) e a **tela de título ainda dizia "SUPER METROID"** (objetivo: "METROID PRIME").

## Contexto

Quem liga o jogo e não aperta nada vê, depois de ~50 s de título, as demos gravadas do Super Metroid: Crateria, Brinstar,
Norfair, Wrecked Ship, Maridia (19 salas vanilla; a spec 11 provou que são o **único** caminho que ainda carrega sala vanilla).
E o título, o primeiro quadro do jogo, diz "SUPER METROID". Os dois são arremates rápidos, aprovados juntos.

## Estado antes (verificado)

validate "136 salas, 284 portas, 0 problemas", sha1 do `.ips` `31218abaaf3b1cb047f1ee6684ecd82fe45aa6c5`, 82/82 testes.

**Demos** (bytes da ROM + `vendor/sm/src/sm_8b.c`, conferido no emulador):
- Depois que o logo aparece (quadro ~1830 parado), a função do título `$1F51` = `$8B:9F29` (`CinematicFunc_Func1`) conta o
  `demo_timer` (`$1F53`, 900 quadros, posto em `$8B:9B53`/`$8B:9F19`). Bytes em `$8B:9F29`:
  `CE 53 1F` (DEC $1F53) `F0 02` (BEQ) `10 08` (BPL) `A9 AE 9F` (LDA #$9FAE) `8D 51 1F` (STA $1F51) `80 0D` (BRA) … `A5 8F`
  em `$8B:9F38` (botões novos: A/B/START vão para a tela de arquivos, `$8B:9F52`).
- Zerado, a função vira `$8B:9FAE` (`CinematicFunc_Func9`): escurece e grava o estado `$28` (`A9 28 00 8D 98 09` em
  `$8B:A000`), a demo. No emulador: quadro 2000 `$1F53` = `$030E`; quadro 3600 estado `$2A` na Landing Site vanilla `$91F8`.
- Em toda a ROM, `LDA #$0028; STA $0998` só existe em `$8B:A000` e em `$82:862F` (`GameState_44`, saída da demo: "próxima
  cena da mesma demo", só alcançável de dentro de uma demo). A palavra `$9FAE` só aparece no banco `$8B` em `$8B:9F31`.

**Logo** (bytes + emulador):
- `LoadTitleSequenceGraphics` (`$8B:9B87`) descomprime os gráficos de sprite do título de `$95:80D8` (16 KB, os dois name
  tables de sprite, DMA para a VRAM `$6000`): `A9 00 95` em `$8B:9BC8` (banco) e `A9 D8 80` em `$8B:9BCD` (endereço). A tela
  de boot ("Nintendo presents", `$8B:9146`) carrega o mesmo gráfico com o próprio ponteiro em `$8B:9293`.
- O logo é o spritemap `$8C:879D`: 39 peças (37 de 16×16 + o "TM" `$9C` e o pedaço `$1E` de 8×8), todas com atributo
  `$34xx` (prioridade 3, paleta 2), tiles nas linhas `$00–$9F` do gráfico; citado só pela lista de instruções do objeto do
  logo (`$8B:A0C7` e `$8B:A0CD`). O spritemap `$8C:833D` (38 peças, sem TM) não é citado nos bancos `$8B/$8C`.
- OAM do título (WRAM `$0370`, amostras a cada 15 quadros até o quadro 3000): do quadro 300 em diante o name table 0 só mostra
  os tiles do logo; o name table 1 mostra os sprites do laboratório (`$100–$1B8`) e o "© 1994 Nintendo" (`$1C1–$1CA`). Os
  tiles `$A0–$CC` (placa da Nintendo) só aparecem na tela de boot, com o gráfico carregado por ela. O objeto desenha o
  spritemap em (128, 48) da tela.
- Desenhando o spritemap sobre o gráfico (`specs/img/16-antes-titulo.png`): "SUPER" ocupa as linhas −32 a −11 do objeto,
  "METROID" −10 a 31 (corte limpo entre −11 e −10; o TM à direita em 24–31). As letras do "SUPER" (S, U, P, E, R) estão em
  perspectiva e se sobrepõem na diagonal; I e M não existem nesse tamanho. Paleta 2: 1 branco, 2–6 amarelo → laranja
  (com linhas pontilhadas 3/4, 4/5, 5/6), 8 vermelho (linha de base), 10–12 roxo/azul escuro (extrusão).

## Mudança

Tudo em `tools/frigate/title.py`, chamado pelo build depois do último blob fixo (`title.apply`):

1. **Demos desligadas** — `$8B:9F2C`: `F0 02` (BEQ) → **`80 0A`** (BRA `$9F38`). O `DEC $1F53` continua; o desvio pula sempre a
   troca para `$9FAE` e cai na leitura dos botões. O título fica parado com a música até alguém apertar A/B/START (a tela de
   arquivos; B lá volta ao título, que toca de novo e fica). 2 bytes, nenhum espaço novo.
2. **Logo "METROID / PRIME"** (`specs/img/16-depois-titulo.png`, `16-depois-logo-ampliado.png`):
   - a imagem do logo vanilla (spritemap sobre o gráfico) perde o "SUPER" (linhas < −10); o "METROID" e o TM sobem 16 px
     (para onde estava o "SUPER");
   - "PRIME" embaixo (linha 18 do objeto, centrado, 8 px entre letras): 5 letras desenhadas como máscaras
     (`PRIME_GLYPHS`, 12 linhas) e pintadas no estilo do METROID com os mesmos índices da paleta 2: linha de cima e borda
     esquerda brancas, gradiente 2 → 6 por linha com as linhas pontilhadas, base vermelha (8) e 3 linhas de extrusão escura
     (12/11 pontilhado) embaixo de cada traço. Letras retas, espaçadas, como o "PRIME" do logo do Prime;
   - a imagem nova é cortada em faixas de 16 px a partir do topo, cada faixa em células 16×16 no deslocamento x (0–15) que
     precisa de menos células: **39 peças** (o mesmo número do vanilla, sem 8×8: o TM entrou numa célula do "D");
   - as células vão para as linhas `$00–$9F` de uma cópia do gráfico (zeradas antes; o resto do gráfico igual ao vanilla) e o
     spritemap `$8C:879D` é reescrito **no lugar** (39 peças, 197 bytes, atributo `$34xx` como o vanilla);
   - a cópia vai para o alocador fixo (`$F1:8000`, 9226 bytes) e o ponteiro do título (`$8B:9BC8`/`$8B:9BCD`) aponta para ela.
     A tela de boot continua com o gráfico vanilla.
   - **Compressão com o tempo do vanilla** (`title.pack`): as linhas do logo comprimidas (`compress`) e, depois, os comandos
     da própria stream vanilla para o resto (os que começam nas linhas do logo ou copiam delas viram cópias literais dos bytes
     vanilla). Ver "Desvios".

## Critérios de aceite

1. Título parado não começa demo: validador `check_orphans` → `title.check_demos_off` (bytes: o BRA em `$8B:9F2C` cai em
   `$8B:9F38`, pula o `LDA #$9FAE`; `$9FAE` citado só ali no `$8B`; `LDA #$0028; STA $0998` só em `$8B:A000` e `$82:862F`).
   Teste `titulo_sem_demo_e_novo_jogo` (protege = estado 1 e função `$9F29` aos 3600 e 9600 quadros, nenhuma sala, bits de
   item intactos; falha_quando = a demo começa (mutação: estado `$2A` aos 3600); não_prova = outros jeitos de chegar ao
   estado `$28` fora do título, que o validador cobre pelos bytes).
2. Nenhuma sala vanilla carrega: `check_orphans` sem a exceção das demos; linha "órfãs: 262 salas vanilla sem caminho …,
   19 delas das demos de atração, desligadas (specs/16)".
3. O título continua funcionando: START → tela de arquivos (estado 4); B → título de novo, parado; novo jogo depois de tudo
   começa limpo no hangar (mesmo teste).
4. O logo diz METROID PRIME: validador `title.check_logo` (o título carrega gráfico próprio, igual ao vanilla fora das
   linhas `$00–$9F`; o spritemap desenhado sobre ele é exatamente `logo_image`; peças 16×16, `$34xx`, tiles < `$A0`); teste
   `titulo_metroid_prime` (os tiles do logo na VRAM `$6000`, as 39 peças no OAM `$0370` na posição do objeto, foto).
5. O título carrega no mesmo número de quadros do vanilla: no quadro 600 (quando os testes apertam START) contador de quadros
   `$05B6` = `$0100` e número aleatório `$05E5` = `$8E82`, os de antes da spec (teste `titulo_metroid_prime`).
6. validate 0 problemas com as linhas do Tallon e das rodadas iguais; dois builds com o mesmo sha1; todos os testes.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_orphans` usa `title.check_demos_off`; `title.check_logo`; o blob novo no `fixed_blobs` | 2 checagens |
| run_tests.py (emulador) | `titulo_sem_demo_e_novo_jogo` (substitui o `atracao_e_novo_jogo` da spec 11), `titulo_metroid_prime` (novo) | +1 (82 → 83) |
| imagem | `img/16-antes-titulo.png`, `img/16-depois-titulo.png`, `img/16-depois-logo-ampliado.png` | 3 |

## Riscos e reversão

- Testes que dependem do número aleatório na hora do novo jogo (as lutas medidas da Chozo) quebram se o título levar outro
  número de quadros para carregar (foi o que aconteceu, ver "Desvios"); o teste `titulo_metroid_prime` vigia isso.
- Reverter: tirar a chamada `title.apply` do `tools/build.py` e reconstruir; o validador e os testes da spec 16 acusam.

## Fora de escopo

- Gravar demos novas no Tallon/Chozo (a opção "gravar novas"): a tabela `$82:876C` e as salas das demos ficam na ROM como estão
  (`DEMO_SCENES`); `check_reclaimed` e `check_ruins_in_rom` continuam tratando essas salas como intocáveis (conservador). O
  espaço que só elas usavam aparece agora na linha "órfãs" (pode ser recuperado numa spec futura).
- O resto da tela de título (laboratório, bebê Metroid, "© 1994 Nintendo"), a tela de boot e o "METROID 3" da abertura (que o
  novo jogo pula).
- Logo em outro estilo (o cromado do Prime): o PRIME usa o estilo e a paleta do METROID do Super Metroid.

## Desvios (preenchido na implementação)

- **Tempo de carga do título** (achado na verificação): a primeira versão recomprimia o gráfico inteiro com o `compress` do
  projeto (8044 bytes, mais cópias de dicionário que o vanilla: 6847 bytes de cópia contra 501). O título passou a levar **4
  quadros a mais** para carregar (o jogo fica sem NMI durante a descompressão): no quadro 600 `$05B6` = `$00FC` (era `$0100`)
  e `$05E5` = `$3186` (era `$8E82`). Os testes `chozo_save_station_3`, `chozo_hive_mecha` e `chozo_incinerator_drone`, cujas
  lutas foram medidas com o número aleatório de antes, falharam (80/83, igual nas duas rodadas; com o ponteiro vanilla e o
  resto igual, passavam: o ponteiro era a causa). Correção sem mexer nos testes: `title.pack` (logo + o rabo da stream
  vanilla); a carga voltou ao mesmo número de quadros e os números da hora do novo jogo voltaram a ser os de antes (as lutas e
  todo o resto do jogo seguem idênticos a antes da spec para os mesmos comandos). O critério 5 vigia isso.
- **Logo com 39 peças 16×16 e nenhuma 8×8** (o vanilla tinha 37 + 2): o corte por faixas com deslocamento livre coube no
  spritemap vanilla no lugar; o build recusa se passar de 39.
- **Teste novo** em vez de só trocar o da spec 11: 83 testes (eram 82).

## Resultado

- validate: "136 salas, 284 portas, 0 problemas"; "tallon (…, 44 salas construídas, alcançáveis agora: 44, 20 itens em 7
  rodadas)" **igual**; "rodadas (specs/12m): … 51 itens em 7 rodadas … 51%" **igual**; linha nova das órfãs: "órfãs: 262 salas
  vanilla sem caminho (por área 0-7: 34 54 76 16 56 19 6 1), 19 delas das demos de atração, desligadas (specs/16); bytes só
  delas: $8F 21688, $83 10458, $A1 27363, $B4 4396" (era 243 + 19 só nas demos; $8F 20637, $83 9356, $A1 24030, $B4 4017);
  "bancos: alocador fixo …: 9 blobs, 37963 bytes" (+1 blob, +9226).
- `.ips` sha1 `0f5cc669fc89800b65e43169c9cd5a816fde0653` igual em dois builds; **83/83** testes (82 + `titulo_metroid_prime`;
  `atracao_e_novo_jogo` virou `titulo_sem_demo_e_novo_jogo`); as 3 lutas medidas da Chozo passam sem mudança.
- **Espaço**: `$8B` 4 bytes (2 do desvio, 2 do ponteiro: banco `$95` → `$F1`, endereço `$80D8` → `$8000`); `$8C` 152 bytes
  mudados dentro dos 197 do spritemap (no lugar); fixo +9226 (`$F1:8000`; o vanilla tinha 9481); nenhum banco de código novo.
- **Números no emulador**: quadro 600 `$05B6` = `$0100`, `$05E5` = `$8E82` (iguais aos de antes); quadros 3600 e 9600 estado 1,
  função `$9F29`, sala `$0000`, `$7ED884` = 0; START → estado 4, B → título de novo (estado 1, `$9F29` depois de 3300
  quadros), o logo novo na VRAM; novo jogo: hangar, bits limpos.
- **Fotos** (olhadas): `img/16-antes-titulo.png` (SUPER METROID, a ROM de antes no quadro 2000), `img/16-depois-titulo.png`
  (METROID / PRIME, quadro 2400 do teste), `img/16-depois-logo-ampliado.png` (o logo ampliado 3×: o METROID intacto, o PRIME
  com a borda branca, o gradiente e a extrusão; o TM ao lado do D). Também `build/tests/16_titulo_parado.png` e
  `16_titulo_de_volta.png` (iguais ao de cima: nenhuma demo, o título de volta da tela de arquivos).

## Mutações

Rodadas no scratchpad (`…/scratchpad/s16/py/mut.py`, chamando as checagens com ROMs mudadas; e o emulador com cópias da ROM):

| # | Mutação | Pega |
|---|---|---|
| M1 | `$8B:9F2C` volta a `F0 02` (demos ligadas) | `check_orphans`: "demos: $8B9F2C = f0 02, esperado 80 0a …"; emulador: estado `$2A` aos 3600 quadros |
| M2 | `$8B:9F2C` = `80 02` (BRA que cai no `LDA #$9FAE`) | `check_orphans` (mesma mensagem) |
| M3 | outro `LDA #$0028; STA $0998` em `$FF:F000` | `check_orphans`: "estado $28 gravado em [… $FFF000] …" |
| M4 | ponteiro do gráfico de volta a `$95:80D8` | `check_logo`: "o gráfico do logo ainda é o vanilla" |
| M5 | uma peça do spritemap 1 px mais baixa | `check_logo`: "o logo desenhado não é METROID + PRIME" |
| M6 | 1 pixel do logo trocado no gráfico | `check_logo` (mesma mensagem) |
| M7 | 1 pixel do "©" (fora das linhas do logo) | `check_logo`: "o gráfico mudou fora das linhas $00-$9F do logo" |
| M8 | gráfico recomprimido inteiro (a 1ª versão) | `titulo_metroid_prime`: `$05B6` = `00FC`, `$05E5` = `3186`; e as 3 lutas da Chozo |
| M9 | spritemap e ponteiro vanilla (SUPER METROID) | `titulo_metroid_prime`: VRAM `$6010` e o OAM diferentes |

## Decisões para confirmar

1. **Título parado fica parado** (com a música) em vez de repetir a animação de abertura; a animação toca de novo quando se
   volta da tela de arquivos com B. Alternativa: recomeçar o título depois de um tempo (mais código).
2. **Desenho do "PRIME"**: letras retas, espaçadas, menores que o METROID, nas cores do METROID (fotos). Ajustar tamanho,
   espaço ou forma é só mudar `PRIME_GLYPHS`/`PRIME_GAP`/`PRIME_Y` (o build recusa se não couber em 39 peças).
3. O TM ficou ao lado do METROID (subiu com ele).
