# 10a — Teleporte de porta alinhado e o A do primeiro míssil

Estado: verificada (26/10/2026: validate 72/148/0; .ips sha1 `9bc37cab…3462` igual em dois builds e igual ao de antes; 50/50 testes)
Esforço estimado: 0,25 dia
Épico: [10 — Polimento do Tallon](10-polimento-tallon.md) (achados A1, A2, A3)

## Contexto

Três fragilidades dos testes que os agentes anteriores anotaram (HANDOFF, "Armadilhas"): a cadeia de `door_teleport` deixa o
deslocamento do BG1 fora de tela inteira (itens e tampas desenhados fora do bloco; os testes repõem valores medidos com
`whole_screen_bg1`), o teleporte para cima por porta de teto não troca de sala, e o A do `tallon_first_missile` chega antes de
a caixa de mensagem aceitar. Só ajudantes de teste: a ROM não muda.

## Estado atual (verificado)

- `door_teleport` (`tests/run_tests.py:627`, antes): põe a Samus diante da porta (posição duas vezes) e dispara a transição
  (`$099C = $E17D`, `$078D`, `$0998 = 9`). A câmera (`$0911/$0915`) fica onde estava. Medido (`scratchpad/s10/audit.py`, as 44
  salas): depois de uma porta de chão/teto o `$091F` sai com `$E1`/`$C4` no byte baixo (Gully → Canyon `$02E1`, Savestation →
  Reactor Access `$00E1`; andando `$0100`) e segue errado pela cadeia; a montagem das salas mostra o Morph, o Ice, o Wave, o E-tank
  da Hydro e a cabana do Life Grove em dobro (`specs/img/10-auditoria-teleporte-chozo-west-antes.png`: tampa da porta em dobro).
- Teleporte para cima (Artifact Temple → Temple Lobby): a Samus fica no próprio templo (09f, Desvios).
- `tallon_first_missile`: A 240 quadros depois do fim da caminhada até o lago. Fotos (`scratchpad/s10/m5_all.png`): a caixa
  MISSILE continua aberta 300 quadros depois desse A; um segundo A a fecha. Com o A 60, 120, 180 ou 240 quadros mais tarde a caixa
  fecha com ele (`m6_all.png`). Hoje quem a fecha é o próximo botão do andador (os testes seguintes) ou um segundo A
  (`chain_round_0`).

## Causa

A transição de porta calcula o deslocamento do BG1 a partir da câmera; andando até uma porta de chão a câmera está na última tela
da sala, embaixo (`$0915 = (altura − 1) · 256 + 31`, Savestation `$001F`), numa de teto em cima (`0`), numa lateral na tela da
porta. O teleporte começava com a câmera em outro lugar (a Savestation recém-carregada tem `$0915 = 0`: `$0100 − $1F = $00E1`).

## Mudança proposta

- `door_teleport` põe também a câmera na tela da porta: lateral x = 0 ou `(largura − 1) · 256`, y = `tela · 256` (no máximo o
  de baixo); teto `(tela · 256, 0)`; chão `(tela · 256, camera_bottom)`. Ajudante novo `camera_bottom(r)`.
- `tallon_first_missile`: o segundo `wait 120` vira `wait 180` (A 300 quadros depois da caminhada). `chain_round_0` não dá mais o
  segundo A (troca por espera, mesmo tempo).
- Os `whole_screen_bg1` e a volta à nave por RAM continuam (valores de tela inteira; mexer neles não é preciso).

## Critérios de aceite

1. Teste novo `teleporte_de_porta_alinhado`: da Landing Site, por teleporte, desce a porta de chão da Gully até a Chozo West
   (foto: o Morph uma vez só), sobe a porta de teto da Tallon Canyon para a Gully (a sala troca), desce a do Temple Lobby e sobe de
   volta; depois de cada teleporte lê `$091D/$091F` e todos são tela inteira (byte baixo 0; checagem `check_whole_screen_bg1`).
   (protege = alinhamento e subida; falha_quando = `door_teleport` sem a câmera: falha com `02E1`… (mutação); não_prova = o jogo
   andando, que já alinhava)
2. Todos os testes antigos passam sem mudar expectativa.
3. Build duas vezes: sha1 igual ao de antes.

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| run_tests.py | `teleporte_de_porta_alinhado` | +1 |
| mutação | `door_teleport` sem a câmera (cópia no scratchpad) | 1 |
| imagem | Chozo West com o Morph; Temple Lobby depois de subir; caixa do primeiro míssil fechada | 3 |

## Riscos e reversão

Os testes que encadeiam teleportes passam a chegar com outro deslocamento do BG1 (agora o certo); se algum dependesse do errado,
falharia: rodado, nenhum. Reversão: `tests/run_tests.py`.

## Fora de escopo

- Os andadores cegos (achado A10): ciclos medidos, nada muda nas salas deles.
- Tirar os `whole_screen_bg1` e as voltas por RAM que existem por causa do problema (funcionam; mudar não traz nada ao jogador).

## Desvios (preenchido na implementação)

Verificação (26/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas` (linha do Tallon igual).
- `python3 -I tools/build.py` duas vezes → sha1 `9bc37cab4865b96ea4be265812fad89d3e253462` nas duas (igual ao de antes: só testes).
- `python3 -I tests/run_tests.py` → **50/50** (os 49 + `teleporte_de_porta_alinhado`).
- Mutação (cópia `scratchpad/s10/proj_base`, `door_teleport` sem a câmera): `teleporte_de_porta_alinhado` **falha** com "deslocamento
  do BG1 fora de tela inteira: ['02E1', '02E1', …, '03C2', '02C2']".
- Antes de mexer na pasta real, a mesma mudança (câmera + A) rodou a bateria inteira numa cópia: 49/49.
- Fotos olhadas: `specs/img/10a-teleporte-chozo-west-morph.png` (um Morph só, na plataforma; antes, tampa e item em dobro:
  `10-auditoria-teleporte-chozo-west-antes.png`), `10a-teleporte-sobe-temple-lobby.png` (subiu do templo para o Lobby, de pé sobre a
  porta de chão), `10a-primeiro-missil-caixa-fechada.png` (a caixa fechada no fim do `tallon_first_missile`).

Mudanças de expectativa dos testes existentes: **nenhuma**. Ajudantes:
- `door_teleport`: põe a câmera na tela da porta (sem mudar o que ele espera ou devolve).
- `tallon_first_missile`: A 60 quadros mais tarde (agora fecha a caixa).
- `chain_round_0`: o segundo A saiu (a espera é a mesma: 322 quadros antes da foto `cadeia_0_missil_pego`).
