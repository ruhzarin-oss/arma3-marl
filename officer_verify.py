"""VERIF OFFICIER : le GRPO a-t-il VRAIMENT appris, ou juste grimpe en reward bruite ?
Compare, sur les 3 rangs, la posture choisie par l'officier ENTRAINE (LoRA) vs le BRUT,
et SCORE chaque choix via le sim koth (play_blu). Entraine > brut => appris pour de vrai.
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from koth_gpu import KothGPU, POSTURES
from train_koth_gpu import Net

DEV = "cuda:0"; LAMBDA = 0.5; MODEL = "Qwen/Qwen2.5-7B-Instruct"
POST = ["prendre_colline", "defendre", "harceler"]
BIASES = {n: torch.tensor(POSTURES[n], device=DEV, dtype=torch.float32) for n in POST}
ZERO = torch.zeros(4, device=DEV)

rl = Net(10, 4, 512, 3).to(DEV)
rl.load_state_dict(torch.load("/home/younes/arma3-marl/league_maneuver_learner.pt", map_location=DEV)); rl.eval()
for p in rl.parameters(): p.requires_grad_(False)

def parse_posture(txt):
    t = (txt or "").lower()
    for n, keys in (("prendre_colline", ["prendre", "colline", "assaut", "avanc", "attaqu", "offensi"]),
                    ("defendre", ["defend", "défend", "tenir", "hold", "couvert"]),
                    ("harceler", ["harcel", "harass", "distance"])):
        if any(k in t for k in keys): return n
    return None

@torch.no_grad()
def play_blu(posture_name, rank_target, n=512, T=180):
    env = KothGPU(num_envs=n, attrition_win=False, timeout_decisive=True, device=DEV, seed=0)
    ot = list(env.reset()); bias = BIASES.get(posture_name, ZERO)
    for _ in range(T):
        ctrl = torch.stack([env.ctrl_time[c] for c in range(env.C)], 0)
        rank_blu = 1 + (ctrl > ctrl[0]).sum(0)
        acts = []
        for c in range(env.C):
            lg = rl.a_logits(ot[c])
            if c == 0:
                lg = lg + torch.where((rank_blu == rank_target).unsqueeze(-1), bias, ZERO).unsqueeze(1)
            acts.append(torch.distributions.Categorical(logits=lg).sample())
        ot, _, done, info = env.step(acts); ot = list(ot)
    tot = sum(env.ctrl_time[c].mean() for c in range(env.C)) + 1e-6
    return float(env.ctrl_time[0].mean() / tot) - LAMBDA * (1.0 - float(env._alive(0).float().mean()))

def make_prompt(rank):
    return ("KOTH 3 factions, prendre et TENIR la colline centrale. Tu commandes BLU, rang %d/3 au controle. "
            "Postures : prendre_colline / defendre / harceler. Reponds par UNE seule posture." % rank)

tok = AutoTokenizer.from_pretrained(MODEL)
base = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa")
model = PeftModel.from_pretrained(base, "/home/younes/arma3-marl/officer_rllm_7b")

@torch.no_grad()
def gen(rank):
    enc = tok.apply_chat_template([{"role": "user", "content": make_prompt(rank)}], add_generation_prompt=True, return_tensors="pt", return_dict=True).to(DEV)
    out = model.generate(**enc, max_new_tokens=24, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)

print("=== VERIF OFFICIER : BRUT vs ENTRAINE (posture choisie + score koth) ===", flush=True)
rows = []
for rank in [1, 2, 3]:
    txt_t = gen(rank); p_t = parse_posture(txt_t)                       # adaptateur LoRA actif = entraine
    with model.disable_adapter():
        txt_b = gen(rank); p_b = parse_posture(txt_b)                   # sans adaptateur = brut
    r_t = play_blu(p_t, rank) if p_t else float("nan")
    r_b = play_blu(p_b, rank) if p_b else float("nan")
    rows.append((rank, p_b, r_b, p_t, r_t))
    print("rang %d | BRUT: %-16s (score %.3f) | ENTRAINE: %-16s (score %.3f)" % (rank, p_b, r_b, p_t, r_t), flush=True)
db = sum(r[2] for r in rows) / 3; dt = sum(r[4] for r in rows) / 3
print("MOYENNE score : BRUT %.3f -> ENTRAINE %.3f (%+.3f)" % (db, dt, dt - db), flush=True)
print("VERIF_DONE", flush=True)
