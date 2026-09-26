"""26/09 ( a7ad896 ) : le benefice des marchands garde le fonds de roulement a l echelle du marche. Idempotent.
   python patch_travail.py chemin/d04_travail.py"""
import sys
p = sys.argv[1]; s = open(p).read()
if 'getattr(m, "echelle", 1.0)' in s: print("deja :", p); sys.exit(0)
a = "        exces = m.caisse - 20000.0\n"
assert s.count(a) == 1, "ligne introuvable"
s = s.replace(a, '        exces = m.caisse - 20000.0 * getattr(m, "echelle", 1.0)     # le fonds de roulement du marche ( moteur, 26/09 )\n')
open(p, "w").write(s); print("corrige :", p)
