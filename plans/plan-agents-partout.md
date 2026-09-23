# Tous les acteurs en agents — portes écrites le 23/09/2026, AVANT toute mesure

Demande de Younes : « pousse-les en mode agents right now » — les habitants, les entreprises, les marchés, le
commerce entre marchés, l'armée, les voyageurs. Même méthode que les ménages, qui a marché (faim 20 % → 7,9 %) :

- **une décision** par groupe, prise par l'agent là où une règle la prenait ;
- **une note qui revient à celui qui a choisi, lue sur trois jours** (la leçon des ménages : une note lue le soir
  même apprend à ne rien faire) ;
- **une doctrine commune** au groupe (bandit contextuel linéaire, poids partagés, écrits sur disque) et une mémoire
  propre à chaque agent ;
- **deux témoins** : la règle d'origine, et le hasard ;
- **une porte écrite ici, avant de voir un chiffre.**

## L'épreuve commune

Un monde de 20 jours, avec l'épidémie de Pyrgos (jour 2) et une sécheresse sur deux capitales sur trois pendant
douze jours (l'épreuve v2 de l'apprenti marchand, dont les témoins se séparent). Mondes d'école : graines 1 à 8.
Examen : graines 101 à 110, jamais vues. Chaque groupe est formé **seul**, les autres restant sur leurs règles, pour
que l'effet mesuré soit le sien.

**Note nationale** : `−100 × part moyenne de ménages sans nourriture − 5 × morts`.

**Porte commune** : le groupe formé bat **la règle** (note médiane, et au moins 7 mondes sur 10) **et le hasard**
(note médiane). Sinon il est refusé et reste sur sa règle.

## Les six groupes

| groupe | décision de l'agent | ce qu'il voit | sa note sur trois jours | note jugée |
|---|---|---|---|---|
| **travailleurs** | chaque matin : aller travailler ou rester (couvre quarantaine et épuisement) | sa maladie, sa faim, la caisse de son ménage, la quarantaine, les malades de son lieu de travail | ménage nourri, −2 s'il tombe malade | nationale, **et** part d'infectés au pic |
| **fraudeurs** (les ménages) | à chaque achat : payer la TVA ou frauder | le taux, la police de sa capitale, les amendes reçues | argent gardé moins amendes | **comportementale** : la fraude doit baisser quand les contrôles montent |
| **entreprises** | chaque aube : activité 10 %, 40 %, 70 % ou 100 % | prix contre coût, stock de son marché, caisse, intrants, faim de sa région | profit + région nourrie | nationale |
| **marchés** | chaque aube, par bien : prix −10 %, −5 %, 0, +5 %, +10 % | demande contre offre, stock, prix mondial, faim de sa région | région nourrie + stock dans la bande + caisse | nationale |
| **commerce** | trois fois par jour, par marché et par bien : rien, vers le plus cher, vers le moins pourvu, vers le plus proche | écarts de prix, stocks, routes | région d'arrivée nourrie + marge | nationale, et bat aussi le commerce aveugle |
| **armée** | chaque matin, par base : stock visé 0, 3, 5 ou 8 jours | son stock, le dépôt national, la dernière livraison | patrouilles tenues − annulées − coût du stock | **patrouilles tenues** sur une épreuve à routes de bases coupées au hasard |
| **voyageurs** | chaque matin, par île : rester, ou partir avec nourriture, carburant ou remèdes vers l'île où ce bien est le plus cher | prix des îles, stocks | marge + île d'arrivée nourrie | nationale, **monde à six îles et 2 000 habitants** (faim 11,9 % avec les règles) |

Les voyageurs portent désormais une **cargaison** : c'est le premier fret maritime, et la conservation doit le voir.

L'hôpital reste une règle : un malade grave n'a pas le choix.

---

## Verdicts — 23/09, première formation (commit 21d060a, 450 s pour les sept groupes)

Examen sur les mondes 101-110, doctrines relues du disque :

| groupe | verdict | mesure |
|---|---|---|
| armée | **RETENU** | patrouilles tenues : formée 0,894, règle 0,765, hasard 0,835 — 9/10 contre la règle |
| fraudeurs | **RETENU** | fraude 56 % sous police ×1, 0 % sous police ×4 — elle baisse dans 10/10 mondes |
| travailleurs | refusé | note −22,79 contre −22,61 (5/10) ; pic d'infectés 11,1 % contre 10,8 % |
| entreprises | refusé | note −42,0 contre −22,6 (0/10) : elles ralentissent pour leur profit, la région a faim |
| marchés | refusé | note −27,5 contre −22,6 (5/10) ; hasard −33,4 |
| commerce | refusé | note −26,4 contre −22,6 (3/10) ; **aveugle −21,9** |
| voyageurs | refusé | note −31,3 contre −45,9 pour la règle (8/10), mais hasard −25,8 et aveugle −26,2 |

**Ce que les échecs disent.** Les deux groupes retenus ont une note qui dépend directement de leur choix. Les cinq
refusés ont une note surtout nationale, presque insensible à leur décision : leur récompense par époque est restée
plate (travailleurs 0,79 sur six époques, marchés 0,62, commerce 0,75). Quand la note est individuelle, elle trahit
le pays : les entreprises ont maximisé leur profit en affamant leur région.

**Ce qui suit, sans toucher aux portes.** Toute nouvelle tentative sur un groupe refusé est une tentative nouvelle,
annoncée d'avance et confirmée sur une troisième série de mondes (graines 201-210). La piste : une note qui mesure
l'effet de CE choix sur ceux qu'il sert (la faim de la région livrée avant et après), pas la moyenne du pays.

**Deux décisions pour Younes, mesurées** : adopter le **fret aveugle** comme règle de base des voyageurs (−26,2 contre
−45,9 sans cargaison), et le **commerce aveugle** comme règle du commerce (−21,9 contre −22,6 ici, et déjà gagnant le
22/09 sur deux séries).

---

## Tentative 2 pour les cinq refusés — écrite le 23/09 AVANT la mesure

**Le diagnostic de la tentative 1.** La note des refusés était surtout nationale : leur récompense par époque est
restée plate, parce que leur choix changeait à peine « ma région a-t-elle mangé ? ». Et la seule part nette de leur
note — la marge, le profit — tirait dans le sens de la règle de rentabilité, ou contre le pays.

**Le principe de la tentative 2** : noter l'effet de CE choix sur ceux qu'il touche, mesuré dans le monde.

| groupe | nouvelle note |
|---|---|
| commerce | un camion vaut ce qu'il manquait là où il arrive : `min(1, manque de la destination / cargaison)` (+ 0,1 × marge). Ne rien envoyer vaut `0,5 × (1 − plus grand manque ailleurs)` : garder son surplus n'est bon que si personne n'en a besoin — sinon il part au port. |
| voyageurs | même règle, d'île à île. |
| entreprises | son marché tenu dans la bande (entre 0,5 et 2 fois la cible de son produit) vaut 1, sinon 0 ; + 0,3 × profit borné. Le profit ne commande plus. |
| marchés | le prix de la nourriture est noté sur la région nourrie ; celui des autres biens sur le stock tenu dans la bande. La caisse du marché sort de la note. |
| travailleurs | ménage nourri, −2 s'il tombe malade, **et** s'il est allé travailler en étant contagieux : moins les nouvelles contaminations de son lieu de travail ce jour-là, partagées entre les contagieux présents. Le coût qu'il fait porter aux autres lui revient. |

**Porte, plus stricte** (deuxième tentative sur la même porte) : les mêmes exigences — battre la règle (médiane et
7 mondes sur 10) et le hasard (médiane), et l'aveugle pour le commerce — **sur l'examen 101-110 ET sur la
confirmation 201-210**. Un groupe qui passe l'une et pas l'autre est refusé.

## Verdicts de la tentative 2 — 23/09 (commit f3fb537, 491 s)

| groupe | examen 101-110 | confirmation 201-210 | verdict |
|---|---|---|---|
| travailleurs | −20,66 contre −22,61, **7/10**, pic 10,7 % contre 10,8 % | −20,73 contre −20,54, 4/10 | refusé |
| entreprises | −31,46 contre −22,61, 2/10 | −27,54 contre −20,54, 2/10 | refusé |
| marchés | −29,11 contre −22,61, 2/10 | −28,22 contre −20,54, 2/10 | refusé |
| commerce | −23,93 contre −22,61, 6/10 (aveugle −21,93) | −24,40 contre −20,54, 4/10 (aveugle −18,05) | refusé |
| voyageurs | −30,17 contre −45,94, 8/10 (hasard −25,82) | −25,77 contre −37,95, 9/10 (hasard −21,51) | refusé |

**La confirmation a servi** : les travailleurs passaient l'examen et échouent sur la seconde série.
**Les notes par effet du choix ont aidé** le commerce (−26,4 → −23,9) et les entreprises (−42,0 → −31,5), et leur
récompense monte enfin d'époque en époque (commerce 0,140 → 0,160 ; marchés 0,27 → 0,31) — sans suffire.

**Diagnostic** : ces agents partent de zéro contre des règles qui contiennent déjà la calibration de plusieurs jours.
Deux tentatives sur la même porte : on s'arrête là avec cette méthode. Proposition soumise à Younes : **former par
imitation** — l'élève apprend d'abord à reproduire la règle, puis ne s'en écarte que là où il fait mieux ; la porte
reste la même (dépasser son maître).
