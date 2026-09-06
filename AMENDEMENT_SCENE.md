# AMENDEMENT — LA SCÈNE DE LA PORTE D'ADOPTION, CHOISIE AVANT LES RÉSULTATS

**Déposé le 27/08/2026, avant de relancer la greffe.** Amende `DEPOT_GREFFE_ARMA.md`
(`f2909ef959c36655`), dont tous les seuils et contrôles restent inchangés.

## POURQUOI LA SCÈNE CHANGE
Le premier passage a rendu **7,50 survivants dans les TROIS bras**, à 0,00 près. Ce n'était
pas « ils se valent » : **le banc ne séparait pas.** Sur 16 hommes, il mourait 1 à 2 amis, donc
la métrique déposée (survivants amis) ne prenait que deux valeurs.
⚠️ Mon garde-fou anti-dégénérescence était **trop étroit** — il ne testait que « les trois à
8,0 », pas la variance. Huitième erreur d'instrument du dossier, même famille que les sept
autres : confondre « pas de signal » et « résultat nul ».

## CE QUE LE PREMIER BALAYAGE A TROUVÉ, ET CE N'ÉTAIT PAS CE QUE JE CHERCHAIS
Huit configurations (distance × compétence × durée) : **aucune recevable**, maximum 2 morts
amis sur 8. La cause n'était **ni la durée, ni la distance, ni la compétence** :

| configuration | bleus | rouges |
|---|---|---|
| d=120 skill=0,5 t=240s | **8** | **0** |

**Les bleus gagnaient 8 à 0.** Deux groupes symétriques qui se ruent l'un sur l'autre ne
coûtent rien à l'attaquant. Le problème était le **RAPPORT DE FORCES**, et accessoirement ma
métrique : mesurer les survivants amis dans un combat gagné 8-0 ne discriminera jamais.

## LE SECOND BALAYAGE — le rapport de forces et le RETRANCHEMENT
| configuration | bleus/8 | rouges | morts amis | |
|---|---|---|---|---|
| d=150, 12 rouges, mobiles | 5 | 9 | 3 | |
| d=150, 12 rouges, **RETRANCHÉS** | 2 | 11 | 6 | ✅ |
| d=150, 20 rouges, mobiles | 1 | 20 | 7 | ✅ |
| **d=150, 20 rouges, RETRANCHÉS** | **3** | 19 | 5 | ✅ |
| d=250, 12 rouges, mobiles | 3 | 12 | 5 | ✅ |

⭐ **Le retranchement est le levier** : à distance et effectif identiques, il fait passer les
morts amis de 3 à 6. Des défenseurs qui tiennent une position **font payer l'approche** ; des
mobiles ne font que converger. C'est exactement la structure du gymnase — et c'est ce qui rend
les deux mondes comparables.

## LA SCÈNE RETENUE, ET POURQUOI CELLE-LÀ
> **d=150 m · 20 rouges RETRANCHÉS (`setUnitPos "DOWN"` + `disableAI "PATH"`) · skill 0,7 · 180 s**

**Ce n'est PAS la plus meurtrière.** Elle laisse **3 survivants sur 8** — le plus de place
**dans les deux sens** : une bonne politique peut monter, une mauvaise peut descendre. À
1 survivant sur 8 (20 rouges mobiles), le plancher est trop proche et la métrique sature
par le bas.
> Même principe que partout ailleurs dans ce dossier : **une métrique qui sature ne discrimine
> pas, qu'elle sature en haut ou en bas.**

## LE GARDE-FOU EST ÉLARGI
L'ancien : « les trois bras à 8,0 » → dégénéré. Le nouveau : **si l'étendue des trois moyennes
est inférieure à 0,25 survivant, le banc est déclaré NON SÉPARANT et aucun verdict n'est
rendu** — quelle que soit la valeur commune.

## CE QUI NE BOUGE PAS
Critère principal **survivants amis** · succès `greffe − nu ≥ +1,0` **et** `greffe − permuté
≥ +0,5` · échec sous +0,3 · contrôle à **prix permuté retiré à chaque décision** · budget
comptant le corpus · deux graines minimum.
