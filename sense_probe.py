"""sense_probe — VALIDATION ISOLEE de la coque de couvert (l'enveloppe spatiale).
On pose 1 soldat, on lance un eventail de K rayons horizontaux autour de lui (repere CORPS),
chaque rayon renvoie la distance au 1er obstacle. On verifie : pres des batiments -> rayons COURTS
vers eux ; en terrain degage -> tous longs. args: server_idx
"""
import time, re, sys
from op_arma import OpArma
import paros as M

SB = "/mnt/data/harmattan-sandbox"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
K = 12          # nb de rayons (1 tous les 30 deg)
R = 15          # portee de detection du couvert (m)

env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=7)

# coque de couvert : eventail de rayons depuis ~hauteur poitrine, en repere corps (0=devant, sens horaire)
SHELL = (
    'private _u = AV select 0;'
    'private _o = getPosASL _u; _o set [2, (_o#2) + 0.9];'        # ~poitrine, repere ASL (robuste a la posture)
    'private _s = "";'
    'for "_i" from 0 to ' + str(K - 1) + ' do {'
    '  private _a = _i * ' + str(360 // K) + ';'
    '  private _dir = _u vectorModelToWorld [sin _a, cos _a, 0];'
    '  private _to = _o vectorAdd (_dir vectorMultiply ' + str(R) + ');'
    '  private _h = lineIntersectsSurfaces [_o, _to, _u];'
    '  private _d = if (count _h == 0) then {' + str(R) + '} else {_o distance ((_h select 0) select 0)};'
    '  _s = _s + format ["%1 ", round _d];'
    '};'
    'diag_log format ["SHELL %1", _s];'
    'private _p = getPosATL _u;'
    'private _nb = nearestObjects [_p, ["House","Building"], ' + str(R + 5) + '];'
    'diag_log format ["NEARB %1 batiments<%2m", count _nb, ' + str(R + 5) + '];'
    'if (count _nb > 0) then { private _b = _nb select 0; diag_log format ["NEARESTB %1 m, cap %2",'
    ' round (_u distance _b), round (_u getDir _b)]; };'
)


def probe(label, spot):
    env.spawn({"AV": spot}, [])
    time.sleep(2)
    ls = env._query(SHELL, settle=0.25)
    shell = None; nearb = None; nb = None
    for l in ls:
        m = re.search(r"SHELL ([\d\. ]+)", l)
        if m:
            shell = [int(float(x)) for x in m.group(1).split()]
        if "NEARB" in l:
            nearb = l.strip().split("NEARB", 1)[1].strip()
        if "NEARESTB" in l:
            nb = l.strip().split("NEARESTB", 1)[1].strip()
    print("\n===== %s @ (%d,%d) =====" % (label, spot[0], spot[1]))
    if shell is None:
        print("  PAS DE LECTURE (shell None)")
        return
    dirs = ["DEV", "DAV-D", "D", "ARR-D", "ARR", "ARR-G", "G", "AV-G"]  # approx pour K=12 on annote tous
    print("  coque (m, 0=devant, horaire, 1 tous les %d deg):" % (360 // K))
    print("   " + "  ".join("%3d" % d for d in shell))
    near = [(i * (360 // K), d) for i, d in enumerate(shell) if d < R]
    print("  COUVERT detecte (<%dm) : %s" % (R, near if near else "AUCUN (terrain degage)"))
    print("  verite-terrain batiments : %s | + proche : %s" % (nearb, nb))


# 1) au COMPLEXE (batiments -> doit detecter du couvert) ; 2) zone degagee (-180 sud -> rien)
probe("COMPLEXE (couvert attendu)", (M.COMPLEXE[0], M.COMPLEXE[1]))
probe("DEGAGE sud (rien attendu)", (M.COMPLEXE[0], M.COMPLEXE[1] - 180))
print("\nPROBE FINI", flush=True)
