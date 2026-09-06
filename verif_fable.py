#!/usr/bin/env python3
"""verif_fable — LES TROIS VERIFICATIONS IMPOSEES AVANT DEPOT.

V1. Le cap aleatoire de S3 est-il retire A CHAQUE DECISION ? (j ai deja paye une fois pour
    une permutation fixe : elle valait 3,9 points, dans le mauvais sens)
V2. Le 91,0 % tient-il sur des graines JAMAIS VUES ? C est le max d une grille lue sur ses
    propres graines de selection — optimiste par construction.
V3. « Tout ce qui fige coute » : DOSE-REPONSE D IMMOBILITE. On injecte dans le maitre gagnant
    des pauses forcees de 0, 1, 2, 4 pas a instants aleatoires, rien d autre ne change.
    Si le cout monte avec la dose, le motif est causal ; sinon mes trois ablations avaient
    trois causes et le motif meurt.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import jouer_phi2
from distillation import cible_shamal

DEV = "cuda:0"
NEUVES = [301, 302, 303, 304, 305, 306]          # ni apprises, ni choisies, ni jugees jusqu ici

print("=" * 92); print(" V1 · LE CAP ALEATOIRE EST-IL RETIRE A CHAQUE DECISION ?"); print("=" * 92)
e = B.monde(512, 11); e.reset()
a1 = cible_shamal(e, hasard=True); a2 = cible_shamal(e, hasard=True)
diff = float((a1 != a2).float().mean())
print("  deux appels sur le MEME etat different sur %.1f %% des hommes" % (100 * diff))
print("  -> %s" % ("OK, le tirage est refait a chaque appel" if diff > 0.5 else
                   "⛔ TIRAGE FIGE — le controle porte un biais directionnel constant"))

def juge(nom, f, graines, n=256):
    pr, sv, dh, tn = [], [], [], []
    for g in graines:
        e = B.monde(n, g)
        st, *_ = jouer_phi2(e, lambda o, t, _e=e: (f(_e, t), None, None), w_phi=0.0)
        pr.append(st["prise"]); sv.append(st["survivants"])
        dh.append(st["danger_homme_pas"]); tn.append(st["metres_tenus"])
    m = lambda v: sum(v) / len(v)
    print("  %-38s %5.1f %%  [%4.1f;%4.1f]  tenus %6.1f m  survivants %.2f"
          % (nom, m(pr), min(pr), max(pr), m(tn), m(sv)))
    return m(pr)

print("\n" + "=" * 92); print(" V2 · LE MAITRE SUR DES GRAINES JAMAIS VUES : " + str(NEUVES)); print("=" * 92)
p_test = juge("maitre v2, graines de JUGEMENT (deja vues)", lambda e, t: cible_shamal(e), B.GRAINES_TEST)
p_neuf = juge("maitre v2, graines NEUVES", lambda e, t: cible_shamal(e), NEUVES)
juge("reference A — doctrine `flanc` du depot", lambda e, t: B.flanc(e, t), NEUVES)
juge("doctrine `frontal` du depot", lambda e, t: B.frontal(e, t), NEUVES)
print("\n  ecart graines vues / graines neuves : %+.1f point" % (p_neuf - p_test))
print("  -> %s" % ("le chiffre TIENT hors selection, il est deposable" if abs(p_neuf - p_test) < 5
                   else "⚠️ le max de grille etait OPTIMISTE : deposer le chiffre des graines NEUVES"))

print("\n" + "=" * 92); print(" V3 · DOSE-REPONSE D IMMOBILITE — le motif est-il causal ?"); print("=" * 92)
print("  on fige l homme `dose` pas apres chaque decision, a instants aleatoires. Rien d autre.")
def fige(dose, seed):
    g = torch.Generator(device=DEV).manual_seed(seed)
    etat = {}
    def f(e, t):
        a = cible_shamal(e)
        if dose == 0: return a
        cle = id(e)
        if cle not in etat: etat[cle] = torch.zeros(e.N, e.A, device=e.dev)
        reste = etat[cle]
        # ceux dont le compteur est chaud restent immobiles (action 8 = TENIR)
        gele = reste > 0
        etat[cle] = (reste - 1).clamp(min=0)
        # on declenche une pause chez ~1 homme sur 8 par pas
        neuf = (torch.rand(e.N, e.A, device=e.dev, generator=g) < 0.125) & ~gele
        etat[cle] = torch.where(neuf, torch.full_like(reste, float(dose)), etat[cle])
        return torch.where(gele | neuf, torch.full_like(a, 8), a)
    return f
base = None
for dose in (0, 1, 2, 4):
    p = juge("pause forcee de %d pas" % dose, fige(dose, 7 + dose), B.GRAINES_TEST)
    if dose == 0: base = p
    else: print("      -> cout %+.1f point" % (p - base))
print("\n  LECTURE : si le cout CROIT avec la dose, « tout ce qui fige coute » devient causal")
print("            dans ce monde. S il est plat ou desordonne, mes trois ablations avaient")
print("            trois causes distinctes, et le motif meurt.")
