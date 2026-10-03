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
EMPORTER_MORTIERS = True               # ( HMT-198 A1-bis ) l expedition emporte les mortiers de ses sections d appui
EMPORTER_ROQUETTES = True              # ( HMT-198 A2 ) ses tireurs antichar emportent leurs roquettes de 84 mm
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
    a = A._dom(pA); rg = A._rangs(pA, ids)
    out["spec"] = a.eff["spec"][rg].astype(np.int64).copy()
    out["mortiers"] = mortiers_emportes(wA, out) if EMPORTER_MORTIERS else {"tubes": 0, "obus": 0.0, "base": None}
    out["at"], out["at_lid"] = roquettes_emportees(wA, out)
    return out


def roquettes_emportees(wA, cp):
    """( 03/10, HMT-198 A2 ) Les roquettes de 84 mm de ses tireurs antichar ( specialite ANTICHAR, le Carl Gustaf en arme
    principale ) : la dotation de combat ( 6 ), au plus ce que l armurerie de leur base a hors reserves. Rend ( roquettes
    par homme, base de chacun ou "" )."""
    n = len(cp["numero"]); at = np.zeros(n); lids = np.array([""] * n, dtype=object)
    if n == 0 or not EMPORTER_ROQUETTES: return at, lids
    pA = wA.pays; a = A._dom(pA); E = a.eff
    rg = A._rangs(pA, cp["hid"]); ic = A.IDX_ARME["carl_gustaf_m3"]; cal = A.NOMS_MUNITIONS.index("roquette_84")
    dot = A.DOTATION_COMBAT.get("carl_gustaf_m3", 0); pris = {}
    for k in range(n):
        if int(E["spec"][rg[k]]) != A.ANTICHAR or int(E["arme_m"][rg[k]]) != ic: continue
        lid = wA.carte.par_n[int(E["base"][rg[k]])].id
        stock = float(A.armurerie(pA, lid).stock[a.bids["roquette_84"]]) - T._dom(pA).reserve.get((lid, cal), 0.0) - pris.get(lid, 0.0)
        q = float(max(0.0, min(dot, math.floor(stock))))
        if q <= 0: continue
        at[k] = q; lids[k] = lid; pris[lid] = pris.get(lid, 0.0) + q
    return at, lids


def roquettes_par_base(cp):
    """{ base : roquettes emportees } ( la reserve de l operation )."""
    out = {}
    for q, lid in zip(cp.get("at", []), cp.get("at_lid", [])):
        if lid and q > 0: out[lid] = out.get(lid, 0.0) + float(q)
    return out


def mortiers_emportes(wA, cp):
    """( 03/10, HMT-198 A1-bis ) Les mortiers que l expedition emporte : les tubes des bases de ses servants ( specialite
    MORTIER ), deux servants par tube, et leur dotation de combat d obus ( 60 par tube ), au plus ce que l armurerie a hors
    reserves. Rend { tubes, obus, base }."""
    pA = wA.pays; a = A._dom(pA); K = a.coll; E = a.eff
    serv = [k for k, sp in enumerate(cp["spec"].tolist()) if sp == A.MORTIER]
    if len(serv) < T.SERVANTS_PAR_TUBE: return {"tubes": 0, "obus": 0.0, "base": None}
    rg = A._rangs(pA, cp["hid"][serv])
    b = int(E["base"][rg[0]])
    im = A.IDX_ARME["mortier_81"]
    dispo = sum(1 for k in range(K.n) if int(K["oid"][k]) >= 0 and int(K["modele"][k]) == im and int(K["base"][k]) == b)
    tubes = min(dispo, len(serv) // T.SERVANTS_PAR_TUBE)
    lid = wA.carte.par_n[b].id; cal = A.NOMS_MUNITIONS.index("obus_81")
    stock = float(A.armurerie(pA, lid).stock[a.bids["obus_81"]]) - T._dom(pA).reserve.get((lid, cal), 0.0)
    obus = float(max(0.0, min(A.DOTATION_COMBAT.get("mortier_81", 0) * tubes, math.floor(stock))))
    return {"tubes": int(tubes) if obus > 0 else 0, "obus": obus, "base": lid}


def objectif(ile, oid):
    """L objectif reel `oid` de la carte de l ile ( guerre/objectifs.objectifs_carte )."""
    return next(o for o in OB.objectifs_carte(ile.lower()) if o["id"] == oid)


def defenseur(wB, o):
    """( unite, couvert ) qui defend l objectif, ou ( None, None ). CHOIX ( 03/10, l etat-major de Qwen a montre qu une
    compagnie entiere et retranchee devant chaque objectif rendait toute attaque vaine ) : une BASE est defendue par sa
    compagnie, retranchee ( couvert dur ) ; un autre objectif ( port, centrale, depot, fonderie, aerodrome ) est garde
    par UNE SECTION de la compagnie la plus proche, a couvert leger ( la garde des points sensibles ) ."""
    pB = wB.pays; U = A._dom(pB).unites; n = U.n; carte = wB.carte
    best = None
    for u in range(n):
        if int(U["niveau"][u]) != A.COMPAGNIE or int(U["base"][u]) < 0: continue
        if not len(T._aptes(pB, u)): continue
        b = carte.par_n[int(U["base"][u])]
        dd = math.hypot(b.pos[0] - o["pos"][0], b.pos[1] - o["pos"][1])
        if best is None or dd < best[0]: best = (dd, u)
    if best is None: return None, None
    u = best[1]
    if o["type"] == "base": return u, "dur"
    sections = [x for x in range(n) if int(U["parent"][x]) == u and int(U["niveau"][x]) == A.SECTION and len(T._aptes(pB, x))]
    return (sections[0], "leger") if sections else (u, "leger")


def point_d_approche(wB, o, distance):
    """( 03/10, HMT-198 ) Le point a `distance` de l objectif d ou part la marche d approche : du cote du port, ou
    debarque le transport. CHOIX : quand le port est l objectif ou en est a moins de `distance` ( le lieu port de chaque
    ile EST son objectif port01 : l assaut partait de l objectif meme, deja arrive ), le chaland debarque plus loin sur la
    cote et l approche vient du lieu de l ile le plus proche a `distance` au moins."""
    c = wB.carte; ile = c.par_n[0].ile; ox, oy = float(o["pos"][0]), float(o["pos"][1])
    port = c.port(ile) or c.gouvernement
    dx, dy = port.pos[0] - ox, port.pos[1] - oy; L = math.hypot(dx, dy)
    if L < distance:
        cands = sorted((math.hypot(l.pos[0] - ox, l.pos[1] - oy), l.n) for l in c.par_n
                       if l.ile == ile and math.hypot(l.pos[0] - ox, l.pos[1] - oy) >= distance)
        if cands:
            l = c.par_n[cands[0][1]]; dx, dy = l.pos[0] - ox, l.pos[1] - oy; L = math.hypot(dx, dy)
    L = max(1.0, L)
    return (ox + distance * dx / L, oy + distance * dy / L)


def _camp(pB, nom_ile):
    d = S._dom(pB); nom = f"expedition_{nom_ile}"
    if not any(c.nom == nom for c in d.camps): S.poser_camp(pB, nom, None, 30, cote="EAST", visible=True)
    return nom


def assaut(wB, nom_ile_A, cp, oid, u=-1, depart=None, seed=None, couvert=None):
    """L assaut des hommes `cp` ( corps ) sur l objectif `oid` de B, defendu par l unite u ( -1 : la plus proche ; None :
    personne ). couvert : celui des defenseurs ( dur : une base fortifiee ; leger : surpris hors de ses positions ). Rend { mission, arrives, dommages, frappe, sorts : [ ( numero, etat, zone, arme, ais, iss ) ],
    restants : { numero : coups } }."""
    pB = wB.pays; c = wB.carte; ile = c.par_n[0].ile; ii = c.iles.index(ile)
    o = objectif(ile, oid); ox, oy = float(o["pos"][0]), float(o["pos"][1])
    n = len(cp["numero"])
    if depart is None: depart = point_d_approche(wB, o, DISTANCE_ASSAUT)
    if u == -1:
        u, couvert_def = defenseur(wB, o)
        if couvert_def is not None and couvert is None: couvert = couvert_def
    sorts = []; restants = {int(k): float(q) for k, q in zip(cp["numero"].tolist(), cp["coups"].tolist())}; avant = None
    obus_tires = 0.0; vehicules_detruits = 0
    roquettes = [(int(cp["numero"][k]), cp["at_lid"][k], float(q), float(q)) for k, q in enumerate(cp.get("at", [])) if q > 0]
    if u is None or n == 0:
        arrives = n; m = None
    else:
        camp = _camp(pB, nom_ile_A)
        ent = S.poser_entite(pB, camp, depart[0], depart[1], ii, "debout", n, 0.0)
        cond = T.Conduite("bond", "objectif", regard="objectif", feu="libre")
        m = T.nouvelle_mission(pB, "defense", u, (ox, oy), (ox, oy), adverses=[(ent, n, cond, [(ox, oy)], None)],
                               mode="combat", voix=True, couvert_poste=couvert or "dur", seed=seed,
                               axe=S.azimut(ox, oy, depart[0], depart[1]), ile=ii)
        rouges = np.nonzero(m.h["side"] == 1)[0]
        for k in CHAMPS: m.h[k][rouges] = cp[k]
        if "at" in cp and "at" in m.h: m.h["at"][rouges] = cp["at"]          # ( HMT-198 A2 ) leurs roquettes
        avant = {k: m.h[k][rouges].copy() for k in CHAMPS}
        Mx = cp.get("mortiers") or {}
        if Mx.get("tubes", 0) > 0 and "spec" in cp:          # ( HMT-198 A1-bis ) ses mortiers tirent de son cote
            m.mortiers_adverses = {"servants": [int(rouges[k]) for k, sp in enumerate(cp["spec"].tolist()) if sp == A.MORTIER],
                                   "tubes": int(Mx["tubes"]), "obus": float(Mx["obus"]), "tires": 0.0}
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
        obus_tires = float((getattr(m, "mortiers_adverses", None) or {}).get("tires", 0.0))
        if "at" in cp and "at" in h:                         # ( HMT-198 A2 ) ( numero, base, emportees, restantes )
            roquettes = [(int(cp["numero"][k]), cp["at_lid"][k], float(cp["at"][k]), float(h["at"][v]))
                         for k, v in enumerate(rouges.tolist()) if cp["at"][k] > 0]
        vehicules_detruits = sum(1 for vh in getattr(m, "vehicules", []) if not vh["intact"])
    dommages = min(1.0, arrives / n) if n else 0.0
    frappe = None
    if dommages > 0:
        frappe = FR.frapper(wB, o, {cc["i"]: dommages for cc in o["composants"]}) if o.get("composants") else None
    wB.noter("assaut", attaquant=nom_ile_A, objectif=oid, hommes=n, arrives=arrives, pertes=len(sorts),
             defenseur=-1 if u is None else int(u))
    return {"mission": m, "arrives": arrives, "dommages": dommages, "frappe": frappe, "sorts": sorts,
            "restants": restants, "objectif": o, "defenseur": u, "rouges_avant": avant, "obus_tires": obus_tires,
            "mortiers": cp.get("mortiers"), "roquettes": roquettes, "vehicules_detruits": vehicules_detruits}


def rapatrier(wA, r):
    """Le sort de l expedition dans le monde de A : les coups tires, les morts, les blesses ( voir la fiche ). Rend
    { tires, morts, blesses }."""
    pA = wA.pays; f = GM._front(wA); out = {"tires": 0.0, "morts": [], "blesses": [], "armes_perdues": 0}
    sort = {num: (etat, zone, arme) for num, etat, zone, arme, _a, _i in r["sorts"]}
    for num, reste in sorted(r["restants"].items()):
        out["tires"] += LO.tirer(wA, num, reste)
    Mx = r.get("mortiers") or {}
    if Mx.get("base") and Mx.get("tubes", 0) > 0:          # ( HMT-198 A1-bis ) les obus : la reserve rendue, les tires payes
        cal = A.NOMS_MUNITIONS.index("obus_81"); res = T._dom(pA).reserve; cle = (Mx["base"], cal)
        res[cle] = max(0.0, res.get(cle, 0.0) - float(Mx["obus"]))
        q = float(r.get("obus_tires", 0.0))
        if q > 0: out["obus_tires"] = A.tirer(pA, Mx["base"], "obus_81", q, "tir_combat")
    cal = A.NOMS_MUNITIONS.index("roquette_84"); res = T._dom(pA).reserve
    for num, lid, q0, q1 in r.get("roquettes", []):      # ( HMT-198 A2 ) la reserve rendue, les tirees payees, celles d un mort perdues
        res[(lid, cal)] = max(0.0, res.get((lid, cal), 0.0) - q0)
        if q0 - q1 > 0: out["roquettes_tirees"] = out.get("roquettes_tirees", 0.0) + A.tirer(pA, lid, "roquette_84", q0 - q1, "tir_combat")
        if q1 > 0 and sort.get(num, ("",))[0] == "mort":
            out["roquettes_perdues"] = out.get("roquettes_perdues", 0.0) + A.tirer(pA, lid, "roquette_84", q1, "perte_au_combat")
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
        T.blesser_soldat(pA, i, zone, arme)                  # ( HMT-198 A2 ) une arme de bord aussi ( la M2HB )
        if ev is not None and t.vivant[i]:
            ps = ev["passage"]; hab = PO.Habitant(t, i); ps.esi = HM.esi(pA, hab); ps.iss = HM._iss(pA, hab)
            pA.compter("evacuation_tactique")
        s.update(etat="blesse", blesse_pas=int(wA.pas), evacuation=ev["moyen"] if ev else None)
        out["blesses"].append(num)
    return out


# ------------------------------------------------------------------ 4b-2 : l operation, du depart au retour
DISTANCE_LARGAGE = 1500.0               # CHOIX : la zone de saut a 1,5 km de l objectif, hors de son feu direct
BUTS_OPERATION = ("assaut", "reconnaissance")   # ( HMT-198 A3 ) attaquer l objectif, ou aller le voir ( guerre/reconnaissance )


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


def membres_a_projeter(wA, hommes):
    """( 03/10, HMT-198 ) Qui part : des COMPAGNIES entieres ( on projette des unites constituees, pas des soldats tires
    au hasard ), jusqu a l effectif demande ; dans chaque compagnie, les servants de mortier d abord ( l appui accompagne
    l assaut : CHOIX ), puis les autres. Rend les habitants, dans l ordre."""
    pA = wA.pays; a = A._dom(pA); U = a.unites; E = a.eff; t = wA.table
    out = []
    for u in range(U.n):
        if int(U["niveau"][u]) != A.COMPAGNIE: continue
        ids = [int(i) for i in A.membres(pA, u, actifs_seulement=True).tolist() if t.vivant[int(i)] and int(t.statut[int(i)]) == PO.RESIDENT]
        if not ids: continue
        rg = A._rangs(pA, ids)
        ids = [i for _s, i in sorted(zip((0 if int(E["spec"][r]) == A.MORTIER else 1 for r in rg.tolist()), ids), key=lambda x: x[0])]
        out.extend(ids)
        if len(out) >= hommes: break
    return out[:int(hommes)]


def lancer_operation(wA, nom_A, oid, modele, hommes, parachutage=False, couvert=None, but="assaut"):
    """Une operation de A contre l objectif `oid` de l autre ile : elle ne part que si le transport peut la porter
    ( projection.raison_refus : rien n est mobilise sinon ) ; puis mobilisation, dotation de combat, traversee. Rend
    { ok, raison } ou l operation."""
    from . import projection as PR
    if but not in BUTS_OPERATION: return {"ok": False, "raison": f"but inconnu {but!r}"}
    raison = PR.raison_refus(wA, modele, hommes, parachutage)
    if raison: return {"ok": False, "raison": raison}
    # ( HMT-198 A3 ) une reconnaissance part en equipe ( la mobilisation ordinaire ) et sans mortiers
    nums = GM.mobiliser(wA, hommes, ids=None if but == "reconnaissance" else membres_a_projeter(wA, hommes)); LO.emporter(wA, nums)
    cp = corps(wA, nums)
    if but == "reconnaissance": cp["mortiers"] = {"tubes": 0, "obus": 0.0, "base": None}
    t = PR.traverser(wA, modele, len(cp["numero"]), parachutage)
    if not t["ok"]:
        demobiliser(wA, nums); return {"ok": False, "raison": t["raison"]}
    # ( 03/10, HMT-198 A2 ) les obus et les roquettes emportes sont reserves une fois la traversee partie ( avant, un
    # refus de la traversee laissait la reserve des obus engagee )
    res = T._dom(wA.pays).reserve
    Mx = cp.get("mortiers") or {}
    if Mx.get("tubes", 0) > 0:                             # ( HMT-198 A1-bis ) les obus
        cal = A.NOMS_MUNITIONS.index("obus_81")
        res[(Mx["base"], cal)] = res.get((Mx["base"], cal), 0.0) + float(Mx["obus"])
    cal = A.NOMS_MUNITIONS.index("roquette_84")
    for lid, q in sorted(roquettes_par_base(cp).items()): res[(lid, cal)] = res.get((lid, cal), 0.0) + q
    ops = _ops(wA)
    op = {"id": len(ops) + 1, "attaquant": nom_A, "objectif": oid, "modele": modele, "parachutage": bool(parachutage), "but": but,
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
                depart = point_d_approche(wB, o, DISTANCE_LARGAGE)
            if op.get("but") == "reconnaissance":            # ( 03/10, HMT-198 A3 ) voir, sans se battre
                from . import reconnaissance as RC
                r = RC.reconnaitre(wB, op["attaquant"], op["corps"], op["objectif"], seed=(9000 + op["id"],))
                r["vehicules_detruits"] = 0
                RC._renseignement(wA)[op["objectif"]] = dict(r["rapport"], detectee=r["detectee"], pas_A=int(wA.pas))
            else:
                r = assaut(wB, op["attaquant"], op["corps"], op["objectif"], depart=depart, couvert=op["couvert"],
                           seed=(9000 + op["id"],))
            op["assaut"] = {k: r[k] for k in ("arrives", "dommages", "sorts", "restants", "defenseur", "obus_tires", "mortiers",
                                              "roquettes", "vehicules_detruits")}
            if "rapport" in r: op["assaut"]["rapport"] = r["rapport"]
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
