# ÉTAT — LA PORTE ORACLE EST MONTÉE, NON JOUÉE, ET PORTE UN DÉFAUT CONNU

*17 août 2026, arrêt demandé. Aucune répétition retenue. **Rien n'est mesuré, rien n'est
lu, rien n'est acquis** sur la question « le banc sait-il payer l'information ».*

## CE QUI EXISTE ET TOURNE

| pièce | chemin |
|---|---|
| critères déposés avant | `CRITERES_PORTE_ORACLE.md` |
| la sonde | `bancs/arma/porte_oracle.sqf` |
| lanceur (instance dédiée, port 6086) | `bancs/lancer_porte_oracle.sh` |
| superviseur avec relance | `bancs/collecte_porte_oracle.sh` |
| lecteur, seuils en dur | `lire_porte_oracle.py` |
| journaux partiels | `journaux/porte_oracle_*_17082026*` |

Le montage tourne : trois bras appariés (FORCÉ-TENU / AVEUGLE / ORACLE), une décision unique
— par quel axe passer —, jugement sur prise + exposition par mètre.

## ⛔ LE DÉFAUT À RÉPARER AVANT TOUTE LECTURE — la CENSURE par le plafond

Relevé par Younes, et il a raison : une répétition qui atteint le plafond de temps est
comptée **non-prise**, alors qu'elle n'a pas été *perdue* — elle a été **interrompue**.

**Ce n'est pas neutre entre les bras.** Un combat qui dure est précisément ce qui arrive au
bras qui tombe sur la planque. Le plafond pénalise donc mécaniquement FORCÉ-TENU et AVEUGLE
plus qu'ORACLE, et **gonfle artificiellement l'écart que la porte doit mesurer**. La porte
mesurerait en partie ma durée d'observation, pas la valeur de l'information.

**Réparation exigée avant de rejouer :**
1. **Journaliser la CAUSE DE FIN** de chaque bras : `PRIS` / `TOUS_MORTS` / `PLAFOND`.
2. **Condition de lecture déposée avant** : le plafond ne doit mordre que rarement — à écrire
   comme un seuil chiffré, au même titre que P1 et P2.
3. Si le plafond mord souvent, ce n'est pas le seuil qu'on desserre : c'est **le monde** qu'on
   re-dimensionne (distance de départ, effectif de la planque), et on le déclare.

⚠️ Sans cette réparation, **aucun chiffre de cette porte ne doit être cité**, même favorable.

## L'HISTORIQUE DES DIMENSIONNEMENTS, pour ne pas le redécouvrir

- **150 s, marche `COMBAT`/`NORMAL`** → prise = 0 partout sur 5 répétitions. Le bras ORACLE
  traversait pourtant proprement (`expo 0`, 4 survivants sur 4) mais s'arrêtait à 146 m sur
  200 : les hommes rampent à ~1 m/s pour un trajet en deux jambes de ~460 m. Branche
  « objectif injouable », prévue au dépôt. 5 répétitions **jetées**.
- **280 s, marche `AWARE`/`FULL`** → relancé, puis **arrêté avant toute répétition complète**.

## CE QUE CES ESSAIS ONT QUAND MÊME MONTRÉ (à confirmer, non certifié)

La géométrie **sépare bien les deux axes** : une répétition a vu l'axe libre traversé avec
`expo 0` et 4 survivants sur 4, pendant que l'axe tenu tuait les 4 hommes en 22 mètres, avec
une exposition de 3,71 par mètre gagné. Il y a donc bien **quelque chose à acheter** — la
précondition a de bonnes chances de passer une fois le monde jouable.

## LE PROCHAIN PAS, QUAND ON REPRENDRA

1. Ajouter la cause de fin à la sonde.
2. Amender les critères : seuil chiffré sur la fréquence du plafond, **déposé avant**.
3. Rejouer 20 répétitions.
4. Ne lire qu'après : précondition, puis porte.
