"""Porte 3a' des blesses, ALIGNEE sur le chemin du domaine 27 ( HMT-194 ). Criteres ecrits avant la mesure ( Plane,
02/10 ) : Malden ( 1991 ), echelle 20, 12 soldats mobilises, emportant leurs coups, suivis a 2 km de leur base, dommages
0 ; 0,3 ; 0,49 ; 0,5 ; 0,7 ; 0,95 ( deux soldats chacun ).

E1  sous 0,5 : au front ( absents ) ; a 0,5 et au-dela : non absents, une evacuation du 26 chacun depuis le lieu le plus
    proche de leur position, un passage du 17 vers l hopital MILITAIRE, une affection balistique cause combat d ISS = la
    formule ( 9 ; 35 ; 68 ), ps.iss = HM._iss recalcule.
E2  controle positif de l ordre : aucun evacue dans la file des ambulances civiles ; un temoin blesse sans evacuation y est
    ( ou part vers un etablissement civil ).
E3  une seule fois : un second releve n evacue ni ne blesse personne, d26.evacuations inchange.
E4  les munitions : la reserve du 27 baisse exactement des coups des evacues ; armureries inchangees ; anomalies du 25
    et du 26 vides.
E5  identite : tous sous 0,5, identique au bit au jumeau sur 2 jours.
Information : helicoptere contre ambulance ; sur 3 jours, morts, encore soignes, gueris.
python -m guerre.porte_soldats"""
import json
import pickle
import sys
import time

from monde import archipel as AR, population as PO, tests as T
from monde.pays import d17_hopitaux as HM, d25_armee as A, d26_armee_soutien as S, d27_armee_tactique as T27
from . import logistique as LO, moteur as GM, soldats as SO
from .arsenal import porte_etat_des_lieux as PE

SORTIE = "/mnt/data/hmt/arsenal/porte_soldats.json"
DOMMAGES = (0.0, 0.3, 0.49, 0.5, 0.7, 0.95) * 2


def blessures(w, depuis):
    return [e for e in list(w.pays.socle.journal.recents)[depuis:] if e.get("type") == "blessure"]


def stocks(w):
    d = w.pays.domaines[A.DOMAINE]
    return {(a.lieu, b): float(a.stock[d.bids[b]]) for a in d.armureries for b in A.NOMS_MUNITIONS + ("pieces",)}


def appel_civil(H, i):
    return any(i in v for v in H.appels.values())


def main():
    t0 = time.time(); R = {}
    print("PORTE 3a' DES BLESSES ( alignee 26 et 27 ) : Malden 1991, 12 soldats", flush=True)
    w0 = AR.creer_ile("Malden", 1991, 20)
    nums = GM.mobiliser(w0, 12); LO.emporter(w0, nums)
    oct_ = pickle.dumps(w0, protocol=4)
    w = pickle.loads(oct_); p = w.pays; f = GM._front(w); t = w.table; carte = w.carte
    rang = p.col("habitant", "ar_rang"); E = A._dom(p).eff
    pos = {}
    for n in nums:
        r = int(rang[f[n]["i"]])
        l = carte.par_n[int(E["base"][r])] if r >= 0 else carte.gouvernement
        pos[n] = (l.pos[0] + 2000.0, l.pos[1], carte.iles.index(l.ile))
    GM.suivre(w, [(n, pos[n][0], pos[n][1], dg) for n, dg in zip(nums, DOMMAGES)])
    d26 = S._dom(p); H = HM._dom(p)
    ev0 = len(d26.evacuations); st0 = stocks(w); rv0 = dict(T27._dom(p).reserve)
    portes0 = {n: (LO._L(w)["porte"].get(n, {}).get("base"), LO._L(w)["porte"].get(n, {}).get("cal"), LO.coups(w, n)) for n in nums}
    j0 = len(p.socle.journal.recents)
    ev = SO.evacuer_blesses(w)
    bl = blessures(w, j0)
    evacues = [n for n, dg in zip(nums, DOMMAGES) if dg >= SO.SEUIL_EVAC]
    restes = [n for n in nums if n not in evacues]
    # E1
    ok_restes = all(f[n]["etat"] == "front" and t.statut[f[n]["i"]] == PO.ABSENT for n in restes)
    evs = {int(x[1]): x for x in d26.evacuations[ev0:]}
    detail = {}
    for n, dg in zip(nums, DOMMAGES):
        if dg < SO.SEUIL_EVAC: continue
        i = f[n]["i"]; ps = H.actifs.get(i)
        lieu_att = carte.par_n[S._lieu_proche(p, d26, pos[n][0], pos[n][1], pos[n][2])].id
        b = [e for e in bl if e.get("habitant") == i]
        iss_att = SO.iss_de(dg)
        hab = PO.Habitant(t, i)
        detail[n] = {
            "non_absent": i not in w.absents and int(t.statut[i]) == PO.RESIDENT,
            "evacue_26": i in evs, "moyen": evs[i][2] if i in evs else None,
            "lieu": f[n].get("lieu_evacuation"), "lieu_attendu": lieu_att,
            "hopital_militaire": ps is not None and d26.hopital is not None and ps.etab == d26.hopital.id,
            "blessure": [(e.get("nature"), e.get("iss"), e.get("cause")) for e in b], "iss_attendu": iss_att,
            "iss_recalcule": ps is not None and ps.iss == HM._iss(p, hab) and ps.iss > 0}
    def bon(x):
        return (x["non_absent"] and x["evacue_26"] and x["lieu"] == x["lieu_attendu"] and x["hopital_militaire"]
                and x["blessure"] == [("balistique", x["iss_attendu"], "combat")] and x["iss_recalcule"])
    E1 = ok_restes and len(ev) == len(evacues) and all(bon(x) for x in detail.values()) and len(evs) == len(evacues)
    R["E1"] = {"ok": E1, "restes_au_front": ok_restes, "evacues": len(ev), "attendus": len(evacues),
               "detail": {str(k): v for k, v in detail.items()}}
    print(f"  E1 seuil et chemin : {'OUI' if E1 else 'NON'} {R['E1']}", flush=True)
    # E2 : l ordre evacuer puis blesser
    aucun_civil = not any(appel_civil(H, f[n]["i"]) for n in evacues)
    wt = pickle.loads(oct_); pt = wt.pays; ft = GM._front(wt); Ht = HM._dom(pt); tt = wt.table
    it = ft[nums[0]]["i"]; ht = wt.habitants[it]
    wt.absents.pop(it, None); tt.statut[it] = PO.RESIDENT
    dom = getattr(ht, "domicile", None)
    if dom is not None: tt.lieu[it] = dom.n
    from monde.pays import d16_medecine as MED
    MED.blesser(pt, ht, "balistique", 35, "combat")
    pst = Ht.actifs.get(it); dt = S._dom(pt)
    temoin_civil = appel_civil(Ht, it) or (pst is not None and dt.hopital is not None and pst.etab != dt.hopital.id)
    E2 = aucun_civil and temoin_civil
    R["E2"] = {"ok": E2, "aucun_evacue_en_file_civile": aucun_civil, "temoin_civil": temoin_civil,
               "temoin": {"appel": appel_civil(Ht, it), "etab": None if pst is None else pst.etab}}
    print(f"  E2 ordre : {'OUI' if E2 else 'NON'} {R['E2']}", flush=True)
    # E3 : une seule fois
    ev_n = len(d26.evacuations); j1 = len(p.socle.journal.recents)
    ev2 = SO.evacuer_blesses(w)
    E3 = ev2 == [] and len(d26.evacuations) == ev_n and not blessures(w, j1)
    R["E3"] = {"ok": E3, "second": ev2}
    print(f"  E3 une seule fois : {'OUI' if E3 else 'NON'}", flush=True)
    # E4 : les munitions
    rv1 = dict(T27._dom(p).reserve)
    attendu = {}
    for n in evacues:
        lid, c, q = portes0[n]
        if lid is not None and c is not None and c >= 0 and q > 0: attendu[(lid, c)] = attendu.get((lid, c), 0.0) + q
    cles = set(rv0) | set(rv1)
    res_ok = all(abs((rv0.get(k, 0.0) - rv1.get(k, 0.0)) - attendu.get(k, 0.0)) <= 1e-9 for k in cles)
    an = A.anomalies(p) + S.anomalies(p)
    E4 = res_ok and stocks(w) == st0 and all(LO.coups(w, n) == 0 for n in evacues) and not an and sum(attendu.values()) > 0
    R["E4"] = {"ok": E4, "rendus": {f"{k[0]}:{k[1]}": v for k, v in attendu.items()}, "reserve_juste": res_ok,
               "armureries_inchangees": stocks(w) == st0, "anomalies": an[:5]}
    print(f"  E4 munitions : {'OUI' if E4 else 'NON'} {R['E4']}", flush=True)
    # E5 : l identite
    wa, wb = pickle.loads(oct_), pickle.loads(oct_)
    GM.suivre(wa, [(n, 1000.0, 1000.0, dg) for n, dg in zip(nums, (0.0, 0.3, 0.49) * 4)])
    r5 = SO.evacuer_blesses(wa)
    ident = r5 == []
    for _ in range(2):
        T.jours(wa, 1); T.jours(wb, 1)
        if PE.empreinte_etendue(wa) != PE.empreinte_etendue(wb): ident = False
    R["E5"] = {"ok": ident}
    print(f"  E5 identite : {'OUI' if ident else 'NON'}", flush=True)
    # information : 3 jours
    moyens = {}
    for x in detail.values(): moyens[x["moyen"]] = moyens.get(x["moyen"], 0) + 1
    T.jours(w, 3)
    ids = [f[n]["i"] for n in evacues]
    R["information"] = {"moyens": moyens, "morts": sum(1 for i in ids if not t.vivant[i]),
                        "encore_soignes": sum(1 for i in ids if t.vivant[i] and i in H.actifs),
                        "sortis": sum(1 for i in ids if t.vivant[i] and i not in H.actifs)}
    print(f"  information : {R['information']}", flush=True)
    oks = [R[k]["ok"] for k in ("E1", "E2", "E3", "E4", "E5")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 3a' DES BLESSES : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_SOLDATS", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
