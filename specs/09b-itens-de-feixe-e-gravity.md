# 09b — Itens de feixe e Gravity Suit

Estado: verificada (23/10/2026: validate 72/148/0 com "alcançáveis agora: 15"; .ips sha1 `ba13be7f…235b` igual em dois builds; 46/46 testes)
Esforço estimado: 1 dia (tabela e validador 0,25 d; Gravity Suit no emulador 0,25 d; testes 0,25 d; verificação 0,25 d)
Épico: [09 — Itens de trava](09-itens-de-trava.md) (linha 09b; decisões 1, 3, 4 e 5)

## Contexto

Depois da 09a as 26 travas de gelo, onda e plasma são portas de feixe, mas nenhum feixe existe como item: só
os testes os dão por RAM. Esta filha põe no Tallon os quatro itens que abrem essas portas e o anteparo da
Vent C — Ice, Wave, Gravity Suit e Plasma — nos lugares decididos no épico, e faz o passeio do validador usar
os itens achados em vez das fases hipotéticas para eles.

## Estado atual (verificado)

Lido nesta filha na pasta real e na ROM base (`base/sm_fix.sfc`):

- Baseline: validate 72 salas / 148 portas / 0 problemas, linha do Tallon "alcançáveis agora: 15"; `.ips` sha1
  `3f6e03c080428f7a12a6bb069920ba587ca0f7e2`; 42/42 testes.
- `tools/tallon/items.py`: 13 linhas (bits `$A0–$AC`), `GRANTS` só de míssil/E-tank/Space Jump/X-Ray.
  Fases hoje (`FIRST_TIER`): 0 = 15 salas, 1 = Gully e Alcove, 3 = Overgrown, Frigate Access, Tunnel C,
  Chozo East, Vent C, 4 = as outras 13 de D e as 8 de E, 6 = Arbor. Itens alcançáveis na fase 0: 3
  (mísseis da Landing Site, Crash Site, Tunnel B).
- PLMs de item visível (cabeçalho lido em `$84`): Ice `$EEEF`, Wave `$EEFB`, Gravity `$EF0B`, Plasma `$EF13`
  (setup `$EE64` nos quatro), Morph `$EF23`, Bombas `$EEE7`, Power Bomb `$EEE3` (= `$EED7 + 4·n`,
  `research/sm_room_format.md` §5).
- Coleta dos feixes (listas `$84:E189/E213/E338`): `8BDD 02` (música) + `88B0 <bit> <msg>` =
  `PlmInstr_PickupBeamAndShowMessage` (`sm_84.c:434`; bytes em `$84:88B0` iguais ao C): `collected_beams` e
  `equipped_beams |= t`; depois `equipped &= ~((t<<1)&8)` e `&= ~((t>>1)&4)`: **só o Spazer (`$4`) e o Plasma
  (`$8`) se excluem**. Ice `$2`, Wave `$1`, Plasma `$8` nunca tiram outro feixe: na ordem do épico (Wave → Ice
  → Plasma) o equipado fica `$1 → $3 → $B`; as pré-instruções da 09a (`AND #$0F00|m / CMP #m`) abrem com
  qualquer combinação que tenha o bit. Não há Spazer no jogo.
- Gravity Suit (lista `$84:E2D6`): `8BDD 02`, `E29D` (zera a carga), `88F3 0020 1A` (`equipped_items |=
  $20`, mensagem `$1A`), `870B $91D5BA` = `GravitySuitPickup` (`sm_91.c:1320`): a cena do traje (luz no meio
  da tela, paleta nova). Ela **põe a Samus em `layer1 + (120, 136)`** (`$91:D64E`: `AD 11 09 18 69 78 00 8D F6
  0A 8D 10 0B AD 15 09 18 69 88 00 8D FA 0A 8D 14 0B`, 26 bytes), o meio da tela de uma sala vanilla de uma
  tela com chão na linha 10.
- **Experimento no emulador** (cópia da ROM construída em `scratchpad/s09b/`, `mkrom_grav.py`: o PLM da porta
  de gelo da Chozo East trocado por Gravity em (12, 25); `exp_grav2.py`): a Samus entra pela porta, desce os
  degraus, pega a suit andando; câmera `y = $109`; a cena a põe em (120, 401): **dentro da parede** (colunas
  0–10 sólidas nas linhas 22–25) e 6 px dentro do chão. A paleta da Gravity aparece certa, o jogo não trava,
  mas **ela fica presa na parede para sempre** (posição igual 1000 quadros depois, com direcionais e pulo).
  Num teste com a câmera em (0, 0) ela foi para (120, 136), em ar, e andou: o problema é o lugar fixo na tela.
  Nas três salas de transporte (1 tela de largura, chão na linha 26) o meio da tela com a câmera embaixo cai
  no chão: nenhum lugar no fundo delas serve à cena vanilla.
- Bits vanilla de item: 0–154 (`validate.vanilla_item_bits`); `$AD–$B3` = 173–179, livres. Os bits de item
  ficam em `$7ED870` (os de porta vermelha `$B0–$B2` são de outro vetor, `$7ED8B0`).
- RAM de equipamento: `$09A2` itens equipados, `$09A4` coletados, `$09A6` feixes equipados, `$09A8` coletados
  (`tallon_gully_alcove` já confere `$09A5` para o Space Jump; 09a põe feixes em `$09A6/$09A8`).

## Mudança proposta

### 1. Tabela (`tools/tallon/items.py`)

As 7 linhas de trava entram juntas (bits fixos `$A0 + linha`), na ordem do épico. `prime` = P# da sala (o item
não é um pickup do Tallon no Prime).

| # | Item | PLM | Bit | Sala | Lugar | Fase |
|---|------|-----|-----|------|-------|------|
| 13 | Ice Beam | `$EEEF` | `$AD` | Root Cave | (4, 9), na prateleira da porta da Arbor | 1 |
| 14 | Wave Beam | `$EEFB` | `$AE` | Transport to Magmoor East | (9, 25), no chão | 0 |
| 15 | Gravity Suit | `$EF0B` | `$AF` | Transport to Chozo Ruins East | (12, 25), no chão embaixo | 1 |
| 16 | Plasma Beam | `$EF13` | `$B0` | Transport to Chozo Ruins South | (6, 25), no chão | 1 |
| 17 | Morph Ball | `$EF23` | `$B1` | Transport to Chozo Ruins West | — (09d) | — |
| 18 | Bombas | `$EEE7` | `$B2` | Artifact Temple | — (09d) | — |
| 19 | Power Bomb | `$EEE3` | `$B3` | Transport to Phazon Mines East | — (09e) | — |

`KIND_NAME` com os 7; `GRANTS`: Ice → `ice`, Wave → `wave`, Gravity → `gravity`, Plasma → `plasma`, Bombas →
`bombs`, Power Bomb → `power_bomb`, Morph → nada (a bola entra no modelo na 09d).

Fases: o passeio (que já pega itens) agora pega os feixes e a suit. Na fase 1 (+ mísseis, Bombas
hipotéticos): Space Jump (Alcove) → gelo (Root Cave) → Overgrown, Tunnel C, Chozo East, Frigate Access, Vent C →
Gravity Suit → região D (o Wave já veio da fase 0) → região E → Plasma → Arbor. `FIRST_TIER`: as 27 salas das
fases 3, 4 e 6 vão para a **1**; itens da Overgrown, da região D e E e da Arbor para a 1. As fases 2–6 de `TIERS`
ficam sem sala (as rodadas da 09f tiram as fases). Alcançáveis agora: **15 → 15** salas (o Wave na fase 0 só abre
portas da região D, atrás do gelo); itens na fase 0: **3 → 4** (+ Wave).

### 2. Cena da Gravity Suit (`tools/tallon/items.py`, `gravity_patch`; build)

`$91:D64E` = `80 18` (BRA para `$91:D668`): a cena deixa a Samus onde ela está (pula os 26 bytes acima; o resto
— parar a Samus, pose de frente, som, luz, paleta — igual). O build confere os 26 bytes vanilla antes de
escrever (erro se diferirem). A luz continua no meio da tela (janela fixa `$7878`, `sm_88.c:2608`): se a Samus
não está no meio, ela fica fora do facho (só aparência). Espaço: 0 (troca no lugar). Varia não existe no jogo:
não muda.

### 3. Validador (`tools/validate.py`)

- `tallon_tiers` registra, para cada sala, **o que a Samus tem quando chega nela pela primeira vez** (fase e
  volta do laço de pegar itens); `check_tallon_water` anda sem a suit as salas inundadas a que ela chega antes
  da Gravity (só a Vent C), no lugar de usar `TIERS[FIRST_TIER]`.
- `check_tallon_tiers`: igual (lugar em ar, fora das portas, fase declarada), agora com os 4 itens.
- `check_tallon_items` (ROM): bits `$A0–$B3` únicos, dentro do vetor, fora dos vanilla; os PLMs de item de cada
  sala do Tallon iguais à tabela (os 7 tipos novos contam: um Morph/Bombas/PB na ROM sem lugar na tabela é erro);
  os 2 bytes da cena da Gravity Suit em `$91:D64E` e os 24 vanilla depois deles iguais aos que
  `items.gravity_patch` gera da ROM base.

### 4. Testes no emulador (`tests/run_tests.py`)

`pick_up` ganha o ponto de partida (`start`: colunas a partir do item, negativo = a oeste) e a duração da
caminhada, para pegar o item vindo do lado aberto. Preparação comum: nave → pouso. Em cada teste: pega o item
**andando para dentro dele**, confere o bit do item e o equipamento na RAM, e usa-o na trava.

- `tallon_onda`: teleporte de porta Tunnel B → Magmoor East (atrás da porta vermelha; documentado); pega o Wave
  vindo do oeste → bit `$AE`, `$09A6 = $09A8 = $0001`; estação 0 por RAM (a nave; o feixe continua), salva na
  nave, game over, continue: bit e `$09A6/$09A8` voltam (**persistência**); tela de equipamento; teleporte
  Reactor Core → Reactor Access (com a suit por RAM: a região D é inundada): a porta de onda (onde ela entrou)
  está fechada, 1 tiro com o Wave pego abre, ela passa.
- `tallon_gelo`: Space Jump por RAM (`$09A2/$09A4 |= $0200`, como o épico manda); teleporte Root Tunnel → Root
  Cave; posição e câmera por RAM na prateleira da Arbor, 2 blocos a oeste do gelo (subir a sala com Space Jump às
  cegas não é o que se testa); pega o gelo indo para leste por 24 quadros (para antes do míssil) → bit `$AD`, `$09A6 = $09A8 =
  $0002`; tela de equipamento no menu de pausa (foto: o feixe aparece); teleporte Crash Site → Frigate Access: a
  porta de gelo fechada atrás, abre com 1 tiro, passa para a Crash Site.
- `tallon_gravity`: sem a suit, teleporte Frigate Access → Vent C (pela porta oeste, a de antes do anteparo):
  anda para leste e pula 8 vezes contra o anteparo → fica na Vent C, encostada nele (x `$BB`); teleporte Tunnel
  C → Chozo East pela porta de gelo; desce andando os degraus para dentro da suit → bit `$AF`, `$09A2 = $09A4 =
  $0020`; depois da cena a Samus está onde pegou (x `$D0`, não `$78`, o meio da tela) e anda (x `$B5`, no chão);
  foto da paleta. A mesma sequência na Vent C, agora com a suit, passa por cima do anteparo e pela porta azul
  para a Vent B.
- `tallon_plasma`: Wave + Ice por RAM (o que ela já pegou antes na ordem do épico, `$09A6 = $09A8 = $0003`);
  teleporte Tunnel D → Chozo South pela porta de gelo; pega o Plasma vindo do oeste → bit `$B0`, `$09A6 = $09A8
  = $000B` (a combinação não tira nenhum); teleporte Arbor → Root Cave pela porta de plasma: fechada atrás da
  Samus, 1 tiro com `$B` abre, ela passa para a Arbor; de volta a Frigate Access pela porta de gelo: o mesmo tiro
  `$B` abre a de gelo (a combinação abre todas). Tela de equipamento com os 3 feixes (foto).

Fotos `build/tests/tallon_{onda,gelo,gravity,plasma}_*.png`, copiadas para `specs/img/09b-*.png`.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 72 salas, 148 portas, **0 problemas**, alcançáveis agora: 15.
   (protege = lugar/fase/bit dos itens, a suit decidindo a água pelo "primeiro a chegar", a ROM; falha_quando =
   mutações do 2; não_prova = a coleta no jogo, critério 4)
2. Mutações na memória (desfeitas; sem mutação 0 problemas), cada uma acusada: (a) gelo dentro da Overgrown
   (atrás da porta de gelo) → círculo: salas de gelo inalcançáveis na fase 1 → `check_tallon_tiers`; (b) Gravity
   na Vent B (atrás do anteparo) → região D/E na fase 4 → `check_tallon_tiers`; (c) `GRANTS` da Gravity vazio →
   idem; (d) bit do Wave igual ao do gelo → `check_tallon_items`; (e) `ITEM_BIT0` = `$90` (bits vanilla) →
   `check_tallon_items`; (f) Wave dentro do chão → "não está num bloco de ar"; (g) PLM do gelo na ROM trocado
   pelo do Wave → `check_tallon_items`; (h) byte da cena da Gravity de volta ao vanilla na ROM →
   `check_tallon_items`; (i) anteparo da Vent C sem a trava da Gravity (`GATES`) → `check_tallon_water` anda a
   Vent B e as seguintes sem a suit e acusa; (j) fase declarada do Plasma 0 → `check_tallon_tiers`.
3. `python3 -I tools/build.py` sem erro; sha1 do `.ips` igual em dois builds; espaço usado anotado (`$8F` das
   listas de PLM; `$91` 2 bytes no lugar).
4. `python3 -I tests/run_tests.py` → **46/46** (os 42 + `tallon_onda`, `tallon_gelo`, `tallon_gravity`,
   `tallon_plasma`). (falha_quando = item não pego andando, bit/equipamento errado, porta não abre com o feixe
   pego, a combinação tira um feixe, a suit não passa o anteparo ou passa sem ela, a Samus presa depois da cena,
   bit perdido no continue)
5. Fotos `specs/img/09b-*.png` olhadas: cada item no lugar, mensagem, a paleta da Gravity, a tela de
   equipamento com os feixes.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `tallon_tiers` com "primeiro a chegar"; `check_tallon_water` por ele; `check_tallon_items` com a cena da Gravity | 3 alteradas |
| mutação à mão | (a)–(j) | 10 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py | `tallon_onda`, `tallon_gelo`, `tallon_gravity`, `tallon_plasma` | +4 |
| imagem | itens, mensagens, Gravity, tela de equipamento | ~10 |

## Riscos e reversão

- A cena da Gravity com a Samus fora do facho de luz (só aparência). Pegar a suit no ar: a cena zera a
  velocidade; ela cai depois (vanilla).
- Rotas cegas antigas não passam por nenhum dos 4 lugares (Root Cave alta, transportes fora das rotas): nenhuma
  expectativa deve mudar.
- Com Wave + Ice + Plasma um tiro abre qualquer porta de feixe (aceito no épico).
- Reversão: tirar as 7 linhas e `gravity_patch` de `items.py`, voltar `FIRST_TIER`, `tallon_tiers`/
  `check_tallon_water`, reconstruir.

## Fora de escopo

- Lugar de Morph, Bombas (09d) e Power Bomb (09e); rodadas e `TIERS` fora (09f); a Varia; mostrar itens no mapa.
- Centrar a luz da cena da Gravity na Samus.

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → linha do Tallon igual (`… 44 salas construídas, alcançáveis agora: 15`) e
  `72 salas, 148 portas, 0 problemas`. **Alcançáveis agora: 15 → 15 salas; itens alcançáveis na fase 0: 3 → 4**
  (+ Wave). Fases: antes 0 = 15, 1 = 2, 3 = 5, 4 = 21, 6 = 1; depois 0 = 15, 1 = 29 (nenhuma nas fases 2–6).
  Itens: Wave fase 0; gelo, Gravity, Plasma fase 1; os 9 itens que estavam nas fases 3/4/6 agora 1.
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `ba13be7f51be21cb8131a4b20a25dc36b469235b` nas duas. Espaço: `$8F` livre a partir de `$8F:F8FD` (era
  `$8F:F8E3`: +26 bytes, 4 PLMs de item de 6 bytes + 1 lista nova, a da Magmoor East); `$91`: 2 bytes trocados no
  lugar (`$91:D64E`); `$84`, `$83`, nível: iguais.
- `python3 -I tests/run_tests.py` → **46/46** (os 42 + `tallon_onda`, `tallon_gelo`, `tallon_gravity`,
  `tallon_plasma`).
- Mutações do validador (na memória, `scratchpad/s09b/mut_validate.py`; sem mutação e depois de desfazer: 0
  problemas): (a) gelo na Overgrown → 38 ("fica alcançável na fase 3 (+ gelo), a tabela FIRST_TIER diz 1" nas
  salas de gelo e tudo depois); (b) Gravity na Vent B → 31 (região D/E e Arbor na fase 4); (c) `GRANTS` da Gravity
  vazio → 30 (idem); (d) bit do Wave = do gelo → "bits de item repetidos" + PLM da Magmoor East diferente; (e) bits
  a partir de `$90` → "bits de item [144…154] já usados por itens vanilla" + PLMs; (f) Wave no chão → "não está num
  bloco de ar" + "inalcançável" + região D na fase 4; (g) PLM do gelo trocado pelo do Wave na ROM →
  `check_tallon_items` (Root Cave); (h) cena da Gravity vanilla na ROM → "cena da Gravity Suit: $91D64E na ROM =
  ad11…"; (i) porta do anteparo sem a trava da Gravity → `check_tallon_water` (a Vent C sem a suit não alcança a
  porta da Vent B; 8 lugares sem volta no poço); (j) Plasma declarado na fase 0 → "fica alcançável na fase 1 …,
  declarado 0".
- Mutação de teste (cópia da ROM sem o patch da cena, `scratchpad/s09b/mut_nograv.sfc`): `tallon_gravity` falha —
  depois da cena a Samus fica em x `$78` (dentro da parede) e não anda.
- Combinação de feixes: `tallon_plasma` mede Wave + Ice (`$3`) + Plasma pego = `$000B` equipado e coletado, e um
  tiro de `$B` abre a porta de plasma e a de gelo; `tallon_onda` abre a de onda com o Wave pego; a tela de
  equipamento do menu de pausa mostra ICE/WAVE/PLASMA (o espaço do Spazer fica vazio).
- Imagens olhadas (`specs/img/09b-*.png`): cada item no lugar (o gelo ao lado do míssil na prateleira, diante da
  porta laranja; Wave e Plasma no chão; a suit na plataforma do elevador), as 4 mensagens, a Samus com a paleta da
  Gravity no lugar em que pegou, a tela de equipamento (Wave; Ice/Wave/Plasma), as portas abertas, a Vent C
  encostada no anteparo e a Vent B.

Mudanças de expectativa dos testes existentes: nenhuma (nenhuma rota antiga passa pelos 4 lugares; a
`porta_de_plasma` entra na Root Cave pela porta da Arbor, ao lado do gelo, e não o pega).

Desvios e detalhes:

- **Cena da Gravity Suit corrigida** (não previsto no épico): a vanilla põe a Samus no meio da tela, onde as
  salas de uma tela da vanilla têm chão; na Chozo East isso é dentro da parede e do chão e ela fica presa para
  sempre (medido). `$91:D64E = 80 18` deixa a Samus onde pegou; o facho de luz continua no meio da tela (só
  aparência). A paleta da Gravity e o fim da cena funcionam na área 0.
- O lugar da Gravity ficou o do épico (12, 25); nenhum lugar no fundo das salas de transporte serviria à cena
  vanilla (meio da tela = chão com a câmera embaixo).
- `pick_up` ganhou `start`/`frames` (a suit e o gelo se pegam vindo do lado aberto / sem chegar ao míssil); os
  testes antigos usam os valores de antes (−3, 40).
- Teleporte de porta com a câmera fora de uma tela inteira (depois de andar na Vent C) desenhava o item 64 px
  fora do lugar (o `bg1_x_offset` da 07h): o `tallon_gravity` põe a câmera em x 0 antes do teleporte (um jogador
  sempre chega à porta com a câmera na tela dela). Fica anotado em HANDOFF.
- `check_tallon_water` chama o passeio de novo (validate de ~4,3 s para ~7 s).
- `TIERS` fica com as fases 2–6 sem sala; as rodadas (09f) as substituem. Morph, Bombas e Power Bomb: linhas na
  tabela (bits `$B1–$B3`) sem lugar; o `GRANTS` do Morph é vazio até a bola entrar no modelo (09d).
