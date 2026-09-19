"""Audit de conformite de CHOIX-P2-TYPES-19-09. On regarde le DISPOSITIF et les PERCEPTIONS, jamais l effet par bras."""
src = open("/mnt/data/hmt/depot/menace/banc_seuil/lire_p2_types.py").read()
ns = {"__name__": "audit"}
exec(compile(src[:src.index("prevus = 8 * 2 * 2 * 4")], "lp2", "exec"), ns)
E = ns["E"]; A = [e for e in E if e["verdict"] == "ACCEPTE"]
import statistics as st
from collections import Counter

def part(L, f): return (sum(1 for e in L if f(e)) / len(L)) if L else float("nan")

print(f"== {len(E)} episodes, {len(A)} acceptes\n")
print("1. PERCEPTION AU MOMENT DU CHOIX, par bras ( instrument, pas effet )")
for b in ("PATROUILLE", "POSTE"):
    L = [e for e in A if e["bras"] == b and e["percue"] is not None]
    print(f"   {b:11s} n {len(L):3d} : percue > 0 dans {part(L, lambda e: e['percue'] > 0):5.0%} ; "
          f"connue ( niveau 2 ) dans {part(L, lambda e: e['percue'] == 2):5.0%} ; "
          f"vehicule vu dans {part(L, lambda e: e.get('vehicule_vu')):5.0%}")
print("\n2. LE CHOIX EST-IL JOUE ? ( attente reelle par option )")
for o, nom in ((1, "TOUT_DE_SUITE"), (2, "ATTENDRE")):
    L = [e for e in A if e["option"] == o and e.get("attente") is not None]
    at = [e["attente"] for e in L if e["attente"] >= 0]
    print(f"   {nom:14s} n {len(L):3d} : attente jouee {min(at) if at else '-'} a {max(at) if at else '-'} s "
          f"( mediane {st.median(at) if at else '-'} ) ; details {Counter(e.get('detail') for e in L).most_common(3)}")
print("\n3. REGLAGE D OBSERVATION applique")
print("  ", Counter((e.get("avant_joue"), e.get("balayage_joue")) for e in A).most_common(5))
print("\n4. HOMMES ET TYPE poses")
print("  ", Counter(tuple(e["types"]) for e in A).most_common(5))
print("\n5. ISSUE PRIMAIRE, TOUS BRAS CONFONDUS ( plancher / plafond, pas d effet )")
L = [e for e in A if e.get("fin") is not None]
print(f"   phase_discrete {part(L, lambda e: e['discrete']):5.0%} sur {len(L)} episodes ; "
      f"fins {Counter(e['fin'] for e in L).most_common(4)}")
print(f"   compromis {part(L, lambda e: e['compromis']):5.0%} ; alarme {part(L, lambda e: e['alarme']):5.0%} ; "
      f"dix vivants {part(L, lambda e: e['vivants'] == 10):5.0%}")
print("\n6. EQUILIBRE DES CASES")
c = Counter((e["monde"], e["bras"], e["option"]) for e in A)
print(f"   cases a 4 : {sum(1 for v in c.values() if v == 4)} ; a 3 : {sum(1 for v in c.values() if v == 3)} ; "
      f"a 2 : {sum(1 for v in c.values() if v == 2)} ; vides : {32 - len(c)}")
