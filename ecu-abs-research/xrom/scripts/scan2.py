import sys,os,re,struct,json
W=lambda r,a: struct.unpack('>H',r[a:a+2])[0]
L=lambda r,a: struct.unpack('>I',r[a:a+4])[0]
def lit(r,pc): i=W(r,pc); return L(r,(pc&~3)+4+(i&0xFF)*4)
# word-level pattern; tokens: exact hex or mask
P=[('4F22',0xFFFF),('D000',0xF000),('400B',0xF0FF),('0009',0xFFFF),('600C',0xF00F),('2008',0xF00F),
   ('8B00',0xFB00),('*',0),('D000',0xF000),('A002',0xFFFF),('6000',0xF00F),('D000',0xF000),('6000',0xF00F),
   ('D000',0xF000),('4F26',0xFFFF),('000B',0xFFFF),('2000',0xF00F)]
def match(r,a):
    pos=a; idx={}
    for k,(v,mk) in enumerate(P):
        i=W(r,pos)
        if v=='*':
            if i==0x0009: pos+=2
            continue
        if (i&mk)!=int(v,16): return None
        idx[k]=pos; pos+=2
    return idx
d=sys.argv[1]; out=[]
for fn in sorted(os.listdir(d)):
    r=open(os.path.join(d,fn),'rb').read()[:0x100000]
    rec={'file':fn}
    for a in range(0,0x80000,2):
        if W(r,a)!=0x4F22: continue
        m=match(r,a)
        if not m: continue
        br=W(r,m[6])
        c1=lit(r,m[8]); c2=lit(r,m[11]); ram=lit(r,m[13]); g=lit(r,m[1])
        if not (0x80000<=c1<0x100000 and 0x80000<=c2<0x100000 and ram>=0xFFFF0000): continue
        # which is flag==0 path: fallthrough after bf (branch if r==0? tst sets T if zero; bf taken when nonzero)
        rec.update(func=a, getter=g, cal_flag0=c1, cal_flag1=c2, ram=ram, b_flag0=r[c1], b_flag1=r[c2],
                   brop='%04x'%br, nbr=r[min(c1,c2)-3:min(c1,c2)+9].hex())
        gi=W(r,g)
        if gi>>12==0xD: rec['flag']=lit(r,g)
        rec.setdefault('nfunc',0); rec['nfunc']+=1
    out.append(rec)
json.dump(out,open(sys.argv[2],'w'),indent=0)
print(sum(1 for x in out if 'func' in x))
