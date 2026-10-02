"""Porte du registre des objectifs reels ( HMT-192, etape 1a ). Criteres ecrits avant la mesure ( Plane ) :

Premier verdict ( 02/10, 21 h 49 ) : REFUSEE ( O1 et O3 ). Rejugement, criteres amendes AVANT la nouvelle mesure :
O1  sur les 5 cartes de pays, chaque site ( centrale, fonderie, base, port, depot ) a un objectif avec au moins un
    composant ; un aeroport sans objet de fonction aeroport ou hangar a moins de 1 500 m est une « piste sans corps
    destructible », listee et exclue.
O2  aucun objet de l inventaire n est composant de deux objectifs ; O2' : la grappe retrouvee a les « objets » et la
    « surface_m2 » de la carte du pays ; un composant d aeroport est a moins de 1 500 m du point.
O3  controle positif : les modeles caracteristiques du champ « source » de chaque site sont parmi ses composants.
O4  dependances ( Malden 1921, Stratis 1922, echelle 20 ) : chaque centrale, fonderie, base, depot et port resout ses
    dependances ; controle negatif : un faux objectif de type base sur un lieu sans armurerie est « sans dependance ».

python -m guerre.porte_objectifs"""
import json
import math
import os
import sys
import time

from monde import archipel as AR
from . import objectifs as OB

MONDES = (("Malden", 1923), ("Stratis", 1924))      # graines neuves du rejugement
SORTIE = "/mnt/data/hmt/arsenal/porte_objectifs.json"
RESOLUS = ("centrale", "fonderie", "base", "depot", "port")


def main():
    t0 = time.time(); res = {"cartes": {}}
    O1 = O2 = O3 = O4 = True
    for ile in OB.CARTES:
        objs = OB.objectifs_carte(ile)
        sans = [o["id"] for o in objs if not o["composants"] and o["type"] != "aeroport"]
        pistes = [o["id"] for o in objs if not o["composants"] and o["type"] == "aeroport"]
        vus = {}; double = []; hors = []; carte_fausse = []
        for o in objs:
            for c in o["composants"]:
                if c["i"] in vus: double.append((c["i"], vus[c["i"]], o["id"]))
                vus[c["i"]] = o["id"]
                if o["type"] == "aeroport" and math.dist((c["x"], c["y"]), o["pos"]) > OB.RAYON_AEROPORT_M:
                    hors.append((o["id"], c["i"]))
            if o["type"] != "aeroport":
                n, surf = len(o["composants"]), int(sum(c["sol_m2"] for c in o["composants"]))
                if (n, surf) != (o["carte"]["objets"], o["carte"]["surface_m2"]):
                    carte_fausse.append((o["id"], (n, surf), (o["carte"]["objets"], o["carte"]["surface_m2"])))
        manquants = {o["id"]: sorted(set(o["modeles_source"]) - set(o["modeles"])) for o in objs
                     if set(o["modeles_source"]) - set(o["modeles"])}
        controles = sum(1 for o in objs if o["modeles_source"])
        o1, o2, o3 = not sans, not double and not hors and not carte_fausse, not manquants
        O1 &= o1; O2 &= o2; O3 &= o3
        par_type = {}
        for o in objs: par_type[o["type"]] = par_type.get(o["type"], 0) + 1
        res["cartes"][ile] = {"objectifs": len(objs), "par_type": par_type, "sans_corps": sans, "pistes_sans_corps": pistes,
                              "doubles": double[:10], "carte_fausse": carte_fausse[:10],
                              "hors_rectangle": hors[:10], "O3_sites_controles": controles, "O3_manquants": manquants,
                              "composants": sum(len(o["composants"]) for o in objs),
                              "detail": [{"id": o["id"], "type": o["type"], "composants": len(o["composants"]),
                                          "poids_m2": round(o["poids_total"]), "modeles": list(o["modeles"].items())[:6]}
                                         for o in objs]}
        print(f"  {ile:8s} {len(objs):3d} objectifs {par_type} ; {res['cartes'][ile]['composants']} composants ; "
              f"O1 {'OUI' if o1 else 'NON ' + str(sans)} ( pistes sans corps {pistes} ) | "
              f"O2 {'OUI' if o2 else 'NON'} {double[:2]} {hors[:2]} {carte_fausse[:3]} | "
              f"O3 {'OUI' if o3 else 'NON'} ( {controles} sites controles ) {manquants}", flush=True)
    for ile, graine in MONDES:
        w = AR.creer_ile(ile, graine, 20)
        objs = OB.registre(ile, w)
        non = [(o["id"], o["type"]) for o in objs if o["type"] in RESOLUS and not o["dependances"]]
        faux = {"id": "Malden_V_Vigny" if ile == "Malden" else next(l for l, x in w.carte.lieux.items() if x.type == "village"),
                "type": "base"}
        neg = OB.dependances(w, faux)
        o4 = not non and not neg
        O4 &= o4
        res.setdefault("mondes", {})[ile] = {"graine": graine, "sans_dependance": non, "controle_negatif": neg,
                                              "objectifs": [{"id": o["id"], "type": o["type"], "dependances": o["dependances"],
                                                             "valeur": o["valeur"]} for o in objs]}
        print(f"  monde {ile} ( {graine} ) : O4 {'OUI' if o4 else 'NON'} sans dependance {non} ; "
              f"controle negatif {faux['id']} -> {neg or 'sans dependance'}", flush=True)
        for o in objs:
            print(f"     {o['id']:12s} {o['type']:9s} {o['dependances']} {o['valeur']}", flush=True)
    verdict = "FRANCHIE" if (O1 and O2 and O3 and O4) else "REFUSEE"
    res.update(verdict=verdict, O1=O1, O2=O2, O3=O3, O4=O4, duree_s=round(time.time() - t0))
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"O1 {O1} O2 {O2} O3 {O3} O4 {O4}")
    print(f"PORTE DU REGISTRE DES OBJECTIFS : {verdict} ( {res['duree_s']} s )")
    print("FIN_PORTE_OBJECTIFS", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
