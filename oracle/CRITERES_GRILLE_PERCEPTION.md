# Critères pré-enregistrés — la grille de perception du 19/09

*Écrits avant le premier épisode. La question : les deux canaux ajoutés ce matin (`moteur_entendu`,
`menace_mobile_vue`) permettent-ils au détachement de savoir **à quoi il a affaire** au moment de choisir ?
Sans cela, le verdict 843118c — contre une patrouille on traverse, contre un poste on attend — reste vrai mais
injouable.*

## Le dispositif

| bras | `menace_p2` | épisodes | rôle |
|---|---|---|---|
| PATROUILLE motorisée seule | 4 | 32 | le canal doit s'allumer |
| POSTE de contrôle seul | 5 | 32 | le canal doit rester muet |
| **AUCUNE menace** | 0 | 8 | **contrôle négatif** : sans lui, « zéro faux positif » n'est pas testé |

8 mondes (4, 5, 6, 7, 8, 9, 11, 12) × 4 graines de situation pour les deux premiers bras, × 1 pour le contrôle.
Option de traversée fixée à 1 : la perception est écrite **avant** le choix, la faire varier doublerait la facture
sans rien changer. Observation à 260 m, balayage réparé, de nuit, palier 4, vignette `d2a2`. Oracle commandant à 0.
Sonde de décision active : une ligne toutes les 10 s pendant 600 s.

## Ce qui est lu, et le critère écrit d'avance

**Un canal est RETENU s'il distingue dans au moins 50 % des épisodes, avec zéro faux positif.**
- sensibilité : part des épisodes du bras PATROUILLE où le canal s'allume ;
- spécificité : part des épisodes des bras POSTE **et** AUCUNE où il reste muet — elle doit valoir **100 %** ;
- **pouvoir de trancher** : part des épisodes où au moins un des deux canaux distingue. C'est le chiffre qui décide
  si la règle est apprenable.

En dessous de 50 % de sensibilité, la règle serait jouable trop rarement pour qu'un agent l'apprenne : on le dira,
et on cherchera un troisième canal plutôt que de lancer une campagne.

## Les questions suivantes, testées maintenant

Chaque champ est journalisé pour qu'une question future ne coûte pas une nouvelle grille.

| question | champ qui y répond |
|---|---|
| pourquoi 600 m, et que donnerait 300 ou 900 ? | `distance_moteur` |
| le son traverse-t-il le relief ? | `vue_vehicule` |
| pourquoi le canal rate-t-il ? distance, ou moteur éteint ? | `moteur_allume` |
| pourquoi `menace_mobile_vue` vaut-elle −1 si souvent ? | `n_vues_menace` |
| et si la fenêtre durait 60 s, ou 180, ou 600 ? | la sonde toutes les 10 s |
| le canal s'allume-t-il quand il n'y a aucune menace ? | le bras AUCUNE |

## Falsificateur

« Si `moteur_entendu` s'allume ne serait-ce qu'une fois dans le bras POSTE ou dans le bras AUCUNE, le canal n'est pas
spécifique et il est retiré — quel que soit son taux dans le bras PATROUILLE. »

## Réserve dite d'avance

Ce dispositif ne distingue pas « c'est une patrouille » de « il y a un véhicule ». Un poste **avec un véhicule à
l'arrêt** serait le test suivant, et il n'est pas joué ici. Tant qu'il ne l'est pas, le canal se lit comme
« un véhicule motorisé est en mouvement quelque part », ce qui suffit à la règle du verdict 843118c mais ne doit pas
être présenté comme une reconnaissance de type.
