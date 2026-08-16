# Dépôt — le budget d'entraînement est-il la cause ? Critères AVANT

Déposé le 16/08/2026. Départage la **première** des trois lectures déposées dans
`VERDICT_CHIRURGIE.md`.

## Ce qu'on sait

Dans le monde **opéré** (couvert directionnel), 140 itérations donnent **4,3 %** — le score
de l'assaut frontal. Le même budget donnait **51,1 %** dans le monde de référence.

Le monde n'est pas injouable : **l'ancienne politique y fait 42,6 %**, le flanc 25 %.

## QUELLE DÉCISION CETTE MESURE FAIT BASCULER

**Si le budget est la cause** → le monde opéré est utilisable, il coûte simplement plus
cher, et le retypage du couvert est acquis. On entraîne désormais là-dedans.

**Si ce n'est pas le budget** → c'est le **façonnage** de la récompense qui ne convient plus
à ce monde, ou le monde est plus dur que ce qu'un apprentissage de cette forme peut porter.
Dans les deux cas, la chirurgie est **suspendue** et le monde de référence reste le seul où
l'on sache entraîner.

## Le dispositif

**560 itérations** — quatre fois le budget, soit environ 50 minutes de GPU. Même graine,
même protocole, même lecture sur les 6 graines **held-out**. Rien d'autre ne change :
un seul facteur à la fois.

## Les lectures, déposées

| prise de la politique réentraînée | lecture |
|---|---|
| **≥ 35 %** | **le budget ÉTAIT la cause.** Le monde opéré s'entraîne, il coûte plus cher. La chirurgie est acquise. |
| **≤ 10 %** | **le budget n'y est pour rien.** Quatre fois plus n'a rien donné : c'est le façonnage ou le monde. Chirurgie suspendue. |
| **10 à 35 %** | **INDÉCIS.** On ne conclut pas, et on ne relance pas un troisième budget en espérant mieux. |

## CONTRÔLE POSITIF ⟨règle 16⟩

**La courbe d'apprentissage doit MONTER.** Si la prise reste plate — comme à 140, où elle
stagnait à 0,8 % au 139ᵉ pas alors que les mètres passaient de 18 à 80 — alors le budget
n'était jamais en cause et la lecture ci-dessus n'est pas admissible : on lirait le bruit
d'un apprentissage qui ne démarre pas.

Concrètement : **la prise au dernier dixième doit dépasser celle du premier tiers.**

## Ce qui n'est PAS promis

Qu'un budget plus gros suffise. Et une chose qu'il ne dira pas : si la politique réapprise
**bat le flanc** (25 % dans ce monde). Elle peut monter à 30 % et rester derrière une
doctrine écrite à la main — auquel cas le vrai sujet n'est ni le budget ni le couvert, mais
**ce que l'apprentissage apporte face à un vocabulaire déjà bon.**
