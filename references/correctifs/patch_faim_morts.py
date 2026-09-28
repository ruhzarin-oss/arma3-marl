"""HMT-136 : un menage eteint par la faim n est pas « nourri ». Applique dans l atelier courant ( idempotent )."""
import re, sys
def remplacer(chemin, ancien, nouveau, n=1):
    s = open(chemin).read()
    if nouveau in s: print(f"deja fait : {chemin}"); return
    assert s.count(ancien) == n, (chemin, ancien[:60], s.count(ancien))
    open(chemin, "w").write(s.replace(ancien, nouveau)); print(f"corrige : {chemin}")

# 1. d01 : chaque menage compte ses morts de faim ( colonne du menage, donc enregistree et sauvee avec l instantane )
remplacer("monde/pays/d01_population.py",
 '''    for nom, dt, defaut in (("dissous", np.int8, 0), ("faim7", np.int8, 0), ("demenage_j", np.int32, -100000)):''',
 '''    for nom, dt, defaut in (("dissous", np.int8, 0), ("faim7", np.int8, 0), ("demenage_j", np.int32, -100000),
                            ("morts_faim", np.int32, 0)):''')
remplacer("monde/pays/d01_population.py",
 '''    col["cause_deces"][h.id] = CAUSES.index(cause)
''',
 '''    col["cause_deces"][h.id] = CAUSES.index(cause)
    if cause == "faim" and h.menage is not None:              # HMT-136 : le menage garde le compte de ses morts de faim
        p.col("menage", "morts_faim")[h.menage.id] += 1
''')

# 2. monde : un menage sans vivant qui a perdu au moins un membre par la faim n est pas nourri ( les notes, l Etat )
remplacer("monde/monde.py",
 '''        self.nourri_menage = ParMenage(~affame)
''',
 '''        eteint = self._eteints_par_la_faim(v)                  # HMT-136 : un menage mort de faim n est pas « nourri »
        self.stats_jour["menages_eteints_faim"] = int(eteint.sum())
        self.nourri_menage = ParMenage(~(affame | eteint))
''')
remplacer("monde/monde.py",
 '''    def repas_python(self):
        sans = 0
''',
 '''    def _eteints_par_la_faim(self, v):
        """HMT-136 ( 28/09 ) : les menages sans aucun vivant a table ( `v` = 0 ) qui ont perdu au moins un membre par la
        faim ( colonne `morts_faim` du domaine 1 ). Avant, un tel menage avait un besoin nul, donc aucun manque : il
        comptait NOURRI dans chaque note et chaque mesure, et la faim « baissait » quand les affames mouraient. Un
        menage vide pour une autre raison ( voyage, emigration, autre cause de mort ) reste neutre. Sans le domaine 1,
        la faim ne tue pas : aucun menage."""
        v = np.asarray(v)
        p = getattr(self, "pays", None)
        if p is None or not p.a("population"): return np.zeros(len(v), bool)
        mf = p.col("menage", "morts_faim")
        m = min(len(v), len(mf))
        out = np.zeros(len(v), bool)
        out[:m] = (v[:m] == 0) & (mf[:m] > 0)
        return out

    def repas_python(self):
        sans = 0
''')
remplacer("monde/monde.py",
 '''        self.stats_jour["menages_sans_nourriture"] = sans
        self.faim_region = {k: affames_region.get(k, 0) / n for k, n in par_region.items()}''',
 '''        self.stats_jour["menages_sans_nourriture"] = sans
        vv = np.array([sum(1 for p in mg.membres if p.vivant) for mg in self.menages], dtype=np.int64)
        eteint = self._eteints_par_la_faim(vv)                  # HMT-136 : meme regle que la version en colonnes
        for k in np.nonzero(eteint)[0].tolist(): self.nourri_menage[self.menages[k].id] = False
        self.stats_jour["menages_eteints_faim"] = int(eteint.sum())
        self.faim_region = {k: affames_region.get(k, 0) / n for k, n in par_region.items()}''')

# 3. la mesure des essais : un menage eteint par la faim compte affame, au numerateur ET au denominateur
remplacer("monde/pays/essais.py",
 '''def faim(w):
    return w.stats_jour.get("menages_sans_nourriture", 0) / max(1, len(menages_habites(w)))''',
 '''def faim(w):
    """Part des menages sans repas ce soir. HMT-136 ( 28/09 ) : les menages eteints par la faim comptent AFFAMES
    ( numerateur et denominateur ) ; avant, la faim « baissait » quand les affames mouraient."""
    e = w.stats_jour.get("menages_eteints_faim", 0)
    return (w.stats_jour.get("menages_sans_nourriture", 0) + e) / max(1, len(menages_habites(w)) + e)''')
