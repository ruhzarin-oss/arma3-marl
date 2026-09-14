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

---

# AMENDEMENT DU 13/09/2026 : CE VERDICT EST FAUX SUR SON POINT CENTRAL

**Le goulot n'est pas l'exfiltration. C'est l'assaut.** Et le taux n'est pas 47 %, il est d'environ 74 %.

## Le défaut

La règle S3 du socle cloue l'appui — `disableAI "PATH"` plus `lambs_danger_disableAI`. La phase 6 ne
le libérait **que si** `CHACAL_APPUI_FIXE == 1`. Or toutes les campagnes tournaient avec `socle=1` et
`appui_fixe=0` : l'appui n'était **jamais** libéré.

Deux hommes sur dix ne pouvaient pas rejoindre le point de ramassage, alors que le critère en exige
six sur dix.

## La preuve, lue dans les traces

Les hommes 6 et 7 parcourent **zéro mètre** pendant la phase 6, dans 11 épisodes sur 12, pendant que
tous les autres marchent entre 1 000 et 2 400 m.

Et dans les échecs dits « d'exfiltration », **tous les survivants mobiles étaient arrivés** :
« 4 exfiltrés, 6 vivants » signifie 4 mobiles et 4 arrivés ; « 5 exfiltrés, 7 vivants » signifie
5 mobiles et 5 arrivés. Ce n'étaient pas des exfiltrations manquées.

## Le recomptage, hors ligne, sur 38 épisodes

| | |
|---|---|
| Taux **réel** mesuré | 18/38 — 47,4 % |
| Taux **projeté**, appui rendu à ses jambes | 28/38 — **73,7 %** |
| Écart | 10 épisodes, 26,3 points |

Échecs qui subsistent : **8 charges incomplètes contre 2 exfiltrations manquées.**

Le projeté est une **hypothèse**, pas une mesure : il suppose que l'appui serait arrivé comme les
autres. Ce qui la rend crédible est que, dans les épisodes lus, tous les survivants mobiles sont
arrivés. Le chiffre réel viendra d'une campagne rejouée avec le correctif.

## Ce que cela invalide

- La conclusion « le goulot est le décrochage » : **fausse**.
- La campagne d'exfiltration à trois bras du 13/09 : les trois bras ont été mesurés sur des hommes qui
  ne pouvaient pas marcher. Le 41 % identique de la référence et du budget s'explique ainsi, et le
  58 % d'AWARE est du bruit.

## Ce que cela apprend, et c'est la troisième fois

C'est la **troisième panne d'instrument lue comme un résultat** : `arret=5` rendait le succès
impossible, le seuil 3 de la phase 3 était hors d'atteinte, et l'appui n'avait pas de jambes.

Le point commun est écrit noir sur blanc : **aucune porte du lecteur ne vérifiait qu'un homme vivant
peut marcher.** Le défaut a traversé quinze portes vertes et trois campagnes.

Correctif : la phase 6 rend les jambes à tout le monde sans condition, et une garde compte les hommes
vivants sans `PATH` et l'écrit dans la ligne FINI sous `sans_jambes`.
