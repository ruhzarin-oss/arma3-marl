"""leviathan_substrate.py — SUBSTRAT ABSTRAIT de LEVIATHAN (incrément 1).

Une faction qui tient des secteurs avec une LOGISTIQUE FINIE — la rareté qui force l'organisation :
  - effectifs finis ; renforts depuis une CASERNE (un rythme ; STOPPE si la caserne est capturee) ;
  - MUNITIONS par secteur (s'epuisent sous attaque, ravitaillees depuis un DEPOT) ;
  - TEMPS DE TRAJET des reserves (geographie : un convoi met des ticks a arriver) ;
  - bases CAPTURABLES en CASCADE (perdre la caserne = plus de renforts ; perdre le depot = plus de muns).

Tick = pas de temps. Chaque tick est HORODATE (UTC ISO-8601) et ecrit dans un HISTORIQUE JSONL
pour voir l'EVOLUTION de la societe militaire dans le temps.

Allocateur = BASELINE reactif (envoie la reserve au secteur tenu le plus faible). C'est le baseline
a battre : l'incrément 2 remplacera cette heuristique par l'ALLOCATEUR APPRIS (la faction qui s'organise).
"""
import os, json, time, math, argparse
from datetime import datetime, timezone
import numpy as np

HIST = "/home/younes/arma3-marl/leviathan/history.jsonl"

# secteurs Altis : (nom, x, y, role)   role: "hq"=caserne(renforts), "depot"=ravito muns, ""=normal
SECTORS = [
    ("Kavala",  3600, 13200, ""),
    ("Pyrgos", 16800, 12600, ""),
    ("Sofia",  25700, 21300, "depot"),
    ("Agios",   9200, 21600, ""),
    ("AirHQ",  14600, 16900, "hq"),
]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dist(a, b):
    return math.hypot(SECTORS[a][1] - SECTORS[b][1], SECTORS[a][2] - SECTORS[b][2])


class Leviathan:
    def __init__(self, seed=0, hist=HIST, reinforce_rate=4.0, threat_rate=0.30, speed=4500.0):
        self.rng = np.random.default_rng(seed)
        self.K = len(SECTORS)
        self.hq = next(i for i, s in enumerate(SECTORS) if s[3] == "hq")
        self.depot = next(i for i, s in enumerate(SECTORS) if s[3] == "depot")
        self.garr = np.array([20, 16, 14, 16, 24], float)   # garnisons initiales
        self.supply = np.full(self.K, 100.0)                 # munitions 0-100
        self.owner = np.ones(self.K)                         # 1=tenu, 0=perdu
        self.reserve = 30.0                                  # reserve a la caserne
        self.reinforce_rate = reinforce_rate
        self.threat_rate = threat_rate
        self.speed = speed                                   # metres par tick (vitesse convoi)
        self.convoys = []                                    # {dest, troops, eta}
        self.tick = 0; self.hist = hist; self.log = []

    def step(self):
        self.tick += 1
        ev = []
        # 1) RENFORTS depuis la caserne (si tenue) -> reserve
        if self.owner[self.hq] > 0:
            self.reserve += self.reinforce_rate
        # 2) RAVITAILLEMENT depuis le depot (si tenu) -> secteurs tenus remontent en muns
        if self.owner[self.depot] > 0:
            m = self.owner > 0
            self.supply[m] = np.minimum(100.0, self.supply[m] + 5.0)
        # 3) MENACES : chaque secteur tenu peut subir une attaque ; peu de muns = plus de pertes
        for i in range(self.K):
            if self.owner[i] <= 0:
                continue
            if self.rng.random() < self.threat_rate:
                inten = self.rng.uniform(2, 7)
                loss = inten * (1.5 - self.supply[i] / 100.0)   # muns pleines -> x0.5 ; vides -> x1.5
                self.garr[i] -= loss
                self.supply[i] -= inten * 1.8
                ev.append({"type": "attaque", "secteur": SECTORS[i][0], "intensite": round(inten, 1), "pertes": round(loss, 1)})
        self.supply = np.clip(self.supply, 0, 100)
        # 4) CONVOIS : decrement eta, livraison a l'arrivee
        for c in self.convoys:
            c["eta"] -= 1
        for c in [c for c in self.convoys if c["eta"] <= 0]:
            if self.owner[c["dest"]] > 0:
                self.garr[c["dest"]] += c["troops"]
                ev.append({"type": "renfort_arrive", "secteur": SECTORS[c["dest"]][0], "troupes": round(c["troops"])})
            else:
                self.reserve += c["troops"]   # secteur deja perdu -> repli sur la reserve
        self.convoys = [c for c in self.convoys if c["eta"] > 0]
        # 5) SECTEURS TOMBES (cascade : si c'est la caserne/depot, la logistique s'effondre)
        for i in range(self.K):
            if self.owner[i] > 0 and self.garr[i] <= 0:
                self.owner[i] = 0; self.garr[i] = 0
                ev.append({"type": "SECTEUR_PERDU", "secteur": SECTORS[i][0], "role": SECTORS[i][3] or "normal"})
        # 6) ALLOCATEUR (baseline reactif) — a remplacer par l'allocateur APPRIS
        alloc = self._allocate_baseline()
        self._record(ev, alloc)
        return ev, alloc

    def _allocate_baseline(self):
        held = [i for i in range(self.K) if self.owner[i] > 0]
        if not held or self.reserve < 5:
            return None
        i = min(held, key=lambda k: self.garr[k])    # secteur tenu le plus faible
        if self.garr[i] >= 18:                        # tout va bien -> on garde la reserve
            return None
        send = min(self.reserve, 12.0); self.reserve -= send
        eta = max(1, math.ceil(dist(self.hq, i) / self.speed))
        self.convoys.append({"dest": i, "troops": send, "eta": eta})
        return {"vers": SECTORS[i][0], "troupes": round(send), "eta": eta}

    def _record(self, ev, alloc):
        rec = {
            "ts": now_iso(), "tick": self.tick,
            "secteurs_tenus": int(self.owner.sum()),
            "garnisons": {SECTORS[i][0]: round(float(self.garr[i]), 1) for i in range(self.K) if self.owner[i] > 0},
            "muns": {SECTORS[i][0]: round(float(self.supply[i])) for i in range(self.K) if self.owner[i] > 0},
            "reserve": round(float(self.reserve), 1),
            "convois": len(self.convoys),
            "renforts_actifs": bool(self.owner[self.hq] > 0),
            "depot_actif": bool(self.owner[self.depot] > 0),
            "evenements": ev, "allocation": alloc,
        }
        self.log.append(rec)
        with open(self.hist, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def alive(self):
        return self.owner.sum() >= 2 and (self.owner[self.hq] > 0 or self.reserve > 5 or self.convoys)


def main(ticks=40, seed=0, cadence=0.0, keep=False, threat=0.30, reinforce=4.0):
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    if not keep and os.path.exists(HIST):
        os.remove(HIST)
    lev = Leviathan(seed=seed, threat_rate=threat, reinforce_rate=reinforce)
    print("LEVIATHAN — substrat abstrait | %d secteurs | caserne=%s depot=%s" % (lev.K, SECTORS[lev.hq][0], SECTORS[lev.depot][0]))
    print("historique horodate -> %s\n" % HIST)
    for _ in range(ticks):
        ev, alloc = lev.step()
        flags = "".join("#" if lev.owner[i] > 0 else "." for i in range(lev.K))
        big = [e for e in ev if e["type"] in ("SECTEUR_PERDU", "renfort_arrive")]
        note = (" | " + "; ".join("%s:%s" % (e["type"], e.get("secteur", "")) for e in big)) if big else ""
        al = (" >alloc %s+%d(eta%d)" % (alloc["vers"], alloc["troupes"], alloc["eta"])) if alloc else ""
        print("t%03d [%s] tenus=%d reserve=%4.1f convois=%d%s%s" % (
            lev.tick, flags, int(lev.owner.sum()), lev.reserve, len(lev.convoys), al, note))
        if not lev.alive():
            print("\n>>> FACTION EFFONDREE au tick %d" % lev.tick); break
        if cadence > 0:
            time.sleep(cadence)
    print("\n[fin] tick %d | secteurs tenus %d/%d | reserve %.0f | historique = %d lignes horodatees"
          % (lev.tick, int(lev.owner.sum()), lev.K, lev.reserve, len(lev.log)))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ticks", type=int, default=40)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--cadence", type=float, default=0.0, help="secondes reelles entre ticks (mode live)")
    p.add_argument("--keep", action="store_true", help="ne pas effacer l'historique existant")
    p.add_argument("--threat", type=float, default=0.30, help="proba d'attaque par secteur par tick")
    p.add_argument("--reinforce", type=float, default=4.0, help="renforts par tick depuis la caserne")
    a = p.parse_args()
    main(ticks=a.ticks, seed=a.seed, cadence=a.cadence, keep=a.keep, threat=a.threat, reinforce=a.reinforce)
