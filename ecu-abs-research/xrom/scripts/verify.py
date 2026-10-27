import sys,os,struct,json,re
W=lambda r,a: struct.unpack('>H',r[a:a+2])[0]
L=lambda r,a: struct.unpack('>I',r[a:a+4])[0]
s=json.load(open(sys.argv[2])); d=sys.argv[1]; out={}
for x in s:
    if 'func' not in x: continue
    r=open(os.path.join(d,x['file']),'rb').read()[:0x100000]
    hits=[m.start() for m in re.finditer(rb'\x00\x00\x06\x00\x00.\x08\x00\xff\xff..', r, re.S) if m.start()%4==0]
    if not hits: out[x['file']]='norec'; continue
    B=L(r,hits[0]+8); T=B+5; S=x['ram']
    ok=False; gbr=None; gs=0
    # literal-based: S literal referenced within 0x200 bytes after a B literal
    Bl=[];Sl=[]
    for pc in range(0,0x80000,2):
        i=W(r,pc)
        if i>>12==0xD:
            v=L(r,(pc&~3)+4+(i&0xFF)*4)
            if v in (B,T): Bl.append(pc)
            if v==S: Sl.append(pc)
        if (i&0xF0FF)==0x401E:
            n=(i>>8)&15
            for q in range(pc-2,pc-12,-2):
                j=W(r,q)
                if j>>12==0xD and ((j>>8)&15)==n: gbr=L(r,(q&~3)+4+(j&0xFF)*4); gs=pc; break
        if (i>>8)==0xC0 and gbr is not None and gbr+(i&0xFF)==T and pc-gs<0x600:
            for q in range(pc-8,pc,2):
                j=W(r,q)
                if (j>>8)==0xC4 and gbr+(j&0xFF)==S: ok='gbr'
    if not ok:
        for b in Bl:
            if any(0<=s_-b<0x200 or 0<=b-s_<0x40 for s_ in Sl): ok='lit'
    out[x['file']]=ok
json.dump(out,open(sys.argv[3],'w'))
import collections; print(collections.Counter(out.values()))
for k,v in out.items():
    if not v or v=='norec': print(k,v)
