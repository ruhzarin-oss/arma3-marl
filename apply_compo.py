P="/home/younes/compose-embodiment/compo_play.py"
src=open(P).read()
A="    # convert to single-agent instance if required by the RL algorithm"
B="            obs, _, _, _, _ = env.step(actions)"
C="        # time delay for real-time evaluation"
SETUP=(
"    # === COMPO : le cerveau tactique pilote le corps via des caps (cible-carotte) ===\n"
"    import json as _json, math as _math\n"
"    MOVE = env.unwrapped\n"
"    MOVE._resample_targets = lambda *a, **k: None   # fige : c est le cap qui commande la cible\n"
"    _LOOK = 4.0\n"
"    try:\n"
"        CAPS = _json.load(open(\"/home/younes/compose-embodiment/caps.json\"))\n"
"    except Exception:\n"
"        CAPS = [0,0,0,2,2,0,1,0]\n"
"    _CAPDIR = {i:(_math.cos(i*_math.pi/4), _math.sin(i*_math.pi/4)) for i in range(8)}\n"
"    _K = 12\n"
"    _MAXC = args_cli.video_length if args_cli.video else 150\n"
"    _ci = 0\n"
"    print(\"[COMPO] caps=%s K=%d maxsteps=%d\" % (CAPS, _K, _MAXC), flush=True)\n"
)
INJECT=(
"            # COMPO: cible-carotte selon le cap courant\n"
"            _cap = CAPS[(_ci // _K) % len(CAPS)]\n"
"            if _cap < 8:\n"
"                _dx,_dy = _CAPDIR[_cap]\n"
"                MOVE.target_w[:,0] = MOVE._root_xy()[:,0] + _dx*_LOOK\n"
"                MOVE.target_w[:,1] = MOVE._root_xy()[:,1] + _dy*_LOOK\n"
"            else:\n"
"                MOVE.target_w[:] = MOVE._root_xy()\n"
"            if _ci %% 12 == 0:\n"
"                _r = MOVE._root_xy()[0].tolist()\n"
"                print(\"[COMPO] t=%3d cap=%d root=(%.1f,%.1f)\" %% (_ci,_cap,_r[0],_r[1]), flush=True)\n"
"            _ci += 1\n"
).replace("%%","%")
BRK=(
"        if _ci >= _MAXC:\n"
"            print(\"[COMPO] stop a %d pas\" % _ci, flush=True)\n"
"            break\n"
)
assert A in src and B in src and C in src, "ancre manquante"
src=src.replace(A, SETUP+A,1).replace(B, INJECT+B,1).replace(C, BRK+C,1)
open(P,"w").write(src)
print("patch applique.")
