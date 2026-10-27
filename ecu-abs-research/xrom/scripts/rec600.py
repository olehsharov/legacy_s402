import sys,os,re,struct
d=sys.argv[1]
for fn in sorted(os.listdir(d))[:400]:
    rom=open(os.path.join(d,fn),'rb').read()[:0x100000]
    hits=[]
    for m in re.finditer(rb'\x00\x00\x06\x00\x00.\x08\x00\xff\xff..', rom, re.S):
        if m.start()%4==0: hits.append((hex(m.start()), rom[m.start():m.start()+16].hex()))
    print(fn[:55], rom[0x2000:0x2008], hits[:3])
