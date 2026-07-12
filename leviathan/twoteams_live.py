#!/usr/bin/env python3
"""twoteams_live.py — COMBAT COLLABORATIF, deux équipes d'AGENTS (plus de LAMBS).

Tout soldat est un agent : les FS ET les défenseurs tournent sur le MEME corps réflexe (reflex_r23wh),
piloté en batch par AgentSwarm. LAMBS coupé des deux côtés. Au-dessus : un commandant pose les buts
(FS -> noeuds à frapper ; défenseurs -> tenir leur FOB / MASSER sur les FS détectés). Le nombre de
défenseurs engagés ÉMERGE du dyn-sim (seuls les actifs proches des FS sont pilotés).

  --dry : boucle complète contre un pont SIMULÉ (positions synthétiques) -> valide la couture sans Arma.
  (live : à brancher sur le vrai serveur une fois prêt — même protocole que traque_reflex_live.)"""
import sys, math, argparse, random
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import torch
from agent_swarm import AgentSwarm

LEV = "/home/younes/arma3-marl/leviathan"
N_FS = 9; INS = (5250, 3050); D = 8


# ---------------- pont SIMULÉ (dry-run : un mini-Arma synthétique) ----------------
class MockBridge:
    """Rejoue un Arma plausible : FS qui avancent vers des noeuds, défenseurs en garnison qui s'activent
    au contact. Vérifie que toute la boucle (read->perceive->act->write) tient, sans serveur."""
    def __init__(self, n_fs, nodes, n_def_per_node=20):
        self.nodes = nodes
        self.fs = [[INS[0] + (i % 3) * 70 - 70, INS[1] + (i // 3) * 45, 1] for i in range(n_fs)]
        self.deff = []                                                  # [x,y,alive] par défenseur (idx = position dans la liste)
        for (nx, ny) in nodes:
            for _ in range(n_def_per_node):
                self.deff.append([nx + random.uniform(-40, 40), ny + random.uniform(-40, 40), 1])
        self.dvx = [0.0] * len(self.deff); self.dvy = [0.0] * len(self.deff)
        self.fvx = [0.0] * n_fs; self.fvy = [0.0] * n_fs
        self.t = 0

    def read_fs(self):
        return [[round(a[0]), round(a[1]), a[2]] for a in self.fs]

    def read_active_def(self, drange=500.0):                           # dyn-sim : défenseurs proches d'un FS
        out = []
        for i, d in enumerate(self.deff):
            if d[2] == 0: continue
            if any(math.hypot(d[0] - f[0], d[1] - f[1]) < drange for f in self.fs if f[2] == 1):
                out.append([i, round(d[0]), round(d[1])])
        return out

    def apply(self):                                                   # intègre les vitesses (EachFrame simulé) + tir
        for i, f in enumerate(self.fs):
            if f[2] == 0: continue
            f[0] += self.fvx[i] * 1.0; f[1] += self.fvy[i] * 1.0
        for i, d in enumerate(self.deff):
            if d[2] == 0: continue
            d[0] += self.dvx[i] * 1.0; d[1] += self.dvy[i] * 1.0
        # tir : un FS proche (<35m) d'un défenseur le neutralise parfois, et vice-versa
        for f in self.fs:
            if f[2] == 0: continue
            for d in self.deff:
                if d[2] == 1 and math.hypot(f[0] - d[0], f[1] - d[1]) < 35 and random.random() < 0.15: d[2] = 0
        for d in self.deff:
            if d[2] == 0: continue
            for f in self.fs:
                if f[2] == 1 and math.hypot(f[0] - d[0], f[1] - d[1]) < 30 and random.random() < 0.10: f[2] = 0
        self.t += 1


def synth_heightmap(HN=200, hres=7.5):
    yy, xx = torch.meshgrid(torch.arange(HN), torch.arange(HN), indexing="ij")
    HM = (8 * torch.sin(xx.float() / 11) * torch.cos(yy.float() / 9) + 4 * torch.sin(xx.float() / 5)).float()
    return HM, 0.0, 0.0, hres, HN


class _Body(torch.nn.Module):                                          # corps factice (dry) — remplacé par FightNet en live
    def __init__(self):
        super().__init__()
        self.b = torch.nn.Sequential(torch.nn.Linear(21, 64), torch.nn.Tanh())
        self.mv = torch.nn.Linear(64, D + 1); self.stc = torch.nn.Linear(64, 2); self.fire = torch.nn.Linear(64, D + 1); self.v = torch.nn.Linear(64, 1)
    def forward(self, o):
        z = self.b(o); return self.mv(z), self.stc(z), self.fire(z), self.v(z).squeeze(-1)


def run_dry(steps=40):
    random.seed(1); torch.manual_seed(1)
    nodes = [(random.uniform(1500, 6000), random.uniform(2500, 6000)) for _ in range(25)]   # 25 positions = ton reseau FOB (6 MAIN + 19 avant-postes)
    HM, hx0, hy0, hres, HN = synth_heightmap()
    body = _Body()                                                     # en live : FightNet + load reflex_r23wh_voyant
    fs_sw = AgentSwarm(body, HM, hx0, hy0, hres, HN, group_var="HMT_FS", enemy_side="east",
                       vx_var="HMT_VX", vy_var="HMT_VY", device="cpu")
    def_sw = AgentSwarm(body, HM, hx0, hy0, hres, HN, group_var="HMT_ALL", enemy_side="west",
                        vx_var="HMT_DVX", vy_var="HMT_DVY", device="cpu")
    mb = MockBridge(N_FS, nodes)
    per = max(1, len(mb.deff) // len(nodes))
    home = {i: nodes[min(i // per, len(nodes) - 1)] for i in range(len(mb.deff))}   # FOB d'origine de chaque défenseur
    fs_prone = [0.0] * N_FS

    print("=== DRY-RUN deux equipes d'agents (pont simule) | %d def. au total ===" % len(mb.deff))
    for step in range(steps):
        sf = mb.read_fs(); da = mb.read_active_def()                   # 1 read FS + 1 read defenseurs ACTIFS
        fs_alive = [a for a in sf if a[2] == 1]
        if not fs_alive: print("  [%02d] tous les FS tombes" % step); break
        fs_pos = [[a[0], a[1]] for a in sf]
        # --- FS : enemis = defenseurs actifs ; but = noeud assigne (ici : le plus proche vivant) ---
        en_for_fs = [[d[1], d[2]] for d in da]
        fs_goals = []
        for a in sf:
            cand = min(nodes, key=lambda n: math.hypot(a[0] - n[0], a[1] - n[1]))
            fs_goals.append([cand[0], cand[1]])
        obs, thr, cdir = fs_sw.perceive(fs_pos, en_for_fs, fs_prone)
        mv, stc, frt = fs_sw.act(obs)
        fvx, fvy = fs_sw.decide_velocity(fs_pos, mv, thr, cdir, fs_goals, assault=True, speed=8.0)
        fs_prone = [float(x) for x in stc.tolist()]
        for i in range(N_FS):
            mb.fvx[i] = float(fvx[i]) if sf[i][2] == 1 else 0.0; mb.fvy[i] = float(fvy[i]) if sf[i][2] == 1 else 0.0
        # --- DEFENSEURS (actifs) : enemis = FS ; but = MASSER sur le FS le plus proche, sinon tenir le FOB ---
        if da:
            d_idx = [d[0] for d in da]; d_pos = [[d[1], d[2]] for d in da]
            d_goals = []
            for (di, dx, dy) in da:
                near = min(fs_alive, key=lambda f: math.hypot(dx - f[0], dy - f[1]))
                if math.hypot(dx - near[0], dy - near[1]) < 250: d_goals.append([near[0], near[1]])   # MASSE sur le FS
                else: d_goals.append([home[di][0], home[di][1]])                                       # tient le FOB
            d_prone = [0.0] * len(da)
            obs2, thr2, cdir2 = def_sw.perceive(d_pos, fs_pos, d_prone)
            mv2, stc2, frt2 = def_sw.act(obs2)
            dvx, dvy = def_sw.decide_velocity(d_pos, mv2, thr2, cdir2, d_goals, assault=False, speed=5.0)  # base de feu
            for k, di in enumerate(d_idx):
                mb.dvx[di] = float(dvx[k]); mb.dvy[di] = float(dvy[k])
            write_sqf = def_sw.write_velocity_sqf(torch.tensor([mb.dvx[i] for i in d_idx]), torch.tensor([mb.dvy[i] for i in d_idx]))
            assert write_sqf.startswith("HMT_DVX ="), "write SQF malforme"
        mb.apply()
        nfs = sum(a[2] for a in mb.read_fs()); ndef = sum(1 for d in mb.deff if d[2] == 1); nact = len(da)
        if step % 5 == 0 or step == steps - 1:
            print("  [%02d] FS %d/9 | def. actifs %d (sur %d vivants) | tirent FS=%d def=%d"
                  % (step, nfs, nact, ndef, len(fs_sw.bearings(frt, thr)[0]), len(def_sw.bearings(frt2, thr2)[0]) if da else 0))
    print("=== DRY-RUN OK : boucle deux-equipes-d'agents complete, read->perceive->act->write sans erreur ===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--steps", type=int, default=40)
    a = ap.parse_args()
    if a.dry: run_dry(a.steps)
    else: print("Mode live : a brancher sur le serveur (ArmaBridge). Lance --dry pour valider la couture.")
