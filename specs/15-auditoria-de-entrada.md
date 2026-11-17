# 15 — Dano cedo na entrada de porta (auditoria de entrada de verdade)

Estado: **verificada** (30/10/2026, junto com a [14b](14b-arena-e-hive-mecha.md): validate "136 salas, 284 portas, 0
problemas", linha do Tallon e `check_world_rounds` iguais; `.ips` sha1 `694be017…d157` igual em dois builds; 80/80 testes)
Esforço estimado: 0,5 dia (medido: ~0,5 dia)
Tipo: problema (achado na [14a](14a-plated-beetle.md), "Desvios"; corrige a auditoria da [12h](12h-inimigos-chozo.md))

## Contexto

Na 14a apareceu: um Sidehopper **pequeno** da Ruined Shrine sobe no terraço e acerta a Samus parada na porta (~195 quadros
depois de entrar pela R0, ~60 pela L0, contados do fim da cadeia de teleportes do roteiro). A auditoria de entrada da 12h
(e o teste `chozo_inimigos_vivos`, "parada na porta 300 quadros não perde energia") não viu porque **entrava por transição de
RAM** (`enter_through`: o quarto de destino escolhido pela entrada de porta, mas a Samus com a posição que tinha, fora do
lugar) e olhava **180 quadros**. O orquestrador pediu: corrigir a Shrine com a menor mudança, auditar de novo com entradas de
verdade e tempo bastante (600 quadros parada), em todas as salas com inimigos do Tallon e da Chozo, e corrigir ou registrar o
que aparecer.

## Estado antes (verificado)

Depois da 14a: 77/77, sha1 `9dfaba59…3a37`. 92 entradas de porta em 39 salas com inimigos (Tallon 34 em 14 salas, Chozo 58
em 25).

**Auditoria forte** (`s14b/scripts/audit2.py`, numa cópia da ROM): para cada entrada, a Samus vai para a sala vizinha
(door_teleport, atalho), fica de pé 3 blocos dentro da porta, atira duas vezes nela (abre tampa de feixe: todos os feixes por
RAM; os bits das portas vermelhas por RAM) e **anda para dentro**: a colisão com o bloco da porta começa a transição (uma de
verdade). Porta de chão/teto, ou sem chão no lugar: door_teleport (a Samus posta na porta e a transição começada como a colisão
começa). Varia/Gravity só onde a sala é quente/inundada. Depois, **parada 600 quadros** contados da chegada (sala certa e
estado 8), energia a cada 5 quadros; o primeiro toque e o inimigo mais perto nele. Cada entrada de **dois jeitos** (andando e
por teleporte) e com **0, 9, 17 e 30 quadros de espera** antes (os pulos e espinhos são aleatórios: o mínimo dos 8). Numa
primeira volta, também **atirando** para dentro da sala desde a chegada.

Toques antes de 600 quadros (o menor dos 8; entradas sem toque não listadas):

| Sala, porta | 1º toque (quadros) | Quem |
|---|---|---|
| **Main Plaza R1** | **10** | Sidehopper em 87 (7 blocos da porta) |
| **Plaza Access R0** | **65** | Sidehopper em 22 sobe na borda da porta |
| **Ruined Nursery L0** | **60** (só andando) | a vespa (Mella) da plataforma |
| **Hive Totem L0** | **65** (só andando) | a vespa do oeste |
| **Root Cave R3** | **95** | Zeela (parasita) em 40 |
| **Great Tree Hall R0** | **90** | espinhos da Blood Flower em 38 |
| **Tunnel D L0 / R0** | **105 / 95** | espinhos dos Seedlings (Cacatac) a 130–150 px |
| **Tunnel E L0 / R0** | **95 / 100** | idem |
| **Elevator Beta R1 / L1** | **50 / 60** | o pirata atira (registrado no épico 10: atirando logo, ela o mata antes) |
| **Ruined Shrine R0 / L0** | **325 / 200** | Sidehoppers pequenos sobem no terraço (o caso da 14a) |
| Ruined Fountain Access L0 / R0, Shrine Access R0 / L0 | 255 / 155, 155 / 155 | rastejadores (HZOOMER) pelo chão |
| Ruins Entrance L0 / R0 | 285 / 300 | Sidehoppers |
| Tower of Light L3 | 470 | Viola |
| Canyon Cavern R0 / L0, Tallon Canyon R0, Tunnel B R0, Vent A R0, Biohazard R0 / L1, Gully R0 | 190 / 215, 505, 155, 155, 155 / 150, 315 | Sidehoppers, Zeelas, rastejador, Rinkas |

**Atirando** desde a chegada, nenhuma entrada levou toque, menos a Shrine Access R0 (o rastejador vem por baixo da linha do tiro
em pé; agachada ela o mata). Por que os inimigos chegam: o Sidehopper pula na direção da Samus (`Sidehopper_Func_7`,
`sm_a3.c`), a vespa desce nela a menos de `$70` px (`Flies_4`, `sm_a2.c`), os espinhos do Cacatac saem ao acaso
(`SpikeShootingPlant_4`, `sm_a2.c`). Um inimigo **fora da câmera não é processado** (`DetermineWhichEnemiesToProcess`
`$A0:8EB6`, `sm_a0.c:578`: só entra na lista se `x + raio >= câmera` e `x <= câmera + 256 + raio`): numa sala de 3 telas, o
que nasce na tela do meio fica parado enquanto a Samus está na porta de qualquer ponta.

## Causa (problemas)

1. A auditoria da 12h media outra coisa (transição por RAM, a Samus fora do lugar, 180 quadros); a promessa "parada na porta
   2 s não perde energia" (12h, `chozo_inimigos_vivos`) não valia em 9 salas.
2. Na Shrine, os pequenos em 14 e 31 ficam na tela de uma das portas e vêm ao terraço.

## Mudança

Regra (a da 12h, agora medida de verdade): **parada depois de uma entrada de verdade, nenhum toque nos primeiros 120 quadros
(2 s)**; a Ruined Shrine (o caso pedido) **600 quadros**. Toques depois disso ficam registrados (a tabela acima): inimigos que
perseguem acabam chegando numa Samus parada, e atirando ela os evita.

1. **Colocações** (só posições; contas, espécies e regras da 07i/12h iguais):

| Sala | Antes → depois | Por quê |
|---|---|---|
| Ruined Shrine | pequenos 14, 20, 31 → **18, 20, 29** | os três na tela do meio: fora da câmera das duas portas, ficam parados até a Samus descer à tigela (o besouro já ficava, 14a) |
| Main Plaza | Sidehopper 87 → **72** | fora da tela da porta R1 |
| Plaza Access | 22 → **19** (e 18) | mais longe da borda da R0 (sala de 2 telas: os dois pulam; 12h já os tirara de perto da porta de chão) |
| Hive Totem | vespa 10 → **11** | 15 px mais longe da L0 |
| Root Cave | Zeela 40 → **37** | |
| Great Tree Hall | Blood Flower 38 → **24** | a oeste do Seedling, fora da tela da R0 |
| Tunnel D | Seedlings 11, 20 → **16, 17** | os espinhos são ao acaso: o mais longe das duas portas |
| Tunnel E | 11, 36 → **18, 29** (23 fica) | fora da tela das portas |

2. **Teste novo** (`tests/run_tests.py`, `entry_audit` / `check_entries`): `entradas_de_porta_tallon` e
   `entradas_de_porta_chozo`: todas as entradas (andando onde dá, senão door_teleport), uma vez, de um estado salvo na área;
   a energia reposta durante a transição; falha se perder energia antes de `ENTRY_GRACE = 120` quadros da chegada (`ENTRY_LONG
   = 600` na Shrine) ou se não chegar à sala. `ENTRY_EXCEPTIONS` (registradas, não checadas): Elevator Beta R1 e L1 (o pirata,
   épico 10) e **Ruined Nursery L0** (abaixo; tirada na 14c).

## Critérios de aceite

1. `entradas_de_porta_tallon` e `entradas_de_porta_chozo` passam (protege = as colocações; falha_quando = E3, E4; não_prova =
   outros tempos de entrada: a auditoria do scratchpad, 8 por entrada, mostra o mínimo).
2. A auditoria forte (8 jeitos por entrada) não acha toque antes de 120 quadros fora das 3 exceções, nem na Shrine antes de 600.
3. validate igual (as regras da 07i/12h aceitam as posições novas); a cadeia e as rotas passam; 14a passa (luta procurada de
   novo, ver 14b).

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| run_tests.py | `entradas_de_porta_tallon`, `entradas_de_porta_chozo` | +2 |
| scratchpad (`s14b/`) | `audit2.py` (antes/depois: `a2_*_cur.out`, `a2_*_fin.out`), mutações do emulador E3/E4 | — |

## Riscos e reversão

- Espinhos e pulos são aleatórios: a Tunnel D R0 fica em **120** no pior dos 8 jeitos medidos (no limite). Um teste com outro
  caminho até a sala pode ver outro número.
- Mexer numa sala com inimigos pode mudar caminhadas medidas da cadeia (foi o caso da Nursery: abaixo).
- Reversão: as posições antigas nas tabelas (`tools/*/enemies.py`).

## Fora de escopo

- Toques depois de 2 s numa Samus parada (a tabela): comportamento normal de inimigo que persegue; atirando ela os evita.
- O pirata do Elevator Beta (decisão do épico 10).

## Desvios (preenchido na implementação)

- **Ruined Nursery L0 não corrigida**: a vespa em 11 resolvia (nenhum toque em 8 jeitos), mas a caminhada da cadeia completa
  pela Nursery terminava em outro lugar e a cadeia caía no buraco da galeria duas salas depois; voltou para 10 e ficou
  registrada (`ENTRY_EXCEPTIONS`: andando ela leva a vespa ~60 quadros depois de entrar; parada na porta por teleporte, não;
  atirando, nunca). Decisão a confirmar.
- **31/10/2026 (na [14c](14c-flaahgra.md), pedido do orquestrador): corrigida.** A vespa foi para **(11, 9)** e a exceção saiu
  de `ENTRY_EXCEPTIONS` (fica só o pirata do Elevator Beta). A causa da queda da cadeia era a caminhada cega do North Atrium:
  com a Samus chegando mais tarde da Nursery, um rastejador a derrubava no pulo para a plataforma e a subida para a galeria
  pousava 30 px a leste, no buraco (medido com `s14c/scripts/probe.py`). A cadeia ganhou `CHAIN_ATRIUM_TO_DOOR` (da parede
  oeste, x `$15`, pela ponta oeste da plataforma, até x `$7A` virada para oeste: a subida sai de um ponto fixo) e, na rodada 1,
  um tiro e um passo a mais quando a caminhada termina contra a tampa fechada da L0 da Totem Access; trechos medidos andando,
  sem RAM. `entradas_de_porta_chozo` passa com a entrada da Nursery L0 conferida.
- O teste fica com **uma** entrada por porta (andando quando dá); os 8 jeitos e os 600 quadros ficam na auditoria do
  scratchpad (custo: ~4 min de CPU).
- Os testes que andavam pela Shrine mudaram (os pequenos não vêm mais à Samus no `SHRINE_FIGHT`; a luta do besouro foi
  procurada de novo): ver a tabela de mudanças da [14b](14b-arena-e-hive-mecha.md).

## Resultado

- Auditoria forte depois (`s14b/a2_chozo_fin.out`, `a2_tallon_fin.out`): **nenhum toque antes de 120 quadros** fora do
  Elevator Beta (50/60, o pirata) e da Nursery L0 (60, andando); a Shrine **sem toque em 600 quadros** pelas duas portas nos 8
  jeitos; Tunnel D R0 = 120 no pior caso; os outros toques entre 150 e 505 quadros (a tabela de "registrados": rastejadores,
  Sidehoppers, Zeelas, Rinkas, a Viola da torre).
- Testes: `entradas_de_porta_chozo` 78 s, `entradas_de_porta_tallon` 45 s sozinhos (em paralelo com os outros: a bateria
  inteira foi de ~6 min para 5 min 47 s, a cadeia continua a mais longa).

## Mutações

Emulador (`s14b/scripts/emu_mut_14b.py` → `s14b/emu_mut_14b.out`): E3 os pequenos da Shrine de volta a 14 e 31 →
`entradas_de_porta_chozo` falha ("ruined_shrine porta 0 (R0): perdeu energia 210 quadros depois de chegar", L0 70); E4 o
Sidehopper da Main Plaza de volta a 87 → falha ("main_plaza porta 1 (R1): … 10 quadros"); sem mutação passa.
