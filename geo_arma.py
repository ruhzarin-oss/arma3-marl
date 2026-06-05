"""geo_arma — TEST GÉO→ARMA (commande Younes : « tester ça sur Arma, 10 serveurs »).
10 serveurs headless = 10 GUERRES GÉOPOLITIQUES en parallèle. À chaque pas géo, la bataille de la
COLLINE LA PLUS MENACÉE de chaque guerre est résolue DANS ARMA : KOTH 3 factions (BLU/OPF/IND = pays
0/1/2), cerveau `koth_finetuned.pt` (ligue sim → fine-tune réel), HANDICAP de dégâts ∝ rapport de forces
géo (le pays militairement faible spawne blessé). Verdict Arma (capture, sinon contrôle cumulé) →
le vainqueur PREND la colline dans la carte géo (+ garnison). Le reste du front se résout en abstrait.
Les CIVILS de la carte géo = la politique APPRISE `civ_learner.pt`. Doctrines AEZ (système complet).
Boucle géo→Arma→géo fermée. Sortie : journal des guerres + comparaison avec 10 guerres 100 % abstraites."""
import time
import numpy as np
import torch
from geo_gpu import GeoGPU
from train_koth_finetune import MultiKoth
from train_koth_gpu import Net
from train_civ import CivNet, masked_logits

dev = "cuda:0"
W = 10                                  # 10 serveurs = 10 guerres
GEO_STEPS = 25; HOLD_T = 3              # guerres courtes (un pas géo coûte ~1.5-2 min de bataille Arma)
BATTLE_STEPS = 25

# --- cerveaux ---
net = Net(10, 4, 512, 3).to(dev)
net.load_state_dict(torch.load("/home/younes/arma3-marl/koth_finetuned.pt", map_location=dev)); net.eval()
civ = CivNet().to(dev)
civ.load_state_dict(torch.load("/home/younes/arma3-marl/civ_learner.pt", map_location=dev)); civ.eval()

def civ_pol(o, l, r):
    with torch.no_grad():
        lg, _ = civ(o)
    return masked_logits(lg, l, r).argmax(-1)

def act(o):
    with torch.no_grad():
        lg = net.a_logits(torch.as_tensor(np.asarray(o), dtype=torch.float32, device=dev))
    return torch.distributions.Categorical(logits=lg).sample().cpu().numpy()

# --- mondes ---
geo = GeoGPU(num_envs=W, n_countries=3, arc=4, hold_T=HOLD_T, max_steps=GEO_STEPS, doctrines="AEZ", device=dev, seed=0)
N_PER_FACTION = 15                      # 15×3 = 45 unités/bataille × 10 serveurs = 450 unités simultanées (plafond CPU mesuré)
arma = MultiKoth(num_servers=W, per_server=1, n=N_PER_FACTION, move=36, max_steps=BATTLE_STEPS)
# ROTATION pays<->faction : guerre i, pays c -> faction (c+i)%3. Neutralise statistiquement TOUT biais
# de faction résiduel (spawn, cerveau entraîné dans l'ancien monde, équipement…), comme les rotations de l'anneau.
SHIFT = [i % 3 for i in range(W)]
# ÉQUIPEMENT ÉGALISÉ : aucune protection, même fusil pour les 3 camps (neutralise l'écart d'armure vanilla).
EQ = ("{ removeUniform _x; removeVest _x; removeHeadgear _x; removeAllWeapons _x; "
      "_x addMagazines ['30Rnd_65x39_caseless_mag', 6]; _x addWeapon 'arifle_MX_F' } forEach allUnits")
print("GEO-ARMA | %d guerres (doctrines %s, hold %d) | %d unités/faction = %d/bataille, %d au total | handicap ∝ forces géo | rotation pays↔faction %s | équipement égalisé"
      % (W, geo.doctrines, HOLD_T, N_PER_FACTION, 3 * N_PER_FACTION, 3 * N_PER_FACTION * W, SHIFT), flush=True)

def target_hills():
    """Par guerre : la colline dont les voisins ennemis portent le plus de force (le front chaud)."""
    left_o = torch.roll(geo.owner, 1, 1); right_o = torch.roll(geo.owner, -1, 1)
    fl = torch.roll(geo.force, 1, 1); fr = torch.roll(geo.force, -1, 1)
    th = torch.zeros(W, 3, device=dev)
    for c in range(3):
        h = int(geo.hill[c])
        tl = torch.where(left_o[:, h] != geo.owner[:, h], fl[:, h], torch.zeros(W, device=dev))
        tr = torch.where(right_o[:, h] != geo.owner[:, h], fr[:, h], torch.zeros(W, device=dev))
        th[:, c] = torch.maximum(tl, tr)
    pick = th.argmax(1)                                  # indice de pays (sa colline)
    return geo.hill[pick], pick                          # (W,) région-colline cible

live = torch.ones(W, dtype=torch.bool, device=dev)
ends = []                                                # (guerre, pas, win_by, vainqueur, morts_civils)
overrides = 0; battles_decided = 0; battles_total = 0
t0 = time.time()
for step in range(GEO_STEPS):
    if not live.any():
        break
    hills_t, hills_c = target_hills()
    fc = torch.stack([(geo.force * (geo.owner == c).float()).sum(1) for c in range(3)], 1)   # (W,3) force militaire totale
    rel = fc / fc.max(1, keepdim=True).values.clamp(min=1e-6)
    dmgmap = (0.5 * (1.0 - rel)).cpu().numpy()           # le + fort spawne intact, le faible blessé (max 0.5)
    # --- bataille Arma (reset propre + égalisation + handicap, via rotation pays->faction) ---
    obs = arma.reset()
    for i, e in enumerate(arma.envs):
        e.t[:] = 0                                       # pas de respawn aléatoire en cours de bataille
        hcap = "; ".join("{ _x setDamage %.2f } forEach (units (%s select 0))"
                         % (dmgmap[i][(f - SHIFT[i]) % 3], g)          # handicap du PAYS mappé sur cette faction
                         for f, g in enumerate(e.GRP) if dmgmap[i][(f - SHIFT[i]) % 3] > 0.02)
        e.b.send(EQ + ("; " + hcap if hcap else ""), wait=False)
    winners = np.full(W, -1)
    for bt in range(BATTLE_STEPS):
        acts = [act(obs[c]) for c in range(3)]
        obs, rew, done_b, info_b = arma.step(acts)
        wv = info_b["winner"]
        newly = (wv >= 0) & (winners < 0)
        winners[newly] = wv[newly]
        if (winners >= 0).all():
            break
    battles_total += int(live.sum())
    battles_decided += int(((winners >= 0) & live.cpu().numpy()).sum())
    for i, e in enumerate(arma.envs):                    # timeout → verdict au contrôle cumulé
        if winners[i] < 0 and e.ctrl_time[:, 0].max() > 0:
            winners[i] = int(e.ctrl_time[:, 0].argmax())
    for i in range(W):                                   # faction vainqueur -> PAYS (défaire la rotation)
        if winners[i] >= 0:
            winners[i] = (winners[i] - SHIFT[i]) % 3
    # --- pas géo (civils RL) ---
    done_g, info_g = geo.step(auto_reset=False, civ_policy=civ_pol)
    # --- le verdict Arma impose le sort de la colline ---
    al = geo.alive()
    for i in range(W):
        wn = int(winners[i])
        if live[i] and wn >= 0 and bool(al[i, wn]):
            h = int(hills_t[i])
            if int(geo.owner[i, h]) != wn:
                overrides += 1
            geo.owner[i, h] = wn
            geo.force[i, h] = torch.maximum(geo.force[i, h], torch.tensor(5.0, device=dev))
    # --- journal ---
    terr = info_g["terr"]; hills_owner = geo.owner[:, geo.hill]
    print("pas %2d | guerres vives %d | verdicts Arma %s | colline-cibles %s | %.0fs"
          % (step, int(live.sum()), winners.tolist(), hills_t.tolist(), time.time() - t0), flush=True)
    for i in range(W):
        if live[i] and bool(done_g[i]):
            wb = int(info_g["win_by"][i]); wg = int(info_g["winner"][i])
            ends.append((i, step + 1, ["2COLLINES", "ÉLIMINATION", "timeout"][wb], wg,
                         float(info_g["civ_dead"][i] / geo.pop0_total)))
            live[i] = False
            print("  >> guerre %d FINIE pas %d : %s, vainqueur pays %d (%s), morts civils %.2f"
                  % (i, step + 1, ends[-1][2], wg, geo.doctrines[wg], ends[-1][4]), flush=True)

print("\n=== BILAN GÉO-ARMA (%.0f min) ===" % ((time.time() - t0) / 60), flush=True)
print("guerres finies %d/%d | batailles Arma %d (décidées en jeu %.2f, le reste au contrôle)"
      % (len(ends), W, battles_total, battles_decided / max(battles_total, 1)), flush=True)
print("verdicts de colline imposés par Arma (changements de mains) : %d" % overrides, flush=True)
wd = {}
for (_, _, wb, wg, _) in ends:
    wd[geo.doctrines[wg]] = wd.get(geo.doctrines[wg], 0) + 1
print("vainqueurs par doctrine : %s | fins : %s | morts civils moy %.2f"
      % (wd, {k: sum(1 for e in ends if e[2] == k) for k in set(e[2] for e in ends)},
         (sum(e[4] for e in ends) / len(ends)) if ends else 0.0), flush=True)

# --- baseline : les MÊMES 10 guerres, 100 % abstraites (même seed, sans Arma) ---
geo2 = GeoGPU(num_envs=W, n_countries=3, arc=4, hold_T=HOLD_T, max_steps=GEO_STEPS, doctrines="AEZ", device=dev, seed=0)
live2 = torch.ones(W, dtype=torch.bool, device=dev); ends2 = []
for step in range(GEO_STEPS):
    done_g, info_g = geo2.step(auto_reset=False, civ_policy=civ_pol)
    for i in range(W):
        if live2[i] and bool(done_g[i]):
            ends2.append((i, step + 1, ["2COLLINES", "ÉLIMINATION", "timeout"][int(info_g["win_by"][i])],
                          int(info_g["winner"][i])))
            live2[i] = False
wd2 = {}
for (_, _, _, wg) in ends2:
    wd2[geo2.doctrines[wg]] = wd2.get(geo2.doctrines[wg], 0) + 1
print("BASELINE abstraite (mêmes guerres sans Arma) : vainqueurs %s | fins %s"
      % (wd2, {k: sum(1 for e in ends2 if e[2] == k) for k in set(e[2] for e in ends2)}), flush=True)
print("[FINI]", flush=True)
