# Un levier écrit n'est pas un levier lu

*Verdict de méthode, 13/09/2026.*

## Ce qui s'est passé

La campagne EXFIL-13-09 a lancé six jobs répartis en trois bras. **Les six ont joué la référence.**

Le paramètre `CHACAL_EXFIL` avait été ajouté à `description.ext` par une expression régulière
`class CHACAL_SOCLE\s*\{[^}]*\};`. Or `[^}]*` s'arrête à la **première** accolade fermante, celle de
`values[] = {0,1}`. La nouvelle classe a donc été posée **à l'intérieur** du bloc `CHACAL_SOCLE`.
Imbriquée, elle est invisible pour `BIS_fnc_getParamValue`, qui a rendu le défaut 0.

Les deux moitiés de la preuve étaient écrites et personne ne les comparait :
- le `server.cfg` portait `CHACAL_EXFIL = 1` ;
- la ligne FINI rendait `exfil|0`.

## Pourquoi la garde n'a rien vu

Le correctif était protégé par un contrôle d'équilibre des accolades. Il a passé, **et il avait
raison** : les accolades étaient équilibrées. Elles étaient seulement mal placées.

**Une garde de forme ne remplace pas une garde de sens.** Un contrôle syntaxique ne dit rien de la
structure, et la structure ne dit rien de ce que le programme fait.

## Les trois corrections

1. **La classe est posée après la fermeture réelle du bloc**, repérée en comptant les accolades et non
   par une expression régulière, puis vérifiée par **profondeur d'imbrication** : `CHACAL_SOCLE` et
   `CHACAL_EXFIL` doivent être au même niveau.
2. **Le contrôle d'identité du lanceur devient générique.** Il relisait six champs ; `LEVIERS_CONTROLES`
   en relit quinze dans la ligne FINI et les compare au job, avec refus de l'épisode en cas d'écart.
   Un levier ajouté demain sera contrôlé sans qu'on y pense. Un levier absent de la ligne FINI est
   sauté, pour ne pas refuser les épisodes antérieurs au champ.
3. **Une porte d'atteignabilité** dans `controle_avant_run.sh` : un job dont l'issue visée est
   impossible avec ses leviers est refusé, sauf s'il déclare `"vignette": 1`. C'est la réponse
   structurelle au défaut des 245 épisodes en `arret=5`.

## La règle

Avant de dépenser une heure par épisode : **jouer un épisode, et vérifier dans la ligne FINI que la
mission a LU ce qu'on a écrit.** Un levier n'existe pas parce qu'on l'a posé ; il existe quand
l'épisode le rend.

Corollaire : toute campagne à trois bras doit être lue une première fois sur son **premier** épisode
terminé, avec pour seule question « les bras sont-ils différents ? ». Pas le résultat — la différence.
