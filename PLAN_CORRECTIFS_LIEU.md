# PLAN DE CORRECTIFS — après le verdict du lieu

17/08/2026. Liste établie par Fable sur le verdict `0cbf82e`. **Rien n'est encore appliqué.**

## À RÉPARER, dans cet ordre

### 1 · Placeur v2 — jugé à l'ACTE
Traverse **réelle** de 24 m **et** acquisition **réelle** à 40 m, **contrôle positif pour
chacun** ⟨règle 16⟩.

> ⚠️ **Candidats en ordre ALÉATOIRE, premier REÇU — jamais « le meilleur ».**
> L'ancien placeur était un sélecteur-du-meilleur-par-le-mauvais-critère. Un placeur qui
> **optimise** fabrique un monde biaisé vers le facile. Le pré-filtre bon marché (densité
> d'objets, éventail de visibilité) est permis pour **ORDONNER**, jamais pour **RECEVOIR** :
> `path:true` figurait dans toutes mes signatures d'échec pendant que l'homme restait cloué.
> **L'état du moteur a menti toute la semaine ; seul l'acte reçoit.**

### 2 · Règle 18 sur le placeur v2
Les cinq lieux comme cas passants et échouants — **smoke test, pas certification** (§ 5).

### 3 · Porte pleine-chemin rejouée, LIEU NEUF PAR TIRAGE
Le levier `HMT_LIEU_FORCE` le permet. Les serveurs enchaînés redeviennent légitimes
**parce que** la variable cachée était le lieu ; garder un petit bras serveurs-neufs pour
borner le résidu serveur. **Cette porte EST la certification du placeur** — les deux objets
fusionnent, ~1 h.

### 4 · Re-mesure du résidu aux lieux REÇUS
Condition de sortie de panne. Voir § statut.

### 5 · Le tirage sacrificiel RESTE
Le transitoire de rang 1 **n'est pas expliqué par le lieu** : le lieu était constant dans ses
sessions, et le rang 1 y rougissait quand même. **Dossier ouvert.**

### 6 · Le procès s'étend à TOUS les placeurs
Scène d'épisode, banc des jambes (±60 m), placement d'objectif. **Lecture d'abord** — énumérer
et lire coûte zéro serveur — acte ensuite si suspect.

### 7 · Rejouer le choix de primitive DANS DES LIEUX ENCOMBRÉS
« On ne change pas la primitive » a été mesuré **en un lieu, vraisemblablement dégagé** — là
où `doMove` et `setVelocity` se ressemblent le plus. **C'est dans l'encombrement que `doMove`
contourne et que `setVelocity` pousse dans le mur.** Le choix a été fait là où il comptait le
moins.

## À JOURNALISER, sans réparer

- **Le lieu dans l'empreinte de CHAQUE mesure** — prévol, épisode, banc : position + scores
  traverse/vue.
- **Les lieux rejetés avec leur cause** — c'est un **atlas d'encombrement gratuit** qui
  capitalise.
- La télémétrie du pont 1.2 **à vie** : bonne instrumentation même hors cause.
- Le taux de rejet du placeur, sous alarme économique.
- La clôture des huit hypothèses au registre — le pont fermé « **SUPPLANTÉ** », pas « réfuté ».

## LE COÛT EST FAUX : personne ne paie 96 secondes

Mes 96 s supposaient un balayage **exhaustif**. On ne note pas 24 candidats, **on en reçoit
un**. Ordre aléatoire, arrêt au premier qui passe : à ~1 lieu praticable sur 3, l'espérance
est de **~3 candidats**, soit ~12 s de traverse ; la vue est quasi gratuite en géométrie
moteur. Avec pré-filtre d'ordonnancement, l'espérance tombe vers 1-2.

**Coût net : 20 à 40 s par prévol, payé une fois par session.**

## STATUT DU BANC — changement OUI, sortie de panne NON

**Le changement de statut est acquis, et la distinction mérite d'être écrite** : un rejet
**AVANT** mesure, sur critère nommé, contrôlé et journalisé, n'est pas un tri — c'est une
**DÉFINITION DE DOMAINE**. Le banc ne mesurera plus « le combat » mais « le combat dans les
mondes praticables au sens du placeur v2 », et chaque verdict porte ce qualificatif.

> **Le rebut sélectionne sur une variable inconnue ; le domaine déclare sa frontière.**

**Mais la panne reste**, pour une raison que mon verdict ne couvre pas : **les 3 échecs sur
12 aux lieux vivants**, aux rangs 3, 5 et 6 — donc **pas** le transitoire de rang 1. Cause
non nommée, taux ~25 %, plafond dérivé 6 % ⟨règle 19⟩. Deux lectures : soit un phénomène
propre, soit « vivant » est **gradué** — un lieu à 25 % d'échec est **marginal**, et le
placeur v2 doit peut-être le rejeter aussi.

## LES SURSIS — aucun ne se lève, un seul change de nom

| acquis | statut |
|---|---|
| **12,2 m** et **62 %** | sursis « n=1 session » → « **n=1 LIEU** ». Le banc des jambes n'emploie pas ce placeur, mais il tire ses positions **dans le même monde**, celui où deux tiers des points bloquent un homme. Levée bon marché : rejouer sur 5-10 lieux reçus et rendre le 62 % **comme une distribution avec son écart**. |
| **44,8 %** | reste à terre, + condition : rejoué sous prévol réparé, lieux journalisés. *« Ses mondes d'origine étaient des tickets de loterie non enregistrés. »* |
| `cible_unique`, l'avantage du flanc, la liste du `clamp` | **intouchés** — autres défauts, autres sursis. |
| la **rétractation** de `setVelocity` | **tient toujours** : une réfutation existentielle survit à tout. |

**Et ce qui se ferme** : le mystère du destin de session. Le `X² = 49,8` reste vrai **comme
mesure** ; son **interprétation** est ré-attribuée — l'unité était le **LIEU**, confondu avec
la session **par construction**, parce que né une fois.

## CINQ LIEUX NE CERTIFIENT PAS — c'est le jeu d'entraînement

Trois raisons : ils ont été **choisis par le diagnostic** (tester sur l'échantillon de
découverte) ; la règle 18 y est satisfaite comme **smoke**, nécessaire et non suffisant ; et
surtout — **les étiquettes elles-mêmes sont suspectes**. « Vivant » signifie seulement « pas
100 % mort » ; un lieu à 33 % d'échec **n'est pas un bon lieu, c'est un lieu marginal**. Le
seuil de réception se dérive du **plafond de résidu**, pas du découpage binaire du diagnostic.

**La certification** : lieux **frais**, tirés de la distribution que le placeur affrontera,
**~50 réceptions vérifiées par l'acte complet, zéro faux-reçu** pour borner à 6 %. Le
faux-rejet, lui, ne coûte que de l'argent — mesuré, plafond économique.

**Les cinq lieux deviennent le test de régression permanent**, joué à chaque version du
socle, en secondes.
