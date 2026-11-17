# 19a — Espaço no `$8F` e no `$A1` para a Mines (mais faixas órfãs)

Estado: verificada (05/11/2026: validate 221/460/0 com as linhas "$8F recuperado: 11808 bytes em 9 faixas …" e "$A1 recuperado: 8139
bytes em 1 faixa …"; .ips sha1 `8e5d377133b668151f4a558ebbb192d1bff0f01a` igual em dois builds, igual ao de antes; os grupos A, B e C
rodados no fim da 19c, com a ROM igual)
Esforço estimado: 0,5–1 dia
Épico: [19 — Phazon Mines](19-phazon-mines.md) (decisão técnica 8; toolchain, ROM igual)

## Contexto

As 42 salas da Mines pedem ~2350 bytes no `$8F` (≈ 53 por sala e ~60 por arena) e ~600–800 no `$A1` (populações de inimigos). O
`$8F` tem 1 byte livre na faixa principal e 1282 na faixa das demos (18a); o `$A1` tem 1053 no fim do banco, e sobraria pouco para a
Impact Crater. Esta filha dá ao alocador mais quatro faixas órfãs do `$8F` e a primeira faixa recuperada do `$A1`, e o validador
prova que são só de salas órfãs. A ROM não muda: as faixas novas entram **no fim** (first fit em ordem: nada que já cabe muda de lugar).

## Estado atual (verificado)

- `tools/build.py` `RECLAIMED_8F` com 5 faixas (12a, 17a, 18a), 7613 bytes, 6330 usados; `FREE_A1 = $A1:EBD1–FFFF`, sem faixa
  recuperada (`Allocator(rom, *FREE_A1, "$A1")`), livre até `$A1:FBE3` (1053 bytes no fim).
- Faixas órfãs fora do `RECLAIMED_8F` (as do épico, conferidas de novo pelo validador): `$8F:C215–C8C6` (1714), `$8F:AD5C–B218` (1213),
  `$8F:A6A1–A97A` (730), `$8F:CAAE–CCC7` (538); nenhuma com cabeçalho comparado (`ROOM_PTR_COMPARED`). Duas têm dado de salas das
  demos: **cabeçalhos** das demos `$AF14`, `$AFFB`, `$B106` (na `AD5C–B218`) e `$CC6F` (na `CAAE–CCC7`), e listas de PLMs na `C215–C8C6`
  (274 bytes de demo nas faixas novas).
- `$A1:AD09–CCD3` (8139): populações só de salas órfãs; 553 bytes delas são de salas das demos. Nenhuma constante `0xA1xxxx` no C
  (`vendor/sm/src`): o `SpawnEnemy` (`$A0:9275`) lê do banco de quem chama (`$A6`, `$A9`), e o `$A1` só é lido pelo ponteiro de
  população do estado da sala.
- `validate.check_reclaimed` só olhava o `$8F`; `check_orphans` aceitava população nossa só a partir do `FREE_A1`.
- `check_ice_in_rom` e `check_ruins_in_rom` leem as 19 salas das demos na ROM construída (nenhuma pode usar os tilesets recoloridos).

## Mudança proposta

1. `tools/build.py`:
   - `RECLAIMED_8F` ganha as 4 faixas **no fim**, com o comentário dos donos;
   - `RECLAIMED_A1 = (($A1:AD09, $A1:CCD3),)` novo e `ours_a1(addr)` (como o `ours_8f`); o alocador do `$A1` passa a ter
     `reclaimed=RECLAIMED_A1` (usada só depois do `FREE_A1` cheio); o resumo do build imprime o uso ("$A1 recuperado (specs/19a): …").
2. `tools/validate.py`:
   - `check_reclaimed` para os dois bancos: faixa no banco (e acima de `$8000`), fora do espaço livre, sem cruzar outra; byte só de sala
     órfã na ROM base (de sala das demos só com as demos desligadas, `title.check_demos_off`); nenhum dado da `VANILLA_SHARED` (fundos
     no `$8F`, populações no `$A1`); na ROM construída, só estrutura de sala nossa escrita nas faixas; o cabeçalho comparado só no `$8F`.
     Novo no `$A1`: **população nossa dentro da faixa é uma que o build escreveu**, nunca a de uma sala vanilla órfã deixada como está
     (o `check_orphans` aceita qualquer ponteiro do espaço do build). Uma linha por banco.
   - `check_orphans`: população nossa no `FREE_A1` **ou** no `RECLAIMED_A1` (`build.ours_a1`).
   - `demo_rooms_kept(rom, base)` novo: as salas das demos com cabeçalho e estados ainda iguais aos da ROM base. `check_ice_in_rom` e
     `check_ruins_in_rom` leem só essas (uma sala das demos com o cabeçalho recuperado não é mais sala: nada a carrega, e o cabeçalho
     não se lê). A linha das ruínas diz quantas ficaram de fora, só quando há alguma.

## Critérios de aceite

1. validate "221 salas, 460 portas, 0 problemas" com as linhas "$8F recuperado: 11808 bytes em 9 faixas (…, $8FC215-$8FC8C6,
   $8FAD5C-$8FB218, $8FA6A1-$8FA97A, $8FCAAE-$8FCCC7), só de salas órfãs; usados pelas nossas salas: 6330 (… 0/1714 0/1213 0/730
   0/538); … 990 bytes de salas das demos, só com as demos desligadas (specs/18a, 19a)" e "$A1 recuperado: 8139 bytes em 1 faixa
   ($A1AD09-$A1CCD3), só de salas órfãs; usados pelas nossas salas: 0 (0/8139); 553 bytes de salas das demos, só com as demos
   desligadas; …"; as outras linhas iguais (a do Tallon e a das rodadas também). (protege = só dado de sala órfã reaproveitado nos dois
   bancos, demos desligadas enquanto houver dado delas nas faixas, nenhum cabeçalho comparado, nenhuma população vanilla usada como
   nossa; falha_quando = mutações abaixo; não_prova = leitor por ponteiro calculado em tempo de execução — nenhum nos bytes nem no C)
2. Mutações (`s19a/mutate_a.py`, em memória), cada uma pega.
3. Experimento positivo numa cópia (`s19a/proj_spill`: as faixas novas do `$8F` **primeiro** e o `FREE_A1` reduzido a 1 byte): o
   build põe estruturas e populações nelas, validate 0 problemas, o grupo A passa nessa ROM.
4. ROM igual na pasta real: sha1 `8e5d3771…f01a` em dois builds.

## Plano de testes

| Camada | O quê | Qtde |
|---|---|---|
| validate.py | `check_reclaimed` com o `$A1`; `check_orphans` com `ours_a1`; `demo_rooms_kept` | 1 generalizada + 1 nova |
| scratchpad | 17 mutações + 5 controles; build forçado às faixas novas + validate + grupo A | 23 |
| run_tests.py | nenhum novo (ROM igual) | 0 |

## Riscos e reversão

- **Religar as demos** quebraria as salas que usarem as faixas: o validador acusa (`check_reclaimed`, `check_orphans`).
- Save vanilla de SRAM (spec 11, B7): como na 12a/17a/18a.
- Reverter: tirar as 4 faixas, o `RECLAIMED_A1`, `ours_a1`, o `reclaimed=` do alocador e as partes novas do `check_reclaimed`, do
  `check_orphans` e o `demo_rooms_kept`.

## Fora de escopo

- As outras faixas órfãs do `$A1` (19 224 bytes em 9 faixas) e do `$83`/`$B4` (sobra espaço livre neles).
- Usar as faixas (as salas da Mines, 19e em diante).

## Desvios (preenchido na implementação)

- **As salas das demos com o cabeçalho recuperado** (achado do experimento positivo): na primeira tentativa a cópia com as faixas
  novas primeiro fazia o validador cair (`condição de estado desconhecida $0000 na sala $8FAF14`): `check_ruins_in_rom` (e
  `check_ice_in_rom`) liam o cabeçalho da sala das demos `$AF14`, já sobrescrito pelas nossas salas. Na 18a a faixa das demos só tinha
  listas de PLMs e scrolls, nenhum cabeçalho; as faixas novas têm 4. Correção: `demo_rooms_kept` (lê só as salas das demos com
  cabeçalho e estados intactos; recuperar o cabeçalho só vale com as demos desligadas, o `check_reclaimed` prova). Com a ROM real nada
  muda (as 19 continuam lidas).
- **Checagem a mais no `$A1`**: população nossa na faixa = uma que o build escreveu (bytes diferentes da ROM base num começo de
  população vanilla órfã é o que ela recusa). É o "população de sala vanilla na faixa" do épico: sem ela, um estado nosso apontando
  para uma população órfã intacta dentro da faixa passaria.
- **O scratchpad da sessão foi apagado três vezes** durante o trabalho (outro processo do Claude Code limpando a pasta da sessão; as
  três vezes logo depois de copiar o projeto **com a pasta `.claude/`** para o experimento). Copiar sem a `.claude/` resolveu. As saídas
  da pesquisa do épico (`s19/`) se perderam com isso; a 19c gera de novo o que precisa (`research/prime_mines_locks.json`).
- Mutações (`s19a/mutate_a.out`), todas pegas: A1 demos religadas com só as faixas novas do `$8F` (274 bytes de demo); A2 demos
  religadas, a faixa do `$A1` (553 bytes); A4 faixa do `$A1` cruzando o `FREE_A1`; A5 um byte além (`$A1:CCD4`, a população vazia da
  `VANILLA_SHARED`); A6 um byte antes (`$A1:AD08`); A7 em outro banco (`$A2`); A8 abaixo de `$8000`; A9 faixas do `$A1` sobrepostas;
  A10 faixa com a população vazia da `VANILLA_SHARED`; A11 byte escrito na faixa do `$A1` sem ser de sala nossa; A12 a Hangar
  apontando para a população órfã `$A1:AD09` intacta; A13 a Hangar apontando para uma população vanilla fora da faixa (`$A1:8000`,
  `check_orphans`); A15 faixa nova do `$8F` com o cabeçalho comparado `$CEFB`; A16 um byte além (`$8F:C8C7`); A17 faixa nova cruzando
  a da 17a; A18 byte escrito na faixa nova do `$8F`; A19 o cabeçalho da demo `$AF14` apagado: 18 das 19 salas das demos lidas.
  Controles limpos: A0 sem mutação (`check_reclaimed` e `check_orphans`), A3 demos religadas sem faixa com dado de demo (o
  `check_orphans` é quem acusa), A14 a população da Hangar movida de verdade para `$A1:AD09` (os dois limpos).
- **Experimento positivo** (`s19a/proj_spill`, sem `research/prime_fs`): `$8F:C215–C8C6` 1713/1714, `AD5C–B218` 1213/1213,
  `A6A1–A97A` 730/730, `CAAE–CCC7` 538/538 usados (o resto na `D4EF–DD57`, 2136); `$A1:AD09–CCD3` 4114/8139 (todas as populações);
  validate "221 salas, 460 portas, 0 problemas" (só as linhas de órfãs, das faixas e das ruínas, "mais 4 das demos com o cabeçalho
  recuperado", diferentes); **grupo A 34/34** nessa ROM.
- Verificação (05/11/2026, pasta real): `python3 -I tools/build.py` duas vezes → sha1 `8e5d377133b668151f4a558ebbb192d1bff0f01a` nas
  duas (igual ao de antes); `python3 -I tools/validate.py` → "221 salas, 460 portas, 0 problemas", só a linha "$8F recuperado" mudou e a
  "$A1 recuperado" é nova (diff com a saída de antes; a do Tallon e a das rodadas iguais). Os grupos A, B e C rodaram uma vez no fim da
  19c (a ROM não mudou nas três filhas): ver a 19c.
