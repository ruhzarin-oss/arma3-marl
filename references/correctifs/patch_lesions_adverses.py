"""03/10 ( HMT-197, etape 4b d Arma a fond ) : LES LESIONS DE L ADVERSAIRE. Le domaine 27 tirait la lesion d un homme
adverse touche ( zone, arme, AIS ) puis l oubliait : l adversaire n etait qu un compte de neutralises. La guerre entre
iles pose dans le monde de l ile attaquee les VRAIS soldats de l attaquant : leur sort ( mort ou blesse ) doit revenir
dans le monde de leur ile. _impact garde desormais ( homme, zone, arme du tireur, AIS, arretee ) de chaque impact sur
l adversaire dans m.lesions_adverses. Rien d autre ne change ( le tirage du hasard est le meme ). Idempotent.
   python patch_lesions_adverses.py racine_de_l_arbre"""
import os, sys
R = sys.argv[1]


def _nouveau(a, b):
    return next((l for l in b.splitlines() if l.strip() and l not in a.splitlines()), None)


def remplacer(chemin, paires):
    f = os.path.join(R, chemin)
    if not os.path.exists(f): print("absent :", f); return
    s = open(f).read(); n = 0
    for a, b in paires:
        m = _nouveau(a, b)
        if b in s or (m is not None and m in s): continue
        if s.count(a) != 1: raise SystemExit(f"{chemin} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


remplacer("monde/pays/d27_armee_tactique.py", [
    ('''"compromis", "n_impacts", "n_arretes", "expo_debout", "expo_marche", "sig_debout", "sig_n")''',
     '''"compromis", "n_impacts", "n_arretes", "expo_debout", "expo_marche", "sig_debout", "sig_n",
                 "lesions_adverses")'''),
    ("""        self.sig_debout = self.sig_n = 0               # sous-pas de marche de la manoeuvre vus debout, et en tout
""", """        self.sig_debout = self.sig_n = 0               # sous-pas de marche de la manoeuvre vus debout, et en tout
        self.lesions_adverses = []                     # ( 03/10, HMT-197 4b ) ( homme, zone, arme, AIS, arretee )
"""),
    ('''    ais, arrete = lesion(zone, arme, int(h["prot"][v]), int(h["casque"][v]))
    p.compter("impact")
''', '''    ais, arrete = lesion(zone, arme, int(h["prot"][v]), int(h["casque"][v]))
    if int(h["side"][v]) == 1 and hasattr(m, "lesions_adverses"):     # ( 03/10, HMT-197 4b ) le sort de l adversaire
        m.lesions_adverses.append((int(v), zone, arme, int(ais), bool(arrete)))
    p.compter("impact")
'''),
])
