# Metroid Prime SNES (demake 2D sobre Super Metroid)

Recria o Metroid Prime (GameCube, GM8E01) como hack de Super Metroid. Base: `base/sm_fix.sfc`
(Super Metroid + Fix Collection Patch v1.0). Saída: `build/metroid_prime_snes.sfc` e o patch
`build/metroid_prime_snes.ips` (aplicar na ROM com a Fix Collection; distribuir só o .ips).

## Estado

- Frigate Orpheon: 28 salas e 30 ligações seguindo o grafo de portas do Prime; ida até o Reactor
  Core e fuga pelas Ventilation Shafts. Portas da fuga ficam cinza até o chefe da área morrer.
- Novo jogo pula intro e Ceres e começa no Exterior Docking Hangar, com o equipamento da intro do
  Prime (Varia, Morph, Bombs, Space Jump, Grapple, X-Ray, Charge/Wave/Ice/Plasma, 30 mísseis), e
  grava o save na hora (continue depois de game over volta ao hangar).
- Inimigos nas quantidades do Prime (`tools/frigate/enemies.py`): Parasite → zoomer laranja da
  Wrecked Ship ($A0:DC3F), Space Pirate → pirata cinza que anda e atira ($A0:F653).
- Parasite Queen = Phantoon ($A0:E4BF) no Reactor Core (sala 1x1, como a do Phantoon). A porta de
  entrada tranca durante a luta. A morte marca o chefe da área 3: as portas cinza abrem e liga o
  timer de fuga de 5:00 (rotina própria em $8F, que carrega os dígitos como o Mother Brain faz).
  Chegar ao hangar para o timer; timer zerado dá game over.
- Forma própria da Parasite Queen (`tools/frigate/queen_art.py`, desenho em `tools/frigate/queen_draw.py`):
  no lugar do "cérebro" do Phantoon, um inseto de pé visto de frente, como o modelo do Prime visto de
  cima: cabeça de carapaça com olhos laranja acesos e duas mandíbulas de osso sobre a boca, dois pares
  de pernas com espinhos, abdômen em gomos com carne carmim entre as placas e cauda com ferrão e pinça.
  Onde o Phantoon abria o olho ela abre a boca, com um núcleo brilhante que segue a Samus (é o ponto
  fraco); a pinça abre e fecha onde ele mexia a boca e os tentáculos. As 8 paletas de vida usam as
  cores das texturas do Prime (placas marrom-acinzentadas, carne carmim, brilho laranja) e "esquentam"
  para o vermelho conforme ela perde vida; as chamas azuis viraram fogo (`tools/frigate/bosses.py`).
  A luta e os ataques continuam os do Phantoon. Prévia: `python3 -I tools/preview_queen.py`
  (`research/render/parasite_queen.png`); antes/depois: `research/parasite_queen_forma.png`.
  Texturas exportadas com `tools/dump_prime_textures.py` em `research/prime_textures/parasite_queen/`.
- Save station no Reactor Core Entrance, onde fica a única do Prime na fragata (load station 1 da
  área 3; a 0 é o início no hangar). Como no Prime ("Save Disabled"), ela só funciona antes da
  Parasite Queen morrer: depois disso a sala usa um estado sem a estação.
- Map station na Map Facility, como no Prime. Ela revela a fragata inteira no mapa de pausa e o jogo
  abre o mapa sozinho em seguida, como no vanilla.
- Mapa de pausa e minimapa da fragata, gerados de `rooms.py` (`tools/frigate/pausemap.py`), com o
  nome "FRIGATE", o ícone de save, o da map station e o "X" do chefe derrotado. As salas foram
  redispostas numa grade coerente: toda porta encosta na sala vizinha no mapa (o validador confere).
- Paleta de fragata pirata aplicada ao tileset da Wrecked Ship (área 3 = fragata).
- Acabamento visual com peças do próprio tileset da Wrecked Ship (`tools/smlib/style.py`):
  - paredes com bordas e cantos certos e casco de luzes e barras, como na sala limpa $8F:CC27,
    sem as peças com musgo;
  - chão rebitado e faixas de luz no teto;
  - costelas de casco nos corredores e colunas de suporte sob as plataformas.
- Objetos de cenário (`tools/frigate/props.py`), sempre como fundo por onde a Samus passa:
  - tanques de estase nas Biotech;
  - consoles na Map Facility, Monitor Hall, Security Hall, Biotech 2 e Reactor Core Entrance.
- Exterior Docking Hangar com cara de hangar aberto para o espaço (`tools/frigate/space.py`, `props.py`):
  céu estrelado no fundo (camada 2, com paralaxe lenta) no lugar da parede do Wrecked Ship, parede
  escura da baía de atracação com faixa de luzes, duas garras sob a nave e plataforma de pouso
  iluminada no chão. Só o desenho mudou: a colisão (inclusive a da nave) é a mesma, e a Samus passa
  sempre na frente da parede do fundo.
- Fim da fragata (`tools/frigate/ending.py`):
  - Meta Ridley: na fuga, ao entrar na Air Lock, ele surge do escuro, ruge e sai voando pelo teto, sem
    luta (Prime: ele foge da fragata para Tallon IV). É o Ridley de Ceres com rotina própria: reusa o
    fade-in, o rugido e o voo de fuga dele, sem o bebê Metroid e sem a cena em modo 7 de Ceres. Depois
    que ele vai embora não volta mais. Cores do modelo do Prime: armadura cinza-metálica, músculos
    lilás, olhos laranja (as tabelas são de todos os Ridleys da ROM).
  - Ele fica na Air Lock, não no hangar, porque os gráficos dele ocupam toda a memória de vídeo de
    inimigos da sala e a nave precisa de parte dela.
  - Enquanto ele está na sala o cronômetro some (continua contando): os números do cronômetro ficam
    na mesma memória de vídeo. Quando ele vai embora, ou se a Samus sai antes, os números voltam.
  - Nave da Samus no hangar, sempre visível (inimigos da nave da Landing Site, com a colisão
    invisível copiada de lá). Antes do chefe ela é só cenário; na fuga, agachar em cima dela faz a
    Samus entrar e a nave decola.
  - Depois da decolagem o jogo continua, como no Prime: toca a cena da fuga de Ceres do Super
    Metroid (a estação, que aqui é a fragata, explode e a nave foge entre asteroides), aparece o
    planeta com o nome "TALLON IV" (letras O, I e V novas no gráfico da cena) e a nave pousa na
    Landing Site do Tallon (área 0, spec 07g), onde o jogo salva. Na decolagem a Samus perde o
    equipamento, como na explosão do Prime (spec 07e): chega só com o Power Beam, sem mísseis, 99 de
    energia (zerado antes do save do começo da cena, então resetar no meio não devolve nada). Continue depois de game over volta à Landing Site; desligar no meio da
    cena e carregar o save repete a cena e pousa lá também. O planeta ainda é o Zebes laranja. Em outras áreas a nave continua levando ao final do Super Metroid.
- Tela de seleção de área (continue depois de game over e carregar save; `tools/frigate/areaselect.py`):
  o título diz "TALLON IV" (com uma letra O grande nova, que o SM não tinha) e a região acesa diz
  "FRIGATE / ORPHEON", no lugar de "PLANET ZEBES / WRECKED SHIP". O desenho do planeta ainda é o Zebes.
- Tallon Overworld (área 0, spec 07g; `tools/tallon/`): as 5 salas do caminho do Prime que não pede
  item nenhum — Landing Site → Canyon Cavern → Tallon Canyon → Transport Tunnel A → Transport to
  Chozo Ruins West —, todas ida e volta sem Space Jump (o validador confere com o pulo medido). A
  nave pousa na Landing Site nova no fim da fragata e salva ali (continue volta para cima dela); a
  Samus chega só com o Power Beam (07e). Agachar na nave recarrega e oferece salvar (estação 0 da
  área 0), como a nave vanilla.
  Superfície com a rocha e a grama da Crateria, céu nublado e chuva (Landing Site e Tallon Canyon);
  túneis de tijolo de pedra; a sala de transporte é um beco sem saída com um elevador de enfeite.
  As portas para o resto do Tallon são parede por enquanto; a Crateria original ficou sem ligação.
  Mapa de pausa e minimapa próprios (spec 07f): nome "TALLON", só as salas do Tallon (aparecem
  quando exploradas; o Tallon não tem map station), ícone da nave na Landing Site, sem os ícones e
  elevadores da Crateria; o explorado volta depois de salvar e continuar. Na tela de continue o
  nome da área é "TALLON / OVERWORLD". Itens (spec 07h): 6 Missile Expansions nas salas construídas.
  Regiões B e C (spec 07k): templo (Temple Hall, Temple Security Station, Temple Lobby, Artifact
  Temple), cachoeira, Frigate Crash Site e raízes, 15 salas, 20 no Tallon. As travas são as do Prime,
  sem atalho: escudo de míssil = porta vermelha do SM (Temple Security → Lobby, Waterfall → Crash Site,
  Root Tunnel → Root Cave), portas de gelo/plasma = cinza que ainda não abre, bordas que pedem Space
  Jump (Crash Site → Overgrown, Root Cave → Arbor). Só com o Power Beam a Samus chega, além das 5 do
  MVP, à Temple Hall, Temple Security, Waterfall Cavern e Root Tunnel (cada uma até a porta vermelha):
  da nave, pelos terraços (Waterfall) ou pelo corredor sob ela (Temple Hall), e na Tallon Canyon por
  plataformas até a porta alta do Root Tunnel. O validador confere em que fase de equipamento cada sala
  fica alcançável. Gully e Alcove: spec 07m (abaixo).
  Inimigos (spec 07i): os da camada 0 do Prime nas salas construídas, trocados por espécies do SM
  (Beetle = Sidehopper pequeno, Geemer = Geemer, Parasite = Zeela, Blood Flower = Cacatac), no máximo
  1 por tela: Canyon Cavern, Tallon Canyon, Transport Tunnel A/B/C, Root Tunnel e Root Cave (27 no total).
  Todos morrem com o Power Beam (até 3 tiros). Armadilhas do Prime (Chubb Weed, Snake Weed) ficaram fora.
  Região D (spec 07l): a fragata afundada, 14 salas no tileset da fragata, inundadas (água em todas
  menos a Deck Beta Transit Hall), 34 salas no Tallon. Fiel ao Prime: fica atrás da porta de gelo da
  Frigate Access (cinza), pede a Gravity Suit (um anteparo na Main Ventilation Shaft C que o pulo
  debaixo d'água sem ela não sobe: o pulo na água foi medido no emulador) e tem portas de condutor de
  energia (Thermal Visor + Wave Beam) cinza: nenhuma sala dela é alcançável agora. Tem a segunda
  estação de save do Tallon (Savestation = load station 1 da área 0, com o ícone no mapa de pausa),
  2 Energy Tanks e 1 Missile Expansion, e os inimigos da camada 0 (Wall Crawler, Space Pirate, e as 4
  Gun Turrets da Biohazard = Rinka). Prévia: `python3 -I tools/preview_rooms.py --salas-07l`.
  Região E e Gully/Alcove (spec 07m): Great Tree Hall, Great Tree Chamber, Transport Tunnel D/E, Life
  Grove Tunnel, Life Grove e os transportes para Chozo South e Phazon Mines East, mais Gully e Alcove:
  **as 44 salas do Tallon na ROM**. Travas do Prime: paredes de Bombas da Gully e portas de gelo = cinza,
  bordas de Space Jump (portas da Gully/Alcove numa câmara no alto do penhasco da Landing Site, porta da
  Great Tree Chamber); o Space Jump na Alcove, o X-Ray no Life Grove e 2 mísseis; Seedlings = Cacatac
  andando. Prévia: `python3 -I tools/preview_rooms.py --salas-07m`.
- Itens de trava (épico 09, `specs/09-itens-de-trava.md`; fechado, 09a–09f): portas de feixe (gelo verde,
  onda roxa desde a 10d (era cinza), plasma laranja) no lugar das cinza; Ice, Wave, Gravity Suit e Plasma nos elevadores de enfeite e na Root
  Cave; Morph Ball na plataforma do elevador da Chozo West e Bombas no Artifact Temple; a Gully atrás de um túnel de
  Morph com 2 blocos de bomba na Tallon Canyon; a Power Bomb no chão do elevador da Mines East e o X-Ray dentro de uma
  cabana de 15 blocos de Power Bomb no Life Grove (spec 09e). **Da nave, só com o Power Beam, a pé: as 44 salas e os 20
  itens**, na ordem do épico (Morph → Bombas → Space Jump → gelo → Gravity → Power Bomb e Plasma → X-Ray).
  O validador declara e confere as 7 rodadas dessa ordem (spec 09f: `FIRST_ROUND`/`Item.round`, sem lugar sem volta em
  nenhuma rodada) e o teste `tallon_cadeia_completa` joga a cadeia inteira no emulador, do fim da fragata aos 20 itens.
  Com isso o épico do Tallon (07) também está fechado.
- Polimento do Tallon (épico 10, `specs/10-polimento-tallon.md`; fechado, 10a–10d): auditoria das 44 salas e das 88
  entradas de porta no emulador; porta de onda roxa (10d); subir por porta de teto para sala seca tem mais folga (empurrão
  `$02A0`, 10b); o mapa de pausa mostra a forma das salas (telas de rocha maciça ficam fora, com parede, 10c); nos testes o
  teleporte de porta põe a câmera na tela da porta (sem itens em dobro, sobe por porta de teto) e o A do primeiro míssil
  fecha a caixa (10a). A tabela de rodadas não mudou.
- Limpeza (etapa 11, `specs/11-limpeza.md`): o validador prova pelos bytes que nenhum caminho do jogo (novo jogo, saves, nave,
  fim da fragata, game over) entra numa sala do Super Metroid original (`check_orphans`). As 262 salas vanilla continuam na ROM, sem
  uso nenhum desde a spec 16 (as 19 das demos de atração também). Nada foi apagado; o validador mede o espaço que só elas ocupam,
  para a próxima área.
- Tela de título (spec 16, `specs/16-titulo-e-demos.md`): o logo diz **METROID / PRIME** (o METROID do Super Metroid subiu para o
  lugar do "SUPER" e o "PRIME" foi desenhado embaixo, no mesmo estilo e cores) e o título parado **não toca mais as demos** do Super
  Metroid: fica no título até alguém apertar um botão.
- Chozo Ruins (épico 12, `specs/12-chozo-ruins.md`; fechado na 12m): as 64 salas na área 1, ligadas ao Tallon pelos três
  elevadores de verdade (Chozo West, East e South), 31 itens (Charge Beam, Varia Suit, mísseis, 5 E-tanks, a expansão de Power
  Bomb), portas vermelhas, de onda e de gelo, blocos de bomba e de Power Bomb, a Magma Pool quente (só a Varia protege), a
  Reflecting Pool inundada, 3 Save Stations e a Map Station. O validador anda o Tallon e a Chozo juntos e confere a rodada
  declarada de cada sala e item (51 itens em 7 rodadas, 51% pela fórmula do fim do SM); a cadeia completa joga as áreas no
  emulador, do pouso a todos os itens, pelos elevadores (desde a 17j com a Magmoor; desde a 18n com Phendrana, em quatro testes:
  `cadeia_completa_parte_1` a `_4`).
- Chefes da Chozo (épico 14, `specs/14-chefes.md`; fechado na 14f): o Plated Beetle (Sidehopper grande nas cores do Prime) na
  Ruined Shrine; o Hive Mecha (2 colmeias + 3 vespas: o míssil do topo do totem aparece quando todas morrem); o Flaahgra (o Spore
  Spawn nas cores do Flaahgra: a Varia aparece e a porta para a Sun Tower Access abre quando ele morre); o Incinerator Drone
  (pegar o míssil do suporte do Burn Dome tranca a porta e traz 2 colmeias + 2 vespas; todas mortas, a porta abre). Música de
  mini-chefe só na luta; chefe morto não volta (salvo com o jogo). Cada luta tem o seu teste no emulador, só com o equipamento
  da rodada.
- Magmoor Caverns (épico 17, `specs/17-magmoor-caverns.md`; fechado na 17j em 01/11/2026): prontos o espaço (17a), o lugar na área 2 da Norfair com o calor dela (17b), a planta das 29 salas com o mapa e as travas do Prime (17c, `specs/img/17c-mapa.png`), o estilo das cavernas de lava (tilesets 09 quente / 0A frio, rocha escura e crosta laranja, porta de onda roxa) e a lava de verdade medida no emulador com as regras do validador (17d, `specs/img/17d-*.png`), e os **dois elevadores de verdade**: Chozo (Transport to Magmoor North) ↔ Magmoor P0 e Tallon (Magmoor East) ↔ Magmoor P16, as duas salas de elevador da Magmoor como becos, mapa "MAGMOOR" e "MAGMOOR / CAVERNS" no continue (17e, `specs/img/17e-elevadores.png`), e a **região norte (A)** vinda da Chozo: Burning Trail, Save Station A (porta vermelha; save e continue na Magmoor), Lake Tunnel, Lava Lake, Pit Tunnel, Triclops Pit, Storage Cavern e Monitor Tunnel, com 2 mísseis, calor nas 5 salas superaquecidas (só a Varia protege) e lava de verdade em fossos e poças, sempre pulável e com saída (17f, `specs/img/17f-*.png`), e os **inimigos da região A** (17g, `specs/img/17g-*.png`): Skrees que mergulham do teto da Burning Trail, Zeelas, uma Sova (o Burrower) na Lake Tunnel, Mellas (os Puffers) sobre a lava e Violas paradas nas rochas (os Triclops), 19 em 6 salas, todos mortos pelo Power Beam e nenhum dano logo ao entrar por uma porta, e a **região do centro (B)** (17h, `specs/img/17h-*.png`): Monitor Station, Transport Tunnel A (E-tank num túnel de Morph com bloco de bomba), o elevador de enfeite de Phendrana North, Warrior Shrine (parede de Power Bomb), Shore Tunnel (porta de chão para a Fiery Shores, que se sobe pela plataforma), Fiery Shores (míssil e expansão de PB atrás da Power Bomb, rodada 6; 2 Violas), Transport Tunnel B e a P16: **a Magmoor liga a Chozo ao Tallon a pé** (com a Varia, rodada 3), sem mudar nenhuma rodada do Tallon e da Chozo, e a **região sul (C)** (17i, `specs/img/17i-*.png`): Twin Fires Tunnel (quente; o penhasco do trilho de Spider só com o Space Jump), Twin Fires (3 Mellas), North Core Tunnel, Geothermal Core (quebra-cabeça = túnel com bloco de bomba diante da porta de gelo da Plasma Processing; a porta de cima numa borda de Space Jump), Plasma Processing (um míssil no lugar do Plasma, atrás do gelo), South Core Tunnel (2 Sovas), Magmoor Workstation (E-tank numa plataforma alta, Space Jump), Workstation Tunnel (2 Zeelas), os elevadores de enfeite de Mines West e Phendrana South, Transport Tunnel C e a **Save Station B** (porta vermelha; save e continue): portas de onda roxas e de gelo verdes como as do Prime, **as 29 salas da Magmoor na ROM**, 7 itens, e as **rodadas das três áreas** (17j, `specs/img/17j-*.png`): o validador anda Tallon, Chozo e Magmoor juntos, **58 itens em 7 rodadas** (os do Tallon e da Chozo nas rodadas de antes; os da Magmoor nas 3, 4 e 6), **58%** pela fórmula do fim do SM (energia 999, mísseis 180, power bombs 15), e a cadeia completa joga as três áreas no emulador, do pouso aos 58 itens, pelos 5 elevadores, em três testes ligados por estados salvos do emulador (`cadeia_completa_parte_1` no grupo A, `_2` e `_3` no grupo B).
- Phendrana Drifts (épico 18, `specs/18-phendrana-drifts.md`, aprovado em 03/11/2026 e fechado na 18n em 04/11/2026: as 56 salas por região, itens com o Super
  Missile do SM no Observatory, os dois chefes — Sheegoth e Thardus —, só a Gravity Chamber inundada; área 4, três caras e Metroids =
  padrão aceito, a confirmar): prontos, sem mudar a ROM, o espaço do `$8F` (18a: a faixa das demos `$8F:8000–8ED3`, usada só com as
  demos desligadas), o lugar na área 4 da Maridia e o plano das áreas (18b: Mines na 5, Impact Crater dentro da 0) e a planta das 56
  salas com o mapa, as travas, a neve, a água e os gelos do Prime (18c, `specs/img/18c-mapa.png`), com a varredura que prova que o
  Super Missile não abre nada no jogo; as **três caras do gelo** (18d, `specs/img/18d-*.png`: exterior com neve, ruínas Chozo de gelo,
  laboratórios dos piratas, cada uma com a porta de onda roxa; a neve = os esporos do SM em branco, caindo devagar; a água da área 4
  medida, tudo numa ROM de teste) e os **dois elevadores de verdade** (18e, `specs/img/18e-*.png`): Magmoor P13 ↔ Phendrana P0 (com
  neve) e Magmoor P27 ↔ Phendrana P29, as duas salas de Phendrana como becos, mapa "PHENDRANA" e "PHENDRANA / DRIFTS" no continue;
  as rodadas das três áreas iguais; e a **região norte (A)** (18f, `specs/img/18f-*.png`): Shoreline Entrance, Phendrana Shorelines
  (a praia com a torre em ruínas), Save Station B (save e continue em Phendrana), Temple Entryway, Chozo Ice Temple (o bomb slot =
  túnel com bloco de bomba), Chapel Tunnel, Chapel of the Elders (porta de onda por dentro; o Sheegoth na 18h), Ruins Entryway (até a
  parede da região B), Plaza Walkway, Ice Ruins Access e Ice Ruins East, com neve onde neva no Prime e **4 mísseis** (2 no alto de
  torres que só o Space Jump alcança, no lugar dos trilhos de Spider), tudo na rodada 3; as rodadas das três áreas iguais; e os
  **inimigos da região A** (18g, `specs/img/18g-*.png`): Zeelas na Shorelines e na Ice Ruins East e os orbes elétricos da Wrecked Ship
  (cópia justa: 5 tiros, 20 por toque) na Ice Ruins Access, justos em toda rodada e longe das portas; e o **Sheegoth** (18h,
  `specs/img/18h-*.png`): na Chapel of the Elders, o Dessgeega do SM em cores de gelo (casca que o tiro sem carga não fere: mísseis ou
  tiros carregados) e 2 Sidehoppers pequenos (os Babygoths); a porta tranca até a vitória, um míssil (no lugar do Wave Beam) aparece no
  altar e o chefe morto não volta; e a **região B** (18i, `specs/img/18i-*.png`): Ice Ruins West (a expansão de PB num nicho atrás de
  uma tampa laranja que só o Plasma abre, rodada 6; porta vermelha para a Canyon Entryway), Courtyard Entryway, Canyon Entryway,
  Phendrana Canyon (beco), Ruined Courtyard (E-tank atrás de um bloco de bomba), Save Station A (porta vermelha; save e continue),
  Quarantine Access, os laboratórios Specimen Storage, Research Entrance (porta de onda roxa no teto), Map Station (revela o mapa),
  Hydra Lab Entryway e Research Lab Hydra (um míssil), com orbes, zoomers, Zeelas e um Sidehopper pequeno; as rodadas das três áreas
  iguais; e a **região C** (18j, `specs/img/18j-*.png`): a North Quarantine Tunnel (uma trilha de terraços nevados descendo da porta
  de chão da Quarantine Access; a porta de onda roxa no teto), a Quarantine Cave (dois penhascos e a arena vazia, à espera do Thardus),
  a Quarantine Monitor (um túnel de Morph Ball e um míssil), a South Quarantine Tunnel (um túnel de degraus até o fundo e um zigue-zague
  de volta), o elevador sul aberto até a porta de gelo da Transport Access (o E-tank num pilar de gelo atrás de uma tampa laranja que
  só o Plasma abre, rodada 6), com orbes elétricos; as rodadas das três áreas iguais; e o **Thardus** (18k, `specs/img/18k-*.png`):
  na Quarantine Cave, o Bomb Torizo do SM em cores de pedra e neve, que acorda quando a Samus entra; as duas portas dos túneis trancam
  até ele morrer (20 tiros do Power Beam); nada no lugar da Spider Ball, e o chefe morto não volta; e a **região D** (18l,
  `specs/img/18l-*.png`): Observatory Access, Observatory (o **Super Missile do SM** numa câmara no alto, atrás de um bloco de bomba;
  um Super Missile abre a porta vermelha da Save Station D), Save Station D (save e continue), West Tower Entrance (porta vermelha),
  West Tower, Control Tower (neve), East Tower, Aether Lab Entryway (um orbe), Research Lab Aether (E-tank e míssil), Research Core
  Access, Research Core e Pike Access (portas de gelo), com os **Metroids** do Prime (o do SM enfraquecido: 5 tiros do Power Beam,
  20 por toque, sem agarrar; o gelo o congela); as rodadas das três áreas iguais; e a **região E** (18m, `specs/img/18m-*.png`), a
  última: Frozen Pike, Frost Cave Access, Hunter Cave Access, Frost Cave (um míssil no lago seco), Save Station C (save e continue),
  Hunter Cave, os túneis da Edge, Chamber Access (porta de onda roxa no chão, aberta com um tiro para baixo no ar), Lake Tunnel,
  Phendrana's Edge (a porta de plasma da Storage Cave; a porta de Morph da Security Cave atrás de blocos de Power Bomb: a expansão de
  PB) e a **Gravity Chamber inundada** (a sala inteira debaixo d'água: o míssil no lugar da Gravity Suit no fundo, pego sem a suit, e
  outro numa borda alta que só o Space Jump com a Gravity alcança), com Beetles e orbes. **Phendrana tem as 56 salas e os 17 itens**
  (11 mísseis, 3 E-tanks, 2 expansões de PB, o Super Missile); e as **rodadas das quatro áreas** (18n, `specs/img/18n-*.png`): o
  validador anda Tallon, Chozo, Magmoor e Phendrana juntos, **75 itens em 7 rodadas** (os das outras áreas nas rodadas de antes; os de
  Phendrana nas 3, 4, 5 e 6), **75%** pela fórmula do fim do SM (energia 1299, mísseis 235, super mísseis 5, power bombs 25), e a
  cadeia completa joga as quatro áreas no emulador, do pouso aos 75 itens, pelos 7 elevadores, com **o Sheegoth e o Thardus vencidos
  de verdade**, em quatro testes ligados por estados salvos (`cadeia_completa_parte_1` no grupo A, `_2` no B, `_3` e `_4` no C); no
  fim, pela nave com o evento da fuga de Zebes posto por RAM (o jogo ainda não tem fim próprio), o fim do SM mostra **"YOUR RATE FOR
  COLLECTING ITEMS IS 75%"**.
- Ainda não tem: os ataques próprios da Parasite Queen (a luta é a do Phantoon), os Chozo Ghosts e o resto do Prime (os
  outros mundos).

## Como construir e testar

Verificação (desde a 17i, um comando por vez, cada um abaixo de ~6 min): `python3 -I tools/build.py` duas vezes (o sha1 do `.ips` igual), `python3 -I tools/validate.py | tail -1` (0 problemas), `python3 -I tests/run_tests.py --grupo A`, **depois** `python3 -I tests/run_tests.py --grupo B` e **depois** (desde a 18e) `python3 -I tests/run_tests.py --grupo C` (todo teste está em exatamente um grupo: `tests/run_tests.py group_of`). Desde a 17j o grupo B carrega o estado do emulador que a cadeia do grupo A salvou (`build/tests/cadeia_completa_parte_1.state`, com um carimbo da ROM e do roteiro): rodado sem o A antes, o B roda a parte 1 primeiro (correto, mas ~3 min a mais). Desde a 18n o grupo C carrega o da parte 2 (grupo B) do mesmo jeito: a ordem é A, B, C.

```sh
python3 -I tools/validate.py     # checagens estáticas (alcance de portas, mapa, progressão)
python3 -I tools/build.py        # gera build/metroid_prime_snes.sfc + .ips + build/manifest.json
python3 -I tests/run_tests.py    # roda a ROM no emulador headless e confere a RAM (em paralelo; tudo: mais que a cadeia sozinha, ~10 min: use os grupos)
python3 -I tests/run_tests.py --grupo A   # metade A (fragata, título, portas de feixe, a parte 1 da cadeia completa): ~3 min
python3 -I tests/run_tests.py --grupo B   # grupo B (Tallon, Chozo, Magmoor, elevadores, entradas de porta, ROMs de teste, a parte 2 da cadeia; depois do A): ~3,3 min
python3 -I tests/run_tests.py --grupo C   # grupo C (desde a 18e: Phendrana, os elevadores dela, a ROM de teste do gelo, a parte 3 da cadeia; depois do B): ~2 min (21 testes)
python3 -I tests/run_tests.py --grupo D   # grupo D (desde a 19e: a Mines, os elevadores dela, a ROM de teste da mina; desde a 19m a parte 5 da cadeia, a 4 voltou ao C; depois do C): ~3,5 min (18 testes)
python3 -I tests/run_tests.py cadeia_completa_parte   # só a cadeia completa, as 5 partes em sequência (19m: pelas cinco áreas, 88%): mais de 10 min (use os grupos)
python3 -I tests/run_tests.py timer   # só os testes cujo nome contém "timer" (combina com --grupo)
python3 -I tools/preview_rooms.py  # PNG de cada sala em research/render/ (--salas-07k: specs/img/07k-sala-*.png; --mapa-magmoor: specs/img/17c-mapa.png; --estilo-lava: specs/img/17d-*.png)
python3 -I tools/build.py --teste-17d  # ROM de teste da lava em build/teste-17d/ (os testes lava_medida e porta_de_onda_lava a constroem sozinhos)
python3 -I tools/build.py --teste-18d  # ROM de teste do gelo em build/teste-18d/ (neve_medida, porta_de_onda_gelo, agua_medida_area_4 a constroem sozinhos)
python3 -I tools/preview_rooms.py --estilo-gelo   # as três caras de Phendrana em specs/img/18d-*.png
python3 -I tools/preview_queen.py  # quadros da Parasite Queen da ROM gerada em research/render/
```

Ferramentas: `tools/snesrun` (emulador headless sobre LakeSnes; recompilar com o comando no topo de
`tools/snesrun.c`; desde a 12m só desenha o último quadro de cada comando, com a mesma saída), `vendor/Flips/flips`, `vendor/asar`. Dados do Prime extraídos com
`tools/dump_prime_world.py` / `tools/dump_prime_area_objects.py` (retro-data-structures).

## Documentos

- `research/sm_room_format.md` — formato verificado de salas/portas/PLMs/inimigos e espaço livre.
- `research/frigate_design.md` — mapeamento Prime → SM e rota da fragata.

## Bugs evitados (pegos pelo validador ou pelos testes)

- Porta de chão sem plataforma ao lado: Samus subia e caía de volta pela mesma porta (loop).
- Subindo por porta de teto e guiando para a borda do outro lado do buraco, a Samus caía de volta em 54 de 160 subidas
  medidas (empurrão `$0240`); com `$02A0` (spec 10b), 28, todas partindo do quarto de fora da porta.
- Porta lateral flutuando acima do chão, e vão menor que a altura da Samus num poço.
- Passagem da fuga aberta antes do chefe (Air Lock → Mech Shaft), o que pulava metade da fragata.
- Porta cinza sem os blocos de tampa por baixo: a Samus atravessava a porta "trancada".
- Continue depois de game over levava a Samus para a Landing Site original (save vazio, área 0):
  o jogo novo agora grava o save no início.
- Uma porta, estação ou save apontado para o lugar errado levaria a Samus a uma sala do Super Metroid original sem erro nenhum:
  o validador anda todos os caminhos de entrada pelos bytes da ROM (spec 11).
- Recomprimir o gráfico do título inteiro fazia o título levar 4 quadros a mais para carregar, o que muda o número aleatório na hora
  do novo jogo (e as lutas medidas dos testes): o gráfico novo reaproveita a compressão vanilla fora do logo (spec 16).
- Timer zerado fora de Ceres tocava a cena de Ceres explodindo (o jogo decide pelo evento da bomba
  de Zebes): agora decide pela área ($82:848E) e dá game over.
- O timer de fuga não aparecia na tela: os dígitos só ficam na VRAM quando alguém os copia; a
  rotina do timer agora copia, como o Mother Brain.
- Salvar durante a fuga deixaria o continue começar com o chefe morto e sem timer (fuga sem
  pressa): a save station se desliga quando a Parasite Queen morre, como no Prime.
- O mapa explorado sumia depois de carregar o save: a SRAM só guarda os bytes de mapa que cada área
  usava no vanilla (18 na área 3; a fragata usa 30). O build agora lista os bytes da fragata e os
  guarda num bloco próprio depois dos dados vanilla (o save tem 1280 bytes para o mapa; nenhuma
  outra área perde bytes). O Tallon (área 0) ganhou o seu na spec 07f: 47 bytes, o mundo inteiro.
- A nave do Super Metroid, antes do chefe, oferecia salvar como a da Landing Site e marcava uma save
  station de Crateria como usada (ela aparece no mapa do continue e levaria à Crateria original):
  na fragata ela só abre depois do chefe.
- O cronômetro da fuga aparecia com pedaços do Ridley no lugar dos números (os dois usam o fim da
  memória de vídeo de inimigos).
- O Ridley de Ceres se apaga sozinho quando o chefe da área morreu (sempre verdade na fuga) e, depois
  do rugido, começa a luta: a rotina nova pula essa checagem e troca a luta pelo voo de fuga.
- Salas posicionadas no mapa sem bater com as portas (7 de 30 ligações): o mapa mostraria salas
  soltas e o minimapa pularia ao passar de uma para outra.
