"""Porte K1 de la base de connaissance du moteur ( HMT-198 ). Criteres et 40 questions ecrits avant la construction de
l index ( Plane, 03/10 ).

C1  couverture : chaque module non vide de monde/pays et de guerre a au moins une fiche ; chaque fonction ou classe a
    docstring a sa fiche ( nombres egaux ).
C2  provenance : pour toutes les fiches, le fichier et la ligne existent et le texte se retrouve a sa place.
C3  recherche : sur les 40 questions du jeu B ( le jeu A est vu depuis le refus du 03/10 ), la fiche attendue dans les 5
    premieres ( hybride ) pour au moins 80 %.
Controle positif : une docstring cherchee telle quelle au rang 1 pour au moins 95 % de 200 tirees au hasard.
Information : rappels par mots seuls et par sens seul ; scores des 10 questions sans reponse.
python -m guerre.connaissance.porte_connaissance"""
import ast
import glob
import json
import os
import random
import re
import sys
import time

from . import extraire as EXT, index as IX

SORTIE = "/mnt/data/hmt/arsenal/porte_connaissance.json"

QUESTIONS = [
    ("Comment un militaire blesse est-il evacue vers l hopital militaire ?", "d26_armee_soutien.py", "evacuer"),
    ("Quelle fonction sort des munitions de l armurerie d une base quand on tire au combat ?", "d25_armee.py", "tirer"),
    ("Comment une garnison demande-t-elle du ravitaillement a sa brigade ?", "d26_armee_soutien.py", "demander"),
    ("Combien de jours de combat une garnison tient-elle en gazole, munitions et vivres ?", "d26_armee_soutien.py", "autonomie"),
    ("Comment lance-t-on une tactique pour une unite ?", "d27_armee_tactique.py", "lancer"),
    ("Quelles conditions une tactique exige-t-elle avant de partir ?", "d27_armee_tactique.py", "verifier"),
    ("Comment pose-t-on un groupe ennemi sur la carte ?", "d26_armee_soutien.py", "poser_entite"),
    ("Quelle est la chance de toucher selon la distance, la posture et le couvert ?", "d27_armee_tactique.py", "p_toucher"),
    ("Quelle blessure fait une balle selon la zone touchee et la protection ?", "d27_armee_tactique.py", "lesion"),
    ("Quand une unite sous le feu rompt-elle et se replie-t-elle ?", "d27_armee_tactique.py", "_rupture"),
    ("Comment calcule-t-on la pension de retraite ?", "d04_travail.py", "calculer_pension"),
    ("Comment la caisse verse-t-elle chaque jour pensions et indemnites ?", "d04_travail.py", "_prestations"),
    ("Que touchent la veuve et les orphelins d un assure mort ?", "d04_travail.py", "_ouvrir_reversions"),
    ("Comment blesse-t-on un habitant, avec sa gravite et sa phase aigue ?", "d16_medecine.py", "blesser"),
    ("Quel est le chemin de toute mort ?", "d01_population.py", "deceder"),
    ("Comment le moral d un habitant suit-il la faim, le chomage et l isolement ?", "d23_culture.py", "_moral_du_jour"),
    ("Comment un deces frappe-t-il le menage et les proches ?", "d23_culture.py", "_deuils"),
    ("Comment l Etat paie-t-il l importation d une arme ou d un vehicule ?", "d07_exterieur.py", "declarer_import"),
    ("L ile est-elle coupee de la mer ?", "d07_exterieur.py", "sous_blocus"),
    ("La banque centrale fournit-elle les devises d un achat a l etranger ?", "d07_exterieur.py", "_controle_devises"),
    ("Comment l Etat emprunte-t-il quand sa caisse ne suffit pas ?", "d06_etat.py", "assurer"),
    ("Comment envoie-t-on des soldats au front d Arma ?", "guerre/moteur.py", "mobiliser"),
    ("Que devient dans le moteur un soldat tue dans Arma ?", "guerre/moteur.py", "morts_au_combat"),
    ("Que fait la destruction d une centrale, d une fonderie ou d un depot ?", "guerre/frappes.py", "frapper"),
    ("Quels sont les vrais objectifs d une carte ( ports, centrales, bases ) ?", "guerre/objectifs.py", "objectifs_carte"),
    ("Comment l ile achete-t-elle un chaland ou un avion de transport ?", "guerre/projection.py", "acheter"),
    ("Combien de temps et de carburant pour traverser vers une autre ile ?", "guerre/projection.py", "traverser"),
    ("Comment les soldats d une ile attaquent-ils l objectif d une autre ?", "guerre/expedition.py", "assaut"),
    ("Que deviennent les morts et les blesses d une expedition ?", "guerre/expedition.py", "rapatrier"),
    ("Une ile peut-elle encore se battre ?", "guerre/fin.py", "peut_combattre"),
    ("Combien de jours de combat l ile tient-elle encore ?", "guerre/fin.py", "capacite"),
    ("Combien de munitions chaque soldat emporte-t-il au front ?", "guerre/logistique.py", "emporter"),
    ("Comment ravitaille-t-on les soldats au front ?", "guerre/logistique.py", "convoi"),
    ("Que fait-on d un soldat blesse dans Arma ?", "guerre/soldats.py", "evacuer_blesses"),
    ("Comment les camarades d un tue sont-ils touches ?", "guerre/soldats.py", "deuil_des_camarades"),
    ("Quel materiel a chaque base ?", "guerre/arsenal/etat_des_lieux.py", "etat_des_lieux"),
    ("Comment l arsenal est-il achete avec le budget de defense ?", "d25_armee.py", "_equiper_selon_budget"),
    ("Quelle est la portee utile d un tireur avec son arme et son optique ?", "d25_armee.py", "portee_utile"),
    ("Comment repare-t-on un objectif frappe, en combien de temps et qui paie ?", "guerre/frappes.py", "~repar"),
    ("Comment Qwen reecrit-il le gouvernement d une ile pendant la guerre ?", "guerre/conseil.py", "module"),
]
QUESTIONS_B = [                           # le jeu qui JUGE ( ecrit le 03/10 avant les changements, Plane ) ; QUESTIONS : vu
    ("Quelle protection arrete une balle et ne laisse qu une contusion ?", "d25_armee.py", "blesser_soldat"),
    ("Ou sont rangees les munitions d une base ?", "d25_armee.py", "armurerie"),
    ("Combien coute au budget un an de solde d un militaire ?", "d25_armee.py", "solde_annuelle"),
    ("Quel est le lieu de la carte le plus proche d un point ?", "d26_armee_soutien.py", "_lieu_proche"),
    ("Ou se trouve une unite, meme en mouvement ?", "d26_armee_soutien.py", "position"),
    ("Comment l armee requisitionne-t-elle des vivres dans les fermes en crise ?", "d26_armee_soutien.py", "requisitionner_vivres"),
    ("Qu y a-t-il dans les depots militaires de brigade et national ?", "d26_armee_soutien.py", "depots"),
    ("Que consomme une garnison en un jour de combat ?", "d26_armee_soutien.py", "besoins_combat"),
    ("Comment cree-t-on un camp adverse ?", "d26_armee_soutien.py", "poser_camp"),
    ("Comment construit-on une mission sans la lancer ?", "d27_armee_tactique.py", "nouvelle_mission"),
    ("Comment joue-t-on une mission d un seul tenant ?", "d27_armee_tactique.py", "executer"),
    ("Dans quel ordre trie-t-on et evacue-t-on les blesses d un combat ?", "d27_armee_tactique.py", "_traiter_pertes"),
    ("Comment les coups tires au combat sortent-ils du grand livre ?", "d27_armee_tactique.py", "_payer_tirs"),
    ("Que perd sur le terrain une unite qui rompt ?", "d27_armee_tactique.py", "_perdre_materiel"),
    ("Comment prepare-t-on le terrain d un exercice ?", "d27_armee_tactique.py", "situation_exercice"),
    ("Comment un blesse est-il admis a l hopital ?", "d17_hopitaux.py", "admettre"),
    ("Un blesse grave sans soins peut-il mourir plus tard ?", "d16_medecine.py", "_phase_aigue"),
    ("Comment se partage l heritage d un defunt ?", "d01_population.py", "_heriter"),
    ("Qui herite quand il n y a pas d enfant ?", "d01_population.py", "_heritiers"),
    ("Comment vend-on un bien a l etranger par le port ?", "d07_exterieur.py", "exporter_au_port"),
    ("Quels ports sont tenus par l ennemi ?", "d07_exterieur.py", "ports_tenus"),
    ("Quels ports ont ete detruits par une frappe ?", "d07_exterieur.py", "ports_hors_service"),
    ("Comment se ferment chaque soir les comptes de l Etat ?", "d06_etat.py", "_cloture"),
    ("Comment fixe-t-on la solde d un appele ?", "d04_travail.py", "fixer_taux"),
    ("Que se passe-t-il quand un payeur n a pas assez d argent ?", "d04_travail.py", "_payer"),
    ("Combien de temps met un convoi par la route ?", "d15_logistique.py", "duree_convoi_pas"),
    ("Comment le moral d un soldat au front suit-il sa maison ?", "d23_culture.py", "_au_front"),
    ("Comment un autre domaine fait-il pleurer des habitants ?", "d23_culture.py", "_deuils_poses"),
    ("Comment un soldat tire-t-il les coups que le pont lui compte ?", "guerre/logistique.py", "tirer"),
    ("Que devient la charge d un convoi si le soldat meurt en route ?", "guerre/logistique.py", "avancer"),
    ("Combien de coups portent les soldats de chaque base ?", "guerre/logistique.py", "portees"),
    ("Pourquoi une traversee ne peut-elle pas partir ?", "guerre/projection.py", "raison_refus"),
    ("Ou stationnent un chaland et un avion ?", "guerre/projection.py", "lieu_de_base"),
    ("Quels hommes partent en expedition, et avec quelles statistiques ?", "guerre/expedition.py", "corps"),
    ("Quelle compagnie defend un objectif attaque ?", "guerre/expedition.py", "defenseur"),
    ("Comment les survivants d une operation rentrent-ils ?", "guerre/expedition.py", "demobiliser"),
    ("Comment calcule-t-on les degats ponderes d un objectif ?", "guerre/frappes.py", "degats"),
    ("Qui sont les soldats aptes d une ile ?", "guerre/fin.py", "aptes"),
    ("Quels taux de guerre le conseil lit-il dans le journal de l horloge ?", "guerre/conseil.py", "scenario"),
    ("Que rend le pont pour incarner les convois militaires dans Arma ?", "d26_armee_soutien.py", "a_incarner"),
]
SANS_REPONSE = [
    "Comment un chasseur F-16 intercepte-t-il un bombardier ?", "Mission SEAD contre une batterie SA-10",
    "Le porte-avions lance sa patrouille aerienne de combat", "Tir d un missile de croisiere Tomahawk sur un port",
    "Le sous-marin lance une torpille sur la fregate", "Ravitaillement en vol des avions de combat",
    "Pose de mines navales devant le port", "Defense antimissile balistique de la capitale",
    "Satellite de reconnaissance au-dessus de l ile", "Bombardement strategique de nuit par B-52",
]


def attendu(f, fich, nom):
    if not f["fichier"].endswith(fich): return False
    base = f["nom"].split("~")[0]
    if nom == "module": return f["type"] in ("module", "section")
    if nom.startswith("~"): return nom[1:] in base.lower() or nom[1:] in f["texte"][:200].lower()
    return base == nom or base.endswith("." + nom)


def _norm(t): return re.sub(r"\s+", " ", t).strip()


def main():
    t0 = time.time(); R = {}
    racine = EXT.RACINE; fs = IX.charger()
    print(f"PORTE K1 DE LA BASE DE CONNAISSANCE : {len(fs)} fiches", flush=True)
    # C1
    attendues = set(); sans = []
    for motif in ("monde/pays/*.py", "guerre/**/*.py"):
        for f in sorted(glob.glob(os.path.join(racine, motif), recursive=True)):
            rel = os.path.relpath(f, racine)
            if "/connaissance/" in rel or "__pycache__" in rel: continue
            src = open(f, encoding="utf-8").read()
            if not src.strip(): continue
            if not any(x["fichier"] == rel for x in fs): sans.append(rel)
            m = ast.parse(src)
            def visiter(noeuds, pre):
                for n in noeuds:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if ast.get_docstring(n): attendues.add((rel, pre + n.name))
                        visiter(n.body, pre + n.name + ".")
            visiter(m.body, "")
    tenues = {(x["fichier"], x["nom"].split("#")[0].split("~")[0]) for x in fs if x["type"] in ("fonction", "classe")}
    tenues_ici = {t for t in tenues if t[0].startswith("monde/pays/") or t[0].startswith("guerre/")}
    C1 = not sans and attendues == tenues_ici
    R["C1"] = {"ok": C1, "modules_sans_fiche": sans[:10], "attendues": len(attendues), "tenues": len(tenues_ici),
               "manquantes": sorted(attendues - tenues_ici)[:10], "en_trop": sorted(tenues_ici - attendues)[:10]}
    print(f"  C1 couverture : {'OUI' if C1 else 'NON'} {R['C1']}", flush=True)
    # C2
    cache = {}; fautes = []
    for x in fs:
        p = os.path.join(racine, x["fichier"])
        if p not in cache: cache[p] = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        src = cache[p]
        if src is None: fautes.append((x["id"], "fichier")); continue
        lignes = src.splitlines()
        if not 1 <= x["ligne"] <= max(1, len(lignes)): fautes.append((x["id"], "ligne")); continue
        n = _norm(src)
        if x["type"] in ("fonction", "classe"):
            nom = x["nom"].split("#")[0].split("~")[0].split(".")[-1]
            if not re.search(rf"\b(def|class)\s+{re.escape(nom)}\b", lignes[x["ligne"] - 1]): fautes.append((x["id"], "def")); continue
            corps = x["texte"].split("\n", 1)[1] if "\n" in x["texte"] and not x["id"].count("#") else x["texte"]
        elif x["type"] == "section":
            corps = x["texte"].split("\n", 1)[1] if "\n" in x["texte"] else x["texte"]
        else: corps = x["texte"]
        if x["type"] == "constantes":
            nues = {l.strip() for l in lignes}
            if not all(l.strip() in nues for l in x["texte"].splitlines() if l.strip()): fautes.append((x["id"], "constantes"))
        elif x["type"] in ("module", "section"):
            if p + "#doc" not in cache: cache[p + "#doc"] = _norm(ast.get_docstring(ast.parse(src)) or "")
            if _norm(corps) not in cache[p + "#doc"]: fautes.append((x["id"], "texte"))
        elif _norm(corps) not in n: fautes.append((x["id"], "texte"))
    C2 = not fautes
    R["C2"] = {"ok": C2, "fautes": len(fautes), "exemples": fautes[:10]}
    print(f"  C2 provenance : {'OUI' if C2 else 'NON'} {R['C2']}", flush=True)
    # C3 et l information
    I = IX.ouvrir()
    if I.vecteurs is None: raise SystemExit("pas de vecteurs : python -m guerre.connaissance.index construire")
    res = {}; vu = {}
    for mode in ("hybride", "mots", "sens"):
        rangs = []
        for q, fich, nom in QUESTIONS:
            top = I.chercher(q, k=50, mode=mode)
            rangs.append(next((k + 1 for k, (f, _s) in enumerate(top) if attendu(f, fich, nom)), None))
        vu[mode] = sum(1 for r in rangs if r and r <= 5) / len(rangs)
        rangs = []
        for q, fich, nom in QUESTIONS_B:
            top = I.chercher(q, k=50, mode=mode)
            r = next((k + 1 for k, (f, _s) in enumerate(top) if attendu(f, fich, nom)), None)
            rangs.append(r)
        res[mode] = {"rappel_5": sum(1 for r in rangs if r and r <= 5) / len(rangs), "rangs": rangs}
    C3 = res["hybride"]["rappel_5"] >= 0.8
    rates = [(QUESTIONS_B[k][0], r) for k, r in enumerate(res["hybride"]["rangs"]) if not r or r > 5]
    R["C3"] = {"ok": C3, "rappel_5_hybride": res["hybride"]["rappel_5"], "rappel_5_mots": res["mots"]["rappel_5"],
               "rappel_5_sens": res["sens"]["rappel_5"], "manquees": rates, "jeu_vu_en_information": vu}
    print(f"  C3 recherche : {'OUI' if C3 else 'NON'} {R['C3']}", flush=True)
    # controle positif
    rng = random.Random(198)
    docs = [x for x in fs if x["type"] in ("fonction", "classe") and "\n" in x["texte"] and len(x["texte"].split("\n", 1)[1]) > 60]
    tir = rng.sample(docs, min(200, len(docs)))
    bons = 0
    for x in tir:
        q = x["texte"].split("\n", 1)[1]
        top = I.chercher(q, k=1)
        if top and (top[0][0]["id"] == x["id"] or _norm(top[0][0]["texte"]) == _norm(x["texte"])): bons += 1
    CP = bons / len(tir) >= 0.95
    R["controle_positif"] = {"ok": CP, "au_rang_1": bons, "sur": len(tir)}
    print(f"  controle positif : {'OUI' if CP else 'NON'} {R['controle_positif']}", flush=True)
    # information : les questions sans reponse ( le meilleur cosinus )
    cos_q = [float(max(I.sens(q))) for q, *_ in QUESTIONS]
    cos_n = [float(max(I.sens(q))) for q in SANS_REPONSE]
    R["information"] = {"cosinus_max_questions": sorted(round(c, 3) for c in cos_q), "cosinus_max_sans_reponse": sorted(round(c, 3) for c in cos_n)}
    print(f"  information : {R['information']}", flush=True)
    verdict = "FRANCHIE" if (C1 and C2 and C3 and CP) else "REFUSEE"
    R.update(verdict=verdict, fiches=len(fs), duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE K1 DE LA BASE DE CONNAISSANCE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_CONNAISSANCE", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
