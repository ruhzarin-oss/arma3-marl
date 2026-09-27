"""27/09 : ce qu un acheteur industriel n a pas pu acheter au marche est une RUPTURE ( non servi ), pas un silence.
d10 : le gazole des mines et des convois ; d15 : les intrants des entreprises. Idempotent."""
import os, sys
racine = sys.argv[1]
def patch(f, subs, garde):
    p = os.path.join(racine, "monde", "pays", f); s = open(p).read()
    if garde in s: print("deja corrige :", p); return
    for a, b in subs:
        assert s.count(a) == 1, (f, a[:60], s.count(a)); s = s.replace(a, b)
    open(p, "w").write(s); print("corrige :", p)
patch("d10_industrie.py", [(
'''        m = w.marches[e.lieu.marche.id]
        q = min(3.0 * besoin - e.stocks["carburant"], m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE)
        m.demande["carburant"] += max(0.0, q)
        if q <= 0.0: continue
''', '''        m = w.marches[e.lieu.marche.id]
        voulu = 3.0 * besoin - e.stocks["carburant"]
        q = min(voulu, m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE)
        # 27/09 : la commande entiere est une demande, et ce que le marche ne peut pas servir est une rupture ( non servi ) :
        # avant, une mine a sec devant un marche sous sa reserve ne laissait aucune trace, le prix ne bougeait pas, la
        # raffinerie ne repartait pas, et la mine attendait
        m.demande["carburant"] += voulu
        _rupture(p, m, "carburant", voulu - max(0.0, q))
        if q <= 0.0: continue
'''), (
'''                m.demande["carburant"] += gaz
                if m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE < gaz:
                    p.compter("livraison_sans_gazole"); break
''', '''                m.demande["carburant"] += gaz
                if m.stocks["carburant"] - RESERVE_CARBURANT_MARCHE < gaz:
                    _rupture(p, m, "carburant", gaz); p.compter("livraison_sans_gazole"); break
'''), (
'''def _besoin_site(s, b):''', '''def _rupture(p, m, b, q):
    """Une demande que le marche n a pas pu servir faute de stock : le signal de prix du marchand ( domaine 3 )."""
    if q > 0.0 and p.a("economie"):
        em = p.domaine("economie").marches.get(m.lieu.id)
        if em is not None: em.non_servi[b] += q


def _besoin_site(s, b):''')], "def _rupture(p, m, b, q):")
patch("d15_logistique.py", [(
'''                if q <= EPS: m.demande[b] += need * 8; continue
''', '''                if q <= EPS:
                    m.demande[b] += need * 8; _rupture(p, m, b, need * 8); continue   # 27/09 : une rupture, pas un silence
'''), (
'''def _compter(d, mid, b, q):''', '''def _rupture(p, m, b, q):
    """Une demande d entreprise que le marche n a pas pu servir faute de stock : le signal de prix du marchand ( d03 )."""
    if q > 0.0 and p.a("economie"):
        em = p.domaine("economie").marches.get(m.lieu.id)
        if em is not None: em.non_servi[b] += q


def _compter(d, mid, b, q):''')], "def _rupture(p, m, b, q):")
