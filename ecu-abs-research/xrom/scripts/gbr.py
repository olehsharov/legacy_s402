import sys,struct
r=open(sys.argv[1],'rb').read()[:0x100000]
T=int(sys.argv[2],16)
W=lambda a: struct.unpack('>H',r[a:a+2])[0]
L=lambda a: struct.unpack('>I',r[a:a+4])[0]
gbr=None
for pc in range(0,0x80000,2):
    i=W(pc)
    if (i&0xF0FF)==0x401E:
        # find preceding mov.l to that reg
        n=(i>>8)&15
        for q in range(pc-2,pc-12,-2):
            j=W(q)
            if j>>12==0xD and ((j>>8)&15)==n: gbr=L((q&~3)+4+(j&0xFF)*4); gs=pc; break
    if (i>>8) in (0xC0,0xC4) and gbr is not None and gbr+(i&0xFF)==T and pc-gs<0x400: print('store',hex(pc),'gbr',hex(gbr),'set at',hex(gs))
