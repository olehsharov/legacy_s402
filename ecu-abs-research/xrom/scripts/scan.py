import sys, os, re, struct, json
d = sys.argv[1]
def lit_l(rom, pc, ins):
    disp = ins & 0xFF
    a = (pc & ~3) + 4 + disp*4
    return struct.unpack('>I', rom[a:a+4])[0]
def lit_w(rom, pc, ins):
    a = pc + 4 + (ins & 0xFF)*2
    return struct.unpack('>H', rom[a:a+2])[0]
def w(rom,a): return struct.unpack('>H', rom[a:a+2])[0]
pat = re.compile(rb'\x4F\x22\xD3.\x43\x0B\x00\x09\x64\x0C\x24\x48\x8F\x03\x00\x09\xD3.\xA0\x02\x64\x30\xD1.\x64\x10\xD3.\x4F\x26\x00\x0B\x23\x40', re.S)
out = []
for fn in sorted(os.listdir(d)):
    rom = open(os.path.join(d,fn),'rb').read()
    if len(rom) > 0x100000: rom = rom[:0x100000]
    rid = rom[0x2000:0x2020].split(b'\x00')[0].decode('latin1', 'replace')
    rec = dict(file=fn, id=rid)
    ms = [m.start() for m in pat.finditer(rom) if m.start()%2==0]
    rec['nmatch'] = len(ms)
    if ms:
        f = ms[0]; rec['func'] = f
        getter = lit_l(rom, f+2, w(rom,f+2))
        a0 = lit_l(rom, f+16, w(rom,f+16))
        a1 = lit_l(rom, f+22, w(rom,f+22))
        ram = lit_l(rom, f+26, w(rom,f+26))
        rec.update(getter=getter, cal0=a0, cal1=a1, ram=ram)
        if a0 < len(rom) and a1 < len(rom):
            rec['b0'] = rom[a0]; rec['b1'] = rom[a1]
            base = min(a0,a1) - 2
            rec['nbr'] = rom[base:base+10].hex()
        # getter decode
        gi = w(rom, getter)
        flag = None
        if gi >> 12 == 0xD:
            flag = lit_l(rom, getter, gi)
        rec['flag'] = flag
        # selector: look for 8855 with a mov.l of flag nearby, and AA literal
        sel = []
        if flag is not None:
            for m in re.finditer(rb'\x88\x55', rom):
                p = m.start()
                if p % 2: continue
                lits = {}
                aa = False
                for q in range(p-0x40, p, 2):
                    i = w(rom, q)
                    if i >> 12 == 0xD:
                        lits[q] = (((i>>8)&15), lit_l(rom, q, i))
                    if i >> 12 == 0x9 and lit_w(rom,q,i) == 0xAA: aa = True
                vals = [v for (_,v) in lits.values()]
                if flag in vals and aa:
                    # cal address: literal in cal region followed by mov.b @rN,r4
                    for q,(rn,v) in sorted(lits.items()):
                        if 0x80000 <= v < 0x100000:
                            for q2 in range(q+2, p, 2):
                                i2 = w(rom, q2)
                                if (i2 & 0xF00F) == 0x6000 and ((i2>>4)&15) == rn:
                                    sel.append((p, v, rom[v])); break
        rec['sel'] = sel
    out.append(rec)
json.dump(out, open(sys.argv[2],'w'), indent=0)
print(len(out), sum(1 for r in out if r['nmatch']), sum(1 for r in out if r.get('sel')))
