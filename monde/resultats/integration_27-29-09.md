# Intégration du 27 au 29/09/2026 : un seul tronc, et la famine découverte

Chef de projet : session « Organisation du projet ». Tronc : `pays-sur-colonnes` (`/mnt/data/hmt/depot-colonnes`).
Le détail de chaque point est dans Plane, module « Pays simulé — une seule direction » (HMT-89 à HMT-142).

## 1. Les certifications du tronc

Chaque certification = `portes.sh` complet, avec 0 porte refusée, sur l'arbre fusionné. Depuis le 28/09, les portes de la guerre sont dans `portes.sh`.

| Commit | Date | Ce qui entre | Références |
|---|---|---|---|
| `1cfd00c` | 27/09 | fusion des 27 domaines, organisation | refaites |
| `12d226b` | 27/09 | prix de d03, autoconsommation, armée du budget, règle 8 (Qwen) | refaites |
| `5077c0a` | 27/09 | population grecque (Classes), `portes.sh` à fichiers privés, tests fragiles | inchangées |
| `7b0be18` | 28/09 | porte unique des devises, priorité des devises, famine au bulletin (guerre) | inchangées |
| `82ffbee` | 28/09 | `ORGANISATION.md` (documentation seulement) | — |
| `f3cfec7` | 28/09 | faim des morts (HMT-136), code à la demande de Qwen, reprise des devises | inchangées |
| `24ac15d` | 28/09 | livraison du moteur (rupture, plafond, lissage et ancre des prix, décès en colonnes), HMT-126 a) (version sourcée de Classes), marge des marchands, G21 au revenu déclaré | **refaites** |

En attente : l'intégration 8 (`0807690` : licencier, passé fiscal, `iles-metiers` de Classes) passe toutes les portes sauf `etat test_controle_fiscal` (p = 0,055). Elle sera certifiée avec `menages-revenus`, dont la version adaptée de ce test fait partie.

## 2. Les découvertes qui comptent

1. **La faim « baissait » parce que les affamés mouraient** (27/09 au soir).
   - Malden n'avait plus que 109 vivants sur 109 044, et Stratis 26 856 sur 108 985.
   - L'indicateur de faim ne comptait que les vivants.
   - Cause : 21 paiements à l'étranger contournaient le contrôle des changes (HMT-131).
   - Correction : une seule porte de sortie des devises.
2. **Un ménage mort de faim comptait « nourri »** : son besoin nul lui donnait un manque nul (HMT-136).
   - Revue en lecture seule de 23 fichiers, confirmée par deux lentilles : 2 portes confirmées fausses, 1 plausible.
   - Correction à la source dans `monde.repas` et `T.faim`.
3. **Une famine dans TOUS les mondes, en paix** (HMT-138).
   - 12 % d'Altis grec meurt de faim en un an.
   - Causes :
     - des emplois fantômes, payés 0, sans chômage ni KEA ;
     - l'ancienne paie des marchands ;
     - l'épargne forcée ;
     - l'ordre des dépenses ;
     - des patrons sans entreprise et des entreprises zombies.
   - La correction a) de la paie divise les morts de faim par 20 à Stratis, mais seulement par ~2 sur Altis : sa porte est REFUSÉE au critère du dixième.
   - La cible du dixième reste à tenir par la combinaison a) + d) + e) + KEA + allocation pour enfant, jugée sur des graines neuves.
4. **Le passé fiscal extrapolait 5 jours de démarrage sur 5 ans** (d06).
   - 336 drachmes devenaient une fraude pénale de 111 762, ce qui engorgeait le tribunal.
   - Correction : au moins un trimestre de pièces.
5. **Le gazole de Stratis** : ce n'était pas une crise de devises, mais le plafond de d03, fixé en monnaie locale (HMT-123).

## 3. Les verdicts négatifs

- **KEA, G21 amendée après avoir vu 4 graines** : −34 % sur les graines vues, −21,6 % sur les graines neuves. Porte refusée, KEA débranché.
  - Le KEA est ensuite branché par défaut, pour copier le réel (la Grèce l'a depuis 2017) ; G21 reste une mesure.
- **Porte de la paie (a)** : refusée au dixième (−44 % sur Altis, −58 % sur Altis grec).
- **G13 et G18** : ce n'étaient pas des régressions. G13 était un artefact du calendrier ; G18 était devenue sans objet (les récoltes passent par d09 et d15).
- **Mon essai d'un monde triplé pour `test_controle_fiscal`** : falsificateur refusé (p = 0,010), essai annulé.

## 4. Les pièges d'exploitation

- **La station est tombée deux fois.**
  - Le 27/09 à 21 h 59, à pleine charge (Kernel-Power 41, sans code d'erreur).
  - Le 28/09 à 01 h 19 : une mise en veille depuis le menu Démarrer ; au réveil, le pilote NVIDIA ne répondait plus, et la station est restée bloquée jusqu'à 10 h 31.
  - Règles : au plus deux gros calculs à la fois ; jamais de veille (réglage à faire par Younes).
- **La tâche `HMT_QWEN` a prouvé qu'elle recharge Qwen**, deux fois au redémarrage, et une fois quand Qwen s'était chargé hors de la carte graphique.
- **`/tmp/echecs_pays.txt` était partagé par les sessions** : fichiers privés depuis `213df93`.
- **Un calcul détaché par ssh doit partir ainsi** : `setsid nohup … < /dev/null &`.

## 5. Ce qui reste ouvert

- La famine (HMT-138) :
  - d) et e) de Classes ;
  - le KEA et l'allocation pour enfant (guerre) ;
  - la gérance et la cessation des paiements (moteur, HMT-139) ;
  - puis le verdict sur des graines neuves.
- Le run long (HMT-119) : feu vert de Younes, sous condition que la famine soit réglée.
- Les dettes :
  - tests fragiles (HMT-127) ;
  - fuite d'état entre tests (HMT-142) ;
  - d09 qui ne paie pas ses factures (HMT-135) ;
  - revenu égal à 7 fois la nourriture (HMT-140) ;
  - coût de d03 (HMT-141) ;
  - pic de faim au jour 17 (HMT-137) ;
  - seuil du 37e jour de la priorité des devises ;
  - dotation de combat de d25 à 1 jour ;
  - « réponse à la famine » (aide, urgence, exode) ;
  - blocus qui coupe le tourisme.
