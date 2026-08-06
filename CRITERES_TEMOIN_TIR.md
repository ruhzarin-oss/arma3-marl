# Témoin côté TIR — critères déposés AVANT tout comptage

*6 août 2026, matinée. ORDRE 3 de Fable. Le corpus A2 est figé (301 accrochages, `serverBA_a2.out`).
Aucun comptage de tir n'a été fait.*

## La question, et pourquoi elle n'est pas celle du flanc

Le banc A2 a rendu son verdict : le deux-axes bat le frontal de **+17,7 points** sur la tenue
(p = 0,0016), défenseurs figés, présence 100 %. **Le flanc est fermé, ce témoin ne le rouvre pas.**

Mais le témoin de visibilité a pointé **à l'envers** : l'axe hors du cône tenu est vu
*davantage* (60,5 % contre 53,9 %, p = 0,0025). Donc l'avantage n'est pas « ne pas être vu ».

Hypothèse restante, à trancher : **ils savent, et ils ne peuvent pas tirer.** Le cône ne pivote
pas, il s'ouvre ; et il est déjà mesuré qu'être vu tue moins fort qu'être engagé.

> Ce témoin sert à l'**étage 1**, pas au flanc. S'il est établi, le champ de risque doit sentir
> le risque d'**engagement**, pas le risque d'être vu. C'est un choix de conception qui coûte
> une nuit de GPU — d'où l'intérêt de le trancher pour le prix d'un dépouillement.

## Les deux témoins

**INTENTION.** Journal `TIR` : un défenseur désigne un assaillant comme cible. On compte, par
accrochage, la **part d'assaillants désignés au moins une fois**, ramenée aux assaillants
présents. Un défenseur se reconnaît à son axe : `hmt_axe = -1` dans le journal `POS`.

**IMPACT.** Journal `IMP` (`HitPart`) : qui touche qui. On compte, par accrochage, la **part
d'assaillants touchés au moins une fois**. C'est la grandeur solide — un impact ne s'interprète
pas.

Les deux se lisent **au niveau de l'accrochage** (moyenne des parts), pas de l'homme : les
hommes d'un même accrochage ne sont pas indépendants, et compter par homme gonflerait
artificiellement l'effectif.

## La sensibilité de la porte, écrite AVANT de lire — la leçon A2

A2 a échoué deux fois parce qu'il jugeait sur 18 puis 31 configurations : il ne pouvait rien
voir, et je l'ai quand même argumenté. On ne rejoue pas ça.

Effectifs disponibles : **160 accrochages deux_axes, 140 frontal.**

> Avec ces effectifs, et une dispersion des parts d'environ 0,25 d'un accrochage à l'autre,
> **ce corpus voit un écart d'environ 8 points ou plus.** En dessous de 8 points, un résultat
> non significatif ne veut rien dire — il faudra le dire ainsi, et non conclure.

## Ce qui tranche

**ÉTABLIE** — le deux-axes est désigné cible **significativement moins** (p < 0,05, écart
≥ 8 points), et les impacts vont dans le même sens.
→ Le mécanisme est le **sursis** : ils savent et ne peuvent pas engager. Le champ de risque de
l'étage 1 devra porter l'engagement.

**MORTE** — le deux-axes est désigné **autant ou plus**, ET touché autant ou plus.
→ L'hypothèse tombe. Le mécanisme reste non établi, et on cesse de le chercher de ce côté.

**ZONE MIXTE** — intention et impact se contredisent, ou l'écart reste sous les 8 points.
→ On garde les chiffres bruts, **on n'écrit pas d'histoire**, et l'étage 1 part sur le risque
appris tel quel, sans réorientation.

Dans les trois cas : **le flanc reste fermé, et aucune nuit supplémentaire n'est ouverte de ce
côté.**

## Contrôle de cohérence, à passer avant de lire les bras

Les assaillants **morts** doivent être touchés à ~100 %, et les assaillants **arrivés** au point
doivent être désignés plus souvent que la moyenne. Si l'une de ces deux banalités est fausse, le
dépouilleur est cassé et rien ne se lit.
