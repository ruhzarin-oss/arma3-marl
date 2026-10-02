"""03/10 ( HMT-194, etape 3c d Arma a fond ) : LE MORAL AU FRONT. Le domaine 23 sautait les habitants ABSENTS dans sa
passe du moral : un soldat mobilise ( guerre/moteur.mobiliser : absent, destination « front » ) gardait le moral du jour
de son depart, la faim de son menage ne l atteignait plus, et _deuils changeait quand meme sa part de deuil - d ou
l anomalie moral_hors_causes des qu un proche mourait. Les soldats au front passent maintenant dans la passe comme les
residents ; les autres absents ne changent pas. Interrupteur MORAL_AU_FRONT. Et _deuils frappe le soir les deuils poses
par un autre domaine dans w.deuils_poses ( la guerre : les camarades d un soldat tue ). Sans soldat au front ni deuil
pose, rien ne change.
Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_moral_front.py racine_de_l_arbre"""
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


remplacer("monde/pays/d23_culture.py", [
    ("""DEMI_VIE_DEUIL_J = 90.0
""", """DEMI_VIE_DEUIL_J = 90.0
# ( 03/10, HMT-194 3c ) un soldat au front de la guerre d Arma garde le moral de chez lui : la faim de son menage, un
# deuil chez lui, l isolement l atteignent ( lettres, telephone ; CHOIX : le jour meme, sans delai de courrier )
MORAL_AU_FRONT = True
"""),
    ("""

def _moral_du_jour(p, d, n, mg, viv, cout, caisse, sortie, chocs):
""", """

def _au_front(p, n):
    \"\"\"( 03/10, HMT-194 3c ) Les habitants au front de la guerre d Arma ( w.absents, destination « front » ) : ils
    passent dans la passe du moral comme des residents. Les autres absents n y passent pas.\"\"\"
    out = np.zeros(n, bool)
    if not MORAL_AU_FRONT: return out
    for i, a in getattr(p.w, "absents", {}).items():
        if 0 <= int(i) < n and isinstance(a, dict) and a.get("destination") == "front": out[int(i)] = True
    return out


def _moral_du_jour(p, d, n, mg, viv, cout, caisse, sortie, chocs):
"""),
    ("""    v = np.nonzero((tb.vivant[:n] == 1) & (tb.statut[:n] != PO.ABSENT) & (col["cul_base"][:n] >= 0))[0]
    s7 = col["cul_sorties7"]
""", """    v = np.nonzero((tb.vivant[:n] == 1) & ((tb.statut[:n] != PO.ABSENT) | _au_front(p, n))     # ( HMT-194 3c ) le front
                   & (col["cul_base"][:n] >= 0))[0]
    s7 = col["cul_sorties7"]
"""),
    ("""    col = p.colonnes["habitant"]; tb = p.w.table
    morts = np.nonzero((col["deces_j"][:n] >= 0) & (col["cul_deuil_vu"][:n] == 0))[0]
""", """    col = p.colonnes["habitant"]; tb = p.w.table
    _deuils_poses(p, n)                                  # ( 03/10, HMT-194 3c ) les camarades d un soldat tue
    morts = np.nonzero((col["deces_j"][:n] >= 0) & (col["cul_deuil_vu"][:n] == 0))[0]
"""),
    ("""

def _deuils(p, d, n, mg):
""", """

def _deuils_poses(p, n):
    \"\"\"( 03/10, HMT-194 3c ) Les deuils poses par un autre domaine dans w.deuils_poses ( [ ( habitants, part ) ] : la
    guerre y met les camarades d un soldat tue ) frappent le soir, comme ceux de la famille, bornes a DEUIL_MIN.\"\"\"
    q = getattr(p.w, "deuils_poses", None)
    if not q: return
    de = p.colonnes["habitant"]["cul_deuil"]
    for ids, part in q:
        ids = np.asarray([int(i) for i in ids if 0 <= int(i) < n], np.int64)
        if len(ids): de[ids] = np.maximum(DEUIL_MIN, de[ids].astype(np.float64) + part).astype(np.float32)
    q.clear()


def _deuils(p, d, n, mg):
"""),
])
