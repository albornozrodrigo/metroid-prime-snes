# 19k — Omega Pirate (arena da Elite Quarters)

Estado: **verificada** (09/11/2026: validate "253 salas, 524 portas, 0 problemas", as linhas do Tallon e das rodadas iguais às da 19j;
`.ips` sha1 `931e7f1043cfe9fc90ab37f6f3c931b9a7256ddb` igual em dois builds; grupo A **34/34** (2 min 58 s), B **64/64** (3 min 9 s), C
**21/21** (1 min 53 s), D **16/16** (3 min 44 s)). Rascunho → aprovada (épico aprovado pelo usuário; "pode seguir") → implementada →
verificada na mesma sessão.
Esforço estimado: 2–3 dias (linha 19k do épico; medido: ~meio dia, a luta achada por busca gulosa no emulador)
Épico: [19 — Phazon Mines](19-phazon-mines.md) (decisão do usuário 4: o Omega Pirate = cópia do Bomb Torizo em cores de phazon, imune ao
feixe sem carga, as portas trancam até ele morrer, sem prêmio, os tetos de justiça do épico 14; linha 19k da tabela de filhas); modelos:
[18k](18k-thardus.md) (o Bomb Torizo corrigido no lugar, a arena do bit do Torizo, as portas cinza de tipo 2), [19h](19h-phazon-elite.md)
(a primeira arena da Mines, as cores de phazon), [19j](19j-regiao-c-mines.md) (a Elite Quarters vazia).

## Contexto

A Elite Quarters (P26, 5×2, base pirata) está construída desde a 19j: o chão da arena na linha 26 de parede a parede (porta L1 da
Elite Quarters Access embaixo a oeste), a prateleira da porta R0 (da Processing Center Access) na linha 10 a leste, três bordas em
zigue-zague (21, 16, 11) e canos no teto; sem inimigo (`ARENA_ROOMS`). No Prime o Omega Pirate é o `OmegaPirate` (tipo `$86`) da camada 5
"Omega Pirate Battle", com 8 `SpacePirate` e os nódulos de cura; as duas portas têm `Actor Door Lock` (`mines/rooms.py BOSS_DOORS`,
esperando esta filha); o prêmio é o Phazon Suit, que não existe no SM.

## Estado antes (verificado)

- validate "253 salas, 524 portas, 0 problemas"; `.ips` sha1 `4c29592959c687dc62b150f1b0c8793419b06da5`; A 34/34, B 64/64, C 21/21,
  D 15/15 (19j).
- **Bomb Torizo** `$A0:EEFF` (ROM base): vida 800, toque 8, tiles `$2000` (a VRAM inteira de inimigos da sala), IA em `$AA`;
  vulnerabilidades `$B4:F0C0`: os 12 feixes sem carga `02`/`82` (1×), míssil 1×, super 2×, bomba 0, power bomb 0, tiro carregado 1×.
- A 18k já corrigiu o código do Torizo **no lugar** (as 7 leituras da área = 0, sem a bruma, a posição fixa `TORIZO_SPOT` = a do
  Thardus (776, 368), as paletas do corpo e o pulso do peito nas cores do Thardus). A posição é uma só nas tabelas do init.
- As rotinas de paleta do Torizo (`Torizo_C250`, `Torizo_C268`, `Torizo_C2B0`) copiam 16 cores de duas tabelas com `LDA abs,X`
  (`BD lo hi`): a estátua (`$86E7`/`$86C7`) e o corpo acordado (`$8727`/`$8707`), 6 cargas. `$AA:F7D3–FFFF` (2093 bytes) é só `$FF` na
  ROM base e na construída.
- Prime (research/prime_fs, `s19k/eq_types.py`): a Elite Quarters tem 6 camadas; a 5 "Omega Pirate Battle" tem 1 `OmegaPirate` (`$86`),
  8 `SpacePirate` (`$24`); a 4 "Easy Omega Killer" tem um `DamageableTrigger`.

## Mudança

1. **A cópia** `OMEGA` (`tools/chozo/bosses.py`): o Bomb Torizo em `$A0:F9FF` (a próxima casa da grade depois do Phazon Elite), vida
   **1200**, toque 8 (o do Torizo), tabela de vulnerabilidade própria (`OMEGA_VULN`, no `$B4` livre): os 12 feixes sem carga `$80`
   (nada, nunca congela), míssil 1× (100: **12 mísseis**), super 2×, power bomb 1×, tiro carregado 1× (o do Power Beam carregado, 60:
   **20 tiros**, o máximo de chefe). A regra 13 do épico 14 (`arena_gear_fight`): na rodada 6 a Samus tem 235 mísseis de capacidade.
2. **As cores**: as 6 cargas de paleta viram `JSR` (os mesmos 3 bytes) para um seletor por tabela no `$AA` livre (`omega_selector`):
   `LDA $079F / CMP #5 / BEQ / LDA tabela,X / RTS / LDA tabela_omega,X / RTS`. Na área 5 (a Mines, `OMEGA_AREA`) lê a cópia da tabela
   nas cores do Omega; nas outras, a tabela no lugar (as do Thardus). As cores do Omega usam as rampas do Phazon Elite (19h, das texturas
   do Elite Pirate: a mesma armadura e o mesmo phazon): corpo 1–8 a armadura cinza, orbe do peito 9–11 o brilho de phazon, olhos e
   realces 12–14 o azul de phazon. O pulso do peito (`TORIZO_PALFX`, um objeto de efeito de paleta no `$8D`) fica o do Thardus nas duas
   áreas. `build.py` aplica `omega_patches` antes de `torizo_patches` (as tabelas vanilla lidas antes de recoloridas no lugar).
3. **A espécie e o lugar**: `omega_pirate` (`tools/frigate/enemies.py`: `$A0:F9FF`, raio 48, os valores do Thardus, set de paleta 1,
   `fixed=(776, 368)`, a posição do Torizo, a mesma do Thardus); `tools/mines/enemies.py`: `Spawn(OP, 48, 26)` na Elite Quarters,
   `ARENA_KINDS` com `OmegaPirate`, `PRIME_BOSS_LAYERS` com 1 `OmegaPirate`. O chão da linha 26 está livre na coluna 48 (as bordas do
   zigue-zague começam na 59).
4. **A arena** (`ARENAS`): `mines_elite_quarters`, bit `$10` (o reservado pelo épico), condição `BOSS_BIT` com o bit `$04` do Torizo
   (a morte dele liga, `Torizo_Instr_38`), `needs = {Missile}`, sem prêmio, música do Torizo (`$24`, faixa 3). As duas portas
   (`BOSS_DOORS`, já mapeadas para a 19k) ganham a tampa cinza de tipo 2 no estado vivo e as de plasma no morto (`build.arena_door_alive_cap`).
5. **O validador**: `MINES_BOSS_CHILDREN_DONE` com a 19k; em `check_arenas_in_rom`: uma só posição fixa para todas as cópias do Torizo;
   `OMEGA_AREA` = a área da Mines; cada carga um `JSR` a um seletor no `$AA` livre igual a `omega_selector`, a tabela do Omega igual a
   `omega_colours` da vanilla e diferente da vanilla e da do Thardus (menos os tons quase pretos, iguais nas duas rampas);
   `TORIZO_NO_PRIZE` dá o item que falta na linha do épico (o Phazon Suit).
6. **Os testes**: `mines_omega_pirate` (grupo D: a luta de verdade na rodada 6) e o atalho `MINES_OMEGA_WON_BY_RAM` (`poke 7ED82D 10`)
   na `mines_regiao_c_rota`, que atravessa a Elite Quarters.

## Resultado

- validate "253 salas, 524 portas, 0 problemas"; linha "arenas": "mines_elite_quarters (Prime: OmegaPirate (Omega Pirate)): 1
  omega_pirate + 0 outros, bit de chefe $04, bit $10, imune ao Power Beam; 12 mísseis (capacidade na rodada 6: 235) ou 20 tiros
  carregados (com o Charge Beam na chegada; máximo de chefe 20) (rodada 6), até 10 por golpe, nenhum prêmio"; "chefes da Mines": o Omega
  Pirate (rodada 6, bit `$10`) com as duas portas trancando até a vitória, "esperando: nenhum". Rodadas: 85 itens, 85% (iguais).
- ROM: a cópia em `$A0:F9FF` (vida `$04B0`, a tabela `80×12 02 04 00 02 00 00 00 02 00 00` no `$B4`); as tabelas do Omega e os 4
  seletores em `$AA:F7D3–F892`; as 6 cargas de paleta = `JSR`. `.ips` sha1 `931e7f10…6ddb`, igual em dois builds.
- Emulador (`mines_omega_pirate`): ao entrar pela L1 o Omega está na posição (776, 368) com 1200 de vida, as tampas cinza `C848` (L1,
  slot 38) e `C842` (R0, slot 39), a música `$24`. O feixe sem carga (Plasma + Ice + Wave) não tira nada; a luta (busca gulosa, 79
  movimentos): a Samus anda até ele e atira mísseis; ele pula para o leste e volta; 11 mísseis gastos (um apanhado de volta), vida 0, a
  morte em 400 quadros, os bits `$04` e `$10` da área 5, a música parada, energia 95, 19 mísseis. A L1 abre com um tiro; o estado morto
  pelas duas portas: sem inimigo, a música da Mines, as tampas de plasma (L1 no slot 38, R0 no 39).
- Fotos: [luta](img/19k-luta.png) (o Omega em cinza e azul de phazon), [morrendo](img/19k-morrendo.png), [morto](img/19k-morto.png).
- Grupos: A 34/34, B 64/64, C 21/21 (o `phendrana_thardus` passa: o Thardus com as cores dele), D 16/16 (o `mines_omega_pirate` novo e
  a `mines_regiao_c_rota` com o atalho `MINES_OMEGA_WON_BY_RAM`). Um D rodado antes de A–C mostrou "19/19": a ROM nova refez as 3
  partes da cadeia que o D carrega; na ordem A, B, C, D a conta é 16.

## Critérios de aceite

- validate "0 problemas", com a linha "arenas" mostrando a Elite Quarters (12 mísseis ou 20 tiros carregados, rodada 6) e "chefes da
  Mines" com o Omega Pirate (as duas portas trancam até a vitória; esperando: nenhum).
- Dois builds com o mesmo sha1. As linhas do Tallon e das rodadas iguais às da 19j (85 itens, 85%).
- `mines_omega_pirate` passa: a arena viva (vida 1200 na posição (776, 368), as duas tampas cinza, a música do Torizo), a luta só com
  mísseis, a morte (bits `$04` e `$10` da área 5, a música parada), a L1 aberta, o estado morto (portas de plasma) pelas duas portas.
- Os grupos A, B, C e D passam (o Thardus da 18k sem mudança: `phendrana_thardus` no grupo C).

## Plano de testes

`python3 -I tools/build.py` duas vezes (sha1), `python3 -I tools/validate.py`, `python3 -I tests/run_tests.py --grupo D`, depois A, B e
C (um por vez, timeout 10 min). Fotos: `build/tests/19k_*.png`, copiadas para `specs/img/19k-*.png`.

## Mutações

Na cópia `scratchpad/s19k/mut` (sem `.claude/`), `s19k/mutate.py` (→ `mutate_vr.out`, `mutate_vr2.out`, `mutate_e.out`): cada uma muda
um arquivo (ou a ROM), constrói, valida (ou roda o teste) e volta. **Todas pegas**; os controles V0, R0 e E0 limpos.
- Validador: V1 vida 30000 ("não se vence com o equipamento da rodada 6": 300 mísseis); V2 míssil e carga sem dano ("nenhum");
  V3 a arena fora de `ARENAS` (o build recusa: 7 arenas construídas, a tabela tem 8); V4 dois Omegas (Prime 1; o Torizo não é o único
  inimigo); V5 a posição (792, 368) (a coluna da tabela e "posições fixas diferentes"); V6 `OMEGA_AREA` 4; V7 a 19k fora de
  `MINES_BOSS_CHILDREN_DONE`; V8 a porta da Processing Center Access fora de `BOSS_DOORS`; V9 o Torizo vanilla `$EEFF`; V10 sem
  `PRIME_BOSS_LAYERS`; V11 a espécie do Thardus na arena.
- ROM: R1 uma carga de volta a `LDA $86E7,X`; R2 um seletor comparando com a área 4; R3 uma cor do Omega igual à vanilla.
- Emulador: E1 vida 1300 → falha (300 de vida no fim); E2 míssil 0,5× → falha (600 no fim).

## Riscos e reversão

- O seletor lê a área a cada carga de paleta: em qualquer área que não a 5, o Torizo usa as tabelas do Thardus (como antes). Se uma sala
  vanilla com Torizo voltasse a carregar, ela também passaria pelo seletor (o validador já recusa o Torizo vanilla e o Golden).
- Reverter: tirar `OMEGA` de `COPIES`, a arena de `ARENAS`, o spawn, `omega_pirate`, a chamada a `omega_patches` e o `bank_aa`; a 19k
  de `MINES_BOSS_CHILDREN_DONE`.

## Fora de escopo

Os 8 piratas e os nódulos de cura da luta (camada 5: fora, decisão 5 do épico); o elevador de saída da Elite Quarters (enfeite); o
Phazon Suit; as fases da luta do Prime (invisível, phazon no chão).

## Desvios (preenchido na implementação)

- O pulso do peito do Torizo é um objeto de efeito de paleta (`$8D:F759`) com uma lista só: fica nas cores do Thardus também na Mines
  (cinza-branco claro). Separar por área seria trocar o `LDY` do `Torizo_Instr_9` por outro seletor; não fiz (o peito pisca só depois do
  despertar e o cinza combina com a armadura).
- As cores usam as rampas do Phazon Elite em vez de rampas tiradas das texturas do Omega (as mesmas famílias: armadura de pirata e
  phazon azul). Não despejei as texturas do `OmegaPirate`.
- A luta foi achada por busca gulosa (não em feixe): 11 mísseis, a Samus perde 4 de energia (dois toques de 8 com a Varia e a Gravity).

## Decisões para o usuário (escolhidas as mais perto do épico e dos padrões; confirmar)

1. **O tiro carregado fere o Omega** (1×, como o épico deixou: só o sem carga é imune). Com o Plasma, o Ice e o Wave juntos o tiro
   carregado tira 900: **dois tiros vencem a luta**. Alternativa: imune também ao tiro carregado (só mísseis e power bombs, mais perto do
   Prime: 12 mísseis).
2. **Vida 1200** (12 mísseis). Alternativa: mais vida (a capacidade da rodada 6 é 235 mísseis).
3. As cores (as do Phazon Elite) e o pulso do peito cinza.
