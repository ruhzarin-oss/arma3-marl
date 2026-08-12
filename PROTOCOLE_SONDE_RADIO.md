# LA SONDE RADIO — déposée AVANT lancement

*10 août 2026, 19 h. Le bras natif du banc de l'étage 1 a tiré 260, 206, **0**, **0** coups sur
quatre runs, dans un monde dont l'empreinte est identique. Cette sonde tranche pourquoi — **sans
toucher une ligne du banc**.*

**Fiches relues ⟨règle 10⟩** : `mesure-doit-savoir-echouer`, `accord-sur-zero-nest-pas-accord`,
`bridge-scripting-gotchas`, `arma-fps-wall-headless-clients`.

## L'ÉCHAPPATOIRE, VÉRIFIÉE ET FERMÉE

⟨Fable⟩ *« Ce qui ressusciterait "conséquence" : que le journal montre la lecture d'entrée
postérieure à l'ordre. »* Lu sur pièces : `HMT_CAP0A` est **ligne 452**, `commandSuppressiveFire`
est **ligne 480**, et sept secondes de `sleep` les séparent. **La lecture d'entrée précède
l'ordre.** L'oisiveté des appuis n'est donc pas une conséquence de l'ordre non pris : c'est un
**marqueur d'état du monde en amont**, et il désigne ma mise en place au lieu de l'innocenter.

| run | appuis prêts à l'entrée | coups du bras natif |
|---|---|---|
| session 1 | 0 sur 3 | 260 |
| session 2 | 0 sur 3 | 206 |
| session 3 | **3 sur 3** | **0** |
| relance | **3 sur 3** | **0** |

## CE QUE LA SONDE MESURE

**Grandeur : le groupe tire-t-il, oui ou non, dans la fenêtre.** Une répétition est une
**réussite** si les trois hommes ont tiré au moins un coup en 60 s — la fenêtre du pré-vol.

**Le facteur : l'état d'entrée du groupe**, lu par `unitReady` **avant** tout ordre de feu.
- **OCCUPÉ** — un ordre de déplacement pendant, que `PATH` coupé rend inexécutable. C'est l'état
  des sessions 1 et 2.
- **OISIF** — ordres vidés, et l'on attend que les trois soient `unitReady`. C'est l'état des
  deux runs muets.

**Douze répétitions par état.** Le monde est minimal : un muret, un groupe de trois, même modset,
mêmes classes, même `disableAI` (PATH, AUTOCOMBAT, AUTOTARGET, FSM), même `COMBAT`/`RED`, même
recharge par coup. **Serveur à part** — jamais celui du balayage ni celui du geste n°1.

## LES SEUILS, DÉPOSÉS MAINTENANT

> **CONDITION CONFIRMÉE** si `commandSuppressiveFire` réussit **≥ 10 sur 12** dans un état et
> **≤ 2 sur 12** dans l'autre.

> **CONTRÔLE POSITIF** : `doSuppressiveFire` — la variante directe, qui ne transite pas par la
> radio — doit réussir **≥ 10 sur 12 dans LES DEUX états**. S'il échoue quelque part, **c'est la
> sonde qui est en panne**, et elle ne répond à rien ce jour-là.

> **CONTRÔLE D'ÉTAT** : chaque répétition relit son propre état d'entrée. Si l'état lu n'est pas
> l'état voulu, la répétition est **refusée et non comptée**, et le refus est journalisé. Un état
> qu'on croit poser sans le vérifier n'est pas un facteur, c'est une intention.

## LES QUATRE ISSUES, ÉCRITES AVANT DE REGARDER

- **Séparation nette** → la condition est nommée. Le banc n'est **ni réparé ni amendé** : son
  pré-vol gagne une **garde** « état d'entrée = celui des sessions 1-2 », ce qui **restaure**
  l'état historique sans toucher un paramètre déposé ⟨règle 13⟩. La session 3 se relance derrière
  cette garde.
- **La radio ne prend JAMAIS** (≤ 2/12 dans les deux états) → alors les 260 et 206 coups des
  sessions 1 et 2 **venaient d'ailleurs**, et ces deux sessions tombent quelle que soit la
  fourche. C'est l'issue la plus chère, et c'est pour ça qu'elle est écrite avant.
- **La radio prend TOUJOURS** (≥ 10/12 dans les deux états) → la sonde ne reproduit pas la panne.
  On ne conclut rien, on redépose un discriminant, on ne bricole pas le banc.
- **Le contrôle positif tombe** → aucune lecture ce jour-là.

⚠️ **INTERDITS, repris de Fable** : pas une ligne changée au banc ni à sa commande ; pas de
relance de la session 3 avant le verdict ; **et les sessions 1 et 2 ne se citent plus comme
acquises** tant que la sonde n'a pas dit ce qu'elles mesuraient.
