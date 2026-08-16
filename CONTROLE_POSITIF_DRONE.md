# LE CONTRÔLE POSITIF DU LIEN DRONE→SOLDAT — déposé avant lancement

*16 août 2026. ⟨Fable, sur la conception du banc drone⟩ « Le bras témoin n'est peut-être pas sans
lien. Le verdict n°2 dit que la connaissance est de camp, pas de soldat. Un drone du même camp,
qui perçoit nativement, alimente peut-être déjà l'escouade par les canaux internes du moteur. Si
c'est le cas, le tuyau de 8 lignes compare quelque chose à lui-même. »*

## LA QUESTION, ET UNIQUEMENT ELLE

On veut mesurer plus tard ce qu'un drone apporte à une escouade au sol. Le tuyau envisagé est
`reveal` — le seul point d'entrée scriptable dans la base de connaissance d'un groupe. **Avant
de mesurer quoi que ce soit avec ce tuyau, il faut savoir s'il existe.** Deux façons pour lui de
ne pas exister :

1. **Il ne transmet rien** — `reveal` ne suffit pas à faire tirer une escouade sur un ennemi
   qu'elle ne perçoit pas. Alors le canal est faux et tout banc bâti dessus mesure du vide.
2. **Il transmet déjà sans nous** — le moteur fait passer la connaissance du drone à l'escouade
   tout seul, parce qu'ils sont du même camp. Alors le bras « sans lien » n'est pas sans lien,
   et le banc comparerait une chose à elle-même.

⚠️ **Ce que ce contrôle N'EST PAS** : une mesure de ce que le drone vaut. Aucun bras ici ne
répond à « le drone paie-t-il ». On mesure **ce que l'instrument sait faire**, pas ce que le
drone apporte.

## LE MONTAGE — trois bras APPARIÉS par scène

Origine `[4644, 5652]` sur Stratis, mods du juge. À chaque répétition on tire **un** azimut, et
les trois bras jouent **le même azimut** — appariés, comme le verdict le sera.

- Escouade au sol : 4 × `B_Soldier_F`, mode **`natif`** du socle (aucun `disableAI` — c'est
  l'IA entière qui décide de tirer, jamais nous).
- Ennemi : 1 × `O_Soldier_F` à **150 m DERRIÈRE** l'escouade, donc **hors de son cône**. On
  s'appuie ici sur un fait déjà certifié : 18/18 dans le cône contre **0/26 hors**. L'ennemi est
  `disableAI "ALL"` + `CARELESS` + `allowDamage false` : il ne tire pas, il ne bouge pas, il ne
  meurt pas.
- Ligne de vue **exigée ≥ 0,5** entre le chef d'escouade et l'ennemi, vérifiée à la pose, jusqu'à
  12 azimuts essayés. Révélé, l'homme doit **pouvoir** tirer — sinon on mesurerait le relief.

## ⛔ AMENDEMENT DU 16/08 — CE N'EST PLUS UN DRONE, ET ÇA SE DÉCLARE

Le montage prévoyait un UAV. **Il ne pouvait pas marcher, et c'est mesuré.**

| engin | montages essayés | `knowsAbout` sur l'ennemi |
|---|---|---|
| AR-2 Darter | alt 50 et 100 m, combatMode BLUE et YELLOW | **0** sur les 4 |
| MQ-4A Greyhawk | en vol libre, puis **cloué à 148 m juste au-dessus** (`dist2D` = 0) | **0** sur les 2 |
| Hummingbird à équipage IA | alt 80 m | **0,91 à 20 s, puis 2,87 à 25 s** |

Étalon dans les trois : un fantassin ami à 300 m, face à l'ennemi, qui monte à **2,87 en 10 s**.
L'ennemi est donc bien détectable — vérifié séparément dans ses trois états de bridage, `disableAI
"ALL"` compris. **Ce n'est ni la cible ni la méthode de lecture : c'est l'engin.**

> **Fait à retenir, indépendamment de ce contrôle : dans Arma, un drone ne donne RIEN à l'IA.**
> Son capteur alimente le terminal d'un opérateur humain, pas la base de connaissance des unités.

L'observateur aérien est donc joué par un **hélicoptère à équipage IA, non armé**. C'est le seul
moyen d'avoir un œil ami en l'air qui perçoive, donc le seul moyen de **poser** la question de la
fuite. Ce que le contrôle mesure devient : *un observateur aérien ami qui voit transmet-il tout
seul à l'escouade au sol ?* — et non plus *un UAV le fait-il*, question désormais close par les
diagnostics ci-dessus.

| bras | observateur aérien | tuyau `reveal` | ce qu'il répond |
|------|-------|----------------|-----------------|
| **A0** | absent | coupé | l'escouade est-elle vraiment aveugle ? |
| **A1** | présent, il voit | **coupé** | le moteur transmet-il **tout seul** ? |
| **B**  | présent, il voit | **niveau 4, toutes les secondes** | le canal existe-t-il ? |

Fenêtre d'observation : **30 s** par bras. 20 répétitions. ~45 min.

**Choix assumé — en bras B on révèle la VÉRITÉ TERRAIN, pas ce que le drone perçoit.** Le
contrôle doit juger le CANAL. Passer par `nearTargets` mêlerait « le tuyau marche-t-il » et « le
drone voit-il », et un échec ne saurait pas dire lequel des deux a lâché. La perception du drone
est mesurée à part, comme condition de lecture (ci-dessous).

## LA MESURE — l'ACTE, jamais l'ÉTAT

⟨Règle 16⟩ On compte les **`Fired`** de l'escouade au sol, et le **temps au premier tir**.
`knowsAbout` est **journalisé pour le diagnostic, et n'entre dans aucune porte** — c'est
exactement l'état qui a fait mentir six sondes en une journée.

## LES PORTES — écrites avant

> **P1 · Le canal existe.** Bras B : **≥ 18 répétitions sur 20** portent au moins un `Fired`,
> **et** la médiane du temps au premier tir est **≤ 8 s**.
>
> **P2 · L'escouade est bien aveugle sans lui.** Bras A0 : **≤ 2 répétitions sur 20** portent un
> `Fired`.

Les deux portes sont sur l'acte, appariées par scène, et posées **avant** toute lecture.

## LA LECTURE — le bras A1, qui n'a pas de porte

A1 n'est pas jugé, il est **lu**, et il ne se lit qu'après P1 et P2 :

- **A1 ≈ A0** → le moteur ne transmet pas tout seul. Le témoin est propre, le tuyau mesure
  quelque chose, le banc drone peut se construire.
- **A1 ≈ B** → **le moteur transmet déjà seul.** La « connexion drone-soldat » existe sans une
  ligne de script, et tout banc qui compare avec/sans `reveal` compare une chose à elle-même.
  Le tuyau est à jeter et la question change : elle devient « que coûte le drone », pas « que
  donne le lien ».
- **entre les deux** → INDÉCIS. On ne relance pas une deuxième sonde le même jour ; on dépose
  l'indécision.

## CONDITION DE LECTURE DE A1 — sinon A1 ne vaut rien

> **Le drone doit VOIR.** `(driver drone) knowsAbout ennemi ≥ 1.5` sur **≥ 18 répétitions sur
> 20** en A1.

Si le drone ne perçoit pas, A1 ≈ A0 est une trivialité — rien ne fuit parce que rien n'est su —
et **on ne peut pas conclure que le moteur ne transmet pas**. Dans ce cas A1 est **VOID**, et
c'est le capteur du drone qu'il faut réparer avant tout le reste.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **P1 tombe** (bras B ne tire pas) → **`reveal` n'est pas le canal**, ou l'escouade ne peut pas
  tirer. L'instrument est mort, et rien d'autre ne se lit ce jour-là. C'est l'issue que je
  crains, et c'est pour ça qu'elle est écrite avant.
- **P2 tombe** (bras A0 tire) → l'angle mort ne tient pas dans ce montage. **La scène est mal
  posée**, pas le tuyau : l'escouade voit derrière elle, et les trois bras sont sans objet.
- **L'ennemi tire** (compteur `Fired` de l'ennemi > 0 sur une répétition) → la répétition est
  **VOID** : le bruit du coup donne une détection native et pollue le bras. Compté et déclaré,
  jamais effacé.
- **La ligne de vue n'est pas trouvée** en 12 azimuts → la répétition est **VOID**, déclarée.
- **Plus de 4 répétitions VOID sur 20** → le montage n'est pas assez propre, on ne lit pas.

## CE QUE CE CONTRÔLE NE PROMET PAS

Qu'un drone paie. Qu'une courbe latence×niveau ait un sens. Que le banc sache payer
l'information — le verdict de l'oracle à 10/20 dit plutôt le contraire, et c'est une **porte
séparée**, à franchir après celle-ci.

## PAS DE PONT

La sonde est autonome dans la mission : elle écrit dans le RPT et ne dépend d'aucun client
Python. Le pont meurt en service après 20-40 min ; une sonde de 45 min ne pouvait pas en
dépendre.
