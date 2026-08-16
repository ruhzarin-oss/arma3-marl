# DÉPÔT — L'INSTRUMENT EST CERTIFIÉ (tentative n° 2)

*16 août 2026, 22 h 25. 20 répétitions valides sur 20, **aucune VOID**, un seul et même monde
(`socle 1.10.0-16082026`). Portes et condition de validité déposées avant lancement dans
`CONTROLE_POSITIF_DRONE_2.md`. Tentative n° 1 : échec, elle le reste.*

## LE RÉSULTAT

| bras | ont tiré | part | médiane du 1ᵉʳ tir |
|---|---|---|---|
| **A0** — sans `reveal` | **2/20** | 10 % | 17,8 s |
| **B** — `reveal` niveau 4 | **20/20** | 100 % | **3,2 s** (bornes 1,8 – 4,6) |

> **P1 · le canal existe** — B ≥ 18/20 et médiane ≤ 8 s → **PASSE**
> **P2 · aveugle sans lui** — A0 ≤ 2/20 → **PASSE**

## LA PRÉDICTION DE LA RÉPARATION EST VÉRIFIÉE

Il était écrit avant lancement que si la réparation était la bonne, le témoin d'ouverture
serait **nul sur 20/20 dans les deux bras**. Observé : **20/20**. La tentative n° 1 en
comptait 3 sur 20 en A0 et 1 sur 20 en B.

**Les 30 s d'attente étaient bien la cause**, et elles n'existaient que pour un observateur
aérien dont on a démontré par ailleurs qu'il n'avait pas lieu d'être. La réparation touchait
la scène ; les seuils n'ont pas bougé d'un point.

## ⚠️ P2 PASSE AU RAS DU SEUIL — à dire, pas à arrondir

A0 est à **2/20 pour un plafond de 2/20**. Ça passe, ce n'est pas confortable.

Les deux répétitions concernées (n° 8 et 10) ont un témoin d'ouverture **nul** : ce sont de
vraies détections tardives *pendant* la fenêtre — premier tir à **28,4 s** et **7,3 s**, à
comparer aux 0,1-2,5 s de la tentative n° 1, qui trahissaient un savoir antérieur. La nature
du reliquat a donc changé : ce n'est plus un artefact de montage, c'est la détection native
résiduelle d'une escouade à 300 m sur 30 s. Elle est irréductible sans changer le monde.

**Conséquence à tenir** : tout banc bâti là-dessus doit supporter ~10 % de détection native
dans son bras témoin, ou allonger la distance. Ce n'est pas un défaut caché, c'est le prix
mesuré de la scène.

## CE QUI EST CERTIFIÉ, ET DANS QUELS TERMES

`reveal` fait tirer, en ~3 s, une escouade en mode `natif` qui sans lui ne tire pas —
sans aucun `forceWeaponFire`, l'IA décidant seule. Le contrôle positif à deux moitiés
exigé par la règle 16 est franchi : le lien coupé ne tire pas, le lien branché tire vite.

⛔ **Ce que ça ne certifie pas** : qu'un drone paie, ni que le banc sache payer
l'information. **La porte oracle reste entière et n'est pas dans ce dépôt.**

## LA REQUALIFICATION QUE CE TRAVAIL IMPOSE AU PROJET

Le moteur n'ayant **aucun canal drone→IA** (UAV `knowsAbout` = 0, y compris cloué à 148 m
au-dessus de la cible), `reveal` ne sonde pas un mécanisme du monde : **il EST la liaison
drone, écrite à la main**. Le banc n'observera donc pas un drone simulé — il implémentera une
hypothèse de liaison, dont le **niveau, la cadence et la latence sont des paramètres de
modèle** à justifier, et à calibrer sur l'étalon d'infanterie : **2,87 en 10 s à 300 m**.

⟨Fable⟩ *« Dans Arma, un drone est un décor plus un script. »*

La question de départ se reformule : non plus « que vaut le lien contre ce que coûte le
drone », mais **« quel est le rendement et le prix d'une information injectée »**. Le bras
muet garde son objet, mais du côté **adverse** : le drone reste un objet physique que
l'ennemi peut percevoir.

## PROCHAIN PAS

La porte oracle, sur un banc qui contienne une **décision consommatrice d'information** —
la première des trois exigences de Fable, toujours pas jouée. Jugement sur **prise +
exposition par mètre gagné**, jamais sur les éliminations. Dépôt séparé, écrit avant.
