# 22 — Trilhas sonoras do Prime (proposta)

Estado: **aprovada pelo usuário (11/11/2026), nenhuma filha começou**. Épico novo: só começa com um "pode seguir"
do usuário.
Esforço estimado: **a definir** pela prova de conceito (filha 22a). Não há número aqui porque o custo depende de medições que ainda
não fizemos.
Relacionado: [21 — Artes do Prime](21-artes-prime.md) (outra proposta, separada).

## Contexto

Pedido do usuário (11/11/2026): o jogo deve ficar o mais fiel possível ao Prime, também nas trilhas sonoras.

Hoje (verificado no projeto):
- As músicas das salas são as do **Super Metroid**: os conjuntos de música são escolhidos por sala (ex.: `$1B/$05` no Chozo,
  `$0F/$05` na Brinstar provisória). Nenhuma faixa do Prime está no jogo.
- O áudio do **Prime está extraído**: 119 arquivos `.dsp` em `research/prime_fs/files/Audio/` (ex.: `int_`, `ice_`, `gen_`, `rui_`,
  `min_`, `pir_`, `cra_`, `lav_`) e o pacote `research/prime_fs/files/AudioGrp.pak`. **Ainda não lemos esses arquivos nem
  convertemos nenhum.** O formato `.dsp` é o de áudio do GameCube/Wii (a confirmar no levantamento).
- O **motor de som do SNES** (o driver SPC700, usado pelo SM) toca músicas como sequências de notas que usam **instrumentos** (amostras
  de som em formato BRR) guardados na memória de áudio (ARAM, 64 KB no total, com o driver e os efeitos já ocupando parte dela).

## Limites (fatos do SNES, não opinião)

- A **ARAM tem 64 KB**. O driver de som e as amostras de efeito (tiros, passos, portas) do SM já ocupam parte dela. Cada faixa do Prime
  usa amostras próprias; é o limite principal do projeto.
- As amostras do Prime estão em outro formato (`.dsp`, ADPCM) e precisam virar **BRR** (o formato do SNES) com a taxa de amostragem certa.
- As sequências do Prime (notas, instrumentos, tempo) precisam ser convertidas para o formato de sequência do motor do SM.

## Escopo e riscos

1. **Trocar as músicas do SM pelas do Prime, por área.** O mais fiel e o mais caro. Cada área do Prime tem sua trilha; no SNES, cada
   faixa precisa caber no que sobra de ARAM **junto** com as amostras de efeito do SM, que não podem ser perdidas (o tiro e a porta
   precisam continuar soando).
2. **Só trilhas de chefe e de área, sem mexer nos efeitos.** Menos ganho, menos risco de quebrar o som do jogo.
3. **Faixas inteiras ou só trechos.** Trechos curtos cabem com mais facilidade; faixas inteiras ficam mais fiéis.

**Risco principal:** o espaço na ARAM. Se uma faixa do Prime não couber sem tirar um efeito do SM, a troca não pode ser feita como está e
precisa de outra solução (um conjunto de amostras menor, ou aceitar menos fidelidade). A prova de conceito mede isso antes de qualquer
decisão em escala.

## Decisões do usuário (abertas)

1. **Escopo:** (1) todas as áreas com a trilha do Prime, (2) só chefes e áreas escolhidas, ou (3) só os trechos de chefe?
2. **Efeitos do SM:** pode haver perda de algum som de efeito do SM se o espaço apertar, ou os efeitos do SM são intocáveis?
3. **Direitos:** a música do Prime é de propriedade da Nintendo/Retro Studios (compositores incluídos). Usar as faixas numa ROM hack é
   uma decisão sua; eu não avalio isso.

## Filhas propostas (sujeitas a aprovação)

| Filha | O quê | Verificação |
|---|---|---|
| 22a | **Prova de conceito**: ler um `.dsp` do Prime, convertê-lo para BRR, medir o tamanho em ARAM e tocar uma amostra no emulador | o som sai no emulador; o tamanho em ARAM medido e comparado com o que sobra |
| 22b | Converter a sequência de uma faixa de área para o motor do SM e tocar a faixa inteira numa sala de teste | a faixa toca do começo ao fim no emulador, sem perder o efeito de tiro |
| 22c | Levantamento de todas as faixas: tamanho em ARAM de cada uma, o que cabe, o que não cabe | tabela com números medidos; sem mudança na ROM |
| 22d | Trilhas de área (escolha da decisão 1), uma filha por grupo de áreas | cada área toca a sua trilha no emulador |
| 22e | Trilhas de chefe (incluindo a do Metroid Prime, no épico 20h) | a luta toca a trilha do chefe no emulador |

Estimativa de dias: **a definir na 22a**: a prova de conceito é a medida que decide tudo.

## Critérios de aceite (proposta)

- Cada faixa usada cabe na ARAM junto com os efeitos do SM, e o validador confere o espaço.
- Build duas vezes com o mesmo sha1; testes de todos os grupos passam.
- Efeitos do SM (tiro, porta, passo) continuam soando nas salas com trilha nova (decisão 2 define se pode haver exceção).

## Fora de escopo

- Efeitos sonoros novos (fora do pedido; só entrariam se a decisão 2 pedir).
- Arte (proposta 21).
