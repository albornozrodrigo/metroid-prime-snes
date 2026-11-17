# Frigate Orpheon — design 2D (demake de Metroid Prime sobre Super Metroid)

Fonte dos dados: `research/prime_worlds.json` e `research/frigate_objects.json`, extraídos do disco GM8E01 rev 0
pelos scripts em `tools/` (retro-data-structures). Índices `P#` = índice da sala no MLVL "Space Pirate Frigate".

## Mapeamento de áreas (projeto completo)

| Mundo do Prime      | Área do SM reaproveitada | Motivo |
|---------------------|--------------------------|--------|
| Space Pirate Frigate| 3 — Wrecked Ship         | nave abandonada, tileset de metal, chefe único da área (Phantoon → Parasite Queen) |
| Tallon Overworld    | 0 — Crateria             | superfície com chuva, nave da Samus |
| Chozo Ruins         | 1 — Brinstar             | |
| Magmoor Caverns     | 2 — Norfair              | calor/lava já implementados |
| Phendrana Drifts    | 4 — Maridia              | |
| Phazon Mines        | 5 — Tourian              | |
| Impact Crater       | 5/6                      | a decidir |

Só a Fragata entra na primeira entrega.

## Rota da fragata (do grafo de portas do Prime)

Ida (intro):
`P0 Exterior Docking Hangar → P1 Air Lock → P2 Deck Alpha Access Hall → P4 Emergency Evacuation Area → P6 Deck Alpha Umbilical Hall → P8 Map Facility → P10 Connection Elevator to Deck Beta → P12 Deck Beta Conduit Hall (túnel de Morph Ball) → P14 Biotech Research Area 1 (piratas nos tanques) → P16 Deck Beta Security Hall → P20 Biohazard Containment → P24 Deck Beta Transit Hall → P26 Cargo Freight Lift to Deck Gamma → P27 Reactor Core Entrance → P25 Reactor Core (Parasite Queen)`

Fuga (timer):
`P25 → P21 Deck Gamma Monitor Hall → P17 Connection Elevator to Deck Beta → P14 → P18 Subventilation Shaft A → P22 Subventilation Shaft B → P26 → P23/19/15/13/11/9 Main Ventilation Shaft A–F → P7 Biotech Research Area 2 → P5 Connection Elevator to Deck Alpha → P3 Deck Alpha Mech Shaft → P1 (Meta Ridley foge voando) → P0 (Samus entra na nave; final)`

Disposição no mapa: grade 16x14 (`map_x`/`map_y` em `tools/frigate/rooms.py`). A ida corre pelo topo
para a direita e desce pela direita até a Biotech 1, depois vai para a esquerda e desce pelo Cargo
Lift até o reator. Na fuga, o elevador Gamma (7 telas) sobe do reator até a Biotech 1, os Subvents
descem até o Cargo Lift e as Ventilation Shafts sobem pela esquerda até o Air Lock. Os lados e as
telas das portas foram escolhidos para que cada porta encoste na vizinha no mapa (o Prime é 3D; só
os pares de salas ligadas vêm dele).

## Conteúdo por sala (do script do Prime)

| P# | Sala | Conteúdo relevante no Prime | Versão 2D |
|----|------|------------------------------|-----------|
| 0 | Exterior Docking Hangar | tutorial de pulo/lock-on, 2 portas | sala de início, casco externo |
| 1 | Air Lock | despressurização | sala pequena de 3 portas |
| 2 | Deck Alpha Access Hall | 3 Parasites | corredor com parasitas |
| 4 | Emergency Evacuation Area | 3 Parasites, 1 Space Pirate, drops | sala 2x2 |
| 6 | Deck Alpha Umbilical Hall | detritos bloqueando | corredor |
| 8 | Map Facility | estação de mapa, 2 Parasites | estação de mapa |
| 10 | Connection Elevator to Deck Beta | elevador | poço vertical |
| 12 | Deck Beta Conduit Hall | túnel de Morph Ball | corredor com túnel |
| 14 | Biotech Research Area 1 | 8 Space Pirates (tanques), 3 portas | sala grande |
| 16 | Deck Beta Security Hall | campo de força/barreira | corredor |
| 20 | Biohazard Containment | 4 Space Pirates, drops | sala |
| 24 | Deck Beta Transit Hall | corredor curto | corredor |
| 26 | Cargo Freight Lift to Deck Gamma | Parasites, pirata, drops | poço alto |
| 27 | Reactor Core Entrance | estação de save | save + porta do chefe |
| 25 | Reactor Core | NewIntroBoss = Parasite Queen | arena do chefe |

## Bugs do Super Metroid a não reintroduzir

A base é a Fix Collection (ver readme do patch). Toda build roda os testes automáticos em `tests/`.
Correções desse patch que dependem de código que nós também vamos alterar (game start, carregamento de sala)
precisam de teste de regressão quando mexermos nessas rotinas.
