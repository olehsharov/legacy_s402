#!/usr/bin/env python3
"""Build '(OEM ABS WITH 2 BYTE FIX)' from '(OEM ABS)': set 0xC1AD2 and 0xC1AD3 to 0xA2,
recompute the Subaru checksum-fix diffs (14 triples (start,end,diff) at 0xFFB80, CHECK_TOTAL 0x5AA5A55A).
Read-only on the source; refuses to overwrite the output. Does NOT touch any ECU."""
import struct, hashlib, sys, os
SRC="kramar/JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (OEM ABS).bin"
DST="kramar/JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (OEM ABS WITH 2 BYTE FIX).bin"
TOTAL=0x5AA5A55A; TAB=0xFFB80
def triples(b):
    out=[]
    for i in range(14):
        s,e,d=struct.unpack(">III",b[TAB+12*i:TAB+12*i+12]); out.append((i,s,e,d))
    return out
def calc(b,s,e):
    return (TOTAL-sum(struct.unpack(">%dI"%((e+1-s)//4),b[s:e+1])))&0xFFFFFFFF
def check(b):
    bad=[]
    for i,s,e,d in triples(b):
        if s==0 and e==0: continue
        if calc(b,s,e)!=d: bad.append(i)
    return bad
src=bytearray(open(SRC,"rb").read())
assert len(src)==1048576 and src[0x2000:0x2008]==b"A2UG000B", "unexpected source"
assert src[0xC1AD2:0xC1AD4]==bytes([0x02,0x22]), "source bytes not stock 02 22"
assert check(src)==[], "source checksums not valid"
dst=bytearray(src); dst[0xC1AD2]=0xA2; dst[0xC1AD3]=0xA2
for i,s,e,d in triples(dst):
    if s==0 and e==0: continue
    dst[TAB+12*i+8:TAB+12*i+12]=struct.pack(">I",calc(dst,s,e))
assert check(dst)==[], "output checksums invalid"
if os.path.exists(DST): sys.exit("refusing to overwrite "+DST)
open(DST,"wb").write(dst)
diff=[i for i in range(len(src)) if src[i]!=dst[i]]
print("bytes changed:",len(diff))
for i in diff: print("  0x%05X  %02X -> %02X"%(i,src[i],dst[i]))
print("src sha256",hashlib.sha256(src).hexdigest()); print("dst sha256",hashlib.sha256(dst).hexdigest())
