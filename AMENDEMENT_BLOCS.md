# AMENDEMENT — LES SIX RÉPARATIONS DU BANC DE MARGE. Déposé 27/08, 22h45, run PRÉCÉDENT ARRÊTÉ

Le protocole lancé à 22h18 est **arrêté au premier bras** et son journal archivé sous
`marge_arma_PROTOCOLE_FAUX.log`. Aucun verdict n'en sortira.

## ⭐ LE DÉFAUT PRINCIPAL, QUE JE N'AVAIS PAS VU — IL N'Y AVAIT PAS DE BLOCS
⟨Fable⟩ *« Les placements sont retirés à chaque épisode, donc ton oracle choisira PAR ÉPISODE :
il ramassera les épisodes chanceux de chaque bras. Le max sur 7 bras d'un bruit à écart-type
1,78 fabrique une marge de plusieurs points tout seul. »*

**Le banc aurait rendu une marge POSITIVE PAR CONSTRUCTION, même sur du bruit pur.** C'est le
**max-de-grille**, déjà payé une fois (le 91 % lu sur ses propres graines de sélection).

**RÉPARATION — 8 SCÉNARIOS GELÉS ET NOMMÉS.** Les placements ennemis sont tirés **une fois**,
avec 8 graines fixes, et **tous les bras jouent les MÊMES 8 scénarios**. L'oracle choisit
**par scénario, sur des répliques**. L'appariement impossible au niveau des dés d'Arma est
possible **au niveau des scènes** : c'est la variance contrôlable, et on la contrôle.

## LES CINQ AUTRES
**1. `assaut` et `couvert` TRICHAIENT.** Ils lisaient `leader HMT_GO` — une vérité-terrain que
le camp bleu n'a pas, et qu'aucun officier n'aura. → remplacés par **le dernier contact CONNU
du camp** (`knowsAbout` > 1,5, qui est de camp — fait déposé du dossier), avec **repli déclaré**
quand rien n'est connu : **axe de recherche fixe** (nord du départ).
*Un assaut vers la vérité-terrain et un assaut vers le dernier contact sont deux gestes
différents, et seul le second est au menu de l'officier.*

**2. `hasard` ÉTAIT TROP FAIBLE.** Redessiner toutes les 12 s fabriquait un oscillateur qui
reste près du départ — un témoin d'agitation qui ne s'agite pas loin. → **tire une destination
et la TIENT jusqu'à l'arrivée**, puis retire. ⟨Fable⟩ *« Le témoin anti-théâtre doit être fort,
sinon il absout. »*

**3. `natif` N'EST PAS LE PLANCHER — répondu par les logs, sans lancer un bras.** Éloignement
médian du chef après 5 min : **147 m**. Il patrouille. → **bras `fige` ajouté** comme plancher.

**4. LA RÉÉMISSION TOUTES LES 12 s TUAIT LE PATHFINDING.** C'est la faute gravée dans le
dossier : *« on répétait "va au FOB" à chaque tour, le jeu recalculait en boucle, aucun geste
n'aboutissait »*. → **on n'émet QUE si `unitReady`** (ordre accompli) **ou si la destination a
changé**. Et `couvert` cumulait les deux fautes — objet tiré AU HASARD à chaque réémission,
donc oscillation entre buissons : → **le couvert est tiré UNE FOIS et gardé jusqu'à l'arrivée**.

**5. LE BRAS NUL MANQUAIT**, alors que ce banc est celui qui en a le plus besoin **puisque son
verdict est un MAX**. → **`natif_bis`** : exactement `natif`, autre étiquette, joué comme un
bras à part entière. **Si l'oracle lui trouve un avantage, le banc s'auto-invalide.**

## LA MÉTRIQUE, DÉPOSÉE MOT POUR MOT (c'était un degré de liberté ouvert)
> **DÉCOUVERTE = nombre d'ennemis DISTINCTS dont le `knowsAbout` DE CAMP (`west knowsAbout _e`)
> franchit 1,5 au moins une fois pendant l'épisode, chacun compté UNE SEULE FOIS, moins ceux
> qui le franchissaient déjà au premier tick.**

## LA DURÉE PASSE À 8 MINUTES — dimensionnée, pas choisie
Anneaux à 280-380 m, infanterie `AWARE` à 5-6 km/h → ~3 min de transit sur 5 d'épisode :
**l'épisode mesurait le trajet, pas le geste.** → **8 minutes**, et on paie en épisodes :
**12 par bras → effet détectable +1,44** (table du plancher). **La marge cible est redéposée
à +1,44 en conséquence**, pas maintenue à +1,25.

## LA LECTURE, INCHANGÉE SUR LE FOND
· **marge ≥ +1,44** → l'officier a un métier, et **seulement alors** on branche le 7B ;
· **marge < +1,44** → il n'a rien à décider sur Arma ; le 7B reste débranché ;
· **aucun exécutant ne se cite s'il ne bat pas `hasard`** ;
· **si `natif_bis` obtient un avantage à l'oracle, le banc est déclaré NON SÉPARANT** et aucun
  verdict n'est rendu.
