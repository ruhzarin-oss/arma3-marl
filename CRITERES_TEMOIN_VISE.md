# Témoin d'INTENTION échantillonné — critères déposés avant lancement

*6 août 2026, 17h15. Troisième programmation de ce témoin. Le serveur n'est pas encore lancé.*

## Pourquoi il a fallu trois fois

Ce témoin a glissé deux fois : le 5 août (priorité au verdict A/B), puis ce matin (priorité à
la loi de mort). Chaque report était défendable. **Leur somme dessinait une préférence** — ce
qui fait avancer la ligne principale gagne contre ce qui ferait seulement *comprendre*.

> Règle appliquée ici : **un report de plus vaut annulation.** Ce banc part maintenant, ou son
> abandon se signe par écrit. Pas de troisième report silencieux.

## Ce qu'il mesure, et ce que l'ancien ne pouvait pas

Le journal `TIR` est émis sur l'événement `Fired` : une ligne n'existe **que si le défenseur
tire**. Mesuré sur le corpus A2 : dans **26 % des accrochages**, aucun défenseur n'a tiré sur
un assaillant.

Or ces accrochages-là sont précisément ceux où l'hypothèse du **sursis** joue à fond. L'ancien
instrument était aveugle exactement là où il fallait regarder.

**Nouveau journal `HMT|G|VISE`** : `assignedTarget` de chaque défenseur vivant, relevé **toutes
les 2 secondes**, qu'il tire ou non.

## L'hypothèse, inchangée depuis ce matin

Le banc A2 a établi que le deux-axes est **vu davantage** (+6,6 pts, p = 0,0025) et **reçoit
moins de feu** (−7,7 pts sur les tirs, −8,8 sur les impacts) — mais l'écart tombait sous la
barre des 10 points déposée, d'où « zone mixte, pas d'histoire ».

> **Ils savent, et ils ne peuvent pas tirer.** Le cône ne pivote pas, il s'ouvre.

Ce témoin la teste sur l'**intention**, là où l'instrument précédent ne pouvait pas voir.

## Les métriques

**A — DÉSIGNATION.** Part des assaillants désignés `assignedTarget` au moins une fois, moyennée
**par accrochage**. Un défenseur se reconnaît à `hmt_axe = -1`.

**B — DURÉE DE DÉSIGNATION.** Nombre de relevés à 2 s où un assaillant est désigné, rapporté
aux relevés où il est vivant. C'est la grandeur neuve : **combien de temps on reste dans le
viseur**, pas seulement si on y est passé.

**C — DÉSIGNÉS SANS TIR.** Part des désignations qui ne sont suivies d'aucun `TIR` du même
défenseur dans les 4 s. **C'est la mesure directe du sursis** : il vise, il ne tire pas.

## La sensibilité, écrite avant

Le banc A2 a rendu **160 accrochages deux-axes contre 140 frontal** en une nuit. À charge
égale, une nuit rend le même ordre de grandeur.

> Avec ces effectifs, ce corpus voit un écart d'environ **10 points** sur A, et environ
> **6 points** sur B — la durée étant moins dispersée qu'une proportion binaire.
> En dessous, un « non significatif » ne veut rien dire, et il faudra l'écrire ainsi.

## Ce qui tranche

**ÉTABLI — le sursis** : le deux-axes est désigné **moins longtemps** (B, p < 0,05, écart
≥ 6 points), **et** la part de désignations sans tir (C) est **plus élevée** pour lui.

**MORT** : désigné autant ou plus longtemps, et pas davantage de désignations sans tir.

**ZONE MIXTE** : A, B et C ne concordent pas → **on garde les chiffres, pas d'histoire.**

## Contrôles

1. **Présence** : ≥ 95 % des accrochages portent au moins un relevé `VISE`. Sinon la boucle
   d'échantillonnage n'a pas tourné et rien ne se lit.
2. **Cohérence** : un assaillant **touché** doit avoir été **désigné** dans la minute
   précédente, dans ≥ 80 % des cas. Sinon le lien intention-impact est cassé.
3. **Santé** : le journal `HMT|G|SANTE` doit rester plat. La fuite de groupes est corrigée,
   mais on ne le suppose pas.

## Règle d'arrêt

Jugement **unique**, au premier de ces termes : **≥ 120 accrochages clos par bras**, ou
**08h00 le 7 août**. Sous 30 événements de désignation au total, la primaire est illisible et
on le dit tel quel.
