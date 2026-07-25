#!/usr/bin/env python3
"""run_bench.py — LANCEUR DE BANC PROPRE : garantit que chaque run part des MÊMES conditions.

Le bug corrigé : on posait les nouveaux défenseurs alors que les attaquants du run PRÉCÉDENT
étaient encore vivants et tiraient -> ils en abattaient 2-3 avant le nettoyage.
Résultat : on demandait 8 défenseurs, le run en voyait 5. Les bras n'étaient pas comparables.

Séquence stricte, avec vérification à chaque étape :
   1. TABLE RASE   (toutes les unités non-joueur supprimées, on attend le calme)
   2. DÉFENSE      (spawn n défenseurs)  -> on VÉRIFIE le compte
   3. ATTAQUANTS   (spawn nag)           -> on RE-VÉRIFIE que la défense est intacte
   4. RUN          -> sinon on REJETTE et on recommence (jusqu'à --tries)

Usage : python run_bench.py --theatre altis --modes frontal,reckless --n 8 --nag 12 --reps 1
"""
import sys, time, json, argparse, subprocess, os
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

LEV = "/home/younes/arma3-marl/leviathan"
PY = "/home/younes/arma3-marl/.venv/bin/python"

ap = argparse.ArgumentParser()
ap.add_argument("--modes", default="frontal,supfront,envelop")
ap.add_argument("--n", type=int, default=8, help="défenseurs")
ap.add_argument("--nag", type=int, default=12, help="attaquants")
ap.add_argument("--skill", type=float, default=0.5)
ap.add_argument("--steps", type=int, default=45)
ap.add_argument("--reps", type=int, default=1)
ap.add_argument("--tries", type=int, default=3, help="tentatives si les conditions ne sont pas réunies")
ap.add_argument("--tag", default="bench")
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)

# IMPORTANT : le pont Arma ne parle qu'à UN client à la fois. On ouvre la ligne, on l'utilise,
# on la FERME — sinon les scripts appelés ensuite se connectent mais restent muets (bug du 25/07).


def wipe():
    """TABLE RASE : supprime toute unité non-joueur, puis attend le calme."""
    b = NativeBridge(port=TH.PORT)
    try:
        b.send('if (!isNil "HMT_WPILOT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; '
               'if (!isNil "HMT_EAST") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_EAST }; HMT_EAST=[]; '
               '{ if (!(isPlayer _x) && {side _x in [east, west, resistance]}) then { deleteVehicle _x } } forEach allUnits; '
               '{ deleteVehicle _x } forEach allDead;')
        time.sleep(3)
        r = b.query('(format ["WIPE e=%1 w=%2", count (allUnits select {side _x==east}), '
                    'count (allUnits select {side _x==west && !(isPlayer _x)})]) call HMT_EMIT;',
                    r"WIPE e=(\d+) w=(\d+)", want=1, timeout=12)
        return (int(r[-1].group(1)), int(r[-1].group(2))) if r else (-1, -1)
    finally:
        b.close()


def count_east():
    b = NativeBridge(port=TH.PORT)
    try:
        r = b.query('(format ["EC %1", count (allUnits select {side _x==east && alive _x})]) call HMT_EMIT;',
                    r"EC (\d+)", want=1, timeout=12)
        return int(r[-1].group(1)) if r else -1
    finally:
        b.close()


def sh(cmd):
    return subprocess.run(cmd, shell=True, cwd=LEV, capture_output=True, text=True, timeout=300).stdout.strip()


print("=== BANC PROPRE sur %s | objectif %s | %d attaquants vs %d défenseurs (skill %.1f) ===" % (
    TH.WORLD, TH.fob_str, a.nag, a.n, a.skill), flush=True)

results = []
for rep in range(1, a.reps + 1):
    for mode in [m.strip() for m in a.modes.split(",") if m.strip()]:
        ok = False
        for attempt in range(1, a.tries + 1):
            e0, w0 = wipe()
            if e0 != 0 or w0 != 0:
                print("  [%s r%d] table rase incomplète (e=%d w=%d), on recommence" % (mode, rep, e0, w0), flush=True)
                continue
            sh("%s spawn_hard_east.py --theatre %s --n %d --skill %.2f" % (PY, TH.NAME, a.n, a.skill))
            time.sleep(2)
            ec1 = count_east()
            if ec1 != a.n:
                print("  [%s r%d] défense incorrecte au spawn : %d/%d -> rejet (essai %d)" % (mode, rep, ec1, a.n, attempt), flush=True)
                continue
            sh("%s envelop_arma.py setup --theatre %s --nag %d" % (PY, TH.NAME, a.nag))
            time.sleep(2)
            ec2 = count_east()
            if ec2 != a.n:
                print("  [%s r%d] défense abîmée avant le run : %d/%d -> rejet (essai %d)" % (mode, rep, ec2, a.n, attempt), flush=True)
                continue
            out = "%s_%s_n%d_r%d.json" % (a.tag, mode, a.n, rep)
            print("  [%s r%d] conditions OK (défense %d/%d) -> run" % (mode, rep, ec2, a.n), flush=True)
            log = sh("%s envelop_arma.py run --theatre %s --mode %s --nag %d --steps %d --out %s"
                     % (PY, TH.NAME, mode, a.nag, a.steps, out))
            line = [l for l in log.splitlines() if l.startswith("===")]
            print("      " + (line[-1] if line else "(pas de résumé)"), flush=True)
            try:
                m = json.load(open(os.path.join(LEV, out)))["metrics"]
                m["mode"] = mode; m["rep"] = rep; m["east_verified"] = ec2
                results.append(m)
            except Exception as ex:
                print("      (métriques illisibles : %s)" % ex, flush=True)
            ok = True
            break
        if not ok:
            print("  [%s r%d] ABANDONNÉ après %d essais — conditions jamais réunies" % (mode, rep, a.tries), flush=True)

print("\n=== BILAN (conditions vérifiées identiques) ===", flush=True)
print("%-10s %4s %8s %10s %8s %10s" % ("bras", "rep", "défense", "pris", "pertes", "approche"), flush=True)
for m in results:
    print("%-10s %4d %8d %10s %8s %10s m" % (
        m["mode"], m["rep"], m["east_verified"],
        ("tick %s" % m["took_tick"]) if m.get("took") else "non",
        "%s/%s" % (m.get("west_losses"), m.get("nag")), m.get("min_fob_dist")), flush=True)
json.dump(results, open(os.path.join(LEV, "%s_summary.json" % a.tag), "w"), indent=1)
print("\n-> %s/%s_summary.json" % (LEV, a.tag), flush=True)
print("BENCH_DONE", flush=True)
