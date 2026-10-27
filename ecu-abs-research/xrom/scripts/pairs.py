# find functions that load two adjacent cal-byte addresses X, X+1 via mov.l and mov.b-read them, then store to RAM
import sys,os,struct
d=sys.argv[1]
def w(r,a): return struct.unpack('>H',r[a:a+2])[0]
def L(r,a): return struct.unpack('>I',r[a:a+4])[0]
for fn in sorted(os.listdir(d)):
    if len(sys.argv)>2 and sys.argv[2] not in fn: continue
    r=open(os.path.join(d,fn),'rb').read()[:0x100000]
    loads=[]
    for pc in range(0,0x80000,2):
        i=w(r,pc)
        if i>>12==0xD:
            a=(pc&~3)+4+(i&0xFF)*4
            v=L(r,a)
            if 0x80000<=v<0x100000: loads.append((pc,v))
    res=[]
    for k in range(len(loads)-1):
        for j in range(k+1,min(k+3,len(loads))):
            p1,v1=loads[k]; p2,v2=loads[j]
            if p2-p1<=12 and abs(v2-v1)==1:
                # require a jsr within 16 bytes before p1, and RAM store after
                if any((w(r,q)&0xF0FF)==0x400B for q in range(p1-16,p1,2)):
                    res.append((hex(p1),hex(v1),hex(v2),'%02x %02x'%(r[v1],r[v2])))
    print(fn[:60], r[0x2000:0x2008], res[:4])
