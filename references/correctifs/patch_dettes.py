"""26/09 : un compte d arrieres par ( creancier, debiteur, motif ), les loyers restant un par terme. Idempotent.
   python patch_dettes.py <racine contenant monde/>"""
import os, sys
R = sys.argv[1]
def sub(p, a, b):
    s = open(p).read()
    if b in s: return
    assert s.count(a) == 1, (p, a[:60], s.count(a)); open(p, "w").write(s.replace(a, b))
p = os.path.join(R, "monde/socle/comptes.py")
sub(p, '''    __slots__ = ("actives", "par_debiteur", "prochain_id", "reglees", "abandonnees")''',
       '''    __slots__ = ("actives", "par_debiteur", "prochain_id", "reglees", "abandonnees", "par_compte")''')
sub(p, '''        self.abandonnees = {}      # raison -> montant perdu par les creanciers
''', '''        self.abandonnees = {}      # raison -> montant perdu par les creanciers
        self.par_compte = {}       # ( creancier, debiteur, motif ) -> id : UN compte d arrieres par triplet
''')
sub(p, '''        c = Creance(self.prochain_id, creancier, debiteur, float(montant), motif, jour, echeance)
        self.prochain_id += 1
        self.actives[c.id] = c
        self.par_debiteur.setdefault(debiteur, []).append(c.id)
        return c
''', '''        # 26/09 : comme un bailleur tient UN compte d arrieres par locataire et le fisc UN par contribuable et par impot,
        # un nouvel impaye du meme creancier, du meme debiteur et du meme motif s ajoute au compte ouvert ( sa date de
        # naissance reste la plus ancienne, son echeance la plus proche ). Une dette par impaye ne grossissait plus que
        # la memoire : 141 000 creances a 6 x 50 000 habitants au jour 96, et en acceleration.
        cle = (_ident(creancier), _ident(debiteur), motif)
        i = self.par_compte.get(cle) if motif not in UN_PAR_TERME else None
        c = self.actives.get(i) if i is not None else None
        if c is not None:
            c.montant += float(montant)
            if echeance is not None and (c.echeance is None or echeance < c.echeance): c.echeance = echeance
            return c
        c = Creance(self.prochain_id, creancier, debiteur, float(montant), motif, jour, echeance)
        self.prochain_id += 1
        self.actives[c.id] = c
        self.par_debiteur.setdefault(debiteur, []).append(c.id)
        if motif not in UN_PAR_TERME: self.par_compte[cle] = c.id
        return c
''')
sub(p, '''    def _retirer(self, c):
        del self.actives[c.id]
''', '''    def _retirer(self, c):
        del self.actives[c.id]
        cle = (_ident(c.creancier), _ident(c.debiteur), c.motif)
        if getattr(self, "par_compte", {}).get(cle) == c.id: del self.par_compte[cle]
''')
sub(p, '''class Creances:''', '''# les motifs dont chaque terme impaye reste une dette a part : le domaine 13 compte les mois de loyer impayes ( litige,
# expulsion ) en comptant ses creances ; ceux-la sont bornes par l expulsion, pas par le compte d arrieres
UN_PAR_TERME = ("loyer",)


def _ident(o):
    """L identite stable d un detenteur : sa classe et son numero ( une vue de menage recreee reste le meme menage ),
    sinon l objet lui-meme ( Etat, caisses : uniques )."""
    i = getattr(o, "id", None)
    return (type(o).__name__, i) if isinstance(i, (int, str)) else (type(o).__name__, id(o))


class Creances:''')
p = os.path.join(R, "monde/pays/d06_etat.py")
sub(p, '''    garde = []
    for cr in f.creances:
        if actives.get(cr.id) is not cr: continue''', '''    garde = []; vues = set()
    for cr in f.creances:
        if actives.get(cr.id) is not cr or cr.id in vues: continue       # un compte d arrieres une fois ( 26/09 )
        vues.add(cr.id)''')
sub(p, '''        for cr in o.creances: par_cr[cr.id] = o''', '''        for cr in o.creances: par_cr.setdefault(cr.id, o)''')
sub(p, "    return [c for c in _etat(p).fisc.creances if K.actives.get(c.id) is c]\n",
       "    return list({c.id: c for c in _etat(p).fisc.creances if K.actives.get(c.id) is c}.values())   # un compte une fois ( 26/09 )\n")
print("corrige :", R)
