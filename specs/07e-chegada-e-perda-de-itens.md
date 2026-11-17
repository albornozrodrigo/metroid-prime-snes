# 07e — Chegada no Tallon com perda de itens, e a nave salvando lá

Estado: verificada (22/10/2026: validate 33/68/0; .ips sha1 `4ad1826b…7ec77`, igual ao reconstruir; 24/24 testes)
Esforço estimado: 3–4 h (spec 1 h, rotina 30 min, testes 1 h, verificação 1 h)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (decisão 3 "Perda de itens", critérios 3 e 4)

## Contexto

Desde a 07g o fim da fragata pousa na Landing Site nova do Tallon (área 0), mas a Samus chega com
**todo** o equipamento da fragata (Varia, Morph, Bombas, Space Jump, Grapple, X-Ray, Charge/Wave/
Ice/Plasma, 30 mísseis). No Prime ela perde tudo numa explosão durante a fuga e chega só com o Power
Beam. O teste da rota da 07g zera os itens por RAM para simular isso. Esta spec faz o jogo zerar de
verdade, num ponto que o jogador não consegue pular (nem resetando no meio da cena), e confere que
a nave do Tallon recarrega e salva como a nave vanilla.

## Estado atual (verificado)

- **RAM do equipamento** (`vendor/sm/src/variables.h:397-433`, mesmos nomes de `NewSaveFile`
  `$81:B2CB`, `sm_81.c:2435`): `$09A2` itens equipados, `$09A4` itens coletados, `$09A6` raios
  equipados, `$09A8` raios coletados (raio 0 = Power Beam), `$09C0` modo da reserva, `$09C2/$09C4`
  energia/máxima, `$09C6/$09C8` mísseis/máx., `$09CA/$09CC` supers, `$09CE/$09D0` power bombs,
  `$09D2` item escolhido no HUD (0 = raio), `$09D4/$09D6` reserva máx./atual, `$0A04` item do
  auto-cancel do HUD. O jogo novo (`tools/build.py:228-230`, rotina `$82:F70F`) põe
  `$09A2/$09A4 = D205`, `$09A6/$09A8 = 100B`, `$09C6/$09C8 = 001E`; energia 99/99 (vanilla).
- **O que o save grava** (`SaveToSram` `$81:8000`, `sm_81.c:40`): os 96 bytes de `$09A2` a `$0A01`
  (tudo acima menos o `$0A04`) e o bloco de eventos/itens/estações `$7ED7C0…`.
- **Recarga ao carregar**: estado 6 (`InitAndLoadGameData`, `sm_82.c:80-110`) chama
  `Samus_Initialize`, `LoadFromLoadStation`, `StartGameplay` (que chama `UpdateBeamTilesAndPalette`,
  `sm_80.c:1608`) e `InitializeHud` (`sm_80.c:1320-1345`: desenha os dígitos de míssil/super/PB só
  se a máxima não for 0). Ou seja, mudar a RAM antes do carregamento basta para o HUD, o raio e o
  traje ficarem certos.
- **Caminho do final** (spec 05, `tools/frigate/ending.py`): `GunshipTop_20` (`$A2:AD0E`), quando a
  nave passa da altura final, faz `JSR` (em `$A2:AD20`, bytes `20 02 F5`, conferidos no build atual)
  para `ending_state_routine` em **`$A2:F502`** (16 bytes: `AD 9F 07 C9 03 00 D0 04 A9 21 00 60 A9 26
  00 60`), que devolve `$21` na área 3, e o `STA $0998` seguinte grava o estado. `GunshipTop_20` troca
  o próprio passo para `GunshipTop_21` na mesma chamada (`sm_a2.c:1718-1727`): a rotina roda **uma
  vez**. O estado `$21` escurece e **salva** (`$82:8388`); o `$22` é a cena; o estado 6 carrega a
  área 0 estação `$12`; a nave pousa e `GunshipTop_7` salva na estação 0 da área 0.
- **Save no meio da cena**: o save do estado `$21` é o que o reset carrega (teste
  `final_reset_no_meio_da_cena`, spec 05). Qualquer zeragem feita **depois** dele (no estado 6 ou no
  pouso) deixaria esse save com os itens: resetar durante a cena devolveria tudo.
- **Espaço em `$A2`**: livre de `$A2:F512` a `$A2:FFFF` (2798 bytes, lido na ROM do build atual).
- **Nave do Tallon** (`sm_a2.c` `GunshipTop_8…16`): agachar em cima dela (Samus parada, `$0998 = 8`,
  ↓) abre a nave, recarrega energia/mísseis/supers/PBs/reserva até a máxima (`GunshipTop_12`),
  pergunta "save?" (caixa `$1C`); com sim liga o bit 0 de `$7ED8F8`, põe `load_station = 0` e salva na
  **área atual**. Os patches da nave em `$A2` (`ending.gunship`) só mudam a área 3: a entrada e a
  decolagem comparam `$079F` com 3; fora dela vale o vanilla (entrada pelo estado do jogo, decolagem só
  com o evento `$0E`, que nunca liga). A estação 0 da área 0 já aponta para a Landing Site nova (07g).
- **Itens de PLM** (`$7ED870…`): a fragata e o Tallon não têm nenhum PLM de item (o build só põe save
  station, map station e tampas de porta cinza, `tools/build.py:469-480`). Nada a mexer.
- Testes hoje: `lands_on_landing_site` (`tests/run_tests.py:181-187`) espera, depois do pouso, o
  equipamento da fragata (`$09A4 = D205`, `$09C8 = 001E`); `tallon_rota_mvp` zera
  `$09A2/$09A4/$09A6/$09A8` por RAM depois do pouso.

## Mudança proposta

1. **Onde zerar: na decolagem, dentro de `ending_state_routine`** (`tools/frigate/ending.py`), no
   ramo da área 3, antes de devolver `$21`. É o último ponto antes do save do estado `$21`; assim o
   save do meio da cena, o carregamento e o save do pouso já saem sem itens. No Prime os itens se
   perdem na explosão da fuga: bate. Fora da área 3 a rotina continua devolvendo `$26` sem mexer
   em nada.
2. **Rotina nova** (substitui a de 16 bytes, mesmo lugar `$A2:F502`, cresce para 70 bytes, até
   `$A2:F547`; nada vem depois dela em `$A2`, sobram 2744 bytes):
   ```
   AD 9F 07     LDA $079F          ; área
   C9 03 00     CMP #$0003
   D0 3A        BNE vanilla
   9C xx 09     STZ $09A2, $09A4, $09A6, $09A8      ; itens e raios: só o Power Beam
   9C C0 09     STZ $09C0                           ; modo da reserva
   9C xx 09     STZ $09C6 … $09D6 (9 palavras)      ; mísseis, supers, PBs, item do HUD, reserva
   9C 04 0A     STZ $0A04                           ; auto-cancel do HUD
   A9 63 00     LDA #99
   8D C2 09     STA $09C2 ; 8D C4 09 STA $09C4       ; energia 99/99
   A9 21 00     LDA #$0021
   60           RTS
   vanilla:
   A9 26 00 60  LDA #$0026; RTS
   ```
   Os endereços zerados ficam numa constante `ARRIVAL_ZEROED` e a energia em `ARRIVAL_ENERGY = 99`.
   O banco de dados é `$A2` (dentro de `$80–$BF`): `STZ abs` alcança a RAM baixa, como o `LDA $079F`
   que a rotina já usa. X (índice do inimigo) não é tocado.
3. **Nave do Tallon**: nenhuma mudança de código (vanilla). Só o teste novo.
4. **Testes** (`tests/run_tests.py`):
   - `lands_on_landing_site` passa a esperar o equipamento da chegada (valores exatos abaixo) em vez
     do da fragata;
   - `tallon_chegada` (novo), `tallon_nave_salva` (novo);
   - `final_reset_no_meio_da_cena` ganha `expect $09A4 = 0000` logo depois de carregar o save do
     meio da cena;
   - `tallon_rota_mvp` perde a zeragem por RAM (o teste já embarca e pousa de verdade: o atalho dele
     é só o `poke` do chefe morto, antes da decolagem).
5. `validate.py`: `ending.check_rom` já compara a rotina inteira com `ending_state_routine()`;
   a mensagem passa a citar a perda de itens.

**Valores exatos depois do pouso** (`tallon_chegada`): `$09A2 = $09A4 = $09A6 = $09A8 = 0000`,
`$09C0 = 0000`, `$09C2 = $09C4 = 0063`, `$09C6 … $09D6 = 0000` (mísseis, supers, PBs, HUD, reserva),
`$0998 = 0008`, `$079F = 0000`, `$079B` = Landing Site nova, `$078B = 0000`.

## Critérios de aceite

1. Teste `tallon_chegada` (novo): jogo novo, `poke` do chefe morto, confere que a Samus tem o
   equipamento da fragata (`$09A4 = D205`), embarca, espera o pouso → estado 8, área 0, Landing Site,
   estação 0, e os valores exatos acima; foto `build/tests/tallon_chegada_hud.png` (HUD sem contador
   de míssil, Power Beam). protege = a zeragem na decolagem; falha_quando = a rotina some, zera
   pouco (ex.: só `$09A2`), ou zera depois do save; não_prova = que a cena inteira da fragata é jogada
   (isso é o `fuga_ridley_nave_e_final`, que usa a mesma checagem de pouso).
2. `fuga_ridley_nave_e_final` (fragata inteira de verdade, chefe morto a tiros) também termina com os
   valores exatos (via `lands_on_landing_site`). falha_quando = algum caminho real devolve os itens.
3. Reset no meio da cena: `final_reset_no_meio_da_cena` carrega o save do estado `$21` e já está sem
   itens (`$09A4 = 0000` no estado `$22`), e pousa com os valores exatos. protege = o save do meio da
   cena; falha_quando = a zeragem acontece depois do save (pouso, estado 6).
4. Teste `tallon_nave_salva` (novo): depois do pouso, energia baixada para 16, `$09E0` (horas de
   jogo, gravadas no save) = 5 como marca, `$078B = 1`; agachar na nave → energia volta a 99, caixa de
   save, A (sim) → `$078B = 0000`, bit 0 de `$7ED8F8`; zerar a energia → game over → continue → estado
   8, área 0, Landing Site, `$09E0 = 0005` (o save veio da nave, não do pouso), equipamento zerado,
   energia 99. protege = nave vanilla na área 0 (patches de `$A2` só na área 3) + estação 0 da área 0;
   falha_quando = a nave não abre/não salva no Tallon ou o continue vai a outro lugar; não_prova = a
   resposta "não".
5. `tallon_rota_mvp` passa **sem** a zeragem por RAM.
6. `python3 -I tools/validate.py` → 0 problemas; `python3 -I tools/build.py` com sha1 igual em dois
   builds; `python3 -I tests/run_tests.py` → 24/24 (22 + 2 novos).
7. Os testes novos/alterados falham na ROM anterior (`pre07e.sfc`, cópia no scratchpad).

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `ending.check_rom` (rotina inteira, já existente) | 0 (+0) |
| run_tests.py (emulador) | `tallon_chegada`, `tallon_nave_salva`; `lands_on_landing_site` e o reset alterados; rota sem zeragem | +2 (4 alterados) |
| imagem | HUD depois do pouso | +1 |

**Mudança de expectativa de testes existentes:** `fuga_ridley_nave_e_final`,
`final_continue_na_landing_site`, `final_reset_no_meio_da_cena` e `tallon_rota_mvp` (pela
`lands_on_landing_site`) passam a esperar, depois do pouso, `$09A4 = 0000` e `$09C8 = 0000` (e o resto
dos valores exatos) em vez de `$09A4 = D205` e `$09C8 = 001E`. Motivo: é o objetivo desta spec
(decisão 3 do épico); a spec 05 tinha posto "o equipamento continua" como provisório (fora de escopo
dela).

## Riscos e reversão

- Durante os poucos quadros do estado `$21` (tela escurecendo) o HUD já está sem mísseis; a Samus
  está dentro da nave e não atira. Sem efeito visível.
- Se um dia houver outra decolagem na área 3 que não seja o fim da fragata, ela também tiraria os
  itens. Hoje só existe esta.
- Reversão: voltar `ending_state_routine` aos 16 bytes e os testes; reconstruir.

## Fora de escopo

- Itens do Tallon (07h), mapa "TALLON" (07f), animação da perda de itens (no Prime é uma cena de
  câmera), visores do Prime.

## Desvios (preenchido na implementação)

Verificação (22/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `33 salas, 68 portas, 0 problemas`.
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `4ad1826bda0ef2b7d4ed91dc15da4d8b1617ec77` nas duas. `$A2` livre a partir de `$A2:F548`.
- `python3 -I tests/run_tests.py` → **24/24** (2 min).
- ROM anterior (`pre07e.sfc`, sha1 do .sfc `ee89ceee…dee92`, .ips da 07g): os 6 testes novos/alterados
  falham só nas checagens de equipamento (`$09A2/$09A4 = D205`, `$09A6/$09A8 = 100B`,
  `$09C6/$09C8 = 001E`); o reset falha também no `$09A4 = D205` logo depois de carregar o save do
  meio da cena. A parte da nave do `tallon_nave_salva` passa na ROM anterior: a nave do Tallon já
  era vanilla (esperado; esta spec só a testa).
- Imagens: `specs/img/07e-chegada-hud.png` (HUD só com "ENERGY 99", sem contador de míssil nem
  ícones, Power Suit; compare com `07g-tallon-chegada.png`: míssil 030, Grapple/X-Ray, Varia),
  `07e-nave-save.png` (caixa "WOULD YOU LIKE TO SAVE?" na nave do Tallon), `07e-nave-continue.png`
  (continue em cima da nave).

Desvios e detalhes:

- **Tamanho da rotina**: 70 bytes (`$A2:F502–F547`), não 64 (conta errada no rascunho).
- **Save da nave precisa de dois A**: na ROM (`$85:80BF`), depois do "sim" da caixa `$1C` a nave abre
  a caixa `$18` ("save completed") e só grava depois que ela fecha (o código C portado não mostra
  isso). O teste aperta A, espera 300 quadros e aperta A de novo, como `step_on_save_station`.
- **Marca do save**: `$09E0` (horas de jogo, dentro dos 96 bytes salvos) = 5 antes de agachar; o
  continue lê `0005`, o que prova que o save veio da nave e não do pouso.
- `tallon_chegada` usa o atalho do chefe morto (`poke 7ED82B 01`) antes da decolagem; a decolagem, a
  cena e o pouso são de verdade. A fragata inteira jogada de verdade é o `fuga_ridley_nave_e_final`,
  que termina com a mesma checagem (`lands_on_landing_site`).
- `POWER_BEAM_ONLY_RAM` continua no fim do `tallon_rota_mvp` (confere que nada muda no caminho); só
  a zeragem por `poke` saiu.
- `ending.check_rom` não mudou de lógica (já comparava a rotina inteira); só a mensagem.
