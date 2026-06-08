"""M1 — C : l'officier LLM (mistral-nemo:12b) retrouve-t-il la règle de coalition et réduit-il le runaway ?
On interroge le LLM sur les 3 situations canoniques (je mène / 2e / dernier) -> politique rang->posture,
puis on l'applique dans le sim à grande échelle et on compare A (rien) / B (oracle) / C (LLM).
Tractable : ~3 appels LLM (lents) au lieu de milliers ; la décision de l'officier ne dépend que du rang."""
import json, urllib.request, time
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net
from officer_m1 import parse_posture, M1_BIAS, NAMES

DEV = "cuda:0"; N = 4096; T = 300; K_EARLY = 8; MODEL = "qwen2.5:14b"
DEFEND = torch.tensor(M1_BIAS["defendre"], device=DEV)
PRESS  = torch.tensor(M1_BIAS["presser"],  device=DEV)

net = Net(10, 4, 512, 3).to(DEV)
net.load_state_dict(torch.load("league_learner.pt", map_location=DEV)); net.eval()


def ask_officer(controle, leader, rank):
    prompt = ("KOTH 3 factions, une colline centrale a tenir. Tu commandes BLU.\n"
              "Controle (temps cumule): %s -> LEADER = %s.\n"
              "Ton rang au controle: %d/3.\n"
              "Deux postures possibles UNIQUEMENT : 'defendre' ou 'presser'.\n"
              "Logique de coalition : si tu MENES, les deux autres vont se liguer contre toi "
              "-> DEFENDRE (tiens ta position, ne t'expose pas). Si tu es DERRIERE, il faut "
              "PRESSER pour contester le leader et l'empecher de filer.\n"
              "Raisonne en UNE phrase, puis termine par EXACTEMENT un mot : defendre OU presser." % (controle, leader, rank))
    req = urllib.request.Request("http://localhost:11434/api/generate",
        data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                         "options": {"temperature": 0.2, "num_predict": 100}}).encode(),
        headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())["response"]
    return r.strip(), parse_posture(r)


# --- interroge l'officier sur les 3 rangs ---
SITUATIONS = {
    1: ("BLU 18 OPF 4 IND 3", "BLU (toi)"),
    2: ("BLU 8 OPF 15 IND 5", "OPF"),
    3: ("BLU 3 OPF 15 IND 9", "OPF"),
}
print("=== POLITIQUE de l'officier LLM (%s) ===" % MODEL)
policy = {}
for rank, (ctrl, leader) in SITUATIONS.items():
    t = time.time(); resp, post = ask_officer(ctrl, leader, rank)
    policy[rank] = post
    print("rang %d (%s) [%.0fs] -> %-9s | %s" % (rank, "leader" if rank == 1 else ("milieu" if rank == 2 else "dernier"),
                                                 time.time() - t, post, resp.replace("\n", " ")[:110]))
print("politique extraite:", {r: policy[r] for r in (1, 2, 3)})

# table biais par rang (index 1..3)
bias_table = torch.zeros(4, 4, device=DEV)
for r in (1, 2, 3):
    bias_table[r] = torch.tensor(M1_BIAS[policy[r]], device=DEV)


def run(mode):
    env = KothGPU(num_envs=N, device=DEV, seed=0); ot = list(env.reset())
    early = torch.full((N,), -1, device=DEV, dtype=torch.long)
    runaway = overturned = 0; wins = torch.zeros(env.C, device=DEV)
    with torch.no_grad():
        ctrl = torch.stack([env.ctrl_time[c] for c in range(env.C)], 0)
        lead = ctrl.argmax(0)
        for t in range(T):
            ctrl = torch.stack([env.ctrl_time[c] for c in range(env.C)], 0); lead = ctrl.argmax(0)
            acts = []
            for c in range(env.C):
                lg = net.a_logits(ot[c])
                if mode == "B":
                    b = torch.where((lead == c).unsqueeze(-1), DEFEND, PRESS)
                    lg = lg + b.unsqueeze(1)
                elif mode == "C":
                    rank_c = 1 + (ctrl > ctrl[c]).sum(0)            # (N,) rang du camp c
                    b = bias_table[rank_c]                          # (N,4)
                    lg = lg + b.unsqueeze(1)
                acts.append(Categorical(logits=lg).sample())
            ot2, _, done, info = env.step(acts)
            dm = done.bool() if torch.is_tensor(done) else torch.as_tensor(done, device=DEV).bool()
            w = info["winner"]
            newly = (env.t == K_EARLY) & (early < 0); early = torch.where(newly, lead, early)
            dec = (w >= 0) & dm & (early >= 0)
            runaway += int(((w == early) & dec).sum()); overturned += int(((w != early) & dec).sum())
            for c in range(env.C): wins[c] += int(((w == c) & dm).sum())
            early = torch.where(dm, torch.full_like(early, -1), early); ot = list(ot2)
    tot = runaway + overturned
    return {"runaway": runaway / tot if tot else 0, "decided": tot, "wins": [int(x) for x in wins.tolist()]}


print("\n=== A / B / C — runaway (leader précoce gagne) ===")
labels = {"A": "A pas d'officier", "B": "B oracle", "C": "C officier LLM"}
for mode in ("A", "B", "C"):
    r = run(mode)
    print("%-18s | runaway=%.3f | décidées=%d | wins/camp=%s" % (labels[mode], r["runaway"], r["decided"], r["wins"]))
print("\nC proche de B (et << A) = le LLM a retrouvé la coalition. C ~ A = il n'a pas su.")
