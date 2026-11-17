# 07j — Elevadores de enfeite (e a casca do Artifact Temple)

Estado: verificada (22/10/2026: validate 33/68/0 com "5 desenhadas fora do build"; .ips sha1 `43f480e1…270c` igual; 26/26 testes)
Esforço estimado: 0,5 dia (spec 1 h, desenhos 2 h, validador/prévia 1 h, verificação 30 min)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (decisões 7 e 8; linha 07j)

## Contexto

O Prime tem 5 salas de transporte no Tallon (3 para a Chozo Ruins, 1 para a Magmoor, 1 para a
Phazon Mines) e o Artifact Temple (teleporte para a Impact Crater). Pela decisão 7 do épico, todas
viram becos sem saída com o elevador como cenário. A 07g já fez a primeira (Transport to Chozo
Ruins West, região A). Esta spec desenha as outras 4 e a casca do Artifact Temple, reaproveitando o
mesmo elevador de enfeite.

## Estado atual (verificado)

- `tools/tallon/rooms.py` (07d/07g): `ACTIVE_REGIONS = {"A"}`, `ACTIVE_ROOMS` = as 5 salas do MVP.
  Sala sem desenho = caixa aberta provisória (`placeholder`). `ALL_ROOMS` (tabela inteira) só passa
  pelas checagens de tabela/mapa (`check_layout`), não pelo alcance.
- `tools/tallon/layouts.py:150-170`: `transport_chozo_west` desenha o elevador à mão (poço de metal
  `$3B2`/`$377`, plataforma `$392/$397`, peças das salas de elevador vanilla do tileset 2).
- As 6 salas desta spec, pela tabela (`screens` e `LINKS`), e a única porta de cada uma:

  | P# | Sala | Região | Tamanho | Visual | Porta (lado/tela) → vizinha |
  |----|------|--------|---------|--------|-----------------------------|
  | 22 | Transport to Chozo Ruins East | C | 1×2 | caverna | L0 → Transport Tunnel C (C) |
  | 23 | Transport to Magmoor Caverns East | C | 1×2 | caverna | R1 → Transport Tunnel B (C) |
  | 41 | Transport to Chozo Ruins South | E | 1×2 | caverna | L1 → Transport Tunnel D (E) |
  | 43 | Transport to Phazon Mines East | E | 1×2 | caverna | L1 → Transport Tunnel E (E) |
  | 16 | Artifact Temple | B | 6×4 | superfície | T3 → Temple Lobby (B) |

  A vizinha de cada uma é da mesma região, então ao ligar a região a sala já tem a porta.
- Nenhuma dessas regiões (B, C, E) está ativa: as 6 salas não estão na ROM.
- Ícone de elevador no mapa de pausa: o jogo desenha as entradas 8–15 da lista de save/elevador
  (`$82:C873` na área 0) só quando o bit "elevador usado" está ligado
  (`used_save_stations_and_elevators`, spec 07f). Nossos elevadores não funcionam, então esse bit
  nunca liga e o ícone nunca apareceria; os rótulos "to <área>" só aparecem com a map station
  usada, e o Tallon não tem map station (decisão 6).

## Mudança proposta

1. **Elevador reaproveitável** (`tools/tallon/layouts.py`): função `elevator(c, sx, floor,
   shaft_bottom)` = poço de metal da linha 0 até `shaft_bottom` (colunas `sx..sx+3` abertas,
   paredes `sx-1` e `sx+4` sólidas com `$3B2`, ponta `$377` embaixo) e plataforma de 4 blocos no
   chão (`floor`) com as pontas. Devolve a lista `skin`. A `transport_chozo_west` passa a usá-la
   **com o mesmo resultado em bytes** (a lista sai na mesma ordem).
2. **Desenhos novos** (mesmas regras da 07g: degraus de no máximo 4 blocos, sem salto de vão
   obrigatório, sem buraco sem saída):
   - **Chozo East** (1×2, porta L0 no alto): a borda da porta é rocha até o chão; três degraus
     descem para a direita até o chão da tela de baixo; elevador à direita (plataforma nas colunas
     11–14, poço subindo encostado na parede direita, até a linha 9).
   - **Magmoor East** (1×2, porta R1 embaixo): corredor plano na tela de baixo; elevador à
     esquerda (colunas 3–6), poço subindo pela rocha até o teto da sala.
   - **Chozo South** e **Mines East** (1×2, porta L1 embaixo): o mesmo corredor, espelhado
     (elevador nas colunas 9–12). Uma função com o lado da porta serve às três.
   - **Artifact Temple** (6×4, porta T3 no teto): casca sem teleporte e sem Meta Ridley. Pirâmide
     de degraus (templo Chozo): o topo é a plataforma da porta (linha 6); degraus de 4 de altura
     e 2 de largura descem dos dois lados até o chão do templo (linha 54); teto de rocha irregular;
     pedestais baixos (4 blocos) no chão, lembrando os totens dos artefatos.
     Sem itens, sem inimigos.
3. **Ativação**: as 6 salas ficam prontas em `LAYOUTS` mas **não entram no build**: cada uma entra
   quando a região dela for ligada (07k: B e C; 07m: E). Nada muda em `ACTIVE_REGIONS` /
   `ACTIVE_ROOMS`, então nenhuma porta aponta para sala não construída e a ROM não muda.
4. **Validador** (`tools/validate.py`): `check_area` separa o trabalho por sala em `check_room`.
   `check_tallon` passa a rodar `check_room` (alcance 07b de cada entrada para cada porta, arte
   só sobre bloco sólido, colisão igual sem a arte) em **toda sala com desenho que ainda não está no
   build**, montada com a região dela sozinha (como a 07d fez com o mapa). A linha do Tallon ganha
   `, 5 desenhadas fora do build`.
5. **Prévia** (`tools/preview_rooms.py --rascunhos-tallon`): desenha essas salas com o tileset da
   ROM base em `specs/img/07j-sala-<nome>.png`.
6. **Mapa de pausa**: sem ícone de elevador (ver "Estado atual": não aparece sem elevador que
   funcione; nada barato a fazer). Documentado, sem código.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 0 problemas, "33 salas, 68 portas" (igual) e linha do Tallon
   com `5 desenhadas fora do build`. (protege = alcance das 6 salas sem Space Jump antes de entrarem
   na ROM; falha_quando = degrau alto demais, porta inalcançável, arte fora de bloco sólido;
   não_prova = como fica no emulador, isso é da spec da região)
2. Mutação: subir um degrau do Artifact Temple 4 blocos (degrau de 8) → validate acusa porta
   inalcançável naquela sala; desfeita a mutação, 0 problemas.
3. `python3 -I tools/build.py` → `build/metroid_prime_snes.ips` sha1
   `43f480e12ee7a3a18d5c700fcba90c2e3183270c` (**igual**: nenhuma sala nova é ativada, e a Chozo West
   com a função nova sai com os mesmos bytes).
4. `python3 -I tests/run_tests.py` → 26/26 (nenhum teste novo: nada novo na ROM).
5. Imagens `specs/img/07j-sala-*.png` (5) olhadas uma a uma: elevador igual ao da Chozo West, sem
   peça quebrada, degraus legíveis.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `check_room` nas salas desenhadas fora do build; lugar sem volta (todas as salas a pé) | +2 checagens (5 salas; +2 casos no `reach.self_test`) |
| mutação à mão | degrau alto no Artifact Temple | 1 |
| build | sha1 igual | 1 |
| run_tests.py | nenhum novo | 0 |
| imagem | 4 transportes + Artifact Temple | 5 |

## Riscos e reversão

- As salas só vão ao emulador quando a região entrar: lá podem aparecer detalhes de visual
  (peças de canto do estilo) que a prévia com a ROM base já mostra, mas não a câmera.
- Artifact Temple: a pirâmide ocupa o meio da sala; quando a spec dos artefatos/Meta Ridley vier,
  o desenho pode mudar.
- Reversão: tirar as 5 funções novas de `LAYOUTS` (voltam a ser caixas provisórias), `check_room`
  pode ficar (é só a divisão do laço de `check_area`).

## Fora de escopo

- Elevador funcionando, teleporte do Artifact Temple, Meta Ridley, artefatos.
- Ligar as regiões B, C, E (07k, 07m) e as outras salas delas.
- Ícone/rótulo de elevador no mapa de pausa.
- Inimigos (07i) e itens (07h) nessas salas.

## Desvios (preenchido na implementação)

Verificação (22/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (tabela inteira, regiões ativas: A, 5 salas construídas,
  5 desenhadas fora do build): 44 salas, 44 ligações, 251 telas, mapa 47/80 …` e
  `33 salas, 68 portas, 0 problemas`.
- Mutações (na memória, `LAYOUTS` trocado e desfeito): degrau do Artifact Temple 4 blocos mais baixo
  (degrau de 8) → "tallon_artifact_temple: 41 lugares sem volta a nenhuma porta…"; degrau de 1 da
  Chozo East tirado (subida de 8) → "5 lugares sem volta…"; buraco sob a plataforma da Magmoor East →
  "acabamento em (5,26) cai num bloco que não é sólido". Sem mutação: 0 problemas.
- `python3 -I tools/build.py` duas vezes → `.ips` sha1 `43f480e12ee7a3a18d5c700fcba90c2e3183270c`
  (**igual ao de antes**: nenhuma sala nova ativada; a Chozo West com `elevator()` sai com os mesmos
  bytes, e a prévia dela `research/render/tallon_tallon_transport_chozo_west.png` também é idêntica).
- `python3 -I tests/run_tests.py` → **26/26**.
- Imagens (tileset da ROM base, olhadas): `specs/img/07j-sala-transport-chozo-east.png`,
  `-transport-magmoor-east`, `-transport-chozo-south`, `-transport-mines-east` (igual à South, mesma
  função), `-artifact-temple`. Tamanho comprimido: 260, 197, 208, 208 e 1190 bytes.

Desvios e detalhes:

- **Checagem nova "lugar sem volta"** (`reach.stuck`, chamada em `reach_on_foot`): com uma porta só,
  "toda porta alcançável de toda entrada" é sempre verdade (a Samus entra pela própria porta), então
  o alcance da 07b não pegava um buraco sem saída num beco. Agora, para cada entrada, todo lugar de pé
  alcançável precisa ter caminho de volta a alguma porta. Vale para todas as salas a pé (as 5 do MVP
  passam sem mudança). Dois casos novos em `reach.self_test` ("buraco sem volta" preso, "chão plano"
  livre). Foi ela que achou o problema abaixo.
- **Artifact Temple**: o topo da pirâmide ficou na linha 6 (a plataforma da porta faz parte do topo),
  e o teto ao lado do poço da porta foi aberto nas linhas 1–2 (colunas 44–52 e 59–67): com o teto na
  linha 2, subir do primeiro degrau ao topo não tinha um bloco de folga sobre a cabeça e a sala inteira
  virava armadilha (78 lugares sem volta). Pedestais: 4 a oeste e 2 a leste (o lado leste é estreito,
  a porta T3 não fica no meio da sala).
- `check_area` foi dividida em `check_area` + `check_room` (mesmo conteúdo; a checagem de objetos em
  salas inexistentes agora roda mesmo se o desenho da 1ª sala falhar).
- Mapa de pausa: nenhum ícone de elevador (motivo em "Estado atual"); nenhuma sala nova está ativa.
- Ativação: as 5 salas entram sozinhas quando a região for ligada (`ACTIVE_REGIONS`; se a região usar
  `ACTIVE_ROOMS`, incluir a chave lá).
