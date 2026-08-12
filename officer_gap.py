"""officer_gap — QUE RESTE-T-IL A APPRENDRE ? Le Qwen BRUT choisit-il deja juste ?

Le piege du 18/06 : la base etait « deja sensee », donc meme une tache non plate n'aurait rien
montre. On mesure donc l'ECART entre le choix du modele brut et l'oracle situe. Cet ecart EST
le budget disponible pour le fine-tuning. S'il vaut zero, inutile d'entrainer quoi que ce soit.

CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 ./.venv/bin/python officer_gap.py
"""
import sys
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import officer_task as T

MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEV = "cuda:0"
REELLES = ["prendre_colline", "defendre", "harceler"]   # le menu de l'officier (neutre exclu : ce n'est pas un ordre)


def lire_posture(txt):
    t = (txt or "").lower()
    for n, cles in (("prendre_colline", ["prendre", "colline", "assaut", "avanc", "attaqu", "offensi"]),
                    ("defendre", ["defend", "défend", "tenir", "hold", "couvert"]),
                    ("harceler", ["harcel", "harass", "distance", "priv"])):
        if any(k in t for k in cles):
            return n
    return None


def main():
    print("=== Table de reference (SCORE = victoire - defaite, gain %.2f) ===" % T.GAIN)
    tab = {}
    for s in T.SITUATIONS:
        for p in REELLES:
            tab[(s, p)] = sum(T.jouer(p, s, n=4096, seed=k)[0] for k in (0, 1)) / 2
        print("  %-8s " % s + "  ".join("%s=%+.3f" % (p, tab[(s, p)]) for p in REELLES), flush=True)

    tok = AutoTokenizer.from_pretrained(MODEL)
    mdl = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16,
                                               device_map={"": 0}, attn_implementation="sdpa")

    @torch.no_grad()
    def demander(prompt):
        enc = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True,
                                      return_tensors="pt", return_dict=True).to(DEV)
        out = mdl.generate(**enc, max_new_tokens=24, do_sample=False, pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)

    print("\n=== CE QUE CHOISIT LE QWEN BRUT ===")
    s_brut, s_oracle, s_pire = 0.0, 0.0, 0.0
    lignes = []
    for s in T.SITUATIONS:
        txt = demander(T.PROMPTS[s])
        p = lire_posture(txt)
        oracle = max(REELLES, key=lambda q: tab[(s, q)])
        pire = min(REELLES, key=lambda q: tab[(s, q)])
        sc = tab[(s, p)] if p else float("nan")
        s_brut += sc if p else 0.0
        s_oracle += tab[(s, oracle)]
        s_pire += tab[(s, pire)]
        lignes.append((s, p, sc, oracle, tab[(s, oracle)]))
        print("  %-8s BRUT=%-16s (%+.3f)   ORACLE=%-16s (%+.3f)   %s"
              % (s, p, sc, oracle, tab[(s, oracle)], "JUSTE" if p == oracle else "FAUX"),
              flush=True)
        print("           reponse : %s" % txt.strip().replace("\n", " ")[:110])

    k = len(T.SITUATIONS)
    print("\n=== BUDGET DISPONIBLE POUR LE FINE-TUNING ===")
    print("  moyenne BRUT    : %+.3f" % (s_brut / k))
    print("  moyenne ORACLE  : %+.3f" % (s_oracle / k))
    print("  moyenne PIRE    : %+.3f" % (s_pire / k))
    ecart = s_oracle / k - s_brut / k
    print("  ECART a rattraper : %.3f" % ecart)
    print("  -> %s" % ("IL Y A DE QUOI APPRENDRE" if ecart >= 0.05 else
                       "RIEN A APPRENDRE : la base choisit deja l'oracle (le piege du 18/06)"))
    justes = sum(1 for _, p, _, o, _ in lignes if p == o)
    print("  (le brut est juste sur %d situation(s) sur %d)" % (justes, k))


if __name__ == "__main__":
    main()
