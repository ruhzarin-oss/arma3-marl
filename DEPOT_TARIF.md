# Dépôt — le TARIF DE L'EXPOSITION, critères écrits AVANT mesure

Déposé le 15/08/2026. Fait suite à `VERDICT_SERIE3.md` : l'agent atteint l'objectif 15 %
du temps sur Arma contre 59,4 % au gymnase, et le corps réparé **fait mourir davantage**
(17/20 anéantis contre 9/20, p = 0,019). L'hypothèse est que **les deux mondes ne facturent
pas l'exposition au même prix**.

## La grandeur, définie une seule fois pour les deux mondes

**Le tarif = P(mourir au pas suivant | exposé) ÷ P(mourir au pas suivant | non exposé).**

- « exposé » = `los > 0,5` — la colonne 7 des douze, celle que la politique reçoit
  réellement. Pas une quantité commode reconstruite à côté ⟨règle 6⟩.
- « mourir » = la colonne `alive` (4) passe de 1 à 0 entre deux pas.
- Mesuré **par homme et par pas**, sur les mêmes définitions, dans les deux mondes.

C'est un **rapport**, donc sans unité : il se compare entre mondes même si les létalités
absolues diffèrent. ⟨règle 11 : deux chemins vers la MÊME grandeur⟩

## CONTRÔLES POSITIFS ⟨règle 16 clause 1⟩

1. **Dans CHAQUE monde, le tarif doit être > 1.** Être exposé doit tuer plus que ne pas
   l'être. Si un monde rend un tarif ≤ 1, l'instrument n'y voit pas le phénomène et
   **aucune lecture n'est admissible pour ce monde** — on ne compare pas un tarif à un
   capteur muet.
2. **Il doit y avoir des morts des deux côtés.** Un monde sans mortalité ne facture rien
   (leçon de la sandbox sans létalité : arriver y était inconditionnel).

## La porte

**Le rapport des tarifs (Arma ÷ gymnase) doit être lisible avec au moins 30 morts de chaque
côté.** En dessous, l'intervalle sur un rapport de proportions est trop large pour trancher
et **on ne lit pas**.

## Les lectures, déposées avant

| rapport Arma / gymnase | lecture |
|---|---|
| **> 2** | Arma fait payer l'exposition **beaucoup plus cher**. L'agent a appris à s'exposer à un prix qui n'existe pas là-bas — le gymnase est trop clément. |
| **< 0,5** | Arma fait payer **moins cher**. L'échec ne vient pas du tarif, et cette piste se ferme. |
| **0,5 à 2** | les deux mondes facturent pareil. **Le tarif n'explique pas l'écart** et il faut chercher ailleurs. |

La bande centrale est large exprès : elle est là pour **fermer la piste** si les tarifs se
ressemblent, pas pour laisser une porte de sortie.

## Ce qui rendrait la mesure fausse

- moins de 30 morts d'un côté → on ne lit pas ;
- un tarif ≤ 1 dans un monde → capteur muet, pas de comparaison ;
- `los` constant dans un monde → il ne sépare rien, et le rapport est vide de sens.

## Ce qui n'est PAS promis

Trouver un écart de tarif ne dit pas comment le corriger, ni que le corriger suffirait.
Et le projet a déjà mesuré un couvert qui protège **11× trop** dans la sandbox : si le
tarif diverge, il faudra vérifier que ce n'est pas ce défaut-là qu'on redécouvre sous un
autre nom.
