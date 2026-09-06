#!/usr/bin/env python3
"""echecs — POURQUOI LA DOCTRINE RATE, SITE PAR SITE.

Le RPT porte `SITEUSE <uid> <x> <y> <az>` et `RESULT <uid> <prise> ...`. On les joint par
uid : chaque episode rend donc le site EXACT sur lequel il s'est joue et son issue.
C'est ce qui decide s'il faut borner le tirage — et Fable est clair : si la doctrine casse,
on borne LE TIRAGE, on n'excuse pas la doctrine.
"""
import re, sys, json, glob, os

R = sorted(glob.glob("/mnt/c/Users/Younes/hmtech2/*.rpt"), key=os.path.getmtime)[-1]
FIN = sys.argv[1] if len(sys.argv) > 1 else "10:27"

sites, res = {}, {}
for l in open(R, errors="ignore"):
    # ⚠️ les lignes d'en-tete du RPT ne commencent pas par une heure, et "=====" > "10:27"
    # en comparaison de chaines : sans ce test, la boucle s'arretait a la premiere ligne.
    if len(l) > 5 and l[2] == ":" and l[:2].isdigit():
        if l[:5] > FIN: break
    m = re.search(r"SITEUSE (\d+) ([\d.]+) ([\d.]+) (\d+)", l)
    if m and int(m[1]) not in sites: sites[int(m[1])] = (float(m[2]), float(m[3]), int(m[4]))
    m = re.search(r"\] RESULT (\d+) (\d+)", l)
    if m and int(m[1]) not in res: res[int(m[1])] = int(m[2])

pool = {(round(r["x"],2), round(r["y"],2), r["az"]): r
        for r in map(json.loads, open("/home/younes/arma3-marl/sites_jugement.jsonl"))}

joues = [(u, sites[u], res[u]) for u in sorted(res) if u in sites]
print(f"{len(joues)} episodes joints (site + issue)\n")
rates = [(u, s) for u, s, p in joues if p == 0]
pris  = [(u, s) for u, s, p in joues if p == 1]
print(f"  rates : {len(rates)}   pris : {len(pris)}\n")

def car(s):
    r = pool.get((round(s[0],2), round(s[1],2), s[2]))
    return r if r else None

print("  LES ECHECS :")
for u, s in rates:
    r = car(s)
    print(f"    uid {u}  site [{s[0]:.0f},{s[1]:.0f}] az={s[2]:3d}  "
          + (f"score={r['score']:5.2f}  pente={r['pente']*100:+6.1f} %  rugosite={r['dev']:.2f}" if r else "hors bassin ?!"))

pentes_r = [abs(car(s)["pente"]) for u, s in rates if car(s)]
pentes_p = [abs(car(s)["pente"]) for u, s in pris if car(s)]
if pentes_r and pentes_p:
    med_p = sorted(pentes_p)[len(pentes_p)//2]
    print(f"\n  |pente| des echecs : {[f'{x*100:.1f} %' for x in pentes_r]}")
    print(f"  |pente| mediane des reussites : {med_p*100:.1f} %   max des reussites : {max(pentes_p)*100:.1f} %")
    print(f"\n  Les echecs sont-ils dans le haut de la distribution de pente ?")
    for x in pentes_r:
        rang = sum(1 for y in pentes_p if y < x) / len(pentes_p)
        print(f"    pente {x*100:5.1f} %  ->  centile {rang*100:.0f} des reussites")
