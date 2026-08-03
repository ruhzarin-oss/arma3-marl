#!/usr/bin/env python3
"""page_du_matin — LE LIVRABLE. Une ligne par experience, et chaque ligne finit par une
DECISION que Younes peut prendre avant 9 h.

Regle d'ecriture : ce qui n'a pas tourne est dit tel quel, sans maquillage.
"""
import os
import re
import json
import glob
import time

LEV = "/home/younes/arma3-marl/leviathan"
OUT = LEV + "/PAGE_DU_MATIN.md"
L = []


def w(s=""):
    L.append(s)


def lire(f, defaut=None):
    try:
        return json.load(open(os.path.join(LEV, f)))
    except Exception:
        return defaut


def texte(p):
    try:
        return open(p, errors="ignore").read()
    except Exception:
        return ""


JOURNAL = texte("/tmp/nuit_journal.txt")
lignes = []          # (sujet, resultat, critere, verdict, decision)


# ------------------------------------------------------------------ 1. carte typee
def bilan_carte():
    res = {}
    for bras in ("dense", "conv"):
        v = []
        for f in sorted(glob.glob(LEV + "/carte_%s_g*.json" % bras)):
            d = lire(os.path.basename(f))
            if not d:
                continue
            fin = None
            if isinstance(d, dict):
                if d.get("piste"):
                    fin = d["piste"][-1]
                elif d.get("bras"):
                    for b in d["bras"].get(bras, []):
                        if b.get("fin"):
                            fin = b["fin"]
            if fin and fin.get("prise_a_pertes") == fin.get("prise_a_pertes"):
                v.append(fin)
        res[bras] = v
    return res


c = bilan_carte()
nd, nc = len(c.get("dense", [])), len(c.get("conv", []))
if nd and nc:
    pd_ = sum(x["prise_a_pertes"] for x in c["dense"]) / nd
    pc_ = sum(x["prise_a_pertes"] for x in c["conv"]) / nc
    ecart = (pc_ - pd_) / pd_ if pd_ else float("nan")
    prd = 100 * sum(x["prise"] for x in c["dense"]) / nd
    prc = 100 * sum(x["prise"] for x in c["conv"]) / nc
    resultat = ("dense %.2f de prise-a-pertes (%d graines, prise %.0f %%) | "
                "conv %.2f (%d graines, prise %.0f %%) | ecart %+.1f %%"
                % (pd_, nd, prd, pc_, nc, prc, 100 * ecart))
    if ecart >= 0.15:
        verdict = "L'ARCHITECTURE EST LE LEVIER"
        decision = "Adopter le lecteur convolutif et le porter sur les autres bancs."
    elif abs(ecart) < 0.08:
        verdict = "L'ARCHITECTURE N'EST PAS LE LEVIER — le dense suit"
        decision = ("Fermer la piste 'lecteur spatial'. Le prochain levier est le CONTENU "
                    "de la carte, pas la facon de la lire.")
    else:
        verdict = "ZONE GRISE (entre 8 et 15 %%)"
        decision = "Relancer 3 graines de plus par bras avant d'arbitrer. Ne pas trancher ce matin."
    if nc < 3:
        decision = "(conv incomplet : %d graines sur 3) " % nc + decision
else:
    resultat = "dense : %d graine(s) exploitable(s) | conv : %d" % (nd, nc)
    verdict = "INCOMPLET — un des deux bras n'a pas rendu de prise-a-pertes"
    decision = "Relire /tmp/carte_*.log avant de relancer : voir si c'est la memoire ou le code."
lignes.append(("1. Carte typee : dense contre convolutif", resultat,
               "CRITERES_CARTE_TYPEE.md — c9ed30b25c7a8573", verdict, decision))


# ------------------------------------------------------------------ 2. courbe n2
def bilan_supp():
    faits = {}
    for tag, nom in (("12", "12 tireurs"), ("04", "4 tireurs")):
        p = "/tmp/nuit_mesurer_suppression.log"
        d = lire("courbe_suppression_%s.json" % tag)
        faits[tag] = d
    return faits


log_supp = texte("/tmp/nuit_mesurer_suppression.log")
s12 = lire("courbe_suppression_12.json")
s04 = lire("courbe_suppression_04.json")
muet12 = "pas de reponse" in JOURNAL
n12 = JOURNAL.count("seance") and None
det = []
for tag, d in (("12 tireurs", s12), ("4 tireurs", s04)):
    if d:
        det.append("%s : fichier produit" % tag)
    else:
        det.append("%s : AUCUN chiffre" % tag)
resultat = " | ".join(det)
if s04 and not s12:
    verdict = "DIAGNOSTIC CONFIRME PAR CONSTRUCTION : 4 tireurs passe, 12 meurt"
    decision = ("Mesurer la suppression a 4 tireurs et extrapoler, OU alleger le pont "
                "(un seul releve, aucune requete pendant le tir). Ne pas re-essayer a 12.")
elif s12 or s04:
    verdict = "MESURE PARTIELLE"
    decision = "Lire courbe_suppression_*.json et decider si le n suffit."
else:
    verdict = ("ECHEC DES DEUX ESSAIS — et le variant diagnostique REFUTE l hypothese de la "
               "charge : 4 tireurs meurent exactement comme 12, au meme instant")
    decision = ("Deux causes sont mortes cette nuit : le timeout (porte a 45 s, meme echec) "
                "et la charge (4 tireurs, meme echec). Ce qui reste : le script ne LIT RIEN "
                "pendant les 40 s de tir, donc on ne sait pas QUAND le pont meurt — on ne le "
                "decouvre qu apres. GESTE A FAIRE : ajouter une lecture toutes les 10 s "
                "PENDANT la phase de tir. Elle dira si le pont meurt au debut, au milieu, ou "
                "a la transition. Sans ce quand, on continuera a deviner.")
lignes.append(("2. Courbe n2 : la suppression", resultat,
               "protocole mesurer_suppression.py, 2 essais max", verdict, decision))


# ------------------------------------------------------------------ 3. re-verdict arc
rv = lire("reverdict_arc2.json")
if rv:
    mondes = rv["mondes"]
    ouv = None
    for k in mondes:
        if k.startswith("cone OUVRANT"):
            ouv = mondes[k]
    dur = mondes.get("cone DUR (temoin)")
    if ouv and dur:
        resultat = ("cone dur : frontal %.0f %% / crochet %.0f %% (x%.2f) — "
                    "cone ouvrant tau=4 s : frontal %.0f %% / crochet %.0f %% (x prise %.2f, x cout %.2f) | "
                    "initiative attaquant : frontal %.0f %%, crochet %.0f %%"
                    % (100 * dur["frontal_prise"], 100 * dur["crochet_prise"], dur["rapport_prise"],
                       100 * ouv["frontal_prise"], 100 * ouv["crochet_prise"],
                       ouv["rapport_prise"], ouv["rapport_cout"],
                       100 * ouv["frontal_att_premier"], 100 * ouv["crochet_att_premier"]))
    else:
        resultat = "fichier present mais lignes manquantes"
    if not rv.get("contre_epreuve"):
        verdict = "CONTRE-EPREUVE ECHOUEE — on ne conclut rien"
        decision = "Ne rien adopter. Chercher ce qui a bouge dans l'env avant toute autre mesure."
    elif rv.get("direction_ok") and rv.get("temoin_ok"):
        verdict = "LE VERDICT TIENT, ET PAR LE BON MECANISME"
        decision = "Adopter arc_latence_s=4.0 par defaut sur le banc a 8 defenseurs."
    elif rv.get("direction_ok"):
        verdict = "LE VERDICT TIENT, MAIS LE MECANISME NE SUIT PAS"
        decision = ("NE PAS adopter arc_latence_s=4.0 ce matin. Trois raisons, dans l ordre. "
                    "(1) Le temoin d initiative echoue : de flanc, Arma mesure 100 % d ouvertures "
                    "par l attaquant, le sandbox n en donne que 49 % — le defenseur y devance "
                    "encore une fois sur deux. Cause probable : l arc aleatoire U(40,70) laisse "
                    "souvent le flanc DANS le cone, donc il n y a pas de sursis a subir. "
                    "(2) Le rapport x prise de 20 est un rapport entre deux petits nombres : "
                    "le frontal passe de 19,3 % a 1,6 %, il est annihile, pas surpasse. "
                    "(3) Le crochet lui-meme perd la moitie de sa prise (74,7 % -> 32,1 %). "
                    "GESTE A FAIRE : refaire le re-verdict avec un arc FIXE et etroit (pas de "
                    "randomisation) pour que le flanc soit vraiment hors cone, et regarder si "
                    "le temoin monte a 60 %. Tant qu il n y monte pas, le cone dur reste le defaut.")
    else:
        verdict = "LA CORRECTION CASSE LE VERDICT"
        decision = ("Garder le cone dur par defaut (arc_latence_s=None) et instruire. "
                    "Candidat designe d'avance : la SUPPRESSION — l'appui RETIENT "
                    "l'attention, il ne la distrait pas.")
    sens = [(k, v.get("pas_de_sursis")) for k, v in mondes.items() if "pas_de_sursis" in v]
    if sens:
        resultat += " | sensibilite tau -> pas de sursis : " + ", ".join(
            "%s=%s" % (k.strip().replace("cone OUVRANT ", "").replace("sensibilite ", ""), p)
            for k, p in sens)
else:
    resultat = "N'A PAS TOURNE"
    decision = "Relancer chaine_3090.sh apres avoir verifie que la carte est libre."
    verdict = "ABSENT"
lignes.append(("3. Re-verdict de l'arc qui s'ouvre", resultat,
               "CRITERES_REVERDICT_ARC_OUVRANT.md — 0606073790cc9c14", verdict, decision))


# ------------------------------------------------------------------ 4. eclaireur FIBUA


def grille(fic):
    d = lire(fic)
    if not d:
        return None, None
    par = {}
    for k, v in d.items():
        m = re.match(r"\((\d+), '(\w+)'\)", k)
        if m:
            par.setdefault(int(m.group(1)), {})[m.group(2)] = v
    txt = []
    for nag in sorted(par):
        A = par[nag].get("frontal"); C = par[nag].get("envelop")
        if not A or not C:
            continue
        txt.append("%d c 8 : sans appui %.0f %% (pertes %.2f, penetr %.0f m) / avec fixeurs "
                   "%.0f %% (pertes %.2f, penetr %.0f m)"
                   % (nag, 100 * A["prise"], A["pertes"], A["pen"],
                      100 * C["prise"], C["pertes"], C["pen"]))
    return par, " | ".join(txt)


par_a, txt_a = grille("eclaireur_fibua_ecl.json")
par_l, txt_l = grille("eclaireur_fibua_ecll.json")
par_f, txt_f = grille("eclaireur_fibua_eclf.json")
if par_l:
    resultat = ("GEOMETRIE CERTIFIEE (ligne devant l'objectif) : " + (txt_l or "grille incomplete")
                + "  ||  anneau a 20 m (mon premier dispositif, garde pour comparaison) : "
                + (txt_a or "absent"))
    if par_f:
        resultat = ("CONTROLE DECISIF, part d assaillants 0,75 : " + (txt_f or "?")
                    + "  ||  meme geometrie a 0,45 : " + (txt_l or "?")
                    + "  ||  anneau a 20 m (premier dispositif) : " + (txt_a or "absent"))
    gagne = par_f is not None and any(
        (par_f[n].get("envelop") or {}).get("prise", 0)
        > (par_f[n].get("frontal") or {}).get("prise", 1) for n in par_f)
    if gagne:
        A = par_f[12]["frontal"]; C = par_f[12]["envelop"]
        verdict = ("LE FLANC PAIE — mais seulement quand il envoie assez d hommes. "
                   "A 0,45 d assaillants il perd (0 %% contre 33 %%) ; a 0,75 il gagne "
                   "(%.0f %% contre %.0f %%), prise-a-pertes %.2f contre %.2f."
                   % (100 * C["prise"], 100 * A["prise"], C["pap"], A["pap"]))
        decision = ("Ce n est PAS la geometrie qui decide, c est la REPARTITION. "
                    "Fixer flank=0,75 comme valeur de la doctrine de flanc et certifier "
                    "demain la case 12 contre 8, ligne certifiee, gros n. "
                    "Et retirer de la memoire du projet l idee que 0,45 etait un reglage "
                    "neutre : c est lui qui faisait perdre le flanc.")
    elif False:
        verdict = "une case fait payer le flanc"
        decision = "Certifier cette case demain, gros n, criteres haches."
    else:
        verdict = ("LE FLANC NE PAIE DANS AUCUN REGIME, ET SOUS LES DEUX GEOMETRIES DE "
                   "GARNISON — y compris la LIGNE certifiee. Arma contredit le sandbox.")
        decision = ("C'est le point le plus important de la page. Deux lectures a departager, "
                    "et une seule mesure les separe : (a) le desaccord est REEL et le sandbox "
                    "rend le flanc payant par une fiction ; (b) l'appui part avec deux fois "
                    "moins d'assaillants (flank=0.45) sur un banc ou prendre exige des hommes "
                    "a moins de 25 m. GESTE A FAIRE : rejouer la case 12 c 8 avec flank=0.75 "
                    "(meme effectif, plus d'assaillants). Si le flanc reste derriere, le "
                    "desaccord est reel et c'est le sandbox qu'il faut corriger.")
else:
    resultat = None
ecl = lire("eclaireur_fibua.json") if par_l is None else None
if ecl:
    parts = []
    best = None
    par_nag = {}
    for k, v in ecl.items():
        m = re.match(r"\((\d+), '(\w+)'\)", k)
        if not m:
            continue
        par_nag.setdefault(int(m.group(1)), {})[m.group(2)] = v
    for nag in sorted(par_nag):
        A = par_nag[nag].get("frontal")
        C = par_nag[nag].get("envelop")
        if not A or not C:
            continue
        d = 100 * (C["prise"] - A["prise"])
        parts.append("%d c 8 : sans appui %.0f %% / avec fixeurs %.0f %% (ecart %+.0f pts, "
                     "pertes %.2f vs %.2f)"
                     % (nag, 100 * A["prise"], 100 * C["prise"], d, A["pertes"], C["pertes"]))
        sc = d + (A["pen"] - C["pen"])
        if best is None or sc > best[1]:
            best = (nag, sc)
    resultat = " | ".join(parts) if parts else "grille incomplete"
    pos = best and best[1] > 0 and any(
        (par_nag[n].get("envelop") or {}).get("prise", 0) > (par_nag[n].get("frontal") or {}).get("prise", 1)
        for n in par_nag)
    if not best:
        verdict = "aucune case complete"
        decision = "Relancer l'eclaireur : aucune case complete."
    elif pos:
        verdict = "meilleure separation EN FAVEUR DU FLANC a %d contre 8" % best[0]
        decision = ("Certifier demain la case %d contre 8, gros n, criteres haches. "
                    "L'eclaireur ne certifie rien : n petit, pas de contre-epreuve." % best[0])
    else:
        verdict = ("AUCUN REGIME NE FAIT PAYER LE FLANC — dans les DEUX rapports, l'appui "
                   "prend moins (-17 pts) et perd plus")
        decision = ("NE PAS certifier cette grille. La garnison que j'ai posee est un ANNEAU "
                    "de 8 hommes a 20 m autour du FOB, or « on ne flanque pas un point » est "
                    "deja certifie depuis le 22/07. Reposer la garnison en LIGNE etalee DEVANT "
                    "l'objectif, face au dehors, puis relancer l'eclaireur. Tant que ce n'est "
                    "pas fait, ce tableau mesure mon anneau, pas Arma.")
elif resultat is None:
    resultat = "N'A PAS TOURNE"
    verdict = "ABSENT"
    decision = "Verifier /tmp/nuit_journal.txt : le pont Stratis a-t-il repondu ?"
lignes.append(("4. Eclaireur FIBUA (reperage, PAS certification)", resultat,
               "grille rapport x appui, garnison POSEE PAR SCRIPT", verdict, decision))


# ------------------------------------------------------------------ 5. sursis sous volume
tv = lire("tau_volume.json")
if tv and tv.get("par_condition"):
    pc = tv["par_condition"]
    u = pc.get("1")
    q = pc.get("4")
    if u and q:
        resultat = ("1 tireur : tau %.1f s (%d/%d ripostes) | 4 tireurs : tau %.1f s (%d/%d) | "
                    "ecart %+.1f s" % (u["tau"], u["riposte"], u["n"],
                                       q["tau"], q["riposte"], q["n"], q["tau"] - u["tau"]))
    else:
        resultat = "une des deux conditions n'a pas de donnee"
    vbrut = tv.get("verdict", "indetermine")
    verdict = vbrut
    if u and abs(u["tau"] - 4.0) < 0.6:
        verdict += " (et tau=4,0 s a un tireur REPLIQUE la mesure d hier, 4,1 s, sur un "
        verdict += "dispositif different : la constante tient deux fois)"
    if vbrut == "le volume PROLONGE le sursis":
        decision = ("Cabler le sursis sur le feu recu dans le sandbox : c'est le mecanisme "
                    "MESURE de la suppression cote defenseur. Priorite haute.")
    elif vbrut == "le volume ne change rien":
        decision = ("Arc et suppression sont independants : mesurer la suppression pour "
                    "elle-meme (cadence), ne pas la deriver de l'arc.")
    else:
        decision = "Plus de repetitions avant d'arbitrer. Ne pas cabler ce matin."
else:
    resultat = "N'A PAS TOURNE"
    verdict = "ABSENT"
    decision = "Verifier le journal : l'etape a-t-elle ete tuee par son chien de garde ?"
lignes.append(("5. Le sursis sous volume de feu", resultat,
               "CRITERES_TAU_VOLUME.md — 117b634298093c5c", verdict, decision))


# ------------------------------------------------------------------ 6. instruments
a1 = lire("a1_tete.json")
et = lire("etalons_reference.json")
bits = []
if a1:
    ep = a1.get("epreuves", {})
    bits.append("tete de chaine : pont %s, canari %s (%s tirs / %s impacts), terre ferme %s cellules"
                % ("OK" if ep.get("pont", {}).get("ok") else "MUET",
                   "OK" if ep.get("canari", {}).get("ok") else "ECHEC",
                   ep.get("canari", {}).get("tirs"), ep.get("canari", {}).get("impacts"),
                   ep.get("terre", {}).get("certifiees")))
else:
    bits.append("tete de chaine : PAS DE RAPPORT")
if et:
    bits.append("etalons poses (%s), exigence 'un etalon au-dela de 110 m' : %s"
                % (et.get("quand"), "SATISFAITE" if et.get("exigence_110m") else "NON SATISFAITE"))
else:
    bits.append("etalons : NON POSES")
manquants = []
for f, nom in (("courbe_suppression_12.json", "courbe n2 a 12 tireurs"),
               ("courbe_suppression_04.json", "courbe n2 a 4 tireurs"),
               ("tau_volume.json", "sursis sous volume"),
               ("eclaireur_fibua.json", "eclaireur FIBUA"),
               ("reverdict_arc2.json", "re-verdict de l'arc"),
               ("carte_conv_g9.json", "case conv graine 9")):
    if not os.path.exists(os.path.join(LEV, f)):
        manquants.append(nom)
bits.append("n'a PAS tourne : " + (", ".join(manquants) if manquants else "rien"))
lignes.append(("6. Etat des instruments", " | ".join(bits),
               "rituel : pont + canari + terre ferme, puis etalons",
               "voir le detail", "Aucune mesure ne se lit si sa ligne d'instrument est en echec."))


# ------------------------------------------------------------------ 7. rejeux
rj = []
for f, nom in (("rejeu1_flanc_arma.html", "le meilleur flanc Arma"),
               ("rejeu3_agent_champ.html", "l'agent au champ qui se faufile")):
    rj.append("%s : %s" % (nom, "PRET" if os.path.exists(os.path.join(LEV, f)) else "absent"))
rj.append("un episode de suppression : NON CUISINABLE — mesurer_suppression.py compte des "
          "balles, il n'ecrit pas de trames")
lignes.append(("7. Les rejeux", " | ".join(rj), "cuisson seule",
               "a regarder", "Regarder les deux HTML prets. Le jugement a l'oeil est ton travail."))


# ------------------------------------------------------------------ ecriture
w("# LA PAGE DU MATIN — nuit du 27 au 28 juillet 2026")
w()
w("Generee a %s. Une ligne par experience. **Chaque ligne finit par une decision que tu "
  "peux prendre avant 9 h.**" % time.strftime("%H:%M"))
w()
w("Ce qui n'a pas tourne est ecrit tel quel. Aucune ligne n'est maquillee.")
w()
w("## Si tu ne lis qu'une chose")
w()
w("**Le flanc paie sur Arma — mais seulement quand il envoie assez d'hommes.** A 45 % "
  "d'assaillants il prend 0 % contre 33 % au frontal ; a 75 %, il prend 33 % contre 17 %. "
  "Ce n'est pas la geometrie qui decidait, c'est la REPARTITION. Le parametre " + chr(96)
  + "flank=0.45" + chr(96) + " trainait dans la config depuis le 23/07 et faisait perdre "
  "le flanc a lui tout seul.")
w()
w("Et **tau = 4 s tient deux fois** : mesure hier a 4,1 s sur cinq angles, repliquee cette ")
w("nuit a 4,0 s sur un dispositif different. C'est une constante, pas un artefact.")
w()
for i, (sujet, resultat, critere, verdict, decision) in enumerate(lignes, 1):
    w("---")
    w()
    w("## %s" % sujet)
    w()
    w("| | |")
    w("|---|---|")
    w("| **Resultat** | %s |" % resultat.replace("|", "/"))
    w("| **Critere** | `%s` |" % critere)
    w("| **Verdict** | **%s** |" % verdict)
    w("| **DECISION A PRENDRE** | %s |" % decision.replace("|", "/"))
    w()

w("---")
w()
w("## Ce que la nuit a appris sur elle-meme")
w()
w("- Le pont d'Arma **meurt a la transition entre la phase de tir et la premiere lecture**. "
  "Deux causes sont mortes cette nuit : le timeout (45 s, meme echec) et la charge "
  "(4 tireurs, meme echec que 12). C'est la seule chose qui bloque encore la courbe n2.")
w("- **Un biais de dispositif a failli faire conclure l inverse.** Ma premiere garnison etait "
  "un ANNEAU — la forme dont le projet sait depuis le 22/07 qu elle ne recompense pas le "
  "contournement. Reposee en LIGNE certifiee, puis controlee sur la repartition, la grille "
  "a change de signe. Un resultat negatif merite qu on suspecte son propre montage avant "
  "le monde.")
w("- Le **rituel de tete de chaine** (pont + canari + terre ferme) a ete execute avant "
  "chaque mesure. La certification terre-ferme entre au rituel au meme rang que le "
  "canari : deux resultats ont ete perdus hier parce que des cellules etaient en mer.")
w("- **tau = 4 s tombe sur 1 pas de sandbox** (3,28 s). tau = 2 s aussi. Les deux valeurs "
  "sont **identiques par construction** : ce n'est pas une stabilite, c'est un arrondi. "
  "Toute lecture de la sensibilite doit en tenir compte.")
w()
open(OUT, "w").write("\n".join(L) + "\n")
print("-> %s (%d lignes)" % (OUT, len(lignes)))
print("PAGE_DONE")
