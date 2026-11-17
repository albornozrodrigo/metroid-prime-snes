"""LoROM address helpers and a small mutable ROM wrapper."""
from __future__ import annotations

from pathlib import Path


def snes_to_pc(addr: int) -> int:
    """LoROM: bank $80-$FF, offset $8000-$FFFF -> file offset (unheadered)."""
    bank = (addr >> 16) & 0x7F
    off = addr & 0xFFFF
    if off < 0x8000:
        raise ValueError(f"endereço LoROM inválido: ${addr:06X}")
    return bank * 0x8000 + (off - 0x8000)


def pc_to_snes(pc: int) -> int:
    return 0x800000 | ((pc // 0x8000) << 16) | (0x8000 + pc % 0x8000)


class Rom:
    def __init__(self, data: bytes):
        self.data = bytearray(data)

    @classmethod
    def load(cls, path: str | Path) -> "Rom":
        return cls(Path(path).read_bytes())

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(bytes(self.data))

    # reads -----------------------------------------------------------------
    def u8(self, addr: int) -> int:
        return self.data[snes_to_pc(addr)]

    def u16(self, addr: int) -> int:
        p = snes_to_pc(addr)
        return self.data[p] | (self.data[p + 1] << 8)

    def u24(self, addr: int) -> int:
        p = snes_to_pc(addr)
        return self.data[p] | (self.data[p + 1] << 8) | (self.data[p + 2] << 16)

    def read(self, addr: int, length: int) -> bytes:
        p = snes_to_pc(addr)
        return bytes(self.data[p:p + length])

    # writes ----------------------------------------------------------------
    def write(self, addr: int, payload: bytes) -> None:
        p = snes_to_pc(addr)
        if (addr & 0xFFFF) + len(payload) > 0x10000:
            raise ValueError(f"escrita em ${addr:06X} atravessa o fim do banco")
        self.data[p:p + len(payload)] = payload

    def w16(self, addr: int, value: int) -> None:
        self.write(addr, bytes([value & 0xFF, (value >> 8) & 0xFF]))

    def w24(self, addr: int, value: int) -> None:
        self.write(addr, bytes([value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF]))

    def expand_to(self, size: int) -> None:
        if len(self.data) < size:
            self.data += b"\xFF" * (size - len(self.data))
