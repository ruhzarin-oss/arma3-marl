# Cahier des charges — un banc a DECISIONS

Etat : PROPOSITION. Ecrit le 15/09/2026 pendant que PORTE-HUIT-MONDES tourne.
Rien n'est lance sur cette base sans accord.

---

## 0. Ce qui motive ce document, et la mesure qui en corrige la premisse

Le constat de depart etait : « CHACAL n'offre aucun choix qui change l'issue, donc
rien a apprendre ». En preparant ce cahier des charges, trois mesures ont ete faites.
La troisieme corrige la premisse.

**Mesure 1 — 96,6 % du corpus est hors corpus.** Sur 1520 episodes de mission
termines, **1468 sont marques `AVERT|hors_corpus|depart|N|approche_non_jouee`**
par le banc lui-meme. 52 seulement ont joue l'approche, tous anterieurs au 13/09.

**Mesure 2 — la regle d'ouverture reparee n'a jamais recu de renseignement.**

| campagne | depart | episodes | renseignement > 0 | gardes differents |
|---|---|---|---|---|
| PORTE-HUIT-MONDES-15-09 | 5 | 147 | **0 / 147** | **0 / 147** |
| CONFIRMATION-MISSION-15-09 | 5 | 96 | **0 / 96** | **0 / 96** |
| PHASE1-CONTROLE-15-09 | 3 | 25 | **13 / 25** | **12 / 25** |

A `depart = 5` la phase 3 ne tourne pas : la crete n'observe rien, `CHACAL_VUES`
est vide, et le choix d'ouverture se fait les yeux fermes — `gardes|[0,0]` dans
**243 episodes sur 243**.

**Mesure 3 — mais a `depart = 3`, la regle reparee FONCTIONNE.** 13 episodes sur
25 rapportent du renseignement, et **12 sur 25 comptent des gardes DIFFERENTS
entre les deux ouvertures** : `[0,1]` neuf fois, `[1,0]` deux fois, `[0,2]` une fois.

> **Conclusion qui change tout : CHACAL n'est pas incapable de porter une decision
> informee. Il en produit une des que la phase 3 tourne. Ce qui etait casse, c'est
> la CONFIGURATION DE LA CAMPAGNE, pas le banc.**
>
> PORTE-HUIT-MONDES pose la question « la porte compte-t-elle ? » dans la seule
> configuration ou la porte ne peut jamais etre choisie en connaissance de cause.
> C'est une faute de plan, et elle est de moi.

---

## 1. La propriete que doit avoir un banc a decisions

Une seule, et tout le reste en decoule :

> **Un banc a decisions doit savoir distinguer une bonne decision d'une mauvaise,
> et le PROUVER avant qu'on y entraine quoi que ce soit.**

Elle se decompose en quatre conditions, chacune verifiable, chacune capable
d'echouer.

### C1 — L'option change l'issue
Forcer A, forcer B, apparie sur **au moins huit mondes**. L'ecart sur la sortie
primaire enregistree d'avance doit exclure zero.
*Pourquoi huit : a quatre mondes le signe des rangs plafonne a p = 0,625 ; le test
ne peut pas conclure meme si l'effet est reel.*

### C2 — La MEILLEURE option change
Il doit exister un observable `o` tel que le signe de (A − B) s'inverse avec `o`.
Si A est toujours meilleure, la politique optimale est une constante : un bit,
rien a apprendre, et le banc ne classe pas deux agents.
*C'est la condition la plus chere : une interaction coute environ quatre fois
l'effet principal a precision egale.*

### C3 — L'observable existe AU MOMENT du choix
Verifiable dans la trace, sur l'episode meme : la ligne de decision doit porter un
observable **non degenere**. `gardes|[0,0]` dans 100 % des episodes = echec de C3.
*C'est la condition que CHACAL vient de rater 243 fois de suite, et que la meme
regle satisfait 12 fois sur 25 des qu'on lui rend la phase 3.*

### C4 — L'option forcee est reellement jouee
Controle positif mecanique dans la trace, comme `azimut_joue` verifie 0 non
conforme sur 68 episodes.

**Un point de decision qui rate une des quatre n'entre pas dans l'arbre. La valeur
de l'arbre est le nombre de points CERTIFIES, pas le nombre de branches dessinees.**

---

## 2. Le piege de la symetrie — a lever avant de depenser un episode

Deux options **echangeables** sous le generateur du monde ne peuvent pas differer
autrement que par hasard.

Le decor de CHACAL pose les ouvertures a 99 deg et 279 deg — a 180 deg l'une de
l'autre — sur un cercle de rayon 46 m, avec des defenseurs nes dans 55 m. Sous un
tel generateur, les portes A et B sont echangeables *a disposition des defenseurs
fixee*, et C1 est impossible **par construction**.

> **Regle : avant de lancer, LIRE LE GENERATEUR et prouver que les options ne sont
> pas echangeables. Ce test coute zero episode.**

C'est exactement ce que la disposition des defenseurs peut briser — et c'est
pourquoi `gardes` est l'observable, pas la geometrie.

---

## 3. Le vivier des decisions candidates

Chacune est candidate parce qu'on a **deja mesure** qu'elle bouge l'issue :

| candidate | effet deja mesure | observable possible |
|---|---|---|
| **repartition assaut / bouchon** | 3 hommes sur 10, 31 coups sur 5753, **46 % des exfiltres** | delai de la QRF |
| ouverture la moins gardee | `gardes` differents 12/25 a depart=3 | `gardes`, `dgarde` |
| tuer le guetteur d'abord | `knowsAbout` est de camp, pas de soldat | qui voit, `targetKnowledge` |
| entrer ou non dans l'arc | l'arc de tir donne **4 s de sursis** | azimut relatif au defenseur |
| route couverte ou courte | cout = exposition par metre | exposition calculable |

**Rang 1 : la repartition de l'effectif.** L'asymetrie est deja mesuree et enorme,
et l'optimum doit basculer avec le delai de la QRF — un parametre de banc, donc
un observable qu'on controle. C'est le candidat le plus susceptible de satisfaire C2.

---

## 4. Les sorties : compter, jamais seuiller ; un axe actif, jamais quatre

- La sortie primaire est un **comptage gradue 0..k**, enregistre d'avance.
  *Mesure : `detruits 0..3` coute 45 % d'episodes de moins que `charges >= 3`.*
- **Un seul axe actif par campagne.** Les epilogues gradues ont ete mesures puis
  refutes : quatre axes coutent quatre fois plus d'episodes (rel 3,78 contre 1,90)
  parce que trois axes inertes diluent le seul actif. Les autres drapeaux sont
  **enregistres, jamais notes**.

---

## 5. Les instruments — chaque cicatrice devient une exigence

1. Chaque point de decision ecrit **une ligne** : `t`, point, options offertes,
   option prise, **l'observable**, et la cause.
2. **Aucun `continue` muet.** Tout renoncement porte une cause. *(54 charges
   manquees sur 72 etaient des renoncements, pas des defaites.)*
3. **Controle positif par decision** : forcer chaque option, verifier dans la trace
   qu'elle a bien ete jouee.
4. **Controle negatif** : drapeaux effaces -> zero branche allumee. Si l'arbre
   affiche encore une branche, l'instrument ment.
5. **Le falsificateur est ecrit dans le job AVANT la campagne.** *(Un p qu'on
   regarde pendant que les donnees arrivent n'est pas un p : +15,4 p=0,031 a 261
   episodes est devenu +11,1 p=0,219 a 302.)*
6. **Le nombre d'instances voyage avec tout taux.**
7. **Les bras sont entrelaces dans la file**, jamais l'un ce soir et l'autre demain.

---

## 6. La table `decision` — ce qui rend le banc ENTRAINABLE

Nouvelle table du socle, une ligne par point de decision par episode :

```
episode_id | t | point | options | choix | <observables> | issue | cause
```

C'est litteralement le triplet (etat, action, recompense). **CHACAL ne l'a jamais
emis parce qu'il n'a jamais eu d'options.** Sans cette table, le banc n'est pas un
support d'apprentissage : c'est un tableau d'affichage.

C'est aussi, tel quel, le prompt de l'officier LLM : les drapeaux sont du texte.

---

## 7. Budget

- **Cout par episode** : cible <= 4 min de mur (CHACAL : 8,3 min) -> >= 150 ep/h a
  10 instances. Debit instantane mesure aujourd'hui : **72 ep/h a 8,4 serveurs**.
- **Certifier C1** : 8 mondes x 2 options x 10 rep = **160 episodes ~ 2 h 30**.
- **Certifier C2** : 8 mondes x 2 options x 2 niveaux de l'observable x 10 rep =
  **320 episodes ~ 5 h**, une nuit.
- Le poste de depense reel n'est pas la machine, c'est la file : elle se vide
  entre deux campagnes. 72 ep/h instantane contre 34 ep/h tenus sur 24 h.

---

## 8. Le montage, par etapes, chacune avec sa porte

**Etape 0 — LA MOINS CHERE, ET ELLE PASSE AVANT TOUTE RECONSTRUCTION.**
Rejouer le contraste des portes a `depart = 3`, la ou l'observable existe
(gardes differents 12/25). 8 mondes x 2 portes x 10 rep.
*Si la porte compte LA, CHACAL porte deja une decision informee et il n'y a rien a
reconstruire — il y a une phase 3 a rendre obligatoire.*
*Si elle ne compte toujours pas la, alors la reconstruction est justifiee par une
mesure et non par une intuition.*

**Etape 1** — squelette du nouveau banc, instruments et controle negatif, sur
**l'instance 9** (le labo : libre, reservee, `server.cfg` sans parametre CHACAL —
donc l'hote naturel d'un banc neuf, et aucune interference avec les campagnes).

**Etape 2** — **un seul** point de decision, certifie contre C1 a C4.

**Etape 3** — le deuxieme point. L'officier LLM n'a rien a decider tant qu'il n'y
a pas **deux** points certifies.

**Etape 4** — l'arbre (debrief, epilogues). **En dernier** : c'est un affichage,
pas une mesure.

---

## 9. La regle d'arret du projet, ecrite d'avance

> Si trois points de decision candidats sont testes et qu'aucun ne satisfait **C2**
> — une inversion de signe predite par un observable — alors une mission Arma de
> cette famille ne peut pas porter un banc a decisions, et **on s'arrete**. On n'en
> construit pas un quatrieme.

---

## 10. Ce qui est deja en place

- `ArbreTest.Stratis` sur la WS (`C:\Users\Younes\Documents\Arma 3\missions\`) :
  `description.ext`, `init.sqf`, `mission.sqm`, quatre scripts — drapeaux, rendu de
  l'arbre, cascade d'epilogues, et le controle negatif « effacer tous les drapeaux ».
  **Jamais lancee dans Arma. Hors du depot git** — le piege deja paye une fois.
- **Instance 9** libre, `server.cfg` sans parametre CHACAL.
- Socle pret a recevoir une table `decision` : `pas` 24,5 M lignes, `perception`
  18,8 M, `evenement` 221 k, catalogue et connaissance en SQLite.

---

## 11. Les deux erreurs commises en ecrivant ce document

1. **J'ai d'abord mesure « 0 renseignement sur 143 episodes » — c'etait faux.**
   Je lisais les 400 premiers kilo-octets de chaque `.rpt` ; a `depart = 3` la ligne
   de choix tombe a **t = 1724 s**, bien au-dela. Corrige en lisant le fichier
   entier : 13/25.
2. **J'ai lance PORTE-HUIT-MONDES a `depart = 5`**, c'est-a-dire dans la seule
   configuration ou la regle que je venais de reparer le matin meme ne peut pas
   s'exprimer. Le banc l'ecrivait pourtant dans son propre journal, a chaque
   episode : `hors_corpus | approche_non_jouee`.
