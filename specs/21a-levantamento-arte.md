# 21a — Levantamento da arte do Prime (só leitura)

Estado: **verificada parcialmente (12/11/2026)**. Só leitura: a ROM não muda. Filha do épico 21 (`specs/21-artes-prime.md`).
Três números (Samus no VRAM e no OAM, e o tamanho dos chefes em tiles) **ainda não foram medidos**; ficam como pendência
explícita, no fim. ROM conferida: duas builds dão sha1 `2f13e756…1423`, igual ao da 20j.

## O que foi pedido

Medir: sprites atuais da Samus e dos chefes (tamanho e tiles), limites de VRAM e OAM, e quais modelos e texturas do Prime estão
extraídos (o que falta extrair).

## Medido

### Texturas do Prime extraídas

Medido com Pillow em `research/prime_textures/` (27 PNG: 19 do Ridley, 8 da Parasite Queen):

| Pasta | Arquivos | Tamanhos | Cores distintas por textura |
|---|---|---|---|
| `ridley/` | 19 | 32×32 a 256×256 | 1 a 4 007 |
| `parasite_queen/` | 8 | 128×128 a 256×256 | 1 156 a 7 474 |

- Total de cores distintas, somando textura por textura: 47 970. Não é a conta de uma paleta única: cada textura tem as
  suas cores.
- Limite do SNES (fato de hardware): cada paleta de sprite tem **16 cores** (uma é a transparente), e há **8 paletas de sprite**.
  Ou seja: uma textura do Prime com 7 474 cores não cabe numa paleta. Qualquer chefe novo precisa de quantização (pior
  fidelidade) ou de várias paletas, como já se viu no 19k e no 20h.
- Ridley e Parasite Queen são as únicas pastas de texturas que existem. Não há textura da Samus, dos chefes novos nem das suits.

### Nomes de modelos nos pacotes do Prime

Contagem de ocorrência do nome em `research/prime_fs/files/*.pak` (busca de texto, não é leitura de modelo):

| Nome | Onde aparece | Situação |
|---|---|---|
| Samus | 11 pacotes | aparece; modelo não lido |
| Flaahgra | `Metroid2.pak` | aparece; é o chefe da 23e (decisão de Flaahgra em aberto) |
| Metroid Prime | `Metroid7.pak` | aparece; modelo não lido |
| Thardus | 6 pacotes | aparece (o Thardus do jogo já é o Bomb Torizo recolorido) |
| Omega | 4 pacotes | aparece (Omega Pirate) |
| Ridley | 5 pacotes | aparece; texturas já extraídas |
| Phazon Elite, Meta Ridley | nenhum | não encontrado pelo nome |

**Atenção:** achar o nome não prova que o modelo está lá em forma usável. Confirmar exige ler o pacote com a biblioteca de
dados do Prime.

### Ferramentas que existem

- `tools/dump_prime_textures.py` lê texturas de um modelo (CMDL) pela biblioteca `retro_data_structures`.
- **Essa biblioteca não está instalada** neste ambiente (`import` falha). O script não roda até ela ser instalada num ambiente de rascunho.
- Não existe pipeline que converta modelo 3D do Prime em pixel art de SNES (já era a premissa da spec 21).

### Limites de sprite do SNES que o projeto já mediu ou verificou

- VRAM de sprites para inimigos: de `$7000` a `$7FFF` = **$2000 bytes (8 KB)** (`research/sm_room_format.md`, seção 13). O
  Ridley de Ceres sozinho ocupa os $2000 inteiros, e os gráficos do cronômetro de fuga ocupam `$7E00`/`$7F00`.
- Sprites por tela e OAM: não medido aqui. (Limite de hardware: 128 sprites no total e 32 por linha; confirmar na 21b.)

## Não medido (pendência da 21a)

1. **Samus**: quantos tiles ocupa cada pose e a VRAM dela. Está no código C do SM (`vendor/sm/src/sm_9b.c` e `sm_90.c`), mas a
   leitura por tile ainda não foi feita. Sem isso não sabemos se a Samus com suit nova cabe.
2. **Chefes do SM** usados como base (Torizo, Dessgeega, Ninja etc.): tiles e VRAM de cada um. Mesma situação.
3. **Modelos do Prime** (Samus, Metroid Prime, Flaahgra, Thardus, Omega): não lidos. Precisa instalar `retro_data_structures`.

## Achados que mudam o plano da 21

- A regra "uma paleta por chefe" (19k, 20h) já é o caminho do projeto. A quantização de texturas grandes (até 7 474 cores)
  mostra que a fidelidade de cor vai ser parcial em qualquer chefe novo. Isso confirma a decisão 3 da spec 21.
- Os efeitos de poder (opção 3, 21b) são o item menor e o que menos depende das medições pendentes: tiro e explosão cabem em
  poucos tiles. Pode ser a primeira coisa a fazer depois da 21a.
- A arte do Metroid Prime (21c) depende da medição de tiles do Torizo, que é a base do chefe final hoje (`20h`).

## Decisões

Atualizadas em 12/11/2026 (ver `specs/21-artes-prime.md`): a arte é feita por código, e os direitos não se aplicam (uso
pessoal). Ainda abertas: escopo (ordem 3 → 1 → 2 recomendada) e fidelidade quando faltar espaço de cor.
