#!/usr/bin/env python3
"""faux_journal.py — LES CONTROLES SE DECLENCHENT-ILS QUAND ILS DOIVENT ?

⟨Younes, 09/08 : « vas-y fais le faux journal »⟩

LE PROBLEME QU IL RESOUT. Le depouillement porte onze controles, ecrits un par un au fil des
pannes de la nuit. Aucun n a jamais ete VERIFIE : on sait qu ils sont tombes quand le banc
etait casse, on ne sait pas s ils tomberaient a chaque fois. Un controle qui laisserait passer
la panne qu il surveille est pire qu absent — il donne le sentiment d avoir regarde.

CE QUE FAIT CE SCRIPT. Il fabrique de faux journaux au format exact du banc, un par PANNE
CONNUE, et verifie que le depouillement REFUSE le verdict a chaque fois. Puis un journal SAIN,
sur lequel il doit au contraire rendre son verdict.

  · le journal sain              -> le depouillement doit CONCLURE
  · un temoin qui ne delivre rien -> il doit REFUSER
  · un bras de feu qui ne tire pas -> il doit REFUSER
  · des coups d appui dans le temoin -> il doit REFUSER
  · des murets qui n encaissent rien -> il doit REFUSER
  · un fusil vide au depart       -> il doit REFUSER
  · des hommes qui ne peuvent pas tirer -> il doit REFUSER
  · un seul terrain               -> il doit REFUSER
  · des bras desequilibres        -> il doit REFUSER
  · un effectif degrade           -> il doit REFUSER

C EST LE CONTROLE POSITIF DU DEPOUILLEMENT LUI-MEME. Dix secondes, aucun serveur. Chaque panne
de cette liste a reellement coute entre quatre minutes et une nuit quand on l a decouverte en
production ; ici elle coute une seconde.
"""
import subprocess, sys, tempfile, os, pathlib

DEP = '/home/younes/arma3-marl/depouille_appui.py'

def ligne(bras, rep, ter, dl, dl2, armes, cap0, cap1, cd, ca, murs, corps,
          angle=0.4, refus=0, vise=0, supp=0.2, vd=6, vv=4, comb=6, res=800):
    """le format REEL du journal, recensement desagrege par role — verifie sur une ligne
    du banc, pas de memoire. cap0 = defenseurs/appuis ; cap1 = defenseurs/appuis/reserve."""
    return (f' 1:00:00 "HMT|AP|essai|{bras}|{rep}|terrain|{ter}|delivre|{dl}|delivre2|{dl2}'
            f'|combat|{comb}|armes|{armes}|cap0|{cap0}|cap1|{cap1}/res{res}|coupsdef|{cd}'
            f'|coupsapp|{ca}|murs|{murs}|corps|{corps}|angle|{angle}|refus|{refus}'
            f'|vise|{vise}|supp|{supp}|vivants|{vd}|{vv}"')

def journal(pathologie=None, terrains=4, reps=3):
    """un journal SAIN, sauf si on lui injecte une pathologie precise"""
    L = [' 0:59:00 "HMT|AP|debut|3"', ' 0:59:30 "HMT|OK|ap_presence|120"',
         ' 0:59:40 "HMT|OK|ap_arrivee|60"']
    for t in range(terrains):
        base = 150 + 30 * t
        for r in range(1, reps + 1):
            # ── le TEMOIN : delivre bien, appui muet, fusils a 6 (les 3 appuis sont vides)
            dl = base + (r - 1) * 5
            L.append(ligne(0, r, t, dl, dl * 7, 6, '6,6,6,2/3,0,3,1', '6,6,6,1/3,0,3,0', 500, 0, 1, 0))
            # ── le FEU NATIF : delivre moins, appui qui tire, murets qui encaissent
            dn = int(dl * 0.75)
            L.append(ligne(2, r, t, dn, dn * 7, 9, '6,6,6,2/3,3,3,1', '6,6,6,1/3,3,3,0', 400, 300, 120, 20))
    L.append(' 1:30:00 "HMT|AP|TERMINE|session|1"')

    if pathologie == 'temoin_muet':
        L[3] = ligne(0, 1, 0, 0, 0, 6, '6,6,6,2/3,0,3,1', '6,6,6,1/3,0,3,0', 500, 0, 1, 0)
    elif pathologie == 'feu_muet':
        L[4] = ligne(2, 1, 0, 100, 700, 9, '6,6,6,2/3,3,3,1', '6,6,6,1/3,3,3,0', 400, 0, 120, 20)
    elif pathologie == 'coups_dans_le_temoin':
        L[3] = ligne(0, 1, 0, 150, 1050, 6, '6,6,6,2/3,0,3,1', '6,6,6,1/3,0,3,0', 500, 7, 1, 0)
    elif pathologie == 'murets_muets':
        L[4] = ligne(2, 1, 0, 110, 770, 9, '6,6,6,2/3,3,3,1', '6,6,6,1/3,3,3,0', 400, 300, 0, 20)
    elif pathologie == 'fusil_vide':
        L[4] = ligne(2, 1, 0, 110, 770, 5, '6,6,6,2/3,3,3,1', '6,6,6,1/3,3,3,0', 400, 300, 120, 20)
    elif pathologie == 'ne_peut_pas_tirer':
        L[4] = ligne(2, 1, 0, 110, 770, 9, '6,6,6,2/3,1,3,1', '6,6,6,1/3,1,3,0', 400, 300, 120, 20)
    elif pathologie == 'un_seul_terrain':
        L = [x for x in L if '|terrain|0|' in x or 'HMT|AP|' not in x or 'essai' not in x]
    elif pathologie == 'bras_desequilibres':
        L = [x for x in L if not ('|essai|2|3|' in x)]
    elif pathologie == 'reserve_percee':
        L[4] = ligne(2, 1, 0, 110, 770, 9, '6,6,6,2/3,3,3,1', '6,6,6,1/3,3,3,0',
                     400, 300, 120, 20, res=12)
    elif pathologie == 'effectif_degrade':
        L[4] = ligne(2, 1, 0, 110, 770, 9, '6,6,6,2/3,3,3,1', '6,6,6,1/3,3,3,0', 400, 300, 120, 20, vd=5)
    return '\n'.join(L) + '\n'

ATTENDU = {
    None:                    ('CONCLURE', 'un journal sain'),
    'temoin_muet':           ('REFUSER',  'un temoin qui ne delivre rien'),
    'feu_muet':              ('REFUSER',  'un bras de feu qui ne tire pas'),
    'coups_dans_le_temoin':  ('REFUSER',  'des coups d appui dans le temoin'),
    'murets_muets':          ('REFUSER',  'des murets qui n encaissent rien'),
    'fusil_vide':            ('REFUSER',  'un fusil vide au depart'),
    'ne_peut_pas_tirer':     ('REFUSER',  'des hommes qui ne peuvent pas tirer'),
    'un_seul_terrain':       ('REFUSER',  'un seul terrain — un endroit, pas une mecanique'),
    'bras_desequilibres':    ('REFUSER',  'des bras desequilibres'),
    'reserve_percee':        ('REFUSER',  'un fusil descendu sous le plancher de 60 coups'),
    'effectif_degrade':      ('REFUSER',  'un effectif degrade'),
}

print("\n  L ESSAI A BLANC DU DEPOUILLEMENT — aucun serveur, dix secondes")
print("  " + "─" * 78)
print("  %-34s%-12s%-12s%s" % ("ce qu on injecte", "attendu", "obtenu", ""))
print("  " + "─" * 78)
bon = 0
for patho, (attendu, nom) in ATTENDU.items():
    with tempfile.NamedTemporaryFile('w', suffix='.out', delete=False) as h:
        h.write(journal(patho)); tmp = h.name
    src = pathlib.Path(DEP).read_text()
    src = src.replace("F = '/mnt/data/harmattan-sandbox/logs/serverAP.out'", f"F = '{tmp}'")
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as h:
        h.write(src); dep = h.name
    r = subprocess.run([sys.executable, dep], capture_output=True, text=True, timeout=60)
    sortie = r.stdout + r.stderr
    obtenu = 'REFUSER' if 'AUCUN VERDICT' in sortie else ('CONCLURE' if 'ETAGE 1' in sortie else 'CASSE')
    ok = (obtenu == attendu)
    bon += ok
    marque = '' if ok else '   <== LE CONTROLE NE SE DECLENCHE PAS'
    print("  %-34s%-12s%-12s%s" % (nom, attendu, obtenu, marque))
    if not ok and '--bavard' in sys.argv:
        print('\n'.join('        ' + x for x in sortie.split('\n')[:24]))
    os.unlink(tmp); os.unlink(dep)

print("  " + "─" * 78)
print(f"  {bon} sur {len(ATTENDU)} conformes")
if bon == len(ATTENDU):
    print("  Les onze controles se declenchent quand ils doivent, ET se taisent quand tout va")
    print("  bien. Le depouillement sait echouer — c est la condition pour croire ses verdicts.")
else:
    print("  ⚠️ UN CONTROLE NE FAIT PAS SON TRAVAIL. Tant qu il n est pas repare, un verdict")
    print("     rendu par ce depouillement ne vaut rien : il laisserait passer cette panne-la.")
