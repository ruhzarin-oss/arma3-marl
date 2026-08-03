#!/usr/bin/env python3
"""sonde_tau_volume — LE SURSIS S'ALLONGE-T-IL SOUS LE VOLUME DE FEU ?

Criteres figes AVANT : leviathan/CRITERES_TAU_VOLUME.md (empreinte 117b634298093c5c)

Un defenseur oriente NORD, attaque DANS LE DOS. Deux conditions, une seule difference :
un tireur, ou quatre. On chronometre le sursis — le delai entre le premier coup recu et
le premier coup rendu.

C'est la jonction entre l'arc et la suppression. Si arroser quelqu'un RETARDE le moment ou
il vous trouve, la suppression a deja un mecanisme mesure cote defenseur.

Montages d'invulnerabilite : ceux qui ont ete PROUVES hier.
  defenseur  allowDamage false      (le plafond HandleDamage min(x, 0,55) NE PROTEGE PAS)
  attaquants HandleDamage -> 0      (survivent 90 s, et le compteur d'impacts marche)
  jamais de setVehicleAmmo periodique : il ETEINT le tir.
"""
import sys
import time
import json
import math
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"

ap = argparse.ArgumentParser()
ap.add_argument("--reps", type=int, default=6)
ap.add_argument("--duree", type=int, default=60)
ap.add_argument("--dist", type=float, default=60.0)
ap.add_argument("--out", default="tau_volume.json")
a = ap.parse_args()

CEL = json.load(open(LEV + "/cellules_altis.json"))["serie"]
NC = min(len(CEL), 8)
CEL = CEL[:NC]
# 4 cellules par repetition : 2 en condition UN, 2 en condition QUATRE
COND = [1, 4, 1, 4]


def fermer(b):
    try:
        b.close()
    except Exception:
        pass


def poser(b, rep):
    plan = []
    for i, n in enumerate(COND):
        cx, cy, _h = CEL[(i + rep) % NC]
        plan.append((n, cx, cy))

    c = ["if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; "
         "HMT_S = []; HMT_DEF = []; HMT_TIR = []; "
         "HMT_TATT = []; HMT_TDEF = []; HMT_FDEF = []; HMT_FATT = []; HMT_IMP = []; HMT_LT = []; HMT_KN = []; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    for i, (n, cx, cy) in enumerate(plan):
        K = str(i)
        c.append(
            "HMT_TATT pushBack -1; HMT_TDEF pushBack -1; HMT_FDEF pushBack 0; HMT_FATT pushBack 0; "
            "HMT_IMP pushBack 0; HMT_LT pushBack 0; HMT_KN pushBack 0; "
            "private _gd = createGroup east; "
            "private _d = _gd createUnit [" + Q + "O_Soldier_F" + Q + ", [" + str(cx) + "," + str(cy) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            "_d setPosATL [" + str(cx) + "," + str(cy) + ",0]; _d setDir 0; _d setSkill 0.5; "
            "_d setUnitPos " + Q + "UP" + Q + "; _d setBehaviour " + Q + "COMBAT" + Q + "; "
            "_d setCombatMode " + Q + "RED" + Q + "; _d disableAI " + Q + "PATH" + Q + "; "
            "_d enableSimulation true; _d enableDynamicSimulation false; "
            "_d allowDamage false; "
            "_d setVariable [" + Q + "hmt_k" + Q + ", " + K + "]; "
            "_d addEventHandler [" + Q + "Fired" + Q + ", { "
            "  private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
            "  if (_k >= 0) then { HMT_FDEF set [_k, (HMT_FDEF select _k) + 1]; "
            "    if ((HMT_TDEF select _k) < 0) then { HMT_TDEF set [_k, diag_tickTime] }; }; }]; "
            "HMT_S pushBack _d; HMT_DEF pushBack _d; HMT_TIR pushBack []; ")
        # les tireurs, dans le DOS du defenseur (180 deg = plein sud), etales
        for j in range(n):
            lat = (j - (n - 1) / 2.0) * 8.0
            ax = cx + lat
            ay = cy - a.dist
            c.append(
                "private _ga = createGroup west; "
                "private _at = _ga createUnit [" + Q + "B_Soldier_F" + Q + ", "
                "[" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
                "_at setPosATL [" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0]; _at setDir 0; "
                "_at setSkill 0.6; _at setUnitPos " + Q + "UP" + Q + "; "
                "_at setBehaviour " + Q + "COMBAT" + Q + "; _at setCombatMode " + Q + "RED" + Q + "; "
                "_at disableAI " + Q + "PATH" + Q + "; _at disableAI " + Q + "COVER" + Q + "; "
                "_at disableAI " + Q + "SUPPRESSION" + Q + "; _at disableAI " + Q + "AUTOCOMBAT" + Q + "; "
                "_at enableSimulation true; _at enableDynamicSimulation false; "
                "_at setVariable [" + Q + "hmt_k" + Q + ", " + K + "]; "
                "_at addEventHandler [" + Q + "Fired" + Q + ", { "
                "  private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
                "  if (_k >= 0) then { HMT_FATT set [_k, (HMT_FATT select _k) + 1]; "
                "    if ((HMT_TATT select _k) < 0) then { HMT_TATT set [_k, diag_tickTime] }; }; }]; "
                "_at addEventHandler [" + Q + "HandleDamage" + Q + ", { "
                "  private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
                "  private _src = _this select 3; "
                "  if (_k >= 0 && {!isNull _src} && {_src isEqualTo (HMT_DEF select _k)}) then { "     # FILTRE PAR SOURCE
                "    private _t = diag_tickTime; "
                "    if (_t - (HMT_LT select _k) > 0.05) then { "                                       # DEDUP PAR TICK
                "      HMT_LT set [_k, _t]; HMT_IMP set [_k, (HMT_IMP select _k) + 1] }; }; "
                "  0 }]; "
                "(HMT_TIR select " + K + ") pushBack _at; HMT_S pushBack _at; ")
    c.append("(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_DEF]) call HMT_EMIT;")
    return b.query("".join(c), r"PRET (\d+)", want=1, timeout=120), plan


def feu(b):
    b.send("{ private _k = _forEachIndex; private _d = HMT_DEF select _k; "
           "  { if (alive _x && alive _d) then { _x reveal [_d, 4]; _x doTarget _d; _x doFire _d; } } forEach _x; "
           "} forEach HMT_TIR;", wait=False)


def lire(b):
    q = ("private _o = " + Q + Q + "; { private _k = _forEachIndex; "
         "  private _kn = 0; { private _v = _x knowsAbout (HMT_DEF select _k); if (_v > _kn) then {_kn = _v} } forEach (HMT_TIR select _k); "
         "  _o = _o + format [" + Q + P + "1/" + P + "2/" + P + "3/" + P + "4/" + P + "5;" + Q + ", "
         "    HMT_FATT select _k, HMT_FDEF select _k, HMT_IMP select _k, "
         "    round ((HMT_TATT select _k) * 100), round ((HMT_TDEF select _k) * 100)]; "
         "} forEach HMT_DEF; (format [" + Q + "V " + P + "1" + Q + ", _o]) call HMT_EMIT;")
    r = b.query(q, r"V (\S+)", want=1, timeout=35)
    if not r:
        return None
    out = []
    for it in r[-1].group(1).strip(";").split(";"):
        p = it.split("/")
        if len(p) != 5:
            continue
        fa, fd, im, ta, td = (int(v) for v in p)
        out.append({"tirs_att": fa, "tirs_def": fd, "impacts": im,
                    "t_att": ta / 100.0, "t_def": td / 100.0})
    return out


def med(v):
    v = sorted(v)
    n = len(v)
    return float("nan") if not n else (v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2]))


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    print("=== LE SURSIS SOUS VOLUME DE FEU ===", flush=True)
    print("    criteres 117b634298093c5c | dos (180 deg) | %d reps x 4 cellules | %d s"
          % (a.reps, a.duree), flush=True)
    if not b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=25):
        print("  pont MUET")
        fermer(b)
        return 2
    b.send("setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange;", wait=False)
    time.sleep(2)

    brut = []
    try:
        for rep in range(a.reps):
            r, plan = poser(b, rep)
            if not r:
                print("  rep %d : mise en place SANS REPONSE — on passe" % (rep + 1), flush=True)
                continue
            print("", flush=True)
            print("  rep %d/%d  %s" % (rep + 1, a.reps,
                  "  ".join("%dtir@%d,%d" % (n, cx, cy) for n, cx, cy in plan)), flush=True)
            time.sleep(1.5)
            t = 0
            feu(b)
            while t < a.duree:
                time.sleep(2)
                t += 2
                feu(b)
                if t % 20 == 0:
                    v = lire(b)
                    if v:
                        print("     +%2ds  %s" % (t, "  ".join(
                            "%dt:%da/%dd" % (plan[i][0], c["tirs_att"], c["tirs_def"])
                            for i, c in enumerate(v))), flush=True)
            v = lire(b)
            b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S; HMT_S = []; "
                   "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
            if v:
                for i, c in enumerate(v):
                    c["cond"] = plan[i][0]
                    c["rep"] = rep
                    c["cellule"] = [plan[i][1], plan[i][2]]
                    brut.append(c)
            json.dump({"brut": brut}, open(LEV + "/" + a.out, "w"), indent=1)
            time.sleep(2)
    finally:
        try:
            b.send("if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S };", wait=False)
        except Exception:
            pass
        fermer(b)

    # ---------------- depouillement : origine COMMUNE a la repetition
    reps = {}
    for c in brut:
        reps.setdefault(c["rep"], []).append(c)
    par = {1: [], 4: []}
    inertes = 0
    for rep, cells in reps.items():
        ts = [c["t_att"] for c in cells if c["t_att"] > 0] + [c["t_def"] for c in cells if c["t_def"] > 0]
        if not ts:
            inertes += len(cells)
            continue
        t0 = min(ts)
        for c in cells:
            if c["tirs_att"] == 0 and c["tirs_def"] == 0:
                inertes += 1
                continue
            c["tau"] = (c["t_def"] - t0) if c["t_def"] > 0 else float(a.duree)
            c["riposte"] = 1 if c["t_def"] > 0 else 0
            par[c["cond"]].append(c)

    print("", flush=True)
    print("=== RESULTAT — %d cellules retenues, %d inertes ==="
          % (len(par[1]) + len(par[4]), inertes), flush=True)
    print("  %-10s %5s %10s %10s %11s %10s" % ("condition", "n", "tau median", "riposte", "impacts", "tirs_def"), flush=True)
    res = {}
    for n in (1, 4):
        v = par[n]
        if not v:
            print("  %-10s %5d   (aucune donnee)" % ("%d tireur(s)" % n, 0), flush=True)
            res[n] = None
            continue
        res[n] = {"n": len(v), "tau": med([c["tau"] for c in v]),
                  "riposte": sum(c["riposte"] for c in v),
                  "impacts": sum(c["impacts"] for c in v) / float(len(v)),
                  "tirs_def": sum(c["tirs_def"] for c in v) / float(len(v)),
                  "taus": [c["tau"] for c in v]}
        r = res[n]
        print("  %-10s %5d %10.1f %7d/%-3d %11.1f %10.1f"
              % ("%d tireur(s)" % n, r["n"], r["tau"], r["riposte"], r["n"], r["impacts"], r["tirs_def"]), flush=True)

    print("", flush=True)
    print("=== VERDICT (seuils figes CRITERES_TAU_VOLUME) ===", flush=True)
    verdict = "indetermine"
    if res.get(1) and res.get(4):
        can1 = res[1]["riposte"] >= 6
        can4 = res[4]["riposte"] >= 6
        print("  CANARI : %d/%d ripostes a 1 tireur, %d/%d a 4 tireurs -> %s"
              % (res[1]["riposte"], res[1]["n"], res[4]["riposte"], res[4]["n"],
                 "OK" if (can1 and can4) else "ECHEC, ON NE COMPARE RIEN"), flush=True)
        if can1 and can4:
            d = res[4]["tau"] - res[1]["tau"]
            print("  tau(4) - tau(1) = %+.1f s" % d, flush=True)
            if d >= 2.0:
                verdict = "le volume PROLONGE le sursis"
                print("  -> LE VOLUME PROLONGE LE SURSIS. La suppression a un mecanisme MESURE", flush=True)
                print("     cote defenseur : arroser, c'est retarder le moment ou il vous trouve.", flush=True)
            elif abs(d) < 1.0:
                verdict = "le volume ne change rien"
                print("  -> LE VOLUME NE CHANGE RIEN. Arc et suppression sont independants ;", flush=True)
                print("     il faudra mesurer la suppression pour elle-meme.", flush=True)
            elif d <= -2.0:
                verdict = "le volume RACCOURCIT le sursis"
                print("  -> LE VOLUME RACCOURCIT LE SURSIS : plus on tire, plus vite on est trouve.", flush=True)
            else:
                verdict = "non concluant"
                print("  -> NON CONCLUANT (entre 1 et 2 s). Il faut plus de repetitions.", flush=True)
        else:
            verdict = "canari en echec"
    json.dump({"criteres": "CRITERES_TAU_VOLUME.md", "duree_s": a.duree, "dist": a.dist,
               "brut": brut, "par_condition": {str(k): v for k, v in res.items()},
               "verdict": verdict},
              open(LEV + "/" + a.out, "w"), indent=1)
    print("-> %s/%s" % (LEV, a.out), flush=True)
    print("TAUVOL_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
