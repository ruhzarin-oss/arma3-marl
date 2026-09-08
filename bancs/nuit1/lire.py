#!/usr/bin/env python3
"""nuit1_lire — extrait une graine NUIT 1 d'un RPT Arma et la CERTIFIE.

Il ne convertit pas : il REFUSE. Chaque controle est rendu REUSSI/ECHOUE, et un seul
manquant rend la graine REFUSEE. « COMPLET n'est pas valide » — Fable, 08/09.

Les trois controles, seuils PRE-INSCRITS :
  ENGAGEMENT    chaque camp a tire dans >= 95 % des episodes
  MANIPULATION  azimut median des debordants au premier coup recu :
                C >= 60 deg dans >= 80 % des episodes C
                B <= 20 deg dans >= 80 % des episodes B
  COUVERTURE    la manipulation n est rendue que si >= 50 % des episodes ont un azimut
"""
import sys, json, re, os

CH = "NUIT1|"
SEUIL_ENGAGEMENT = 0.95
SEUIL_AZ_C, SEUIL_AZ_B = 60.0, 20.0
SEUIL_PART = 0.80
SEUIL_COUVERTURE = 0.50


def lire(path):
    """Les lignes NUIT1, et on S ARRETE a FINI. Ce qui suit n appartient a rien."""
    eps, monte, fini, apres = [], None, None, 0
    with open(path, "r", errors="ignore") as f:
        for l in f:
            i = l.find(CH)
            if i < 0:
                continue
            t = l[i:].rstrip().rstrip('"')
            if fini is not None:
                apres += 1
                continue
            c = t.split("|")
            if len(c) > 2 and c[1] == "OK":
                monte = t
            elif len(c) > 2 and c[1] == "FINI":
                fini = t
            elif len(c) >= 11 and c[1] == "EP":
                try:
                    eps.append(dict(idx=int(c[2]), cond=c[3], pris=int(c[4]),
                                    att=int(c[5]), deff=int(c[6]), tir_att=int(c[7]),
                                    tir_def=int(c[8]), azimut=float(c[9]),
                                    n_azimut=int(c[10]), duree=int(c[11])))
                except ValueError:
                    pass
    return eps, monte, fini, apres


def main():
    rpt, graine = sys.argv[1], int(sys.argv[2])
    eps, monte, fini, apres = lire(rpt)
    P, det = {}, {}

    P["mission_montee"] = monte is not None
    P["episode_termine"] = fini is not None
    P["episodes_lus"] = len(eps) > 0
    det["episodes"] = len(eps)
    det["lignes_apres_fini"] = apres

    if eps:
        n = len(eps)
        eng = sum(1 for e in eps if e["tir_att"] > 0 and e["tir_def"] > 0)
        det["engagement"] = round(eng / n, 3)
        P["engagement"] = (eng / n) >= SEUIL_ENGAGEMENT

        avec = [e for e in eps if e["n_azimut"] > 0 and e["azimut"] >= 0]
        det["couverture_azimut"] = round(len(avec) / n, 3)
        P["couverture_azimut"] = (len(avec) / n) >= SEUIL_COUVERTURE

        for cond, seuil, sens in (("C", SEUIL_AZ_C, "sup"), ("B", SEUIL_AZ_B, "inf")):
            s = [e for e in avec if e["cond"] == cond]
            if s:
                ok = sum(1 for e in s if (e["azimut"] >= seuil if sens == "sup" else e["azimut"] <= seuil))
                det["manipulation_%s" % cond] = round(ok / len(s), 3)
                det["azimut_median_%s" % cond] = round(
                    sorted(e["azimut"] for e in s)[len(s) // 2], 1)
                P["manipulation_%s" % cond] = (ok / len(s)) >= SEUIL_PART
            else:
                det["manipulation_%s" % cond] = None
                P["manipulation_%s" % cond] = False

        for cond in ("B", "C"):
            s = [e for e in eps if e["cond"] == cond]
            if s:
                det["prise_%s" % cond] = "%d/%d" % (sum(e["pris"] for e in s), len(s))
                det["pertes_att_%s" % cond] = round(sum(8 - e["att"] for e in s) / len(s), 2)
                det["pertes_def_%s" % cond] = round(sum(4 - e["deff"] for e in s) / len(s), 2)
        det["abba"] = "".join(e["cond"] for e in sorted(eps, key=lambda e: e["idx"]))[:24]
    else:
        for k in ("engagement", "couverture_azimut", "manipulation_B", "manipulation_C"):
            P[k] = False

    verdict = "ACCEPTE" if all(P.values()) else "REFUSE"
    print(json.dumps({"verdict": verdict, "graine": graine,
                      "controles": {k: ("REUSSI" if v else "ECHOUE") for k, v in P.items()},
                      "detail": det}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
