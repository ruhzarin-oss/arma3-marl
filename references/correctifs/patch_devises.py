"""27/09 ( HMT-131 ) : une seule porte de sortie des devises. Toute sortie d argent vers l etranger hors des imports du
domaine 7 passe par exterieur.payer_en_devises, qui demande les devises a la banque centrale ( _controle_devises ) :
21 paiements des domaines 3, 7, 11, 13, 15, 16, 17, 20, 22 et 23 partaient sans elles et vidaient les reserves sous zero
( guerre des iles : le fioul des centrales, d11, vidait seul celles de Stratis et de Malden ; la nourriture, elle
controlee, ne recevait plus rien ). Tant que les reserves suffisent, rien ne change ( lecture seule, meme paiement ).
Le meme texte pour le depot et pour l arbre des references ; les fichiers absents ( domaines nes apres 5917fa8 ) sont
passes. Idempotent.
   python patch_devises.py racine_de_l_arbre"""
import os, sys
R = os.path.join(sys.argv[1], "monde", "pays")


def lire(nom):
    f = os.path.join(R, nom)
    return (f, open(f).read()) if os.path.exists(f) else (f, None)


def remplacer(nom, paires):
    f, s = lire(nom)
    if s is None: print("absent :", f); return
    n = 0
    for a, b in paires:
        if b in s and a not in s: continue                      # deja fait
        if a in b and b in s: continue                          # une insertion ( le texte garde son ancre ) deja faite
        if s.count(a) != 1: raise SystemExit(f"{nom} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


FONCTION = '''# ================================================================== la sortie des devises ( 27/09, HMT-131 )
def _dispo_euros(p, e):
    """Les reserves de ce moment moins le plancher, en LECTURE SEULE : les flux du grand livre depuis le dernier suivi,
    convertis au taux du jour comme les rangerait _suivre_reserves, sans les ranger."""
    L = p.socle.livre
    return e.reserves_euros + (L.ext["entree"] - L.ext["sortie"] - e.ext_reserves) * e.taux - PLANCHER_RESERVES


def refuser_devises(p, montant):
    """Compte une demande de devises refusee par un appelant qui a lu part_en_devises avant de payer."""
    if montant > EPS: p.compter("devises_refusees", montant)


def part_en_devises(p, montant):
    """La part de `montant` ( monnaie de l ile ) que la banque centrale fournirait maintenant, en LECTURE SEULE."""
    if not p.a("exterieur") or montant <= EPS: return 1.0
    e = _ext(p); euros = montant * e.taux; d = _dispo_euros(p, e)
    return 1.0 if d >= euros else max(0.0, d / euros)


def payer_en_devises(p, de, montant, motif, essentiel=False, entier=False):
    """TOUTE sortie d argent vers l etranger hors des imports de ce domaine passe ici ( 27/09, HMT-131 ). Tant que les
    reserves suffisent, c est le paiement direct, a l identique ( lecture seule ). Sinon la banque centrale fournit ce
    qu elle peut ( _controle_devises ) et le reste ne part pas ( compte devises_refusees, en demandes : un importateur
    qui redemande chaque heure est compte chaque heure ). Ce qui n est pas paye n arrive pas : l appelant achete moins
    ( fioul, medicaments, materiaux, machines, second oeuvre ), renonce a l objet ( entier : un abri importe ), ou garde
    au pays le dividende, le capital, le transfert, les droits - le controle des capitaux grec de juin 2015. Chaque
    paiement relit le grand livre : dix paiements du meme pas voient chacun les reserves laissees par le precedent.
    `essentiel` : nourriture, medicaments, energie. Rend le paye."""
    L = p.socle.livre
    if not p.a("exterieur"): return L.payer_l_exterieur(de, montant, motif)
    e = _ext(p)
    euros = montant * e.taux
    if _dispo_euros(p, e) >= euros: return L.payer_l_exterieur(de, montant, motif)
    part = _controle_devises(p, e, euros)
    if entier and part < 1.0: part = 0.0
    refuse = montant * (1.0 - part)
    if refuse > EPS: p.compter("devises_refusees", refuse)
    return L.payer_l_exterieur(de, montant * part, motif) if part > 0.0 else 0.0


# ================================================================== la douane
def _declarer(p, e, sens, motif, bien, q, valeur, droit=0.0, declarant="exterieur"):'''

remplacer("d07_exterieur.py", [
    ('''# ================================================================== la douane
def _declarer(p, e, sens, motif, bien, q, valeur, droit=0.0, declarant="exterieur"):''', FONCTION),
    ('''              "envoi_de_fonds", "aide_ue", "depart_empeche"):
        J.declarer(t, "exterieur", "compte")''',
     '''              "envoi_de_fonds", "aide_ue", "depart_empeche", "devises_refusees"):
        J.declarer(t, "exterieur", "compte")'''),
    ('''            paye = L.payer_l_exterieur(cb, q * cout, "contrebande")''',
     '''            paye = payer_en_devises(p, cb, q * cout, "contrebande")'''),
    ('''    x = L.payer_l_exterieur(mg, part, "transfert_migrant") if part > 0 else 0.0''',
     '''    x = payer_en_devises(p, mg, part, "transfert_migrant") if part > 0 else 0.0'''),
])
EX = 'importlib.import_module(".d07_exterieur", __package__)'
remplacer("d03_economie.py", [
    ('''else L.payer_l_exterieur(unite, montant, motif)''',
     f'''else {EX}.payer_en_devises(p, unite, montant, motif)'''),
])
remplacer("d11_energie.py", [
    ('''                paye = L.payer_l_exterieur(res.proprietaire, manque * prix, "import_combustible")''',
     f'''                paye = {EX}.payer_en_devises(p, res.proprietaire, manque * prix, "import_combustible", essentiel=True)'''),
    ('''    paye = L.payer_l_exterieur(E.raffinerie, q * parite, "import_combustible")''',
     f'''    paye = {EX}.payer_en_devises(p, E.raffinerie, q * parite, "import_combustible", essentiel=True)'''),
    ('''                paye = L.payer_l_exterieur(u.reservoir.proprietaire, q * prix, "import_combustible")''',
     f'''                paye = {EX}.payer_en_devises(p, u.reservoir.proprietaire, q * prix, "import_combustible", essentiel=True)'''),
])
remplacer("d13_immobilier.py", [
    ('''    p.socle.livre.payer_l_exterieur(g, prix, "achat_abri")''',
     f'''    EX = {EX}
    if EX.part_en_devises(p, prix) < 1.0:                 # pas de devises : l abri importe n arrive pas ( refus compte )
        EX.payer_en_devises(p, g, prix, "achat_abri", entier=True); return None
    EX.payer_en_devises(p, g, prix, "achat_abri")'''),
    ('''        b = _abri(p, d, mg.domicile, n)
        _occuper(p, d, mg, b, ABRI)''',
     '''        b = _abri(p, d, mg.domicile, n)
        if b is None: continue                            # ni reserve ni devises : il cherche toujours, sans abri
        _occuper(p, d, mg, b, ABRI)'''),
    ('''                    paye = p.socle.livre.payer_l_exterieur(ch.btp, manque * pu, "import_materiaux")''',
     f'''                    paye = {EX}.payer_en_devises(p, ch.btp, manque * pu, "import_materiaux")'''),
    ('''    delta = nouvelle - ch.avancement
    if delta <= 1e-12: return
    for x, q in sorted(ch.besoins.items()):''',
     f'''    delta = nouvelle - ch.avancement
    if delta <= 1e-12: return
    EX = {EX}
    part = EX.part_en_devises(p, PART_SECOND_OEUVRE * ch.devis * delta)
    if part < 1.0:                                        # le second oeuvre importe non paye : le chantier n avance que d autant
        EX.refuser_devises(p, PART_SECOND_OEUVRE * ch.devis * delta * (1.0 - part))
        nouvelle = ch.avancement + delta * part; delta = nouvelle - ch.avancement
        if delta <= 1e-12: return
    for x, q in sorted(ch.besoins.items()):'''),
    ('''    f = L.payer_l_exterieur(ch.btp, PART_SECOND_OEUVRE * ch.devis * delta, "second_oeuvre")''',
     '''    f = EX.payer_en_devises(p, ch.btp, PART_SECOND_OEUVRE * ch.devis * delta, "second_oeuvre")'''),
])
remplacer("d16_medecine.py", [
    ('''            paye = L.payer_l_exterieur(w.gouv, voulu * mol.prix, "import_produits_sante")''',
     '''            from . import d07_exterieur as EX
            paye = EX.payer_en_devises(p, w.gouv, voulu * mol.prix, "import_produits_sante", essentiel=True)'''),
])
# les domaines nes apres 5917fa8 ( absents de l arbre des references d origine )
remplacer("d15_logistique.py", [
    ('''        L.payer_l_exterieur(tr, tr.caisse - garde, "rapatriement_capital")''',
     '''        EXT.payer_en_devises(p, tr, tr.caisse - garde, "rapatriement_capital")'''),
])
remplacer("d17_hopitaux.py", [
    ('''        paye = L.payer_l_exterieur(g, q * prix, "import_grossiste")''',
     '''        from . import d07_exterieur as EX
        paye = EX.payer_en_devises(p, g, q * prix, "import_grossiste", essentiel=True)'''),
])
remplacer("d20_assurances.py", [
    ('''                y = L.payer_l_exterieur(A, min(DIVIDENDE_PART * A.resultat, max(0.0, A.fp - DIVIDENDE_RATIO * A.scr)),
                                        "dividende_assureur")''',
     '''                y = EXT.payer_en_devises(p, A, min(DIVIDENDE_PART * A.resultat, max(0.0, A.fp - DIVIDENDE_RATIO * A.scr)),
                                         "dividende_assureur")'''),
    ('''    y = p.socle.livre.payer_l_exterieur(A, montant, "dividende_assureur"); D.cpt["dividende_assureur"] += y''',
     '''    y = EXT.payer_en_devises(p, A, montant, "dividende_assureur"); D.cpt["dividende_assureur"] += y'''),
])
remplacer("d22_medias.py", [
    ('''    if imp > 0: L.payer_l_exterieur(x, imp, "equipement_telecom" if tel else "papier_journal")''',
     '''    from . import d07_exterieur as EX
    if imp > 0: EX.payer_en_devises(p, x, imp, "equipement_telecom" if tel else "papier_journal")'''),
    ('''            L.payer_l_exterieur(x, exces * x.part_etrangere, "dividende_exterieur_telecom")''',
     '''            EX.payer_en_devises(p, x, exces * x.part_etrangere, "dividende_exterieur_telecom")'''),
])
remplacer("d23_culture.py", [
    ('''            x = L.payer_l_exterieur(e, p_ext * ht, "droits_films"); d.compte["droits_films"] += x; e.verse_exterieur += x''',
     '''            from . import d07_exterieur as EX
            x = EX.payer_en_devises(p, e, p_ext * ht, "droits_films"); d.compte["droits_films"] += x; e.verse_exterieur += x'''),
])
