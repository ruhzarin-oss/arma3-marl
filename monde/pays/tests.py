"""Toutes les portes du pays, ou celles de quelques domaines.   python -m monde.pays.tests [ domaine ... ]"""
import importlib, sys, time
from . import pays as P


def main(noms):
    noms = noms or [n for n, _, _ in P.DOMAINES]
    total = passees = 0
    for n in noms:
        try: m = importlib.import_module(f".tests_{P.MODULE[n]}", __package__)
        except ModuleNotFoundError as e:
            if f"tests_{P.MODULE[n]}" not in str(e): raise
            print(f"ABSENT  {n}"); continue
        for t in m.TESTS:
            t0 = time.perf_counter()
            try: r, msg = t()
            except Exception as e: r, msg = False, f"EXCEPTION {type(e).__name__} : {e}"
            total += 1; passees += bool(r)
            print(f"{'PASSE' if r else 'ECHOUE':7s} {n:17s} {t.__name__:36s} ({time.perf_counter() - t0:5.1f} s) {msg}", flush=True)
    print(f"{passees} / {total} portes du pays")
    return passees == total


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
