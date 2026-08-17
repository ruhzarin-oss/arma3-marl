import re, sys
"""CRITERES de l en-tete de jambes2.sqf, ecrits avant : grandeur = metres en 3,28 s ;
   statistique = MEDIANE par condition ; n minimum = 8 par condition."""
L = [l for l in open("/mnt/data/harmattan-sandbox/logs/serverJ2.out", errors="ignore") if "HMT|J2|lieu|" in l]
D = {}
for l in L:
    d = dict(zip(*[iter([x.strip().strip('"') for x in l[l.index("HMT|J2|"):].split("|")][2:])]*2))
    D.setdefault((d["lieu"], d["comp"]), []).append(float(d["m"]))
med = lambda v: sorted(v)[len(v)//2]
print(f"\n  ── BANC DES JAMBES II — {len(L)} essais ──\n")
print("  lieu      comportement   n   mediane   min-max        (reference gymnase : 19,7 m)")
for k in sorted(D):
    v = D[k]
    print(f"  {k[0]:9s} {k[1]:12s} {len(v):2d}   {med(v):6.1f} m   {min(v):.1f} - {max(v):.1f}")
if len(D) < 4 or min(len(v) for v in D.values()) < 8:
    print("\n  ⛔ n INSUFFISANT sur au moins une condition — le critere NE SE LIT PAS."); sys.exit(2)
g = lambda l, c: med(D[(l, c)])
lieu_aware  = g("recu","AWARE")  - g("hasard","AWARE")
lieu_combat = g("recu","COMBAT") - g("hasard","COMBAT")
mode_recu   = g("recu","AWARE")  - g("recu","COMBAT")
mode_hasard = g("hasard","AWARE")- g("hasard","COMBAT")
print(f"\n  effet du LIEU   : {lieu_aware:+.1f} m en AWARE, {lieu_combat:+.1f} m en COMBAT")
print(f"  effet du MODE   : {mode_recu:+.1f} m sur lieu recu, {mode_hasard:+.1f} m sur lieu hasard")
seuil = 3.0
L_ok = lieu_aware > seuil and lieu_combat > seuil
M_ok = mode_recu > seuil and mode_hasard > seuil
print(f"\n  ── LE VERDICT, SUR LES CRITERES ECRITS AVANT ──")
if L_ok and M_ok:  print("  ➤ LES DEUX EXPLIQUENT — le 62 % melangeait bien lieu ET comportement.")
elif L_ok:         print("  ➤ LE LIEU EXPLIQUE, pas le mode. Le 62 % etait une mesure de TERRAIN.")
elif M_ok:         print("  ➤ LE MODE EXPLIQUE, pas le lieu. Le 62 % etait une mesure de COMPORTEMENT.")
else:              print("  ➤ AUCUN N EXPLIQUE — le 62 % tient tel quel, et le corps est bien limite.")
print(f"\n  meilleure condition : {max(D, key=lambda k: med(D[k]))} a {max(med(v) for v in D.values()):.1f} m")
print(f"  → soit {100*max(med(v) for v in D.values())/19.7:.0f} % de ce que le gymnase suppose")
