# Super Metroid room format: verified spec for programmatic room creation

Target ROM: `base/sm_fix.sfc`. It is NTSC, unheadered, 3 MB LoROM, with the Fix Collection patch applied (CRC32 `3F8F3EAA`, MD5 `67f700263c995d10ff49935acd2d9eb9`).
Addresses are SNES LoROM (`$BB:AAAA`). File offset = `((bank & 0x7F) << 15) | (addr & 0x7FFF)`.

**How things were verified.** Each item carries a *Verified* note:
- **C** means the function was read in `vendor/sm/src` (snesrev/sm).
- **ROM** means the bytes were dumped from `sm_fix.sfc` with a Python script.
- **CRAWL** means the claim was checked over every room. The crawl started from all load stations, followed every door, and found 262 rooms with 323 states. It decompressed every level and checked each field.
- **ASM** means the 65816 bytes in the ROM were hand-disassembled.

Anything else is marked **UNVERIFIED**.

---

## 0. Bank-lock summary (read this first)

| Structure | Bank | Pointer width | Verified |
|---|---|---|---|
| Room header | **$8F** | 16-bit (door entry, load station) | C `get_RoomDefHeader` = `0x8F0000\|p` |
| State header | **$8F** | 16-bit | C `get_RoomDefRoomstate` |
| Door-out list (array of door ptrs) | **$8F** | 16-bit (room header +9) | C `BlockColl_Horiz_Door`: `RomPtr_8F(door_list_pointer + 2*(bts&0x7F))` |
| Door entry | **$83** | 16-bit | C `get_DoorDef` = `0x830000\|p` |
| Door ASM | **$8F** | 16-bit | ASM `$8F:E8A3`: `LDA $83000A,x; BEQ; … JMP ($0012)` with DB=$8F |
| Level data (compressed) | **any bank** | **24-bit** (state +0) | C `Load24(&room_compr_level_data_ptr)`. The decompressor crosses bank boundaries (ASM `$80:B119`: `INX; BNE; JSR $B266`). Vanilla room $ADAD's data runs $C7:FF02→$C8:8532. |
| FX list | **$83** | 16-bit | ASM `$89:AB82` (`PEA $8300; PLB`) |
| Enemy population | **$A1** | 16-bit | C `get_EnemyPopulation(0xa1, …)` |
| Enemy set ("enemy tilesets") | **$B4** | 16-bit | C `get_EnemyTileset` = `0xB40000\|p` |
| Enemy species header | $A0 | 16-bit | C `get_EnemyDef_A2` = `0xA00000\|p` |
| Scroll data | **$8F** | 16-bit | C `LoadLevelDataAndOtherThings`: `RomPtr_8F(rdf_scroll_ptr)` |
| Scroll-PLM change lists | **$8F** | 16-bit (PLM arg) | C `PlmInstr_ProcessAirScrollUpdate`: `RomPtr_8F(arg)` |
| PLM population | **$8F** | 16-bit | C `get_RoomPlmEntry` = `0x8F0000\|p` |
| PLM headers/code | $84 | 16-bit | C `SpawnRoomPLM` → `CallPlmHeaderFunc(func\|0x840000)` |
| Library-BG command list | **$8F** | 16-bit (its payloads are 24-bit) | C `LoadLibraryBackground` |
| Room setup / main ASM | **$8F** | 16-bit | ASM `$8F:E88F`: `LDX $07BB; LDA $0018,x; BEQ; PHK; PLB; JSR ($0018,x)` |
| X-ray special-case list | **$8F** | 16-bit | C `RomPtr_8F(xray_special_casing_ptr)` |
| Tileset table / entries | $8F:E7A7 / $8F:E6A2.. | entries hold three 24-bit ptrs | C `LoadStateHeader` + ROM (`$82:DF03: BE A7 E7` = `LDX $E7A7,y`) |
| Tileset gfx / tile tables / palettes | **any bank** | 24-bit | ROM (vanilla uses $BA–$C2) |
| Load-station table | $80:C4B5 | 16-bit | C `LoadFromLoadStation` + ASM `$80:C437` |

**Takeaways:**
- Level data and tileset data can go in the expanded banks $E0–$FF.
- Everything else for a room must go into $8F, $83, $A1 or $B4.

---

## 1. Room header ($8F), 11 bytes + state-select list

Verified by C `LoadRoomHeader` ($82:DE6F), the `RoomDefHeader` struct, and the crawl.

| Off | Size | Field | Notes |
|---|---|---|---|
| 0 | 1 | room index | Stored to $7E079D (semi-unique per area). |
| 1 | 1 | area | 0 Crateria, 1 Brinstar, 2 Norfair, 3 Wrecked Ship, 4 Maridia, 5 Tourian, 6 Ceres, 7 Debug. Stored to $7E079F. |
| 2 | 1 | map X | Pause-map tile coordinate. |
| 3 | 1 | map Y | |
| 4 | 1 | width | In screens (16 blocks each). Width × height must be ≤ 50 (scroll array is 50 bytes; level buffer is $6400 bytes). |
| 5 | 1 | height | In screens. |
| 6 | 1 | up scroller | Vanilla is $70 (239/262 rooms), sometimes $90 or $A0. C `samus_y_pos - up_scroller`. |
| 7 | 1 | down scroller | Vanilla is $A0. |
| 8 | 1 | CRE bitset | Vanilla is 0 (253 rooms). **bit1** ($02) = reload the CRE tiles and CRE tile table on entry (C `LoadLevelScrollAndCre`, `DoorTransitionFunction_PlaceSamusLoadTiles`). **bit2** ($04) = re-upload CRE VRAM. **bit0** ($01) = don't preserve some BG palette lines and the timer across doors, and change the IRQ `TM` (C `GameState_10_LoadingNextRoom`, `IrqHandler_10`). Use **$00**. |
| 9 | 2 | door-out ptr | Points into $8F, to an array of 16-bit $83 door pointers. |
| 11 | … | state-select list | See below. |

The room pointer must be ≥ $8000. A door whose destination pointer has bit 15 clear is treated as solid (or as an elevator), not as a transition. Verified by C `BlockColl_Horiz_Door`.

### State-select list

Starts at room+11. The engine executes each entry's code pointer in order (ASM `$8F:E5D2`: `TXA; ADC #$0B; TAX; loop: LDA $0000,x; STA $07B7; INX×2; PEA $E5D7; JMP ($07B7)`). The first entry that matches selects its state header. The list must end with `$E5E6`; the **default state header immediately follows** that word (ASM `$8F:E5E6`: `STX $07BB; PLA; RTL`).

| Code ($8F) | Args after the word | Condition | Vanilla uses |
|---|---|---|---|
| **E5E6** | none; 26-byte default state follows | always (terminator) | 262 |
| **E5EB** | door ptr (2), state ptr (2) | `$078D` (door used to enter) == arg | 0 (exists in ROM; **not** in the C port) |
| E5FF | state ptr (2) | area boss bit 1 set (`JSL $8081DC` with A=1) | 1 (MB room) |
| **E612** | event# (1), state ptr (2) | event set (`JSL $808233`) | 24 |
| **E629** | boss-bit mask (1), state ptr (2) | `boss_bits[area] & mask` | 33 |
| E640 | state ptr (2) | morph ball collected (`$09A4 & 4`) | 0 |
| E652 | state ptr (2) | morph and max missiles ≠ 0 | 2 |
| E669 | state ptr (2) | max power bombs ≠ 0 (`$09D0`) | 1 |
| E676 | state ptr (2) | speed booster collected (`$09A4 & $2000`) | 0 |

*Verified:* ASM dump of `$8F:E5D2–$8F:E689`, C `HandleRoomDefStateSelect` (the C port lists only E5E6/E5FF/E612/E629/E652/E669), and crawl counts.

**Minimal new room:** `[11-byte header] E6 E5 [26-byte state]`.

Example from ROM, Crateria save room `$8F:93D5`: `04 00 12 06 01 01 70 A0 00 FC 93 | E6 E5 | state…`.

### State header, 26 bytes

Verified by C `LoadStateHeader` ($82:DEF2), `RoomDefRoomstate`, and ASM (setup at +$18).

| Off | Size | Field | Notes |
|---|---|---|---|
| 0 | 3 | level data | 24-bit pointer, any bank. |
| 3 | 1 | tileset index | Into the table at $8F:E7A7 (§8). |
| 4 | 1 | music data index (song set) | 0 = keep current (C `LoadRoomMusic`). |
| 5 | 1 | music track | 0 = keep current (C `UpdateMusicTrackIndex`). Save rooms use `09 05`. |
| 6 | 2 | FX ptr ($83) | **$0000 = no FX.** ASM `$89:AB82`: `LDX $07CD; BNE …; PLB; PLP; RTL`. A pointer to a `$FFFF` word also means no FX. |
| 8 | 2 | enemy population ptr ($A1) | Must be valid. Empty list = `FF FF 00`. |
| 10 | 2 | enemy set ptr ($B4) | Empty = a `FF FF` word. 0 is tolerated only when the population is empty. |
| 12 | 2 | layer-2 scroll | Low byte = X, high byte = Y. Per byte: `00` = BG2 locked 1:1 to BG1; `01` = BG2 static; other values = parallax ratio `(v & $FE)/256`. **bit0 set in a byte = layer 2 is not taken from level data** (it comes from the library BG). See C `CalculateLayer2Xpos/Ypos` and the `layer2_scroll_x & 1` checks in `$80`. Crawl: bit0=1 ⇒ no layer-2 data and BG ptr set (179 states); bit0=0 ⇒ layer-2 in level data (124). Common values: $C1C1, $0101, $0000. |
| 14 | 2 | scroll ptr | $0000/$0001 special, else $8F pointer (§4). |
| 16 | 2 | special x-ray ptr ($8F) | 0 = none. Otherwise entries `{x u8, y u8, block u16}` terminated by x=y=0 (C `$84` x-ray code). |
| 18 | 2 | main ASM ($8F) | 0 = none (C `RunRoomMainCode` $8F:E8BD). |
| 20 | 2 | PLM population ptr ($8F) | 0 = none (C), or point at a `00 00` word. |
| 22 | 2 | library-BG ptr ($8F) | Used only if bit 15 is set; 0 = none (C `LoadLibraryBackground`). |
| 24 | 2 | setup ASM ($8F) | 0 = none (ASM `$8F:E88F` `BEQ`). |

**Library-BG commands** (word opcode, then args; C `kLoadLibraryBackgroundFuncs`):

| Opcode | Args | Meaning |
|---|---|---|
| `0000` | — | end |
| `0002` | src24, VRAM dst16, size16 | DMA to VRAM |
| `0004` | src24, WRAM dst16 | decompress to `$7E:dst` |
| `0006` | — | clear FX tilemap |
| `0008` | as `0002` | DMA and set BG3 base |
| `000A` | — | clear BG2 tilemap |
| `000C` | — | clear Kraid BG2 |
| `000E` | door16 + `0002` args | transfer only if entered via that door |

---

## 2. Level data

### Decompressed layout

The data is decompressed to `$7F:0000`. Verified by C `LoadLevelDataAndOtherThings` ($82:E7D3) and `LoadLevelScrollAndCre` ($82:EA73). The crawl checked all 262 rooms: size word == 2·W·H·256 except $ADAD and $C98E, which store more data than their dimensions need (harmless).

```
+0          u16  S = layer-1 size in bytes = 2 * (W*16) * (H*16)
+2          S bytes   layer-1 block words, row-major, row length = W*16 blocks
+2+S        S/2 bytes BTS, one byte per block
+2+S+S/2    S bytes   layer-2 block words (optional; only meaningful when layer-2 scroll bit0 = 0)
```

After decompression the engine copies the sections to fixed places:
- BTS goes to `$7F:6402`.
- Layer 2 goes to `$7F:9602`.
- Layer 1 stays at `$7F:0002`. Before decompressing, layer 1 is cleared to `$8000` (solid) for $6400 bytes.

Maximum S = $6400 (12800 blocks = 50 screens).

### Block word (layer 1 / layer 2)

Verified by C `$80` row/column update (`&0x3FF`, `&0xC00` with H/V-flip XOR `0x4000`/`0x8000`) and `kBlockColl_*_CheckColl[(w & 0xF000)>>12]` in `$94`.

| Bits | Meaning |
|---|---|
| 0–9 | metatile index $000–$3FF. $000–$0FF = CRE metatiles; $100–$3FF = tileset (SCE) metatiles. |
| 10 | horizontal flip |
| 11 | vertical flip |
| 12–15 | block type |

Block types (C `kBlockColl_Horiz_CheckColl` $94:9515):

| Type | Meaning |
|---|---|
| 0 | air |
| 1 | slope (BTS = slope shape) |
| 2 | spike-air |
| 3 | special air |
| 4 | shootable air |
| 5 | horizontal extension (BTS = signed X offset to the parent block) |
| 6 | unused air |
| 7 | bombable air |
| 8 | solid |
| **9** | **door** (BTS = door index) |
| A | spike |
| B | special / crumble |
| C | shot block (BTS selects the PLM; **$40–$43 = blue door cap**) |
| D | vertical extension (BTS = signed Y offset) |
| E | grapple |
| F | bomb block |

Vanilla "empty air" is `$00FF`. Door transition tile example: `$9040` with BTS `00`.

### Compression format

Accepted by `DecompressToMem` $80:B119 and `DecompressToVRAM` $80:B271. Verified by the C port and ASM header bytes. A Python reimplementation decompresses every vanilla level to the exact size word. A Python compressor was round-trip tested on 60 vanilla levels; its output was 66,222 bytes against 102,900 for vanilla.

The stream is a sequence of chunks; byte `$FF` terminates it.

- **Header byte `c`:**
  - If `c & $E0 != $E0`: `cmd = c >> 5`, `len = (c & $1F) + 1` (1–32).
  - If `c & $E0 == $E0` (extended): `cmd = (c >> 2) & 7`, `len = ((c & 3) << 8 | next) + 1` (1–1024).
  - `c = $FF` is end. So an extended cmd 7 can't use length high bits = 3; avoid it.

| cmd | Args | Output |
|---|---|---|
| 0 | `len` bytes | literal copy |
| 1 | b | `b` repeated `len` times |
| 2 | b0 b1 | alternating b0 b1 b0 … (`len` bytes total) |
| 3 | b | b, b+1, b+2 … (8-bit wrap) |
| 4 | lo hi | copy `len` bytes from output offset `hi:lo` (relative to destination start; byte-by-byte, so overlap is OK) |
| 5 | lo hi | same as 4, each byte XOR $FF |
| 6 | n | copy from `cur - n` (n = 1–255) |
| 7 | n | same as 6, XOR $FF |

The source pointer wraps from `$xx:FFFF` to `$(xx+1):8000`, so compressed data may straddle banks.

Reference code (`decompress` mirrors the C port exactly; `compress` is a simple greedy compressor, tested):

```python
def decompress(src):
    out=bytearray(); i=0
    while True:
        c=src[i]; i+=1
        if c==0xFF: return bytes(out)
        if c&0xE0==0xE0: cmd=(c<<3)&0xE0; n=((c&3)<<8|src[i])+1; i+=1
        else: cmd=c&0xE0; n=(c&0x1F)+1
        if cmd&0x80:
            x=0xFF if cmd&0x20 else 0
            if cmd>=0xC0: p=len(out)-src[i]; i+=1
            else: p=src[i]|src[i+1]<<8; i+=2
            for k in range(n): out.append(out[p+k]^x)
        elif cmd==0x20: out+=bytes([src[i]])*n; i+=1
        elif cmd==0x40: out+=bytes(src[i+(k&1)] for k in range(n)); i+=2
        elif cmd==0x60: out+=bytes((src[i]+k)&0xFF for k in range(n)); i+=1
        else: out+=src[i:i+n]; i+=n

def _hdr(cmd,n):
    n-=1
    return bytes([cmd<<5|n]) if n<32 and cmd!=7 else bytes([0xE0|cmd<<2|n>>8, n&0xFF])

def compress(data):
    out=bytearray(); lit=bytearray(); i=0; L=len(data)
    def flush():
        nonlocal lit
        for k in range(0,len(lit),1024): ch=lit[k:k+1024]; out.extend(_hdr(0,len(ch))+ch)
        lit=bytearray()
    while i<L:
        best=(0,None); mx=min(1024,L-i)
        n=1
        while n<mx and data[i+n]==data[i]: n+=1
        if n>=3: best=(n-2,(1,n,bytes([data[i]])))
        if i+1<L:
            n=2
            while n<mx and data[i+n]==data[i+(n&1)]: n+=1
            if n>=4 and n-3>best[0]: best=(n-3,(2,n,data[i:i+2]))
        n=1
        while n<mx and data[i+n]==(data[i]+n)&0xFF: n+=1
        if n>=3 and n-2>best[0]: best=(n-2,(3,n,bytes([data[i]])))
        for p in range(max(0,i-0x2000),i):          # O(n*window); fine for rooms
            if data[p]!=data[i]: continue
            n=0
            while n<mx and data[p+n]==data[i+n]: n+=1
            if n-3>best[0]: best=(n-3,(4,n,bytes([p&0xFF,p>>8])))
        if best[1] is None: lit.append(data[i]); i+=1; continue
        flush(); cmd,n,arg=best[1]; out.extend(_hdr(cmd,n)+arg); i+=n
    flush(); out.append(0xFF); return bytes(out)
```

---

## 3. Doors

### Door-out list ($8F)

The room header +9 points to a plain array of 16-bit pointers into bank $83, with **no terminator**. Index = `BTS & $7F` of the type-9 block Samus touches.

A door is normally 4 type-9 blocks on the screen-edge column (or row), all with the same BTS. The cap sits one block inward:
- a type-C block with BTS $40/$41/$42/$43,
- plus 3 extension blocks (type D with BTS FF/FE/FD for horizontal doors).

*Verified:* C `BlockColl_Horiz_Door`/`BlockColl_Vert_Door` ($94:938B/$94:93CE), and a dump of room $93D5 (column 15 = `9040 9060 9860 9840`, BTS 00; column 14 = `C00C:40 D02C:FF D82C:FE D80C:FD`).

### Door entry ($83), 12 bytes

Verified by C `LoadDoorHeader` ($82:DE12) and the `DoorDef` struct. ROM example `$83:89BE` = `FD 92 00 04 11 26 01 02 00 80 81 B9`.

| Off | Size | Field | Notes |
|---|---|---|---|
| 0 | 2 | destination room ptr ($8F) | Bit 15 clear ⇒ not a real door (solid / elevator). |
| 2 | 1 | bitflags | **$80** = elevator (`elevator_flags`). **$40** = area change (saves/loads the explored-map mirror; C `SaveMapExploredifElevator`). Low nibble = elevator-used index (C `SetElevatorsAsUsed` $80:CD07). Normal door = **$00**. |
| 3 | 1 | direction | bits 0–1: **0 = right, 1 = left, 2 = down, 3 = up** (direction Samus travels). **bit 2 ($04)** = spawn a door-closing cap behind Samus. The cap PLM comes from $8F:E68A[dir]: dir 4→C8BE, 5→C8BA, 6→C8C6, 7→C8C2 (C `SpawnDoorClosingPLM`; ROM). |
| 4 | 1 | cap X | Block X of the door cap in the destination room (used for the closing PLM and the colored-cap check). |
| 5 | 1 | cap Y | Block Y. |
| 6 | 1 | screen X | Destination screen X (`door_destination_x_pos = x << 8`). |
| 7 | 1 | screen Y | Destination screen Y. |
| 8 | 2 | distance from door | Bit 15 set ⇒ default (200 horizontal / 384 vertical; C). Vanilla uses **$8000** in 544 of 589 doors. |
| 10 | 2 | door ASM ($8F) | 0 = none (ASM $8F:E8A3). |

Samus keeps her sub-screen X/Y offset across the transition (C `DoorTransitionFunction_PlaceSamusLoadTiles`).

---

## 4. Scroll data

Verified by C `LoadLevelDataAndOtherThings`, the camera code in `$80:A893…`, and ROM.

- **Pointer < $8000 is a special value:**
  - **$0000**: every screen = 02 (green) except the bottom row = 01 (blue).
  - **$0001**: every screen = 02 (green).
  - Vanilla uses $0000 117 times and $0001 6 times.
- **Otherwise** it is a $8F pointer to W·H bytes, row-major (`index = y*W + x`). The engine always copies 50 bytes into `$7E:CD20`.
- **Values:**
  - 00 = red (the camera never shows that screen).
  - 01 = blue (shown, but vertical camera clamp is 31 px tighter, so the bottom of the screen is hidden).
  - 02 = green (fully visible).

Example: Landing Site `$8F:9283` = `00 00 02 02 …`.

**Scroll PLM** argument = $8F pointer to `{screen idx u8, value u8}` pairs, terminated by a byte with bit 7 set (`$80`). Verified by C `PlmInstr_ProcessAirScrollUpdate`; ROM `$8F:92B0` = `13 01 80`.

---

## 5. PLM population ($8F)

6-byte entries terminated by a `$0000` word. Verified by C `SpawnRoomPLM` $84:846A and `RoomPlmEntry`.

| Off | Size | Field |
|---|---|---|
| 0 | 2 | PLM header ptr ($84) |
| 2 | 1 | X block |
| 3 | 1 | Y block |
| 4 | 2 | argument |

Limit: 40 PLM slots.

PLM IDs below were verified by mapping the header's setup pointer to the C function name, by usage counts across all rooms, and by position checks.

| PLM | ID | Argument |
|---|---|---|
| Door caps (`PlmSetup_C794_GreyDoor` / `PlmSetup_Door_Colored`) | Order per color: **on right wall (facing L), left wall (facing R), bottom (facing U), top (facing D)**. Position-checked over all rooms: C842 on the right edge in 34 cases, C848 on the left edge in 38. | |
| — Grey | C842, C848, C84E, C854 | `type<<10 \| doorbit`. Type (bits 10–14): 0 = area boss dead, 1 = mini-boss dead, 2 = torizo dead, 3 = enemy kill quota (enemy-pop trailing byte), 4 = never opens, 5 = Tourian statues, 6 = animals escaped (table $84:BE4B). Bit 15 = no saved open bit. |
| — Yellow (power bomb) | C85A, C860, C866, C86C | door bit index (0–$1FF, unique, saved at $7ED8B0); bit 15 = don't remember |
| — Green (super) | C872, C878, C87E, C884 | same |
| — Red (missile) | C88A, C890, C896, C89C | same |
| — Blue | **no PLM**: level block type C with BTS $40 (facing L) / $41 (R) / $42 (U) / $43 (D). These spawn PLMs C8A2/C8A8/C8AE/C8B4 when shot (table $94:9EA6). | — |
| Closing caps (auto-spawned) | C8BA, C8BE, C8C2, C8C6 | — |
| Save station `PlmSetup_B76F_SaveStation` | **B76F** | save index 0–7 = **this area's load-station index** (`arg & 7`, C `PlmInstr_ActivateSaveStationAndGotoIfNo`) |
| Map station | B6D3 | $8000 |
| Energy refill | B6DF | vanilla values |
| Missile refill | B6EB | vanilla values |
| Scroll PLM (air) | **B703** | $8F scroll-list ptr |
| Scroll PLM (solid) | B707 | $8F scroll-list ptr |
| Extensions (make neighbors trigger the PLM) | B63B (right of PLM, writes type 5 BTS FF), B63F (left, 5/01), B643 (below, D/FF), B647 (above, D/01) | $8000 |
| Items | base + 4·n | **item bit index** (0–$1FF unique; $7ED870) |

Item bases: **visible EED7**, **chozo orb EF2B**, **hidden / shot-block EF7F**.

Item order n = 0 E-tank, 1 Missile, 2 Super, 3 PB, 4 Bombs, 5 Charge, 6 Ice, 7 Hi-Jump, 8 Speed, 9 Wave, 10 Spazer, 11 Spring, 12 Varia, 13 Gravity, 14 X-ray, 15 Plasma, 16 Grapple, 17 Space Jump, 18 Screw, 19 Morph, 20 Reserve.

So: E-tank EED7/EF2B/EF7F; Missile EEDB/EF2F/EF83; Super EEDF/EF33/EF87; PB EEE3/EF37/EF8B.

*Verified:*
- The setup pointers restart their pattern (EE4D, EE52, EE57, EE5C, then EE64…) exactly at EED7 and EF2B, and switch to EE77… at EF7F; $84:EFD3 = `FFFF` (end).
- Spot checks: EF23 (morph) in $9E9F Morph room; EF3B (chozo bombs) in $9804 Bomb Torizo; EF43 (ice) in $A890; EF57 (spring) in $D6D0; EF6F (space jump) in $D9AA; EF7B (chozo reserve) ×4 in the 4 reserve rooms.

---

## 6. Enemies

### Enemy population ($A1)

16-byte entries. Verified by C `InitializeEnemies` $A0:8A9E.

| Off | Size | Field |
|---|---|---|
| 0 | 2 | species header ptr ($A0) |
| 2 | 2 | X (pixels) |
| 4 | 2 | Y (pixels) |
| 6 | 2 | init param (initial instruction / orientation) |
| 8 | 2 | properties |
| 10 | 2 | extra properties |
| 12 | 2 | param 1 |
| 14 | 2 | param 2 |

Terminator: `FF FF` followed by **1 byte = kills required to "clear" the room** (`num_enemy_deaths_left_to_clear`, used by grey-door type 3). Empty room = `FF FF 00` (e.g. ROM `$A1:85D8`).

### Enemy set ($B4)

4-byte entries `{species ptr ($A0) u16, palette/VRAM word u16}`, terminated by `$FFFF`.
- Low nibble of the second word = sprite palette slot (`(v & 0xF) << 9`; palette is loaded to line `lo+8`).
- Bits 12–13 select fixed VRAM placement when the species' tile size has bit 15 set.
- At most **4** species (C `ProcessEnemyTilesets` fills 4-entry arrays).
- The 7 bytes before the list are an ASCII debug name (e.g. `SF1_05 `). They are not read in normal play, but vanilla always has them.

*Verified:* C `ProcessEnemyTilesets` $A0:8D64 and `LoadEnemyGfxToVram` $82:DFD1; ROM `$B4:8122` = `"SF1_05 " FF FF`.

---

## 7. FX ($83)

The FX pointer points to a list of 16-byte entries. Verified by C `LoadFXHeader`, ASM $89:AB82, and the `FxDef` struct.

**Selection:**
- Walk the entries.
- Word0 = $0000 ⇒ use this entry (default).
- Word0 = $FFFF ⇒ **no FX**, stop.
- Word0 == `$078D` (door used) ⇒ use this entry.
- Otherwise go to the next entry (+16).

**FX pointer $0000 = no FX** (ASM-verified BEQ). Vanilla's most common default entry is `00 00 FF FF FF FF 00 00 00 00 02 02 00 00 00 00` (29 states); 59 states point at a `$FFFF` word.

| Off | Size | Field |
|---|---|---|
| 0 | 2 | door ptr / $0000 / $FFFF |
| 2 | 2 | base Y |
| 4 | 2 | target Y |
| 6 | 2 | Y velocity |
| 8 | 1 | timer |
| 9 | 1 | type |
| 10 | 1 | default layer blend |
| 11 | 1 | layer-3 blend |
| 12 | 1 | liquid options |
| 13 | 1 | palette-FX bitset (per-area list $83:AC46) |
| 14 | 1 | animated-tiles bitset (per-area list $83:AC56) |
| 15 | 1 | palette blend |

FX types (C `kFxTypeFuncPtrs`): 0 none, 2 lava, 4 acid, 6 water, 8 spores, A rain, C fog, 20 ?, 22 scrolling sky, 24 ?, 26 Tourian statue, 28 Ceres Ridley, 2A Ceres elevator, 2C haze.

---

## 8. Tilesets

- **Table:** `$8F:E7A7` holds 29 word pointers (indices $00–$1C) to 9-byte entries at `$8F:E6A2 + 9·i`.
- **Entry:** `{tile-table (metatile defs) ptr24, tiles gfx ptr24, palette ptr24}`, all compressed.
- **To add tilesets:** relocate the table and patch the operand at `$82:DF04` (`LDX $E7A7,y`). The table is immediately followed by other data at $8F:E7E1.

**CRE/SCE split** (verified by C `LoadCRETilesTilesetTilesAndPalette`, `LoadLevelDataAndOtherThings`, `DoorTransitionFunction_PlaceSamusLoadTiles`):

| | CRE (common) | SCE (tileset) |
|---|---|---|
| Graphics | `$B9:8000` → VRAM byte $5000–$7FFF (tiles $280–$3FF) | → VRAM byte $0000–$4FFF (tiles $000–$27F); at most **$5000 bytes** |
| Metatile table | `$B9:A09D` → `$7E:A000` (metatiles $000–$0FF) | → `$7E:A800` (metatiles $100–$3FF; at most $1800 bytes) |
| Palette | — | → `$7E:C200` (BG palettes) |

On door transitions the CRE is only reloaded if the room's CRE bitset has bit1 set.

**Area 6 (Ceres):** the tileset's tile table goes to `$7E:A000` and the CRE table is *not* loaded. Using Ceres tilesets ($0F–$14) outside area 6 would overwrite metatiles $000–$0FF with CRE: **UNVERIFIED in practice**.

| Idx | Name (rooms using it, from the crawl) |
|---|---|
| 00 | Upper Crateria (Landing Site $91F8, Parlor $92FD …) |
| 01 | Red Crateria — **unused by any vanilla state** |
| 02 | Lower Crateria / Crateria tech ($94CC, $962A, $9804 Bomb Torizo, $97B5 …) |
| 03 | Old Tourian ($96BA Old MB room default, $975C) |
| **04** | **Wrecked Ship, power ON** (all 14 WS rooms, state `E629:01` = Phantoon dead) |
| **05** | **Wrecked Ship, power OFF** (same 14 rooms, default state) |
| 06 | Green/Pink/Blue Brinstar |
| 07 | Red Brinstar / Kraid's Lair |
| 08 | Statues hallway / pre-Tourian ($A5ED) |
| 09 | Heated Norfair (54 states) |
| 0A | Unheated Norfair (names per PJBoy; heat semantics UNVERIFIED) |
| 0B | Sandy Maridia |
| 0C | Rocky Maridia |
| **0D** | **Tourian** (all area-5 rooms) |
| 0E | Mother Brain room ($DD58) |
| **0F / 10** | **Ceres** rooms, normal / escape (`E629:01`) |
| 11 / 12 | Ceres elevator room $DF45, normal / escape |
| 13 / 14 | Ceres Ridley room $E0B5, normal / escape |
| 15 | Map rooms (+ powered WS map/save) |
| 16 | WS map/save rooms, unpowered |
| 17 | Energy/missile refill rooms |
| 18 | Refill rooms (variant: $9C89, $A641, $DD2E) |
| 19 | Save rooms (18 states) |
| 1A | Kraid room |
| 1B | Crocomire room |
| 1C | Draygon room |

**Frigate candidates:**
- 04/05 (Wrecked Ship tech, both palettes).
- 0D (Tourian metal).
- 02/03 (Crateria tech / Old Tourian).
- 0F–14 (Ceres space station, but tied to area 6 and mode-7 room code).

### Crateria tilesets, rain and Landing Site music (verified, spec 07c)

Read from `base/sm_fix.sfc` with `tools/smlib/room_reader.py` over every state of the 34 area-0 rooms.
- Tileset 0 (Upper Crateria): green rock with a blue stone rim, grass on top. Interior `$111`, floor
  `$10C/$118/$10F/$101`, wall `$110` (H-flip for air on the right), outer corners `$100` (top) /
  `$10D|V` (bottom), inner corners `$114`, thin ledge `$11A/$11B`; grass tufts `$12D–$130` are **air**
  (type 0) blocks. Pieces and counts: `specs/07c-estilo-crateria.md`, code `tools/smlib/crateria.py`.
- Tileset 2 (Lower Crateria) mixes metal (`$96BA`, `$99F9`) and stone bricks (`$99BD`, `$9879`):
  bricks `$2B6/$2B8` in a checker by (x+y) parity, floor `$2AF/$2AD` by x parity, ceiling the same
  V-flipped, no edge pieces; plant stalks `$36D–$370` are air. The purple organic rock (`$990D`,
  `$9969`) exists only as slopes (type 1) over black fill.
- Landing Site `$8F:91F8` default state: tileset 0, music `$06/$05`, FX `$83:80C0` =
  `00 00 FF FF FF FF 00 00 00 0A 02 0E 00 01 00 22` (default entry, type `$0A` rain, palette-FX
  bitset `$01` from the area's list). Checked in the emulator on a test room: `$196E` = `$000A`,
  `$07F3/$07F5` = `0006/0005`. Its library BG `$B76A` is only door-conditional (`0E`) transfers;
  `$8F:B8B4` (Parlor, BG2 scroll `$C1C1`) is a plain Crateria rock background.
- The project's palette recolor touches tileset 4 only; tilesets 0/2 in the built ROM equal the base.

---

## 9. Game start / load stations

### Load-station table

- `$80:C4B5`: 8 word pointers (one per area) into bank $80: C4C5, C5CF, C6D9, C81B, C917, CA2F, CB2B, CC19.
- Entry = **14 bytes**; address = `table[area] + 14·station` (ASM $80:C437 computes `((st*2)*2+st*2+st)*2`).
- Entries per area (from the gaps between tables): 19, 19, 23, 18, 20, 18, 17, 17. Area 7's list ends where `SetElevatorsAsUsed` code starts at $80:CD07.

| Off | Size | Field |
|---|---|---|
| 0 | 2 | room ptr. Only used to read the **area** byte (`area_index = header[1]`). |
| 2 | 2 | door ptr ($83). **The actual room loaded is the door's destination**, because `LoadDestinationRoomThings` → `LoadDoorHeader` overwrites `room_ptr`. The door's FX/door ASM/elevator flag also apply. Keep the door's destination equal to the room field: verified on 90 stations; the only 2 mismatches are debug entries. |
| 4 | 2 | door BTS (written to $078F; unused, "REMOVED" in C) |
| 6 | 2 | screen X (layer-1 X, pixels) |
| 8 | 2 | screen Y |
| 10 | 2 | Samus Y offset → `samus_y = screenY + off` |
| 12 | 2 | Samus X offset → `samus_x = screenX + 128 + off` (signed; FFE0 = −32) |

Verified by C `LoadFromLoadStation` and `StartGameplay_Async` $80:A07B.

**Station indices:**
- **$00–$07** = save stations (save PLM `arg & 7`).
- **$08–$0F** = elevators. These are selectable from the file-select map only when the debug flag is set; their "used" bits are $7ED8F8 bits 8–15.
- **$10+** = debug/special. They are reachable only via the debug file-select map: `enable_debug $7E05D1` ≠ 0, then press Select on pad 2 (C `$81` file-select-map code).
- Exception: **Crateria $12** (Landing Site via door $88FE) is what the game uses after the Ceres escape (`loading_game_state == $22` ⇒ area 0, station 18; C `InitAndLoadGameData_Async`).

Area 0 station 0 = Landing Site at the ship (room $91F8, door $896A).

### New-game flow (C + ASM)

1. File select (`$81`). For an empty slot, `LoadFromSram` fails, which sets `area=0`, `station=0`; then `NewSaveFile` $81:B2CB runs (99 HP, no items). The game goes to state 2 (options menu) → "Start Game" → `GameOptionsMenu_4_StartGame` **$82:EEB4**.
2. `$82:EEC3`: `LDA $7ED914` (`loading_game_state`).
   - If ≠0: `STA $0998` (5 = file-select map → then state 6).
   - If 0 (new game) → `$82:EED9`: `A9 1E 00 8D 98 09` (game state $1E intro), then `A9 95 A3 8D 51 1F` (cinematic fn $A395), `9C 9E 09 9C 23 07 9C 25 07 60`.
3. The intro ends at `$8B:C100`: `loading_game_state = game_state = $1F`, `area = 6`, `station = 0`, then `SaveToSram`.
4. State $1F = `InitAndLoadGameData` (same as state 6), which forces area 6 / station 0 (Ceres).
5. Ceres escape → `loading_game_state = $22` → area 0 / station $12.
6. The ship landing (`GunshipTop_7` $A2:A987) sets `loading_game_state = 5` (normal) and station 0.

**Cleanest patch: skip intro and Ceres, start at chosen (area, station).** Replace `$82:EED9` (PC 0x016ED9) with `4C 0F F7` (`JMP $F70F`). Then put this at **$82:F70F** (vanilla free, untouched by Fix Collection):

```
A9 06 00      LDA #$0006 ; STA game_state -> LoadingGameData
8D 98 09      STA $0998
A9 05 00      LDA #$0005 ; loading_game_state = Main (saves made later won't replay the intro)
8F 14 D9 7E   STA $7ED914
A9 aa 00      LDA #area
8D 9F 07      STA $079F
A9 ss 00      LDA #station
8D 8B 07      STA $078B
9C 9E 09      STZ $099E
9C 23 07      STZ $0723
9C 25 07      STZ $0725
60            RTS        ; (same bank; StartGame was reached via JSR)
```

Why this works:
- With `loading_game_state == 5`, `InitAndLoadGameData` does not override area/station; it calls `LoadFromLoadStation` and then `CallSomeSamusCode(9)` (Samus appears facing forward with the "load" flash).
- Existing saves are unaffected, because their `loading_game_state` is ≠0 and they take the other branch.
- The patch logic is derived from the C code and ASM bytes. **It has not been run in an emulator.**

---

## 10. Free space (this ROM)

Method: trailing `$FF` runs per bank (`free.py` scan), cross-checked against the end of crawled structures and against well-known vanilla free-space starts (from memory, except $A1:EBD1, which was confirmed via [metroidconstruction.com](https://metroidconstruction.com/SMMM/adding-enemies-plm.html)).

| Bank | Free range | Size | Notes |
|---|---|---|---|
| **$8F** | **$8F:E9AF–$8F:FFFF** | **$1651 (5713)** | Vanilla free starts at $E99B. **Fix Collection put code at $8F:E9A0–$E9AE** (new room setup ASM, see below). Avoid $E99B–$E9AE. The build fills it up to $8F:F029 (hangar background list: 20 bytes, §15). |
| **$83** | **$83:AD66–$83:FFFF** | **$529A (21146)** | Matches vanilla. Max vanilla door entry is $ABB8, max FX ptr $A188. |
| **$A1** | **$A1:EBD1–$A1:FFFF** | **$142F (5167)** | Matches vanilla. |
| **$B4** | **$B4:F4B8–$B4:FFFF** | **$0B48 (2888)** | Matches vanilla. Vanilla enemy sets end ≤ $92C3; $B4 also holds vulnerabilities and drops. |
| $84 | $84:EFD3–$84:F0FF and $84:F10F–$84:FFFF | $12D + $EF1 | **Fix Collection code at $84:F100–$F10E** (called from $84:861A and $84:E094). |
| $80 | $80:CD8E–$80:FFBF | $3232 | Matches vanilla. |
| VRAM | BG tiles $240–$27F (word $2400–$27FF) | 64 tiles | Free with tileset 4 (frigate); hangar star tiles (§15). |
| $82 | $82:F70F–$82:FFFF | $8F1 | New-game routine at $F70F, then the `bank82` allocator in `build()` (area-select label, section 14). Use the allocator, not fixed addresses. |
| $A9 | $A9:FB70–$A9:FBFF, $A9:FC0B–$A9:FFFF | — | **Fix Collection code at $A9:FC00–$FC0A** (31 call sites in $A9). |
| $A0 | $A0:F7D3–$A0:FFFF | $82D | Trailing `$FF` scan. Used for new enemy species headers (keep them on the $xx3F/$xx7F/$xxBF/$xxFF grid like vanilla). |
| $A2 | $A2:F498–$A2:FFFF | $B68 | Trailing `$FF` scan. Gunship patches. |
| $A6 | $A6:FEBC–$A6:FFFF | $144 | Trailing `$FF` scan. Meta Ridley init/main (small: plan it). |
| $B8 | entire bank | $8000 | |
| $CE / $DE / $DF | $CE:B22D / $DE:D1C0 / $DF:D4DF – end | $4DD3 / $2E40 / $2B21 | |
| $E0–$FF | after 4 MB expansion | 1 MB | Usable only for **24-bit-pointed data**: level data, tileset gfx/tables/palettes, library-BG payloads, enemy tile gfx. The hangar starfield uses $1100 bytes (§15); the Parasite Queen's tileset 4 graphics 12754 bytes in one bank (§17). |

The header ROM-size byte `$00:FFD7` is already `$0C` (4 MB) in this ROM. In LoROM, banks $E0–$FF map to file offset $300000–$3FFFFF.

**Fix Collection touches room data, not just code.** In Tourian room **$DCB1**, the two states' setup-ASM pointers are `$E9A0` (`LDA #1; JSL $8081FA; RTS`) and `$E9A8` (`STZ $0F78; STZ $0FB8; RTS`). The vanilla values are UNVERIFIED (no clean ROM on disk).

---

## 11. WRAM for testing

All verified via `variables.h` (offsets from $7E0000).

| Address | Meaning |
|---|---|
| $7E0998 | game state: 6 loading game, 7 fade-in, **8 gameplay**, 9 hit door, $A/$B loading next room, $1E intro, $1F new-game setup (Ceres), $28+ demo |
| $7E079B | room header ptr |
| $7E079D | room index |
| $7E079F | area |
| $7E07BB | selected state header ptr |
| $7E07B5 | door-out list ptr |
| $7E078B | load-station index |
| $7E078D | door ptr (last door used) |
| $7E0791 | door direction |
| $7E0793 | door bitflags/dir word |
| $7E0E16 | elevator flags |
| $7E0931 | door transition flag |
| $7E0795 / $7E0797 | door transition flag (elevator/zebetites) / (enemies) |
| $7E099C | door transition function |
| $7E0AF6 / $7E0AF8 | Samus X / X sub |
| $7E0AFA / $7E0AFC | Samus Y / Y sub |
| $7E0A1C | Samus pose |
| $7E09C2 / $7E09C4 | health / max health |
| $7E09C6 / $7E09C8 | missiles / max |
| $7E09A2 / $7E09A4 | equipped / collected items |
| $7E0911 / $7E0915 | layer-1 X / Y |
| $7E05D1 | enable_debug |
| $7ED914 | loading_game_state (0 intro, 5 main, $1F Ceres, $22 escaping Ceres) |
| $7E1F51 | cinematic function |
| $7ED820 | events |
| $7ED828 | boss bits per area |
| $7ED870 | item bits |
| $7ED8B0 | opened-door bits |
| $7ED8F8 | used save stations/elevators |
| $7F0000 | size word |
| $7F0002 | layer 1 |
| $7F6402 | BTS |
| $7F9602 | layer 2 |
| $7ECD20 | scroll array (50 bytes) |
| $7EA000 | metatile table |

---

## 12. Pause map, minimap and map station

Verified in the emulator (test `map_station_e_mapa_de_pausa`) and against vanilla data.

### Tables in $82 (per area, index = area)

| Table | Address | Format |
|---|---|---|
| Tilemaps | $82:964A | 24-bit pointers; area 3 = $B5:B000. 0x1000 bytes = 64x32 tiles as two 32x32 pages (x 0-31, then x 32-63). |
| Map-station reveal | $82:9717 | $82 pointers to 0x100-byte bit masks (area 3 = $82:9A27; areas 5 and 7 share one). |
| Area name | $82:965F | $82 pointers to 12 tilemap words. Letters A-Z = $3830-$3849, blank = $2801. |
| Map icons | $82:C7CB | blocks of 0x10 bytes (8 area pointers) per kind: +$00 boss (drawn when the boss bit is set), +$30 map station, +$40 save stations (entry n = load station n; the file-select map puts Samus there), +$50 elevators, +$60 debug. Entries are (x, y) map pixels; $FFFE skips a slot, $FFFF ends the list. |
| "To <area>" labels | $82:C74D | $82 pointers to 6-byte entries (x, y, spritemap), $FFFF ends. Area 3 had 2. |

### Coordinates

- A room screen (sx, sy) is tile **(map_x + sx, map_y + sy + 1)**. The game adds 1 to the row (C `MarkMapTileAsExplored`, `UpdateMinimap`), and so do the vanilla icons: the WS save room at map (17,14) has its icon at (0x88, 0x78).
- Bit masks (explored, reveal): byte = `(tx>>5)*128 + ty*4 + (tx&31)>>3`, bit = `0x80 >> (tx&7)`.
- Icon pixel = tile × 8.
- Scroll limits come from the mask (C `DetermineMapScrollLimits`), so no table needs editing.
- Explored bits of the current area live at **$7E07F7** (0x100 bytes). $7ECD52 holds one 0x100 copy per area.

### Tiles (pause BG1 tiles at $B6:8000)

- Tilemap words use palette 3 (`$0C00`); the game clears bit $400 on explored tiles. `$001F` = empty.
- Vanilla draws room outlines only, no door marks.
- Walls by side, other orientations by H/V flip:
  - **$1B** none, **$26** top, **$27** right, **$22** top+bottom, **$23** left+right;
  - **$25** left+top, **$24** left+right+top, **$21** left+top+bottom, **$20** all four.
- Save rooms use **$4D** (a box with an "S"). Vanilla map rooms use **$6F** (a box with a dot).

### Area 0 specifics (specs/07f, verified by bytes and in the emulator)

- The ship icon (menu spritemap $63) is hard-coded for area 0 in `DrawMapIcons` ($82:B6BC) and
  `DrawFileSelectMapIcons` ($82:B777): always drawn at (`$82:C853`, `$82:C855`) = entry 0 of area 0's
  save-icon list. Moving that entry moves the ship icon.
- The save-icon list is read until `$FFFF`, one used-station bit per entry: entries 8-15 are the next
  list (area 0: the elevator icons at `$82:C873`, drawn by the elevator bits). The area-select screen
  draws an area's name only when a used bit falls on an entry that is not `$FFFE`.
- The pause map as shown is DMA'd from `$7E:4000` to VRAM `$3000` (name: 12 words at VRAM `$38AA`);
  `$7E:4000` is reused right after, so tests read VRAM.

### Map station (PLM B6D3, argument $8000)

- The PLM block sits at Samus' cannon height: Samus must stand with `samus_y == 16*plm_y + 11`, i.e. on the floor 2 rows below the PLM.
- Setup writes access blocks B/47 at +1 block and B/48 at −2 blocks. Samus activates the station by running into one of them (pose "ran into wall").
- The vanilla base is a T shape: a row of 4 solid blocks (x−2..x+1) over a 2-block stem (x−1..x). The space under each access block is open.
- It sets `$7ED908 + area` = $FF. Closing message $14 ("map data access completed") **opens the pause map by itself** (vanilla, C $85 `message_box_index == 20`).
- In the pause menu a 2-frame tap of START is ignored; 10 frames works.

### SRAM keeps only some explored bytes

- Saving packs the explored map (C `PackMapToSave` $81:834B / `UnpackMapFromSave` $81:82E4). Only the byte offsets listed per area are kept:
  - counts (bytes) at $81:8131: 74, 72, 76, **18**, 66, 21;
  - packed offsets (words) at $81:8138;
  - lists at the $81 pointers in $81:82D6 (area 3's has room for 32 bytes).
- **A new map for an area must update that area's list**, or explored rooms vanish after loading.
- The save buffer for the packed map is fixed, not the sum of the vanilla counts: $7ED91C-$7EDE1B = 0x500 = **1280 bytes**,
  saved and loaded whole; vanilla uses 327 (starts 0, 74, 146, 222, 240, 306), the other **953 are free**.
  The count is a 16-bit loop counter: 0 would loop 65536 times (valid 1-255).
- The demake gives each remade area its own block after the 327 vanilla bytes, in area order, and takes
  nothing from other areas: area 3 = 30 bytes at +327 (counts 74, 72, 76, 30, 66, 21; starts 0, 74, 146, 327,
  240, 306). Lists stay in their vanilla place while they fit (area 0 up to 80 bytes, area 5 up to 21);
  rules and checks in `tools/frigate/mapsave.py`.

### Grey floor and ceiling doors

- An unlocked grey door turns into the blue door under it, as in vanilla.
- A blue cap in a floor or ceiling has to be shot from mid-air (jump, hold down or up, shoot).

---

## 13. Enemy VRAM, Ceres Ridley and the gunship

Verified in the emulator (tests `fuga_ridley_nave_e_final`, `nave_fechada_antes_do_chefe`) and in the C port.

### Enemy VRAM and the escape timer

- Enemy tiles load from VRAM word **$7000** up to $7FFF ($2000 bytes), one species after the other (C `LoadEnemyGfxToVram` $82:DFD1). Ceres Ridley ($A0:E13F) alone takes $2000; the gunship takes $1200 (top $1000 + bottom $200).
- The escape timer digits are sprites with tiles at **$7E00** ($200 bytes) and **$7F00** ($120), from $B0:C000/$B0:C200 (Mother Brain's list $A6:C4CB). Nothing reloads them: an enemy set that reaches $7E00 draws the timer with its own tiles. Ridley's spritemaps use tiles up to $1EE (OBJ tiles, base $6000), so his set can't be shortened.
- Timer RAM: status $0943 (low byte = step; 6 = counting in place), x $0948, y $094A (high byte = screen y; in place = $3000). It is drawn every frame while status ≠ 0 (C `Samus_Func3`).

### Ceres Ridley ($A0:E13F, code in $A6)

- Init $A6:A0F5 starts with `boss_bits[area] & 1 → delete myself`; the rest starts at **$A6:A10E** (PHB). Outside area 2 it takes the Ceres branch: x=186, y=169, stops the music, palette line 15 black, baby Metroid ilist at $7E7806 (bit 15 clear = not drawn).
- State machine in `cry_var_A` ($0FA8 for enemy 0), timer `cry_var_F` ($0FB2): $A35B wait for the door → $A377 wait 512 frames → $A389 eyes light up → $A3DF fade-in from the table $A6:E30A (16 steps × colours 1-11 of lines 9 and 15) → $A455/$A478 roar (ilist $E91D) → $A354 idle. The roar's instruction $A6:E969 (processed after the main) sets $A6AF (take-off, the fight). $A971 = getaway flight to (192,−128); when y < −128 → $A9A0, then $A9A0/$AA11 start the mode-7 cutscene.
- Main $A6:A288 (`LDA #$7FFF; STA $0F8C; PEA; JMP ($0FA8)`), ends in RTL.
- Properties $0F86: $0400 intangible, $0200 deleted, $0100 invisible. `enemy_gfx_drawn_hook` $7E178C (24-bit); LoadEnemies resets it to $A0:804C.
- Body palette = species palette $A6:E14F (colours 1-8 skin, 9-11 membranes, 12-14 eyes, animated from $A6:E2AA).

### Gunship ($A0:D07F top, $A0:D0BF bottom; code in $A2)

- Population (Landing Site $A1:883D): top, bottom (param 2 = 0), hatch (bottom with param 2 = 1), all at the same (x, y), properties $2400; set $B4:8193 = D07F/0002, D0BF/0007. The code finds the parts at enemy index +$40 and +$80.
- Collision: invisible blocks ($x0FF) under the sprite, Landing Site rows 69-73 around the centre block 72, ground row 77 (`tools/frigate/ending.py` keeps the table). Enemy y = ground·16 − 88.
- `GunshipTop_8` $A2:A9BD: boards when Samus is within ±8 px of the centre, up to 64 px above the top, standing, and presses down. `GunshipTop_12` $A2:AAA2: `LDA #$0E; JSL $808233` (event $0E, Zebes timebomb) → lift-off and ending; otherwise refill and "save?" (saves to load station 0 and sets bit 0 of $7ED8F8, i.e. **Crateria's** station 0, whatever the area).
- Lift-off heights: `GunshipTop_19` rises 2 px/frame until y < $380 ($A2:ACFC), `GunshipTop_20` speeds up until y < $100 ($A2:AD15), then game state $26 → fade → $27 ending and credits (`LDA #$26; STA $0998` at $A2:AD20). In area 3 this hack goes to the Ceres escape instead (§16).
- Helpers that answer in the carry: `CheckBossBitForCurArea` $80:81DC (A = mask), `CheckEventHappened` $80:8233; `SetBossBitForCurArea` $80:81A6.

## 14. Area-select screen (file-select map, step 6)

Verified by bytes and in the emulator (specs/01-tela-de-continue.md; code `tools/frigate/areaselect.py`).

- Shown on continue after game over and on loading a save (game state 5, `$0727` = 6), not on new game.
- Title and area names are **menu spritemaps**, not tilemap: table of 104 $82 pointers at `$82:C569`;
  the title is the id stored at `$82:C749` (`$38`), area n's name is `$38 + 1 + n` (drawn only if
  `$7ED8F8 + 2·n` ≠ 0). Spritemap = count (16 bits) + 5 bytes per piece: x (16 bits, 9 used), y (s8),
  attribute (tile | palette<<9 | `$3000` priority). Name positions: table `$81:AA1C` (x, y per area).
- Menu sprite tiles: `$B6:C000`, `$2000` bytes, uncompressed (also used by the pause menu). Small
  letters A–Z = tiles 106–131; big letters (8x16) are (top, bottom) pairs listed in `areaselect.BIG`;
  vanilla has no big O/Q. Tiles 15 and 23 are unused by every menu spritemap; this hack puts the big O there.
- Sprites built this frame are in WRAM `$7E0370` (x, y, tile, attribute high byte; 4 bytes each), in
  spritemap order: title first, then the area names. Tests read it (`snesrun` can also check VRAM
  now: `expectvram`, §15).

## 15. Library background of the hangar (starfield)

Verified by bytes and in the emulator (specs/04-visual-hangar.md; code `tools/frigate/space.py`).

- Vanilla WS background `$8F:E117`: `0004 $BA:8DE7 → $7E:4000` (decompress), `0002 $7E:4000 → VRAM
  $4800, $800 bytes`, `0002 $7E:4000 → VRAM $4C00, $800 bytes`, `0000`. Only the BG2 tilemap changes.
  Command `0002` = DMA: src24, VRAM word address, size in bytes. The DMA source wraps inside its
  bank, so the payloads must not cross one (`LinearAllocator.put_in_bank` in `tools/build.py`).
- Tileset 4 graphics `$BB:AE9E` decompress to **$4800 bytes = tiles $000–$23F**; CRE starts at tile
  $280 (§8). Tiles **$240–$27F** (VRAM word $2400–$27FF) are unused by the frigate rooms; the build
  fails if the tileset graphics ever grow into them.
- State layer-2 word `$2121` = library background (bit 0) + parallax $20/256 on both axes.
- The background is reloaded on every room entry, after the pause menu and after the X-ray
  (test `hangar_ceu_estrelado`); the Air Lock keeps the WS map at VRAM $4800.
- Tileset 4 metatile priority (table `$C1:C5CF`, `$7E:A800` = metatiles $100+): back-wall pieces
  $2D0/$2D1/$2EF/$2F0/$2DB have no priority bit (Samus stays in front); $11F and the ceiling
  lights $115–$117 have it (they would cover Samus as background; the build refuses priority
  metatiles in `props.BACKDROPS`).
- In this build: command list at `$8F:EA7D` (20 bytes), hangar state at `$8F:EA9E`, star tiles at
  `$E0:913A` ($100 bytes) and BG2 map at `$E0:923A` ($1000 bytes); addresses follow the build order
  (they were `$E1:8189`/`$E1:8289` before spec 05 put the cutscene graphic first).

## 16. Ceres escape cutscene as the frigate's ending

Verified by bytes and in the emulator (specs/05-final-da-fragata.md; code `tools/frigate/ending.py`;
tests `fuga_ridley_nave_e_final`, `final_continue_na_landing_site`, `final_reset_no_meio_da_cena`).

- `$A2:AD20` (`GunshipTop_20`, vanilla `A9 26 00`) is now `JSR` to a 16-byte routine in `$A2` free
  space (`$A2:F502` in this build): area 3 → A = `$21`, other areas → `$26`; the `STA $0998` after it
  is vanilla.
- Game state `$21` ($82:8388): gameplay runs while the screen fades; when black it sets
  `$7ED914` (loading game state) = `$22`, `$0998` = `$22`, **saves** (area 3), clears the timer `$0943`
  and the Ceres status `$093F`. State `$22` = cutscene `$8B:C11B` (station in mode 7 exploding among
  asteroids; state `$22` from ~+380 frames after boarding, station seen at +500…+800), then the
  planet (seen at +1190) with its name (seen at +1490), then the
  ship flies down. Then state 6 with `$7ED914 = $22` loads **area 0, load station `$12`** (room `$91F8`
  Landing Site); the ship descends, opens and lets Samus out; `GunshipTop_7` sets `$7ED914 = 5`, load
  station 0, bit 0 of `$7ED8F8` and saves again (~+3140 frames after boarding). Equipment, missiles
  and boss/event bits pass through unchanged (events `$7ED820` stay 0: Crateria is "asleep").
- Loading the save made by state `$21` (power off mid-cutscene, `snesrun reset`): the file select goes
  straight to state `$22` (no area-select screen), the cutscene plays again and Samus lands at the
  Landing Site. Loading after the landing shows the area-select screen on Crateria.
- Planet text: spritemap `$8C:9654` (count + 5 bytes per piece: x word (9 bits), y s8, attribute word);
  vanilla 11 pieces "PLANET ZEBES". Its sprite tiles come from the compressed graphic `$96:EC76`
  (16384 bytes = 512 4bpp tiles; letters P `$8F`, L `$97`, A `$98`, N `$99`, E `$9A`, T `$9B`, Z `$9C`,
  B `$9D`, S `$9E`, colours 1/3 only; tiles `$AC`–`$AE` are empty), loaded by `$8B:C699` through
  `LDA #$9600; STA $48` (`$8B:C6BE`) and `LDA #$EC76; STA $47` (`$8B:C6C3`). This hack draws O/I/V in
  `$AC`–`$AE`, recompresses the graphic into the expanded banks (`$E0:8000`, 4017 bytes) and rewrites
  the spritemap in place with 8 pieces ("TALLON IV").

## 17. Phantoon's body = the Parasite Queen (BG2)

Verified by bytes, C (`vendor/sm/src/sm_a7.c`) and the emulator (specs/06-forma-parasite-queen.md;
code `tools/frigate/queen_art.py`, `queen_draw.py`; validate `check_queen_art`, test
`parasite_queen_forma_nova`).

- The body is BG2, not sprites: a 10x14-tile (80x112 px) tilemap built in WRAM `$7E:2000` (64 bytes
  per row; `Phantoon_Init` `$A7:CDF3` fills it with `$0338` and sets the transfer size to 864 bytes)
  and sent to VRAM word `$4800`. Pixel (40, 40) of the drawing is the enemy position
  (`Phantoon_Main` `$A7:CEA6` sets the BG2 scroll); the flames spawn there.
- 22 "extended tilemap" blocks in `$A7:E0AA`-`$A7:E3D1` (`$FFFE`, then {WRAM address, n, n words},
  `$FFFF`), picked by the extended spritemaps `$A7:DEDD`-`$A7:E010` (8 bytes per entry: x, y,
  block, hitbox list): body `$E0AA` (rows 0-11), eye 3 poses `$E1CE`/`$E202`/`$E236`, iris 9
  directions `$E26A`-`$E30A`, tentacles 3 poses (left `$E31E`.., right `$E34E`.., **always drawn
  together**), mouth 3 poses `$E37E`.. (rows 12-13, animates on its own). Columns 0-1 and 8-9 of
  rows 12-13 are never written.
- Tiles: tileset 4/5 graphics (both point at `$BB:AE9E`) tiles `$110`-`$18F`, palette line 7,
  priority 1. No metatile of tileset 4 and not the WS background `$BA:8DE7` uses them. **Reserved for
  the Queen.** This hack recompresses the tileset graphics with only those tiles changed into the
  expanded banks (one bank, `put_in_bank`) and repoints **only tileset 4**; tileset 5 keeps Phantoon.
  The recompressed graphics load both on door transitions and on loading a save
  (`continue_na_save_station`).
- Hitbox lists (count, then 12 bytes: left, top, right, bottom, touch, shot): `$A7:E020` (empty),
  `$A7:E02E` (5 boxes), `$A7:E06C` (1 box). `Phantoon_Shot` (`$A7:DD9B`) does not care which box was
  hit.
- Body colours: 8 palettes, one per 312 HP (`$A7:DC0F`), pointers `$A7:DC4A` -> `$A7:CB41`..`$CC21`.
  Fade-out goes to black (`$A7:CA41`), fade-in to the HP palette; nothing else reads them.
- The fight is chaotic: any change in the size of the data loaded at the door (e.g. the recompressed
  graphics) changes the boss pattern of a scripted fight, so the emulator test shoots for 200 rounds.

## Checklist: appending a new room

1. **Level data:** build W·H screens of block words, BTS and optional layer 2; prefix the size word; compress (§2); write anywhere (e.g. $E0:8000); point state +0 at it.
2. **In $8F free space:** room header (area, map x/y, W, H, $70, $A0, $00, doorlist ptr) + `E6 E5` + 26-byte state.
3. **Also in $8F:**
   - door-out list (one $83 pointer per door BTS index);
   - scroll bytes (or use $0001);
   - PLM list ending in `00 00`;
   - optional scroll-PLM lists.
4. **In $83:** one 12-byte entry per door; FX = $0000.
5. **In $A1:** enemy population (`FF FF 00` if empty). **In $B4:** enemy set (`FF FF`, optionally preceded by a 7-byte name).
6. **Link it:** point an existing door entry (or a load station's door + room) at the new room.
7. **Save rooms:** the save PLM argument must equal a load-station index in that area whose door leads into the room.
   - Verified in the emulator (tests `save_station_*`): PLM B76F on the **left** block of a 2-block solid pedestal; Samus saves standing on it at `x = (plm_x+1)·16` (trigger needs `(x−8)>>4 == plm_x`, standing pose, on ground). Load-station Samus Y = pedestal top − 24 (vanilla WS save room: $98 with the pedestal top at $B0).
   - The station graphics are drawn by the PLM itself; no level tiles needed.
   - A save writes `$078B` = station and sets bit `station` of `$7ED8F8 + 2·area`.
   - Vanilla WS save room $CE8A puts the save PLM only in its E629 (boss dead) state: putting the PLM in one state only is how to switch a station on or off.
   - Samus dies from `health ≤ 0` checked every gameplay frame ($82:DB69), but not while a message box is open.
