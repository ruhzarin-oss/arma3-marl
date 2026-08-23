# RÈGLE DE DÉCISION DU BRAS R — déposée AVANT d'avoir regardé son résultat

**23/08/2026, 19 h.** Le bras R (140 itérations, γ_Φ = 1,0, la récompense d'avant le 17/08)
a fini ou est sur le point de finir. **Je n'ai pas encore ouvert son journal.**

## La règle, telle que Fable l'a posée

> **R « franchit »** si la courbe des mètres **ne s'arrête pas à 95 m** *et* si la prise
> finale **dépasse la frontale (12,1 %)**. Prise ≥ flanc (32,9 %) serait une victoire pleine.

**Prédiction de Fable, écrite avant le résultat : R franchit.** Si R plafonne à 95 m, son
hypothèse γ tombe **en même temps que la mienne**.

## Ce que Fable a réfuté dans mon hypothèse, avec mes propres chiffres

1. **« Le monde du 13/08 était moins létal, traverser était survivable »** — réfuté. **Le
   flanc scripté rend 32,9 % AUJOURD'HUI.** Une manœuvre aveugle traverse une fois sur trois
   dans le monde durci. Le monde n'interdit pas la traversée.
2. **« Le gradient ne voit jamais la prise »** — faux au sens strict. 0,8 % × 256 ≈ 2 prises
   par itération, soit 100 à 300 événements sur un entraînement. **Il les voit et il ne bouge
   pas.** La formulation juste : le signal est sous le bruit, et une **rente** pousse en sens
   inverse.
3. **5,7 % appris < 12,1 % frontale.** S'il mourait en essayant, il ferait ~12 %. Il fait
   **pire** : il retient ses pas. **C'est la signature d'un équilibre de camping**, pas d'un
   monde qui tue tout le monde.

## Le suspect qu'il désigne : ma correction du 17/08

Arithmétique au bord de l'enveloppe, à 95 m, prise invisible :

| | tenir | avancer puis mourir |
|---|---|---|
| **γ_Φ = 1,0** (avant) | **exactement 0** | +0,015 |
| **γ_Φ = 0,99** (après) | **+0,00095 par pas**, ~+0,03 sur 40 pas | +0,015 à +0,029 |

**Sous 0,99, une rente de survie proportionnelle à la distance rend le camping meilleur
qu'une incursion**, tant que p(prise) reste sous ~0,2-1 %. **Le mur à 95 m est exactement
la ligne où « avancer » devient « avancer-puis-mourir ».**

> Le théorème de Ng garantit l'invariance de l'**optimum**, pas la **trajectoire du gradient**
> depuis une initialisation aveugle à la prise. Et **sa prémisse n'est pas satisfaite ici** :
> troncature à 60 pas et Φ(terminal) ≠ 0. **Ma « faute » d'avant le 17/08 était un façonnage
> non-potentiel qui FINANÇAIT L'EXPLORATION SOUS LE FEU. La correction était théoriquement
> propre et pratiquement fatale.**

⭐ **Cliquet : un correctif théoriquement juste peut détruire l'apprentissage, parce que le
théorème protège l'optimum et pas le chemin qui y mène.**

## Ce que je dois corriger dans mon propre dossier

Mon point « l'artefact rend 50,7 % avant et après le durcissement » est **muet** : les deux
mesures ont été faites **aujourd'hui**. Je n'ai aucune évaluation datée du 13/08. Il dit
que l'artefact marche encore ; il ne dit **rien** sur le durcissement du monde.

## Ce qu'il ne faut PAS faire (repris tel quel)

1. **Pas de pénalité de mort** — la panne est un excès de prudence ; renchérir la mort
   renforce le camping.
2. **Ne pas grossir le 0,001** — sous γ=0,99 c'est une homothétie, la rente grossit autant.
3. **Ni entropie, ni curriculum de létalité, ni epsilon maintenant** — ça réparerait le
   symptôme et masquerait la cause.
4. **Ne pas juger sur les mètres moyens** : ils confondent **mourir-en-avançant** et
   **camper**. Juger sur le taux d'incursion sous 60 m, la position des morts, la prise.
5. **Ne pas relancer « γ=1,0 ET ancienne létalité »** pour que ça remarche : ça remarcherait,
   et on ne saurait rien.
6. **Pas de verdict sur n=1** — deux graines par bras.
7. **Ne pas faire de « retrouver 50,7 % » la porte.** 50,7 est peut-être une queue de
   distribution. La porte déposée — battre les deux doctrines écrites à la main — est la
   bonne, on la garde.
