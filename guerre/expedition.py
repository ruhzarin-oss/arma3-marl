"""L EXPEDITION ( Arma a fond, etape 4b, HMT-197 ) : les vrais soldats d une ile A attaquent un objectif reel d une ile B.

Le combat est juge HORS LIGNE par le domaine 27 de B, sur le chemin de son exercice de defense ( situation_exercice
« defense » ) : l expedition est un element adverse pose au domaine 26 de B ( camp « expedition_<A> » ), qui avance par
bonds du point d assaut vers l objectif, feu libre ; l unite de B qui garde l objectif fait la tactique « defense »,
en combat, ordres a la voix ( elle est sur place ). Ses hommes rouges sont les VRAIS soldats de A : tir, discipline,
stress, moral, portee utile, protection, casque, arme ( la regle du domaine 27 : le tireur antichar se bat a son arme
de poing ) et les coups qu ils portent ( guerre/logistique ), lus dans le monde de A ( `corps` ).

Le sort de chaque homme revient dans le monde de A ( `rapatrier` ) : une lesion non arretee le met hors de combat -
ISS >= 75 ( AIS 6 ) : mort ( moteur.morts_au_combat : deuil, pension ) ; sinon blesse, ramene par le transport, evacue
par le domaine 26 de A depuis son port puis blesse par d25.blesser_soldat ( la zone et l arme du tireur de B ) ; les coups
tires sortent de son armurerie ( logistique.tirer ) ; ceux d un mort sont perdus ( le corps reste chez l ennemi ). Un
homme que l adversaire fait decrocher ( rupture ) n est pas une perte. Les pertes de B suivent le domaine 27 de B.

CHOIX ecrits : une unite attaquee se defend sans preconditions ( radio, autonomie ) ; l assaut part a DISTANCE_ASSAUT
de l objectif, la ou la marche d approche s acheve ( de 500 a 900 m dans l exercice de defense du domaine 27 ) ; un
objectif atteint est detruit a proportion de la part de l expedition qui l atteint encore en etat de combattre
( dommages = actifs arrives / partis, borne a 1 ; frappes.frapper ) ; les heures de traversee d un blesse ne comptent
pas dans sa phase aigue."""
import math

import numpy as np

from monde import population as PO
from monde.pays import d16_medecine as MED, d17_hopitaux as HM, d25_armee as A, d26_armee_soutien as S
from monde.pays import d27_armee_tactique as T
from . import frappes as FR, logistique as LO, moteur as GM, objectifs as OB

DISTANCE_ASSAUT = 800.0
CHAMPS = ("tir", "portee", "prot", "casque", "arme", "cal", "coups", "disc", "stress", "moral")


def corps(wA, numeros):
    """Les hommes de l expedition, lus dans le monde de A : { numero, hid, et CHAMPS } en tableaux, dans l ordre des
    numeros ( les soldats hors des effectifs du domaine 25 n en sont pas )."""
    pA = wA.pays; f = GM._front(wA); rang = pA.col("habitant", "ar_rang")
    nums = [int(n) for n in numeros if int(n) in f and int(rang[f[int(n)]["i"]]) >= 0 and wA.table.vivant[f[int(n)]["i"]]]
    ids = [f[n]["i"] for n in nums]
    if not ids: return {"numero": np.zeros(0, np.int64), "hid": np.zeros(0, np.int64), **{k: np.zeros(0) for k in CHAMPS}}
    h = T._hommes_bleus(pA, ids, np.zeros(len(ids), np.int16), True, {})
    out = {"numero": np.array(nums, np.int64), "hid": np.array(ids, np.int64)}
    for k in CHAMPS: out[k] = h[k].copy()
    out["coups"] = np.array([LO.coups(wA, n) for n in nums], np.float64)     # ce qu ils portent vraiment
    return out


def objectif(ile, oid):
    """L objectif reel `oid` de la carte de l ile ( guerre/objectifs.objectifs_carte )."""
    return next(o for o in OB.objectifs_carte(ile.lower()) if o["id"] == oid)


def defenseur(wB, o):
    """La compagnie de B la plus proche de l objectif ( sa base ), ou None."""
    pB = wB.pays; U = A._dom(pB).unites; n = U.n; carte = wB.carte
    best = None
    for u in range(n):
        if int(U["niveau"][u]) != A.COMPAGNIE or int(U["base"][u]) < 0: continue
        if not len(T._aptes(pB, u)): continue
        b = carte.par_n[int(U["base"][u])]
        dd = math.hypot(b.pos[0] - o["pos"][0], b.pos[1] - o["pos"][1])
        if best is None or dd < best[0]: best = (dd, u)
    return None if best is None else best[1]


def _camp(pB, nom_ile):
    d = S._dom(pB); nom = f"expedition_{nom_ile}"
    if not any(c.nom == nom for c in d.camps): S.poser_camp(pB, nom, None, 30, cote="EAST", visible=True)
    return nom


def assaut(wB, nom_ile_A, cp, oid, u=-1, depart=None, seed=None, couvert="dur"):
    """L assaut des hommes `cp` ( corps ) sur l objectif `oid` de B, defendu par l unite u ( -1 : la plus proche ; None :
    personne ). couvert : celui des defenseurs ( dur : une base fortifiee ; leger : surpris hors de ses positions ). Rend { mission, arrives, dommages, frappe, sorts : [ ( numero, etat, zone, arme, ais, iss ) ],
    restants : { numero : coups } }."""
    pB = wB.pays; c = wB.carte; ile = c.par_n[0].ile; ii = c.iles.index(ile)
    o = objectif(ile, oid); ox, oy = float(o["pos"][0]), float(o["pos"][1])
    n = len(cp["numero"])
    if depart is None:
        port = c.port(ile) or c.gouvernement
        dx, dy = port.pos[0] - ox, port.pos[1] - oy; L = max(1.0, math.hypot(dx, dy))
        depart = (ox + DISTANCE_ASSAUT * dx / L, oy + DISTANCE_ASSAUT * dy / L)
    if u == -1: u = defenseur(wB, o)
    sorts = []; restants = {int(k): float(q) for k, q in zip(cp["numero"].tolist(), cp["coups"].tolist())}; avant = None
    if u is None or n == 0:
        arrives = n; m = None
    else:
        camp = _camp(pB, nom_ile_A)
        ent = S.poser_entite(pB, camp, depart[0], depart[1], ii, "debout", n, 0.0)
        cond = T.Conduite("bond", "objectif", regard="objectif", feu="libre")
        m = T.nouvelle_mission(pB, "defense", u, (ox, oy), (ox, oy), adverses=[(ent, n, cond, [(ox, oy)], None)],
                               mode="combat", voix=True, couvert_poste=couvert, seed=seed,
                               axe=S.azimut(ox, oy, depart[0], depart[1]), ile=ii)
        rouges = np.nonzero(m.h["side"] == 1)[0]
        for k in CHAMPS: m.h[k][rouges] = cp[k]
        avant = {k: m.h[k][rouges].copy() for k in CHAMPS}
        T.executer(pB, m)
        h = m.h
        lesion = {}
        for v, zone, arme, ais, arrete in getattr(m, "lesions_adverses", []):
            if not arrete: lesion[int(v)] = (zone, arme, int(ais))
        e_r = next(e for e in m.elts if e.side == 1)
        arrives = 0
        for k, v in enumerate(rouges.tolist()):
            num = int(cp["numero"][k]); restants[num] = float(h["coups"][v])
            if v in lesion:
                zone, arme, ais = lesion[v]; iss = MED.iss_depuis_ais({zone: ais})
                sorts.append((num, "mort" if iss >= 75 else "blesse", zone, arme, ais, iss))
            elif int(h["actif"][v]) == 1 and e_r.arrive: arrives += 1
        if ent is not None and S._dom(pB).ent["vivant"][ent]: S.retirer_entite(pB, ent)
    dommages = min(1.0, arrives / n) if n else 0.0
    frappe = None
    if dommages > 0:
        frappe = FR.frapper(wB, o, {cc["i"]: dommages for cc in o["composants"]}) if o.get("composants") else None
    wB.noter("assaut", attaquant=nom_ile_A, objectif=oid, hommes=n, arrives=arrives, pertes=len(sorts),
             defenseur=-1 if u is None else int(u))
    return {"mission": m, "arrives": arrives, "dommages": dommages, "frappe": frappe, "sorts": sorts,
            "restants": restants, "objectif": o, "defenseur": u, "rouges_avant": avant}


def rapatrier(wA, r):
    """Le sort de l expedition dans le monde de A : les coups tires, les morts, les blesses ( voir la fiche ). Rend
    { tires, morts, blesses }."""
    pA = wA.pays; f = GM._front(wA); out = {"tires": 0.0, "morts": [], "blesses": [], "armes_perdues": 0}
    sort = {num: (etat, zone, arme) for num, etat, zone, arme, _a, _i in r["sorts"]}
    for num, reste in sorted(r["restants"].items()):
        out["tires"] += LO.tirer(wA, num, reste)
    port = wA.carte.port(wA.carte.par_n[0].ile) or wA.carte.gouvernement
    for num, (etat, zone, arme) in sorted(sort.items()):
        s = f.get(num)
        if s is None: continue
        i = int(s["i"])
        if etat == "mort":
            LO.mort(wA, num, abandonne=True)
            rg = int(pA.col("habitant", "ar_rang")[i])          # le corps et son arme restent chez l ennemi
            if rg >= 0:
                oa = int(A._dom(pA).eff["arme"][rg])
                if oa >= 0 and oa in pA.socle.parc.objets: A.perdre_objet(pA, oa, "detruit"); out["armes_perdues"] += 1
            GM.morts_au_combat(wA, [num]); out["morts"].append(num)
            continue
        LO.rendre(wA, num)
        wA.absents.pop(i, None); t = wA.table; t.statut[i] = PO.RESIDENT; t.poste[i] = PO.CODE_POSTE["maison"]
        t.lieu[i] = port.n
        ev = S.evacuer(pA, i, lieu=port.id) if pA.a("armee_soutien") else None
        A.blesser_soldat(pA, i, zone, arme)
        if ev is not None and t.vivant[i]:
            ps = ev["passage"]; hab = PO.Habitant(t, i); ps.esi = HM.esi(pA, hab); ps.iss = HM._iss(pA, hab)
            pA.compter("evacuation_tactique")
        s.update(etat="blesse", blesse_pas=int(wA.pas), evacuation=ev["moyen"] if ev else None)
        out["blesses"].append(num)
    return out


# ------------------------------------------------------------------ 4b-2 : l operation, du depart au retour
DISTANCE_LARGAGE = 1500.0               # CHOIX : la zone de saut a 1,5 km de l objectif, hors de son feu direct


def _ops(w): return w.__dict__.setdefault("operations", [])


def demobiliser(wA, numeros):
    """Les survivants rentrent ( au retour du transport ) : l unite ramasse leurs coups, ils redeviennent residents."""
    f = GM._front(wA); t = wA.table; out = []
    for num in numeros:
        s = f.get(int(num))
        if s is None or s["etat"] in ("mort", "blesse") or not t.vivant[s["i"]]: continue
        i = int(s["i"]); LO.rendre(wA, num)
        wA.absents.pop(i, None); t.statut[i] = PO.RESIDENT; t.poste[i] = PO.CODE_POSTE["maison"]
        dom = getattr(wA.habitants[i], "domicile", None)
        if dom is not None: t.lieu[i] = dom.n
        s.update(etat="rentre", rentre_pas=int(wA.pas)); out.append(int(num))
    return out


def lancer_operation(wA, nom_A, oid, modele, hommes, parachutage=False, couvert="dur"):
    """Une operation de A contre l objectif `oid` de l autre ile : elle ne part que si le transport peut la porter
    ( projection.raison_refus : rien n est mobilise sinon ) ; puis mobilisation, dotation de combat, traversee. Rend
    { ok, raison } ou l operation."""
    from . import projection as PR
    raison = PR.raison_refus(wA, modele, hommes, parachutage)
    if raison: return {"ok": False, "raison": raison}
    nums = GM.mobiliser(wA, hommes); LO.emporter(wA, nums)
    cp = corps(wA, nums)
    t = PR.traverser(wA, modele, len(cp["numero"]), parachutage)
    if not t["ok"]:
        demobiliser(wA, nums); return {"ok": False, "raison": t["raison"]}
    ops = _ops(wA)
    op = {"id": len(ops) + 1, "attaquant": nom_A, "objectif": oid, "modele": modele, "parachutage": bool(parachutage),
          "couvert": couvert, "numeros": [int(n) for n in cp["numero"]], "corps": cp, "traversee": t["id"],
          "depart": t["depart"], "arrivee": t["arrivee"], "retour": t["retour"], "etat": "en_route", "assaut": None,
          "rapatriement": None}
    ops.append(op)
    wA.noter("operation", objectif=oid, modele=modele, hommes=len(op["numeros"]), arrivee=op["arrivee"])
    return {"ok": True, **op}


def avancer_operations(wA, wB):
    """A chaque pas des deux mondes : a l arrivee, l assaut dans B ; au retour du transport, le rapatriement dans A
    ( morts, blesses evacues, coups ), les survivants rentrent, le transport brule son retour. Rend les evenements."""
    from . import projection as PR
    evts = []
    for op in _ops(wA):
        if op["etat"] == "en_route" and int(wB.pas) >= op["arrivee"]:
            depart = None
            if op["parachutage"]:
                c = wB.carte; ile = c.par_n[0].ile; o = objectif(ile, op["objectif"])
                port = c.port(ile) or c.gouvernement
                dx, dy = port.pos[0] - o["pos"][0], port.pos[1] - o["pos"][1]; L = max(1.0, math.hypot(dx, dy))
                depart = (o["pos"][0] + DISTANCE_LARGAGE * dx / L, o["pos"][1] + DISTANCE_LARGAGE * dy / L)
            r = assaut(wB, op["attaquant"], op["corps"], op["objectif"], depart=depart, couvert=op["couvert"],
                       seed=(9000 + op["id"],))
            op["assaut"] = {k: r[k] for k in ("arrives", "dommages", "sorts", "restants", "defenseur")}
            op["assaut"]["pas"] = int(wB.pas); op["assaut"]["depart_assaut"] = depart
            op["etat"] = "au_retour"; evts.append(("assaut", op["id"]))
        if op["etat"] == "au_retour" and int(wA.pas) >= op["retour"]:
            rap = rapatrier(wA, op["assaut"])
            touches = {n for n, *_ in op["assaut"]["sorts"]}
            rap["rentres"] = demobiliser(wA, [n for n in op["numeros"] if n not in touches])
            PR.rentrer(wA)
            op["rapatriement"] = rap; op["rapatriement"]["pas"] = int(wA.pas); op["etat"] = "rentree"
            evts.append(("retour", op["id"]))
    return evts
