# 21 — Artes do Prime: chefes e Samus, o mais fiel possível (proposta)

Estado: **aprovada pelo usuário (11/11/2026); em andamento: 21a verificada parcialmente (12/11/2026); 21b em andamento (12/11/2026, `specs/21b-efeitos-de-poder.md`, ainda sem mudança na ROM)**. A 21a é só leitura
(`specs/21a-levantamento-arte.md`); as medições de tiles da Samus e dos chefes ficaram pendentes.
Esforço estimado: **a definir** no levantamento (filha 21a). Não há número aqui porque ainda não medimos o custo de cada arte.
Relacionado: [22 — Trilhas sonoras do Prime](22-trilhas-prime.md) (outra proposta, separada).

## Contexto

Pedido do usuário (11/11/2026): o jogo deve ficar o mais fiel possível ao Prime, também no visual dos chefes e da Samus.

Hoje (verificado no projeto):
- A **Samus, as suits (Varia, Gravity) e os poderes** são os gráficos originais do Super Metroid. Nenhum foi redesenhado no
  estilo do Prime.
- Os **chefes e inimigos novos** (Metroid Prime, Omega Pirate, Phazon Elite, Parasite Queen) são **cópias de sprites que já existem
  no SM**, recoloridas. Ex.: o ninja dourado `$F593` do épico 19; a regra "cópia de chefe existente com vida e ataques próprios"
  (19k, 20a).
- O Prime é um jogo 3D. Seus modelos e texturas foram extraídos para `research/prime_fs/` e `research/prime_textures/` (esta última só
  tem as pastas de Parasite Queen e Ridley), e o script `tools/dump_prime_textures.py` lê texturas. **Não existe hoje um pipeline que
  converta modelo 3D do Prime em pixel art de SNES.**

## Limites do SNES (fatos, não opinião)

- Cada sprite usa uma paleta de **16 cores** (com a cor 0 transparente). Um chefe grande usa várias paletas.
- A VRAM de sprites e o OAM (número de sprites por linha) são pequenos: um chefe do tamanho do Prime na tela ocupa muitos tiles e
  pode exigir truques (sprites por partes, animação em quadros).
- Cada quadro de animação é um conjunto de tiles novos: mais animação = mais espaço na ROM (a ROM tem espaço, medido nas filhas 20a/20b,
  mas o espaço de sprite é outro: a medir).

## Escopo (opções para o usuário escolher)

1. **Chefes no visual do Prime:** redesenhar em pixel art os chefes que aparecem no jogo (Metroid Prime e os chefes novos), com as
   proporções e cores do Prime, dentro dos limites do SNES.
2. **Samus com as suits do Prime:** Power Suit, Varia, Gravity e Phazon Suit em pixel art nova (o Prime tem Phazon Suit; o SM não).
   Isso mexe em todas as animações da Samus (andar, pular, atirar, morrer): é o trabalho mais caro desta lista.
3. **Efeitos de poder** (Power Beam, Charge, Wave, Ice, Plasma): só os tiros e explosões, sem mexer no corpo da Samus. É o item de
   menor custo e o de maior ganho visual por esforço.
4. **Inimigos comuns no visual do Prime:** fora do escopo proposto; fica para outra decisão, pois são muitos.

Sugestão de ordem (se o usuário aprovar tudo): 3 → 1 → 2. Efeitos e chefes são menores e testáveis antes da Samus.

## Decisões do usuário

Respondidas em 12/11/2026:

1. **Quem desenha:** a arte é feita por mim, por código (não à mão por um artista). Consequência: a qualidade depende de
   conversão automática a partir dos modelos e texturas do Prime, e pode ficar abaixo da pixel art do SM. Cada arte será
   conferida no emulador antes de ser aceita.
2. **Direitos:** não se aplicam. O jogo é para uso pessoal (só o dono joga). Não há mais essa decisão.

Ainda abertas:

3. **Escopo:** quais das opções 1 a 3 entram? (A opção 4 fica de fora sem decisão contrária.) Recomendação: a 3 (efeitos de
   poder) primeiro, depois a 1 (chefes), depois a 2 (Samus).
4. **Fidelidade vs. limite do SNES:** quando o Prime não cabe em 16 cores ou no tamanho de sprite, o que vale: manter a cor do
   Prime (com paleta extra por chefe) ou aproximar? Recomendação: aproximar onde faltar espaço e registrar cada caso como desvio.

## Filhas propostas (sujeitas a aprovação)

| Filha | O quê | Verificação |
|---|---|---|
| 21a | Levantamento (só leitura): sprites atuais da Samus e dos chefes, tamanho e tiles de cada um, limites de VRAM/OAM, e quais modelos e texturas do Prime estão extraídos (o que falta extrair) | relatório com números medidos; sem mudança na ROM |
| 21b | Efeitos de poder (tiros e explosões) no visual do Prime, numa ROM de teste | emulador: cada tiro aparece e tem a cor certa |
| 21c | Metroid Prime como chefe final no visual do Prime: paleta e sprite (depende da decisão 2) | a luta no emulador com o sprite novo |
| 21d | Phazon Suit e demais suits da Samus (depende da decisão 1) | Samus animada em cada suit, no emulador |

Estimativa de dias: **a definir na 21a**.

## Critérios de aceite (proposta)

- Cada arte nova cabe no SNES (paleta, VRAM, OAM) e o validador confere isso.
- Build duas vezes com o mesmo sha1; testes de todos os grupos passam.
- A arte aparece no emulador em cada situação em que é usada (tiro, luta, morte, animação).

## Riscos

- **Qualidade artística:** o maior risco. Pixel art automática pode ficar pior que a do SM; por isso a decisão 2.
- **Espaço de sprite:** pode não caber sem recuperar espaço (como o épico 19a fez com as populações de sala). A 21a mede.
- **Direitos:** decisão 4.

## Fora de escopo

- Música (está na proposta 22).
- Inimigos comuns (opção 4).
- Mudança de Samus fora das suits e poderes (como a física de pulo).
