# DÉRIVATION DU CRITÈRE NEUF — CAS D'ARRÊT ATTEINT. Le critère n'est pas écrit.

**19/08/2026, 21 h 10.** Socle 4.0.0, canal `sv_vz_preserve_10hz`.
Spécification écrite et committée **avant** : `CRITERE_NEUF_DU_PLACEUR.md`, `a489262`.
Mesure : 60 lieux tirés à l'aveugle (graine 19, ±250 m autour de 4644/5652) × 8 azimuts,
en parallèle, plus le sabotage des jambes sur les mêmes 60, plus les 12 lieux connus.
n = 132 lieux, 1 056 gestes. Journal `serverVUEAZ.out`. FPS 48-50 avec 60 hommes.

## L'HISTOGRAMME DES MINIMA SUR 8 AZIMUTS

| minimum | lieux | |
|---|---|---|
| 0 m | 5 | |
| 1 m | 4 | |
| 2 m | 2 | **régime coincé — 19 lieux** |
| 3 m | 3 | |
| 4 m | 3 | |
| 5 m | 2 | |
| **6 m** | **0** | |
| 7 m | 2 | **creusement — 3 lieux** |
| **8 m** | **0** | |
| 9 m | 1 | |
| 10-19 m | 38 | **régime marchant** |

## LA RÈGLE ÉCHOUE SUR SA PROPRE PRÉCONDITION

La règle disait : *« le seuil est le milieu du creux séparant les deux modes »*, avec ce
cas d'arrêt : *« si le creux n'existe pas — distribution unimodale ou continue — la règle
échoue et le critère n'est pas écrit ce soir »*.

**Il n'y a pas de creux, il y a un creusement.** Le plus large intervalle vide fait
**un seul bac** (6 m), entre deux bacs à deux lieux. Mon programme l'a pris pour le creux :
il a appliqué la **lettre** de la règle, pas sa substance. Un bac vide n'est pas un
séparateur de modes.

> **⛔ LE CAS D'ARRÊT S'APPLIQUE. Le critère n'est pas écrit.**
> On ne pose pas un seuil dans un continuum : ce serait un chiffre rond de plus, et c'est
> exactement la faute qui a coûté la semaine.

## LES CONTRÔLES — 2 SUR 3, ET LE TROISIÈME ÉTAIT MAL POSÉ

| contrôle | résultat | |
|---|---|---|
| jambes coupées → 0 reçu | **0/60** | **PASSE franchement** |
| lieux dans l'eau → 0 reçu | 0/0 | vide — le tirage n'en a produit aucun |
| les 12 lieux connus → 12 reçus | **10/12** | **ÉCHOUE** |

**Le troisième contrôle était mal spécifié, et l'erreur est mienne.** Ces 12 lieux ont été
certifiés pour une marche **vers le nord seulement**. Rien ne garantissait qu'ils fussent
libres dans les **huit** directions. Exiger 12/12 supposait ce qu'il fallait démontrer.
Un contrôle positif doit reposer sur une propriété **établie**, pas héritée d'un critère
qu'on vient de retirer pour prémisse fausse.

⚠️ Cliquet : *un contrôle positif hérité d'un critère retiré n'est pas un contrôle — c'est
la prémisse fausse qui revient par la porte de service.*

## CE QUE LA MESURE APPREND QUAND MÊME

- **Un tiers du terrain (19/60) bloque un homme dans au moins une des huit directions.**
  Le mode d'échec que le placeur doit attraper est donc **fréquent**, pas marginal.
- Le régime marchant plafonne à **19,1 m** de minimum : cohérent avec le canal adopté
  (max 22,5 m mesuré dans la meilleure direction).
- Médiane des minima : **11,6 m**.
- Réception à un seuil hypothétique de 6 m : **41/60 (68 %)**.
- Le sabotage des jambes est refusé **60 fois sur 60** : l'instrument sait dire non.
- **60 hommes simultanés à 48-50 FPS** : la mesure parallèle est peu coûteuse, elle
  pourra servir de routine.

## CE QU'IL FAUT POUR ÉCRIRE LE CRITÈRE — À PRÉ-ENREGISTRER SÉPARÉMENT

Le **minimum sur 8 azimuts** est peut-être une statistique trop dure : un lieu libre dans
sept directions sur huit est refusé par elle. Deux pistes, à spécifier **avant** de mesurer
et sans regarder ces nombres-ci :

1. **Une statistique de comptage** : « au moins k azimuts sur 8 dépassent X » — k et X
   dérivés ensemble, sur un corpus de lieux dont la praticabilité est établie
   **autrement** que par l'ancien critère.
2. **Un contrôle positif construit, pas hérité** : des lieux dont on sait qu'ils sont
   libres parce qu'on les a **choisis plats et dégagés**, mesurés comme tels.

⚠️ Ce qui est **interdit** : choisir la statistique ou le seuil en regardant laquelle fait
passer les lieux qu'on aimerait voir passer. C'est du réglage sur les résultats.

## CONSÉQUENCE OPÉRATIONNELLE

Le bloc C reste **éteint**, et **aucune porte ne se lance**. L'état est inchangé depuis
ce soir 20 h : le placeur n'a pas de critère valide, et il n'en aura pas avant une
dérivation dont la précondition est satisfaite.
