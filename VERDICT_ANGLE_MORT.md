# L'angle mort décide de la survie

## Verdict de simulation certifié sur trois dispositifs indépendants

*Arma 3 · 3 août 2026 · Younes Bouhassoun*

---

## 1. Le verdict

**Dans un affrontement d'infanterie simulé, l'orientation du regard adverse décide de la
détection — pas la distance, pas la posture, pas le mouvement.**

Approcher une position défendue à l'intérieur du cône de vision de ses occupants conduit à
une détection systématique, à environ 105 mètres. Approcher par le flanc ou l'arrière ne
conduit à aucune détection, sur toute la portée testée.

Cette bascule est **binaire**, et elle se traduit directement en survie : un soldat vu par
ses adversaires meurt **1,75 fois plus** qu'un soldat qui ne l'est pas, et l'écart **grandit**
avec la distance.

Conséquence opérationnelle : une attaque menée sur deux axes bat une attaque frontale de
**12,3 points de taux de succès**, à effectif total égal.

---

## 2. Les trois dispositifs

Le même fait a été établi par trois voies qui ne partagent ni le monde, ni la méthode, ni
l'instrument de mesure.

### 2.1 — Expérience contrôlée sur générateur d'engagements

| | |
|---|---|
| dispositif | générateur d'engagements v11, garnison en bâtiments, IA LAMBS des deux côtés |
| protocole | assaut à deux axes contre assaut frontal, **effectif total égal** |
| mesure | tenue exclusive de l'objectif pendant 60 s continues |
| volume | **1 324 engagements** sur dix mondes parallèles |

| bras | prises | engagements | taux | intervalle 95 % |
|---|---|---|---|---|
| **deux axes** | 274 | 699 | **39,2 %** | 35,6 – 42,9 |
| un seul axe | 168 | 625 | 26,9 % | 23,6 – 30,5 |

**Écart : +12,3 points. z = 4,75, p < 0,0001.**

Élément de robustesse : l'écart s'est **creusé** à mesure que l'échantillon grandissait
(+8,3 points à 429 engagements, +12,3 à 1 324). Un effet dû au hasard se dilue ; celui-ci
s'est renforcé.

### 2.2 — Corpus observationnel

| | |
|---|---|
| dispositif | mod *Pinned Down: Battle Lines*, front autonome à deux camps, sans intervention |
| durée | 8 heures continues, 173 338 relevés, **tous complets** |
| mesure | part des adversaires ayant le sujet dans leur champ de vision, puis mortalité à 30 s |
| volume | **563 018 observations** |

| part d'adversaires ayant le sujet dans leur champ | mortalité à 30 s |
|---|---|
| 0 – 20 % | **7,44 %** |
| 40 – 60 % | 10,75 % |
| 80 – 100 % | **13,00 %** |

**+75 %** de mortalité (seuil de significativité fixé avant mesure : +30 %).

**L'effet croît avec la distance** : +45 % à 80 m, +73 % à 150 m, **+84 % à 300 m**. De près,
un homme est vu quelle que soit l'orientation ; de loin, l'orientation décide seule.

**Asymétrie mesurée** — voir l'ennemi ne protège pas autant qu'être vu expose : avoir
l'adversaire dans son propre champ n'augmente la mortalité que de 38 %, contre 75 % pour
l'inverse. C'est cette asymétrie qui rend le contournement payant.

### 2.3 — Banc de certification en conditions contrôlées

| | |
|---|---|
| dispositif | six défenseurs alignés, cap **verrouillé et vérifié à chaque relevé** |
| protocole | approchant désarmé et invulnérable, 4 m/s depuis 300 m, azimut et posture imposés |
| conditions | 5 azimuts × 3 postures × 3 répétitions, **ordre brassé** |
| volume | **44 essais** |

| azimut d'approche | détections | distance |
|---|---|---|
| 0° — face | **9 / 9** | 105 m |
| 45° | **9 / 9** | 105 m |
| 90° — flanc | **0 / 8** | jamais |
| 135° | **0 / 9** | jamais |
| 180° — dos | **0 / 9** | jamais |

**Dix-huit détections sur dix-huit dans le cône. Zéro sur vingt-six en dehors. Aucune
exception dans les deux sens.**

---

## 3. Ce que la posture ajoute — et où elle s'arrête

Second banc, 52 essais, approchant **posé à distance fixe** derrière un couvert donné.

| couvert | posture | 60 m | 100 m | 150 m |
|---|---|---|---|---|
| terrain nu | debout / accroupi | 4,00 | 4,00 | 4,00 |
| **terrain nu** | **couché** | 4,00 | 4,00 | **0,00** |
| obstacle 1 m | couché | 4,00 | 2,71 | 2,00 |
| mur 1,8 m | debout | 2,00 | **0,00** | **0,00** |
| mur 1,8 m | couché | **0,00** | **0,00** | **0,00** |

*(valeurs : connaissance acquise par le camp adverse, 0 = jamais repéré, 4 = maximum)*

**Se coucher ne sert à rien en deçà de 100 m, et rend invisible au-delà de 130 m.** Le seuil
se situe autour de 120 mètres. L'accroupissement n'a aucun effet en terrain découvert.

Un mur d'1,80 m masque intégralement dès 100 m, quelle que soit la posture. Un obstacle d'un
mètre ne sert que si la posture suit.

---

## 4. Ce que tirer révèle — et ce que ça ne révèle pas

Troisième banc, 25 essais. Tireur placé à distance et azimut imposés, empêché d'ouvrir le feu
de lui-même, puis contraint à tirer un nombre de coups **compté et vérifié**. Fenêtre
d'observation de 60 secondes avant et après.

| position | distance | coups tirés | connaissance avant | après |
|---|---|---|---|---|
| dans le dos | 100 m | 0 | 0,00 | **0,00** |
| dans le dos | 100 m | 5 | 0,00 | **1,50** |
| dans le dos | 100 m | 20 | 0,00 | **1,50** |
| dans le dos | 200 m | 0 | 0,00 | **0,00** |
| dans le dos | 200 m | 5 | 0,00 | **1,50** |
| dans le dos | 200 m | 20 | 0,00 | **1,50** |
| dans le cône | 100 m | 0 | 3,76 | 3,76 |
| dans le cône | 100 m | 20 | 4,00 | 4,00 |

**Trois faits :**

**Tirer révèle, mais plafonne.** Un tireur dans l'angle mort passe de 0,00 à **1,50** — jamais
à 4,00. L'adversaire apprend qu'un tireur existe sans le localiser précisément.

**Cinq coups suffisent, vingt n'ajoutent rien.** Le saut se produit dès la première rafale.
Au-delà, tirer davantage ne coûte plus rien.

**La distance ne change rien.** Valeur identique à 100 et 200 mètres.

**Conséquence tactique.** Le contournement n'achète pas seulement une approche : il achète une
**position de combat durable**. Un homme dans l'angle mort peut engager et rester à 1,50, très
en deçà des 4,00 que subit quiconque approche de face.

L'asymétrie est frappante : **approcher de face coûte 3,76 sans tirer un seul coup ; tirer
vingt fois depuis le dos coûte 1,50. Se montrer coûte plus cher que faire feu.**

---

## 5. Ce qu'un adversaire retient — et pour combien de temps

Quatrième banc. Un homme est d'abord amené à être pleinement connu du camp adverse, puis
retiré de sa vue sans être supprimé. La connaissance est relevée toutes les dix secondes
pendant cinq minutes.

| condition | 30 s | 150 s | 300 s |
|---|---|---|---|
| **retiré de la vue** (passé dans le dos) | **4,00** | **4,00** | **4,00** |
| reste visible *(contrôle)* | 4,00 | 4,00 | 4,00 |
| jamais vu *(contrôle nul)* | **0,00** | **0,00** | **0,00** |

**La connaissance ne décroît pas.** Cinq minutes hors de vue, aucune perte.

Les deux contrôles écartent les explications concurrentes : celui qui reste visible ne décroît
pas non plus — il ne s'agit donc pas d'un oubli automatique qu'on aurait pris pour un effet.
Et celui qui n'a jamais été vu reste à zéro sur toute la durée — rien d'autre ne renseigne
les défenseurs.

**Conséquence : l'angle mort est un capital qui se dépense une seule fois.** Un homme repéré
reste connu pour toute la durée de l'engagement, où qu'il se déplace. Se replier, contourner
à nouveau, attendre : rien ne restaure l'avantage. **Le contournement doit réussir du premier
coup ; l'erreur n'est pas rattrapable.**

---

## 6. La hiérarchie des coûts

Les quatre bancs se recoupent en une échelle unique :

| action | ce qu'elle coûte |
|---|---|
| **se montrer une seule fois** | **4,00 — et c'est définitif** |
| tirer vingt fois depuis l'angle mort | 1,50, plafonné, réversible |
| rester dans l'angle mort | 0,00 |

**Se montrer coûte plus cher que faire feu, et ce coût est irréversible.**

C'est le résumé opérationnel du verdict : ce qui se paie, ce n'est pas l'agressivité, c'est
l'exposition. Un tireur discret peut engager longtemps ; un homme vu une seconde a perdu son
avantage pour la durée du combat.

---

## 7. Méthode — ce qui rend ces chiffres opposables

Chaque mesure a été conduite selon le même protocole, formalisé avant toute collecte.

**Critères d'échec écrits et figés avant de regarder les données.** Chaque banc dispose d'un
document de critères horodaté, avec les seuils numériques au-delà desquels la mesure est
déclarée non concluante. Aucun seuil n'a été modifié après lecture.

**Contrôle de présence.** Avant chaque campagne, une condition dont la réponse est connue est
mesurée. Un homme debout à 30 m dans l'axe *doit* être détecté. Sans cette vérification, un
résultat « aucune détection » serait indiscernable d'un instrument mort.

**Contrôle nul.** Un angle tiré au hasard sur les mêmes paires ne doit rien prédire. Résultat
obtenu : **−1 %**. Le dispositif ne fabrique pas de signal.

**Contrôle de confusion.** L'effet mesuré doit résister au contrôle des variables corrélées.
Ici : l'effet d'orientation tient à distance comparable, et la variable inverse (voir plutôt
qu'être vu) se comporte différemment (+38 % contre +75 %).

**Empreinte du monde.** Chaque corpus porte l'empreinte cryptographique du journal et la liste
des extensions chargées. Deux mesures ne sont comparables que si leurs mondes le sont.

---

## 8. Les mesures qui ont échoué

Ces échecs font partie du dossier. Ils délimitent ce que les chiffres ci-dessus valent.

**Un cap supposé au lieu d'être mesuré a inversé une conclusion entière.** Le premier banc
plaçait les défenseurs face au nord, puis les passait en posture de combat — mode dans lequel
l'intelligence artificielle du jeu fait balayer le regard. Le cap réel n'était donc plus celui
qui était supposé. Résultat obtenu : approche frontale jamais détectée, approche par l'arrière
détectée à 70 m — l'inverse exact du résultat correct. Correction : cap verrouillé par
processus dédié et **journalisé à chaque relevé**. Douze essais écartés.

**Un dispositif mobile ne peut pas voir un effet situé au-delà de sa distance de détection.**
Le premier banc mesurait la première détection lors d'une approche. Elle survient à 105 m,
c'est-à-dire *avant* la zone où la posture agit. Conclusion initiale : « la posture ne compte
pas, 9 mètres de gain ». Conclusion corrigée après changement de dispositif : elle rend
invisible au-delà de 130 m. Le protocole conditionnait le résultat.

**Une estimation intermédiaire s'est révélée fausse par vérification incomplète.** L'analyse
des décès sans auteur identifié avait conclu que 76 % étaient récupérables par recoupement
avec les impacts. Elle vérifiait la *présence* d'un impact, non l'*identité* du tireur. Après
mesure : 85 % des impacts n'identifient pas non plus leur auteur. Gain réel : 1 %.

**Une variable supposée contrôlée ne l'était pas, et un compteur l'a révélé.** Le premier banc
de tir imposait un nombre de coups à un tireur censé n'ouvrir le feu que sur ordre. Un compteur
de coups réels, ajouté par précaution, a montré qu'il tirait **21 fois dans la condition « zéro
coup »**. La comparaison entre conditions ne valait rien. Correction : ordre de tenir le feu,
coupure des automatismes de tir, et boucle qui vérifie le compteur au lieu de supposer qu'un
ordre a été exécuté. Sans ce compteur, la conclusion « tirer révèle systématiquement » aurait
été publiée.

**Une modification non remesurée a rendu un banc aveugle.** Le banc de persistance a d'abord
été monté avec une variante de configuration des défenseurs — une commande de coupure d'IA
remplacée par une autre, sans revérification. Résultat : plus aucune détection, trois essais
perdus, et la mesure aurait été déclarée impossible. Correction : retour exact à la
configuration dont le contrôle de présence donnait 4,00, et **contrôle de présence exécuté
avant le plan** plutôt qu'après. La règle qui en découle : ne jamais modifier un dispositif
qui fonctionne sans remesurer son contrôle.

**Un agent d'apprentissage a exploité une faille du simulateur avant d'être détecté par un
critère, non par l'observation.** Un agent atteignait son objectif à 98,9 % avec une exposition
divisée par quatorze — **en deux pas pour 250 mètres**. Une normalisation de vecteur manquante
lui permettait de se téléporter. Détecté par le critère de temps de mission, imposé avant le
run. Un détecteur de déplacement aberrant a depuis été ajouté au dispositif.

---

## 9. Domaine de validité

Ce qui est établi l'est **dans ce périmètre, et pas au-delà** :

- **Moteur** : Arma 3, serveur dédié Linux, extensions CBA · RHS · LAMBS Danger · Pinned Down
- **Terrain** : île de Stratis, zones de faible dénivelé (moins de 12 m sur 300 m)
- **Infanterie** à pied uniquement — aucun véhicule, aucun appui indirect
- **Couverts** : béton uniquement. **La végétation n'a pas été testée.**
- **Portées** : 25 à 300 mètres
- **Conditions** : jour, sans brouillard

**Non mesuré à ce stade, et identifié comme tel :**

| question ouverte | ce qu'elle déciderait |
|---|---|
| la largeur exacte du cône | bascule localisée entre 45° et 90°, non affinée |
| la végétation | seul le béton a été testé comme couvert |
| la persistance au-delà de 5 min | aucune décroissance observée sur la fenêtre testée ; le comportement à l'heure reste inconnu |

---

## 10. Ce que ce verdict permet

Trois usages immédiats, indépendants de tout modèle appris :

**Évaluer une doctrine.** Un plan d'approche peut être noté avant exécution, à partir des
orientations adverses connues.

**Calibrer un simulateur.** Les valeurs mesurées ici — bascule de cône, seuil de posture à
120 m, croissance de l'effet avec la distance — sont directement transposables dans un
modèle de détection.

**Certifier un agent autonome.** Le dispositif de banc est réutilisable tel quel : il dit si
un agent exploite réellement l'angle mort ou s'il en donne l'apparence.

---

*Ce document est un verdict de simulation. Il porte sur un moteur de jeu et ne prétend à
aucune validité opérationnelle réelle. Sa valeur tient à la méthode : critères écrits avant
mesure, contrôles négatifs, échecs documentés, domaine de validité borné.*
