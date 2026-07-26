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


def mk_markers_sqf(fx, fy):
    """SQF des marqueurs de carte. On les CREE UNE FOIS puis on les DEPLACE (setMarkerPos).
    Les recreer en boucle les faisait clignoter sans jamais s'afficher cote client."""
    return (
        '{ deleteMarker _x } forEach allMapMarkers select { (_x select [0,4]) == "hmk_" }; '
        'HMT_MKINIT = true; '
        'private _o = createMarker ["hmk_obj", [%d,%d,0]]; _o setMarkerType "mil_objective"; '
        '_o setMarkerColor "ColorGreen"; _o setMarkerSize [1.3,1.3]; _o setMarkerText "OBJECTIF"; '
        'for "_i" from 0 to 29 do { private _n = createMarker [format ["hmk_w%%1", _i], [0,0,0]]; '
        '_n setMarkerType "mil_dot"; _n setMarkerColor "ColorBLUFOR"; _n setMarkerSize [0.8,0.8]; '
        '_n setMarkerAlpha 0; }; '
        'for "_i" from 0 to 29 do { private _n = createMarker [format ["hmk_e%%1", _i], [0,0,0]]; '
        '_n setMarkerType "mil_dot"; _n setMarkerColor "ColorOPFOR"; _n setMarkerSize [0.8,0.8]; '
        '_n setMarkerAlpha 0; }; '
        'private _m = createMarker ["hmk_moi", [0,0,0]]; _m setMarkerType "mil_triangle"; '
        '_m setMarkerColor "ColorPink"; _m setMarkerSize [1.4,1.4]; _m setMarkerText "MOI"; '
        '_m setMarkerAlpha 0; }; '
        'HMT_MARKERS = { '
        'private _k = 0; { private _n = format ["hmk_w%%1", _k]; '
        '_n setMarkerPos (getPosATL _x); _n setMarkerAlpha 1; '
        '_n setMarkerColor (if (alive _x) then {"ColorBLUFOR"} else {"ColorGrey"}); '
        '_k = _k + 1; } forEach HMT_WPILOT; '
        'for "_i" from _k to 29 do { (format ["hmk_w%%1", _i]) setMarkerAlpha 0 }; '
        '_k = 0; { private _n = format ["hmk_e%%1", _k]; '
        '_n setMarkerPos (getPosATL _x); _n setMarkerAlpha 1; '
        '_n setMarkerColor (if (alive _x) then {"ColorOPFOR"} else {"ColorGrey"}); '
        '_k = _k + 1; } forEach HMT_EAST; '
        'for "_i" from _k to 29 do { (format ["hmk_e%%1", _i]) setMarkerAlpha 0 }; '
        'if (count allPlayers > 0) then { "hmk_moi" setMarkerPos (getPosATL (allPlayers select 0)); '
        '"hmk_moi" setMarkerAlpha 1; }; };' % (fx, fy))


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
    ap.add_argument("--cone", type=float, default=None, help="demi-angle du cône de décision, en degrés (90 = défaut, 135 = grand contournement autorisé)")
    ap.add_argument("--w_expo", type=float, default=None, help="poids de l'exposition dans le choix du point")
    ap.add_argument("--secteur", default=None, help="FORCE le secteur d'approche (exploration) : sud, est, nord, ouest...")
    ap.add_argument("--valeur", default=None, help="fichier de valeur apprise (valeur_v1.npz) : remplace le barème écrit à la main")
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

    # --- le terrain : relevé EXACT du moteur si dispo (relief + vrais obstacles), sinon plan reconstruit ---
    terr = IN.charger_terrain(LEV, TH.WORLD, TH.FOB[0], TH.FOB[1])
    print("terrain : %s" % ("relevé EXACT (relief + obstacles réels)" if isinstance(terr, IN.TerrainExact)
                            else "plan reconstruit (approché)"), flush=True)
    if a.cone:                       # ouvrir le cône = autoriser le GRAND contournement (sinon ±90° interdit le vrai flanc)
        IN.CFG["cone"] = math.radians(a.cone)
    if a.w_expo is not None:
        IN.CFG["w_expo"] = a.w_expo
    print("cône de décision ±%.0f° | poids de l'exposition %.1f" % (math.degrees(IN.CFG["cone"]), IN.CFG["w_expo"]), flush=True)
    V = None
    if a.valeur:
        V = IN.Valeur(a.valeur if "/" in a.valeur else "%s/%s" % (LEV, a.valeur))
        print("décision : JUGEMENT APPRIS (r2 sur parties inédites = %.3f)" % V.r2, flush=True)
    else:
        print("décision : barème écrit à la main", flush=True)
    b.send('call compile preprocessFileLineNumbers "intent_exec.sqf";'); time.sleep(0.4)
    # CONDITIONS FIXES : plein jour, ciel dégagé. De nuit les défenseurs ne voient rien et
    # l'agent apprendrait que l'exposition ne compte pas (piège attrapé le 25/07).
    b.send("setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange;"); time.sleep(0.6)
    # MARQUEURS DE CARTE (touche M) : agents bleus, defenseurs rouges, joueur rose, objectif vert.
    # Injectes a chaque run -> ils survivent aux redemarrages de serveur.
    b.send(mk_markers_sqf(fx, fy)); time.sleep(0.4)
    # boucle PERMANENTE : on la (re)lance a chaque run, l'ancienne s'arrete d'elle-meme (jeton)
    b.send('HMT_MKGEN = (if (isNil "HMT_MKGEN") then {0} else {HMT_MKGEN}) + 1; '
           'private _g = HMT_MKGEN; [_g] spawn { params ["_g"]; '
           'while { _g == HMT_MKGEN } do { call HMT_MARKERS; sleep 1 } };')
    b.send("private _es = allUnits select {side _x==east && alive _x}; "
           "{ private _e=_x; { _e reveal [_x,3] } forEach HMT_WPILOT } forEach _es; "
           "{ private _w=_x; { _w reveal [_x,3] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)

    agents = [IN.Agent(i) for i in range(a.nag)]
    plans = None; expo_sect = {}
    prev_dmg = [0.0] * a.nag
    frames = []; took_tick = None; min_pen = 999.0; changements = 0; finis = {}; stagne = 0
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

        # --- LA VOIX INTERNE : les plans longs, distribués une fois, tenus ensuite ---
        if plans is None and ennemis:
            plans, expo_sect = IN.repartir_plans(a.nag, terr, ennemis, secteur_force=a.secteur)
            print("  carte d'exposition par secteur : %s" % ", ".join(
                "%s %.0f%%" % (k, 100 * v[0]) for k, v in sorted(expo_sect.items(), key=lambda kv: kv[1][0])), flush=True)
            for r in (IN.BASE_DE_FEU, IN.MANOEUVRE):
                p = next((x for x in plans if x.role == r), None)
                if p: print("  %-11s (%d hommes) se dit : « %s »" % (
                    r, sum(1 for x in plans if x.role == r), p.voix), flush=True)

        cmds = []
        for i in range(n):
            if not vivant[i]:
                continue
            ag = agents[i]
            sous_le_feu = (degats[i] - prev_dmg[i]) > 0.01
            fini, raison = ag.done(step, pos[i], vivants_idx, IN.LIMITES)
            if fini:
                finis[raison] = finis.get(raison, 0) + 1
                # le PLAN décide vers quoi « progresser » veut dire en ce moment
                but = (0.0, 0.0)
                if plans and i < len(plans):
                    av = plans[i].voix
                    but = plans[i].but(pos[i])
                    if plans[i].voix != av:
                        print("  [%02d] soldat %d : « %s »" % (step, i, plans[i].voix), flush=True)
                if but is None:                      # base de feu : tenir et appuyer, ne pas avancer
                    vus = [k for k, e in enumerate(ennemis)
                           if math.hypot(pos[i][0] - e[0], pos[i][1] - e[1]) < IN.CFG["portee_appui"]]
                    kind, tgt, en = (IN.APPUYER, None, vus[0]) if vus else (IN.ABRITER, None, -1)
                else:
                    if V is not None:
                        kind, tgt, en = IN.prof_appris(ag, pos[i], but, terr, ennemis,
                                                       sous_le_feu, allies, degats[i], IN.CFG, V)
                    else:
                        kind, tgt, en = IN.prof(ag, pos[i], but, terr, ennemis,
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
        progresse = pen < min_pen - 1.0     # comparer AVANT de mettre a jour le record (bug du 26/07)
        min_pen = min(min_pen, pen)
        if pen < a.secure and took_tick is None:
            took_tick = step
        frames.append({"t": step,
                       "west": [[round(W[i][0], 1), round(W[i][1], 1), int(vivant[i]),
                                 (1 if agents[i].kind in (IN.APPUYER, IN.ABRITER) else 0)] for i in range(n)],
                       "intent": [agents[i].kind if agents[i].kind is not None else -1 for i in range(n)],
                       "east": [[e[0], e[1], e[2]] for e in E],
                       "firew": [1 if agents[i].kind == IN.APPUYER else 0 for i in range(n)],
                       "voix": [(plans[i].voix if plans and i < len(plans) else "") for i in range(n)],
                       **({"player": [round(P[0], 1), round(P[1], 1)]} if P else {})})
        nv = sum(vivant)
        if step % 5 == 0 or pen < a.secure:
            rep = {}
            for i in range(n):
                if vivant[i]:
                    rep[IN.NOMS.get(agents[i].kind, "?")] = rep.get(IN.NOMS.get(agents[i].kind, "?"), 0) + 1
            print("  [%02d] vivants=%2d ->obj=%3.0fm | %s" % (step, nv, pen,
                  " ".join("%s:%d" % kv for kv in sorted(rep.items()))), flush=True)
        stagne = 0 if progresse else stagne + 1
        if stagne >= 30 and pen > a.secure + 15 and step > 35:
            print("  -> ARRÊT ANTICIPÉ : plus de terrain gagné depuis 25 tours (issue connue)", flush=True)
            break
        if nv == 0:
            print("  -> ESCOUADE ANÉANTIE"); break
        if pen < a.secure:
            print("  -> OBJECTIF PRIS !"); break
        time.sleep(a.tick)

    ef = sum(1 for e in E if e[2] > 0)
    wf = sum(1 for i in range(min(len(W), a.nag)) if W[i][2] > 0)
    # CE QUI SERT À L'APPRENTISSAGE : le secteur choisi ET son exposition MESURÉE.
    # C'est l'exposition qui doit être apprise, pas la direction : les défenseurs bougent d'une
    # partie à l'autre, donc « le sud » ne veut rien dire — « 5 % d'exposition » si.
    sect = plans[-1].secteur if plans else ""
    metrics = {"secteur": sect, "expo_secteur": round(expo_sect.get(sect, (None, 0))[0], 3) if sect in expo_sect else None,
               "expo_tous": {k: round(v[0], 3) for k, v in expo_sect.items()},
               "mode": "intentions", "nag": a.nag, "west_end": wf, "west_losses": a.nag - wf,
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
