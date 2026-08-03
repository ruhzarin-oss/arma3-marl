# CRITÈRES FIGÉS — COURBE N°2, VERSION DUEL SYMÉTRIQUE

Figés **avant** le run. Toute lecture postérieure se juge là-dessus, pas sur ce qui sortira.

## La question

Que fait un feu de suppression à un soldat **déjà au combat** ?

L'ancienne version ne posait pas cette question. Elle comparait un vrai duel à un stand de
tir : la cible du témoin était `CARELESS` avec la visée coupée, donc le témoin se
désintéressait d'elle. Le « ×4,29 de cadence » mesurait l'inactivité du bras témoin.

## Le dispositif

Deux bras qui tournent **en même temps**, sur le même serveur, dans la même séance :

- **TÉMOIN** — un défenseur, une cible à 100 m. **Les deux se tirent dessus.**
- **SUPPRIMÉ** — le même duel, **plus deux arroseurs** à 120 m sur le défenseur.

La seule différence entre les bras est donc le feu supplémentaire. C'est ce qu'on veut
isoler.

## Ce qui invalide le run, quoi qu'il donne

1. **Une cible morte** dans une séance → le bras concerné est muet, la séance ne compte pas.
   (`setDamage 0` à chaque ordre doit l'empêcher ; le relevé `[cibles]` doit afficher
   `0 morte(s)`.)
2. **Moins de 100 balles** dans un bras → trop peu pour conclure.
3. **Le bras témoin sous 0,5 balle/s** → il ne combat toujours pas, la correction a échoué.
4. **Cellules non certifiées terre ferme** → deux bancs ont déjà mesuré des noyés.
5. **Pont muet** pendant le tir → run nul, on ne lit rien.
6. **Théâtre ≠ Altis** alors que les cellules sont des cellules d'Altis.

## Ce qu'on lit, et dans quel ordre

La grandeur qui décide est la **capacité de nuire** = cadence × précision.

- Si la cadence des deux bras est du même ordre (rapport entre 0,7 et 1,4), alors la
  précision porte seule l'effet, et on la lit directement.
- Si la cadence diverge encore d'un facteur 2 ou plus, **le banc est encore biaisé** et on
  ne conclut pas sur le produit.

## Le verrou

Un paramètre mesuré ne se retouche que par une **meilleure mesure**, jamais par un meilleur
ajustement. Si le résultat déplaît, il reste.

## Référence à battre

L'ancienne version, désormais annulée pour biais de bras témoin :
`courbe_suppression_stand_de_tir.json` — cadence ×4,29, précision ×0,16, « danger » ×0,67.
Seule la précision de cette version est reprise comme ordre de grandeur attendu.
