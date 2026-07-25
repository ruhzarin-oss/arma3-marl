P = "/home/younes/compose-embodiment/g1_aim.py"
src = open(P).read().split("\n")
out = []
i = 0
SETUP = [
'    # === COMBAT + POSTURE DE TIR ===',
'    import sys as _sys, math as _math, torch as _torch',
'    _sys.path.insert(0, "/home/younes/compose-embodiment")',
'    from assault_terrain import AssaultTerrain as _AT',
'    from train_koth_gpu import Net as _Net',
'    _sd = _torch.load("/home/younes/compose-embodiment/soldier_shell.pt", map_location="cpu")',
'    AT = _AT(num_envs=1, A=1, D=2, relief=40.0, hit=0.06, shell_obs=True, replica=True, replica_path="/home/younes/arma3-marl/replica.npz", max_steps=600, device="cpu", seed=0)',
'    AT.move = 0.0',
'    BRAIN = _Net(AT.obs_dim, AT.n_actions, 512, 3); BRAIN.load_state_dict(_sd); BRAIN.eval()',
'    AT.reset()',
'    _d0 = float((AT.apx[0,0]**2 + AT.apy[0,0]**2) ** 0.5); _f = 40.0 / max(_d0, 1.0)',
'    _ATs = (float(AT.apx[0,0]) * _f, float(AT.apy[0,0]) * _f)',
'    G1 = env.unwrapped',
'    try: CMD = G1.command_manager.get_term("base_velocity")',
'    except Exception: CMD = G1.command_manager._terms["base_velocity"]',
'    ROB = G1.scene["robot"]; CMD._resample_command = lambda env_ids: None',
'    _arm_ids, _arm_nm = ROB.find_joints([".*_shoulder_pitch.*", ".*_elbow_pitch.*"])',
'    _arm_ids = _torch.tensor(_arm_ids, device=ROB.device, dtype=_torch.long)',
'    _defp = ROB.data.default_joint_pos[0, _arm_ids].clone()',
'    _aimp = _defp.clone()',
'    for _j in range(len(_arm_nm)): _aimp[_j] = -0.3 if "shoulder" in _arm_nm[_j] else 1.6',
'    _aim_act = (_aimp - _defp) / 0.5',
'    _SPEED = 1.0; _K = 20; _MAXC = args_cli.video_length if args_cli.video else 220; _ci = 0; _g1s = [None, None]; _cap = [0]',
'    _LAB = ["N","NE","E","SE","S","SW","W","NW","HOLD","SUPP"]',
'    print("[AIM] arms=%s default=%s" % (_arm_nm, _defp.tolist()), flush=True)',
'    print("[CB] start=%s d0=%.0f" % (_ATs, _d0), flush=True)',
]
INJ = [
'            if _ci % _K == 0:',
'                _xy = ROB.data.root_pos_w[0,:2].tolist()',
'                if _g1s[0] is None: _g1s[0] = _xy[0]; _g1s[1] = _xy[1]',
'                AT.apx[0,0] = _ATs[0] + (_xy[0] - _g1s[0]); AT.apy[0,0] = _ATs[1] + (_xy[1] - _g1s[1])',
'                with _torch.no_grad(): _cap[0] = int(BRAIN.a_logits(AT._obs()).argmax(-1).reshape(-1)[0])',
'                AT.step(_torch.tensor([[_cap[0]]]), auto_reset=False)',
'                print("[CB] t=%3d cap=%s dmg=%.2f" % (_ci, _LAB[_cap[0]], float(AT.admg[0,0])), flush=True)',
'            _c = _cap[0]',
'            if _c < 8:',
'                CMD.heading_target[:] = _math.atan2(_math.cos(_c * _math.pi/4.0), _math.sin(_c * _math.pi/4.0))',
'                CMD.vel_command_b[:,0] = _SPEED; CMD.vel_command_b[:,1] = 0.0',
'            else:',
'                CMD.vel_command_b[:,0] = 0.0; CMD.vel_command_b[:,1] = 0.0; CMD.heading_target[:] = ROB.data.heading_w',
'                actions[:, _arm_ids] = _aim_act',
'            _ci += 1',
]
BREAK = [
'        if _ci >= _MAXC:',
'            print("[CB] stop", flush=True); break',
]
while i < len(src):
    l = src[i]
    if l.strip().startswith("# convert to single-agent"):
        out += SETUP + [l]; i += 1; continue
    if l.strip() == "obs, _, _, _, _ = env.step(actions)":
        out += INJ + [l]; i += 1; continue
    if l.strip().startswith("# time delay for real-time"):
        out += BREAK + [l]; i += 1; continue
    out.append(l); i += 1
open(P, "w").write("\n".join(out))
print("patch ok, CB:", sum(1 for x in out if "[CB]" in x), "AIM:", sum(1 for x in out if "_aim_act" in x))
