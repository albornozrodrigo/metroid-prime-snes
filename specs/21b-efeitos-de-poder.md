# 21b — Efeitos de poder no visual do Prime (tiros e explosões)

Estado: **em andamento (12/11/2026). A ROM do jogo não muda; existe uma ROM de teste (`build.py --teste-21b`, pasta `build/teste-21b/`) com as cores do Prime nas paletas dos feixes. Conferência no emulador: pendente.** Filha do épico 21 (`specs/21-artes-prime.md`), primeira da
ordem aprovada pelo usuário (3 → 1 → 2): efeitos de poder, depois chefes, depois Samus.
Decisões do usuário que valem aqui: a arte é feita por código (não à mão); direitos não se aplicam (uso pessoal).

## Objetivo

Cada tiro e explosão aparece com o visual do Prime (forma e cor de cada feixe: Power, Charge, Wave, Ice, Plasma), numa ROM de
teste. A Samus, as suits e os chefes não mudam nesta filha.

## Fatos medidos até agora

- **Tiros do SM na ROM:** a tabela de tiles dos feixes fica em `$90:C3B1` (12 entradas, uma por combinação de feixes), e as
  paletas em `$90:C3C9`. Os tiles apontam para `$90:F200–$90:FA00`. (Lido direto do `base/sm_fix.sfc`; função
  `UpdateBeamTilesAndPalette` em `vendor/sm/src/sm_90.c`, linha 2425.)
- **Texturas do Prime dos tiros:** `research/prime_fs/files/SamusGun.pak` tem 456 recursos de textura e
  `SamGunFx.pak` tem 455. A biblioteca de leitura (`retro_data_structures` 0.44.1) foi instalada só no ambiente de rascunho
  (`scratchpad/s21venv`), não no projeto.
- **Nomes dos feixes achados** (conjuntos de animação `ANCS` nos pacotes): Power, Wave, Ice, Plasma, Phazon, Holo (no
  `SamusGun.pak`). **Achado:** todos os feixes apontam para o **mesmo modelo** (`19AE626C`, 59 texturas, a arma da Samus),
  e o "Holo" é um modelo de 2 texturas. Ou seja, o tiro em si **não** é esse modelo.
- Hipótese (a confirmar): o tiro e a explosão são **partículas** (`PART`, 317 recursos no `SamGunFx.pak`), não modelos. Próximo
  passo: achar qual `PART` é de cada feixe e qual textura ele usa.
- **Texturas de partícula do `SamGunFx.pak`** (57 TXTR, folha de contato em `scratchpad/fx_sheet.png`): são efeitos genéricos,
  em sua maioria **brilhos e anéis em tons de cinza** (que podem ser tingidos por código, uma cor por feixe), mais raios,
  chamas, gelo, fogo e uma bola magenta. Ainda não sei qual é o tiro de cada feixe: o personagem do feixe não lista as
  partículas (`particle_resource_data` vazio). Falta ler os `PART` (317) para ligar cada um a um feixe.
- **Cadeia dos efeitos de tiro (decodificada, 12/11/2026):** `DGRP` (grupo) → `WPSC`/`CRSC` (conjunto) → `PART` (partícula)
  → `TXTR` (textura). Os recursos `PART`, `DGRP` e `TXTR` vêm comprimidos (4 bytes de tamanho + zlib, exceto `PART` que começa
  com `GPSM`); ler sem descomprimir dá falso "sem textura". Resultado: **5 grupos**, um por feixe (provável), com as texturas:
  - `4DFA1079` (4 texturas): `51E53870` (estrelas), `6DE7CF4F` (linhas azuis), `750763B1` (orbes azuis), `E224FF03` → **candidato a Wave ou Ice**.
  - `C888B149` (7 texturas): `25CAF202`, `29782CA6`, `89E739A0`, `D1C18E03` (fogo laranja), `E224FF03`, `EC89B813`, `FEB6DBF9`
    (brilhos laranja) → **candidato a Power** (laranja).
  - `24DB85F3` (5 texturas): `29782CA6`, `79B5BD15`, `B8ACF65E`, `D1C18E03`, `E224FF03`.
  - `928D1777` (2): `1FB2AA92` (barra branca), `D1C18E03`.
  - `E2E00FDA` (1): `1FB2AA92`.
  **Busca da ligação (12/11/2026), sem resultado para os feixes:** os IDs dos 31 grupos (`DGRP`, `WPSC`, `CRSC`) foram procurados
  nos `Metroid1`–`Metroid8`/`metroid5` (já descomprimidos) e no `main.dol`. Só apareceram referências de cenário (`MREA`,
  `MLVL`, `CMDL` do mundo, em `Metroid3` e `metroid5`), nenhuma do `SamusGun` nem do executável. A ligação dos tiros deve
  estar em outro formato (a confirmar; hipótese: ID escrito de outro jeito, ou montado pelo código). Script: `scratchpad/find_link.py`.
  **Ainda não confirmado** qual grupo é de qual feixe: os nomes dos personagens não apontam para os grupos (o que procurei nos
  bytes do `SamusGun.pak` não bateu). Falta achar a ligação (provavelmente nos eventos `EVNT`/`ANIM` ou no script do jogo).
- **Cores medidas nas partículas (12/11/2026, `scratchpad/part_colors.py`, saída em `scratchpad/part_colours.json`):** a cor de
  cada partícula é a constante `LCLR` (RGBA, 0–1) e a textura é a `TEXR`. Resultado por grupo, só as cores constantes:
  - `928D1777` e `C888B149` (dois grupos): **laranja-amarelo** (1.0, 0.62–0.85, 0.0–0.54) → candidatos a **Power** (normal) e
    **Charge** (carregado).
  - `4DFA1079`: **roxo** (0.67, 0.0, 0.50) → candidato a **Wave**.
  - `24DB85F3`: **azul-claro** (0.16–0.33, 0.30–0.67, 1.0) → candidato a **Ice**.
  - `E2E00FDA`: **azul** (0.20–0.39, 0.20–0.39, 1.0) → candidato a Ice carregado ou Plasma (não resolvido).
  - **Plasma e Phazon** não têm grupo com cor clara: ainda não resolvido.
  Como as partículas usam cor constante, estas cores são as do Prime, não palpite. A ligação grupo → feixe continua sendo
  por cor (não confirmada no jogo).
- **Paletas dos tiros no SM hoje** (medidas na `base/sm_fix.sfc`, por combinação de feixes 0–11): Power `#f87830`, Wave
  `#f800f8` (magenta), Ice `#00b0f8` (azul), Spazer `#f8f800` (amarelo), Plasma/verde `#00f870`.
- Texturas de Wave, Ice e Plasma exportadas para conferência visual em `scratchpad/beams/` (84 PNG, da arma da Samus, não do tiro).

## Passos

1. Achar, por nome do modelo (CMDL) ou por tamanho, as texturas dos feixes e das explosões nos dois pacotes. Registrar a lista.
2. Ler cada textura (tamanho e cores) e medir quantas cores e tiles cada feixe precisa no SNES (16 cores por paleta, 8 paletas
   de sprite; tiles de 8×8 e 16×16).
3. Desenhar os tiles por código a partir das texturas, com quantização para a paleta do feixe.
4. Gravar numa ROM de teste (sem mexer na ROM do jogo) e conferir no emulador: cada tiro aparece, com a cor certa.

## Pendências e riscos

- A identificação das texturas (passo 1) é a parte que mais pode atrasar: os nomes não estão nas texturas.
- Qualidade: a conversão automática pode ficar pior que a pixel art do SM. Cada feixe será conferido no emulador.
- A ROM do jogo só muda depois da aprovação do resultado no emulador.

## Critérios de aceite (proposta)

- Cada feixe tem o seu visual do Prime, medido e conferido no emulador (tiro e explosão).
- Duas builds com o mesmo sha1; testes de todos os grupos passam.
- O que não couber (cor ou tiles) é dito no relatório, não escondido.

## ROM de teste (12/11/2026)

- Comando: `python3 -I tools/build.py --teste-21b` → `build/teste-21b/metroid_prime_snes.sfc`. A ROM do jogo (`build/metroid_prime_snes.ips`, sha1 `2f13e756…1423`) continua igual.
- Mudança: só as paletas dos feixes, em `$90:C3E1` (Power), `$90:C461` (Wave) e `$90:C401` (Ice). Código em `tools/beam21b.py`. (Correção de 17/11/2026: o Wave estava em `$C421`, que é a paleta do **Charge** (combinação 1) e do Wave+Charge (combinação 5). A tabela de ponteiros do SM dá o Wave (combinação 4) em `$90:C461`; por isso o `$C421` deixou de ser mexido. Build de teste: sha1 `d85d5b97…`, 35 bytes em `$C3E1`, `$C401` e `$C461`; a ROM do jogo segue `2f13e756…1423`.)
- Cores usadas (valor médio medido no Prime): Power `#ffb233`, Wave `#aa0080`, Ice `#4099ff`. Só os índices 2 a 7 mudam (35 bytes no total); o degradê de claro para escuro vem do brilho original de cada cor.
- Antes → depois (ver faixa `scratchpad/beam21b_swatch.png`): Power `#f87830` → laranja do Prime; Wave `#f800f8` → roxo do Prime; Ice `#00b0f8` → azul-claro do Prime.
- **Desvio:** o Ice `$90:C401` é compartilhado por quase todas as combinações de feixes. Ao mudar, muda o azul de todas elas, não só do Ice puro.
- **Não coberto:** Plasma e Phazon (sem grupo de cor identificado) e Charge (o segundo grupo laranja não foi ligado a um feixe).
- **Pendente:** conferir no emulador (`tools/snesrun`) que o tiro aparece com essas cores. Até lá, nada disso vai para a ROM do jogo. Ver o débito abaixo.

## Débito técnico (validar depois)

Decisão do usuário em 17/11/2026: a conferência visual no headless fica para depois; o desenvolvimento segue.

- **Medição de cor no headless não confirmada.** As cores de tiro medidas antes (`f76b00`, `732100`, `290029`) são **inválidas**: vieram da paleta de objeto 4 (Samus e efeitos do cano), não do tiro. Nenhuma comparação de cor de tiro feita até aqui vale.
- **Pixels do tiro não localizados.** O tiro na OAM (sprite com tile `0x30`, atributo `0xEC`, paleta 6) não tem pixels da paleta 6 na caixa dele, no quadro medido. Causa não encontrada: tamanho do sprite (bit da tabela alta), deslocamento da caixa, ou tiles não carregados na VRAM.
- **Paleta 6 recebe a cor nova na RAM.** Lido de `$7EC1C0`: azul na base, laranja na ROM de teste (após escrever `$C3E1`). Mas não se viu isso sair na tela.
- **Pausa/despausa no roteiro** deixa `game_state` preso em `0F`; a troca de sala no roteiro não tinha porta alcançável.
- **O que validar depois:** (1) equipar Power, Wave e Ice na ROM de teste, atirar e ver a cor na tela (no emulador do usuário é o caminho mais rápido); (2) só então decidir se a cor entra na ROM do jogo, com aprovação.

Pendências não rodadas nesta rodada: testes de grupo A, B, C e D (última rodada conhecida: A 34, B 64, C 22, D a confirmar).
