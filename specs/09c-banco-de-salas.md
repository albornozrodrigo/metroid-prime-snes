# 09c — Segurança do banco de dados de sala

Estado: verificada (23/10/2026: validate 72/148/0; .ips sha1 `11071b46…94bd` igual em dois builds; 46/46 testes; experimento de cruzamento 47/47)
Esforço estimado: 0,5–1 dia (pesquisa 0,1 d; alocadores e build 0,15 d; validador e mutações 0,2 d; teste de
cruzamento 0,15 d; verificação 0,15 d)
Épico: [09 — Itens de trava](09-itens-de-trava.md) (linha 09c; decisão 6, risco "Banco `$E0`")

## Contexto

As filhas 09d e 09e vão mudar o nível (dados de sala comprimidos) da Tallon Canyon e do Life Grove. Hoje o nível
das salas vive no banco `$E0` misturado com outras coisas, sobram 96 bytes antes da arte da Parasite Queen
(`$E1:8000`), e o nível nunca cruzou de banco neste projeto. Se crescer, a Queen e as estrelas do hangar mudam de
lugar sozinhas (nunca testado). Esta filha separa o que é fixo do que cresce e prova uma vez, no emulador, uma
sala cujo nível atravessa a divisa `$E0`/`$E1`.

## Estado atual (verificado)

Lido na ROM base, na ROM construída (sha1 do `.ips` `ba13be7f51be21cb8131a4b20a25dc36b469235b`) e no código:

- **Tamanho e cabeçalho**: `base/sm_fix.sfc` tem `0x300000` bytes (3 MB, bancos `$80–$DF`); cabeçalho em
  `$80:FFC0` = "Super Metroid", mapa `$30` (LoROM FastROM), tamanho `$80:FFD7` = `$0C` (2^12 KB = **4 MB** já
  declarados). O build expande para `0x400000` (`Rom.expand_to`, `tools/build.py:448`) e o cabeçalho não muda.
  LoROM mapeia `$80–$FF:8000–FFFF` = 128 × 32 KB = 4 MB: `$F0:8000` = arquivo `0x380000`. No LakeSnes
  (`vendor/LakeSnes/snes/cart.c:108`, `cart_readLorom`) `$F0–$FF:0000–7FFF` é SRAM e `$8000–$FFFF` é ROM
  (`(bank & 0x7f) << 15 | adr & 0x7fff`); no SNES a SRAM do LoROM fica só nas metades baixas, igual.
- **Uso da expansão** (cauda de `$FF` por banco na ROM construída): `$E0` 0x7FA0 bytes, `$E1` 0x31D1, `$E2–$FF`
  vazios (0x8000 bytes `$FF` cada). Ordem do build hoje (`LinearAllocator` a partir de `0x300000`): gráfico do
  "TALLON IV" (`ending.tallon_text`, em `$E0:8000`), os 72 níveis na ordem de `all_rooms()` com as estrelas do
  hangar (tiles + mapa, `put_in_bank`) logo depois do nível do hangar, as paletas recoloridas dos tilesets e por
  fim a arte da Parasite Queen (`$E1:8000`, 12754 bytes, `put_in_bank`). Só os 72 níveis somam 24119 bytes.
- **Descompressor cruza banco** (ROM, desmontado à mão): `DecompressToMem` `$80:B119` e `DecompressToVRAM`
  `$80:B271` leem cada byte de origem com `LDA $0000,X; INX; BNE +3; JSR $B266` (20 leituras de origem em
  `$80:B119–$80:B440`, as 20 com esse par), e `$80:B266` = `LDX #$8000; PHA; PHB; PLA; INC; PHA; PLB; PLA; RTS`
  (próximo banco, `X = $8000`). O C (`vendor/sm/src/sm_80.c:2480`, `DecompNextByte`) faz o mesmo. Sala vanilla
  `$8F:ADAD` (Norfair): nível `$C7:FF02`, 0x630 bytes, termina em `$C8:8531`. O nível só é lido por
  `DecompressToMem` (`sm_82.c:4211` e `:4392`, as duas leituras de `room_compr_level_data_ptr`). Os outros
  blobs comprimidos (gráficos do tileset = Queen, paleta, gráfico da cena de Ceres via `$80:B0FF`, chamado em
  `$8B:C6C8`) passam pelo mesmo descompressor. **Só as estrelas** vão por DMA (lista de fundo op 2,
  `space.library_bg`): DMA não cruza banco.

## Mudança proposta

### 1. Dois alocadores na expansão (`tools/build.py`)

| Alocador | Faixa | Conteúdo | Cruza banco? |
|----------|-------|----------|--------------|
| `level` | `$E0:8000–$EF:FFFF` (512 KB) | só os níveis das salas, na ordem de `all_rooms()` | sim (o descompressor cruza) |
| `fixed` | `$F0:8000–$FF:FFFF` (512 KB) | gráfico do TALLON IV, estrelas do hangar (tiles, mapa), paletas recoloridas, arte da Parasite Queen | não: cada blob num banco só |

Uma classe `ExpandedAllocator(rom, start, end, name, cross_banks)` substitui o `LinearAllocator`: escreve só em
bytes `$FF`, para com erro no fim da faixa, guarda (rótulo, endereço, tamanho) de cada blob e diz quantos bytes
sobram. Assim crescer o nível nunca move o que está no `fixed`. `ending.tallon_text` passa a receber a função
`put`; `queen_art.apply` recebe a do `fixed`. O manifest (`build/manifest.json`) ganha, por sala, `level`
(endereço, tamanho) e uma entrada `banks` com as faixas, o próximo livre, os livres e os blobs. O build imprime os
bytes livres de cada alocador e as salas cujo nível cruza banco.

### 2. Modo de teste do cruzamento

`python3 -I tools/build.py --cruzar-banco SALA` enche o começo do `level` com `$FF` (pulando bytes, nada
escrito) até o nível de SALA começar a meio caminho antes da próxima divisa de banco: o nível atravessa a divisa
e tudo depois dele fica no banco seguinte. Grava em `build/` como o build normal (o manifest anota o
enchimento); para voltar, build normal. Experimento desta filha: SALA = `hangar` (o primeiro nível; carregado
em todo teste, pela load station e pela porta da Air Lock).

### 3. Validador (`tools/validate.py`, `check_banks`, ROM construída)

1. Faixas: `level` e `fixed` não se sobrepõem, estão dentro da ROM construída (4 MB) e do tamanho do cabeçalho,
   e fora da ROM base (3 MB).
2. Cada sala: todo estado aponta (`+0`, 24 bits) para o endereço do manifest, dentro do `level`, e os bytes lá
   são exatamente `RoomDef.level().compressed()` (o descompressor consome esse tamanho).
3. Fixos, seguidos pelos ponteiros da ROM: paleta de cada tileset recolorido (= `recolor` da paleta vanilla),
   gráficos do tileset 4 (Queen; o conteúdo já é do `check_queen_art`), gráfico da cena de Ceres (conteúdo no
   `ending.check_rom`), e os 2 DMAs da lista de fundo do hangar (bytes = `space.star_tiles()`/`star_tilemap()`),
   todos dentro do `fixed`, nenhum cruzando banco.
4. Nenhum blob (níveis + fixos) se sobrepõe a outro.
5. Imprime os livres de cada alocador e avisa quais salas têm o nível cruzando banco.

### 4. Teste no emulador (`tests/run_tests.py`)

`nivel_cruza_banco_<sala>`, gerado do manifest para cada sala cujo nível cruza banco (nenhum num build normal):
chega na sala (fragata: novo jogo + rota andando; Tallon: pouso + teleporte de porta), confere a sala e o estado
de jogo, lê o nível descomprimido da WRAM (camada 1 em `$7F:0002`, BTS em `$7F:6402`) e compara com o da
ferramenta (diferenças só nos blocos dos PLMs da sala: tampas de porta, itens, estações), confere que a Samus
fica parada no chão (y igual em duas leituras com 60 quadros) e tira uma foto.

## Critérios de aceite

1. `python3 -I tools/validate.py` → 72 salas, 148 portas, 0 problemas, com a linha dos bancos (livres; nenhuma
   sala cruzando banco no build normal).
2. Mutações na memória (`scratchpad/s09c/mut_banks.py`, cada uma acusada por `check_banks`; sem mutação 0):
   (a) ponteiro de nível de uma sala = o de outra; (b) faixa `fixed` sobreposta à `level`; (c) nível de uma sala
   copiado por cima do fim de outra (sobreposição); (d) estrelas movidas para cruzar banco; (e) paleta movida
   para dentro do `level`; (f) ponteiro de nível para bytes livres.
3. `python3 -I tools/build.py` duas vezes com o mesmo sha1 (muda em relação a `ba13be7f…`: os blobs mudaram de
   lugar); livres impressos.
4. `python3 -I tests/run_tests.py` → 46/46 no build normal (forma da Parasite Queen, céu do hangar, TALLON IV
   inclusos), sem mudança de expectativa.
5. Experimento `--cruzar-banco hangar`: validate 0 problemas (avisa o hangar cruzando `$E0`/`$E1`), e
   `run_tests.py` → 47/47 (os 46 + `nivel_cruza_banco_hangar`).

## Plano de testes

| Camada | O quê | Qtde |
|--------|-------|------|
| validate.py | `check_banks` | +1 checagem |
| mutação à mão | (a)–(f) | 6 |
| build | sha1 igual em dois builds | 1 |
| run_tests.py (emulador) | `nivel_cruza_banco_<sala>` (só quando alguma sala cruza) | +1 no experimento |

## Riscos e reversão

- O sha1 muda (blobs em outro lugar): esperado. Os testes que dependem de endereço leem do manifest.
- Um hardware/emulador que espelhe a SRAM em `$F0–$FF:8000+` (não é o mapa LoROM padrão) quebraria os fixos: o
  LakeSnes e o mapa LoROM não fazem isso.
- Reversão: `tools/build.py`, `tools/frigate/ending.py`, `tools/validate.py`, `tests/run_tests.py` voltam e
  reconstrói.

## Fora de escopo

- Mudar nível de qualquer sala (09d, 09e). Mover os outros bancos (`$8F`, `$83`, `$84`...).
- Teste de cruzamento permanente no build normal (o nível só cruza `$E0`/`$E1` quando crescer ~8,6 KB, ou no modo
  de teste; aí o teste aparece sozinho).

## Desvios (preenchido na implementação)

Verificação (23/10/2026, na pasta real):

- `python3 -I tools/validate.py` → `72 salas, 148 portas, 0 problemas` (linha do Tallon igual, "alcançáveis
  agora: 15"), com as linhas novas "bancos: alocador nível $E08000-$EFFFFF: 72 blobs, 24119 bytes, livres 500169
  depois do último", "bancos: alocador fixo $F08000-$FFFFFF: 5 blobs, 21308 bytes, livres 502980 depois do
  último" e "bancos: nenhum nível cruza banco". Validate ~10,7 s (o `check_banks` recomprime os 72 níveis).
- `python3 -I tools/build.py` duas vezes → `build/metroid_prime_snes.ips` sha1
  `11071b4656e2f548e832492fe9bc7cb8e64d94bd` nas duas (era `ba13be7f…235b`: os blobs mudaram de lugar, esperado).
  Livres: **nível 500169 bytes a partir de `$E0:DE37`** (72 níveis, `$E0:8000–$E0:DE36`), **fixo 502980 bytes a
  partir de `$F0:D33C`**. Fixos: cena de Ceres (TALLON IV) `$F0:8000` (4017 bytes), estrelas do hangar tiles
  `$F0:8FB1` (256) e mapa `$F0:90B1` (4096), paleta do tileset 4 `$F0:A0B1` (185), Parasite Queen (gráficos do
  tileset 4) `$F0:A16A` (12754). Os outros bancos (`$8F`, `$83`, `$84`, `$A0`–`$B4`) iguais.
- `python3 -I tests/run_tests.py` → **46/46** (inclusos `parasite_queen_forma_nova`, `hangar_ceu_estrelado` e os
  do céu do hangar depois de pause/X-ray/Air Lock, `fuga_*` com o TALLON IV), nenhuma expectativa mudou; o
  runner avisa "nenhum nível cruza banco neste build".
- Mutações do validador (`scratchpad/s09c/mut_banks.py`, na memória; sem mutação e depois: 0 problemas), todas
  acusadas: (a) estados do hangar apontando o nível da airlock → "nível em $E08189 … o manifest diz $E08000",
  "bytes do nível … não são os da sala" e 2 sobreposições; (b) `FIXED_BANKS` a partir de `$EF:8000` → "alocadores
  … se sobrepõem"; (c) nível da airlock copiado 8 bytes antes do fim do do hangar e repontado → "bytes … não são
  os da sala" (hangar) + "se sobrepõem"; (d) tiles das estrelas em `$F1:FFF0` → "cruza o banco"; (e) paleta do
  tileset 4 copiada para `$E0:F000` → "fora do alocador fixo"; (f) nível da Tallon Canyon apontando `$E4:8000`
  (`$FF`) → manifest diferente + "bytes … não são os da sala".
- **Experimento de cruzamento** (`python3 -I tools/build.py --cruzar-banco hangar`, enchimento de 32572 bytes):
  nível do hangar em `$E0:FF3C` + 393 bytes (196 no `$E0`, 197 no `$E1`), todos os outros níveis no `$E1`;
  validate 0 problemas com "AVISO nível de hangar cruza banco ($E0FF3C + 393)"; `run_tests.py` → **47/47** (os 46
  + `nivel_cruza_banco_hangar`: nível na WRAM = o da sala nos 2048 blocos, Samus parada em y `$00A8`; foto
  `specs/img/09c-hangar-cruza-banco.png`). Também `--cruzar-banco tallon_canyon` (a sala da 09d; `$E0:FE18` +
  977): validate 0, `nivel_cruza_banco_tallon_canyon` passa (4 blocos diferentes, todos da tampa cinza da T3;
  `specs/img/09c-tallon-canyon-cruza-banco.png`). Mutação do teste: na ROM do experimento do hangar, 1 bit
  trocado num byte do nível já no `$E1` (`$E1:803D`, cópia em `scratchpad/s09c/mut_cross.sfc`) → "16 blocos do
  nível na WRAM diferentes do da sala": o jogo lê mesmo os bytes do banco seguinte. Depois, build normal de novo.

Desvios e detalhes:

- **Paletas e o gráfico do TALLON IV também foram para o fixo** (a decisão 6 do épico os deixava no fluxo do
  nível): o pedido desta filha foi tirar do `$E0–$EF` tudo que não é nível. Assim o alocador de nível só tem os
  72 níveis, em ordem, e as checagens ficam simples (todo blob do `level` é um nível de sala).
- O descompressor cruza banco também no `DecompressToVRAM` (`$80:B271`, usado nos gráficos do tileset ao
  carregar um save): o comentário de `queen_art.apply` foi corrigido. Os fixos continuam num banco só (regra do
  alocador), por causa do DMA das estrelas.
- Faixas escolhidas: metade da expansão para cada alocador (`$E0–$EF` e `$F0–$FF`, 512 KB cada); toda a expansão
  estava vazia (`$FF`) antes, fora o que o build punha no `$E0`/`$E1`.
- O manifest ganhou a chave `banks` (não é sala): `tests/run_tests.py` a pula ao montar a tabela de salas.
- O teste `nivel_cruza_banco_<sala>` só existe quando algum nível cruza banco (nenhum no build normal: o próximo
  cruzamento natural pede ~8,6 KB a mais de nível, que é o que falta para o `$E0:FFFF`). A chegada na sala do
  Tallon é por teleporte de porta do pouso (caminho mais curto pelo grafo de portas, travas ignoradas), com a
  Gravity Suit.
