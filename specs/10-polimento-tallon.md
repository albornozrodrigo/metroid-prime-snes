# 10 — Polimento do Tallon (épico)

Estado: verificada (26/10/2026: as 4 filhas verificadas; validate 72/148/0 com a linha do Tallon igual; .ips sha1 `3919c3c7…64ff` igual em dois builds; 52/52 testes)
Esforço estimado: 2–3 dias no total (10a 0,25 d; 10b 0,25 d; 10c 0,5 d; 10d 1–1,5 d)
Épicos anteriores: [07 — Tallon Overworld](07-tallon-overworld.md), [09 — Itens de trava](09-itens-de-trava.md) (verificados)

## Contexto

Depois do épico 09 o Tallon inteiro é jogável: 44 salas, 20 itens em 7 rodadas, a cadeia completa no emulador. Esta etapa
é de **acabamento**: olhar as 44 salas no emulador, achar o que destoa (visual, portas, inimigos, mapa) e o que deixa os
testes frágeis, e corrigir o que for barato e seguro. **Sem sala nova, item novo nem mudança de progressão**: a tabela de
rodadas do validador (20 itens em 7 rodadas, 44 salas) fica igual.

## Estado atual (verificado)

Na pasta real, antes do épico: `python3 -I tools/validate.py` → "72 salas, 148 portas, 0 problemas" (linha do Tallon:
"alcançáveis agora: 44, 20 itens em 7 rodadas"); `build/metroid_prime_snes.ips` sha1 `9bc37cab4865b96ea4be265812fad89d3e253462`;
`python3 -I tests/run_tests.py` → 49/49.

### Como foi a auditoria

Roteiros no scratchpad da sessão (`…/scratchpad/s10/`), nunca em `build/`; ROM = `build/metroid_prime_snes.sfc` de agora:

- `mkstate.py`: estado salvo depois do pouso na Landing Site (fim da fragata, como os testes do Tallon).
- `audit.py` + `stitch.py`: para **cada uma das 44 salas**, da Landing Site (ou da Savestation, para D/E) por teleporte de
  porta até a sala; uma foto por tela (Samus e câmera postas por RAM a cada quadro durante a pausa, pausar/despausar
  redesenha) e a montagem da sala inteira. As 44 montagens foram olhadas (`audit/full_tallon_*.png`); cópias de algumas em
  `specs/img/10-auditoria-sala-*.png`.
- `entry.py`: **cada uma das 88 entradas de porta do Tallon** por teleporte, a Samus parada 500 quadros depois de ganhar o
  controle: chegou? quanto perdeu de energia e quando? (`entry.out`).
- `upsweep.py`: **as 16 portas de teto que sobem para sala seca** (14 da fragata, Canyon → Gully, Artifact Temple → Temple
  Lobby): Samus de pé na plataforma da linha 6 sob a porta, em 5 posições x dentro das 4 colunas da porta, pulo parado
  guiando para a direita, para a esquerda, pulo sem direção e pulo em parafuso, a direção segurada até depois da transição.
- `capsheet.py`, `mapshot.py`: as tampas de porta em cada linha de paleta do tileset 4; o mapa de pausa com todas as telas
  não maciças exploradas.

### Achados

| # | Achado | Evidência | Decisão |
|---|--------|-----------|---------|
| A1 | **Teleporte de porta dos testes desalinha o BG1.** `door_teleport` (`tests/run_tests.py:627`) põe a Samus diante da porta mas deixa a câmera onde estava; numa porta de chão/teto a transição sai com `$091F` fora de tela inteira (ex.: Savestation → Reactor Access `$00E1`, andando `$0100`; Gully → Canyon `$02E1`) e o erro passa adiante por toda a cadeia. Os PLMs se desenham fora do bloco: itens e tampas em dobro (Morph na Chozo West, Ice/míssil na Root Cave, Wave na Magmoor East, E-tank na Hydro, cabana de PB repetida no Life Grove). **Só nos testes**: andando o jogo alinha. | `10-auditoria-teleporte-chozo-west-antes.png` (tampa dupla), `-depois.png`; `audit.out` (`$091D/$091F` de cada sala) | 10a |
| A2 | **Teleporte para cima por porta de teto não troca de sala** (09f, Desvios). Mesma causa: com a câmera na tela da porta (y 0) as 4 subidas (Canyon → Gully, Artifact Temple → Lobby, Reactor Access → Savestation, GTH → Hydro) chegam. | `entry.out`: `chegou=True` nas 88 entradas com a câmera posta | 10a |
| A3 | **O A do `tallon_first_missile` é ignorado** (`tests/run_tests.py:548`: A 240 quadros depois do fim da caminhada). Fotos: a caixa MISSILE continua 300 quadros depois desse A; um A **60 quadros mais tarde** fecha (180/240/300 também). Hoje quem fecha é o próximo botão do andador. | `scratchpad/s10/m5_all.png`, `m6_all.png` | 10a |
| A4 | **Subir por porta de teto para sala seca**: com a direção segurada até o fim da transição, das 16 portas só **Canyon → Gully** derruba a Samus de volta, partindo da beira oeste da porta (x +6) e guiando para a borda **leste** (a do outro lado): ela ganha o controle com o pé 47 px acima da borda (`$0240`) e chega a x 155 com o pé em 215, 7 px abaixo do topo (208). Sem direção ela sempre cai de volta (como no SM: o buraco da porta fica aberto); fechar a tampa atrás dela (bit `$04` da direção, como 24 das 31 portas de subir vanilla) **não segura** a Samus no meio da porta (experimento: cai através). Os "XX" restantes da varredura são cabeçada no teto da sala de baixo (guiando para fora das 4 colunas), não queda. Com `$0280` (+14 px), `$02A0` (+21 px) e `$02C0` (+28 px) nenhuma queda; `$02A0` passa os 49 testes, inclusive as fugas (a spec 08 viu `$0340` quebrar a Vent D → Vent E). | `upsweep.py` (`sweep_base.txt`, `sw_0280/02A0/02C0.txt`); traço `tr2.py tallon_canyon tallon_gully 6 RIGHT` | 10b |
| A5 | **Mapa de pausa diferente da forma da sala**: telas inteiras de rocha (16 no Tallon: Canyon 3, Artifact Temple 5, Life Grove 3, Vent C 2, Tunnel C 1, Reactor Core 1, Elevator Beta 1; 1 na fragata: Vent A) entram no retângulo da sala; como nunca são exploradas, a sala aparece recortada e **sem parede** do lado da rocha (Canyon em L aberto, Artifact Temple com degraus abertos). `pausemap.room_tile` (`tools/frigate/pausemap.py:63`) só põe parede na borda do retângulo. | `10-auditoria-mapa-de-pausa.png` | 10c |
| A6 | **Porta de onda cinza com pouco contraste**: a tampa cinza (metatiles `$0AE/$0CE…`, tiles `$398–$39B`, paleta 1) só usa as cores 4–7 da linha 1 (moldura cinza-rosada) e some no fundo da fragata afundada. As tampas de cor (`$004/$024`, tiles `$300…`) usam as cores 1–3 da linha: linha 0 = laranja (plasma), 1 = verde (gelo), 2 = rosa (míssil), 3 = azul (comum). Nenhuma linha do tileset 4 dá roxo (a cor da porta de onda do Prime); a **linha 6 não é usada por nenhum metatile do tileset 4** (CRE + SCE, conferido) e os metatiles SCE `$3E0–$3FE` são enchimento (`$03FF ×4`) que nenhuma sala do tileset 4/5 (vanilla ou nossa) usa. As 7 portas de onda ficam no tileset 4. | `10-auditoria-porta-de-onda.png`; `capsheet.png` | 10d |
| A7 | **Inimigos na entrada das portas**: parada, a Samus leva o primeiro dano de 1 s (Elevator Beta, o Space Pirate, das duas portas) a 4,5 s depois de ganhar o controle; nas outras 74 entradas, nada. No Elevator Beta, atirando para a frente logo que entra ela mata o pirata **sem perder energia** (`pirate.py`: 99 → 99). Nenhum dano inevitável. | `entry.out`; `10-auditoria-elevator-beta-entrada.png` | sem mudança |
| A8 | **Salas vazias**: Landing Site, Crash Site, Artifact Temple, Reactor Core, Cargo Lift e outras não têm inimigo: é a camada 0 do Prime (spec 07i: contas do Prime, `check_tallon_enemies`). Pôr inimigos fora dessas contas muda uma regra de projeto. | `10-auditoria-sala-crash-site.png`, `-artifact-temple.png` | **decisão do usuário** (fora deste épico) |
| A9 | **Visual das salas**: nas 44 montagens não há emenda de tile, metatile errado nem cor quebrada; itens no lugar (fora os fantasmas do A1). A Canyon e o Artifact Temple têm muitas telas de rocha maciça (forma da caixa do Prime); o mapa (A5) é o que destoa. | montagens `audit/full_tallon_*.png` | só o A5 |
| A10 | **Andador cego na Chozo West** (`TALLON_CYCLES`, `TALLON_CYCLES_BACK`, `tallon_rota_bc`): ciclos medidos; mexer nas salas do caminho pode pedir novo ajuste (o verificador mostra a sequência de salas). | `tests/run_tests.py:330–340` | documentado; nenhuma filha muda as salas do caminho |

## Filhas (ordem: mais rápida primeiro)

| # | Spec | O quê | Muda a ROM? |
|---|------|-------|-------------|
| 10a ✔ | [Teleporte de porta alinhado e o A do primeiro míssil](10a-teleporte-alinhado.md) | A1, A2, A3: `door_teleport` põe a câmera na tela da porta; o A do `tallon_first_missile` 60 quadros depois; teste novo | não |
| 10b ✔ | [Subir por porta de teto com folga](10b-subida-com-folga.md) | A4: `build.UP_PUSH` `$0240` → `$02A0` (regra única `door_push`, conferida por `check_door_push`); teste novo da subida pela borda longe | sim (bytes 8–9 das entradas de subir para sala seca) |
| 10c ✔ | [Mapa de pausa com a forma da sala](10c-mapa-com-a-forma-da-sala.md) | A5: tela maciça fica fora do mapa e as vizinhas ganham parede; máscara e lista do save iguais | sim (tilemap dos mapas) |
| 10d ✔ | [Porta de onda roxa](10d-porta-de-onda-roxa.md) | A6: tampa da onda com os tiles das portas de cor na linha 6 do tileset 4, pintada de roxo; 8 metatiles novos e quadros próprios | sim |

## Definição de pronto

- As 4 filhas `verificada`, cada uma com Desvios, checagem no validador e/ou teste no emulador, fotos `specs/img/10x-*.png`
  olhadas.
- `python3 -I tools/validate.py` → 72 salas, 148 portas, 0 problemas, linha do Tallon igual ("alcançáveis agora: 44, 20 itens
  em 7 rodadas").
- Build duas vezes, mesmo sha1; testes todos passando.

## Fora de escopo

- Sala, item, trava ou rodada nova; inimigos além das contas do Prime (A8: decisão do usuário).
- Tampa que fecha embaixo da Samus nas portas de subir (A4: não segura no meio da porta; seria preciso tampa no nível e
  atirar para descer).
- Reajuste dos andadores cegos (A10).

## Desvios (preenchido na implementação)

Verificação final (26/10/2026, na pasta real, depois das 4 filhas):

- `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas`; linha do Tallon "… 44 salas construídas, alcançáveis agora:
  44, 20 itens em 7 rodadas …" (igual à de antes: rodadas e salas sem mudança).
- `python3 -I tools/build.py` duas vezes → sha1 `3919c3c73d46afc45ffd4eb51083daebbe8264ff` nas duas (antes do épico `9bc37cab…3462`;
  10a não muda a ROM, 10b → `ed565db6…`, 10c → `2eb8a710…`, 10d → `3919c3c7…`).
- `python3 -I tests/run_tests.py` → **52/52** (49 + `teleporte_de_porta_alinhado`, `sobe_porta_de_teto_pela_borda_longe`,
  `mapa_com_a_forma_da_sala`). Expectativas antigas: nenhuma mudou; `porta_de_onda` ganhou a checagem da cor; ajudantes
  `door_teleport` (câmera), `tallon_first_missile` (A mais tarde) e `chain_round_0` (sem o segundo A).

Desvios do épico:

- **A4 (subida)**: "confiável num pulo normal" ficou parcial: guiando para a borda do outro lado do buraco ainda cai partindo do
  quarto de fora da porta, e sem direção cai sempre (10b, Desvios). O empurrão tem teto (`$02E0` quebra a fuga da fragata) e a tampa
  fechando atrás não segura; o resto pede mexer na geometria das 18 portas de chão das duas áreas.
- **A5 e A4 valem para as duas áreas**: o mapa (função única `pausemap.room_tile`) muda também a Vent A da fragata; o empurrão
  (regra única `door_push`) também as 14 portas de subir da fragata. As duas áreas foram conferidas (validador e testes).
- **A7 (inimigos)**: nenhuma mudança: nenhum dano inevitável medido. **A8**: fica para o usuário decidir.
- Roteiros e saídas da auditoria: no scratchpad da sessão, `s10/` (`audit.py`, `entry.py`, `upsweep.py`, `climbscan.py`,
  `pirate.py`, `missile*.py`, `capsheet.py`, `purple.py`, `mapshot.py`; experimentos em cópias `proj_*`, nunca em `build/`).
