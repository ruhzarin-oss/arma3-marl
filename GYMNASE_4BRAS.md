# Le classement du GYMNASE, quatre bras — moitié du banc de concordance

Mesuré le 15/08/2026. Critères déposés avant dans `DEPOT_CONCORDANCE.md` (`0236f1c`).
6 graines **held-out** × 256 environnements par bras.

## Le classement

| bras | prise |
|---|---|
| FRONTAL | **12,8 %** |
| FLANC | **34,3 %** |
| **SCRIPT** (feu-et-mouvement alterné, sans apprentissage) | **46,1 %** |
| POLITIQUE apprise | **51,1 %** |

## Les deux contrôles positifs

1. **Le gymnase sépare ses bras** : 38,3 points entre le meilleur et le pire (porte 10). ✓
2. **`SCRIPT` émet bien l'action 9** : 33,3 % des décisions, à partir du pas 5. ✓

## Aveu — septième critère troué, et il est arithmétique

Ma première version du contrôle 2 testait l'émission de l'action 9 **au pas 0**. Les hommes
naissent à **170 m** et l'appui exige **d < 0,9 × 110 = 99 m** : la condition est
**impossible au premier pas**, démontrable sans regarder une donnée. Le contrôle tombait
pour ma faute, pas pour celle du bras. Refait sur l'épisode entier, il passe.

Septième du jour, après l'arrondi du choix de site, le critère `dcover` insatisfiable, la
porte d'azimut, la bande de gel, les bandes de masquage non partitionnantes et le seuil
décimal contre une grandeur quantifiée.

## Ce que ce classement dit déjà, avant même la concordance

**Le feu-et-mouvement scripté fait 46,1 % contre 51,1 % à la politique apprise.** Trente
lignes sans apprentissage capturent **neuf dixièmes** de ce que la politique obtient.

Fable : *« si le script saute déjà vers 35 %, l'apprentissage n'est que le dernier tiers du
chemin. »* Au gymnase, il vaut **5 points sur 51**. Le **vocabulaire** porte presque tout ;
l'optimisation ajoute la finition.

⚠️ C'est vrai **au gymnase**. Rien ne dit que le partage soit le même sur Arma — c'est
précisément ce que la chaîne mesure.

## Ce qui manque

`FLANC` et `SCRIPT` côté Arma. Le classement inter-mondes se lira quand ils seront là,
sous la porte déposée : **zéro inversion de signe**, tolérance d'amplitude ×3.
Le bras NATIF reste **hors concordance** — l'IA d'Arma n'existe pas au gymnase — et sert
seulement d'étalon absolu.
