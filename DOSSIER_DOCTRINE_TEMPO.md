# DOSSIER DOCTRINE — LE TEMPO DU CORPS. Arbitrage de Younes.

**19/08/2026.** Fondé sur `VERDICT_LA_PENTE_DANS_LE_SENS_DE_LA_MARCHE.md`.
Ce document ne tranche pas : il pose les trois branches avec leurs chiffres.

## LE FAIT

Le canal de locomotion de la campagne (`arma_couture.py:185`, `setVelocity [vx, vy, 0]`
réémis à 10 Hz) **annule la composante verticale**. Conséquence mesurée :

| | ce que le canal rend | part du terrain concernée |
|---|---|---|
| **en montée** | **2,8 – 3,7 m/s** | ~57 % des lieux échantillonnés (150/261) |
| **en descente** | **5,5 – 6,4 m/s** | ~43 % (111/261) |

**Le gymnase entraîne à 6 m/s uniformes.** Il est donc juste sur les descentes et
**optimiste d'un facteur ~1,8 sur les montées** — c'est-à-dire sur la majorité du terrain.

⚠️ Ce n'est pas une erreur de simulation : c'est une **incohérence entre ce que la politique
apprend et ce que son corps peut faire**. Une politique qui planifie « j'y serai en 4 s »
arrive en 7 s une fois sur deux, et son plan est faux au moment où il compte.

## BRANCHE 1 — RENDRE LA GRAVITÉ AU CANAL, RECALER LE GYMNASE SUR LE SOL

`setVelocity [vx, vy, (velocity _u)#2]` — la forme qu'emploient déjà `squad_deploy*.py` et
les théâtres LEVIATHAN. Puis recaler le tempo du gymnase sur la capacité mesurée au sol.

- **Pour** : le corps devient physique et cohérent ; les soldats cessent de traverser
  les ravins en ligne droite ; le gymnase enseigne un tempo atteignable.
- **Contre** : **tout ce qui a été appris jusqu'ici l'a été sur l'autre corps.** Les
  politiques déployées, le commandant appris, SHAMAL, ALIZÉ — leur tempo est calibré sur
  6 m/s. Il faut réentraîner.
- **Prédiction à pré-enregistrer** : rendre le vz **n'empêchera pas** les décollages (le
  terrain déclenche toujours), il les transformera en **sautillements courts** — fraction
  de vol faible, distances en descente qui se rapprochent des distances en montée.
- **Coût** : un réentraînement complet. Le plus cher, le plus propre.

## BRANCHE 2 — GARDER Z=0 ET L'ASSUMER

Ne rien changer, et **écrire noir sur blanc** que les soldats du projet planent dans les
descentes.

- **Pour** : coût nul, rien à réentraîner, tous les acquis restent lisibles.
- **Contre** : c'est un **écart de fidélité de plus** — famille du couvert ×11 et de la
  létalité ×4. Et il est **directionnel**, donc il biaise la tactique elle-même : descendre
  devient gratuit, monter devient cher. Les manœuvres apprises exploiteront ce biais.
- **Conséquence pour le doctorat et la vente** : un dossier VV&A qui déclare un corps
  non physique se défend mal devant un client de simulation.

## BRANCHE 3 — RALENTIR LE GYMNASE À LA CAPACITÉ RÉELLE, SANS TOUCHER AU CANAL

Garder `Z=0` mais commander ~3,5 m/s au lieu de 6.

- **Pour** : le tempo appris devient atteignable **partout** (3,5 m/s est sous le plafond
  des deux régimes) ; un seul paramètre change ; pas de refonte du canal.
- **Contre** : on **plafonne volontairement** le corps en descente là où il pourrait aller
  deux fois plus vite ; et l'incohérence physique reste (le vz est toujours annulé).
- **C'est le compromis** : le moins cher qui supprime le mensonge de tempo.

## CE QUI NE DÉPEND PAS DE L'ARBITRAGE

Le **critère neuf du placeur** doit se dériver de la capacité **mesurée du canal retenu** —
jamais des 6 m/s du gymnase. Il ne peut donc pas s'écrire avant la décision. D'ici là :
**bloc C désactivé, aucune porte lancée.**

## CE QUE JE RECOMMANDE

**Branche 1**, pour une raison qui n'est pas de fidélité mais de but : l'objectif est un
agent qui **comprend et joue** Arma. Un agent dont le corps traverse les ravins n'apprend
pas le terrain — il apprend une carte plate avec des raccourcis. Le coût du réentraînement
se paiera de toute façon, et il est plus petit aujourd'hui qu'après la prochaine campagne.
