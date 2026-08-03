# CRITÈRES FIGÉS — LE FRONTAL SILENCIEUX (avant les données)

Figés le 2026-07-28, AVANT tout run.

## LA QUESTION
Le run `657f109d4af8e368` a donné, à A=12 vs D=8 : frontal **67 % d'abandons**, envelop
**17 %**. Le bras frontal est déclaré NON MESURÉ, mais l'écart désigne un mécanisme.

Dans `envelop_arma.py`, pendant leur crochet les débordeurs reçoivent `fire = 0` (« swing
silencieux ») ; les frontaux reçoivent tous `fire = 1`. Et `doSuppressiveFire` **fige l'unité**
(mesuré le 28/07 : c'est la cause de six semaines d'enlisement).

**Hypothèse à tester : l'avantage du flanc sur ce banc vient de l'ORDRE DE FEU, pas de la
géométrie.** Les débordeurs avanceraient parce qu'on leur interdit de tirer, les frontaux
s'arrêteraient parce qu'on leur ordonne de tirer.

## UNE SEULE VARIABLE
`--silencieux` : `fire = 0` pour tous, en progression. Même trajet, même effectif, même
théâtre, même nombre de pas. A=12 vs D=8, 6 répétitions, mode frontal uniquement.
Comparaison au bras frontal BRUYANT déjà mesuré (33 % de prise, 67 % d'abandons).

## SEUILS PRÉ-ENREGISTRÉS
1. **ABANDONS** : le frontal silencieux doit tomber **≤25 %** d'abandons (il était à 67 %).
   - Atteint → le mécanisme est confirmé : c'est l'ordre de feu qui figeait le frontal.
   - Non atteint → l'ordre de feu n'explique pas l'enlisement, chercher ailleurs.
2. **PRISE**, lue seulement si le seuil 1 est atteint : si la prise du frontal silencieux
   atteint **≥60 %** (l'envelop bruyant était à 83 %, le frontal bruyant à 33 %), alors
   **l'avantage du flanc mesuré sur ce banc est un artefact de l'ordre de feu**, et tous les
   A/B frontal-vs-débordement du banc — y compris FIBUA du 23/07 — sont à relire.
3. Si le silence fait CHUTER la prise (< 33 %), le résultat s'écrit tel quel : tirer en
   progression coûte du mouvement mais rapporte plus qu'il ne coûte.

## CE QUI N'EST PAS MESURÉ
Le silence appliqué à l'envelop. Une variable à la fois.

## INTERDICTIONS
Pas de retouche des seuils, des effectifs ni du nombre de répétitions après un chiffre.
