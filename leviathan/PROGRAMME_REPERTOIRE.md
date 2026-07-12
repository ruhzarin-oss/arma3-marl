# PROGRAMME — Maîtrise du répertoire complet des agents (leviathan001)

## MISSION
Amener TOUT le répertoire de combat des agents-soldats à ✅. Tu construis et entraînes ~17 briques
restantes, EN CHAÎNE, dans l'ordre de dépendance ci-dessous. Chaque brique = un env vectorisé (torch) +
un entraînement PPO A/B (voyant/aveugle), comme les briques déjà faites. Tu travailles dans
`/home/younes/arma3-marl/leviathan/`, venv `~/arma3-marl/.venv`, GPU `CUDA_VISIBLE_DEVICES=0` (3090 ;
Ollama y tourne aussi → laisse de la marge, ~2048-4096 envs OK).

## DÉJÀ FAIT (réutilise, ne refais pas)
`reflex_r1` (réaction au feu), `reflex_r23wh` (tir réactif visé), `reflex_travel` (voyage 92%),
`suppression_voyant` (clouer), `bounding` (feu-et-mouvement), `formations`, `sf-infiltration` (furtivité+
takedown), `coevo_nuit2_fs` (commandant), Qwen officier, `PatrolBrain`. Les `*_env.py`/`*_train.py`
existants sont tes MODÈLES de structure.

## MÉTHODE — le pattern de brique (prouvé, suis-le)
1. `XXX_env.py` : classe `XXXEnv(n, device, blind=False)` vectorisée ; `_obs()` ; `step(action)` →
   `(obs, reward, done, info)` ; auto-reset des envs done ; `obs_dim`. Flag `blind` met à 0 la
   perception clé (l'A/B prouve que la perception paie).
2. `XXX_train.py` : `XXXNet` (MLP obs→128→têtes+value), `act()`, `evaluate()`, `train(blind,...)` PPO
   (gamma .99, lam .95, clip .2, 4 epochs, ent .02-.03). Sauve `XXX_voyant.pt`/`XXX_aveugle.pt`.
   Affiche la métrique de succès toutes les 150 iters + l'écart final voyant-aveugle.
3. SMOKE d'abord : 512 envs, ~40 iters. **Vérifie que la baseline (it 0) n'est PAS trop haute** (si
   >70%, l'env est trop facile → DURCIS : rends le succès DÉPENDANT du skill, ajoute un coût/contrainte).
4. Entraînement complet : 500-600 iters, 4096 envs, `nohup ... > log 2>&1 </dev/null &` (PAS de `pkill -f`
   du nom de la brique dans la même commande → ça se tue soi-même !). Lis le log à la fin.
5. Logge le résultat dans `PROGRESSION.md` (brique, voyant%, aveugle%, écart) et passe à la suivante.

## GOTCHAS (leçons chères — ne les refais pas)
- **Baseline trop facile** = l'A/B s'effondre. Le succès doit EXIGER le skill (ex. suppression : ajouter
  un budget MUNITION serré force à TIMER au lieu d'arroser).
- **Coût/contrainte** rend le skill réel : munition limitée, exposition au tir, temps, distance.
- **Reward = PROGRÈS** (shaping dense) + gros bonus à l'accomplissement + pénalité à l'échec. Pas juste
  sparse.
- **Lancement** : `nohup python xxx_train.py ... > log 2>&1 </dev/null &` puis `echo $!`. JAMAIS
  `pkill -f xxx_train` dans la même ligne (matche la commande ssh elle-même).
- **cuda:0 = 3090** (Ollama y vit, ~9 Go libres → 2048-4096 envs ok ; 50000 envs non).
- Précédence SQF si tu touches au live : `round ((getPosATL _x)#0)` jamais `round (getPosATL _x)#0`.
- Juge au COMPORTEMENT/métrique, pas au reward brut.

## PROTOCOLE
Pour chaque brique dans l'ordre : construire env → smoke → durcir si baseline>70% → train complet →
logger → suivante. Ne bloque pas sur l'A/B parfait : si le VOYANT apprend le skill (métrique haute depuis
une baseline basse), garde-le et avance. Vise 1 brique / ~10-15 min.

---

# CATALOGUE DES BRIQUES (ordre de dépendance)

## PHASE A — cœur tactique (casse le « frontal = suicide »)
**A2. Flanc / enveloppement** *(dép : suppression)*
- Apprend : ROUTER par le flanc/l'arrière d'un ennemi retranché pendant qu'un élément le cloue, au lieu de l'assaut frontal.
- Env : 1 manœuvrier vs 1 ennemi retranché (champ de tir frontal large, flancs faibles) ; un ami supprime (réduit le feu frontal). Obs : pos+orientation ennemi, secteur de feu frontal (létal), ouverture flanc gauche/droite, ami-supprime, ma progression. Action : déplacement 8 dir. Reward : atteindre le flanc/arrière (zone <90° derrière l'ennemi) = +10 ; pénalité forte si on entre dans le cône frontal ; survie.
- Métrique : % atteint le flanc vivant. Blind = ne voit pas l'orientation/le cône → fonce frontal → meurt.

**A3. Soutien mutuel** *(dép : -)*
- Apprend : couvrir l'angle mort d'un coéquipier (quand il est exposé/recharge, je couvre son secteur).
- Env : 2 agents (1 appris + 1 ami scripté qui s'expose par moments) vs ennemis multi-secteurs. Obs : secteur où l'ami est exposé/vulnérable, mes secteurs ennemis. Action : choisir le secteur à couvrir. Reward : survie de l'AMI (couvert au bon moment) + survie propre.
- Métrique : survie de l'ami. Blind = ne voit pas la vulnérabilité de l'ami.

## PHASE B — outils du soldat
**B4. Grenade** *(dép : -)*
- Apprend : utiliser une grenade quand l'ennemi est en couvert DUR (tir direct bloqué) ; sinon tir visé.
- Env : ennemi derrière couvert dur (tir direct = 0 effet) OU à découvert ; grenade dispo (1-2), arc par-dessus le couvert. Obs : ennemi-en-couvert-dur (flag), distance, grenades restantes, mon exposition. Action : tir visé / grenade / couvert. Reward : neutraliser l'ennemi (SEULE la grenade marche sur le couvert dur) ; économiser les grenades.
- Métrique : % ennemi-en-couvert neutralisé. Blind = ne voit pas qu'il est en couvert → tire dans le vide.

**B5. CQB** *(dép : -)*
- Apprend : combat rapproché — dégager des angles, ID rapide, courte portée, plusieurs ennemis proches.
- Env : intérieur (pièces/angles) ; 2-3 ennemis surgissent à courte portée selon l'angle franchi. Obs : ennemis proches par secteur (apparition selon position), angle non-dégagé. Action : déplacement + tir secteur. Reward : nettoyer (tous neutralisés) + survie ; pénalité de se faire surprendre par un angle non couvert.
- Métrique : % pièce nettoyée vivant.

**B6. R4 repli propre** *(dép : -)*
- Apprend : décrocher quand SUBMERGÉ — bondir vers le couvert arrière en minimisant l'exposition, au lieu de mourir sur place.
- Env : 1 soldat vs trop d'ennemis (perdant) ; couvert derrière. Obs : niveau de submersion (nb menaces vs ma capacité), dir du couvert arrière, mon exposition. Action : tenir/tirer / bondir-au-couvert-arrière. Reward : SURVIVRE un combat perdu en se repliant intact (atteindre le couvert arrière vivant) ; mourir en restant = échec.
- Métrique : % survie quand submergé. Blind = ne sent pas la submersion → reste → meurt.

**B7. Soin de soi (ACE)** *(dép : -)*
- Apprend : quand blessé (pas mort), se mettre à couvert + se soigner AVANT de ré-engager.
- Env : soldat qui peut être blessé (saignement → dégradation continue → mort si non soigné) ; ennemi. Obs : mon saignement/santé, menace actuelle, suis-je à couvert. Action : combattre / couvert+soin. Reward : survie longue (se soigner au bon moment évite la mort lente) ; ré-engager en saignant = mort.
- Métrique : % survie avec gestion du saignement.

## PHASE C — rôles spécialisés (la divergence)
**C8. Médic** *(dép : soutien mutuel)*
- Apprend : rejoindre un coéquipier À TERRE (inconscient ACE) sous le feu et le ranimer (force qui dure).
- Env : 1 médic + des amis qui tombent (inconscients, pas morts) + ennemis. Obs : pos du blessé le + proche, menace sur le trajet/la zone, suis-je à couvert. Action : aller-au-blessé / ranimer / se couvrir. Reward : amis RANIMÉS (chacun = +) ; se faire tuer en route = pénalité ; équilibre risque/sauvetage.
- Métrique : % blessés ranimés. = transforme l'ACE médical en atout (la force ne fond pas).

**C9. AT (anti-véhicule)** *(dép : -)*
- Apprend : engager un véhicule (Tigr/BTR) au lance-roquettes — viser le point faible, puis SE REPLACER (back-blast/exposition).
- Env : 1 AT + 1 véhicule (blindage frontal fort, arrière/flanc faible, il tire/écrase) ; 1-2 roquettes. Obs : pos+orientation+type véhicule, mon angle (frontal/flanc/arrière), roquettes, mon couvert. Action : tirer-AT (depuis l'angle courant) / se replacer / couvert. Reward : véhicule détruit (seulement si tir au flanc/arrière) + survie ; tir frontal = gaspillé + repéré.
- Métrique : % véhicule détruit vivant.

**C10. Mitrailleur / servant statique** *(dép : suppression)*
- Apprend : servir une arme statique (KORD/mortier) — suppression de ZONE soutenue depuis un poste fixe, gérer surchauffe/munitions, traverser vers les menaces.
- Env : servant fixe + ennemis qui avancent par vagues sur plusieurs axes ; chaleur monte au tir continu (enraye si surchauffe). Obs : densité ennemie par secteur, chaleur, munitions. Action : traverser+tirer secteur / cesser (refroidir). Reward : ennemis arrêtés/zone tenue ; gérer chaleur+munitions (rafales, pas continu).
- Métrique : ennemis arrêtés sans enrayer.

**C11. Grenadier** *(dép : grenade)*
- Apprend : UGL/frag à distance sur des GROUPES ou du couvert (variante portée de la grenade).
- Env : groupes ennemis serrés / en couvert à 50-200 m ; UGL (arc balistique, dégâts de zone). Obs : groupes (densité+pos), couvert, munitions UGL. Action : viser-lober secteur+distance / tir fusil / couvert. Reward : dégâts de zone (toucher un groupe = gros), économiser l'UGL.
- Métrique : ennemis neutralisés par tir indirect.

**C12. Marksman** *(dép : -)*
- Apprend : tir de précision longue portée — choisir les cibles PRIORITAIRES (officier, MG), patience, exposition minimale.
- Env : cibles variées à 200-500 m, certaines à HAUTE VALEUR (officier/MG = effet d'équipe) ; s'exposer pour tirer attire le contre-feu. Obs : cibles (pos+priorité), distance, mon exposition. Action : viser-tirer cible / attendre / couvert. Reward : tuer du HAUTE VALEUR (×3 vs un troufion) ; rester non repéré.
- Métrique : valeur neutralisée / exposition.

**C13. Sapeur** *(dép : -)*
- Apprend : brèche (poser une charge sur un mur/une porte, reculer, détoner) et éviter/poser des mines.
- Env : obstacle à brécher (mur/porte) gardé ; charge à poser au contact puis distance de sécurité ; mines sur le terrain (éviter). Obs : point de brèche, distance, charge posée/non, mines proches. Action : avancer / poser-charge / reculer / détoner. Reward : brèche faite + survie (reculé hors souffle) ; sauter sur une mine/son propre souffle = échec.
- Métrique : % brèche réussie vivant.

## PHASE D — team avancé
**D14. Assaut d'objectif** : COMPOSE suppression+flanc+CQB → entrer et nettoyer un objectif défendu. Env multi-agents (base de feu + élément d'assaut). Métrique : objectif pris, pertes minimales.
**D15. Repli en équipe** : décrochage COORDONNÉ (un élément couvre pendant que l'autre se replie, alterné = bounding inverse). Métrique : % escouade extraite intacte.
**D16. Récupération de blessés** : 2 agents — un PORTE le blessé (drag/carry, lent, vulnérable), l'autre COUVRE. Métrique : blessé ramené au couvert.
**D17. Ratissage** : balayer une zone pour trouver des ennemis CACHÉS (motif de recherche, couverture max, ne pas laisser de trou). Métrique : % ennemis cachés trouvés.
**D18. Embuscade** : se positionner + DÉCLENCHER au bon moment (tenir le feu jusqu'au trigger pour effet max, kill-zone). Métrique : % colonne ennemie détruite dans la kill-zone.

## PHASE E — commandement + contextes
**E19. Appui indirect** : niveau commandant — appeler/ajuster un tir de mortier sur une zone (corrections). Réutilise `commander_env`. Métrique : cibles neutralisées par l'indirect.
**E20. Allocation véhicules** : FINIR `commander_drone` (allouer drones/véhicules aux menaces, fog-mémoire). Déjà bâti — relancer le curriculum D4→8→12.
**E21. Nuit (doctrine)** : comportement dédié d'exploitation de la nuit (bouger dans l'ombre, NVG, frapper l'angle mort). Réutilise le cycle jour/nuit + co-évo nuit.
**E22. Défense statique** : tenir une position (FOB) — secteurs, champs de tir, positions de repli. Métrique : % assauts repoussés.
**E23. Véhicules (conduite)** : monter/conduire/débarquer (locomotion véhicule, transport de l'escouade).

## PHASE F — co-évolution (raffine TOUT)
Une fois le répertoire en place : league AlphaStar (pool de politiques, meilleure-réponse alternée
attaquant/défenseur) qui RAFFINE l'usage des briques par la pression adverse → flanc/nuit/feinte émergent
et se stabilisent (anti-oubli = la league). Réutilise `coevo_sandbox.py`/`traque_league.py`.

---

# SORTIE ATTENDUE
- 1 `.pt` par brique (`XXX_voyant.pt`) dans `leviathan/`.
- `PROGRESSION.md` : tableau brique × (voyant%, aveugle%, écart, note).
- À la fin : le répertoire complet ✅, prêt à composer dans le live (deux-corps + officier).
- Tourne en continu (remplit la nuit) ; à chaque brique finie, enchaîne la suivante sans attendre.
