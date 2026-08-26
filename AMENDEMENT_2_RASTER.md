# AMENDEMENT 2 — LECTURE ASYMÉTRIQUE DU 2×2, ET LE DÉFAUT CONNU DE Φ

**Déposé le 26/08/2026 à 02h20, PENDANT le run de la vague graine 0 (partie à 01h38),
AVANT que la moindre cellule ne rende un chiffre de jugement.** Vérifiable : aucune ligne
`== bras` n'existe dans `/mnt/data/dd_*.log` à cette heure.

## 1. LA SONDE ÉCRIVAIT DANS LE MONDE — vérifié inerte, documenté quand même

`danger_position()` fait `e.champ_R = 0.0` et ne restaure pas. `prix_des_actions()` fait
`e.champ_R = e.move`. Les deux sont appelées à chaque pas.

**Vérification (10 min) :** `champ_R` n'est lu qu'aux lignes 379-380 d'`assault_terrain.py`,
à l'intérieur de `_champ_danger`, et par `_obs()` **uniquement si `champ_risque=True`**.
Or `champ_risque` est **ABSENT de MONDE_ARMA** et vaut donc `False`. Mesuré :
`_obs()` est **strictement identique** quand on force `champ_R=0`. Chaque appelant règle la
valeur juste avant son propre calcul. **Le monde joué est bien le monde déposé.**

⚠️ **Le principe reste violé** : une sonde n'a pas le droit d'écrire dans ce qu'elle mesure.
Corrigé en instantané-restauration pour tout run ultérieur. Ici, l'innocuité est établie
par mesure, pas par raisonnement.

## 2. LE DÉFAUT CONNU DE Φ — Φ PAIE LA MORT

`Φ = −(danger × vivants).sum(1) / vivants.sum(1).clamp(min=1)`.

Un homme meurt presque toujours en zone dangereuse. Le retirer de la moyenne **fait monter
Φ**, donc le façonnage **verse une prime à l'instant de sa mort**. Et quand tous meurent, le
`clamp(min=1)` rend **Φ = 0, sa valeur MAXIMALE** : l'anéantissement solde la dette de danger
d'un coup.

**Et la récompense ne facture la mort NULLE PART ailleurs.** Le seul terme qui la price dans
tout le montage est celui-ci, et il la price **positivement**. Même classe que la revue du
17/08 : `clamp` + un terme qui rend la mort avantageuse.

**La forme correcte, pour tout run ultérieur** ⟨Fable⟩ : chaque homme mort compte **GELÉ à son
dernier danger de vivant**, somme divisée par l'**effectif total constant**. La mort déplace
alors Φ d'exactement zéro — elle n'est pricée que par le réel, la perte de capacité de prise.
Plus aucun clamp n'est nécessaire. C'est toujours une fonction d'état : la position de mort
EST de l'état.

## 3. LE TERMINAL — choix déposé, pas oubli

On **NE force PAS** `Φ(terminal) = 0`. Zéroter rouvrirait le trou : Φ vaut au mieux 0, donc
atteindre le terminal depuis un état dangereux verserait la prime — **mourir effacerait la
dette**. On cesse simplement d'ajouter du façonnage à la fin. Le résidu télescopé vaut
`γ^T·Φ(s_T)` : finir EN danger reste légèrement pénalisé.

C'est une entorse assumée à la pureté du théorème — l'optimum peut glisser vers « finir hors
de danger ». Elle est du bon côté, non pompable, et **le jugement est de toute façon rendu
SANS façonnage**, donc l'instrument de mesure n'est pas touché.

## 4. LE TÉMOIN DE MÉCANISME EST REMPLACÉ — l'ancien pouvait mentir

`danger_par_metre = Σ danger / mètres tenus` favorise structurellement **« avancer vite et
mourir »** : un agent qui sprinte et meurt au pas 10 accumule dix pas de danger, celui qui
survit soixante en accumule soixante, et par mètre tenu le sprinter-mort gagne. Le
`clamp(min=1)` du dénominateur masquait en plus le recul.

**Trois colonnes séparées, jamais un ratio :**
· danger payé par **HOMME-PAS VIVANT** ;
· **survivants** en fin d'épisode ;
· **mètres tenus signés**, sans clamp.
Critère de mécanisme : **le danger par homme-pas BAISSE ET les survivants NE BAISSENT PAS.**
Le ratio reste affiché, jamais en critère.

## 5. LE POIDS RESTE W = 0,352, CONSTANT

Que le façonnage pèse 3× le terme de progression tant que la politique se conduit comme
`frontal` est la **propriété**, pas le défaut : c'est dans ce régime que le prix est le plus
actionnable (le +20,4 scripté y a été récolté), et le déséquilibre **s'éteint tout seul**
puisque Φ rétrécit à mesure que la politique apprend à éviter. Le façonnage par potentiel
porte son propre recuit.
⛔ **Pas de W(t)** : un poids variable casse la forme potentielle, Φ cesserait d'être une
fonction d'état fixe.

## 6. ⭐ LA LECTURE ASYMÉTRIQUE — c'est l'objet de cet amendement

Le trou de la mort **ne peut pas FABRIQUER de la prise au jugement**, puisque le jugement est
rendu sans façonnage. Il ne peut que **corrompre l'apprentissage**. Donc :

· **SUCCÈS de `PF − P` ≥ +5,0 → DÉPOSABLE A FORTIORI.** Le façonnage aura gagné **malgré**
  un handicap connu et documenté. Sous réserve des trois témoins recalculés.
· **ÉCHEC → NON DIAGNOSTIQUE.** Le trou peut l'avoir causé. Il déclenche une relance avec le
  Φ **gelé**, dénominateur constant, zéro clamp — **avant toute conclusion**, et en
  particulier avant d'ouvrir la branche distillation.

⟨Fable⟩ *« Huit heures de machine ne valent pas un verdict ambigu ; un verdict positif malgré
un handicap connu, si. »*

## 7. UNE SONDE OUVERTE, À FAIRE — E2 réfute ma lecture

E2 (positions permutées) rend **61,7 %** contre 49,6 % pour A. Ma lecture — « le réseau
ignore la branche et redevient A » — est **incompatible** avec ce chiffre : un réseau qui
ignore une branche atterrit SUR A, pas douze points au-dessus.
Deux hypothèses debout : (a) les **attributs non spatiaux** des unités (effectifs, états),
intacts dans E2 et lisibles en statistique d'ensemble par l'attention, portent une information
absente des 12 nombres ; (b) les positions permutées agissent en **bruit régularisant**.
**Sonde qui tranche :** E **sans positions du tout**, attributs conservés. ~61 → ce sont les
attributs ; ~49 → c'était le bruit.
Note au registre : **E2 à 61,7 et la greffe à 61,6 atterrissent au même endroit** — deux
objets indépendants suggèrent un **plafond du gymnase vers 61-62 %** sous cette recette.
Une graine chacun : rien de tout cela ne se dépose sans réplication.
