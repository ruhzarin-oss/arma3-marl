# Plan — rendre la menace visible au moment de choisir

*17/09/2026, après-midi. Demandé par Younes (« oui prépare le plan »). Suite des verdicts de la nuit (P1, P2 et P4 : aucun
choix ne dépend de la situation), du banc d'équation (test B : aucune règle possible sur les vrais épisodes) et de
`plans/plan-architecte-oracle.md` (§ 4 ter, niveau 3 : nouvelle perception). Plan à valider : aucune ligne de mission
avant.*

## Le constat, mesuré

- **Perceptions constantes.** Au moment du choix, la ligne de décision écrit 5 perceptions : alarme, depuis_alarme,
  compromis, vivants, defenseurs_connus. Dans les campagnes de la nuit, elles sont presque constantes :
  - P2 : seul `vehicule_vu` varie, dans 8 épisodes sur 128 ;
  - P4 : rien ne varie ;
  - P1 : presque rien ne varie.
- **Menaces absentes.** `defenseurs_connus` ne compte que les défenseurs du site (`CHACAL_EST_SITE`). Les menaces posées
  par la situation (`CHACAL_MENACES` : guetteur, patrouilles, poste de contrôle, poste d'écoute) n'entrent jamais dans
  la ligne.
- **Décision trop tôt.** Le choix est pris au tout début de la phase, avant d'avoir pu observer.
- **Conséquence.** Aucune règle, ni équation ni Oracle, ne peut choisir selon une menace qu'elle ne perçoit pas. Le
  banc d'équation l'a confirmé : aucun gain sur les vrais épisodes.

## Le principe

Le détachement ne décide que sur ce qu'il **perçoit**. On ajoute deux choses :
1. des **perceptions de la menace**, calculées comme le moteur les connaît, jamais la vérité ;
2. une **fenêtre d'observation** avant le choix.

La vérité (nombre, position et type réels des menaces) est écrite **à part**, comme `verite_defenseurs` aujourd'hui.
Elle est réservée à l'Oracle et à la lecture, et un test dbt interdit ces colonnes à l'Architecte.

## 1. Les perceptions nouvelles

Deux canaux distincts, parce que la géométrie et la connaissance ne disent pas la même chose (mesuré le 02/08) :

| perception | canal | calcul, à l'instant du choix | quand rien n'est perçu |
|---|---|---|---|
| `menaces_vues` | géométrie | nombre d'unités de menace vivantes vues **maintenant** par au moins un homme du détachement (`CHACAL_fnc_voit`, déjà utilisé en P2 : portée 800 m, cône 70°) | 0 |
| `menaces_connues` | connaissance | nombre d'unités de menace que le **groupe du détachement** connaît : champ « known by group » (vrai ou faux) de `targetKnowledge`, et non `knowsAbout` du camp | 0 |
| `distance_menace` | connaissance | distance à la plus proche menace connue, **à sa position crue** (champ « target position » de `targetKnowledge`), pas à sa position vraie | −1 |
| `erreur_position` | connaissance | erreur de position que le moteur s'accorde sur cette menace (champ « position error ») | −1 |
| `menace_mobile` | connaissance | 1 si la position crue de la menace la plus proche a bougé de plus de 10 m pendant la fenêtre, sinon 0 | −1 |
| `vue_depuis` | connaissance | secondes depuis que la menace la plus proche a été vue (champ « last time seen ») | −1 |
| `vehicule_connu` | connaissance | 1 si un véhicule de menace est connu (patrouille motorisée de P2) | 0 |

Le champ « known by group » vient de la description embarquée dans le binaire (`targetKnowledge` : 7 champs, relevés le
12/09). Il remplace `knowsAbout`, qui est une connaissance de **camp** : un camarade n'importe où suffit à la faire
monter.

**Vérité, écrite à part** : `verite_menaces` (unités de menace vivantes), `verite_distance_menace` (distance réelle à la
plus proche), `verite_types` (types posés).

## 2. La fenêtre d'observation

Nouveau levier `CHACAL_OBSERVATION` : 0 = origine (décision immédiate, rien ne change), sinon la durée de la fenêtre en
secondes. **Durée fixée à 90 s par Younes le 17/09.** Pendant la fenêtre, le détachement reste immobile (couché ou arrêté selon la phase). Les
perceptions sont échantillonnées toutes les 5 s, et la ligne de décision écrit leur état **à la fin** de la fenêtre.

| phase | où observe-t-on | puis le choix |
|---|---|---|
| P1 insertion | couchés à la zone de poser | partir tout de suite ou se terrer 3 min |
| P2 route | arrêtés au bord de la route | traverser tout de suite ou attendre la patrouille |
| P4 mise en place | au regroupement | itinéraire direct ou détour |
| P3, P5, P6 | inchangé dans un premier temps | perceptions de la menace ajoutées à la ligne, sans fenêtre |

La fenêtre coûte le même temps aux deux options : elle ne biaise pas la comparaison. Elle change en revanche la vignette.
Les épisodes avec fenêtre ne se mélangent donc pas aux campagnes de la nuit.

Marqueur `CHACAL|OK|decision|version|3` : les tests dbt des nouvelles perceptions ne s'appliquent qu'aux épisodes qui
l'ont.

## 3. Contrôles avant toute campagne (règle 16 : une mesure doit savoir échouer)

| contrôle | montage | attendu |
|---|---|---|
| **positif** | une patrouille posée à 150 m, droit devant, terrain découvert | `menaces_connues` > 0 à la fin de la fenêtre dans au moins 80 % des épisodes |
| **négatif géométrique** | la même patrouille à 1500 m derrière un relief | `menaces_vues` = 0 dans au moins 95 % des épisodes |
| **nul** | bras témoin, aucune menace posée | `menaces_connues` = 0 et `menaces_vues` = 0 dans 100 % des épisodes. Sinon, fuite : des défenseurs ou des véhicules de décor comptés comme menaces |
| **cohérence** | tous les épisodes où une menace est connue | \|position crue − position vraie\| du même ordre que `erreur_position`, écrit par épisode |
| **origine intacte** | `CHACAL_OBSERVATION = 0` | décisions, délais et `choix_joue` identiques à la mission actuelle sur une fumée appariée (mêmes mondes, mêmes graines) |
| **pas de fuite** | test dbt | les colonnes `verite_*`, `bras`, `niveau_menace` et `graine` sont absentes de la table de l'Architecte |

## 4. Vérifier que la perception varie à 90 s, sur graines disjointes

La durée est fixée à 90 s (Younes, 17/09). On vérifie seulement que la perception **varie** sous menace : si le
détachement voit toujours la menace, ou ne la voit jamais, une règle n'a rien à apprendre.
- **Mesure** : pour chaque phase (P1, P2, P4) et chaque type de menace **séparé** (niveaux 1 et 2, pas le 3 qui les
  mêle), la part d'épisodes où `menaces_connues` > 0 à la fin des 90 s.
- **Attendu** : entre 30 et 70 %. Hors de cette plage pour une phase ou un type, c'est rapporté à Younes avant la
  campagne de cette phase. Rien n'est changé seul.
- **Coût** : 3 phases × 2 types × 4 mondes × 2 épisodes = 48 épisodes, moins d'une heure sur 12 serveurs.

## 5. Les campagnes qui suivent (critères écrits à part, avant)

- **Plan d'expérience**, pour chaque phase P2, P1 puis P4 : option tirée à pile ou face, menace de **type 1, de type 2
  ou absente** (tiers égaux), 8 mondes, environ 192 épisodes.
- **Lectures**
  - le banc d'équation (L1, arbre, EvoGP) sur (perceptions, option, issue) ;
  - la valeur de l'information cachée (plan Architecte / Oracle, § 4 ter) avec θ = type de menace, pour voir combien
    les nouvelles perceptions en récupèrent.
- **Hypothèse à tester** (écrite dans le plan du 16/09) : patrouille mobile repérée → attendre ou se terrer ; guetteur ou
  poste fixe → partir ou traverser.
- **Ordre** : P2 d'abord, parce que la perception y existe déjà en partie (`vehicule_vu`, `CHACAL_fnc_voit`) et que
  l'hypothèse y est la plus nette.

## 6. Ce qu'il faudra construire (aucune ligne avant validation)

1. **Mission `00_socle.sqf`** : paramètre `CHACAL_OBSERVATION` (défaut 0).
2. **Mission `60_phases.sqf`**
   - fonction `CHACAL_fnc_perceptionMenace` (les 7 perceptions et la vérité à part) ;
   - fenêtre d'observation avant les points P1, P2 et P4 ;
   - perceptions ajoutées à toutes les lignes de décision ;
   - marqueur de version 3.
3. **`description.ext`, `lancer.sh`, `verifier_valeurs.py`** : le nouveau levier.
4. **dbt**
   - `stg_decision` lit les nouveaux champs ;
   - tests : perception nulle sans menace (bloquant), perception qui varie sous menace (avertissement), Architecte sans
     vérité (bloquant).
5. **Fumées** : contrôles du § 3, puis calibrage du § 4.
6. **Critères et campagnes** : § 5.

## 7. Pièges connus d'avance

- **Localité** : `targetKnowledge` et `knowsAbout` ne sont à jour que pour un groupe qui a au moins un membre local
  (description du moteur, 12/09). Les épisodes CHACAL tournent en serveur dédié, et `lancer.sh` ne démarre aucun
  client headless : toutes les IA sont locales au serveur. Le contrôle positif le vérifie quand même.
- **Un zéro n'est pas une preuve** : `knowsAbout` = 0 peut vouloir dire « pas dans la liste de cibles » (décompilé le
  13/09). Le champ « last time seen » lève l'ambiguïté : −1 veut dire jamais vu.
- **Le cône compte plus que la distance** (mesuré le 02/08) : l'orientation du détachement pendant la fenêtre change ce
  qu'il voit. Elle est écrite dans la ligne (azimut du chef de groupe).
- **La fenêtre expose** : le détachement peut être repéré pendant qu'il observe. `compromis` et `alarme` sont écrits au
  moment du choix ; un épisode compromis avant le choix reste valide, mais il est rapporté à part.
- **Le type de menace est une vérité** : la règle apprise ne doit jamais le lire directement. Seules `menace_mobile` et
  `vehicule_connu` en sont des perceptions.

## Décisions pour Younes

1. ~~La fenêtre d'observation~~ : **90 s**, fixée par Younes le 17/09.
2. **L'ordre** : P2, P1 puis P4, ou autre chose ?
3. **La perception de groupe** (`targetKnowledge` du détachement) plutôt que la connaissance du camp (`knowsAbout`) :
   d'accord ?
