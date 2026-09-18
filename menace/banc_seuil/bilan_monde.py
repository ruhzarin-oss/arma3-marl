import subprocess, re, sys
sys.argv = ["x"]; src = open("/mnt/c/hmt/tmp/lire_seuil_par_monde.py").read()
src = src[:src.index('print(f"{len(E)} episodes lus')]          # on reprend la lecture, pas l affichage
exec(src)
C = [e for e in E if e["valide"] and e["centre"]]; K = [e for e in C if e["connue"] is not None]; J = [e for e in C if e["connue"] is None]
print("centres valides", len(C), "| connus", len(K), "| jamais", len(J), "| refuses", sum(e["refuse"] for e in E), "| non centres valides", sum(1 for e in E if e["valide"] and not e["centre"]))
print("connus : distance", min(e["distance"] for e in K), "a", max(e["distance"] for e in K), "m | delai", min(e["connue"] for e in K), "a", max(e["connue"] for e in K), "s | mediane", sorted(e["connue"] for e in K)[len(K)//2], "s | mondes", sorted(set(e["monde"] for e in K)))
print("connus <= 8 s :", sum(1 for e in K if e["connue"] <= 8), "/", len(K), "| vis_moy des connus : min", min(e["vis_moy"] for e in K), "mediane", sorted(e["vis_moy"] for e in K)[len(K)//2], "max", max(e["vis_moy"] for e in K))
print("connus a vis_moy <= 0.01 :", [(e["monde"], e["distance"], e["connue"], e["vis_moy"], e["vis_max"]) for e in K if e["vis_moy"] <= 0.01])
print("jamais :", [(e["monde"], e["distance"], e["vis_moy"], e["vis_max"], e.get("hommes")) for e in J])
auc = sum((1 if a["vis_moy"] > b["vis_moy"] else 0.5 if a["vis_moy"] == b["vis_moy"] else 0) for a in K for b in J) / (len(K) * len(J))
print("aire sous la courbe, TOUS les centres valides ( vis_moy connus > jamais ) :", round(auc, 3))
import statistics
d1 = [e["connue"] for e in K if e["distance"] < 170]; d2 = [e["connue"] for e in K if e["distance"] >= 170]
print("delai moyen < 170 m :", round(statistics.mean(d1), 1), "s ( n =", len(d1), ") | >= 170 m :", round(statistics.mean(d2), 1), "s ( n =", len(d2), ")")
print("hommes avec vue < 10 :", [(e["monde"], e["distance"], e.get("hommes"), e["connue"]) for e in C if str(e.get("hommes")) not in ("10",)])
