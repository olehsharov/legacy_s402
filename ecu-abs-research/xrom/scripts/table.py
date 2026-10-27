import json,re,collections,csv
xr='<project>/tmp/xrom/'
rows=json.load(open(xr+'rows.json'))
def fname_trans(b):
    b=b.upper()
    if re.search(r'MT-AT|AT-MT',b): return '?'
    if re.search(r'-MT|6MT|5MT',b): return 'MT'
    if re.search(r'-AT|AUTO|CVT',b): return 'AT'
    return '?'
w=csv.writer(open(xr+'rows.csv','w'))
w.writerow(['rom_id','file','def_market','def_model','def_sub','def_trans','name_trans','kind','addr_flag0','byte_flag0','addr_flag1','byte_flag1','selector_addr','selector','neighbours'])
G=collections.defaultdict(list)
for r in rows:
    b=r['file'].split('__')[-1]; d=r['df']
    nt=fname_trans(b)
    if r['kind']=='pair':
        sel=r['sel']
        w.writerow([r['id'],b,d.get('market'),d.get('model'),d.get('sub'),d.get('trans'),nt,'pair',hex(r['a0']),'%02X'%r['v0'],hex(r['a1']),'%02X'%r['v1'],sel[0] if sel else '',sel[1].upper() if sel else '',r['nbr']])
        G[('pair','%02X/%02X'%(r['v0'],r['v1']))].append((r['id'],d.get('model',''),d.get('sub',''),d.get('trans',''),nt,sel[1] if sel else '-'))
    elif r['kind']=='single':
        (a,v),=r['cv'].items()
        w.writerow([r['id'],b,d.get('market'),d.get('model'),d.get('sub'),d.get('trans'),nt,'single',a,'%02X'%v,'','','','',''])
        G[('single','%02X'%v)].append((r['id'],d.get('model',''),d.get('sub',''),d.get('trans',''),nt,'-'))
    else:
        w.writerow([r['id'],b,d.get('market'),d.get('model'),d.get('sub'),d.get('trans'),nt,r['kind']]+['']*7)
        G[(r['kind'],'')].append((r['id'],d.get('model',''),d.get('sub',''),d.get('trans',''),nt,'-'))
for k,v in sorted(G.items()):
    print(k,len(v))
    c=collections.Counter((m,s) for _,m,s,_,_,_ in v); print('   ',dict(c))
    if k[0]=='pair':
        cs=collections.Counter((t or nt, se) for _,_,_,t,nt,se in v); print('   trans/selector:',dict(cs))
    if k[0]=='single':
        print('   ', [(i,t,nt) for i,_,_,t,nt,_ in v])
