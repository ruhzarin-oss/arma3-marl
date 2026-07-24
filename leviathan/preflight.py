#!/usr/bin/env python3
"""preflight.py — FIXTURE anti-invalidateur-silencieux (reco Fable). À lancer AVANT tout déploiement Arma.
Compare la distribution des 17 obs entre l'ENTRAÎNEMENT (sandbox) et le DÉPLOIEMENT (Arma live), feature par feature.
HURLE si une feature est constante au training mais varie live (bug #2 = feature couvert), ou sort des bornes vues.
(Le 2e volet, l'oracle « ce banc est-il gagnable ? », est déjà `corps_arma.py --oracle`.)
Prérequis : WEST + EAST déjà spawnés sur Arma (spawn_hard_east + corps_arma setup)."""
import sys, time, math, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import torch
from corps import mkenv, timid
import shamal_arma as SH
from native_bridge import NativeBridge

FEAT = ["relx", "rely", "-relx", "-rely", "alive", "dcov", "los", "nd", "suf0", "suf1", "adx", "ady", "asup", "tf", "post_UP", "post_CROUCH", "post_PRONE"]
FOB = "3253,2984"


@torch.no_grad()
def sandbox_stats(steps=12):
    e = mkenv(256, 7); obs = e.reset(); buf = []
    for _ in range(steps):
        a = timid(e); buf.append(obs.reshape(-1, 17)); obs, _, _, _ = e.step(a)
    O = torch.cat(buf, 0).cpu().numpy()
    return O.min(0), O.max(0), O.std(0)


def live_stats(fx, fy, ticks=6):
    b = NativeBridge(port=5816); buf = []
    prev = [0.0] * 60; sup = [False] * 60
    for _ in range(ticks):
        r = b.query("call HMT_SHAMAL_SENSE;", r"HARMATTAN_SHS (.+)", want=1, timeout=12)
        if not r: time.sleep(1); continue
        rows = SH.parse_sense(r[-1].group(1))
        if not rows: time.sleep(1); continue
        n = len(rows); targets = [(fx, fy)] * n
        buf.append(SH.build_obs(rows, targets, fx, fy, prev, sup).numpy())
        acts = [int(round(math.atan2(-row[0], -row[1]) / (math.pi / 4)) % 8) for row in rows]   # avance pour faire VARIER les obs
        b.send("HMT_ACTS=%s; call HMT_SHAMAL_APPLY;" % json.dumps(acts)); time.sleep(3)
    if not buf: return None
    O = np.concatenate(buf, 0)
    return O.min(0), O.max(0), O.std(0)


fx, fy = [int(v) for v in FOB.split(",")]
print("=== PREFLIGHT : diff distribution d'obs ENTRAÎNEMENT vs DÉPLOIEMENT (17 features) ===", flush=True)
tmn, tmx, tsd = sandbox_stats()
live = live_stats(fx, fy)
if live is None:
    print("  !! pas d'obs live (WEST spawné ? serveur ?)"); sys.exit(1)
lmn, lmx, lsd = live
print("  %-13s | TRAIN[min..max] std | LIVE[min..max] std | VERDICT" % "feature", flush=True)
flags = 0
for i, f in enumerate(FEAT):
    verdict = "ok"
    if tsd[i] < 1e-4 and lsd[i] > 1e-3:
        verdict = ">>> CONSTANT au TRAIN, VARIE live = BUG (signal jamais appris)"; flags += 1
    elif lmn[i] < tmn[i] - 0.15 or lmx[i] > tmx[i] + 0.15:
        verdict = ">> hors des bornes vues au training (extrapolation)"; flags += 1
    print("  %-13s | [%6.2f..%6.2f] %.2f | [%6.2f..%6.2f] %.2f | %s" % (
        f, tmn[i], tmx[i], tsd[i], lmn[i], lmx[i], lsd[i], verdict), flush=True)
print("\n  >>> %d feature(s) suspecte(s). %s" % (flags, "PROPRE, déploiement autorisé." if flags == 0 else "NE PAS conclure d'un run tant que non résolu."), flush=True)
print("PREFLIGHT_DONE", flush=True)
