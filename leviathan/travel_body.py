#!/usr/bin/env python3
"""travel_body.py — le CORPS DE VOYAGE (R5 calme, reflex_travel_voyant.pt). En patrouille (0 menace),
pilote les agents avec ce corps (marche + contournement d'obstacles) AU LIEU du corps de combat qui les
fige. Perception d'obstacles = bâtiments/HESCO STATIQUES bakés UNE FOIS (pas de coût par tick)."""
import math, torch


class TravelBody:
    def __init__(self, ckpt="/home/younes/arma3-marl/leviathan/reflex_travel_voyant.pt",
                 device="cpu", D=8, field=180.0, speed=4.0):
        from reflex_travel_train import TravelNet
        self.net = TravelNet(12, D, 128).to(device)
        self.net.load_state_dict(torch.load(ckpt, map_location=device)); self.net.eval()
        self.dev = device; self.D = D; self.field = field; self.speed = speed
        ang = [k * 2 * math.pi / D for k in range(D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        self.obs = torch.zeros(0, 3, device=device)                 # obstacles statiques [M,3] (x,y,radius)
        self.last_pos = {}                                          # pour le flag stuck (par id agent)

    def set_obstacles(self, obstacles):
        """obstacles = liste (x,y,radius) bâtiments/HESCO. Bakée UNE fois via query_obstacles_sqf."""
        self.obs = (torch.tensor(obstacles, dtype=torch.float32, device=self.dev)
                    if obstacles else torch.zeros(0, 3, device=self.dev))

    @staticmethod
    def query_obstacles_sqf(radius=130):
        """SQF (à appeler UNE fois après _ensure_anchors) : bâtiments/murs près des FOB -> HARMATTAN_OBST [[x,y,r],...]."""
        return ('private _o = [];\n'
                '{ private _c = [_x#0, _x#1, 0];\n'
                '  { private _b = _x; private _bb = boundingBoxReal _b;\n'
                '    private _rr = ((abs ((_bb#1#0)-(_bb#0#0))) max (abs ((_bb#1#1)-(_bb#0#1))))/2;\n'
                '    _o pushBack [round ((getPosATL _b)#0), round ((getPosATL _b)#1), round _rr];\n'
                '  } forEach (nearestObjects [_c, ["House","Building","Wall","HBarrier","Land_HBarrier_Big_F","Land_Cargo_HQ_V1_F"], %d));\n'
                '} forEach HMT_FOB_ANCHORS;\n'
                '(format ["HARMATTAN_OBST %%1", _o]) call HMT_EMIT;\n' % radius)

    @torch.no_grad()
    def _perceive(self, pos, goals, idx):
        pos = torch.as_tensor(pos, dtype=torch.float32, device=self.dev)
        goals = torch.as_tensor(goals, dtype=torch.float32, device=self.dev)
        N = pos.shape[0]
        dg = goals - pos; d = dg.norm(dim=1, keepdim=True) + 1e-6; gdir = dg / d
        osense = torch.zeros(N, self.D, device=self.dev)
        if self.obs.shape[0] > 0:
            ox = self.obs[:, 0][None, :] - pos[:, 0][:, None]; oy = self.obs[:, 1][None, :] - pos[:, 1][:, None]
            od = torch.sqrt(ox ** 2 + oy ** 2 + 1e-6); edge = (od - self.obs[:, 2][None, :]).clamp(min=0)
            prox = (1 - edge / 60.0).clamp(0, 1)
            proj = ox[:, :, None] * self.DX[None, None, :] + oy[:, :, None] * self.DY[None, None, :]
            sect = proj.argmax(-1)
            osense.scatter_reduce_(1, sect, prox, reduce="amax", include_self=True)
        st = torch.zeros(N, device=self.dev)                        # stuck : n'a pas bougé depuis le tick précédent
        for k, i in enumerate(idx):
            lp = self.last_pos.get(i)
            if lp is not None and ((float(pos[k, 0]) - lp[0]) ** 2 + (float(pos[k, 1]) - lp[1]) ** 2) < 1.0:
                st[k] = 1.0
            self.last_pos[i] = (float(pos[k, 0]), float(pos[k, 1]))
        return torch.cat([gdir, (d / self.field).clamp(0, 1), osense, st[:, None]], dim=1)   # [N,12]

    @torch.no_grad()
    def velocity(self, pos, goals, idx):
        """pos/goals [N,2], idx = ids agents -> (vx, vy) listes. Le corps de VOYAGE décide la marche."""
        obs = self._perceive(pos, goals, idx)
        ml, _ = self.net(obs); mvi = ml.argmax(-1).clamp(0, self.D)
        z = torch.zeros(len(idx), device=self.dev)
        dx = torch.where(mvi > 0, self.DX[(mvi - 1).clamp(0, self.D - 1)], z)
        dy = torch.where(mvi > 0, self.DY[(mvi - 1).clamp(0, self.D - 1)], z)
        return (dx * self.speed).tolist(), (dy * self.speed).tolist()
