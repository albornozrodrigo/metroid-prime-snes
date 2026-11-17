# 03 — Cota de mapa da Tourian na SRAM

Estado: verificada (data 22/10/2026; sha1 do .ips 267661235301fe71dfac77d6821ee385b9481667; testes 14/14)
Esforço estimado: código 30–45 min (módulo novo de ~45 linhas, `write_map_save_list` reescrita,
+1 linha no validate); testes 20 min (+1 checagem no validate, +1 teste no emulador); documentação
10 min; verificação completa ~3 min de máquina. Total: 1–1,5 h.

## Contexto

Ninguém vê problema jogando hoje: é uma **restrição latente**, não um bug vivo. Para guardar os 30
bytes de mapa da fragata, o build tirou 12 bytes da cota da Tourian (área 5). A Tourian não é usada
ainda, mas vai ser a Impact Crater; e a Tallon Overworld (área 0) vai precisar de uma lista nova.
O HANDOFF pede para rever. A pesquisa mostrou que **não é preciso tirar de ninguém**: o espaço do
save para o mapa tem 1280 bytes e o vanilla usa só 327.

## Estado atual (verificado)

Como funciona o save do mapa (C `PackMapToSave` $81:834B / `UnpackMapFromSave` $81:82E4, conferido
nos bytes da ROM base):

- Para cada área 0–5 (`CMP #$0006` no laço; Ceres e Debug não são salvas), o jogo copia só os
  bytes listados da máscara de 0x100 bytes da área (`$7ECD52 + área*0x100`) para o buffer
  `$7ED91C` (`STA $7ED91C,X`).
- Tabelas em $81 (lidas de `base/sm_fix.sfc`):

  | Tabela | Endereço | Vanilla |
  |---|---|---|
  | quantidade por área (byte) | $81:8131 | 74, 72, 76, **18**, 66, **21** (soma 327) |
  | início no buffer (word) | $81:8138 | 0, 74, 146, 222, 240, 306 |
  | ponteiros das listas ($81) | $81:82D6 | $8146, $8196, $81E6, $8236, $8256, $82A6 |

- Espaço de cada lista antes da seguinte: 80, 80, 80, **32**, 80 bytes; a da área 5 tem 21 bytes
  usados, 11 zeros e, a partir de $81:82C6, 8 bytes de dados desconhecidos (`2d 31 35 39 3d 41 45 46`).
- A contagem é um contador de 16 bits (`AND #$00FF; STA $12 … DEC $12; BNE`): **0 faria 65536
  voltas** e escreveria fora do buffer. Contagem válida: 1–255.
- **Orçamento real:** o buffer vai de `$7ED91C` até `$7EDE1B` (`plm_instruction_timer` começa em
  `$7EDE1C`, fora do slot; `vendor/sm/src/variables.h:1106-1107`) = **0x500 = 1280 bytes**, dentro
  do slot de save ($7ED7C0–$7EDE1B, 0x65C bytes, slots na SRAM em $0010/$066C/$0CC8, `$81:812B`).
  O vanilla usa 327; **sobram 953 bytes** que já são gravados e lidos em todo save.
- Esses 953 bytes estão livres:
  - nenhuma variável do port C fica entre `$7ED91C` e `$7EDE1C`;
  - varredura da ROM por endereçamento longo em $7E:D91C–$7E:DE1B: só as duas rotinas acima
    ($81:8330 e $81:8386); as outras 10 ocorrências são bytes desalinhados (gráficos em
    $95/$BE/$BF, meio de instruções em $A0/$A7/$A8);
  - emulador (cópia do projeto): `$7EDA63`–`$7EDE1B` fica todo zero depois do save, do continue,
    da map station e da fuga inteira até a nave; valores-sentinela escritos em $7EDA63, $7EDC00 e
    $7EDE1B antes de salvar, zerados na WRAM depois do save, **voltam** após morrer e dar continue
    (vieram da SRAM).
- O que o build faz hoje: `tools/build.py:77-84` (constantes, `MAP_SAVE_DONOR_AREA = 5`) e
  `tools/build.py:261-281` (`write_map_save_list`): área 3 recebe 30 bytes (lista no lugar vanilla
  $81:8236, cabe em 32), área 5 cai de 21 para **9**, áreas 4 e 5 andam 12 bytes no buffer. ROM
  gerada: contagens `74, 72, 76, 30, 66, 9`, inícios `0, 74, 146, 222, 252, 318`.
- `tools/validate.py` não confere nada disso; só o build falha (RuntimeError) se a fragata passar
  de 32 bytes.

Respostas às perguntas da pesquisa:

- **(a) Algo quebra hoje?** Não. O jogo só usa a área 3 (começa no hangar, continue volta para a
  área 3, a nave leva aos créditos). Crateria (área 0) e Tourian (5) nunca são visitadas. Os 13
  testes passam. Na fuga completa nenhum bit explorado cai fora dos 30 bytes listados (comparação
  da máscara `$7E07F7` com `pausemap.build` no emulador). Prova do problema latente: escrevendo o
  bit explorado da Tourian no byte $5A (21º da lista vanilla) e salvando, depois do continue ele
  **some** no build atual; o byte $26 (1º) volta.
- **(b) Orçamento:** 1280 bytes por slot; vanilla 327; livres 953. Dá para dar a cada área
  refeita o que ela precisa sem tirar de nenhuma outra (limite 255 por área).
- **(c) Restrição para Tallon e Impact Crater:** ver "Mudança proposta", item 5.

## Causa (problemas)

A correção do mapa sumindo depois do save assumiu que "o total é fixo"
(`research/sm_room_format.md:652`) e por isso pegou bytes da Tourian. O total que é fixo é o
buffer de 1280 bytes, não a soma das cotas vanilla.

## Mudança proposta

1. **Módulo novo `tools/frigate/mapsave.py`** (fonte única do layout; protótipo testado):
   - constantes `COUNTS = 0x818131`, `PACKED_OFFS = 0x818138`, `LISTS = 0x8182D6`,
     `VANILLA_COUNTS = (74, 72, 76, 18, 66, 21)`, `VANILLA_PACKED = (0, 74, 146, 222, 240, 306)`,
     `VANILLA_LIST_PTRS = (0x8146, 0x8196, 0x81E6, 0x8236, 0x8256, 0x82A6)`,
     `LIST_ROOM = (80, 80, 80, 32, 80, 21)`, `PACKED_SIZE = 0x500`, `VANILLA_END = 327`,
     `MAX_COUNT = 255`;
   - `needed(mask) -> list[int]`: índices dos bytes não nulos da máscara de revelação;
   - `layout(custom) -> {área: início}`: cada área refeita ganha um bloco **depois** dos 327
     bytes vanilla, em ordem de área (área 3 hoje: início 327);
   - `check(custom) -> list[str]`: área fora de 0–5; contagem fora de 1–255; soma
     `327 + Σ contagens > 1280`.
2. **`tools/build.py`**: apagar `MAP_SAVE_*` (linhas 80-84); `write_map_save_list(rom, area, offs)`
   chama `mapsave.check` (RuntimeError com as mensagens), confere as três tabelas vanilla (assert),
   falha se `len(offs) > LIST_ROOM[area]`, e escreve só três coisas: contagem da área em
   `$81:8131+área`, início em `$81:8138+2*área` (= `layout`), lista no ponteiro vanilla da área.
   **Nenhuma outra área muda.** Chamada em `write_pause_map`:
   `write_map_save_list(rom, a, mapsave.needed(reveal))`. Imprimir no log do build:
   `mapa na SRAM: área 3 = 30 bytes em +327 (357/1280 usados)`.
   Resultado na ROM: contagens `74, 72, 76, 30, 66, 21`; inícios `0, 74, 146, 327, 240, 306`;
   área 3 grava em `$7EDA63`–`$7EDA80`.
3. **`tools/validate.py`**: importar `mapsave`; `FRIGATE_AREA = 3`; em `check()`, depois de
   `check_map` (linha 109):
   `problems += mapsave.check({FRIGATE_AREA: mapsave.needed(pausemap.build(ROOMS)[1])})`.
4. **Documentação**: `research/sm_room_format.md` §12 ("SRAM keeps only some explored bytes"):
   trocar "The total is fixed…" pelo orçamento de 1280 bytes e o layout novo; README (bug
   resolvido: "tira a diferença da cota da Tourian" → "bloco próprio depois dos dados vanilla");
   HANDOFF: tirar a pendência da cota da Tourian.
5. **Regra para áreas futuras (Tallon = 0, Impact Crater = 5)**, escrita no docstring do módulo:
   - a lista de bytes de cada área é gerada da máscara de revelação (`mapsave.needed`), nunca à mão;
   - cada byte da máscara cobre 8 tiles de uma linha; a contagem é o número de pares
     (linha, grupo de 8 colunas) com alguma sala. Máximo 255 por área;
   - todas as áreas refeitas juntas cabem em **953 bytes**;
   - a lista fica no lugar vanilla enquanto couber: **área 0 até 80 bytes** ($81:8146–$81:8195),
     **área 5 até 21 bytes**. Passou disso, o build para com erro claro; a solução (fora desta
     spec) é pôr a lista no espaço livre de $81 (`$81:EF1A`–`$81:FEFF`, 4070 bytes de `$FF`,
     conferido na ROM base e na gerada) e apontar `$81:82D6+2*área` para lá.

## Critérios de aceite

1. Build gera contagens `74, 72, 76, 30, 66, 21` em $81:8131 e inícios `0, 74, 146, 327, 240, 306`
   em $81:8138 (assert no build + linha no log: protege=nenhuma área perde bytes;
   falha_quando=voltar a usar doador; não_prova=que o jogo lê esses bytes).
2. `python3 -I tools/validate.py` passa com 0 problemas no estado atual (30 bytes).
3. Mutação: com `mapsave.MAX_COUNT = 29` o validate acusa `área 3: mapa usa 30 bytes; a SRAM
   aceita 1-29`; `mapsave.check({3: list(range(256))})` acusa 256 bytes; quatro áreas com 255
   bytes acusam `mapas salvos somam 1347 bytes; o save tem 1280`; área com 0 bytes é acusada.
   (Conferido no protótipo; fica como teste de unidade dentro de `validate.py` ou rodado à mão na
   revisão: protege=checagem não fica muda; não_prova=layout na ROM.)
4. Teste novo `mapa_da_tourian_sobrevive_ao_save` em tests/run_tests.py: novo jogo até a Reactor
   Core Entrance, `poke 7ED278 FF` e `poke 7ED2AC FF` (bytes $26 e $5A da cópia salva da área 5,
   `$7ECD52+0x500`), salvar, morrer, continue, `expect 7ED278 00FF` e `expect 7ED2AC 00FF`
   (protege=cota da Tourian inteira; falha_quando=área 5 com menos de 21 bytes — **falha no build
   atual** em 7ED2AC, passa no protótipo; não_prova=mapa da Tourian desenhado).
5. Teste existente `save_station_grava_e_continue_volta_nela` continua passando (bits da fragata
   voltam depois do continue, agora lidos de +327).
6. Os 13 testes atuais + o novo passam (`python3 -I tests/run_tests.py`: 14/14).

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `mapsave.check` da área 3 (contagem 1–255, soma ≤ 1280) | +1 |
| build.py | asserts das tabelas vanilla + linha de log com o uso | +1 |
| run_tests.py (emulador) | `mapa_da_tourian_sobrevive_ao_save` | +1 |
| imagem | — | 0 |

## Riscos e reversão

- **Saves feitos com builds anteriores**: o mapa explorado da fragata é lido de +327 (zeros num save
  velho), então aparece apagado uma vez; nada mais (áreas 4/5 recebem lixo de bits que nunca são
  mostrados, porque o jogo não vai lá). Itens, chefes e estação salva não mudam.
- A conclusão "953 bytes livres" vem de: port C, varredura de endereçamento longo e emulador só
  dentro da fragata. Código que acesse `$7EDA63+` com DB=$7E e endereço absoluto escaparia da
  varredura; o teste de sentinela cobre o caminho jogado. Se aparecer conflito, o protótipo mostra o
  sintoma (sentinela some) e o recuo é o build antigo.
- Reverter: restaurar `tools/build.py`/`tools/validate.py`, apagar `tools/frigate/mapsave.py`,
  reconstruir.

## Fora de escopo

- Mover listas para o espaço livre de $81 (só quando a área 0 passar de 80 bytes ou a 5 de 21;
  spec 07 ou a da Impact Crater).
- Mapa, ícones e nomes das áreas 0 e 5.
- Os 8 bytes desconhecidos em $81:82C6.
- Bits explorados marcados pela tabela de salas de chefe ($90:A83A, `DisableMinimapAndMarkBossRoomAsExplored`)
  fora das salas: não aconteceu na fuga testada; o minimapa da Air Lock é a spec 02.

## Desvios (preenchido na implementação)

Nenhum. Notas: as mutações do critério 3 foram rodadas à mão (opção prevista no critério), não
ficaram como teste dentro de `validate.py`; `check` também acusa área fora de 0–5 com
`área N: só as áreas 0-5 têm mapa salvo`. A linha `mapa na SRAM: …` sai de `write_map_save_list`, antes
da lista de salas no log. O teste novo falhou na ROM anterior (`FAIL 7ED2AC = 0000, esperado 00FF`).
