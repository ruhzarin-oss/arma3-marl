"""27/09 ( HMT-125 ) : dans la bande des prix collants, le prix ne derive plus : il revient lentement vers sa reference, le prix
d installation indexe sur le prix mondial du jour ( petite economie ouverte : le niveau des prix des biens echangeables suit
le monde, l ecart local ne vient que des ruptures et des surplus ). Idempotent.   python patch_ancre.py <racine>"""
import os, sys
racine = sys.argv[1]
f = os.path.join(racine, "monde", "pays", "d03_economie.py"); s = open(f).read()
if "prix_ref" in s: print("deja corrige :", f); sys.exit(0)
def sub(a, b):
    global s
    assert s.count(a) == 1, (f, a[:70], s.count(a)); s = s.replace(a, b)
sub('''                 "stock_soir", "couv_lisse")
''', '''                 "stock_soir", "couv_lisse", "prix_ref")
''')
sub('''        self.couv_lisse = {b: COUVERTURE_CIBLE_J.get(b, 0.0) for b in C.BIENS}   # couverture lissee sur ~3 jours ( HMT-125 )
''', '''        self.couv_lisse = {b: COUVERTURE_CIBLE_J.get(b, 0.0) for b in C.BIENS}   # couverture lissee sur ~3 jours ( HMT-125 )
        self.prix_ref = None                            # { bien : [ prix a l installation, cours mondial alors, cours mondial lisse ] }
''')
sub('''ALPHA_COUVERTURE = 1.0 / 3.0''', '''BETA_REF = 0.02                 # dans la bande, rappel vers la reference : le prix d installation indexe sur le prix mondial LISSE
ALPHA_MONDIAL = 1.0 / 90.0      # ... lisse sur ~3 mois : le prix de detail ne suit qu une part lente des cours mondiaux ( transmission
                                # partielle, 6 a 12 mois dans les etudes de la BCE ) ; le cours du jour ne fait pas le prix du rayon
                                # ( HMT-125 : la bande laissait deriver la nourriture de +2 % et les remedes de +3 a 10 % par mois, sans
                                # cause locale ; petite economie ouverte, loi du prix unique a une marge pres )
ALPHA_COUVERTURE = 1.0 / 3.0''')
sub('''            if abs(couv - cible) <= TOLERANCE_COUVERTURE * cible: x *= LENTEUR_DANS_LA_BANDE   # 27/09 : prix collants dans la bande
            if em.non_servi[b] > 0.0: x = max(x, min(1.0, em.non_servi[b] / dem))
            dlog = KAPPA_PRIX * x
''', '''            dans_la_bande = abs(couv - cible) <= TOLERANCE_COUVERTURE * cible
            if dans_la_bande: x *= LENTEUR_DANS_LA_BANDE                          # 27/09 : prix collants dans la bande
            if em.non_servi[b] > 0.0: x = max(x, min(1.0, em.non_servi[b] / dem))
            dlog = KAPPA_PRIX * x
            if dans_la_bande and em.non_servi[b] <= 0.0:                            # HMT-125 : dans la bande, retour vers la reference
                ref = _prix_de_reference(p, em, m, b)
                if ref is not None and ref > 0.0: dlog += BETA_REF * (math.log(ref) - math.log(m.prix[b]))
''')
sub('''def _parite_import(p, m, b):''', '''def _prix_de_reference(p, em, m, b):
    """Le prix d installation du bien a ce marche, indexe sur le prix mondial du jour ( prix_port du domaine 7 ) : ce vers quoi
    le prix revient quand rien ne manque ni ne deborde. None pour un bien qui ne s echange pas."""
    if em.prix_ref is None: em.prix_ref = {}
    pm = _prix_mondial_du_jour(p.w, b)
    r = em.prix_ref.get(b)
    if r is None: r = em.prix_ref[b] = [m.prix[b], pm, pm]          # prix d installation, cours mondial alors, cours lisse
    r[2] = (1.0 - ALPHA_MONDIAL) * r[2] + ALPHA_MONDIAL * pm
    prix0, pm0, pml = r
    return prix0 * pml / pm0 if pm0 > 0.0 else prix0


def _parite_import(p, m, b):''')
open(f, "w").write(s); print("corrige :", f)
