# 14f — Rodadas e cadeia com os chefes (fecha o épico 14)

Estado: **verificada** (31/10/2026: validate "136 salas, 284 portas, 0 problemas", linha do Tallon e `check_world_rounds`
iguais; `.ips` sha1 `31218abaaf3b1cb047f1ee6684ecd82fe45aa6c5` igual em dois builds; **82/82** testes; bateria de testes
5 min 55 s)
Esforço estimado: 1 dia (medido: ~0,3 dia, junto com a [14d](14d-incinerator-drone.md))
Épico: [14 — Chefes](14-chefes.md) (linha 14f; decisão 9 / padrões aceitos 9 e 11; critérios "14f — Rodadas e cadeia").

## Contexto

O épico deixou para a última filha: as lutas na cadeia completa, o tempo total medido, uma linha "chefes (specs/14)" no
validador que resume os 4 chefes, as rodadas iguais e o épico `verificada`. Pedido do orquestrador: conferir que toda trava de
chefe está no passeio das rodadas, que os bits de chefe são distintos e não colidem com os vanilla da área 1, que a docstring da
cadeia lista toda vitória por RAM, e refazer as fotos `specs/img/14a-*.png` (eram da luta de antes da 14b mover os Sidehoppers).

## Estado antes (verificado)

Depois da 14d: as 4 arenas na ROM (`bosses.ARENAS`: Hive Totem `$08`, Ruined Shrine `$20`, Sunchamber `$40`, Burn Dome `$10`);
a cadeia vence o Hive Mecha, o Flaahgra e (desde a 14d) o Incinerator Drone por RAM, anotados em `FullChain.note`; a docstring de
`full_chain` citava só o Hive Mecha. As fotos `img/14a-luta*.png` / `14a-morto.png` eram da 14a (antes da spec 15 e da 14b).

## Mudança

1. **Validador** (`tools/validate.py`): `check_epic_bosses` (chamada por `check_bosses`), linha nova **"chefes (specs/14)"**:
   - `EPIC_BOSSES`: os 4 chefes do épico por sala e o que cada um trava no Prime (inventário do épico: prêmio que aparece, porta
     trancada, item que começa a luta); as `ARENAS` são exatamente esses 4 e cada uma trava o que o épico diz;
   - bits de chefe da área 1 das arenas distintos e **fora dos vanilla da área**, lidos da ROM base (`vanilla_boss_bits`: as
     condições `E629` das salas vanilla da área 1 e as tampas cinza de tipo 0–2: dá `$01`, `$02`); uma condição `BOSS_BIT` só
     espera um bit vanilla (o `$02` que o próprio Spore Spawn liga);
   - toda trava modelada no passeio: o prêmio e o item que começa a luta em `boss_locks`; a porta de chefe uma porta construída
     com a trava `boss`;
   - a linha lista, na ordem das rodadas, cada chefe com sala, rodada, bit e trava; diz que a Parasite Queen é a da etapa 6 e
     que os Chozo Ghosts (14e) ficam fora.
2. **Cadeia** (`tests/run_tests.py`): a docstring de `full_chain` lista os três chefes vencidos por RAM (Hive Mecha rodada 0,
   Incinerator Drone rodada 1, Flaahgra rodada 2, cada um com o seu teste de luta de verdade) e o Plated Beetle deixado vivo
   (padrão aceito 11). O atalho do Incinerator Drone entrou na 14d.
3. **Fotos**: `img/14a-luta.png`, `img/14a-luta-2.png`, `img/14a-morto.png` copiadas da bateria desta ROM (`build/tests/14a_*`).

## Critérios de aceite

1. validate 0 problemas; Tallon "44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas" e "rodadas (specs/12m): …
   51 itens em 7 rodadas … 51%" iguais; linha nova "chefes (specs/14)". (falha_quando = V14–V16 abaixo)
2. A cadeia passa com os três atalhos anotados e a docstring os lista; todo chefe tem o seu teste de luta de verdade.
3. Bateria inteira < ~7,5 min (medido e anotado); 2 builds iguais; fotos olhadas.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_epic_bosses` (linha "chefes (specs/14)") | +1 linha |
| run_tests.py | docstring da cadeia | 0 |
| scratchpad | mutações V14–V16 em `s14d/scripts/mutate_14d.py` | 3 |
| imagem | `img/14a-*.png` refeitas | 3 |

## Riscos e reversão

- `EPIC_BOSSES` repete o inventário do épico (o que cada chefe trava): mudar uma arena de propósito pede mudar a tabela.
- Reversão: tirar `check_epic_bosses`.

## Fora de escopo

- Chozo Ghosts (14e, fora por decisão do usuário), Meta Ridley e os fantasmas do Life Grove (guardam artefatos).

## Desvios (preenchido na implementação)

- Nenhum teste novo: as lutas de verdade são os testes de cada filha (`chozo_plated_beetle`, `chozo_hive_mecha`,
  `chozo_flaahgra`, `chozo_incinerator_drone`); a cadeia só ganhou o atalho da 14d.

## Resultado

- validate: "136 salas, 284 portas, 0 problemas"; Tallon e `check_world_rounds` **iguais**; nova: "chefes (specs/14): 4 da
  Chozo, cada um uma arena (a Parasite Queen da fragata é a etapa 6; os Chozo Ghosts, 14e, fora): Hive Mecha (chozo_hive_totem,
  rodada 0, bit $08): Missile Expansion só depois da luta (rodada 0); Incinerator Drone (chozo_burn_dome, rodada 1, bit $10):
  Missile Expansion começa a luta (rodada 1), a porta para chozo_burn_dome_access tranca até a vitória; Plated Beetle
  (chozo_ruined_shrine, rodada 1, bit $20): nenhuma trava; Flaahgra (chozo_sunchamber, rodada 2, bit $40): Varia Suit só depois
  da luta (rodada 2), a porta para chozo_sun_tower_access só depois da luta; bits da área 1 distintos, nenhum dos vanilla dela
  ($01, $02, lidos da ROM base; o $02 do Spore Spawn só como condição)".
- **Tempo**: bateria inteira **5 min 55 s** (82 testes em paralelo; 5 min 48 s na cópia de rascunho); a cadeia continua a mais
  longa; o teste novo da 14d ~40 s. Verificação inteira (2 builds, validate, testes) **6 min 2 s** (medida com `time`): abaixo dos ~7,5 min.
- **Fotos** (olhadas): `img/14a-luta.png` (o besouro cinza-verde ao lado da Samus, um pequeno no terraço leste),
  `img/14a-luta-2.png` (a Samus pulando sobre o besouro, dois pequenos e o míssil do chão), `img/14a-morto.png` (a explosão da
  morte; os pequenos já mortos).
- **Mutações** (`s14d/scripts/mutate_14d.py`): V14 o bit do Burn Dome `$02` (vanilla da área 1) → erro; V15 o Hive Mecha fora
  das `ARENAS` → erro; V16 a Varia sem ser prêmio (o Flaahgra deixaria de travá-la) → erro "Flaahgra … trava (prêmio, porta,
  item que começa) = (False, True, False), o épico diz (True, True, False)" (esta só a linha nova pega).
