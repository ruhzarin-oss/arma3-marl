"""Applique la correction du 26/09 ( stocks, caisse et fonds de roulement d un marche proportionnels a la population
qu il sert ) a un monde.py : colonnes ( --colonnes ) ou ancien moteur a objets. Idempotent.
   python patch_echelle.py chemin/monde.py [--colonnes]"""
import sys
p = sys.argv[1]; colonnes = "--colonnes" in sys.argv
s = open(p).read()
if "POP_MARCHE_E1" in s: print("deja corrige :", p); sys.exit(0)
def sub(a, b):
    global s
    assert s.count(a) == 1, (p, a[:60], s.count(a)); s = s.replace(a, b)
a = 'CATEGORIES_PUBLIQUES = ("hopitaux", "armee", "reserve", "population")\n'
sub(a, a + '''# le monde E1 : 500 habitants, trois marches, ~167 par marche. Ses stocks de depart ( 600 de nourriture = 3,6 jours ),
# la caisse d un marche et le fonds qu il garde avant de verser son benefice ( 20 000 ) etaient faits pour eux
POP_MARCHE_E1 = 500 / 3
''')
a = '''            m.stocks.update({"nourriture": 600.0, "carburant": 300.0, "remedes": 40.0, "fer": 100.0, "zinc": 60.0,
                             "petrole": 200.0, "outils": 10.0})
'''
sub(a, a + '''        # ! 26/09 : les stocks, la caisse et le fonds de roulement d un marche suivent la population qu il sert ( au moins
        # ceux du monde E1 ). Fixes, ils donnaient 0,06 jour de nourriture au marche unique de Malden a 10 000 habitants,
        # presque rien a un million : le pays demarrait sans nourriture ni carburant, et le cercle ( pas de carburant ->
        # pas de camion -> pas de recolte au marche -> pas de caisse -> pas de carburant ) tenait 12 jours.
        pop = self._population_des_marches()
        for m in self.marches.values():
            m.echelle = max(1.0, pop.get(m.lieu.id, 0) / POP_MARCHE_E1)
            for b in m.stocks: m.stocks[b] *= m.echelle
            m.caisse *= m.echelle
''')
if colonnes:
    methode = '''    def _population_des_marches(self):
        """Les vivants de chaque marche, comptes au marche du domicile de leur menage ( comme `indexer` )."""
        t, n = self.table, self.table.n
        vivant = t.vivant[:n] == 1
        mt = t.menages
        mm = P.menages_inscrits(t, n)
        marche = self._marche_du_lieu[mt.domicile[:mt.n][mm[vivant & (mm >= 0)]]]
        comptes = np.bincount(marche[marche >= 0], minlength=len(self.carte.par_n))
        return {self.carte.par_n[k].id: int(comptes[k]) for k in np.nonzero(comptes)[0]}

'''
else:
    methode = '''    def _population_des_marches(self):
        """Les vivants de chaque marche, comptes au marche du domicile de leur menage ( comme `indexer` )."""
        pop = {}
        for mg in self.menages:
            if mg.domicile is None or mg.domicile.marche is None: continue
            k = mg.domicile.marche.id
            pop[k] = pop.get(k, 0) + len([p for p in mg.membres if p.vivant])
        return pop

'''
sub("    def indexer(self):", methode + "    def indexer(self):")
sub("            exces = m.caisse - 20000.0\n", '            exces = m.caisse - 20000.0 * getattr(m, "echelle", 1.0)\n')
open(p, "w").write(s); print("corrige :", p)
