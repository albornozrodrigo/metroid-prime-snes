# 20 — Impact Crater (épico)

Estado: **verificada, épico 20 fechado na 20j** (11/11/2026: as 10 filhas 20a–20j verificadas; critérios conferidos em "Verificação do épico", no fim; sha1 `2f13e756…c423`; a cadeia completa do começo do jogo à tela do fim com 88%, passando pela cratera e pelo Metroid Prime vencido de verdade; `specs/20j-rodadas-e-cadeia-impact.md`). Antes: 20i verificada (11/11/2026: o fim do jogo: depois da vitória, a tampa aberta e o pulo para a porta do teto da Lair levam ao fim do SM reaproveitado (estado `$26` → `$27`: os créditos e a tela "YOUR RATE FOR COLLECTING ITEMS"), lido do bit `$10` da área 0; sem a vitória nada; a tela com 88% (a conta do jogo com o equipamento dos 88 itens); `specs/20i-fim-do-jogo-impact.md`); antes, 20h verificada (11/11/2026: o Metroid Prime na Metroid Prime Lair, a terceira cópia do Bomb Torizo, vida 3000, uma fase (decisão 3), a porta do teto trancada até a vitória, o evento = o bit `$10` da área 0 (o chefe final vencido, que a 20i lê); a luta vencida de verdade no emulador; `specs/20h-metroid-prime-impact.md`); antes, 20g verificada (11/11/2026: a descida, Phazon Infusion Chamber e Subchambers
One a Five na ROM, sem inimigos (no Prime só a luta, decisão 3); o phazon que machuca = o ácido do SM (a lava não machuca com a Gravity
da rodada 6) em poças fora do caminho nas Subchambers One, Two e Four (as três salas com porta de chão não podem: o FX cobre a sala da
superfície para baixo); `specs/20g-infusion-subchambers-impact.md`); antes, 20f verificada (11/11/2026: a cratera de cima, Phazon Core, Crater Missile
Station com a recarga de mísseis e Crater Tunnel B sem o trilho de Spider Ball, 2 Metroids na Phazon Core; o Burrower proposto na 20a
ficou fora: no Prime ele é de uma camada inativa; `specs/20f-phazon-core-impact.md`); antes, 20e verificada (a entrada: Crater Entry Point com a Save Station e Crater Tunnel A
na ROM, na área 0; o teleporte do Artifact Temple = um elevador dentro da área 0 que só funciona com o bit `$10` da área 5, o Omega
Pirate vencido; `specs/20e-entrada-impact.md`); 20d verificada (estilo da cratera: a rocha da Mines no tileset `$03` com a rocha
avermelhada e o phazon da Mines, numa ROM de teste, ROM do jogo igual, `specs/20d-estilo-impact.md`); 20c verificada (grafo, mapa e travas do Prime em `tools/impact/`, só dados, ROM igual, `specs/20c-grafo-e-mapa-impact.md`), 20b verificada (espaço e a checagem de folga no validador, ROM igual, `specs/20b-espaco-e-toolchain.md`) e 20a verificada (levantamento, `specs/20a-levantamento-impact-crater.md`). As 7 decisões = padrão/proposta aceitos pelo usuário; ver "Respostas do usuário".

Esforço estimado: **12–16 dias** em 8 filhas (20c–20j) de 1–3 dias, mais a 20b (0,5 dia), depois da 20a (0,5 dia). Medido na 20a: **12 salas e 90 telas**, nenhum item, 3 inimigos comuns propostos, 1 chefe, o espaço da ROM sobra. Referência: a Mines (42 salas, 205 telas) levou 13 filhas e foi estimada em 25–30 dias.

## Contexto

A Phazon Mines (épico 19) fechou com 42 salas, 88 itens e os dois chefes; a cadeia completa das cinco áreas passa no emulador. Falta o último mundo do Prime, a **Impact Crater**, onde ficam o núcleo do phazon e a luta final contra o Metroid Prime. Hoje o jogo **não tem fim próprio**: o final que existe é o da fragata (Ridley, épico 7). Sem a Impact Crater não há como chegar ao Prime nem ver o fim do jogo.

O plano das áreas já reserva o lugar: `tools/areas.py:181` `IMPACT_CRATER_AREA = 0`, dentro da área 0 (Crateria), com a nota de que o Prime entra nela pelo Artifact Temple do Tallon. Ou seja: a Impact Crater fica **dentro da área 0**, sem área nova.

## Estado atual (verificado nos dados do Prime)

Fonte: `research/prime_worlds.json` (MLVL "Impact Crater", mlvl `0xc13b09d1`, pak `Metroid7.pak`), lido em 10/11/2026.

- **12 áreas** e **22 portas** (docks) entre elas. Nomes e ligações:

| # | Área do Prime | Ligações (áreas) |
|---|---|---|
| 0 | Crater Entry Point | 1 |
| 1 | Crater Tunnel A | 2, 0 |
| 2 | Phazon Core | 3, 1, 4 |
| 3 | Crater Missile Station | 2 |
| 4 | Crater Tunnel B | 5, 2 |
| 5 | Phazon Infusion Chamber | 6, 4 |
| 6 | Subchamber One | 5, 7 |
| 7 | Subchamber Two | 6, 8 |
| 8 | Subchamber Three | 9, 7 |
| 9 | Subchamber Four | 10, 8 |
| 10 | Subchamber Five | 9, 11 |
| 11 | Metroid Prime Lair | 10 |

- **Caminho em linha reta**: entrada → Tunnel A → Phazon Core → Tunnel B → Infusion Chamber → Subchambers 1 a 5 → Lair. A Missile Station é um beco a partir da Phazon Core.
- **Medido na 20a** (`specs/20a-levantamento-impact-crater.md`): 90 telas no SM; **nenhum item de verdade** (os 35 `Pickup` são recargas de inimigo), uma Save Station (Crater Entry Point) e uma recarga de mísseis (Crater Missile Station); as 5 ligações de cima com porta de plasma, e da Infusion Chamber para baixo uma descida sem porta; trilho de Spider Ball na Tunnel B; 7 inimigos comuns no Prime (3 propostos); o Metroid Prime em duas fases (exoesqueleto nas Subchambers 1–4, essência na Lair); nenhum `Area Damage`, a `Phazon Pool` só na Lair. Vida e ataques do Metroid Prime **não lidos** *(incerto)*.
- **Espaço na ROM** (medido na 20a): **sobra**. `$8F` 2849 livres para ~700–1050; `$A1` 8786 livres (a faixa que a 19a recuperou está sem uso) para ~200. O aviso antigo do épico 19 ("sobram ~300 de `$A1`") é de antes da 19a e não vale mais.
- **Fim do jogo**: não existe. Hoje o último evento é o do Ridley (`specs/05-final-da-fragata.md`). A tela de fim do jogo mostra a porcentagem de itens (88% na Mines, épico 19m), que é a conta que o fim da Impact Crater vai usar.

## Decisões do usuário

Cada uma tem um **padrão proposto**. Se você não responder, eu sigo com o padrão, marcado como "padrão aceito, a confirmar".

1. **Escopo.** A Impact Crater completa (12 áreas), ou só o caminho até a Metroid Prime Lair?
   - *Padrão proposto:* completa, como as outras áreas. O caminho até a Lair sem as Subchambers deixaria o último mundo pela metade.
2. **Área no SM.** Fica dentro da área 0 (Crateria), como o plano já prevê (`tools/areas.py:181`), ou ganha área própria?
   - *Padrão proposto:* área 0. Área própria exigiria mexer no mapa e no `$81`, que a Mines já ocupou.
3. **Metroid Prime (chefe final).** Como fica a luta?
   - *Padrão proposto:* arena na Lair, no molde da Omega Pirate (19k): cópia de chefe existente com vida e ataques próprios, travada por portas que abrem na vitória.
   - *Alternativa:* uma luta de várias fases, como no Prime. Custa mais filhas.
4. **Phazon.** Onde ele machuca? O épico 19 usou "phazon que machuca" (padrão b, +1,5–2 dias) e "só cor" na Mines.
   - *Padrão proposto:* machuca na Phazon Infusion Chamber e nas Subchambers, não no caminho obrigatório sem saída, como a lava da Magmoor (decisão do épico 17).
5. **Fim do jogo.** O que acontece depois da luta final?
   - *Padrão proposto:* créditos e tela de fim com a porcentagem de itens, reaproveitando o fim da fragata (épico 7).
   - *Alternativa:* um final próprio, com cena nova. Custa mais.
6. **Itens.** Quantos, e em que rodada cada um fica? Hoje as áreas seguem a regra das outras: nenhum item antes da rodada certa, e a expansão de Power Bomb nunca antes da rodada 6.
   - *Padrão proposto:* a regra das outras áreas. O número exato sai da filha 20a.

## Filhas

Cada filha segue o molde do épico 19: spec, implementação, validate, build com sha1 conferido, testes, mutações, imagens e documentos.
A filha de "recuperar espaço" do rascunho saiu: a 20a mediu que o espaço sobra. A 20b (10/11/2026) só confirma a medição e põe a folga no validador; as filhas seguintes andaram uma letra (20c–20j).

| Filha | O quê | Dias | Verificação |
|---|---|---|---|
| 20a | Levantamento (só leitura) | 0,5 | **verificada** (10/11/2026) |
| 20b | Espaço no `$8F` e no `$A1` confirmado e a checagem de folga `check_impact_space` no validador (nenhuma faixa nova) | 0,5 | **verificada** (10/11/2026; ROM igual, grupo A) |
| 20c | Grafo, mapa e travas em `tools/impact/` (dados, nenhuma sala; o lugar das 90 telas no mapa da área 0) | 1 | **verificada** (10/11/2026; ROM igual, grupo A) |
| 20d | Estilo da cratera (tileset e cores de phazon, a partir dos da Mines, 19d), numa ROM de teste | 1–1,5 | **verificada** (10/11/2026; ROM igual, grupo A) |
| 20e | A entrada (pela decisão 7), a Crater Entry Point com a Save Station e a Tunnel A | 1,5–2 | **verificada** (10/11/2026; rota e save no emulador, todos os grupos) |
| 20f | Phazon Core, Missile Station e Tunnel B (sem Spider Ball), os inimigos comuns (2 Metroids: o Burrower é de camada inativa no Prime) | 2–2,5 | **verificada** (11/11/2026; rota, recarga de mísseis e inimigos no emulador, todos os grupos) |
| 20g | Infusion Chamber e Subchambers 1–5: a descida e o phazon que machuca (o ácido do SM, em 3 das 6 salas: as com porta de chão não podem) | 1,5–2 | **verificada** (11/11/2026; rota e dano do phazon no emulador, todos os grupos) |
| 20h | Metroid Prime: arena na Lair (molde da 19k), vida e ataques definidos (o Bomb Torizo, vida 3000, uma fase; vitória = bit `$10` da área 0) | 2–3 | **verificada** (11/11/2026; a luta vencida de verdade no emulador, a porta, a morte e o continue, todos os grupos) |
| 20i | Fim do jogo: a saída da Lair (a porta do teto depois da vitória), créditos e tela de fim com a porcentagem (o fim do SM que a fragata usava, como está) | 1,5–2 | **verificada** (11/11/2026; a luta real, a saída, os créditos e a tela com 88% no emulador; sem a vitória nada; todos os grupos) |
| 20j | Rodadas e cadeia completa com a Impact Crater; fecha o épico | 1–1,5 | **verificada** (11/11/2026; ROM igual; a cadeia em 6 partes até a tela do fim com 88%; todos os grupos) |

Total 20c–20j: **12–16 dias** (mais 0,5 da 20b).

## Critérios de aceite (proposta)

- `python3 -I tools/validate.py` com "0 problemas", incluindo as ligações das 12 áreas.
- Build duas vezes com o mesmo sha1.
- Testes de todos os grupos passando; cadeia completa, com a Impact Crater, passando no emulador do início ao fim.
- A luta final vencida de verdade no emulador; a tela de fim aparece.
- A porcentagem final conferida pela conta do jogo, no molde da 19m.

## Riscos

- **Espaço na ROM**: medido na 20a, sobra (ver "Estado atual").
- **Luta final**: a maior incerteza; vida e ataques do Metroid Prime não foram lidos dos dados (20a).
- **Entrada**: sem artefatos e sem o Meta Ridley no Artifact Temple, o que abre a cratera é decisão nova (7).
- **Fim do jogo**: hoje não existe fim depois do Tallon; a 20h mexe no fluxo do fim da fragata.

## Fora de escopo

- Qualquer mudança nas outras áreas, salvo o que a cadeia exigir (cada uma seria anotada como desvio).
- Os ataques próprios da Parasite Queen (sugestão já anotada no handoff, não é parte deste épico).

## Respostas do usuário

Em 10/11/2026 o usuário respondeu "pode seguir com os padrões e começar a 20a". Todas as seis = **padrão aceito pelo usuário em 10/11/2026**:

1. Escopo: a Impact Crater completa (as 12 salas).
2. Área: dentro da área 0, com o Tallon.
3. Metroid Prime: arena na Lair, no molde da Omega Pirate (19k).
4. Phazon: machuca só na Phazon Infusion Chamber e nas Subchambers, nunca no caminho obrigatório sem saída. (20g: o ácido do SM nas
   Subchambers One, Two e Four; a Infusion e as Subchambers Three e Five têm porta de chão: sem ácido, a confirmar com o usuário.)
5. Fim do jogo: créditos e tela de fim com a porcentagem, reaproveitando o fim da fragata (épico 7).
6. Itens: a regra das outras áreas. A 20a mediu que a cratera não tem item de verdade: nada a colocar, a conta fica em 88 itens.
7. Entrada (decisão nova da 20a): **aceita pelo usuário em 10/11/2026** ("pode seguir com a proposta"): o teleporte do Artifact
   Temple liga depois do Omega Pirate (19k), sem artefatos.

## Decisão nova (da 20a)

7. **O que abre a cratera?** No Prime são os 12 artefatos no Artifact Temple e a luta com o Meta Ridley. No nosso jogo o Artifact Temple é
   só casca (`tools/tallon/layouts.py:304`), não há artefatos, e o Meta Ridley é o chefe da fragata.
   - *Proposta:* o teleporte do Artifact Temple liga depois do Omega Pirate (o último chefe antes da cratera), sem artefatos.
   - *Alternativas:* liga depois de todos os chefes; ou fica sempre aberto a partir da rodada em que o Plasma chega (as portas da cratera
     são de plasma).
   - **Aceita pelo usuário em 10/11/2026** ("pode seguir com a proposta"): o teleporte do Artifact Temple liga depois do Omega
     Pirate (19k), sem artefatos. Usada pela 20e (a entrada).

## Verificação do épico (11/11/2026, 20j)

Conferido no fim da 20j, contra os critérios de aceite do épico e as decisões do usuário (pasta real; saídas em
`scratchpad/s20j/`):

| Critério | Onde | Resultado |
|---|---|---|
| `validate.py` com "0 problemas", incluindo as ligações das 12 áreas | `check_impact_graph` (tabela), `check_impact_rooms` (andadas com o equipamento da rodada 6), **`check_epic_impact`** (as 11 ligações construídas = as do Prime, lados e telas, nenhuma porta para fora) | sim: "275 salas, 568 portas, 0 problemas"; linha nova "impact (specs/20, épico fechado na 20j): as 12 salas construídas (regiões A B C D) na área 0, 11 ligações = as do Prime …" |
| Build duas vezes com o mesmo sha1 | `tools/build.py` ×2 | sim: `2f13e7563c7202f82602ad21ba00ba6588c21423` nas duas (o da 20i: a 20j não muda a ROM) |
| Testes de todos os grupos | `run_tests.py --grupo A/B/C/D`, nessa ordem | sim: A 34/34, B 64/64, C 22/22, D 29/29 (183, 197, 246, 214 s) |
| Cadeia completa com a Impact Crater, do início ao fim, no emulador | `cadeia_completa_parte_1..6` (a 6 nova: o teleporte, a cratera andada até a Subchamber Two, a Lair, a luta, a saída, o fim) | sim: as 6 partes passam; a parte 6 sai do estado salvo da 5 |
| A luta final vencida de verdade; a tela de fim aparece | `impact_metroid_prime`, `impact_fim_do_jogo` (20h, 20i) e a parte 6 da cadeia (`CHAIN_PRIME_FIGHT`, nenhuma RAM na luta) | sim: vida do Metroid Prime 0, bits `$04`/`$10` da área 0; estado `$26` → `$27`, os créditos, "YOUR RATE FOR COLLECTING ITEMS IS 88%" |
| Porcentagem final conferida pela conta do jogo (molde da 19m) | `chain_percent` (a conta de `$8B:E627` com as tabelas da ROM, sobre o que a cadeia pegou), `check_world_rounds`, `check_epic_impact`, `check_impact_ending` | sim: 88 itens pegos, conta = 88 (um por item); os dígitos que o jogo escreveu na tela (`7E339E`/`7E33A0`) = os de 88 |
| Decisão 1: as 12 salas | `check_epic_impact` | sim |
| Decisão 2: área 0 | `check_epic_impact`, `check_impact_rooms` | sim |
| Decisão 3: arena na Lair (molde 19k) | `check_impact_boss`, `check_epic_impact` (uma arena, bit `$10`) | sim (pendência (c) abaixo) |
| Decisão 4: phazon que machuca fora do caminho | `check_impact_rooms` (ácido nas salas da descida sem porta de chão) | sim (pendência (a) abaixo) |
| Decisão 5: créditos e tela de fim reaproveitados | `check_impact_ending`; a parte 6 | sim (pendência (d) abaixo) |
| Decisão 6: itens pela regra das outras áreas | `check_epic_impact` (nenhum item na cratera, a conta igual com e sem ela), a linha das rodadas igual | sim: nenhum item; nenhuma rodada muda |
| Decisão 7: o teleporte depois do Omega Pirate | `check_impact_rooms`, `check_epic_impact` (o único elevador, rodada 6, a última); a cadeia (o Omega vencido de verdade na 19m abre o teleporte) | sim |

Pendências herdadas, sem resposta do usuário (padrão mantido, **não resolvidas**): (a) o ácido das Subchambers em 3 de 6 salas,
laranja-ferrugem; (b) a tela vazia dos testes de mapa em (30, 30); (c) a luta do Prime: vida 3000 chutada, o feixe fere, uma fase,
as cores do Thardus; (d) o fim: textos do SM, o fim vem pela porta do teto (o usuário ainda não disse se prefere o fim na morte do
Prime).
