"""M0b / M1 — PONT TEXTE de l'officier LLM (vocab ÉLAGUÉ, validé sur l'axe qui paie : defendre↔presser).
- M1_BIAS : postures actives (biais de logits sur exécuteurs GELÉS). Calibrées sur le diagnostic M0a
  (DEFEND a gagné 66 %, suppress-press 29 %, neutre 4 %) -> seules les postures de l'axe défensif/agressif
  sont retenues ; les postures de MANŒUVRE (prendre_colline/focus_leader/harceler/repli) sont DIFFÉRÉES
  tant que le sim ne récompense pas le positionnement (cf. PDF §5 « mission = 80 % »).
- serialize_state : état d'UN env -> texte pour l'officier (raisonnement de coalition à 3).
- parse_posture : texte du LLM -> posture valide (robuste, fallback neutre).
Les noms de factions suivent le projet : BLU/OPF/IND."""
import torch

NAMES = ["BLU", "OPF", "IND"]

# Postures actives M1 — biais de logits [HOLD, AVANCER, SUPPRESS, COUVERT]
M1_BIAS = {
    "defendre": [4.0, -8.0,  0.0,  3.0],   # tenir+couvert (profil gagnant à 66 % en M0a)
    "presser":  [-2.0, 1.0,  3.0, -1.0],   # contester par le feu, agressif
    "neutre":   [0.0,  0.0,  0.0,  0.0],
}
M1_POSTURES = list(M1_BIAS.keys())


def bias_tensor(name, device):
    return torch.tensor(M1_BIAS.get(name, M1_BIAS["neutre"]), device=device, dtype=torch.float32)


def serialize_state(env, i, camp):
    """État de l'env i, vu par `camp`, en texte court pour l'officier. Coalition à 3 = info clé : qui MÈNE."""
    alive = [int(env._alive(c)[i].sum().item()) for c in range(env.C)]
    ctrl = [float(env.ctrl_time[c][i].item()) for c in range(env.C)]
    leader = max(range(env.C), key=lambda c: ctrl[c])
    owner = int(env.cap_owner[i].item())
    capp = float(env.cap_prog[i].item())
    # rang de `camp` par contrôle (1 = en tête)
    rank = 1 + sum(1 for c in range(env.C) if ctrl[c] > ctrl[camp])
    lead_txt = " ".join("%s %.0f" % (NAMES[c], ctrl[c]) for c in range(env.C))
    eff_txt = " ".join("%s %d" % (NAMES[c], alive[c]) for c in range(env.C))
    cap_txt = ("%s capture %.0f/%d" % (NAMES[owner], capp, env.cap_need)) if owner >= 0 else "personne"
    return (
        "KOTH 3 factions, une colline centrale a tenir. Tu commandes %s.\n"
        "Controle (temps cumule): %s  -> LEADER = %s.\n"
        "Effectifs vivants: %s.\n"
        "Capture en cours: %s.\n"
        "Ton rang au controle: %d/%d.\n"
        "Postures possibles: %s.\n"
        "Principe: si tu MENES, les deux autres se liguent contre toi -> defendre. "
        "Si tu es DERRIERE, presser pour contester. Reponds par UNE seule posture."
        % (NAMES[camp], lead_txt, NAMES[leader], eff_txt, cap_txt, rank, env.C, ", ".join(M1_POSTURES))
    )


def parse_posture(text):
    """Texte du LLM -> posture valide. Robuste : cherche le mot-clé, sinon neutre."""
    t = (text or "").lower()
    # priorité au dernier mot-clé prononcé (le LLM conclut souvent)
    last = None; pos = -1
    for name, keys in (("defendre", ["defend", "défend", "défens", "defens", "tenir", "hold", "couvert"]),
                       ("presser",  ["press", "agress", "attaqu", "contest", "suppress", "offensi"]),
                       ("neutre",   ["neutre", "neutral", "observ", "attente"])):
        for k in keys:
            j = t.rfind(k)
            if j > pos: pos = j; last = name
    return last or "neutre"


if __name__ == "__main__":
    from koth_gpu import KothGPU
    DEV = "cuda:0"
    env = KothGPU(num_envs=8, device=DEV)
    ot = env.reset()
    # quelques pas aléatoires pour varier l'état
    for _ in range(20):
        acts = [torch.randint(0, env.n_actions, (env.N, env.A), device=DEV) for _ in range(env.C)]
        ot, _, _, _ = env.step(acts)
    print("===== TEST sérialiseur (env 0, vu par BLU) =====")
    print(serialize_state(env, 0, 0))
    print("\n===== TEST parseur (réponses LLM simulées) =====")
    samples = [
        "Je mène donc les autres vont me liguer dessus. Je joue defendre.",
        "Je suis en retard au contrôle, il faut presser pour contester la colline.",
        "Situation neutre, je reste en observation : neutre.",
        "I will hold my position and defend the hill.",
        "bla bla bla sans mot-clé clair",
    ]
    for s in samples:
        print("  %-60s -> %s" % (s[:58], parse_posture(s)))
