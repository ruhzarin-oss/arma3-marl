"""LES FRAPPES SUR LES OBJECTIFS REELS ( Arma a fond, etape 1b, HMT-192 ) : ce que la destruction de vrais batiments du
terrain d Arma fait dans le moteur. Les degats d un objectif ( guerre/objectifs.py ) valent la somme des poids de ses
composants ponderee par leur dommage ( [ 0 ; 1 ] ), sur le poids total. Une frappe n applique que la HAUSSE des degats.
Chaque effet passe par le chemin du domaine concerne, jamais par un stock ecrit a la main :
  centrale  ceil( degats x n ) groupes du domaine 11 en panne, cause « frappe » ( d11._panne ) ;
  fonderie  ceil( degats x n ) machines du domaine 10 en panne ; la reparation avance avec les heures d atelier ouvert
            ( d10._machines ), sur DUREE_REPARATION_J journees de poste ;
  depot     le carburant de l armee BRULE en proportion des cuves restantes detruites ( flux « brule » du moteur ) ;
  base      en proportion de ce qui reste : vehicules detruits ( d25.perdre_objet ), munitions et pieces perdues
            ( d25.tirer, perte_au_combat ), carburant de la garnison brule ;
  port      degats >= SEUIL_PORT : hors service pendant DUREE_REPARATION_J ( w.ports_hors_service ; le domaine 7 le traite
            comme un port tenu par l ennemi, correctif patch_port_detruit.py ) ;
  aeroport  aucun effet dans le moteur ( declare ).
LA REPARATION ( 1c ) : une duree sourcee, du jour ou elle est PAYEE a la remise en service, selon la gravite :
  centrale  60 j sous 0,5 de degats ( Kyiv, centrale de Darnytsia frappee le 03/02/2025 : « pas moins de deux mois »,
            le maire Klitschko, Kyiv Independent ) ; 365 j au-dela ( DTEK, S&P Global 28/03/2024 : les centrales gravement
            touchees « prendront un an a reconstruire » ) ;
  fonderie  105 j sous 0,5 ; 380 j au-dela ( Gen Re, Business Interruption Exposure : une usine detruite par le feu,
            3,5 mois pour reprendre ailleurs, 12,5 mois pour reconstruire ) ; en heures d atelier ouvert, 8 h x 5/7 par jour
            ( CHOIX ) : la reparation n avance que si l atelier tourne ;
  port      7 j ( Beyrouth, 2020 : le terminal a conteneurs reprend en partie une semaine apres l explosion, Al Jazeera
            12/08/2020, Lloyd s List ) ; il rouvre a pleine capacite ( CHOIX ).
Le materiel frappe ( groupes du domaine 11, machines du domaine 10 ) se paie a son prix au Parc : 100 % au-dela de 0,5
( remplacement ), PART_REPARATION en dessous ( CHOIX ), comme une importation ( d07.declarer_import ). Qui paie : l ETAT
pour une centrale ( import_etat ; en guerre l energie se reconstruit sur fonds publics - Ukraine : l Etat et l Energy
Support Fund ), apres avoir emprunte le manque ( d06.assurer : bons, puis avances de la banque centrale ) ; l ENTREPRISE
pour une fonderie ( import_biens ; CHOIX : les polices dommages excluent d ordinaire la guerre ) - sans caisse, elle reste
detruite ( 02/10 : une sonde hors porte a montre 0 dr dans la caisse de la centrale, 5 000 dr dans celle de la fonderie ). Faute de caisse, de devises, ou sous blocus, la reparation n a pas
lieu : le materiel reste hors service, et le paiement est retente chaque jour a 7 h ( une routine posee a la premiere
frappe seulement ). Ne sont pas comptes ( declare ) : la reconstruction des batiments, des bases et du depot ; les
vehicules detruits se rachetent par le budget.

   frapper( w, objectif, { indice de composant : dommage } )"""
import math

from monde import config as C

DUREES_J = {"centrale": (60.0, 365.0), "fonderie": (105.0, 380.0), "port": (7.0, 7.0)}   # ( sous 0,5 ; au-dela )
SEUIL_GRAVE = 0.5
PART_REPARATION = 0.3                                        # CHOIX : la part du prix d une reparation sous 0,5 de degats
JOURS_OUVRES = 5.0 / 7.0                                     # CHOIX : la semaine de l atelier
DUREE_REPARATION_J = {"centrale": None, "fonderie": None, "port": None}   # pour les portes : une duree forcee
SEUIL_PORT = 0.5                                                          # CHOIX
ATTENTE_H = 1e7                                              # une reparation non payee n avance pas
HEURE_RETENTE = 7.0


def duree_j(genre, d):
    """La duree de reparation d un objectif de ce genre a ces degats ( jours ), forcee par une porte si demande."""
    f = DUREE_REPARATION_J.get(genre)
    if f is not None: return float(f)
    a, b = DUREES_J[genre]
    return b if d >= SEUIL_GRAVE else a


def _reparations(w): return w.__dict__.setdefault("reparations", {})


def _poser_routine(w):
    p = w.pays
    if getattr(w, "routine_reparations", False): return
    p.routine(HEURE_RETENTE, 50, "guerre", retenter_reparations)
    w.routine_reparations = True


def _demarrer(w, r):
    """La reparation payee commence : chaque materiel frappe a sa date de remise en service."""
    p = w.pays; j = r["duree_j"]
    if r["genre"] == "centrale":
        E = p.domaine("energie")
        for u in E.unites:
            if u.id in r["materiel"] and u.en_panne: u.panne_jusqu = int(w.pas) + int(round(j * C.PAS_PAR_JOUR))
    elif r["genre"] == "fonderie":
        from monde.pays import d10_industrie as IN
        for s in IN._dom(p).sites:
            for a in s.ateliers:
                for m in a.machines:
                    if m.objet.id in r["materiel"]: m.repar_h = j * IN.HEURES_POSTE * JOURS_OUVRES
    r["paye_pas"] = int(w.pas)


PAYE_PAR_L_ETAT = ("centrale",)


def _payer(w, r):
    """Tente de payer une reparation ; rend vrai si elle commence."""
    from monde.pays import d07_exterieur as X, d06_etat as ET
    p = w.pays
    etat = r["genre"] in PAYE_PAR_L_ETAT
    e = w.gouv if etat else w.entreprises.get(r["lieu"])
    if e is None: return False
    caisse = float(e.caisse)
    if etat and r["montant_fob"] > 0 and p.a("etat") and not X.sous_blocus(p):
        ET.assurer(p, r["montant_fob"] * (1.0 + X.FRET.get("produit_fini", 0.05)))
    r["caisse_avant"] = caisse
    paye = X.declarer_import(p, e, r["montant_fob"], "produit_fini", "import_etat" if etat else "import_biens") \
        if r["montant_fob"] > 0 else 0.0
    if r["montant_fob"] > 0 and paye <= 0.0:
        r["refus"] = r.get("refus", 0) + 1; return False
    r["paye_dr"] = paye; r["baisse_caisse"] = caisse - float(e.caisse)
    _demarrer(w, r)
    w.noter("reparation_payee", objectif=r["lieu"], montant=round(paye, 2), jours=r["duree_j"])
    return True


def retenter_reparations(p):
    """7 h : chaque reparation en attente tente d etre payee."""
    w = p.w
    for r in _reparations(w).values():
        if r.get("paye_pas") is None: _payer(w, r)


def _ouvrir_reparation(w, o, d, materiel, prix):
    """Une reparation pour le materiel frappe ( { id : prix au Parc } ) ; payee tout de suite si possible."""
    part = 1.0 if d >= SEUIL_GRAVE else PART_REPARATION
    r = _reparations(w).get(o["id"])
    if r is None or r.get("paye_pas") is not None:
        r = {"lieu": o["id"], "genre": o["type"], "materiel": set(), "montant_fob": 0.0}
        _reparations(w)[o["id"]] = r
    r["materiel"] |= set(materiel)
    r["montant_fob"] += part * sum(prix[k] for k in materiel)
    r["duree_j"] = duree_j(o["type"], d); r["degats"] = d
    _poser_routine(w)
    _payer(w, r)
    return r


def degats(o, dommages):
    """Les degats ponderes de l objectif `o` pour { indice de composant : dommage }."""
    tot = o.get("poids_total") or 0.0
    if tot <= 0.0: return 0.0
    s = sum(c["poids"] * min(1.0, max(0.0, float(dommages.get(c["i"], 0.0)))) for c in o["composants"])
    return min(1.0, s / tot)


def _etat(w): return w.__dict__.setdefault("objectifs_degats", {})


def _frapper_centrale(w, o, d):
    from monde.pays import d11_energie as EN
    p = w.pays; E = p.domaine("energie")
    us = sorted((u for u in E.unites if u.lieu == o["id"]), key=lambda u: u.id)
    deja = w.__dict__.setdefault("groupes_frappes", set())
    cible = int(math.ceil(d * len(us) - 1e-9))
    a_faire = [u for u in us if u.id not in deja][:max(0, cible - len([u for u in us if u.id in deja]))]
    for u in a_faire:
        EN._panne(p, E, u, ATTENTE_H, "frappe"); deja.add(u.id)
    parc = p.socle.parc
    r = _ouvrir_reparation(w, o, d, [u.id for u in a_faire], {u.id: parc.modeles[u.objet.modele].prix_monde for u in a_faire})
    return {"groupes": len(us), "en_panne": len([u for u in us if u.id in deja]), "reparation": dict(r, materiel=sorted(r["materiel"]))}


def _frapper_fonderie(w, o, d):
    from monde.pays import d10_industrie as IN
    from monde.socle import objets as O
    p = w.pays; D_ = IN._dom(p)
    ms = [m for s in D_.sites if s.entreprise.lieu.id == o["id"] for a in s.ateliers for m in a.machines]
    deja = w.__dict__.setdefault("machines_frappees", set())
    cible = int(math.ceil(d * len(ms) - 1e-9))
    frappees = [m for m in ms if id(m.objet) in deja]
    nouvelles = [m for m in ms if id(m.objet) not in deja][:max(0, cible - len(frappees))]
    for m in nouvelles:
        p.socle.parc.mettre_en_etat(m.objet, O.PANNE)
        m.repar_h = ATTENTE_H; m.pm_h = 0.0
        deja.add(id(m.objet))
    parc = p.socle.parc
    r = _ouvrir_reparation(w, o, d, [m.objet.id for m in nouvelles],
                           {m.objet.id: parc.modeles[m.objet.modele].prix_monde for m in nouvelles})
    return {"machines": len(ms), "en_panne": len([m for m in ms if id(m.objet) in deja]),
            "reparation": dict(r, materiel=sorted(r["materiel"]))}


def _bruler(w, stock_dict, cle, q):
    q = min(float(stock_dict[cle]), max(0.0, q))
    stock_dict[cle] -= q; w.flux["brule"]["carburant"] += q
    return q


def _frapper_depot(w, o, f):
    q = _bruler(w, w.publics["armee"], "carburant", f * float(w.publics["armee"]["carburant"]))
    return {"carburant_brule": q}


def _frapper_base(w, o, f):
    from monde.pays import d25_armee as A
    p = w.pays; d = p.domaines[A.DOMAINE]; V = d.veh
    b = w.carte.lieux[o["id"]].n
    vk = [k for k in range(V.n) if V["base"][k] == b and V["oid"][k] >= 0]
    n = int(math.ceil(f * len(vk) - 1e-9))
    for k in vk[:n]: A.perdre_objet(p, int(V["oid"][k]), "detruit")
    arm = A.armurerie(p, o["id"]); perdu = {}
    for bien in A.NOMS_MUNITIONS + ("pieces",):
        q = f * float(arm.stock[d.bids[bien]])
        if q > 0: perdu[bien] = A.tirer(p, o["id"], bien, q, "perte_au_combat")
    carb = _bruler(w, w.garnisons[o["id"]], "carburant", f * float(w.garnisons[o["id"]]["carburant"])) \
        if o["id"] in getattr(w, "garnisons", {}) else 0.0
    return {"vehicules_detruits": n, "perdu": perdu, "carburant_brule": carb}


def _frapper_port(w, o, d):
    hs = w.__dict__.setdefault("ports_hors_service", {})
    if d >= SEUIL_PORT:
        fin = int(w.pas) + int(round(duree_j("port", d) * C.PAS_PAR_JOUR))
        hs[o["id"]] = max(hs.get(o["id"], 0), fin)
    return {"hors_service_jusqu_au_pas": hs.get(o["id"])}


def frapper(w, o, dommages):
    """Applique la hausse des degats de l objectif `o` ( guerre/objectifs.objectifs_carte ) dans le monde `w` de son ile.
    Rend ( degats, effets )."""
    etat = _etat(w); avant = etat.get(o["id"], 0.0)
    d = max(avant, degats(o, dommages))
    if d <= avant + 1e-12: return d, {}
    f = (d - avant) / (1.0 - avant) if avant < 1.0 else 0.0      # la part de CE QUI RESTE que la frappe detruit
    t = o["type"]
    if t == "centrale": eff = _frapper_centrale(w, o, d)
    elif t == "fonderie": eff = _frapper_fonderie(w, o, d)
    elif t == "depot": eff = _frapper_depot(w, o, f)
    elif t == "base": eff = _frapper_base(w, o, f)
    elif t == "port": eff = _frapper_port(w, o, d)
    else: eff = {}
    if t != "aeroport":                                   # un aeroport n a pas d effet dans le moteur : rien n est note
        etat[o["id"]] = d
        w.noter("frappe", objectif=o["id"], genre=t, degats=round(d, 4))
    return d, eff
