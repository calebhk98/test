import sys, re, subprocess
sys.path.insert(0,'/home/user/test/rome/playtest/naive5/B/scratch')
from drive import parse_avail
sess=sys.argv[1]; rounds=int(sys.argv[2]); stepn=sys.argv[3] if len(sys.argv)>3 else '3'
def R(cmds):
    p=subprocess.run(['python3','/home/user/test/rome/sim/simulator.py','play','--session',sess],
        input='\n'.join(cmds)+'\n',capture_output=True,text=True,
        cwd='/home/user/test/rome/playtest/naive5/B',timeout=1200)
    return p.stdout+p.stderr
for r in range(rounds):
    out=R(['available all','money'])
    rows=parse_avail(out)
    m=re.search(r'Capital: ([-\d,\.]+) den',out); cap=float(m.group(1).replace(',','')) if m else 0
    rows.sort(key=lambda d:d['cost'])
    picks=[];spend=0;hrs=0
    for d in rows:
        if spend+d['cost']>max(cap,0)*0.85: continue
        if hrs+d['hours']>1900: continue
        picks.append(d['id']); spend+=d['cost']; hrs+=d['hours']
    cmds=['policy auto_open on','policy auto_train on','policy auto_mine on','policy auto_forest on','policy auto_bribe on']+['start '+p for p in picks]+['step '+stepn,'state','money']
    out2=R(cmds)
    m2=re.search(r'Capital: ([-\d,\.]+) den',out2); cap2=m2.group(1) if m2 else '?'
    y2=re.search(r'YEAR (\d+)',out2); rev=re.search(r'Revenue: ([\d,\.]+) den',out2)
    tech=re.search(r'technologies: ([\d,\.]+) built by you',out2)
    av=re.search(r'AVAILABLE: (\d+) startable',out)
    ev=[l.strip() for l in out2.splitlines() if re.search(r'EVENT|RUIN|DEAD|scandal|SACK|lost',l)][:8]
    print('r%d year %s cap %s rev %s built %s avail %s started %d'%(r,y2.group(1) if y2 else '?',cap2,rev.group(1) if rev else '?',tech.group(1) if tech else '?',av.group(1) if av else '?',len(picks)))
    for e in ev: print('   ',e[:150])
