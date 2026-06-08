"""M1 ENRICHI — officier A/B/C sur l'exécuteur MANŒUVRE (league_maneuver), env enrichi
(attrition_win=False + timeout_decisive). Vocab de MANŒUVRE complet. Coalition INVERSÉE :
prendre la colline GAGNE -> oracle = leader TIENT (defendre), retardataires PRENNENT (prendre_colline).
Métrique = runaway (le leader précoce gagne-t-il ?). Officier LLM = qwen2.5:14b."""
import json, urllib.request, time
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU, POSTURES
from train_koth_gpu import Net

DEV = "cuda:0"; N = 4096; T = 300; K_EARLY = 8; MODEL = "qwen2.5:14b"
PUSH = torch.tensor(POSTURES["prendre_colline"], device=DEV)
HOLD = torch.tensor(POSTURES["defendre"], device=DEV)
VOCAB = {"prendre_colline": PUSH, "defendre": HOLD, "harceler": torch.tensor(POSTURES["harceler"], device=DEV),
         "neutre": torch.zeros(4, device=DEV)}
net = Net(10, 4, 512, 3).to(DEV)
net.load_state_dict(torch.load("league_maneuver_learner.pt", map_location=DEV)); net.eval()


def parse(text):
    t = (text or "").lower(); pos = -1; last = None
    for name, keys in (("prendre_colline", ["prendre", "colline", "assaut", "avanc", "prends", "offensi", "attaqu"]),
                       ("defendre", ["defend", "défend", "défens", "tenir", "hold", "couvert"]),
                       ("harceler", ["harcel", "harass", "distance"])):
        for k in keys:
            j = t.rfind(k)
            if j > pos: pos = j; last = name
    return last or "neutre"


def ask(ctrl, leader, rank):
    p = ("KOTH 3 factions : prendre et TENIR la colline centrale. Tu commandes BLU.\n"
         "Controle (temps cumule): %s -> LEADER = %s. Ton rang: %d/3.\n"
         "Pour GAGNER il faut controler la colline le plus longtemps. Postures : "
         "prendre_colline (assaut vers la colline) / defendre (tenir sa position) / harceler (feu a distance).\n"
         "Coalition : le LEADER tient la colline, les deux autres veulent l'en deloger. "
         "Si tu MENES -> defendre (tiens). Si tu es DERRIERE -> prendre_colline (va la chercher).\n"
         "Raisonne UNE phrase, puis termine par EXACTEMENT une posture." % (ctrl, leader, rank))
    req = urllib.request.Request("http://localhost:11434/api/generate",
        data=json.dumps({"model": MODEL, "prompt": p, "stream": False, "options": {"temperature": 0.2, "num_predict": 90}}).encode(),
        headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())["response"]
    return r.strip().replace("\n", " "), parse(r)


SIT = {1: ("BLU 18 OPF 4 IND 3", "BLU (toi)"), 2: ("BLU 8 OPF 15 IND 5", "OPF"), 3: ("BLU 3 OPF 15 IND 9", "OPF")}
print("=== POLITIQUE officier LLM (%s, jeu enrichi) ===" % MODEL)
policy = {}
for rk, (c, l) in SIT.items():
    t = time.time(); resp, post = ask(c, l, rk); policy[rk] = post
    print("rang %d [%.0fs] -> %-16s | %s" % (rk, time.time() - t, post, resp[:100]))
print("politique:", {r: policy[r] for r in (1, 2, 3)})
bias_table = torch.stack([torch.zeros(4, device=DEV)] + [VOCAB[policy[r]] for r in (1, 2, 3)])  # index 1..3


def run(mode):
    env = KothGPU(num_envs=N, device=DEV, attrition_win=False, timeout_decisive=True, seed=0); ot = list(env.reset())
    early = torch.full((N,), -1, device=DEV, dtype=torch.long); runaway = overturned = 0; wins = torch.zeros(3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            ctrl = torch.stack([env.ctrl_time[c] for c in range(env.C)], 0); lead = ctrl.argmax(0)
            acts = []
            for c in range(env.C):
                lg = net.a_logits(ot[c])
                if mode == "B":
                    b = torch.where((lead == c).unsqueeze(-1), HOLD, PUSH); lg = lg + b.unsqueeze(1)
                elif mode == "C":
                    rank_c = 1 + (ctrl > ctrl[c]).sum(0); lg = lg + bias_table[rank_c].unsqueeze(1)
                acts.append(Categorical(logits=lg).sample())
            ot2, _, done, info = env.step(acts); dm = done.bool() if torch.is_tensor(done) else torch.as_tensor(done, device=DEV).bool()
            w = info["winner"]; newly = (env.t == K_EARLY) & (early < 0); early = torch.where(newly, lead, early)
            dec = (w >= 0) & dm & (early >= 0); runaway += int(((w == early) & dec).sum()); overturned += int(((w != early) & dec).sum())
            for c in range(3): wins[c] += int(((w == c) & dm).sum())
            early = torch.where(dm, torch.full_like(early, -1), early); ot = list(ot2)
    tot = runaway + overturned
    return {"runaway": runaway / tot if tot else 0, "decided": tot, "wins": [int(x) for x in wins.tolist()]}


print("\n=== A / B / C — runaway (jeu enrichi, exécuteur manœuvre) ===")
for mode, lab in (("A", "A pas d'officier"), ("B", "B oracle inversé"), ("C", "C officier LLM")):
    r = run(mode)
    print("%-18s | runaway=%.3f | décidées=%d | wins/camp=%s" % (lab, r["runaway"], r["decided"], r["wins"]))
