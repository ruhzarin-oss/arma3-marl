"""Correctif ( 28/09, chef de projet, trouve par Classes ) : un salarie licencie par d03 ( licencier ) ne garde pas ses
heures du jour. La docstring le disait ( « la paie ne lui doit plus d heures » ), le code ne le faisait pas : le
revoque etait paye des heures deja faites dans la journee, et monde.payer plantait pour un convoyeur incarcere par d21
( self.marches[p.travail.id] avec p.travail vide ). Le meme texte pour le depot et pour l arbre des references.
Idempotent.   python patch_licencier.py racine_de_l_arbre"""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d03_economie.py"); s = open(f).read()
ancien = '''    h.travail, h.horaire = None, None
    if h.poste == "travail": h.lieu, h.poste = h.domicile, "maison"
'''
nouveau = '''    h.travail, h.horaire = None, None
    h.heures_jour = 0.0                                  # la paie ne lui doit plus d heures ( ni celles du jour )
    if h.poste == "travail": h.lieu, h.poste = h.domicile, "maison"
'''
if nouveau in s: print(f"deja : {f}")
elif s.count(ancien) == 1: open(f, "w").write(s.replace(ancien, nouveau)); print(f"corrige : {f}")
else: sys.exit(f"motif introuvable ( {s.count(ancien)} fois ) : {f}")
