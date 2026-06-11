# DOCTRINE-RÉPERTOIRE — recherche approfondie sur les formes d'attaque et de défense
*(2026-06-10, archi — base : FM 3-90/ADP 3-90 US, doctrine soviétique de l'art opératif, exemples classiques ;
chaque forme est mappée sur les primitives du harnais : phases × ordres(but, posture) × contingences(goto) × done_when)*

## Pourquoi ce catalogue est LA plus-value
1. Chaque pièce est **Arma-exécutable par construction** (pas de fiction de sim → pas de mur sim-to-real).
2. Le **sélecteur** (officier) choisit dans un répertoire fini et mesuré → données réelles, variantes par situation.
3. La **matrice attaque×défense** devient le terrain de jeu de la co-évolution : plus le répertoire est riche,
   plus la valeur de sélection monte (verdict Gate 1 : +4.2 pts seulement sur 3 défenses → il faut élargir).
4. Les **knobs de variante** (axes, seuils, allocation d'escouades, timing) = l'espace que le RL explorera ensuite.

## A. FORMES OFFENSIVES (les 6 classiques + dérivées)
| # | Forme | Mécanisme | Bat | Battue par | Statut |
|---|---|---|---|---|---|
| M1 | Attaque frontale appuyée | base de feu + assaut direct | défenses minces | défense en profondeur (mesuré : depth 18.8 %) | ✅ mesurée |
| M2 | Double enveloppement | pression simultanée 2 flancs | défense statique (62.5→… loi des 2 axes) | réserve anti-flanc (18.8 %) | ✅ mesurée |
| M3 | Enveloppement simple | fixer + déborder flanc lourd | passive (62.5 %), anti-centre (50 %) | anti-flanc (21.9 %) | ✅ mesurée |
| M4 | Assaut massé | masse sur 1 axe sans appui | défenses faibles (plafond v3 100 %) | toute défense compétente | ✅ mesurée |
| M5 | Feinte + débordement | fixation PHYSIQUE par la démo | écrans statiques | (à mesurer vs mobile) | ✅ mesurée |
| M6 | Infiltration | axes couverts, assaut rapproché sans base de feu | écrans lâches | spot élevé, hérisson | ✅ mesurée |
| M7 | Attaque échelonnée | échelons successifs, passage de lignes | (préservation) | défaite en détail (mesuré 25 %) | ✅ mesurée |
| **M8** | **Percée (penetration)** | TOUTE la force sur un axe ÉTROIT → rupture → exploitation vers l'arrière | défenses étalées/cordon | défense en profondeur, réserve mobile | 🆕 codée |
| **M9** | **Mouvement tournant** | marche profonde, prise de l'ARRIÈRE avant l'objectif → force la défense à sortir | défenses ancrées au terrain | réserve mobile, hérisson (rien à tourner) | 🆕 codée |
| **M10** | **Marteau-enclume** | bloc au nord (enclume) + assaut sud (marteau) → l'ennemi qui rompt meurt sur le bloc | défenses élastiques/qui replient | hérisson (ne bouge pas) | 🆕 codée |
| **M11** | **Raid (coup de main)** | détruire vite, partir AVANT la contre-attaque | garnisons isolées | appât (le raid fonce dans le piège) | 🆕 codée |
| **M12** | **Reconnaissance en force** | sonde 1 escouade → le plan SE DÉCIDE sur sa réception (branchement par contingences) | défenses inconnues (= méta-manœuvre adaptative) | coût du temps de sonde | 🆕 codée |
*(Non codables à cette échelle : exploitation de poursuite (pas de profondeur de théâtre), attaque par le feu seule (pas de prise).)*

## B. OPÉRATIONS DÉFENSIVES (le miroir, celui qui manquait)
| # | Forme | Mécanisme | Bat | Battue par | Statut |
|---|---|---|---|---|---|
| D0 | Défense de zone (passive) | garnison + écran de patrouilles | attaques sans appui | M3/M2 (mesuré) | ✅ mesurée (« skilled ») |
| D1 | Réserve anti-flanc | les patrouilles se massent sur le flanc menacé | enveloppements (M3 : −40.6 pts) | frontal M1, (feinte ?) | ✅ mesurée (« skilled_react ») |
| D2 | Bloc anti-centre | bloc central avancé si contact frontal | frontal (M1 : 50→18.8) | enveloppements (M3 50 %) | ✅ mesurée (« react_depth ») |
| **D3** | **Réserve mobile (strike force)** | force de frappe au nord ; CONTRE-ATTAQUE sur le centroïde des contacts connus | l'attaquant CONCENTRÉ (percée, massé) | attaques dispersées, feinte (frappe la démo) | 🆕 codée |
| **D4** | **Défense élastique (en profondeur)** | lignes successives 16000→16150→16270 ; on recule sous pression, l'attaquant s'étire | percée, frontal (rien à rompre) | marteau-enclume (le repli meurt sur le bloc) | 🆕 codée |
| **D5** | **Hérisson (réduit)** | TOUT le monde dans le complexe, périmètre dense, pas d'écran | infiltration, raid, tournant (rien dehors) | appui-feu massif + assauts convergents | 🆕 codée |
| **D6** | **Appât (retraite feinte)** | la garnison ABANDONNE l'objectif → surplombs nord → contre-assaut quand ≥3 attaquants dessus | raid, massé (foncent dans le vide) | attaquant patient/qui consolide hors zone | 🆕 codée |
| **D7** | **Sortie préventive (spoiling)** | au premier contact, patrouilles + moitié garnison ATTAQUENT les zones de rassemblement sud | plans à mise en place lente (M1, M7) | infiltration (déjà passée), réserve forte | 🆕 codée |
*(Non codables proprement ici : retardement/échange d'espace (théâtre trop petit), contre-pente vraie (terrain plat au complexe).)*

## C. LES KNOBS DE VARIANTE (l'espace des situations — pour le sélecteur puis le RL)
- **Axes** : ouest/est/sud/nord — toute manœuvre à flanc a son miroir (M3-O vs M3-E) → ×2 le répertoire gratuitement.
- **Allocation** : qui appuie / qui assaute / qui bloque (ex. M10 à enclume double = M2 + bloc).
- **Seuils de contingence** : pertes (0.08 prudent → 0.45 mordant), pas de phase — c'est le « tempérament » du chef.
- **Timing défensif** : seuils de repli D4 (0.7/0.4), seuil de déclenchement D6 (2 contacts) — agressivité de la défense.
- **Composition** : qrf inf/mech, effectifs (mult), compétences (pro), chasse (hunt) — déjà paramétrés.

## D. INTERACTIONS PRÉDITES (hypothèses pour la grande matrice 12×8 — PRÉ-ENREGISTRÉES en bloc, à affiner par cellule avant mesure)
- M8 percée : forte vs D0/D5-cordon, FAIBLE vs D2/D4 (la profondeur avale la rupture).
- M9 tournant : fort vs D0/D1 (ancrées), FAIBLE vs D5 hérisson (rien à tourner) et D3 (la frappe attrape la marche).
- M10 marteau-enclume : LE contre de D4 élastique (le repli meurt sur le bloc) ; cher vs D5.
- M11 raid : fort vs D0/D2, SUICIDAIRE vs D6 appât.
- M12 reco-en-force : ne gagne jamais le plus, ne perd jamais le plus — sa valeur = ROBUSTESSE inter-défenses
  (c'est un mini-officier en SQF : si sa moyenne ≈ celle du sélecteur parfait, le sélecteur appris devra le battre).
- D6 appât : tueuse de M4/M11, vulnérable à M1 patient (l'appui-feu traite les surplombs).
- D3 mobile : tueuse de concentration (M4/M8), vulnérable à M5 (frappe la démonstration → le vrai effort passe).

## E. PROTOCOLE (discipline inchangée)
Smoke 1 op par pièce nouvelle (validité SQF/plan) → prédictions par cellule AVANT mesure → matrice par vagues n=16
bornées (mur 1200 s) → n=32 sur les cellules pivots serrées → valeur de sélection recalculée sur le répertoire élargi.
Coût estimé matrice complète 12×8 = 96 cellules ; on mesure d'abord les COLONNES NOUVELLES (5 défenses × 6-7 attaques utiles)
et les LIGNES NOUVELLES (5 attaques × 3 défenses connues) ≈ 50 cellules ≈ 2 nuits de flotte bornée.
