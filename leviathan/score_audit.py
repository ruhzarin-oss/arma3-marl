"""score_audit — la recompense de l'officier peut-elle seulement SEPARER deux ordres ?

Audit fait AVANT de construire le banc, et sans Arma : c'est une propriete de la fonction, pas
du monde. On mesure la SENSIBILITE de `score_outcome` a chacun des 7 faits — combien le score
bouge quand un fait bouge d'une unite. Un fait dont la derivee est sous le bruit ne pourra
jamais porter d'apprentissage, quelle que soit la pression qu'on mette dans le theatre.

Seuil de reference : 0.05 (celui qui a servi pour E1/E3 sur KOTH).
"""
import sys
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from officer_memory import score_outcome, DOCTRINE

N_FOB, N_CIBLES, N_HOMMES = 25, 8, 480

BASE = {"cibles_intactes_frac": 1.0, "pertes_amies": 0, "fobs_tenus_frac": 1.0,
        "pertes_ennemies": 0, "exposition": 0}

print("=== doctrine en vigueur ===")
for k, v in DOCTRINE.items():
    print("  %-11s %.2f" % (k, v))
s0 = score_outcome(BASE)
print("\nscore d'une campagne de paix parfaite : %+.4f" % s0)
print("  (c'est le +1.25 qui sature 89 %% du journal : cibles 1.00 + terrain 0.25)")

print("\n=== SENSIBILITE : de combien le score bouge-t-il par unite ? ===")
print("  %-26s %-10s %-10s %s" % ("fait", "par unite", "pour 0.05", "verdict"))
tests = [
    ("1 cible vitale perdue (/8)", dict(cibles_intactes_frac=(N_CIBLES - 1) / N_CIBLES)),
    ("1 homme perdu (/480)",       dict(pertes_amies=1)),
    ("1 FOB perdu (/25)",          dict(fobs_tenus_frac=(N_FOB - 1) / N_FOB)),
    ("1 ennemi tue",               dict(pertes_ennemies=1)),
    ("exposition (binaire 0->1)",  dict(exposition=1)),
]
for nom, delta in tests:
    o = dict(BASE); o.update(delta)
    d = abs(score_outcome(o) - s0)
    n_pour_seuil = (0.05 / d) if d > 0 else float("inf")
    verdict = "OK" if d >= 0.05 else ("faible" if d >= 0.02 else "SOUS LE BRUIT")
    print("  %-26s %-10.4f %-10s %s"
          % (nom, d, ("%.1f" % n_pour_seuil) if d > 0 else "jamais", verdict))

print("\n=== PLAGE TOTALE de chaque terme (du meilleur au pire cas) ===")
extremes = [
    ("cibles : 8/8 -> 0/8",   dict(cibles_intactes_frac=0.0)),
    ("terrain : 25/25 -> 0/25", dict(fobs_tenus_frac=0.0)),
    ("pertes amies : 0 -> 100", dict(pertes_amies=100)),
    ("pertes ennemies : 0 -> 50", dict(pertes_ennemies=50)),
    ("exposition : 0 -> 1",   dict(exposition=1)),
]
for nom, delta in extremes:
    o = dict(BASE); o.update(delta)
    print("  %-28s amplitude %.3f" % (nom, abs(score_outcome(o) - s0)))

print("\n=== CE QUE CA IMPOSE AU BANC ===")
print("  Un ordre ne peut se distinguer d'un autre que par les faits dont la derivee depasse")
print("  le seuil. La pression doit donc frapper CES faits-la, pas seulement contester du terrain.")
