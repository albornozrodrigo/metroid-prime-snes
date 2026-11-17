# 20b — Espaço no `$8F` e no `$A1` para a Impact Crater (a checagem de folga)

Estado: verificada (10/11/2026: validate "263 salas, 546 portas, 0 problemas" com a linha nova "impact crater (specs/20b): $8F livre
2849 (principal 1, faixas recuperadas 2848) para ~1050; $A1 livre 8786 (principal 647, faixas recuperadas 8139) para ~200; 12 de 12
salas por construir"; .ips sha1 `f5b0f58b3cd6ef58d573403852b091a7446b0dac` igual em dois builds, igual ao de antes; grupo A 34/34)
Esforço estimado: 0,5 dia
Épico: [20 — Impact Crater](20-impact-crater.md) (toolchain, ROM igual)

## Contexto

A 20a mediu que o espaço dos dois bancos de dados de sala sobra para a Impact Crater (`specs/20a-levantamento-impact-crater.md`,
tabela de espaço): a cratera pede ~700–1050 bytes no `$8F` (cabeçalhos, estados, listas) e ~200 no `$A1` (populações). Esta filha
confirma esses números com o build atual e põe a conta no validador, para que uma sala nova de outra área, ou da própria cratera, que
coma a folga seja acusada antes de faltar espaço no meio do épico. Nenhuma faixa nova é recuperada: a medição mostra que não precisa.

## Estado atual (verificado)

- `tools/build.py`: `FREE_8F = $8F:E9AF–FFFF`, `RECLAIMED_8F` com 9 faixas (12a, 17a, 18a, 19a); `FREE_A1 = $A1:EBD1–FFFF`,
  `RECLAIMED_A1 = $A1:AD09–CCD3` (19a). Os alocadores são de ponteiro que só sobe (`Allocator.put`): o livre é a cauda de cada faixa.
- Resumo do build agora: "livre: $8F até $8FFFFF … $A1 até $A1FD79"; "$8F recuperado: … $8FC215-$8FC8C6 1350/1714, $8FAD5C-$8FB218
  0/1213, $8FA6A1-$8FA97A 0/730, $8FCAAE-$8FCCC7 0/538"; "$A1 recuperado: $A1AD09-$A1CCD3 0/8139".
- O validador já confere **onde** os dados ficam (`check_reclaimed`: só sala órfã, faixas fora do livre e sem cruzar; `check_banks`:
  os alocadores do nível e do fixo) e imprime o uso, mas **nenhuma checagem compara o que sobra com o que a próxima área pede**.

## Mudança feita

`tools/validate.py`:
- constantes `IMPACT_ROOMS = 12`, `IMPACT_NEED_8F = 1050`, `IMPACT_NEED_A1 = 200` (pontas de cima da 20a) e `IMPACT_KEY_PREFIX =
  "impact_"`;
- `ff_tail_free(rom, lo, hi)`: bytes `$FF` no fim da faixa livre principal; `bank_tail_free(lo, hi, used)`: bytes depois do último
  byte nosso numa faixa recuperada (os bytes nossos lidos das estruturas das salas, como no `check_reclaimed`);
- `check_impact_space(rom, manifest)`: soma o livre de cada banco e compara com o que pedem as salas da cratera ainda não construídas
  (a necessidade cai na proporção das salas `impact_*` já no manifest); imprime uma linha; chamada logo depois do `check_reclaimed`.

ROM igual: só o validador mudou.

## Critérios de aceite

1. validate "263 salas, 546 portas, 0 problemas" com a linha "impact crater (specs/20b)" e os números da 20a: `$8F` 2849, `$A1`
   8786. **Feito.**
2. Mutações pegas (abaixo). **Feito.**
3. ROM igual: sha1 `f5b0f58b…dac` em dois builds. **Feito.**
4. Grupo A passa (os outros grupos não rodaram: a ROM é a mesma byte a byte e só o validador mudou). **Feito: 34/34.**

## Mutações (`scratchpad/s20b/mutate.py`, em memória)

| Mutação | Resultado |
|---|---|
| controle (ROM e constantes como estão) | limpa |
| `$8F` pede 3000 | pega ("$8F livre 2849 bytes, as 12 salas por construir pedem ~3000") |
| `$A1` pede 9000 | pega ("$A1 livre 8786 …") |
| controle: `$A1` pede 8200 com a ROM intacta | limpa (8786 ≥ 8200) |
| a cauda livre do `FREE_A1` escrita (647 bytes), `$A1` pede 8200 | pega ("$A1 livre 8139 …") |
| 12 salas `impact_*` no manifest e `$8F` pede 99999 | limpa (nada mais a pedir) |

Uma primeira versão da mutação do `$A1` zerou também as populações nossas do `FREE_A1` e quebrou a leitura das salas (erro de
endereço, não um aviso): a mutação estava errada, não o validador; refeita só sobre a cauda livre.

## Riscos e reversão

- **A conta é uma estimativa** (as pontas de cima da 20a). Se uma filha da cratera usar mais por sala, a checagem acusa antes do fim
  do espaço; aí se recupera mais faixa órfã (há 19 224 bytes de `$A1` órfão em 9 faixas não usadas, `specs/19a`, e mais no `$8F`).
- `ff_tail_free` contaria a mais se o último dado escrito na faixa principal terminasse em `$FF`; hoje a faixa do `$8F` tem 1 byte
  livre e a do `$A1` 647, os mesmos do resumo do build.
- Reverter: tirar as constantes, as três funções e a chamada.

## Fora de escopo

- Recuperar faixas novas (não precisa).
- O grafo, o mapa e as travas da cratera (próxima filha, 20c).
