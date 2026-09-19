"""Que fait reellement l option ATTENDRE, dans chaque bras ? ( semantique de l option, pas effet sur l issue )"""
src = open("/mnt/data/hmt/depot/menace/banc_seuil/lire_p2_types.py").read()
ns = {"__name__": "audit"}
exec(compile(src[:src.index("prevus = 8 * 2 * 2 * 4")], "lp2", "exec"), ns)
A = [e for e in ns["E"] if e["verdict"] == "ACCEPTE"]
from collections import Counter
import statistics as st
print("== ce que devient le choix, par bras et par option ==")
for b in ("PATROUILLE", "POSTE"):
    for o, nom in ((1, "TOUT_DE_SUITE"), (2, "ATTENDRE")):
        L = [e for e in A if e["bras"] == b and e["option"] == o]
        at = [e["attente"] for e in L if e.get("attente") is not None and e["attente"] >= 0]
        print(f"   {b:11s} {nom:14s} n {len(L):3d} : {Counter(e.get('detail') for e in L).most_common(4)}")
        if at: print(f"                                  attente reelle : mediane {st.median(at):.0f} s, de {min(at)} a {max(at)} s")
print("\n== le vehicule de patrouille est-il vu au moment du choix ? ==")
for b in ("PATROUILLE", "POSTE"):
    L = [e for e in A if e["bras"] == b and e.get("vehicule_vu") is not None]
    print(f"   {b:11s} : vehicule vu dans {sum(1 for e in L if e['vehicule_vu']) }/{len(L)} episodes")
print("\n== menace percue au moment du choix, par bras et option ==")
for b in ("PATROUILLE", "POSTE"):
    for o, nom in ((1, "TOUT_DE_SUITE"), (2, "ATTENDRE")):
        L = [e for e in A if e["bras"] == b and e["option"] == o and e["percue"] is not None]
        print(f"   {b:11s} {nom:14s} : percue > 0 dans {sum(1 for e in L if e['percue'] > 0)}/{len(L)}")
