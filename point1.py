#!/usr/bin/env python3
"""point1 — LE DECLIN : geste EMIS contre geste EXECUTE, sur les episodes immobiles.

⟨Fable⟩ « Sur les 9 episodes immobiles de la graine 1, mettre cote a cote le geste emis
par la politique et l'ordre recu par la mission. Caps emis mais jamais executes -> le pont
vieillit (pas le serveur). Posture ou ENGAGER repetes -> effondrement sur un geste nul.
Dans les deux cas le dossier est classe ce soir. »

Le monde est prouve stationnaire : 1200 episodes de doctrine a 99,9 %, FPS plats.
"""
import re, glob, os, collections

R = [f for f in glob.glob("/mnt/c/Users/Younes/hmtech2/*.rpt") if "2026-09-02_10-15" in f][0]
print(f"rpt : {os.path.basename(R)}\n")

GESTE = {**{i: f"cap {i*45}deg" for i in range(8)},
         8: "VERS_LE_BUT", 9: "ENGAGER", 10: "DEBOUT", 11: "ACCROUPI", 12: "COUCHE"}

# la sonde de vacance de la graine 1 : 13:07 -> 14:12
res, act = {}, collections.defaultdict(list)
for l in open(R, errors="ignore"):
    if not (len(l) > 8 and l[2] == ":" and l[:2].isdigit()): continue
    if not ("13:" <= l[:3] or "14:0" <= l[:4] or "14:1" <= l[:4]): continue
    if l[:5] < "13:07" or l[:5] > "14:12": continue
    m = re.search(r"\] RESULT (\d+) (\d+) ([\d.]+) ([\d.]+) (\d+) (\d+) (\d+) (\d+)", l)
    if m: res[int(m[1])] = dict(prise=int(m[2]), temps=float(m[3]), dfin=float(m[4]), voids=int(m[7]))
    m = re.search(r"\] ACT (\d+) (\d+) (\d+) ?(\d*)", l)
    if m: act[int(m[1])].append((int(m[3]), m[4]))

immobiles = [u for u, r in res.items() if r["prise"] == 0 and r["voids"] == 0 and r["dfin"] >= 29]
bougeants = [u for u, r in res.items() if r["prise"] == 1]
print(f"{len(res)} episodes  ·  {len(immobiles)} IMMOBILES  ·  {len(bougeants)} pris\n")

print("=== LES EPISODES IMMOBILES : que leur a-t-on demande ? ===")
for u in sorted(immobiles):
    g = act.get(u, [])
    noms = [f"{GESTE.get(x[0], x[0])}{'' if x[1] in ('1','') else '/REFUSE'}" for x in g]
    print(f"  uid {u}  {len(g):2d} gestes : {', '.join(noms) if noms else 'AUCUN GESTE RECU'}")

def profil(lot, nom):
    c = collections.Counter()
    ref = 0; tot = 0
    for u in lot:
        for gid, fait in act.get(u, []):
            c[GESTE.get(gid, gid)] += 1; tot += 1
            if fait == "0": ref += 1
    print(f"\n=== {nom} : {tot} gestes ===")
    for k, v in c.most_common(6): print(f"    {k:14s} {v:4d}  ({100*v/tot:4.1f} %)")
    print(f"    gestes REFUSES par la mission : {ref}  ({100*ref/tot if tot else 0:.1f} %)")

profil(immobiles, "profil des gestes dans les IMMOBILES")
profil(bougeants, "profil des gestes dans les episodes PRIS")
