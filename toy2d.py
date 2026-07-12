"""Harmattan — simulateur-jouet 2D vectorisé (v0).

Dec-POMDP miniature : 4 agents coopératifs, un objectif à sécuriser, des zones de
danger, observation partielle. Vectorisé sur N mondes en parallèle (NumPy) pour
produire de gros lots d'expérience à nourrir au réseau sur la RTX 3090.

Actions (par agent) : 0=rester, 1=haut, 2=bas, 3=gauche, 4=droite.
Récompenses : +1 d'équipe quand l'objectif est sécurisé (>=3 agents vivants dedans),
shaping par potentiel (rapprochement), -0.01/pas. Le COÛT (pertes) est un canal séparé
(prêt pour la contrainte CMDP / le curseur lambda).
"""
import numpy as np


class VectorizedToy2D:
    def __init__(self, num_envs=1024, grid=12, n_agents=4, vision=4,
                 max_steps=100, p_hit=0.15, secure_count=3, gamma=0.99, seed=0):
        self.N, self.G, self.A = num_envs, grid, n_agents
        self.vision, self.max_steps = vision, max_steps
        self.p_hit, self.secure_count, self.gamma = p_hit, secure_count, gamma
        self.rng = np.random.default_rng(seed)
        self.obj_lo = np.array([grid - 2, grid - 2])
        self.obj_hi = np.array([grid - 1, grid - 1])
        self.obj_center = (self.obj_lo + self.obj_hi) / 2.0
        self.danger = np.array([[5, 5], [5, 6], [6, 5], [6, 6], [4, 8], [8, 4]])
        self.moves = np.array([[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]])
        self.n_actions = 5
        self.obs_dim = 11
        self._alloc()

    def _alloc(self):
        self.pos = np.zeros((self.N, self.A, 2), dtype=np.int32)
        self.alive = np.ones((self.N, self.A), dtype=bool)
        self.t = np.zeros(self.N, dtype=np.int32)
        self.done = np.zeros(self.N, dtype=bool)
        self.success = np.zeros(self.N, dtype=bool)
        self.prev_phi = np.zeros(self.N, dtype=np.float32)
        self.reset()

    def reset(self, mask=None):
        if mask is None:
            mask = np.ones(self.N, dtype=bool)
        idx = np.where(mask)[0]
        gs = int(np.ceil(np.sqrt(self.A)))                              # bloc carre depuis (1,1), A quelconque
        starts = np.array([[1 + k // gs, 1 + k % gs] for k in range(self.A)], dtype=np.int32)
        starts = np.clip(starts, 0, self.G - 1)                          # (A=4 -> identique a avant)
        self.pos[idx] = starts[None, :, :]
        self.alive[idx] = True
        self.t[idx] = 0
        self.done[idx] = False
        self.success[idx] = False
        self.prev_phi[idx] = self._phi()[idx]
        return self._get_obs()

    def _phi(self):
        d = np.abs(self.pos - self.obj_center[None, None, :]).sum(-1)
        alive = self.alive.astype(np.float32)
        mean_d = (d * alive).sum(1) / np.maximum(alive.sum(1), 1.0)
        return (-mean_d / (2 * self.G)).astype(np.float32)

    def _in_obj(self):
        ge = (self.pos >= self.obj_lo[None, None, :]).all(-1)
        le = (self.pos <= self.obj_hi[None, None, :]).all(-1)
        return ge & le & self.alive

    def step(self, actions, auto_reset=True):
        delta = self.moves[actions]
        self.pos = np.clip(self.pos + delta * self.alive[..., None], 0, self.G - 1)
        on_danger = np.zeros((self.N, self.A), dtype=bool)
        for d in self.danger:
            on_danger |= (self.pos[..., 0] == d[0]) & (self.pos[..., 1] == d[1])
        on_danger &= self.alive
        hit = on_danger & (self.rng.random((self.N, self.A)) < self.p_hit)
        casualties = hit.sum(1).astype(np.float32)
        self.alive &= ~hit
        secured = self._in_obj().sum(1) >= self.secure_count
        newly = secured & ~self.success
        self.success |= secured
        self.t += 1
        wiped = ~self.alive.any(1)
        self.done = self.success | (self.t >= self.max_steps) | wiped
        phi = self._phi()
        shaping = self.gamma * phi - self.prev_phi
        self.prev_phi = phi
        reward = newly.astype(np.float32) + shaping - 0.01
        cost = casualties
        info = {"success": self.success.copy(), "casualties": casualties}
        done_out = self.done.copy()
        if auto_reset and self.done.any():
            self.reset(self.done)
        return self._get_obs(), reward, cost, done_out, info

    def _get_obs(self):
        N, A, G = self.N, self.A, self.G
        pos = self.pos.astype(np.float32)
        own = pos / (G - 1)
        dir_obj = (self.obj_center[None, None, :] - pos) / G
        alive_f = self.alive.astype(np.float32)[..., None]
        dgr = self.danger.astype(np.float32)
        obs = np.zeros((N, A, self.obs_dim), dtype=np.float32)
        for i in range(A):
            p = pos[:, i, :]
            others = [j for j in range(A) if j != i]
            rel = pos[:, others, :] - p[:, None, :]
            dist = np.abs(rel).sum(-1)
            vis = (self.alive[:, others] & (dist <= self.vision)).astype(np.float32)
            cnt = vis.sum(1)
            cen = (rel * vis[..., None]).sum(1) / np.maximum(cnt[:, None], 1.0) / G
            reld = dgr[None, :, :] - p[:, None, :]
            dd = np.abs(reld).sum(-1)
            k = dd.argmin(1)
            nd_rel = reld[np.arange(N), k, :] / G
            nd_vis = (dd[np.arange(N), k] <= self.vision).astype(np.float32)[:, None]
            obs[:, i, :] = np.concatenate(
                [own[:, i, :], dir_obj[:, i, :], alive_f[:, i, :], cen,
                 (cnt / A)[:, None], nd_rel * nd_vis, nd_vis], axis=1)
        return obs


if __name__ == "__main__":
    import time
    env = VectorizedToy2D(num_envs=1024, seed=0)
    obs = env.reset()
    print(f"Mondes parallèles : {env.N} | agents : {env.A} | obs/agent : {env.obs_dim}")
    print(f"forme du lot d'observations : {obs.shape}  (mondes, agents, obs)")
    rng = np.random.default_rng(1)
    steps = 2000
    t0 = time.time()
    tot_cost = tot_rew = 0.0
    for _ in range(steps):
        a = rng.integers(0, env.n_actions, size=(env.N, env.A))
        obs, r, c, d, info = env.step(a)
        tot_cost += float(c.sum())
        tot_rew += float(r.mean())
    dt = time.time() - t0
    total = steps * env.N
    print(f"\n{steps} pas x {env.N} mondes = {total:,} transitions en {dt:.2f}s")
    print(f"DEBIT : {total / dt:,.0f} transitions/seconde")
    print(f"recompense moyenne/pas : {tot_rew / steps:+.4f} | pertes cumulees (aleatoire) : {tot_cost:,.0f}")
    try:
        import torch
        g = torch.as_tensor(obs).to("cuda:0")
        print(f"\nPont GPU OK : lot d'obs sur {torch.cuda.get_device_name(0)} | tensor {tuple(g.shape)} ({g.device})")
    except Exception as e:
        print("Pont GPU non teste :", e)
