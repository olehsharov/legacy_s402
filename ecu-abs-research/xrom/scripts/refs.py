import sys,struct
r=open(sys.argv[1],'rb').read()[:0x100000]
tg=[int(x,16) for x in sys.argv[2:]]
for pc in range(0,0x80000,2):
    i=struct.unpack('>H',r[pc:pc+2])[0]
    if i>>12==0xD:
        a=(pc&~3)+4+(i&0xFF)*4; v=struct.unpack('>I',r[a:a+4])[0]
        if v in tg: print(hex(pc),hex(v))
