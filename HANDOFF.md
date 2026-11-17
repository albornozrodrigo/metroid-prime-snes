# Handoff — onde paramos (13/11/2026): **épico 20 (Impact Crater) fechado (20a–20j verificadas); épico 21 (Artes do Prime) em andamento: 21a verificada parcialmente, 21b em andamento (ROM de teste pronta, falta conferir no emulador)**

Leia junto com o `README.md` (estado do jogo e comandos) e `research/sm_room_format.md`
(formatos verificados da ROM; a seção 13 cobre Ridley, nave e cronômetro). Este arquivo diz o que
retomar e como. As specs de cada filha têm o detalhe; o índice é `specs/README.md`.

## Como recomeçar (registrado em 13/11/2026)

**Onde parou:**
- **Épico 20 (Impact Crater): fechado** na 20j (20a–20j verificadas; 12 salas, 90 telas, nenhum item, o Metroid Prime vencido de verdade, o fim do jogo; cadeia completa com 88%). Detalhe em `specs/20-impact-crater.md`, seção "Verificação do épico".
- **Épico 21 (Artes do Prime): aprovado em 11/11/2026**, em andamento. Decisões do usuário: a arte é feita por mim, por código; direitos não se aplicam (uso pessoal); ordem 21b → chefes → Samus; quando o Prime não cabe no SNES, aproximar e registrar cada caso como desvio.
  - **21a (só leitura): verificada parcialmente.** Medido: 27 texturas do Prime (47 970 cores somadas; limite de 16 cores por paleta). Não medido ainda: tiles da Samus e dos chefes do SM, e os modelos do Prime (precisa instalar `retro_data_structures` em ambiente de rascunho).
  - **21b (efeitos de poder): em andamento.** Cores medidas do Prime nas partículas: Power laranja, Wave roxo, Ice azul-claro. Plasma e Phazon sem cor identificada; Charge não ligado a um feixe.
    - Nova ROM de teste: `python3 -I tools/build.py --teste-21b` → `build/teste-21b/metroid_prime_snes.sfc` (sha1 `d85d5b97…48552d`, mudou em 17/11 por causa da correção do Wave; uma build só, a repetição ainda não foi conferida). Código em `tools/beam21b.py`; muda só 35 bytes nas paletas `$90:C3E1` (Power), `$90:C461` (Wave) e `$90:C401` (Ice). O Wave estava em `$C421` (que é do Charge): corrigido.
    - **Não conferido no emulador ainda.** Até isso, a mudança não vai para a ROM do jogo. Débito técnico registrado em `specs/21b-efeitos-de-poder.md` ("Débito técnico (validar depois)"): as cores de tiro medidas no headless antes são inválidas e o pixel do tiro não foi localizado.
    - Desvio conhecido: a paleta do Ice `$90:C401` é compartilhada por quase todas as combinações de feixes.
- **ROM do jogo**: `build/metroid_prime_snes.ips`, sha1 **`2f13e756…1423`**, duas builds iguais. Validate: `275 salas, 568 portas, 0 problemas`. (A ROM do jogo não mudou na 21a nem na 21b.)
- **Pendências do usuário:** nenhuma decisão aberta sobre o épico 21 além da conferência visual da 21b (ver `specs/21b-efeitos-de-poder.md`).

**Próximo passo:** (17/11, decisão do usuário: a conferência da 21b fica para depois, como débito técnico) rodar os testes A–D e seguir o desenvolvimento. A conferência visual continua pendente: carregar a ROM de teste com um feixe equipado e ver o tiro com a cor nova. Se estiver ok, decidir com o usuário se a cor entra na ROM do jogo; se não, ajustar `tools/beam21b.py`. Depois: testes A–D, registrar em `specs/21b`, `specs/README.md` e este arquivo. Em seguida: 21c (chefes), e as medições pendentes da 21a.

**Como recomeçar:**
1. Ler este arquivo, `specs/21-artes-prime.md`, `specs/21b-efeitos-de-poder.md` e a seção "Verificação do épico" de `specs/20-impact-crater.md`.
2. Conferir o estado antes de mexer (cada comando com timeout de 10 min; um grupo de testes por vez):
   ```
   python3 -I tools/build.py | tail -1 && shasum build/metroid_prime_snes.ips   # duas vezes: 2f13e756…1423
   python3 -I tools/validate.py | tail -1                                       # 275 salas, 568 portas, 0 problemas
   python3 -I tools/build.py --teste-21b && shasum build/teste-21b/metroid_prime_snes.sfc   # duas vezes: 01683f72…2b499e
   python3 -I tests/run_tests.py --grupo A   # depois B, C, D (A 34, B 64, C 22; D a confirmar)
   ```
3. A contagem de testes do grupo D não foi reconferida nesta atualização: o número certo é o que o comando `--grupo D` mostrar.

**Cuidados aprendidos nesta rodada (12–13/11):**
- Bibliotecas de leitura do Prime ficam **só** num ambiente de rascunho (`scratchpad/s21venv`), nunca no projeto. Ler os pacotes exige a raiz `research/prime_fs` (não `prime_fs/files`) e descomprimir os recursos (4 bytes de tamanho + zlib; `PART` começa com `GPSM` sem compressão).
- No macOS, `sed -i` precisa de sufixo (`sed -i ''`); preferir Python para edições simples.
- O scratchpad fica em `/private/tmp/…` e pode sumir ao reiniciar. O que importa está nas specs e no código.
- Não mexer no tempo do título/boot (quebra o RNG e as lutas medidas).
- Ao copiar o projeto, não apagar a pasta `.claude/`.

**Histórico (o texto de 10/11, antes do épico 20, fica abaixo para referência):**


### Estado de 10/11/2026 (histórico), **épico 19 (Phazon Mines) fechado na 19m: 19a–19m verificadas** — **19m**: as rodadas das cinco áreas (a linha das rodadas com os 2 elevadores da Mines: mines_east 5, mines_west 4; `check_epic_mines`) e a cadeia completa em 5 partes pelos 13 itens da Mines, andando, com **o Phazon Elite e o Omega Pirate vencidos de verdade**, os 2 elevadores de verdade e **88% na tela do fim**; ROM igual, sha1 `f5b0f58b…0dac`; A 34/34 (3 min 17 s), B 64/64 (3 min 52 s), C 22/22 (4 min 24 s), D 18/18 (3 min 31 s); próximo passo: **um épico novo, que precisa do usuário** (a Impact Crater, um fim próprio do jogo ou outro); pendente para o usuário: as escolhas da 19j, 19k, 19l e 19m (lista em "Verificação do épico" de `specs/19-phazon-mines.md`); antes, onde paramos (09/11/2026, **épico 19 (Phazon Mines) aprovado e em implementação: 19a–19l verificadas** — **19l**: a região D (as 10 salas do nível de baixo: **as 42 da Mines na ROM**; a porta de plasma vertical; a Fungal Hall A com gelo do lado dela e plasma do outro (`SIDE_CAPS`); a Phazon Mining Tunnel com um túnel de bomba e de PB; a Missile Station (PLM `$B6EB`); Save Station C = estação 3; 3 mísseis na rodada 6; 2 Metroids, 2 Hunter Metroids, 1 Sova, 2 orbes, 1 pirata; 88 itens, 88%); sha1 `f5b0f58b…0dac`; A 34/34 (3 min 8 s), B 64/64 (3 min 17 s), C 21/21 (1 min 49 s), D 18/18 (3 min 47 s); próximo passo: **19m** — as rodadas das cinco áreas e a cadeia completa; pendente para o usuário: as escolhas da 19l (o míssil da Metroid Quarantine B numa coluna de Space Jump; o túnel da Phazon Mining Tunnel com 1 bloco de bomba e 1 de PB; os inimigos; a Missile Station sem ícone no mapa; as formas), as da 19k e as da 19j; antes, **19k**: o Omega Pirate (a segunda cópia do Bomb Torizo na Elite Quarters, `$A0:F9FF`, vida 1200, imune ao feixe sem carga, na posição do Thardus; as cores por área com seletores no `$AA`; as 2 portas cinza de tipo 2 até a vitória; sem prêmio; `mines_omega_pirate`, a luta só com mísseis); sha1 `931e7f10…6ddb`; A 34/34 (2 min 58 s), B 64/64 (3 min 9 s), C 21/21 (1 min 53 s), D 16/16 (3 min 44 s); próximo passo: **19l** — a região D; pendente para o usuário: as escolhas da 19k (o tiro carregado fere: com Plasma + Ice + Wave dois tiros vencem; vida 1200; as cores e o pulso do peito cinza) e as da 19j; antes, **19j**: a região C (5 salas e a P25 aberta; o Phazon Processing Center com o salão da Omega Research e o míssil num fosso de PB, rodada 6; o E-tank da Processing Center Access entre portas de plasma, rodada 6; a Elite Quarters vazia e pronta para a 19k; a parede de PB da Maintenance Tunnel fecha o atalho Magmoor ↔ Tallon até a rodada 6; o gancho da Transport Access sem trava; 85 itens, 85%); sha1 `4c295929…6da5`; A 34/34 (3 min 10 s), B 64/64 (3 min 38 s), C 21/21 (1 min 52 s), D 15/15 (3 min 48 s); **em 09/11/2026 o usuário confirmou todos os padrões que estavam "a confirmar" (19b–19i e as decisões 2, 5, 7, 8 do épico)**; escolhas da 19j (o míssil do PPC atrás de PB; o gancho da Transport Access sem trava; as formas); antes, **19i**: a região B (12 salas; Save Station B; a Map Station; 83 itens); 19h: o Phazon Elite; 19g: os inimigos da região A; 19f: a região A; 19e: os elevadores e a área 5; 19a–19d com a ROM igual; antes: **épico 18 (Phendrana) fechado na 18n**)

Leia junto com o `README.md` (estado do jogo e comandos) e `research/sm_room_format.md`
(formatos verificados da ROM; a seção 13 cobre Ridley, nave e cronômetro). Este arquivo diz o que
retomar e como.

### Como recomeçar (10/11/2026, depois da 19m)

**Onde parou:** **épico 19 (Phazon Mines) fechado**: as 13 filhas **19a–19m verificadas** (a 19m feita por um agente em
10/11/2026; o orquestrador confere de novo antes de seguir). Última conferência (19m): dois builds iguais, sha1
`f5b0f58b3cd6ef58d573403852b091a7446b0dac` (a ROM da 19l: a 19m não mexe na ROM); validate "263 salas, 546 portas, 0 problemas"; linha
do Tallon igual ("44 salas construídas, alcançáveis agora: 44, 20 itens em 7 rodadas"); rodadas "88 itens em 7 rodadas … elevadores …
mines_east 5 (do Tallon), mines_west 4 (da Magmoor); … com todos: 88%"; linha nova "mines (specs/19, épico fechado na 19m)"; testes **A
34/34, B 64/64, C 22/22, D 18/18** (na ordem A, B, C, D: a cadeia tem 5 partes, a 1 no A, a 2 no B, a 3 e a 4 no C, a 5 no D). Nenhum
trabalho pela metade: nada em andamento, nenhum arquivo meio editado.

**Próximo passo:** **um épico novo, que precisa do usuário** (os épicos seguem o molde: levantar os fatos, decidir o técnico, perguntar
o de gosto e de escopo, aprovar antes de começar). Candidatos: a **Impact Crater** (o último mundo do Prime; o plano das áreas a põe na
área 0), um **fim próprio do jogo** (hoje a cadeia usa o fim do SM com o evento `$0E` por RAM), ou responder às escolhas pendentes
abaixo.

**Como recomeçar:**
1. Ler este arquivo, `specs/19-phazon-mines.md` ("Verificação do épico", no fim) e a spec da última filha
   (`specs/19m-rodadas-e-cadeia-cinco-areas.md`).
2. Conferir o estado antes de mexer (cada comando com timeout de 10 min; um grupo de testes por vez):
   ```
   python3 -I tools/build.py | tail -1 && shasum build/metroid_prime_snes.ips   # duas vezes: f5b0f58b…0dac
   python3 -I tools/validate.py | tail -1                                       # 263 salas, 546 portas, 0 problemas
   python3 -I tests/run_tests.py --grupo A   # depois B, C, D (34, 64, 22, 18)
   ```
3. Perguntar ao usuário qual o próximo épico.

**Cuidados aprendidos nesta rodada:**
- O scratchpad da sessão fica em `/private/tmp/…` e **some ao reiniciar**: os roteiros de busca e de mutação das 19a–19h (`s19a/` …
  `s19h/`) se perdem. O que importa já está nas specs e no código; os resultados das mutações estão registrados em cada spec.
- Copiar o projeto para outro lugar **sem a pasta `.claude/`** (uma cópia com ela apagou o scratchpad três vezes na 19c).
- A máquina ficou muito carregada (antivírus Kaspersky e outras sessões; carga até ~150): os grupos levaram 5–10× o normal
  (normal: A ~3,5 min, B ~4 min, C ~2,5 min, D ~4 min). Lentidão não é falha: os testes contam quadros. Rodar os grupos em segundo plano.
- O computador dormindo derruba o agente no meio (aconteceu na 19h): deixar o computador sem dormir enquanto roda.
- Nunca mexer no tempo do título/boot (muda o RNG e quebra as lutas medidas).
- (19l) O driver de medição da 19l (`scratchpad/s19l/drv.py`: `make`/`tryin`/`hop_search` com estados salvos do emulador)
  some ao reiniciar; a ideia é a mesma da 19i. Rodar um grupo de testes junto com medições no emulador estoura os 10 min: um de cada vez.
- (19i) As caminhadas medidas saem rápido com um estado salvo do emulador por sala e uma busca dos quadros antes de cada pulo
  (`scratchpad/s19i/scripts/drv.py`: `state`/`chain`/`steps`/`hop_search`/`upto`); o roteiro some ao reiniciar, a ideia está na
  spec da 19i. Uma Mella balança: os primeiros tiros nem sempre acertam (6 tiros agachada). Tiros a mais abrem a tampa da porta do
  outro lado da sala: conferir onde a Samus para depois.

**Decisões em aberto para o usuário:** (19m: nenhuma nova de jogo; a lista inteira está em "Verificação do épico" do épico 19.) Em 09/11/2026 o usuário mandou seguir com as sugestões do handoff: **todos os padrões que
estavam "a confirmar" ficam confirmados** (19b–19i e as decisões 2, 5, 7 e 8 do épico; registrado em "Confirmação (09/11/2026)" do
épico e em cada spec). Novas, da 19j (padrão aceito, a confirmar): o míssil do PPC atrás de blocos de PB num fosso (alternativa: numa
borda de Space Jump, rodada 4); o gancho da Transport Access sem trava (a sala tem 1 tela de altura); as formas (o PPC = o salão da
Omega Research).
Da 19k (padrão aceito, a confirmar): o tiro carregado fere o Omega (com Plasma + Ice + Wave tira 900: dois tiros vencem; alternativa:
imune também ao carregado, só mísseis); vida 1200 (12 mísseis); as cores (as rampas do Phazon Elite) e o pulso do peito cinza do Thardus.
Da 19l (padrão aceito, a confirmar): o míssil da Metroid Quarantine B no alto de uma coluna de Space Jump (alternativa: a pé); a
Phazon Mining Tunnel com 1 bloco de bomba e 1 de Power Bomb antes da câmara (o Prime tem 17 blocos e a parede Bendezium); os inimigos
(1 orbe, 1 Sova, 2 Metroids, 1 pirata + 1 orbe, 2 Hunter Metroids; Rippers fora); a Missile Station sem ícone no mapa de pausa; as
formas (salas reaproveitadas das regiões A–C).

## Objetivo

Recriar o Metroid Prime (GameCube) como jogo 2D de SNES, hack sobre Super Metroid com a Fix
Collection (`base/sm_fix.sfc`). Corrigir bugs dos dois jogos no caminho. O usuário não é
especialista em ROM hacking: falar em português simples. Trabalho por etapas, cada uma aprovada
pelo usuário antes de começar a próxima.

## Etapas

| # | Etapa | Estado |
|---|-------|--------|
| 1 | Salas navegáveis da Frigate Orpheon | feito |
| 2 | Inimigos e Parasite Queen (Phantoon) | feito |
| 3 | Save station no Reactor Core Entrance | feito |
| 4 | Map station na Map Facility + mapa de pausa | feito |
| 5 | Acabamento visual das salas | feito |
| 6 | Aparência da Parasite Queen | feito (cores e, desde a spec 06, forma própria) |
| 7 | Meta Ridley / fim da fragata | feito (+ specs 01–05: continue, minimapa, SRAM, hangar, final com a fuga de Ceres) |
| 8 | Tallon Overworld (`specs/07-tallon-overworld.md`) | **verificado** (fechado na 09f); MVP feito (07a–07g) + 07j (elevadores) + 07k (regiões B e C, travas fiéis) + 07h (6 mísseis) + 07i (inimigos) + 07l (região D, fragata afundada) + 07m (região E, Gully e Alcove): **as 44 salas na ROM**, 13 filhas verificadas |
| 9 | Itens de trava — o Tallon inteiro jogável (`specs/09-itens-de-trava.md`) | **verificado**: 09a (portas de feixe), 09b (itens de feixe e Gravity Suit), 09c (banco do nível), 09d (Morph Ball e Bombas), 09e (Power Bomb e a cabana do X-Ray) e 09f (rodadas declaradas e a cadeia completa) verificadas: **as 44 salas e os 20 itens a pé da nave, em 7 rodadas** |
| 10 | Polimento do Tallon (`specs/10-polimento-tallon.md`) | **verificado**: auditoria das 44 salas e 88 entradas de porta no emulador; 10a (teleporte de porta alinhado e o A do primeiro míssil, só testes), 10b (subir por porta de teto com folga, `UP_PUSH` `$02A0`), 10c (mapa de pausa com a forma da sala), 10d (porta de onda roxa); rodadas iguais |
| 11 | Limpeza (`specs/11-limpeza.md`) | **verificada**: auditoria das salas vanilla órfãs (243 sem caminho, 19 só nas demos de atração); `check_orphans` no validador, bits vanilla lidos dos bytes (262 salas), teste `atracao_e_novo_jogo` (desde a spec 16: `titulo_sem_demo_e_novo_jogo`, as demos desligadas); ROM igual; espaço por banco e nota para a Chozo |
| 12 | Chozo Ruins (`specs/12-chozo-ruins.md`) | **verificado** (28/10/2026, fechado na 12m): opção B (Tallon intacto; a Chozo com Charge, Varia, mísseis, E-tanks e a expansão de PB, sem artefatos), área 1, as 64 salas, os 3 elevadores de verdade, 31 itens; 12a–12m e 12g2 verificadas; Tallon + Chozo andados juntos em 7 rodadas declaradas (51 itens, 51% pela fórmula do fim) e a cadeia completa no emulador (`cadeia_completa_tallon_chozo`). Decisões de 28/10: a Reflecting Pool fica inundada; a porta de charge branca fica para uma área futura; paredes de míssil = blocos de bomba |
| 13 | Chefes (`specs/14-chefes.md`) | **verificado** (31/10/2026, fechado na 14f): os 4 chefes da Chozo como arenas, cada um com a sua luta de verdade no emulador; **14d verificada** (Incinerator Drone: o míssil do suporte do Burn Dome tranca a porta e gera 2 colmeias + 2 vespas, todas mortas abre; teste `chozo_incinerator_drone`); **14f verificada** (linha "chefes (specs/14)", a cadeia com os 3 atalhos anotados, 82 testes em 5 min 55 s). Histórico: decisões do usuário de 30/10/2026 (os 4 da Chozo; Flaahgra = Spore Spawn; Incinerator Drone = arena; Chozo Ghosts fora) e padrões aceitos registrados no épico; **14a verificada** (Plated Beetle = cópia do Sidehopper grande em `$A0:F83F`, toque 40, cores do Prime, na Ruined Shrine; teste `chozo_plated_beetle`); **spec 15 verificada** (auditoria de entrada de porta de verdade, 8 colocações, testes `entradas_de_porta_*`); **14b verificada** (rotina comum das arenas em `$84:F500`, estado "morto", Hive Mecha = 2 Kagos + 3 Mellas, o míssil aparece; música de mini-chefe também no besouro); **14c verificada** (Flaahgra = Spore Spawn na Sunchamber: fosso no canto, porta cinza tipo 1, a Varia aparece, cores do Flaahgra; a vespa da Nursery corrigida); **próxima: 14d**, depois 14f |
| 14 | Arremates: demos e título (`specs/16-titulo-e-demos.md`) | **verificado** (31/10/2026): demos de atração desligadas (`$8B:9F2C` BEQ → BRA, 2 bytes; `check_orphans` sem exceção: nenhuma sala vanilla carrega, 262 órfãs); logo do título **METROID / PRIME** (`tools/frigate/title.py`: METROID sobe 16 px, PRIME desenhado embaixo no mesmo estilo, gráfico próprio em `$F1:8000` comprimido com o rabo da stream vanilla para carregar no mesmo número de quadros, spritemap `$8C:879D` no lugar); testes `titulo_metroid_prime` e `titulo_sem_demo_e_novo_jogo`; 83 testes |
| 15 | Magmoor Caverns (`specs/17-magmoor-caverns.md`) | **verificado** (01/11/2026, fechado na 17j; seção "Verificação do épico"). Aprovado em 01/11/2026: decisões do usuário — as 29 salas por região (A norte, B centro, C sul); itens como na Chozo (3 mísseis, 2 E-tanks, a expansão de PB atrás da parede de PB, nunca antes da rodada 6; um míssil no lugar do Plasma; nada no do Ice Spreader; sem artefatos); calor só nas 12 salas superaquecidas do Prime; lava de verdade em fossos e lagos, que machuca, nunca no caminho obrigatório sem saída; área 2 (Norfair); nenhum chefe; elevadores de Phendrana/Mines de enfeite e vazios. **17a verificada** (mais `$8F`: `$8F:8ED6–9193` e `$8F:A9E5–AD41`, só órfãs da Norfair, 3817 bytes recuperados no total); **17b verificada** (`areas.MAGMOOR_AREA = 2`, `VANILLA_PAUSE[2]`, `check_magmoor_slot`, calor por área `heat.HEAT_BITS`: a 2 nativa, sem patch); **17c verificada** (`tools/magmoor/rooms.py`: 29 salas, 29 ligações, 1 de chão/teto, mapa 30/80 bytes, travas, cores e calor do Prime como dados, `check_magmoor`, `specs/img/17c-mapa.png`). ROM igual nas três (sha1 `0f5cc669…0653`), 83/83. **17d verificada** (`tools/smlib/lava.py`: tilesets 09 quente / 0A frio com as cores da Magmoor e a porta roxa; lava do SM medida numa ROM de teste, `build.py --teste-17d`; regras da lava no validador; 85/85). **17e verificada** (as salas P0 e P16 da Magmoor, becos; elevadores Chozo P24 ↔ P0 e Tallon P23 ↔ P16; área 2 com mapa "MAGMOOR" e "MAGMOOR / CAVERNS" no continue; rodadas do Tallon e da Chozo iguais; 87/87). **17f verificada** (região A: 8 salas, Save Station A, 5 quentes, 2 mísseis, lava), **17g verificada** (os inimigos da região A, 91/91) e **17h verificada** (região B: 7 salas + a P16 aberta, 3 itens, parede de PB, 2 Violas, Magdolite fora; 93/93). **17i verificada** (região C: 12 salas, as 29 da Magmoor na ROM; portas de onda/gelo do Prime, a de plasma da Plasma Processing de gelo; Save Station B; míssil no lugar do Plasma e o E-tank da Workstation; 3 Mellas, 2 Sovas, 2 Zeelas; bateria dividida em 2 grupos; 96 testes). **17j verificada** (as rodadas das três áreas: 58 itens em 7 rodadas, 58%; `check_epic_magmoor`; a cadeia completa com a Magmoor em 3 testes, `cadeia_completa_parte_1` no grupo A, `_2` e `_3` no B; 98 testes) |
| 16 | Phendrana Drifts (`specs/18-phendrana-drifts.md`) | **verificado** (04/11/2026, fechado na 18n; seção "Verificação do épico"). Aprovado em 03/11/2026. Decisões do usuário: as 56 salas por região (A–E); itens = 9 mísseis, 3 E-tanks, 2 expansões de PB (nunca antes da rodada 6), **o Super Missile do SM no Observatory**, míssil no lugar do Wave e da Gravity, nada no da Boost/Spider/Thermal/artefatos (17 itens, 75%); os dois chefes (Sheegoth = cópia mais dura do Dessgeega em cores de gelo + 2–3 Sidehoppers pequenos na Chapel; Thardus = Bomb Torizo em cores de pedra na Quarantine Cave, portas trancadas até ele morrer; tetos de justiça do épico 14); sem frio, só a Gravity Chamber inundada. **Padrão aceito, a confirmar**: área 4 (Mines na 5, Impact Crater na 0), três caras com neve, Metroid do SM enfraquecido. **18a verificada** (`$8F:8000–8ED3` no `RECLAIMED_8F`, 3796 bytes; `check_reclaimed` aceita dado de sala das demos só com `title.check_demos_off`); **18b verificada** (`areas.PHENDRANA_AREA = 4`, `MINES_AREA`, `IMPACT_CRATER_AREA`, `VANILLA_PAUSE[4]`, `check_phendrana_slot`: listas de FX da Maridia intocadas e nenhuma sala nossa da área 4 as liga); **18c verificada** (`tools/phendrana/rooms.py`: 56 salas, 59 ligações, 8 de chão/teto, mapa 57/80 bytes, travas/cores/neve/água/gelo de plasma/painéis do Prime como dados; `check_phendrana`, `check_no_super_locks`; `specs/img/18c-mapa.png`). ROM igual nas três; A 34/34, B 64/64. **18d verificada** (`tools/smlib/ice.py`: neve no tileset `$01`, ruínas de gelo no `$1C` com os gráficos e a tabela da Chozo, laboratórios no `$1B` com a tabela do tileset 4; porta roxa nas três; neve = os esporos do SM, medida numa ROM de teste, `build.py --teste-18d`; a água da área 4 medida). **18e verificada** (Magmoor P13 ↔ Phendrana P0 e P27 ↔ P29 de verdade, `areas.PHENDRANA`, "PHENDRANA / DRIFTS"; grupo C de testes; rodadas iguais). **18f verificada** (região A: 11 salas + a P0 aberta, Save Station B = estação 1, 4 mísseis `$DA–$DD` na rodada 3, bomb slot = túnel com bloco de bomba, porta de onda da Chapel; A 34/34, B 64/64, C 8/8). **18g verificada** (`tools/phendrana/enemies.py`: Shorelines 3 Zeelas, Ice Ruins Access 2 orbes = cópia do ATOMIC `$A0:F8BF` com vida 100 e toque 20 (`SpeciesCopy.health`), Ice Ruins East 2 Zeelas; `check_phendrana_enemies`: justiça em toda rodada, deriva do orbe a mais de 120 quadros de toda porta, a Chapel livre para a arena, tabela do Prime de B–E com propostas; teste `entradas_de_porta_phendrana`; caminhadas da 18f medidas de novo; sha1 `1c152d18…fb92`; A 34/34, B 64/64, C 9/9). **18h verificada** (o Sheegoth: cópia do Dessgeega `$A0:F8FF` com vida 800 e as vulnerabilidades dele — o feixe sem carga não fere, regra 13 —, toque 40, cores de gelo; 2 Sidehoppers pequenos; arena `KILLS` bit `$08` da área 4; porta cinza de cota de mortes no estado vivo e de onda no morto; o míssil `$DE` no altar, rodada 3; teste `phendrana_sheegoth`; sha1 `81fcea22…acef`; A 34/34, B 64/64, C 10/10). **18i verificada** (região B: 12 salas; Save Station A = estação 2, Map Station; portas vermelhas `$C2`/`$C3`; itens `$DF` PB num nicho com **tampa de plasma dentro da sala** (`RoomDef.caps`, rodada 6), `$E0` E-tank atrás de bloco de bomba, `$E1` míssil da Hydra; **porta de onda vertical** roxa em `$84:FE00`; 9 inimigos (orbes, zoomer, Zeelas, Sidehopper pequeno); `check_niche_caps`, `check_vertical_wave_doors`; testes `phendrana_regiao_b_rota`, `phendrana_save_station_a`, `phendrana_map_station`; sha1 `942db180…5cfe`; A 34/34, B 64/64, C 13/13). **18j verificada** (região C: 5 salas + a P29 aberta; itens `$E2` míssil da Monitor (túnel de Morph, rodada 3) e `$E3` E-tank da Transport Access num nicho de plasma (rodada 6, a sala na 4: portas de gelo); a porta de onda vertical pintada na tabela da neve (`VERTICAL_WAVE_TILESETS`); 5 orbes; regra nova: a porta de Morph do Prime fecha algo na sala; teste `phendrana_regiao_c_rota`; sha1 `4982c9c6…5858`; A 34/34, B 64/64, C 14/14). **18k verificada** (o Thardus: cópia do Bomb Torizo `$A0:F93F` com vida 400 (20 tiros do Power Beam) e o toque dele (8); o código dos Torizos corrigido no lugar: as 7 leituras da área viram 0, sem a bruma, a posição da tabela, paletas e pulso do peito em cores de pedra e neve; acorda quando a sala carrega; condição = o bit `$04` que a morte do Torizo liga, portas L0/R0 cinza de tipo 2 só no estado vivo (`build.arena_door_alive_cap`), bit da arena `$10`; sem prêmio; teste `phendrana_thardus`; sha1 `a7a45deb…5b30`; A 34/34, B 64/64, C 15/15). **18l verificada** (região D: 12 salas + a R0 da Hydra aberta; o **Super Missile do SM** `$E4` no Observatory atrás de bloco de bomba (rodada 3), um super abre a porta vermelha `$C4` da Save Station D (estação 3); porta vermelha WTE ↔ West Tower `$C5` (um bit para os dois lados); E-tank `$E5` e míssil `$E6` da Aether; portas de gelo Research Core ↔ Pike Access (rodada 4); **Metroids** = cópia `$A0:F97F` do Metroid do SM com vida 100, toque comum 20 (sem agarrar), IA de tiro e tabela próprias; regra `chaser_problems` (o Metroid fora da câmera de toda porta); 1 orbe na ALE; testes `phendrana_regiao_d_rota`, `phendrana_save_station_d`; sha1 `88a4a158…6b6e`; A 34/34, B 64/64, C 17/17; `$8F`: 2146 livres na faixa das demos). **18m verificada** (região E: 14 salas, Phendrana com as **56 salas e os 17 itens**; a Gravity Chamber inundada andada sem a suit (escada de rocha), míssil do lugar da Gravity `$E8` (rodada 4) e o da borda `$E9` (Gravity + Space Jump, rodada 5); míssil da Frost Cave `$E7`; Save Station C (estação 4); portas de plasma da Storage Cave; porta de Morph da Security Cave com blocos de Power Bomb dos dois lados, a expansão `$EA` (rodada 6); Beetles e orbes, o Ripper fora; testes `phendrana_regiao_e_rota`, `phendrana_regiao_e_agua`, `phendrana_save_station_c`; sha1 `8e5d3771…f01a`; A 34/34, B 64/64, C 20/20; `$8F`: 1282 livres na faixa das demos). **18n verificada** (as rodadas das quatro áreas: `check_world_rounds` com Phendrana, **75 itens em 7 rodadas, 75%** (energia 1299, mísseis 235, super mísseis 5, power bombs 25); `check_epic_phendrana`; a cadeia completa em **4 partes** (`cadeia_completa_parte_1` no A, `_2` no B, `_3` e `_4` no C) com os 17 itens de Phendrana nas rodadas declaradas, **o Sheegoth e o Thardus vencidos de verdade** (lutas buscadas da entrada da cadeia), uma visita a Phendrana por rodada (3, 4, 5, 6), e no fim **a tela do fim do SM: "YOUR RATE FOR COLLECTING ITEMS IS 75%"** (o evento `$0E` por RAM, o único atalho novo); os roteiros das regiões viraram pedaços reaproveitáveis, idênticos; ROM igual, sha1 `8e5d3771…f01a`; A 34/34 (3 min), B 63/63 (3 min 20 s), C 22/22 (5 min 30 s)). |
| 17 | Phazon Mines (`specs/19-phazon-mines.md`) | **verificado** (10/11/2026, fechado na 19m: as 13 filhas verificadas; as 42 salas, os 13 itens e os 2 chefes na ROM; a cadeia completa pelas cinco áreas com os 2 chefes vencidos de verdade, **88%** na tela do fim; seção "Verificação do épico"). Aprovado em 05/11/2026. Decisões do usuário: as 42 salas por região (A nível de cima, B do meio, C oeste, D de baixo); itens = 9 mísseis, 2 E-tanks, míssil no lugar da Power Bomb, **o Grapple Beam do SM na Storage Depot B** (nenhuma trava o pede), nada no lugar do Flamethrower, do Phazon Suit e dos artefatos (13 itens, 88% no fim); os dois chefes (Phazon Elite = cópia do pirata ninja dourado; Omega Pirate = cópia do Bomb Torizo, imune ao feixe sem carga; sem prêmio); phazon só cor. **Padrão aceito, confirmado pelo usuário em 09/11/2026**: área 5 (lista do mapa no `$81`), as 3 Elite Pirates fora, duas caras (Tourian e Brinstar), grupo D de testes. **19a verificada** (`RECLAIMED_8F` + `$8F:C215–C8C6`, `AD5C–B218`, `A6A1–A97A`, `CAAE–CCC7`; `RECLAIMED_A1` novo com `$A1:AD09–CCD3` e o alocador de populações usando-o depois do fim do banco; `check_reclaimed` nos dois bancos; `demo_rooms_kept`: as salas das demos com o cabeçalho recuperado não são lidas). **19b verificada** (`VANILLA_PAUSE[5]`, `check_mines_slot`; `mapsave.list_at`: a lista da área 5 maior que 21 vai para `$81:EF1A`; achados: máscara da área 5 dividida com a 7, lista de map station da área 5 vazia, calor `$F761` na entrada 0 da lista de paleta). **19c verificada** (`tools/mines/rooms.py`: 42 salas, 43 ligações, 7 de chão/teto, mapa 39 bytes no `$81`, travas (event 15, key 86: gelo 48, plasma 26, onda 12), features, `PB_ONLY` (11 objetos em 10 salas), painel de onda; `research/prime_mines_locks.json`; `check_mines`, `check_no_grapple_locks`; `specs/img/19c-mapa.png`). ROM igual nas três; A 34/34, B 63/63, C 22/22. **19d verificada** (`tools/smlib/mines.py`: base pirata na entrada `$0E` com os gráficos e uma cópia da tabela da Tourian `$0D` — canos no azul do phazon, painéis de aço escuro, fundo `$E454` —, rocha e fungos na `$08` (não `$07`/`$1A`: salas de demo) com os do Brinstar `$06` — rocha cinza, fungo azul, fundo `$BAF4` —, música `$1E/$05`, portas de onda roxas de lado e vertical na linha 7; só a ROM de teste as escreve (`build.py --teste-19d`, área 5 própria com 4 salas), a ROM do jogo igual; `check_mines_in_rom` nas duas ROMs (a de teste feita na memória), `check_mines_test_rooms`; teste `porta_de_plasma_mina` (a porta de plasma da mina abre só com o Plasma) no grupo A; achado: 3 ligações de plasma no chão/teto no mapa, sem porta de plasma vertical, para o usuário; sha1 `8e5d3771…f01a`; A 35/35 (3 min 05 s), B 63/63 (3 min 27 s), C 22/22 (5 min 35 s)). **19e verificada** (Tallon P43 ↔ Mines P0 e Magmoor P26 ↔ Mines P25 de verdade, a Mines embaixo dos dois — a P26 redesenhada descendo —, `areas.MINES` com a lista do mapa de 39 bytes no `$81`, "PHAZON / MINES", as entradas `$0E/$08` na ROM do jogo; lados nas rodadas 5 e 4 como o épico previa, linhas do Tallon e das rodadas iguais; grupo D: `elevador_mines_leste`, `elevador_mines_oeste`, `porta_de_plasma_mina`; 2 testes antigos ajustados; sha1 `b4ede270…63fb`; A 34/34 (3 min 26 s), B 63/63 (4 min 12 s), C 22/22 (5 min 45 s), D 3/3 (30 s)). **19f verificada** (a região A: 13 salas, Save Station A, 3 mísseis, o Grapple Beam do SM na Storage Depot B; 79 itens, 79%, a linha do Tallon igual; `check_mines_locks_mapped`; a parte 4 da cadeia no grupo D; sha1 `92332441…f074`; A 34/34 (3 min 22 s), B 64/64 (4 min 00 s), C 21/21 (2 min 06 s), D 7/7 (4 min 08 s)). **19g verificada** (inimigos da região A: 2 piratas e 2 orbes, a tabela de B–D, `check_mines_enemies` e a regra do que atira; `mines_inimigos_vivos`, `entradas_de_porta_mines`; sha1 `06289783…04fa`; A 34/34 (3 min 29 s), B 64/64 (3 min 42 s), C 21/21 (2 min 05 s), D 9/9 (3 min 58 s)). **19h verificada** (o Phazon Elite: cópia do ninja dourado `$F593` em `$A0:F9BF`, vida 400, toque 40, o feixe sem carga fere, cores de phazon e a paleta do salto em `$B2`; arena de cota de mortes, bit `$08` da área 5, porta de teto cinza até a vitória e de gelo depois; sem prêmio; a sala sem mudança; `check_ninja`; `mines_phazon_elite`; sha1 `18260846…d2d4`; A 34/34 (18 min 24 s), B 64/64 (39 min 32 s), C 21/21 (13 min 26 s), D 10/10 (16 min 32 s), com a máquina muito carregada (carga 40–147, outros processos)). 19i–19l verificadas (as regiões B, C e D, o Omega Pirate; as specs têm os detalhes). **19m verificada** (as rodadas das cinco áreas, `check_epic_mines`, a cadeia em 5 partes com os 13 itens da Mines e os 2 chefes de verdade, 88% na tela do fim; ROM igual; A 34/34, B 64/64, C 22/22, D 18/18). |

## Etapa 7 (feita nesta sessão)

Código em `tools/frigate/ending.py` (Ridley, nave, cores) e `tools/frigate/timer.py` (números do
cronômetro), ligado em `tools/build.py`.

- **Meta Ridley na Air Lock** (não no hangar: os gráficos dele ocupam toda a VRAM de inimigos, e a
  nave precisa de parte). Estados da Air Lock: boss bit 2 → normal; bit 1 → cena; padrão → normal.
  Espécie nova em `$A0:F7FF` = cópia do Ridley de Ceres com init/main próprios em `$A6:FEBC`: init
  pula a checagem "chefe morto → me apago" (`JSL $A6:A10E`), tira o bebê Metroid, encurta a espera
  no escuro, esconde o cronômetro; main troca a luta pelo voo de fuga ($A971) e, quando ele passa
  do teto ($A9A0), apaga o Ridley, liga o boss bit 2 e devolve o cronômetro. As portas de saída da
  Air Lock também devolvem o cronômetro (door ASM), caso a Samus saia antes dele.
- **Nave no hangar** (centro no bloco 54, chão na linha 26), inimigos e colisão da Landing Site.
  Patches em `$A2`: só abre na área 3 depois do chefe; decola na área 3 com o chefe morto (além do
  evento $0E vanilla); alturas de decolagem menores na área 3. Depois vinha o final do SM e créditos;
  desde a spec 05 vem a cena da fuga de Ceres com "TALLON IV" e o pouso na Landing Site (abaixo).
- Cores do Meta Ridley tiradas das texturas do Prime (`research/prime_textures/ridley/`).

## Estado conferido agora

- Specs 07a–07d, **07g** e **07e** verificadas (épico Tallon, `specs/07-tallon-overworld.md`). A 07g
  veio antes da 07e/07f por decisão do líder: 5 salas do MVP do Tallon na área 0 + chegada mínima
  (`specs/07g-salas-mvp-tallon.md`). A **07e** (`specs/07e-chegada-e-perda-de-itens.md`) tira os
  itens na decolagem da fragata (`ending_state_routine`, `$A2:F502`, antes do save do estado `$21`):
  a Samus chega só com o Power Beam, 0 mísseis, 99/99; a nave do Tallon (vanilla) recarrega e salva
  na estação 0 da área 0. A **07f** (`specs/07f-mapa-de-pausa-tallon.md`) fecha o MVP: mapa de
  pausa/minimapa "TALLON" das salas construídas, ícone da nave na Landing Site (o jogo desenha a
  nave da área 0 na entrada 0 da lista de save, `$82:C853`, código fixo em `$82:B6BC`/`$82:B777`),
  sem map station/elevadores/rótulos da Crateria; lista do save da área 0 = 47 bytes (tabela
  inteira do Tallon, não muda quando as regiões entrarem) em +357; `mapsave.layout` agora em ordem
  de build (fragata fica em +327); nome "TALLON / OVERWORLD" na tela de continue.
  A **07j** (`specs/07j-elevadores-de-enfeite.md`) desenhou em `tools/tallon/layouts.py` as outras 4
  salas de transporte (Chozo East/South, Magmoor East, Mines East) e a casca do Artifact Temple
  (pirâmide de degraus, sem teleporte/Ridley), com o elevador de enfeite numa função só
  (`elevator()`, que a Chozo West também usa, bytes iguais). **Não estão na ROM**: entram quando a
  região delas for ligada (B/C na 07k, E na 07m). O validador já confere o alcance delas (cada região
  sozinha) e, em toda sala a pé, que nenhum lugar alcançável fica sem volta a uma porta
  (`reach.stuck`). Prévia: `python3 -I tools/preview_rooms.py --rascunhos-tallon` →
  `specs/img/07j-sala-*.png`. Sem ícone de elevador no mapa (só aparece com elevador usado).
  A **07k** (`specs/07k-regioes-b-e-c.md`) ligou as regiões B e C (15 salas; Gully/Alcove fora) com
  as travas do Prime, sem acesso provisório: `GATES` em `tools/tallon/rooms.py` (escudo de míssil =
  porta vermelha `$C88A…` com bit `$B0–$B2`; gelo/plasma = cinza tipo 4, nunca abre, provisória;
  Space Jump = borda alta), fases `TIERS` e `FIRST_TIER` (em que fase cada sala fica alcançável). O
  validador anda sala a sala por fase (`check_tallon_tiers`), confere que borda de Space Jump não se
  alcança a pé, que os blocos de tampa fechada contam como sólidos (`foot_grid`) e os PLMs na ROM
  (`check_gates`). Alcançáveis agora só com o Power Beam: as 5 do MVP + Temple Hall, Temple Security,
  Waterfall Cavern, Root Tunnel (até a porta vermelha). Fontes de cada trava (dados do Prime ou
  conhecimento, com os incertos) na tabela da spec.
  A **07h** (`specs/07h-itens-tallon.md`) pôs os itens das salas construídas: tabela
  `tools/tallon/items.py` com os 13 itens SM do Tallon (bits `$A0–$AC`, fixos; vanilla usa 0–154), 6
  Missile Expansions na ROM (Landing Site fase 0, Crash Site 0, Transport Tunnel B 0, Root Cave 2,
  Overgrown 3, Arbor 4). **Impasse dos mísseis**: o míssil da Landing Site fica no fundo do lago, a pé
  (desvio: no Prime pede Morph Ball); com ele as portas vermelhas abrem e as 6 salas atrás delas
  entraram na fase 0 (`FIRST_TIER`; alcançáveis agora: 15). O validador anda as fases pegando itens
  (`tallon_tiers`) e confere lugar/fase/bit/PLM (`check_tallon_tiers`, `check_tallon_items`). Corrigido
  bug da 07g: câmera das estações do Tallon em x 576 desenhava todo PLM animado 64 px à esquerda
  (`bg1_x_offset`, `$84:91DC`); agora x em tela inteira (512).
  A **07i** (`specs/07i-inimigos-tallon.md`) pôs os inimigos da camada 0 do Prime nas salas construídas
  (`tools/tallon/enemies.py`, `TALLON.enemies`; contas lidas de `research/prime_fs` por camada, tabela
  `PRIME_LAYER0`), no máximo 1 por tela: Beetle → Sidehopper pequeno `$D93F` (o grande do épico tira 80
  por toque: recusado), Geemer → Geemer `$DCFF`, Parasite → Zeela `$DC7F`, Blood Flower → Cacatac
  `$CFFF` parado; Chubb/Snake Weed fora. 27 inimigos em 7 salas (Canyon Cavern 2, Tallon Canyon 7,
  Tunnel A 2, Root Tunnel 1, Root Cave 6, Tunnel B 3, Tunnel C 4), paletas 1/2/3/7 fixas por espécie,
  set "TALLON ". Validador: caixa inteira do inimigo no ar e na sala (`check_enemies`), set ≤ 4
  espécies/paletas/VRAM ≤ `$2000` (`$1C00` na fragata, por causa do cronômetro) (`check_enemy_sets`),
  ROM = tabela (`check_enemies_in_rom`), contas do Prime e justiça da fase 0 — morre com ≤ 5 tiros do
  Power Beam, toque ≤ 20 (`check_tallon_enemies`).
  A **07l** (`specs/07l-regiao-d-fragata-afundada.md`) ligou a região D (14 salas, tileset 4 da fragata com
  o fundo dela; Hydro Access em caverna), **inundada** (FX de água em toda a sala, `build.WATER_FX`,
  `RoomDef.water`; seca só a Transit Hall), fiel e **inalcançável agora**: porta de gelo da Frigate Access,
  Gravity Suit (anteparo de 4 blocos na Vent C: o pulo debaixo d'água sem a suit sobe 51 px = 3 blocos) e
  portas de condutor (Thermal + Wave = cinza "nunca abre": Reactor Core↔Access, Access↔Cargo Lift dos dois
  lados; Cargo Lift, Biohazard, Biotech só do lado deles). Fases: nova 4 "+ Gravity Suit, Wave Beam, Thermal
  Visor" (a antiga 4 virou 5: Arbor). `reach.py` tem o pulo na água medido (`WATER_*`, com e sem a suit;
  sem Space Jump na água sem a suit, `sm_90.c:1915`); o validador anda as salas inundadas com o pulo certo
  (`room_loadout`, `check_tallon_water`) e confere a água na ROM (`check_water_in_rom`). Estação de save P28
  = **load station 1 da área 0** (Savestation, ícone no mapa de pausa; estado único: o "Save Disabled" é só
  da fragata). Itens: E-tank Cargo Lift (`$A7`), míssil Biohazard (`$A8`), E-tank Hydro Access (`$A9`), fase 4.
  Inimigos: Wall Crawler = HZOOMER (Vent A), Space Pirate = `$F653` (Elevator Beta), **Gun Turret = Rinka
  `$D23F`** (4 na Biohazard, paleta 3); Spank Weed fora; Jelly Zap/Drone só em camadas de evento.
  Portas verticais (spec 08, regra única `build.door_push` para todas as áreas): descer usa `$0140`
  (`DOWN_PUSH`; o padrão `$8000` afundava a Samus 7 px na borda da linha 6 e ela não andava: era assim nas
  14 portas de chão da fragata), subir `$0240` (`UP_PUSH`) e subir para sala inundada `$0340`
  (`UP_PUSH_WATER`; com `$0240` ela caía de volta). O validador confere a regra em toda entrada de porta
  (`check_door_push`).
  A **07m** (`specs/07m-regiao-e-grande-arvore.md`) ligou a região E (8 salas) e Gully/Alcove (região A):
  **44 salas na área 0** (`ACTIVE_ROOMS = None`). Travas fiéis nos mecanismos de sempre: Canyon → Gully =
  Bombas (blocos quebráveis nos dados) = **cinza na porta de teto T3** da Canyon; as portas da Gully (L1) e
  da Alcove (L0) na Landing Site ficam numa **câmara no alto do penhasco oeste** (borda de Space Jump; a Gully
  sobe até ela, um ressalto 15 blocos acima do chão desce para a nave); região E: portas de cor (`Key` nos
  dados) = gelo = cinza dos dois lados (GTH↔Tunnel D/E, Tunnels↔transportes, GTH↔Life Grove Tunnel); a porta
  da Great Tree Chamber (R1 do GTH) é borda de Space Jump; o caminho do Life Grove pede ainda Spider/Boost/
  Power Bombs (só no passeio por fases). Hydro Access B2 ↔ GTH T0 aberta (poço sob os degraus, agora de 1
  bloco). Fases: a 1 virou "+ mísseis, Morph Ball, Bombas", nova **5 "+ Spider Ball, Boost Ball, Power
  Bombs"**, a antiga 5 virou 6 (Arbor). `FIRST_TIER`: Gully/Alcove 1, E 4 (LGT e Life Grove 5); alcançáveis
  agora: 15 (igual). O passeio por fases deixa a **geometria decidir os itens de movimento** de uma trava (a
  Alcove, que dá o Space Jump, se alcança pela borda vinda da Gully); a regra da borda vale para entradas que
  não estão numa borda; tampa de porta de teto não vira sólida no modelo a pé. Itens: **Space Jump** na Alcove
  (`$A1`, fase 1: o míssil da Root Cave foi da fase 2 para a 1), mísseis da Great Tree Chamber (`$AA`, 4) e
  do Life Grove Tunnel (`$AB`, 5), **X-Ray** no Life Grove (`$AC`, 5): os 13 itens SM do Tallon na ROM.
  Inimigos: Seedling = **Cacatac andando** (`seedling`, p2 `$0301`, ±64 px; mesma espécie/paleta da Blood
  Flower: o enemy set lista a espécie uma vez, `set_species`; o validador confere o chão do caminho inteiro):
  GTH 4 Seedlings + 2 Blood Flowers, Tunnel D 2, Tunnel E 3; Gully 3 Zeelas. Jelly Zaps fora (o lago do GTH
  fica seco; nenhuma água nova). No GTH a ordem das portas segue o mapa da 07d (Hydro no teto), não o Prime.
  A **09a** (`specs/09a-portas-de-feixe.md`) trocou as 26 cinza "nunca abre" de gelo (18), onda (7, as de
  condutor) e plasma (1) por **portas de feixe** (`tools/tallon/beamdoors.py`): PLM próprio em `$84:F10F`
  (462 bytes): 3 pré-instruções = cópia de `$84:BD88` com `AND #$0F00|m / CMP #m` (gelo `$2`, onda `$1`,
  plasma `$8`), 6 blocos feixe × lado (23 bytes de fechar copiados da cor + lista de 27) e 6 cabeçalhos
  (`$C7B1`, lista, fechar). PLMs: gelo R/L `$F2B9/$F2BF` (verde), onda `$F2C5/$F2CB` (cinza; roxa desde a 10d), plasma
  `$F2D1/$F2D7` (laranja); argumento `$8000` (fecha a cada visita). `LOCK_OF` ice/wave/plasma; cinza só na
  T3 da Canyon (Bombas, 09d). Thermal, grapple, X-Ray (trava), Spider, Boost saíram de `GATES`/`TIERS`
  (fase 4 "+ Gravity, Wave", 5 "+ Power Bombs" sem trava ainda, 6 "+ plasma"); Life Grove Tunnel, Life Grove
  e os 2 itens deles: fase 5 → 4. `check_gates` confere PLM/argumento de cada tampa de feixe, cinza só na de
  Bombas e os bytes do `$84` contra o que `beamdoors` gera da ROM base. Para o jogador nada muda ainda: os
  feixes como item chegam na 09b.
  A **09b** (`specs/09b-itens-de-feixe-e-gravity.md`) pôs as 7 linhas de trava em `tools/tallon/items.py` (bits
  `$AD–$B3`, linhas 13–19) e o lugar de 4: **Ice** `$EEEF` na prateleira da porta da Arbor na Root Cave (4, 9),
  `$AD`; **Wave** `$EEFB` no chão da Magmoor East (9, 25), `$AE`; **Gravity Suit** `$EF0B` na plataforma do
  elevador da Chozo East (12, 25), `$AF`; **Plasma** `$EF13` no chão da Chozo South (6, 25), `$B0`; Morph `$B1`,
  Bombas `$B2`, Power Bomb `$B3` sem lugar (09d/09e). `GRANTS` dos 7. O passeio usa os itens achados: na fase 1,
  Space Jump → gelo → Gravity (+ o Wave da fase 0) → D, E, Plasma → Arbor: `FIRST_TIER` das 27 salas das fases
  3/4/6 → 1 (fases 2–6 sem sala até as rodadas da 09f); alcançáveis agora 15 (igual), itens na fase 0: 4.
  `tallon_tiers` registra o que a Samus tem ao chegar a cada sala; `check_tallon_water` usa isso (só a Vent C sem a
  suit). Coleta do SM: só Spazer e Plasma se excluem; Wave → Ice → Plasma dá `$B` e abre todas as portas de feixe.
  **Cena da Gravity Suit**: a vanilla põe a Samus no meio da tela (`$91:D64E`), dentro da parede da Chozo East
  (presa para sempre, medido); `items.gravity_patch` troca 2 bytes (`80 18`) e ela fica onde pegou (o facho de
  luz continua no meio da tela). `check_tallon_items` confere os bytes.
  A **09c** (`specs/09c-banco-de-salas.md`) separou a expansão (ROM base 3 MB, `$80–$DF`; o build expande para 4 MB,
  cabeçalho `$FFD7 = $0C` já diz 4 MB) em dois alocadores (`build.ExpandedAllocator`): **nível** `$E0:8000–$EF:FFFF`
  (`LEVEL_BANKS`, só os 72 níveis, em ordem; um nível pode cruzar banco: o descompressor `$80:B119`/`$80:B271` passa
  ao banco seguinte em `$80:B266`, conferido nos bytes; vanilla `$8F:ADAD` `$C7:FF02→$C8:8531`) e **fixo**
  `$F0:8000–$FF:FFFF` (`FIXED_BANKS`, cada blob num banco: TALLON IV `$F0:8000`, estrelas do hangar `$F0:8FB1`/`$F0:90B1`,
  paleta do tileset 4 `$F0:A0B1`, Parasite Queen `$F0:A16A`). Crescer o nível não move mais nada. `check_banks` no
  validador (ponteiros de todo estado → bytes do nível da sala, fixos pelos ponteiros da ROM, sem sobreposição, sem
  DMA cruzando banco, livres e aviso de nível cruzando). Modo de teste `python3 -I tools/build.py --cruzar-banco SALA`
  (enche o começo do nível para SALA cruzar a divisa; grava em `build/`: depois rodar o build normal); o
  `tests/run_tests.py` gera `nivel_cruza_banco_<sala>` (nível na WRAM = o da sala, Samus parada) para cada nível que
  cruza banco: nenhum no build normal; experimento com o hangar 47/47, com a Tallon Canyon passa.
  A **09d** (`specs/09d-morph-e-bombas.md`) pôs a **Morph Ball** (`$EF23`, bit `$B1`) na plataforma do elevador da Chozo West
  (8, 25) e as **Bombas** (`$EEE7`, `$B2`) no chão do Artifact Temple entre os totens (13, 53); a cinza da T3 da Tallon Canyon
  saiu: **túnel de Morph** de 1 linha na plataforma (teto em (53,3–4) e (54,4)) com **2 blocos de bomba** em (53, 5) e (54, 5)
  (tipo F, metatile CRE `$058`, BTS 4 = não volta; BTS 0 volta em ~380 quadros: medido), depois a câmara sob a porta (desfaz a
  bola) e a T3 = passagem aberta. Trava Canyon↔Gully = `{morph, bombs}` atrás de geometria (`GEOMETRY` no lugar de `MOVEMENT`;
  sem tampa cinza no Tallon). Modelo (`reach.py`): estado de **bola** (rola ±1, cai, vira bola onde está de pé, desfaz só com 3
  linhas; sem pulo/bomb jump), blocos de bomba ar só com as Bombas (`with_bombs`), flood fill exige a Morph. Validador: regra da
  borda geral (entrada atrás de geometria anda com ela; porta atrás de geometria fora de alcance sem os itens, cada item a pé
  necessário sozinho, alcançável com eles), toda sala a pé andada também com Morph + Bombas (sem lugar sem volta),
  `check_breakables` (bloco do projeto, sala com trava de Bombas, dá para bombá-lo), `check_tallon_return` (em cada rodada = volta
  do passeio da fase 0, de toda sala/entrada alcançada há volta à nave), justiça dos inimigos pela chegada (Power Beam, mísseis,
  Morph), passeio cacheado por `check()`. **Alcançáveis agora: 15 → 44**; os 19 itens com lugar na fase 0, nas rodadas do épico
  (0: Morph; 1: Bombas, Wave; 2: Space Jump; 3: Ice; 4: Gravity; 5: D, E, Plasma, X-Ray no chão aberto; 6: Arbor).
  A **09e** (`specs/09e-power-bombs-e-xray.md`) pôs a **Power Bomb** (`$EEE3`, bit `$B3`) no chão da Mines East (6, 25) e cercou o
  X-Ray do Life Grove com uma **cabana de 15 blocos de Power Bomb** (paredes nas colunas 37 e 43, linhas 26–29, teto na linha 25,
  colunas 37–43; `layouts.xray_hut`): **tipo C, metatile `$057`, BTS `$09`** (não volta; BTS `$08` volta ~450 quadros depois: medido;
  o tipo F é o bloco de bomba). Modelo: `Loadout.power_bomb`; `reach.with_breakables(types, bts, loadout)` (era `with_bombs`): bloco
  de PB ar só com Morph + Power Bomb, sólido sem (nunca o "ar" das tampas tipo C); `foot_grid(r, l1, bts, …)`. Validador:
  `LOADOUT_FIELD`/`with_items` (item → campo do `Loadout`), `FOOT_GEOMETRY` + PB, sala com blocos de PB andada também com a PB,
  `check_breakables` cobre os blocos de PB (`$057`/`$09`, sala com item que peça PB, bola a ≤ 2 blocos), novo `Item.needs` (X-Ray =
  Morph + PB) com **`check_item_geometry`** (com os itens pega de toda porta; sem qualquer um, não). Rodadas: 5 pega a PB, **6 o
  X-Ray** (e Arbor): **20 itens**, igual ao épico (o passeio dá uma volta 7 vazia: o `xray` que o X-Ray dá não abre nada; 09f decide).
  A **09f** (`specs/09f-rodadas-e-cadeia-completa.md`) trocou as fases hipotéticas (`TIERS`/`FIRST_TIER`/`Item.tier`) por **rodadas
  declaradas**: `FIRST_ROUND` (`tools/tallon/rooms.py`) e `Item.round` (`items.py`); `validate.tallon_rounds`: rodada 0 só com o Power
  Beam, rodada k com os itens pegos nas anteriores; **para na primeira volta sem sala nova e sem item novo** (essa volta, a do `xray`,
  não é rodada nem erro). `check_tallon_rounds` compara sala e item com o declarado (mensagem com a rodada achada e o equipamento);
  `check_tallon_round_stuck`: em cada rodada, de cada (sala, entrada) alcançada, com o equipamento dela, nenhum lugar sem volta a uma
  porta que ela possa usar (com Space Jump é o flood fill: só as rodadas 0–2 e a Vent C sem suit são andadas). Caminhamento de sala
  memorizado por `check()` (`tallon_room_walk`; `reset_tallon_cache()` em roteiros de mutação): validate de ~7,9 s para ~3,3 s.
  Teste `tallon_cadeia_completa` (~200 s, o mais longo): do fim da fragata, os 20 itens na ordem das rodadas, cada um pego andando,
  cada trava aberta de verdade (3 portas vermelhas com mísseis, blocos de bomba, **subida da Root Cave com o Space Jump**
  (`ROOT_CAVE_CLIMB`, medida), portas de gelo, anteparo da Vent C, porta de onda, cabana de PB, porta de plasma); atalhos anotados
  (teleporte de porta só por portas abertas, Samus posta diante de portas/itens, munição e energia por RAM, volta à nave por RAM); no
  fim os 20 bits, salva, game over, continue. Épicos **07 e 09 `verificada`**.
  O **épico 10** (`specs/10-polimento-tallon.md`, 26/10/2026) auditou o Tallon no emulador (roteiros no scratchpad da sessão,
  `s10/`: foto de cada tela das 44 salas montada por sala, as 88 entradas de porta com a Samus parada, a subida pelas 16 portas de
  teto secas) e fechou 4 filhas: **10a** (só testes) `door_teleport` põe a câmera na tela da porta: o BG1 fica em tela inteira
  (sem item/tampa em dobro) e o teleporte para cima por porta de teto troca de sala; o A do `tallon_first_missile` vem 60
  quadros depois e fecha a caixa (teste novo `teleporte_de_porta_alinhado`). **10b** `build.UP_PUSH` `$0240` → `$02A0`: subindo
  e guiando para a borda do outro lado do buraco, as quedas de volta caem de 54 para 28 em 160 (sobram as que partem do quarto de
  fora da porta; `$02E0`+ quebra a fuga da fragata, tampa fechando atrás não segura; teste `sobe_porta_de_teto_pela_borda_longe`).
  **10c** `pausemap.solid_screens`: tela inteira de rocha fica fora do mapa e as vizinhas ganham parede (16 telas no Tallon, a
  Vent A da fragata); máscara e lista do save iguais; `check_map_shapes` lê o tilemap da ROM; teste `mapa_com_a_forma_da_sala`.
  **10d** porta de onda **roxa**: cópia da verde com 8 metatiles próprios (`$3F0–$3F7`) numa cópia da tabela do tileset 4 e a linha
  de paleta 6 (sem uso no tileset 4) pintada; `$84` 462 → 600 bytes; validador confere paleta, tabela e que nenhuma sala usa os
  metatiles (`check_wave_paint_free`); `porta_de_onda` confere a cor na WRAM. Inimigos: nenhum dano inevitável na entrada (o
  pirata do Elevator Beta acerta a Samus parada em 1 s, mas atirando logo ela o mata sem perder energia); salas vazias seguem a
  camada 0 do Prime (mudar isso é decisão do usuário).
  A **etapa 11** (`specs/11-limpeza.md`, 26/10/2026) auditou as salas vanilla pelos bytes (`tools/smlib/roomgraph.py`: sala só
  carrega por entrada de porta; portas pelos BTS dos blocos tipo 9; 262 salas na ROM base, o `research/sm_rooms.json` tem 250).
  Entradas do jogo (novo jogo `$82:F70F` → 3/0, fim da fragata `$82:8035` → 0/`$12`, saves 3/1 e 0/1, nave 0/0, game over = SRAM;
  debug só com `$7E05D1`, que nada liga): exatamente as 72 salas nossas. **Única sala vanilla que o jogo ainda carrega: as demos de
  atração** (título parado ~2900 quadros: 19 salas da Crateria, Brinstar, Norfair, Wrecked Ship e Maridia, iguais às da ROM base menos o
  minimapa do HUD, que desenha a nossa área; a demo enche os bits de item `$7ED870…` com `$FF` na WRAM, um novo jogo logo depois começa
  limpo). Bits vanilla: itens 0–`$9A`, portas até `$A9`; nenhuma sobreposição com `$A0–$B3`/`$B0–$B2`. Validador: **`check_orphans`**
  (salas alcançadas = manifest; estação usada sem porta; `DEMO_SCENES` = tabela e bytes da base; dados vanilla que nossas salas usam só
  na `VANILLA_SHARED`, iguais à base; linha "órfãs: …" com os bytes que só órfãs usam), `vanilla_door_bits`/`vanilla_item_bits` pelos
  bytes; `build.FREE_8F/83/A1/B4`. Teste `atracao_e_novo_jogo`. ROM igual. Decisão do usuário sobre as demos (deixar, desligar
  ou gravar novas): **desligar**, feito na spec 16. Espaço recuperável (só documentado): `$8F` 20637, `$83` 9356, `$A1` 24030, `$B4` 4017 bytes.
  A **etapa 12** (`specs/12-chozo-ruins.md`, 26/10/2026) começou pela pesquisa: Chozo do Prime = 64 salas, 68 ligações (136 docks), 3 saves,
  1 map station, 4 elevadores (destinos lidos dos bytes: North ↔ nossa `tallon_transport_chozo_west`, East ↔ `…_chozo_east`, South ↔
  `…_chozo_south`, Magmoor North sem par); 35 itens (Morph, Bombas e **Ice** — os três já no Tallon pelo épico 09 —, Missile Launcher,
  Charge, Varia, Wavebuster, 1 PB, 19 mísseis, 5 E-tanks, 3 artefatos; **Wave, Boost e Spider não são da Chozo**, são de Phendrana);
  5 regiões A–E (~202 telas). **Decisão pendente do usuário**: (A) devolver Morph/Bombas/Ice à Chozo e refazer o Tallon, (B) Tallon
  intacto e a Chozo com Charge/Varia/mísseis/E-tanks e travas novas (**recomendada**), (C) B + o Morph na Ruined Shrine. Outras perguntas
  no épico (área, travas novas, elevadores, chefes, artefatos, água, tileset 0C, tamanho, demos). Implementadas só as filhas independentes:
  **12a** `build.RECLAIMED_8F` = `$8F:D4EF–DD57` e `$8F:DD59–DDBD` (2254 bytes de 38 salas órfãs de Maridia/Tourian, sem o cabeçalho
  `$DD58` que o código compara), o `Allocator` usa first fit depois do espaço livre, `put_at` guarda os cabeçalhos condicionais,
  `build.ROOM_PTR_COMPARED` (8 cabeçalhos que `LDA $079B; CMP #` compara, lidos dos bytes), `validate.check_reclaimed` (só dado de sala
  órfã, nada de demo/`VANILLA_SHARED`/código, nada nosso num endereço comparado, só estruturas nossas escritas ali); hoje nada vai para lá
  (ROM igual); numa cópia com o `FREE_8F` encurtado 1547 bytes (21 cabeçalhos) foram ao bloco e os 53 testes passaram. **12b**
  `areas.CHOZO_AREA = 1` (a confirmar), `build.VANILLA_PAUSE[1]` (Brinstar, lido dos bytes), `check_vanilla_pause` (todas as entradas
  contra a ROM base) e `check_chozo_slot` (área livre, 0–4, SRAM: 876 livres, lista ≤ 80 no lugar).
  A **12c** (`specs/12c-grafo-e-mapa-chozo.md`) fez a planta da Chozo sem construir sala: `tools/chozo/rooms.py` (`TABLE` 64 salas com
  chave `chozo_*`, tamanho pela regra do Tallon = 202 telas, `LINKS` 68, `REGIONS` A–E do épico, `ROOMS = []`, `ALL_ROOMS` em caixas
  provisórias), disposição achada por recozimento (script descartável `s12c/layout_sa.py`): **15 ligações de chão/teto, 41/80 bytes de SRAM**;
  travas do Prime como dados, **sem item SM**: `DOCK_LOCKS` (51 docas: missile 14, key 23 = porta de cor, morph 8, event 8, one_way 1) e
  `FEATURES` por sala (spider, bomb_slot, breakable, halfpipe, grapple, heat, water, lava, morph_door), lidos dos objetos do Prime por
  `tools/dump_prime_locks.py` (venv) → `research/prime_chozo_locks.json` (docas do JSON estão no espaço da sala: precisam do `transform`).
  Validador `check_chozo` (Prime × tabela × travas, mapa inteiro e por região, cota); prévia `--mapa-chozo` → `specs/img/12c-mapa.png`.
  A **12d** (`specs/12d-estilo-das-ruinas.md`): `tools/smlib/ruins.py` (`RUINS` = tijolos do 0C, peças da linha de paleta 7 das salas
  `$DA2B/$D7E4/$D72A`; **`SANDSTONE`** = as 15 cores da linha 7, a única tabela a mudar se o usuário quiser outra cor); o build grava a paleta
  do 0C com essa linha numa cópia no alocador fixo (último blob, `$F0:DDB7`) e aponta a entrada do 0C para ela; `ruins.check` e
  `check_ruins_in_rom` (paleta = definida, gráficos/metatiles vanilla, nenhuma sala nossa fora da Chozo nem das demos usa o 0C); prévia
  `--estilo-ruinas` → `specs/img/12d-*.png`; foto do emulador `specs/img/12d-emulador-D78F-antes-depois.png`.
  A **12e** (`specs/12e-elevadores-de-verdade.md`, **verificada** depois das decisões do usuário): os três transportes do Tallon para a
  Chozo (West, East, South) são **elevadores de verdade** para a área 1, como os vanilla (`$9938` ↔ `$9AD9`, lidos dos bytes):
  `RoomDef.elevator` = `Elevator(x, row, up)` (`tools/frigate/rooms.py`); a lista de portas segue depois das portas com a **saída** (flags
  `$C0` = elevador + troca de área, orientação 2/3, sem empurrão, câmera na plataforma do outro lado) e a **plataforma** (cópia nossa da
  entrada sem sala `$83:88FC`: sólida, liga `elevator_flags`); `level()` põe os 4 blocos `$90FF`; a população começa pelo inimigo
  **`$D73F`** (p1 0 desce / 1 sobe, p2 = altura da sala + 64 / `$0018`), sem entrada no set. Pares em `tools/areas.py ELEVATORS`.
  Tallon: `layouts.elevator(..., ride=True)` abre os 2 blocos do meio da plataforma e o poço até a última linha (Magmoor East e Mines
  East continuam de enfeite). **Chozo** (`tools/chozo/layouts.py`, novo; `AreaDef CHOZO`, área 1, `AREAS = [FRIGATE, TALLON, CHOZO]`): as
  3 salas de elevador (P0, P62, P63, 1×2) em arenito (tileset 0C), **becos** (a porta da tabela fica fechada até a vizinha existir:
  12f/12l), salão na tela da porta futura, poço da linha 0 até a plataforma (x 128); fundo = lista nossa `0A00 0000` (limpa o BG2: preto),
  música `$0F/$05` provisória; estação 0 = chão ao lado da plataforma da North; mapa/minimapa "CHOZO"; lista do mapa salvo = a tabela
  inteira (41 bytes) em **+404** (SRAM 445/1280); o ícone de chefe vanilla da área 1 (Kraid) sai. **Morph** (8, 25) → **(12, 25)** (ao
  pé dos degraus, a leste da plataforma) e **Gravity** (12, 25) → **(10, 21)** (último degrau, ao lado da plataforma); rodadas iguais.
  Validador: os 2 blocos da plataforma contam como sólidos (`elevator_solid`), a plataforma é entrada e saída no `reach_on_foot`
  (`reach.stuck(..., exits)`), `check_elevators` (pares do Prime `PRIME_ELEVATORS`, áreas, sentido, blocos e poço; linha "chozo (specs/12e)
  …" com as rodadas 0/4/5 do lado do Tallon; a Chozo fica **fora das rodadas do Tallon**), `check_elevators_in_rom`. Emulador: o elevador
  só parte com ↓/↑ num quadro com `$0E16` ligado — liga quando ela **anda ou cai** na plataforma (não posta por RAM nem depois de estação);
  em cima dos 2 blocos fica ligado sempre, na borda (meio corpo no bloco sólido) um quadro sim, outro não (vanilla igual). A cor: a linha
  7 da paleta numa sala da Chozo é exatamente `SANDSTONE` (o oliva da 12d era FX da sala da Maridia): nada a corrigir.
  A **12f** (`specs/12f-regiao-a-chozo.md`, **verificada**): a região A da Chozo (12 salas, `chozo/rooms.py ACTIVE_REGIONS = {"A"}`,
  desenhos em `chozo/layouts.py`); a North abre para a Ruins Entrance. Travas do Prime com itens do Tallon (`GATES`): Main Plaza →
  Ruined Shrine Access = vermelha (bit `$B3`, rodada 1); Main Plaza B0 → Piston Tunnel = túnel de Morph (rodada 1); Shrine → Tower
  Access → Tower → Tower Chamber = **portas de onda roxas no tileset 0C** (linha 5 da paleta e metatiles `$3F0–$3F7` numa cópia da
  tabela de metatiles do 0C, `beamdoors.RUINS_PAINT_LINE`; rodada 2); Main Plaza T1 → Plaza Access = **mão única** (`ONE_WAY_DOORS`:
  cinza "nunca abre" do lado da praça, gate `one_way`; a Plaza Access espera a região B, `WAITS_FOR`). Portas para B/C = parede:
  Nursery Access L0, Plaza Access R0, Ruined Fountain Access R0, Piston Tunnel R0. Itens (`tools/chozo/items.py`, bits `$B4–$BA`):
  6 mísseis (Plaza meio-tubo/gancho com Space Jump, árvore com Power Bomb, Shrine chão (o Morph do Prime), meio-tubo, túnel com bloco
  de bomba) e o E-tank da borda da mão única; rodadas 1, 2, 3 e 6. Fundo `$8F:E25A` (linha 6 do 0C em arenito escuro,
  `ruins.SANDSTONE_BACKGROUND`), música `$1B/$05`. Sem save/map station (P22/P34 são da região B, 12i). Validador: o passeio das
  rodadas anda **Tallon + Chozo juntos** pelos elevadores (`ELEVATOR`, `world_rooms`, `world_items`), a linha do Tallon conta só o
  Tallon; `check_chozo_rounds` (linha "chozo (specs/12f …)"), `check_bombed_items(_in_rom)`. **Achado do motor**: item varrido por
  Power Bomb cria um PLM morto com o índice do bloco do item; com um slot mais alto livre o toque da Samus acha o morto e não pega o
  item até a sala recarregar (`sub_84EEAB`): o item da Power Bomb da Chozo vai primeiro na lista de PLMs; o X-Ray do Tallon tem o
  risco latente (não mexido).
  A **spec 13** (`specs/13-power-bomb-apaga-item.md`, **verificada**) corrigiu esse achado no motor: a busca do toque no item
  (`$84:EEAB`, `sm_84.c:2882`) comparava só o índice de bloco, e um slot morto (cabeçalho 0, deixado por `PlmInstr_Delete $84:86BC`;
  a bomba/PB no bloco do item cria um: `$94:9E2E` → PLM `$B62F`, lista `$84:AAE3` = Delete) acima do item roubava o toque. Agora
  `$84:EEB7` = `JSR $FFDF` + `BRA $EEC4` e a rotina em `$84:FFDF–FFFF` (33 bytes, `tools/smlib/itemtouch.py`) procura primeiro um slot
  **vivo** com o índice e, sem ele, faz a busca vanilla (`BRK` sem nenhum, como antes); `itemtouch.check` no validador. O X-Ray do Life
  Grove **não era afetado** (medido: é o único PLM da sala, slot 39). Teste `power_bomb_nao_apaga_item` (Overgrown Cavern: abre a porta
  leste, PB a 4 blocos do míssil, o morto no slot 38 com o índice do míssil, atalho por RAM: o slot 39 termina; o míssil é pego; na ROM
  antiga, não). A varredura da PB vai até `$FA` px (a caixa `$86` da 12f é só a 1ª fase): a ordem da 12f e `check_bombed_items` ficam,
  redundantes (decisão do usuário).
  A **12g** (`specs/12g-itens-e-travas-novas.md`, **verificada**): **Charge Beam** `$EEEB` (bit `$BB`) e **Varia Suit** `$EF07` (bit `$BC`)
  como linhas 7 e 8 de `tools/chozo/items.py`, **sem lugar** (Watery Hall/região D, Sunchamber/região C); `GRANTS` `charge`/`varia`
  (`tools/tallon/rooms.py` `CHARGE`, `VARIA`, `LOCK_OF`, `BEAM_LOCKS`); `varia_patch` (`$91:D576`, como a Gravity). **Porta de charge**
  (`tools/tallon/beamdoors.py`, depois da pintura da onda: ids antigos iguais): pré-instrução `AND #$0F10 / CMP #$0010` (tiro carregado =
  `equipped_beams & $100F | $8010`, `sm_90.c:3490`), cópia da porta amarela (`CHARGE_COLOUR`), PLMs `$F3F5`/`$F3FB`, argumento `$8000`.
  **Calor** (`tools/chozo/heat.py`, `RoomDef.heat`, `chozo/rooms.py HOT_ROOMS` vazio, `heat_gates`): o objeto de FX de paleta `$F761`
  da Norfair (pré-instrução `$8D:E379`: ¼ de energia por quadro sem `$0021`) na entrada 4 da lista da área 1 (`$83:AC8E`); sala quente =
  FX `HEAT_FX` com o bit 4; **modelo: sem a Varia não entra** (toda porta para sala quente com `varia` na trava). Validador
  `check_heat`, `check_heat_in_rom`, linha "chozo (specs/12g): …". **ROM de teste** `python3 -I tools/build.py --teste-12g` →
  `build/teste-12g/` (`tools/chozo/testrooms.py`: a Ruined Fountain Access quente, porta de charge, os dois itens); o `run_tests.py`
  constrói essa ROM antes de `porta_de_charge` e `sala_quente`. Medido: sem suit −60 de energia em 240 quadros; **com a Gravity só, 0**
  (o SM protege com Varia **ou** Gravity: decisão aberta); a cena da Varia deixa a Samus onde pegou.
  A **12g2** (`specs/12g2-ajustes-calor-e-cor.md`, **verificada**, decisões do usuário de 27/10): **só a Varia protege do calor**
  (`heat.varia_only_patch`: `$8D:E37C` `29 21 00` → `29 01 00`; com a Gravity só a energia cai ¼ do normal, regra geral do
  `$90:E9CE`: medido −15 em 240 quadros, `sala_quente`); **porta de charge branca** (cópia da verde com metatiles `$3E8–$3EF` e a
  linha **4** do tileset `$0C`, `beamdoors.CHARGE_METATILES/CHARGE_LINE/WHITE`; o tileset 4 não tem linha livre: porta de charge só
  no `$0C`, `check_charge_doors`; `porta_de_charge` confere bloco e cor na WRAM; foto `specs/img/12g2-cores-das-portas.png`); **a
  ordem da 12f saiu** (item da PB primeiro, `check_bombed_items(_in_rom)`): medido que o teste da 12f nem exercitava o defeito (o
  toque nascia no próprio slot morto); `chozo_regiao_a_itens` ganhou o caso real (`tree_dead_slot`: morto no slot 37 acima do
  míssil vivo no 35, slot 39 liberado por RAM; falha sem a spec 13); **tiro em porta de cor** (`$84:C7E2`) com a mesma correção
  (`itemtouch.DOOR_*`, rotina `$84:FFBB–FFDE`, carry = achou): o tiro cria 2 PLMs por quadro, então o defeito só apareceria com
  2 mortos acima de uma porta no slot ≤ 36 (nenhuma sala tem): sem teste no emulador; o validador roda as duas rotinas num
  **interpretador mínimo de 65816** (`itemtouch.behaviour_problems`). `check_ruins_in_rom` lê direto as linhas 4/5 e os metatiles
  pintados.
  A **12h** (`specs/12h-inimigos-chozo.md`, **verificada**): camada 0 do Prime nas salas da região A (`tools/chozo/enemies.py`,
  `areas.CHOZO.enemies`): Beetle → Sidehopper pequeno, Wall Crawler → HZOOMER, **Oculus → Viola `$DABF`**, **Puffer → Mella `$D13F`**
  (PUYO/PUU do épico tiram 60/100 por toque); 30 inimigos em 8 salas (≤ 1 por tela); set "CHOZO  "; elevadores, Piston, Tower
  Access e Tower Chamber vazios (o Prime não tem). `check_tallon_enemies` virou `check_layer0_enemies(area, tabela)` +
  `check_chozo_enemies` (linha "chozo (specs/12h)"). Tabela do Prime das regiões B–E só registrada (`PRIME_LAYER0_LATER`,
  `PROPOSED_LATER`). Testes: novo `chozo_inimigos_vivos`; `chozo_walk` repõe a energia a cada ciclo; o shrine da rota é atravessado
  atirando (`SHRINE_FIGHT`: 2 Sidehoppers mortos); `chozo_regiao_a_itens` apaga os inimigos por RAM (`clear_room_enemies`). A ROM
  de teste da 12g tira os inimigos da sala de teste.
  A **12i** (`specs/12i-regiao-b-chozo.md`, **verificada**): a região B da Chozo (12 salas, `ACTIVE_REGIONS = {"A", "B"}`, desenhos em
  `chozo/layouts.py`); a Nursery Access L0 e a Plaza Access R0 abrem (a Plaza Access fica alcançável, `WAITS_FOR` vazio; o E-tank "Locked
  Door" da praça passa da rodada 3 para a 1, vindo do Vault como no Prime). Travas: só escudos de míssil no Prime = portas vermelhas
  (Gallery → Map Station `$B4`; Hive Totem ↔ Transport Access North **dos dois lados, um bit**, `$B5`; `check_gates` aceita o mesmo bit
  só nos dois lados de uma ligação); nenhuma porta de charge (o Prime não tem porta de cor ali), nenhuma sala quente (o "Check Varia Suit"
  da galeria troca a água venenosa da poça, seca aqui). Itens (bits `$BD–$C2`): Vault (jaula: bloco de bomba), Ruined Nursery (bloco de
  bomba), Ruined Gallery "Tunnel" (Morph) e "Missile Wall" (**bloco de bomba: o SM não tem bloco só de míssil**), Transport Access North
  E-tank (Morph), Hive Totem **Missile Launcher = Missile Expansion** no topo do totem (rodada 0). **Save Station 1** = estação 1 da
  área 1 (`areas.chozo_stations`), "CHOZO / RUINS" na tela de continue (`areaselect.LABELS[1]`); **Map Station** (PLM `$B6D3`) revela as
  salas construídas. Elevador da Magmoor North de enfeite; a porta dela para a Sun Tower (região C) é parede. Inimigos: Eyon → **1
  olho da Morph Ball `$E6BF`** (inofensivo: dano 0, sem colisão, `Species.harmless` lido da ROM; dois registros, encaixe e olho,
  `Species.companion`, `mount="wall"`), War Wasp → **Mella** (o Kihunter morre com 6 tiros; o Rio mergulha longe demais para a
  Ruined Nursery), Fire Flea → **Fireflea** (`hover`/`bob`); 10 inimigos em 5 salas. Validador: `check_arrival` confere a porta
  fantasma de cada estação (Tallon e Chozo), o PLM de save e o de map station na ROM. Testes novos: `chozo_regiao_b_rota` (o laço a pé,
  com as subidas pelas portas de chão, o totem e a porta vermelha), `chozo_regiao_b_itens`, `chozo_save_e_continue`, `chozo_map_station`.
  Decisões pequenas do orquestrador registradas no épico como "padrão aceito" (decisão 9).
  A **12j** (`specs/12j-regiao-c-chozo.md`, **verificada**): a região C (15 salas, `ACTIVE_REGIONS = {"A", "B", "C"}`); abertas
  as paredes Ruined Fountain Access R0, Piston Tunnel R0 e Magmoor North R0. Fatos dos dados (roteiros em `s12j/scripts`): a cor
  das portas "key" vem da `DamageVulnerability` do `Trigger_DoorKey` (região C: só Wave = roxas, como a Tower of Light); o calor
  do Prime é a `SpecialFunction` 18 (`Area Damage`), na Chozo só na **Magma Pool** (`HOT_ROOMS`). Travas: vermelhas Arboretum
  Access→Arboretum `$B6`, Arboretum→Sunchamber Lobby `$B7` (+ túnel de Morph com bloco de bomba na copa), Arboretum→Gathering
  Hall Access `$B8`, Gathering Hall→Save Station 2 `$B9`; Piston↔Training Chamber = túnel com bloco de bomba (pistão); ondas
  Training Chamber↔Access↔Magma Pool; Sun Tower: a porta R2 é borda de Space Jump (Spider Ball) e a descida da Sunchamber à
  Magmoor é livre (o mapa da 12c pôs a porta da Magmoor acima). Itens (`$C3–$C7` + a Varia `$BC`): Varia no pedestal da
  Sunchamber (rodada 2, o Flaahgra depois), míssil da fonte e E-tank da Training Chamber em bordas de Space Jump (3), míssil da
  Training Chamber Access (túnel, 2), expansão de PB da Magma Pool (bloco de PB, 6), míssil da Gathering Hall (jaula com bloco de
  bomba, 2). **Save Station 2** = estação 2 da área 1. Inimigos: Metaree → **Skree** `$DB7F` (teto), Fire Flea, Oculus, War Wasp
  como antes: 13 em 4 salas. Validador: **`check_chozo_locks_mapped`** (toda trava do Prime numa ligação construída tem o seu
  mecanismo SM); sala construída ainda em `PRIME_LAYER0_LATER` é erro. Build: o `$8F` livre acabou e 288 bytes foram para a faixa
  recuperada da 12a; o `Allocator.put` comparava só 16 bits (ia para `$90:0000`): corrigido. O nível da Sunchamber cruza o banco
  `$E0` (teste automático `nivel_cruza_banco_chozo_sunchamber`, o gerador agora aceita sala da Chozo). Testes novos:
  `chozo_regiao_c_rota`, `chozo_regiao_c_itens`, `chozo_varia_e_calor`, `chozo_save_station_2`.
  A **12k** (`specs/12k-regiao-d-chozo.md`, **verificada**): a região D (11 salas, `ACTIVE_REGIONS = {"A", "B", "C", "D"}`);
  abertas as paredes R0 e R1 da Gathering Hall; as portas da Furnace para a região E (B3, R0) ficam parede (sacada leste na linha
  10 e chão na 28 já desenhados). Fatos dos dados (`s12k/dtrig.out`, `s12k/specialfn.out`, `s12k/objs_d.txt`): nenhuma porta de
  cor na região (**nenhuma porta de charge**; a Furnace → East Furnace Access da região E é só Ice), nenhum `Area Damage` (**nenhuma
  sala quente**; a Furnace é fria e seca). Travas: vermelhas Watery Hall Access→Watery Hall `$BA`, Watery Hall→Dynamo Access `$BB`
  (+ túnel com bloco de bomba: o "Breakable Block"), Dynamo Access→Dynamo `$BC`; Energy Core↔Burn Dome Access = túnel de Morph do
  lado da Burn Dome Access (câmara sobre a porta de chão); Energy Core→West Furnace Access = os bomb slots ("event" que é quebra-
  cabeça, `EVENT_LOCKS`) = túnel com bloco de bomba; Incinerator Drone fora. Itens (`$C8–$CF` + o Charge `$BB`): **Charge Beam** no
  pedestal da Watery Hall (rodada 1, portão de runas aberto), mísseis da Watery Hall Access e da Dynamo (paredes de míssil = bloco
  de bomba, 2), da poça da Watery Hall (túnel, 1), do trilho da Dynamo e da Furnace (bordas de Space Jump, 3), do suporte do Burn
  Dome (o lugar das Bombas, 1) e do túnel do Burn Dome (2), E-tank da Furnace (túnel com bomba sob o chão, 2). Inimigos: Parasite →
  **Zeela** (`zoomer`), Metaree → Skree, Eyon → 1 olho, Fire Flea, War Wasp → Mella: 16 em 8 salas. Validador: **`flood_touch`**
  (com o Space Jump um item só é pego onde ela fica de pé ou a bola descansa sob um teto: fecha a lacuna da 12j; linha do Tallon
  igual) e `EVENT_LOCKS` em `check_chozo_locks_mapped`. Testes novos: `chozo_regiao_d_rota`, `chozo_regiao_d_itens`
  (`to_the_door`: num corredor de 1 tela o pulo do `chozo_walk` pode parar em cima da tampa da porta).
  A **12l** (`specs/12l-regiao-e-chozo.md`, **verificada**): a região E (12 salas: **as 64 da Chozo construídas**,
  `ACTIVE_REGIONS = {"A", "B", "C", "D", "E"}`); abertas a B3 (porta de gelo **de chão**) e a R0 (porta de Morph: túnel na sacada
  leste, só com o Space Jump) da Furnace e as portas das salas de elevador East (→ Save Station 3) e South (→ Transport Access
  South). Fatos dos dados (`s12l/dtrig.out`, `s12l/objs_e.txt`, `s12l/conns52.txt`): portas key só Ice (Furnace↔EFA, EFA↔Hall,
  Hall↔Elder Chamber, Hall↔CAS, CAS↔Crossway, Reflecting Pool↔TAS, o lado da Antechamber), só Wave (CAW→Crossway); escudos de
  míssil Crossway→Elder Hall Access, Reflecting Pool→Save Station 3 e →Antechamber; a estátua ("Chozo bowling": slot roxo →
  Reflecting Pool Access, branco → E-tank); nenhum inimigo na camada 0; nenhum `Area Damage`. **Conflito**: o caminho do Prime
  (Furnace→CAW→Crossway→Elder Hall Access→Hall, estátua) chega à Reflecting Pool na rodada 3, e os elevadores East/South
  ficariam uma rodada antes dos lados do Tallon (4/5): a **Reflecting Pool inundada** (`chozo_rooms.FLOODED`, FX da 07l) com as
  portas dela (Save Station 3, Antechamber, TAS) atrás de degraus de 4 debaixo d'água = Gravity Suit; a porta de cima (T2) num
  bolso de onde se volta sem a suit (medido no emulador: guiando, ela sobe para a RPA). Linha do Tallon igual. Mecanismos novos:
  **portas de gelo de chão/teto** (`beamdoors.VERTICAL`, PLMs `$F4EF` B / `$F4F5` T, cópias da verde `$C87E/$C884`, depois da de
  charge); **`SIDE_CAPS`** (tampa diferente por lado: a Antechamber, vermelha do lado da piscina, gelo do lado dela; cada lado pede
  só o seu item); **`KEY_BEAM`** (o feixe do Prime de cada uma das 23 portas key, conferido pelo `check_chozo_locks_mapped`).
  Itens `$D0–$D2`: E-tank da Hall (bloco de bomba, 3), míssil da Crossway (cabana de Power Bomb no chão, 6), míssil da
  Antechamber (o lugar do Ice Beam, 4). Vermelhas `$BD–$BF`. **Save Station 3** = estação 3 da área 1. Validador: a água da
  Chozo no `check_tallon_water` (linha "água"), `check_ball_ledges` (túnel de Morph em borda de Space Jump: a Samus de pé, voando,
  não chega à porta). Testes novos: `chozo_regiao_e_rota` (a porta de gelo de chão: Power Beam, mísseis e Wave não abrem, o gelo
  abre; a estátua; a piscina sem e com a suit; o elevador South para o Tallon), `chozo_regiao_e_itens` (a porta de Morph da
  Furnace, a onda, a Crossway, a vermelha de chão, a Hall sem gelo, a Antechamber e a porta de gelo dela),
  `chozo_save_station_3` (pelo elevador East a pé).
  A **12m** (`specs/12m-rodadas-e-cadeia-completa.md`, **verificada**, 28/10/2026): fecha o épico 12. As rodadas das duas áreas
  já eram declaradas desde a 12f; `validate.check_world_rounds` (linha "rodadas (specs/12m)") confere o todo: o passeio
  Tallon + Chozo pega os 51 itens, cada rodada acrescenta algo, as rodadas declaradas = as do passeio (0–6) e a porcentagem
  do fim do SM (`CalcItemPercentageCount`, `$8B:E627`, tabelas lidas da ROM; `ITEM_GAIN`) com todos os itens = **51%** (um por
  item). Teste novo **`cadeia_completa_tallon_chozo`** (`tests/run_tests.py`, `full_chain`/`FullChain`/`fc_round_*`): do pouso,
  os 51 itens na ordem das rodadas (o gerador levanta erro se a ordem divergir das declarações: `check_order`), trocando de
  área só pelos elevadores (North nas rodadas 0–3 e 6, East na 4, South na 6; a Samus **anda** até a plataforma nas 9
  viagens), cada trava aberta de verdade, as subidas em zigue-zague das 12i–12l feitas com botões (copa do Arboretum, arena
  da Sunchamber, Sun Tower — atirando nos Oculus antes dos pulos —, escada da Watery Hall, galeria leste da Gathering Hall,
  fundo da Reflecting Pool com a Gravity, sacada da Furnace com o Space Jump; e as portas de teto da praça, da Meditation
  Fountain, do Energy Core, da Save Station 3, da piscina, da RPA e da EHA): **nenhuma correção de layout**. Atalhos que
  ficam (contados no roteiro): 217 `door_teleport`, 30 Samus posta perto de item, 7 diante de porta do Tallon, inimigos
  apagados em 7 salas (10 vezes), energia reposta, 1 recarga de mísseis, volta à nave por RAM 1 vez (Artifact Temple), a
  plataforma da Canyon e o topo da nave. ~215 000 quadros, ~270 s sozinha. **Emulador de teste**: `tools/snesrun.c` +
  `vendor/LakeSnes/snes/ppu.c/.h` (`Ppu.skipRender`): só o último quadro de cada `wait`/`hold` é desenhado (saída idêntica,
  conferida no `tallon_cadeia_completa`: stdout e 57 PNG iguais; 200 s → 85 s); `run_tests.main` começa pelos roteiros mais
  longos. Verificação inteira (dois builds, validate, testes) 5 min 54 s (antes ~8 min 15 s com 75 testes).
- 12m: validate "136 salas, 284 portas, 0 problemas" (linha do Tallon igual; Chozo igual à da 12l; nova "rodadas (specs/12m):
  Tallon + Chozo andados juntos, 51 itens em 7 rodadas, cada um na rodada declarada (itens por rodada, Tallon + Chozo: 0: 2 + 1;
  1: 4 + 7; 2: 1 + 11; 3: 2 + 8; 4: 2 + 1; 5: 7 + 0; 6: 2 + 3); elevadores a partir da rodada: chozo_west 0, chozo_east 4,
  chozo_south 5; porcentagem do fim ($8B:E627) com todos: 51% (energia 799, mísseis 160, power bombs 10)"); `.ips` sha1
  `0bcb610afa5639eb2cadc657ac9f357a1a8dcaf0` (dois builds, igual à 12l); **76/76**.
- 12l: validate "136 salas, 284 portas, 0 problemas" (linha do Tallon igual; Chozo "… regiões ativas: ABCDE): 64 salas
  construídas, alcançáveis …: 64, 31 itens; rodada 0: 15 salas, 1 itens; rodada 1: 22 salas, 7 itens; rodada 2: 12 salas, 11
  itens; rodada 3: 7 salas, 8 itens; rodada 4: 6 salas, 1 itens; rodada 5: 2 salas, 0 itens; rodada 6: 0 salas, 3 itens");
  `.ips` sha1 `0bcb610afa5639eb2cadc657ac9f357a1a8dcaf0` (dois builds); **75/75**; `$8F` recuperado 1524 de 2254 usados (**730
  livres**), `$83` de `$83:BB96` (+396), `$84` portas de feixe 1004 (+112), nível 136 blobs (+2925); `$A1`, `$B4`, SRAM iguais.
- 12k: validate "124 salas, 252 portas, 0 problemas" (linha do Tallon igual; Chozo "… regiões ativas: ABCD): 52 salas construídas,
  alcançáveis …: 52, 28 itens; rodada 0: 15 salas, 1 itens; rodada 1: 22 salas, 7 itens; rodada 2: 12 salas, 11 itens; rodada 3: 1
  salas, 7 itens; rodada 4: 1 salas, 0 itens; rodada 5: 1 salas, 0 itens; rodada 6: 0 salas, 2 itens"); `.ips` sha1
  `ebad8fa673c701847863a1ff8a16ae0a04f07093` (dois builds); **72/72**; `$8F` recuperado 846 de 2254 usados (**1408 livres**, a
  região E pede ~600), `$83` de `$83:BA0A` (+264), `$A1` de `$A1:F632` (+312), `$B4` de `$B4:F799` (+104), nível 124 blobs (+2489);
  SRAM igual.
- 12j: validate "113 salas, 230 portas, 0 problemas" (linha do Tallon igual; Chozo "… regiões ativas: ABC): 41 salas construídas,
  alcançáveis …: 41, 19 itens; rodada 0: 15 salas, 1 itens; rodada 1: 15 salas, 4 itens; rodada 2: 8 salas, 7 itens; rodada 3: 1
  salas, 5 itens; rodada 4: 1 salas, 0 itens; rodada 5: 1 salas, 0 itens; rodada 6: 0 salas, 2 itens"); `.ips` sha1
  `3df756e39c5098c35e911073f4a39e97b2bde840` (dois builds); **70/70**; `$8F` livre: **0** na faixa principal, faixa recuperada
  1966 de 2254 (a partir de `$8F:D60F`; as regiões D–E vão precisar dela e talvez dos outros pedaços órfãos do épico), `$83` de
  `$83:B902` (+436), `$A1` de `$A1:F4FA` (+220), `$B4` de `$B4:F731` (+56), nível 113 blobs (+3659); SRAM igual.
- 12i: validate "98 salas, 196 portas, 0 problemas" (linha do Tallon igual; a da Chozo "chozo (specs/12f, 12i; regiões ativas: AB): 26
  salas construídas, alcançáveis a pé da nave do Tallon: 26, 13 itens; … rodada 0: 12 salas, 1 itens; rodada 1: 9 salas, 4 itens; rodada
  2: 3 salas, 4 itens; …; fora das rodadas: nenhuma"; 12h "40 inimigos em 13 salas … regiões CDE: só a tabela do Prime"); `.ips` sha1
  `8bd21bf1644bffe3befe1038e59d13991ec983a9` (dois builds); **65/65** (novos `chozo_regiao_b_rota`, `chozo_regiao_b_itens`,
  `chozo_save_e_continue`, `chozo_map_station`; `chozo_inimigos_vivos` com as 5 salas da região B); `$8F` livre a partir de `$8F:FE27`
  (**473 bytes**; a 12i usou 600; a faixa recuperada da 12a, 2254, sem uso: as regiões C–E vão precisar dela), `$83` de `$83:B74E`
  (+324), `$A1` de `$A1:F41E` (+191), `$B4` de `$B4:F6F9` (+69), `$82` de `$82:F826` (+52), nível 98 blobs (+2585); SRAM do mapa igual
  (445/1280).
- 12g2 + 12h: validate "86 salas, 170 portas, 0 problemas" (linhas do Tallon e da Chozo 12f iguais; nova "chozo (specs/12h): 30
  inimigos em 8 salas …"); `.ips` sha1 `9a632d29fa3b6e80ac9bc2663d45a6d4a5785971` (dois builds; a 12g2 sozinha deu `8371049f…14d3`,
  60/60); **61/61**; `$84` livre a partir de `$84:F48B` (a 12g2 usou 138 + 36 em `$84:FFBB`); `$8D` 1 byte; `$A1` a partir de
  `$A1:F35F` (+504), `$B4` de `$B4:F6B4` (+108).
- 12g (+ spec 13): validate "86 salas, 170 portas, 0 problemas" (linhas do Tallon e da Chozo iguais; nova "chozo (specs/12g): travas
  novas prontas: …"); `.ips` sha1 `3fb636cf46244959557e8855b0fc526196a9691c` (dois builds; a spec 13 sozinha deu `425f0796…981f`, 58/58);
  **60/60** (novos `power_bomb_nao_apaga_item` (13), `porta_de_charge` e `sala_quente` (12g, na ROM de teste); nenhuma expectativa
  antiga mudou); `$84` livre a partir de `$84:F401` (a 12g usou 154; a 13 usou 33 em `$84:FFDF–FFFF` e trocou 5 em `$84:EEB7`); `$91` 2
  bytes (`varia_patch`); `$83` 2 bytes no lugar (lista de FX de paleta da área 1); o resto igual à 12f.
- 12f: validate "86 salas, 170 portas, 0 problemas" (linha do Tallon igual, linha nova "chozo (specs/12f, regiões ativas: A): 14 salas
  construídas, alcançáveis a pé da nave do Tallon: 13, 7 itens; …"); `.ips` sha1 `e22a2f9f78f4fb2b2d2ac49ab281be5b0fb4572c` (dois
  builds); **57/57** (novos `chozo_regiao_a_rota`, `chozo_regiao_a_itens`; nenhuma expectativa antiga mudou); `$8F` livre a partir de
  `$8F:FBCF` (1073; a 12f usou 563, faixa recuperada 0); fixo +4457 (metatiles do 0C em `$F0:DEB2`). As linhas abaixo são da 12e.
- `python3 -I tools/validate.py` → linha do Tallon "(regiões ativas: ABCDE, 44 salas construídas,
  alcançáveis agora: 44, 20 itens em 7 rodadas)", linhas "bancos: …" (livres, "nenhum nível cruza banco"), "órfãs: 243 salas vanilla
  sem caminho (por área 0-7: 31 43 73 15 55 19 6 1), 19 só nas demos; bytes só delas: $8F 20637, $83 9356, $A1 24030, $B4 4017" (11) e
  as linhas "chozo (specs/12b): área 1, 3 salas construídas; …; lista … (usa 41); SRAM do mapa livre: 835 de 1280" e "$8F recuperado:
  2254 bytes em 2 faixas …; usados pelas nossas salas: 0; …" (12), "chozo (tabela inteira, specs/12c, salas construídas: 3): 64 salas, 68
  ligações (15 de chão/teto), 202 telas, mapa 41/80 …" (12c), "chozo (specs/12e): 3 elevadores área 0 <-> área 1: … (rodada 0) … (rodada 4)
  … (rodada 5) …; 3 salas da Chozo construídas (becos, 0 itens), fora das rodadas do Tallon; ida e volta: …" (12e), "ruínas (specs/12d):
  tileset 0C com a linha 7 em arenito (paleta em $F0DDB7); usado só pelas 3 salas da Chozo; …" e "alocador fixo …: 7 blobs" (12d) e
  "75 salas, 148 portas, 0 problemas" (as portas são os `DoorLink`; os elevadores não entram na conta).
- `python3 -I tools/build.py` → `build/metroid_prime_snes.ips` sha1
  `d90984d0f621c88f8e5e2bac77ddb1a2e88026e6` (igual ao reconstruir; mudou na 12e: elevadores, 3 salas da Chozo, área 1; antes
  `04dc19af…d9dc` da 12d); `$84` livre a partir de `$84:F367`
  (3225 bytes); log "mapa na SRAM: área 0 = 47
  bytes em +357", "área 1 = 41 bytes em +404", "área 3 = 30 bytes em +327" (445/1280); as salas de elevador com "elevador (saída,
  plataforma) [...]". `$8F` livre: 1636 bytes
  (a partir de `$8F:F99C`; a 07m usou 544, a 09b 26, a 09d 8, a 09e 6, a 12e 145); `$91:D64E` 2 bytes trocados (09b); `$83` livre a partir de `$83:B502`
  (19198 bytes; a etapa 11 mediu: os números entre parênteses daqui antes não eram o livre); `$A1` (populações) a partir
  de `$A1:F167` (3737), `$B4` (enemy sets) a partir de `$B4:F648` (2488); `$A0` a partir de `$A0:F83F` (1985); `$A2` a partir de `$A2:F548` (2744); `$A6` de `$A6:FF91` (111); `$82` de `$82:F7F2` (2062); **nível
  das salas** `$E0:8000–$E0:E005` (24582 bytes, 75 níveis), **livres 499706** até `$EF:FFFF` (cruzar
  para o `$E1` é seguro, provado na 09c); **fixos** 7 blobs, 24247 bytes (até `$F0:DEB6`; a 10d pôs a tabela de metatiles do tileset 4, a 12d a paleta do 0C em `$F0:DDB7`), **livres 500041** até `$FF:FFFF`.
- `python3 -I tests/run_tests.py` → **55/55** (12e: novos `elevador_chozo_ida_e_volta` — do pouso, por teleporte até a Chozo West, posta
  na plataforma e 4+4 quadros nela, ↓: Chozo North, `$079F` = 1, bits explorados (o do Tallon na cópia da área 0), paleta linha 7 =
  `SANDSTONE`, pausa "CHOZO" na VRAM; ↑: de volta, o bit da North na cópia da área 1; nave, save, game over, continue: as duas áreas
  mantidas — e `elevador_chozo_east_e_south` — os outros dois, ida e volta, por teleporte; expectativas mudadas: `tallon_rota_bc` subida
  28 → 25 ciclos (a Morph é pega na ida), `tallon_mapa_salvo` ida 70 → 71 ciclos (a volta pega a Morph), `tallon_morph_e_bombas` e a
  rodada 0 da cadeia pegam a Morph de 2 blocos a oeste (era 3 a leste), `tallon_gravity` → 14 quadros do degrau da coluna 9 até a
  Gravity, x depois da cena `$00AC` (era `$00D0`) e anda → até a plataforma (x `$00CC`), a rodada 4 da cadeia idem do degrau;
  `tallon_rota_mvp` igual; fotos `build/tests/12e_*.png`, cópias em `specs/img/12e-*.png`; 12c/12d: nenhum teste novo, nenhuma expectativa mudou; 11: novo `atracao_e_novo_jogo` — título parado, as 6 salas vanilla do conjunto 0 de demos, bits de item
  `$FF` na demo, novo jogo limpo no hangar; nenhuma expectativa antiga mudou; 10: novos `teleporte_de_porta_alinhado`, `sobe_porta_de_teto_pela_borda_longe`,
  `mapa_com_a_forma_da_sala`; `porta_de_onda` confere a cor; nenhuma expectativa antiga mudou; 09f: novo `tallon_cadeia_completa`, nenhuma expectativa mudou; ajudantes `pick_up` (conta
  os itens pegos do byte seguinte também), `near_item`, `tallon_first_missile(name)`, `save_on_tallon_ship(shot, energy)`; 09e: novo `tallon_power_bomb` — da Savestation, por teleporte de porta até a Mines East,
  pega a Power Bomb andando (5/5, bit `$B3`), Morph por RAM, teleporte até o Life Grove, BG1 reposto numa tela inteira, anda da porta até a
  cabana e para na parede, o Power Beam não quebra, bola + SELECT (`$09D2 = 3`) + X: os 15 blocos = ar na WRAM, 600 quadros depois
  continuam, desfaz a bola e pega o X-Ray andando; expectativas mudadas: `tallon_grande_arvore` pega a Power Bomb na Mines East e, no Life
  Grove, em vez de pegar o X-Ray, para na parede da cabana (X-Ray não pego; foto `tallon_e_cabana_do_xray.png`); 09d: novo `tallon_morph_e_bombas` — pega o Morph e as Bombas andando (salas por
  teleporte de porta, Samus posta por RAM perto dos itens e na ponta da plataforma da Canyon), em pé para nos blocos, bola,
  bomba os 2 blocos (nível na WRAM = ar), sob o teto do túnel ↑ não desfaz a bola, na câmara desfaz, 600 quadros depois os
  blocos continuam quebrados, sobe à Gully; expectativas mudadas: `tallon_rota_mvp`/`tallon_mapa_salvo` voltam com 65 ciclos (eram
  56), `tallon_rota_bc` sobe com 28 (eram 21), as três terminam com o Morph (`$09A2 = $09A4 = $0004`, pego na volta da Chozo
  West), `tallon_mapa_salvo` repõe a Samus na nave antes de salvar e confere o Morph depois do continue, `tallon_gully_alcove`
  termina parando nos blocos de bomba e subindo de volta à Gully; 09c: nenhum teste novo no build normal, nenhuma expectativa mudou; `nivel_cruza_banco_<sala>`
  só quando algum nível cruza banco; novos da 09b: `tallon_onda`, `tallon_gelo`, `tallon_gravity`,
  `tallon_plasma` — cada item pego andando para dentro dele (sala por teleporte de porta, documentado), bit e
  `$09A2/$09A4`/`$09A6/$09A8` conferidos, usado na trava: porta de onda, de gelo, de plasma e de gelo com `$B`,
  anteparo da Vent C (sem a suit fica, com ela passa); o Wave sobrevive a save na nave + continue; tela de
  equipamento com os feixes; nenhuma expectativa antiga mudou; novos da 09a: `porta_de_gelo`, `porta_de_onda`, `porta_de_plasma` —
  feixe e mísseis por RAM, sala por teleporte de porta entrando pela porta; Power Beam, mísseis e feixe errado não
  abrem, o certo abre, passa e na volta está fechada; nenhuma expectativa antiga mudou; novos da 07m: `tallon_grande_arvore` — da estação 1, por teleporte
  de porta: as 8 salas de E, secas, inimigos vivos, pega o míssil da Great Tree Chamber e o X-Ray —, e
  `tallon_gully_alcove` — da nave: Alcove (pega o Space Jump), borda da Landing Site, Gully, desce na Canyon e a
  tampa cinza da T3 não abre; nenhuma expectativa antiga mudou; novo da 08: `fragata_desce_porta_de_chao_e_anda` — desce andando
  pela porta de chão da Map Facility, pousa na borda e anda; nenhuma expectativa antiga mudou; novos da 07l: `pulo_na_agua_medido` — constantes `WATER_*` na
  Savestation —, `tallon_rota_d` — da estação 1, desce ao Reactor Access, portas cinza fechadas, sobe —,
  `tallon_save_fragata` — salva na estação 1 (depois de sair e voltar: estação recém-carregada não salva,
  vanilla), continue volta nela —, `tallon_fragata_afundada` — as outras salas por teleporte de porta,
  água, inimigos vivos, pega o E-tank da Cargo Lift; nenhuma expectativa antiga mudou; novos da 07i: `tallon_inimigos_vivos` — cada inimigo das
  salas do caminho na tabela da WRAM `$7E0F78 + $40·n`, vida cheia —, `tallon_inimigos_atras_da_porta_vermelha`
  — Root Cave e Tunnel B depois de abrir a porta do Root Tunnel com mísseis —, `tallon_power_beam_mata_inimigo`
  — o Cacatac morre com 3 tiros agachada; as rotas cegas (`tallon_walk`) repõem a energia a cada ciclo e a
  subida da `tallon_rota_bc` começa encostada na porta L1; novos da 07h: `tallon_missil_abre_porta_vermelha` — pega o
  míssil do lago, abre a porta vermelha da Waterfall com mísseis e entra na Crash Site —, e
  `tallon_missil_salvo` — bit e 5/5 sobrevivem ao save; `tallon_rota_bc` agora termina com 5 mísseis,
  pegos no lago; novo da 07k: `tallon_rota_bc`, rota andando por trechos
  medidos; a volta da rota do MVP agora anda 56 ciclos; novos da 07f: `tallon_mapa_salvo`, `continue_mostra_o_tallon`;
  da 07e: `tallon_chegada`, `tallon_nave_salva`;
  `lands_on_landing_site` agora espera o equipamento da chegada, não o da fragata; a rota do Tallon
  não zera mais por RAM).
- Fim da fragata → área 0 estação `$12` (não a 0) → Landing Site nova; a nave desce até a altura
  da nossa sala (constantes de `GunshipTop_3` trocadas em `ending.landing_height`) e salva na
  estação 0 (em cima da nave).
- Imagens: `build/tests/meta_ridley.png`, `timer_fora_da_air_lock.png`,
  `timer_depois_do_ridley.png`, `nave_no_hangar.png`, `nave_decolando.png`,
  `fuga_tallon_iv.png`, `fuga_pouso_landing_site.png`, `final_continue_landing_site.png`,
  `tallon_chegada_hud.png`, `tallon_nave_save.png`, `tallon_nave_continue.png`,
  `tallon_mapa_salvo.png`, `tallon_minimapa.png`, `continue_tela_do_tallon.png`,
  `continue_mapa_do_tallon.png`,
  `final_reset_cena.png`, `parasite_queen.png`; antes/depois da forma da Parasite Queen em
  `research/parasite_queen_forma.png`.
- A pasta **não é repositório git**: nada foi commitado; tudo está só no disco.

## Épico 17 (Magmoor), 17d e 17e, 01/11/2026

- **17d** (`specs/17d-estilo-das-cavernas-de-lava.md`): `tools/smlib/lava.py` — estilo `LAVA_HOT` (tileset 09) / `LAVA_COOL` (0A),
  peças das salas vanilla `$8F:A923`/`$AE07` (todas na linha 4), cores em `COLOURS_HOT/COOL` (as únicas tabelas de cor; linha 4 do
  estilo e linha 6 do fundo `$BE5A`), porta roxa na linha 7, música `$15/$05`, `fx_entry` (FX de lava tipo 2 no molde do vanilla
  `$83:8430`), `FX_HOT = $1F` (calor + brilhos da lava; `heat.GLOWS`). Build: paletas 09/0A e uma tabela de metatiles dividida depois do
  logo do título; `RoomDef.lava` = linha da superfície; `build.room_fx`. Modelo (`reach.py`): `LAVA`, `with_lava`, `lava_escapes`,
  `LAVA_RISE_PX = {1: 46, 2: 58, 3: 69}`, `LAVA_MAX_DEPTH = 3`, `LAVA_MAX_MOVES = 5`. Validador: `check_lava` (lava só na área 2,
  nunca no caminho — os passeios não entram nela —, toda lava com saída medida), `check_lava_test_rooms`, `check_lava_in_rom`, linhas
  "lava (specs/17d)". ROM de teste `python3 -I tools/build.py --teste-17d` → `build/teste-17d/` (`tools/magmoor/testrooms.py`: duas salas
  de lava penduradas na R0 da P16); testes `lava_medida` (dano ½/¼/0 por quadro, pulos, saídas, calor + lava) e `porta_de_onda_lava`.
  A lava do SM (BG3) cobre a sala inteira da superfície para baixo: as regiões põem a superfície abaixo de todo chão andável.
- **17e** (`specs/17e-elevadores-da-magmoor.md`): `tools/magmoor/layouts.py` (P0 1×2 e P16 2×1, becos, poço até a plataforma em x 7–8),
  `areas.MAGMOOR` (área 2, estação 0 ao lado da plataforma da P0), `ELEVATORS` = (de cima, de baixo) com Chozo P24 → P0 e Tallon P23 →
  P16 (P23 com `ride=True`, o Wave fica em (9, 25); P24 com a plataforma sob o poço), "MAGMOOR / CAVERNS" (`areaselect.LABELS[2]`).
  Validador: `PRIME_ELEVATORS` por (área, P#), `world_rooms` com a Magmoor, `check_magmoor_rounds` (linha "magmoor (specs/17e)"); a
  linha das rodadas e a do Tallon iguais. Testes `elevador_magmoor_ida_e_volta`, `elevador_magmoor_tallon`; a caminhada da região B
  (P24 → Vault Access) ganhou `chozo_walk_paused` (pausa de 16 quadros depois do ciclo 13, medida).
- **17f** (`specs/17f-regiao-a-magmoor.md`, verificada): região A (`magmoor/rooms.py ACTIVE_REGIONS = {"A"}`): Burning Trail, Save Station A
  (estação 1 da área 2, `areas.magmoor_stations`; porta vermelha do lado da trilha, bit `$C0`, `GATES`, `MAGMOOR_MISSILE_BIT0`), Lake
  Tunnel, Lava Lake, Pit Tunnel, Triclops Pit, Storage Cavern, Monitor Tunnel (R0 = parede até a 17h); `heat_gates` (Varia nas portas
  das 5 quentes); lava pela tabela `layouts.LAVA` (superfície sob todo chão; fossos/poças de 2 linhas; túneis de uma tela com o chão
  na linha 12). Itens `tools/magmoor/items.py` (bits `$D3–$D4`, rodada 3; o da Triclops Pit com `needs = {Space Jump}`). Validador:
  chaves de item `("magmoor", n)` (`item_world`, `item_bit`, `ITEM_TABLES`), `check_magmoor_rounds` com itens (linha "magmoor (specs/17e,
  17f)"), `check_magmoor_locks_mapped` (linha "magmoor (specs/17f)": trava do Prime → mecanismo, lava só onde o Prime tem),
  `check_item_geometry` com borda de Space Jump, `check_arrival` com a Magmoor, guarda "rodada só da Magmoor" em `check_world_rounds`
  (que continua só Tallon + Chozo: 51 itens, 51%). Testes `magmoor_regiao_a_rota` (caminhada medida inteira com Space Jump de verdade,
  energia 99 do começo ao fim), `magmoor_calor`, `magmoor_save_station_a`; 90/90 em 6 min 31 s. Roteiros de medida no scratchpad
  `s17f/scripts/` (`route.py`/`chain.py`: busca dos quadros de andar antes de cada pulo). **`$8F`: a faixa da 12a está cheia
  (2151/2153); as regiões B e C usam as da 17a (1563 livres).**
- **17g** (`specs/17g-inimigos-magmoor.md`, verificada): `tools/magmoor/enemies.py` (`ENEMIES`, `STAND_IN`, `PRIME_LAYER0` com **todas**
  as salas do Prime com inimigo na camada 0 — B e C inclusive —, `PROPOSED_LATER`): 19 inimigos em 6 salas — Burning Trail 3 Skrees
  (sob os dentes do teto, que a 17g desceu até a linha 16: acima da câmera um inimigo não roda) + 1 Zeela; Lake Tunnel 1 **Sova**
  (Burrower, `$DCBF`, kind `burrower`) + 2 Zeelas; Lava Lake 3 Mellas; Pit Tunnel 2 e Triclops Pit 5 **Violas paradas** (Tryclops, kind
  `tryclops`: parâmetro 1 = `$FF`, velocidade 0; andando elas iam para o fundo das poças sob a lava); Monitor Tunnel 2 Mellas. Validador
  `check_magmoor_enemies` (linha "magmoor (specs/17g)"): justiça em **toda** sala da Magmoor (`MAGMOOR_FAIR_EVERY_ROUND`: ≤ 5 tiros do
  Power Beam, ≤ 20 por toque), inimigo fora da lava, tabela ⊂ Magmoor, `ENEMIES` só em salas construídas. Testes: novo
  `entradas_de_porta_magmoor` (spec 15, 13 entradas); `magmoor_regiao_a_rota`/`magmoor_save_station_a` medidos de novo **com os inimigos
  vivos e a energia 99 do começo ao fim**: strings de `MAGMOOR_MOVES` (`moves()`, achadas por busca em feixe no emulador:
  `s17g/scripts/fight.py`, `route17g.py`) e, no fundo da Triclops Pit, 2 tiros agachada por Viola + o pulo da poça. 91/91 em ~6,5 min.
- **17h** (`specs/17h-regiao-b-magmoor.md`, verificada): região B (`ACTIVE_REGIONS = {"A", "B"}`): Monitor Station (6×4, zigue-zagues
  de 9 e 3 bordas, 4 fossos), Transport Tunnel A (E-tank `$D5` num túnel de 1 linha com bloco de bomba, rodada 3), Transport to Phendrana
  North (de enfeite: salão e poço, sem elevador), Warrior Shrine (a R0 numa câmara atrás de um túnel com **bloco de Power Bomb**), Shore
  Tunnel (porta de chão B2), Fiery Shores (praia com 4 fossos; sob a plataforma da T0 o bolso da L0 com o míssil `$D6` e o túnel com a
  **expansão de PB** `$D7`, bloco de PB na saída: os dois na rodada 6), Transport Tunnel B, a L0 da P16 aberta (a R0 parede até a 17i).
  `GATES` Warrior Shrine ↔ Fiery Shores = `{Morph, Power Bomb}` só geometria (ledge dos dois lados; `build_rooms` da Magmoor aceita).
  Rodadas: as 7 na 3 (dos dois lados: Monitor Tunnel e a P16 pela TTB quente); **linhas do Tallon e das rodadas (12m) iguais** (o
  caminho Chozo ↔ Tallon pela Magmoor só existe com a Varia e liga duas salas da rodada 1). Inimigos: Fiery Shores 2 Violas paradas;
  **Magdolite fora** (`STAND_IN None`; decisão a confirmar); a Mella leste da Monitor Tunnel 24 → 12 (a porta nova; spec 15).
  Validador: `check_magmoor_locks_mapped` com morph, `check_breakables` e `check_item_geometry` (porta atrás da mesma geometria) na
  Magmoor. Testes novos `magmoor_regiao_b_rota` (até o elevador do Tallon a pé, ↑ para a P23) e `magmoor_regiao_b_itens` (a parede de
  PB, os itens, a subida pela T0); `entradas_de_porta_magmoor` 17 entradas; `magmoor_regiao_a_rota` termina entrando na Monitor Station;
  `lava_medida`/`porta_de_onda_lava` acham a porta da P16 para a sala de teste (`host_door_to_cool`). 93/93 (verificação inteira 6 min 58 s; `.ips` sha1 `2b960ef9…8a5c`). `$8F`: a
  região B usou 331 bytes (livres 1335: 472 + 861 nas faixas da 17a, 2 nas da 12a). Roteiros em `s17h/scripts/` (`tr.py` traço,
  `hops.py`/`grid.py` janelas de pulo, `route17h.py` busca em feixe, `gen.py` estados de partida).
- **17i** (`specs/17i-regiao-c-magmoor.md`, verificada): região C (`ACTIVE_REGIONS = {"A", "B", "C"}`: **as 29 salas**). Twin Fires
  Tunnel (a única quente do sul; a R0 num penhasco de 16 linhas = borda de Space Jump, o trilho de Spider; trava só de geometria
  sem trava de porta no Prime, justificada pela feature: `rooms.FEATURE_GEOMETRY`), Twin Fires (3 Mellas), North Core Tunnel,
  Geothermal Core (laje da L1 pelo zigue-zague 37/32/27; a L1 numa câmara atrás de um túnel com **bloco de bomba** = os bomb slots;
  a L0 no topo da rocha da câmara, 16 linhas acima da laje = Space Jump), Plasma Processing (**míssil** `$D8` no lugar do Plasma,
  rodada 4; a porta de plasma do Prime = **gelo**, `rooms.SM_BEAM`), South Core Tunnel (2 Sovas), Workstation (**E-tank** `$D9` numa
  plataforma alta = Space Jump, rodada 3; zigue-zagues oeste 42→26 e leste 26→10; rocha sobre a L2 e a R0), Workstation Tunnel (2
  Zeelas), Mines West e Phendrana South de enfeite (salão + poço, sem elevador), Transport Tunnel C, **Save Station B** (estação 2
  da área 2, porta vermelha `$C1`). Puddle Spore fora (`STAND_IN None`). Rodadas: C na 3 (a Twin Fires Tunnel é quente: Varia),
  Plasma Processing e Mines West na 4 (gelo); **linhas do Tallon e das rodadas (12m) iguais**. Validador: `check_magmoor_locks_mapped`
  com key (tampa do feixe do Prime ou de `SM_BEAM`), nenhuma porta de plasma, `FEATURE_GEOMETRY`. A **ROM de teste da 17d** saiu da
  R0 da P16 para uma porta R1 da Mines West (`testrooms.HOST`/`HOST_DOOR`; salas de teste no mapa em 60–62, linha 11). Testes novos
  `magmoor_regiao_c_rota`, `magmoor_regiao_c_itens`, `magmoor_save_station_b`; `entradas_de_porta_magmoor` 23 entradas. **Bateria
  dividida**: `tests/run_tests.py --grupo A|B` (`TEST_GROUP_B` por prefixo: tallon_, chozo_, magmoor_, elevador_, entradas_de_porta_,
  nivel_cruza_banco_ e os das ROMs de teste; A = o resto, com a cadeia completa, ~5,2 min sozinha, o piso do grupo A); sem
  `--grupo` roda tudo (~9 min, passa do limite de uma execução da ferramenta). `$8F`: a região C usou 640 bytes (livres agora 695:
  1 + 1 + 0 + 693 nas faixas recuperadas). Roteiros em `s17i/scripts/` (`seg.py` busca em feixe com letras de Space Jump, `trp.py`,
  `hops.py`, `gen.py`, `mutate_i.py`, `emu_mut_i.sh`).
- **17j** (`specs/17j-rodadas-e-cadeia-tres-areas.md`, verificada; **fecha o épico 17**): `check_world_rounds` anda as três áreas
  (linha "rodadas (specs/12m, 17j)": 58 itens em 7 rodadas, Tallon + Chozo + Magmoor por rodada 0: 2 + 1 + 0; 1: 4 + 7 + 0; 2: 1 + 11 +
  0; 3: 2 + 8 + 4; 4: 2 + 1 + 1; 5: 7 + 0 + 0; 6: 2 + 3 + 2; elevadores chozo_west 0, chozo_east 4, chozo_south 5, magmoor_north 1 (da
  Chozo), magmoor_east 1 (do Tallon); **58%**, energia 999, mísseis 180, power bombs 15); a guarda da 17f fica ("nenhuma rodada só da
  Magmoor"); `check_epic_magmoor` (linha "magmoor (specs/17, épico fechado na 17j)": as 29 salas e 29 ligações, os 7 itens da decisão
  2 por sala do Prime, as 16 travas, as 12 quentes, a lava, os 2 elevadores de verdade e os 3 de enfeite, as 2 save stations, nenhum
  chefe). Cadeia (`tests/run_tests.py`): os pedaços das caminhadas das regiões (`magmoor_a_to_storage`/`_to_column`/`_to_station`,
  `magmoor_b_to_tank`/`_to_p16`, `magmoor_c_to_slab`/`_to_tank`: os roteiros dos testes das regiões idênticos), `fc_round_3_magmoor`
  (da Hall of the Elders à Magmoor North da Chozo, regiões A, B, C, sobe pela P16 ao Tallon), `fc_round_4_magmoor` (da Root Cave
  pela Magmoor East: o míssil da Plasma Processing), `fc_round_6_magmoor` (a parede de PB da Warrior Shrine, o míssil e a expansão
  da Fiery Shores, o mapa da Magmoor); **três testes** `cadeia_completa_parte_1` (rodadas 0–2, grupo A), `_2` (rodada 3) e `_3`
  (rodadas 4–6 e o fim), grupo B, ligados por `save`/`load` do `snesrun` (`CHAIN_PARTS`, `chain_handoff`: as mesmas checagens dos
  dois lados; `run_chain_parts`: carimbo `.state.json` com o sha1 da ROM e dos roteiros; estado faltando ou de outra ROM/roteiro roda
  a parte anterior antes, como pré-requisito).
- **Verificação desde a 17j** (um comando por vez, **A antes de B**): `python3 -I tools/build.py` duas vezes (sha1 igual), `python3 -I
  tools/validate.py | tail -1`, `python3 -I tests/run_tests.py --grupo A` (~3,3 min) e `python3 -I tests/run_tests.py --grupo B`
  (~4,8 min; carrega o estado que a parte 1 da cadeia salvou no grupo A).
- **Decisões da 17j para o usuário (recomendadas, a confirmar)**: a cadeia em 3 testes ligados por estado salvo (o grupo B depende do
  A); os atalhos novos da cadeia: 2 portas de teto por `rise_through` (Sunchamber Lobby, Fiery Shores), energia/mísseis/power bombs
  repostos por RAM ao entrar na Magmoor (nunca capacidade).
- **Decisões da 17i para o usuário (recomendadas, a confirmar)**: Puddle Spore fora; o E-tank da Workstation numa borda de Space
  Jump (os painéis de Wave do Prime viram nada: o Wave já é pedido nas portas); a borda de Space Jump da Twin Fires Tunnel e da porta
  de cima da Geothermal Core (trilhos de Spider); 3 Mellas de 15 Puffers, 2 Zeelas de 3 Parasites; os desenhos (`specs/img/17i-salas.png`).
- (registro da 17h) **Próximo era 17i (região C, sul)**: as 12 salas (Twin Fires Tunnel da R0 da P16 em diante); portas de onda (9 docas) e de gelo (3), a de
  dentro da Plasma Processing como gelo; Save Station B (estação 2, porta vermelha `$C1`); itens: um míssil no lugar do Plasma e o
  E-tank da Workstation; inimigos (`PRIME_LAYER0`: Twin Fires Puffer 15, South Core Tunnel Burrower 2 + PuddleSpore 1, Workstation
  Tunnel Parasite 3). A ROM de teste da 17d pendura na R0 da P16: a 17i precisa mudá-la de lugar.
- **Decisões da 17h para o usuário (recomendadas, a confirmar)**: Magdolite fora; a porta Warrior Shrine ↔ Fiery Shores nos dois
  sentidos (atrás de PB dos dois lados); os desenhos (telas de baixo em rocha na Warrior Shrine e na P13; a P13 sem plataforma de metal).
- **Decisões da 17g para o usuário (recomendadas, a confirmar)**: Burrower = Sova, Tryclops = Viola parada; as contas por sala (abaixo
  do Prime onde a sala 3D tem muitos: 3 de 16 Metarees, 3 de 6 e 2 de 5 Puffers, 2 de 3 Tryclops); justiça em toda rodada; os dentes
  mais longos da Burning Trail.
- **Decisões da 17f para o usuário (recomendadas, a confirmar)**: o míssil da Triclops Pit numa borda de Space Jump (oco de coluna);
  sem as rochas/ganchos do artefato da Lava Lake; os desenhos das salas.
- **Decisões para o usuário (recomendadas, a confirmar)**: as cores da Magmoor (`lava.COLOURS_*`); a regra da lava (5 movimentos, 3
  linhas de fundo); brilho só nas salas quentes; o chão das cavernas é escuro com pouca crosta (a peça de chão vanilla `$11D` é quase toda
  a cor 11): se o usuário quiser mais brilho no chão, trocar a peça ou a cor 11.

- **Próximo passo: decisão do usuário** (nenhuma etapa aprovada depois do épico 17). Itens abertos do usuário: a **cor final das
  ruínas** (pergunta 8 do épico 12); os **Chozo Ghosts** (14e, adiados); as **decisões a confirmar da Magmoor** (17d: as cores e a
  regra da lava, brilho só nas quentes, o chão escuro; 17f: o míssil da Triclops Pit numa borda de Space Jump, a Lava Lake sem as
  rochas do artefato, os desenhos; 17g: Burrower = Sova, Tryclops = Viola parada, as contas por sala, justiça em toda rodada, os
  dentes da Burning Trail; 17h: Magdolite fora, a porta Warrior Shrine ↔ Fiery Shores nos dois sentidos, os desenhos; 17i: Puddle
  Spore fora, o E-tank da Workstation numa borda de Space Jump, bordas de Space Jump no lugar dos trilhos de Spider, as contas da
  região C, a divisão da bateria; 17j: a cadeia em 3 testes, os atalhos novos); o **plano das áreas para Phendrana, Mines e Impact
  Crater** (aviso de capacidade do épico 17, decisão 6: sobram as áreas 4 e 5 para 3 mundos); e as decisões a confirmar das filhas
  14b–14d, da 16 e das 12i–12m (listas nas specs).

## Etapa dos chefes (épico 14), 30/10/2026

- **14a — Plated Beetle** (`specs/14a-plated-beetle.md`, verificada): `tools/chozo/bosses.py` (novo): `SpeciesCopy` (cópia de
  cabeçalho de espécie em `$A0` com toque e paleta próprios; a paleta no espaço livre do banco da IA, `$A3:F311`), `BOSSES`
  (sala, tipo, objeto do Prime, tiros do Power Beam, trava); `build_copies` chamado logo depois do Meta Ridley.
  `Species.boss` (frigate/enemies.py) tira o chefe da regra da camada 0; `validate.check_bosses` + `check_species_copies`
  (linha "chefes (specs/14a)"): regra de justiça de chefe `FAIR_BOSS_SHOTS = 20`, `FAIR_BOSS_TOUCH = 40`. Teste
  `chozo_plated_beetle`: luta de verdade só com o Power Beam, nada reposto (roteiro `BEETLE_FIGHT` achado por busca no
  emulador, `s14a/scripts/beam.py`; vale para a entrada exata do teste). A cadeia passa com o besouro vivo (ela anda por ele
  com a energia reposta, como antes), sem atalho.
- **Spec 15** (`specs/15-auditoria-de-entrada.md`, problema achado na 14a, verificada): a auditoria de entrada da 12h entrava por
  RAM e olhava 180 quadros; refeita no scratchpad (`s14b/scripts/audit2.py`: a Samus anda para dentro pela porta, ou door_teleport
  em porta de chão/teto; 600 quadros parada; 2 jeitos × 4 tempos por entrada): toques antes de 2 s em 9 salas. Regra: parada,
  nenhum toque nos primeiros **120 quadros** (600 na Shrine). Mudadas 8 colocações (Shrine 14/31 → 18/29: os pequenos na tela do
  meio ficam parados fora da câmera, `sm_a0.c:578`; Main Plaza 87 → 72; Plaza Access 22 → 19; vespa do Hive Totem 10 → 11; Root
  Cave Zeela 40 → 37; Great Tree Hall Blood Flower 38 → 24; Tunnel D 11/20 → 16/17; Tunnel E 11/36 → 18/29). Exceções registradas:
  o pirata do Elevator Beta (épico 10) e a vespa da Ruined Nursery na L0 (movê-la quebra a caminhada da cadeia; corrigida na 14c: só o pirata ficou). Testes novos
  `entradas_de_porta_tallon` / `entradas_de_porta_chozo` (`entry_audit`, `check_entries`, `ENTRY_EXCEPTIONS`).
- **14b — Arena e Hive Mecha** (`specs/14b-arena-e-hive-mecha.md`, verificada): `tools/chozo/bosses.py` `ARENAS` + rotina comum
  em `$84:F500` (140 bytes; tabela de 10 bytes por arena logo depois): chamada pelo main ASM do estado vivo (`JSL`/`RTS`, 5 bytes no
  `$8F`, uma para todas), acha a sala, com o bit da arena desligado confere a condição (`KILLS`: `$0E50 >= $0E52`; `SLOT`: o slot de
  inimigo vazio; `BOSS_BIT`; `ITEM`), liga o bit nosso da área (`SetBossBitForCurArea`), **para** a música (`QueueMusic(0)`: pôr o set da área de volta
  congelava ~38 quadros) e gera o PLM do prêmio (`SpawnRoomPLM`, a entrada da lista do estado morto). O build dá à sala um estado
  morto por `E629 #bit` (sem as espécies `boss`, música da área, sem main ASM, o prêmio só na lista dele) e o vivo com a música de
  mini-chefe `2A/05`. Hive Totem: 2 Kagos (`hive`, `$E7FF`, parâmetro 1 = 4: 5 golpes; vanilla 11) sob os favos + as 3 Mellas;
  bit `$08`; o míssil (23, 8) aparece. Ruined Shrine: o besouro da 14a pela condição `SLOT` 3, bit `$20` (música e estado morto).
  Validador: trava `boss` no passeio (`boss_locks`: o prêmio só com o `needs` da arena), `check_arenas`/`check_arenas_in_rom`
  (linha "arenas (specs/14b)": justiça de chefe somada, Kago pela regra dos golpes lida dos bytes, cabeçalho/estados/rotina/tabela,
  nenhum `E612`). Testes: `chozo_hive_mecha` (luta de verdade achada por busca, `s14b/scripts/hive_beam.py` + `hive_beam2.py`;
  sai/volta morto; salva, game over, continue: morto), `chozo_plated_beetle` com a luta procurada de novo (`beetle_beam.py`) e o
  estado morto; a cadeia e a rota B vencem a arena por RAM ao entrar no Hive Totem (`arena_won_by_ram`, anotado).
- Bits de chefe nossos na área 1: `$08` Hive Mecha, `$10` reservado ao Incinerator Drone (14d), `$20` Plated Beetle; o Flaahgra
  (14c) usa o `$02` do próprio Spore Spawn. A rotina tem 4 condições (`KILLS`, `SLOT`, `BOSS_BIT` para a 14c, `ITEM` para a 14d;
  as duas últimas sem arena ainda, conferidas no emulador numa ROM de rascunho, `s14b/scripts/conds.py`); a 14d precisa ainda
  da trava `boss` em **porta** no passeio e da porta cinza gerada como prêmio.
- **14c — Flaahgra = Spore Spawn** (`specs/14c-flaahgra.md`, verificada, 31/10/2026). Passo 1 (sobra da spec 15): a vespa
  da Ruined Nursery em (11, 9), sem exceção na auditoria de entrada; a cadeia ganhou `CHAIN_ATRIUM_TO_DOOR` (ponto fixo no
  North Atrium) e um tiro a mais na tampa da Totem Access (rodada 1). Passo 2: a Sunchamber refeita em volta do código do
  Spore Spawn (`layouts.sunchamber`: o fosso nas colunas 1–15, linhas 32–43, chão 44, teto até a galeria da L0, o entalhe
  (7–8, 30–31) já ar para o PLM `$B78F` da morte; salão a leste com os fossos dos bomb slots e o zigue-zague até a L0);
  espécie `flaahgra` = `$DF3F` com a população vanilla (extras `$0004`: spritemaps estendidos), slot 0, `Species.fixed`
  (128, 624). Arena: condição `BOSS_BIT $02` (o bit do próprio Spore Spawn, `$7ED829`), bit da arena **`$40`**, prêmio a Varia
  em (8, 43) (rodada 2, igual), `needs {missile}`. Porta cinza tipo 1 (`$8400`) na L0 (`chozo/rooms.py BOSS_DOORS`,
  `BOSS_GATE`); o passeio das rodadas abre a porta só com o `needs` (`validate.door_open`). Patches no `$A5`
  (`bosses.spore_spawn_patches`): paletas nas cores do Flaahgra (texturas do CMDL `EC81CD52`), as tabelas da morte
  `$A5:E4F9/$E5D9` = as linhas 4 e 7 das ruínas (o arenito não escurece), o gancho de câmera desligado. Justiça de chefe
  com o equipamento da rodada (`arena_gear_fight`: 10 mísseis com capacidade 40 na rodada 2, ou 8 tiros carregados).
  Teste `chozo_flaahgra` (luta de verdade com mísseis, `FLAAHGRA_FIGHT` gravado de uma política em malha fechada,
  `s14c/scripts/policy2.py`; a Varia, a porta, a volta morta, save/continue); `flaahgra_won_by_ram` (vida 0 por RAM, ele morre
  no primeiro toque) na rota C, na cadeia e no `chozo_varia_e_calor`.
- Bits de chefe da área 1: `$02` (Spore Spawn, SM), `$08` Hive Mecha, `$10` reservado ao Incinerator Drone, `$20` Plated
  Beetle, `$40` arena da Sunchamber.
- **14d — Incinerator Drone** (`specs/14d-incinerator-drone.md`, verificada, 31/10/2026): condição `ITEM` da rotina
  **redefinida** (a luta começa no item, termina na cota): a população viva da arena tem cota 0 ("não começou"); pego o item
  (`$CC`, o míssil do suporte), a rotina lê o registro de luta (`$84`, depois da tabela; `ENTRY_SIZE` 12, campo +10): `$0E52` =
  cota, `QueueMusic(5)` (o estado vivo carrega `2A/03`, como o Torizo vanilla), `SpawnRoomPLM` da tampa cinza tipo 3 (`$8C00`,
  uma entrada de 6 bytes no `$8F` fora das listas), `SpawnEnemy` (`$A0:9275`, `DB=$84`) das colmeias e vespas, e `$0800`
  (processar fora da câmera) em todo inimigo da sala. Rotina 222 bytes (`$84:F500`), arenas até `$84:F657`. Colmeias = **cópia
  do Kago com 1 parte** (`bosses.KAGO_COPY`, `$A0:F87F`: o Kago diz 9 e o `SpawnEnemy` gerava 9 slots e travava; o Hive Totem
  usa a mesma); vespa da camada 0 do Burn Dome em (40, 9) e as da luta (`arena_wasp`, `hover=72`) no ar (a Mella abaixo da Samus
  afunda e fora da câmera para). Porta: `BOSS_DOORS` + Burn Dome → Burn Dome Access, azul até a luta (`build.item_arena_door`).
  Validador: `boss_locks` com o item que começa a luta, `door_open` aberta para arena `ITEM`, `check_item_arena`, registro e
  tampa na ROM. Teste `chozo_incinerator_drone` (save na Save Station 2, item, porta trancada, morte e continue que refaz a luta,
  luta de verdade `DRONE_FIGHT` achada por busca `s14d/scripts/drone_beam.py`, saída, volta morta, save/continue); a rota D e a
  cadeia vencem por RAM depois do item (anotado).
- **14f — Rodadas e cadeia com os chefes** (`specs/14f-rodadas-e-cadeia-com-chefes.md`, verificada): `check_epic_bosses` (linha
  "chefes (specs/14)": `EPIC_BOSSES` com o que cada chefe trava no Prime; travas no passeio; bits distintos e fora dos vanilla da
  área 1, `vanilla_boss_bits` lidos da ROM base: `$01`, `$02`); docstring da cadeia com os 3 atalhos e o besouro vivo; fotos da 14a
  refeitas. Épico 14 **verificado** (seção "Verificação do épico").
- Bits de chefe da área 1 (final): `$02` (Spore Spawn, SM; condição da Sunchamber), `$08` Hive Mecha, `$10` Incinerator Drone,
  `$20` Plated Beetle, `$40` arena da Sunchamber. Livre: `$80`.
- **Spec 16 verificada** (31/10/2026, `specs/16-titulo-e-demos.md`): as demos de atração desligadas (decisão do usuário: desligar)
  e o logo do título diz METROID / PRIME. Decisões a confirmar na spec (título parado fica parado; desenho do PRIME).
- (registro de 31/10) Próximo passo era a decisão do usuário depois da spec 16; o usuário aprovou a Magmoor (épico 17, fechado na
  17j: ver "Épico 17" acima e o fim deste arquivo).

## Épico 18 (Phendrana), 18a–18c, 03/11/2026

- **18a** (`specs/18a-espaco-8f-das-demos.md`): `build.RECLAIMED_8F` ganhou `$8F:8000–8ED3` no fim (ROM igual: first fit em ordem);
  `validate.check_reclaimed` aceita bytes de sala das demos só se `title.check_demos_off` passa na ROM construída (religar as demos
  vira erro ali e no `check_orphans`); faixa em `$8F:0000–7FFF` = "fora do banco". Experimento positivo (faixa primeiro, numa cópia):
  3122 bytes nela, validate limpo, A 34/34 e B 64/64. Livre no `$8F` para Phendrana: 695 + 3796.
- **18b** (`specs/18b-area-da-phendrana.md`): área 4 (Maridia). `VANILLA_PAUSE[4]` (tilemap `$B5:C000`, save `$82:C9F3` 4 ícones,
  elevador `$82:CA13`, rótulos `$82:C7AF` 3); listas de FX da área (`$83:ACE6` paleta: 3 objetos da Maridia; `$83:ACF6` tiles
  animados: 2 comuns + 2 da Maridia): nenhuma sala nossa da área 4 liga paleta nem os bits da Maridia (`check_phendrana_slot`). O mapa
  da área 4 rola 24 px a mais para a esquerda (`sm_82.c:1811`): conferir na 18e. A lista do mapa salvo da área 5 só muda de lugar
  no épico da Mines.
- **18c** (`specs/18c-grafo-e-mapa-phendrana.md`): `tools/phendrana/rooms.py` (dados; `ROOMS = []`), `research/prime_phendrana_locks.json`
  (o dumper grava também `env_fx` e `beam_only`), `check_phendrana`, `check_no_super_locks` (nenhuma porta verde nem bloco de super:
  a regra 3 do épico), `python3 -I tools/preview_rooms.py --mapa-phendrana`. Mapa visto de cima (x = norte → sul, y = oeste → leste);
  a P29 tem a porta R0 na tela de cima. Os dados mostraram 20 travas de evento e 1 porta key de qualquer feixe que o épico não listava
  (Desvios da 18c). Roteiros da busca do mapa: `scratchpad/s18c/layout_phen.py`, `gen.py`.
- **18d** (`specs/18d-estilos-do-gelo.md`): `tools/smlib/ice.py` — três caras em entradas da tabela de tilesets que nenhuma sala carregada
  usa: **neve** = `$01` (metatiles/gráficos do `$00`; `SNOW` = `crateria.SURFACE` sem a grama; linha 4 neve e gelo, linha 5 o céu; porta
  roxa na linha 6 numa cópia da tabela do `$00`), **ruínas de gelo** = `$1C` (gráficos do `$0C` e a cópia da tabela da Chozo; linhas 7 e 6
  em gelo), **laboratórios** = `$1B` (gráficos vanilla do `$04` e a cópia da tabela do tileset 4; linhas 4 e 5 em aço frio). O `$05` do
  épico foi trocado pelo `$1B`: a sala de demo `$CC6F` usa o `$05`. **Neve** = o FX dos esporos (tipo 8, `ice.SNOW_FX`, BG3 desce ¼ px por
  quadro; a chuva desce ~1,9) com as cores 9–10 da linha 1 (`SNOW_FLAKES`; nenhum tile do CRE as usa); `RoomDef.snow` (só na área 4, só
  os esporos no jogo); música `$1B/$06`. Validador: `ice.check`, `check_ice_in_rom`, `check_ice_test_rooms`, neve no `check_room`. ROM de
  teste `python3 -I tools/build.py --teste-18d` → `build/teste-18d/` (`tools/phendrana/testrooms.py`); testes `neve_medida`,
  `porta_de_onda_gelo`, `agua_medida_area_4` (o pulo na água da área 4 começa com os sub-pixels da Savestation: o alcance muda 1–3 px
  com eles). Prévia `--estilo-gelo`.
- **18e** (`specs/18e-elevadores-de-phendrana.md`): `tools/phendrana/layouts.py` (P0 e P29, 2×2, becos, salão nas telas de baixo, o poço
  **desce** da plataforma em x 7–8), `phendrana/rooms.py LOOK` (P0 neve com neve caindo, P29 ruínas de gelo), `FIRST_ROUND` 3; Magmoor
  P13/P27 com elevador subindo (`magmoor_rooms.ELEVATOR_ROOMS`, `TRANSPORT_TO` com as chaves); `areas.PHENDRANA` (área 4, estação 0 ao
  lado da plataforma da P0, lista do mapa salvo = a tabela, 57 bytes em +475), `ELEVATORS` + 2; "PHENDRANA / DRIFTS" (`areaselect.LABELS[4]`).
  Validador: `PRIME_ELEVATORS` + 2, `world_rooms` com Phendrana, `check_phendrana_rounds` (linha "phendrana (specs/18e)"), a guarda das
  rodadas vale para Phendrana, a linha das rodadas igual, `PHENDRANA_MIN_MAP_X = 3` (o mapa da área 4 rola 24 px a mais: medido, o mapa
  inteiro rola de `$0008` a `$0128`). A ROM de teste da 18d entrou na área de Phendrana (linha 25 do mapa, estação 7). Testes
  `elevador_phendrana_norte` (ida e volta, mapa, save, continue com o nome) e `elevador_phendrana_sul`. **Grupo C**
  (`TEST_GROUP_C`: `phendrana_`, `elevador_phendrana_` e os 3 da 18d; as partes novas da cadeia da 18n vão nele).
- **Verificação desde a 18e** (um comando por vez, **A → B → C**): `python3 -I tools/build.py` duas vezes (sha1 igual), `python3 -I
  tools/validate.py | tail -1`, `python3 -I tests/run_tests.py --grupo A` (~3 min), `--grupo B` (~4,5 min; carrega o estado da parte 1 da
  cadeia que o A salvou), `--grupo C` (~0,6 min; 10 testes desde a 18h).
- **Decisões da 18d/18e para o usuário (recomendadas, a confirmar)**: as cores das três caras (`ice.*_COLOURS`); neve = os esporos (a chuva
  ficou só na ROM de teste); música `$1B/$06`; a P0 com neve e a P29 nas ruínas de gelo; os elevadores descem em Phendrana; o grupo C.
- **18f** (`specs/18f-regiao-a-phendrana.md`): `tools/phendrana/layouts.py` (as 11 salas da região A; `zigzag` da Magmoor), `rooms.py`
  (`ACTIVE_REGIONS = {A}`, `LOOK` com as ruínas de gelo nas salas Chozo, `FIRST_ROUND` 3 em todas, `GATES` = porta de onda da Chapel do
  lado dela + bomb slot do Ice Temple como borda de Morph/Bombas, `FEATURE_GEOMETRY`, `BOSS_DOORS`), `items.py` (novo: 4 mísseis `$DA–$DD`,
  2 com `needs` Space Jump no alto das torres = trilhos de Spider). Validador: `world_items`/`ITEM_TABLES`/bits com Phendrana; a linha das
  rodadas (12m, 17j) **filtra Phendrana** (fica das três áreas até a 18n); `check_phendrana_rounds` com itens (linha "phendrana (specs/18e,
  18f)"); `check_phendrana_locks_mapped` (novo, linha "phendrana (specs/18f)": travas do Prime, a do Sheegoth esperando a 18h, eventos de
  camada fora, geometria só onde o Prime tem a feature, item de Space Jump só em sala com trilho/gancho/meio-tubo e item sem `needs` pegável a
  pé, neve = `SNOW_ROOMS`, nenhuma inundada/quente/com lava); `check_breakables` aceita a área 4. Testes (grupo C): `phendrana_regiao_a_rota`
  (os 4 mísseis andando, Space Jump nas torres), `phendrana_regiao_a_templo` (Temple Entryway, bomba no bloco, Chapel, porta de onda),
  `phendrana_save_station_b`. Caminhadas medidas com `s18f/scripts/{mv,hopx,try}.py`.
- **Decisões da 18f para o usuário (recomendadas, a confirmar)**: as formas das salas (torre sobre arco na Shorelines, saliência de gelo
  sobre a bacia da porta de chão, estátua no Ice Temple); o 2º míssil da Shorelines no buraco do lago congelado e o do "bloco de gelo" da Ice
  Ruins East num nicho a pé (os dados do Prime não têm gatilho de feixe ali); as caras (neve nas exteriores, ruínas de gelo nas Chozo e na
  Save Station B); a Chapel de 4×1 com chão plano (a arena da 18h pode mudar).
- **18g** (`specs/18g-inimigos-phendrana.md`): `tools/phendrana/enemies.py` (novo, molde da Magmoor: `ENEMIES` da região A, `STAND_IN`,
  `PRIME_LAYER0` de todas as salas, `ARENA_LATER` = a Chapel (18h), `PROPOSED_LATER` para B–E); `tools/chozo/bosses.py` `SpeciesCopy.health`
  e `ATOMIC_COPY` (`$A0:F8BF`: o orbe da Wrecked Ship com vida 100 e toque 20); `tools/frigate/enemies.py` `Species.homing`,
  `atomic_alpha`/`atomic_beta` (paleta 3, `hover` 32, velocidade 8 = ½ px por quadro, atravessa paredes); `areas.PHENDRANA.enemies`.
  Validador: `check_phendrana_enemies` (linha "phendrana (specs/18g)": justiça em toda rodada como a Magmoor, `homing_problems` = deriva a
  mais de 120 quadros das células de toda porta + 2 blocos, a arena livre, todo tipo decidido ou proposto). Testes: `entradas_de_porta_phendrana`
  (grupo C); as caminhadas da 18f medidas de novo com tiros (`P18G_*`, `P18F_TOWER_OFF`, `P18F_ACCESS`, `P18F_RUINS_DOWN`), busca em feixe
  `s18g/scripts/srch.py` (`fight.py` da 17g). Os inimigos voltam a cada visita: a rota mata a Zeela da saliência na segunda passagem.
- **Decisões da 18g para o usuário (recomendadas, a confirmar)**: Atomic = o orbe da Wrecked Ship vindo a ½ px por quadro; as contas
  (Shorelines 3 de 4, Ice Ruins East 2 de 4, Ice Ruins Access 2); sem cores de gelo nos inimigos; as propostas para B–E (Metroid
  enfraquecido na 18l precisa de uma tabela de vulnerabilidade própria, o Ripper do SM é imune ao Power Beam: 18m decide).
- **18h** (`specs/18h-sheegoth.md`): `tools/chozo/bosses.py` `SHEEGOTH` (cópia do Dessgeega `$DA3F` em `$A0:F8FF`: vida 800 e as
  vulnerabilidades `$B4:EC32` dele — Power/Wave/Ice sem carga = 0, míssil 100, carregado 60 —, toque 40, paleta de gelo em `$A3:F331`
  com rampas das texturas do Prime, CMDL `B1DAB41D`) e a 5ª entrada de `ARENAS` (`KILLS`, bit `$08`, `needs` = mísseis, prêmio = o míssil
  do altar `CHAPEL_ALTAR_MISSILE` (58, 7), bit `$DE`, rodada 3); `frigate/enemies.py` `sheegoth` e `sheegoth_baby` (Sidehopper pequeno,
  `boss`: somem no estado morto); `phendrana/enemies.py` `ARENA_ROOMS` + `ARENA_KINDS` (no lugar de `ARENA_LATER`); `DoorLink.dead_lock`
  e a porta de chefe em `phendrana/rooms.py` (lock `boss` + a de onda guardada para o estado morto); `build.py` `kills_arena_door` (cinza
  tipo 3 só no estado vivo, a tampa do Prime só no morto) e `Allocator.next_at` (o cabeçalho condicional cai na faixa das demos). Validador:
  `check_arenas`/`check_arenas_in_rom`/`check_epic_bosses` de **qualquer área** (`arena_area`, `epic_area_bosses`, bits únicos por área,
  justiça de Phendrana em toda rodada), linha nova "chefes de Phendrana (specs/18h)" (`EPIC_PHENDRANA_BOSSES`,
  `PHENDRANA_BOSS_CHILDREN_DONE`: a 18k acrescenta "18k" quando fizer o Thardus), a arena em `check_phendrana_enemies`, a porta da arena
  por estado na ROM. Testes: `phendrana_sheegoth` (a luta de verdade com mísseis, `SHEEGOTH_FIGHT` da busca `s18h/scripts/boss.py`, com
  estados salvos por nó; o estado exato do teste por `s18h/scripts/entry.py`), `phendrana_regiao_a_templo` com o atalho `poke 7ED82C 08`
  (a Chapel morta: a porta de onda). Movimento novo `S` (SELECT) em `MAGMOOR_MOVES`; logo depois de um `door_teleport` a Samus fica na
  pose 0 e o SELECT não troca a arma (dar um passo antes).
- **Decisões da 18h para o usuário (recomendadas, a confirmar)**: o Sheegoth imune ao feixe sem carga (o Dessgeega inteiro, 8 mísseis) em
  vez de vida cortada para o Power Beam; 2 Babygoths com as cores do SM (3–4 e cor de gelo pediriam outra cópia); a porta tranca (o
  `Actor Door Lock` do Prime) e volta a ser de onda; o míssil no meio do altar, a Chapel sem mudar de forma; o azul escuro do Sheegoth
  (o brilho do Dessgeega; o do Prime é mais claro).
- **18i verificada** (`specs/18i-regiao-b-phendrana.md`): `phendrana/layouts.py` região B (`west_cliff`: o penhasco oeste com zigue-zague
  da Shorelines nas salas com duas portas de um lado; os nichos cortados na face dele diante do 1º degrau); `ACTIVE_REGIONS = {A, B}`, a R0 da
  Ruins Entryway aberta. **Tampa de feixe dentro da sala** (`RoomDef.caps`/`Shape.caps`: x, linha de cima, parede, feixe; o build põe o PLM
  de `beamdoors`; `RoomDef.cap_blocks` grava no nível os blocos de tampa de porta: tipo C + 3 extensões D com BTS `$FF/$FE/$FD`, **sem eles a
  Samus atravessa a tampa**, medido); modelo: `Loadout.plasma`, `LOADOUT_FIELD[PLASMA]`, `validate.with_caps` (a pé e no flood fill), memo do
  passeio com o feixe só nas salas com tampa. **Porta de onda vertical** (`beamdoors`: `(WAVE, "B"/"T")` em `$84:FE00`, PLMs `$FE64/$FE6A`,
  `VERT_PAINT_METATILES` `$3F8–$3FE`+`$3EF` pintados só na tabela do tileset 4 = laboratórios; `paint_vertical`): **as regiões C e E têm 3
  ligações de onda verticais** (Quarantine Access ↔ North Quarantine Tunnel, Chamber Access ↔ Gravity Chamber, Hunter Cave ↔ Lake Tunnel):
  se caírem em sala de neve/ruínas, pintar `VERT_PAINT_METATILES` na tabela da neve (enchimento) ou das ruínas e incluir o tileset em
  `VERT_PAINT_TILESETS` (`check_vertical_wave_doors` recusa antes). Portas vermelhas: `PHENDRANA_MISSILE_BIT0 = $C2`, `MISSILE_BITS` (ordem de
  `GATES`; a região D acrescenta `$C4–$C6`). Inimigos: `STAND_IN` + Wall Crawler (zoomer `$DC3F`) e Babygoth (espécie `babygoth`, não de arena).
  Validador: `check_niche_caps` (linha "nichos (specs/18i)"), `check_vertical_wave_doors`, tampas na `check_gates`, `check_room` com a tampa
  aberta, `check_phendrana_locks_mapped` (item atrás de geometria só com a feature do Prime; item atrás de feixe só no gelo de plasma com
  tampa de plasma; estações exatamente nas salas do Prime: `EPIC_PHENDRANA_SAVES`/`EPIC_PHENDRANA_MAP`). Testes (grupo C, 13 em 43 s):
  `phendrana_regiao_b_rota` (caminhada por busca `s18i/scripts/srch.py`; o Plasma por RAM para a PB), `phendrana_save_station_a`,
  `phendrana_map_station`; `phendrana_red_door` (bit escrito no teste). `$8F`: **3194 bytes livres** na faixa das demos (+3 nas outras).
- **Decisões da 18i para o usuário (recomendadas, a confirmar)**: gelo de plasma = nicho com tampa laranja (ficam as colunas do batente
  depois de aberta); as formas (penhasco com zigue-zague, câmara do E-tank, Hydra em dois andares, Canyon com plataformas vazias); caras
  (ruínas nas salas Chozo, laboratório nas dos piratas, neve-exterior só na Canyon); inimigos = as propostas da 18g.
- **18j verificada** (`specs/18j-regiao-c-phendrana.md`): `phendrana/layouts.py` região C: North Quarantine Tunnel (6×4, terraços
  alternados `NQT_TERRACES` de cada parede até `NQT_SPLIT`: desce-se e sobe-se pelo meio), Quarantine Cave (6×2, penhascos com
  zigue-zague, câmara + túnel de Morph da L1 sob o penhasco oeste, **arena plana nas colunas 15–80 para o Thardus**), South Quarantine
  Tunnel (6×4, 11 degraus `SQT_STEPS` até o chão 58, zigue-zague `SQT_ZIGZAG` até a prateleira da R1), Quarantine Monitor (3×1, túnel de
  Morph diante da R0, míssil `QM_MISSILE`), P29 (o caminho até a R0: `P29_UP`, `P29_ZIGZAG`, `P29_SHELF`), Transport Access (2×1, pilar
  `TA_PILLAR` com nicho e `TA_CAP` de plasma, E-tank `TA_ETANK`); `ACTIVE_REGIONS = {A, B, C}`; `FIRST_ROUND` 3 (a TA 4); `GATES`: onda
  nos lados do Prime (NQT ↔ Quarantine Access só do lado da NQT, vertical), gelo P29 ↔ TA, `Gate({MORPH}, (), (QC, QM))`. **Pintura
  vertical na neve**: `build.ice_metatiles` pinta `VERT_PAINT_METATILES` também na cópia do `$00`; `validate.VERTICAL_WAVE_TILESETS` (4,
  `$1B`, `$01`); `check_ice_in_rom` lê a pintura vertical na tabela da neve da ROM independente do build; `ice.check` confere o enchimento.
  As **ruínas de gelo (`$1C`) ainda não têm a porta vertical**: a região E (Chamber Access ↔ Gravity Chamber, Hunter Cave ↔ Lake Tunnel)
  pinta lá se cair nelas. Regra nova em `check_phendrana_locks_mapped`: da entrada de cada porta de Morph do Prime, sem a Morph, menos
  lugares. Teste (grupo C, 14 em ~1 min): `phendrana_regiao_c_rota` (caminhadas por `s18j/scripts/srch.py` e `hopx.py`; Ice e Plasma por
  RAM). `$8F`: **2892 bytes livres** na faixa das demos (+303 nesta filha).
- **Decisões da 18j para o usuário (recomendadas, a confirmar)**: a Monitor só pelo túnel de Morph (sem a borda do gancho do Prime: a L1
  fica no chão); as formas (NQT de terraços — parece um pouco estacionamento —, SQT de degraus, QC plana, pilar de gelo da TA); neve nas 5
  salas novas, a P29 nas ruínas; orbes nas contas do Prime.
- **18k verificada** (`specs/18k-thardus.md`): `chozo/bosses.py` `THARDUS = SpeciesCopy($F93F, $EEFF, 8, health=400)` e a arena
  `Arena("phendrana_quarantine_cave", $10, BOSS_BIT, $04, None, music=(24, 03))`; **o código dos Torizos corrigido no lugar**
  (`torizo_patches`, como o Spore Spawn): `TORIZO_AREA_READS` (as 7 leituras de `$079F` em `$AA` → constante 0: o jeito do Bomb Torizo
  em qualquer área; some o atalho de depuração `$C0C0`), `TORIZO_HAZE` (NOPs no `JSL $88:DD32`: a bruma lavava as cores e escondia a
  neve), `TORIZO_SPOT` (a posição da tabela do init = `Species.fixed` do `thardus`, (776, 368)), `TORIZO_PALETTES` e o pulso do peito
  `TORIZO_PALFX` (`$8D:E2F1`) nas rampas das texturas do Prime (`THARDUS_ROCK/SNOW/GLOW`). Sem o PLM da estátua `$84:D6EA`: acorda quando
  a sala carrega. A morte do Torizo **não** conta na cota de mortes (medido): a condição é o bit `$04` (`TORIZO_BIT`) e as portas são
  cinza de **tipo 2** (`GREY_DOOR_TORIZO`); `build.kills_arena_door` virou `arena_door_alive_cap` (KILLS → tipo 3, Torizo → tipo 2; o
  `dead_lock` no estado morto). `phendrana/enemies.py`: o Thardus sozinho (VRAM inteira), `PRIME_BOSS_LAYERS` (o Thardus é da camada 3).
  Validador: `check_torizo`, `torizo_arena`, patches/cores/leituras na ROM, o `$04` como condição só numa arena de Torizo, o Golden
  Torizo proibido, inimigo de arena fora de `ARENA_ROOMS` = erro, linha "chefes de Phendrana (specs/18h, 18k)". Testes (grupo C, 15 em
  55 s): `phendrana_thardus` (luta achada por busca, `s18k/scripts/boss.py`/`entry.py`; subida até a R0 `THARDUS_CLIMB`, medida);
  `phendrana_regiao_c_rota` com o atalho `poke 7ED82C 10`; o `entry_audit` ganha a arena por RAM ao sair dela por porta de chefe.
  `$8F`: **2846 bytes livres** na faixa das demos (+46); `$A0` livre a partir de `$A0:F97F`.
- **Decisões da 18k para o usuário (recomendadas, a confirmar)**: nenhum prêmio (decisão 3 à letra); dificuldade = vida 400 e o toque do
  Torizo (8; a luta é fácil na rodada 3, alternativa: toque até 40); acorda na entrada; a música do Torizo (set `$24`) em vez da de
  mini-chefe; cores de pedra com peito branco-gelo; a porta de Morph para a Monitor não tranca (como no Prime).
- **18l verificada** (`specs/18l-regiao-d-phendrana.md`): região D, 12 salas (`tools/phendrana/layouts.py`: Observatory Access,
  Observatory (`west_cliff` + o espelho na parede leste; a câmara do projetor no alto atrás de `OBS_BOMB`), West Tower Entrance, Save
  Station D (estação 3), West/East Tower, Control Tower (neve), Aether Lab Entryway (luminária `ALE_FITTING`: o orbe em cima, mais de
  60 px acima das portas), Research Lab Aether (laje + tanque com o E-tank), Research Core Access, Research Core (núcleo + poço,
  `RC_ZIGZAG`), Pike Access (L0 parede até a 18m)); `ACTIVE_REGIONS` ABCD; `GATES`: `$C4` Observatory → Save D, `$C5` WTE ↔ WT (um bit
  para os dois lados), 9 ligações de onda, gelo Research Core ↔ Pike Access (Pike Access na rodada 4). **Super Missile**:
  `tallon/items.py` `SUPER_MISSILE_TANK = $EEDF`, `GRANTS` → `tallon/rooms.py SUPER` (nenhuma trava o pede), `validate.ITEM_GAIN`
  `$EEDF` = 5 supers; regra nova: o único Super Missile do jogo é o do Observatory (`EPIC_PHENDRANA_SUPER`). **Metroid**:
  `chozo/bosses.py METROID` (`$A0:F97F`), `SpeciesCopy.touch/shot/vulnerability` (`build_copies` põe a IA de tiro de 6 bytes no `$A3` e a
  tabela de 22 no `$B4`); `validate.species_info` lê a tabela da cópia e trata o Metroid vanilla (ou cópia sem a IA) como imune e de
  toque sem teto (`METROID_SOURCE`, `DRAIN`); `frigate/enemies.py` `metroid` com `Species.chase = 3`; `chaser_problems` (fora da
  câmera de toda porta) e a regra "todo Metroid declara chase ≥ 3". Testes (grupo C, 17 em ~1 min): `phendrana_regiao_d_rota` (o
  super disparado abre a porta vermelha; 4 Metroids mortos sem dano, com o Wave da rodada 3), `phendrana_save_station_d`; caminhadas
  achadas por busca em feixe (`s18l/scripts/seg.py`). `$8F`: **2146 livres** na faixa das demos; `$A0` livre a partir de `$A0:F9BF`.
- **Decisões da 18l para o usuário (recomendadas, a confirmar)**: o Metroid **não agarra** (toque comum de 20; um agarrar com dreno
  limitado pediria código novo); 3 Metroids no Research Core e 1 na Aether (as contas do Prime), mortos com 5 tiros do Power Beam; 1 orbe
  na Aether Lab Entryway (o Prime tem 3; a sala tem 1 tela); a porta WTE ↔ West Tower com um bit para os dois lados; a Control Tower de
  neve e a Pike Access na cara de neve sem neve caindo; o Super Missile no alto do Observatory atrás de bloco de bomba.
- **18m verificada** (`specs/18m-regiao-e-phendrana.md`): região E, 14 salas (`tools/phendrana/layouts.py`: Frozen Pike (lajes
  nas linhas 10 e 26, vão `PIKE_GAP`), Frost Cave Access, Hunter Cave Access, Frost Cave (`FROST_MISSILE` no lago seco), Save Station C
  (estação 4), Hunter Cave, Upper/Lower Edge Tunnel, Chamber Access, Lake Tunnel, Phendrana's Edge (`EDGE_PB`: a câmara da R2), Gravity
  Chamber (`GRAV_STAIR`, `GRAV_LEDGE`), Storage Cave, Security Cave (`SEC_PB_BLOCK`)); `ACTIVE_REGIONS` ABCDE (as 56 salas);
  `rooms.FLOODED = {gravity_chamber}` → `RoomDef.water`; `GATES`: 15 ligações de onda, plasma Edge ↔ Storage, Morph + Power Bomb Edge ↔
  Security; itens bits `$E7–$EA` (Frost Cave 4, Gravity Chamber 4 e 5, Security Cave 6); inimigos: 2 Beetles + 1 zoomer na Frost Cave
  Access, orbes na Lower Edge Tunnel (2) e na Lake Tunnel (1); `STAND_IN` com o Ripper, as Jelly Zaps, o Drone, os Flying Pirates e as
  Spank Weeds = None, `PROPOSED_LATER` vazio. Validador: `check_tallon_water` com `phendrana_rooms.FLOODED`, `EPIC_PHENDRANA_FLOODED`,
  `check_power_bomb_blocks` em Phendrana, a porta de Morph × cada item de geometria da trava (mutação V11), "todas as 56 do Prime" na
  linha da 18c. Testes (grupo C, 20 em ~1 min 15 s): `phendrana_regiao_e_rota`, `phendrana_regiao_e_agua` (o tiro para baixo no ar abre
  a tampa de uma porta de chão; o pulo debaixo d'água sem a suit sobe a escada; o Space Jump com a Gravity até a borda, achado por
  `s18m/scripts/sjsearch.py`), `phendrana_save_station_c`; `TA_CAP_SLOT` 37. `$8F`: **1282 livres** na faixa das demos.
- **Decisões da 18m para o usuário (recomendadas, a confirmar)**: o Ripper fora (imune a todo feixe, como o do Prime; alternativa: uma
  cópia que o feixe mata); o míssil da borda da Gravity Chamber pede Gravity + Space Jump (rodada 5; alternativa: rodada 4); a porta de
  Morph da Security Cave com bloco de Power Bomb dos dois lados; a região toda na cara de neve; as formas (a Pike em dois andares, a
  Gravity Chamber com escada de rocha).
- **18n verificada (04/11/2026; épico 18 fechado)** (`specs/18n-rodadas-e-cadeia-quatro-areas.md`): `check_world_rounds` anda e confere
  as quatro áreas (o filtro de Phendrana da 18f saiu): linha **"rodadas (specs/12m, 17j, 18n): Tallon + Chozo + Magmoor + Phendrana
  andados juntos, 75 itens em 7 rodadas … (0: 2 + 1 + 0 + 0; 1: 4 + 7 + 0 + 0; 2: 1 + 11 + 0 + 0; 3: 2 + 8 + 4 + 11; 4: 2 + 1 + 1 + 2;
  5: 7 + 0 + 0 + 1; 6: 2 + 3 + 2 + 3); elevadores … phendrana_north 3 (da Magmoor), phendrana_south 3 (da Magmoor); … 75% (energia
  1299, mísseis 235, super mísseis 5, power bombs 25)"**; a linha do Tallon igual; `check_epic_phendrana` (linha "phendrana (specs/18,
  épico fechado na 18n)": 56 salas, 59 ligações, os 17 itens por sala do Prime, nada no lugar da Boost/Spider/Thermal/artefatos, as
  PBs na 6, 88 travas, neve nas 23, só a Gravity Chamber inundada, 2 elevadores, 4 saves + map, 2 chefes). A cadeia
  (`tests/run_tests.py`): `FullChain` com Phendrana e o Super Missile (o lugar 2 do HUD no `select`, os super mísseis na passagem);
  os testes das regiões viraram pedaços (`phendrana_a_to_*`, `_b_to_*`, `_c_to_*`, `_d_to_*`, `_e_to_*`; roteiros dos testes
  idênticos); passos novos `fc_round_3_phendrana_up/_a/_sheegoth/_shore/_ruins/_labs/_quarantine/_thardus/_down`,
  `fc_round_4_phendrana`, `fc_round_5_phendrana`, `fc_round_6_phendrana`, `fc_ending`; as lutas `CHAIN_SHEEGOTH_FIGHT` (10 mísseis,
  -40) e `CHAIN_THARDUS_FIGHT` (só o feixe, -5) buscadas do estado da cadeia (`s18n/scripts/boss.py`, agora rodando cada sequência
  inteira da entrada); caminhadas buscadas de novo onde a entrada da cadeia difere (`CHAIN_PIKE_MID`, `CHAIN_LAKE`, `CHAIN_LAKE_5`,
  `CHAIN_TA_6`, `CHAIN_FROST_UP_6`, `CHAIN_GRAV_*`, as plataformas P13/P27/P29). `CHAIN_PARTS` em 4 (A, B, C, C): a parte 2 termina na
  Workstation; a 3 = Phendrana na rodada 3 e o Ice; a 4 = rodadas 4–6, o fim e a tela do fim. **A tela do fim**: a nave do Tallon com o
  evento `$0E` por RAM decola para o fim do SM; no fim dos créditos `CalcItemPercentageCount` escreve os dígitos no tilemap da WRAM
  (`$7E339E/$33A0`, tabela `$8B:E741`): "75%" conferido (`ending_digits`) e fotografado (`specs/img/18n-fim.png`). Mutações V1–V12, T1–T5,
  E1–E4 pegas (`s18n/mut/`). Grupos na pasta real: A 34/34 em 3 min 0 s, B 63/63 em 3 min 20 s, **C 22/22 em 5 min 30 s**.
- (registro de 04/11) **Próximo passo era: nenhum planejado** (o épico 18 fechado); em 05/11/2026 o usuário aprovou a **Phazon Mines**
  (épico 19: seção abaixo). **Decisões do usuário em aberto** (continuam):
  - da 18n: o grupo C em 5 min 30 s (acima dos ~5 min que o épico pedia) ou um grupo D só com a parte 4 da cadeia; a tela do fim do SM
    com o evento `$0E` posto por RAM (o jogo ainda não tem fim próprio: o do Prime vem depois da Impact Crater); a rodada 3 subindo
    para Phendrana pela Shore Tunnel (`rise_through`, atalho já usado) com o Ice do Tallon no fim da rodada 3;
  - do épico 18, padrão aceito a confirmar: a área 4 (Mines na 5, Impact Crater na 0), as três caras com neve, o Metroid do SM
    enfraquecido; e as decisões das filhas 18d–18m (cores, neve = esporos, música; formas; o orbe que deriva; o Sheegoth imune ao feixe
    sem carga e 2 Babygoths; o gelo de plasma = nicho com tampa; o Thardus sem prêmio; o Metroid sem agarrar; o Ripper fora, a borda da
    Gravity Chamber na rodada 5): lista em "Verificação do épico" de `specs/18-phendrana-drifts.md`;
  - de antes: a cor final das ruínas (épico 12), os Chozo Ghosts (14e), as decisões a confirmar da Magmoor (17d–17j) e das filhas
    14b–14d, 16, 12i–12m;
  - a próxima etapa (Phazon Mines na área 5? Impact Crater? os ataques próprios da Parasite Queen?): o usuário escolhe.

## Épico 19 (Phazon Mines), 19a–19h, 05–06/11/2026

- **19a** (`specs/19a-espaco-8f-e-a1.md`): `build.RECLAIMED_8F` ganhou `$8F:C215–C8C6`, `$8F:AD5C–B218`, `$8F:A6A1–A97A`, `$8F:CAAE–CCC7`
  no fim (+4195; 274 bytes de salas das demos); `build.RECLAIMED_A1 = (($A1:AD09, $A1:CCD3),)` (8139; 553 de demos), o alocador do `$A1`
  usa a faixa só depois do `FREE_A1` cheio (ROM igual); `build.ours_a1`. `validate.check_reclaimed` nos dois bancos (linha nova "$A1
  recuperado"), `check_orphans` aceita população nossa na faixa, e a população nossa na faixa tem de ser uma que o build escreveu.
  **Armadilha**: as faixas novas guardam **cabeçalhos de salas das demos** (`$AF14`, `$AFFB`, `$B106`, `$CC6F`); quando o build escrever
  ali, essas salas deixam de existir: `validate.demo_rooms_kept` (o gelo e as ruínas leem só as intactas). Experimento positivo (faixas
  novas primeiro, `FREE_A1` de 1 byte): 4114 bytes de populações e as 4 faixas do `$8F` cheias, validate limpo, grupo A 34/34.
- **19b** (`specs/19b-area-da-mines.md`): área 5 (Tourian). `VANILLA_PAUSE[5]` (tilemap `$B5:D000`, máscara `$82:9C27` — **a mesma da
  área 7**, debug: `build.DEBUG_AREA`, a trava do `write_pause_map` aceita —; **sem lista de chefe** (ponteiro 0); **map station vazia**
  `$82:CA4F` = `FFFF`: a 19e dá uma lista nova no `$82` livre; save `$82:CA51` 8 entradas; elevador `$82:CA71` 8; rótulo `$82:C7C3` 1).
  `mapsave.FREE_81`/`MOVES_TO_81`/`list_at`: a lista da área 5 com mais de 21 bytes vai para `$81:EF1A` e o ponteiro `$81:82D6 + 10`
  aponta para ela (`build.write_map_save_lists`; ensaio no scratchpad). **A entrada 0 da lista de paleta da área 5 é o calor `$F761`**:
  nenhuma sala nossa da área 5 liga bit de paleta (`own_fx_bits`). Bits de chefe vanilla da área 5: só `$04` (portas cinza de tipo 2 de
  2 salas órfãs); as arenas planejadas `$08` e `$10`. `check_mines_slot`, linha "mines (specs/19b)". SRAM livre 748.
- **19c** (`specs/19c-grafo-e-mapa-mines.md`): `tools/mines/rooms.py` (dados; `ROOMS = []`), `research/prime_mines_locks.json` (o dumper
  grava também `key_vuln_full`, a vulnerabilidade inteira da porta, e `pb_only`, o que só a Power Bomb fere: lida dos bytes, +222 na
  `Platform`), `check_mines`, `check_no_grapple_locks` (nenhum bloco de gancho tipo `$E`, nenhuma espécie com reação `$8005/$8014/$8019`:
  a regra 3a do épico), `python3 -I tools/preview_rooms.py --mapa-mines`. Mapa em **faixas por nível** (A em cima, B no meio à direita, C
  no meio à esquerda, D embaixo), colunas 17–47, linhas 8–22; as portas dos 2 elevadores na tela de baixo (regra da busca). Os dados
  mostraram 15 travas de evento, nenhuma doca de Morph (o túnel da Waste Disposal é dentro da sala) e um objeto de PB a mais na Ore
  Processing (Desvios da 19c). Roteiros da busca: `scratchpad/s19c/layout_mines.py`, `run_many.sh`, `gen.py`.
- **Scratchpad**: copiar o projeto **com a pasta `.claude/`** para dentro do scratchpad fez outro processo do Claude Code apagar a pasta
  da sessão (três vezes). Para experimentos numa cópia: `rsync … --exclude .claude --exclude research/prime_fs --exclude build`.
- **19d** (`specs/19d-estilos-da-mina.md`): `tools/smlib/mines.py`, base pirata `$0E` e rocha `$08`; até a 19e só a ROM de teste.
- **19e** (`specs/19e-elevadores-da-mines.md`): `tools/mines/layouts.py` (P0 1×2 e P25 1×3: salão na tela de baixo, o poço sobe até o
  topo), `mines/rooms.py` (`LOOK`, `FIRST_ROUND` P0 = 5, P25 = 4, `ROOMS` = as 2 salas), `areas.MINES` (estação 0 ao lado da plataforma
  da P0; `save_map_rooms` = a tabela inteira, 39 bytes → `$81:EF1A`), `ELEVATORS` + 2 (**a Mines embaixo**: `tallon/layouts.py`
  `transport_mines_east` com `ride=True`; `magmoor/layouts.py` `transport_mines_west` **desce** agora, o poço de enfeite que subia saiu;
  `magmoor_rooms.DECORATIVE_ELEVATORS` vazio), `areaselect.AREA5_LABEL` "PHAZON / MINES" (`$3E`, era `$82:CCE4` "TOURIAN"); o build
  escreve as entradas `$0E/$08` quando a área 5 tem sala; a ROM de teste da 19d põe as 4 salas numa **cópia** da `MINES`
  (`mines/testrooms.area()`, estação 7). Validador: `check_mines_rounds` (linha "mines (specs/19e)", `EPIC_MINES_LIFT_ROUNDS`), a linha
  das rodadas **sem** os 2 elevadores novos (igual; entram na 19m), `VANILLA_SHARED` com o fundo `$8F:E454` (o da rocha `$BAF4` entra
  com a primeira sala de rocha), `check_epic_magmoor` com pares sem ordem. Testes: **grupo D** (`TEST_GROUP_D`: `mines_`,
  `elevador_mines_`, `porta_de_plasma_mina`, `entradas_de_porta_mines`; conferido antes do B e do C em `group_of`); `elevador_mines_leste`
  (ida e volta, mapa, save, game over com **os cinco nomes** — `check_five_labels` —, continue com o bit da Mines salvo pelo `$81`),
  `elevador_mines_oeste` (o poço de 3 telas). Ajustados: `magmoor_regiao_c_itens` (o fim agora desce até a P25) e
  `mapa_da_tourian_sobrevive_ao_save` (os bytes da lista da Mines). Mutações em `scratchpad/s19e/` (13 do validador, 6 de ROM, 4 do
  emulador). **A lista de ícones de map station da área 5** continua a vanilla `FFFF`: a 19i faz a nova no `$82` livre (ponteiro
  `$82:C7FB + 2·5`) junto com a Map Station Mines.
- **19f** (`specs/19f-regiao-a-mines.md`): `tools/mines/layouts.py` (as 13 salas da região A: rocha na Quarry Access, Main Quarry,
  Waste Disposal e Ore Processing, base pirata no resto), `mines/rooms.py` (`ACTIVE_REGIONS = {"A"}`, `LOOK`, `FIRST_ROUND`: tudo na
  rodada 5 menos a Storage Depot A na 6; `GATES`: as tampas de feixe do Prime dos dois lados, a borda de Morph da Waste Disposal, a de
  Morph + Power Bomb da Mine Security Station; `FEATURE_GEOMETRY`, `PB_NOTHING`, `BOSS_DOORS` com a da Elite Research esperando a 19h),
  `tools/mines/items.py` (novo: bits `$EB–$EE`: míssil da torre da Main Quarry `needs` Space Jump, míssil do nicho de PB da Security
  Access A rodada 6, **Grapple Beam** `$EF17` na Storage Depot B, míssil da Elite Research), `tallon/items.py` `GRAPPLE_BEAM`/`GRANTS`
  (`tallon/rooms.py GRAPPLE`). Validador: `world_items`/`ITEM_TABLES` com a Mines, `ITEM_GAIN[$EF17]` = bit `$4000`; **a linha das
  rodadas com os itens da Mines** ("rodadas (specs/12m, 17j, 18n, 19f)": 79 itens, 79%, coluna Mines); `check_mines_rounds` com itens e
  o Grapple único (`EPIC_MINES_GRAPPLE`); **`check_mines_locks_mapped`** (novo; blocos de PB só onde o Prime tem PB_ONLY); o tileset de
  cada estado da área 5 = a cara da sala; `VANILLA_SHARED` + o fundo da rocha `$BAF4`. **O nível da Main Quarry cruza `$E1:FFFF`**: o
  teste gerado `nivel_cruza_banco_mines_main_quarry` (grupo B) agora chega à Mines. Testes (grupo D): `mines_regiao_a_rota` (a região a
  pé, o Grapple com o HUD: SELECT mísseis → super mísseis → gancho, `$09D2` = 4), `mines_regiao_a_rodada_6` (bomba não quebra PB, PB
  quebra; porta de plasma), `mines_save_station_a`. **`CHAIN_GROUP` = A, B, C, D** (a parte 4 da cadeia no grupo D; ordem A → B → C → D).
  Truques: um tiro numa porta logo depois de virar (`M19F_TURN_SHOT`: `hold LEFT 4`, `wait 10`, `hold X 2`): com `LEFT+X` no mesmo
  quadro ela vira e o tiro sai para o outro lado; embaixo de uma plataforma de porta de teto precisa de mais de 3 linhas para pular nela.
  Mutações em `scratchpad/s19f/` (22 do validador, 5 de ROM, 5 do emulador). Roteiros das caminhadas: `scratchpad/s19f/scripts/drv.py`
  (estado salvo na P0), `hop.py` (busca dos quadros de cada pulo), `route.py`/`segs.py` (a rota por pedaços).

- **19g** (`specs/19g-inimigos-mines.md`): `tools/mines/enemies.py` (novo: `ENEMIES` da região A — Main Quarry 2 piratas em (45, 7) no
  braço do guindaste e (77, 42) no chão a leste da torre; Elevator Access A 2 orbes `atomic_beta` em (4, 11) e (12, 26) —, `STAND_IN`,
  `PRIME_LAYER0` das 42 salas, `ARENA_ROOMS` = Elite Research 19h e Elite Quarters 19k, `PROPOSED_LATER` para B–D), `areas.MINES.enemies`,
  `frigate/enemies.py` `Species.fires` (o `pirate` com 16). Validador: **`check_mines_enemies`** (linha "mines (specs/19g)"; justiça em toda
  sala, deriva, câmera, propostas justas, arenas) e **`shooter_problems`** (o pirata fora da câmera de toda porta ou fora da altura da
  Samus nela). **Armadilhas**: o laser do pirata atravessa paredes; o Ice Beam congela o orbe e os tiros seguintes não tiram vida (a rota
  usa míssil: `M19G_ORB_WEST`/`M19G_ORB_EAST`, HUD de volta com `M19G_HUD_OFF`); logo depois da porta o míssil passa pelo orbe (esperar 30
  quadros); `tallon_look` ganhou `settle` (as fotos dos piratas aos 110 quadros: aos 60 a volta da pausa não terminou e a tela fica
  corrompida). Testes (grupo D, 9): `mines_inimigos_vivos`, `entradas_de_porta_mines`. Mutações em `scratchpad/s19g/` (17 do validador,
  3 de ROM, 5 do emulador; auditoria forte de 600 quadros). Roteiros: `s19g/scripts/drv.py`, `trace.py` (inimigos e Samus quadro a
  quadro).
- **19h** (`specs/19h-phazon-elite.md`): `chozo/bosses.py` `PHAZON_ELITE` (cópia do `$F593` em `$A0:F9BF`: vida 400, toque 40,
  `ELITE_VULN` = a tabela do dourado com Power/Wave/Ice/Ice+Wave a `$82`, cores `ELITE_ARMOUR/PHAZON/GLOW`), `ninja_patches` (o operando
  do `LDA $8727,Y` em `$B2:F692` → a paleta do salto em `$B2:FECA`; `$B2:8727` fica), `ninja_leap`, `NINJA_EPROJS` (garras 20) e a arena
  `mines_elite_research` (`KILLS`, bit `$08`, sem prêmio); `build.py` com o alocador `$B2:FEAA`; `frigate/enemies.py` `phazon_elite`
  (set de paleta 1: o código volta à linha 1 depois do salto); `mines/enemies.py` `Spawn(PE, 28, 26)`, `ARENA_KINDS`, `PRIME_BOSS_LAYERS`;
  `mines/rooms.py` a regra de porta de chefe de Phendrana (a T3 vira `boss` com a de gelo como `dead_lock`). Validador: `check_ninja`,
  paleta do salto e tampas por estado na ROM, justiça da Mines em toda rodada nas arenas, tipos da arena, linha "chefes da Mines
  (specs/19h)". Testes (grupo D, 10): **`mines_phazon_elite`** (`ELITE_FIGHT = "LLLLLLLLCCL"`, `MAGMOOR_MOVES["C"]` = tiro carregado,
  `ELITE_CLIMB` medido da parede leste); `mines_regiao_a_rota` com `MINES_ELITE_WON_BY_RAM`. **Armadilhas**: o ninja do SM **não** pede
  sala de uma tela (o código não lê paredes); uma cópia perde o rebote e os 5 itens do dourado (só o ponteiro `$F593` os tem); **o
  sistema de arquivos ignora maiúsculas** (na busca em feixe, os estados `…r` e `…R` eram o mesmo arquivo: nomes com `_`); a
  `M19F_ELITE_UP` da 19f só serve vindo do oeste correndo. Roteiros e mutações em `scratchpad/s19h/` (`boss.py`, `climb.py`,
  `robust.py`, `mutate_h.py` 14+1, `mutate_rom.py` 5, `mutate_emu.py` 4).
- **19i** (região B, verificada em 06/11/2026): ver `specs/19i-regiao-b-mines.md` e o épico ("Desvios").
- **19j** (região C, verificada em 09/11/2026): 5 salas (`tools/mines/layouts.py` "region C"), `ACTIVE_REGIONS` = A, B, C; as portas de
  gelo e plasma em `GATES`; a trava da Maintenance Tunnel (19i) passa a valer (V2b: sem ela o Tallon fica alcançável na rodada 4 pela
  Magmoor); a Maintenance Tunnel na rodada 4 (o pedaço entre a L0 e a parede); itens `$F3` (míssil do PPC no fosso de PB) e `$F4`
  (E-tank da Processing Center Access); nenhuma regra nova no validador. Teste (grupo D, 15): `mines_regiao_c_rota` (as caminhadas do
  PPC são as da Omega Research: `M19I_DOWN_EAST`, `M19I_OR_UP`, `M19I_PIT_OUT`). Roteiros e mutações em `scratchpad/s19j/`
  (`mutate_j.py` 13+1, `mutate_emu.py` 2, `rooms_img.py`, `sheet.py`).
- **Próximo passo: 19k** (o Omega Pirate).

## Pendências e ideias (nenhuma pedida ainda)

- Tallon: épicos 07 e 09 fechados (09f): as 44 salas e os 13 itens do Tallon (+ os 7 de trava) pegos no jogo. Próximos
  passos possíveis (nenhum pedido): outro mundo (Chozo Ruins: `$8F` com 1821 bytes livres não basta, ver o
  risco do épico), itens de trava, ou camadas de evento. Regiões D e E e Gully/Alcove: nada alcançável a pé;
  testes da região E começam na estação 1 e descem a fragata por teleporte até a Hydro Access. Região D: nada alcançável a pé até existirem gelo, Gravity Suit,
  Wave/Thermal; testes entram pela estação 1 (carregar por RAM: `$079F`/`$078B`/`$7ED914`=5/`$0998`=6) e
  por teleporte de porta (`$099C`=`$E17D`, `$078D`, `$0998`=9; `door_teleport` em `tests/run_tests.py`).
  Subir por porta de teto em sala seca (spec 08; 10b): com `$02A0` guiando para a borda do outro lado do buraco ela ainda cai
  de volta partindo do quarto de fora da porta (28 de 160 na varredura da 10b); sem direção cai sempre (buraco aberto, como no
  SM). `$02E0`/`$0300`/`$0340` quebram as fugas da fragata (cabeça debaixo do degrau do poço); o resto pede geometria (borda mais
  baixa ou buraco mais estreito nas 18 portas de chão) — ideia, não pedida. Inimigos fora das contas da camada 0 do Prime nas salas
  vazias (Crash Site, Artifact Temple, Reactor Core…): decisão do usuário (épico 10, A8). Camadas
  de evento do Prime (Beetles do 1st pass da Root Cave/Crash Site, piratas da Crash Site) pedem estados
  de sala por evento: fora até agora (Life Grove: Chozo Ghosts, Spank Weeds). Itens das fases 1–6 estão
  na ROM; desde a 09b gelo, Wave, Plasma e Gravity existem como item, mas o gelo fica numa borda de Space
  Jump e o Space Jump atrás das paredes de Bombas da Gully; desde a 09d (Morph + Bombas) a pé, da nave, as 44 salas e os
  19 itens com lugar; desde a 09e os 20 (Power Bomb na Mines East, X-Ray atrás da cabana de PB). Épico 09 fechado na 09f (rodadas declaradas, `stuck` por rodada,
  `tallon_cadeia_completa`); épico 07 fechado junto. Artefatos fora. Água só na fragata
  afundada (sala inteira); lagos e poças das outras regiões secos (água parcial mudaria o pulo medido). Rotas cegas dos testes passam pelo lago da Landing Site (pegam o míssil).
- Teste `tallon_rota_bc` usa nº de ciclos medido por trecho: mexer nas salas do caminho pode pedir
  novo ajuste (o verificador mostra a sequência de salas obtida).
- Salas vanilla (etapa 11, `specs/11-limpeza.md`): as 262 sem caminho nenhum (o validador prova com `check_orphans`; as 19 das demos de
  atração também desde a spec 16, que desligou as demos). Nada foi apagado; o espaço que só elas usam está medido na
  linha "órfãs" do validador. **Chozo Ruins** (64 salas, 136 portas no Prime): desde a 12a o `$8F` cabe (1781 livres + 2254 do bloco
  recuperado = 4035 para ~3500; mais pedaços órfãos medidos no épico 12 se faltar; a 12e usou 145). **Épico 12 fechado (12m, 28/10/2026).** Épico 14 (chefes) fechado (14f, 31/10/2026). **Próximo passo: decisão do usuário** (ver o fim da seção "Etapa dos chefes"). Itens abertos do usuário: a cor final das ruínas (pergunta 8 do épico 12) e os padrões a confirmar das filhas 12i–12m (lista no épico). Feitas: 12g2, 12h, 12i (região B), 12j (região C, Varia, Magma Pool quente, Save Station 2), 12k (região D, Charge Beam) e 12l (região E, as 64 salas). Era: 12f (região A da
  Chozo: a Transport North ganha a porta R1 para a Ruins Entrance — a parede do salão, já no batente —, save, música e fundo das ruínas,
  nome na tela de continue); depois 12g–12m, uma região por vez, cada uma verificada antes da próxima; chefes numa etapa no fim. Abertas
  no épico: água (7), confirmação final da cor (8), demos (10).

## Mapa do código

- `tools/areas.py` — as áreas do jogo (`AreaDef`: número, nome, salas, tileset/música/fundo padrão,
  load stations, inimigos, objetos, recolor, sala do chefe). `FRIGATE` (área 3) e `TALLON` (área 0, desde a 07g); build,
  validate, prévia e testes percorrem `AREAS` (spec 07a). Chave de sala é global: áreas novas usam
  prefixo (`tallon_...`).
- `tools/build.py` — monta a ROM (alocadores da expansão `LEVEL_BANKS`/`FIXED_BANKS`, spec 09c; `--cruzar-banco SALA`): salas, portas, load stations, save/map station, mapa de pausa,
  timer de fuga, Meta Ridley e nave (`ending.meta_ridley`/`ending.gunship`), cores e forma da Parasite
  Queen (`bosses.py`, `queen_art.py`).
- `tools/frigate/rooms.py` — salas (tamanho, posição no mapa, portas, save/map station, nave);
  `RoomDef` também serve ao Tallon.
- `tools/tallon/rooms.py` (tabela das 44 salas, regiões, `ACTIVE_REGIONS`/`ACTIVE_ROOMS`, travas e
  rodadas `FIRST_ROUND` (09f), salas inundadas `FLOODED` da 07l), `tools/tallon/layouts.py` (desenhos das salas construídas), `tools/tallon/items.py` (itens,
  bits, lugar e rodada (`Item.round`, 09f); spec 07h; itens de trava e `gravity_patch` da cena da Gravity, 09b) e `tools/tallon/enemies.py` (inimigos por sala, Prime → SM, contas da
  camada 0 do Prime; spec 07i; as espécies ficam em `SPECIES` de `tools/frigate/enemies.py`).
- `tools/frigate/enemies.py`, `props.py`, `pausemap.py`, `bosses.py`, `ending.py`, `timer.py`. Desde a 12i `Species` tem `companion`
  (segundo registro da população), `mount` (chão/parede/teto), `harmless` e `hover`/`bob`; `slots()` dá a espécie de cada slot.
  `tools/frigate/areaselect.py` escreve os nomes das áreas 3, 0 e (12i) 1 na tela de continue.
- `tools/frigate/title.py` (spec 16): demos desligadas (`check_demos_off`, usado pelo `check_orphans`) e o logo METROID PRIME
  (`logo_image`, `new_logo`, `pack` com o rabo da stream vanilla, `check_logo`).
- `tools/frigate/queen_art.py` (tiles, blocos de tilemap, paletas e caixas da Parasite Queen) e
  `queen_draw.py` (o desenho, em grades de texto editáveis; prévia com `tools/preview_queen.py`).
- `tools/tallon/beamdoors.py` — portas de feixe no `$84` (spec 09a): layout fixo (ids de PLM conhecidos sem
  build), `code(rom)` gera os bytes da ROM base, `apply(rom)` escreve; desde a 10d a onda roxa (`paint_table`, `paint_palette`:
  metatiles `$3F0–$3F7` e linha 6 do tileset 4).
- `tools/smlib/` — biblioteca da ROM (`level.py` aceita `overlay` = blocos crus de colisão; `RoomDef.blocks`/`Shape.blocks`
  = blocos crus da sala, os blocos de bomba da 09d e de Power Bomb da 09e; `reach.py` com a bola desde a 09d e a Power Bomb desde a 09e).
- `tools/validate.py` — checagens estáticas (alcance, mapa, progressão, save/map station, objetos, nave;
  na ROM construída, `check_pause_maps`: tilemap, nome, ícones e lista do save de cada área; `check_orphans`, etapa 11: só salas
  nossas alcançáveis, demos `DEMO_SCENES`, dados vanilla compartilhados `VANILLA_SHARED`).
- `tools/build.py` `RECLAIMED_8F`/`ROOM_PTR_COMPARED`/`ours_8f`/`put_at` e `Allocator(reclaimed=…)` (12a); `VANILLA_PAUSE[1]` e
  `tools/areas.py` `CHOZO_AREA` (12b); validador: `check_reclaimed`, `room_ptr_compares`, `check_vanilla_pause`, `check_chozo_slot`.
- `tools/chozo/rooms.py` — tabela da Chozo (12c): `TABLE`, `LINKS`, `REGIONS`, `DOCK_LOCKS`, `FEATURES`, `check_prime`; no build só as 3
  salas de elevador (`ELEVATOR_ROOMS`, 12e, desenhadas em `tools/chozo/layouts.py`). Elevadores: `frigate/rooms.py Elevator`,
  `areas.ELEVATORS`/`elevator_target`/`CHOZO`, `build.elevator_spawn`/`elevator_exit_entry`/`ELEVATOR_PAD_DOOR`, validador
  `check_elevators`/`check_elevators_in_rom`. `tools/dump_prime_locks.py` (venv) gera `research/prime_chozo_locks.json`. `tools/smlib/ruins.py` — estilo e cor das ruínas (12d).
- 12l: `tools/chozo/rooms.py` `SIDE_CAPS` (tampa por lado), `KEY_BEAM` (o feixe do Prime de cada porta key), `FLOODED` (a
  Reflecting Pool); `tools/tallon/beamdoors.py` `VERTICAL` (portas de gelo de chão/teto); validador `check_ball_ledges`.
- `tools/smlib/itemtouch.py` — correção do toque no item (spec 13, `$84:EEAB` → rotina em `$84:FFDF`) e do tiro em porta de cor
  (12g2, `$84:C7E2` → `$84:FFBB`); interpretador mínimo das duas rotinas (`simulate`, `behaviour_problems`). `tools/chozo/enemies.py`
  — inimigos da Chozo (12h). `tools/chozo/heat.py` (calor,
  12g), `tools/chozo/testrooms.py` (sala da ROM de teste da 12g, `build.py --teste-12g` → `build/teste-12g/`).
- `tools/chozo/bosses.py` — chefes do épico 14: `SpeciesCopy`/`COPIES` (o Plated Beetle `$A0:F83F`, a cópia do Kago de 1 parte
  `$A0:F87F`), `BOSSES` (14a), `ARENAS` e a rotina comum das arenas em `$84:F500` (`routine`, `table_entry`, `fight_record`;
  condições `KILLS`, `SLOT`, `BOSS_BIT`, `ITEM`), os patches do Spore Spawn (14c). O validador: `check_bosses`, `check_arenas`,
  `check_item_arena`, `check_arenas_in_rom`, `check_epic_bosses` (linha "chefes (specs/14)").
- `tools/smlib/roomgraph.py` — grafo de salas lido dos bytes (portas pelos blocos, estações, demos, saves, estruturas presas a banco
  de uma sala); etapa 11.
- `tests/run_tests.py` — testes no emulador headless `tools/snesrun` (LakeSnes).
  Desde a 12m: `FullChain`/`fc_round_*`/`full_chain` (a cadeia Tallon + Chozo), trechos medidos (`*_CLIMB`, `zig_jump`,
  `CHAIN_*_PAD`), os jobs mais longos primeiro. Validador: `check_world_rounds`, `ITEM_GAIN`, `item_percentage` (12m).
  Desde a 17j: a Magmoor na cadeia (`fc_round_3/4/6_magmoor`, os pedaços `magmoor_a/b/c_*` das caminhadas das regiões,
  `CHAIN_P24_PAD`/`CHAIN_P16_PAD`/`CHAIN_P23_PAD`), a cadeia em partes (`CHAIN_PARTS`, `CHAIN_TESTS`, `chain_handoff`,
  `run_chain_parts`, `CHAIN_GROUP`); validador `check_epic_magmoor`, `EPIC_MAGMOOR_*`.
- `tools/smlib/lava.py` (17d: estilo, cores, FX de lava), `tools/magmoor/layouts.py` (17e: salas P0 e P16; 17f: a região A e `LAVA`), `tools/magmoor/items.py` (17f), `tools/magmoor/enemies.py` (17g: inimigos, a tabela do Prime das 3 regiões), `tools/magmoor/testrooms.py` (17d: ROM de teste da lava, `build.py --teste-17d`), `areas.MAGMOOR` (17e).
- `tools/magmoor/rooms.py` — tabela da Magmoor (17c): `TABLE`, `LINKS`, `REGIONS` A–C, `ELEVATOR_ROOMS`/`DECORATIVE_ELEVATORS`/`TRANSPORT_TO`, `DOCK_LOCKS`, `KEY_BEAM` (do `key_vuln`), `FEATURES`, `HOT_ROOMS` (do `area_damage`), `check_prime`; nenhuma sala no build. `areas.MAGMOOR_AREA = 2`, `build.VANILLA_PAUSE[2]` (17b); `tools/chozo/heat.py` por área (`HEAT_BITS`, `heat_fx`, `native`; 17b); `build.RECLAIMED_8F` com 4 faixas (17a). Validador: `check_magmoor_slot`/`check_slot`, `check_magmoor`, `HOT_WORLDS`, `room_ptr_memory_compares`. Prévia: `python3 -I tools/preview_rooms.py --mapa-magmoor`. `tools/dump_prime_locks.py` grava também `key_vuln` (cor das portas) e `area_damage` (calor): `research/prime_magmoor_locks.json`.
- `tools/smlib/ice.py` (18d: as três caras, a neve), `tools/phendrana/testrooms.py` (18d: ROM de teste do gelo, `build.py --teste-18d`),
  `tools/phendrana/layouts.py` (18e: P0 e P29), `areas.PHENDRANA` (18e).
- `tools/phendrana/rooms.py` — tabela de Phendrana (18c): `TABLE`, `LINKS`, `REGIONS` A–E, `ELEVATOR_ROOMS`/`TRANSPORT_TO`, `DOCK_LOCKS`, `KEY_BEAM` (`BEAM_OF_KEY`, `ANY_BEAM`), `FEATURES`, `SNOW_ROOMS`, `WATER_ROOMS`, `PLASMA_ICE`, `WAVE_PANELS`, `check_prime`; nenhuma sala no build. `areas.PHENDRANA_AREA = 4`, `MINES_AREA = 5`, `IMPACT_CRATER_AREA = 0`, `build.VANILLA_PAUSE[4]` (18b); `build.RECLAIMED_8F` com 5 faixas (18a). Validador: `check_phendrana_slot`, `check_phendrana`, `check_no_super_locks`.
- `tools/mines/rooms.py` — tabela da Phazon Mines (19c): `TABLE`, `LINKS`, `REGIONS` A–D, `ELEVATOR_ROOMS`/`TRANSPORT_TO`, `DOCK_LOCKS`, `KEY_BEAM`, `FEATURES`, `PB_ONLY` (o que só a Power Bomb quebra, camada 0), `WAVE_PANELS`, `check_prime`; `ROOMS = []`. `mapsave.list_at` (19b: a lista da área 5 no `$81`), `build.RECLAIMED_A1` (19a).
- `tools/dump_prime_*.py` — extração de dados do Prime (precisa de `tools/venv`, Python 3.14 com
  retro-data-structures 0.44.1; raiz dos arquivos = `research/prime_fs`).

## Armadilhas já conhecidas

- Testes: caixas de mensagem precisam ser fechadas com A, senão o jogo congela; a nave pergunta
  "save?" e depois mostra "save completed" (caixa `$18`), e só salva quando essa fecha: dois A
  com ~300 quadros entre eles; no menu de pausa
  START precisa ficar 10 quadros apertado; `expect` compara 16 bits, para bit único use `expectbit`.
- Rodar um roteiro de teste numa ROM modificada sobrescreve as fotos em `build/tests/`: rode os
  testes de novo depois.
- Bits de mapa explorado ficam em $7E07F7 (o $7ECD52 é a cópia salva).
- O mapa de pausa como aparece fica na VRAM `$3000` (nome em `$38AA`); o buffer `$7E:4000` é
  reaproveitado logo depois: teste com `expectvram`.
- Map station abre o mapa de pausa sozinha (comportamento vanilla, não é bug).
- Câmera de load station tem que começar em x múltiplo de 256 (senão os PLMs animados saem
  deslocados: `bg1_x_offset`). A caixa de item ("MISSILE") só fecha com A depois de ~240 quadros.
  Posição posta por RAM mantém a corrida da Samus: a nave não aceita (apertar UP e repor).
- Porta cinza de chão/teto destrancada vira tampa azul: tem que atirar no ar.
- Carregar uma estação por RAM: a Samus só aceita comando ~550 quadros depois (pose de frente), e a
  estação de save recém-carregada não salva até ela trocar de sala (`save_station_lockout_flag`).
- Item só é pego andando para dentro dele (posição posta por RAM em cima do item não pega).
- Teleporte de porta com a Samus andando não começa: pôr a posição duas vezes (parar) antes.
- Debaixo d'água, subir por porta de chão: segurar a direção até depois da transição (~190 quadros).
- Bits de item do Tallon dividem bytes (`$A8–$AF` em `$7ED885`): conferir "ainda não pego" com o byte
  esperado dos itens já pegos no mesmo teste (`pick_up(..., taken=...)`), não com 0.
- Enemy sets que chegam a VRAM $7E00 cobrem os números do cronômetro (ver `timer.py`); o validador
  limita os sets da fragata a `$1C00` bytes.
- Rotas cegas do Tallon: o andador atira 1 vez por ciclo e não desvia; com inimigos ele morreria, por
  isso `tallon_walk` repõe a energia. Trechos medidos em ciclos podem mudar se um inimigo empurrar a
  Samus num ponto de precisão (a subida da Tallon Canyon já começa de um ponto fixo).
- Foto depois de pôr a câmera por RAM: o fundo não se redesenha; pausar e despausar redesenha.
- Inimigo de 16 px no chão (Cacatac, Geemer): o tiro em pé passa por cima; atirar agachada.
- O estado do Ridley muda dentro da animação (processada depois da rotina principal): checar o
  estado antes de chamar a rotina dele, não só depois.
- Recompilar o emulador: `cc -O2 -o tools/snesrun tools/snesrun.c vendor/LakeSnes/snes/*.c
  -Ivendor/LakeSnes/snes -lz`.
- REA não abre .sfc, .rvz nem .dol: usar as ferramentas acima.
- Cena da Gravity Suit vanilla teleporta a Samus para o meio da tela: corrigido (09b, `$91:D64E`); a Varia
  (não usada) continua vanilla. Teleporte de porta (`door_teleport`) com a câmera fora de uma tela inteira faz
  o item da sala seguinte aparecer 64 px fora do lugar (`bg1_x_offset`): pôr `$0911` numa tela inteira antes.
  Tela de equipamento no pause: R segurado 10 quadros, espera 200 (`$0727` = 1).
- Bloco de bomba (09d): BTS 0–3 voltam (~380 quadros), 4–7 não; o jogo redesenha o que volta como `$058`. Subir pela porta de
  teto da Gully (e outras de sala seca): pular e guiar para a borda da porta de chão do outro lado, senão ela cai de volta e a
  sala recarrega (os blocos quebrados voltam inteiros). Até a 10a o `door_teleport` deixava a câmera onde estava e a transição
  de porta de chão/teto saía com o deslocamento do BG1 (`$091D/$091F`) fora de tela inteira (Savestation → Reactor Access
  `$00E1`; a pé `$0100`): PLMs em dobro. Desde a 10a ele põe a câmera na tela da porta (`camera_bottom` nas de chão) e o BG1 fica
  em tela inteira; os `whole_screen_bg1` e valores repostos dos testes antigos continuam (inofensivos). Pôr a câmera por RAM
  (`tallon_look`) desalinha o redesenho de bloco quebrado: chegar andando.
- Bloco de Power Bomb (09e): tipo C BTS `$08/$09` (o tipo F é o de bomba); `$08` volta (~450 quadros), `$09` não; desenho `$057`.
  Pôr a PB: em bola, um SELECT (`$09D2 = 3`; o segundo volta a 0) e X; a explosão quebra em ~75 quadros. O modelo (`reach.py`)
  só vê o bloco com o BTS (`with_breakables`): sem ele, o tipo C seria ar para o corpo (como as tampas).
- `door_teleport` **para cima** por porta de teto troca de sala desde a 10a (antes ficava na sala, 09f). O A do
  `tallon_first_missile` fecha a caixa desde a 10a (300 quadros depois da caminhada; 240 era cedo demais). Samus posta por RAM e
  parada de frente pula mais alto que virada para um lado: para medir subidas, um toque de direção antes (10b). Pulo em parafuso (e o Space Jump) só
  correndo; o Space Jump pega com A solto ~12 quadros depois de um A de 30 (caindo); `ROOT_CAVE_CLIMB` tem o ritmo medido. A nave
  enche a energia até o máximo (`save_on_tallon_ship(..., energy)`).
- Elevador (12e): ↓/↑ só pega num quadro com `$0E16` ligado; ele liga quando a Samus anda ou cai na plataforma, não posta por RAM
  (aí ela fica de frente, pose `$9B`, e o A nem pula: andar 4 quadros → e 4 ←) nem depois de estação. Na borda da plataforma o flag pisca
  (um quadro sim, outro não) e um ↓ pode falhar e agachar (agachada não liga): nos testes, ficar no meio (`onto_platform`). Câmera posta
  por RAM antes de foto: pausar e despausar (o `onto_platform` já faz). A viagem leva ~600 quadros (↓) / ~540 (↑) até ela estar de pé do
  outro lado.
- Desde a spec 16 o título parado não toca demo (fica no título; antes, ~2900 quadros levavam às demos do SM). O tempo de carga do
  título decide o número aleatório na hora do novo jogo (`$05E5`, e o contador `$05B6`): as lutas medidas da Chozo
  (`chozo_hive_mecha`, `chozo_incinerator_drone`, `chozo_save_station_3`) dependem dele. Mexer no título (gráfico, compressão,
  quadros) pode mudar as lutas: o teste `titulo_metroid_prime` confere os dois números no quadro 600.
- 17f: o pulo andando cobre só ~85–115 px na horizontal (no ar ela anda devagar): fosso de 4 colunas entre rochas de 4 deixa uma
  janela de 2–3 quadros; as caminhadas medidas usam `hops` (quadros de andar, de pulo, depois: > 0 segurando a direção, < 0 esperando
  solta, para cair reto). Space Jump nos testes: `hold LEFT+A 30`, `hold LEFT 16` repetidos mantém a altura (medido na Triclops Pit).
  Uma `save`/`load` de estado do `snesrun` acelera muito a busca (roteiros em `s17f/scripts/`).
- Testes da 17d (`lava_medida`, `porta_de_onda_lava`) rodam na ROM de teste `build/teste-17d/` (o `run_tests.py` a constrói antes). Na
  lava sem roupa a Samus perde ½ por quadro (¾ numa sala quente): pôr a energia alta (999 por RAM) **antes** de colocá-la na lava, senão
  ela morre durante as esperas da colocação e o resto do roteiro roda na tela de morte.
- Testes da 12g (`porta_de_charge`, `sala_quente`) rodam na ROM de teste `build/teste-12g/` (o `run_tests.py` a constrói antes);
  tiro carregado no roteiro: `hold X 90` e soltar. Com o Charge Beam e mísseis, um SELECT volta ao feixe.
- 17h: tiro em porta azul à queima-roupa (1–2 blocos) não abre: a bala nasce depois da tampa; atirar de ~4 blocos. Em sala alta a Samus que cai junto da parede pode pousar em cima da tampa de uma porta lateral (o modelo a vê como ar): a Monitor Station tem rocha sobre as portas L0 e L3. Com mísseis, SELECT vai do feixe aos mísseis e depois às PBs (`$09D2` 0 → 1 → 3) e da PB volta ao feixe. A bola virada para oeste tem pose `$41` (`BALL_POSE` `$1D` é para leste).
- 17i: o Space Jump nos testes sobe encostado numa parede/face de rocha (`hold LEFT+A 30`, `hold LEFT 16` repetidos), mas **colado na
  parede não pega**: afastar-se uns pixels antes (`hold RIGHT 10`); virar no ar (LEFT+A depois RIGHT) desfaz o giro. Em salas altas pôr
  rocha sobre as portas laterais (a Samus pousa na tampa). Um tiro de longe sai da tela e não abre a porta (dois `E`/`D`). No `tr.py`
  da sessão, passos com espaço quebram no shell com `$(...)`: usar `trp.py` (`'passo*N'`). Nunca reconstruir a ROM com uma busca ou
  bateria rodando na mesma pasta.
- 18d/18e: a ROM de teste do gelo (`build/teste-18d/`) entra na área 4 carregando a estação 7 por RAM (`ice_station`); o pulo na água
  medido depende dos sub-pixels da Samus (`ICE_WATER_SUBPIXELS`). O grupo C é por prefixo: `elevador_phendrana_` é conferido antes do
  `elevador_` do grupo B em `group_of`.
- 17j: com mais feixes (a cadeia tem Wave + Ice + Plasma) o tiro **atravessa a parede e abre a porta de trás**: um trecho medido
  com o Power Beam que atira num bloco junto de uma porta muda (Geothermal Core, Warrior Shrine: a bola entrava rolando na sala
  seguinte). Inimigos mortos soltam munição: numa conta exata de mísseis/PBs, encher antes (cheio, nada muda). O `door_teleport` para
  cima fica na sala em mais duas portas de teto (Sunchamber Lobby, Fiery Shores → Shore Tunnel): `rise_through` (na Fiery Shores só a
  coluna 0 guiando para oeste sobe). Depois de `door_teleport` o lugar de chegada depende para que lado ela olhava: para andar até
  uma plataforma, encostar antes numa parede/tampa (P16, P23). Na P16, andando da L0, o primeiro tiro já abre a R0 (vindo do
  elevador ele sai da tela). Estado do `snesrun` (`save`/`load`): a mesma saída que rodar direto (medido); ele não guarda a ROM:
  carregado numa ROM diferente roda o código novo (o carimbo do `run_tests.py` impede isso nas partes da cadeia).
- 17g: um inimigo só roda se estiver na janela da câmera **também na vertical** (`y + 8 ≥` topo da câmera; `$A0:8EB6`): na Burning
  Trail o topo fica em y 256–288 com a Samus no chão, e um Skree pendurado no teto da linha 12 nunca acordava. Um rastejador que sai da
  câmera fica parado na borda dela até a Samus chegar. Rastejadores (Zeela, Sova, Viola) seguem a superfície e entram nos fossos de
  lava (andam no fundo, sob a lava, onde o tiro não chega). Com o Space Jump, apertar A de novo no ar gira de novo: as buscas da 17g
  sobem por cima dos inimigos; para andar no chão (fundo da Triclops Pit) a busca aceita só estados de pé (`ok` em `fight.search`).
  Mira para cima e à frente: `hold R 6`, `hold R+X 2` (R antes, senão atira reto).
- Inimigos da Chozo (12h): roteiros cegos na região A repõem a energia a cada ciclo (`chozo_walk`); testes de itens/travas apagam os
  inimigos da sala por RAM (`clear_room_enemies`, bit `$0200`). Pôr a Samus por RAM sobre o buraco de uma porta de chão começa uma
  transição: outra transição por RAM no meio dela corrompe a VRAM (gráficos de lixo nas salas seguintes).
- Subir por porta de chão numa sala de 1 tela com porta lateral ao lado (12i: Ruined Nursery, Ruined Gallery, Nursery Access): só a
  borda do lado oposto serve de pouso; nos testes, de pé na metade da porta longe dessa borda (`chozo_climb`/`climb_jump`, a técnica
  da 10b) ou a transição por RAM guiando (`rise_through`); `door_teleport` para cima sem guiar cai de volta. A caixa de item pega o A
  só ~420 quadros depois de andar para dentro do item (com 300 ela ficava aberta e o START seguinte a fechava, sem pausar).
- Estação de load: o jogo carrega a sala da **porta fantasma** da estação (`build.write_load_station`), não a palavra da sala dela.
- 12l: atirar numa porta de chão (de gelo/vermelha): posta por RAM ela fica de frente e o A não pula (um toque de direção
  antes); pulo curto e DOWN+X no ar (`SHOOT_DOWN`); com mísseis, um por pulo (5 pulos abrem a vermelha). Da porta de teto da
  piscina inundada para cima sem a suit ela sobe e cai de volta se não guiar. Depois de andar para leste o `onto_platform`
  pode parar 2 px fora: um toque para oeste antes.
- 12j: Samus posta por RAM no pedestal de save depois de entrar por uma porta do leste fica de frente e a estação não pergunta:
  um toque de direção (`hold LEFT 1`). Depois de pegar a Varia (e outros itens), a caixa só fecha com o A ~420 quadros depois
  da caminhada; antes disso ela fica parada. O andador (`chozo_walk`) não sobe degraus de 4 (a Arboretum Access usa pulos
  inteiros); se os últimos ciclos começam uma porta, esperar mais antes de conferir a sala.
- Inimigos de dois registros (12i: o olho, encaixe + olho): `frigate.enemies.slots()` dá o slot de cada um (testes).
- 12m: andando contra a tampa de uma porta vermelha, o primeiro X só faz a Samus mirar (nenhum míssil sai): um tiro de feixe
  antes de trocar para mísseis (`FullChain.red_door`). Um inimigo pode empurrá-la pela porta recém-aberta enquanto o SELECT
  volta ao feixe: trocar o HUD na sala seguinte. `poke 7E09C2 63` escreve só o byte baixo (com E-tanks a energia fica
  $1xx63). Com 799 de energia a nave leva ~800 quadros para encher. Posições depois de `door_teleport` dependem para que lado
  ela olha: para trechos medidos, encostar numa parede/tampa antes (ponto fixo). `tools/snesrun` só desenha o último quadro
  de cada comando: uma `shot` vê o mesmo quadro de antes.
- Lista de fechar de porta de cor (3ª palavra do cabeçalho) não termina: cai na lista principal logo depois.
  PLM de porta novo precisa de cópia própria dos quadros de fechar (spec 09a), senão a porta em que a Samus
  entra vira a vanilla.

- 14c: inimigo de spritemaps estendidos (o Spore Spawn) precisa das propriedades extras `$0004` da colocação vanilla, senão o
  corpo não é desenhado e o hitbox vira o do cabeçalho (uma luta falsa); os hitboxes por parte (`$A5:EF4F`…) decidem onde o
  tiro conta. Projétil fora da tela some: atirar no chefe de longe não chega. Entrar ou sair de uma arena viva (song set
  `$2A`) leva ~150 quadros a mais na porta (`out_of_arena`).

- 18n: uma caixa de mensagem de item que ainda não aceita o A (o teste esperou menos antes do A) pega o próximo botão segurado: a
  caminhada medida depois dela conta com isso (`walked_into(wait=…)` igual ao teste). Uma busca de luta que salva um estado por passo
  e continua dele pode divergir de uma execução contínua (o Thardus da cadeia sobrou com 50 de vida): a busca da 18n roda cada
  sequência inteira desde o estado da entrada. A pose de chegada importa: de frente (vindo do elevador) ou virada para um lado (vinda
  de outra sala), o primeiro "segure à direita" anda quadros diferentes. Rodar a cadeia por passos com estados salvos e depois em
  partes contínuas deu o mesmo resultado (as quatro partes passaram de primeira).

## Regras do usuário (CLAUDE.md / CARL)

Nunca commitar sem pedido explícito; não declarar pronto sem validar (validate + build + testes);
relatar trabalho parcial com honestidade; não apagar nada fora do escopo sem confirmar; menor
mudança correta; não silenciar erros.
