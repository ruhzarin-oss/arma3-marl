"""Correctif ( 29/09, run long HMT-119 ) : une commande publique entre UNE fois dans la demande du marche, comme dans le
moteur depuis le 26/09 ( _demande_comptee ). Le domaine 15, en remplacant monde.expedier, avait perdu ce correctif : la
commande etait recomptee a chaque heure tant qu elle n etait pas servie. Applique au domaine 15 d un arbre. Idempotent."""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d15_logistique.py")
s = open(f, encoding="utf-8").read()
if "_demande_comptee" in s:
    print("deja corrige :", f); sys.exit(0)
a = '        m.demande[b] += cmd["quantite"]\n        if q < 1: continue\n'
if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} )")
s = s.replace(a,
    '        # ( 29/09 ) une commande publique est UNE demande, comptee le jour ou le marche la voit, comme dans le moteur depuis le\n'
    '        # 26/09 ( _demande_comptee ). Ce domaine, en remplacant monde.expedier, avait perdu ce correctif : recomptee a chaque\n'
    '        # heure tant qu elle n etait pas servie, la subvention des hopitaux en remedes du run long ( Stratis, 100 000\n'
    '        # habitants ) faisait 1,2 million de remedes demandes par jour, que le negoce importait et que le marche rachetait\n'
    '        # avec la caisse de sa nourriture ( 64 a 71 % de menages sans nourriture, jours 24 a 27 ).\n'
    '        if not cmd.get("_demande_comptee"):\n'
    '            m.demande[b] += cmd["quantite"]; cmd["_demande_comptee"] = True\n'
    '        if q < 1: continue\n')
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
