# 18a — Espaço do `$8F` para Phendrana (a faixa das demos)

Estado: verificada (03/11/2026: validate 165/342/0 com a linha "$8F recuperado: 7613 bytes em 5 faixas …"; .ips sha1
`15d37c8ace02ff12e8c0907cd085febe3eca65cd` igual em dois builds; grupo A 34/34, grupo B 64/64)
Esforço estimado: 0,5 dia
Épico: [18 — Phendrana Drifts](18-phendrana-drifts.md) (decisão técnica 7; toolchain, ROM igual)

## Contexto

As 56 salas de Phendrana pedem ~3000 bytes no `$8F` (cabeçalhos, estados, listas de porta e de PLMs: ≈ 53 por sala), e as faixas
recuperadas (12a, 17a) têm 695 livres. A maior faixa órfã que sobra é `$8F:8000–8ED3` (3796 bytes), que a 17a deixou de fora porque
tem dado de salas das demos de atração. As demos estão **desligadas desde a spec 16** (decisão do usuário, provada nos bytes por
`title.check_demos_off`): nenhuma sala das demos carrega mais. Esta filha dá a faixa ao alocador e troca a regra "nada de demo" do
validador por "dado de demo só com as demos desligadas". A ROM não muda: a faixa entra **no fim** de `RECLAIMED_8F` (first fit em
ordem: nada que já cabe muda de lugar).

## Estado atual (verificado)

- `tools/build.py:155` `RECLAIMED_8F` com 4 faixas (12a, 17a), 3817 bytes, 3122 usados (`2152/2153 100/101 702/702 168/861`).
- Donos de `$8F:8000–8ED3` na ROM base (roteiro `s18a/probe.py`, `roomgraph.structures` das 262 salas vanilla): os **3796 bytes**
  são estrutura de **149 salas** das áreas 0–2 (scroll e listas de PLMs); **716** são de **17 salas das demos** (`DEMO_SCENES`), só
  delas; nenhum cabeçalho começa na faixa; nenhum dos 8 cabeçalhos comparados (`ROOM_PTR_COMPARED`, o menor é `$96BA`); nenhum fundo
  de `VANILLA_SHARED`; iguais à ROM base na construída (nada escrito ali hoje). `$8F:8ED4–8ED5` (`0000`, fim de outra lista) fica fora.
- No C (`vendor/sm/src`) nenhuma constante `0x8f8000–0x8f8ed3`.
- `validate.check_reclaimed` (`tools/validate.py:2463`) acusa todo byte recuperado que seja de sala das demos, mesmo com as demos
  desligadas; `title.check_demos_off` (`tools/frigate/title.py:318`) prova nos bytes que o título não começa demo e que só a rotina
  da demo grava o estado `$28`; hoje só o `check_orphans` a chama.

## Mudança proposta

1. `tools/build.py`: `RECLAIMED_8F` ganha `(0x8F8000, 0x8F8ED3)` **no fim**, com o comentário dos donos.
2. `tools/validate.py` `check_reclaimed`:
   - os bytes de sala das demos contam como órfãos **só se** `title.check_demos_off(rom)` (ROM construída) não acusa nada; com as demos
     religadas, cada byte recuperado de sala das demos é erro, com o motivo do `check_demos_off` na mensagem;
   - faixa com parte em `$8F:0000–7FFF` (não é ROM) = "fora do banco" (antes o validador caía lendo o byte);
   - a linha diz quantos bytes de sala das demos as faixas têm ("… 716 bytes de salas das demos, só com as demos desligadas").

## Critérios de aceite

1. validate "165 salas, 342 portas, 0 problemas" com a linha "$8F recuperado: 7613 bytes em 5 faixas (…, $8F8000-$8F8ED3), só de
   salas órfãs; usados pelas nossas salas: 3122 (2152/2153 100/101 702/702 168/861 0/3796); o código compara a sala com 8
   cabeçalhos, nenhum nosso nem nas faixas; 716 bytes de salas das demos, só com as demos desligadas (specs/18a)"; as outras linhas
   iguais (as do Tallon e das rodadas também). (protege = só dado de sala órfã reaproveitado, demos desligadas enquanto houver dado
   delas nas faixas, nenhum cabeçalho comparado; falha_quando = mutações abaixo; não_prova = leitor por ponteiro calculado em tempo de
   execução fora de cabeçalho/porta — nenhum nos bytes nem no C)
2. Mutações (`s18a/mutate_a.py`, em memória), cada uma pega.
3. Experimento positivo numa cópia (`s18a/proj_spill`, a faixa nova **primeiro**): o build põe estruturas nela, validate 0 problemas,
   os grupos A e B passam nessa ROM.
4. ROM igual na pasta real: sha1 `15d37c8a…65cd` em dois builds; A 34/34, B 64/64.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` com 5 faixas e as demos desligadas como condição | 1 generalizada |
| scratchpad | 10 mutações + controle; build forçado à faixa nova + validate + grupos A e B | 12 |
| run_tests.py | nenhum novo (ROM igual) | 0 |

## Riscos e reversão

- **Religar as demos** quebraria as salas que usarem a faixa: o validador acusa (`check_reclaimed` e `check_orphans`).
- Save vanilla de SRAM (spec 11, B7): como na 12a/17a.
- Reverter: tirar a faixa de `RECLAIMED_8F` e as linhas novas do `check_reclaimed`.

## Fora de escopo

- `$8F:C215–C8C6`, `$8F:AD5C–B218`, `$8F:A6A1–A97A` (ficam para a Mines).
- Usar a faixa (as salas de Phendrana, 18e em diante).

## Desvios (preenchido na implementação)

- **Faixa fora da metade de ROM** (`$8F:7FFF…`): a mutação A5 fazia o validador cair (`endereço LoROM inválido`) em vez de acusar;
  `check_reclaimed` passou a acusar "fora do banco" e parar antes de ler os bytes.
- A mutação "fundo vanilla compartilhado na faixa" não foi feita: não há fundo nenhum na faixa, e um ponteiro de fundo falso não é
  fundo (o `roomgraph.bg_size` recusa o dado, como deve).
- Mutações (`s18a/mutate_a.out`), todas pegas: A1 demos religadas (`$8B:9F2C` = `F0 02`); A2 a troca para a rotina da demo apagada; A3
  faixa cruzando a da 17a; A4 um byte além (`$8F:8ED4`); A5 um byte antes (`$8F:7FFF`); A6 faixa com o cabeçalho comparado `$8F:B457`;
  A7 faixa cruzando o `FREE_8F`; A8 byte escrito na faixa nova sem ser de sala nossa; A9 cabeçalho nosso num endereço comparado.
  Controle A10: demos religadas **sem** a faixa nova → `check_reclaimed` limpo (o `check_orphans` é quem acusa). Sem mutação: limpo.
- **Experimento positivo** (`s18a/proj_spill`, sem `research/prime_fs`, a faixa das demos primeiro): 3122 bytes nela (32 cabeçalhos:
  as 29 salas da Magmoor e 3 da Chozo; 704 dos bytes escritos são dos que eram de sala das demos), as outras faixas vazias; validate
  "165 salas, 342 portas, 0 problemas", só a linha do `$8F` diferente; **grupo A 34/34, grupo B 64/64** nessa ROM.
- Verificação (03/11/2026, pasta real): `python3 -I tools/build.py` duas vezes → sha1 `15d37c8ace02ff12e8c0907cd085febe3eca65cd` nas
  duas (igual ao de antes); `python3 -I tools/validate.py` → "165 salas, 342 portas, 0 problemas", só a linha "$8F recuperado" mudou
  (diff com uma cópia de antes da 18a); grupo A **34/34** (3:00), grupo B **64/64** (4:14).
