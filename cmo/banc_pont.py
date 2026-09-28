#!/usr/bin/env python3
"""banc_pont — le pont dans le VRAI CMO : la seule preuve. Un banc, pas le labo : il écrit un verdict et, s'il passe,
certifie le build de CMO ( cmo_labo refuse ensuite tout autre build, cf. garantie 9 ).

Prérequis : CMO ouvert sur un scénario où l'on a lancé, dans la console Lua,
    ScenEdit_RunScript('hmt_pont/installer.lua')
et le temps qui s'écoule ( x1 ).

CRITÈRES ÉCRITS D'AVANCE ( comme le banc pontmcp d'Arma ). Un seul raté : pas de certification.
  C1 100 canaris : 0 perte, médiane < 1,5 s, p99 < 3 s.
  C2 deux F-15C ( dbid 3500, loadout 16934 ) posés à l'ouest de Kéa, un par camp : état = 2, positions = 2 ; ordre
     « aller » ; 60 s plus tard l'avion a bougé de plus de 0,02° ; table rase prouvée ( 0 unité HMT ).
  C3 une erreur Lua au milieu d'une commande rend EchecLua, jamais un reçu « exécutée ».
  C4 un reçu de 3000 lignes arrive entier ( sinon : la taille où CMO coupe, dite ).
  C5 endurance : un canari toutes les 5 s pendant 10 min, 0 perte ( le limiteur de la 1.10 vise la console, pas les
     événements : c'est ici qu'on le vérifie ).

    .venv/bin/python cmo/banc_pont.py [--endurance-min 10]
"""
import json
import logging
import os
import statistics
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

KEA_OUEST = (37.55, 24.05)
CIBLE = (37.80, 24.50)
DOSSIER = os.path.join(CL.ETAT, "cmo_banc")


def c1_canaris(l, n=100):
    rtt, pertes = [], 0
    for _ in range(n):
        try:
            rtt.append(l.canari()["recu"]["rtt_ms"])
        except CL.ErreurLabo as e:
            pertes += 1
            logging.warning("canari perdu : %s", e)
    rtt.sort()
    med = statistics.median(rtt) if rtt else None
    p99 = rtt[min(len(rtt) - 1, int(0.99 * len(rtt)))] if rtt else None
    ok = pertes == 0 and med is not None and med < 1500 and p99 < 3000
    return ok, {"n": n, "pertes": pertes, "mediane_ms": med, "p99_ms": p99, "max_ms": rtt[-1] if rtt else None}


def c2_unites(l):
    d = {}
    l.nettoyer()
    for k, camp in ((1, "Stratis"), (2, "Malden")):
        d[f"pose_{k}"] = l.poser(camp, "air", 3500, k, KEA_OUEST[0] + k / 50, KEA_OUEST[1], 6000, 16934)
    d["etat"] = l.etat_camps()["camps"]
    p0 = l.positions()["vivants"]
    d["positions"] = sum(len(v) for v in p0.values())
    u0 = [u for u in p0["Stratis"] if u[0] == 1][0]
    l.aller(1, *CIBLE)
    time.sleep(60)
    u1 = [u for u in l.positions()["vivants"]["Stratis"] if u[0] == 1][0]
    d["deplacement_deg"] = round(abs(u1[1] - u0[1]) + abs(u1[2] - u0[2]), 5)
    d["nettoyer"] = {k: v for k, v in l.nettoyer().items() if k != "recu"}
    ok = (d["etat"]["Stratis"]["hmt_vivants"] == 1 and d["etat"]["Malden"]["hmt_vivants"] == 1
          and d["positions"] == 2 and d["deplacement_deg"] > 0.02 and d["nettoyer"]["apres"] == 0)
    return ok, d


def c3_erreur(l):
    try:
        l.lua("R('AVANT', {1}) error('erreur volontaire du banc') R('APRES', {2})", par_humain=True)
    except CL.EchecLua as e:
        return "erreur volontaire" in str(e), {"exception": str(e)[:200]}
    return False, {"exception": None}


def c4_gros_recu(l, n=3000):
    try:
        r = l.lua(f"for i = 1, {n} do R('X', {{i, i / 7}}) end", par_humain=True)
        return len(r["lignes"]) == n, {"lignes": len(r["lignes"])}
    except CL.Incomplet as e:
        return False, {"incomplet": str(e)[:200]}


def c5_endurance(l, minutes):
    fin, n, pertes, rtt = time.monotonic() + 60 * minutes, 0, 0, []
    while time.monotonic() < fin:
        n += 1
        try:
            rtt.append(l.canari()["recu"]["rtt_ms"])
        except CL.ErreurLabo as e:
            pertes += 1
            logging.warning("endurance : canari %d perdu : %s", n, e)
        time.sleep(5)
    return pertes == 0 and n > 0, {"minutes": minutes, "canaris": n, "pertes": pertes,
                                   "mediane_ms": statistics.median(rtt) if rtt else None}


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    minutes = float(sys.argv[sys.argv.index("--endurance-min") + 1]) if "--endurance-min" in sys.argv else 10.0
    os.makedirs(DOSSIER, exist_ok=True)
    verdict = {"debut": time.strftime("%Y-%m-%d %H:%M:%S"), "criteres": {}}
    sonde = CL.lire_inst(os.path.join(CL.SORTIE, "hmt_sonde.inst"))
    verdict["sonde"] = sonde.split("\n")[0] if sonde else None          # SONDE io dofile loadfile load os lecteur
    with CL.Labo(strict=False) as l:
        verdict["canari"] = {k: v for k, v in l.version.items() if k != "recu"}
        for nom, fn in (("C1_canaris", c1_canaris), ("C2_unites", c2_unites), ("C3_erreur", c3_erreur),
                        ("C4_gros_recu", c4_gros_recu), ("C5_endurance", lambda x: c5_endurance(x, minutes))):
            try:
                ok, d = fn(l)
            except Exception as e:
                ok, d = False, {"exception": f"{type(e).__name__}: {e}"[:300]}
            verdict["criteres"][nom] = {"passe": ok, **d}
            print(f"{'PASSE ' if ok else 'ÉCHOUE'} {nom} {json.dumps(d, ensure_ascii=False)}", flush=True)
            with open(os.path.join(DOSSIER, "en_cours.json"), "w") as g:
                json.dump(verdict, g, ensure_ascii=False, indent=1)
    verdict["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
    verdict["passe"] = all(c["passe"] for c in verdict["criteres"].values())
    chemin = os.path.join(DOSSIER, time.strftime("%Y%m%d_%H%M%S") + ".json")
    with open(chemin, "w") as g:
        json.dump(verdict, g, ensure_ascii=False, indent=1)
    if verdict["passe"]:
        CL.certifier(verdict["canari"]["build"], {"banc": chemin}, CL.ETAT)
        print(f"BANC PASSÉ : build {verdict['canari']['build']} certifié ( {chemin} )")
    else:
        print(f"BANC ÉCHOUÉ : rien n'est certifié ( {chemin} )")
    return 0 if verdict["passe"] else 1


if __name__ == "__main__":
    sys.exit(main())
