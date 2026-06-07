"""run_op_visual — OPÉRATION TRACÉE dans la mission HMT-EcoleDeGuerre.Altis. Exécute UNE manœuvre du
répertoire (maneuvers.py) comme run_maneuver, mais en dessinant l'op sur la carte en temps réel via la
couche hmt_trace.sqf : points du théâtre, axes d'effort de la phase courante, trails des escouades,
ennemis vivants/détruits, HUD (nom de baptême + phase + pertes). Rejoindre le serveur visuel (hmt-visu.sh,
port 2302) avec le client Arma pour REGARDER l'op se dérouler — ou la capturer pour un clip Harmattan.
Chaque run est baptisé (baptism.py) et le nom est écrit dans le jsonl -> données traçables op par op."""
import time, argparse, json, os, glob, re
import numpy as np
import torch
from op_arma import OpArma, OperationRunner
from arma_bridge import ArmaBridge
from train_koth_gpu import Net
from baptism import op_name
import maneuvers as M

SB = "/mnt/data/harmattan-sandbox"
DEV = "cuda:0"
MISSION = SB + "/arma3server/mpmissions/HMT-EcoleDeGuerre.Altis"
LOG = SB + "/logs/visu.out"
# mode --editor : la mission tourne dans le CLIENT (preview Eden), pas sur un serveur dédié.
# Pont via la copie Eden de la mission (drive_c lisible des deux côtés — acquis C.4), état lu dans le RPT client.
EDEN_MISSION = SB + "/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser/Documents/Arma 3/missions/HMT-EcoleDeGuerre.Altis"
RPT_DIR = SB + "/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser/AppData/Local/Arma 3"
DLL_BRIDGE = SB + "/Steam/steamapps/compatdata/107410/pfx/drive_c/hmt_bridge"   # C:\hmt_bridge lu par hmt_ext_x64.dll
# Spawns SECS pour le mode visuel UNIQUEMENT (mesuré in-game 07/06 : les spawns de maneuvers.py
# y=15560-15740 sont DANS L'EAU — rivage entre 15700 et 15800 ; surfaceIsWater=false sur ces 4 points).
# ⚠️ maneuvers.py reste INTOUCHÉE : ses spawns mouillés sont ceux des 112 ops de la table (comparabilité) ;
# le déplacement à terre se fera pour TOUTE la chaîne à la table v3, avec le fix QRF, en re-mesurant tout.
VISU_SPAWNS = {"SQ_APPUI": (14920, 15830), "SQ_A_OUEST": (15080, 15830),
               "SQ_A_EST": (15290, 15900), "SQ_RESERVE": (15000, 15820)}
# LZ de mesure (15180,15620) = OCÉAN (vu in-game par Younes 07/06) -> LZ visuelle au sec, même axe sud-est
# (rivage local ~y=15750-15800 ; les voisins x=15080 et x=15290 sont secs à y=15830).
VISU_LZ = (15180, 15840)

# ---- PROFILS ENNEMIS (mode visuel ; demande Younes 07/06 : « rendre les IA hardcore, 50-90 ennemis ») ----
# mult échelonne garnison+patrouilles, qrf_mult la contre-attaque ; skill+hunt = niveau « pro » :
# sous-compétences montées (visée/détection/sang-froid) + boucle de CHASSE (un groupe qui acquiert un
# contact convertit sa patrouille en seek-and-destroy — fini l'ennemi statique qui attend la mort).
# ⚠️ Gradué exprès : à 1:3 contre des pros, l'attente doctrinale est 0 % partout (effet plancher déjà
# documenté au palier 1) — l'intéressant est le cran où le classement des manœuvres bascule.
ENEMY_PROFILES = {
    "normal":    dict(mult=1.0, qrf_mult=1.0, pro=False),   # 20 + QRF 8  = 28 (la table)
    "pro":       dict(mult=1.5, qrf_mult=1.5, pro=True),    # 30 + QRF 12 = 42
    "hardcore":  dict(mult=2.2, qrf_mult=2.0, pro=True),    # 44 + QRF 16 = 60
    "nightmare": dict(mult=3.0, qrf_mult=3.0, pro=True),    # 60 + QRF 24 = 84
}
PRO_SKILL_SQF = (
    '{ _x setSkill ["aimingAccuracy", 0.75]; _x setSkill ["aimingSpeed", 0.9];'
    ' _x setSkill ["aimingShake", 0.9]; _x setSkill ["spotDistance", 0.95];'
    ' _x setSkill ["spotTime", 0.9]; _x setSkill ["courage", 1]; _x setSkill ["commanding", 1];'
    ' _x setSkill ["general", 1]; } forEach HMT_EN;\n')
HUNT_SQF = (
    'HMT_HUNT = true;\n'
    '[] spawn {\n'
    '  while {HMT_HUNT} do {\n'
    '    {\n'
    '      private _g = _x;\n'
    '      private _best = objNull; private _bk = 1.5;\n'
    '      { private _k = _g knowsAbout _x; if (_k > _bk) then { _bk = _k; _best = _x; }; }\n'
    '        forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '      if (!isNull _best && {({alive _x} count units _g) > 0}) then {\n'
    '        while {count waypoints _g > 0} do { deleteWaypoint [_g, 0] };\n'
    '        private _wp = _g addWaypoint [getPos _best, 30];\n'
    '        _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL"; _g setBehaviour "COMBAT";\n'
    '      };\n'
    '    } forEach (allGroups select { side _x == east });\n'
    '    sleep 30;\n'
    '  };\n'
    '};\n')


def scaled_garrison(mult):
    """M.GARRISON échelonné : mêmes positions/rayons, effectifs xmult (la géométrie de défense est conservée)."""
    return [(x, y, max(1, round(n * mult)), rad) for (x, y, n, rad) in M.GARRISON]


def metrics_dyn(env, runner, garrison):
    """metrics de run_maneuver, mais avec effectifs DYNAMIQUES (les profils ennemis cassent les tranches 12/8/8)."""
    eal = env.en_alive()
    gn = garrison[0][2]; pn = sum(g[2] for g in garrison[1:])
    garr_a = int(eal[0:gn].sum()); pat_a = int(eal[gn:gn + pn].sum()); qrf_a = int(eal[gn + pn:].sum())
    qrf_live = "qrf" in runner.qrf_done
    qrf_n = max(0, eal.size - gn - pn)
    alive_tot = sum(int(env.alive(si).sum()) for si in range(env.S))
    pertes = 1 - alive_tot / sum(env.sizes)
    eff_total = gn + pn + (qrf_n if qrf_live else 0)
    reste = garr_a + pat_a + qrf_a
    ennemi_brise = (garr_a == 0) and ((1 - reste / max(eff_total, 1)) >= 0.7)
    mil = bool(ennemi_brise and pertes <= 0.5)
    return {"mil": mil, "pertes": float(pertes), "garr_pris": bool(garr_a == 0),
            "qrf_spawn": bool(qrf_live), "qrf_reste": qrf_a, "ennemis_total": int(eff_total)}


def _swap_point(obj, old, new):
    """Remplace récursivement un point (tuple/liste == old) dans le plan-dict — goals des orders ET
    conditions squad_at imbriquées. Ne touche pas maneuvers.py : correction du théâtre visuel seulement."""
    if isinstance(obj, (tuple, list)):
        if tuple(obj) == tuple(old):
            return type(obj)(new)
        return type(obj)(_swap_point(x, old, new) for x in obj)
    if isinstance(obj, dict):
        return {k: _swap_point(v, old, new) for k, v in obj.items()}
    return obj


class EditorBridge(ArmaBridge):
    """Pont mode éditeur (preview Eden, solo) — protocole v2 SANS ÉTAT CACHÉ, apparié à
    harmattan_actuator_ext.sqf v2. Trois invariants, chacun né d'un échec mesuré :
    (1) dossier = C:\\hmt_bridge lu par la DLL (preprocessFile gèle son index en solo — acquis C.4) ;
    (2) on ne SUPPRIME jamais et on ne repart JAMAIS de 1 : compteur = max(fichiers présents)+1, et
        l'actuateur rattrape en sondant 1,2,3... au démarrage (la re-synchro v1 par sentinelle cmd_1
        a resetté le compteur en plein vol — 3 ops tuées) ;
    (3) écriture ATOMIQUE tmp+rename : l'actuateur ne peut pas lire un fichier à moitié écrit
        (cmd_7 retrouvé à 0 octet = course écriture/lecture)."""

    def __init__(self, log):
        self.bridge = DLL_BRIDGE; self.log = log
        os.makedirs(self.bridge, exist_ok=True)
        nums = [int(m.group(1)) for f in os.listdir(self.bridge)
                for m in [re.match(r"cmd_(\d+)\.sqf$", f)] if m]
        self._n = max(nums) if nums else 0

    def send(self, sqf, wait=True, timeout=600):
        # timeout long : Arma solo se met en PAUSE à la perte de focus (alt-tab) -> le pont gèle le temps
        # de la pause ; 30 s tuait l'op dès que Younes passait au terminal. Remède définitif : -noPause.
        # GARDE : un fichier VIDE est indistinguable d'un fichier absent pour l'actuateur -> deadlock.
        # (Cause réelle des 4 ops mortes : obs lue dans un RPT en retard -> 0 unité vivante -> step sans
        # ordres -> send("") -> cmd_N à 0 octet -> l'actuateur attend pour toujours.)
        if not sqf.strip():
            sqf = 'diag_log "HARMATTAN_NOOP (step vide - obs en retard)";'
        self._n += 1; n = self._n
        p = os.path.join(self.bridge, "cmd_%d.sqf" % n)
        tmp = p + ".tmp"
        with open(tmp, "w") as f:
            f.write(sqf)
        os.replace(tmp, p)                       # atomique : jamais de lecture partielle
        if wait:
            t0 = time.time()
            while time.time() - t0 < timeout:
                if self._last_recv() >= n:
                    return n
                time.sleep(0.2)
            raise TimeoutError("cmd %d non recue — la preview Eden est-elle lancee et toujours ouverte ?" % n)
        return n
SHORT = {"SQ_APPUI": "APPUI", "SQ_A_OUEST": "OUEST", "SQ_A_EST": "EST", "SQ_RESERVE": "RES"}


def _a(s):
    """SQF-safe : ASCII pur (les accents cassent l'encodage des cmd_N.sqf côté Arma)."""
    return str(s).encode("ascii", "ignore").decode()


class TracedRunner(OperationRunner):
    """OperationRunner + couche visuelle : chaque jalon du journal (OP_START/PHASE/SITREP/CONTINGENCE/
    QRF/OP_END) émet aussi le SQF de traçage correspondant. Le traçage ne doit JAMAIS casser l'op
    (try/except englobant) — c'est une couche d'observation, pas de contrôle."""

    def __init__(self, env, net, plan, opname, lz=None, **kw):
        super().__init__(env, net, plan, **kw)
        self.opname = opname
        self.lz = lz or M.LZ   # le marqueur carte doit pointer la LZ réellement jouée (visuelle ou mesure)

    def centroid(self, si):
        al = self.env.alive(si)
        if not al.any():
            return None
        return [float(self.env.px[si][al].mean()), float(self.env.py[si][al].mean())]

    def sqf(self, code):
        self.env.b.send(code, wait=True)

    def jlog(self, kind, **kw):
        super().jlog(kind, **kw)
        try:
            self._trace(kind, kw)
        except Exception as e:
            print("[trace] ignoré: %s %s" % (type(e).__name__, e), flush=True)

    def _hud(self, line2):
        return '["OP %s - %s", "%s"] call HMT_fnc_hud;' % (_a(self.opname), _a(self.plan["name"]), _a(line2))

    def _trace(self, kind, kw):
        if kind == "OP_START":
            pts = [("COMPLEXE", M.COMPLEXE, "mil_objective", "ColorRed", "COMPLEXE"),
                   ("CRETE", M.CRETE, "mil_triangle", "ColorBlue", "CRETE"),
                   ("LZ", self.lz, "mil_pickup", "ColorGreen", "LZ"),
                   ("QRF", M.QRF_PT, "mil_unknown", "ColorRed", "QRF?")]
            code = '["%s"] call HMT_fnc_traceStart;\n' % _a(self.opname)
            code += "\n".join('["%s", [%d,%d], "%s", "%s", "%s"] call HMT_fnc_point;'
                              % (i, p[0], p[1], t, c, x) for i, p, t, c, x in pts)
            code += "\n" + self._hud("debut d'operation")
            # insertion : le joueur-observateur est pose AU SOL a 10 m de l'escouade d'assaut OUEST
            # (demande Younes — il suit l'op au contact ; F5 a tout moment pour la vue du dessus)
            code += ('\nif (!isNull player) then { private _a = missionNamespace getVariable ["SQ_A_OUEST", []];'
                     ' private _v = _a select { !isNull _x && {alive _x} };'
                     ' if (count _v > 0) then { call HMT_fnc_camKill;'
                     ' player setPosATL ((getPosATL (_v select 0)) vectorAdd [10, -5, 0]);'
                     ' hintSilent "Insere avec SQ A-OUEST — suis-les ! (F5 = vue du dessus)"; }; };')
            self.sqf(code)
        elif kind == "PHASE":
            lines = []
            for sq, (goal, stance) in kw["orders"].items():
                si = self.env.squads.index(sq)
                c = self.centroid(si)
                if c is None:
                    continue
                col = ["ColorBlue", "ColorGreen", "ColorOrange", "ColorYellow"][si]
                lines.append('["%s", [%d,%d], [%d,%d], "%s", "%s"] call HMT_fnc_axis;'
                             % (sq, c[0], c[1], goal[0], goal[1], col, SHORT.get(sq, sq)))
            lines.append(self._hud("phase %s | pertes %d%%" % (_a(kw["name"]), 100 * kw.get("losses", 0))))
            self.sqf("\n".join(lines))
        elif kind == "SITREP":
            if self.step_i % 15 == 0:   # throttle : 1 cmd HUD / 15 steps (l'actuateur a une course rare à haut débit)
                self.sqf(self._hud("phase %s | step %d | pertes %d%% | ennemis %d"
                                   % (_a(kw["phase"]), self.step_i, 100 * kw.get("losses", 0), kw.get("ennemis", -1))))
        elif kind == "CONTINGENCE":
            cs = [c for c in (self.centroid(si) for si in range(self.env.S)) if c]
            pos = [sum(c[0] for c in cs) / len(cs), sum(c[1] for c in cs) / len(cs)] if cs else list(M.COMPLEXE)
            self.sqf('["c%d", [%d,%d], "%s"] call HMT_fnc_event;\n%s'
                     % (self.step_i, pos[0], pos[1], _a(kw["raison"]),
                        self._hud("CONTINGENCE -> %s" % _a(kw["goto"]))))
        elif kind == "QRF":
            self.sqf('["qrf", [%d,%d], "QRF !"] call HMT_fnc_event;' % (M.QRF_PT[0], M.QRF_PT[1]))
        elif kind == "OP_END":
            verdict = "SUCCES" if kw.get("succes") else "ECHEC"
            self.sqf(self._hud("%s | steps %d | pertes %d%%" % (verdict, kw.get("steps", 0), 100 * kw.get("losses", 0)))
                     + "\ncall HMT_fnc_traceStop;")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--maneuver", type=str, default="M2", choices=list(M.MANEUVERS.keys()))
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--qrf", type=str, default="inf")
    p.add_argument("--max_steps", type=int, default=500)
    p.add_argument("--name", type=str, default="", help="nom de bapteme (defaut: baptism.op_name)")
    p.add_argument("--out", type=str, default="ecole_visu.jsonl")
    p.add_argument("--editor", action="store_true",
                   help="piloter la mission jouee dans le CLIENT (preview Eden) au lieu du serveur dedie")
    p.add_argument("--speed", type=float, default=1.0,
                   help="acceleration du temps en mode editeur (1 = temps reel, 4 = cadence de la mesure)")
    p.add_argument("--enemy", type=str, default="normal", choices=list(ENEMY_PROFILES.keys()),
                   help="profil ennemi (mode editeur) : normal 28 | pro 42 | hardcore 60 | nightmare 84")
    a = p.parse_args()
    name = a.name or op_name(a.maneuver, a.seed)

    mission, log = MISSION, LOG
    if a.editor:
        rpts = sorted(glob.glob(RPT_DIR + "/*.rpt"), key=os.path.getmtime)
        if not rpts:
            raise SystemExit("aucun RPT client — lancer Arma 3 et entrer en preview Eden d'abord")
        mission, log = EDEN_MISSION, rpts[-1]
        print("[editor] pont DLL: %s\n[editor] rpt    : %s" % (DLL_BRIDGE, log), flush=True)

    brain = Net(10, 4, 512, 3).to(DEV)
    brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
    plan = M.MANEUVERS[a.maneuver](qrf=a.qrf)

    print("=== OP %s — %s (visuelle, mission HMT-EcoleDeGuerre, seed %d) ===" % (name, plan["name"], a.seed), flush=True)
    env = OpArma(squads=M.SQUADS, mission=mission, log=log, move=36, seed=a.seed)
    spawns, garrison = M.SPAWNS, M.GARRISON
    prof = ENEMY_PROFILES[a.enemy]
    if a.editor:
        env.b = EditorBridge(log)   # remplace le pont fichier par le pont socket (même API send/read)
        spawns = VISU_SPAWNS        # spawns au sec (les spawns de mesure sont dans l'eau — voir VISU_SPAWNS)
        # vitesse : la mesure headless tourne à setAccTime 4 (injouable à l'œil). --speed 1 = temps réel.
        # step_wait compense (4 s-jeu de marche par décision dans les DEUX cas) -> mêmes dynamiques,
        # même nombre de steps que la table ; seul le temps-mur change (~40 min à 1x, ~10 min à 4x).
        env.acc = float(a.speed)
        env.step_wait = 4.0 / float(a.speed)
        plan = _swap_point(plan, M.LZ, VISU_LZ)   # exfil au sec (la LZ de mesure est dans l'océan)
        # profil ennemi : effectifs échelonnés + QRF échelonnée (wrapper) ; pro/hunt envoyés post-spawn
        garrison = scaled_garrison(prof["mult"])
        if prof["qrf_mult"] != 1.0:
            _oq, _oqm = env.spawn_qrf, env.spawn_qrf_mech
            env.spawn_qrf = lambda x, y, n, t: _oq(x, y, max(1, round(n * prof["qrf_mult"])), t)
            env.spawn_qrf_mech = lambda x, y, n, t: _oqm(x, y, max(1, round(n * prof["qrf_mult"])), t)
        # purge du théâtre : les unités orphelines d'une op précédente (morte ou finie) polluent la preview
        env.b.send("HMT_HUNT = false; { if (_x != player) then { deleteVehicle _x }; } forEach allUnits; "
                   "{ deleteVehicle _x } forEach vehicles;", wait=True)
        print("[enemy] profil %s : garnison+patrouilles %d, QRF x%.1f, pro=%s"
              % (a.enemy, sum(g[2] for g in garrison), prof["qrf_mult"], prof["pro"]), flush=True)
    env.spawn(spawns, garrison)
    if a.editor and prof["pro"]:
        env.b.send(PRO_SKILL_SQF + HUNT_SQF, wait=True)   # compétences pro + boucle de chasse (ennemi offensif)
    runner = TracedRunner(env, brain, plan, opname=name, lz=(VISU_LZ if a.editor else None),
                          log_path="op_journal_visu.jsonl", verbose=True)
    t0 = time.time()
    runner.run(max_steps=a.max_steps)
    m = metrics_dyn(env, runner, garrison)
    rec = {"op": name, "man": a.maneuver, "seed": a.seed, "enemy": a.enemy, "dt": round(time.time() - t0, 1), **m}
    with open(a.out, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("[OP %s] %s" % (name, rec), flush=True)
