#!/usr/bin/env python3
"""Cartographie le MUR DE DENSITE : commander.pt vs nombre croissant de defenseurs."""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"; N = 4096
CK = "/home/younes/compose-embodiment/commander.pt"
class CNet(nn.Module):
    def __init__(self, obs=17, act=4, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1); self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)
net = CNet().to(DEV); net.load_state_dict(torch.load(CK, map_location=DEV)); net.eval()
print("=== MUR DE DENSITE : commander.pt vs D defenseurs retranches (n=%d) ===" % N, flush=True)
for D in [6, 8, 10, 12, 14, 16]:
    env = CommanderEnv(N, A=8, K=2, D=D, device=DEV, seed=1, max_steps=96)
    obs = env.reset(); ever = torch.zeros(N, dtype=torch.bool, device=DEV)
    lastinfo = None
    for t in range(env.maxT):
        with torch.no_grad(): mu, _ = net(obs)
        obs, r, done, info = env.step(mu.clamp(-1, 1).view(N, env.K, 2)); lastinfo = info
        ever = ever | info["secured"]
    print("  D=%2d | securise %3.0f%% | neutralise %3.0f%% | survie %3.0f%%" % (
        D, 100 * ever.float().mean().item(), 100 * lastinfo["neut"].float().mean().item(),
        100 * (lastinfo["alive"] / 8).mean().item()), flush=True)
print("=== FIN cartographie densite ===", flush=True)
