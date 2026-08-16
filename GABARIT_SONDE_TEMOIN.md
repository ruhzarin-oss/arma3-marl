# Gabarit de sonde — pourquoi le témoin du prévol est infirme

⟨Fable, 16/08⟩ *« Le premier pari est gratuit, le deuxième s'achète avec une sonde. »*
Premier constat de cette panne → une seule passe, quatre causes discriminées d'un coup.

## Le symptôme, brut

Le témoin jetable du prévol, posé par `HMT_POSER_HOMME` en mode `pilote` à 300 m :
**`T4 AUCUNE BALLE REELLE (0 en 6 s)`** et **`T5 IMMOBILE : 8 m en 4 s (attendu ~24)`**.
Reproductible sur deux épisodes. Les hommes du banc, eux, tiraient 145 coups et
parcouraient 154 m hier, mêmes `disableAI`, même `combatMode RED`.

## Les causes candidates (4 au plus)

1. **le lieu** — 300 m au hasard : eau, forte pente, ou obstacle ;
2. **le mode** — le `pilote` du socle diffère de ce que la scène pose réellement ;
3. **le groupe** — le témoin est seul dans un groupe neuf, sans chef ni ordre ;
4. **la cible** — le mannequin à 45 m n'est jamais acquis, donc rien à engager.

## LA SONDE — une seule passe

Poser **côte à côte** un témoin **exactement comme le socle le pose** et un attaquant
**exactement comme la scène le pose**, puis mesurer sur les deux les **mêmes cinq
grandeurs** : arme en main, coups tirés en 6 s, mètres parcourus en 4 s sous `setVelocity`,
hauteur du terrain sous les pieds, et l'état réel de `FSM`/`AUTOCOMBAT`/`PATH`.

## La « balle réelle » de chaque cause ⟨la clause de Fable⟩

Chaque hypothèse a une observation qui reviendrait **positive si elle était vraie** :

| cause | ce qu'on verrait si elle est la bonne |
|---|---|
| 1. le lieu | hauteur ≤ 0 ou pente forte sous le témoin, normale sous l'attaquant |
| 2. le mode | `FSM`/`AUTOCOMBAT`/`PATH` diffèrent entre les deux |
| 3. le groupe | les deux identiques sur tout, seul le groupe change → la panne suit le groupe |
| 4. la cible | le témoin tire quand on lui donne un ennemi de la scène au lieu du mannequin |

## Ce qui rendrait la sonde muette

Si **les deux** échouent, ce n'est pas le témoin qui est infirme mais la scène entière —
et alors le prévol avait raison de tout bloquer.
