"""Correctif ( 29/09, run long HMT-119 ) : deux gardes du domaine 7. ( 1 ) La demande que le negoce et le marche lisent
est bornee par habitant du marche, loin de l ordinaire ( 10 fois la demande ordinaire ), et une commande bornee est
comptee ( import_borne ). ( 2 ) Le marche garde de quoi racheter sa couverture de nourriture avant d acheter un autre
bien au negoce. Applique au domaine 7 d un arbre. Idempotent. Usage : python patch_garde_import.py <arbre>"""
import os, sys
f = os.path.join(sys.argv[1], "monde", "pays", "d07_exterieur.py")
s = open(f, encoding="utf-8").read()
if "PLAFOND_DEMANDE_HAB_J" in s:
    print("deja corrige :", f); sys.exit(0)


def remplacer(s, a, b):
    if s.count(a) != 1: raise SystemExit(f"{f} : ancre introuvable ou multiple ( {s.count(a)} ) : {a[:70]!r}")
    return s.replace(a, b)


s = remplacer(s,
    "def _demande(p, mid, b):\n"
    "    em = p.domaine(\"economie\").marches[mid]\n"
    "    return max(EC.DEMANDE_MIN, em.demande_lisse.get(b, 0.0))\n",
    "# ( 29/09, run long HMT-119 ) Une GARDE de plausibilite, pas un reglage : la demande qu un marche montre au negoce est\n"
    "# bornee par habitant qu il sert, a 10 fois la demande ordinaire. L ordinaire : Altis, graine 41, sans epidemie\n"
    "# ( epidemie_jour = -1 ), mediane des jours 11 a 30, mesure du 29/09 sur le tronc e8f1ee8 corrige ( d15 ) : nourriture\n"
    "# 1,22, remedes 0,0315, outils 0,27 par habitant et par jour ( outils jusqu a 2,5 les dix premiers jours : le\n"
    "# renouvellement des durables a l installation, sous la borne ). Sans elle, une demande recomptee ( la subvention des\n"
    "# hopitaux, 12 remedes par habitant et par jour a Stratis ) faisait importer 907 875 traitements en un jour.\n"
    "PLAFOND_DEMANDE_HAB_J = {\"nourriture\": 12.2, \"remedes\": 0.315, \"outils\": 2.7}\n"
    "GARDE_RESERVE_NOURRITURE = True       # la reserve de caisse du marche pour sa nourriture ( ci-dessous, _vendre_aux_marches )\n"
    "\n"
    "\n"
    "def _demande_brute(p, mid, b):\n"
    "    em = p.domaine(\"economie\").marches[mid]\n"
    "    return max(EC.DEMANDE_MIN, em.demande_lisse.get(b, 0.0))\n"
    "\n"
    "\n"
    "def _plafond(p, mid, b):\n"
    "    k = PLAFOND_DEMANDE_HAB_J.get(b)\n"
    "    pop = getattr(p.w, \"_pop_marche\", {}).get(mid, 0) if k is not None else 0\n"
    "    return k * pop if pop > 0 else math.inf\n"
    "\n"
    "\n"
    "def _demande(p, mid, b):\n"
    "    return min(_demande_brute(p, mid, b), _plafond(p, mid, b))\n")
s = remplacer(s,
    "            dem = _demande(p, neg.marche_id, nom)\n"
    "            e.suivi[cle] = [neg.marche_id, nom, p.jour, 0, None, max(EPS, dem * prix_import(p, b)), dem]\n",
    "            dem = _demande(p, neg.marche_id, nom)\n"
    "            if _demande_brute(p, neg.marche_id, nom) > dem + EPS: p.compter(\"import_borne\")   # la garde a joue : au bulletin\n"
    "            e.suivi[cle] = [neg.marche_id, nom, p.jour, 0, None, max(EPS, dem * prix_import(p, b)), dem]\n")
s = remplacer(s,
    "        m = w.marches[neg.marche_id]\n"
    "        for b, lots in sorted(neg.lots.items(), key=lambda kv: cat[kv[0]].nom not in PRIORITE_RACHAT):   # tri stable\n",
    "        m = w.marches[neg.marche_id]\n"
    "        # ( 29/09 ) comme un vrai commercant, le marche garde de quoi racheter sa couverture de nourriture avant d acheter\n"
    "        # un autre bien : sans cela, les remedes d une demande recomptee vidaient sa caisse ( Stratis, 14,0 M -> 3,1 M ) et\n"
    "        # 64 a 71 % des menages restaient sans nourriture les jours 24 a 27 du run long\n"
    "        reserve_n = _cible(\"nourriture\") * _demande(p, neg.marche_id, \"nourriture\") * m.prix[\"nourriture\"] * (1.0 - m.marge)\n"
    "        for b, lots in sorted(neg.lots.items(), key=lambda kv: cat[kv[0]].nom not in PRIORITE_RACHAT):   # tri stable\n")
s = remplacer(s,
    "                q = min(lot[1], besoin, max(0.0, m.caisse) / cession)\n",
    "                garde = 0.0 if nom == \"nourriture\" or not GARDE_RESERVE_NOURRITURE else reserve_n\n"
    "                q = min(lot[1], besoin, max(0.0, m.caisse - garde) / cession)\n")
s = remplacer(s,
    "              \"envoi_de_fonds\", \"aide_ue\", \"depart_empeche\", \"devises_refusees\"):",
    "              \"envoi_de_fonds\", \"aide_ue\", \"depart_empeche\", \"devises_refusees\", \"import_borne\"):")
open(f, "w", encoding="utf-8").write(s); print("corrige :", f)
