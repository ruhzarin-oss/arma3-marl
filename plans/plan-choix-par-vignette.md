# Plan — un vrai choix dans chaque vignette

*16/09/2026. Validé par Younes le 16/09 au soir. Suite de `plans/plan-curriculum-chacal.md` et du verdict
`la-situation-pese-sur-cinq-phases-la-phase-4-est-vide` (les menaces agissent sur les six phases).*

## Le principe

Une menace qui pèse ne suffit pas : l'agent n'apprend que si la menace **change quel choix est le meilleur**.
Chaque vignette reçoit donc **un choix à deux options**, forcé par le job pour être mesuré, et gardé seulement si
**la bonne option change selon la situation**. Sinon il reste comme **choix témoin**, comme la porte.

## Les six choix

| phase | vignette | le choix | ce qui devrait inverser la bonne option (hypothèse) | ce que coûte chaque option | existe ? |
|---|---|---|---|---|---|
| 5 assaut | `d4a5`, ~7 min | délai du porteur 45 s ou 180 s | sans alarme, attendre paie (+11,1 points de charges mesurés) ; avec alarme et renfort, rester 3 min sur l'objectif coûte des hommes | temps exposé contre charges posées | oui : `delai_porteur` et `menace_p5` |
| 2 route | `d2a2`, 6-15 min | traverser tout de suite ou attendre la patrouille | patrouille qui roule : attendre ; poste fixe : attendre ne sert à rien | temps contre contact | à moitié : règle `FENETRE_OBSERVEE` / `TRAVERSEE_AVEUGLE` décidée par le script, à forcer |
| 6 exfiltration | `d4a6`, 4-31 min | extraction principale ou de secours | patrouille sur la sortie : secours ; sinon principale | distance contre rencontre | à moitié : `exfil` existe, sens des valeurs à vérifier ; durée à plafonner |
| 4 mise en place | `d3 obs0 a4`, 4-7 min | itinéraire direct ou détour | patrouille ou poste d'écoute côté regroupement : détour ; sinon direct | exposition par mètre contre contact | non : levier d'itinéraire |
| 1 insertion | `d1a1`, ~4 min | partir tout de suite ou se terrer 3 min | patrouille mobile : se terrer ; guetteur fixe : partir | temps contre détection | non : levier d'attente |
| 3 observation | `d3 obs1 a3`, 8-31 min | observer 2 min ou 8 min | patrouille de crête : court ; sinon long | détection contre renseignement | non, et risqué : l'utilité d'observer n'est pas démontrée (oracle 8/18 contre 4/12) |

## Les fondations

1. **Ligne de décision** `CHACAL|E|decision|t|phase|point|options|choix|decideur|observables…` : une par choix,
   même forme partout. Observables = ce que le détachement peut savoir au moment du choix (alarme, depuis quand,
   compromission, vivants, défenseurs connus) ; `verite_defenseurs` est écrit à part, pour la lecture seulement.
   Marqueur `CHACAL|OK|decision|version|1` au démarrage : les tests ne s'appliquent qu'aux épisodes qui l'ont.
2. **Table dbt `stg_decision`** et tests : décision présente et unique, choix conforme au job, choix exécuté
   (le moteur l'a bien joué), observable lu après la pose de la situation, conséquence avant l'arrêt, durée,
   observable vivant.
3. **Symétrie sur papier** avant tout lancement : les deux options doivent coûter des choses différentes.
4. **Gymnase v1** : chaque choix validé devient une case (phase, situation, option) → issue mesurée.

## Comment un choix est jugé

- 2 options × (menace niveau 3, témoin) × 8 mondes × 6 répétitions = **192 épisodes**, un job par (bras, monde),
  bras entrelacés dans le temps, ~2 à 3 h sur 12 serveurs.
- **Critères écrits avant le lancement**, dans un fichier commité, avec le script de lecture :
  effet de l'option dans le témoin ; **modulation** (écart menace − écart témoin, apparié par monde, IC 95 % par
  rééchantillonnage des mondes) ; **inversion** (modulation établie et signes opposés).
- Modulation établie : le choix entre au curriculum. Sinon : choix témoin.
- Puissance écrite d'avance : à 48 épisodes par case, seule une modulation forte est détectable.

## Ordre

1. Fondations (ligne de décision, dbt), fumée de 4 épisodes.
2. **Pilote phase 5** : levier et menaces existent, il n'y a qu'à mesurer.
3. Phase 2, phase 6, phase 4, phase 1, puis phase 3.

Rien ne part dans la file sans contrôle avant run ; aucune modification de mission pendant qu'une campagne tourne.
