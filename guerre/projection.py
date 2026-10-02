"""LA FLOTTE DE PROJECTION ( Arma a fond, etape 4a, HMT-197 ) : de vrais chalands et de vrais avions de transport, pour
qu une ile puisse porter la guerre chez n importe quelle autre ( Younes, 03/10 : « vrais bateaux payes », « avions pour
les parachutistes » ).

Les engins sont des objets du Parc au depot national du domaine 26 ( comme ses helicopteres d evacuation ), achetes par
l Etat a l etranger ( d07.declarer_import, motif import_armement : prix FOB, fret, devises, refus sous blocus ). Une
traversee porte des hommes sur des engins libres : la duree est km / vitesse, le carburant de l aller est brule au
depart ( le chaland : le gazole du stock de l armee ; l avion : le kerosene du depot national ), celui du retour au
retour ; l engin est reserve jusqu a son retour.

Les modeles ( sources dans MODELES ) :
  lcu        chaland de debarquement : la capacite du LCU-1600 ( 170 t, ou 3 chars, ou 400 hommes ; 11 noeuds charge ;
             1 100 milles - GlobalSecurity, US Navy ), le prix du LCU 1700 qui le remplace ( NAVSEA et Swiftships,
             option de 2019 : 50,1 M$ pour 4, soit 12,5 M$ ; 1 euro = 1,1195 $ en 2019, BCE ) ; corps Arma
             CUP_B_LCU1600_USMC ( 51 places dans Arma ) ; consommation a calibrer ( CHOIX : deux diesels Detroit 12V-71
             de ~ 500 kW, a 70 %, ~ 210 g/kWh : ~ 150 kg/h de gazole ).
  c130j      avion de transport C-130J : 92 hommes ou 64 parachutistes, 18 955 kg, 628 km/h en croisiere economique
             ( Lockheed, GlobalSecurity ) ; 2 455 kg/h de kerosene, derive de 20 519 kg pour 5 250 km avec 18 t ; prix
             62 M$ a l unite au depart de l usine ( 2008 ; 1 euro = 1,4708 $ en 2008, BCE ), a actualiser ; corps Arma
             CUP_B_C130J_USMC ( 60 places dans Arma ).
CHOIX : la livraison au jour de l achat ( marche de l occasion ou stocks d un allie ; un engin neuf demanderait 1 a 3 ans,
a calibrer ) ; aucune qualification de parachutiste au domaine 25 ( tout soldat saute ) ; les equipages de la marine
et de l air ne sont pas modelises ; la traversee vaut carte.km_mer ( 120 km entre iles, valeur d attente du moteur ) ;
l avion ajoute 0,4 h de roulage, montee et approche ( BLOC_SUPPLEMENT_H du domaine 15 ) ; l Etat emprunte ce qui
lui manque pour payer ( d06.assurer, comme la reparation d une centrale frappee ).

Rien ne change tant qu aucune fonction n est appelee ( porte P3 )."""
import math

from monde import config as C
from monde.pays import d07_exterieur as X, d15_logistique as LG, d25_armee as A, d26_armee_soutien as S

FAMILLE = "produit_fini"                  # la famille de l armement importe ( guerre/moteur.FAMILLE_ARMEMENT )
DENSITE_GAZOLE, DENSITE_KEROSENE = 0.84, 0.80
EPS = 1e-9


class Modele:
    __slots__ = ("nom", "genre", "prix_eur", "masse_kg", "vie_h", "arma", "hommes", "parachutistes", "charge_t",
                 "vitesse_kmh", "conso_kg_h", "carburant", "bloc_h", "source")

    def __init__(self, nom, genre, prix_eur, masse_kg, vie_h, arma, hommes, parachutistes, charge_t, vitesse_kmh,
                 conso_kg_h, carburant, bloc_h, source):
        self.nom, self.genre, self.prix_eur, self.masse_kg, self.vie_h, self.arma = nom, genre, prix_eur, masse_kg, vie_h, arma
        self.hommes, self.parachutistes, self.charge_t, self.vitesse_kmh = hommes, parachutistes, charge_t, vitesse_kmh
        self.conso_kg_h, self.carburant, self.bloc_h, self.source = conso_kg_h, carburant, bloc_h, source

    def unites_h(self):
        """La consommation en unites de 10 litres par heure."""
        dens = DENSITE_GAZOLE if self.carburant == "carburant" else DENSITE_KEROSENE
        return self.conso_kg_h / dens / A.LITRES_UNITE


MODELES = {
    "lcu": Modele("lcu", "chaland", 12.5e6 / 1.1195, 390 * 1016.0, 30 * 3000.0, "CUP_B_LCU1600_USMC", 400, 0, 170.0,
                  11 * 1.852, 150.0, "carburant", 0.0,
                  "LCU-1600 ( capacite : 170 t, 3 chars ou 400 hommes, 11 noeuds charge, 1 100 milles ; 390 t a pleine "
                  "charge - GlobalSecurity ) ; prix du LCU 1700 ( NAVSEA, option 2019 : 50,1 M$ pour 4 ) ; conso a "
                  "calibrer ( 2 x 12V-71 ~ 500 kW a 70 %, 210 g/kWh )"),
    "c130j": Modele("c130j", "avion", 62e6 / 1.4708, 34274.0, 50000.0, "CUP_B_C130J_USMC", 92, 64, 18.955, 628.0,
                    2455.0, "kerosene", LG.BLOC_SUPPLEMENT_H,
                    "C-130J ( 92 hommes, 64 parachutistes, 18 955 kg, 628 km/h, 20 519 kg de carburant pour 5 250 km "
                    "avec 18 t - Lockheed, GlobalSecurity ) ; 62 M$ en 2008 ( Wikipedia ), a actualiser"),
}


def _P(w):
    return w.__dict__.setdefault("projection", {"flotte": {}, "libre": {}, "traversees": [], "prochaine": 1, "mids": {}})


def _mid(w, nom):
    """Le modele du Parc ( declare a la premiere demande )."""
    p = w.pays; parc = p.socle.parc; P = _P(w); m = MODELES[nom]
    if nom not in P["mids"]:
        x = parc.par_nom.get("projection_" + nom)
        if x is None:
            x = parc.declarer_modele("projection_" + nom, "aeronef" if m.genre == "avion" else "navire", S._dr(m.prix_eur),
                                     m.masse_kg, m.vie_h, m.arma, None, m.source)
        P["mids"][nom] = x.id
    return P["mids"][nom]


def lieu_de_base(w, nom):
    """Le chaland au port de l ile ; l avion a l aerodrome ( le lieu le plus proche de l objectif aeroport ), a defaut la
    capitale."""
    c = w.carte; ile = c.par_n[0].ile
    if MODELES[nom].genre == "chaland":
        port = c.port(ile)
        return port.id if port is not None else c.gouvernement.id
    try:
        from guerre import objectifs as OB
        aer = [o for o in OB.objectifs_carte(ile.lower()) if o["type"] == "aeroport"]
    except Exception:
        aer = []
    if aer:
        x, y = aer[0]["pos"][:2]
        return c.par_n[S._lieu_proche(w.pays, S._dom(w.pays), float(x), float(y), c.iles.index(ile))].id
    return c.gouvernement.id


def acheter(w, nom, n=1):
    """L Etat achete n engins a l etranger. Rend { achetes, paye, objets }."""
    p = w.pays; d = S._dom(p); parc = p.socle.parc; P = _P(w); m = MODELES[nom]
    lieu = lieu_de_base(w, nom); mid = _mid(w, nom); out = {"achetes": 0, "paye": 0.0, "objets": []}
    fob = S._dr(m.prix_eur)
    for _ in range(int(n)):
        if p.a("etat") and not X.sous_blocus(p):          # le manque est emprunte ( d06 : bons, puis avances )
            from monde.pays import d06_etat as ET
            ET.assurer(p, fob * (1.0 + X.FRET.get(FAMILLE, 0.05)))
        paye = X.declarer_import(p, w.gouv, fob, FAMILLE, motif="import_armement")
        if paye <= 0: break
        o = parc.creer(mid, d.national, lieu, "importe", w.pas)
        P["flotte"][int(o.id)] = nom; P["libre"][int(o.id)] = int(w.pas)
        out["achetes"] += 1; out["paye"] += paye; out["objets"].append(int(o.id))
    if out["achetes"]: w.noter("achat_projection", modele=nom, engins=out["achetes"], paye=round(out["paye"], 2))
    return out


def libres(w, nom):
    P = _P(w)
    return [o for o, x in sorted(P["flotte"].items()) if x == nom and P["libre"].get(o, -1) <= int(w.pas)]


def duree_h(w, nom, km=None):
    m = MODELES[nom]
    if km is None: km = KM_TRAVERSEE
    return km / m.vitesse_kmh + m.bloc_h


KM_TRAVERSEE = 120.0                      # carte.km_mer entre deux iles ( valeur d attente du moteur, a calibrer )


def _stock_carburant(w, nom):
    p = w.pays; d = S._dom(p); m = MODELES[nom]
    return S._quantite(p, d, "depot", d.national.k, m.carburant)


def traverser(w, nom, hommes, parachutage=False, km=None):
    """Une traversee de `hommes` sur les engins libres du modele : le carburant de l aller est brule au depart, les engins
    sont reserves jusqu a leur retour. Rend { ok, raison } ou { ok, id, engins, depart, arrivee, retour, carburant }."""
    p = w.pays; d = S._dom(p); P = _P(w); m = MODELES[nom]
    km = KM_TRAVERSEE if km is None else float(km)
    if parachutage and m.genre != "avion": return {"ok": False, "raison": "un parachutage demande un avion"}
    par = m.parachutistes if parachutage else m.hommes
    besoin = math.ceil(int(hommes) / par) if par > 0 else 10 ** 9
    lib = libres(w, nom)
    if not lib: return {"ok": False, "raison": f"aucun {nom} libre"}
    if besoin > len(lib): return {"ok": False, "raison": f"capacite : {hommes} hommes demandent {besoin} {nom}, {len(lib)} libres"}
    h = duree_h(w, nom, km)
    q = m.unites_h() * h * besoin
    if _stock_carburant(w, nom) < q - EPS: return {"ok": False, "raison": f"pas assez de {m.carburant} pour l aller"}
    _motif(p)
    S._sortir(p, d, "depot", d.national.k, m.carburant, q, MOTIF_CARBURANT, "brule")
    pas = max(1, math.ceil(h * C.PAS_PAR_JOUR / 24.0 - 1e-9))
    engins = lib[:besoin]
    for o in engins: P["libre"][o] = int(w.pas) + 2 * pas
    t = {"id": P["prochaine"], "modele": nom, "engins": engins, "hommes": int(hommes), "parachutage": bool(parachutage),
         "depart": int(w.pas), "arrivee": int(w.pas) + pas, "retour": int(w.pas) + 2 * pas, "km": km, "carburant": q,
         "retour_brule": False}
    P["prochaine"] += 1; P["traversees"].append(t)
    w.noter("traversee", modele=nom, engins=len(engins), hommes=int(hommes), arrivee=t["arrivee"])
    return {"ok": True, **t}


MOTIF_CARBURANT = "carburant_projection"


def _motif(p):
    L = p.socle.livre
    if MOTIF_CARBURANT not in L.motifs: L.declarer_motif(MOTIF_CARBURANT, "achat", "guerre")


def rentrer(w):
    """Les engins revenus brulent le carburant du retour ( s il manque, ils rentrent quand meme : la dette de carburant
    n existe pas, CHOIX ). Rend les traversees closes a cet appel."""
    p = w.pays; d = S._dom(p); P = _P(w); out = []
    for t in P["traversees"]:
        if t["retour_brule"] or t["retour"] > int(w.pas): continue
        m = MODELES[t["modele"]]
        q = min(t["carburant"], _stock_carburant(w, t["modele"]))
        if q > EPS: _motif(p); S._sortir(p, d, "depot", d.national.k, m.carburant, q, MOTIF_CARBURANT, "brule")
        t["retour_brule"] = True; t["retour_carburant"] = q; out.append(t["id"])
    return out


def capacite_par_jour(w):
    """Information : les hommes qu une ile peut porter en un jour, par modele, avec sa flotte ( allers-retours )."""
    out = {}
    for nom, m in MODELES.items():
        n = sum(1 for x in _P(w)["flotte"].values() if x == nom)
        if not n: continue
        rotations = max(1, int(24.0 // (2 * duree_h(w, nom))))
        out[nom] = n * m.hommes * rotations
    return out
