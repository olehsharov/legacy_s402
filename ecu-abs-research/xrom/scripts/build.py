import os,re,json,sys
defs={}
root='<project>/RomRaider/definitions'
for dp,dn,fns in os.walk(root):
    for f in fns:
        if not f.lower().endswith('.xml'): continue
        try: s=open(os.path.join(dp,f),errors='replace').read()
        except Exception: continue
        for m in re.finditer(r'<romid>(.*?)</romid>',s,re.S):
            b=m.group(1); g=lambda t: (re.search(r'<%s>(.*?)</%s>'%(t,t),b,re.S) or [None,''])[1].strip()
            x=g('xmlid')
            if x and x not in defs or (x in defs and not defs[x].get('transmission')):
                defs[x]=dict(market=g('market'),model=g('model'),sub=g('submodel'),trans=g('transmission'),year=g('year'),mem=g('memmodel'))
xr='<project>/tmp/xrom/'
s2={x['file']:x for x in json.load(open(xr+'scan2.json'))}
tr={x['file']:x for x in json.load(open(xr+'trace.json'))}
sel=json.load(open(xr+'sel.json'))
rows=[]
for fn in sorted(s2):
    base=fn.split('__')[-1]; rid=re.match(r'([A-Za-z0-9]{8})',base.split('-')[0] if not base.startswith('A2WC50-') else 'A2WC50ZU')
    rid=base[:8].upper()
    x=s2[fn]; t=tr.get(fn,{})
    row=dict(file=fn,id=rid,df=defs.get(rid,{}))
    if 'func' in x:
        row.update(kind='pair',a0=x['cal_flag0'],a1=x['cal_flag1'],v0=x['b_flag0'],v1=x['b_flag1'],nbr=x['nbr'])
        se=[c for c in sel.get(fn,[]) if c[1] in ('55','aa')]
        row['sel']=se[0] if se else None
    elif t.get('calvals'):
        cv={k:v for k,v in t['calvals'].items() if v not in (0x40,0x00)}
        row.update(kind='single',cv=cv)
    elif 'buf' in t and any(q==['imm',0] for q in t.get('src',[])):
        row.update(kind='zero')
    elif 'buf' in t: row.update(kind='unresolved')
    else: row.update(kind='no600')
    rows.append(row)
json.dump(rows,open(xr+'rows.json','w'),indent=0)
import collections; print(collections.Counter(r['kind'] for r in rows))
for r in rows:
    if r['kind'] in ('single','unresolved'): print(r['id'],r['file'].split('__')[-1][:40],r.get('cv'))
