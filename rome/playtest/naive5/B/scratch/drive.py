import subprocess, re, sys, shutil, os
BASE='/home/user/test/rome/playtest/naive5/B'
SIM='/home/user/test/rome/sim/simulator.py'
sess=sys.argv[1]
def run(cmds):
    p=subprocess.run(['python3',SIM,'play','--session',sess],input='\n'.join(cmds)+'\n',
                     capture_output=True,text=True,cwd=BASE,timeout=600)
    return p.stdout+p.stderr
def parse_avail(out):
    rows=[]
    for line in out.splitlines():
        m=re.match(r'^([a-z0-9_]+)\s{2,}(.+?)\s{2,}([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+(\d+)%\s+([\d,\.]+)\s+([\d,\.]+)',line)
        if m:
            f=lambda s: float(s.replace(',',''))
            rows.append(dict(id=m.group(1),cost=f(m.group(3)),hours=f(m.group(4)),yrs=f(m.group(5)),
                             risk=int(m.group(6)),earn=f(m.group(7)),upk=f(m.group(8))))
    return rows
if __name__=='__main__':
    pass
