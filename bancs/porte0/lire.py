#!/usr/bin/env python3
"""porte0_lire — certifie une graine de la PORTE ZERO. Un seul controle manquant = REFUSE."""
import sys, json

CH = "PORTE0|"


def lire(path):
    eps, monte, fini, apres = [], None, None, 0
    with open(path, "r", errors="ignore") as f:
        for l in f:
            i = l.find(CH)
            if i < 0:
                continue
            t = l[i:].rstrip().rstrip('"')
            if fini is not None:
                apres += 1; continue
            c = t.split("|")
            if len(c) > 2 and c[1] == "OK":
                monte = t
            elif len(c) > 2 and c[1] == "FINI":
                fini = t
            elif len(c) >= 12 and c[1] == "EP":
                try:
                    eps.append(dict(rep=int(c[2]), intention=c[3], ratio=c[4], pris=int(c[5]),
                                    vivants=int(c[6]), effectif=int(c[7]), def_vivants=int(c[8]),
                                    tir_att=int(c[9]), tir_def=int(c[10]), dist_fin=float(c[11])))
                except ValueError:
                    pass
    return eps, monte, fini, apres


def main():
    rpt, graine = sys.argv[1], int(sys.argv[2])
    eps, monte, fini, apres = lire(rpt)
    P, det = {}, {"repetitions": len(eps), "lignes_apres_fini": apres}
    P["mission_montee"] = monte is not None
    P["episode_termine"] = fini is not None
    P["repetitions_lues"] = len(eps) >= 2

    if eps:
        n = len(eps)
        eng = sum(1 for e in eps if e["tir_att"] > 0 and e["tir_def"] > 0)
        det["engagement"] = round(eng / n, 3)
        P["engagement"] = eng == n            # chaque run : les DEUX camps ont tire
        det["intention"] = eps[0]["intention"]; det["ratio"] = eps[0]["ratio"]
        # MANIPULATION : l intention doit etre EXECUTEE, sinon un nul ne veut rien dire
        loin = [e for e in eps if e["dist_fin"] > 300]
        pres = [e for e in eps if 0 <= e["dist_fin"] < 220]
        if eps[0]["intention"] == "ROMPRE":
            det["manipulation"] = "%d/%d se sont ELOIGNES au-dela de 300 m" % (len(loin), n)
            P["manipulation"] = len(loin) >= 0.8 * n
        else:
            det["manipulation"] = "%d/%d se sont RAPPROCHES sous 220 m" % (len(pres), n)
            P["manipulation"] = len(pres) >= 0.8 * n
        det["prise"] = "%d/%d" % (sum(e["pris"] for e in eps), n)
        det["survivants_moyen"] = round(sum(e["vivants"] / max(e["effectif"], 1) for e in eps) / n, 3)
        det["dist_fin_moyenne"] = round(sum(e["dist_fin"] for e in eps if e["dist_fin"] >= 0)
                                        / max(sum(1 for e in eps if e["dist_fin"] >= 0), 1), 0)
        det["pertes_def_moyen"] = round(sum(e["def_vivants"] for e in eps) / n, 2)
    else:
        P["engagement"] = False; P["manipulation"] = False

    verdict = "ACCEPTE" if all(P.values()) else "REFUSE"
    print(json.dumps({"verdict": verdict, "graine": graine,
                      "controles": {k: ("REUSSI" if v else "ECHOUE") for k, v in P.items()},
                      "detail": det}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
