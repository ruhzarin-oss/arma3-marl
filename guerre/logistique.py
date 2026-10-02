"""LA LOGISTIQUE QUI COMMANDE LE COMBAT ( Arma a fond, etape 2a, HMT-193 ) : on ne tire que ce qui a ete paye et apporte.

Le FRONT est un detenteur reel : une armurerie du domaine 25 hors des bases ( lieu « front » ), dans la liste des
armureries, donc dans la conservation du domaine ( stock = depart + entrees - sorties comptees ). Tout mouvement passe
par le grand livre :
  emporter   un soldat mobilise emporte, pour chaque arme de sa dotation, la dotation de combat du domaine 25
             ( DOTATION_COMBAT ), au plus ce que l armurerie de SA base a encore ( transfert_munitions vers le front ) ;
  tirer      ce que le pont rend comme coups restants d un soldat fait la sortie tir_combat du front ( l arme principale
             d abord : CHOIX, tant que le pont compte des coups et non des chargeurs - etape 6, CUP ) ;
  mort       un soldat tue perd ce qu il portait ( perte_au_combat, nature perdu ) ;
  convoi     un ravitaillement : un camion du domaine 25 en service a la base, le gazole de la garnison pour l aller et le
             retour ( km x consommation du modele, brule au depart ), une route de distance x DETOUR / VITESSE_CONVOI ; la
             charge quitte la base au depart ( vers le front, « en route » ) et n est remise aux soldats qu a l arrivee.
CHOIX : DETOUR 1,3 ( le coefficient de circuite des routes mesure est de 1,2 a 1,4 ) ; VITESSE_CONVOI 40 km/h ( allure
d un convoi militaire sur route, ordre de grandeur des manuels de mouvement ).

Rien ne change tant qu aucune fonction n est appelee ( porte L6 )."""
import math

from monde import config as C
from monde.pays import d25_armee as A
from monde.socle import objets as O

DETOUR = 1.3
VITESSE_CONVOI_KMH = 40.0
CAMION = "steyr_12m18"
LIEU_FRONT = "front"


def _L(w):
    return w.__dict__.setdefault("logistique", {"porte": {}, "convois": [], "camions_pris": {}, "prochain": 1})


def front(w):
    """L armurerie du front de l ile ( creee a la premiere demande, dans la liste des armureries du domaine 25 )."""
    d = w.pays.domaines[A.DOMAINE]
    for a in d.armureries:
        if a.lieu == LIEU_FRONT: return a
    a = A.Armurerie(-1, LIEU_FRONT); d.armureries.append(a)
    return a


def _rang(w, i):
    col = w.pays.colonnes["habitant"]
    return int(col["ar_rang"][i])


def _armes(d, r):
    """( nom, calibre ) des armes individuelles de la ligne r : la principale, puis la secondaire."""
    E = d.eff; out = []
    for champ in ("arme_m", "arme2_m"):
        k = int(E[champ][r])
        if k >= 0 and A.ARMES[k].nom not in A.COLLECTIVES: out.append((A.ARMES[k].nom, A.ARMES[k].calibre))
    return out


def emporter(w, numeros):
    """Chaque soldat mobilise emporte sa dotation de combat, au plus ce que sa base a encore. Rend { numero : { bien : q } }."""
    from guerre import moteur as GM
    p = w.pays; d = p.domaines[A.DOMAINE]; L = p.socle.livre; fr = front(w); f = GM._front(w); lg = _L(w)
    out = {}
    for num in numeros:
        s = f.get(int(num))
        if s is None: continue
        r = _rang(w, s["i"])
        porte = {"base": None, "coups": {}, "armes": []}
        if r >= 0:
            b = int(d.eff["base"][r]); arm = d.armureries[d.par_base[b]]
            porte["base"] = arm.lieu; porte["armes"] = _armes(d, r)
            for nom, bien in porte["armes"]:
                bid = d.bids[bien]
                q = min(float(A.DOTATION_COMBAT[nom]), float(arm.stock[bid]))
                if q > 0: q = L.deplacer(arm.stock, fr.stock, bid, q, "transfert_munitions")
                porte["coups"][bien] = porte["coups"].get(bien, 0.0) + q
        lg["porte"][int(num)] = porte; out[int(num)] = dict(porte["coups"])
    return out


def coups(w, num):
    return sum(_L(w)["porte"].get(int(num), {"coups": {}})["coups"].values())


def tirer(w, num, restant):
    """Le pont rend `restant` coups pour le soldat `num` : la difference sort du front ( tir_combat ). Rend les coups tires."""
    p = w.pays; d = p.domaines[A.DOMAINE]; fr = front(w)
    po = _L(w)["porte"].get(int(num))
    if po is None: return 0.0
    tire = max(0.0, coups(w, num) - max(0.0, float(restant)))
    reste = tire
    for _nom, bien in po["armes"] or [(None, b) for b in po["coups"]]:
        q = min(reste, po["coups"].get(bien, 0.0))
        if q > 0:
            q = A._sortir(p, d, fr, bien, q, "tir_combat"); po["coups"][bien] -= q; reste -= q
            p.compter("tir_combat", q)
    return tire - reste


def mort(w, num):
    """Le soldat tue perd ce qu il portait. Rend les coups perdus."""
    p = w.pays; d = p.domaines[A.DOMAINE]; fr = front(w)
    po = _L(w)["porte"].pop(int(num), None)
    if po is None: return 0.0
    perdu = 0.0
    for bien, q in po["coups"].items():
        if q > 0: perdu += A._sortir(p, d, fr, bien, q, "perte_au_combat", "perdu")
    return perdu


def _camion_libre(w, b):
    d = w.pays.domaines[A.DOMAINE]; V = d.veh; pris = _L(w)["camions_pris"]
    m = A.IDX_VEHICULE[CAMION]
    for k in range(V.n):
        if V["base"][k] == b and V["oid"][k] >= 0 and V["modele"][k] == m and V["etat"][k] == O.SERVICE \
                and pris.get(int(V["oid"][k]), -1) <= int(w.pas):
            return k
    return -1


def convoi(w, base_lieu, numeros, coups_par_soldat, destination):
    """Un ravitaillement de la base vers `destination` ( x, y ) pour ces soldats. Rend { ok, raison, ... }."""
    p = w.pays; d = p.domaines[A.DOMAINE]; L = p.socle.livre; fr = front(w); lg = _L(w)
    lieu = w.carte.lieux[base_lieu]; b = lieu.n
    arm = d.armureries[d.par_base[b]]
    k = _camion_libre(w, b)
    if k < 0: return {"ok": False, "raison": "aucun camion en service a la base"}
    km_aller = math.dist(lieu.pos, destination) * DETOUR / 1000.0
    besoin = 2.0 * km_aller * A.VEHICULE[CAMION].unites_par_km
    g = w.garnisons.get(base_lieu)
    if g is None or float(g["carburant"]) < besoin - 1e-9: return {"ok": False, "raison": "pas assez de gazole a la garnison"}
    g["carburant"] -= besoin; w.flux["brule"]["carburant"] += besoin
    pas_route = int(math.ceil(km_aller / VITESSE_CONVOI_KMH * C.PAS_PAR_JOUR / 24.0))
    charge = {}
    for num in numeros:
        po = lg["porte"].get(int(num))
        if po is None: continue
        for _nom, bien in po["armes"][:1]:              # le convoi apporte la munition de l arme principale
            bid = d.bids[bien]
            q = min(float(coups_par_soldat), float(arm.stock[bid]))
            if q > 0: q = L.deplacer(arm.stock, fr.stock, bid, q, "transfert_munitions")
            charge.setdefault(int(num), {})[bien] = charge.get(int(num), {}).get(bien, 0.0) + q
    oid = int(d.veh["oid"][k])
    lg["camions_pris"][oid] = int(w.pas) + 2 * pas_route
    c = {"id": lg["prochain"], "base": base_lieu, "camion": oid, "depart": int(w.pas), "arrivee": int(w.pas) + pas_route,
         "km_aller": km_aller, "gazole": besoin, "charge": charge, "livre": False}
    lg["prochain"] += 1; lg["convois"].append(c)
    w.noter("convoi", base=base_lieu, km=round(km_aller, 1), arrivee=c["arrivee"], soldats=len(charge))
    return {"ok": True, **c}


def avancer(w):
    """Les convois arrives remettent leur charge aux soldats. Rend les convois livres a cet appel."""
    lg = _L(w); out = []
    for c in lg["convois"]:
        if c["livre"] or c["arrivee"] > int(w.pas): continue
        for num, ch in c["charge"].items():
            po = lg["porte"].get(int(num))
            if po is None: continue                      # mort en route : la charge reste au front, comptee
            for bien, q in ch.items(): po["coups"][bien] = po["coups"].get(bien, 0.0) + q
        c["livre"] = True; out.append(c["id"])
    return out
