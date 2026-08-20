# DOSSIER DOCTRINE — LE TEMPO DU CORPS

> # ⛔ VERSION DU 19/08 : RETIRÉE POUR PRÉMISSE FAUSSE
>
> **Elle affirmait que « le gymnase enseigne 6 m/s ». C'est faux, et je ne l'avais jamais lu.**
> Le 6 m/s est la **consigne envoyée à Arma** par la couture (`arma_couture.py:21`), dont le
> commentaire dit lui-même pourquoi : *« le sandbox move=14/pas ; on tempère pour le FPS »*.
> **J'ai pris la consigne du pont pour le paramètre du gymnase**, et bâti un arbitrage à trois
> branches dessus. L'écart annoncé — 60 % — était surestimé d'un facteur dix.
>
> ⚠️ **Cliquet : avant de chiffrer un écart entre deux mondes, LIRE le paramètre de chacun.**
> J'ai mesuré Arma pendant deux jours sans jamais ouvrir le fichier du gymnase.

---

**Corrigé le 20/08/2026, après lecture du code.**

## CE QUE LE GYMNASE JOUE VRAIMENT

| | source | valeur |
|---|---|---|
| distance d'un pas | `assault_terrain.py:13` — `move=14.0`, **non surchargé** par `monde_fidele` | **14 m** |
| durée d'un pas | `monde_fidele.py:27` — `SEC_PAR_PAS`, dérivé par `leviathan/mesurer_vitesse.py` | **3,28 s** |
| **vitesse effective** | 14 / 3,28 | **4,27 m/s** |

## CE QUE LE CORPS REND, SUR LE CANAL ADOPTÉ

| régime | distance en 4 s | vitesse | part du terrain |
|---|---|---|---|
| **montée** | 15,0 m | **3,75 m/s** | ~57 % (150/261) |
| **descente** | 22,1 m | **5,5 m/s** | ~43 % (111/261) |
| **mélange pondéré** | — | **≈ 4,5 m/s** | — |

## L'ÉCART RÉEL

> **Gymnase 4,27 m/s contre 4,5 m/s mesurés : environ 5 %.**

Et ce n'est pas un hasard : `SEC_PAR_PAS` a été **dérivé d'une vitesse mesurée sur Arma**, sur
des lieux tirés au hasard — donc sur le même mélange des deux régimes. **Le gymnase était déjà
calibré**, et il l'était bien.

> ### ⛔ IL N'Y A PAS DE RECALAGE À FAIRE. L'ARBITRAGE À TROIS BRANCHES EST SANS OBJET.
> Aucun réentraînement n'est justifié par le tempo.

## LE VRAI SUJET, QUI SUBSISTE ET QUI EST AUTRE

**Dans le gymnase, la pente n'agit pas sur le déplacement.**
Elle est dans l'**observation** — l'agent la voit (`slope`, mesurée sur Stratis : p01 0,000,
médiane 0,408, p99 1,057) — mais le pas fait **14 m qu'on monte ou qu'on descende**. La seule
modulation du déplacement est le **frein sous le feu** (`frein_feu=0.35`).

Or Arma sépare nettement les deux régimes — **3,75 contre 5,5 m/s, soit 1,47×** — et
l'**intervention** l'établit causalement : marcher vers le sud inverse le régime, 3 fois sur 3
dans les deux sens.

**La question n'est donc pas « à quelle vitesse », mais :**

> **Faut-il que le gymnase fasse SUBIR la pente qu'il MONTRE déjà ?**

| | pour | contre |
|---|---|---|
| **laisser tel quel** | le tempo moyen est juste à 5 % ; rien à réentraîner ; l'agent voit la pente et peut l'exploiter par apprentissage | il apprend qu'un versant se traverse au même prix dans les deux sens — **la descente est gratuite, la montée aussi** |
| **faire subir la pente** | le coût du terrain devient réel : contourner, choisir son axe, préférer la descente deviennent des décisions **payantes** | **c'est un terme NEUF** dans le modèle de déplacement, pas un réglage — donc à mesurer, pré-inscrire, et il invalide les politiques existantes |

⚠️ Ce n'est **pas** un problème de fidélité de vitesse. C'est un problème de **fidélité de
décision** : un agent qui ne paie pas la pente n'a aucune raison d'apprendre à la lire, même
s'il la voit.

## CE QUI SERAIT NÉCESSAIRE AVANT DE TRANCHER

1. **Mesurer proprement les deux régimes** sur le canal adopté : n ≥ 50 par régime,
   pré-inscription, témoin — mes chiffres actuels tiennent sur **6 lieux par régime**.
2. **Établir la forme du terme** : la pente le long du pas, pas la pente au point (c'est la
   faute de fenêtre qui a tué trois dérivations le 19/08).
3. **Un témoin sans terme** : la politique entraînée avec la pente qui coûte doit **battre**
   celle entraînée sans, sur le même banc — sinon le terme n'a rien apporté.

**Rien de cela n'est urgent.** Le tempo moyen est juste ; c'est une question de qualité de
décision, pas de panne.
