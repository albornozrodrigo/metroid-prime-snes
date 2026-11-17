# 20a — Levantamento da Impact Crater (só leitura)

Estado: **verificada** (10/11/2026). Só leitura: nenhuma sala, nenhum código de sala, a ROM igual (sha1 `f5b0f58b3cd6ef58d573403852b091a7446b0dac`
antes e depois, `python3 -I tools/build.py`).
Esforço: 0,5 dia.

## Como foi medido

- Grafo e caixas: `research/prime_worlds.json` (MLVL "Impact Crater", `0xc13b09d1`, `Metroid7.pak`).
- Objetos por sala: `tools/dump_prime_area_objects.py` e `tools/dump_prime_locks.py` (venv `tools/venv`, retro-data-structures 0.44.1)
  rodados para "Impact Crater"; mais um roteiro de leitura crua (nomes e campos lidos dos bytes, como em 17c/19c, porque o
  retro-data-structures não lê o nome destes objetos): item do `Pickup` = a palavra 60 bytes depois do nome; função do
  `SpecialFunction` = a palavra 24 bytes depois do nome; vulnerabilidade do `DamageableTrigger` = 4 palavras 40 bytes depois do nome
  (power, ice, wave, plasma; 1 fere, 2 imune, 0 dobro). Roteiros e saídas no scratchpad da sessão (`s20a/raw.py`, `raw.out`,
  `objs.json`, `locks.json`), que somem ao reiniciar; os números ficam aqui.
- Tamanho SM: a regra do Tallon (`tools/tallon/rooms.py:57` `screens`: 30 m por tela, o maior de x/y na largura e z na altura, no
  máximo 6×4), a mesma das áreas 12–19.
- Espaço: as linhas do validador ("$8F recuperado", "$A1 recuperado", "bancos") e a maior faixa de `$FF` de cada banco na ROM construída.
- "*(incerto)*" = o que os dados não mostram e eu sei só do jogo, ou não consegui ler.

## Salas e tamanho

**12 salas, 11 ligações (22 docas), 90 telas** (Tallon 251, Chozo 202, Magmoor 156, Phendrana 302, Mines 205).

| # | Sala do Prime | Caixa (m) | Telas SM | Ligações | Portas (cor pelo `Trigger_DoorKey`) |
|---|---|---|---|---|---|
| 0 | Crater Entry Point | 63×64×55 | 2×2 | 1 | plasma |
| 1 | Crater Tunnel A | 35×71×21 | 2×1 | 2, 0 | plasma, plasma |
| 2 | Phazon Core | 142×150×102 | 5×3 | 3, 1, 4 | plasma ×3 |
| 3 | Crater Missile Station | 34×36×23 | 1×1 | 2 | plasma |
| 4 | Crater Tunnel B | 36×71×25 | 2×1 | 5, 2 | plasma, plasma |
| 5 | Phazon Infusion Chamber | 73×100×72 | 3×2 | 6, 4 | (para a 6: sem porta), plasma |
| 6 | Subchamber One | 120×60×76 | 4×3 | 5, 7 | sem porta |
| 7 | Subchamber Two | 56×134×51 | 4×2 | 6, 8 | sem porta |
| 8 | Subchamber Three | 55×126×53 | 4×2 | 9, 7 | sem porta |
| 9 | Subchamber Four | 118×53×47 | 4×2 | 10, 8 | sem porta |
| 10 | Subchamber Five | 50×57×142 | 2×4 | 9, 11 | sem porta |
| 11 | Metroid Prime Lair | 121×125×144 | 4×4 | 10 | sem porta |

- **Travas:** as 5 ligações de cima (Entry–A, A–Core, Core–Missile Station, Core–B, B–Infusion) têm porta de **plasma** dos dois
  lados (vulnerabilidade 2 2 2 1). Da Infusion para baixo não há porta: é uma descida (as Subchambers são o caminho da queda até a
  Lair). Nenhuma parede de míssil, bomba ou Power Bomb (`pb_only` vazio em todas).
- **Crater Tunnel B:** trilho de Spider Ball (77 pontos de trilho, 2 `SpecialFunction - spiderball`). O jogo não tem Spider Ball
  (decisão do épico 18): a sala precisa de outra forma de passar *(a decidir na filha da sala, como os trilhos de Spider da Mines)*.
- **Forma:** as Subchambers no Prime são uma descida vertical; pela regra elas saem largas (4×2, 4×3). A forma no SM fica para a filha.

## Itens

**Nenhum item de verdade.** Os 35 `Pickup` da área são todos recargas soltas por inimigo (`Pickup Generator`), lidas dos bytes:
"Small Health" (item 26, 10), "Large Health" (26, 20), "100 Health" (26, 100), "Small Missle" (4, 5) e "Powerbomb" (7, 1), 5 por sala
em Tunnel A, Phazon Core, Subchambers 2–4 e 10 na Lair. Nenhuma expansão, E-tank ou arma.

- Consequência: a Impact Crater **não muda a conta de itens** (88 itens, 88% na tela do fim, 19m). A decisão 6 do épico ("itens na
  regra das outras áreas") não tem item a colocar.
- **Estações:** Save Station na Crater Entry Point (`SpecialFunction Save Station`, função 7); recarga de mísseis na Crater Missile
  Station (`SpecialFunction Missile Station`, função 23; a mesma da Mines, 19l).

## Inimigos (todos na camada 0, salvo onde diz)

| Sala | Inimigos do Prime | Proposta (espécies que já existem) |
|---|---|---|
| 1 Tunnel A | 1 enxame de Lumigek (`WallCrawlerSwarm`), `VisorGoo` | fora (enxame de parede, sem par no SM) *(proposta)* |
| 2 Phazon Core | 4 Fission Metroid (`MetroidAlpha` "Beta Metroid"), 3 `FishCloud` | 2 Metroids (a cópia da 18l), peixes fora (enfeite) |
| 3 Missile Station | 4 `FishCloud` | nenhum |
| 4 Tunnel B | camada 1: 1 enxame de Lumigek, 1 `Burrower` | 1 Burrower como na 19l |
| 6–10 Subchambers | `MetroidPrimeStage1` (um em 6, 7, 8, 9), `EnergyBall` ×4 em 7, 8, 9 (Ice, Plasma, Power, Wave) | parte da luta (ver abaixo) |
| 11 Lair | `MetroidPrimeStage2`, 1 `MetroidBeta`, 2 `MetroidAlpha`, `Phazon Pool` | parte da luta (ver abaixo) |

Comuns: **7 no Prime** (4 Fission Metroids, 2 enxames, 1 Burrower) fora os peixes; proposta: **3** (2 Metroids e 1 Burrower), a regra
da 19l (no máximo 1 por tela, longe das portas).

## A luta final (Metroid Prime)

- **Fase 1 (exoesqueleto):** `MetroidPrimeStage1` em cada uma das Subchambers One a Four (um objeto por sala) e um
  `DamageableTrigger` com vulnerabilidade 0 4 4 4 em cada; as `EnergyBall` de quatro cores nas 2, 3 e 4. No Prime a luta desce sala
  por sala, e o ponto fraco muda de feixe *(conhecimento; o ponto fraco por cor não foi lido)*.
- **Fase 2 (essência):** `Metroid Prime - Stage 2` na Lair, com `Phazon Pool`, Metroids que nascem na luta e 9 `DamageableTrigger`
  imunes a todos os feixes (2 2 2 2). No Prime o golpe final é o feixe de phazon *(conhecimento)*; o jogo não tem Phazon Suit (19k,
  sem prêmio).
- **Vida, ataques e tempos:** **não lidos** *(incerto)*: o retro-data-structures não lê estes objetos, e os campos de vida não
  foram localizados nos bytes. A 20g mede ou define.
- **Fim:** a Lair tem um `WorldTeleporter` (a saída para o fim do jogo) e 10 `SpecialFunction` de função 22 *(o que fazem: incerto)*.
- **Pelo padrão aceito (decisão 3):** uma arena só, na Lair, no molde da 19k. As Subchambers ficam como descida, sem luta.

## Phazon

- **Nenhum `Area Damage`** (função 18) em sala nenhuma: o Prime não usa o calor para o phazon aqui.
- **`Phazon Pool`:** só na Lair (dentro da luta).
- O nome com "heat"/"varia" aparece em 4 objetos da Lair (contagem `heat` do `dump_prime_locks`) *(o que são: incerto)*.
- **Pelo padrão aceito (decisão 4):** machuca na Infusion Chamber e nas Subchambers, nunca no caminho sem saída. O dano é escolha nossa,
  não dado do Prime.

## Como se entra (decisão nova)

No Prime a cratera abre no **Artifact Temple** do Tallon com os 12 artefatos e a luta com o Meta Ridley; a Crater Entry Point tem
um `WorldTeleporter`. No nosso jogo o Artifact Temple é **só casca** (`tools/tallon/layouts.py:304`: sem teleporte, sem Meta Ridley, sem
artefatos), e o Meta Ridley já é o chefe do fim da fragata. **O que abre a cratera ainda não foi decidido**: fica como pergunta ao
usuário no épico (decisão 7).

## Espaço na ROM (medido em 10/11/2026)

| Banco | Livre hoje | A Impact Crater pede (12 salas, 11 ligações) | Cabe? |
|---|---|---|---|
| `$8F` (cabeçalhos, estados, listas) | **2849** (faixas recuperadas: 364 + 1213 + 730 + 538 + 4 de sobras; principal 1) | ~700–1050 (≈ 56 por sala, como a Mines, + arenas) | **sim** |
| `$A1` (populações) | **8786** (8139 da faixa recuperada na 19a, sem uso, + 647 no fim) | ~200 (3 comuns + a arena) | **sim** |
| `$83` (portas, FX) | 13 938 | ~400 (22 entradas + FX de 12 salas) | sim |
| `$B4` (enemy sets) | 1514 | ~100 | sim |
| `$84` (PLMs) | 1912 | arena e portas (~150) | sim |
| `$A0` (espécies) | 1473 | 1–2 cópias (o Metroid Prime, talvez a 2ª fase) ≈ 128 | sim |
| `$AA` | 1901 | seletores de cor, se a luta usar o Torizo (19k) | sim |
| nível / fixo | 449 712 / 477 501 | ~6 KB de nível; paleta e tabelas (~3 KB) | sim |
| SRAM do mapa (área 0) | Tallon usa 47 de 80 bytes | ~17 (90 telas pela proporção do Tallon) | sim *(a posição no mapa 64×32 da área 0 fica para a 20b)* |

**Conclusão:** o espaço **dá** sem recuperar nada. O aviso do épico 19 ("sobram ~300 de `$A1`") era de antes da 19a, que recuperou
`$A1:AD09–CCD3` (8139 bytes) e não o usou.

## Recomendações para as filhas

1. Dados primeiro (grafo, mapa, travas como na 19c), ROM igual.
2. A entrada só depois da decisão 7.
3. A luta numa filha só (padrão 3), medida no emulador como a 19k.
4. O fim do jogo numa filha própria: hoje não há fim depois do Tallon.
