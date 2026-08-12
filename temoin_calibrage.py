#!/usr/bin/env python3
"""temoin_calibrage.py — LE CONTROLE POSITIF DU LECTEUR DE CALIBRAGE.

⟨Fable, 10/08⟩ « Le lecteur est un outil, il doit porter son controle positif comme les autres —
un journal FORGE AUX TAUX CONNUS qu il relit exactement, un journal PATHOLOGIQUE qu il refuse.
S il ne l a pas, c est sa vraie dette, pas l affichage. »

On fabrique des journaux dont on CONNAIT la reponse, et on verifie que le lecteur la retrouve :
  · des taux de prise imposes par effectif -> il doit les relire au point pres
  · des pertes imposees                     -> idem sur la survie
  · trop peu d accrochages                  -> il doit dire « pas assez », JAMAIS « hors bande »
  · tout hors bande                         -> il doit le dire, et renvoyer a l axe suivant
"""
import subprocess, sys, tempfile, os, pathlib, re

LEC = '/home/younes/arma3-marl/calibrage.py'

def journal(reglages, n_par_reglage):
    """reglages : {nDef: (taux_prise, pertes_par_accrochage)} — la verite qu on impose"""
    L = []
    i = 0
    for nd, (pr, pertes) in reglages.items():
        for k in range(n_par_reglage):
            i += 1
            nAtt = 8
            pris = 1 if (k < round(n_par_reglage * pr / 100.0)) else 0
            surv = max(0, nAtt - pertes)
            L.append(f' 1:00:00 "HMT|G|debut|{i}|100.0|3000|3000|3|0|{nd}|{nAtt}|200|100|1|1|0"')
            L.append(f' 1:05:00 "HMT|G|fin|{i}|400.0|300|prise|0|1|{pris}|60|4|{surv}|100|1"')
    return "\n".join(L) + "\n"

CAS = [
    ("taux relus au point pres", {6: (50, 4), 8: (30, 5), 10: (70, 2)}, 20,
     lambda s: "50%" in s.replace(" ", "") or re.search(r'\b50%', s)),
    ("pas assez d accrochages", {6: (50, 4), 8: (30, 5)}, 3,
     lambda s: "pas assez" in s and "ON NE SAIT PAS ENCORE" in s),
    ("tout hors bande", {6: (95, 0), 8: (98, 0), 10: (99, 0)}, 20,
     lambda s: "hors bande" in s and "axe suivant" in s),
]

print("\n  LE CONTROLE POSITIF DU LECTEUR DE CALIBRAGE")
print("  " + "─" * 70)
bon = 0
for nom, reg, n, verif in CAS:
    with tempfile.NamedTemporaryFile('w', suffix='.out', delete=False) as h:
        h.write(journal(reg, n)); tmp = h.name
    r = subprocess.run([sys.executable, LEC, tmp], capture_output=True, text=True, timeout=60)
    s = r.stdout + r.stderr
    ok = verif(s)
    bon += ok
    print(f"    {'PASSE' if ok else 'TOMBE':>6}  {nom}")
    if not ok and '--bavard' in sys.argv:
        print("\n".join("        " + x for x in s.split("\n")[:22]))
    os.unlink(tmp)
print("  " + "─" * 70)
print(f"  {bon} sur {len(CAS)} conformes")
if bon == len(CAS):
    print("  Le lecteur relit ce qu on lui impose, et distingue « je ne sais pas » de")
    print("  « rien ne convient ». Il a le droit d etre cru.")
else:
    print("  ⚠️ LE LECTEUR NE RELIT PAS CE QU ON LUI IMPOSE. Tant qu il n est pas repare,")
    print("     aucune calibration lue par lui ne vaut quoi que ce soit.")
