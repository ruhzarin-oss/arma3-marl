"""26/09 ( 06d3d50 ) : une commande publique est UNE demande. Idempotent.   python patch_demande.py chemin/monde.py"""
import sys
p = sys.argv[1]; s = open(p).read()
if "_demande_comptee" in s: print("deja :", p); sys.exit(0)
a = '            m.demande[b] += cmd["quantite"]\n'
assert s.count(a) == 1, "ligne introuvable"
s = s.replace(a, '            if not cmd.get("_demande_comptee"):\n                m.demande[b] += cmd["quantite"]; cmd["_demande_comptee"] = True\n')
open(p, "w").write(s); print("corrige :", p)
