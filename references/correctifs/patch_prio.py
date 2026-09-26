import sys
p = sys.argv[1]; s = open(p).read()
if "PRIORITE_RACHAT" in s: print("deja :", p); sys.exit(0)
a = 'PROTEGES_EXPORT = ESSENTIELS + ("carburant", "petrole")\n'
assert s.count(a) == 1
s = s.replace(a, a + 'PRIORITE_RACHAT = ESSENTIELS + ("carburant",)       # 26/09 : le marche rachete d abord ce qui fait vivre et rouler\n')
a = '''        for b, lots in neg.lots.items():
            if not lots: continue
            nom = cat[b].nom'''
assert s.count(a) == 1, "boucle de rachat introuvable"
s = s.replace(a, '''        for b, lots in sorted(neg.lots.items(), key=lambda kv: cat[kv[0]].nom not in PRIORITE_RACHAT):   # tri stable
            if not lots: continue
            nom = cat[b].nom''')
open(p, "w").write(s); print("corrige :", p)
