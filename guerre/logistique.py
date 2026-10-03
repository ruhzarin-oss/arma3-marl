"""LA LOGISTIQUE QUI COMMANDE LE COMBAT ( Arma a fond, etape 2a, HMT-193 ) : on ne tire que ce qui a ete paye et apporte.
ALIGNEE le 02/10 sur les domaines 26 et 27 : la guerre d Arma passe par leurs chemins, elle ne tient pas une seconde
verite a cote d eux.

Les coups qu un soldat porte sont une RESERVE du domaine 27 sur l armurerie de sa base ( d27.reserve, cle ( base,
calibre ) ) : ils restent au livre de la base jusqu a ce qu ils soient tires, comme ceux des missions du domaine 27, et
une mission du 27 ne peut pas les promettre une seconde fois.
  emporter   la regle du domaine 27 ( `_hommes_bleus` ) : l arme principale ( le tireur antichar : son arme de poing ),
             sa dotation de combat, au prorata de ce que la base a encore hors reserves, arrondi a l entier inferieur ;
  tirer      les coups restants rendus par le pont : la difference est tiree a la base ( d25.tirer, tir_combat ), la
             reserve baisse, le domaine 27 compte la demande et la sortie ( tirs, tirs_sortis ) ;
  mort       l unite ramasse ce que portait le mort ( la reserve est rendue ) ; si le corps est abandonne
             ( abandonne=True : l unite rompt, regle du domaine 27 ), c est une perte_au_combat ;
  rendre     un evacue : l unite ramasse ses coups ( la reserve est rendue ) ;
  convoi     un ravitaillement de la base vers le lieu le plus proche des soldats, par les moyens du domaine 26 : un
             camion Steyr libre et son conducteur, reserves DANS le domaine 26 ( camion_libre, chauffeur_libre : il ne
             les donne plus a ses propres convois ), le gazole de la garnison brule par son livre de flux
             ( carburant_convoi_militaire ), la duree de route du domaine 15 ( duree_convoi_pas sur la vraie route ),
             l usure du camion ( kilometres, Parc ). La charge est reservee au depart et remise a l arrivee ( avancer ).
CHOIX : une garnison ne ravitaille que ses propres soldats ( la reserve d un soldat tient a une seule base ).
Le ravitaillement de la base elle-meme ( depot de brigade -> garnison ) est celui du domaine 26 : sa decision S4 du
matin, ou `d26.demander`.

Rien ne change tant qu aucune fonction n est appelee ( porte A6 )."""
import math

import numpy as np

from monde.pays import d15_logistique as LG, d25_armee as A, d26_armee_soutien as S, d27_armee_tactique as T

EPS = 1e-9


def _L(w):
    return w.__dict__.setdefault("logistique", {"porte": {}, "convois": [], "prochain": 1})


def _cle(po):
    return po["base"], po["cal"]


def _reserver(p, cle, q):
    r = T._dom(p).reserve
    r[cle] = r.get(cle, 0.0) + q


def _liberer(p, cle, q):
    r = T._dom(p).reserve
    r[cle] = max(0.0, r.get(cle, 0.0) - q)


def emporter(w, numeros):
    """Chaque soldat mobilise emporte la dotation de combat de son arme, selon la regle du domaine 27. Un soldat qui
    porte deja n emporte pas une seconde fois. Rend { numero : coups }."""
    from guerre import moteur as GM
    p = w.pays; f = GM._front(w); lg = _L(w); rang = p.col("habitant", "ar_rang")
    ids, nums = [], []
    for num in numeros:
        s = f.get(int(num))
        if s is None or int(num) in lg["porte"]: continue
        if int(rang[s["i"]]) < 0:                       # hors des effectifs du domaine 25 : rien a emporter
            lg["porte"][int(num)] = {"base": None, "cal": -1, "coups": 0.0}; continue
        ids.append(int(s["i"])); nums.append(int(num))
    if ids:
        h = T._hommes_bleus(p, ids, np.zeros(len(ids), np.int16), False, T._dom(p).reserve)
        for v, num in enumerate(nums):
            c = int(h["cal"][v])
            lg["porte"][num] = {"base": w.carte.par_n[int(h["base"][v])].id if c >= 0 else None, "cal": c,
                                "coups": float(h["coups"][v]) if c >= 0 else 0.0}
    return {int(num): coups(w, num) for num in numeros if int(num) in lg["porte"]}


def coups(w, num):
    """Les coups que porte le soldat au front `num` ( sa reserve au domaine 27 )."""
    po = _L(w)["porte"].get(int(num))
    return 0.0 if po is None else po["coups"]


def tirer(w, num, restant):
    """Le pont rend `restant` coups pour le soldat `num` : la difference est tiree a sa base. Rend les coups sortis."""
    p = w.pays; po = _L(w)["porte"].get(int(num))
    if po is None or po["cal"] < 0: return 0.0
    q = max(0.0, po["coups"] - max(0.0, float(restant)))
    if q <= EPS: return 0.0
    lid, c = _cle(po); bien = A.NOMS_MUNITIONS[c]; t = T._dom(p)
    sortis = A.tirer(p, lid, bien, q, "tir_combat")
    t.tirs[(lid, bien)] = t.tirs.get((lid, bien), 0.0) + q
    t.tirs_sortis[(lid, bien)] = t.tirs_sortis.get((lid, bien), 0.0) + sortis
    _liberer(p, (lid, c), q); po["coups"] -= q
    return sortis


def rendre(w, num):
    """Un soldat qui quitte le front vivant ( evacue ) : l unite ramasse ses coups. Rend les coups rendus."""
    po = _L(w)["porte"].pop(int(num), None)
    if po is None or po["cal"] < 0 or po["coups"] <= 0: return 0.0
    _liberer(w.pays, _cle(po), po["coups"])
    return po["coups"]


def mort(w, num, abandonne=False):
    """Un soldat tue : l unite ramasse ses coups ( rendus ), sauf si son corps est abandonne ( perte_au_combat ). Rend
    les coups perdus."""
    p = w.pays; po = _L(w)["porte"].get(int(num))
    if po is None or po["cal"] < 0 or po["coups"] <= 0 or not abandonne:
        rendre(w, num); return 0.0
    _L(w)["porte"].pop(int(num))
    lid, c = _cle(po); bien = A.NOMS_MUNITIONS[c]; t = T._dom(p); q = po["coups"]
    perdu = A.tirer(p, lid, bien, q, "perte_au_combat")
    t.tirs[(lid, bien + ":perte")] = t.tirs.get((lid, bien + ":perte"), 0.0) + q
    t.tirs_sortis[(lid, bien + ":perte")] = t.tirs_sortis.get((lid, bien + ":perte"), 0.0) + perdu
    _liberer(p, (lid, c), q)
    return perdu


def convoi(w, base_lieu, numeros, coups_par_soldat, destination):
    """Un ravitaillement de la base `base_lieu` vers le lieu le plus proche de `destination` ( x, y ), pour ceux de ces
    soldats qui sont de cette base. Rend { ok, raison } ou { ok, id, camion, chauffeur, vers, km, depart, arrivee,
    gazole, charge }."""
    p = w.pays; d = S._dom(p); carte = w.carte; lg = _L(w)
    o = carte.lieux[base_lieu]; b = o.n
    t = carte.par_n[S._lieu_proche(p, d, float(destination[0]), float(destination[1]), carte.iles.index(o.ile))]
    if t.id != o.id and not LG.route_praticable(p, o, t): return {"ok": False, "raison": "route coupee"}
    camions = S._camions_libres(p, d, b)
    if not camions: return {"ok": False, "raison": "aucun camion libre a la base ( domaine 26 )"}
    h = S._chauffeur(p, d, b)
    if h < 0: return {"ok": False, "raison": "aucun conducteur libre a la base ( domaine 26 )"}
    km = carte.km_route(o, t) if t.id != o.id else 0.0
    aller, retour = LG.duree_convoi_pas(p, o, t, km)
    gaz = 2.0 * km * A.VEHICULE[S.CAMION].unites_par_km
    if S._quantite(p, d, "base", b, "carburant") < gaz - EPS: return {"ok": False, "raison": "pas assez de gazole a la garnison"}
    # la charge : de ce que la base a hors reserves, soldat par soldat, dans la limite d un camion de 5 t
    charge, cals = {}, {}; kg = 0.0
    for num in numeros:
        po = lg["porte"].get(int(num))
        if po is None or po["cal"] < 0 or po["base"] != base_lieu: continue
        c = po["cal"]; bien = A.NOMS_MUNITIONS[c]
        stock = float(A.armurerie(p, base_lieu).stock[A._dom(p).bids[bien]])
        dispo = max(0.0, stock - T._dom(p).reserve.get((base_lieu, c), 0.0))
        m = LG.masse_kg(p, bien)
        q = float(math.floor(min(float(coups_par_soldat), dispo, max(0.0, S.CHARGE_CAMION_KG - kg) / max(EPS, m)) + EPS))
        if q <= 0: continue
        _reserver(p, (base_lieu, c), q); kg += q * m
        charge[int(num)] = q; cals[int(num)] = c
    if gaz > EPS: S._sortir(p, d, "base", b, "carburant", gaz, "carburant_convoi_militaire", "brule")
    k = camions[0]; depart = S._depart(d, o.id, w.pas)
    d.camion_libre[k] = depart + aller + retour; d.chauffeur_libre[h] = depart + aller + retour
    V = A._dom(p).veh; parc = p.socle.parc
    A._rouler(V, k, 2.0 * km)
    parc.user(parc.objets[int(V["oid"][k])], 2.0 * km / A.VITESSE_USAGE_KMH)
    c_ = {"id": lg["prochain"], "base": base_lieu, "camion": int(k), "chauffeur": int(h), "vers": t.id, "km": km,
          "depart": int(depart), "arrivee": int(depart + aller), "gazole": gaz, "charge": charge, "cal": cals, "livre": False}
    lg["prochain"] += 1; lg["convois"].append(c_)
    w.noter("convoi", base=o.id, km=round(km, 1), arrivee=c_["arrivee"], soldats=len(charge))
    return {"ok": True, **c_}


def avancer(w):
    """Les convois arrives remettent leur charge aux soldats ; celle d un soldat parti entre-temps ( mort, evacue ) est
    rendue a la base. Rend les convois livres a cet appel."""
    p = w.pays; lg = _L(w); out = []
    for c in lg["convois"]:
        if c["livre"] or c["arrivee"] > int(w.pas): continue
        for num, q in c["charge"].items():
            po = lg["porte"].get(int(num))
            if po is None: _liberer(p, (c["base"], c["cal"][num]), q); continue
            po["coups"] += q
        c["livre"] = True; out.append(c["id"])
    return out


def portees(w):
    """Les coups portes par les soldats et les missions, par base et par bien ( la reserve du domaine 27 )."""
    out = {}
    for (lid, c), q in sorted(T._dom(w.pays).reserve.items()):
        if q > EPS: out.setdefault(lid, {})[A.NOMS_MUNITIONS[c]] = q
    return out
