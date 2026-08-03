#!/usr/bin/env python3
"""banc_gpu.py — saturation de la 3090, mesurée et non estimée.

⟨Fable : « que le banc mesure le VRAI réseau dans la VRAIE boucle, pas un réseau jouet »⟩
Ce banc fait donc tourner exactement la simulation et le réseau de l'entraînement — attention
comprise — et relève l'occupation réelle de la carte à quatre tailles de lot, avec et sans
compilation.

Le risque qu'on écarte : avec un petit réseau et une simulation légère, le goulot n'est pas le
calcul mais le LANCEMENT des opérations. On peut faire tourner une nuit à 15 % d'occupation
sans le savoir.
"""
import torch, torch.nn as nn, time, math, subprocess, sys
import numpy as np

dev='cuda'; torch.cuda.set_device(0)
print(torch.cuda.get_device_name(0), f"{torch.cuda.get_device_properties(0).total_memory/1e9:.0f} Go", flush=True)

DMAX, NPAS, CE = 12, 50, 9
H = 128

class Politique(nn.Module):
    """le VRAI réseau : attention sur les entités, puis trois têtes d'action"""
    def __init__(s):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(CE,H), nn.ReLU(), nn.Linear(H,H))
        s.q   = nn.Linear(8, H)
        s.tronc = nn.Sequential(nn.Linear(8+H,H), nn.ReLU(), nn.Linear(H,H), nn.ReLU())
        s.dir = nn.Linear(H,2); s.allure = nn.Linear(H,3); s.posture = nn.Linear(H,3)
    def forward(s, moi, ent, msk):
        h = s.enc(ent)
        a = (h * s.q(moi).unsqueeze(1)).sum(-1) / math.sqrt(H)
        a = torch.softmax(a.masked_fill(msk<0.5, -1e9), -1).unsqueeze(-1)
        z = s.tronc(torch.cat([moi, (h*a).sum(1)], -1))
        return s.dir(z), s.allure(z), s.posture(z)

def occupation():
    try:
        o = subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used',
                            '--format=csv,noheader,nounits','-i','0'],
                           capture_output=True, text=True, timeout=5).stdout.strip().split(',')
        return int(o[0]), int(o[1])
    except Exception: return -1, -1

def tourner(B, compile_, bf16, iters=25):
    torch.manual_seed(1)
    pol = Politique().to(dev)
    f = torch.compile(pol) if compile_ else pol
    opt = torch.optim.Adam(pol.parameters(), lr=1e-3)
    POS = torch.randn(B, DMAX, 2, device=dev)*100
    AZI = torch.rand(B, DMAX, device=dev)*360
    MSK = (torch.rand(B, DMAX, device=dev) < 0.6).float()
    ctx = torch.autocast('cuda', dtype=torch.bfloat16) if bf16 else torch.autocast('cuda', enabled=False)
    for _ in range(3):                                    # chauffe
        _boucle(f, opt, POS, AZI, MSK, B, ctx)
    torch.cuda.synchronize()
    occ = []
    t0 = time.time()
    for i in range(iters):
        _boucle(f, opt, POS, AZI, MSK, B, ctx)
        if i % 5 == 0: occ.append(occupation()[0])
    torch.cuda.synchronize()
    dt = time.time()-t0
    u, m = occupation()
    pas = B*NPAS*iters
    return dict(B=B, compile=compile_, bf16=bf16, s=dt, pas_par_s=pas/dt,
                occ=max([o for o in occ if o>0], default=-1), mem=m)

def _boucle(f, opt, POS, AZI, MSK, B, ctx):
    p = torch.randn(B, 2, device=dev)*250
    perte = 0.0
    with ctx:
        for t in range(NPAS):
            v = p.unsqueeze(1) - POS
            d = v.norm(dim=-1).clamp(min=1)
            gis = torch.rad2deg(torch.atan2(v[...,0], v[...,1])) % 360
            ec = ((gis - AZI + 180) % 360 - 180).abs()
            ent = torch.stack([v[...,0]/300, v[...,1]/300, d/400, ec/180,
                               torch.sigmoid((60-ec)*.5), MSK, AZI/360,
                               torch.ones_like(d), torch.zeros_like(d)], -1)
            moi = torch.cat([p/300, p.norm(dim=-1,keepdim=True)/300,
                             torch.zeros(B,5,device=dev)], -1)
            dr, al, po = f(moi, ent, MSK)
            dr = dr / dr.norm(dim=-1, keepdim=True).clamp(min=1e-6)
            p = p + dr * 12.0
            perte = perte + (torch.sigmoid((60-ec)*.5)*MSK).sum(-1).mean()*0.01 \
                          + al.mean()*0 + po.mean()*0
    opt.zero_grad(); perte.backward(); opt.step()

print(f"\n{'lot':>7s} {'compile':>8s} {'bf16':>6s} {'durée':>8s} {'pas/s':>12s} {'occup.':>8s} {'mém.':>8s}")
res = []
for B in (4096, 8192, 16384, 32768):
    for compile_, bf16 in ((False,False), (False,True), (True,True)):
        try:
            r = tourner(B, compile_, bf16)
            res.append(r)
            print(f"{r['B']:7d} {str(r['compile']):>8s} {str(r['bf16']):>6s} "
                  f"{r['s']:7.1f}s {r['pas_par_s']:12,.0f} {r['occ']:7d}% {r['mem']:7d}M", flush=True)
        except torch.cuda.OutOfMemoryError:
            print(f"{B:7d} {str(compile_):>8s} {str(bf16):>6s}   mémoire insuffisante", flush=True)
            torch.cuda.empty_cache()
        except Exception as e:
            print(f"{B:7d} {str(compile_):>8s} {str(bf16):>6s}   erreur : {str(e)[:60]}", flush=True)
            torch.cuda.empty_cache()

if res:
    best = max(res, key=lambda r: r['pas_par_s'])
    pire = min(res, key=lambda r: r['pas_par_s'])
    print(f"\nMEILLEUR RÉGLAGE : lot {best['B']}, compile={best['compile']}, bf16={best['bf16']}")
    print(f"  {best['pas_par_s']:,.0f} pas/s   occupation {best['occ']} %   mémoire {best['mem']} Mo")
    print(f"  gain contre le pire réglage : x{best['pas_par_s']/pire['pas_par_s']:.1f}")
    cible = 400e6
    print(f"\n  400 millions de pas -> {cible/best['pas_par_s']/60:.0f} minutes")
    if best['occ'] < 70:
        print(f"  ATTENTION : occupation {best['occ']} % — le goulot n'est pas le calcul.")
        print(f"  Chercher : lancements d'opérations trop nombreux, ou synchronisation cachée.")
    else:
        print(f"  occupation {best['occ']} % — la carte travaille.")
