"""MultiArmaEnv — agrege M serveurs Arma (chacun = un ArmaVecEnv) et les pilote EN PARALLELE (threads).
Chaque serveur fait son aller-retour de pont pendant que les autres font le leur (l'attente libere le GIL)
-> debit ~ M x un seul serveur. Interface identique au toy : reset()->(N,A,O), step(a)->obs,rew,cost,done,info."""
import threading
import numpy as np

SB = "/mnt/data/harmattan-sandbox"


class MultiArmaEnv:
    def __init__(self, num_servers=4, per_server=48, max_steps=22, step_wait=0.7,
                 settle=0.6, spacing=400, acc=4.0, env_b1=0, env_macro=0):
        if env_macro:
            from arma_env_macro import ArmaEnvMacro as EnvCls
        elif env_b1:
            from arma_env_b1 import ArmaEnvB1 as EnvCls
        else:
            from arma_env_vec import ArmaVecEnv as EnvCls
        self.EnvCls = EnvCls
        self.envs = []
        for i in range(num_servers):
            mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % i
            log = SB + "/logs/server%d.out" % i
            self.envs.append(self.EnvCls(num_envs=per_server, mission=mis, log=log, seed=i,
                                        max_steps=max_steps, step_wait=step_wait, settle=settle,
                                        spacing=spacing, acc=acc))
        self.n_actions = self.envs[0].n_actions
        self.obs_dim = self.envs[0].obs_dim
        self.A = self.envs[0].A
        self.sizes = [e.N for e in self.envs]
        self.N = sum(self.sizes)
        self._splits = np.cumsum(self.sizes)[:-1]

    def _run_parallel(self, fns):
        results = [None] * len(self.envs)
        threads = []
        def wrap(i):
            results[i] = fns[i]()
        for i in range(len(self.envs)):
            t = threading.Thread(target=wrap, args=(i,)); t.start(); threads.append(t)
        for t in threads:
            t.join()
        return results

    def reset(self):
        res = self._run_parallel([(lambda e=e: e.reset()) for e in self.envs])
        return np.concatenate(res, axis=0)

    def step(self, actions):
        a = np.asarray(actions)
        parts = np.split(a, self._splits, axis=0)
        res = self._run_parallel([(lambda e=self.envs[i], p=parts[i]: e.step(p)) for i in range(len(self.envs))])
        obs = np.concatenate([r[0] for r in res], axis=0)
        rew = np.concatenate([r[1] for r in res], axis=0)
        cost = np.concatenate([r[2] for r in res], axis=0)
        done = np.concatenate([r[3] for r in res], axis=0)
        info = {"success": np.concatenate([r[4]["success"] for r in res]),
                "alive": np.concatenate([r[4]["alive"] for r in res]),
                "in_obj": np.concatenate([r[4]["in_obj"] for r in res])}
        return obs, rew, cost, done, info
