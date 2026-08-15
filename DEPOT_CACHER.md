# Dépôt — le couvert CACHE-t-il, ou protège-t-il seulement ? Critères AVANT

Déposé le 15/08/2026.

## Ce que le code du gymnase dit, et qui n'est pas une mesure

```python
los    = self._losc(self.hm, ...)                    # la ligne de vue ne lit QUE le relief
dmg_a += _p * los * tir * (1.0 - 0.7 * incover)      # le couvert n entre QUE dans les degats
```

**`cover` n'apparaît nulle part dans le calcul de la visibilité.** Au gymnase, être sur le
couvert retire 70 % des dégâts **sans rien cacher**. Sur Arma, aucun multiplicateur de ce
genre n'existe : la seule protection est de rompre la ligne de vue.

C'est une lecture de code. **Elle ne devient un fait mesuré que si l'agent le vit ainsi.**

## La grandeur, la même des deux côtés

**Rapport de masquage = P(exposé | SUR le couvert) ÷ P(exposé | hors couvert).**

- **= 1** → le couvert **ne cache pas** ;
- **< 1** → il cache, d'autant plus qu'il est bas.

« exposé » = `los > 0,5` (colonne 7). « sur le couvert » = `incover > 0,5` au gymnase,
`dcover == 0` sur Arma — définitions déjà arrêtées dans `AMENDEMENT_COUVERT.md`.

## LES PORTES SONT EXÉCUTÉES AVANT DE JUGER ⟨règle 18⟩

Quatre cas fabriqués, imprimés avant toute donnée réelle.

## Les lectures

| gymnase | Arma | lecture |
|---|---|---|
| ≈ 1 (0,85-1,15) | **< 0,7** | **LE DÉSACCORD EST ÉTABLI** : le gymnase enseigne un abri qui protège sans cacher, Arma n'offre qu'un abri qui cache. L'agent a appris une chose qui n'existe pas là-bas. |
| ≈ 1 | ≈ 1 | le couvert ne cache **nulle part**. Le désaccord se réduit au seul multiplicateur de dégâts. |
| < 0,7 | < 0,7 | il cache des deux côtés. **Cette piste se ferme.** |
| autre combinaison | **INDÉCIS**, on ne conclut pas. |

## CONTRÔLE POSITIF ⟨règle 16⟩

**Au moins 100 pas sur le couvert et 100 hors, dans chaque monde.** En dessous, la
conditionnelle est vide et rien ne se lit. *Je sais qu'Arma n'a rendu que 150 pas sur le
couvert en 20 épisodes : le seuil peut échouer, et je ne l'ajuste pas.*

## Ce qui n'est PAS promis

Si le désaccord est établi, ça ne dit pas comment le corriger. Deux voies existeraient —
donner à Arma un couvert qui protège, ou retirer au gymnase son multiplicateur — et **la
seconde change le monde d'entraînement**, donc invalide tout ce qui y a été mesuré.
Rien de cela n'est engagé ici.
