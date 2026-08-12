"""officer_rft — RFT (Rejection-sampling Fine-Tuning) de l'officier sur la tache REFAITE.

Recette (celle que la litterature 2026 place devant GRPO sous signal rare, et celle de SIMA 2) :
  1. table de recompense : pour chaque situation, le score reel de chaque posture (pure sim) ;
  2. echantillonnage : K reponses du Qwen BRUT par situation, a temperature 1 (il faut de la
     DIVERSITE, sinon il n'y a rien a selectionner) ;
  3. rejet : on ne garde que les reponses dont la posture est l'optimum de cette situation ;
  4. SFT LoRA sur les paires gardees ;
  5. verification COMPORTEMENTALE entraine vs brut — jamais la courbe de perte.

POURQUOI UNE FAMILLE DE SITUATIONS, pas 3 : avec 3 prompts, un LoRA memorise 3 reponses et on
n'a rien prouve. On fait donc varier l'avance en continu, et on GARDE DE COTE des situations
jamais vues pour tester si une REGLE a ete apprise ou seulement une table.

CE QUI FERAIT ECHOUER LE RFT (ecrit AVANT le run) :
  R1. si l'echantillonnage a temperature 1 ne produit qu'une seule posture, il n'y a rien a
      selectionner -> le goulot est l'EXPLORATION, pas l'entrainement. On l'affiche.
  R2. si l'entraine egale le brut sur les situations TENUES A L'ECART, il a memorise, pas appris.
  R3. si l'entraine bat le brut sur l'apprentissage mais pas sur le score, on a appris a parler,
      pas a decider. On rapporte les DEUX.
  CONTROLE : le score de l'ORACLE (choix parfait) et celui du PIRE choix bornent la mesure.

CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 ./.venv/bin/python officer_rft.py
"""
import sys, json, os, math, random
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, PeftModel
import officer_task as T

MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEV = "cuda:0"
OUT = "/home/younes/arma3-marl/officer_rft_lora"
TABLE = "/home/younes/arma3-marl/officer_rft_table.json"
POSTURES_OFF = ["prendre_colline", "defendre", "harceler"]   # le menu de l'officier

LEADS_TRAIN = [140., 96., 60., 30., 0., -30., -60., -96.]
LEADS_TEST = [120., 45., -15., -75.]        # JAMAIS vues a l'entrainement
K = 32              # echantillons par situation
TEMP = 1.0
NENV = 4096
SEEDS = (0, 1)


def prompt_de(lead):
    """La situation en CHIFFRES : le modele doit apprendre une regle, pas 3 phrases par coeur."""
    blu = int(max(lead, 0.)); rouge = int(max(-lead, 0.)); vert = 0
    return ("KOTH a 3 factions, colline centrale. Tu commandes BLU.\n"
            "Temps de controle actuel — BLU (toi) : %d | ROUGE : %d | VERT : %d.\n"
            "Ta force : 3 hommes valides sur 3.\n"
            "Postures possibles : prendre_colline / defendre / harceler.\n"
            "Reponds par UNE seule posture, rien d'autre." % (blu, rouge, vert))


def lire_posture(txt):
    t = (txt or "").lower()
    for n, cles in (("prendre_colline", ["prendre", "colline", "assaut", "avanc", "attaqu", "offensi", "take"]),
                    ("defendre", ["defend", "défend", "tenir", "hold", "couvert"]),
                    ("harceler", ["harcel", "harass", "distance", "priv"])):
        if any(k in t for k in cles):
            return n
    return None


# ---------------------------------------------------------------- 1. table de recompense
def table_recompense(leads):
    tab = {}
    for lead in leads:
        T.SITUATIONS["_t"] = dict(lead=lead, usure=0.0)
        for p in POSTURES_OFF:
            s = sum(T.jouer(p, "_t", n=NENV, seed=k)[0] for k in SEEDS) / len(SEEDS)
            tab["%.0f|%s" % (lead, p)] = s
        best = max(POSTURES_OFF, key=lambda p: tab["%.0f|%s" % (lead, p)])
        print("  lead %+6.0f : " % lead + "  ".join("%s=%+.3f" % (p, tab["%.0f|%s" % (lead, p)])
                                                    for p in POSTURES_OFF) + "   -> %s" % best, flush=True)
    return tab


def score(tab, lead, posture):
    return tab.get("%.0f|%s" % (lead, posture))


def oracle(tab, lead):
    return max(POSTURES_OFF, key=lambda p: score(tab, lead, p))


def pire(tab, lead):
    return min(POSTURES_OFF, key=lambda p: score(tab, lead, p))


# ---------------------------------------------------------------- utilitaires LLM
def charger_base():
    return AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16,
                                                device_map={"": 0}, attn_implementation="sdpa")


@torch.no_grad()
def generer(mdl, tok, prompts, n_par_prompt=1, temperature=0.0, max_new=16):
    """Genere en lot. temperature=0 -> glouton."""
    sorties = []
    for pr in prompts:
        txt = tok.apply_chat_template([{"role": "user", "content": pr}],
                                      add_generation_prompt=True, tokenize=False)
        enc = tok([txt] * n_par_prompt, return_tensors="pt", padding=True).to(DEV)
        kw = dict(max_new_tokens=max_new, pad_token_id=tok.eos_token_id)
        if temperature > 0:
            kw.update(do_sample=True, temperature=temperature, top_p=0.95)
        else:
            kw.update(do_sample=False)
        out = mdl.generate(**enc, **kw)
        L = enc["input_ids"].shape[1]
        sorties.append([tok.decode(o[L:], skip_special_tokens=True) for o in out])
    return sorties


def main():
    torch.manual_seed(0); random.seed(0)
    print("=== 1. TABLE DE RECOMPENSE (pure simulation, aucun LLM) ===", flush=True)
    print("-- entrainement --", flush=True)
    tab = table_recompense(LEADS_TRAIN)
    print("-- tenues a l'ecart --", flush=True)
    tab.update(table_recompense(LEADS_TEST))
    json.dump(tab, open(TABLE, "w"), indent=1)

    tok = AutoTokenizer.from_pretrained(MODEL, padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    print("\n=== 2. ECHANTILLONNAGE DU BRUT (K=%d, T=%.1f) ===" % (K, TEMP), flush=True)
    mdl = charger_base()
    prompts = [prompt_de(l) for l in LEADS_TRAIN]
    ech = generer(mdl, tok, prompts, n_par_prompt=K, temperature=TEMP)

    print("\n=== 3. REJET : on ne garde que la posture optimale ===", flush=True)
    garde = []
    for lead, sorties in zip(LEADS_TRAIN, ech):
        cible = oracle(tab, lead)
        cpt = {p: 0 for p in POSTURES_OFF}; illisible = 0
        for s in sorties:
            p = lire_posture(s)
            if p is None:
                illisible += 1
            else:
                cpt[p] += 1
                if p == cible:
                    garde.append((prompt_de(lead), cible))
        div = sum(1 for p in POSTURES_OFF if cpt[p] > 0)
        print("  lead %+6.0f cible=%-16s | %s | illisible=%d | postures distinctes=%d"
              % (lead, cible, "  ".join("%s:%d" % (p[:4], cpt[p]) for p in POSTURES_OFF), illisible, div),
              flush=True)
    print("  -> %d paires gardees sur %d echantillons" % (len(garde), K * len(LEADS_TRAIN)))
    if len(garde) == 0:
        print("  R1 ECHEC : le brut n'emet JAMAIS la bonne posture -> le goulot est l'EXPLORATION.")
        return

    del mdl; torch.cuda.empty_cache()

    print("\n=== 4. SFT LoRA sur les paires gardees ===", flush=True)
    base = charger_base()
    base.config.use_cache = False
    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    mdl = get_peft_model(base, lora)
    mdl.print_trainable_parameters()

    ex = []
    for pr, rep in garde:
        pt = tok.apply_chat_template([{"role": "user", "content": pr}], add_generation_prompt=True, tokenize=False)
        pi = tok(pt, add_special_tokens=False)["input_ids"]
        ci = tok(rep + tok.eos_token, add_special_tokens=False)["input_ids"]
        ex.append((pi + ci, [-100] * len(pi) + ci))
    random.shuffle(ex)

    opt = torch.optim.AdamW([p for p in mdl.parameters() if p.requires_grad], lr=1e-4)
    BS, EPOCHS = 4, 3
    mdl.train()
    for ep in range(EPOCHS):
        tot, nb = 0.0, 0
        for i in range(0, len(ex), BS):
            lot = ex[i:i + BS]
            L = max(len(a) for a, _ in lot)
            ids = torch.full((len(lot), L), tok.pad_token_id, dtype=torch.long)
            lab = torch.full((len(lot), L), -100, dtype=torch.long)
            att = torch.zeros((len(lot), L), dtype=torch.long)
            for j, (a, b) in enumerate(lot):
                ids[j, :len(a)] = torch.tensor(a); lab[j, :len(b)] = torch.tensor(b); att[j, :len(a)] = 1
            out = mdl(input_ids=ids.to(DEV), attention_mask=att.to(DEV), labels=lab.to(DEV))
            out.loss.backward(); opt.step(); opt.zero_grad()
            tot += float(out.loss); nb += 1
        print("  epoque %d : perte %.4f" % (ep + 1, tot / max(1, nb)), flush=True)
    mdl.eval(); mdl.config.use_cache = True
    mdl.save_pretrained(OUT)
    print("  adaptateur ecrit dans %s" % OUT)

    print("\n=== 5. VERIFICATION COMPORTEMENTALE (glouton, entraine vs brut) ===", flush=True)
    for nom, leads in (("APPRISES", LEADS_TRAIN), ("TENUES A L'ECART", LEADS_TEST)):
        prompts = [prompt_de(l) for l in leads]
        with torch.no_grad():
            r_ent = [g[0] for g in generer(mdl, tok, prompts, 1, 0.0)]
            with mdl.disable_adapter():
                r_bru = [g[0] for g in generer(mdl, tok, prompts, 1, 0.0)]
        sb = so = st = sp = 0.0; jb = jt = 0
        print("\n--- %s ---" % nom)
        print("  %8s  %-16s %-16s %-16s   score brut / entraine / oracle" % ("lead", "BRUT", "ENTRAINE", "ORACLE"))
        for lead, tb, tt in zip(leads, r_bru, r_ent):
            pb, pt_ = lire_posture(tb), lire_posture(tt)
            orc = oracle(tab, lead)
            vb = score(tab, lead, pb) if pb else 0.0
            vt = score(tab, lead, pt_) if pt_ else 0.0
            sb += vb; st += vt; so += score(tab, lead, orc); sp += score(tab, lead, pire(tab, lead))
            jb += (pb == orc); jt += (pt_ == orc)
            print("  %+8.0f  %-16s %-16s %-16s   %+.3f / %+.3f / %+.3f  %s"
                  % (lead, pb, pt_, orc, vb, vt, score(tab, lead, orc),
                     "OK" if pt_ == orc else "rate"), flush=True)
        k = len(leads)
        print("  MOYENNE  brut %+.3f  ->  entraine %+.3f   (oracle %+.3f, pire %+.3f)"
              % (sb / k, st / k, so / k, sp / k))
        print("  JUSTESSE brut %d/%d  ->  entraine %d/%d" % (jb, k, jt, k))
        print("  GAIN     %+.3f de score, %+d situations justes" % (st / k - sb / k, jt - jb))


if __name__ == "__main__":
    main()
