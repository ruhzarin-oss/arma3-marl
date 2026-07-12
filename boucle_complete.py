"""boucle_complete — RL -> LLM -> RL-LLM, le tout en UNE boucle.
Monde koth_gpu (3 factions, enrichi) ; executeur RL gele (league_maneuver_learner) ;
officier LLM (Qwen HF + LoRA) -> POSTURE de BLU par rang (biais logits) ;
RL-LLM = GRPO (TRL) : G postures/situation -> JOUER chacune -> score CMDP -> avantage groupe -> update LoRA + KL.
--model Qwen/Qwen2.5-7B-Instruct (bf16) ou Qwen/Qwen2.5-14B-Instruct (4-bit). Coalition EMERGE."""
import argparse, torch
from datasets import Dataset
from transformers import BitsAndBytesConfig
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer
from koth_gpu import KothGPU, POSTURES
from train_koth_gpu import Net

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
ap.add_argument("--epochs", type=int, default=4)
ap.add_argument("--envs", type=int, default=512)
A = ap.parse_args()
DEV = "cuda:0"; LAMBDA = 0.5; MODEL = A.model

rl = Net(10, 4, 512, 3).to(DEV)
rl.load_state_dict(torch.load("league_maneuver_learner.pt", map_location=DEV)); rl.eval()
for p in rl.parameters():
    p.requires_grad_(False)

POST = ["prendre_colline", "defendre", "harceler"]
BIASES = {n: torch.tensor(POSTURES[n], device=DEV, dtype=torch.float32) for n in POST}
ZERO = torch.zeros(4, device=DEV)


def parse_posture(txt):
    t = (txt or "").lower()
    for n, keys in (("prendre_colline", ["prendre", "colline", "assaut", "avanc", "attaqu", "offensi"]),
                    ("defendre", ["defend", "défend", "tenir", "hold", "couvert"]),
                    ("harceler", ["harcel", "harass", "distance"])):
        if any(k in t for k in keys):
            return n
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


data = Dataset.from_list([{"prompt": make_prompt(r), "rank": r} for r in (1, 2, 3) for _ in range(8)])


def reward_fn(completions, rank=None, **kw):
    out = []
    for comp, rk in zip(completions, rank):
        txt = comp[-1]["content"] if isinstance(comp, list) else comp
        p = parse_posture(txt)
        out.append(play_blu(p, rk, n=A.envs) if p else -0.5)
    return out


is14 = "14B" in MODEL or "14b" in MODEL
if is14:
    mik = {"quantization_config": BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                                                     bnb_4bit_quant_type="nf4"), "device_map": {"": 0}, "attn_implementation": "sdpa"}
else:
    mik = {"dtype": torch.bfloat16, "device_map": {"": 0}, "attn_implementation": "sdpa"}
lora = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")
cfg = GRPOConfig(output_dir="officer_grpo_%s" % ("14b" if is14 else "7b"), per_device_train_batch_size=6,
                 num_generations=6, max_completion_length=24, learning_rate=1e-5, num_train_epochs=A.epochs,
                 logging_steps=1, beta=0.04, bf16=True, report_to="none", model_init_kwargs=mik)
print("=== BOUCLE COMPLETE  RL->LLM->RL-LLM  | modele=%s | %s ===" % (MODEL, "4-bit" if is14 else "bf16"), flush=True)
trainer = GRPOTrainer(model=MODEL, args=cfg, train_dataset=data, reward_funcs=reward_fn, peft_config=lora)
trainer.train()
trainer.save_model("officer_rllm_%s" % ("14b" if is14 else "7b"))
print("[FINI] officier RL-LLM -> officer_rllm_%s" % ("14b" if is14 else "7b"), flush=True)
