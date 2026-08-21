import re, glob, sys, os
# ⚠️ REPERTOIRE SURCHARGEABLE : un juge qu on ne peut pas saboter ne peut pas etre
# juge (regle 18). `HMT_PORTE_DIR` permet de lui presenter des donnees FABRIQUEES
# sans toucher aux vraies. Par defaut, la porte reelle.
_PORTE = os.environ.get("HMT_PORTE_DIR", "/mnt/data/porte")
# ⚠️ LES JOURNAUX SERVEUR : c est la SEULE trace des erreurs de script. Surchargeable
# pour que la ligne 5 puisse etre sabotee comme les autres (regle 18).
_OUT = os.environ.get("HMT_OUT_DIR", "/mnt/data/harmattan-sandbox/logs")
"""LES QUATRE LIGNES de DEPOT_PORTE_PLEIN_CHEMIN.md, ecrites AVANT. Vertes ENSEMBLE ou panne.
⚠️ REECRITES LE 20/08 : le selecteur est mort, donc le concept de « faux-recu » aussi.
La ligne 1 juge desormais LA VIE DU CANAL, pas la qualite d un tri."""
lots = []
for f in sorted(glob.glob(_PORTE + "/lot*.txt"), key=lambda x: int(re.search(r"lot(\d+)", x).group(1))):
    n = int(re.search(r"lot(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    seq, prev = [], 0
    for l in t.splitlines():
        m = re.search(r"(\d+)/12\s+vert=(\d+)\s+echec=(\d+)(.*)", l)
        if not m: continue
        e, d = int(m.group(3)), m.group(4)
        if "ECARTE" in d or "abandonne" in d: k = "ECARTE"
        elif "PONT MUET" in d: k = "PONT"
        elif "PREVOL PLANTE" in d: k = "PLANTE"
        elif "PREVOL LENT" in d: k = "LENT"
        # ⚠️ « T0 AUCUN LIEU PRATICABLE » N EST PAS UNE RECEPTION ⟨Fable, 18/08⟩ : le placeur
        # n a RIEN recu, donc ce tirage ne doit pas gonfler le denominateur de la ligne 1.
        # Latent tant que 60/60 recevaient — mais l acte unifie va refuser davantage.
        # ⚠️ `T2` ETAIT AVALE PAR `AUTRE` : le 20/08 un homme est ne chargeur vide, et
        # l echec est tombe dans le fourre-tout que rien ne borne. Un label qui n existe
        # pas ne peut pas etre juge. On le NOMME.
        elif e > prev: k = ("T0" if "AUCUN LIEU TENABLE" in d else
                            ("T5" if "T5 CANAL MORT" in d else
                             ("T7" if "T7 " in d else
                              ("T2" if "T2 " in d else "AUTRE"))))
        else: k = "."
        prev = e
        seq.append(k)
    lots.append((n, seq))

print("\n  lot  rang → 1  2  3  4  5  6  7  8  9 10 11 12   verts")
tot = {}
for n, s in lots:
    for k in s: tot[k] = tot.get(k, 0) + 1
    print(f"   {n}        " + " ".join(f"{k[:2]:>2}" if k != "." else " ." for k in s) + f"     {s.count('.')}")
N = sum(len(s) for _, s in lots)
print(f"\n  {N} tirages : " + "  ".join(f"{k}={v}" for k, v in sorted(tot.items())))

# les tirages mesures excluent T0 : le prevol n y a pas atteint T5
# ⚠️ `T2` COMPTE COMME TIRAGE MESURE. En lui donnant son propre label j avais oublie
# de le remettre ici : le denominateur du lot 5 tombait de 12 a 11 et la ligne 3
# changeait de nombres (X2 4,07 -> 0,00) alors que l amendement ne devait TOUCHER
# QUE le T2. Le temoin C2 l a attrape. Un prevol qui atteint T2 a bien MESURE :
# il a echoue SUR un acte, il n a pas ete empeche de mesurer.
recep = tot.get(".", 0) + tot.get("T5", 0) + tot.get("T7", 0) + tot.get("T2", 0) + tot.get("AUTRE", 0)
if tot.get("T0", 0): print(f"  (T0 · aucun lieu tenable pour la VUE ou le TIR : {tot['T0']} tirages, hors mesure)")
# ═══ LA CARTE DES JURIDICTIONS ⟨pre-inscription du 20/08⟩ ══════════════════════════════
# Le vrai defaut n etait pas qu `AUTRE` soit non borne — c est qu un LABEL D ECHEC PUISSE
# EXISTER SANS JURIDICTION. Deux l etaient : `T2` (avale par AUTRE) et `T7` (imprime par la
# ligne 1 mais absent de son verdict). Une grandeur que rien ne borne derive sans rougir.
# ⚠️ UN LABEL NON CARTOGRAPHIE REND ROUGE LE JUGE, PAS LE MONDE. Un juge qui rencontre un
# echec qu il ne sait pas classer doit le DIRE, pas l absorber.
_JURIDICTION = {
    ".":       "vert (aucun echec)",
    "T5":      "ligne 1",
    "T7":      "ligne 1",
    "T2":      "ligne 1",
    "PLANTE":  "ligne 2",
    "PONT":    "ligne 2bis",
    "LENT":    "ligne 2bis",
    "ECARTE":  "ligne 2bis",
    "T0":      "hors mesure (declare, non juge)",
}
_sans = sorted(set(tot) - set(_JURIDICTION))
_n_sans = sum(tot[k] for k in _sans)
print(f"\n  ══ CARTE DES JURIDICTIONS ══")
for _k in sorted(tot):
    print(f"  {_k:8s} {tot[_k]:3d}  →  {_JURIDICTION.get(_k, '⛔ AUCUNE JURIDICTION')}")
_competent = (not _sans)
if not _competent:
    print(f"  ⛔ LE JUGE SE DECLARE INCOMPETENT : labels sans juridiction {_sans} ({_n_sans} tirages)")
    print(f"     Ce n est PAS un verdict sur le monde — c est le juge qui ne sait pas classer.")
else:
    print(f"  ✓ carte totale : tout label rencontre a exactement une juridiction")
# filet de la regle 19 pour l imprevu : <= 3 sur 60
_filet = _n_sans <= 3
print(f"  filet (regle 19) : {_n_sans} echecs sans juridiction sur {N}   seuil : <= 3")

print(f"\n  ══ LIGNE 1 · LES ACTES DU PREVOL REPONDENT-ILS ? ══")
# ⚠️ RENOMMEE LE 20/08. « Faux-recu » n a plus d objet : le SELECTEUR est mort avec
# l acte de traverse, qui mesurait la pente vers le nord et non la praticabilite.
# Un T5 rouge ne signale plus un lieu mal choisi mais un CANAL MORT — les jambes ne
# repondent pas dans cette session. C est une panne reelle, pas un artefact de tri.
# Critere : max des 8 azimuts >= 15,2 m, valide sur tirage frais (0/60 dans les deux
# sens, 0/60 de desaccord entre passages). Voir CRITERE_CANAL_VIVANT_VALIDE.md.
print(f"  tirages ou le prevol a pu mesurer le canal : {recep}   exige : >= 50")
print(f"  actes du prevol en echec : T5={tot.get('T5',0)} (canal)  T7={tot.get('T7',0)} (feu)  T2={tot.get('T2',0)} (etat a la naissance)")
# ⚠️ RESSERREMENT ⟨regle 13⟩ : la ligne exigeait zero T5. Elle exige desormais zero sur
# LES TROIS actes du prevol — T5 (le canal), T7 (le feu), T2 (l etat a la naissance).
# Ca ne compte que des echecs DE PLUS : ca resserre, donc c est licite. Et ca ferme
# deux juridictions vides d un coup.
l1 = tot.get("T5", 0) == 0 and tot.get("T7", 0) == 0 and tot.get("T2", 0) == 0 and recep >= 50
print(f"  → {'✓ VERTE' if l1 else '⛔ ROUGE'}  (zero echec sur les TROIS actes, >= 50 tirages mesures)")

print(f"\n  ══ LIGNE 2 · MUETS DECOMPOSES ══")
print(f"  pont muet : {tot.get('PONT',0)}   prevol lent : {tot.get('LENT',0)}   prevol PLANTE : {tot.get('PLANTE',0)}   ecartes : {tot.get('ECARTE',0)}")
l2 = tot.get("PLANTE", 0) == 0
print(f"  → {'✓ VERTE' if l2 else '⛔ ROUGE'}  (zero PLANTE tolere ; lent et pont comptes a part)")

print(f"\n  ══ LIGNE 2bis · REBUT D INSTRUMENT ══")
# ⚠️ LIGNE NEUVE ⟨Fable, 18/08⟩ : la ligne 2 ne bornait QUE les PLANTE. LENT et ECARTE etaient
# « comptes a part » — sans plafond. La nuit du 17/08 ils ont mange 4 tirages sur 59, soit
# 6,8 %, AU-DESSUS du plafond de rebut de la regle 19, et personne n a sonne. Un critere qui
# laisse l instrument devorer 7 % de sa mesure sans rougir est une economie non declaree.
# grandeur : tirages perdus par l instrument (LENT + ECARTE + PONT) ; statistique : compte ;
# seuil : <= 3 sur 60, soit 6 % de la regle 19 ; n minimum : 60 tirages.
_reb = tot.get("LENT", 0) + tot.get("ECARTE", 0) + tot.get("PONT", 0)
print(f"  rebut d instrument : {_reb} sur {N}   seuil : <= 3 (6 % de la regle 19)")
l2b = _reb <= 3 and N >= 60
print(f"  → {'✓ VERTE' if l2b else '⛔ ROUGE'}")

print(f"\n  ══ LIGNE 3 · REGROUPEMENT PAR SERVEUR — SUR LES RECEPTIONS SEULES ══")
# ⚠️ SCINDEE ⟨Fable⟩ : cette ligne a TOUJOURS parle du MONDE (« pas de surdispersion entre
# serveurs »). En melant les echecs d INSTRUMENT, elle mesurait le regroupement des
# expirations de patience — qui est session-couple PAR CONSTRUCTION, l anneau de candidats
# etant fixe par session. Le 17/08 : les receptions du monde ont fait 55/55, et les 4 non-verts
# etaient tous des echecs de patience dont le lot 2 portait 7,31 des 9,97. La ligne juge
# desormais LES RECEPTIONS SEULES ; le regroupement des echecs d instrument est NOTE en clair
# mais NON JUGE — un X2 sur 2-3 evenements ne declare pas de n honnete.
# tirages mesures par lot = verts + T5 + T7 + T2 + AUTRE, sans les
# echecs d instrument qui ne jugent pas le monde
# ⚠️ `T2` MANQUAIT ICI AUSSI — deuxieme endroit ou le nouveau label devait entrer.
# Sans lui, le denominateur du lot 5 tombait de 12 a 11 et X2 passait de 4,07 a 0,00 :
# l amendement deplacait la ligne 3 alors qu il ne devait toucher QUE le T2.
# ⚠️ LECON : ajouter un label oblige a re-deriver TOUS les endroits qui enumerent les
# labels. Meme famille que « une longueur qui change oblige a re-deriver ce qui en depend ».
# Le temoin C2 a attrape les deux occurrences ; sans lui je n aurais vu ni l une ni l autre.
ok_l = [(n, s.count("."), sum(1 for k in s if k in (".", "T5", "T7", "T2", "AUTRE"))) for n, s in lots]
ok_l = [(n, v, t) for n, v, t in ok_l if t > 0]
p = sum(v for _, v, _ in ok_l) / sum(t for _, _, t in ok_l)
X2 = sum(t * ((v/t) - p)**2 for _, v, t in ok_l) / (p*(1-p)) if 0 < p < 1 else 0
seuil = {4: 9.49, 5: 11.07}.get(len(lots), 9.49)
print(f"  taux de verts par lot : " + "  ".join(f"{v}/{t}" for _, v, t in ok_l))
print(f"  X2 = {X2:.2f}   ddl = {len(lots)-1}   seuil 5 % = {seuil}")
l3 = X2 <= seuil
print(f"  → {'✓ VERTE' if l3 else '⛔ ROUGE'}  (pas de surdispersion entre serveurs)")

# ═══ LIGNE 5 · LE MONDE A-T-IL PLANTE EN SILENCE ? ⟨21/08⟩ ═════════════════════════════
# ⚠️ CETTE LIGNE MANQUAIT, ET SON ABSENCE A COUTE UNE PORTE. Le 20/08 j ai declare quatre
# lignes vertes sur une porte dont le placeur PLANTAIT sur sa ligne de retour — variable
# `_m` orpheline par mon propre refactoring, 16 erreurs dans le seul lot 1. Aucune ligne
# ne regardait les erreurs de script ; le juge ne pouvait donc pas les voir.
# J avais propose cette ligne le 19/08 et je ne l ai JAMAIS branchee.
#   grandeur    : erreurs de script imputables a NOTRE code, dans les journaux serveur
#   statistique : le COMPTE
#   seuil       : ZERO — une erreur de script est une panne, pas un bruit de fond
#   n           : les journaux des lots de la porte
# ⚠️ Les erreurs des ADDONS tiers sont comptees a part et declarees : elles ne sont pas
# les notres, et les confondre rendrait la ligne inutilisable ou complaisante.
print(f"\n  ══ LIGNE 5 · LE MONDE A-T-IL PLANTE EN SILENCE ? ══")
import glob as _g
# ⚠️ UNE ERREUR SQF S ECRIT SUR TROIS LIGNES — « Error in expression », « Error position »,
# « Error Undefined variable ». Mon premier compteur comptait des LIGNES : il annoncait
# 102 erreurs a nous ET 102 tierces, les secondes n etant que les autres lignes des memes
# erreurs. Un juge qui compte mal est exactement ce qu on repare ici.
# On compte donc les EVENEMENTS — une occurrence de « Error in expression » — et on les
# impute en regardant les lignes qui la suivent immediatement.
# ⚠️ REECRITE LE 21/08 APRES REVUE — ma premiere version etait DEUX FOIS fausse, et la
# revue l a demontre en FABRIQUANT des journaux, pas en raisonnant :
#   (a) elle ne comptait que « Undefined variable » : cinq erreurs d un autre genre
#       (`Type Number, expected Array` — celle qui a tue l actuateur en juin) passaient
#       et la ligne restait VERTE ;
#   (b) elle imputait par PREFIXE DE NOM : `LIEU_FORCE` (globale a nous) comptee tierce,
#       `_ace_private` (privee d un addon) comptee a nous. Un prefixe n est pas une mesure.
# ⚠️ LA MESURE EXISTE ET JE NE L AVAIS PAS CHERCHEE : chaque erreur SQF est suivie d une
# ligne « File <chemin>, line N ». C est le FICHIER qui impute, et la LIGNE qui designe.
# On lit en automate — pas de fenetre, le bloc n a pas de longueur fixe : une erreur s ouvre
# sur « Error in expression » et se ferme sur sa ligne « File » (ou sur l erreur suivante).
_nous, _tiers, _fic, _sansfic = 0, 0, 0, 0
_det = {}
_NOTRES = ("socle.sqf", "sonde_vue.sqf", "sondes.sqf", "mpmissions")
for _f in sorted(_g.glob(_OUT + "/serverPV_L*.out")):
    _fic += 1
    _ouvert, _nom = False, None
    for _l in open(_f, errors="ignore"):
        _mn = re.search(r"Undefined variable in expression: ([a-zA-Z_0-9]+)", _l)
        if _mn: _nom = _mn.group(1)
        if "Error in expression" in _l:
            if _ouvert: _nous += 1; _det["(sans fichier)"] = _det.get("(sans fichier)", 0) + 1; _sansfic += 1
            _ouvert, _nom = True, None
            continue
        _mf = re.search(r"File ([^,]+), line (\d+)", _l)
        if _mf and _ouvert:
            _chem, _lig = _mf.group(1), _mf.group(2)
            _cle = "%s:%s%s" % (_chem.split("\\")[-1][:22], _lig, (" (%s)" % _nom) if _nom else "")
            if any(_n in _chem for _n in _NOTRES):
                _nous += 1; _det[_cle] = _det.get(_cle, 0) + 1
            else:
                _tiers += 1
            _ouvert = False
    # ⚠️ UNE ERREUR SANS LIGNE `File` EST A NOUS : c est du code que le PONT a envoye,
    # donc du notre. La ranger ailleurs serait la meme complaisance que le prefixe.
    if _ouvert: _nous += 1; _det["(sans fichier)"] = _det.get("(sans fichier)", 0) + 1; _sansfic += 1
# ⚠️ ET LE DESACCORD D ACTIONS EST LU ICI. Le 20/08 j ai remplace 14 erreurs de script par
# une ligne `ACT_DESACCORD` que PERSONNE NE LISAIT : des hommes recevaient HOLD en silence
# et la porte restait verte. J avais converti une panne bruyante en panne muette, dans le
# commit qui pretendait rendre les pannes visibles. Elle a desormais sa juridiction.
_desac = 0
for _f in sorted(_g.glob(_OUT + "/serverPV_L*.out")) + sorted(_g.glob(_OUT + "/serverLV*.out")):
    for _l in open(_f, errors="ignore"):
        if "ACT_DESACCORD" in _l: _desac += 1
if _desac: _nous += _desac; _det["ACT_DESACCORD (hommes figes en silence)"] = _desac
print(f"  journaux lus : {_fic}   erreurs A NOUS : {_nous}   tierces (declarees) : {_tiers}"
      + (f"   dont sans fichier : {_sansfic}" if _sansfic else ""))
if _det:
    for _k, _v2 in sorted(_det.items(), key=lambda kv: -kv[1])[:5]:
        print(f"    {_k:28s} {_v2}")
l5 = (_fic > 0) and (_nous == 0)
if _fic == 0: print("  ⛔ AUCUN JOURNAL SERVEUR LU — la ligne ne peut pas juger.")
print(f"  → {'✓ VERTE' if l5 else '⛔ ROUGE'}  (zero erreur de script imputable a notre code)")

print(f"\n  ══ LIGNE 4 · LES CINQ SABOTAGES, LUS DANS LEURS TAMPONS ══")
# ⚠️ CETTE LIGNE ETAIT UNE CONSTANTE QUE JE BASCULAIS A LA MAIN ⟨Fable, 18/08⟩ — et je l avais
# mise a VRAI alors que mes sabotages dataient de TROIS socles differents : munitions et
# jambes sur 2.8.0, gel sur 2.10.0, lenteur sur 2.12.0. La faute d hier reconstruite : la
# porte sur un hash, les sabotages sur d autres. Elle LIT desormais les tampons que chaque
# run ecrit — mode, version LUE DANS LE MONDE, commit, verdict, date — et exige que les cinq
# portent LA MEME VERSION que la porte. Le gardien de version, applique aux ACTES.
import os
_TAMP = "/mnt/data/sabotages6/TAMPONS.txt"
# ⛔ LE SABOTAGE `traverse` EST RETIRE LE 20/08 — IL VISAIT UN ACTE QUI N EXISTE PLUS.
# L acte 2 du placeur (traverse >= 23 m) etait le SELECTEUR : mesure du 19/08, son seuil
# n etait franchissable qu en descente, et inverser la direction de marche inversait le
# regime (3/3 et 3/3). Il a ete retire pour premisse fausse, et son sabotage meurt avec lui.
# ⚠️ UN TAMPON QUI CERTIFIE UN ACTE SUPPRIME EST PIRE QU UN TAMPON ABSENT : il rend vert
# un canal qui n existe plus. La batterie passe donc de SIX a CINQ, et c est ecrit.
# Ce que la locomotion perd ici, elle le retrouve dans `jambes`, qui eprouve desormais le
# critere FUSIONNE du canal vivant (max des 8 azimuts >= 15,2 m) — verifie en situation le
# 20/08 : 3 lieux sains -> vivant, 3 lieux sabotes -> mort.
_ATTENDUS = {"tir", "munitions", "jambes", "gel", "lenteur"}
_vus, _mauvais, _vers = {}, [], set()
if os.path.exists(_TAMP):
    for _l in open(_TAMP, errors="ignore"):
        _c = _l.strip().split("|")
        if len(_c) >= 5:
            _vus[_c[0]] = (_c[1], _c[2], _c[3], _c[4])
            _vers.add(_c[1])
            if _c[3] != "PASSE": _mauvais.append(_c[0])
for _k in sorted(_ATTENDUS):
    if _k in _vus:
        _v = _vus[_k]
        print(f"  {'ok ' if _v[2]=='PASSE' else 'NON'} {_k:10s} socle {_v[0]:18s} commit {_v[1]:9s} {_v[3]}")
    else:
        print(f"  NON {_k:10s} AUCUN TAMPON")
_manquants = _ATTENDUS - set(_vus)
# la version du socle sous laquelle la PORTE a tourne
_vp = None
for _l in open(_PORTE + "/JOURNAL.txt", errors="ignore") if os.path.exists(_PORTE + "/JOURNAL.txt") else []:
    _m = re.search(r'HMT_SOCLE_VERSION = "([^"]*)"', _l)
    if _m: _vp = _m.group(1); break
print(f"  version de la PORTE : {_vp}   versions des tampons : {sorted(_vers)}")
l4 = (not _manquants) and (not _mauvais) and len(_vers) == 1 and (_vp in _vers if _vp else False)
if _manquants: print(f"  ⛔ tampons manquants : {sorted(_manquants)}")
if _mauvais:   print(f"  ⛔ sabotages en ECHEC : {sorted(_mauvais)}")
if len(_vers) > 1: print(f"  ⛔ les tampons ne portent PAS la meme version")
if _vp and _vp not in _vers: print(f"  ⛔ la porte a tourne sur {_vp}, les sabotages sur {sorted(_vers)}")
print(f"  → {'✓ VERTE' if l4 else '⛔ ROUGE'}")
# ⛔ LIGNE MORTE SUPPRIMEE LE 20/08 : elle imprimait « ROUGE (deux sabotages sur quatre
# non rejoues) » EN DUR, sans rien calculer, et contredisait le verdict juste au-dessus.
# Vestige d un etat ancien ou la ligne 4 etait une constante basculee a la main.
# ⚠️ SI ELLE AVAIT DIT « VERTE » AU LIEU DE « ROUGE », ELLE AURAIT MASQUE UN VRAI ROUGE.
# Un juge qui imprime un verdict qu il ne calcule pas ment aussi bien dans un sens
# que dans l autre — meme famille que la ligne GESTE qui ecrivait `any`.

_ecl = [k for _, s in lots for k in s if k in ("LENT", "ECARTE", "PONT")]
from collections import Counter as _C
print(f"  regroupement des echecs d INSTRUMENT (note, NON juge) : " +
      ", ".join(f"lot {n}={sum(1 for k in s if k in ('LENT','ECARTE','PONT'))}" for n, s in lots))

print(f"\n  ══════ VERDICT ══════")
if not _competent:
    print("  ⛔ AUCUN VERDICT : le juge est INCOMPETENT sur des labels rencontres.")
    print("     Un juge qui ne sait pas classer un echec ne peut pas prononcer sur le monde.")
elif l1 and l2 and l2b and l3 and l4 and l5: print("  ➤ LES CINQ LIGNES SONT VERTES — LE BANC SORT DE PANNE DIAGNOSTIQUE.")
else:
    rouges = [n for n, x in zip(["1","2","2bis","3","4","5"], [l1,l2,l2b,l3,l4,l5]) if not x]
    print(f"  ➤ LIGNE(S) ROUGE(S) : {rouges} — LE BANC RESTE EN PANNE.")
    # ⛔ UN PLAIDOYER CODE EN DUR A ETE RETIRE ICI le 21/08 : il excusait d avance une
    # ligne 4 rouge (« ce n est qu une procedure, les lignes du monde sont vertes »).
    # Un juge qui plaide pour l accuse avant d avoir lu le dossier n est pas un juge —
    # meme famille que le ROUGE code en dur retire hier.
