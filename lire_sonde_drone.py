#!/usr/bin/env python3
"""lire_sonde_drone.py — applique les portes DEPOSEES AVANT (CONTROLE_POSITIF_DRONE.md).

Le lecteur ne decide rien : les seuils sont ceux du depot, ecrits avant le lancement.
Il refuse de lire si le montage n est pas assez propre (>4 VOID sur 20).
"""
import re, sys, statistics as st

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/harmattan-sandbox/logs/sonde_drone.out"

# ── seuils du depot, en dur : ils ne se negocient pas apres lecture ──
P1_MIN_TIRS   = 18   # bras B : >=18/20 reps avec au moins un Fired
P1_MED_T1_MAX = 8.0  # bras B : mediane du temps au premier tir <= 8 s
P2_MAX_TIRS   = 2    # bras A0 : <=2/20 reps avec un Fired
COND_A1_DRONE = 18   # bras A1 : >=18/20 reps avec drone knowsAbout >= 1.5
VOID_MAX      = 4

RX = re.compile(
    r"HMT\|DR\|rep\|(\d+)\|bras\|(\w+)\|az\|(-?\d+)\|tirs\|(-?\d+)\|t1\|(-?[\d.]+)\|vue\|([\d.]+)"
    r"\|saitdrone\|([\d.]+)\|saitgrp\|([\d.]+)\|saitcamp\|([\d.]+)\|tirsenn\|(\d+)\|void\|(\d+)"
    r"\|saitgrp0\|([\d.]+)")

rows, fini = [], False
with open(LOG, "r", encoding="utf-8", errors="ignore") as f:
    for ln in f:
        if "HMT|DR|TERMINE" in ln:
            fini = True
        m = RX.search(ln)
        if m:
            rows.append(dict(rep=int(m[1]), bras=m[2], az=int(m[3]), tirs=int(m[4]),
                             t1=float(m[5]), vue=float(m[6]), saitdrone=float(m[7]),
                             saitgrp=float(m[8]), saitcamp=float(m[9]),
                             tirsenn=int(m[10]), void=int(m[11]), saitgrp0=float(m[12])))

if not rows:
    print("aucune ligne HMT|DR — la sonde n a rien ecrit."); sys.exit(2)

voids = {r["rep"] for r in rows if r["void"] == 1}
bons  = [r for r in rows if r["rep"] not in voids and r["bras"] in ("A0", "A1", "B")]
reps_ok = sorted({r["rep"] for r in bons})

print(f"sonde {'TERMINEE' if fini else 'EN COURS'} — {len(reps_ok)} reps lisibles, {len(voids)} VOID")
if voids:
    print(f"  reps VOID (ennemi qui tire, ou aucun azimut avec ligne de vue) : {sorted(voids)}")

def bilan(bras):
    xs = [r for r in bons if r["bras"] == bras]
    if not xs:
        return None
    tire = [r for r in xs if r["tirs"] > 0]
    t1s  = [r["t1"] for r in tire if r["t1"] >= 0]
    return dict(n=len(xs), ntire=len(tire), part=len(tire) / len(xs),
                med_t1=st.median(t1s) if t1s else None,
                med_saitgrp=st.median([r["saitgrp"] for r in xs]),
                med_saitcamp=st.median([r["saitcamp"] for r in xs]),
                med_saitdrone=st.median([r["saitdrone"] for r in xs]),
                ndrone=len([r for r in xs if r["saitdrone"] >= 1.5]),
                navant=len([r for r in xs if r["saitgrp0"] >= 1.5]))

B = {b: bilan(b) for b in ("A0", "A1", "B")}
print("\nbras   reps  ont tire   part    med t1    saitgrp  saitcamp  saitdrone")
for b in ("A0", "A1", "B"):
    x = B[b]
    if not x:
        print(f"{b:5s}  — pas de ligne"); continue
    t1 = f"{x['med_t1']:6.1f}s" if x["med_t1"] is not None else "     —"
    print(f"{b:5s}  {x['n']:4d}  {x['ntire']:8d}  {100*x['part']:5.1f}%  {t1}   "
          f"{x['med_saitgrp']:7.2f}  {x['med_saitcamp']:8.2f}  {x['med_saitdrone']:9.2f}")

print("\nreps ou le groupe SAVAIT DEJA a l ouverture de la fenetre (saitgrp0 >= 1.5) :")
for b in ("A0", "A1", "B"):
    if B[b]:
        print(f"   {b:3s} {B[b]['navant']:2d}/{B[b]['n']:2d}")

print("\n── PORTES (seuils deposes avant lancement) ──")
if len(voids) > VOID_MAX:
    print(f"⛔ {len(voids)} VOID > {VOID_MAX} : LE MONTAGE N EST PAS ASSEZ PROPRE, on ne lit pas.")
    sys.exit(1)

p1 = B["B"] and B["B"]["ntire"] >= P1_MIN_TIRS and B["B"]["med_t1"] is not None \
     and B["B"]["med_t1"] <= P1_MED_T1_MAX
p2 = B["A0"] and B["A0"]["ntire"] <= P2_MAX_TIRS
print(f"P1 · le canal existe      (B >= {P1_MIN_TIRS} tirs ET med t1 <= {P1_MED_T1_MAX}s) : "
      f"{'PASSE' if p1 else 'TOMBE'}")
print(f"P2 · aveugle sans lui     (A0 <= {P2_MAX_TIRS} tirs)                     : "
      f"{'PASSE' if p2 else 'TOMBE'}")

if not p1:
    print("\n⛔ `reveal` N EST PAS LE CANAL (ou l escouade ne peut pas tirer).")
    print("   L INSTRUMENT EST MORT. Rien d autre ne se lit aujourd hui — A1 compris.")
    sys.exit(1)
if not p2:
    print("\n⛔ L ESCOUADE VOIT DERRIERE ELLE : l angle mort ne tient pas dans ce montage.")
    print("   La SCENE est mal posee, pas le tuyau. Les trois bras sont sans objet.")
    sys.exit(1)

print("\n── LECTURE DU BRAS A1 (le moteur transmet-il tout seul ?) ──")
if B["A1"]["ndrone"] < COND_A1_DRONE:
    print(f"⚠️  A1 est VOID : le drone ne voit pas ({B['A1']['ndrone']}/{B['A1']['n']} reps a "
          f"knowsAbout >= 1.5, il en fallait {COND_A1_DRONE}).")
    print("   « rien ne fuit » serait une trivialite : rien n est su. Reparer le capteur d abord.")
    sys.exit(0)

a0, a1, b = B["A0"]["part"], B["A1"]["part"], B["B"]["part"]
print(f"part de reps ou l escouade a tire :  A0 {100*a0:.0f}%   A1 {100*a1:.0f}%   B {100*b:.0f}%")
# « proche de » = a moins d un tiers de l ecart A0->B, borne posee avec les seuils
seuil = (b - a0) / 3.0
if a1 - a0 <= seuil:
    print("\n✅ A1 ≈ A0 — le moteur NE transmet PAS tout seul.")
    print("   Le temoin est propre : le tuyau mesure quelque chose, le banc drone peut se batir.")
elif b - a1 <= seuil:
    print("\n⛔ A1 ≈ B — LE MOTEUR TRANSMET DEJA SEUL.")
    print("   La connexion drone-soldat existe sans une ligne de script. Tout banc qui compare")
    print("   avec/sans `reveal` compare une chose a elle-meme. Le tuyau est a jeter, et la")
    print("   question devient « que COUTE le drone », pas « que donne le lien ».")
else:
    print("\n⚠️  INDECIS — A1 est entre les deux. On ne relance pas une 2e sonde le meme jour :")
    print("   l indecision se depose telle quelle.")
