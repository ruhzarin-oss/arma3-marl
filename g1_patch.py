src=open("g1_compo.py").read().split("\n"); out=[]; i=0
SETUP=[
"    # === COMPO G1 : l esprit (caps) pilote la commande de vitesse ===",
"    import json as _json, math as _math",
"    G1 = env.unwrapped",
"    try: CMD = G1.command_manager.get_term(\"base_velocity\")",
"    except Exception: CMD = G1.command_manager._terms[\"base_velocity\"]",
"    ROB = G1.scene[\"robot\"]",
"    CMD._resample_command = lambda env_ids: None",
"    _SPEED = 1.0",
"    try: CAPS = _json.load(open(\"/home/younes/compose-embodiment/caps.json\"))",
"    except Exception: CAPS = [0,0,0,2,2,0,1,0]",
"    _K = 20",
"    _MAXC = args_cli.video_length if args_cli.video else 140",
"    _ci = 0",
"    print(\"[G1COMPO] caps=%s K=%d max=%d\" % (CAPS,_K,_MAXC), flush=True)",
]
INJ=[
"            _cap = CAPS[(_ci // _K) % len(CAPS)]",
"            if _cap < 8:",
"                CMD.heading_target[:] = _cap * (_math.pi/4.0)",
"                CMD.vel_command_b[:, 0] = _SPEED",
"                CMD.vel_command_b[:, 1] = 0.0",
"            else:",
"                CMD.vel_command_b[:, 0] = 0.0",
"                CMD.vel_command_b[:, 1] = 0.0",
"                CMD.heading_target[:] = ROB.data.heading_w",
"            if _ci %% 20 == 0:",
"                _p = ROB.data.root_pos_w[0, :2].tolist()",
"                print(\"[G1COMPO] t=%3d cap=%d xy=(%.1f,%.1f)\" %% (_ci,_cap,_p[0],_p[1]), flush=True)",
"            _ci += 1",
]
INJ=[l.replace("%%","%") for l in INJ]
while i < len(src):
    l=src[i]
    if l.strip().startswith("# convert to single-agent"):
        out += SETUP + [l]; i+=1; continue
    if l.strip()=="obs, _, _, _, _ = env.step(actions)":
        out += INJ + [l]; i+=1; continue
    if l.strip().startswith("# time delay for real-time"):
        out += ["        if _ci >= _MAXC:", "            print(\"[G1COMPO] stop\", flush=True); break", l]; i+=1; continue
    out.append(l); i+=1
open("g1_compo.py","w").write("\n".join(out)); print("patch ok")
