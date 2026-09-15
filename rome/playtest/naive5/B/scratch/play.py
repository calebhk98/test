import sys, re, os
sys.path.insert(0,'/home/user/test/rome/playtest/naive5/B/scratch')
from drive import run, parse_avail
sess=sys.argv[1]; rounds=int(sys.argv[2]); stepn=sys.argv[3] if len(sys.argv)>3 else '3'
import drive; drive.sess=sess
def R(cmds):
    import subprocess
    p=subprocess.run(['python3','/home/user/test/rome/sim/simulator.py','play','--session',sess],
        input='\n'.join(cmds)+'\n',capture_output=True,text=True,
        cwd='/home/user/test/rome/playtest/naive5/B',timeout=900)
    return p.stdout+p.stderr
for r in range(rounds):
    out=R(['available all','state','money'])
    rows=parse_avail(out)
    m=re.search(r'Capital: ([-\d,\.]+) den',out)
    cap=float(m.group(1).replace(',','')) if m else 0
    yr=re.search(r'YEAR (\d+)',out)
    # pick best value: prefer things that earn, cheap first
    rows.sort(key=lambda d:(-(d['earn']-d['upk'])/max(d['cost'],1), d['cost']))
    budget=cap+ (0 if cap<0 else 0)
    picks=[]; spend=0; hrs=0
    for d in rows:
        if d['earn']-d['upk']<=0: continue
        if spend+d['cost']>max(cap,0)*0.9: continue
        if hrs+d['hours']>1900: continue
        picks.append(d['id']); spend+=d['cost']; hrs+=d['hours']
    cmds=['policy auto_open on']+['start '+p for p in picks]+['step '+stepn,'state','money']
    out2=R(cmds)
    m2=re.search(r'Capital: ([-\d,\.]+) den',out2); cap2=float(m2.group(1).replace(',','')) if m2 else None
    y2=re.search(r'YEAR (\d+)',out2)
    rev=re.search(r'Revenue: ([\d,\.]+) den',out2)
    tech=re.search(r'technologies: ([\d,\.]+) built by you',out2)
    ev=[l.strip() for l in out2.splitlines() if 'EVENT' in l or 'RUIN' in l or 'DEAD' in l][:6]
    print('round',r,'year',y2.group(1) if y2 else '?','cap',cap2,'rev',rev.group(1) if rev else '?',
          'built',tech.group(1) if tech else '?','started',len(picks))
    for e in ev: print('    ',e)
