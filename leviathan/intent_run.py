#!/usr/bin/env python3
"""intent_run.py — BOUCLE À INTENTIONS sur Arma (étage 1).

La différence avec l'ancien pilotage : on ne redonne PAS d'ordre à chaque tour.
Chaque soldat mène son geste À SON TERME ; on ne redécide QUE pour ceux qui ont fini.
   -> plus de gigotement, chaque décision correspond à une action entière (donc apprenable).

Sortie : le MÊME format JSON que envelop_arma.py -> le rejeu animé et les schémas marchent tels quels,
avec en plus l'intention de chaque soldat à chaque instant (pour colorer et mesurer).

Usage : python intent_run.py setup --theatre altis --nag 12
        python intent_run.py run   --theatre altis --nag 12 --steps 80
"""
import sys, time, json, math, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre
import intentions as IN
from envelop_arma import loadout003, setup_sqf

LEV = "/home/younes/arma3-marl/leviathan"


def parse_sense(payload):
    """'x,y,alive,dmg;...|x,y,alive;...|px,py' -> (attaquants, défenseurs, joueur)"""
    w, e, p = (payload.split("|") + ["", "", ""])[:3]
    W = []
    for t in w.strip().rstrip(";").split(";"):
        f = t.split(",")
        if len(f) >= 4 and f[0].lstrip("-").isdigit():
            W.append((float(f[0]), float(f[1]), int(f[2]), int(f[3]) / 100.0))
    E = []
    for t in e.strip().rstrip(";").split(";"):
        f = t.split(",")
        if len(f) >= 3 and f[0].lstrip("-").isdigit():
            E.append((float(f[0]), float(f[1]), int(f[2])))
    P = None
    pf = p.strip().split(",")
    if len(pf) == 2 and pf[0].lstrip("-").isdigit():
        P = (float(pf[0]), float(pf[1]))
    return W, E, P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--nag", type=int, default=12)
    ap.add_argument("--steps", type=int, default=80)
    ap.add_argument("--secure", type=float, default=25.0)
    ap.add_argument("--tick", type=float, default=1.1)
    ap.add_argument("--out", default="intent_run.json")
    ap.add_argument("--fob", default=None)
    ap.add_argument("--markers", action="store_true", help="points live sur la carte du jeu (touche M)")
    theatre.add_theatre_arg(ap)
    a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
    fx, fy = [int(v) for v in (a.fob or TH.fob_str).split(",")]
    sx, sy = [int(round(v)) for v in TH.spawn_for((fx, fy))]
    b = NativeBridge(port=TH.PORT)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "intent_exec.sqf";'); time.sleep(0.4)
        r = b.query(setup_sqf(sx, sy, fx, fy, loadout003(), a.nag), r"HARMATTAN_SHL west=(\d+)", want=1, timeout=120)
        print("intentions : %s attaquants en place (départ %d,%d -> objectif %d,%d)"
              % (r[-1].group(1) if r else "?", sx, sy, fx, fy))
        return

    if a.cmd == "disarm":
        b.send('if (!isNil "HMT_WPILOT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];')
        print("nettoyé"); return

    # --- le plan (pour les candidats et les lignes de vue) ---
    terr = IN.Terrain("%s/map_%s_%d_%d.json" % (LEV, TH.WORLD.lower(), TH.FOB[0], TH.FOB[1]))
    b.send('call compile preprocessFileLineNumbers "intent_exec.sqf";'); time.sleep(0.4)
    b.send("private _es = allUnits select {side _x==east && alive _x}; "
           "{ private _e=_x; { _e reveal [_x,3] } forEach HMT_WPILOT } forEach _es; "
           "{ private _w=_x; { _w reveal [_x,3] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)

    agents = [IN.Agent(i) for i in range(a.nag)]
    prev_dmg = [0.0] * a.nag
    frames = []; took_tick = None; min_pen = 999.0; changements = 0; finis = {}
    print("=== INTENTIONS | %d attaquants | objectif %d,%d | %d tours ===" % (a.nag, fx, fy, a.steps), flush=True)

    for step in range(a.steps):
        r = b.query("call HMT_INTENT_SENSE;", r"HARMATTAN_INT (.+)", want=1, timeout=12)
        if not r:
            time.sleep(1); continue
        W, E, P = parse_sense(r[-1].group(1))
        if not W:
            time.sleep(1); continue
        n = min(len(W), a.nag)
        # repères relatifs à l'objectif (le module d'intentions travaille en relatif)
        pos = [(W[i][0] - fx, W[i][1] - fy) for i in range(n)]
        vivant = [W[i][2] > 0 for i in range(n)]
        degats = [W[i][3] for i in range(n)]
        ennemis = [(e[0] - fx, e[1] - fy) for e in E if e[2] > 0]
        vivants_idx = set(range(len(ennemis)))
        allies = [pos[i] if vivant[i] else None for i in range(n)]

        cmds = []
        for i in range(n):
            if not vivant[i]:
                continue
            ag = agents[i]
            sous_le_feu = (degats[i] - prev_dmg[i]) > 0.01
            fini, raison = ag.done(step, pos[i], vivants_idx, IN.LIMITES)
            if fini:
                finis[raison] = finis.get(raison, 0) + 1
                kind, tgt, en = IN.prof(ag, pos[i], (0.0, 0.0), terr, ennemis,
                                        sous_le_feu, allies, degats[i], IN.CFG)
                ag.set(kind, step, tgt, en)
                changements += 1
                tx = (tgt[0] + fx) if tgt else 0.0
                ty = (tgt[1] + fy) if tgt else 0.0
                cmds.append([i, kind, round(tx, 1), round(ty, 1), en])
        prev_dmg = [degats[i] if i < len(degats) else 0.0 for i in range(a.nag)]

        if cmds:                                   # on n'envoie QUE les intentions qui changent
            b.send("HMT_ICMD=%s; call HMT_INTENT_APPLY;" % json.dumps(cmds))
        if a.markers:                              # points sur la carte du jeu (touche M) : bleu=agents, rouge=défenseurs, MOI=joueur
            b.send("call HMT_MARKERS;")

        pen = min((math.hypot(pos[i][0], pos[i][1]) for i in range(n) if vivant[i]), default=999)
        min_pen = min(min_pen, pen)
        if pen < a.secure and took_tick is None:
            took_tick = step
        frames.append({"t": step,
                       "west": [[round(W[i][0], 1), round(W[i][1], 1), int(vivant[i]),
                                 (1 if agents[i].kind in (IN.APPUYER, IN.ABRITER) else 0)] for i in range(n)],
                       "intent": [agents[i].kind if agents[i].kind is not None else -1 for i in range(n)],
                       "east": [[e[0], e[1], e[2]] for e in E],
                       "firew": [1 if agents[i].kind == IN.APPUYER else 0 for i in range(n)],
                       **({"player": [round(P[0], 1), round(P[1], 1)]} if P else {})})
        nv = sum(vivant)
        if step % 5 == 0 or pen < a.secure:
            rep = {}
            for i in range(n):
                if vivant[i]:
                    rep[IN.NOMS.get(agents[i].kind, "?")] = rep.get(IN.NOMS.get(agents[i].kind, "?"), 0) + 1
            print("  [%02d] vivants=%2d ->obj=%3.0fm | %s" % (step, nv, pen,
                  " ".join("%s:%d" % kv for kv in sorted(rep.items()))), flush=True)
        if nv == 0:
            print("  -> ESCOUADE ANÉANTIE"); break
        if pen < a.secure:
            print("  -> OBJECTIF PRIS !"); break
        time.sleep(a.tick)

    ef = sum(1 for e in E if e[2] > 0)
    wf = sum(1 for i in range(min(len(W), a.nag)) if W[i][2] > 0)
    metrics = {"mode": "intentions", "nag": a.nag, "west_end": wf, "west_losses": a.nag - wf,
               "east_start": len(E), "east_end": ef, "east_neutralized": len(E) - ef,
               "took": took_tick is not None, "took_tick": took_tick, "steps": len(frames),
               "min_fob_dist": round(min_pen), "decisions": changements,
               "decisions_par_soldat": round(changements / max(a.nag, 1), 1), "fins": finis}
    if frames:
        json.dump({"fob": [fx, fy], "A": a.nag, "B": len(E), "mode": "intentions",
                   "metrics": metrics, "frames": frames}, open("%s/%s" % (LEV, a.out), "w"))
    print("=== INTENTIONS | objectif %s | pertes %d/%d | %d décisions (%.1f/soldat) | fins: %s ===" % (
        ("PRIS tick %d" % took_tick) if took_tick is not None else "non pris",
        metrics["west_losses"], a.nag, changements, metrics["decisions_par_soldat"],
        ", ".join("%s=%d" % kv for kv in sorted(finis.items()))), flush=True)


if __name__ == "__main__":
    main()
