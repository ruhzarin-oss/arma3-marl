#!/usr/bin/env python3
"""chasse_alertes — QUELQU UN A EFFACE UNE ALERTE UNE FOIS. Combien d autres ?

`courbe_toucher_juge.json` porte EXACTEMENT les chiffres de `courbe_toucher.json` avec
`alertes: []`. Le verificateur avait parle ; on l a fait taire, et tous les bancs tournent
dessus depuis. Ce balayage cherche les autres.

Deux signatures :
  · un JSON dont `alertes` est vide alors qu un fichier voisin, mêmes donnees, en portait ;
  · un JSON dont `alertes` est vide mais dont les donnees violent leur propre regle connue.
"""
import json, pathlib, hashlib, sys
from collections import defaultdict

RACINE = pathlib.Path("/home/younes/arma3-marl")
vus, sans_alerte, avec_alerte = defaultdict(list), [], []
for f in list(RACINE.glob("*.json")) + list(RACINE.glob("*/*.json")):
    try:
        c = json.loads(f.read_text())
    except Exception:
        continue
    if not isinstance(c, dict) or "alertes" not in c:
        continue
    # ⚠️ LE PREMIER JET COMPARAIT TOUTES LES CLES et rendait ZERO — y compris sur le seul
    # cas que je CONNAIS. Un chasseur qui rate sa propre proie connue est aveugle : deux
    # fichiers peuvent porter la meme MESURE et differer par une cle annexe. On ne compare
    # donc que la DONNEE, et le controle positif ci-dessous exige que le cas connu ressorte.
    DONNEE = ("pct_au_but", "balles", "distances", "postures")
    coeur = {k: c[k] for k in DONNEE if k in c}
    if not coeur:
        coeur = {k: v for k, v in c.items() if k not in ("alertes", "reparation")}
    h = hashlib.sha256(json.dumps(coeur, sort_keys=True).encode()).hexdigest()[:16]
    vus[h].append((f, c.get("alertes")))
    (sans_alerte if not c.get("alertes") else avec_alerte).append(f)

print(f"\n  {len(sans_alerte) + len(avec_alerte)} fichiers portent un champ `alertes`")
print(f"    {len(avec_alerte)} en portent une · {len(sans_alerte)} sont vides")
print("\n  MEMES DONNEES, ALERTE DIFFERENTE — la signature de l effacement")
print("  " + "-" * 70)
trouve = 0
for h, lot in vus.items():
    if len(lot) < 2:
        continue
    etats = {bool(a) for _, a in lot}
    if len(etats) > 1:
        trouve += 1
        print(f"    empreinte {h} :")
        for f, a in lot:
            marque = "ALERTE EFFACEE" if not a else "alerte presente"
            print(f"      {marque:<16} {f.name}")
            if a:
                for x in a:
                    print(f"                       -> {x}")
if not trouve:
    print("    aucun autre couple de ce type.")
print("  " + "-" * 70)
print(f"  {trouve} effacement(s) detecte(s) par duplication.")
# ─── LE CONTROLE POSITIF : le cas CONNU doit ressortir, sinon le chasseur est aveugle.
connu = {f.name for h, lot in vus.items() if len(lot) > 1 and len({bool(a) for _, a in lot}) > 1
         for f, _ in lot}
if {"courbe_toucher.json", "courbe_toucher_juge.json"} <= connu:
    print("\n  CONTROLE POSITIF : PASSE — le couple connu ressort bien du balayage.")
else:
    print("\n  ⚠️ CONTROLE POSITIF TOMBE : le couple courbe_toucher / _juge NE ressort pas.")
    print("     Le chasseur est aveugle ; son zero ne vaut rien.")

print("\n  ⚠️ CE QUE CE BALAYAGE NE PEUT PAS VOIR : une alerte effacee SANS laisser")
print("     l original a cote. La duplication est la seule trace qu il sait lire.")
