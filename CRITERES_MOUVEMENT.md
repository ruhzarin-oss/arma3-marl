# CRITERES — `movement` CONDITIONNE-T-IL LA DETECTION ?

Ecrits AVANT tout chiffre. C est l equation 2 du plan de Fable, et il l a assortie d une
garde explicite : *« un terme qui recompense l immobile est exactement ce qui fabrique un
agent fige »*. Le resultat doit donc etre lu contre [[tout-ce-qui-fige-un-homme-coute]]
(doctrine scriptee 91,0 % contre 35,0 %) et contre le geste n°1 (bond, +15,0 pts sur 8/8).

## LA REVENDICATION
`Target.cpp:1000` : `spotCoef = movement * spotOptics * sensitivity * lightCoef * hidden`,
et `movement = ai->VisibleMovement()`. Le facteur est MULTIPLICATIF :

> **Un homme immobile est quasi indetectable, quelle que soit la distance.**

## LE DISPOSITIF — DEUX BRAS, MEME LIEU, MEME DISTANCE
Defenseur en COMBAT/RED, aucun `reveal`. Attaquant pleinement visible, `CARELESS`, sans
armement actif (AUTOTARGET et TARGET coupes) pour qu il ne combatte pas.
- **BRAS I (immobile)** : `disableAI "PATH"`, il ne bouge pas d un metre.
- **BRAS M (mobile)** : il fait la navette laterale, sans jamais se masquer.
La fraction de corps visible est relevee a chaque pas et doit rester **elevee et comparable
entre les deux bras** — sinon on compare la detection ET l occultation, et l episode est ECARTE.

## LA MESURE
Temps jusqu a `knowsAbout >= 0,5` puis `>= 1,5`, et `knowsAbout` max sur 90 s.
Le seuil de 0,5 est celui que Fable a nomme ; le 1,5 est celui de la reconnaissance de camp.

## CE QUI FALSIFIE, ECRIT D AVANCE
- **Si l immobile est detecte aussi vite que le mobile** — ecart de temps median
  **inferieur a 1,5x** — le facteur `movement` est REFUTE et **on ne le met pas dans le
  gymnase**. C est l issue la plus probable ET la plus souhaitable : elle evite d ajouter un
  terme qui paie l immobilite dans un monde ou l on sait deja que figer coute.
- **Si l immobile n est JAMAIS detecte** (knowsAbout max = 0 sur tous les episodes) alors que
  le mobile l est, le facteur est confirme dans sa forme la plus dure.
- **Si les deux bras sont a 4,00 instantanement**, la distance est trop courte : le banc ne
  discrimine pas, on ne conclut pas et on recule la distance.

## CONTROLE POSITIF
A 60 m, les DEUX bras doivent atteindre 4,00 : c est le cas connu massif, et il prouve que la
sonde voit la detection quand elle a lieu. S il tombe, rien n est lu.

## DISTANCES
La distance de travail est choisie APRES le banc de portee visuelle, dans la zone ou la
detection n est ni instantanee ni impossible. Balayage : 150, 250, 350 m.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur le toucher, rien sur la prise. Ce banc teste UN facteur.
