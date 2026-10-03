"""Porte S3a du defenseur qui a un stratege ( HMT-198 ). Criteres ecrits avant la mesure ( Plane, 03/10 07 h 00 ) : Stratis
( 2141 ) contre Malden ( 2142 ), echelle 20.

G1  les deux sens : B achete un LCU et lance 400 hommes sur le port de A ; par EM.avancer l assaut a lieu DANS A ( son
    port frappe > 0, l attaque subie notee dans A ), le rapatriement dans B ( l operation rentree ).
G2  le renfort ( controle positif, 100 hommes de A contre le port de B, 3 graines ) : sans renfort, des dommages sur au
    moins une mission ; avec, le defenseur est la compagnie posee, retranchee, et la somme des dommages strictement
    plus petite.
G3  les comptes et les refus : le gazole brule = la regle du domaine 27, le stock de la garnison baisse d autant ; la base
    de la compagnie defendue par une autre ; refuses sans rien bruler : un objectif deja tenu, un objectif inconnu, plus
    de compagnie libre.
G4  identite : sans operation de B, EM.avancer donne au bit les memes mondes que l ancienne boucle ( 1 jour, une
    operation de A en cours ).
G5  le temoin : campagne de 4 jours, Stratis ( doctrine ) contre Malden ( defense ) : chaque jour B pose une garde
    acceptee tant qu il reste des objectifs a tenir ; sa premiere garde va a un objectif attaque s il y en a eu ; en
    information, les buts de A avec et sans defenseur actif.
( amende 03/10 07 h 15 apres le refus sur 2141 / 2142, avant le rejugement sur 2143 / 2144 : G3 sur le premier objectif
  dont la compagnie libre la plus proche est a plus de 2 km ; G5 : une garde chaque jour ou le temoin a un objectif,
  attendre seulement sa liste epuisee ; G6 ( le defaut de la mobilisation ) : apres une vraie operation avec des
  blesses, tous les rentres sains de nouveau mobilisables, aucun blesse hospitalise ; mobiliser toute l armee, la
  demobiliser, la remobiliser : le meme nombre )
python -m guerre.porte_defenseur"""
import json
import math
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d17_hopitaux as HM, d25_armee as A, d27_armee_tactique as TT
from . import campagne as CA, etat_major as EM, expedition as EX, frappes as FR, logistique as LO, moteur as GM
from . import projection as PR
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_defenseur.json"


def gazole(w, lid):
    return float(w.garnisons[lid].get("carburant", 0.0))


def cible_lointaine(w):
    """Le premier objectif de Malden dont la compagnie libre la plus proche est a plus de KM_TRANSPORT."""
    p = w.pays; U = A._dom(p).unites; c = w.carte
    for o in EX.OB.objectifs_carte("malden"):
        best = min((math.hypot(c.par_n[int(U["base"][u])].pos[0] - o["pos"][0], c.par_n[int(U["base"][u])].pos[1] - o["pos"][1])
                    for u in range(U.n) if int(U["niveau"][u]) == A.COMPAGNIE and int(U["base"][u]) >= 0 and len(TT._aptes(p, u))),
                   default=None)
        if best is not None and best / 1000.0 > TT.KM_TRANSPORT: return o["id"]
    return None


def main(gA=2143, gB=2144):
    t0 = time.time(); R = {}
    print(f"PORTE S3a DU DEFENSEUR : Stratis {gA} contre Malden {gB}", flush=True)
    wA = AR.creer_ile("Stratis", gA, 20); T.jours(wA, 1); wB = AR.creer_ile("Malden", gB, 20); T.jours(wB, 1)
    octA, octB = pickle.dumps(wA, protocol=4), pickle.dumps(wB, protocol=4)
    # G1
    a = pickle.loads(octA); b = pickle.loads(octB)
    PR.acheter(b, "lcu", 1); op = EX.lancer_operation(b, "Malden", "port01", "lcu", 400)
    if op.get("ok"): EM.avancer(a, b, int(a.pas) + 144)
    ob = EX._ops(b)[0] if EX._ops(b) else {}
    sub = [x for x in EX._subies(a) if x["type"] == "assaut" and x["attaquant"] == "Malden"]
    G1 = bool(op.get("ok")) and FR._etat(a).get("port01", 0.0) > 0 and bool(sub) and ob.get("etat") == "rentree"
    R["G1"] = {"ok": G1, "operation": {k: op.get(k) for k in ("ok", "raison", "arrivee", "retour")}, "port_de_A": FR._etat(a).get("port01"),
               "subies_par_A": sub, "etat_dans_B": ob.get("etat")}
    print(f"  G1 : {'OUI' if G1 else 'NON'} {json.dumps(R['G1'], default=str)[:500]}", flush=True)
    # G2
    w = pickle.loads(octA); nums = GM.mobiliser(w, 100, ids=EX.membres_a_projeter(w, 100)); LO.emporter(w, nums); cp = EX.corps(w, nums)
    o = EX.objectif("Malden", "port01"); res = {False: [], True: []}; poses = []
    for renf in (False, True):
        for sg in range(3):
            wb = pickle.loads(octB)
            rr = EX.renforcer(wb, "port01") if renf else None
            u, cv = EX.defenseur(wb, o)
            r = EX.assaut(wb, "Stratis", cp, "port01", seed=(9960 + sg,))
            res[renf].append(r["dommages"])
            if renf: poses.append((rr["ok"], rr["unite"], u, cv, r["defenseur"]))
    G2 = (any(d > 0 for d in res[False]) and all(ok and un == u == ud and cv == "dur" for ok, un, u, cv, ud in poses)
          and sum(res[True]) < sum(res[False]))
    R["G2"] = {"ok": G2, "dommages_sans": res[False], "dommages_avec": res[True], "poses": poses}
    print(f"  G2 : {'OUI' if G2 else 'NON'} {R['G2']}", flush=True)
    # G3
    wb = pickle.loads(octB); pB = wb.pays; U = A._dom(pB).unites
    lids = {wb.carte.par_n[int(U["base"][x])].id for x in range(U.n) if int(U["niveau"][x]) == A.COMPAGNIE and int(U["base"][x]) >= 0}
    g0 = {l: gazole(wb, l) for l in lids}
    c3 = cible_lointaine(wb)
    rr = EX.renforcer(wb, c3); u = rr["unite"]; b = wb.carte.par_n[int(U["base"][u])]
    n = len(TT._aptes(pB, u)); od = EX.objectif("Malden", c3)
    km = math.hypot(b.pos[0] - od["pos"][0], b.pos[1] - od["pos"][1]) / 1000.0
    attendu = math.ceil(n / TT.PLACES_CAMION) * 2.0 * 1.3 * km * A.VEHICULE["steyr_12m18"].unites_par_km if km > TT.KM_TRANSPORT else 0.0
    baisse = g0[b.id] - gazole(wb, b.id)
    autres = all(abs(g0[l] - gazole(wb, l)) <= 1e-9 for l in lids if l != b.id)
    base_o = {"id": "base_de_la_compagnie", "type": "base", "pos": (b.pos[0], b.pos[1])}
    u_base, _ = EX.defenseur(wb, base_o)
    g_av = {l: gazole(wb, l) for l in lids}
    deja = EX.renforcer(wb, c3); inconnu = EX.renforcer(wb, "lune01")
    sans_bruler_1 = all(abs(g_av[l] - gazole(wb, l)) <= 1e-9 for l in lids)
    while True:                                     # epuiser les compagnies libres
        libres = [x for x in EX.OB.objectifs_carte("malden") if x["id"] not in EX._gardes(wb)]
        if not libres: break
        r_ = EX.renforcer(wb, libres[0]["id"])
        if not r_["ok"]: break
    reste = [x for x in EX.OB.objectifs_carte("malden") if x["id"] not in EX._gardes(wb)]
    g_av2 = {l: gazole(wb, l) for l in lids}
    plus = EX.renforcer(wb, reste[0]["id"]) if reste else {"ok": False, "raison": "plus d objectif libre"}
    G3 = (rr["ok"] and attendu > 0 and abs(rr["gazole"] - attendu) <= 1e-9 and abs(baisse - attendu) <= 1e-9 and autres and u_base is not None
          and u_base != u and not deja["ok"] and not inconnu["ok"] and sans_bruler_1
          and not plus["ok"] and plus.get("raison") == "aucune compagnie libre" and all(abs(g_av2[l] - gazole(wb, l)) <= 1e-9 for l in lids))
    R["G3"] = {"ok": G3, "objectif": c3, "renfort": rr, "attendu": attendu, "baisse": baisse, "autres_garnisons_intactes": autres,
               "base_defendue_par": u_base, "deja_tenu": deja, "inconnu": inconnu, "plus_de_compagnie": plus,
               "gardes": len(EX._gardes(wb))}
    print(f"  G3 : {'OUI' if G3 else 'NON'} {json.dumps(R['G3'], default=str)[:700]}", flush=True)
    # G4
    w1, b1 = pickle.loads(octA), pickle.loads(octB); w2, b2 = pickle.loads(octA), pickle.loads(octB)
    for w_ in (w1, w2): PR.acheter(w_, "lcu", 1); EX.lancer_operation(w_, "Stratis", "base01", "lcu", 60)
    EM.avancer(w1, b1, int(w1.pas) + 144)
    while int(w2.pas) < int(w1.pas): w2.pas_suivant(); b2.pas_suivant(); EX.avancer_operations(w2, b2)
    G4 = PE.empreinte_etendue(w1) == PE.empreinte_etendue(w2) and PE.empreinte_etendue(b1) == PE.empreinte_etendue(b2)
    R["G4"] = {"ok": G4}
    print(f"  G4 : {'OUI' if G4 else 'NON'}", flush=True)
    # G5
    avec = CA.campagne("Stratis", gA, "Malden", gB, "doctrine", 4, chef_B="defense")
    sans = CA.campagne("Stratis", gA, "Malden", gB, "doctrine", 4)
    tb = avec["tours_B"]; okj = True; premier = None; tenus = []; ordre_ok = True
    for t in tb:
        ex = t["execution"][0] if t["execution"] else None
        if ex is None: okj = False; continue
        act, r = ex
        attaques = [s["objectif"] for s in avec["subies_B"] if s["pas"] < t["pas"]]
        cands = [x for x in reversed(attaques) if x not in tenus] + [x for x in ("port01", "centrale01", "depot01") if x not in tenus]
        if not cands:                                   # ( amende ) la liste du temoin epuisee : il attend
            if act.get("type") != "attendre": okj = False
            continue
        if act.get("type") != "renforcer" or not r.get("ok"): okj = False; continue
        if act["objectif"] != cands[0]: ordre_ok = False
        if premier is None: premier = (t["jour"], act["objectif"], bool(attaques))
        tenus.append(act["objectif"])
    G5 = okj and ordre_ok and premier is not None and len(tb) == 4
    R["G5"] = {"ok": G5, "tours_B": [(t["jour"], t["execution"]) for t in tb], "premiere_garde": premier, "ordre": ordre_ok,
               "attaques_subies": avec["subies_B"],
               "buts_A_avec_defenseur": avec["buts"], "pertes_A_avec": avec["bilan"]["pertes_A"],
               "buts_A_sans_defenseur": sans["buts"], "pertes_A_sans": sans["bilan"]["pertes_A"]}
    print(f"  G5 : {'OUI' if G5 else 'NON'} {json.dumps(R['G5'], default=str)[:900]}", flush=True)
    # G6 ( amende ) : la mobilisation
    a6 = pickle.loads(octA); b6 = pickle.loads(octB)
    PR.acheter(a6, "lcu", 1); op6 = EX.lancer_operation(a6, "Stratis", "base01", "lcu", 60)
    k = 0
    while op6.get("ok") and EX._ops(a6)[0]["etat"] != "rentree" and k < 400:
        a6.pas_suivant(); b6.pas_suivant(); EX.avancer_operations(a6, b6); k += 1
    f6 = GM._front(a6); hop = {int(h) for h in HM._dom(a6.pays).actifs}
    rentres = {s["i"] for s in f6.values() if s["etat"] == "rentre"}
    hosp = {s["i"] for s in f6.values() if s["etat"] == "blesse" and s["i"] in hop}
    ids2 = {f6[x]["i"] for x in GM.mobiliser(a6, 10 ** 6)}
    w7 = pickle.loads(octA); k1 = GM.mobiliser(w7, 10 ** 6); LO.emporter(w7, k1); EX.demobiliser(w7, k1); k2 = GM.mobiliser(w7, 10 ** 6)
    G6 = bool(rentres) and rentres <= ids2 and bool(hosp) and not (hosp & ids2) and len(k1) == len(k2) > 0
    R["G6"] = {"ok": G6, "rentres": len(rentres), "rentres_remobilisables": len(rentres & ids2), "blesses_hospitalises": len(hosp),
               "hospitalises_remobilises": len(hosp & ids2), "armee_1": len(k1), "armee_2": len(k2)}
    print(f"  G6 : {'OUI' if G6 else 'NON'} {R['G6']}", flush=True)
    oks = [R[k]["ok"] for k in ("G1", "G2", "G3", "G4", "G5", "G6")]
    verdict = "FRANCHIE ( S1 a part )" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graines=[gA, gB], duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE S3a DU DEFENSEUR : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_DEFENSEUR", flush=True)
    return 0 if all(oks) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(int(a[0]), int(a[1])) if len(a) >= 2 else main())
