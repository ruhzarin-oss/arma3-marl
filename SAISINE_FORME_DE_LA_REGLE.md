# SAISINE DE FABLE — quelle forme de règle tiendrait sur une mission jamais jouée

*18/09/2026, 11 h 45. Demandée par Younes. Écrite avant la prochaine campagne : aucune de ses réponses ne peut être
comblée par un résultat que nous aurions déjà lu.*

## La décision que cette saisine éclaire

Nous devons **choisir la forme de la règle** que l'Architecte apprendra, avant de lancer la campagne P2 à types de
menace séparés (environ 192 épisodes, 3 heures sur 12 serveurs) et la boucle EvoGP (une nuit, environ 1500 épisodes).
Aujourd'hui, la règle s'écrit sur les seules perceptions du point de décision. La question est de savoir si elle doit
aussi prendre en entrée des **descripteurs de mission**, et sous quelle forme.

## Les faits, tous mesurés, avec leurs chiffres

**1. Les six choix de vignette, campagnes du 17/09 (576 épisodes + remplacements, critères pré-enregistrés).**

| phase | choix | classement | chiffres |
|---|---|---|---|
| P1 | partir / se terrer | INDIFFÉRENT | 100 %/100 % sans menace ; 33 %/43 % avec ; modulation +0,092 [−0,033 ; +0,213] |
| P2 | traverser / attendre | INDIFFÉRENT | 100 %/100 % ; 77 %/78 % ; modulation +0,010 [−0,250 ; +0,281] ; attendre coûte +203 s |
| P3 | observer 2 / 8 min | DOMINÉ (8 min) | 21 %/29 % ; 12,5 %/50 % ; écart moyen +0,229 [+0,042 ; +0,438] ; modulation +0,292 [0 ; +0,583] |
| P4 | direct / détour | DOMINÉ (direct) | 62,5 %/25 % ; 9,4 %/0 % ; écart moyen −0,234 [−0,406 ; −0,078] |
| P5 | délai 45 / 180 s | DOMINÉ (180 s) | assaut utile +0,333 [+0,125 ; +0,542] sans menace, +0,146 [+0,021 ; +0,271] avec |
| P6 | repli prudent / rapide | INDIFFÉRENT à la limite | 58 %/83 % ; 50 %/71 % ; écart moyen +0,229, borne basse exactement 0 |

**Aucun choix n'est dépendant de la situation** à la précision de ces dispositifs (R = 3 ou 4, 8 mondes appariés,
IC par rééchantillonnage des mondes).

**2. La perception, mesurée le 18/09 sur un banc dédié (10 épisodes, 0 erreur).** De nuit, lune 0,79, tous nos hommes
équipés de jumelles de nuit, cible debout, ligne de vue vérifiée, **regardée** :

| distance | vue | connue du groupe |
|---|---|---|
| 50 m | oui | oui, en 6 s |
| 100 m | oui | oui, en 6 s |
| 150 m | oui | oui, en 6 s |
| 300 m | oui, 100 % du temps | jamais en 300 s |
| 600 m | oui | jamais |

La connaissance a donc une **portée de 150 à 300 m de nuit**, et elle arrive vite ou jamais. Les menaces des campagnes
sont posées entre 150 et 350 m : la perception est au bord de sa portée.

**3. Ce que la ligne de décision écrit aujourd'hui** : alarme, temps depuis l'alarme, compromission, vivants,
défenseurs connus ; et depuis le 17/09 : menace vue, menace connue (groupe, camp, homme), distance crue, erreur de
position, mobilité, dernière vue, plus un niveau conjugué `menace_percue` ∈ {0, 1, 2}. La vérité du monde est écrite à
part et interdite à la règle.

**4. Le transfert a échoué une fois** : politique certifiée en sandbox, 0 succès sur 20 dans Arma (verdict
`transfert-non-etabli-0-sur-20`). Et le gymnase v0 (16/09) prédit **l'écart entre options**, jamais le **niveau** de
réussite.

**5. Le coût d'un épisode**, mesuré : 6 à 11 minutes selon la vignette, 2,1 Go de RAM et 0,2 cœur par serveur, 12
serveurs, soit environ 110 à 130 épisodes par serveur et par jour, ou 1 400 par jour au total. Une modulation de moins
de 35 points n'est pas établie à R = 4 sur 8 mondes ; la règle de puissance est n ≈ 4/δ².

**6. Les algorithmes d'écriture de règles, bancs du 17/09.** Sur formules cachées : la logistique L1 retrouve la forme
linéaire et le seuil (19/20 chacune) mais jamais la croix ; EvoGP retrouve les trois formes à 1000 épisodes
(19, 19 et 20 sur 20) et aucune fausse formule sur 300 essais sans formule cachée. Côté Oracle : QDax trouve la faille
étroite 13 fois sur 20 contre 7 pour le hasard ; BoTorch aux réglages par défaut fait pire que le hasard.

## Ce que nous avons déjà écarté

- **Donner la vérité à la règle** (type, position réelle de la menace) : elle deviendrait injouable.
- **Une table de situations** : 4⁵ situations perçues donnent 2¹⁰²⁴ règles ; nous cherchons des formules courtes.
- **Un verdict tiré du gymnase seul** : il prédit l'écart, pas le niveau, et le transfert a déjà échoué une fois.
- **Un Oracle à modèle mal réglé** : mesuré pire que le tirage au hasard.

## La question

**Quelle forme d'équation, prenant en entrée les perceptions du point de décision et des descripteurs de mission,
garderait sa validité sur une mission jamais jouée ?**

Trois précisions demandées, sans lesquelles la réponse ne nous servirait pas :
1. **Les descripteurs** : lesquels, parmi ceux qu'un détachement connaît vraiment avant de partir (phase, distance à
   l'objectif, effectif, temps imparti, heure, palier de défense) ? Et sous quelle forme entrent-ils : coefficients
   multiplicatifs, seuils conditionnels, ou paramètres d'une famille de règles ?
2. **Le critère qui la ferait rejeter** : quelle mesure, écrite avant, ferait dire « cette forme ne tient pas » ?
3. **Le nombre d'épisodes** pour la tester, avec son raisonnement de puissance, et **combien de missions distinctes**
   il faut avant de pouvoir parler de généralisation.

## Ce que nous ferons de la réponse

La forme retenue sera écrite dans les critères de la campagne P2 à types séparés, avant le premier épisode. Si la
réponse demande plus d'épisodes que la nuit n'en permet, nous réduirons le nombre de points de décision plutôt que la
puissance.
