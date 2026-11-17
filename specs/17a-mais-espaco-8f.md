# 17a — Mais espaço no `$8F` (as duas faixas órfãs da Norfair)

Estado: verificada (01/11/2026: validate 136/284/0 com a linha "$8F recuperado: 3817 bytes em 4 faixas …"; .ips sha1
`0f5cc669fc89800b65e43169c9cd5a816fde0653` igual em dois builds; manifest igual; 83/83 testes)
Esforço estimado: 0,5 dia
Épico: [17 — Magmoor Caverns](17-magmoor-caverns.md) (toolchain; não muda a ROM)

## Contexto

Cabeçalhos de sala, estados e listas de porta e de PLMs têm de morar no banco `$8F`. O espaço livre (`FREE_8F`) acabou na Chozo; a
faixa recuperada da 12a (`$8F:D4EF–DDBD`, 2254 bytes) tem 1681 usados, sobram 573. As 29 salas da Magmoor pedem ~1500 (≈ 52 por sala,
medido na Chozo). O épico achou duas faixas do `$8F` que só salas órfãs da Norfair usam, sem dado das demos e sem cabeçalho que o código
compara: `$8F:8ED6–9193` (702) e `$8F:A9E5–AD41` (861), 1563 bytes. Esta filha as dá ao alocador, com a mesma prova da 12a. A ROM não
muda: as faixas entram **depois** das da 12a e o alocador é first fit em ordem, então nada do que já cabe muda de lugar.

## Estado atual (verificado)

- `tools/build.py:143` `RECLAIMED_8F = ((0x8FD4EF, 0x8FDD57), (0x8FDD59, 0x8FDDBD))`; `Allocator.put`: primeiro o `FREE_8F`, depois a
  primeira faixa recuperada onde couber, em ordem. `validate.check_reclaimed` prova, nos bytes da ROM base, que todo byte das faixas é
  estrutura de sala órfã (nem demo, nem `VANILLA_SHARED`, nem código ou dado sem dono) e que nenhuma faixa contém um cabeçalho que o
  código compara (`room_ptr_compares`: `LDA $079B; CMP #…`).
- Donos (roteiro `s17a/probe.py`, `roomgraph.structures` das 262 salas vanilla na ROM base):
  - `$8F:8ED6–9193`: 702 de 702 bytes são **listas de PLMs** de 15 salas da área 2 (`$B40A $B457 $B482 $B4AD $B4E5 $B510 $B55A $B585
    $B5D5 $B62B $B656 $B698 $B6C1 $B6EE $B741`); nenhum cabeçalho começa ali. (`$B457` é sala de terremoto comparada pelo código, mas o
    que se compara é o endereço do cabeçalho, `$8F:B457`, fora da faixa; a lista de PLMs dela só é lida pela própria sala.)
  - `$8F:A9E5–AD41`: 861 de 861 bytes são de 18 salas da área 2 (`$A9E5` … `$AD1B`): cabeçalhos e estados 702, listas de porta 76,
    scroll 62, scroll de PLM 21. Os 18 cabeçalhos começam dentro; nenhum é comparado.
  - Iguais à ROM base na construída (nada escrito ali hoje). Os bytes vizinhos (`$8F:8ED4–8ED5` = `0000`, o fim da lista anterior; `$8F:AD42`
    em diante) ficam fora.
- Quem lê o cabeçalho pelo endereço, nos bytes da ROM base (roteiro do probe): só 4 `LDA $079B` existem, todos seguidos de `CMP #`
  (`$88:81CC`, `$88:8200`, `$88:82CA`, `$91:D143`; os 8 cabeçalhos da 12a); os 4 `LDX $079B` só leem o cabeçalho (`$80:C4A6`, `$81:AD34`,
  `$82:86E6`, `$82:DE74`: `LDA $0001,X`…); nenhum `LDY $079B`, nenhum `CMP/CPX/CPY $079B`, nenhuma forma longa (`$7E:079B`). Imediatos
  iguais aos 18 cabeçalhos nos bancos de código: só `$98:BBE1` (gráfico) e `$8F:B58C` (dentro do cabeçalho `$B585`): dados, não código.
- No C (`vendor/sm/src`), constantes nas faixas: só `sm_81.c:22` `kRoomState_aa82_aa8f = RomFixedPtr(0x8faa8f)` (um estado da sala `$AA82`),
  **definido e nunca usado** (nenhuma outra linha cita o nome); nenhum `8F AA 8F` nos bytes da ROM, e nos bancos `$80–$82` nenhum operando
  `$AA8F–$AAA8` lido com o banco `$8F` (os que existem são tabelas do próprio `$81`, `kExpandingSquareVels` etc.). As outras constantes do C
  na faixa são de outros bancos (`$86`, RAM `$7E:9000`…).
- `$8F:8000–8ED3` (3796, dados das demos) **não** entra (regra do usuário; as demos podem voltar um dia).

## Mudança proposta

1. `tools/build.py`: `RECLAIMED_8F` ganha, **no fim** (para a ROM não mudar), `(0x8F8ED6, 0x8F9193)` e `(0x8FA9E5, 0x8FAD41)`, com o
   comentário dos donos acima.
2. `tools/validate.py`:
   - `room_ptr_compares`: além de `LDA $079B; CMP #`, também `LDX $079B; CPX #` e `LDY $079B; CPY #` (hoje nenhum; a prova "nenhum
     cabeçalho comparado nas faixas" passa a cobrir os três registradores). E **`check_reclaimed`** passa a acusar qualquer comparação
     direta do `$079B` com memória (`CMP/CPX/CPY $079B`, absoluta ou longa): o alvo não seria um imediato que a varredura vê.
   - `check_reclaimed` (sem mudar a lógica das provas da 12a) imprime o uso por faixa.
3. Nada nas salas: nenhuma estrutura vai para as faixas novas enquanto as da 12a tiverem lugar.

## Critérios de aceite

1. validate "136 salas, 284 portas, 0 problemas", com a linha "$8F recuperado: 3817 bytes em 4 faixas (…), só de salas órfãs; usados
   pelas nossas salas: 1681 (…); o código compara a sala com 8 cabeçalhos, nenhum nosso nem nas faixas". (protege = só dado de sala órfã
   reaproveitado, nenhum cabeçalho comparado, nada das demos; falha_quando = mutações abaixo; não_prova = código que leia o pedaço por
   ponteiro calculado em tempo de execução que não passe por cabeçalho/porta — nenhum achado nos bytes nem no C)
2. Mutações no scratchpad (`s17a/mutate_a.py`, em memória), cada uma pega: faixa com o chunk das demos `$8F:8000–8ED3`; faixa que cruza a da
   12a; faixa com um cabeçalho comparado (`$8F:B457`); faixa um byte além (`$8F:9194`); faixa sobre código; faixa cruzando o `FREE_8F`;
   `LDA $079B; CMP #$AA82` e `LDX $079B; CPX #$A9E5` plantados na ROM; `CMP $079B` plantado no código vanilla; byte escrito na faixa nova
   sem ser de sala nossa; cabeçalho nosso num endereço comparado.
3. Experimento positivo numa cópia do projeto (`s17a/proj_spill`, `FREE_8F` encurtado): o build põe estruturas nas faixas novas,
   validate 0 problemas (linhas do Tallon e das rodadas iguais) e os testes do emulador passam nessa ROM.
4. ROM igual na pasta real: sha1 `0f5cc669…0653` em dois builds; linhas do Tallon e das rodadas iguais; 83/83.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` com 4 faixas; `room_ptr_compares` com LDX/LDY; comparação com memória acusada | +1 sub-checagem |
| scratchpad | ~9 mutações; build forçado às faixas novas + validate + testes | ~10 |
| run_tests.py | nenhum novo (ROM igual) | 0 |

## Riscos e reversão

- **Save de SRAM vanilla** (spec 11, B7): um `.srm` do SM que carregue uma sala da Norfair cairia em dado sobrescrito (já documentado na 12a).
- **Demos**: se voltarem, `check_reclaimed` reavalia (as faixas novas não têm dado de demo).
- O estado `$8F:AA8F` do C não é usado; se algum dia aparecer um leitor (outro patch), a faixa `$8F:A9E5–AD41` deve ser partida em volta
  dele, como a 12a fez com `$DD58`.
- Reverter: tirar as duas faixas de `RECLAIMED_8F` e as linhas novas de `room_ptr_compares`/`check_reclaimed`.

## Fora de escopo

- `$8F:8000–8ED3`, `$8F:91F8–A0FA` e as outras faixas com dado de demo ou cabeçalho comparado (Phendrana/Mines).
- `$83`, `$A1`, `$B4` (sobra espaço).

## Desvios (preenchido na implementação)

- **Comparação com memória só na ROM base**: a primeira versão varria a ROM construída e acusou `CMP $079B` em `$84:F50E` — a rotina das
  arenas (14b), nossa, que procura a sala atual na tabela de cabeçalhos **nossos**. A varredura de `CMP/CPX/CPY $079B` passou a olhar o
  código vanilla (ROM base), que é o que a regra protege; a de imediatos (`room_ptr_compares`) continua na construída, como na 12a.
- Nenhum `LDX/LDY $079B; CPX/CPY #` existe hoje: a extensão de `room_ptr_compares` não muda os 8 cabeçalhos.
- A linha do validador ganhou o uso por faixa (`1681/2153 0/101 0/702 0/861`).
- **Experimento positivo**: encurtar o `FREE_8F` não serve — o primeiro cabeçalho condicional que passa do fim (uma arena da 14b) para no
  `put_at` da 12a, como deve. Em vez disso, numa cópia (`s17a/proj_spill`, sem `research/prime_fs`), as faixas novas foram postas **antes**
  das da 12a: o build pôs nelas 861 + 702 bytes (3 cabeçalhos — `chozo_antechamber` em `$8F:A9E5`, `chozo_transport_tallon_east`,
  `chozo_transport_tallon_south` — e as listas de PLMs e de porta de ~110 salas do Tallon, da fragata e da Chozo) e 118 na da 12a; validate
  "136 salas, 284 portas, 0 problemas", linhas do Tallon e das rodadas iguais, "$8F recuperado: … usados 1681 (861/861 702/702 118/2153
  0/101)"; `python3 -I tests/run_tests.py` nessa cópia → **83/83**. (Antes, com a faixa da 12a cortada a 208 bytes: 702/702 e 672/861 nas
  novas, só listas; validate igualmente limpo.)
- Mutações (`s17a/mutate_a.out`): A1–A11 todas pegas; sem mutação, limpo.
- O estado `$8F:AA8F` que o C nomeia (`kRoomState_aa82_aa8f`) fica dentro da faixa: nunca usado (Estado atual); registrado em Riscos.
- Verificação (01/11/2026, pasta real): `python3 -I tools/build.py` duas vezes → sha1 `0f5cc669fc89800b65e43169c9cd5a816fde0653` nas duas
  (igual ao de antes), `build/manifest.json` byte a byte igual; `python3 -I tools/validate.py` → "136 salas, 284 portas, 0 problemas", só a
  linha "$8F recuperado" mudou; `python3 -I tests/run_tests.py` → **83/83**.
