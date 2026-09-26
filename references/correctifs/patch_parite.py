"""26/09 : au depart, le prix au marche d un bien importe que la region ne produit pas est sa parite a l import
( cout rendu + marge du negoce + marge du detaillant ), pas le prix mondial. Idempotent.
   python patch_parite.py chemin/d07_exterieur.py"""
import sys
p = sys.argv[1]; s = open(p).read()
if "_prix_de_depart_a_la_parite" in s: print("deja :", p); sys.exit(0)
a = '''    _port_horaire(p)       # ce que les marches ont deja en trop part avant la premiere heure pleine
    return e
'''
assert s.count(a) == 1, "fin de l installation introuvable"
s = s.replace(a, '''    _prix_de_depart_a_la_parite(p)
    _port_horaire(p)       # ce que les marches ont deja en trop part avant la premiere heure pleine
    return e


def _prix_de_depart_a_la_parite(p):
    """26/09 : un pays qui importe tout son gazole le vend a la pompe au cout rendu plus les marges, des le premier jour.
    Au prix mondial ( 8,76 pour une parite de ~13,5 ), le negoce n importait qu une fois le prix remonte a 8 % par jour
    ouvre ; le stock de depart s epuisait vers le jour 10, les camions s arretaient et la faim tenait du jour 14 au jour
    21 ( six iles d un million ). Seulement les biens que la region du marche ne produit pas, et seulement a la hausse."""
    w = p.w
    for mid, m in w.marches.items():
        for nom in BIENS_IMPORT:
            if any(nom in e.produits for e in w.entreprises.values()
                   if e.lieu.marche is not None and e.lieu.marche.id == mid): continue
            parite = prix_import(p, _id(p, nom)) * (1.0 + MARGE_NEGOCE) / (1.0 - m.marge)
            if parite > m.prix[nom]: m.prix[nom] = parite
''')
open(p, "w").write(s); print("corrige :", p)
