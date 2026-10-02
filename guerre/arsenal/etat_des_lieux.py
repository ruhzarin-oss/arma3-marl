"""L ETAT DES LIEUX DU MATERIEL d une ile ( Arma a fond, etape 0d, HMT-191 ) : qui a quoi, ou, en quel etat.

Pour chaque base : les effectifs ; les armes et optiques par modele ( dotees, au ratelier, en reserve, usure moyenne ) ;
les protections et les radios ( en stock, dotees ) ; les vehicules par modele ( en service, en panne, km moyens ) ; les
mortiers ; les munitions par calibre ( stock, journees de tir, dotation de combat couverte ) ; les pieces ; le carburant
de la garnison. Pour l ile : les totaux, les vehicules detruits depuis l installation, la valeur du materiel, les
credits d achats de la defense, les anomalies du domaine 25 et la classe Arma de chaque modele avec son statut dans le
catalogue verifie ( guerre/arsenal/sonde_registre.json ).

LECTURE SEULE : rien n est ecrit dans le monde ( porte E3 ). Chaque compte est pris a la source du domaine 25 ( ses
tables ) ; la porte le recoupe par le Parc et le Livre du socle ( E1 ).

   python -m guerre.arsenal.etat_des_lieux --ile Stratis --graine 7 --echelle 20 --jours 3
   python -m guerre.arsenal.etat_des_lieux --instantane <fichier d une ile> [--json sortie.json]"""
import argparse
import json
import math
import os
import time

import numpy as np

from monde.pays import d25_armee as A
from monde.socle import objets as O

REGISTRE = "/mnt/data/hmt/arsenal/sonde_registre.json"


def _statuts_arma():
    """{ classe : statut } tire de la sonde du registre ( 0b ) : « jeu » ( catalogue verifie en jeu, porte du lecteur
    franchie le 02/10 ), « CUP » ( present avec CUP, lecture de CUP pas encore verifiee en jeu ), « absente »."""
    try:
        lignes = json.load(open(REGISTRE))
    except (OSError, ValueError):
        return {}
    out = {}
    for l in lignes:
        if l.get("jeu", {}).get("existe"): out[l["arma"]] = "jeu"
        elif l.get("jeu+CBA+CUP", {}).get("existe"): out[l["arma"]] = "CUP"
        else: out[l["arma"]] = "absente"
    return out


def _nom_lieu(w, b):
    l = w.carte.par_n[b]
    return str(l.id)


def _usure_moyenne(parc, oids):
    u = [parc.objets[o].usure for o in oids if o in parc.objets]
    return round(float(np.mean(u)), 3) if u else None


def etat_des_lieux(w):
    """Le dictionnaire de l etat des lieux de l ile du monde `w` ( domaine 25 installe )."""
    t0 = time.perf_counter()
    p = w.pays; d = p.domaines[A.DOMAINE]; parc = p.socle.parc
    E = d.eff; V = d.veh; K = d.coll
    rows = A._lignes(d)
    statuts = _statuts_arma()
    mun_eur = {m[0]: m[2] for m in A.MUNITIONS}
    prix_pieces = A.IND.BIENS["pieces"][2]
    bases, tot = {}, {"armes": {}, "optiques": {}, "protections": {}, "radios": {}, "vehicules": {}, "munitions": {},
                      "pieces": 0.0, "valeur_dr": 0.0, "effectifs": 0, "conscrits": 0, "instruction": 0}
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]; lid = arm.lieu
        rb = rows[E["base"][rows] == b]
        eb = {"lieu": _nom_lieu(w, b), "effectifs": int(len(rb)),
              "conscrits": int((E["conscrit"][rb] == 1).sum()),
              "instruction": int((E["statut"][rb] == A.EN_INSTRUCTION).sum())}
        valeur = 0.0
        # armes et optiques individuelles ( numeros de serie )
        for famille, table, champs, idx in (("armes", A.ARMES, ("arme", "arme2"), A.IDX_ARME),
                                            ("optiques", A.OPTIQUES, ("optique",), A.IDX_OPTIQUE)):
            sortie = {}
            tous = np.arange(E.n)
            sur_base = tous[E["base"][:E.n] == b]
            for k, mod in enumerate(table):
                if mod.nom not in d.mids or (famille == "armes" and mod.nom in A.COLLECTIVES): continue
                dotes = []
                for ch in champs:
                    m = sur_base[E[ch + "_m"][sur_base] == k]
                    dotes += [int(x) for x in E[ch][m].tolist() if x >= 0]
                ratelier = list(d.ratelier.get((b, mod.nom), []))
                c = parc.cohortes.get((d.mids[mod.nom], arm, arm.lieu))
                reserve = int(c.nombre) if c is not None else 0
                n = len(dotes) + len(ratelier) + reserve
                if n == 0: continue
                prix = parc.modeles[d.mids[mod.nom]].prix_monde
                valeur += n * prix
                sortie[mod.nom] = {"total": n, "dotees": len(dotes), "ratelier": len(ratelier), "reserve": reserve,
                                   "usure_moyenne": _usure_moyenne(parc, dotes + ratelier), "arma": mod.arma,
                                   "statut_arma": statuts.get(mod.arma, "?")}
                tt = tot[famille].setdefault(mod.nom, {"total": 0, "dotees": 0})
                tt["total"] += n; tt["dotees"] += len(dotes)
            eb[famille] = sortie
        # protections et radios ( cohortes de l armurerie, dotees comptees par le domaine )
        for famille, table, champs in (("protections", A.PROTECTIONS, ("protection", "casque")),
                                       ("radios", A.RADIOS, ("radio",))):
            sortie = {}
            for k, mod in enumerate(table):
                dotees = int(sum(((E[ch][rb] == k).sum()) for ch in champs))
                c = parc.cohortes.get((d.mids[mod.nom], arm, arm.lieu))
                stock = int(c.nombre) if c is not None else 0
                if stock == 0 and dotees == 0: continue
                valeur += stock * parc.modeles[d.mids[mod.nom]].prix_monde
                sortie[mod.nom] = {"stock": stock, "dotees": dotees, "compte_du_domaine": int(d.dotes.get((b, mod.nom), 0)),
                                   "arma": mod.arma, "statut_arma": statuts.get(mod.arma, "?")}
                tt = tot[famille].setdefault(mod.nom, {"stock": 0, "dotees": 0})
                tt["stock"] += stock; tt["dotees"] += dotees
            eb[famille] = sortie
        # vehicules
        vk = np.nonzero((V["base"][:V.n] == b) & (V["oid"][:V.n] >= 0))[0]
        sortie = {}
        for k in vk.tolist():
            mod = A.VEHICULES[int(V["modele"][k])]
            s = sortie.setdefault(mod.nom, {"total": 0, "service": 0, "panne": 0, "immobilise": 0, "km": [], "arma": mod.arma,
                                            "statut_arma": statuts.get(mod.arma, "?")})
            s["total"] += 1; s[O.ETATS[int(V["etat"][k])]] += 1; s["km"].append(float(V["km"][k]))
            valeur += parc.modeles[d.mids[mod.nom]].prix_monde
        for nom, s in sortie.items():
            s["km_moyen"] = round(float(np.mean(s.pop("km"))), 1)
            tt = tot["vehicules"].setdefault(nom, {"total": 0, "service": 0, "panne": 0, "immobilise": 0})
            for c in ("total", "service", "panne", "immobilise"): tt[c] += s[c]
        eb["vehicules"] = sortie
        # mortiers ( armes collectives )
        kk = np.nonzero((K["base"][:K.n] == b) & (K["oid"][:K.n] >= 0))[0]
        eb["mortiers"] = int(len(kk))
        for _ in kk.tolist(): valeur += parc.modeles[d.mids["mortier_81"]].prix_monde
        # munitions, pieces, carburant
        cible = A._cible_munitions(p, d, b, 0)                      # la dotation de combat seule
        par_jour = A._instruction_par_jour(p, d, rb)
        mun = {}
        for bien in A.NOMS_MUNITIONS:
            s = float(arm.stock[d.bids[bien]])
            if s <= 0 and cible.get(bien, 0.0) <= 0: continue
            mun[bien] = {"stock": round(s, 1), "dotation_combat": round(cible.get(bien, 0.0), 1),
                         "dotations_couvertes": round(s / cible[bien], 2) if cible.get(bien, 0.0) > 0 else None,
                         "journees_de_tir": round(s / par_jour[bien], 1) if par_jour.get(bien, 0.0) > 0 else None}
            valeur += s * A._dr(mun_eur[bien])
            tot["munitions"][bien] = tot["munitions"].get(bien, 0.0) + s
        eb["munitions"] = mun
        eb["pieces_t"] = round(float(arm.stock[d.bids["pieces"]]), 3)
        valeur += eb["pieces_t"] * prix_pieces
        tot["pieces"] += eb["pieces_t"]
        try:
            g, bz, jours = A.carburant(p, lid)
            eb["carburant"] = {"unites_10l": round(float(g), 1), "besoin_jour": round(float(bz), 2),
                               "jours": round(float(jours), 1)}
        except (KeyError, AttributeError):
            eb["carburant"] = None
        eb["valeur_dr"] = round(valeur, 2)
        tot["valeur_dr"] += valeur
        for c in ("effectifs", "conscrits", "instruction"): tot[c] += eb[c]
        bases[eb["lieu"]] = eb
    # ( 02/10, HMT-193 ) le front : les munitions emportees par les soldats et celles des convois en route
    fr = next((a for a in d.armureries if a.lieu == "front" and a.lieu not in w.carte.lieux), None)
    front = None
    if fr is not None:
        front = {bien: round(float(fr.stock[d.bids[bien]]), 1) for bien in A.NOMS_MUNITIONS if float(fr.stock[d.bids[bien]]) > 0}
        for bien in A.NOMS_MUNITIONS:
            q = float(fr.stock[d.bids[bien]])
            if q > 0: tot["munitions"][bien] = tot["munitions"].get(bien, 0.0) + q
        tot["pieces"] += float(fr.stock[d.bids["pieces"]])
    detruits = {m.nom: parc.comptes[d.mids[m.nom]]["detruit"] for m in A.VEHICULES if parc.comptes[d.mids[m.nom]]["detruit"]}
    loi = getattr(d, "loi", None) or {}
    out = {"ile": getattr(w, "ile", None) or "?", "pas": int(w.pas),
           "jour": int(p.jour), "bases": bases, "front": front, "ile_totaux": tot, "vehicules_detruits": detruits,
           "valeur_eur": round(tot["valeur_dr"] * A.EUROS, 0),
           "achats_defense_an_dr": round(loi.get("achats_an", 0.0), 2) if loi else None,
           "anomalies": [list(map(str, a)) for a in A.anomalies(p)],
           "sans_preuve_arma": parc.sans_preuve_arma(),
           "duree_ms": None}
    if out["achats_defense_an_dr"]:
        out["valeur_sur_achats_an"] = round(tot["valeur_dr"] / out["achats_defense_an_dr"], 2)
    out["duree_ms"] = round(1000 * (time.perf_counter() - t0), 1)
    return out


def texte(e):
    """L etat des lieux en clair, base par base."""
    L = [f"ETAT DES LIEUX DU MATERIEL - ile {e['ile']}, jour {e['jour']} ( pas {e['pas']} )"]
    for nom, b in e["bases"].items():
        L.append(f"\nBASE {nom} : {b['effectifs']} militaires ( {b['conscrits']} conscrits, {b['instruction']} en instruction ) "
                 f"- valeur {b['valeur_dr']:,.0f} dr".replace(",", " "))
        for fam in ("armes", "optiques"):
            for m, x in b[fam].items():
                L.append(f"  {fam[:-1]:8s} {m:16s} {x['total']:5d}  dotees {x['dotees']:5d}  ratelier {x['ratelier']:3d}  "
                         f"reserve {x['reserve']:4d}  usure {x['usure_moyenne']}  [{x['arma']} : {x['statut_arma']}]")
        for fam in ("protections", "radios"):
            for m, x in b[fam].items():
                L.append(f"  {fam[:-1]:8s} {m:16s} {x['stock']:5d}  dotees {x['dotees']:5d}  [{x['arma']} : {x['statut_arma']}]")
        for m, x in b["vehicules"].items():
            L.append(f"  vehicule {m:16s} {x['total']:5d}  service {x['service']:3d}  panne {x['panne']:3d}  "
                     f"{x['km_moyen']:9.0f} km  [{x['arma']} : {x['statut_arma']}]")
        if b["mortiers"]: L.append(f"  mortier  mortier_81       {b['mortiers']:5d}")
        for m, x in b["munitions"].items():
            L.append(f"  munition {m:16s} {x['stock']:12,.0f}  dotation de combat x{x['dotations_couvertes']}  "
                     f"journees de tir {x['journees_de_tir']}".replace(",", " "))
        L.append(f"  pieces {b['pieces_t']} t ; carburant {b['carburant']}")
    t = e["ile_totaux"]
    L.append(f"\nILE : {t['effectifs']} militaires, materiel {t['valeur_dr']:,.0f} dr ( {e['valeur_eur']:,.0f} EUR )".replace(",", " ")
             + (f", soit {e['valeur_sur_achats_an']} annees de credits d achats de la defense" if e.get("valeur_sur_achats_an") else ""))
    L.append(f"  vehicules detruits depuis l installation : {e['vehicules_detruits'] or 0}")
    L.append(f"  anomalies du domaine 25 : {len(e['anomalies'])} {e['anomalies'][:5]}")
    L.append(f"  modeles sans preuve de vie dans Arma : {len(e['sans_preuve_arma'])}")
    L.append(f"  ( calcule en {e['duree_ms']} ms )")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ile"); ap.add_argument("--graine", type=int, default=7)
    ap.add_argument("--echelle", type=float, default=20); ap.add_argument("--jours", type=int, default=0)
    ap.add_argument("--instantane"); ap.add_argument("--json")
    a = ap.parse_args()
    from monde import archipel as AR, tests as T
    if a.instantane:
        w = AR.charger(a.instantane)
    else:
        w = AR.creer_ile(a.ile, a.graine, a.echelle)
        if a.jours: T.jours(w, a.jours)
    e = etat_des_lieux(w)
    print(texte(e))
    if a.json:
        json.dump(e, open(a.json, "w"), indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
