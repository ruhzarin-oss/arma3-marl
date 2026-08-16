#!/usr/bin/env python3
"""lire_porte_oracle.py — applique les seuils DEPOSES AVANT (CRITERES_PORTE_ORACLE.md).

Precondition : PRISE(OR) - PRISE(FT) >= 25 points, sinon la porte est SANS OBJET.
Porte        : PRISE(OR) - PRISE(AV), APPARIE par scene, borne inferieure a 95 % > 0.
Le lecteur ne decide rien : les seuils sont ceux du depot, ecrits avant le lancement.
"""
import re, sys, random, statistics as st

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/harmattan-sandbox/logs/porte_oracle_cumul.out"
PRECOND_MIN = 25.0     # points de prise
BOOT_N, SEED = 20000, 20260816

RX = re.compile(
    r"HMT\|PO\|rep\|(\d+)\|bras\|(\w+)\|beta\|(-?\d+)\|cote\|(-?\d+)\|pristenu\|(\d+)\|prise\|(\d+)"
    r"\|tenue\|(\d+)\|gagnes\|(-?\d+)\|expo\|(\d+)\|cout\|(-?[\d.]+)\|vivants\|(\d+)\|defmorts\|(\d+)")

rows, fini = [], False
for ln in open(LOG, encoding="utf-8", errors="ignore"):
    if "HMT|PO|TERMINE" in ln:
        fini = True
    m = RX.search(ln)
    if m:
        rows.append(dict(rep=int(m[1]), bras=m[2], beta=int(m[3]), cote=int(m[4]),
                         pristenu=int(m[5]), prise=int(m[6]), tenue=int(m[7]),
                         gagnes=int(m[8]), expo=int(m[9]), cout=float(m[10]),
                         vivants=int(m[11]), defmorts=int(m[12])))
if not rows:
    print("aucune ligne HMT|PO — la porte n a rien ecrit."); sys.exit(2)

# une repetition ne compte que si ses TROIS bras sont la
par_rep = {}
for r in rows:
    par_rep.setdefault(r["rep"], {})[r["bras"]] = r
complets = sorted(k for k, v in par_rep.items() if {"FT", "AV", "OR"} <= set(v))
print(f"porte {'TERMINEE' if fini else 'EN COURS'} — {len(complets)} repetitions completes")

# ⚠️ le TEMOIN D INSTRUMENT : chaque bras a-t-il pris l axe qu il devait prendre ?
faux = [k for k in complets if par_rep[k]["FT"]["pristenu"] != 1 or par_rep[k]["OR"]["pristenu"] != 0]
if faux:
    print(f"⛔ INSTRUMENT CASSE : {len(faux)} repetitions ou FT ou OR n a pas pris l axe prevu {faux[:6]}")
    sys.exit(1)
part_av = 100 * sum(par_rep[k]["AV"]["pristenu"] for k in complets) / max(1, len(complets))
print(f"temoin du tirage : AVEUGLE a pris l axe tenu dans {part_av:.0f} % des cas (attendu ~50 %)")

def taux(bras, champ="tenue"):
    return 100 * sum(par_rep[k][bras][champ] for k in complets) / max(1, len(complets))

def cout_median(bras):
    xs = [par_rep[k][bras]["cout"] for k in complets if par_rep[k][bras]["cout"] >= 0]
    return st.median(xs) if xs else float("nan")

print("\nbras            prise   tenue   cout (expo/m)   metres gagnes   survivants")
for b, nom in (("FT", "FORCE-TENU"), ("AV", "AVEUGLE   "), ("OR", "ORACLE    ")):
    mg = st.median([par_rep[k][b]["gagnes"] for k in complets])
    sv = st.mean([par_rep[k][b]["vivants"] for k in complets])
    print(f"{nom}    {taux(b,'prise'):5.0f} % {taux(b,'tenue'):6.0f} % {cout_median(b):13.2f} "
          f"{mg:14.0f} {sv:12.2f}")

print("\n── PRECONDITION (le controle positif de cette porte) ──")
ecart_pc = taux("OR") - taux("FT")
print(f"PRISE(ORACLE) - PRISE(FORCE-TENU) = {ecart_pc:+.0f} points   (exige >= {PRECOND_MIN:.0f})")
if ecart_pc < PRECOND_MIN:
    print("\n⛔ LA PORTE EST SANS OBJET : les deux axes ne different pas assez.")
    if taux("OR") > 85 and taux("FT") > 85:
        print("   Les deux bras passent presque toujours : LES DEFENSEURS SONT TROP FAIBLES.")
    elif taux("OR") < 15 and taux("FT") < 15:
        print("   Les deux bras echouent presque toujours : L OBJECTIF EST INJOUABLE.")
    else:
        print("   Les deux bras sont egaux et moyens : LA PLANQUE VOIT LES DEUX AXES.")
    print("   On re-dimensionne le monde, et on NE LIT PAS la porte.")
    sys.exit(1)
print("✅ precondition franchie : il y a bien quelque chose a acheter.")

# ── LA PORTE : difference APPARIEE OR - AV, borne inferieure a 95 % par bootstrap ──
d = [par_rep[k]["OR"]["tenue"] - par_rep[k]["AV"]["tenue"] for k in complets]
moy = 100 * st.mean(d)
random.seed(SEED)
tirs = sorted(100 * st.mean([random.choice(d) for _ in d]) for _ in range(BOOT_N))
b_inf, b_sup = tirs[int(0.025 * BOOT_N)], tirs[int(0.975 * BOOT_N)]

print("\n── LA PORTE (seuil depose avant lancement) ──")
print(f"PRISE(ORACLE) - PRISE(AVEUGLE), apparie : {moy:+.1f} points  IC 95 % [{b_inf:+.1f} ; {b_sup:+.1f}]")
if b_inf > 0:
    print("\n✅ LA PORTE EST FRANCHIE — LE BANC SAIT PAYER L INFORMATION.")
    print("   L information parfaite achete de la prise sur un banc qui contient une decision.")
    print("   Le verdict « le banc refusait l oracle » etait un defaut de BANC, pas du monde.")
    print("   Un banc drone peut desormais se batir : il y a une echelle sur laquelle le mesurer.")
    sys.exit(0)
print("\n⛔ LA PORTE TOMBE ALORS QUE LA PRECONDITION PASSE.")
print("   LE BANC NE SAIT PAS PAYER L INFORMATION, sur un banc qui contient pourtant une")
print("   vraie decision ET un vrai gain a obtenir (precondition a "
      f"{ecart_pc:+.0f} points).")
print("   « Le banc refusait l oracle » cesse d etre un accident de montage : c est un fait")
print("   du monde. Tout banc drone bati la-dessus serait SANS OBJET.")
sys.exit(1)
