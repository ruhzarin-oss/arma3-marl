"""P2 cote GYMNASE : les memes segments, contre des boites 3D."""
import json, sys
import monde, los_boites

chemin = sys.argv[1] if len(sys.argv) > 1 else "batiment.json"
b = json.load(open(chemin))
m = monde.charger_pour_gymnase(chemin)
s = monde.points_de_sonde(b)

noms = list(s["segments"].keys())
A = [s["segments"][k][0] for k in noms]
B = [s["segments"][k][1] for k in noms]
res = los_boites.vue_degagee(m["boites"], A, B)
try:
    res = res.cpu().numpy()
except AttributeError:
    pass

print("GYM moteur      : %s" % ("torch" if los_boites.TORCH else "numpy"))
print("GYM boites      : %d" % len(m["boites"]))
print("GYM EMPREINTE   : %s" % m["empreinte"])
print("GYM arete=%d trumeau=%.3f" % (s["arete"], s["trumeau_m"]))
sortie = {}
for k, v in zip(noms, res):
    sortie[k] = bool(v)
    print("GYM   %-24s %s" % (k, bool(v)))
json.dump({"empreinte": m["empreinte"], "sondes": sortie},
          open("p2_gymnase.json", "w"), indent=1)
print("GYM ecrit -> p2_gymnase.json")
