"""prevol_gym — LE GYMNASE PASSE ENFIN SON EXAMEN.

⟨Fable, 16/08⟩ « Arma subit six tests avant chaque episode ; le gymnase, zero — et c est
pourtant lui qui fournit le 59,4 %, la reference de tout ton calibrage. Le cote le moins
audite de ta comparaison, c est le gymnase. »

Il a deja eu DEUX pannes de ce cote : un bac sans letalite ou arriver etait inconditionnel,
puis un bac 4x trop letal. Six tests, chacun ne d une panne connue ou d une propriete que
le mecanisme DOIT avoir.
"""
import sys, math, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B, terrain_gpu as TG
from boucle import monde, jouer, cap, frontal, flanc
from porter_boucle import charger
ALIVE, LOS, DC = 4, 7, 6

# ═══ REGLE 18 : chaque porte EXECUTEE sur un cas qui doit passer et un qui doit echouer ═══
PORTES = {
 "G1 letalite non nulle":      (lambda m: 0.01 <= m <= 0.30,  [(0.08, True), (0.0, False), (0.6, False)]),
 "G2 le couvert attenue":      (lambda r: r >= 1.5,           [(3.0, True), (1.0, False)]),
 "G3 expo seulement si vu":    (lambda f: f <= 0.02,          [(0.0, True), (0.4, False)]),
 "G4 les 8 caps deplacent":    (lambda n: n == 8,             [(8, True), (5, False)]),
 "G5 graine = trajectoire":    (lambda d: d < 1e-4,           [(0.0, True), (2.0, False)]),
 "G6 prise dans la bande":     (lambda p: 20 <= p <= 80,      [(59.4, True), (100.0, False), (0.0, False)]),
}
print("─── REGLE 18 : les six portes passent leur propre banc ───")
ok18 = True
for nom, (f, cas) in PORTES.items():
    r = all(f(v) == att for v, att in cas)
    ok18 &= r
    print(f"  {'✓' if r else '⛔'} {nom}")
if not ok18: sys.exit("  ⛔ une porte ne fait pas ce qu elle dit. On ne mesure pas.")
print("  ✓ chaque porte est franchissable ET rejetable.\n")

pol = charger(B.DEV)
def gele(o, t):
    with torch.no_grad(): lo, v = pol(o)
    return lo.argmax(-1), None, None

ec = []
print("─── LES SIX TESTS ───")

# G1 · la letalite existe et n est pas absurde (bac sans letalite / bac 4x trop letal)
e = monde(256, 101); e.reset()
morts, pas = 0, 0
for t in range(60):
    a0 = (e._obs()[..., ALIVE] > 0.5)
    e.step(gele(e._obs(), t)[0], auto_reset=False)
    a1 = (e._obs()[..., ALIVE] > 0.5)
    morts += int((a0 & ~a1).sum()); pas += int(a0.sum())
m = morts / max(pas, 1)
print(f"  G1 letalite non nulle      P(mort/homme-pas) = {m:.4f}   (bande 0,01-0,30)")
if not PORTES["G1 letalite non nulle"][0](m): ec.append(f"G1 letalite {m:.4f} hors bande")

# G2 · le couvert attenue vraiment les degats (le mecanisme dit 1 - 0,7*incover)
e = monde(256, 101); e.reset()
C, M = [], []
for t in range(60):
    inc = TG.sample(e.cover, e.apx, e.apy, e.scale).clamp(max=1.0).reshape(-1).cpu().numpy()
    o0 = e._obs().reshape(-1, 12).cpu().numpy()
    e.step(gele(e._obs(), t)[0], auto_reset=False)
    o1 = e._obs().reshape(-1, 12).cpu().numpy()
    v = (o0[:, ALIVE] > 0.5) & (o0[:, LOS] > 0.5)          # exposes vivants
    C.append((inc > 0.5)[v]); M.append(((o0[:,ALIVE]>0.5)&(o1[:,ALIVE]<=0.5))[v])
C, M = np.concatenate(C), np.concatenate(M)
pc = M[C].mean() if C.sum() else 0.0; pl = M[~C].mean() if (~C).sum() else 0.0
r = pl/pc if pc > 0 else float("inf")
print(f"  G2 le couvert attenue      hors {pl:.4f} / sur {pc:.4f} = x{r:.2f}   (attendu ~3,3 ; porte >= 1,5)")
if not PORTES["G2 le couvert attenue"][0](r): ec.append(f"G2 attenuation x{r:.2f} trop faible")

# G3 · l exposition ne s accumule QUE quand on est vu
# ⚠️ CORRIGE : `exposed = torch.maximum(exposed, ...)` est un MAXIMUM COURANT — le cliquet.
# La version precedente comparait ce max a l instant courant et voyait 27 % d expo « sans
# etre vu » : elle mesurait une PERSISTANCE VOULUE et l appelait une anomalie. On mesure
# donc l INCREMENT : le max ne doit monter QUE quand quelqu un est vu.
e = monde(64, 101); e.reset()
prec = None; hausses_sans_vue = 0; hausses = 0
for t in range(30):
    o = e._obs().reshape(e.N, e.A, 12).cpu().numpy()
    vu = (o[:, :, LOS] > 0.01).any(1)
    _, _, _, info = e.step(gele(e._obs(), t)[0], auto_reset=False)
    ex = info.get("exposed", None)
    if ex is None: continue
    ex = ex.cpu().numpy()
    if prec is not None:
        monte = ex > prec + 1e-6
        hausses += int(monte.sum()); hausses_sans_vue += int((monte & ~vu).sum())
    prec = ex
f = hausses_sans_vue / max(hausses, 1)
print(f"  G3 expo seulement si vu    {f:.4f} des HAUSSES surviennent sans que personne soit vu")
print(f"                             ({hausses_sans_vue} sur {hausses} hausses)   (porte <= 0,02)")
if not PORTES["G3 expo seulement si vu"][0](f): ec.append(f"G3 hausse d expo sans etre vu {f:.4f}")

# G4 · les huit caps deplacent, chacun dans SA direction
e = monde(8, 101); e.reset()
bons = 0
for k in range(8):
    e2 = monde(8, 101); e2.reset()
    p0x, p0y = e2.apx.clone(), e2.apy.clone()
    e2.step(torch.full((e2.N, e2.A), k, dtype=torch.long, device=e2.dev), auto_reset=False)
    dx = (e2.apx - p0x).mean().item(); dy = (e2.apy - p0y).mean().item()
    att = (math.sin(k*math.pi/4), math.cos(k*math.pi/4))
    n = math.hypot(dx, dy)
    if n > 1.0 and (dx/n*att[0] + dy/n*att[1]) > 0.7: bons += 1
print(f"  G4 les 8 caps deplacent    {bons}/8 dans la bonne direction")
if not PORTES["G4 les 8 caps deplacent"][0](bons): ec.append(f"G4 seulement {bons}/8 caps deplacent")

# G5 · graine fixee = trajectoire identique (sans quoi rien n est reproductible)
d = 0.0
for _ in range(2):
    e = monde(16, 101); e.reset()
    for t in range(20): e.step(gele(e._obs(), t)[0], auto_reset=False)
    v = torch.cat([e.apx.flatten(), e.apy.flatten()]).cpu().numpy()
    d = v if isinstance(d, float) else float(np.abs(d - v).max())
print(f"  G5 graine = trajectoire    ecart max {d:.2e}   (porte < 1e-4)")
if not PORTES["G5 graine = trajectoire"][0](d): ec.append(f"G5 non deterministe, ecart {d:.2e}")

# G6 · la prise est dans la bande 20-80 : ni impossible, ni gratuite ⟨regle 2⟩
pr = []
for g in B.GRAINES_TEST:
    st, *_ = jouer(monde(256, g), gele); pr.append(st["prise"])
p = float(np.mean(pr))
print(f"  G6 prise dans la bande     {p:.1f} %   (bande 20-80)")
if not PORTES["G6 prise dans la bande"][0](p): ec.append(f"G6 prise {p:.1f} hors bande")

print(f"\n─── VERDICT DU PREVOL DU GYMNASE ───")
print(("  ✓ VERT — le gymnase passe ses six tests." if not ec
       else "  ⛔ ROUGE\n" + "\n".join("     " + x for x in ec)))
