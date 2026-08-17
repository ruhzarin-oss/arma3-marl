import re, glob
"""MINAGE II — les 34 sessions de la NUIT, un serveur neuf par épisode donc un journal par
   session. SIGNATURES ÉCRITES AVANT :
     · groupement temporel → les mortes se suivent en rafales, longueur de série anormale
     · dérive → le taux de mortes monte ou descend au fil de la nuit
     · rien → le destin est indépendant du temps, et aucune variable gratuite ne reste."""
S = []
for f in sorted(glob.glob("/mnt/data/natif/p1_e*.txt"), key=lambda x: int(re.search(r"e(\d+)", x).group(1))):
    n = int(re.search(r"e(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    if "PREVOL" not in t and "prevol" not in t: continue
    v = ("prevol VERT" in t) or ("HMT|PV|true" in t)
    quoi = "T5" if "T5 IMMOBILE" in t else ("T4" if "T4 " in t else ("T7" if "T7 " in t else ""))
    S.append((n, v, quoi))
if not S: print("  aucun journal exploitable"); raise SystemExit
seq = "".join("V" if v else "M" for _, v, _ in S)
nv = seq.count("V"); nm = seq.count("M")
print(f"\n  sessions de la nuit : {len(S)}   vivantes {nv}   mortes {nm}   taux de mortes {100*nm//len(S)} %")
print(f"\n  séquence chronologique :\n  {seq}")
# séries
ser, cur = [], seq[0]; l = 1
for c in seq[1:]:
    if c == cur: l += 1
    else: ser.append((cur, l)); cur, l = c, 1
ser.append((cur, l))
mx = max((l for c, l in ser if c == "M"), default=0)
print(f"\n  nombre de séries  : {len(ser)}   plus longue série de MORTES : {mx}")
# test des séries (runs test) : sous indépendance, E[runs] = 2*nv*nm/N + 1
N = len(seq); E = 2*nv*nm/N + 1
V = (2*nv*nm*(2*nv*nm - N)) / (N*N*(N-1)) if N > 1 else 0
z = (len(ser) - E) / (V ** 0.5) if V > 0 else 0
print(f"  séries attendues sous INDÉPENDANCE : {E:.1f}   observées : {len(ser)}   z = {z:+.2f}")
print(f"  ➤ {'GROUPEMENT (les mortes se suivent)' if z < -1.96 else ('ALTERNANCE anormale' if z > 1.96 else 'PAS DE GROUPEMENT — le destin est indépendant du temps')}")
# dérive
h1 = seq[:len(seq)//2]; h2 = seq[len(seq)//2:]
print(f"\n  1re moitié : {h1.count('M')}/{len(h1)} mortes    2e moitié : {h2.count('M')}/{len(h2)} mortes")
print(f"  ➤ {'DÉRIVE' if abs(h1.count('M')/len(h1) - h2.count('M')/len(h2)) > 0.3 else 'pas de dérive nette'}")
q = {}
for _, v, w in S:
    if not v: q[w] = q.get(w, 0) + 1
print(f"\n  canal des morts : {q}")
