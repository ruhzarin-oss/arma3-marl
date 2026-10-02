#!/usr/bin/env python3
"""banc_charge — combien de vraies installations CMO tient-il en temps réel ? ( préalable du palier 9, mais le théâtre
Baltique réel est déjà de l'ordre de 2 000 à 3 000 éléments ). Importe et numérote TOUT le théâtre
( theatres/baltique_reel.INSTALLATIONS ), puis mesure pendant MESURE_S secondes :
  - la vitesse du scénario ( temps du jeu / temps réel, par le canari ) ;
  - l'aller-retour du pont ( rtt ) ;
puis fait table rase et chronomètre la suppression. Sorties : /mnt/data/hmt/etat/cmo_sondes/charge_<date>.json.

    .venv312/bin/python cmo/banc_charge.py [--mesure 180]
"""
import json
import os
import statistics
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import deployer                                           # noqa: E402
import bases_construites as BC                            # noqa: E402
from theatres import baltique_reel as T                   # noqa: E402

DEC_INST = 90_000_000                                     # installation i : 90 000 000 + i x 1 000 + 1 …


def mesurer(l, duree_s, res, etiquette):
    """Vitesse du scénario ( temps du jeu / temps réel ) et aller-retour du pont, toutes les 20 s pendant duree_s."""
    t0 = time.time()
    c0 = l.canari()
    prec = (c0["temps"], time.time())
    vs = []
    while time.time() - t0 < duree_s:
        time.sleep(20)
        c = l.canari()
        v = (c["temps"] - prec[0]) / max(1e-6, time.time() - prec[1])
        prec = (c["temps"], time.time())
        vs.append(v)
        res["mesures"].append({"etape": etiquette, "s": round(time.time() - t0), "vitesse": round(v, 3),
                               "rtt_ms": c["recu"]["rtt_ms"]})
        print(res["mesures"][-1], flush=True)
    return statistics.median(vs) if vs else None


def par_paliers(paliers, mesure_s=60):
    """Importe le théâtre par paquets de rôles ( ex. [ {'chasse', ...}, {'radar'}, {'sol-air'} ] ) et mesure la vitesse
    après chaque paquet : ce qui ralentit CMO se voit au paquet qui fait chuter la vitesse."""
    sortie = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("charge_paliers_%Y%m%d_%H%M%S.json"))
    res = {"debut": time.strftime("%Y-%m-%d %H:%M:%S"), "paliers": [], "mesures": []}
    BC.ecrire()
    deployer.deployer(camps=T.CAMPS, installations=T.FICHIERS)
    CL.recharger()
    with CL.Labo(camps=T.CAMPS, installations=T.FICHIERS) as l:
        l.nettoyer()
        l.hostiles(*T.CAMPS)
        res["paliers"].append({"roles": [], "elements": 0, "vitesse": mesurer(l, mesure_s, res, "vide")})
        total = 0
        for roles in paliers:
            n = 0
            for i, (f, camp, pays, role) in enumerate(T.INSTALLATIONS):
                if role not in roles:
                    continue
                try:
                    l.importer(camp, f)
                    time.sleep(1.5)
                    n += len(l.adopter(camp, DEC_INST + i * 1000 + 1)["elements"])
                except CL.ErreurLabo as e:
                    print(f"{f} : {e}", flush=True)
            total += n
            v = mesurer(l, mesure_s, res, "+".join(sorted(roles)))
            res["paliers"].append({"roles": sorted(roles), "elements": n, "total": total, "vitesse": v})
            print(f"PALIER {sorted(roles)} : +{n} éléments ( {total} au total ), vitesse {v}", flush=True)
            with open(sortie, "w") as g:
                json.dump(res, g, ensure_ascii=False, indent=1, default=str)
        l.nettoyer()
    with open(sortie, "w") as g:
        json.dump(res, g, ensure_ascii=False, indent=1, default=str)
    return res


def banc(mesure_s=180):
    sortie = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("charge_%Y%m%d_%H%M%S.json"))
    res = {"debut": time.strftime("%Y-%m-%d %H:%M:%S"), "installations": [], "mesures": []}

    def ecrire():
        with open(sortie, "w") as g:
            json.dump(res, g, ensure_ascii=False, indent=1, default=str)

    res["construites"] = BC.ecrire()
    deployer.deployer(camps=T.CAMPS, installations=T.FICHIERS)
    res["version"] = CL.recharger()
    with CL.Labo(camps=T.CAMPS, installations=T.FICHIERS) as l:
        res["nettoyer_avant"] = l.nettoyer()["avant"]
        l.hostiles(*T.CAMPS)
        t_imp = time.monotonic()
        total = 0
        for i, (f, camp, pays, role) in enumerate(T.INSTALLATIONS):
            x = {"fichier": f, "camp": camp, "pays": pays, "role": role}
            try:
                x["elements"] = l.importer(camp, f)["elements"]
                time.sleep(1.5)
                el = l.adopter(camp, DEC_INST + i * 1000 + 1)["elements"]
                x["numerotes"] = len(el)
                total += len(el)
            except CL.ErreurLabo as e:
                x["erreur"] = f"{type(e).__name__}: {e}"
            res["installations"].append(x)
            print(f"{i + 1:2d}/{len(T.INSTALLATIONS)} {f[:70]:70s} {x.get('numerotes', x.get('erreur'))}", flush=True)
            ecrire()
        res["import_s"] = round(time.monotonic() - t_imp, 1)
        res["elements"] = total
        res["etat_camps"] = l.etat_camps()["camps"]
        t0, c0 = time.time(), l.canari()
        prec = (c0["temps"], time.time())
        while time.time() - t0 < mesure_s:
            time.sleep(20)
            c = l.canari()
            v = (c["temps"] - prec[0]) / max(1e-6, time.time() - prec[1])
            prec = (c["temps"], time.time())
            res["mesures"].append({"s": round(time.time() - t0), "vitesse": round(v, 3), "rtt_ms": c["recu"]["rtt_ms"]})
            print(res["mesures"][-1], flush=True)
            ecrire()
        v = [m["vitesse"] for m in res["mesures"]]
        res["vitesse_mediane"] = statistics.median(v) if v else None
        t_n = time.monotonic()
        res["nettoyer_apres"] = l.nettoyer()["avant"]
        res["nettoyer_s"] = round(time.monotonic() - t_n, 1)
    res["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ecrire()
    print(f"{total} éléments, vitesse médiane {res['vitesse_mediane']}, écrit dans {sortie}")
    return res


if __name__ == "__main__":
    if "--paliers" in sys.argv:
        BASES = {"chasse", "transport", "aéronavale", "police du ciel balte", "hélicoptères", "aérodrome", "attaque"}
        par_paliers([BASES, {"radar"}, {"sol-air"}])
    else:
        banc(float(sys.argv[sys.argv.index("--mesure") + 1]) if "--mesure" in sys.argv else 180)
