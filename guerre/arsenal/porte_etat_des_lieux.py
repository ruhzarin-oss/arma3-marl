"""Porte de l etat des lieux du materiel ( HMT-191, etape 0d ). Criteres ecrits avant la mesure ( Plane ) :

E1  deux chemins, jours 0, 10, 20, 30, chaque base et chaque modele : armes et optiques ( dotees + ratelier du domaine
    25 = individus du Parc tenus par l armurerie ) ; mortiers ( table du domaine = individus du Parc ) ; protections et
    radios ( dotees = compte du domaine <= cohorte du Parc ) ; vehicules ( lignes vivantes = individus du Parc, meme etat ) ;
    munitions et pieces ( stocks du Livre = depart + entrees - sorties comptees ; aucune munition_hors_consommation ) ;
    Parc.verifier() = 0 sur les modeles du domaine 25. Aucun ecart.
E2  controle positif ( Stratis, jour 30, sur une copie ) : un vehicule detruit, 100 cartouches de 5,56 tirees, 50 de 7,62
    sorties en cachette : -1 vehicule et +1 detruit, -100 et -50, anomalie pour le 7,62 SEUL.
E3  lecture seule ( Malden, 10 jours ) : avec et sans etat des lieux toutes les 6 h, empreinte etendue identique au bit.
E4  information : temps, objets, valeur du materiel et sa part dans les credits d achats annuels.

Iles de l archipel Stratis ( graine 1913 ) et Malden ( 1914 ), echelle 20.
python -m guerre.arsenal.porte_etat_des_lieux"""
import hashlib
import json
import pickle
import sys
import time

import numpy as np

from monde import archipel as AR, config as C, tests as T
from monde.porte_domaines import empreinte
from monde.pays import d25_armee as A
from monde.socle import objets as O
from . import etat_des_lieux as EL

ILES = (("Stratis", 1913), ("Malden", 1914))
ECHELLE = 20
JOURS_E1 = (0, 10, 20, 30)
SORTIE = "/mnt/data/hmt/arsenal/porte_etat_des_lieux.json"


def _h(x): return hashlib.sha1(pickle.dumps(x, protocol=4)).hexdigest()[:16]


def empreinte_etendue(w):
    """L empreinte du moteur ( porte_domaines ) plus les tables du domaine 25, le Parc et les stocks des armureries."""
    e = empreinte(w)
    d = w.pays.domaines[A.DOMAINE]; parc = w.pays.socle.parc
    for nom, tab in (("eff", d.eff), ("veh", d.veh), ("coll", d.coll), ("unites", d.unites)):
        e[f"armee.{nom}"] = _h({k: np.asarray(v[:tab.n]).tobytes() for k, v in sorted(tab.cols.items())})
    e["armee.comptes"] = _h((sorted(d.ratelier.items()), sorted(d.dotes.items()), sorted(d.stock0.items()),
                             sorted(d.entrees.items()), sorted(d.sorties.items())))
    e["parc.objets"] = _h(sorted((o.id, o.modele, o.lieu, o.usure, o.etat) for o in parc.objets.values()))
    e["parc.cohortes"] = _h(sorted((m, l, c.nombre, c.usure) for (m, _p, l), c in parc.cohortes.items()))
    e["parc.comptes"] = _h(parc.comptes)
    e["armureries"] = _h([[float(a.stock[d.bids[b]]) for b in A.NOMS_MUNITIONS + ("pieces",)] for a in d.armureries])
    return e


def recouper(w):
    """E1 : [ ecarts ] entre l etat des lieux ( tables du domaine 25 ) et le Parc / le Livre."""
    p = w.pays; d = p.domaines[A.DOMAINE]; parc = p.socle.parc
    e = EL.etat_des_lieux(w)
    ecarts = []
    mid_vehicule = {d.mids[v.nom]: v.nom for v in A.VEHICULES}
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]; eb = e["bases"][EL._nom_lieu(w, b)]
        individus = {}
        for o in parc.objets.values():
            if o.proprietaire is arm: individus.setdefault(o.modele, []).append(o)
        for fam in ("armes", "optiques"):
            table = A.ARMES if fam == "armes" else A.OPTIQUES
            for mod in table:
                if mod.nom not in d.mids or mod.nom in A.COLLECTIVES: continue
                x = eb[fam].get(mod.nom, {"dotees": 0, "ratelier": 0})
                a = x["dotees"] + x["ratelier"]; bb = len(individus.get(d.mids[mod.nom], []))
                if a != bb: ecarts.append((eb["lieu"], mod.nom, "individus", a, bb))
        bb = len(individus.get(d.mids["mortier_81"], []))
        if eb["mortiers"] != bb: ecarts.append((eb["lieu"], "mortier_81", "individus", eb["mortiers"], bb))
        for fam in ("protections", "radios"):
            for nom, x in eb[fam].items():
                if x["dotees"] != x["compte_du_domaine"] or x["dotees"] > x["stock"]:
                    ecarts.append((eb["lieu"], nom, "dotees", x["dotees"], x["compte_du_domaine"], x["stock"]))
        par_etat = {}
        for mid, nom in mid_vehicule.items():
            for o in individus.get(mid, []):
                s = par_etat.setdefault(nom, {"total": 0, "service": 0, "panne": 0, "immobilise": 0})
                s["total"] += 1; s[O.ETATS[o.etat]] += 1
        for nom in set(par_etat) | set(eb["vehicules"]):
            a = {k: eb["vehicules"].get(nom, {}).get(k, 0) for k in ("total", "service", "panne", "immobilise")}
            bb = par_etat.get(nom, {"total": 0, "service": 0, "panne": 0, "immobilise": 0})
            if a != bb: ecarts.append((eb["lieu"], nom, "vehicules", a, bb))
    for bien in A.NOMS_MUNITIONS + ("pieces",):
        s = sum(float(a.stock[d.bids[bien]]) for a in d.armureries)
        att = d.stock0.get(bien, 0.0) + d.entrees.get(bien, 0.0) - sum(v for (bb, m), v in d.sorties.items() if bb == bien)
        lu = (e["ile_totaux"]["munitions"].get(bien, 0.0) if bien != "pieces" else e["ile_totaux"]["pieces"])
        if abs(s - att) > 1e-6 * max(1.0, abs(att)): ecarts.append(("ile", bien, "livre_contre_comptes", s, att))
        if abs(lu - s) > 1e-6 * max(1.0, abs(s)) and not (bien != "pieces" and lu == 0.0 and s == 0.0):
            ecarts.append(("ile", bien, "etat_contre_livre", lu, s))
    for a in A.anomalies(p):
        if a[0] == "munition_hors_consommation": ecarts.append(("ile",) + tuple(map(str, a)))
    noms = {m.nom for m in parc.modeles if m.id in d.idx_parc}
    for nom, v in parc.verifier().items():
        if nom in noms and v != 0: ecarts.append(("ile", nom, "parc_verifier", v))
    return ecarts, e


def controle_positif(w):
    """E2 sur une copie du monde : ( resultat, details )."""
    w = pickle.loads(pickle.dumps(w, protocol=4))
    p = w.pays; d = p.domaines[A.DOMAINE]; L = p.socle.livre; V = d.veh
    e0 = EL.etat_des_lieux(w)
    nveh0 = sum(x["total"] for x in e0["ile_totaux"]["vehicules"].values())
    det0 = sum(e0["vehicules_detruits"].values())
    k = int(np.nonzero(V["oid"][:V.n] >= 0)[0][0]); oid = int(V["oid"][k])
    A.perdre_objet(p, oid, "detruit")
    arm = max(d.armureries, key=lambda a: float(a.stock[d.bids["mun_556"]]))
    tire = A.tirer(p, arm.lieu, "mun_556", 100.0, "tir_combat")
    vole = L.puits(arm.stock, d.bids["mun_762"], 50.0, "consomme", "tir_combat")   # sans passer par le domaine
    e1 = EL.etat_des_lieux(w)
    nveh1 = sum(x["total"] for x in e1["ile_totaux"]["vehicules"].values())
    det1 = sum(e1["vehicules_detruits"].values())
    d556 = e0["ile_totaux"]["munitions"]["mun_556"] - e1["ile_totaux"]["munitions"]["mun_556"]
    d762 = e0["ile_totaux"]["munitions"]["mun_762"] - e1["ile_totaux"]["munitions"]["mun_762"]
    anom = {a[1].split(",")[0].strip("('\" ") for a in e1["anomalies"] if a[0] == "munition_hors_consommation"}
    ok = (nveh0 - nveh1 == 1 and det1 - det0 == 1 and abs(d556 - 100) < 1e-9 and abs(d762 - 50) < 1e-9
          and tire == 100 and vole == 50 and anom == {"mun_762"})
    return ok, {"vehicules": [nveh0, nveh1], "detruits": [det0, det1], "mun_556_sortie": d556, "mun_762_sortie": d762,
                "anomalies_munitions": sorted(anom), "tire": tire, "vole": vole}


def lecture_seule(octets, jours=10):
    """E3 : deux copies d un meme monde ; l une lit l etat des lieux toutes les 6 h. Rend ( identique, premier jour faux )."""
    w1 = pickle.loads(octets); w2 = pickle.loads(octets)
    pas6 = C.PAS_PAR_JOUR // 4
    for j in range(jours):
        for s in range(C.PAS_PAR_JOUR):
            w1.pas_suivant()
            if (s + 1) % pas6 == 0: EL.etat_des_lieux(w1)
        T.jours(w2, 1)
        if empreinte_etendue(w1) != empreinte_etendue(w2): return False, j + 1
    return True, None


def main():
    t0 = time.time(); res = {"iles": {}}
    E1 = True; E2 = None; E3 = None
    for ile, graine in ILES:
        print(f"PORTE DE L ETAT DES LIEUX : {ile}, graine {graine}, echelle {ECHELLE}", flush=True)
        w = AR.creer_ile(ile, graine, ECHELLE)
        if ile == "Malden":
            octets = pickle.dumps(w, protocol=4)
            E3, jour_faux = lecture_seule(octets)
            print(f"  E3 lecture seule sur 10 jours : {'OUI' if E3 else 'NON, jour ' + str(jour_faux)}", flush=True)
            res["E3"] = {"ok": E3, "jour_faux": jour_faux}
        info = []
        for j in range(max(JOURS_E1) + 1):
            if j in JOURS_E1:
                ecarts, e = recouper(w)
                E1 = E1 and not ecarts
                nobj = sum(1 for o in w.pays.socle.parc.objets.values() if o.modele in w.pays.domaines[A.DOMAINE].idx_parc)
                info.append({"jour": j, "ecarts": ecarts[:20], "n_ecarts": len(ecarts), "duree_ms": e["duree_ms"],
                             "objets_individuels": nobj, "valeur_eur": e["valeur_eur"],
                             "valeur_sur_achats_an": e.get("valeur_sur_achats_an"),
                             "militaires": e["ile_totaux"]["effectifs"],
                             "vehicules": {k: v["total"] for k, v in e["ile_totaux"]["vehicules"].items()},
                             "detruits": e["vehicules_detruits"]})
                print(f"  jour {j:2d} : E1 {len(ecarts)} ecart(s) {ecarts[:3]} ; {e['duree_ms']} ms, {nobj} objets, "
                      f"{e['ile_totaux']['effectifs']} militaires, {e['valeur_eur']:,.0f} EUR, "
                      f"{e.get('valeur_sur_achats_an')} ans d achats".replace(",", " "), flush=True)
            if j < max(JOURS_E1): T.jours(w, 1)
        res["iles"][ile] = info
        if ile == "Stratis":
            E2, det = controle_positif(w)
            print(f"  E2 controle positif : {'OUI' if E2 else 'NON'} {det}", flush=True)
            res["E2"] = {"ok": E2, **det}
    print(f"E1 deux chemins : {'OUI' if E1 else 'NON'}")
    print(f"E2 controle positif : {'OUI' if E2 else 'NON'}")
    print(f"E3 lecture seule : {'OUI' if E3 else 'NON'}")
    verdict = "FRANCHIE" if (E1 and E2 and E3) else "REFUSEE"
    res.update(verdict=verdict, E1=E1, duree_s=round(time.time() - t0))
    json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE DE L ETAT DES LIEUX : {verdict} ( {res['duree_s']} s )")
    print("FIN_PORTE_ETAT_DES_LIEUX", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
