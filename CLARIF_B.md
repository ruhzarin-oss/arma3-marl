# Clarification — ce que la question B mesure vraiment, écrite AVANT de la lire

Déposé le 15/08/2026, **pendant que le run des 67 tourne encore**. Sur avertissement de
Fable : *« la question B utilise quelle définition du couvert ? Si c'est la carte de pentes,
son verdict héritera de l'inversion. Sache-le avant de le lire. »*

## Vérifié

```
gymnase : cover = (slope > 1,4 × slope.mean())      # commentaire du code : « crêtes/pentes = abris »
Arma    : dcover == 0  ⟺  gradient > 1,4 × moyenne locale
```

**Les deux côtés désignent le même objet : une cellule PENTUE.**

## Ce que B mesure donc réellement

**B ne demande pas « le couvert protège-t-il sur Arma ».**
**B demande « la définition du couvert du gymnase transfère-t-elle sur Arma ».**

C'est une question légitime et utile — mais ce n'est pas celle que son nom suggère, et le
verdict doit être **nommé ainsi** quand il sortira.

## Ce que B ne pourra PAS dire

**Si Arma offre des positions protectrices.** Le couvert réel est relationnel et
directionnel — on est à couvert *de* quelque chose, *derrière* un masque. `slope > 1,4 ×
moyenne` localise les **générateurs** de masque, pas les positions masquées : la position
payante est un cran **derrière** la crête, côté ami.

Cette grandeur-là n'est pas mesurée, ni au gymnase ni sur Arma. Un B négatif ne dira donc
rien contre Arma — il dira que **le gymnase a mal typé le couvert**.

## Ce qui est déjà connu et qui rend B partiellement prévisible

Sur Arma, se tenir sur une cellule pentue **expose davantage** (rapport de masquage 1,37,
observation non tranchée). Un verdict B défavorable à Arma était donc partiellement écrit
d'avance.

**Je le déclare maintenant, avant lecture**, pour ne pas présenter comme une découverte ce
qui était déjà à moitié connu.

## Ce que B garde d'utile

B mesure la **mortalité**, pas l'exposition. Même si les crêtes exposent plus, la question
« réduisent-elles quand même les dégâts reçus ? » n'a pas de réponse connue sur Arma — et
elle chiffre la taille du désaccord, ce qui manque encore.

**Les critères, contrôles et bandes de `DEPOT_COUVERT.md`, `AMENDEMENT_COUVERT.md` et
`DEPOT_67_AVENANT.md` sont inchangés.** Cette note ne touche à rien : elle nomme.
