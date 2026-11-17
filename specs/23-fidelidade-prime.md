# 23 — Fidelidade ao Prime: visores, scan, HUD, atmosfera, chefes e inimigos (épico)

Estado: **aberto (11/11/2026), proposta, nenhuma filha começou.** Cada filha só começa com um "pode seguir" do usuário. Este épico
reúne o que falta para o jogo ficar o mais fiel possível ao Metroid Prime, além das artes (épico 21) e das trilhas (épico 22), que
continuam em épicos próprios.
Esforço estimado: **a definir** no levantamento (filha 23a). Sem número aqui: cada item tem custo diferente, e medi-lo é o primeiro passo.

## Contexto

Pedido do usuário (11/11/2026): o jogo deve ficar o mais fiel possível ao Metroid Prime. Hoje o projeto recria a estrutura do Prime
(áreas, salas, travas, chefes) sobre o Super Metroid: a mecânica de visores, o scan e o HUD ainda são os do SM.

## Itens do escopo

Cada item abaixo tem o que existe hoje no projeto (verificado no HANDOFF e nos specs) e o que falta.

1. **Visores do Prime (Combat, Scan, Thermal, X-Ray).** Hoje: Thermal e X-Ray existem como itens do SM (portas e travas), sem a troca
   de visor do Prime nem a tela do visor. Falta: o sistema de troca de visor e o que cada visor mostra.
2. **Scan e logbook.** Hoje: não existe. No Prime, escanear objetos revela textos de lore dos Chozo e dos piratas, e marca o logbook.
   Falta: pontos de scan, o texto e a interface. Limite: o espaço de texto no SNES (a medir).
3. **HUD do Prime** (energia, mísseis, radar, visor). Hoje: HUD do SM. Falta: o HUD do Prime. Depende da arte do épico 21.
4. **Chefes que ainda faltam.** Hoje: os chefes já planejados (Metroid Prime, filha 20h). **Não confirmado:** Flaahgra (Tallon) e
   Meta Ridley (Artifact Temple) não aparecem no HANDOFF. Primeiro passo: conferir no projeto se estão no jogo.
5. **Atmosfera.** Névoa e iluminação do Prime (luzes de área, névoa). Hoje: o fundo e as cores do SM. Limite: o SNES tem poucos
   recursos para isso (HDMA, matemática de cor); a fidelidade será parcial. A medir numa ROM de teste.
6. **Inimigos comuns no visual do Prime.** Hoje: sprites do SM recoloridos, com parte feita por área (Magmoor e Mines). Falta: o
   visual do Prime para os inimigos. Depende da arte do épico 21.

## Relação com outros épicos

- **21 (Artes do Prime):** os itens 3 e 6 e a parte visual do 1 dependem dela. Aprovado (11/11/2026).
- **22 (Trilhas sonoras):** independente. Aprovado (11/11/2026).
- **20 (Impact Crater):** o item 4 (Metroid Prime) já está na 20h; o item 5 se aplica também à cratera.

## Decisões do usuário (abertas)

1. **Ordem:** começar pelos visores (item 1), que mudam mais o jogo, ou pelo scan e logbook (item 2)? Proposta: visores primeiro.
2. **Idioma dos textos do scan e do logbook:** os textos do Prime são em inglês. Mantemos em inglês, traduzimos para português, ou
   escolhemos outro caminho? Isso muda o espaço usado e precisa ser decidido antes da filha 23c.
3. **Chefes (item 4):** se Flaahgra e Meta Ridley não estiverem no jogo, entram neste épico ou ficam de fora?
4. **Atmosfera (item 5):** aceitar fidelidade parcial, ou ficar só com as cores do Prime sem névoa?

## Filhas propostas (sujeitas a "pode seguir")

| Filha | O quê | Verificação |
|---|---|---|
| 23a | Levantamento (só leitura): o que o Prime faz em cada visor, quais pontos de scan existem em cada área, quanto texto cabe no SNES, quais chefes faltam, quais limites de HDMA/cor | relatório com números medidos; sem mudança na ROM |
| 23b | Visores do Prime: troca de visor (Combat, Scan, Thermal, X-Ray) e o que cada um mostra, numa ROM de teste | emulador: cada visor troca, mostra e volta; o Thermal e o X-Ray das portas continuam funcionando |
| 23c | Scan e logbook: pontos de scan, texto e a tela de scan (depende da decisão 2) | emulador: escanear um objeto mostra o texto e marca o logbook |
| 23d | HUD do Prime (depende do épico 21) | emulador: o HUD aparece com energia, mísseis e radar corretos |
| 23e | Chefes que faltarem, se confirmados (item 4; decisão 3) | a luta vencida de verdade no emulador |
| 23f | Atmosfera: névoa e luzes de área, se a 23a mostrar que cabe (decisão 4) | emulador: a área mostra a névoa e as luzes do Prime |
| 23g | Visual do Prime nos inimigos comuns (depende do épico 21) | emulador: cada inimigo aparece com o visual novo |

Estimativa de dias: **a definir na 23a**.

## Critérios de aceite (proposta)

- Cada item entregue aparece e funciona no emulador, em toda situação em que é usado.
- Build duas vezes com o mesmo sha1; testes de todos os grupos passam.
- O que não couber (ex.: texto por limite de espaço) é dito no relatório, não escondido.

## Riscos

- **Espaço no SNES** (texto do scan, HUD, sprites): pode não caber sem recuperar espaço. A 23a mede.
- **Dependência da arte (épico 21):** sem a arte, os itens 3 e 6 ficam parados.
- **Escopo:** são seis itens com custos diferentes; a ordem e os cortes são decisão do usuário.

## Fora de escopo

- Arte (épico 21) e trilhas (épico 22), que têm épicos próprios.
- Mudanças nas áreas, salas e travas que já estão verificadas, salvo o que a fidelidade exigir (cada uma anotada como desvio).
