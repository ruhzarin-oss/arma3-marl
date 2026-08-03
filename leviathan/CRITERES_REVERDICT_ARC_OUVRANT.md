# CRITÈRES — RE-VERDICT DE L'ARC CORRIGÉ (le cône OUVRE, il ne pivote pas)

Figés dans la nuit du 27 au 28/07/2026, **avant** le run.

## Ce qui a changé dans le monde, et pourquoi

Mesuré sur Arma (`CRITERES_ARC_CONTACT.md`, empreinte 82f3dad52683dd8f) : un défenseur
attaqué hors de son cône **riposte à 100 %**, avec un retard de **3,5 à 4,1 s**, et
**sans jamais pivoter** (`t_direction` = jamais à moins de 25° en 75 s), **sans atténuation
d'ampleur** (impacts 180°/0° = 1,17).

`assault_terrain.py` a donc été corrigé : `arc_latence_s` fait **OUVRIR** le cône après le
sursis (`_ouvrir_arcs`, drapeau `d_ouvert`). Il ne le fait pas tourner. Défaut `None` =
ancien cône dur, non régressif — **vérifié** : sans latence, `d_ouvert` reste faux partout.

## ⚠ Contre quoi ce re-verdict se juge — et contre quoi il NE se juge PAS

**La référence Arma « ×2-3 à un tiers du coût » N'EST PLUS COMPARABLE.** Elle vient du banc
FIBUA dont la garnison de mission **n'existe plus** (mesuré : le serveur Stratis redémarre
avec zéro unité EAST), et le banc durci à 8 défenseurs n'est pas cette configuration.
Prétendre certifier contre ce chiffre serait se raconter une histoire.

Ce re-verdict se juge donc sur la **NON-RÉGRESSION DU VERDICT** : le monde corrigé
continue-t-il à dire que le crochet vaut mieux que le frontal ?

## Le paramètre est VERROUILLÉ

**τ = 4 s**, parce que c'est la mesure (médiane sur 90°-180° : 3,9 / 3,5 / 4,1 s).
**Un paramètre mesuré ne se retouche que par une meilleure mesure, jamais par un meilleur
ajustement.** Le balayage τ ∈ {2, 4, 6} est une **analyse de sensibilité** — trois lignes de
plus dans le tableau — et rien d'autre. Aucune de ces valeurs ne devient le réglage.

⚠ **Limite d'instrument, connue d'avance** : le pas de sandbox vaut 3,28 s, et
`arc_latence_pas = max(1, round(τ / 3,28))`. Donc **τ = 2 s et τ = 4 s donnent tous deux
1 pas** — ils seront **identiques par construction**, et τ = 6 s donne 2 pas. La
sensibilité n'a que **deux** points distincts, pas trois. Dit d'avance pour que personne ne
lise une « stabilité » là où il n'y a qu'une collision d'arrondi.

## Seuils, écrits avant

Doctrines **scriptées** des deux côtés : on teste le MONDE, pas la politique.
Banc figé : A = 4, D = 8 (`DURETE_FIGEE.md`, 0eeae9efcdd67572). Graines 7, 8, 9.

### 1. DIRECTION — le verdict survit-il à la correction ?
Dans le monde à cône ouvrant, τ = 4 s :
- **× prise (crochet ÷ frontal) ≥ 1,5** ET **× coût (crochet ÷ frontal) ≤ 0,7**
  → **le verdict tient**. On adopte le cône ouvrant.
- En dessous de l'un ou l'autre → **la correction casse le verdict**.
  → **on garde le cône dur par défaut et on instruit** : l'écart devient l'objet d'étude,
  pas un bouton à tourner. Le candidat désigné d'avance est la **suppression**
  (l'appui ne distrait pas, il RETIENT l'attention : tant qu'il tire, le sursis reste
  ouvert pour celui qui contourne).

### 2. TÉMOIN DE MÉCANISME — l'initiative, tirée des données Arma
La part d'engagements où **l'ATTAQUANT tire le premier**, c'est-à-dire où le défenseur n'a
pu ouvrir le feu **qu'après** l'expiration du sursis.

Mesuré sur Arma : **de face, le défenseur garde l'initiative (7/8 = 88 %)** ; **de flanc et
de dos, il la perd totalement (0/8 = 0 %)**.

Le monde corrigé doit reproduire le MÉCANISME, pas seulement le score :
- **frontal** : part « attaquant premier » **≤ 35 %**
- **crochet** : part « attaquant premier » **≥ 60 %**
Si le score tient mais que le témoin ne suit pas, **le monde donne le bon résultat pour une
mauvaise raison** — et c'est écrit avant de le voir.

### 3. CONTRE-ÉPREUVE
La ligne `cône DUR` (latence `None`) doit reproduire le banc figé : **frontal 19,3 %**,
**crochet 74,7 %**, à ±8 points. Sinon on ne conclut rien : l'environnement a bougé.

## Interdits
1. Retoucher τ pour faire passer un seuil.
2. Présenter une des lignes de sensibilité comme le réglage retenu.
3. Comparer le résultat au « ×2-3 » d'Arma, qui n'a plus de banc.
