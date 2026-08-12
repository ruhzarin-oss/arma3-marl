"""officer_task — la TACHE de l'officier, REFAITE pour que le CHOIX COMPTE.

======================================================================================
POURQUOI L'ANCIENNE ETAIT PLATE (officer_verify.py + play_blu : les 3 postures a ~0.243)
======================================================================================
CINQ causes, toutes mesurees sur le code d'origine, chacune suffisante a elle seule :

  1. LE MONDE N'INSTANCIE PAS LA SITUATION. Le prompt annonce « tu es rang d/3 » mais
     play_blu appelle toujours le meme reset avec seed=0 : les 3 prompts tournent dans le
     MEME monde. L'officier est interroge sur une situation qui n'existe pas.

  2. L'ORDRE NE PORTE QUE SUR UNE FRACTION DES PAS. Le biais n'etait applique que la ou le
     rang courant egalait le rang demande — un ordre qui ne s'applique presque jamais.

  3. L'EPISODE FACONNE PAR L'ORDRE ETAIT JETE. T=180 alors que max_steps=120, avec
     auto_reset : au pas 120 tout repart a zero et le ctrl_time lu a la fin ne couvre que
     60 pas d'un episode NEUF.

  4. LE SCORE CONFOND « NUL » ET « DEFAITE ». Mesure ici : de 14 % a 52 % des episodes
     finissent NULS (attrition_win=False : s'entretuer ne fait gagner personne). Une part de
     temps-zone, ou un taux de victoire seul, ecrase ces 40 % dans le meme sac que les
     defaites et detruit toute resolution.

  5. LE BIAIS PLEINE PUISSANCE ECRASE UNE POLITIQUE DEJA ENTRAINEE. Mesure : a gain 1.0
     TOUTES les postures font PIRE que ne rien ordonner. Le menu entier de l'officier etait
     nuisible. A gain 0.5 elles modulent au lieu d'ecraser — et la, elles gagnent.

  Consequence : variance de recompense nulle -> « advantage collapse » dans GRPO
  (A_i = (r_i - moyenne)/ecart-type = 0) -> gradient EXACTEMENT nul. L'apprentissage nul du
  18/06 n'etait ni un manque de steps ni de la malchance : c'etait de l'arithmetique.

======================================================================================
CE QUI CHANGE
======================================================================================
  - la SITUATION est instanciee dans le monde (avance au controle + usure), pas seulement
    affirmee dans le prompt ;
  - l'ordre est PERMANENT : applique a tous les pas de l'episode ;
  - episode COMPLET, auto_reset=False, verdict fige au premier « done » ;
  - SCORE = victoire - defaite, dans [-1, +1]. Un nul vaut zero, ce qu'il est. C'est ce
    changement qui rend la plage dynamique utilisable (ecart mesure x4 sur « serre ») ;
  - GAIN 0.5 sur le biais : l'ordre module la politique, il ne la remplace pas.

L'HYPOTHESE, ecrite AVANT de mesurer :
  avance -> tenir/priver (defendre ou harceler) : on protege l'avance, on ne depense pas d'hommes
  serre  -> prendre_colline : il FAUT du temps-zone pour se detacher
  retard -> prendre_colline : rien d'autre ne rattrape

CE QUI FERAIT ECHOUER LA TACHE (criteres poses AVANT le run) :
  E1. ecart max-min entre postures < 0.05 dans une situation -> encore plate, gradient nul.
  E2. la MEME posture optimale partout -> « toujours dire X » gagne, l'officier n'a aucune
      raison de LIRE la situation : un LLM ne pourra jamais montrer de gain.
  E3. VALEUR DU CHOIX SITUE = moyenne(meilleure posture par situation)
                            - max_posture(moyenne de cette posture sur les situations)
      C'est le PLAFOND de ce qu'un officier peut gagner en lisant la situation. Sous 0.05,
      NO-GO : aucun fine-tuning ne peut rapporter quoi que ce soit.
  CONTROLE POSITIF : « neutre » (gain nul) est dans le tableau. Si aucune posture ne le bat
      nulle part, le menu d'ordres est nuisible et c'est le MENU qu'il faut refaire, pas
      l'algorithme. C'est exactement ce qui se passait a gain 1.0.

Usage :
  cd /home/younes/arma3-marl
  CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 ./.venv/bin/python officer_task.py --grid
"""
import sys, argparse
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from koth_gpu import KothGPU, POSTURES
from train_koth_gpu import Net

DEV = "cuda:0"
CKPT = "/home/younes/arma3-marl/league_maneuver_learner.pt"
POST = ["prendre_colline", "defendre", "harceler", "neutre"]   # neutre = controle positif
GAIN = 0.5      # cf. cause 5 : a 1.0 le biais ecrase la politique gelee

SITUATIONS = {
    "avance": dict(lead=+96.0, usure=0.00),   # BLU mene d'un ecart = l'ecart naturel de fin
    "serre":  dict(lead=0.0,   usure=0.00),   # tout le monde a egalite
    "retard": dict(lead=-45.0, usure=0.00),   # le camp 1 mene
}

_rl = None
def brain():
    global _rl
    if _rl is None:
        net = Net(10, 4, 512, 3).to(DEV)
        net.load_state_dict(torch.load(CKPT, map_location=DEV))
        net.eval()
        for p in net.parameters():
            p.requires_grad_(False)
        _rl = net
    return _rl


def make_env(n, seed):
    # attrition_win=False : exterminer n'est PAS une victoire, il faut TENIR la colline.
    # timeout_decisive=True : a l'expiration, le plus de temps-zone gagne.
    return KothGPU(num_envs=n, attrition_win=False, timeout_decisive=True, device=DEV, seed=seed)


def instancier(env, lead, usure):
    """Met le MONDE dans la situation annoncee. C'est ce qui manquait a l'ancienne tache.

    lead<0 : UN SEUL adversaire (camp 1) mene. Donner l'avance aux deux ecrase BLU au
    plancher (mesure : 0.06 de victoire) et recree une variance nulle par saturation basse.
    usure : degats prealables sur tous les agents BLU. On BLESSE, on ne TUE pas : avec A=3 et
    secure_n=2, tuer un homme rend la securisation quasi impossible (mesure : 0.014).
    """
    if lead > 0:
        env.ctrl_time[0] += lead
    elif lead < 0:
        env.ctrl_time[1] += -lead
    if usure > 0:
        env.dmg[0] = env.dmg[0] + usure


@torch.no_grad()
def jouer(posture, situation, n=4096, seed=0):
    """Un episode COMPLET, ordre permanent. Rend (score, victoire, defaite, nul, survie)."""
    rl = brain()
    env = make_env(n, seed)
    ot = list(env.reset())
    instancier(env, **SITUATIONS[situation])
    bias = torch.tensor(POSTURES[posture], device=DEV, dtype=torch.float32) * GAIN
    winner = torch.full((n,), -2, dtype=torch.long, device=DEV)   # -2 = pas encore fini
    encours = torch.ones(n, dtype=torch.bool, device=DEV)
    for _ in range(env.max_steps):
        acts = []
        for c in range(env.C):
            lg = rl.a_logits(ot[c])
            if c == 0:
                lg = lg + bias                                    # ORDRE PERMANENT
            acts.append(torch.distributions.Categorical(logits=lg).sample())
        ot, _, done, info = env.step(acts, auto_reset=False)      # PAS de reset
        ot = list(ot)
        fini = done > 0.5
        neuf = encours & fini
        winner = torch.where(neuf, info["winner"], winner)        # verdict FIGE au premier done
        encours = encours & ~fini
    winner = torch.where(encours, torch.full_like(winner, -1), winner)
    vict = float((winner == 0).float().mean())
    defa = float((winner > 0).float().mean())
    nul = float((winner < 0).float().mean())
    surv = float(env._alive(0).float().mean())
    return vict - defa, vict, defa, nul, surv       # SCORE = victoire - defaite


PROMPTS = {
    "avance": "KOTH 3 factions. Tu commandes BLU. Tu MENES au temps de controle avec une avance "
              "nette. Ta force est intacte. Postures : prendre_colline / defendre / harceler. "
              "Reponds par UNE seule posture.",
    "serre":  "KOTH 3 factions. Tu commandes BLU. Les trois camps sont a EGALITE au temps de "
              "controle. Ta force est intacte. Postures : prendre_colline / defendre / harceler. "
              "Reponds par UNE seule posture.",
    "retard": "KOTH 3 factions. Tu commandes BLU. Un adversaire te DEVANCE nettement au temps de "
              "controle. Ta force est intacte. Postures : prendre_colline / defendre / harceler. "
              "Reponds par UNE seule posture.",
}


def grid(n=4096, seeds=(0, 1, 2), detail=True):
    print("=== GRILLE situation x posture — SCORE = victoire - defaite  (gain %.2f) ===" % GAIN)
    print("    n=%d envs x %d graines, episode complet, ordre permanent\n" % (n, len(seeds)))
    tab = {}
    hdr = "%-10s" % "situation" + "".join("%18s" % p for p in POST)
    print(hdr); print("-" * len(hdr))
    brut = {}
    for s in SITUATIONS:
        ligne = "%-10s" % s
        for p in POST:
            runs = [jouer(p, s, n=n, seed=k) for k in seeds]
            m = sum(r[0] for r in runs) / len(runs)
            et = (max(r[0] for r in runs) - min(r[0] for r in runs)) / 2
            tab[(s, p)] = m
            brut[(s, p)] = runs[0]
            ligne += "%13.3f±%.3f" % (m, et)
        print(ligne, flush=True)

    if detail:
        print("\n--- detail graine 0 : victoire / defaite / NUL / survie ---")
        for s in SITUATIONS:
            for p in POST:
                _, v, d, nl, su = brut[(s, p)]
                print("  %-10s %-16s  v=%.3f  d=%.3f  nul=%.3f  survie=%.3f" % (s, p, v, d, nl, su))

    print("\n=== LECTURE ===")
    ecarts = []
    for s in SITUATIONS:
        vals = {p: tab[(s, p)] for p in POST}
        best = max(vals, key=vals.get); worst = min(vals, key=vals.get)
        ec = vals[best] - vals[worst]; ecarts.append(ec)
        print("  %-10s meilleure=%-16s (%+.3f)  pire=%-16s (%+.3f)  ECART %.3f"
              % (s, best, vals[best], worst, vals[worst], ec))

    par_situ = sum(max(tab[(s, p)] for p in POST) for s in SITUATIONS) / len(SITUATIONS)
    fixe = max(sum(tab[(s, p)] for s in SITUATIONS) / len(SITUATIONS) for p in POST)
    meilleure_fixe = max(POST, key=lambda p: sum(tab[(s, p)] for s in SITUATIONS))
    valeur = par_situ - fixe
    argmax = {s: max(POST, key=lambda p: tab[(s, p)]) for s in SITUATIONS}
    bat_neutre = [(s, p) for s in SITUATIONS for p in POST if p != "neutre" and tab[(s, p)] > tab[(s, "neutre")]]

    print("\n=== VERDICT (criteres poses AVANT le run) ===")
    print("  E1 ecart minimum sur les situations : %.3f  -> %s"
          % (min(ecarts), "OK" if min(ecarts) >= 0.05 else "ECHEC (tache encore plate)"))
    print("  E2 postures optimales : %s" % argmax)
    print("     -> %s" % ("OK (elles different selon la situation)" if len(set(argmax.values())) > 1
                          else "ECHEC (une seule posture gagne partout)"))
    print("  CONTROLE POSITIF : %d cases sur %d battent 'neutre' -> %s"
          % (len(bat_neutre), len(SITUATIONS) * (len(POST) - 1),
             "OK (le menu d'ordres sert)" if bat_neutre else "ECHEC (le menu entier est nuisible)"))
    print("  E3 VALEUR DU CHOIX SITUE : %.3f" % valeur)
    print("     (choix par situation %+.3f  -  meilleure posture fixe '%s' %+.3f)"
          % (par_situ, meilleure_fixe, fixe))
    print("     -> %s" % ("GO : il y a de quoi apprendre" if valeur >= 0.05
                          else "NO-GO : aucun fine-tuning ne peut rapporter"))
    return tab


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("-n", type=int, default=4096)
    a = ap.parse_args()
    grid(a.n)
