"""cmo_anchor — orchestrateur d'ANCRAGE batch (hote Linux) <-> CMO (VM Windows), via dossier PARTAGE.
Pas la telemetrie 1/s (pilotage live) : ici on RESOUT des combats scriptes et on exporte l'ISSUE (attrition).
Objectif Phase B (critere Fable) : un scenario scripte tourne dans CMO et exporte ses issues SANS INTERVENTION,
10 fois de suite, ZERO run perdu.

Lecons du pont Arma, appliquees telles quelles :
  - COMPTEUR MONOTONE  : chaque run a un id k unique ; on reprend a max(result_*)+1 -> jamais rejoue, jamais perdu.
  - WATCHDOG ANTI-GEL  : on lit le heartbeat hb.json ; si t/wall n'avance plus > STALL_S -> run declare fige, requeue.
  - LOCK ANTI-ZOMBIE   : un seul orchestrateur par dossier (lock avec pid ; pid mort -> on vole, pid vivant -> refus).
Echanges (ecritures ATOMIQUES tmp->rename des DEUX cotes) :
  job_<k>.json   host->guest : {k,nb,nr,aw,seed}          (composition a resoudre)
  hb.json        guest->host : {t,wall,k,phase}           (battement, reecrit chaque tick Lua)
  result_<k>.json guest->host: {k,nb,nr,aw,seed,blue0,red0,blue_surv,red_surv,status}
"""
import os, json, glob, re, time, tempfile


def _atomic_write(path, obj):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None


class AnchorOrchestrator:
    STALL_S = 45.0          # heartbeat fige plus longtemps que ca -> run considere mort
    RUN_TIMEOUT_S = 900.0   # un combat CMO ne doit pas depasser ca en horloge murale
    MAX_RETRY = 3           # tentatives par composition avant abandon (et log explicite)
    POLL_S = 0.5

    def __init__(self, bridge_dir):
        self.dir = bridge_dir
        os.makedirs(self.dir, exist_ok=True)
        self._acquire_lock()

    # ---- lock anti-zombie ----
    def _acquire_lock(self):
        lp = os.path.join(self.dir, "orchestrator.lock")
        old = _read_json(lp)
        if old and self._pid_alive(old.get("pid", -1)):
            raise RuntimeError("orchestrateur DEJA actif (pid %s) sur %s -> refus (anti-zombie)"
                               % (old.get("pid"), self.dir))
        _atomic_write(lp, {"pid": os.getpid(), "host": os.uname().nodename})
        self._lock = lp

    @staticmethod
    def _pid_alive(pid):
        try:
            os.kill(int(pid), 0); return True
        except (OSError, ValueError):
            return False

    def release(self):
        try:
            os.remove(self._lock)
        except OSError:
            pass

    # ---- compteur monotone / reprise ----
    def _results(self):
        out = {}
        for f in glob.glob(os.path.join(self.dir, "result_*.json")):
            r = _read_json(f)
            if r and "k" in r:
                out[r["k"]] = r
        return out

    def _next_k(self):
        done = self._results()
        pend = [int(re.search(r"job_(\d+)\.json$", f).group(1))
                for f in glob.glob(os.path.join(self.dir, "job_*.json"))]
        return max([0] + list(done.keys()) + pend) + 1

    # ---- un run : emettre le job, surveiller le heartbeat, recuperer le result ----
    def _await_result(self, k):
        rp = os.path.join(self.dir, "result_%d.json" % k)
        hbp = os.path.join(self.dir, "hb.json")
        t0 = time.time()
        last_beat, last_change = None, time.time()
        while True:
            r = _read_json(rp)
            if r is not None:
                return r
            hb = _read_json(hbp)
            beat = None if hb is None else (hb.get("t"), hb.get("wall"))
            now = time.time()
            if beat != last_beat:
                last_beat, last_change = beat, now
            if now - last_change > self.STALL_S:
                return {"status": "STALLED", "k": k}      # gel detecte -> requeue
            if now - t0 > self.RUN_TIMEOUT_S:
                return {"status": "TIMEOUT", "k": k}
            time.sleep(self.POLL_S)

    def resolve(self, nb, nr, aw, seed):
        """Demande a CMO de resoudre UNE composition. Requeue sur gel/timeout. Renvoie le result ou None."""
        for attempt in range(1, self.MAX_RETRY + 1):
            k = self._next_k()
            _atomic_write(os.path.join(self.dir, "job_%d.json" % k),
                          {"k": k, "nb": nb, "nr": nr, "aw": aw, "seed": seed})
            r = self._await_result(k)
            if r.get("status") == "ok":
                return r
            print("  run k=%d (%dv%d aw%d s%d) -> %s ; tentative %d/%d"
                  % (k, nb, nr, aw, seed, r.get("status"), attempt, self.MAX_RETRY), flush=True)
        return None

    def run_batch(self, batch, out_path):
        """batch = liste de (nb,nr,aw,reps). Resout chaque composition x reps. ZERO perdu = 100% aboutis."""
        rows, lost = [], 0
        total = sum(reps for *_c, reps in batch)
        i = 0
        for nb, nr, aw, reps in batch:
            for rep in range(reps):
                i += 1
                r = self.resolve(nb, nr, aw, seed=1000 + rep)
                if r is None:
                    lost += 1
                    print("  [%d/%d] PERDU (%dv%d aw%d rep%d) apres %d tentatives"
                          % (i, total, nb, nr, aw, rep, self.MAX_RETRY), flush=True)
                    continue
                rows.append(r)
                print("  [%d/%d] %dv%d aw%d rep%d -> bleu %d/%d , rouge %d/%d"
                      % (i, total, nb, nr, aw, rep, r["blue_surv"], r["blue0"],
                         r["red_surv"], r["red0"]), flush=True)
        _atomic_write(out_path, {"rows": rows, "lost": lost, "requested": total})
        print("\n=== BATCH FINI : %d/%d aboutis, %d perdus -> %s ==="
              % (len(rows), total, lost, out_path), flush=True)
        return rows, lost


# DOE Phase C issu de l'audit Phase A : 99% du levier sur bleu=8+AWACS vs rouge aminci.
# On ancre la rangee decisive (8v8 = golden de re-verif, 8v6/8v4/8v2 = les 3 cellules extrapolees)
# + un temoin lointain (2v2 no-AWACS). N=10 par cellule -> distributions, jamais un point.
DOE_PHASE_C = [(8, 8, 1, 10), (8, 6, 1, 10), (8, 4, 1, 10), (8, 2, 1, 10), (2, 2, 0, 10)]


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/MONDE/assets/fab_inbox/cmo_bridge"
    orch = AnchorOrchestrator(d)
    try:
        orch.run_batch(DOE_PHASE_C, os.path.join(d, "anchor_results.json"))
    finally:
        orch.release()
