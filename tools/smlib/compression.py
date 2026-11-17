"""Super Metroid LZ compression (the format read by the game's decompressor in bank $80).

Each chunk starts with a header byte:
  - 0xFF ends the stream.
  - top 3 bits = command, low 5 bits = length - 1.
  - command 7 means "extended header": the next 3 bits are the real command and the
    length - 1 is 10 bits (low 2 bits of this byte + the next byte).
Commands:
  0 direct copy        : copy the next `length` bytes.
  1 byte fill          : repeat 1 byte `length` times.
  2 word fill          : alternate 2 bytes for `length` bytes.
  3 incrementing fill  : write a byte, then +1 each time.
  4 dictionary copy    : copy from an absolute 16-bit output offset.
  5 inverted dict copy : same as 4, every byte XOR 0xFF.
  6 relative copy      : copy from (output position - 1-byte offset).
  7 inverted relative  : same as 6, every byte XOR 0xFF.
"""
from __future__ import annotations


class CompressionError(ValueError):
    pass


def decompress(data: bytes, start: int = 0) -> tuple[bytes, int]:
    """Decompress from `data[start:]`. Returns (output, number of input bytes consumed)."""
    out = bytearray()
    pos = start
    while True:
        if pos >= len(data):
            raise CompressionError("fim inesperado dos dados comprimidos")
        header = data[pos]
        pos += 1
        if header == 0xFF:
            break
        cmd = header >> 5
        if cmd == 7:
            cmd = (header >> 2) & 7
            length = (((header & 3) << 8) | data[pos]) + 1
            pos += 1
        else:
            length = (header & 0x1F) + 1
        if cmd == 0:
            out += data[pos:pos + length]
            pos += length
        elif cmd == 1:
            out += bytes([data[pos]]) * length
            pos += 1
        elif cmd == 2:
            pair = data[pos:pos + 2]
            pos += 2
            out += (pair * ((length + 1) // 2))[:length]
        elif cmd == 3:
            value = data[pos]
            pos += 1
            out += bytes((value + i) & 0xFF for i in range(length))
        elif cmd in (4, 5):
            src = data[pos] | (data[pos + 1] << 8)
            pos += 2
            for i in range(length):
                b = out[src + i]
                out.append(b ^ 0xFF if cmd == 5 else b)
        else:  # 6 / 7
            src = len(out) - data[pos]
            pos += 1
            if src < 0:
                raise CompressionError("cópia relativa antes do início da saída")
            for i in range(length):
                b = out[src + i]
                out.append(b ^ 0xFF if cmd == 7 else b)
    return bytes(out), pos - start


MAX_LEN = 1024


def _emit(out: bytearray, cmd: int, length: int, payload: bytes) -> None:
    if length <= 32 and cmd != 7:
        out.append((cmd << 5) | (length - 1))
    else:
        n = length - 1
        out.append(0xE0 | (cmd << 2) | (n >> 8))
        out.append(n & 0xFF)
    out += payload


def compress(data: bytes) -> bytes:
    """Greedy compressor: byte/word/incrementing fills and absolute dictionary copies.

    Not optimal, but always produces a stream that `decompress` (and the game) reads back
    to exactly `data`. The output is verified before returning.
    """
    out = bytearray()
    literal = bytearray()
    n = len(data)
    # index of 3-byte sequences -> list of positions, for dictionary matches
    index: dict[bytes, list[int]] = {}

    def flush_literal() -> None:
        while literal:
            chunk = bytes(literal[:MAX_LEN])
            del literal[:MAX_LEN]
            _emit(out, 0, len(chunk), chunk)

    def add_index(p: int) -> None:
        if p + 3 <= n:
            index.setdefault(bytes(data[p:p + 3]), []).append(p)

    i = 0
    while i < n:
        best_len, best = 0, None
        # byte fill
        j = i
        while j < n and j - i < MAX_LEN and data[j] == data[i]:
            j += 1
        if j - i > best_len:
            best_len, best = j - i, (1, bytes([data[i]]))
        # word fill
        if i + 1 < n:
            j = i
            while j < n and j - i < MAX_LEN and data[j] == data[i + ((j - i) & 1)]:
                j += 1
            if j - i > best_len + 1:
                best_len, best = j - i, (2, bytes(data[i:i + 2]))
        # incrementing fill
        j = i + 1
        while j < n and j - i < MAX_LEN and data[j] == (data[j - 1] + 1) & 0xFF:
            j += 1
        if j - i > best_len:
            best_len, best = j - i, (3, bytes([data[i]]))
        # absolute dictionary copy (source must be < 0x10000)
        key = bytes(data[i:i + 3])
        for p in reversed(index.get(key, [])[-64:]):
            if p > 0xFFFF:
                continue
            k = 0
            while i + k < n and k < MAX_LEN and data[p + k] == data[i + k]:
                k += 1
            if k > best_len + 2:
                best_len, best = k, (4, bytes([p & 0xFF, p >> 8]))
        cost_ok = best is not None and (
            (best[0] in (1, 3) and best_len >= 3) or (best[0] == 2 and best_len >= 4) or (best[0] == 4 and best_len >= 4)
        )
        if cost_ok:
            flush_literal()
            _emit(out, best[0], best_len, best[1])
            for p in range(i, i + best_len):
                add_index(p)
            i += best_len
        else:
            literal.append(data[i])
            add_index(i)
            i += 1
    flush_literal()
    out.append(0xFF)
    result = bytes(out)
    check, _ = decompress(result)
    if check != bytes(data):
        raise CompressionError("auto-verificação da compressão falhou")
    return result
