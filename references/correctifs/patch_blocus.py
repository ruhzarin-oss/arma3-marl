"""29/09 ( chef de projet : go ; porte G25 ) : le port pris, c est le blocus. Un port est tenu quand son lieu est dans une
zone occupee ( guerre/moteur.occuper : w.occupations ) ; l ile est sous blocus quand elle a un port et que l ennemi les
tient tous - aucun drapeau, la regle se relit a chaque appel. Rien n entre ni ne sort par la mer : les imports
( importer_au_port, declarer_import ) et les exports ( exporter_au_port ) sont refuses et comptes ( import_blocus,
export_blocus ), personne ne part ( _peut_partir ) ; le refus d import du gouvernement dit « blocus ». Sans occupation,
rien ne change. Le meme texte pour le depot et pour l arbre des references ; une ancre absente de l arbre ( fonction nee
apres 5917fa8 ) est passee. Idempotent.
   python patch_blocus.py racine_de_l_arbre"""
import os, sys
R = sys.argv[1]


def _nouveau(a, b):
    """La premiere ligne de `b` absente de `a` : le marqueur d une insertion ( chaque insertion de ce correctif en a une
    qui lui est propre ; un texte deja insere ne l est pas deux fois, meme si une insertion voisine l a coupe )."""
    return next((l for l in b.splitlines() if l.strip() and l not in a.splitlines()), None)


def remplacer(chemin, paires, facultatives=()):
    f = os.path.join(R, chemin)
    if not os.path.exists(f): print("absent :", f); return
    s = open(f).read(); n = 0
    for a, b in paires:
        m = _nouveau(a, b)
        if b in s or (m is not None and m in s): continue       # deja fait
        if s.count(a) != 1:
            if a in facultatives: print(f"ancre absente, passee : {chemin} {a[:50]!r}"); continue
            raise SystemExit(f"{chemin} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


FONCTION = '''# ================================================================== le blocus ( 29/09, guerre des iles )
def ports_tenus(p):
    """Les ports de l ile ( lieux de type port ) dans une zone occupee par l ennemi ( guerre/moteur.occuper :
    w.occupations ) ; la regle se relit a chaque appel, aucun drapeau."""
    w = p.w; occ = getattr(w, "occupations", None)
    if not occ: return ()
    tenus = {l for o in occ.values() for l in o.get("lieux", ())}
    return tuple(sorted(l for l in tenus if l in w.carte.lieux and w.carte.lieux[l].type == "port"))


def sous_blocus(p):
    """Le blocus ( 29/09, chef de projet ; Hodeidah 2017, Gaza ) : l ile a un port et l ennemi les tient tous. Rien
    n entre ni ne sort par la mer : les imports ( importer_au_port, declarer_import ) et les exports ( exporter_au_port )
    sont refuses et comptes ( import_blocus, export_blocus ), personne ne part ( _peut_partir ) ; le domaine 28 n attend
    plus de touristes, le domaine 15 annule ses lots par ce port. Un port libre leve le blocus. La contrebande continue
    ( elle force les blocus ). Choix ecrits ( a verifier ) : un aeroport libre ne rouvre ni le fret ni le tourisme ; les
    navires deja en mer font demi-tour ( leur arrivee est refusee )."""
    w = p.w
    if not getattr(w, "occupations", None): return False
    ports = [l for l, x in w.carte.lieux.items() if x.type == "port"]
    return bool(ports) and set(ports) <= set(ports_tenus(p))


def importer_au_port(p, importateur, stock, bien, q, motif="import_biens", droits=True):'''

remplacer("monde/pays/d07_exterieur.py", [
    ('''def importer_au_port(p, importateur, stock, bien, q, motif="import_biens", droits=True):''', FONCTION),
    ('''    fob = prix_port(p, b); fret = fret_unitaire(p, b)
''', '''    fob = prix_port(p, b); fret = fret_unitaire(p, b)
    if sous_blocus(p):                                   # ( 29/09 ) le blocus : rien n entre par la mer
        p.compter("import_blocus", q * (fob + fret)); return 0.0, 0.0
'''),
    ('''    fret = valeur_fob * FRET.get(famille, 0.05)
''', '''    fret = valeur_fob * FRET.get(famille, 0.05)
    if sous_blocus(p):                                   # ( 29/09 ) le blocus : ni vehicule ni arme n entrent
        p.compter("import_blocus", valeur_fob + fret); return 0.0
'''),
    ('''    nom = p.socle.catalogue[b].nom
    q = L.exporter(stock, b, q, motif)
''', '''    nom = p.socle.catalogue[b].nom
    if sous_blocus(p):                                   # ( 29/09 ) le blocus : rien ne sort par la mer
        p.compter("export_blocus", q * prix_export(p, b)); return 0.0, 0.0
    q = L.exporter(stock, b, q, motif)
'''),
    ('''def _peut_partir(p, gens):
    w = p.w
''', '''def _peut_partir(p, gens):
    w = p.w
    if sous_blocus(p): return False                      # ( 29/09 ) le blocus : aucun navire ne part
'''),
    # ( chef de projet, integration 12 ) ancre courte : la garde du negoce ( patch_garde_import, avant dans la chaine ) a
    # deja ajoute « import_borne » en fin de liste ; les deux correctifs se composent dans les deux ordres
    ('''"depart_empeche", "devises_refusees"''',
     '''"depart_empeche", "devises_refusees", "import_blocus", "export_blocus"'''),
    ('''    if "devises_refusees" not in getattr(J, "types", {}): J.declarer("devises_refusees", "exterieur", "compte")
''', '''    for t in ("devises_refusees", "import_blocus", "export_blocus"):          # ( 29/09 ) et ceux du blocus
        if t not in getattr(J, "types", {}): J.declarer(t, "exterieur", "compte")
'''),
    # les marchandises payees hors du port ( payer_en_devises ), les exports hors d exporter_au_port ( premier essai de
    # G25 : le fioul des centrales, d11, arrivait au septieme jour du blocus ; les ventes du negoce agricole partaient )
    ('''def sous_blocus(p):
''', '''MARCHANDISES_HORS_PORT = ("achat_abri", "second_oeuvre", "equipement_telecom", "papier_journal", "investissement")
# ( 29/09 ) les marchandises payees a l etranger par payer_en_devises : tout motif import_* ( le fioul des centrales, les
# materiaux, les medicaments, le grossiste ) et ceux-ci ( les abris, le second oeuvre, l equipement des medias, les
# machines de d03.investir ). Le reste de ce qui y passe est financier ( dividendes, capitaux, transferts des migrants,
# droits ) : le blocus ne l arrete pas, la contrebande non plus.


def marchandise(motif):
    return motif.startswith("import_") or motif in MARCHANDISES_HORS_PORT


def export_bloque(p, valeur):
    """( 29/09 ) Un export hors d exporter_au_port ( le negoce agricole, le petrole, les vehicules d occasion ) : sous
    blocus il ne part pas - compte export_blocus et rend vrai ; l appelant garde son bien."""
    if not sous_blocus(p): return False
    p.compter("export_blocus", valeur); return True


def sous_blocus(p):
'''),
    ('''    if not p.a("exterieur"): return L.payer_l_exterieur(de, montant, motif)
''', '''    if not p.a("exterieur"): return L.payer_l_exterieur(de, montant, motif)
    if marchandise(motif) and sous_blocus(p):            # ( 29/09 ) le blocus : la marchandise n arrive pas
        p.compter("import_blocus", montant); return 0.0
'''),
    ('''    if not p.a("exterieur") or montant <= EPS: return 1.0
''', '''    if not p.a("exterieur") or montant <= EPS: return 1.0
    if sous_blocus(p): return 0.0                        # ( 29/09 ) ses appelants achetent des marchandises ( d13 )
'''),
    ('''    if montant > EPS: p.compter("devises_refusees", montant)
''', '''    if montant > EPS: p.compter("import_blocus" if sous_blocus(p) else "devises_refusees", montant)
'''),
    ('''        q, gain = exporter_au_port(p, w.gouv, StockE1(w.publics["reserve"], p.socle.catalogue), "or", q, "export_or_etat")
''', '''        q, gain = exporter_au_port(p, w.gouv, StockE1(w.publics["reserve"], p.socle.catalogue), "or", q, "export_or_etat")
        if q <= 0.0 and sous_blocus(p): return False, "blocus : l ennemi tient le port, l or ne part pas"
'''),
], facultatives=('''    if "devises_refusees" not in getattr(J, "types", {}): J.declarer("devises_refusees", "exterieur", "compte")
''', '''    if not p.a("exterieur") or montant <= EPS: return 1.0
''', '''    if montant > EPS: p.compter("devises_refusees", montant)
'''))

remplacer("monde/pays/d09_agriculture.py", [
    ('''    """Vend au negoce ( exportation ) : le bien sort du pays, l exterieur paie la caisse de la ferme."""
    pris = _sortir(p, A, ex, nom, q, "exporte", "vente_negoce")
''', '''    """Vend au negoce ( exportation ) : le bien sort du pays, l exterieur paie la caisse de la ferme."""
    # ( 29/09 ) le blocus : sous blocus, la vente au negoce ne part pas ( d07.export_bloque )
    from . import d07_exterieur as X
    if X.export_bloque(p, q * p.socle.catalogue[nom].prix_monde * PARITE_NEGOCE): return 0.0
    pris = _sortir(p, A, ex, nom, q, "exporte", "vente_negoce")
'''),
])

remplacer("monde/pays/d11_energie.py", [
    ('''        q = L.exporter(E.depot.stock, i, E.depot.stock[i] - garde, "export_petrolier")
''', '''        if importlib.import_module(".d07_exterieur", __package__).export_bloque(p, (E.depot.stock[i] - garde) * cat[b].prix_monde):
            continue                                     # ( 29/09 ) le blocus : le petrole reste au depot
        q = L.exporter(E.depot.stock, i, E.depot.stock[i] - garde, "export_petrolier")
'''),
])

remplacer("monde/pays/d14_transport.py", [
    ('''        v = _valeur_fiche(p, CARAC[m], tr.fiches[oid]) * DECOTE_IMPORT_OCCASION
        del conc.occasions[oid]
''', '''        v = _valeur_fiche(p, CARAC[m], tr.fiches[oid]) * DECOTE_IMPORT_OCCASION
        if EXT.export_bloque(p, v): break                # ( 29/09 ) le blocus : l occasion reste chez le concessionnaire
        del conc.occasions[oid]
'''),
])

remplacer("monde/gouvernement.py", [
    ('''                if recu is not None and recu <= 1e-9:
                    return False, f"import refuse : rien n est entre sur {q:.0f} ( devises de la banque centrale ou caisse de l Etat )"
''', '''                if recu is not None and recu <= 1e-9:
                    pays = getattr(monde, "pays", None)             # ( 29/09 ) le blocus : le gouvernement doit savoir pourquoi
                    if pays is not None and pays.a("exterieur"):
                        from .pays import d07_exterieur as X
                        if X.sous_blocus(pays):
                            return False, "import refuse : blocus, l ennemi tient le port ( rien n entre ni ne sort par la mer )"
                    return False, f"import refuse : rien n est entre sur {q:.0f} ( devises de la banque centrale ou caisse de l Etat )"
'''),
], facultatives=('''                if recu is not None and recu <= 1e-9:
                    return False, f"import refuse : rien n est entre sur {q:.0f} ( devises de la banque centrale ou caisse de l Etat )"
''',))
