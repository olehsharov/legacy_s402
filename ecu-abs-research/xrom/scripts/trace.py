import sys,os,re,struct,json
def W(r,a): return struct.unpack('>H',r[a:a+2])[0]
def L(r,a): return struct.unpack('>I',r[a:a+4])[0]
def run(r, start, end, watch, arm=0):
    """linear symbolic exec. watch(pc, kind, base_state, off, val_state) for byte stores"""
    R={}
    pc=start; ind=False; tgt=None; stop=False; steps=0
    while True:
        i=W(r,pc); n=(i>>8)&15; m=(i>>4)&15; t=i>>12
        if t==0xD: R[n]=('lit',L(r,(pc&~3)+4+(i&0xFF)*4))
        elif t==0x9: v=W(r,pc+4+(i&0xFF)*2); R[n]=('imm',v-0x10000 if v&0x8000 else v)
        elif t==0xE: R[n]=('imm',((i&0xFF)^0x80)-0x80)
        elif t==0x6 and (i&15)==0:
            R[n]=('mem',R[m][1]) if R.get(m,('',0))[0]=='lit' else ('?',)
        elif t==0x6 and (i&15) in (3,0xC,0xE): R[n]=R.get(m,('?',))
        elif t==0x6: R[n]=('?',)
        elif t==0x8 and n==4: # mov.b @(d,rm),r0
            R[0]=('mem',R[m][1]+(i&15)) if R.get(m,('',0))[0]=='lit' else ('?',)
        elif t==0x8 and n==0: # mov.b r0,@(d,rm)
            watch(pc,R.get(m,('?',)),i&15,R.get(0,('?',)))
        elif t==0x2 and (i&15)==0: watch(pc,R.get(n,('?',)),0,R.get(m,('?',)))
        elif t==0x2 and (i&15) in (8,): pass
        elif t==0x2: R[n]=R.get(n,('?',)) if (i&15) in (1,2,4,5,6) else ('?',)
        elif t==0x3 and (i&15) in (8,0xC,0xA,0xE,0xB,0xF): R[n]=('?',)
        elif t==0x7: R[n]=('?',) if R.get(n,('',))[0]!='lit' else ('lit',R[n][1]+(((i&0xFF)^0x80)-0x80))
        elif t==0xC and n in (4,):  R[0]=('?',)
        elif t==0xC and n in (9,0xA,0xB): R[0]=('?',)
        elif t==0x4 and (i&0xFF)==0x0B: R={k:v for k,v in R.items() if k>=8}; R[0]=('?',)
        elif (i&0xF0FF)==0x0029: R[n]=('?',)
        if t==0xA and not ind:
            d=i&0xFFF; d=d-0x1000 if d&0x800 else d
            tgt=pc+4+d*2; ind=True; pc+=2; continue
        if (i==0x000B or (i&0xF0FF)==0x402B) and not ind:
            stop=True; ind=True; pc+=2; continue
        if ind:
            ind=False
            if stop:
                if pc<arm: R={}; stop=False; pc+=2; continue
                return
            if tgt is not None: pc=tgt; tgt=None; steps+=1; continue
        pc+=2; steps+=1
        if steps>400: return
def lits(r, vals):
    out=[]
    for pc in range(0,0x80000,2):
        i=W(r,pc)
        if i>>12==0xD:
            v=L(r,(pc&~3)+4+(i&0xFF)*4)
            if v in vals: out.append((pc,v))
    return out
res=[]
d=sys.argv[1]
for fn in sorted(os.listdir(d)):
    r=open(os.path.join(d,fn),'rb').read()[:0x100000]
    rec={'file':fn}
    hits=[m.start() for m in re.finditer(rb'\x00\x00\x06\x00\x00.\x08\x00\xff\xff..', r, re.S) if m.start()%4==0]
    if not hits: res.append(rec); continue
    B=L(r,hits[0]+8); rec['buf']=B
    srcs=set()
    for pc,v in lits(r,{B,B+5}):
        def wt(p,base,off,val):
            if base[0]=='lit' and base[1]+off==B+5: srcs.add(val)
        run(r,pc-0x20,pc+0x200,wt,arm=pc); run(r,pc,pc+0x200,wt)
    rec['src']=[list(s) for s in srcs]
    cals=set()
    for s in srcs:
        if s[0]=='mem' and s[1]>=0xFFFF0000:
            S=s[1]
            for pc,v in lits(r,{S}):
                for q in range(max(0,pc-0x30),pc+0x12,2):
                    i=W(r,q)
                    if i>>12==0xD:
                        v=L(r,(q&~3)+4+(i&0xFF)*4)
                        if 0x80000<=v<0x100000: cals.add(('mem',v))
        if s[0]=='mem' and s[1]<0x100000: cals.add(('mem',s[1]))
    rec['cals']=sorted([list(c) for c in cals],key=str)
    rec['calvals']={hex(c[1]):r[c[1]] for c in cals if c[0]=='mem' and c[1] is not None and c[1]<0x100000}
    res.append(rec)
json.dump(res,open(sys.argv[2],'w'),indent=0)
