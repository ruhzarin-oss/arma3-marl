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
Durees de reparation : des CHOIX a sourcer ( HMT-192, 1c ).

   frapper( w, objectif, { indice de composant : dommage } )"""
import math

from monde import config as C

DUREE_REPARATION_J = {"centrale": 180.0, "fonderie": 60.0, "port": 30.0}   # CHOIX ( 1c : a sourcer )
SEUIL_PORT = 0.5                                                          # CHOIX


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
        EN._panne(p, E, u, DUREE_REPARATION_J["centrale"] * 24.0, "frappe"); deja.add(u.id)
    return {"groupes": len(us), "en_panne": len([u for u in us if u.id in deja])}


def _frapper_fonderie(w, o, d):
    from monde.pays import d10_industrie as IN
    from monde.socle import objets as O
    p = w.pays; D_ = IN._dom(p)
    ms = [m for s in D_.sites if s.entreprise.lieu.id == o["id"] for a in s.ateliers for m in a.machines]
    deja = w.__dict__.setdefault("machines_frappees", set())
    cible = int(math.ceil(d * len(ms) - 1e-9))
    frappees = [m for m in ms if id(m.objet) in deja]
    for m in [m for m in ms if id(m.objet) not in deja][:max(0, cible - len(frappees))]:
        p.socle.parc.mettre_en_etat(m.objet, O.PANNE)
        m.repar_h = DUREE_REPARATION_J["fonderie"] * IN.HEURES_POSTE; m.pm_h = 0.0
        deja.add(id(m.objet))
    return {"machines": len(ms), "en_panne": len([m for m in ms if id(m.objet) in deja])}


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
        fin = int(w.pas) + int(round(DUREE_REPARATION_J["port"] * C.PAS_PAR_JOUR))
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
