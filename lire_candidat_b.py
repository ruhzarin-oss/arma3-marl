#!/usr/bin/env python3
"""LECTEUR DU CANDIDAT B — compare les trois manoeuvres entre ARMA et le GYMNASE.

Pre-inscription 82101f9 · AMENDEMENT 87e06cf · ANGLE MORT 819354e.
  B1  au moins un observable EMERGENT differe de plus de 30 %
      (les deux ajustes — distance du premier tir, coups par pas — sont publies mais
       NE COMPTENT PAS : ils sont calibres sur Arma, ils ne peuvent pas le juger)
  B2  l ORDRE des trois manoeuvres n est pas le meme des deux cotes

⚠️ Un episode ne compte que s il a eu lieu : prevol VERT, et escouade vivante au depart.
Les episodes « sans escouade » se NOMMENT, ils ne se comptent ni en reussite ni en echec.
"""
import re, os, json, glob, sys

DOS = "/mnt/data/candb"
LOGS = "/mnt/data/logs"
BRAS = ["b_frontale", "b_flanc", "b_arret"]
NOM = {"b_frontale": "frontale", "b_flanc": "flanc", "b_arret": "arret"}
RE_ETAT = re.compile(r"HARMATTAN_ETAT vivants=(\d+) def=(\d+) dmin=(-?\d+)"
                     r"(?: tou=(-?\d+) cda=(-?\d+) cdd=(-?\d+) d1=(-?\d+)(?: hom=(-?\d+))?)?")
RE_SCENE = re.compile(r"HARMATTAN_SCENE def=(\d+) att=(\d+)")

def lire_episode(bras, i):
    f = "%s/%s_e%d.txt" % (DOS, bras, i)
    if not os.path.exists(f): return None
    txt = open(f, errors="ignore").read()
    if "BANC DE MONTAGE TERMINE" not in txt: return None          # episode coupe
    if "prevol VERT" not in txt: return {"ecarte": "prevol non vert"}
    if "ESCOUADE MORTE AVANT LE DEPART" in txt: return {"ecarte": "sans escouade"}
    lg = "%s/serverLV_%se%d.out" % (LOGS, bras, i)
    if not os.path.exists(lg): return {"ecarte": "journal serveur absent"}
    brut = open(lg, errors="ignore").read()
    ms = RE_SCENE.search(brut)
    natt = int(ms.group(2)) if ms else 4
    pas = []
    for m in RE_ETAT.finditer(brut):
        if m.group(8) is None: continue                            # ligne d avant la greffe
        pas.append(dict(viv=int(m.group(1)), tou=int(m.group(4)),
                        cdd=int(m.group(6)), d1=int(m.group(7)), hom=int(m.group(8))))
    if len(pas) < 5: return {"ecarte": "moins de 5 etats lus"}
    hom = sum(p["hom"] for p in pas); vivpas = sum(p["viv"] for p in pas)
    d1 = next((p["d1"] for p in pas if p["d1"] >= 0), -1)
    return dict(touche=100.0 * hom / max(vivpas, 1),
                pertes=natt - pas[-1]["viv"],
                d_premier_tir=d1,
                coups_par_pas=pas[-1]["cdd"] / float(len(pas)),
                n_pas=len(pas))

def moyenne(v, k):
    x = [e[k] for e in v if e.get(k) is not None and e[k] >= 0]
    return (sum(x) / len(x)) if x else float("nan")

arma = {}; ecartes = {}
for b in BRAS:
    ok = []; ec = {}
    for i in range(1, 41):
        r = lire_episode(b, i)
        if r is None: continue
        if "ecarte" in r: ec[r["ecarte"]] = ec.get(r["ecarte"], 0) + 1; continue
        ok.append(r)
    arma[b] = ok; ecartes[b] = ec

print("\n  ══ ARMA — trois manoeuvres ══\n")
print("  %-10s %5s %14s %10s %16s %13s" % ("manoeuvre", "n", "% temps touche", "pertes",
                                            "d 1er tir (m)", "coups/pas"))
A = {}
for b in BRAS:
    v = arma[b]
    if not v:
        print("  %-10s %5d   — aucun episode valide —" % (NOM[b], 0)); continue
    A[NOM[b]] = dict(touche=moyenne(v, "touche"), pertes=moyenne(v, "pertes"),
                     d_premier_tir=moyenne(v, "d_premier_tir"),
                     coups_par_pas=moyenne(v, "coups_par_pas"), n=len(v))
    r = A[NOM[b]]
    print("  %-10s %5d %13.1f %% %10.2f %16.1f %13.2f"
          % (NOM[b], r["n"], r["touche"], r["pertes"], r["d_premier_tir"], r["coups_par_pas"]))
    if ecartes[b]:
        print("             ecartes : %s" % ", ".join("%s x%d" % (k, n) for k, n in ecartes[b].items()))

if len(A) < 3:
    print("\n  ⛔ LES TROIS BRAS NE SONT PAS COMPLETS — aucun verdict.")
    sys.exit(0)

G = json.load(open("/mnt/data/candidat_b_gymnase.json"))["res"]
print("\n  ══ ARMA contre GYMNASE ══\n")
print("  %-10s %-16s %10s %10s %10s   %s" % ("manoeuvre", "observable", "arma", "gymnase", "ecart", ""))
B1 = False
EMERGENT = {"touche": "% temps touche", "pertes": "pertes"}
AJUSTE = {"d_premier_tir": "d 1er tir", "coups_par_pas": "coups/pas"}
for k, lib in list(EMERGENT.items()) + list(AJUSTE.items()):
    for n in ["frontale", "flanc", "arret"]:
        a = A[n][k]; g = G[n][k]
        e = 100.0 * abs(a - g) / max(abs(g), 1e-9)
        tag = "  [B1]" if k in EMERGENT else "  [calibration, ne compte pas]"
        if k in EMERGENT and e > 30.0: B1 = True
        print("  %-10s %-16s %10.2f %10.2f %9.0f %%%s" % (n, lib, a, g, e, tag))

oa_t = sorted(A, key=lambda n: A[n]["touche"]); og_t = sorted(G, key=lambda n: G[n]["touche"])
oa_p = sorted(A, key=lambda n: A[n]["pertes"]); og_p = sorted(G, key=lambda n: G[n]["pertes"])
print("\n  ordre par %% temps touche   arma : %s" % " < ".join(oa_t))
print("                            gymnase : %s" % " < ".join(og_t))
print("  ordre par pertes          arma : %s" % " < ".join(oa_p))
print("                            gymnase : %s" % " < ".join(og_p))
B2 = (oa_t != og_t) or (oa_p != og_p)
print("\n  B1 · un observable EMERGENT differe de plus de 30 %% : %s" % ("PASSE" if B1 else "ECHOUE"))
print("  B2 · l ORDRE des manoeuvres differe                : %s" % ("PASSE" if B2 else "ECHOUE"))
print()
if B1 or B2:
    print("  ➤ CANDIDAT B RETENU : l adversaire du gymnase ne se comporte pas comme l IA d Arma.")
    if B2:
        print("    Et l ORDRE differe — le gymnase enseigne une tactique que le monde ne paie pas.")
    elif B1:
        print("    ⚠️ Mais l ordre CONCORDE : c est un ecart d intensite, pas de classement.")
else:
    print("  ⛔ CANDIDAT B TOMBE. Les deux candidats sont tombes : les 15,4 points restent")
    print("     INEXPLIQUES, et la liste est fermee — on l ecrit, on n en invente pas un troisieme.")
    print("     ⚠️ Rappel de l angle mort declare le 22/08 : B2 avait une puissance FAIBLE.")
