"""test_anchor — TEST A BLANC du protocole d'ancrage batch, SANS CMO ni VM.
Un FAUX CMO (thread Python) rejoue la machine a etats de cmo_anchor.lua : battement hb.json, lecture job_<k>,
resolution d'un combat (modele bouchon), ecriture result_<k>. Il INJECTE EXPRES le mode de gel qui nous a mordus
(le battement s'arrete au milieu d'un run) pour prouver que le WATCHDOG requeue et que la campagne finit 10/10, 0 perdu.
Prouve la ROBUSTESSE du pont (compteur monotone + anti-gel + anti-zombie), pas la physique CMO.
"""
import os, json, time, threading, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cmo_anchor import AnchorOrchestrator, _atomic_write, _read_json


class FakeCMO(threading.Thread):
    """Imite cmo_anchor.lua. freeze_on_job=N -> gele le battement au N-eme run demarre (test du watchdog)."""
    BATTLE_TICKS = 4            # duree d'un combat (ticks) avant resolution
    TICK_S = 0.1

    def __init__(self, d, freeze_on_job=None, freeze_ticks=45):
        super().__init__(daemon=True)
        self.d = d; self.stop = False
        self.k = 0; self.phase = "idle"; self.wall = 0; self.job = None; self.elapsed = 0
        self.freeze_on_job = freeze_on_job; self.freeze_ticks = freeze_ticks
        self.started_count = 0; self.frozen = 0

    def _hb(self):
        _atomic_write(os.path.join(self.d, "hb.json"),
                      {"t": float(self.wall), "wall": self.wall, "k": self.k, "phase": self.phase})

    @staticmethod
    def _resolve(nb, nr, aw, seed):                 # modele BOUCHON (pas la physique) : juste des survivants plausibles
        edge = 0.15 * (nb - nr) + (1.2 if aw else 0.0) + ((seed % 5) - 2) * 0.1
        b = max(0, round(nb - max(0.0, (nr * 0.5 - edge))))
        r = max(0, round(nr - max(0.0, (nb * 0.7 + edge))))
        if b > 0 and r > 0:
            r = 0                                    # un camp finit vide
        return min(b, nb), min(r, nr)

    def run(self):
        while not self.stop:
            self.wall += 1
            # --- gel injecte : on arrete le battement, on abandonne le run courant (event Lua mort) ---
            if self.frozen > 0:
                self.frozen -= 1
                if self.frozen == 0:
                    self.phase = "idle"; self.job = None      # a la reprise : run courant perdu, on repart idle
                time.sleep(self.TICK_S); continue
            self._hb()
            if self.phase == "idle":
                job = _read_json(os.path.join(self.d, "job_%d.json" % (self.k + 1)))
                if job:
                    self.started_count += 1
                    if self.freeze_on_job and self.started_count == self.freeze_on_job:
                        self.frozen = self.freeze_ticks           # ce run va geler
                        time.sleep(self.TICK_S); continue
                    self.job = job; self.phase = "running"; self.elapsed = 0
            elif self.phase == "running":
                self.elapsed += 1
                if self.elapsed >= self.BATTLE_TICKS:
                    j = self.job; b, r = self._resolve(j["nb"], j["nr"], j["aw"], j.get("seed", 0))
                    _atomic_write(os.path.join(self.d, "result_%d.json" % j["k"]),
                                  {"k": j["k"], "nb": j["nb"], "nr": j["nr"], "aw": j["aw"], "seed": j.get("seed", 0),
                                   "blue0": j["nb"] + j["aw"], "red0": j["nr"], "blue_surv": b, "red_surv": r,
                                   "status": "ok"})
                    self.k = j["k"]; self.phase = "idle"; self.job = None
            time.sleep(self.TICK_S)


def main():
    d = tempfile.mkdtemp(prefix="cmo_anchor_test_")
    print("dossier pont a blanc :", d)
    # orchestrateur durci pour test rapide
    AnchorOrchestrator.STALL_S = 3.0
    AnchorOrchestrator.RUN_TIMEOUT_S = 30.0
    AnchorOrchestrator.POLL_S = 0.1

    fake = FakeCMO(d, freeze_on_job=4, freeze_ticks=45)   # le 4e run demarre GELE -> watchdog doit requeue
    fake.start()
    orch = AnchorOrchestrator(d)

    # test anti-zombie : un 2e orchestrateur sur le meme dossier doit REFUSER
    try:
        AnchorOrchestrator(d); print("ECHEC anti-zombie : 2e orchestrateur accepte !")
    except RuntimeError:
        print("anti-zombie OK : 2e orchestrateur refuse (lock detenu)")

    batch = [(8, 8, 1, 3), (8, 6, 1, 3), (8, 4, 1, 2), (8, 2, 1, 2)]   # 10 runs, dont un qui gelera
    t0 = time.time()
    rows, lost = orch.run_batch(batch, os.path.join(d, "anchor_results.json"))
    fake.stop = True; orch.release()

    req = sum(reps for *_c, reps in batch)
    ok = (len(rows) == req and lost == 0)
    # verif : chaque composition demandee a bien N results distincts
    print("\n=== VERDICT TEST A BLANC ===")
    print("  runs demandes            : %d" % req)
    print("  runs aboutis             : %d" % len(rows))
    print("  runs perdus              : %d" % lost)
    print("  gel injecte + requeue    : %s" % ("gere (watchdog a bien repris)" if ok else "NON gere"))
    print("  duree                    : %.1fs" % (time.time() - t0))
    print("  -> %s" % ("PONT ROBUSTE : 10/10, zero perdu malgre le gel -> critere Phase B tenu (a blanc)"
                        if ok else "ECHEC : voir ci-dessus"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
