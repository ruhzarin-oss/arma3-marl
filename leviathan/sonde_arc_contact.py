#!/usr/bin/env python3
"""sonde_arc_contact — COMBIEN DE TEMPS VIT L'ANGLE MORT QUAND ON TIRE DEDANS ?

Critères figés AVANT le run : leviathan/CRITERES_ARC_CONTACT.md (empreinte 82f3dad52683dd8f).

La sonde précédente a mesuré un ÉTAT avec un attaquant PASSIF, et a posé trois de ses cinq
angles EN MER (−22, −118, −146 m). Ses zéros étaient de la noyade. Elle est annulée.

Ici on mesure une DURÉE, avec un attaquant qui OUVRE LE FEU :
    t_riposte(θ) = premier tir du défenseur − premier tir de l'attaquant
    t_direction(θ) = instant où le défenseur a tourné à moins de 25° de l'attaquant

Corrections appliquées (les deux, pas l'une ou l'autre) :
  - filtre par SOURCE   : un impact ne compte que si (_this select 3) == le défenseur de CETTE cellule
  - déduplication par TICK : HandleDamage est appelé ~1,9× par balle → 0,05 s de garde
  - cellules espacées de ≥ 700 m ET vérifiées TERRE, plates, sans bâti (cellules_altis.json)

Invulnérabilité, et pourquoi elle est asymétrique :
  - attaquant : HandleDamage renvoie 0 → il survit et continue de tirer toute la fenêtre.
  - défenseur : HandleDamage renvoie min(dégât, 0,55) → il ENCAISSE (donc son IA réagit à
    l'impact, ce qui est précisément le mécanisme mesuré) mais ne meurt pas.
    `allowDamage false` a été écarté : il aurait pu supprimer la réaction au coup reçu.

Usage : python3 sonde_arc_contact.py --reps 6
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
ANGLES = [0, 45, 90, 135, 180]

ap = argparse.ArgumentParser()
ap.add_argument("--reps", type=int, default=6)
ap.add_argument("--duree", type=int, default=75)
ap.add_argument("--dist", type=float, default=60.0)
ap.add_argument("--tag", default="lambs")
a = ap.parse_args()

CELLS = json.load(open(LEV + "/cellules_altis.json"))["serie"]
if len(CELLS) < len(ANGLES):
    print("!! pas assez de cellules valides (%d)" % len(CELLS))
    sys.exit(2)
NC = min(len(CELLS), 10)
CELLS = CELLS[:NC]


def fermer(b):
    try:
        b.close()
    except Exception:
        pass


def poser(b, rep):
    """Une cellule par angle. L'affectation angle->cellule TOURNE à chaque répétition :
    sans cela, l'angle serait confondu avec l'emplacement."""
    plan = []
    for i, ang in enumerate(ANGLES):
        cx, cy, _h = CELLS[(i + rep) % NC]
        plan.append((ang, cx, cy))

    c = ["if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; "
         "if (!isNil " + Q + "HMT_EF" + Q + ") then { removeMissionEventHandler [" + Q + "EachFrame" + Q + ", HMT_EF] }; "
         "HMT_S = []; HMT_DEF = []; HMT_ATT = []; "
         "HMT_FATT = []; HMT_FDEF = []; HMT_IMP = []; "
         "HMT_TATT = []; HMT_TDEF = []; HMT_TIMP = []; HMT_TDIR = []; HMT_LT = []; HMT_KNOW = []; "
         "HMT_LASTEF = 0; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]

    for i, (ang, cx, cy) in enumerate(plan):
        K = str(i)
        rad = math.radians(ang)
        ax = cx + a.dist * math.sin(rad)
        ay = cy + a.dist * math.cos(rad)
        c.append(
            "HMT_FATT pushBack 0; HMT_FDEF pushBack 0; HMT_IMP pushBack 0; "
            "HMT_TATT pushBack -1; HMT_TDEF pushBack -1; HMT_TIMP pushBack -1; HMT_TDIR pushBack -1; "
            "HMT_LT pushBack 0; HMT_KNOW pushBack 0; "
            # --- le défenseur : regarde le NORD, tient sa position, encaisse sans mourir
            "private _gd = createGroup east; "
            "private _d = _gd createUnit [" + Q + "O_Soldier_F" + Q + ", "
            "[" + str(cx) + "," + str(cy) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            "_d setPosATL [" + str(cx) + "," + str(cy) + ",0]; "
            "_d setDir 0; _d setSkill 0.5; _d setUnitPos " + Q + "UP" + Q + "; "
            "_d setBehaviour " + Q + "COMBAT" + Q + "; _d setCombatMode " + Q + "RED" + Q + "; "
            "_d disableAI " + Q + "PATH" + Q + "; "
            "_d setVariable [" + Q + "hmt_k" + Q + ", " + K + "]; "
            # INSTRUMENT (corrige apres sonde_arret) : « HandleDamage renvoyant min(degat, 0,55) »
            # NE PROTEGE PAS — le defenseur ainsi monte est mort en 10 s. `allowDamage false`
            # protege reellement (cellule 1 de sonde_arret : vivant et tirant sur 90 s).
            "_d allowDamage false; "
            "_d addEventHandler [" + Q + "Fired" + Q + ", { "
            "  private _k = (_this select 0) getVariable [" + Q + "hmt_k" + Q + ", -1]; "
            "  if (_k >= 0) then { HMT_FDEF set [_k, (HMT_FDEF select _k) + 1]; "
            "    if ((HMT_TDEF select _k) < 0) then { HMT_TDEF set [_k, diag_tickTime] }; }; }]; "
            # --- l'attaquant : invulnérable, cloué au sol, et il TIRE
            "private _ga = createGroup west; "
            "private _at = _ga createUnit [" + Q + "B_Soldier_F" + Q + ", "
            "[" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0], [], 0, " + Q + "NONE" + Q + "]; "
            "_at setPosATL [" + ("%.1f" % ax) + "," + ("%.1f" % ay) + ",0]; "
            "_at setDir " + ("%.1f" % ((ang + 180) % 360)) + "; "
            "_at setSkill 0.6; _at setUnitPos " + Q + "UP" + Q + "; "
            "_at setBehaviour " + Q + "COMBAT" + Q + "; _at setCombatMode " + Q + "RED" + Q + "; "
            "_at disableAI " + Q + "PATH" + Q + "; _at disableAI " + Q + "COVER" + Q + "; "
            "_at disableAI " + Q + "SUPPRESSION" + Q + "; _at disableAI " + Q + "AUTOCOMBAT" + Q + "; "
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
            "      HMT_LT set [_k, _t]; HMT_IMP set [_k, (HMT_IMP select _k) + 1]; "
            "      if ((HMT_TIMP select _k) < 0) then { HMT_TIMP set [_k, _t] }; }; }; "
            "  0 }]; "
            "HMT_S pushBack _d; HMT_S pushBack _at; "
            "HMT_DEF pushBack _d; HMT_ATT pushBack _at; ")

    # --- détection de la RÉORIENTATION, à 0,2 s près, côté serveur
    c.append(
        "HMT_EF = addMissionEventHandler [" + Q + "EachFrame" + Q + ", { "
        "  if (isNil " + Q + "HMT_DEF" + Q + ") exitWith {}; "
        "  private _t = diag_tickTime; "
        "  if (_t - HMT_LASTEF < 0.2) exitWith {}; "
        "  HMT_LASTEF = _t; "
        "  { private _k = _forEachIndex; private _aa = HMT_ATT select _k; "
        "    if (!isNull _x && {!isNull _aa}) then { "
        "      private _kn = _x knowsAbout _aa; "
        "      if (_kn > (HMT_KNOW select _k)) then { HMT_KNOW set [_k, _kn] }; "
        "      if ((HMT_TDIR select _k) < 0) then { "
        "        private _br = _x getDir _aa; "
        "        private _e = abs (((_br - (getDir _x)) + 540) " + P + " 360 - 180); "
        "        if (_e < 25) then { HMT_TDIR set [_k, _t] }; }; }; "
        "  } forEach HMT_DEF; }]; ")
    c.append("(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_DEF]) call HMT_EMIT;")
    r = b.query("".join(c), r"PRET (\d+)", want=1, timeout=120)
    return (r, plan)


def feu(b):
    """On force l'attaquant à ouvrir et à MAINTENIR le feu. Sans accusé : 5 ordres, zéro attente."""
    o = []
    for i in range(len(ANGLES)):
        K = str(i)
        o.append("private _x" + K + " = HMT_ATT select " + K + "; private _y" + K + " = HMT_DEF select " + K + "; "
                 "if (alive _x" + K + " && alive _y" + K + ") then { "
                 "_x" + K + " reveal [_y" + K + ", 4]; _x" + K + " doTarget _y" + K + "; "
                 "_x" + K + " doFire _y" + K + "; }; ")
    b.send("".join(o), wait=False)


def lire(b):
    q = ("private _o = " + Q + Q + "; "
         "{ private _k = _forEachIndex; "
         "  _o = _o + format [" + Q + P + "1/" + P + "2/" + P + "3/" + P + "4/" + P + "5/" + P + "6/" + P + "7/" + P + "8;" + Q + ", "
         "    HMT_FATT select _k, HMT_FDEF select _k, HMT_IMP select _k, "
         "    round ((HMT_TATT select _k) * 100), round ((HMT_TDEF select _k) * 100), "
         "    round ((HMT_TIMP select _k) * 100), round ((HMT_TDIR select _k) * 100), "
         "    round ((HMT_KNOW select _k) * 100)]; "
         "} forEach HMT_DEF; "
         "(format [" + Q + "L " + P + "1" + Q + ", _o]) call HMT_EMIT;")
    r = b.query(q, r"L (\S+)", want=1, timeout=30)
    if not r:
        return None
    out = []
    for item in r[-1].group(1).strip(";").split(";"):
        p = item.split("/")
        if len(p) != 8:
            continue
        fa, fd, im, ta, td, ti, tdir, kn = (int(v) for v in p)
        out.append({"tirs_att": fa, "tirs_def": fd, "impacts": im,
                    "t_att": ta / 100.0, "t_def": td / 100.0, "t_imp": ti / 100.0,
                    "t_dir": tdir / 100.0, "knows": kn / 100.0})
    return out


def main():
    b = NativeBridge(port=theatre.use("altis").PORT)
    print("=== DUREE DE VIE DE L'ANGLE MORT AU CONTACT ===", flush=True)
    print("    criteres 82f3dad52683dd8f | %d angles x %d reps | %.0f m | %d s"
          % (len(ANGLES), a.reps, a.dist, a.duree), flush=True)
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
                print("  rep %d : mise en place SANS REPONSE — arret" % (rep + 1), flush=True)
                break
            print("", flush=True)
            print("  rep %d/%d  cellules %s" % (rep + 1, a.reps,
                  " ".join("%d deg@%d,%d" % (ang, cx, cy) for ang, cx, cy in plan)), flush=True)
            time.sleep(1.5)          # le moins de temps possible : le defenseur ne doit pas
            t = 0                    # reperer l attaquant AVANT que celui-ci ouvre le feu
            feu(b)
            while t < a.duree:
                time.sleep(2)
                t += 2
                feu(b)
                if t % 20 == 0:
                    v = lire(b)
                    if v:
                        print("     +%2ds  %s" % (t, "  ".join(
                            "%d:%da/%dd/%di" % (ANGLES[i], c["tirs_att"], c["tirs_def"], c["impacts"])
                            for i, c in enumerate(v))), flush=True)
            v = lire(b)
            b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S; HMT_S = []; "
                   "removeMissionEventHandler [" + Q + "EachFrame" + Q + ", HMT_EF]; "
                   "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
            if v:
                for i, c in enumerate(v):
                    c["angle"] = ANGLES[i]
                    c["rep"] = rep
                    c["cellule"] = [plan[i][1], plan[i][2]]
                    brut.append(c)
            time.sleep(3)
    finally:
        try:
            b.send("if (!isNil " + Q + "HMT_S" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; "
                   "if (!isNil " + Q + "HMT_EF" + Q + ") then { removeMissionEventHandler [" + Q + "EachFrame" + Q + ", HMT_EF] };",
                   wait=False)
        except Exception:
            pass
        fermer(b)

    depouiller(brut)
    return 0


def med(v):
    v = sorted(v)
    n = len(v)
    if n == 0:
        return float("nan")
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def depouiller(brut):
    D = float(a.duree)
    par = {ang: [] for ang in ANGLES}
    jetes = 0
    for c in brut:
        if c["tirs_att"] == 0 or c["t_att"] < 0:
            jetes += 1                        # cellule sans feu d'ouverture : jetee, pas interpretee
            continue
        t0 = c["t_att"]
        c["lat_rip"] = (c["t_def"] - t0) if c["t_def"] > 0 else D
        c["lat_dir"] = (c["t_dir"] - t0) if c["t_dir"] > 0 else D
        c["lat_imp"] = (c["t_imp"] - t0) if c["t_imp"] > 0 else D
        c["riposte"] = 1 if c["t_def"] > 0 else 0
        par[c["angle"]].append(c)

    print("", flush=True)
    print("=== RESULTAT — %d cellules retenues, %d jetees (attaquant muet) ==="
          % (sum(len(v) for v in par.values()), jetes), flush=True)
    print("  %5s %5s %10s %10s %10s %9s %9s %8s"
          % ("angle", "n", "t_riposte", "t_direct", "t_impact", "riposte", "impacts", "knows"), flush=True)
    res = {}
    for ang in ANGLES:
        v = par[ang]
        if not v:
            print("  %5d %5d        (aucune donnee)" % (ang, 0), flush=True)
            res[str(ang)] = None
            continue
        res[str(ang)] = {
            "n": len(v),
            "t_riposte_med": med([c["lat_rip"] for c in v]),
            "t_direction_med": med([c["lat_dir"] for c in v]),
            "t_impact_med": med([c["lat_imp"] for c in v]),
            "taux_riposte": sum(c["riposte"] for c in v) / float(len(v)),
            "impacts_moy": sum(c["impacts"] for c in v) / float(len(v)),
            "tirs_def_moy": sum(c["tirs_def"] for c in v) / float(len(v)),
            "tirs_att_moy": sum(c["tirs_att"] for c in v) / float(len(v)),
            "knows_max_moy": sum(c["knows"] for c in v) / float(len(v)),
            "lat_rip": [c["lat_rip"] for c in v],
        }
        r = res[str(ang)]
        print("  %5d %5d %10.1f %10.1f %10.1f %8.0f%% %9.1f %8.2f"
              % (ang, r["n"], r["t_riposte_med"], r["t_direction_med"], r["t_impact_med"],
                 100 * r["taux_riposte"], r["impacts_moy"], r["knows_max_moy"]), flush=True)

    print("", flush=True)
    print("=== VERDICTS (seuils figes 82f3dad52683dd8f) ===", flush=True)
    r0 = res.get("0")
    r180 = res.get("180")
    verdicts = {}

    # CANARI
    if r0:
        vite = sum(1 for x in r0["lat_rip"] if x < 10.0)
        ok = (vite >= max(4, int(round(0.8 * r0["n"]))))
        verdicts["canari"] = {"riposte_moins_10s": vite, "n": r0["n"], "ok": bool(ok)}
        print("  CANARI 0 deg : %d/%d ripostes en moins de 10 s -> %s"
              % (vite, r0["n"], "OK" if ok else "ECHEC, ON NE CONCLUT RIEN"), flush=True)
        if not ok:
            json.dump({"brut": brut, "par_angle": res, "verdicts": verdicts},
                      open(LEV + "/sonde_arc_contact_%s.json" % a.tag, "w"), indent=1)
            print("ARCCONTACT_DONE", flush=True)
            return

    if r0 and r180:
        d = r180["t_riposte_med"] - r0["t_riposte_med"]
        v1 = d >= 3.0
        verdicts["V1_latence_dorsale"] = {"delta_s": d, "oui": bool(v1)}
        print("  V1 : t_rip(180) - t_rip(0) = %+.1f s -> %s"
              % (d, "IL EXISTE une latence dorsale" if v1 else "PAS d'angle mort au contact"), flush=True)

        jamais = sum(1 for x in r180["lat_rip"] if x >= D - 0.01)
        geo = jamais >= max(4, int(round(0.8 * r180["n"])))
        verdicts["V2_nature"] = {"jamais_riposte": jamais, "n": r180["n"],
                                 "nature": "GEOMETRIE" if geo else "COMPORTEMENT"}
        print("  V2 : a 180 deg, %d/%d n'ont JAMAIS riposte en %ds -> %s"
              % (jamais, r180["n"], a.duree, "GEOMETRIE (le dos est un abri durable)"
                 if geo else "COMPORTEMENT (le cone se reoriente : le sandbox doit modeliser une LATENCE)"), flush=True)

        inv = [ang for ang in ANGLES if res.get(str(ang)) and
               res[str(ang)]["t_direction_med"] > res[str(ang)]["t_riposte_med"] + 0.5]
        verdicts["V3_direction_avant_riposte"] = {"angles_en_defaut": inv, "ok": not inv}
        print("  V3 : reorientation avant riposte -> %s"
              % ("OK a tous les angles" if not inv
                 else "EN DEFAUT a %s : il tire sans se tourner" % inv), flush=True)

        rap = r180["impacts_moy"] / max(r0["impacts_moy"], 1e-9)
        verdicts["V4_ampleur"] = {"impacts_0": r0["impacts_moy"], "impacts_180": r180["impacts_moy"],
                                  "rapport": rap}
        print("  V4 : impacts 180/0 = %.1f / %.1f = %.2f  <- le facteur que le sandbox doit reproduire"
              % (r180["impacts_moy"], r0["impacts_moy"], rap), flush=True)

    json.dump({"criteres": "82f3dad52683dd8f", "duree_s": a.duree, "dist": a.dist,
               "brut": brut, "par_angle": res, "verdicts": verdicts},
              open(LEV + "/sonde_arc_contact_%s.json" % a.tag, "w"), indent=1)
    print("-> %s/sonde_arc_contact_%s.json" % (LEV, a.tag), flush=True)
    print("ARCCONTACT_DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
