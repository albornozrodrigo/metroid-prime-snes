# Specs (desenvolvimento guiado por especificação)

Cada mudança começa como uma spec neste diretório, antes de qualquer código. A spec diz o que muda,
por quê, como verificar, e o que fica de fora. A implementação segue a spec; se a realidade obrigar
a desviar, a spec é atualizada (seção "Desvios") em vez de o código divergir em silêncio.

## Fluxo

1. **Pesquisa + spec** (`specs/NN-nome.md`, estado `rascunho`): fatos verificados na ROM/no código,
   com endereço ou `arquivo:linha`. Experimentos só numa cópia do projeto, nunca em `build/`.
2. **Revisão** (estado `aprovada`): critérios de aceite testáveis, fora de escopo explícito.
3. **Implementação** (estado `implementada`): código + testes juntos. Um item por vez (o build e os
   testes escrevem em caminhos fixos de `build/`).
4. **Verificação** (estado `verificada`): `python3 -I tools/validate.py`, `python3 -I tools/build.py`
   e `python3 -I tests/run_tests.py` rodados de novo por quem revisa, com resultado anotado.

## Ordem (problemas primeiro, depois do mais rápido ao mais complexo)

| # | Spec | Tipo | Estado |
|---|------|------|--------|
| 01 | [Tela de continue com a fragata](01-tela-de-continue.md) | problema | verificada |
| 02 | [Minimapa apagado na Air Lock](02-minimapa-air-lock.md) | problema | verificada |
| 03 | [Cota de mapa da Tourian na SRAM](03-cota-sram-mapa.md) | problema | verificada |
| 04 | [Hangar com cara de hangar](04-visual-hangar.md) | problema | verificada |
| 05 | [Final próprio da fragata](05-final-da-fragata.md) | etapa | verificada |
| 06 | [Forma da Parasite Queen](06-forma-parasite-queen.md) | etapa | verificada |
| 07 | [Tallon Overworld](07-tallon-overworld.md) | etapa (épico) | verificada (13 filhas verificadas, 44 salas na ROM; os 13 itens pegos no jogo desde o épico 09, fechado na 09f) |
| 07a | [Toolchain para várias áreas](07a-toolchain-multi-area.md) | etapa (filha do 07) | verificada |
| 07b | [Alcance sem Space Jump](07b-alcance-sem-space-jump.md) | etapa (filha do 07) | verificada |
| 07c | [Estilo da Crateria](07c-estilo-crateria.md) | etapa (filha do 07) | verificada |
| 07d | [Grafo e mapa do Tallon](07d-grafo-e-mapa-tallon.md) | etapa (filha do 07) | verificada |
| 07g | [Salas do MVP do Tallon (com a chegada)](07g-salas-mvp-tallon.md) | etapa (filha do 07; antes da 07e/07f) | verificada |
| 07e | [Chegada e perda de itens](07e-chegada-e-perda-de-itens.md) | etapa (filha do 07) | verificada |
| 07f | [Mapa de pausa e minimapa do Tallon](07f-mapa-de-pausa-tallon.md) | etapa (filha do 07) | verificada |
| 07j | [Elevadores de enfeite (e a casca do Artifact Temple)](07j-elevadores-de-enfeite.md) | etapa (filha do 07) | verificada |
| 07k | [Regiões B e C do Tallon (travas fiéis)](07k-regioes-b-e-c.md) | etapa (filha do 07) | verificada |
| 07h | [Itens do Tallon](07h-itens-tallon.md) | etapa (filha do 07) | verificada |
| 07i | [Inimigos do Tallon](07i-inimigos-tallon.md) | etapa (filha do 07) | verificada |
| 07l | [Região D do Tallon (fragata afundada)](07l-regiao-d-fragata-afundada.md) | etapa (filha do 07) | verificada |
| 07m | [Região E do Tallon (Grande Árvore), com Gully e Alcove](07m-regiao-e-grande-arvore.md) | etapa (filha do 07) | verificada |
| 08 | [Samus presa ao descer por porta de chão na fragata](08-porta-de-chao-fragata.md) | problema | verificada |
| 09 | [Itens de trava: o Tallon inteiro jogável](09-itens-de-trava.md) | etapa (épico) | verificada (09a–09f verificadas: as 44 salas e os 20 itens a pé, em 7 rodadas, e a cadeia completa no emulador) |
| 09a | [Portas de feixe (gelo, onda, plasma)](09a-portas-de-feixe.md) | etapa (filha do 09) | verificada |
| 09b | [Itens de feixe e Gravity Suit](09b-itens-de-feixe-e-gravity.md) | etapa (filha do 09) | verificada |
| 09c | [Segurança do banco de dados de sala](09c-banco-de-salas.md) | etapa (filha do 09) | verificada |
| 09d | [Morph Ball e Bombas](09d-morph-e-bombas.md) | etapa (filha do 09) | verificada |
| 09e | [Power Bombs e as paredes do X-Ray](09e-power-bombs-e-xray.md) | etapa (filha do 09) | verificada |
| 09f | [Rodadas declaradas e a cadeia completa](09f-rodadas-e-cadeia-completa.md) | etapa (filha do 09) | verificada |
| 10 | [Polimento do Tallon](10-polimento-tallon.md) | etapa (épico) | verificada (10a–10d verificadas; rodadas iguais) |
| 10a | [Teleporte de porta alinhado e o A do primeiro míssil](10a-teleporte-alinhado.md) | problema (testes; filha do 10) | verificada |
| 10b | [Subir por porta de teto com folga](10b-subida-com-folga.md) | problema (filha do 10) | verificada |
| 10c | [Mapa de pausa com a forma da sala](10c-mapa-com-a-forma-da-sala.md) | problema (filha do 10) | verificada |
| 10d | [Porta de onda roxa](10d-porta-de-onda-roxa.md) | problema (filha do 10) | verificada |
| 11 | [Limpeza: salas vanilla órfãs](11-limpeza.md) | etapa | verificada (nenhum caminho entra em sala vanilla além das demos; `check_orphans`; ROM igual) |
| 12 | [Chozo Ruins](12-chozo-ruins.md) | etapa (épico) | verificada (12a–12m e 12g2 verificadas: as 64 salas, os 3 elevadores, 31 itens; Tallon + Chozo em 7 rodadas declaradas, 51 itens, e a cadeia completa no emulador) |
| 12a | [Segundo espaço do `$8F` (bloco órfão recuperado)](12a-espaco-8f-recuperado.md) | etapa (filha do 12; toolchain) | verificada |
| 12b | [Lugar da Chozo na área 1](12b-area-da-chozo.md) | etapa (filha do 12; toolchain; área confirmada) | verificada |
| 12c | [Grafo, mapa e travas do Prime da Chozo](12c-grafo-e-mapa-chozo.md) | etapa (filha do 12; dados, nenhuma sala) | verificada |
| 12d | [Estilo das ruínas (tileset 0C em arenito)](12d-estilo-das-ruinas.md) | etapa (filha do 12; cor conferida numa sala da Chozo na 12e) | verificada |
| 12e | [Elevadores de verdade (Tallon ↔ Chozo)](12e-elevadores-de-verdade.md) | etapa (filha do 12) | verificada |
| 12f | [Região A da Chozo (entrada, Main Plaza, Ruined Shrine, Tower of Light)](12f-regiao-a-chozo.md) | etapa (filha do 12) | verificada |
| 13 | [Item varrido por Power Bomb fica impegável](13-power-bomb-apaga-item.md) | problema (achado da 12f; correção no motor, `$84:EEAB`) | verificada |
| 12g | [Itens e travas novas (Charge Beam, Varia Suit)](12g-itens-e-travas-novas.md) | etapa (filha do 12; mecanismos na ROM de teste, lugar nas regiões C/D) | verificada |
| 12g2 | [Ajustes da 12g: calor só com a Varia, porta de charge branca, sem a ordem da 12f, tiro na porta de cor](12g2-ajustes-calor-e-cor.md) | problema (decisões do usuário sobre a 12g e a spec 13) | verificada |
| 12h | [Inimigos da Chozo (região A)](12h-inimigos-chozo.md) | etapa (filha do 12) | verificada |
| 12i | [Região B da Chozo (Nursery, Gallery, Hive Totem, Vault), Save Station 1 e Map Station](12i-regiao-b-chozo.md) | etapa (filha do 12) | verificada |
| 12j | [Região C da Chozo (Ruined Fountain, Arboretum, Sunchamber com a Varia, Sun Tower, Save Station 2)](12j-regiao-c-chozo.md) | etapa (filha do 12) | verificada |
| 12k | [Região D da Chozo (Watery Hall com o Charge Beam, Energy Core, Burn Dome, Dynamo, Furnace)](12k-regiao-d-chozo.md) | etapa (filha do 12) | verificada |
| 12l | [Região E da Chozo (Hall of the Elders, Crossway, Reflecting Pool inundada, Save Station 3, as saídas East/South)](12l-regiao-e-chozo.md) | etapa (filha do 12) | verificada |
| 12m | [Rodadas das duas áreas e a cadeia completa (Tallon + Chozo)](12m-rodadas-e-cadeia-completa.md) | etapa (filha do 12) | verificada |
| 14 | [Chefes](14-chefes.md) | etapa (épico) | verificada (31/10/2026; 14a–14d e 14f verificadas; 14e fora) |
| 14a | [Plated Beetle (Sidehopper grande na Ruined Shrine)](14a-plated-beetle.md) | etapa (filha do 14) | verificada |
| 15 | [Dano cedo na entrada de porta (auditoria de entrada de verdade)](15-auditoria-de-entrada.md) | problema (achado na 14a) | verificada |
| 14b | [Arena (rotina comum) e Hive Mecha](14b-arena-e-hive-mecha.md) | etapa (filha do 14) | verificada |
| 14c | [Flaahgra = Spore Spawn na Sunchamber (e a vespa da Ruined Nursery, sobra da spec 15)](14c-flaahgra.md) | etapa (filha do 14) | verificada |
| 14d | [Incinerator Drone (arena do Burn Dome: o míssil do suporte tranca a porta)](14d-incinerator-drone.md) | etapa (filha do 14) | verificada |
| 14f | [Rodadas e cadeia com os chefes (fecha o épico 14)](14f-rodadas-e-cadeia-com-chefes.md) | etapa (filha do 14) | verificada |
| 16 | [Arremates: demos e tela de título (demos desligadas, logo METROID PRIME)](16-titulo-e-demos.md) | problema (itens abertos do usuário) | verificada |
| 17 | [Magmoor Caverns](17-magmoor-caverns.md) | etapa (épico) | verificada (01/11/2026; 17a–17j verificadas: as 29 salas, 7 itens, 58 itens em 7 rodadas nas três áreas) |
| 17a | [Mais espaço no `$8F` (as duas faixas órfãs da Norfair)](17a-mais-espaco-8f.md) | etapa (filha do 17; toolchain) | verificada |
| 17b | [Lugar da Magmoor na área 2 (e o calor por área)](17b-area-da-magmoor.md) | etapa (filha do 17; toolchain) | verificada |
| 17c | [Grafo, mapa e travas do Prime da Magmoor](17c-grafo-e-mapa-magmoor.md) | etapa (filha do 17; dados, nenhuma sala) | verificada |
| 17d | [Estilo das cavernas de lava (tilesets 09/0A), lava e a porta de onda](17d-estilo-das-cavernas-de-lava.md) | etapa (filha do 17; estilo, lava medida numa ROM de teste) | verificada |
| 17e | [Elevadores de verdade para a Magmoor](17e-elevadores-da-magmoor.md) | etapa (filha do 17; as 2 salas de elevador da Magmoor) | verificada |
| 17f | [Região A da Magmoor (norte)](17f-regiao-a-magmoor.md) | etapa (filha do 17; 8 salas, Save Station A, 2 mísseis, calor e lava) | verificada |
| 17g | [Inimigos da Magmoor (região A)](17g-inimigos-magmoor.md) | etapa (filha do 17; 19 inimigos em 6 salas, auditoria de entrada, caminhadas medidas de novo) | verificada |
| 17h | [Região B da Magmoor (centro: Monitor Station, Warrior Shrine, Fiery Shores, a saída para o Tallon)](17h-regiao-b-magmoor.md) | etapa (filha do 17; 7 salas + a P16 aberta, 3 itens, parede de Power Bomb, porta de chão/teto, 2 Violas, Magdolite fora) | verificada |
| 17i | [Região C da Magmoor (sul: Twin Fires, Geothermal Core, Workstation, Save Station B)](17i-regiao-c-magmoor.md) | etapa (filha do 17; 12 salas, portas de onda/gelo, 2 itens, 7 inimigos, a ROM de teste da 17d na Mines West, a bateria em 2 grupos) | verificada |
| 17j | [Rodadas das três áreas e a cadeia completa (fecha o épico 17)](17j-rodadas-e-cadeia-tres-areas.md) | etapa (filha do 17; 58 itens, 58%, a cadeia com a Magmoor em 3 partes ligadas por estado salvo, a linha do épico) | verificada |
| 18 | [Phendrana Drifts](18-phendrana-drifts.md) | etapa (épico) | verificada (04/11/2026; 18a–18n verificadas: as 56 salas, 17 itens com o Super Missile do SM, os dois chefes (Sheegoth e Thardus), só a Gravity Chamber inundada; 75 itens em 7 rodadas nas quatro áreas, 75%; área 4, três caras e Metroids = padrão aceito, a confirmar) |
| 18a | [Espaço do `$8F` para Phendrana (a faixa das demos)](18a-espaco-8f-das-demos.md) | etapa (filha do 18; toolchain) | verificada |
| 18b | [Lugar de Phendrana na área 4 (e o plano das áreas)](18b-area-da-phendrana.md) | etapa (filha do 18; toolchain; área = padrão aceito, a confirmar) | verificada |
| 18c | [Grafo, mapa e travas do Prime de Phendrana](18c-grafo-e-mapa-phendrana.md) | etapa (filha do 18; dados, nenhuma sala) | verificada |
| 18d | [Estilos do gelo (três caras), neve, portas e água medidas numa ROM de teste](18d-estilos-do-gelo.md) | etapa (filha do 18; estilo, neve = esporos, `build.py --teste-18d`) | verificada |
| 18e | [Elevadores de verdade para Phendrana e o grupo C de testes](18e-elevadores-de-phendrana.md) | etapa (filha do 18; as 2 salas de elevador de Phendrana, `--grupo C`) | verificada |
| 18f | [Região A de Phendrana (norte: Shorelines, Ice Temple, Chapel, Ice Ruins East)](18f-regiao-a-phendrana.md) | etapa (filha do 18; 11 salas + a P0 aberta, Save Station B, 4 mísseis, bomb slot, porta de onda da Chapel) | verificada |
| 18g | [Inimigos de Phendrana (região A)](18g-inimigos-phendrana.md) | etapa (filha do 18; 3 Zeelas, 2 orbes = cópia justa do ATOMIC, 2 Zeelas; justiça em toda rodada, deriva longe das portas, `entradas_de_porta_phendrana`) | verificada |
| 18h | [Sheegoth (arena da Chapel of the Elders)](18h-sheegoth.md) | etapa (filha do 18; o Dessgeega em cores de gelo, imune ao feixe sem carga, + 2 Sidehoppers pequenos; a porta tranca até a vitória; o míssil no lugar do Wave aparece no altar; arenas de qualquer área no validador; `phendrana_sheegoth`) | verificada |
| 18i | [Região B de Phendrana](18i-regiao-b-phendrana.md) | etapa (filha do 18; 12 salas; Save Station A e Map Station; portas vermelhas `$C2`/`$C3`; a expansão de PB num nicho com tampa de plasma dentro da sala (mecanismo novo), o E-tank atrás de bloco de bomba, o míssil da Hydra; porta de onda vertical roxa nova; 9 inimigos; `phendrana_regiao_b_rota`, `phendrana_save_station_a`, `phendrana_map_station`) | verificada |
| 18j | [Região C de Phendrana](18j-regiao-c-phendrana.md) | etapa (filha do 18; 5 salas novas e a P29 aberta: as duas Quarantine Tunnels, a Quarantine Cave (vazia até o Thardus, 18k), a Quarantine Monitor atrás de túnel de Morph com o míssil, a Transport Access com o E-tank num nicho de plasma (rodada 6) atrás das portas de gelo; a porta de onda vertical pintada na cara de neve; 5 orbes; regra nova: a porta de Morph fecha algo; `phendrana_regiao_c_rota`) | verificada |
| 18k | [Thardus (arena da Quarantine Cave)](18k-thardus.md) | etapa (filha do 18; cópia do Bomb Torizo com vida 400, em cores de pedra, o código do Torizo corrigido no lugar (as 7 leituras da área, sem a bruma); acorda na entrada; as portas L0/R0 trancam (cinza tipo 2, o bit `$04` do Torizo) até a vitória; bit `$10`; sem prêmio (decisão 3); `phendrana_thardus`) | verificada |
| 18l | [Região D de Phendrana (observatório, torres, laboratórios; o Super Missile)](18l-regiao-d-phendrana.md) | etapa (filha do 18; as 12 salas e a R0 da Hydra aberta; o Super Missile do SM no Observatory atrás de um bloco de bomba; Save Station D (estação 3); portas vermelhas `$C4`/`$C5`, de onda e de gelo; E-tank e míssil da Aether; os Metroids = cópia justa do Metroid do SM (vida 100, toque comum 20, IA de tiro e tabela próprias) e a regra da câmera; `phendrana_regiao_d_rota`, `phendrana_save_station_d`) | verificada |
| 18m | [Região E de Phendrana (sul fundo; a Gravity Chamber inundada)](18m-regiao-e-phendrana.md) | etapa (filha do 18; as 14 salas, a R0 da Transport Access e a L0 da Pike Access abertas: Phendrana com as 56 salas e os 17 itens; a Gravity Chamber inundada (`FLOODED`, andada sem a suit, escada de rocha de 3 linhas; o míssil do lugar da Gravity no fundo, rodada 4, e o da borda com a Gravity + Space Jump, rodada 5); o míssil da Frost Cave; Save Station C (estação 4); portas de plasma da Storage Cave; a porta de Morph da Security Cave com blocos de Power Bomb dos dois lados (a expansão de PB, rodada 6); Beetles e orbes, o Ripper fora; `phendrana_regiao_e_rota`, `phendrana_regiao_e_agua`, `phendrana_save_station_c`) | verificada |
| 18n | [Rodadas das quatro áreas e a cadeia completa (75%)](18n-rodadas-e-cadeia-quatro-areas.md) | etapa (filha do 18; fecha o épico: `check_world_rounds` com Phendrana — 75 itens em 7 rodadas, 75% —, `check_epic_phendrana`; a cadeia completa em 4 partes (A, B, C, C) com os 17 itens de Phendrana nas rodadas declaradas, o Sheegoth e o Thardus vencidos de verdade e a tela do fim do SM com 75%) | verificada |
| 19 | [Phazon Mines](19-phazon-mines.md) | etapa (épico) | verificada (10/11/2026, fechado na 19m: 19a–19m verificadas; 42 salas, 13 itens, os 2 chefes, 88%; seção "Verificação do épico") |
| 19a | [Espaço no `$8F` e no `$A1` para a Mines (mais faixas órfãs)](19a-espaco-8f-e-a1.md) | etapa (filha do 19; toolchain) | verificada |
| 19b | [Lugar da Mines na área 5 (e a lista do mapa no `$81`)](19b-area-da-mines.md) | etapa (filha do 19; toolchain; área = padrão aceito, a confirmar) | verificada |
| 19c | [Grafo, mapa e travas do Prime da Mines](19c-grafo-e-mapa-mines.md) | etapa (filha do 19; dados, nenhuma sala; a varredura do gancho) | verificada |
| 19d | [Estilos da mina (duas caras), o azul do phazon e as portas, numa ROM de teste](19d-estilos-da-mina.md) | etapa (filha do 19; base pirata `$0E` e rocha `$08`, `build.py --teste-19d`, ROM do jogo igual) | verificada |
| 19e | [Elevadores de verdade para a Mines e o grupo D de testes](19e-elevadores-da-mines.md) | etapa (filha do 19; as 2 salas de elevador da Mines, a Mines embaixo do Tallon e da Magmoor, `--grupo D`) | verificada |
| 19f | [Região A da Mines (nível de cima) e o Grapple Beam do SM](19f-regiao-a-mines.md) | etapa (filha do 19; 13 salas, Save Station A, 3 mísseis, o Grapple na Storage Depot B, 79 itens; a parte 4 da cadeia no grupo D) | verificada |
| 19g | [Inimigos da Mines (região A)](19g-inimigos-mines.md) | etapa (filha do 19; camada 0 do Prime: 2 piratas na Main Quarry, 2 orbes na Elevator Access A; a tabela de B–D com propostas; regra nova do que atira na altura da Samus; `mines_inimigos_vivos`, `entradas_de_porta_mines`) | verificada |
| 19h | [Phazon Elite (arena da Elite Research)](19h-phazon-elite.md) | etapa (filha do 19; cópia do pirata ninja dourado `$F593` em `$A0:F9BF` com vida 400 (20 tiros do Power Beam), toque 40, o feixe sem carga fere, cores de phazon e a paleta do salto; arena de cota de mortes, bit `$08` da área 5, a porta de teto para a Security Access B cinza até a vitória e de gelo depois; sem prêmio; a sala não mudou; `check_ninja`, linha "chefes da Mines"; `mines_phazon_elite`) | verificada |
| 19i | [Região B da Mines (nível do meio)](19i-regiao-b-mines.md) | etapa (filha do 19; 12 salas; Save Station B (estação 2) e a Map Station, com a lista de ícones de map station da área 5 nova no `$82`; mísseis da Elite Control Access e no lugar da Power Bomb (labirinto da Central Dynamo, rodada 5), E-tank da Ventilation Shaft e míssil da Metroid Quarantine A atrás de blocos de PB (rodada 6); a parede de PB da Maintenance Tunnel; 1 pirata, 1 Mella, 2 Metroids; `MAZES`; 83 itens, 83%; `mines_regiao_b_rota`, `mines_regiao_b_rodada_6`, `mines_save_station_b`, `mines_map_station`) | verificada |
| 19j | [Região C da Mines (oeste)](19j-regiao-c-mines.md) | etapa (filha do 19; 5 salas e a P25 aberta; o PPC com o salão da Omega Research e o míssil num fosso de PB (rodada 6), o E-tank da Processing Center Access entre portas de plasma (rodada 6), a Elite Quarters pronta para a 19k; a parede da Maintenance Tunnel fecha o atalho Magmoor ↔ Tallon até a rodada 6; o gancho da Transport Access sem trava; 85 itens, 85%; `mines_regiao_c_rota`) | verificada |
| 19k | [Omega Pirate](19k-omega-pirate.md) | etapa (filha do 19; a segunda cópia do Bomb Torizo na Elite Quarters, vida 1200, imune ao feixe sem carga, na posição do Thardus; as cores por área com seletores no `$AA`; as 2 portas cinza de tipo 2 até a vitória; sem prêmio; `mines_omega_pirate`, a luta só com mísseis) | verificada |
| 19l | [Região D da Mines (nível de baixo)](19l-regiao-d-mines.md) | etapa (filha do 19; as 10 salas do nível de baixo, as 42 da Mines na ROM; a porta de plasma vertical; a Fungal Hall A com gelo do lado dela e plasma do outro (`SIDE_CAPS`); a Phazon Mining Tunnel com o túnel de bomba e de PB; a Missile Station (PLM `$B6EB`); Save Station C; 3 mísseis (rodada 6); os Metroids, os Hunter Metroids, a Sova, os orbes e o pirata; `mines_regiao_d_rota`, `mines_save_station_c`) | verificada |
| 19m | [Rodadas das cinco áreas e a cadeia completa](19m-rodadas-e-cadeia-cinco-areas.md) | etapa (filha do 19; a linha das rodadas com os 2 elevadores da Mines; `check_epic_mines`; a cadeia em 5 partes pelos 13 itens da Mines, o Phazon Elite e o Omega Pirate vencidos de verdade, os 2 elevadores; 88% na tela do fim; fecha o épico 19; a ROM não muda) | verificada |
| 20 | [Impact Crater](20-impact-crater.md) | etapa (épico) | verificada (11/11/2026, fechado na 20j: 20a–20j verificadas; 12 salas, 90 telas, nenhum item, o Metroid Prime vencido de verdade, o fim do jogo; a cadeia completa do começo à tela do fim com 88%; seção "Verificação do épico") |
| 20a | [Levantamento da Impact Crater](20a-levantamento-impact-crater.md) | etapa (filha do 20; só leitura, ROM igual: salas, itens, inimigos, travas, phazon, a luta, o espaço) | verificada |
| 20b | [Espaço no `$8F` e no `$A1` para a Impact Crater (a checagem de folga)](20b-espaco-e-toolchain.md) | etapa (filha do 20; toolchain, ROM igual; `check_impact_space`: $8F 2849 livres para ~1050, $A1 8786 para ~200) | verificada |
| 20c | [Grafo, mapa e travas do Prime da Impact Crater](20c-grafo-e-mapa-impact.md) | etapa (filha do 20; dados, nenhuma sala, ROM igual; `tools/impact/`, `check_impact_graph`: 12 salas, 11 ligações (3 de chão/teto), 90 telas debaixo do Artifact Temple no mapa da área 0, 70 de 80 bytes com o Tallon; 10 docas de plasma, 1 de evento, 12 sem porta) | verificada |
| 20d | [Estilo da cratera (tileset, paleta e cores de phazon)](20d-estilo-impact.md) | etapa (filha do 20; numa ROM de teste, nenhuma sala, ROM do jogo igual; `tools/impact/style.py`, `check_impact_style`: a rocha da Mines no tileset `$03` com a rocha avermelhada (matiz 12 das texturas do Prime) e o phazon igual ao da Mines) | verificada |
| 20e | [A entrada da Impact Crater](20e-entrada-impact.md) | etapa (filha do 20; **muda a ROM**: Crater Entry Point (Save Station = estação 2 da área 0) e Crater Tunnel A com portas de plasma, na área 0; o teleporte do Artifact Temple = elevador dentro da área 0, ligado pelo bit `$10` da área 5 (Omega Pirate vencido); `check_impact_rooms`, `check_teleporter_states`; testes `impact_entrada_rota`, `impact_save_station`) | verificada |
| 20f | [Phazon Core, Crater Missile Station e Crater Tunnel B](20f-phazon-core-impact.md) | etapa (filha do 20; **muda a ROM**: a região B da cratera na área 0, portas de plasma, a recarga de mísseis (PLM `$B6EB`) na Missile Station, a Tunnel B sem o trilho de Spider Ball; 2 Metroids na Phazon Core (o Burrower da Tunnel B é de camada inativa no Prime: fora); `check_impact_enemies` (tela a tela); testes `impact_regiao_b_rota`, `impact_inimigos_vivos`) | verificada |
| 20g | [Phazon Infusion Chamber e Subchambers 1 a 5](20g-infusion-subchambers-impact.md) | etapa (filha do 20; **muda a ROM**: a região C da cratera na área 0 (6 salas), a porta de plasma Tunnel B ↔ Infusion, a descida sem tampa (portas de chão/teto); o phazon que machuca = o ácido do SM (FX tipo 4, machuca com a Gravity; `RoomDef.acid`, regra da `check_lava`) em poças fora do caminho nas Subchambers One, Two e Four (as com porta de chão não podem); a trava de evento da Infusion fora (`EVENT_OUT`); a descida vazia (no Prime só a luta, decisão 3); testes `impact_descida_rota`, `impact_phazon_dano`; a tela vazia do mapa da área 0 em (30, 30)) | verificada |
| 20h | [Metroid Prime (arena da Lair)](20h-metroid-prime-impact.md) | etapa (filha do 20; **muda a ROM**: a Metroid Prime Lair (região D, a última sala da cratera); a terceira cópia do Bomb Torizo (`METROID_PRIME` `$A0:FA3F`, vida 3000, os ataques e a vulnerabilidade do Torizo); a arena do bit do Torizo com o bit `$10` da área 0 = o chefe final vencido; a porta do teto trancada até a vitória (cinza tipo 2, `BOSS_DOORS`); `check_impact_boss`, `check_gates` nas salas da cratera; testes `impact_metroid_prime` (a luta vencida de verdade) e `impact_prime_porta_e_morte`) | verificada |
| 20i | [Fim do jogo (a saída da Lair, créditos e a porcentagem)](20i-fim-do-jogo-impact.md) | etapa (filha do 20; **muda a ROM**: a saída da Lair (main ASM nos dois estados, `tools/impact/ending.py`): depois da vitória (bit `$10` da área 0), a tampa aberta e o pulo para a porta do teto travam a Samus e ligam o fim do SM reaproveitado (estado `$26` → `$27`: créditos e "YOUR RATE FOR COLLECTING ITEMS"); `check_impact_ending` (o bit, a porta, o fim do SM intacto, a porcentagem 88% com as tabelas da ROM); testes `impact_fim_do_jogo` (a luta real, a saída, os créditos, a tela com 88%) e `impact_fim_sem_vitoria`) | verificada |
| 20j | [Rodadas e a cadeia completa com a Impact Crater](20j-rodadas-e-cadeia-impact.md) | etapa (filha do 20; a linha das rodadas igual (a cratera não tem item: nenhuma rodada muda); `check_epic_impact` (as 12 salas, as 11 ligações do Prime, nenhum item na cratera, 88%, o teleporte da última rodada, o chefe e o bit do fim); a cadeia em 6 partes: a parte 6 desce o teleporte, anda a cratera, vence o Metroid Prime de verdade e sai pela porta da Lair para a tela do fim com 88% (o evento `$0E` por RAM saiu); fecha o épico 20; a ROM não muda) | verificada |
| 21 | [Artes do Prime: chefes e Samus, o mais fiel possível](21-artes-prime.md) | aprovada (11/11/2026); em andamento: 21a verificada parcialmente (12/11/2026); 21b em andamento (cores dos feixes em ROM de teste; falta conferir no emulador) |
| 21a | [Levantamento da arte do Prime](21a-levantamento-arte.md) | etapa (filha do 21; só leitura, ROM igual; 27 texturas medidas, 47 970 cores somadas, limite de 16 cores por paleta; nomes de chefes e Samus achados nos pacotes; tiles da Samus e dos chefes do SM ainda não medidos) | verificada parcialmente |
| 21b | [Efeitos de poder do Prime](21b-efeitos-de-poder.md) | etapa (filha do 21; ROM de teste `--teste-21b` com as cores medidas do Prime nas paletas de Power, Wave e Ice; ROM do jogo igual; Plasma e Phazon sem cor identificada; conferência no emulador pendente) | em andamento |
| 22 | [Trilhas sonoras do Prime](22-trilhas-prime.md) | aprovada (11/11/2026); em andamento: 22a parcial (17/11/2026: cabeçalhos de 115 `.dsp` medidos, ≈ 18 KB/s em ARAM; decodificação e teste no emulador não feitos) |
| 23 | [Fidelidade ao Prime: visores, scan, HUD, atmosfera, chefes e inimigos](23-fidelidade-prime.md) | aberto (épico, proposta) | sem filha começada; começa com 'pode seguir'; esforço a definir na 23a |

A ordem final de 01–06 pode mudar conforme o esforço medido em cada spec.

## Modelo

```markdown
# NN — Título

Estado: rascunho | aprovada | implementada | verificada
Esforço estimado: (por parte)

## Contexto
Quem nota o problema / o que o jogador vê, e por que agora.

## Estado atual (verificado)
O que acontece hoje, com endereços da ROM ($BB:AAAA), `arquivo:linha` e como foi conferido
(leitura de bytes, emulador, imagem).

## Causa (problemas)
Por que acontece.

## Mudança proposta
O que muda, onde, com bytes/rotinas/estruturas concretas. Espaço livre usado (banco, endereço,
tamanho). Nenhuma decisão de projeto deixada para quem implementa.

## Critérios de aceite
Numerados, passa/falha, cada um ligado a um teste ou checagem:
1. ... (teste `nome` em tests/run_tests.py: protege=...; falha_quando=...; não_prova=...)

## Plano de testes
| Camada | O quê | Qtde |
| validate.py | ... | +N |
| run_tests.py (emulador) | ... | +N |
| imagem | ... | +N |

## Riscos e reversão
O que pode quebrar; como desfazer (todas as mudanças vêm de tools/, então reverter o código e
reconstruir basta).

## Fora de escopo
- ...

## Desvios (preenchido na implementação)
```

## Regras do projeto que valem para toda spec

- Não commitar (a pasta nem é git). Não apagar nada fora do escopo.
- Não declarar pronto sem validate + build + testes. Relatar trabalho parcial como parcial.
- Menor mudança correta. Não silenciar erros.
- Fatos sobre a ROM sempre conferidos (bytes ou emulador), nunca de memória.
