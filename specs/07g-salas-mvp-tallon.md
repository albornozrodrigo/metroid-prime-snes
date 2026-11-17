# 07g — Salas do MVP do Tallon (com a chegada mínima)

Estado: verificada (22/10/2026: validate 33/68/0 com a linha do Tallon; .ips sha1 `5a7e4977…2cb7`, igual ao reconstruir; 22/22 testes)
Esforço estimado: 1 dia (spec 1 h, salas 3 h, chegada 2 h, teste 1 h, verificação 1 h)
Épico: [07 — Tallon Overworld](07-tallon-overworld.md) (MVP; decisões 1, 2, 5, 7 e 8)

## Contexto

Até a 07d o Tallon existia só como tabela: nenhuma sala na ROM. Quem termina a fragata pousa na
Landing Site **da Crateria vanilla**. O líder mudou a ordem: a 07g vem **antes** da 07e/07f e
inclui a ligação mínima de chegada, para o MVP ser jogável: o fim da fragata pousa na Landing Site
nova, ao lado da nave, e dali a Samus anda, só com o Power Beam, pelas 5 salas do caminho do Prime
que não pede item nenhum.

## Estado atual (verificado)

- `tools/tallon/rooms.py` (07d): 44 salas, `ACTIVE_REGIONS = frozenset()`, salas com caixa
  provisória. A ativação é por região; a região A tem 7 salas (Gully e Alcove ficam fora do MVP).
- `tools/areas.py`: `TALLON` declarada, fora de `AREAS`, `load_stations=[]`.
- `tools/build.py`: `write_pause_map` para se a área não estiver em `VANILLA_PAUSE` (só a 3 está).
- Fim da fragata (spec 05) — lido no código C (`vendor/sm/src/sm_82.c:94`, `sm_a2.c:1309-1500`) e
  nos bytes: com `loading_game_state = $22` o jogo carrega a **área 0, estação `$12`** (não a 0):
  `$82:8032 STZ $079F`, `$82:8035 A9 12 00` (`LDA #$0012; STA $078B`). A estação `$12` vanilla
  (`$80:C5C1`) = sala `$91F8`, câmera x `$400`, Samus y `$80`. A nave (`GunshipTop_Init`) começa
  17 px acima da Samus e desce (`GunshipTop_3`, `$A2:A80C`) rápido até y `$300` e devagar até
  **y `$45F` fixo** (`$A2:A80F C9 00 03`, `$A2:A8AD C9 5F 04`, `$A2:A8B2 A9 5F 04`); depois
  `GunshipTop_7` grava a estação **0** da área 0 e salva. Na Landing Site vanilla a nave fica com
  o chão na linha 77 (y do topo = 77·16 − 88 − 25 = `$45F`). A nossa Landing Site tem 3 telas
  (48 linhas): essa altura não cabe.
- A nave vanilla salva em qualquer área ≠ 3: os patches de `tools/frigate/ending.py` (`gunship`)
  só mudam a área 3 (conferido: todas as rotinas comparam `$079F` com 3).
- Fundo: `$8F:B8B4` (Parlor) é rocha de caverna; no emulador o céu da superfície ficava "dentro de
  uma caverna". O céu vanilla da Landing Site vem de `$8F:B76A`: só comandos `0E` (por porta de
  entrada) copiando um dos tilemaps de nuvens `$8A:B180…$8A:D980` ($800 bytes) para o BG2, com
  scroll `$0181`. `$8F:B80A` (sala `$968F`) copia só `$8A:C180 → VRAM $4800`; a outra metade do
  BG2 (`$4C00`) fica com lixo da sala anterior (visto no emulador).
- Espaço antes: `$8F` livre a partir de `$8F:F029` (**4055 bytes**; o épico citava 4075, medido
  antes da spec 06), `$83` de `$83:B04E`, expandido até PC `$306DF4`.

## Mudança proposta

1. **Ativação por sala** (`tools/tallon/rooms.py`): `ACTIVE_REGIONS = {"A"}` e
   `ACTIVE_ROOMS` = as 5 salas do MVP; `build_rooms(regiões, only=None)` monta só essas (sala ativa
   fora das regiões ativas = erro). Porta para sala não construída = parede, como para região
   desligada (decisão 8). `ROOMS = build_rooms(ACTIVE_REGIONS, ACTIVE_ROOMS)`.
2. **Desenhos** em `tools/tallon/layouts.py` (novo; `LAYOUTS[chave]() -> Shape`: canvas + nave +
   arte por cima de blocos). `build_rooms` usa o desenho quando existe e confere o tamanho com a
   tabela. Regras: degraus de no máximo 4 blocos, nenhum salto de vão no caminho, nenhum buraco
   sem saída (o pulo medido na 07b sobe 7).

   | Sala (P#, tamanho) | Visual | Desenho |
   |---|---|---|
   | Landing Site (P0, 5×3) | superfície, chuva, céu | bacia a céu aberto; nave no meio (centro bloco 44, chão linha 42); pedra com musgo à esquerda dela (degrau de 4) para subir na nave; lago raso a oeste; penhasco a oeste com a boca da caverna até a porta L2; terraços a leste até o planalto sob a saliência (onde vão abrir Temple Hall e Waterfall Cavern); portas L0/L1/R1/R2 fechadas |
   | Canyon Cavern (P2, 2×1) | caverna (tijolos) | túnel com teto irregular, rebaixo de 2 no meio, bloco caído no teto, entulho de 2 |
   | Tallon Canyon (P6, 4×3) | superfície, chuva, céu | da porta R0 (alto, leste) terraços de 4 descem ao fundo do cânion (riacho), que sobe de novo em degraus até a porta L1 (oeste); saliências no teto, uma laje de pedra solta no meio; L0 (Root Tunnel) e T3 (Gully) fechadas |
   | Transport Tunnel A (P9, 2×1) | caverna | túnel com trecho elevado de 2 e vigas no teto |
   | Transport to Chozo Ruins West (P14, 2×2) | caverna | beco sem saída (decisão 7): degraus descem da porta até o elevador de enfeite: plataforma de metal no chão e poço de metal subindo pela rocha (peças `$392/$397/$377/$3B2` das salas de elevador vanilla do tileset 2, `$8F:9938`/`$8F:94CC`), sem inimigo de elevador e sem porta |

3. **Fundo**: superfície = céu da Landing Site: lista nova de 20 bytes em `$8F`
   (`crateria.SKY_BG`: `$8A:C180` → VRAM `$4800` e `$4C00`) com scroll `$0181`; cavernas =
   `$8F:B905` (fundo das salas vanilla do tileset 2 `$99F9`, `$9A90`, `$9804`). `RoomDef` ganha
   `library_bg`/`layer2`/`skin`/`backdrop` (padrão = o de antes; a fragata não muda). O build aceita
   uma lista de fundo em bytes e a põe em `$8F` uma vez, na frente da primeira sala que a usa.
4. **Área 0 no build**: `TALLON` entra em `AREAS` (depois da fragata: endereços da fragata não
   mudam). `AreaDef.pause_map` (novo, padrão `True`); o Tallon fica com `False`: sem mapa de pausa
   próprio nem lista de SRAM até a 07f (o jogo usa as tabelas vanilla da Crateria).
5. **Chegada** (`areas.gunship_stations`, `build.py`, `ending.py`):
   - estação **0** da área 0 = em cima da nave (Samus 31 px acima do y do topo, como a vanilla):
     onde a nave salva e onde o continue começa;
   - estação **`$12`** = a mesma sala, Samus na coluna da nave em y `$80` (de onde a nave desce no
     fim da fragata); o build confere `$82:8035 = A9 12 00`;
   - `ending.landing_height`: troca as 3 constantes de `GunshipTop_3` pela altura da nossa nave
     (topo y = `$22F`; trecho lento começa em `$22F − $15F = $D0`). Só a cena de chegada usa essas
     constantes, e ela só acontece na área 0 (onde a Crateria vanilla ficou inalcançável);
   - `write_load_station` passa a pôr a câmera onde a Samus está (no canto da sala se ela está
     a menos de 192 px dele, que é o caso de todas as estações da fragata: bytes iguais).
6. **Validador**: a área 0 passa pelas checagens de sala (alcance 07b de **cada** entrada para
   **cada** porta, nave alcançável e subível, estilo × tileset); linha do Tallon com "5 salas
   construídas"; `check_arrival` na ROM construída: estações 0 e `$12` da área 0 apontam para a
   Landing Site do manifest e o pouso para na altura da nave.

Crateria vanilla fica sem ligação: as portas das 5 salas só apontam umas para as outras (o build
monta as entradas de porta a partir de `LINKS`), e as duas estações da área 0 que o jogo usa
(0 e `$12`) apontam para a sala nova. As outras 17 estações da área 0 ficam vanilla, mas só são
usadas por save stations/elevadores da Crateria, que não se alcança mais.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 0 problemas, com a linha
   `tallon (tabela inteira, regiões ativas: A, 5 salas construídas): …` e "33 salas, 68 portas".
   (protege = alcance sem Space Jump das 5 salas, nave, chegada; falha_quando = degrau alto demais,
   estação/pouso fora da sala nova; não_prova = que fica bonito)
2. `python3 -I tools/build.py` sem erro; sha1 igual em dois builds.
3. `python3 -I tests/run_tests.py` → 22/22: os 21 de antes + `tallon_rota_mvp` (novo): fim da
   fragata → pouso na Landing Site nova (`lands_on_landing_site`), equipamento zerado por RAM
   (`$09A2/$09A4/$09A6/$09A8 = 0`: só Power Beam), andar para a esquerda (direção + tiro + pulo, sem
   teleporte) até o elevador, pausar e voltar ao jogo na área 0, andar de volta até a Landing Site;
   a sequência de salas lida a cada ciclo tem que ser exatamente
   LS → CC → TC → TA → TW → TA → TC → CC → LS, e o equipamento continua zerado no fim.
   (falha_quando = porta não passa, sala trocada, pausa trava; na ROM anterior falha já no pouso)
4. Mudança de expectativa dos testes existentes `fuga_ridley_nave_e_final`,
   `final_continue_na_landing_site` e `final_reset_no_meio_da_cena`: o ponteiro de sala do pouso
   passa de `$91F8` (Crateria vanilla) para o da Landing Site nova (lido do manifest). Motivo: é o
   objetivo desta spec (o fim da fragata chega ao Tallon).
5. Imagens de cada sala (sala inteira e emulador), olhadas uma a uma: cara de Crateria/Tallon, chuva
   na Landing Site e na Tallon Canyon, sem lixo na tela.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | 5 salas da área 0 nas checagens por área; `check_arrival` | +1 área, +1 checagem |
| run_tests.py (emulador) | `tallon_rota_mvp`; 3 testes do final com a sala nova | +1 (3 alterados) |
| imagem | 5 salas inteiras + 5 do emulador + chegada, continue, pausa | 13 |

## Riscos e reversão

- Mapa de pausa e minimapa da área 0 ainda são os da Crateria vanilla (título "CRATERIA", nossas
  salas aparecendo sobre a grade dela): aceito até a 07f. A pausa não trava (testado).
- Itens não são tirados ao chegar (a Samus chega com o equipamento da fragata; o teste zera por
  RAM): 07e.
- As constantes do pouso em `$A2` agora servem só à Landing Site nova; se um dia a Crateria vanilla
  voltar a ser usada, o pouso dela ficaria na altura errada.
- Reversão: `ACTIVE_REGIONS = frozenset()`, `ACTIVE_ROOMS = None`, tirar `TALLON` de `AREAS`, e
  desfazer `landing_height`/estação `$12` no build; ou reverter os arquivos e reconstruir.

## Fora de escopo

- Itens e perda de itens (07e/07h), inimigos (07i), mapa de pausa/minimapa "TALLON" e lista de
  SRAM da área 0 (07f), Gully e Alcove (salas da região A fora do caminho sem itens), elevador
  funcionando.

## Desvios (preenchido na implementação)

Verificação (22/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `tallon (tabela inteira, regiões ativas: A, 5 salas construídas):
  44 salas, 44 ligações, 251 telas, mapa 47/80 bytes de SRAM (por região: A 11 B 6 C 14 D 13 E 10)`
  e `33 salas, 68 portas, 0 problemas`.
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `5a7e49779509f25f2f502fbd8d79c2ed27f52cb7` nas duas.
- `python3 -I tests/run_tests.py` → **22/22** (2 min).
- Mutações: terraço da Tallon Canyon 4 blocos mais baixo (degrau de 8) → validate "porta 0 (R0)
  inalcançável a partir da entrada porta 1 (L1)"; estação `$12` de volta para `$91F8` e pouso em
  `$45F` (na memória) → `check_arrival` acusa os dois. Na ROM anterior o teste da rota falha no
  pouso (`$079B = 91F8`).
- Espaço usado: **`$8F` 231 bytes** (`$F029` → `$F110`; 5 cabeçalhos+estados, listas de portas e
  a lista do céu de 20 bytes): **sobram 3824 bytes** em `$8F`. `$83` 120 bytes (7 portas + 2
  portas falsas das estações), `$A1` 51 e `$B4` 17 (nave), expandido 2589 bytes (dados das salas).
  Média ~42 bytes de `$8F` por sala: as 39 salas que faltam do Tallon dão ~1,7 KB.
- Imagens: `specs/img/07g-sala-*.png` (sala inteira, tileset da ROM base),
  `specs/img/07g-emulador-*.png` (uma por sala, do teste da rota), `07g-tallon-chegada.png` (nave
  pousada, chuva), `07g-final-continue-landing-site.png`, `07g-tallon-pausa.png` (mapa vanilla).

Desvios e detalhes:

- **Estação `$12`**: o pedido falava só da estação 0; o fim da fragata carrega a `$12` (código C e
  bytes acima). As duas apontam para a sala nova; a 0 é onde a nave salva e onde o continue começa.
- **Altura do pouso**: a sala de 3 telas não comporta a altura fixa da nave vanilla; em vez de
  mudar o tamanho da tabela da 07d, as 3 constantes de `GunshipTop_3` são trocadas (só a cena de
  chegada as usa).
- **Câmera das estações**: `write_load_station` punha sempre a tela (0,0); com a Samus em y 528 o
  continue mostrava a nave sem a Samus (visto no emulador). Agora centraliza quando ela está longe
  do canto; os bytes das estações da fragata não mudam (as duas estão perto do canto).
- **Fundo**: o Parlor (`$B8B4`, valor provisório da 07d) parecia caverna; a superfície usa o céu da
  Landing Site vanilla (lista nova, as duas metades do BG2). Cavernas com `$B905`.
- O teste anda de verdade (não usa `go_through`): direção + tiro + pulo a cada ciclo; o verificador
  `check_tallon_route` lê a sala de cada ciclo, e copia uma foto do meio de cada sala para
  `build/tests/<sala>.png` (as fotos de 5 em 5 ciclos ficam em `build/tests/tallon_rota/`).
- A preocupação da 07b (regra de teto mais rígida que o jogo) não pesou: o desenho não tem vão sob
  teto baixo.
