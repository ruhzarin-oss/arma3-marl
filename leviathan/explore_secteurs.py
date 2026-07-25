#!/usr/bin/env python3
"""explore_secteurs.py — PHASE 0 : peupler la banque de rejeux avec de la VARIÉTÉ.

Le constat qui rend cette phase obligatoire : tous nos enregistrements approchent par l'OUEST.
Un apprentissage sur ces données ne ferait que graver notre propre erreur — on ne peut pas
apprendre la valeur d'un chemin qu'on n'a jamais emprunté.

Ici, le « plan » (l'intention longue) ne sert PAS de politique : il sert d'OUTIL D'EXPLORATION.
On force le secteur d'approche (sud, est, nord, ouest...) et on enregistre tout, gagné ou perdu.
Les défaites sont AUSSI précieuses : c'est le contraste qui donne sa valeur à la victoire.

Chaque partie est jouée dans des conditions VÉRIFIÉES (table rase, défense recomptée), sinon rejetée.

Usage : python explore_secteurs.py --theatre altis --par_secteur 6 --secteurs sud,est,nord,ouest
"""
import sys, os, time, json, math, argparse, subprocess, random
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

LEV = "/home/younes/arma3-marl"
PY = "/home/younes/arma3-marl/.venv/bin/python"
BANQUE = "/home/younes/arma3-marl/leviathan/banque"

ap = argparse.ArgumentParser()
ap.add_argument("--secteurs", default="sud,est,nord,ouest,sud-est,nord-ouest")
ap.add_argument("--par_secteur", type=int, default=6)
ap.add_argument("--n", type=int, default=8, help="défenseurs")
ap.add_argument("--nag", type=int, default=12)
ap.add_argument("--skill", type=float, default=0.5)
ap.add_argument("--steps", type=int, default=90)
ap.add_argument("--tries", type=int, default=3)
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
os.makedirs(BANQUE, exist_ok=True)


def bridge_do(fn):
    """le pont ne parle qu'à UN client : on ouvre, on fait, on ferme."""
    b = NativeBridge(port=TH.PORT)
    try:
        return fn(b)
    finally:
        b.close()


def wipe():
    def f(b):
        b.send('if (!isNil "HMT_WPILOT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; '
               'if (!isNil "HMT_EAST") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_EAST }; HMT_EAST=[]; '
               '{ if (!(isPlayer _x) && {side _x in [east, west, resistance]}) then { deleteVehicle _x } } forEach allUnits; '
               '{ deleteVehicle _x } forEach allDead;')
        time.sleep(3)
        r = b.query('(format ["W e=%1 w=%2", count (allUnits select {side _x==east}), '
                    'count (allUnits select {side _x==west && !(isPlayer _x)})]) call HMT_EMIT;',
                    r"W e=(\d+) w=(\d+)", want=1, timeout=12)
        return (int(r[-1].group(1)), int(r[-1].group(2))) if r else (-1, -1)
    return bridge_do(f)


def count_east():
    def f(b):
        r = b.query('(format ["E %1", count (allUnits select {side _x==east && alive _x})]) call HMT_EMIT;',
                    r"E (\d+)", want=1, timeout=12)
        return int(r[-1].group(1)) if r else -1
    return bridge_do(f)


def sh(cmd, t=400):
    return subprocess.run(cmd, shell=True, cwd=LEV + "/leviathan", capture_output=True, text=True, timeout=t).stdout


secteurs = [s.strip() for s in a.secteurs.split(",") if s.strip()]
print("=== PHASE 0 : peupler la banque | %d secteurs x %d parties = %d ===" % (
    len(secteurs), a.par_secteur, len(secteurs) * a.par_secteur), flush=True)
print("    (le plan sert d'OUTIL D'EXPLORATION ici, pas de politique)", flush=True)

bilan = []
for rep in range(1, a.par_secteur + 1):
    for sect in secteurs:
        ok = False
        for essai in range(1, a.tries + 1):
            e0, w0 = wipe()
            if (e0, w0) != (0, 0):
                print("  [%s r%d] table rase incomplète -> on refait" % (sect, rep), flush=True); continue
            sh("%s spawn_hard_east.py --theatre %s --n %d --skill %.2f" % (PY, TH.NAME, a.n, a.skill))
            time.sleep(2)
            if count_east() != a.n:
                print("  [%s r%d] défense incorrecte -> rejet (essai %d)" % (sect, rep, essai), flush=True); continue
            sh("%s intent_run.py setup --theatre %s --nag %d" % (PY, TH.NAME, a.nag))
            time.sleep(2)
            if count_east() != a.n:
                print("  [%s r%d] défense abîmée avant le run -> rejet" % (sect, rep), flush=True); continue
            out = "banque/ex_%s_r%d.json" % (sect.replace("-", ""), rep)
            log = sh("%s intent_run.py run --theatre %s --nag %d --steps %d --secteur %s --out %s"
                     % (PY, TH.NAME, a.nag, a.steps, sect, out))
            fin = [l for l in log.splitlines() if l.startswith("=== INTENTIONS |")]
            print("  [%-10s r%d] %s" % (sect, rep, (fin[-1][16:] if fin else "(pas de résumé)")), flush=True)
            try:
                m = json.load(open("%s/leviathan/%s" % (LEV, out)))["metrics"]
                bilan.append(dict(secteur=sect, rep=rep, pris=bool(m.get("took")),
                                  pertes=m.get("west_losses"), approche=m.get("min_fob_dist")))
            except Exception:
                pass
            ok = True
            break
        if not ok:
            print("  [%s r%d] ABANDONNÉ (conditions jamais réunies)" % (sect, rep), flush=True)

print("\n=== BANQUE CONSTITUÉE ===", flush=True)
print("%-12s %8s %10s %12s" % ("secteur", "parties", "prises", "pertes moy"), flush=True)
for s in secteurs:
    L = [b for b in bilan if b["secteur"] == s]
    if L:
        print("%-12s %8d %10s %12.1f" % (s, len(L), "%d/%d" % (sum(1 for x in L if x["pris"]), len(L)),
                                         sum(x["pertes"] for x in L) / len(L)), flush=True)
json.dump(bilan, open(BANQUE + "/bilan.json", "w"), indent=1)
print("\n-> %s (%d parties)" % (BANQUE, len(bilan)), flush=True)
print("LECTURE : c'est le CONTRASTE entre secteurs qui donnera sa valeur à chaque situation.", flush=True)
print("EXPLORE_DONE", flush=True)
