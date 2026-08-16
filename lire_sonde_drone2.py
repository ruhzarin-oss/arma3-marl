#!/usr/bin/env python3
"""lire_sonde_drone2.py — applique les portes DEPOSEES AVANT (CONTROLE_POSITIF_DRONE_2.md).

TENTATIVE N 2. Deux bras (A0, B). Les SEUILS SONT CEUX DE LA TENTATIVE N 1, recopies a
l identique : une reparation touche la scene, jamais la porte.
Nouveaute deposee avant : une repetition n est VALIDE que si le temoin d ouverture est nul
dans les DEUX bras. C est la PREMISSE du bras qu on verifie (l escouade ignore a t0), pas
son resultat — et le plafond de 4 VOID empeche que ca devienne une trappe a donnees.
"""
import re, sys, statistics as st

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/harmattan-sandbox/logs/sonde_drone2_cumul.out"

# ── seuils du depot n 1, INCHANGES ──
P1_MIN_TIRS   = 18
P1_MED_T1_MAX = 8.0
P2_MAX_TIRS   = 2
VOID_MAX      = 4
SEUIL_SAIT    = 1.5      # temoin d ouverture : au-dela, la premisse du bras est fausse

RX = re.compile(
    r"HMT\|DR2\|rep\|(\d+)\|bras\|(\w+)\|az\|(-?\d+)\|tirs\|(-?\d+)\|t1\|(-?[\d.]+)\|vue\|([\d.]+)"
    r"\|saitdrone\|([\d.]+)\|saitgrp\|([\d.]+)\|saitcamp\|([\d.]+)\|tirsenn\|(\d+)\|void\|(\d+)"
    r"\|saitgrp0\|([\d.]+)")

rows, fini = [], False
with open(LOG, "r", encoding="utf-8", errors="ignore") as f:
    for ln in f:
        if "HMT|DR2|TERMINE" in ln:
            fini = True
        m = RX.search(ln)
        if m:
            rows.append(dict(rep=int(m[1]), bras=m[2], az=int(m[3]), tirs=int(m[4]),
                             t1=float(m[5]), vue=float(m[6]), saitgrp=float(m[8]),
                             tirsenn=int(m[10]), void=int(m[11]), saitgrp0=float(m[12])))

if not rows:
    print("aucune ligne HMT|DR2 — la sonde n a rien ecrit."); sys.exit(2)

# ── les VOID, avec LEUR CAUSE : on ne jette jamais en silence ──
void_enn  = {r["rep"] for r in rows if r["tirsenn"] > 0 or r["void"] == 1}
void_sait = {r["rep"] for r in rows if r["saitgrp0"] >= SEUIL_SAIT}
voids = void_enn | void_sait
bons = [r for r in rows if r["rep"] not in voids and r["bras"] in ("A0", "B")]
reps_ok = sorted({r["rep"] for r in bons})

print(f"sonde {'TERMINEE' if fini else 'EN COURS'} — {len(reps_ok)} reps valides, {len(voids)} VOID")
if void_sait:
    print(f"  VOID « savait deja a l ouverture » : {sorted(void_sait)}")
if void_enn:
    print(f"  VOID « ennemi qui tire / azimut introuvable » : {sorted(void_enn)}")

def bilan(bras):
    xs = [r for r in bons if r["bras"] == bras]
    if not xs:
        return None
    tire = [r for r in xs if r["tirs"] > 0]
    t1s = [r["t1"] for r in tire if r["t1"] >= 0]
    return dict(n=len(xs), ntire=len(tire), med_t1=st.median(t1s) if t1s else None,
                med_saitgrp=st.median([r["saitgrp"] for r in xs]))

B = {b: bilan(b) for b in ("A0", "B")}
print("\nbras   reps  ont tire   part    med t1    saitgrp")
for b in ("A0", "B"):
    x = B[b]
    if not x:
        print(f"{b:5s}  — pas de ligne"); continue
    t1 = f"{x['med_t1']:6.1f}s" if x["med_t1"] is not None else "     —"
    print(f"{b:5s}  {x['n']:4d}  {x['ntire']:8d}  {100*x['ntire']/x['n']:5.1f}%  {t1}   {x['med_saitgrp']:7.2f}")

# ── LA PREDICTION DE LA REPARATION, jugee AVANT les portes ──
print("\n── LA REPARATION A-T-ELLE MARCHE ? (predite avant lancement) ──")
n_tot = len({r["rep"] for r in rows})
print(f"predit : temoin d ouverture nul sur 20/20 dans les deux bras."
      f"   observe : {n_tot - len(void_sait)}/{n_tot}")
if len(void_sait) == 0:
    print("✅ la reparation TIENT — l attente de 30 s etait bien la cause.")
else:
    print(f"⚠️  {len(void_sait)} repetition(s) contaminee(s) subsistent : la reparation "
          f"n a PAS entierement pris.")

print("\n── PORTES (seuils de la tentative n 1, recopies a l identique) ──")
if len(voids) > VOID_MAX:
    print(f"⛔ {len(voids)} VOID > {VOID_MAX} : LA REPARATION A ECHOUE, on ne lit pas.")
    print("   (et on ne desserre pas le plafond : ce serait la trappe a donnees)")
    sys.exit(1)

p1 = B["B"] and B["B"]["ntire"] >= P1_MIN_TIRS and B["B"]["med_t1"] is not None \
     and B["B"]["med_t1"] <= P1_MED_T1_MAX
p2 = B["A0"] and B["A0"]["ntire"] <= P2_MAX_TIRS
print(f"P1 · le canal existe   (B >= {P1_MIN_TIRS} tirs ET med t1 <= {P1_MED_T1_MAX}s) : "
      f"{'PASSE' if p1 else 'TOMBE'}")
print(f"P2 · aveugle sans lui  (A0 <= {P2_MAX_TIRS} tirs)                  : "
      f"{'PASSE' if p2 else 'TOMBE'}")

if p1 and p2:
    print("\n✅ L INSTRUMENT EST CERTIFIE.")
    print("   `reveal` fait tirer une escouade qui, sans lui, ne tire pas. Le tuyau est reel,")
    print("   sa latence et son niveau sont des PARAMETRES DE MODELE — pas un mecanisme du")
    print("   monde : le moteur n a aucun canal drone -> IA. Prochaine etape : LA PORTE ORACLE,")
    print("   qui n est PAS dans ce depot.")
    sys.exit(0)

if not p1:
    print("\n⛔ `reveal` N EST PAS LE CANAL. L INSTRUMENT EST MORT.")
if not p2:
    print("\n⛔ P2 TOMBE ALORS QUE LE TEMOIN D OUVERTURE EST PROPRE." if not void_sait else
          "\n⛔ P2 TOMBE.")
    if not void_sait:
        print("   Ce ne sont plus les 30 s d attente : CE SONT LES LIEUX QUI FUIENT.")
        print("   On repare alors la GEOMETRIE — distance, choix des azimuts — jamais le seuil.")
        azf = sorted({r["az"] for r in bons if r["bras"] == "A0" and r["tirs"] > 0})
        print(f"   azimuts fautifs de cette tentative : {azf}")
sys.exit(1)
