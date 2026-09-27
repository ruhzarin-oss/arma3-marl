"""27/09 ( HMT-123, guerre des iles ) : les bornes de prix de d03 ( plancher, plafond, parite a l export de la nourriture )
suivent le prix mondial du JOUR en monnaie de l ile ( domaine 7 : change et chocs compris ), et non le prix du moteur, fixe
en monnaie locale. Apres la devaluation de l obole, le plafond fixe ( 2,5 x 9 = 22,5 ) passait sous la parite a l import du
gazole ( 28,1 ) : le negociant gardait dix jours de gazole, le marche restait a zero, 36 ruptures par jour. Idempotent.
   python patch_plafond.py <racine>"""
import os, sys
racine = sys.argv[1]
f = os.path.join(racine, "monde", "pays", "d03_economie.py"); s = open(f).read()
if "_prix_mondial_du_jour" in s: print("deja corrige :", f); sys.exit(0)
a = '''def _borner(w, b, x):
    bas = (PARITE_EXPORT if b == "nourriture" else PLANCHER) * PM[b]
    x = min(PLAFOND * PM[b], max(bas, x))
    plafond = w.gouv.lois.get("prix_plafond", {}).get(b)
    return min(x, float(plafond)) if plafond else x
'''
assert s.count(a) == 1, (f, s.count(a))
s = s.replace(a, '''def _borner(w, b, x):
    # 27/09 ( guerre des iles, Stratis, HMT-123 ) : les bornes suivent le prix mondial du JOUR en monnaie de l ile ( domaine
    # 7 : change et chocs compris ), non le prix du moteur, fixe en monnaie locale. Apres la devaluation de l obole, le
    # plafond fixe ( 2,5 x 9 = 22,5 ) passait sous la parite a l import du gazole ( 28,1 ) : le negociant gardait dix jours
    # de gazole en entrepot, le marche restait a zero, 36 ruptures par jour. Une borne technique n est pas un controle des
    # prix : un vrai plafonnement est une loi ( prix_plafond, domaine 6 ), avec sa subvention ou sa penurie.
    pm = _prix_mondial_du_jour(w, b)
    bas = (PARITE_EXPORT if b == "nourriture" else PLANCHER) * pm
    x = min(PLAFOND * pm, max(bas, x))
    plafond = w.gouv.lois.get("prix_plafond", {}).get(b)
    return min(x, float(plafond)) if plafond else x


def _prix_mondial_du_jour(w, b):
    """Le prix mondial d un bien echangeable au port, en monnaie de l ile, le jour meme ( domaine 7 : prix FOB a la parite
    du jour ) ; sans negoce, ou pour un bien qui ne s echange pas, le prix du moteur."""
    p = getattr(w, "pays", None)
    if p is None or not p.a("exterieur"): return PM[b]
    X = importlib.import_module(".d07_exterieur", __package__)
    return X.prix_port(p, b) if b in X.BIENS_IMPORT else PM[b]
''')
open(f, "w").write(s); print("corrige :", f)
