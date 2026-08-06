#!/usr/bin/env python3
"""patch_loi_predicteur.py — LE PREDICTEUR DEVIENT LA LOI DU MONDE.

Decisions deposees AVANT ce code : CRITERES_LOI_PREDICTEUR.md (commit cbee4fa).

  1. HORIZON        p30 = sortie du predicteur (mort a 30 s, appris sur 563 383 observations)
                    p_pas = 1 - (1 - p30)^(1/9,1)     9,1 pas = 30 s / 3,28 s le pas
                    Maillon ASSUME : taux constant sur la fenetre. Monotone, donc il peut
                    fausser l amplitude, JAMAIS le sens. Sa cage : le pouls v3 journalisera
                    le delai avant la mort.
  2. LA FLAMME      a l ENTRAINEMENT la mort pondere, elle ne se tire pas. L agent porte une
                    flamme ; chaque pas risque en mange une part ; tout ce qu il gagne est
                    pese par ce qui reste. Traverser un etat a 50 % de mort divise par deux
                    l esperance d arriver : le plein tarif, a chaque passage.
  3. LES DES        au JUGEMENT la mort se tire au sort (--des). On entraine sur la flamme,
                    on certifie aux des, et l ecart entre les deux se rapporte.
  4. PLUS DE TARIF  le terme de risque etait un echafaudage pour un monde sans mort. Le
                    garder serait compter deux fois. RECOMPENSE = ARRIVER.
  5. EMPREINTE      le monde imprime son empreinte au demarrage. Le juge refusera de comparer
                    des bras aux empreintes differentes.

LA CHAINE FAITE MAIN MEURT ICI. Elle composait des maillons vrais en un organisme faux :
mortalite 7,42 fois trop forte sur du semblable, et pente de SIGNE OPPOSE au corpus.
Ses constantes restent mesurees et resserviront ailleurs ; sa composition, non.
"""
import pathlib, hashlib

P = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = P.read_text(encoding='utf-8')

# ---------------------------------------------------------------- 1. la loi
ANC = "def degats_du_pas(p_xy, post_poids, idx):"
NEUF = '''PAS_PAR_FENETRE = 30.0 / 3.28        # 9,15 pas — la conversion MESUREE
MODE_DES = '--des' in sys.argv       # jugement : la mort se TIRE. Entrainement : elle PONDERE.

def p_mort_du_pas(p_xy, post_poids, idx):
    """probabilite de mourir PENDANT CE PAS, tiree du predicteur appris sur Arma. (B,)

    Le predicteur rend « mort dans les 30 s ». Taux constant sur la fenetre — le maillon
    assume, monotone donc sans effet sur le SENS de la pente."""
    p30 = risque(p_xy, None, idx, post_poids).clamp(1e-6, 1 - 1e-6)
    return 1.0 - (1.0 - p30) ** (1.0 / PAS_PAR_FENETRE)

# ---- LA CHAINE FAITE MAIN, MORTE le 06/08. Conservee pour memoire, plus jamais appelee.
def degats_du_pas(p_xy, post_poids, idx):'''
assert t.count(ANC) == 1, "ancre degats_du_pas"
t = t.replace(ANC, NEUF, 1)

# ---------------------------------------------------------------- 2. la flamme dans la boucle
A2 = """        # ---- ON PEUT MOURIR. C est la reparation du 06/08. ----
        # Les degats s accumulent au tarif MESURE sur Arma ; au seuil de 0,70 (trois impacts)
        # l homme est neutralise : il cesse d avancer et il n arrivera pas.
        deg = deg + degats_du_pas(p, wp, idx) * dehors
        vivant = (deg < SEUIL_MORT).float()
        mort_ici = dehors * (1.0 - vivant)
        tues = tues + mort_ici
        dehors = dehors * vivant"""
N2 = """        # ---- LA FLAMME. La mort vient du PREDICTEUR, pas d une chaine faite main. ----
        # A l entrainement elle PONDERE : la flamme descend en pente douce et le gradient la
        # suit. Au jugement (--des) elle se TIRE : le monde redevient stochastique.
        pm = p_mort_du_pas(p, wp, idx)
        if MODE_DES:
            pris = (torch.rand_like(pm) < pm).float()
            tues = tues + dehors * pris
            dehors = dehors * (1.0 - pris)
        else:
            flamme = flamme * (1.0 - pm * dehors)
            tues = tues + 0.0     # aux des seulement ; ici la flamme EST le compte"""
assert t.count(A2) == 1, "ancre de la mort"
t = t.replace(A2, N2, 1)

# ---------------------------------------------------------------- 3. les compteurs
A3 = """    deg = torch.zeros(B, device=dev)          # degats cumules, seuil de mort a 0,70
    tues = torch.zeros(B, device=dev)         # combien sont tombes, et quand"""
N3 = """    deg = torch.zeros(B, device=dev)          # (mort) heritage de la chaine faite main
    tues = torch.zeros(B, device=dev)         # combien sont tombes (mode --des)
    flamme = torch.ones(B, device=dev)        # LA FLAMME : probabilite d etre encore en vie"""
assert t.count(A3) == 1, "ancre des compteurs"
t = t.replace(A3, N3, 1)

# ---------------------------------------------------------------- 4. la recompense
A4 = "        val_l.append(val); rec_l.append(-tarif*d_pic + 0.05*gagne)"
N4 = ("        # RECOMPENSE = ARRIVER. Plus de terme de risque : c etait un echafaudage pour un\n"
      "        # monde sans mort, et le garder maintenant compterait deux fois. Les metres\n"
      "        # gagnes sont peses par la flamme — on ne gagne du terrain que vivant.\n"
      "        val_l.append(val); rec_l.append(0.05*gagne*flamme)")
assert t.count(A4) == 1, "ancre de la recompense"
t = t.replace(A4, N4, 1)

A5 = "        arrive = arrive + vient; dehors = dehors*(1-vient)"
N5 = ("        arrive = arrive + vient*flamme; dehors = dehors*(1-vient)\n"
      "        # arriver ne compte que si l on est encore la : l ARRIVEE EST UNE ESPERANCE.")
assert t.count(A5) == 1, "ancre de l arrivee"
t = t.replace(A5, N5, 1)

# ---------------------------------------------------------------- 5. l empreinte du monde
A6 = "print(\"\\n\" + \"=\"*78, flush=True)"
emp = hashlib.md5(t.encode()).hexdigest()[:12]
N6 = ('import hashlib as _h\n'
      '_EMPREINTE = _h.md5(open(__file__, "rb").read()).hexdigest()[:12]\n'
      'print(f"EMPREINTE DU MONDE {_EMPREINTE}"\n'
      '      f"   mort = PREDICTEUR APPRIS (AUC {_ck[\'auc\']:.4f})"\n'
      '      f"   {\'DES\' if MODE_DES else \'FLAMME\'}", flush=True)\n'
      '# La barriere nee de ma faute du 06/08 : un juge REFUSE de comparer des bras aux\n'
      '# empreintes differentes. Detection, pas prevention.\n'
      + A6)
assert t.count(A6) == 1, "ancre du bandeau"
t = t.replace(A6, N6, 1)

P.write_text(t, encoding='utf-8')
print("loi-predicteur installee — flamme a l entrainement, des au jugement, recompense = arriver")
