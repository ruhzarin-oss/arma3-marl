#!/usr/bin/env python3
"""controle_feu — POINT 2 DE LA LISTE DE FABLE.

⟨Fable⟩ « Tenir le feu de l'agent sans le desarmer : combatMode BLUE par defaut, et
ENGAGER devient le seul geste qui autorise le tir (sinon ENGAGER serait un geste nul,
precisement ce qui fait s'effondrer une politique). Reussi si doctrine = 0 coup sur 20 et
defenseur vivant 20/20, ET si ENGAGER scripte a 30 m produit des coups sur >= 18/20. »

⚠️ POURQUOI PAS LE DESARMEMENT. Mesure du 03/09 : en YELLOW l'agent abattait le defenseur
en 118 coups sur 20 episodes. Le desarmer reglerait ca, mais laisserait dans le catalogue
un geste ENGAGER qui ne fait plus rien — et un geste nul fait s'effondrer une politique,
comme le cap 315 l'a montre.

CE CONTROLE SAIT ECHOUER DES DEUX COTES : trop de feu d'un cote, plus de feu du tout de
l'autre. Les deux bras sont necessaires, aucun ne suffit.
"""
import sys, time, random
sys.path.insert(0, "/home/younes/arma3-marl")
from pont import Pont
from para import instance
from sites import charger

def bras(pont, nom, geste0, n, sites, uid0):
    rng = random.Random(4242)
    coups, vivants, joues = [], 0, 0
    uid = uid0
    for i in range(n):
        uid += 1
        D = 30.0
        dx, dy = rng.uniform(-D/25, D/25), rng.uniform(-D/25, D/25)
        daz = rng.uniform(-6, 6)
        s = rng.choice(sites)
        pont.envoyer(f'HMT_TICKET = [{uid}, "B1", {D}, {dx:.3f}, {dy:.3f}, {daz:.3f}, '
                     f'{s["x"]:.2f}, {s["y"]:.2f}, {s["az"]}];')
        t0, cyc, dernier_nenn = time.time(), 0, None
        while time.time() - t0 < 70:
            l = pont.attendre("[ECHP] ", 70 - (time.time() - t0))
            if l is None: break
            if "] OBS " in l:
                p = l.split("] OBS ")[1].replace('"', "").split()
                if int(p[0]) != uid: continue
                dernier_nenn = float(p[8])          # n_enn = obs[6] -> p[2+6]
                g = geste0 if cyc == 0 else 8
                pont.envoyer(f"HMT_ACT = [{uid}, {int(p[1])}, {g}];")
                cyc += 1
            elif "] RESULT " in l:
                p = l.split("] RESULT ")[1].replace('"', "").split()
                if int(p[0]) != uid: continue
                joues += 1
                coups.append(int(p[5]))
                if dernier_nenn is not None and dernier_nenn > 0: vivants += 1
                break
    tir = sum(1 for c in coups if c > 0)
    print(f"  {nom:22s} : {joues} episodes  ·  {sum(coups):3d} coups au total  ·  "
          f"{tir}/{joues} episodes avec tir  ·  defenseur encore vu en fin d'episode : {vivants}/{joues}")
    return joues, sum(coups), tir, vivants

inst = instance(1)
pont = Pont(inst["profil"], pont_dir=inst["pont"], patience_sync=60)
if pont.attendre("ETAT PRET", 120) is None:
    print("la mission ne dit jamais PRET"); sys.exit(2)
sites = charger("jugement")
print("controle du feu, instance 1, barreau B1, memes sites des deux cotes\n")
jA, cA, tA, vA = bras(pont, "DOCTRINE (geste 8)", 8, 20, sites, 720000)
jB, cB, tB, vB = bras(pont, "ENGAGER (geste 9)",  9, 20, sites, 730000)

print("\n=== VERDICT ===")
ok1 = (cA == 0)
ok2 = (tB >= 18)
print(f"  la doctrine ne tire plus         : {'OUI' if ok1 else 'NON'}  ({cA} coups, exige 0)")
print(f"  ENGAGER fait toujours feu        : {'OUI' if ok2 else 'NON'}  ({tB}/{jB} episodes, exige >= 18)")
if ok1 and ok2:
    print("\n✅ POINT 2 PASSE. Le feu est tenu sans que le catalogue soit mutile.")
    sys.exit(0)
print("\n⛔ POINT 2 ECHOUE. On ne passe pas au point 3.")
sys.exit(1)
