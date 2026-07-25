src=open("g1_cl.py").read().split("\n"); out=[]; i=0
SETUP=[
"    # === BOUCLE FERMEE : le cerveau lit letat reel du G1 et decide ===",
"    import sys as _sys, math as _math, torch as _torch",
"    _sys.path.insert(0, \"/home/younes/compose-embodiment\")",
"    from assault_terrain import AssaultTerrain as _AT",
"    from train_koth_gpu import Net as _Net",
"    _sd = _torch.load(\"/home/younes/compose-embodiment/soldier_shell.pt\", map_location=\"cpu\")",
"    AT = _AT(num_envs=1, A=1, D=2, relief=40.0, hit=0.10, shell_obs=True, replica=True, replica_path=\"/home/younes/arma3-marl/replica.npz\", max_steps=60, device=\"cpu\", seed=0)",
"    BRAIN = _Net(AT.obs_dim, AT.n_actions, 512, 3); BRAIN.load_state_dict(_sd); BRAIN.eval()",
"    AT.reset(); _ATs=(float(AT.apx[0,0]), float(AT.apy[0,0]))",
"    G1 = env.unwrapped",
"    try: CMD = G1.command_manager.get_term(\"base_velocity\")",
"    except Exception: CMD = G1.command_manager._terms[\"base_velocity\"]",
"    ROB = G1.scene[\"robot\"]; CMD._resample_command = lambda env_ids: None",
"    _SPEED=1.0; _K=20; _MAXC = args_cli.video_length if args_cli.video else 160; _ci=0; _g1s=[None,None]; _cap=[0]",
"    print(\"[CL] AT obs=%d act=%d start=%s\" % (AT.obs_dim, AT.n_actions, _ATs), flush=True)",
]
INJ=[
"            if _ci %% _K == 0:",
"                _xy = ROB.data.root_pos_w[0,:2].tolist()",
"                if _g1s[0] is None: _g1s[0]=_xy[0]; _g1s[1]=_xy[1]",
"                AT.apx[0,0]=_ATs[0]+(_xy[0]-_g1s[0]); AT.apy[0,0]=_ATs[1]+(_xy[1]-_g1s[1])",
"                with _torch.no_grad(): _cap[0]=int(BRAIN.a_logits(AT._obs()).argmax(-1).reshape(-1)[0])",
"                print(\"[CL] t=%3d cap=%d g1=(%.1f,%.1f) at=(%.1f,%.1f)\" %% (_ci,_cap[0],_xy[0],_xy[1],float(AT.apx[0,0]),float(AT.apy[0,0])), flush=True)",
"            _c=_cap[0]",
"            if _c < 8:",
"                CMD.heading_target[:]=_math.atan2(_math.cos(_c*_math.pi/4.0), _math.sin(_c*_math.pi/4.0))",
"                CMD.vel_command_b[:,0]=_SPEED; CMD.vel_command_b[:,1]=0.0",
"            else:",
"                CMD.vel_command_b[:,0]=0.0; CMD.vel_command_b[:,1]=0.0; CMD.heading_target[:]=ROB.data.heading_w",
"            _ci+=1",
]
INJ=[l.replace("%%","%") for l in INJ]
while i < len(src):
    l=src[i]
    if l.strip().startswith("# convert to single-agent"): out+=SETUP+[l]; i+=1; continue
    if l.strip()=="obs, _, _, _, _ = env.step(actions)": out+=INJ+[l]; i+=1; continue
    if l.strip().startswith("# time delay for real-time"): out+=["        if _ci >= _MAXC:","            print(\"[CL] stop\", flush=True); break",l]; i+=1; continue
    out.append(l); i+=1
open("g1_cl.py","w").write("\n".join(out)); print("patch ok")
