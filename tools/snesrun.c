// Headless SNES runner built on LakeSnes, used to test ROMs without a window.
//
// Usage: snesrun <rom.sfc> <script.txt>
// Build (from the project root):
//   cc -O2 -o tools/snesrun tools/snesrun.c vendor/LakeSnes/snes/*.c -Ivendor/LakeSnes/snes -lz
// Script commands (one per line, '#' starts a comment):
//   wait N                 run N frames with no buttons held
//                          (specs/12m: only the last frame of a wait/hold is drawn: the PPU's pixels are never read by
//                          the game, so the run is the same and a shot sees the same picture, ~2.4x faster)
//   hold BUTTONS N         hold buttons for N frames (e.g. "hold R+B 30")
//                          buttons: B Y SELECT START UP DOWN LEFT RIGHT A X L R
//   shot FILE.png          save the current frame (256x224) as PNG
//   peek ADDR LEN          print LEN bytes of WRAM starting at ADDR (hex, 7E0000-7FFFFF)
//   peekw ADDR             print a little-endian 16-bit word of WRAM
//   poke ADDR VAL          write one byte to WRAM
//   save FILE / load FILE  savestates
//   reset                  power off and on: WRAM cleared, SRAM (battery-backed) kept
//   expect ADDR VAL        16-bit WRAM check; prints FAIL and exits 2 if different
//   expectbit ADDR MASK    WRAM byte check: (byte & MASK) must be non-zero
//   expectvram ADDR FILE   VRAM from word address ADDR (hex) must equal FILE's bytes (little-endian
//                          words); prints FAIL with the first differing word otherwise
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#include "snes.h"

static uint8_t frame_rgba[512 * 480 * 4];

static int button_index(const char* name) {
  static const char* names[] = {"B", "Y", "SELECT", "START", "UP", "DOWN", "LEFT", "RIGHT", "A", "X", "L", "R"};
  for(int i = 0; i < 12; i++) if(strcmp(names[i], name) == 0) return i;
  return -1;
}

static void put_be32(uint8_t* p, uint32_t v) {
  p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v;
}

static void write_chunk(FILE* f, const char* type, const uint8_t* data, uint32_t len) {
  uint8_t hdr[8];
  put_be32(hdr, len);
  memcpy(hdr + 4, type, 4);
  fwrite(hdr, 1, 8, f);
  if(len) fwrite(data, 1, len, f);
  uint32_t crc = crc32(0, (const uint8_t*) type, 4);
  if(len) crc = crc32(crc, data, len);
  uint8_t c[4];
  put_be32(c, crc);
  fwrite(c, 1, 4, f);
}

static int save_png(Snes* snes, const char* path) {
  const int w = 256, h = 224;
  snes_setPixels(snes, frame_rgba);
  size_t raw_len = (size_t) h * (1 + w * 3);
  uint8_t* raw = malloc(raw_len);
  for(int y = 0; y < h; y++) {
    uint8_t* row = raw + y * (1 + w * 3);
    row[0] = 0;
    const uint8_t* src = frame_rgba + (size_t) (y * 2 + 16) * 2048;
    for(int x = 0; x < w; x++) {
      // BGRX output: byte 0 unused, then B, G, R (second half of the hi-res pair)
      const uint8_t* px = src + x * 8 + 4;
      row[1 + x * 3 + 0] = px[3];
      row[1 + x * 3 + 1] = px[2];
      row[1 + x * 3 + 2] = px[1];
    }
  }
  uLongf comp_len = compressBound(raw_len);
  uint8_t* comp = malloc(comp_len);
  compress(comp, &comp_len, raw, raw_len);
  FILE* f = fopen(path, "wb");
  if(!f) { free(raw); free(comp); return 0; }
  static const uint8_t sig[8] = {0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'};
  fwrite(sig, 1, 8, f);
  uint8_t ihdr[13];
  put_be32(ihdr, w);
  put_be32(ihdr + 4, h);
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  write_chunk(f, "IHDR", ihdr, 13);
  write_chunk(f, "IDAT", comp, (uint32_t) comp_len);
  write_chunk(f, "IEND", NULL, 0);
  fclose(f);
  free(raw);
  free(comp);
  return 1;
}

static uint8_t* read_file(const char* path, long* len) {
  FILE* f = fopen(path, "rb");
  if(!f) return NULL;
  fseek(f, 0, SEEK_END);
  *len = ftell(f);
  rewind(f);
  uint8_t* buf = malloc(*len);
  if(fread(buf, 1, *len, f) != (size_t) *len) { fclose(f); free(buf); return NULL; }
  fclose(f);
  return buf;
}

static uint32_t wram_index(unsigned long addr) {
  return (uint32_t) ((addr - 0x7e0000) & 0x1ffff);
}

int main(int argc, char** argv) {
  if(argc < 3) {
    fprintf(stderr, "usage: %s rom.sfc script.txt\n", argv[0]);
    return 1;
  }
  long rom_len;
  uint8_t* rom = read_file(argv[1], &rom_len);
  if(!rom) { fprintf(stderr, "cannot read rom %s\n", argv[1]); return 1; }
  Snes* snes = snes_init();
  if(!snes_loadRom(snes, rom, (int) rom_len)) { fprintf(stderr, "rom load failed\n"); return 1; }
  FILE* script = fopen(argv[2], "r");
  if(!script) { fprintf(stderr, "cannot read script %s\n", argv[2]); return 1; }

  char line[512];
  int lineno = 0;
  long frame = 0;
  int failures = 0;
  while(fgets(line, sizeof line, script)) {
    lineno++;
    char* hash = strchr(line, '#');
    if(hash) *hash = 0;
    char cmd[32] = {0}, a[256] = {0}, b[64] = {0};
    int n = sscanf(line, "%31s %255s %63s", cmd, a, b);
    if(n <= 0) continue;
    if(strcmp(cmd, "wait") == 0) {
      int frames = atoi(a);
      for(int i = 0; i < frames; i++, frame++) { snes->ppu->skipRender = i < frames - 1; snes_runFrame(snes); }
      snes->ppu->skipRender = false;
    } else if(strcmp(cmd, "hold") == 0) {
      int frames = atoi(b);
      char tmp[256];
      strcpy(tmp, a);
      for(char* tok = strtok(tmp, "+"); tok; tok = strtok(NULL, "+")) {
        int idx = button_index(tok);
        if(idx < 0) { fprintf(stderr, "line %d: unknown button %s\n", lineno, tok); return 1; }
        snes_setButtonState(snes, 1, idx, true);
      }
      for(int i = 0; i < frames; i++, frame++) { snes->ppu->skipRender = i < frames - 1; snes_runFrame(snes); }
      snes->ppu->skipRender = false;
      for(int i = 0; i < 12; i++) snes_setButtonState(snes, 1, i, false);
    } else if(strcmp(cmd, "shot") == 0) {
      if(!save_png(snes, a)) { fprintf(stderr, "cannot write %s\n", a); return 1; }
      printf("[f%ld] shot %s\n", frame, a);
    } else if(strcmp(cmd, "peek") == 0) {
      unsigned long addr = strtoul(a, NULL, 16);
      int len = atoi(b);
      printf("[f%ld] %06lX:", frame, addr);
      for(int i = 0; i < len; i++) printf(" %02X", snes->ram[wram_index(addr + i)]);
      printf("\n");
    } else if(strcmp(cmd, "peekw") == 0) {
      unsigned long addr = strtoul(a, NULL, 16);
      uint16_t v = snes->ram[wram_index(addr)] | (snes->ram[wram_index(addr + 1)] << 8);
      printf("[f%ld] %06lX = %04X\n", frame, addr, v);
    } else if(strcmp(cmd, "expect") == 0) {
      unsigned long addr = strtoul(a, NULL, 16);
      unsigned long want = strtoul(b, NULL, 16);
      uint16_t v = snes->ram[wram_index(addr)] | (snes->ram[wram_index(addr + 1)] << 8);
      if(v != want) {
        printf("[f%ld] FAIL %06lX = %04X, esperado %04lX (linha %d)\n", frame, addr, v, want, lineno);
        failures++;
      } else {
        printf("[f%ld] ok   %06lX = %04X\n", frame, addr, v);
      }
    } else if(strcmp(cmd, "expectbit") == 0) {
      unsigned long addr = strtoul(a, NULL, 16);
      unsigned long mask = strtoul(b, NULL, 16);
      uint8_t v = snes->ram[wram_index(addr)];
      if(!(v & mask)) {
        printf("[f%ld] FAIL %06lX = %02X, bit %02lX desligado (linha %d)\n", frame, addr, v, mask, lineno);
        failures++;
      } else {
        printf("[f%ld] ok   %06lX = %02X (bit %02lX)\n", frame, addr, v, mask);
      }
    } else if(strcmp(cmd, "expectvram") == 0) {
      unsigned long addr = strtoul(a, NULL, 16);
      long len;
      uint8_t* want = read_file(b, &len);
      if(!want || len % 2 || addr + len / 2 > 0x8000) { fprintf(stderr, "line %d: bad vram file %s\n", lineno, b); return 1; }
      long bad = -1;
      for(long i = 0; i < len / 2 && bad < 0; i++)
        if(snes->ppu->vram[addr + i] != (want[2 * i] | (want[2 * i + 1] << 8))) bad = i;
      if(bad >= 0) {
        printf("[f%ld] FAIL vram %04lX = %04X, esperado %04X (%s, linha %d)\n", frame, addr + bad,
               snes->ppu->vram[addr + bad], want[2 * bad] | (want[2 * bad + 1] << 8), b, lineno);
        failures++;
      } else {
        printf("[f%ld] ok   vram %04lX..%04lX = %s\n", frame, addr, addr + len / 2 - 1, b);
      }
      free(want);
    } else if(strcmp(cmd, "poke") == 0) {
      unsigned long addr = strtoul(a, NULL, 16);
      snes->ram[wram_index(addr)] = (uint8_t) strtoul(b, NULL, 16);
    } else if(strcmp(cmd, "save") == 0) {
      int size = snes_saveState(snes, NULL);
      uint8_t* buf = malloc(size);
      snes_saveState(snes, buf);
      FILE* f = fopen(a, "wb");
      fwrite(buf, 1, size, f);
      fclose(f);
      free(buf);
    } else if(strcmp(cmd, "reset") == 0) {
      snes_reset(snes, true);
      printf("[f%ld] reset\n", frame);
    } else if(strcmp(cmd, "load") == 0) {
      long len;
      uint8_t* buf = read_file(a, &len);
      if(!buf || !snes_loadState(snes, buf, (int) len)) { fprintf(stderr, "line %d: load failed\n", lineno); return 1; }
      free(buf);
    } else {
      fprintf(stderr, "line %d: unknown command %s\n", lineno, cmd);
      return 1;
    }
  }
  return failures ? 2 : 0;
}
