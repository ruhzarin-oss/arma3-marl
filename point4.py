#!/usr/bin/env python3
"""point4 — LA SUPPRESSION EST-ELLE UN NOMBRE VIVANT ?

⟨Fable⟩ « Suppression [8] : lue pendant le controle (3). Allumee si > 0 sur >= 10 % des
observations sous le feu ; toujours a 0 -> retiree de l'entree, on ne traine pas un nombre
inerte. »

Le 03/09 au controle du decor, elle etait a 0 des deux cotes — mais le decor ne tirait
jamais, donc elle etait NON TESTEE, pas inerte. Le defenseur arme tire : 17 agents tues
sur 51 au test precedent. Le nombre peut enfin etre juge.
"""
import re, glob, os, collections

R = sorted(glob.glob("/mnt/c/Users/Younes/hmtech1/*.rpt"), key=os.path.getmtime)[-1]
print(f"rpt : {os.path.basename(R)}\n")

obs = collections.defaultdict(list)
res = {}
defs = set()
for l in open(R, errors="ignore"):
    m = re.search(r"DEFENSEUR (\d+) ", l)
    if m: defs.add(int(m[1]))
    m = re.search(r"\] OBS (\d+) (\d+) ((?:[-\d.]+ ?){9})", l)
    if m:
        v = [float(x) for x in m[3].split()]
        obs[int(m[1])].append(v)
    m = re.search(r"\] RESULT (\d+) (\d+) [\d.]+ [\d.]+ (\d+) ", l)
    if m and int(m[1]) not in res: res[int(m[1])] = int(m[3])

com = [u for u in obs if u in defs and u in res]
print(f"{len(com)} episodes avec defenseur arme")
tous = [v for u in com for v in obs[u]]
sup = [v[8] for v in tous]
nz = [x for x in sup if x > 0]
print(f"  {len(tous)} observations  ·  suppression > 0 sur {len(nz)}  ({100*len(nz)/len(tous):.1f} %)")
if nz: print(f"  valeurs non nulles : min {min(nz):.3f}  max {max(nz):.3f}")

morts = [u for u in com if res[u] == 0]
o_morts = [v for u in morts for v in obs[u]]
nzm = [v[8] for v in o_morts if v[8] > 0]
print(f"\n  chez les {len(morts)} agents TUES : {len(o_morts)} observations, "
      f"suppression > 0 sur {len(nzm)} ({100*len(nzm)/len(o_morts) if o_morts else 0:.1f} %)")

print("\n=== VERDICT POINT 4 ===")
part = 100*len(nz)/len(tous) if tous else 0
if part >= 10:
    print(f"  ✅ VIVANTE : {part:.1f} % des observations, seuil 10 %. Elle reste dans l'entree.")
else:
    print(f"  ⛔ INERTE : {part:.1f} % des observations, seuil 10 %.")
    print("     A RETIRER de l'entree — on ne traine pas un nombre qui ne dit rien.")
    print("     ⚠️ Nuance : la mediane de survie des tues etait de 4 s, soit 1 cycle de geste.")
    print("        Un agent abattu en 4 s n'a peut-etre jamais eu le temps d'etre SUPPRIME")
    print("        avant d'etre tue. Le nombre peut etre vivant et le banc trop rapide.")
