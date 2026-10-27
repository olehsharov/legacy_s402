import sys,os,struct,json
W=lambda r,a: struct.unpack('>H',r[a:a+2])[0]
L=lambda r,a: struct.unpack('>I',r[a:a+4])[0]
s=json.load(open(sys.argv[2]))
d=sys.argv[1]; res={}
for x in s:
    if 'flag' not in x: continue
    r=open(os.path.join(d,x['file']),'rb').read()[:0x100000]
    F=x['flag']; refs=[]
    # literal refs + GBR refs
    gbr=None
    for pc in range(0,0x80000,2):
        i=W(r,pc)
        if i>>12==0xD and L(r,(pc&~3)+4+(i&0xFF)*4)==F: refs.append(pc)
        if (i&0xF0FF)==0x401E:
            n=(i>>8)&15
            for q in range(pc-2,pc-12,-2):
                j=W(r,q)
                if j>>12==0xD and ((j>>8)&15)==n: gbr=L(r,(q&~3)+4+(j&0xFF)*4); gs=pc; break
        if (i>>8)==0xC0 and gbr is not None and gbr+(i&0xFF)==F and pc-gs<0x600: refs.append(pc)
    cands=set()
    for pc in refs:
        has55=hasAA=False; cal=[]
        for q in range(pc-0x40,pc+0x20,2):
            i=W(r,q)
            if i in (0x8855,) or (i>>12==0xE and i&0xFF==0x55): has55=True
            if i==0x88AA or (i>>12==0xE and i&0xFF==0xAA): hasAA=True
            if i>>12==0x9 and W(r,q+4+(i&0xFF)*2) in (0xAA,0xFFAA): hasAA=True
            if i>>12==0x9 and W(r,q+4+(i&0xFF)*2)==0x55: has55=True
            if i>>12==0xD:
                v=L(r,(q&~3)+4+(i&0xFF)*4)
                if 0x80000<=v<0x100000 and r[v] in (0x55,0xAA,0x00,0xFF): cal.append((hex(v),'%02x'%r[v]))
        if has55 and hasAA: cands.update(cal)
    res[x['file']]=sorted(cands)
json.dump(res,open(sys.argv[3],'w'),indent=0)
