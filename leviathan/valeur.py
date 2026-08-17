#!/usr/bin/env python3
"""valeur.py — ÉTAPE 1 : le REJEU INVERSÉ, et la fonction de valeur qu'il produit.

Le blocage mesuré : un décideur glouton ne peut PAS exécuter un détour. Chaque pas qui éloigne
paraît mauvais sur l'instant, donc il fait demi-tour — même si le détour était le bon plan.

Le correctif (mécanisme du rejeu hippocampique) : on remonte chaque partie GAGNÉE **à l'envers,
depuis l'objectif**. La valeur redescend de proche en proche. Les pas de détour cessent
mécaniquement de paraître mauvais : ils deviennent « la chaîne qui a mené à la victoire ».

RÉCOMPENSE — celle trouvée le 25/07, et qui ne se triche pas :
   se terrer      -> aucun mètre gagné -> coût infini
   foncer bêtement-> beaucoup d'exposition pour peu de terrain
   MANŒUVRER      -> beaucoup de terrain pour peu d'exposition   <- la seule qui marque

ÉTAT (délibérément petit : on a 36 parties, pas 36 000) :
   distance à l'objectif · exposition ici · couvert · alliés vivants · mes dégâts · j'avance ou j'appuie

Usage : python valeur.py            (entraîne + vérifie sur des parties JAMAIS VUES)
"""
import sys, os, json, glob, math, random
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import intentions as IN

LEV = "/home/younes/arma3-marl/leviathan"
GAMMA = 0.97          # patience : à quel point l'agent prend en compte le futur lointain
terr = IN.charger_terrain(LEV, "Altis", 16781, 12604)


def etat(px, py, expo, couvert, allies, degats, intent):
    """La situation, vue par le soldat. Normalisée pour que rien n'écrase le reste."""
    d = math.hypot(px, py)
    return [min(d / 160.0, 1.5),                       # loin / près de l'objectif
            expo,                                       # suis-je vu, ici et maintenant
            min(couvert / 30.0, 1.0),                   # ai-je du bâti autour
            allies / 12.0,                              # combien de camarades debout
            degats,                                     # mon état
            1.0 if intent == IN.AVANCER else 0.0,       # je progresse
            1.0 if intent == IN.APPUYER else 0.0]       # je couvre


NOMS_ETAT = ["distance", "exposition", "couvert", "alliés", "dégâts", "j'avance", "j'appuie"]


def transitions(path):
    """Déroule une partie -> une liste d'états + la récompense de chaque pas.
    La récompense est le COÛT DU PROGRÈS : mètres gagnés moins l'exposition payée."""
    d = json.load(open(path))
    fx, fy = d["fob"]; F = d["frames"]; m = d["metrics"]
    n = len(F[0]["west"])
    out = []
    for k in range(len(F) - 1):
        f, g = F[k], F[k + 1]
        est = [(e[0] - fx, e[1] - fy) for e in f.get("east", []) if len(e) < 3 or e[2]]
        vivants = [i for i in range(n) if f["west"][i][2]]
        na = len(vivants)
        for i in vivants:
            w = f["west"][i]; px, py = w[0] - fx, w[1] - fy
            vu = 1.0 if any(terr.los(px, py, ex, ey) for ex, ey in est) else 0.0
            it = f.get("intent", [0] * n)[i]
            s = etat(px, py, vu, terr.cover_at(px, py), na, w[3] if len(w) > 3 else 0.0, it)
            # récompense du pas : terrain gagné vers l'objectif, moins ce que l'exposition a coûté
            _mort = 0.0
            if g["west"][i][2]:
                qx, qy = g["west"][i][0] - fx, g["west"][i][1] - fy
                gagne = math.hypot(px, py) - math.hypot(qx, qy)
            else:
                # REVUE 17/08 : la mort ne coûtait que -8/14 - 0,35 ~ -0,92 UNE SEULE FOIS,
                # quand tenir vingt pas à découvert coûte 20 x 0,35 = -7,0. Le retour d'un
                # homme exposé qui meurt vite était donc PLUS ÉLEVÉ que celui d'un homme qui
                # tient : la valeur apprenait que mourir est bon. La mort paie désormais AU
                # MOINS ce que le pire survivant paierait sur les pas qui lui restaient.
                gagne = -8.0                       # tombé : c'est cher
                _mort = 0.35 * ((len(F) - 1) - k)  # les pas qu'il ne paiera pas
            r = (gagne / 14.0) - 0.35 * vu - _mort # le coût par mètre, converti en récompense de pas
            out.append((s, r, i, k))
    # bonus terminal : avoir pris l'objectif, et l'avoir pris avec du monde debout
    if m.get("took"):
        survie = (m.get("nag", 12) - m.get("west_losses", 0)) / max(m.get("nag", 12), 1)
        for j in range(len(out)):
            # REVUE 17/08 : `k` va de 0 a len(F)-2, donc `>= len(F)-3` attrapait DEUX
            # images par soldat : le bonus terminal etait verse deux fois (+6 au lieu
            # de +3) et ecrasait le cout d exposition accumule.
            if out[j][3] == len(F) - 2:
                out[j] = (out[j][0], out[j][1] + 3.0 * survie, out[j][2], out[j][3])
    return out, bool(m.get("took"))


def rejeu_inverse(trans):
    """LE MÉCANISME : on remonte la partie DEPUIS LA FIN. Le retour se propage vers l'arrière,
    donc les pas de détour héritent de la valeur de ce qu'ils ont permis."""
    par_soldat = {}
    for s, r, i, k in trans:
        par_soldat.setdefault(i, []).append((k, s, r))
    X, Y = [], []
    for i, L in par_soldat.items():
        L.sort(key=lambda t: t[0])
        retour = 0.0
        for k, s, r in reversed(L):        # <- à l'envers, depuis l'objectif
            retour = r + GAMMA * retour
            X.append(s); Y.append(retour)
    return X, Y


# ---------------- construction de la banque ----------------
parties = sorted(glob.glob(os.path.join(LEV, "banque/ex_*.json")))
random.seed(3); random.shuffle(parties)
n_test = max(6, len(parties) // 5)
test, train = parties[:n_test], parties[n_test:]
print("=== REJEU INVERSÉ | %d parties d'entraînement, %d de VÉRIFICATION (jamais vues) ===" % (len(train), len(test)), flush=True)

def banque(liste, label):
    X, Y, gagnees = [], [], 0
    for p in liste:
        tr, pris = transitions(p)
        gagnees += pris
        x, y = rejeu_inverse(tr)
        # PRIORISATION : les victoires sont rares et instructives -> on les rejoue plus souvent
        poids = 3 if pris else 1
        for _ in range(poids):
            X += x; Y += y
    print("  %s : %d parties (%d gagnées) -> %d situations" % (label, len(liste), gagnees, len(X)), flush=True)
    return np.array(X, dtype="float32"), np.array(Y, dtype="float32")

Xtr, Ytr = banque(train, "entraînement")
Xte, Yte = banque(test, "vérification")

# ---------------- apprentissage : modèle VOLONTAIREMENT petit ----------------
mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
A = np.hstack([(Xtr - mu) / sd, np.ones((len(Xtr), 1), dtype="float32")])
B = np.hstack([(Xte - mu) / sd, np.ones((len(Xte), 1), dtype="float32")])
w, *_ = np.linalg.lstsq(A, Ytr, rcond=None)

def r2(pred, vrai):
    return 1.0 - ((pred - vrai) ** 2).sum() / max(((vrai - vrai.mean()) ** 2).sum(), 1e-9)

r2_tr, r2_te = r2(A @ w, Ytr), r2(B @ w, Yte)
print("\n=== LA VALEUR PRÉDIT-ELLE ? ===", flush=True)
print("  sur ce qu'il a appris   : %.3f" % r2_tr, flush=True)
print("  sur des parties INÉDITES: %.3f   <- c'est CE chiffre qui décide" % r2_te, flush=True)
verdict = ("elle GÉNÉRALISE -> on peut la brancher dans la décision" if r2_te > 0.15 else
           "elle ne généralise PAS -> NE PAS brancher (Fable : une valeur peu fiable EMPIRE les choses)")
print("  >>> %s" % verdict, flush=True)

print("\n=== CE QUE L'AGENT A COMPRIS (poids appris) ===", flush=True)
for nom, poids in sorted(zip(NOMS_ETAT, w[:-1]), key=lambda t: -abs(t[1])):
    sens = "AUGMENTE la valeur" if poids > 0 else "la DIMINUE"
    print("  %-12s %+7.3f   %s" % (nom, poids, sens), flush=True)

np.savez(os.path.join(LEV, "valeur_v1.npz"), w=w, mu=mu, sd=sd, r2_test=r2_te, gamma=GAMMA)
print("\n-> %s/valeur_v1.npz" % LEV, flush=True)
print("VALEUR_DONE", flush=True)
