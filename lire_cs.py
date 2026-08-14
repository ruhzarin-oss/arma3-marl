import re, pathlib, collections
L = pathlib.Path("/mnt/data/harmattan-sandbox/logs/choix_site.out").read_text(errors="ignore")
R = re.findall(r'HMT\|CS\|PT\|(\d+)\|ox\|(-?\d+)\|oy\|(-?\d+)\|slope\|([\d.eE+-]+)\|dcell\|(\d+)', L)
D = collections.defaultdict(lambda: {"o": None, "s": [], "d": []})
for i, ox, oy, s, d in R:
    e = D[int(i)]; e["o"] = (int(ox), int(oy)); e["s"].append(float(s)); e["d"].append(int(d))
def med(v):
    v = sorted(v); n = len(v); return 0.0 if not n else (v[n//2] if n % 2 else (v[n//2-1]+v[n//2])/2)
C = []
for i, e in D.items():
    if len(e["s"]) < 25: continue
    C.append(dict(i=i, o=e["o"], sl=med(e["s"]),
                  z=100*sum(1 for x in e["s"] if x == 0)/len(e["s"]),
                  dc=med(e["d"])/30,
                  jt=100*sum(1 for x in e["d"] if x >= 16)/len(e["d"])))
print(f"  {len(C)} candidats mesures, 30 points chacun dans le disque de 200 m\n")

GATE = lambda c: 0.20 <= c["sl"] <= 0.60 and c["z"] < 10.0 and c["jt"] < 25.0
S = [c for c in C if GATE(c)]
print("─── LES PORTES DURES ───")
for nom, f in [("mediane slope dans [0,20 ; 0,60]", lambda c: 0.20 <= c["sl"] <= 0.60),
               ("pentes nulles < 10 %",             lambda c: c["z"] < 10.0),
               ("dcover jamais-trouve < 25 %",      lambda c: c["jt"] < 25.0)]:
    n = sum(1 for c in C if f(c)); print(f"  {n:>3}/{len(C)}  {nom}")
print(f"  {len(S):>3}/{len(C)}  LES TROIS ENSEMBLE\n")

print("─── CE QUI FERAIT ECHOUER LA MESURE ───")
if not S:
    print("  ⛔ AUCUN candidat ne passe : Stratis n offre pas de site compatible.")
    print("     C est le monde d ENTRAINEMENT qu il faut rapprocher, pas le site."); raise SystemExit
if len(S) == len(C):
    print("  ⛔ TOUS passent : les portes ne separent rien et ne valent rien."); raise SystemExit
print(f"  ✓ ni zero ni tous : {len(S)} survivants sur {len(C)}. Les portes separent.\n")

# ⚠️ LA REGLE DEPOSEE, PAS UN ARRONDI. Le depot dit « en cas d egalite A 0,01 PRES, le plus
# petit dcover jamais-trouve l emporte ». `round(x, 2)` cree des paniers — il separait 0,004
# de 0,006 alors que le depot les declare EGAUX. Ma premiere sortie designait donc un site
# que la regle ecrite ne designe pas. Corrige ici, sans toucher au depot.
_emin = min(abs(c["sl"] - 0.368) for c in S)
for c in S:
    c["ex"] = abs(c["sl"] - 0.368)
    c["ties"] = (c["ex"] - _emin) <= 0.01          # egalite au sens du depot
# parmi les ex aequo : le plus petit jamais-trouve ; puis le plus petit ecart ; puis l index
S.sort(key=lambda c: (0 if c["ties"] else 1, c["jt"] if c["ties"] else 0.0, c["ex"], c["i"]))
print(f"  ex aequo a 0,01 pres de l ecart minimal ({_emin:.3f}) : {sum(1 for c in S if c['ties'])} candidats")
print("─── LE CLASSEMENT, PAR LA REGLE DEPOSEE ───")
print(f"  {'rang':>4}  {'objectif':>16}  {'med slope':>10}  {'ecart':>7}  {'zeros':>7}  {'dcover':>7}  {'jamais':>7}")
for r, c in enumerate(S[:8], 1):
    print(f"  {r:>4}  ({c['o'][0]:>5}, {c['o'][1]:>5})  {c['sl']:>10.3f}  {abs(c['sl']-0.368):>7.3f}  {c['z']:>6.1f} %  {c['dc']:>7.3f}  {c['jt']:>6.1f} %")
g = S[0]
print(f"\n  ⇒ SITE RETENU : ({g['o'][0]}, {g['o'][1]})")
print(f"     mediane slope {g['sl']:.3f} contre 0,368 au gymnase — ecart {abs(g['sl']-0.368):.3f}")
print(f"     pentes nulles {g['z']:.1f} %   (site actuel : 58,3 %)")
print(f"     dcover mediane {g['dc']:.3f}, jamais-trouve {g['jt']:.1f} %   (site actuel : 0,533 et 78,3 %)")
print(f"\n  RESIDU DECLARE D AVANCE : dcover reste decale (gymnase 0,035). Non corrige ici.")
