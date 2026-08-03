#!/usr/bin/env python3
"""envelop_arma.py — A/B sur ARMA : ASSAUT FRONTAL vs DÉBORDEMENT, mêmes forces, même FOB, même caméra.
Fire-and-maneuver (mode envelop) : les FIXEURS tiennent une ligne de feu et SUPPRIMENT (ne vont jamais au FOB) ;
les DÉBORDEURS filent au flanc sur un ARC (points distincts par binôme, pas de blob) puis assautent le FOB à
l'ARRIVÉE au flanc. Mode frontal : tout le monde assaute le FOB de face (la mauvaise exécution = le témoin).
La caméra sort des NOMBRES (pertes, FOB pris, temps) + le replay top-down. doMove déterministe = placement propre.
  setup : spawn WEST (loadout 003, --nag soldats), compile sqf, coupe LAMBS
  run   : SENSE -> cibles selon --mode -> doMove + feu ; écrit <out> (frames + metrics)
  disarm: nettoie"""
import sys, time, ast, math, json, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre   # THÉÂTRE : coordonnées + port du monde actif (défaut STRATIS, inchangé)

LOAD003 = "/home/younes/Bureau/003.ar"


def loadout003():
    try: return str(ast.literal_eval(open(LOAD003).read().strip())[0]).replace("'", '"')
    except Exception: return None


def setup_sqf(sx, sy, fx, fy, ld, nag):   # spawn nag soldats WEST autour de (sx,sy), FOB=(fx,fy), ARM (coupe LAMBS)
    setl = ("{ _x setUnitLoadout %s } forEach HMT_WPILOT; " % ld) if ld else ""
    loop = ("private _try=0; while { count HMT_WPILOT < %d && _try < 500 } do { _try=_try+1; "
            "if ((count HMT_WPILOT) mod 10 == 0) then { HMT_WG = createGroup west }; "
            "private _px=%d+(random 60)-30; private _py=%d-(random 40); "
            "private _u = HMT_WG createUnit [\"B_soldier_F\",[_px,_py,0],[],0,\"NONE\"]; "
            "if (!isNull _u) then { _u allowDamage false; _u setPosATL [_px,_py,0]; "
            "_u enableSimulation true; _u enableDynamicSimulation false; "   # DÉGEL : simulé même sans joueur proche (sinon l'escouade reste inerte)
            "HMT_WPILOT pushBack _u }; }; ") % (nag, sx, sy)
    return ("[] spawn { if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; "
            "HMT_FOB=[%d,%d]; " % (fx, fy)
            + loop + setl + "call HMT_SHAMAL_ARM; { if (!isNull _x) then { _x allowDamage true } } forEach HMT_WPILOT; "
            "(format [\"HARMATTAN_SHL west=%1\", count HMT_WPILOT]) call HMT_EMIT; };")


def parse_sense(payload):
    _, _, right = payload.partition("|")
    rows = []
    for t in right.strip().rstrip(";").split(";"):
        f = t.strip().split(",")
        if len(f) >= 9 and f[0].lstrip("-").isdigit():
            rows.append([float(v) for v in f[:9]])
    return rows


def east_count(b):   # compte FIABLE des défenseurs (pour les métriques, indépendant de l'émission de positions)
    r = b.query('(format ["HARMATTAN_ECNT %1 %2", count (allUnits select {side _x==east}), count (allUnits select {side _x==east && alive _x})]) call HMT_EMIT;',
                r"HARMATTAN_ECNT (\d+) (\d+)", want=1, timeout=10)
    return (int(r[-1].group(1)), int(r[-1].group(2))) if r else (0, 0)


def east_positions(b, fx, fy):   # positions des défenseurs pour la caméra
    er = b.query(f'private _o=""; {{ _o=_o+format ["%1,%2,%3;", round((getPosATL _x select 0)-{fx}), round((getPosATL _x select 1)-{fy}), (if (alive _x) then {{1}} else {{0}})] }} forEach (allUnits select {{side _x==east}}); (format ["HARMATTAN_EPOS %1", _o]) call HMT_EMIT;',
                r"HARMATTAN_EPOS (.*)", want=1, timeout=10)
    east = []
    if er:
        for tt in er[-1].group(1).strip().rstrip(";").split(";"):
            ff = tt.split(",")
            if len(ff) >= 3 and ff[0].lstrip("-").isdigit():
                east.append([fx + float(ff[0]), fy + float(ff[1]), int(float(ff[2]))])
    return east


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--fob", default=None); ap.add_argument("--steps", type=int, default=60)
    # A=frontal (simple), B=supfront (fixeurs + assaut FRONTAL, SANS l'angle), C=envelop (fixeurs + FLANC) -> isole suppression vs géométrie (Fable, 3 bras)
    ap.add_argument("--mode", choices=["frontal", "supfront", "envelop", "reckless"], default="envelop")
    ap.add_argument("--nag", type=int, default=18)          # nb attaquants (mêmes pour A et B)
    ap.add_argument("--offset", type=float, default=45.0)   # rayon du flanc (m) — SHALLOW (le finding)
    ap.add_argument("--standoff", type=float, default=70.0) # distance ligne de feu au FOB (m)
    ap.add_argument("--flank", type=float, default=0.45)    # part DÉBORDEURS (reste = fixeurs)
    ap.add_argument("--side", choices=["L", "R"], default="L")
    ap.add_argument("--assault_tick", type=int, default=24)   # après ce tick, les débordeurs assautent le FOB (bascule temporelle)
    ap.add_argument("--silencieux", action="store_true")   # les assaillants NE TIRENT PAS en progression :
                                                          # doSuppressiveFire FIGE l unite (mesure 2026-07-28).
                                                          # Teste si l avantage du flanc est un artefact de l ordre de feu.
    ap.add_argument("--assaut_final", type=float, default=0.0)   # sous cette distance (m) l element d assaut CESSE de tirer et franchit ; 0 = desactive
    ap.add_argument("--smoke", action="store_true")           # écran de fumée sur l'axe (nier la détection)
    ap.add_argument("--smoke_dist", type=float, default=45.0) # distance de l'écran au FOB (m)
    ap.add_argument("--out", default="envelop_replay.json")
    theatre.add_theatre_arg(ap)
    a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)   # --theatre d'abord, PUIS on résout le FOB
    fx, fy = [int(v) for v in (a.fob or TH.fob_str).split(",")]
    sx, sy = [int(round(v)) for v in TH.spawn_for((fx, fy))]   # départ selon l'AXE D'APPROCHE du théâtre (Stratis: nord = ancien comportement)
    b = NativeBridge(port=TH.PORT)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "shamal_obs.sqf";'); time.sleep(0.3)
        b.send('call compile preprocessFileLineNumbers "envelop_arma.sqf";'); time.sleep(0.3)
        ld = loadout003()
        r = b.query(setup_sqf(sx, sy, fx, fy, ld, a.nag), r"HARMATTAN_SHL west=(\d+)", want=1, timeout=120)
        print("WEST en place : soldats=%s | loadout 003=%s | ZERO LAMBS" % (r[-1].group(1) if r else "?", "ok" if ld else "défaut"))
        return

    if a.cmd == "disarm":
        b.send('if (!isNil "HMT_WPILOT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];')
        print("nettoyé"); return

    # --- run ---
    b.send("private _es = allUnits select {side _x==east && alive _x}; { private _e=_x; { _e reveal [_x,4] } forEach HMT_WPILOT } forEach _es; { private _w=_x; { _w reveal [_x,4] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)
    sgn = 1.0 if a.side == "L" else -1.0
    OUT_JSON = "/home/younes/arma3-marl/leviathan/" + a.out
    _, east0 = east_count(b)
    print("=== A/B ARMA : mode=%s | %d WEST vs %d EAST (défense tenue) | flanc %s | fumée=%s ===" % (a.mode.upper(), a.nag, east0, a.side, "ON" if a.smoke else "off"), flush=True)
    if a.smoke:                                              # écran de fumée : ligne perpendiculaire à l'axe, entre l'escouade et le FOB
        spos = [[round(fx + (k - 3) * 12, 1), round(fy + a.smoke_dist, 1)] for k in range(7)]
        b.send("HMT_SMOKEPOS=%s; call HMT_SMOKE;" % json.dumps(spos))
    frames = []; axis = None; flank_tg = []; reached = [False] * (a.nag + 8)
    west0 = None; min_pen = 999.0; took_tick = None; series = []   # (front_dist, west_vivants, east_vivants) par tick
    for step in range(a.steps):
        r = b.query("call HMT_SHAMAL_SENSE;", r"HARMATTAN_SHS (.+)", want=1, timeout=12)
        if not r: time.sleep(1); continue
        rows = parse_sense(r[-1].group(1))
        if not rows: time.sleep(1); continue
        n = len(rows)
        ax = [fx + row[0] for row in rows]; ay = [fy + row[1] for row in rows]
        alive = [row[2] > 0.5 for row in rows]; los = [row[4] > 0.5 for row in rows]
        na = sum(alive)
        if west0 is None: west0 = na
        pen_now = min((math.hypot(ax[i] - fx, ay[i] - fy) for i in range(n) if alive[i]), default=999)
        franchit = a.assaut_final > 0 and pen_now < a.assaut_final   # ORDRE D ASSAUT FINAL
        tgts = []; fire = []; assaulting = 0
        if a.mode == "reckless":                            # (a) TÉMÉRAIRE : debout, sprint, ignore le feu (écrase l'auto-plat-ventre)
            n_deb = 0; fire = [0] * n; assaulting = na
        elif a.mode == "frontal":                           # TÉMOIN TIMIDE : assaut de face (l'IA se couche sous le feu)
            n_deb = 0
            for i in range(n):
                tgts.append([fx, fy]); fire.append(1 if los[i] else 0)
        else:                                               # DÉBORDEMENT : fire-and-maneuver
            if axis is None:                                # fige l'axe + les points de flanc en ARC au 1er tick
                cx = sum(ax[i] for i in range(n) if alive[i]) / (na or 1); cy = sum(ay[i] for i in range(n) if alive[i]) / (na or 1)
                dirx = fx - cx; diry = fy - cy; dn = math.hypot(dirx, diry) or 1.0
                ux, uy = dirx / dn, diry / dn               # vers le FOB
                px, py = -uy * sgn, ux * sgn                # perpendiculaire (côté flanc)
                fbx, fby = fx - ux * a.standoff, fy - uy * a.standoff
                nd0 = int(round(n * a.flank))
                for k in range(nd0):                        # arc : de l'abeam (p) vers l'arrière (-u), points DISTINCTS
                    frac = k / max(nd0 - 1, 1)
                    dx = px * (1 - frac) + (-ux) * 0.9 * frac; dy = py * (1 - frac) + (-uy) * 0.9 * frac
                    dl = math.hypot(dx, dy) or 1.0
                    flank_tg.append((fx + dx / dl * a.offset, fy + dy / dl * a.offset))
                axis = (ux, uy, px, py, fbx, fby, nd0)
            ux, uy, px, py, fbx, fby, n_deb = axis
            nfix = n - n_deb; fi = 0
            for i in range(n):
                if i < n_deb:                               # ÉLÉMENT DE MANŒUVRE
                    if a.mode == "supfront":                # BRAS B : assaut FRONTAL (droit au FOB, tire au contact) — MÊME suppression que C, SANS l'angle
                        tgts.append([fx, fy]); fire.append(1 if los[i] else 0); assaulting += 1
                        continue
                    tgx, tgy = flank_tg[i] if i < len(flank_tg) else (fx, fy)                       # BRAS C : débordement au flanc
                    if math.hypot(ax[i] - tgx, ay[i] - tgy) < 14 or step >= a.assault_tick: reached[i] = True   # au flanc OU signal temporel -> assaut
                    if reached[i]:
                        tgts.append([fx, fy]); fire.append(1 if los[i] else 0); assaulting += 1    # assaut sur le FOB (tire au contact)
                    else:
                        tgts.append([round(tgx, 1), round(tgy, 1)]); fire.append(0)               # swing silencieux
                else:                                       # FIXEUR : TIENT la ligne de feu, SUPPRIME, ne va JAMAIS au FOB
                    off = (fi - (nfix - 1) / 2.0) * 5.0; fi += 1
                    tgts.append([round(fbx + px * off, 1), round(fby + py * off, 1)]); fire.append(1 if los[i] else 0)
        # ORDRE D ASSAUT FINAL : l element d assaut cesse de tirer et court ; les fixeurs
        # continuent de supprimer. En frontal il n y a pas de fixeur : tout le monde franchit.
        if a.silencieux:
            fire = [0] * len(fire)   # SILENCE : personne ne tire en progression
        assaut = [0] * len(tgts)
        if franchit:
            for i in range(len(tgts)):
                est_assaut = (a.mode == "frontal") or (i < n_deb)
                if est_assaut:
                    assaut[i] = 1
                    if i < len(fire): fire[i] = 0
        if a.mode == "reckless":
            b.send("call HMT_RECKLESS;")
        else:
            b.send("HMT_ASSAUT=%s; HMT_TGTS=%s; HMT_FIRE=%s; call HMT_ENVELOP_APPLY;"
                   % (json.dumps(assaut), json.dumps(tgts), json.dumps(fire)))
        if a.smoke and step == 12: b.send("call HMT_SMOKE;")   # 2e (et dernière) salve -> budget 14 fumigènes, puis dissipation
        east = east_positions(b, fx, fy)
        role = [0] * n if a.mode == "frontal" else [int(i < n_deb) for i in range(n)]
        frames.append({"t": step, "west": [[round(ax[i], 1), round(ay[i], 1), int(alive[i]), role[i]] for i in range(n)], "east": east, "firew": fire})
        pen = min((math.hypot(ax[i] - fx, ay[i] - fy) for i in range(n) if alive[i]), default=999)
        min_pen = min(min_pen, pen)
        _, ea_now = east_count(b)                            # comptage FIABLE des défenseurs vivants (métrique par anneau)
        series.append((pen, na, ea_now))
        if pen < 25 and took_tick is None: took_tick = step
        print("  [%02d] vivants=%d/%d ->FOB=%3.0fm | assaut=%d tirent=%d%s" % (step, na, n, pen, assaulting, sum(fire), " | FRANCHISSEMENT" if franchit else ""), flush=True)
        if na == 0: print("  -> ESCOUADE ANÉANTIE"); break
        if pen < 20: print("  -> FOB PRIS !"); break
        time.sleep(0.9)
    _, east_final = east_count(b)
    west_final = na
    metrics = {"mode": a.mode, "nag": a.nag, "west_start": a.nag, "west_end": west_final,
               "west_losses": a.nag - west_final, "east_start": east0, "east_end": east_final,
               "east_neutralized": east0 - east_final, "took": took_tick is not None, "took_tick": took_tick,
               "steps": len(frames), "min_fob_dist": round(min_pen)}
    # TAUX D'ÉCHANGE PAR ANNEAU (figure de Fable) : pertes WEST vs EAST par tranche de 10m du front
    rings = {}
    for t in range(1, len(series)):
        band = int(series[t][0] // 10) * 10
        dW = max(0, series[t - 1][1] - series[t][1]); dE = max(0, series[t - 1][2] - series[t][2])
        r = rings.setdefault(band, [0, 0]); r[0] += dW; r[1] += dE
    metrics["rings"] = [{"ring": bnd, "west": v[0], "east": v[1]} for bnd, v in sorted(rings.items())]
    metrics["smoke"] = bool(a.smoke); metrics["smoke_grenades"] = 14 if a.smoke else 0
    if frames:
        json.dump({"fob": [fx, fy], "A": len(frames[0]["west"]), "B": max((len(f["east"]) for f in frames), default=0),
                   "mode": a.mode, "metrics": metrics, "frames": frames}, open(OUT_JSON, "w"))
    verdict = ("FOB PRIS tick %d" % took_tick) if metrics["took"] else ("ANÉANTIE" if west_final == 0 else "ÉCHEC (FOB non pris)")
    print("=== %s%s | pertes WEST %d/%d, EAST neutralisés %d/%d | -> %s | %s ===" % (
        a.mode.upper(), " +fumée(14)" if a.smoke else "", metrics["west_losses"], a.nag, metrics["east_neutralized"], east0, verdict, OUT_JSON), flush=True)
    if metrics["rings"]:
        print("  anneau(m) : W perdus / E perdus  ->  " + "  ".join("%d:W%dE%d" % (r["ring"], r["west"], r["east"]) for r in metrics["rings"]), flush=True)


if __name__ == "__main__":
    main()
