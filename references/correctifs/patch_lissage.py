"""27/09 ( HMT-125 ) : le marchand lit sa couverture LISSEE sur trois jours, pas celle d un seul soir : un creux de livraison
d une journee ( 0,9 jour au lieu de 2 ) le faisait monter de 4 a 8 % d un coup, et la bande des prix collants ne le laissait
redescendre qu au quart de la vitesse - d ou +4 % par mois sur la nourriture dans le monde par defaut. Une rupture
( non servi ) reste un signal immediat. Idempotent.   python patch_lissage.py <racine>"""
import os, sys
racine = sys.argv[1]
f = os.path.join(racine, "monde", "pays", "d03_economie.py"); s = open(f).read()
if "couv_lisse" in s: print("deja corrige :", f); sys.exit(0)
def sub(a, b):
    global s
    assert s.count(a) == 1, (f, a[:70], s.count(a)); s = s.replace(a, b)
sub('''    __slots__ = ("id", "demande_lisse", "non_servi", "non_solvable", "couverture", "ventes_ht", "ventes_q", "ventes_jour",
                 "stock_soir")
''', '''    __slots__ = ("id", "demande_lisse", "non_servi", "non_solvable", "couverture", "ventes_ht", "ventes_q", "ventes_jour",
                 "stock_soir", "couv_lisse")
''')
sub('''        self.stock_soir = None                          # { bien : stock a 19 h, avant les courses } ( 27/09 )
''', '''        self.stock_soir = None                          # { bien : stock a 19 h, avant les courses } ( 27/09 )
        self.couv_lisse = {b: COUVERTURE_CIBLE_J.get(b, 0.0) for b in C.BIENS}   # couverture lissee sur ~3 jours ( HMT-125 )
''')
sub('''TOLERANCE_COUVERTURE = 0.5
''', '''TOLERANCE_COUVERTURE = 0.5
ALPHA_COUVERTURE = 1.0 / 3.0    # la couverture que lit le marchand est lissee sur ~3 soirs : un seul creux de livraison ne
                                # fait pas un prix ( HMT-125 : +4 % par mois sur la nourriture par des creux d un soir )
''')
sub('''            em.couverture[b] = couv
            x = max(-1.0, min(1.0, (cible - couv) / cible))
''', '''            em.couverture[b] = couv
            cl = getattr(em, "couv_lisse", None)
            if cl is None: cl = em.couv_lisse = {k: COUVERTURE_CIBLE_J.get(k, 0.0) for k in C.BIENS}
            couv = cl[b] = (1.0 - ALPHA_COUVERTURE) * cl.get(b, couv) + ALPHA_COUVERTURE * couv
            x = max(-1.0, min(1.0, (cible - couv) / cible))
''')
open(f, "w").write(s); print("corrige :", f)
