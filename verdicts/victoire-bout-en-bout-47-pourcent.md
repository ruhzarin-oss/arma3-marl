# La mission gagne de bout en bout : 17 succès sur 36, et le goulot n'est pas l'assaut

*Verdict du 13/09/2026. Campagne VICTOIRE-BOUT-EN-BOUT-12-09. Tâche Plane HMT-46.*

## Ce qui est établi

Pour la première fois du projet, la mission CHACAL est jouée **jusqu'à l'exfiltration** et gagne.

- **17 succès sur 36 épisodes, soit 47 %** (intervalle de Wilson à 95 % : 32 % à 63 %).
- Critère : les trois charges posées **et** au moins six hommes sur dix ramenés au point de ramassage.
- Phase 6 atteinte dans les 36 épisodes. Deux graines, 7 et 8. Réglage : `socle=1`, `appui_feu=0`,
  `oracle=0`, palier 4, effectif 10, `depart=3`, `arret=6`.
- Deux épisodes supplémentaires en **départ complet** (`depart=1`, approche de 4,4 km jouée) :
  un succès sur la graine 8, un échec par charge manquante sur la graine 7. Coût : 12 383 s pour deux
  épisodes, soit 1 h 43 chacun.

## La prédiction était fausse sur les deux points

Elle était écrite dans le job avant le lancement : « taux entre 10 et 40 %, cause d'échec dominante
`CHARGES_INCOMPLETES` ».

- Le taux est **47 %**, au-dessus de la fourchette annoncée.
- La cause dominante est **`EXFIL_MANQUEE`, 12 échecs contre 7** pour les charges.

Le falsificateur inscrit dans le job se déclenche donc : *« si `EXFIL_MANQUEE` domine, le problème n'est
pas l'assaut mais le décrochage, et tout le travail sur l'assaut visait le mauvais organe. »*
**C'est le cas.** Trois jours de travail sur le placeur, l'appui et les tactiques portaient sur la phase
qui n'était pas le goulot.

## Pourquoi cela n'avait jamais été vu

Les 245 épisodes joués du 10 au 12 septembre portaient tous `arret=5`. La phase 6 n'était jamais jouée,
`CHACAL_EXFILTRES` restait à zéro, et le critère de succès exige six exfiltrés. **Le succès était
structurellement impossible**, et les 245 épisodes sont sortis en ECHEC par construction.

Règle qui en découle : *avant toute campagne, vérifier que l'issue visée est atteignable avec les leviers
du job.* C'est le contrôle positif appliqué à la mesure elle-même.

## Le goulot, chiffré

Les douze échecs d'exfiltration finissent **tous en PLAFOND**, jamais en DETRUIT.

| Fin de la phase 6 | Épisodes | Issue |
|---|---|---|
| ATTEINT | 18 | tous des succès |
| PLAFOND | 12 | tous des échecs d'exfiltration |

Les hommes sont vivants : un épisode finit à **9 vivants pour 3 exfiltrés**, un autre à 8 vivants pour 1.
Ce n'est pas un problème de pertes, c'est un problème de vitesse. Les survivants marchent encore quand
le chronomètre tombe.

La cause était écrite en commentaire dans la phase 6, avant que le problème ne survienne :

> « En COMBAT sur 1,4 à 2,4 km, 1,8 m/s de moyenne n'est pas garanti même sans ennemi : l'issue serait
> EXFIL_MANQUEE sur un détachement intact. »

L'assaut compromet toujours le détachement, donc `_compExf` vaut toujours `COMBAT`. Et la récolte du
moteur établit que l'itinéraire se calcule en fonction du comportement.

## Ce que ce verdict ne dit pas

- **Deux graines seulement.** Le 47 % vaut pour les sites des graines 7 et 8, pas pour la famille de sites.
- **Le départ complet n'a que deux épisodes.** On ne sait pas si jouer l'approche change le taux.
- **L'appui est coupé** dans toute la campagne. L'atelier MCP suggère qu'un appui à 300 m non cloué
  transforme l'assaut, mais cela n'a jamais été mesuré dans la mission.
- La cause de l'échec d'exfiltration n'est pas encore **séparée** : comportement ou budget.
  La campagne EXFIL-13-09 le tranche.

## Suite

Campagne EXFIL-13-09, trois bras : référence, AWARE après rupture de contact, budget à 1,2 m/s.
