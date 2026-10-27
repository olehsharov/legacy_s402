#!/usr/bin/env python3
"""Minimal SH-2A (big-endian) disassembler for Renesas SH7058 ROM images.
Uses Capstone 5.x SH backend, and additionally resolves PC-relative literal
pool loads (mov.w/mov.l @(disp,PC), mova) to the constant actually fetched --
which Capstone does not do, and which is essential on SuperH."""
import sys, struct, capstone

import os; ROM = open(os.environ["ROMF"],"rb").read()
MD = capstone.Cs(capstone.CS_ARCH_SH, capstone.CS_MODE_SH2A + capstone.CS_MODE_BIG_ENDIAN)
MD.detail = True

def u16(a): return struct.unpack(">H", ROM[a:a+2])[0]
def u32(a): return struct.unpack(">I", ROM[a:a+4])[0]

def pcrel(addr):
    """If instruction at addr is a PC-relative literal load, return (target_addr, value, kind)."""
    w = u16(addr)
    top = w >> 12
    if top == 0xD:  # mov.l @(disp,PC),Rn
        disp = w & 0xFF
        base = (addr & ~3) + 4
        ta = base + disp*4
        return ta, u32(ta), "L"
    if top == 0x9:  # mov.w @(disp,PC),Rn  (sign-extended 16-bit)
        disp = w & 0xFF
        base = addr + 4
        ta = base + disp*2
        v = u16(ta)
        if v & 0x8000: v -= 0x10000
        return ta, v & 0xffffffff, "W"
    if (w & 0xFF00) == 0xC700:  # mova @(disp,PC),R0
        disp = w & 0xFF
        base = (addr & ~3) + 4
        ta = base + disp*4
        return ta, ta, "A"
    return None

def disasm(start, count):
    a = start
    n = 0
    while n < count:
        code = ROM[a:a+2]
        got = list(MD.disasm(code, a))
        if not got:
            print("%08X  %s   .word 0x%04X   (undecoded)" % (a, code.hex(), u16(a)))
            a += 2; n += 1; continue
        i = got[0]
        ann = ""
        pr = pcrel(a)
        if pr:
            ta, val, kind = pr
            if kind == "A":
                ann = "        ; => R0 = 0x%08X (addr)" % val
            else:
                ann = "        ; = 0x%08X" % (val & 0xffffffff)
                fa = struct.unpack(">f", ROM[ta:ta+4])[0] if kind=="L" else None
                if kind=="L" and (abs(fa) < 1e9) and fa != 0.0:
                    ann += "  (f32=%g)" % fa
                ann += "  [lit@0x%06X]" % ta
        print("%08X  %-6s %-6s %-24s%s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, ann))
        a += i.size; n += 1
    return a

if __name__ == "__main__":
    start = int(sys.argv[1],16) if len(sys.argv)>1 else 0xB68
    count = int(sys.argv[2]) if len(sys.argv)>2 else 40
    disasm(start, count)
