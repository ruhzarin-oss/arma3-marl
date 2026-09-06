# LA MÉTRIQUE DÉCOUVERTE — déposée avant la première donnée, 27/08/2026

## LE CHANGEMENT D'OBJECTIF, ET POURQUOI CE N'EST PAS DU MAGASINAGE
⟨Younes⟩ *« On s'en fout que les soldats meurent. Ce qu'on veut, c'est qu'ils AGISSENT, qu'ils
BOUGENT, qu'ils DÉCOUVRENT, et que ce soit PILOTÉ PAR LE LLM. »*

Changer de MÉTRIQUE après avoir vu un résultat est du magasinage. Changer d'OBJECTIF est la
prérogative de Younes. ⟨Fable, vérification sur pièces⟩ : **la couche 5 est dans la mission
depuis le premier jour** ; les trois jours de négatifs n'ont pas motivé une fuite, ils ont
**fermé les couches du dessous** — perception saturée, crédit clos, marge du choix nulle au
gymnase. **C'est un retour au but déposé, pas un déplacement.**
> Et la bascule ne devient du magasinage que dans un cas : **si le nouvel objectif n'a pas de
> mesures capables d'échouer, déposées avant le premier appel au LLM.** D'où ce fichier.

## LA GRANDEUR PRIMAIRE — UNE SEULE
> **DÉCOUVERTE = nombre d'ennemis LOCALISÉS qui ne l'étaient pas au début de l'épisode.**

Vérité-terrain **gratuite** : le serveur connaît toutes les positions. Un ennemi est « localisé »
si `west knowsAbout _e > 1,5` — le seuil qui, dans les journaux, sépare l'observé du supposé.
· **Elle sait échouer** : zéro se produit, et se produira.
· **Elle n'est pas pompable par l'agitation** : c'est ce qui l'a fait préférer à « part du temps
  actif » et « nombre de gestes distincts », **refusées comme mesures** ⟨Fable⟩ — *« un
  tourniquet agit beaucoup et découvre rien »*. Elles restent DESCRIPTIVES, incapables de valider.

## LA MORT CHANGE DE STATUT : DE SCORE À COÛT
Colonne obligatoire à côté : **découverte par homme perdu**. Une escouade morte en 90 secondes
cesse de découvrir. **La survie redevient un instrument, plus jamais un objectif.**

## LES TÉMOINS — et l'un d'eux existe pour tuer le théâtre
· **plancher** : escouade FIGÉE (aucun ordre, `disableAI PATH`) ;
· **natif seul** : l'IA d'Arma sans aucun ordre de notre part ;
· ⭐ **ORDRES ALÉATOIRES** : mêmes exécutants, mêmes cadences, destinations tirées au hasard.
  ⟨Fable⟩ *« L'ordre aléatoire est le témoin qui tue le théâtre — car lui aussi s'affaire. »*
  **Aucune phrase sur l'officier ne se prononcera autrement que « il bat les ordres aléatoires
  et le natif seul, sur la découverte, à n dimensionné ».**

## EXIGENCE STRUCTURELLE — RANDOMISER LES ENNEMIS À CHAQUE ÉPISODE
Sinon le LLM « découvre » une scène apprise par cœur. Positions tirées à chaque épisode dans
un anneau autour du départ, jamais un dispositif fixe.

## LA FAMILLE DE SCÈNES — celle de la RECONNAISSANCE, pas celle de l'assaut
⚠️ **La scène calibrée à 3 survivants sur 8 est la MAUVAISE scène ici** ⟨Fable⟩ : elle a été
dimensionnée pour un assaut, où l'on meurt vite. Pour la découverte il faut de l'espace et du
temps. Famille déposée : **8 bleus · 12 ennemis dispersés dans un anneau de 200 à 500 m ·
skill 0,6 · 6 minutes**. Recevabilité, mesurée avant tout verdict :
> **une scène est recevable si le natif seul découvre entre 2 et 9 ennemis sur 12** — sous 2,
> la métrique sature en bas ; au-dessus de 9, en haut. Même principe que partout ailleurs.

## LES SEUILS — NON FIXÉS ICI (règle 3)
**Aucun seuil ne se dépose sans le couple « plancher de bruit mesuré · n requis ».** Le
plancher se mesure par **12 répétitions du MÊME bras** dans la même famille de scènes, et le
tableau graines↔effet détectable en sortira. Tant qu'il n'existe pas, aucune comparaison n'est
recevable.

## L'ORDRE, ET IL N'EST PAS NÉGOCIABLE
1. plancher de bruit de la découverte ; 2. recevabilité de la famille de scènes ;
3. **marge du choix sur Arma** — oracle du choix moins meilleur exécutant fixe ;
4. **et SEULEMENT si la marge dépasse l'effet détectable**, brancher le 7B.
⛔ **Brancher le LLM avant la porte 3 est interdit.** ⟨Fable⟩ *« Ce verdict-là doit pouvoir
tomber, sinon toute la suite est du théâtre. »* Au gymnase la marge du choix valait **+1,0** —
un officier n'y avait rien à décider. **Sur Arma elle n'a jamais été mesurée.**

---

# LE PLANCHER EST MESURÉ, ET LA MARGE DU CHOIX EST DÉPOSÉE — 27/08, 22h20

## LE PLANCHER DE BRUIT — 12 épisodes du bras `natif`, ennemis retirés à chaque fois
**moyenne 7,42 / 12 · écart-type 1,78 · étendue [4 ; 10]**
Pertes moyennes **5,33 / 8** · **découverte par homme perdu 1,84**.
→ **SCÈNE RECEVABLE** au critère déposé (natif entre 2 et 9) : la métrique ne sature ni en
haut ni en bas et varie d'un épisode à l'autre.

⭐ **La colonne « par homme perdu » sert DÉJÀ** : l'épisode 0 fait **7 découvertes pour 0
perte**, l'épisode 3 fait **9 pour 8 morts**. Sans elle, on classerait le 3 comme le meilleur.
La mort n'a pas disparu — **elle est devenue le prix.**

## LE SEUIL, DIMENSIONNÉ (règle 3) — plus jamais choisi
| épisodes par bras | effet détectable à 95 % |
|---|---|
| 2 | +3,53 |
| 8 | +1,76 |
| **16** | **+1,25** |
| 32 | +0,88 |
**RETENU : 16 épisodes par bras → +1,25 découverte.** Rappel de la faute que ça répare : le
banc précédent déposait +1,0 avec 2 graines pour un bruit de 1,57 — **trois fois sous le
plancher**, et trois verdicts n'ont rien voulu dire.

## LA MARGE DU CHOIX SUR ARMA — la porte avant tout LLM
> **oracle du choix (le meilleur exécutant par scénario) MOINS le meilleur exécutant FIXE.**

Au gymnase elle valait **+1,0 point** : un officier n'y avait **rien à décider**, ce qui a
fermé la couche 5 là-bas. **Sur Arma elle n'a jamais été mesurée.**

**LES CINQ EXÉCUTANTS** — nommés, énumérables, c'est le vocabulaire que l'officier aurait :
`ASSAUT` (doMove vers l'ennemi connu) · `PATROUILLE` (points de passage en anneau) ·
`ÉVENTAIL` (dispersion, chacun son secteur) · `TENIR-ET-OBSERVER` (fixe, `AWARE`) ·
`RECHERCHE-COUVERT` (progression d'un point haut à l'autre).

**LES DEUX TÉMOINS OBLIGATOIRES** : `natif` seul · ⭐ **`hasard`** — mêmes ordres, mêmes
cadences, destinations tirées au hasard. *L'ordre aléatoire est le témoin qui tue le théâtre,
car lui aussi s'affaire.*

**LA LECTURE, ÉCRITE AVANT :**
· **marge ≥ +1,25** (l'effet détectable à 16 épisodes) → **l'officier a un métier**, et
  seulement alors on branche le 7B ;
· **marge < +1,25** → **il n'a rien à décider sur Arma non plus**, le 7B reste débranché, et on
  l'aura su pour une nuit au lieu de trois semaines ;
· et **aucun exécutant ne se cite s'il ne bat pas `hasard`** — un exécutant battu par des
  destinations aléatoires n'est pas un geste, c'est de l'agitation.

⛔ **Brancher le LLM avant cette porte reste interdit.** ⟨Fable⟩ *« Ce verdict-là doit pouvoir
tomber, sinon toute la suite est du théâtre. Tu as tenu neuf fois l'ordre instrument-avant-
verdict ; c'est la dixième qui décide si la méthode a tenu ou si elle attendait qu'on
s'amuse. »*
