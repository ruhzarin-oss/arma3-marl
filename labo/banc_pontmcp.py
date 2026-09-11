#!/usr/bin/env python3
"""banc_pontmcp — le premier banc du labo (verdict Fable du 11/09/2026). CRITÈRES ÉCRITS AVANT.

Joué par bancs/pontmcp/lancer.sh dans un job de la file, instance 9 : file3.sh tient déjà le verrou
j9, le banc ouvre donc le labo SANS le reprendre. Il ne prouve pas une tactique : il prouve que le
labo dit vrai, et qu'il sait dire « panne ».

CONTRÔLE POSITIF
  C1  100 canaris : chacun rend son reçu ; médiane < 1 s, p99 < 3 s, 0 perte (critère de PontTest).
  C2  poser_groupe(rouge, 8) -> etat : 8 rouges, tous à moins de 20 m du point demandé.
DOIT SAVOIR ÉCHOUER
  E1  SQF avec `//` -> REFUSÉ, et le compteur prouve que rien n'est parti.
  E2  une 2e session (autre processus) sur le pont -> refusée ; la 1re répond encore.
  E3  3 hommes posés « à la main » par SQF brut après les 8 -> etat dit 11, pas 8.
  E4  20 tirages : etat.unites == `count allUnits` lu par SQF brut, 20 fois sur 20.
  E5  serveur tué -> etat LÈVE PontMort, jamais une réponse. Joué en dernier.

CHIFFRE DU LABO CASSÉ, écrit d'avance : un seul reçu manquant sur 100, un p99 > 3 s, un écart
etat / count allUnits sur 1 tirage sur 20, ou un E5 qui rend quelque chose -> ÉCHOUE.
Sortie de Fable : dans ce cas le MCP est retiré et le diagnostic revient à un CLI sur ce module.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import arma_labo as al  # noqa: E402

PWSH = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
PIDF = f"{al.ETAT}/labo_arma.pid"
POINT = (8300.0, 10070.0)          # à côté de l'ancre d'EchellePol, terrain dégagé
DEUXIEME = ("import sys; sys.path.insert(0, %r); import arma_labo as al\n"
            "try:\n    al.Labo(prendre_verrou_file=False, **al.config_env()).ouvrir()\n"
            "except al.Occupe:\n    sys.exit(3)\nsys.exit(0)") % ICI


def tuer_le_serveur():
    if os.environ.get("HMT_LABO_TEST") == "1":            # le jouet : un fichier le rend muet
        open(os.environ["HMT_LABO_TUER"], "w").close()
        return
    with open(PIDF) as f:
        pid = int(f.read().strip())
    subprocess.run([PWSH, "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"], check=False)


def main():
    res = {"banc": "pontmcp", "criteres": {}, "mesures": {}}
    C, M = res["criteres"], res["mesures"]
    l = al.Labo(prendre_verrou_file=False, **al.config_env()).ouvrir()
    try:
        # C1 — cent allers-retours
        rtt, perdus = [], []
        for _ in range(100):
            try:
                rtt.append(l.canari()["recu"]["rtt_ms"])
            except al.ErreurLabo as e:
                perdus.append(f"{type(e).__name__}: {e}"[:160])
        rtt.sort()
        med = statistics.median(rtt) if rtt else None
        p99 = rtt[min(len(rtt), 99) - 1] if rtt else None
        M["C1"] = {"recus": len(rtt), "perdus": len(perdus), "mediane_ms": med, "p99_ms": p99,
                   "pannes": perdus[:5]}
        C["C1_canaris"] = not perdus and med is not None and med < 1000 and p99 < 3000

        # C2 — huit posés, huit comptés, tous là où on les a mis
        l.nettoyer()
        g = l.poser_groupe("rouge", 8, *POINT)
        e = l.etat(detail=50)
        dist = [((u["x"] - POINT[0]) ** 2 + (u["y"] - POINT[1]) ** 2) ** 0.5 for u in e["detail"]]
        M["C2"] = {"poses": g["poses"], "rouges": e["camps"]["rouge"]["vivants"],
                   "detail": len(dist), "distance_max_m": round(max(dist), 1) if dist else None}
        C["C2_huit_poses"] = (g["poses"] == 8 and e["camps"]["rouge"]["vivants"] == 8
                              and len(dist) == 8 and max(dist) < 20)

        # E1 — un commentaire est refusé, et rien ne part
        n0 = l.canari()["recu"]["n_cmd"]
        try:
            l.sqf("count allUnits // commentaire", par_humain=True)
            refuse = False
        except al.Refus:
            refuse = True
        n1 = l.canari()["recu"]["n_cmd"]
        M["E1"] = {"refuse": refuse, "n_avant": n0, "n_apres": n1}
        C["E1_commentaire_refuse"] = refuse and n1 == n0 + 1

        # E2 — un autre processus ne prend pas le pont
        rc = subprocess.run([sys.executable, "-c", DEUXIEME], timeout=60).returncode
        M["E2"] = {"code_deuxieme": rc}
        C["E2_deuxieme_session_refusee"] = rc == 3 and l.canari()["pont"] == "vivant"

        # E3 — etat compte le monde, pas sa mémoire
        l.sqf(f'private _g = createGroup [east, true]; for "_i" from 1 to 3 do '
              f'{{ _g createUnit ["O_Soldier_F", [{POINT[0]}, {POINT[1]}, 0], [], 5, "FORM"] }};',
              par_humain=True)
        time.sleep(1)
        M["E3"] = {"non_joueurs": l.etat()["non_joueurs"]}
        C["E3_etat_compte_le_monde"] = M["E3"]["non_joueurs"] == 11

        # E4 — deux lectures indépendantes du même nombre
        ecarts = []
        for _ in range(20):
            a = l.etat()["unites"]
            b = l.sqf("count allUnits", par_humain=True)["valeur"]
            if a != b:
                ecarts.append((a, b))
        M["E4"] = {"tirages": 20, "ecarts": len(ecarts), "exemples": ecarts[:3]}
        C["E4_etat_egal_count_allUnits"] = not ecarts
        l.nettoyer()

        # E5 — on tue le serveur : le labo doit LEVER, jamais répondre
        tuer_le_serveur()
        time.sleep(3)
        t0 = time.monotonic()
        try:
            r = l.etat()
            M["E5"] = {"a_rendu": str(r)[:200]}
            C["E5_serveur_tue_pont_mort"] = False
        except al.PontMort as ex:
            M["E5"] = {"leve_en_s": round(time.monotonic() - t0, 1), "message": str(ex)[:200]}
            C["E5_serveur_tue_pont_mort"] = True
        except al.ErreurLabo as ex:
            M["E5"] = {"autre_erreur": f"{type(ex).__name__}: {ex}"[:200]}
            C["E5_serveur_tue_pont_mort"] = False
    except al.ErreurLabo as ex:
        res["panne"] = f"{type(ex).__name__}: {ex}"
    finally:
        l.fermer()
    complet = len(C) == 7 and "panne" not in res
    res["verdict"] = "PASSE" if complet and all(C.values()) else "ECHOUE"
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res["verdict"] == "PASSE" else 1


if __name__ == "__main__":
    sys.exit(main())
