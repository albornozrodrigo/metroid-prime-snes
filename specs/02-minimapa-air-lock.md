# 02 — Minimapa apagado na Air Lock

Estado: verificada (22/10/2026: validate 0 problemas; build sha1 0f31447b6163c4a5764cac800c47e7a785ed50fa; testes 13/13; checagens novas falham na ROM antiga)
Esforço estimado: código 10 min (1 instrução); testes 20 min (3 checagens num teste que já existe);
verificação completa ~3 min de máquina (build + validate + 13 testes). Total: menos de 1 hora.

## Contexto

Na fuga, quando a Samus entra na Air Lock e o Meta Ridley aparece, o minimapa do HUD (canto
superior direito) fica vazio. Ele só volta na sala seguinte. O jogador perde a referência do mapa
justo na cena final, e a Air Lock não é sala de chefe: não há luta, só a cena do Ridley voando.
Está na lista de pendências do `HANDOFF.md`.

## Estado atual (verificado)

Tudo conferido na ROM gerada por `tools/build.py` (cópia privada do projeto) e no emulador
`tools/snesrun`, com o roteiro do teste `fuga_ridley_nave_e_final` mais leituras de RAM.

1. **Quem apaga o minimapa.** A rotina vanilla `$90:A7E2` (`DisableMinimapAndMarkBossRoomAsExplored`
   no C de `vendor/sm/src/sm_90.c:2200`) faz, lida byte a byte na ROM:
   ```
   $90:A7E8  A9 01 00     LDA #$0001
   $90:A7EB  8D F7 05     STA $05F7          ; minimapa desligado
   $90:A7EE  A9 1F 00 / 09 00 2C              ; tile vazio $2C1F
   $90:A7F7  9F 3C C6 7E  STA $7EC63C,x      ; 3 linhas x 5 tiles do HUD
   $90:A7FB  9F 7C C6 7E  STA $7EC67C,x
   $90:A7FF  9F BC C6 7E  STA $7EC6BC,x
   $90:A80A  AD 9C 17     LDA $179C          ; boss_id: procura na tabela $90:A83A
   ```
   A tabela `$90:A83A` tem os chefes 3, 6, 7, 8, 10 e 5 (marcam a sala do chefe como explorada).
2. **Quem chama.** O init do Ridley de Ceres (`$A6:A0F5`, C em `sm_a6.c:1076`), logo depois da
   checagem "chefe morto → me apago":
   ```
   $A6:A0FF  F0 0D        BEQ $A10E          ; chefe vivo -> continua
   $A6:A10E  8B           PHB                ; <- nosso init pula para cá
   ...                                        ; zera $7E:2000-2FFF
   $A6:A122  22 E2 A7 90  JSL $90:A7E2       ; desliga e apaga o minimapa
   ```
   Nosso init do Meta Ridley (`tools/frigate/ending.py:117`, `meta_ridley_init`, montado em
   `$A6:FEBC`) começa com `JSL $A6:A10E` (`RIDLEY_INIT_PAST_BOSS_CHECK`, `ending.py:45`) para
   reaproveitar o resto do init de Ceres. Por isso herda o `JSL $90:A7E2`.
3. **Quem desenha.** `UpdateMinimap` (`$90:A91B`, `sm_90.c:2230`) roda todo quadro (chamada pelas
   rotinas de movimento da Samus) e sai logo no começo se `$05F7 != 0`. É a mesma rotina que liga
   o bit de "explorado" da tela atual (`$7E07F7+`): com o minimapa desligado, **a sala também não
   é marcada no mapa**.
4. **Quem religa.** `$05F7` só volta a 0 na troca de sala (`GameState_10_LoadingNextRoom`,
   `sm_82.c:3824`) e em alguns pontos fixos (novo jogo, Crocomire, elevador de Ceres). Por isso o
   minimapa volta na sala seguinte, e continua apagado mesmo depois que o Ridley vai embora.
5. **Não é a sala nem o estado.** O cabeçalho da Air Lock (`tools/build.py:372`,
   `conditional_header`) não tem nada de chefe; o que liga `$05F7` é só o init da espécie. O valor
   de chefe da espécie (byte $10 do cabeçalho: `$0001`, igual ao do Ridley de Ceres `$A0:E13F`)
   não está na tabela `$90:A83A`, então a rotina não marca nenhuma sala extra; ele só põe
   `$179C = 1` (efeito à parte, ver Fora de escopo).
6. **Medido no emulador** (ROM atual, cena carregada; quadros do roteiro):

   | Momento | `$05F7` | HUD `$7EC67C` (linha do meio) | `$7E0803` (bit $04 = Air Lock) |
   |---|---|---|---|
   | f16808, Air Lock com o Ridley | `0001` | `1F 2C` x5 (vazio) | `0E` |
   | f17154, Deck Alpha Access Hall | `0000` | `25 E8 20 28 21 3C 1F 2C 1F 2C` | `0E` |
   | f17590, volta à Air Lock (byte zerado antes, de propósito) | `0001` | vazio | `02` (Air Lock **não** marcada) |
   | f18190, depois que o Ridley saiu | `0001` | vazio | `02` |

   Imagem: `specs/img/02-antes-air-lock.png` (canto superior direito vazio).

## Causa (problemas)

O nosso init do Meta Ridley reaproveita o init do Ridley de Ceres a partir de `$A6:A10E`, e esse
trecho chama `$90:A7E2`, a rotina que o Super Metroid usa em salas de chefe para desligar o
minimapa (`$05F7 = 1`) e apagar os 15 tiles dele no HUD. Nada religa `$05F7` até a próxima troca de
sala. Como o desenho do minimapa e a marcação de "explorado" são a mesma rotina, a Air Lock também
deixa de ser marcada no mapa enquanto esse estado está carregado.

## Mudança proposta

Uma instrução no fim do trecho reaproveitado, dentro do **nosso** init (não muda nada vanilla):
`STZ $05F7` (`9C F7 05`) logo depois do `JSL $A6:A10E; REP #$30`. No quadro seguinte
`UpdateMinimap` redesenha os 15 tiles e volta a marcar a tela explorada.

- Onde: `tools/frigate/ending.py`, `meta_ridley_init`. Espaço: +3 bytes no bloco do Ridley em `$A6`
  (livre de `$A6:FEBC` a `$A6:FFFF`; hoje usado até `$A6:FF8E`, passa a `$A6:FF91`).
- O init roda com DB=`$A6`; `STZ $05F7` absoluto cai no espelho da WRAM baixa (`$A6:05F7` =
  `$7E:05F7`), como os `STA $0F7A` que já estão nesse init.
- Diferença de ROM conferida (antes x depois): só `$A0:F817` (byte baixo do ponteiro de main no
  cabeçalho da espécie, que andou 3 bytes) e `$A6:FEC2-$A6:FF90` (nosso código, deslocado). Nenhum
  byte vanilla muda: o Ridley de Ceres/Norfair e as outras salas de chefe ficam iguais.

Código resultante em `$A6:FEBC`:
```
$A6:FEBC  22 0E A1 A6  JSL $A6:A10E
$A6:FEC0  C2 30        REP #$30
$A6:FEC2  9C F7 05     STZ $05F7     ; novo: religa o minimapa
$A6:FEC5  A9 00 00     LDA #$0000    ; (resto igual: sem bebê Metroid, posição, timer)
```

Diff exato (prototipado na cópia privada):
```diff
--- tools/frigate/ending.py
+++ tools/frigate/ending.py
@@ -61,6 +61,7 @@
 CHECK_EVENT = 0x808233       # carry = event A happened
 RIDLEY_POP_PROPS = 0x2800    # vanilla Ceres Ridley placement ($A1:E939)
 RIDLEY_PALETTE_SLOT = 0x0001
+MINIMAP_DISABLED = 0x05F7    # debug_disable_minimap: UpdateMinimap ($90:A91B) does nothing while set
 
 RIDLEY_SPECIES_PALETTE = 0xA6E14F   # body: colours 1-8 skin, 9-11 membranes, 12-14 eyes
 RIDLEY_FADE_TABLE = 0xA6E30A        # 16 steps x colours 1-11 (CeresRidley_Func_5)
@@ -116,8 +117,11 @@
 
 def meta_ridley_init() -> bytes:
     """Species init ($A6, JSL'd, DB=$A6). Ceres Ridley's own init deletes him when the area boss
-    is dead, which is always true during the escape: jump past that check."""
+    is dead, which is always true during the escape: jump past that check. The rest of his init
+    turns the HUD minimap off (JSL $90:A7E2 at $A6:A122, as in every SM boss room); this is a
+    cutscene in a normal room, so turn it back on: the minimap redraws and marks the map next frame."""
     return (_long(0x22, RIDLEY_INIT_PAST_BOSS_CHECK) + bytes([0xC2, 0x30])     # JSL; REP #$30
+            + _abs(0x9C, MINIMAP_DISABLED)                                      # STZ $05F7
             + _lda(0x0000) + _long(0x8F, BABY_METROID_IP)                       # no baby Metroid
             + _lda(RIDLEY_XY[0]) + _abs(0x8D, ENEMY0["x"])
             + _lda(RIDLEY_XY[1]) + _abs(0x8D, ENEMY0["y"])
```

Testes (no mesmo teste da cena, sem teste novo):
```diff
--- tests/run_tests.py
+++ tests/run_tests.py
@@ -132,6 +132,13 @@
     return f"expectbit {EXPLORED_TILES + byte:06X} {mask:02X}"
 
 
+def forget_explored(room_key: str) -> str:
+    """Clear the explored byte that holds this room's first screen (and its neighbours in it)."""
+    r = {r.key: r for r in ROOMS}[room_key]
+    byte, _ = pausemap.bit(r.map_x, r.map_y + 1)
+    return f"poke {EXPLORED_TILES + byte:06X} 00"
+
+
 ROOM_STATE = "7E07BB"
 TIMER_Y = "7E094A"
 TIMER_HIDDEN, TIMER_IN_PLACE = "F000", "3000"   # hidden while Meta Ridley's tiles cover its digits
@@ -140,6 +147,7 @@
 GUNSHIP_WAITING = "A9BD"        # GunshipTop_8: waiting for Samus to board
 GAME_STATE_ENDING = "0027"      # ending cinematic and credits
 BOSS_AND_RIDLEY_GONE = "0003"   # area 3 boss bits: Parasite Queen dead (1) + Meta Ridley gone (2)
+MINIMAP_OFF = "7E05F7"           # 1 = HUD minimap off (SM boss rooms; Ceres Ridley's init sets it)
 
 
 def board_ship() -> list[str]:
@@ -270,13 +278,15 @@
         "fuga_ridley_nave_e_final": NEW_GAME + traverse(route("hangar", "reactor_core", False), room)
         + kill_parasite_queen()
         + traverse(walk_rooms(ESCAPE[:-1]), room)
-        + [f"expect {ROOM_PTR} {room['airlock']}", f"expect {ENEMY0_SPECIES} {ridley}", f"expect {TIMER_Y} {TIMER_HIDDEN}"]
+        + [f"expect {ROOM_PTR} {room['airlock']}", f"expect {ENEMY0_SPECIES} {ridley}", f"expect {TIMER_Y} {TIMER_HIDDEN}",
+           "wait 20", f"expect {MINIMAP_OFF} 0000", "shot build/tests/minimapa_air_lock.png"]
         # leaving before he flies off: the timer comes back (digits copied again), and he is
         # still there when Samus returns
         + traverse(walk_rooms(["airlock", "access_hall"]), room)
-        + [f"expect {TIMER_Y} {TIMER_IN_PLACE}", "shot build/tests/timer_fora_da_air_lock.png"]
+        + [f"expect {TIMER_Y} {TIMER_IN_PLACE}", "shot build/tests/timer_fora_da_air_lock.png",
+           forget_explored("airlock")]   # the minimap must mark the Air Lock again during the scene
         + traverse(walk_rooms(["access_hall", "airlock"]), room)
-        + [f"expect {ENEMY0_SPECIES} {ridley}", "wait 90", "shot build/tests/meta_ridley.png", "wait 600",
+        + [f"expect {ENEMY0_SPECIES} {ridley}", "wait 90", explored_bit("airlock"), f"expect {MINIMAP_OFF} 0000", "shot build/tests/meta_ridley.png", "wait 600",
            f"expect {BOSS_BITS_AREA3} {BOSS_AND_RIDLEY_GONE}", f"expectbit {ENEMY0_PROPS_HI} 02",
            f"expect {TIMER_Y} {TIMER_IN_PLACE}", "shot build/tests/timer_depois_do_ridley.png"]
         + traverse(walk_rooms(["airlock", "access_hall", "airlock"]), room)
```
`forget_explored` zera o byte inteiro `$7E0803` (Air Lock e vizinhas no mesmo byte); só afeta este
teste e nada depois dele confere esses bits.

Resultado do protótipo na cópia: `validate.py` 28 salas / 60 portas / 0 problemas; `build.py` →
`build/metroid_prime_snes.ips` sha1 `0f31447b6163c4a5764cac800c47e7a785ed50fa`; `run_tests.py`
13/13. Com a ROM antiga e os testes novos: `fuga_ridley_nave_e_final` falha nas 3 checagens novas
(`$05F7 = 0001` duas vezes, `$7E0803 = 02, bit 04 desligado`).

Medido depois da mudança (mesmos quadros da tabela acima):

| Momento | `$05F7` | HUD `$7EC67C` | `$7E0803` |
|---|---|---|---|
| f16808, Air Lock com o Ridley | `0000` | `1F 2C 25 E8 20 28 21 28 1F 2C` | `0E` |
| f17590, volta à Air Lock (byte zerado antes) | `0000` | `1F 2C 1F 2C 20 28 21 28 1F 2C` | `06` (Air Lock marcada de novo) |
| f18190, depois que o Ridley saiu | `0000` | `1F 2C 1F 2C 20 3C 21 28 1F 2C` | `06` |

Imagem: `specs/img/02-depois-air-lock.png` (minimapa desenhado com o Ridley na sala).

## Critérios de aceite

1. Com o Meta Ridley carregado na Air Lock, `$7E05F7 = 0000` 20 quadros depois de entrar
   (teste `fuga_ridley_nave_e_final`, linha `expect 7E05F7 0000` após `TIMER_HIDDEN`:
   protege=minimapa ligado durante a cena; falha_quando=o `STZ $05F7` some ou outra rotina do
   Ridley religa o desligamento; não_prova=que os tiles certos foram desenhados).
2. A Air Lock volta a ser marcada como explorada durante a cena: depois de zerar `$7E0803` na
   Access Hall e voltar, `expectbit 7E0803 04` passa e `$05F7` continua `0000` 90 quadros depois
   (mesmo teste: protege=marcação do mapa no estado do Ridley; falha_quando=minimapa desligado em
   qualquer momento dessa entrada; não_prova=as outras telas do mapa).
3. A foto `build/tests/minimapa_air_lock.png` mostra o minimapa preenchido no canto superior
   direito com o Ridley na tela (conferência visual; comparar com `specs/img/02-antes-air-lock.png`).
4. Os 13 testes existentes continuam passando, e `validate.py` continua com 0 problemas
   (protege=cena do Ridley, cronômetro, nave e final sem regressão).
5. Nenhum byte vanilla muda: diff da ROM antes/depois restrito a `$A0:F817` e ao bloco nosso em
   `$A6:FEBC-$A6:FFFF` (checagem manual na implementação, comparando as duas `.sfc`; protege=salas
   de chefe do SM, que dependem de `$90:A7E2` e de `$A6:A0F5` intactos).

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | nada novo (mudança só em código de inimigo) | +0 |
| run_tests.py (emulador) | `fuga_ridley_nave_e_final`: `$05F7 = 0` na 1ª entrada; bit da Air Lock remarcado e `$05F7 = 0` na 2ª | +3 checagens, 0 testes novos |
| imagem | `build/tests/minimapa_air_lock.png` | +1 |
| diff de ROM | só `$A0:F817` e `$A6:FEC2-$A6:FF90` mudam | manual, 1 vez |

## Riscos e reversão

- Risco baixo: é 1 instrução no nosso init, sem tocar em código vanilla. O minimapa passa a ser
  desenhado também sobre a área do HUD durante a cena; foi conferido na foto que os tiles do Ridley
  não cobrem o HUD (ele usa sprites, o HUD é BG3).
- Se algum dia o init reaproveitado mudar de ponto de entrada (outro valor em
  `RIDLEY_INIT_PAST_BOSS_CHECK`), o `STZ` continua certo enquanto vier depois do `JSL`.
- Reversão: tirar a linha `+ _abs(0x9C, MINIMAP_DISABLED)` (e a constante) de `ending.py`, tirar as
  3 checagens de `run_tests.py`, reconstruir.

## Fora de escopo

- `$179C` (boss_id) continua `1` na Air Lock com o estado do Ridley (vem do byte $10 do cabeçalho da
  espécie, copiado do Ridley de Ceres; `sm_a0.c:395`). Não afeta o minimapa (`1` não está na tabela
  `$90:A83A`); outros usos de `$179C` não foram investigados aqui.
- Os tiles do HUD apagados por `$90:A7E2` são redesenhados pelo próprio jogo no quadro seguinte; não
  há mudança no desenho do minimapa nem no mapa de pausa.
- Reactor Core (luta da Parasite Queen) e salas de chefe vanilla: não mudam. O `Phantoon_Init`
  (`$A7:CDF3`, `sm_a7.c:2112`) também chama `$90:A7E2`, então o minimapa fica apagado na luta e até a
  Samus sair do Reactor Core, como em toda sala de chefe do SM. Isso é luta de verdade e fica como
  está; se o usuário quiser o minimapa lá também, é outra spec.

## Desvios (preenchido na implementação)
