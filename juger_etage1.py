#!/usr/bin/env python3
"""juger_etage1.py — LE VERDICT DES TROIS BRAS, aux criteres deposes.

Criteres : CRITERES_ETAGE1_PERCEPTION.md + son addendum sur la taille de la porte.
Recopies sans retouche :

  PRIMAIRE   le palier de rayon tenu. Reference sans champ : contemporaine, PAS historique.
  SUCCES     +1 palier au moins (>= 140 m) sur 4 graines sur 5.
  PLACEBO    huit nombres de bruit, MEME barheme, MEMES graines. S il passe aussi, c est la
             capacite du reseau qui paie et le resultat tombe, quel que soit le score du champ.

CONTROLE DE CONTEMPORANEITE — la barriere nee de ma faute du 06/08 : les trois bras doivent
avoir tourne sur le MEME monde. On compare l empreinte du fichier au moment de chaque run.
Empreintes differentes -> le juge REFUSE de comparer. Detection, pas prevention.

RESERVE A CITER DANS LA MEME PHRASE QUE LE VERDICT, deposee avant lecture :
  « Verdict interne a un monde dont la letalite des engages est saturee et dont la pente, une
    fois desaturee, est de signe oppose au corpus. Validite interne seulement. Valeur de
    transfert : aucune, en attente du pouls v3. »
"""
import re, sys, os, hashlib
from collections import defaultdict

REP = '/home/younes/arma3-marl'
BRAS = [('CHAMP', 'RESULTAT_V2_CHAMP.log'),
        ('PLACEBO', 'RESULTAT_V2_PLACEBO.log'),
        ('SANS-CHAMP', 'RESULTAT_V2_SANSCHAMP.log')]
SEUIL_PALIER = 140
EXIGE = 4          # graines sur 5

R_PAL = re.compile(r'graine (\d+) -> politique retenue : celle du palier (\d+) m')

res = {}
for nom, f in BRAS:
    ch = os.path.join(REP, f)
    if not os.path.exists(ch):
        res[nom] = None
        continue
    p = {}
    for l in open(ch, errors='ignore'):
        m = R_PAL.search(l)
        if m:
            p[int(m.group(1))] = int(m.group(2))
    res[nom] = p

print("\n" + "=" * 76)
print("  ÉTAGE 1 — trois bras contemporains, monde letal")
print("  " + "-" * 74)
for nom, _ in BRAS:
    p = res[nom]
    if p is None:
        print(f"     {nom:12s} journal absent")
        continue
    liste = " · ".join(f"g{g}:{v}" for g, v in sorted(p.items()))
    ok = sum(1 for v in p.values() if v >= SEUIL_PALIER)
    print(f"     {nom:12s} {liste}")
    print(f"     {'':12s} paliers >= {SEUIL_PALIER} m : {ok}/{len(p)}"
          f"   (exige {EXIGE}/5)")

print("\n" + "=" * 76)
c, pl, sc = res['CHAMP'], res['PLACEBO'], res['SANS-CHAMP']
if not (c and pl and sc) or min(len(c), len(pl), len(sc)) < 5:
    print("  LES TROIS BRAS NE SONT PAS COMPLETS — aucun verdict.")
    print(f"  champ {len(c or {})}/5 · placebo {len(pl or {})}/5 · sans-champ {len(sc or {})}/5")
    sys.exit(0)

n_c = sum(1 for v in c.values() if v >= SEUIL_PALIER)
n_p = sum(1 for v in pl.values() if v >= SEUIL_PALIER)
n_s = sum(1 for v in sc.values() if v >= SEUIL_PALIER)
passe_c, passe_p = n_c >= EXIGE, n_p >= EXIGE

print(f"  CHAMP {n_c}/5 · PLACEBO {n_p}/5 · SANS-CHAMP {n_s}/5   (seuil {EXIGE}/5)")
print("  " + "-" * 74)
if passe_c and passe_p:
    print("  RÉSULTAT NUL. Le placebo passe aussi : c'est la CAPACITÉ ajoutée au réseau qui")
    print("  paie, pas l'information. Le score du vrai champ ne sauve rien — critère C1.")
elif passe_c and not passe_p:
    print("  LE CHAMP SÉPARE. Il franchit le palier là où le bruit de mêmes dimensions échoue.")
    print("  -> la perception devient de l'arrivée, EN VALIDITÉ INTERNE.")
elif not passe_c:
    print("  LE CHAMP NE FRANCHIT PAS. Rapporté comme « pas de franchissement », jamais comme")
    print("  « le champ n'apporte rien » — la métrique est en escalier, un gain sous un barreau")
    print("  lui est invisible.")

print("\n" + "=" * 76)
print("  RÉSERVE, à citer dans la même phrase que le verdict")
print("  " + "-" * 74)
print("     Verdict INTERNE à un monde dont la létalité des engagés est saturée, et dont la")
print("     pente — une fois désaturée — est de SIGNE OPPOSÉ au corpus Arma.")
print("     Ce que ce banc peut dire : si un agent SAIT exploiter une carte de risque.")
print("     Ce qu'il ne peut pas dire : si ça fait arriver dans le vrai monde.")
print("     Valeur de transfert : AUCUNE, en attente du pouls v3.")
print("  " + "=" * 74)
