"""Controle positif de l ordre « aller » : quatre methodes de deplacement mises en concurrence dans Arma.
   1 agent + moveTo   2 agent + setDestination + moveTo   3 unite en groupe civil + doMove   4 groupe civil + move
On incarne trois corps par methode a Kavala, on leur ordonne un autre batiment, et on mesure la distance parcourue.
Un corps qui ne bouge pas de plus de 5 m en 90 s est un ordre mort.
   python -m monde.essai_aller --port 2350
Le cerveau du monde doit etre arrete : il tient le port."""
import argparse, math, time
from . import pont as PT

KAVALA = (3600, 13070)
METHODES = (1, 2, 3, 4)
PAR_METHODE = 3


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=2350)
    a = p.parse_args()
    pont = PT.Pont(a.port)
    print("en attente d Arma", flush=True)
    if not pont.attendre(300): print("Arma ne s est pas connecte"); return 2
    corps = {9000 + 10 * m + k: m for m in METHODES for k in range(PAR_METHODE)}
    pont.envoyer([["essai_creer", i, m, [KAVALA[0], KAVALA[1]], 300, 37 + 7 * (i % 100)] for i, m in corps.items()])

    def positions(duree):
        vus, t0 = {}, time.time()
        while time.time() - t0 < duree:
            for msg in pont.messages(0.5):
                if msg and msg[0] == "corps":
                    for c in msg[1]:
                        if c[0] in corps: vus[c[0]] = (c[1], c[2], c[4])
        return vus

    depart = positions(10)
    print(f"corps crees : {len(depart)} / {len(corps)}", flush=True)
    pont.envoyer([["essai_aller", i, m, [KAVALA[0], KAVALA[1]], 300, 500 + 11 * (i % 100)] for i, m in corps.items()])
    for etape in (30, 60, 90):
        vus = positions(30)
        for m in METHODES:
            ds = [math.dist(depart[i][:2], vus[i][:2]) for i, mm in corps.items() if mm == m and i in depart and i in vus]
            vits = [vus[i][2] for i, mm in corps.items() if mm == m and i in vus]
            print(f"{etape:3d} s methode {m} : parcouru {[round(d, 1) for d in ds]} m, vitesses {vits}", flush=True)
        print("---", flush=True)
    pont.envoyer([["diag", i] for i in corps])
    time.sleep(3)
    pont.envoyer([["desincarner", i] for i in corps])
    time.sleep(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
