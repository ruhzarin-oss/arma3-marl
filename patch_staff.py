"""patch_staff — ajoute a run_op_visual : --llm (l'officier-LLM choisit la manoeuvre) et --staff
(dump de l'etat temps reel dans staff/state.json pour le dashboard etat-major). Idempotent."""
f = "run_op_visual.py"; s = open(f).read()

INJ = '''
import json as _jstaff, os as _ostaff
LLM_DECISION = {}
STAFF_DIR = "/home/younes/arma3-marl/staff"
_SQCOL = {"SQ_APPUI": "#3b82f6", "SQ_A_OUEST": "#22c55e", "SQ_A_EST": "#f59e0b", "SQ_RESERVE": "#eab308"}
def STAFF_DUMP(runner):
    env = runner.env
    sq = {}
    for si, nm in enumerate(env.squads):
        units = [[int(env.px[si][u]), int(env.py[si][u]), int(env.dmg[si][u] < env.dmg_dead * 100)] for u in range(env.sizes[si])]
        sq[nm] = {"color": _SQCOL.get(nm, "#ddd"), "units": units, "goal": [int(env.goals[si][0]), int(env.goals[si][1])], "stance": env.stances[si]}
    en = [[int(env.epx[k]), int(env.epy[k]), int(env.edmg[k] < env.dmg_dead * 100)] for k in range(env.en_n)]
    st = {"op": getattr(runner, "opname", "OP"), "step": runner.step_i, "losses": round(runner.losses(), 3),
          "squads": sq, "enemies": en,
          "pts": {"COMPLEXE": list(M.COMPLEXE), "CRETE": list(M.CRETE), "FLANC_O": list(M.FLANC_O), "FLANC_E": list(M.FLANC_E), "QRF": list(M.QRF_PT)},
          "llm": LLM_DECISION}
    try:
        _ostaff.makedirs(STAFF_DIR, exist_ok=True)
        _jstaff.dump(st, open(STAFF_DIR + "/state.json", "w"))
    except Exception:
        pass
'''

LLMBLOCK = '''    if a.llm:
        import officer_op
        _rep = ("Objectif TENU. Garnison urbaine d'environ 12 hommes massee dans la ville de Paros (bati dense), "
                "ecran de patrouilles ~8 hommes au nord. Pas de reserve mobile. Terrain : crete d'appui au nord-ouest "
                "qui domine la ville, flancs ouest et est praticables, approche qui monte depuis le sud.")
        _d = officer_op.decide(_rep)
        _raw = str(_d.get("manoeuvre", "M3")).upper()
        a.maneuver = next((mk for mk in M.MANEUVERS if mk in _raw), "M3")
        LLM_DECISION = {"posture": _d.get("posture"), "maneuver": a.maneuver,
                        "justification": _d.get("justification"), "allocation": _d.get("allocation")}
        print("[LLM] %s -> %s : %s" % (_d.get("posture"), a.maneuver, _d.get("justification")), flush=True)
    plan = M.MANEUVERS[a.maneuver](qrf=a.qrf)'''

if "STAFF_DUMP" in s:
    print("deja patche.")
else:
    s = s.replace("    import maneuvers as M\n", "    import maneuvers as M\n" + INJ, 1)
    s = s.replace('    p.add_argument("--out", type=str, default="ecole_visu.jsonl")',
                  '    p.add_argument("--out", type=str, default="ecole_visu.jsonl")\n    p.add_argument("--llm", action="store_true")\n    p.add_argument("--staff", action="store_true")', 1)
    s = s.replace("    plan = M.MANEUVERS[a.maneuver](qrf=a.qrf)", LLMBLOCK, 1)
    s = s.replace("    runner.run(max_steps=a.max_steps)",
                  "    runner.run(max_steps=a.max_steps, trace=(STAFF_DUMP if a.staff else None))", 1)
    open(f, "w").write(s)
    print("run_op_visual patche : --llm, --staff, STAFF_DUMP.")
