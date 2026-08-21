import sys, re, subprocess, importlib.util
from pathlib import Path
HERE = Path("/home/user/test/halstead")
sys.path.insert(0, str(HERE))
import prose_grade as pg
print(f"{'file':<22}{'words':>7}{'fk':>7}{'wps':>7}{'spw':>7}{'l7%':>6}{'neg%':>6}{'spkn':>6}")
for p in sys.argv[1:]:
    t = Path(p).read_text()
    m = pg.measure(t)
    spw = (m['fk'] + 15.59 - 0.39*m['wps'])/11.8
    spoken = ''
    r = subprocess.run([sys.executable, str(HERE/"grade.py"), "--one", p], capture_output=True, text=True, cwd=str(HERE))
    mm = re.search(r"mean spoken sentence, words\s+([\d.]+)", r.stdout)
    if mm: spoken = mm.group(1)
    print(f"{Path(p).name:<22}{m['_words']:>7.0f}{m['fk']:>7.2f}{m['wps']:>7.2f}{spw:>7.3f}{m['long7']:>6.1f}{m['negative']:>6.2f}{spoken:>6}")
