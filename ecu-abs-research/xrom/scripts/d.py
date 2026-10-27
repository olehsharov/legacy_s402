import sys,struct
r=open(sys.argv[1],'rb').read()
def w(a): return struct.unpack('>H',r[a:a+2])[0]
def L(a): return struct.unpack('>I',r[a:a+4])[0]
def dec(pc,i):
    n=(i>>8)&15; m=(i>>4)&15; t=i>>12
    if t==0xD: a=(pc&~3)+4+(i&0xFF)*4; v=L(a); return 'mov.l @%x,r%d ; =%08X%s'%(a,n,v,(' [%02x]'%r[v]) if 0x80000<=v<0x100000 else '')
    if t==0x9: a=pc+4+(i&0xFF)*2; return 'mov.w @%x,r%d ; =%04X'%(a,n,w(a))
    if t==0xE: return 'mov #%d,r%d'%(((i&0xFF)^0x80)-0x80,n)
    if t==0x6: return ['mov.b @r%d,r%d','mov.w @r%d,r%d','mov.l @r%d,r%d','mov r%d,r%d','mov.b @r%d+,r%d','mov.w @r%d+,r%d','mov.l @r%d+,r%d','not r%d,r%d','swap.b','swap.w','negc','neg','extu.b r%d,r%d','extu.w r%d,r%d','exts.b r%d,r%d','exts.w'][i&15]%((m,n) if '%' in ['mov.b @r%d,r%d','mov.w @r%d,r%d','mov.l @r%d,r%d','mov r%d,r%d','mov.b @r%d+,r%d','mov.w @r%d+,r%d','mov.l @r%d+,r%d','not r%d,r%d','swap.b','swap.w','negc','neg','extu.b r%d,r%d','extu.w r%d,r%d','exts.b r%d,r%d','exts.w'][i&15] else ())
    if t==0x2:
        ops=['mov.b r%d,@r%d','mov.w r%d,@r%d','mov.l r%d,@r%d','?','mov.b r%d,@-r%d','mov.w r%d,@-r%d','mov.l r%d,@-r%d','div0s','tst r%d,r%d','and r%d,r%d','xor r%d,r%d','or r%d,r%d','cmp/str','xtrct','mulu','muls']
        o=ops[i&15]; return o%(m,n) if '%' in o else o
    if t==0x3:
        ops=['cmp/eq','?','cmp/hs','cmp/ge','div1','dmulu','cmp/hi','cmp/gt','sub','?','subc','subv','add','dmuls','addc','addv']
        return '%s r%d,r%d'%(ops[i&15],m,n)
    if t==0x8:
        s=(i>>8)&15; d=((i&0xFF)^0x80)-0x80
        if s==0x8: return 'cmp/eq #%d,r0 (0x%02x)'%(d,i&0xFF)
        if s in (9,0xB,0xD,0xF): return '%s %x'%({9:'bt',0xB:'bf',0xD:'bt/s',0xF:'bf/s'}[s],pc+4+d*2)
        if s==4: return 'mov.b @(%d,r%d),r0'%(i&15,m)
        if s==0: return 'mov.b r0,@(%d,r%d)'%(i&15,m)
    if t==0xA: d=i&0xFFF; d=d-0x1000 if d&0x800 else d; return 'bra %x'%(pc+4+d*2)
    if t==0xB: d=i&0xFFF; d=d-0x1000 if d&0x800 else d; return 'bsr %x'%(pc+4+d*2)
    if t==0x4:
        lo=i&0xFF
        return {0x0B:'jsr @r%d',0x2B:'jmp @r%d',0x22:'sts.l pr,@-r%d',0x26:'lds.l @r%d+,pr',0x15:'cmp/pl r%d',0x11:'cmp/pz r%d',0x10:'dt r%d'}.get(lo,'4xxx')%n if lo in (0x0B,0x2B,0x22,0x26,0x15,0x11,0x10) else '4xxx'
    if i==0x000B: return 'rts'
    if i==0x0009: return 'nop'
    if (i&0xF0FF)==0x0029: return 'movt r%d'%n
    if t==0xC: return 'c-op %02x #%d'%(i>>8,i&0xFF)
    if t==0x7: return 'add #%d,r%d'%(((i&0xFF)^0x80)-0x80,n)
    return '?'
a=int(sys.argv[2],16); n=int(sys.argv[3])
for k in range(n):
    pc=a+2*k; i=w(pc); print('%06X %04X  %s'%(pc,i,dec(pc,i)))
