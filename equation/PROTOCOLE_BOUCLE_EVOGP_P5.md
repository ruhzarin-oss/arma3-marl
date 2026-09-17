# Protocole — boucle Arma ↔ EvoGP sur le délai du porteur (phase 5)

*17/09/2026, après-midi. Demandé par Younes : « branche evogp sur arma comme ça sur un serveur pour voir ce que ça
donne ; on laisse evogp sur gpu, il faut lui donner de la puissance ». Suite de `plans/plan-architecte-oracle.md`
(l'Architecte seul, sans Oracle) et du verdict `aucun-algorithme-d-equation-retenu-evogp-seul-trouve-les-trois-formes`.
Écrit et commité avant le premier épisode de la boucle.*

## Ce que c'est

Une **démonstration**, pas une mesure. Elle répond à trois questions :
1. Une formule apprise par EvoGP peut-elle être jouée **exactement** par la mission, au point de décision ?
2. La boucle tourne-t-elle seule : Arma joue → EvoGP réapprend sur la 3090 → la nouvelle formule part au tour suivant ?
3. Que devient la formule au fil des tours ? C'est descriptif, sans décision.

Aucun classement « la formule bat l'option fixe » ne sera tiré de cette boucle. Sur un seul serveur, un tour fait
12 épisodes, soit environ 1 h 30. Le banc a montré qu'il faut de l'ordre de 1000 épisodes pour qu'EvoGP retrouve une
forme non linéaire.

## Pourquoi le délai du porteur

C'est le seul choix mesuré où le détachement **perçoit quelque chose qui varie** au moment de décider : l'alarme, et
depuis quand elle sonne. Dans P1, P2 et P4, les perceptions sont constantes, donc une formule serait forcément
constante.

## Comment la formule arrive dans Arma

- **Codes.** EvoGP écrit une formule (+, −, ×, min, max, neg, >) sur les 5 perceptions de la ligne de décision :
  alarme, depuis_alarme, compromis, vivants, defenseurs_connus. `equation/formule.py` la traduit en codes entiers,
  en ordre préfixe : 101 à 107 pour les opérations, 201 à 205 pour les variables, 301 à 307 pour les constantes.
- **Transport.** Les codes passent dans le job (`delai_mode = 1`, `f_len`, `f0` à `f31`), puis `lancer.sh` les écrit
  dans `server.cfg`, comme tous les leviers.
- **Décision.** Au point de décision, un interpréteur SQF (`CHACAL_fnc_evalNoeud`) calcule la formule. Si elle est
  positive, le délai est 180 s, sinon 45 s. La décision est écrite avec `decideur = FORMULE`, `valeur_formule` et
  `codes_lus`.
- **Mode 0 inchangé.** Par défaut, le délai reste celui du job, avec le même délai joué qu'avant. `CHACAL_DELAI_PORTEUR`
  garde la valeur du job, pour la ligne FINI et le contrôle d'identité ; `CHACAL_DELAI_JOUE` est le délai réellement
  joué.
- **Contrôle avant tout épisode.** Le traducteur a été testé sur 2000 formules EvoGP tirées au hasard, dont des cas
  d'égalité, avec 0 écart. Ce test a aussi montré que chez EvoGP, « > » vaut +1 ou −1, et non 1 ou 0.

## Un tour

1. **Apprendre** sur les épisodes d'exploration : le pilote P5 (192 épisodes, délai imposé et équilibré), plus
   l'exploration de la boucle.
   - Réglages : EvoGP à population 300 000 et 300 générations (environ 15 s par ajustement sur la 3090).
   - Parcimonie choisie parmi {0,001 ; 0,003 ; 0,01 ; 0,03} par gain croisé, un monde laissé de côté à chaque fois.
2. **Poser 3 jobs** sur l'instance 1, sur une paire de mondes tournante (4, 5, 6, 7, 8, 11, 12 ; le monde 9 est retiré),
   2 répétitions chacun :
   - délai imposé 45 s ;
   - délai imposé 180 s ;
   - formule.
   La menace de phase 5 alterne d'un tour à l'autre : niveau 3, puis témoin.
3. **Vérifier** chaque épisode FORMULE : recalculer la formule en Python sur les perceptions écrites.
   - Le choix doit être égal, `valeur_formule` égale, et `codes_lus` égal à `f_len`.
   - **Une seule faute arrête la boucle.**
4. **Journal** : `/mnt/data/hmt/equation/boucle/journal.jsonl` (formule, parcimonie, gain croisé par parcimonie,
   réussite des épisodes formule et exploration).

## Fumée, avant la boucle

Un job FORMULE de 2 épisodes (mondes 4 et 5, menace 3), avec la formule apprise sur le pilote. Attendus :
- 2 épisodes ACCEPTE, 0 erreur SQF ;
- `decideur = FORMULE` ;
- choix et valeur égaux au calcul Python ;
- `codes_lus = f_len` ;
- une ligne `porteur` avec `delai` égal au choix.

**Si une attente échoue, la boucle ne part pas.**

## Arrêt

Fichier `STOP` dans le dossier de la boucle, 12 tours, ou une faute de vérification. Younes peut arrêter à tout moment.
