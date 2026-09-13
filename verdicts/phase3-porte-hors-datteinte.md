# La phase 3 est une porte que personne ne peut franchir

*Verdict du 13/09/2026. Lecture hors ligne de 111 épisodes déjà enregistrés, zéro seconde d'Arma.*

## Ce qui est mesuré

| | |
|---|---|
| Épisodes où la phase 3 OBSERVATION a été jouée | 111 |
| Fins en `RENSEIGNEMENT_PAUVRE` | **110 sur 111** (le 111ᵉ sort en COMPROMIS) |
| Vues obtenues — médiane | **0** |
| Distribution | 0 vue : 63 épisodes · 1 vue : 34 · 2 vues : 13 · **3 ou plus : jamais** |
| Seuil `CHACAL_SEUIL_RENS` | **3** |
| Renseignements restitués à l'assaut | **0**, dans les 55 épisodes qui le journalisent |

## Le verdict

**Le maximum jamais atteint est 2. Le seuil est 3.** Sur 111 épisodes, la porte n'a pas été franchie
une seule fois, et elle ne peut pas l'être : ce n'est pas un réglage trop serré, c'est un seuil hors
d'atteinte.

C'est **le même défaut que celui des 245 épisodes en `arret=5`** : un critère qu'aucune configuration
ne peut satisfaire, et dont l'échec est lu comme un résultat au lieu d'être lu comme une panne
d'instrument.

## La cause, cohérente avec le reste

L'observation se fait depuis l'observatoire `CHACAL_OP`, à environ 773 m du site, **de nuit**, contre
des défenseurs **en garnison à l'intérieur des bâtiments**.

Trois mesures rendent le résultat prévisible :
- la récolte du moteur donne, pour un défenseur en garnison de nuit, une détection à **36 m en médiane**
  et presque jamais au-delà de 250 m — la réciproque vaut pour l'observateur ;
- le site offre 29 postes intérieurs et **zéro poste sur l'enceinte** : les hommes à voir sont derrière
  des murs ;
- 79 postes sur 80 mesurés le 12/09 ne voyaient aucun défenseur.

## Et cela ne change rien à l'issue

La mission gagne **34 fois sur 99** épisodes jugeables malgré `RENSEIGNEMENT_PAUVRE` systématique.
Il n'existe aucun groupe de comparaison — aucun épisode n'a jamais eu de bon renseignement — donc on
ne peut pas dire ce qu'un bon renseignement apporterait.

Mais on a déjà la réponse par un autre chemin : le verdict `oracle-savoir-a-l-assaut.md` a mesuré
l'effet de **donner** la position des défenseurs, et il est négatif (8/18 contre 4/12). Savoir où ils
sont ne fait pas gagner.

**La phase 3 ne mesure donc rien, et ce qu'elle produirait ne servirait à rien.**

## Ce qu'il faut en faire

Trois options, par ordre de préférence :

1. **Assumer.** Déclarer la phase 3 décorative, abaisser son seuil à 1 pour qu'elle puisse au moins
   réussir, et cesser de compter ses échecs comme un résultat.
2. **La rendre jouable.** Rapprocher l'observation, ou lui donner un moyen — jumelles thermiques,
   drone, poste à 250 m. Mais l'oracle dit que le gain attendu est nul.
3. **La retirer du corpus.** Si elle ne discrimine rien, elle ne mérite pas une demi-heure d'épisode.

La phase 3 a coûté environ trente minutes par épisode sur 111 épisodes, soit près de **55 heures de
calcul** pour produire zéro information.

## Ce que ce verdict ne dit pas

- Le seuil de 3 n'a pas été relu dans le code : il est lu **dans le journal**, où il apparaît à 3 dans
  tous les épisodes qui l'écrivent. Sa justification d'origine n'a pas été retrouvée.
- La lecture porte sur les runs de septembre présents sur le disque. Des épisodes plus anciens
  pourraient avoir franchi la porte.
