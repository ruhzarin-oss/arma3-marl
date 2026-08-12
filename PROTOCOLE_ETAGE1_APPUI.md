# ÉTAGE 1 DU GESTE N°2 — protocole de la campagne appariée

*9 août 2026, 10 h 30. **Déposé avant le premier essai de cette campagne.** Contresigné par Fable.*

**Fiches relues ⟨règle 10⟩** : `courbe1-toucher-mesuree`, `flanc-fait-arriver-pas-proteger`,
`porte-a2-tient-instrument-valide`, `mesure-doit-savoir-echouer`,
`accord-sur-zero-nest-pas-accord`, `detection-en-cascade-part-hommes-vus`.

**Inventaire ⟨règle 7 étendue⟩** : le moteur expose `commandSuppressiveFire` et `suppressFor` ;
Antistasi les emploie en 8 lignes (`fn_suppressingFire`, MIT) ; **notre propre code emploie
`doSuppressiveFire` 66 fois** dans `shamal_obs.sqf` et `envelop_arma.sqf`. Le feu natif est donc
l'implémentation retenue, et mon feu scripté sort du chemin d'exécution.

## Ce que la campagne précédente a établi, et qui fonde celle-ci

48 essais, 4 terrains, 3 bras. Aucun verdict — un contrôle est tombé. Mais deux acquis :

| | |
|---|---|
| **le feu scripté est illisible** | +57 %, −40 %, −10 %, −5 % selon le terrain. Le +57 % venait d'un témoin qui s'effondrait (79, 66, 314, 0 — dispersion de 120 %), pas d'un appui qui améliorait. **Épitaphe : illisible.** Archivé, hors du chemin. |
| **le feu natif tient** | −11, −13, −25, −6 %. Ratios appariés 0,89 · 0,87 · 0,75 · 0,94 — quatre sur quatre sous l'unité. Mais 4 blocs valent 1/16, soit 6 % : insuffisant. |

**Le théorème qui en sort ⟨règle 12, déposée le 09/08⟩** : *la ligne de base appartient au lieu ;
toute grandeur comparée se lit appariée par lieu, et un agrégat sans sa décomposition par lieu
n'est pas une lecture.* Le témoin délivre 90 impacts sur un terrain et 253 sur un autre — sur du
plat dégagé. Cette variance n'entre **jamais** dans un ratio apparié : **les répétitions
n'achètent presque rien, les terrains achètent tout.**

## Le dispositif

Inchangé depuis la v3, sauf le nombre de bras. Six défenseurs à couvert derrière un muret,
invulnérables, **libres de leur posture** ; quatre victimes à 150 m qui ne tirent pas ; trois
appuis à 150 m à 90°. **Deux bras seulement : témoin, et feu natif.**

**Grandeur : les impacts DÉLIVRÉS** par les défenseurs sur les victimes, par `HitPart`.

## Le plan, déposé

**8 terrains admis × 3 répétitions × 2 bras = 48 essais**, plus le contrôle positif.

⚠️ **AMENDÉ LE 09/08 À 10 H 30, AVANT LA PREMIÈRE MESURE DE LIGNE DE BASE.** Je voulais
12 candidats. La recherche en rend **9 sur 150 000 tirages** — et la courbe dit que ce n'est pas
elle qui s'épuise mais l'île : le 9ᵉ a demandé 98 000 tirages quand le 2ᵉ en demandait 75.
**Stratis porte environ neuf sites de cette qualité à 800 m d'écart.** On ne baisse ni le
critère de site ni l'écart — c'est en abaissant le critère qu'on avait admis le terrain 0, dont
la ligne de base variait de 120 % et qui a produit un bras entier de bruit.

**Conséquence, déposée maintenant plutôt que découverte plus tard** : la campagne crible
**9 candidats**. La marge d'échec à l'admission passe de 4 à **1**. Si moins de 8 terrains sont
admis, on ne compense pas — on rend l'étage 1 sur le nombre réellement admis, en le disant, et
la clause d'échec ci-dessous se lit sur 9 et non sur 12.

## L'ADMISSION D'UN TERRAIN — la nouveauté, et la règle 11 appliquée au lieu

Un terrain n'est admis que si **sa ligne de base est reproductible**.

- deux mesures du témoin, **dans deux sessions séparées** ⟨Fable : l'ennemi du banc est de
  session — fusils à sec au 3ᵉ essai, panne au 235ᵉ accrochage ; deux runs adossés peuvent
  s'accorder et mentir ensemble⟩ ;
- **tolérance déposée en aveugle, ci-dessous, avant d'avoir vu le moindre candidat** :

> **Les deux mesures de ligne de base doivent s'accorder à ±35 % de leur moyenne.**

**Justification, et elle ne regarde pas les candidats** : le ratio apparié absorbe la variance
de niveau entre terrains, mais pas la variance *interne* à un terrain. Les ratios mesurés
(0,75 à 0,94) sont à 6-25 % de l'unité ; une ligne de base qui bouge de plus d'un tiers d'une
session à l'autre noierait l'effet qu'on cherche. Le terrain 0 était à 120 % de dispersion —
il tombe largement. Le terrain 3, à 0,363-0,632 de rendement, est le cas limite honnête : si
une tolérance à 35 % le refuse, **on crible plus de candidats, on n'élargit jamais la tolérance.**

## LE CONTRÔLE POSITIF — détectable, pas mesuré

Un terrain **à découvert**, sans muret, où le régime certifié du ×0,08 s'applique.
**Un terrain, 3 répétitions par bras, 6 essais.** Défenseurs invulnérables comme derrière le
muret : une seule variable change, le mur.

> **Plancher grossier : les trois paires doivent toutes tomber sous un ratio de 0,5.**
> Le régime certifié promet de l'ordre de 0,1 à 0,3 ; la marge est telle qu'un échec accuse
> **l'instrument**, jamais l'effet.

⟨Fable, principe déposé avec lui⟩ ***un contrôle positif qui a besoin de statistiques pour
passer a déjà échoué.***

Ce contrôle exerce en outre le double chemin au régime qui encaisse le plus d'impacts — donc là
où les deux chemins ont le plus d'occasions de diverger. Test de charge offert.

## LE DOUBLE CHEMIN ⟨règle 11⟩

Les impacts délivrés décident d'un certificat, donc ils se mesurent **deux fois** :
`HitPart` sur les victimes, et **`HandleDamage` rendant zéro** — qui compte chaque impact et
annule chaque dégât, donc préserve l'invulnérabilité tout en fournissant un second mécanisme.

⚠️ **Le premier jet employait `Hit`, et il était mort-né** : cet événement ne se déclenche pas
sur un homme `allowDamage false`. Il comptait 0 quand `HitPart` comptait 80. Corrigé au pré-vol,
avant la première mesure.

⚠️ **CRITÈRE REDÉPOSÉ LE 09/08 À 10 H 35, AVANT TOUTE MESURE.** Le pré-vol a donné 96 contre
**692**. La règle 11 a fait son travail — instrument déclaré en panne, cause cherchée — et la
cause est que **les deux chemins ne comptent pas la même unité** : `HitPart` compte l'impact,
`HandleDamage` se déclenche par partie du corps touchée. Une tolérance de 10 % sur les *comptes*
était inapplicable dès l'écriture.

> **Le critère porte sur la STABILITÉ DE LEUR RAPPORT, non sur l'égalité des comptes.**
> Si deux mécanismes voient les mêmes événements, leur facteur de conversion est constant.
> **Le rapport `HandleDamage` / `HitPart` ne doit pas s'écarter de plus de ±20 % de sa médiane,
> sur aucun essai.** Au-delà, on ne réconcilie pas — instrument en panne, on cherche la cause.

**Divulgation honnête** : les deux pré-vols ont donné 7,2 et 7,3. Je ne choisis pas ±20 % pour
les faire passer — n'importe quelle tolérance les aurait acceptés. Je la choisis assez large
pour tolérer le bruit de comptage d'un événement rare, assez serrée pour attraper un chemin qui
décroche. Ce que ça ne peut pas faire : détecter deux chemins qui se trompent **ensemble**, et
c'est écrit ici pour qu'on ne l'oublie pas.

## LA DÉCISION

> **Étage 1 rendu VIVANT si l'intervalle de confiance à 95 % du ratio apparié exclut l'unité.**

Huit terrains, huit ratios, tous sous 1 : un sur 256. Aucun seuil chiffré n'est emprunté à
l'ancre du −92 % — elle vient du régime à découvert et ne se convertit pas.

**Et ce que l'étage 1 ne fait pas** : il ne prédit rien du gain en mission. Faiblement vivante
et lisible suffit ; le banc se tait alors et laisse la **PORTE 0 du lieu** trancher, à ses
10 points sur la prise.

## CE QUI FERAIT ÉCHOUER LA CAMPAGNE — écrit avant

- **L'intervalle contient l'unité** → l'appui arrose sans figer, le geste n°2 **tombe**, et
  aucun terrain ne le sauvera. La mission est tuée à bas prix : le seul droit de ce banc.
- **Le contrôle positif ne passe pas** → ce n'est pas l'effet qui est absent, c'est
  l'instrument qui est aveugle. On ne lit rien d'autre ce jour-là.
- **Le rapport entre les deux chemins s'écarte de plus de ±20 % de sa médiane** → instrument en
  panne, on cherche la cause.
- **Le feu natif ne tire pas** → et il ne faut pas chercher loin : le 09/08 j'ai recopié
  `suppressFor` d'Antistasi sans savoir qu'elle **supprime celui à qui on l'applique**. Mes
  propres tireurs étaient supprimés, et le natif est passé de 248-414 coups à zéro. ⟨la règle 7
  oblige à **lire** ce que le moteur expose, pas à recopier ce que d'autres en font⟩
- **Plus de 3 candidats sur 9 échouent à l'admission** → ⟨clause de Fable, réécrite sur 9⟩ ce ne
  sont plus les terrains qu'on accuse, c'est **le géomètre** qui les qualifie de « plats et
  dégagés ». On retourne le voir **avant** de brûler des nuits.
- **Les deux chemins de mesure ne peuvent pas diverger si l'un est mort** : le premier jet
  employait `Hit`, qui ne se déclenche pas sur un homme invulnérable — il comptait 0 quand
  `HitPart` comptait 80. Remplacé par `HandleDamage` rendant 0, qui compte l'impact et annule
  le dégât. **Une tolérance entre deux chemins dont l'un est mort-né ne vaut rien**, et c'est
  le pré-vol qui l'a montré, pas le dépouillement.
- **Un essai où les hommes ne pouvaient pas obéir** (recensement `canFight`/`canFire`/`canMove`)
  → aucun verdict, comme pour tout contrôle qui tombe.

## Journalisé en plus, sans être jugé

Le canal **`behaviour`** de chaque défenseur ⟨demande de Fable⟩ — non pour chasser l'hypothèse
du couplage alerte/suppression, mais pour que si le natif change un jour de signe quelque part,
l'autopsie ait déjà ses pièces. Deux lignes maintenant valent une nuit plus tard.
