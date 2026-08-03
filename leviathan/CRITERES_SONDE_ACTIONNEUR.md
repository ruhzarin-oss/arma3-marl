# CRITERES — SONDE D ACTIONNEUR : le gel vient-il de NOTRE COMMANDE ou DU MOTEUR ?

Pre-enregistre AVANT la mesure. Empreinte prise apres ecriture.

## Le defaut a l origine

Mesure du 31/07 : dans notre banc, trois des quatre executeurs se figent en terrain decouvert des
qu ils ouvrent le feu. C etait deja ecrit dans notre code de mission, date du 28/07 : « doSuppressive
Fire ARRETE l unite. Tout attaquant qui obtenait une ligne de vue se figeait vers 28 m et n allait
jamais au bout. » Le quatrieme executeur ne tire JAMAIS — son tableau de tir est constant a zero —
donc il ne s arrete jamais, et c est lui qui dominait toutes les comparaisons.

Consequence : l ecart de mortalite mesure (-23 % en pire cas) ne mesure PAS « courir protege » mais
« s arreter pour tirer a decouvert tue ». Et l arret vient de nous.

Regle applicable (ecrite le 31/07) : une anomalie n est un DEFAUT que si elle est un artefact de
notre instrumentation ou de nos actionneurs ; sinon c est une propriete du monde certifie.
Ici l arret est commande par nous : c est un defaut.

## Ce que la sonde tranche, et rien d autre

Le gel est-il une propriete de LA COMMANDE que nous scriptons, ou DU MOTEUR — c est-a-dire est-ce
que toute ouverture de feu immobilise, quoi qu on fasse ?

On ne peut pas y repondre en lisant du code. On croise donc six cases :

  MECANISME DE FEU                          POSTURE
  0. jamais tirer                           A. libre    (setUnitPos AUTO, forceSpeed -1)
  1. tir NATIF : le moteur decide seul       B. forcee   (setUnitPos UP, forceSpeed 100)
     (COMBAT + RED + ordre de mouvement,
      aucune commande de tir de notre part)
  2. tir SUPPRESSIF scripte (l actuel)

La case jamais testee, et la plus interessante : 1B — un homme qu on EMPECHE de s arreter mais
qu on LAISSE tirer. Si elle est admissible, la reparation se fait sans revenir au pilotage par
velocite, que nos notes interdisent (il ecroule le FPS).

## Deux phases, parce que deux pathologies distinctes

PHASE SANS OPPOSITION (aucun defenseur) : isole la LOCOMOTION. L unite atteint-elle l objectif ?
En combien de temps ? Une case qui ne franchit pas sans opposition est disqualifiee sans discussion.

PHASE AVEC OPPOSITION (D=8, poses par poser_fob.py) : verifie que l unite TIRE effectivement, et
mesure ce qu il lui en coute.

A=8 attaquants, 60 pas, n=3 par case et par phase. 36 episodes au total.

## Criteres d admissibilite d un actionneur, poses d avance

Un actionneur est ADMISSIBLE si les trois tiennent ensemble :

  1. FRANCHISSEMENT SANS OPPOSITION : distance minimale atteinte < 25 m dans 3 essais sur 3.
     C est le test de la pathologie du gel a 28 m.
  2. IL TIRE QUAND IL EST OPPOSE : au moins 10 tirs enregistres par episode oppose, en moyenne.
     Un actionneur muet n est pas une doctrine, c est le bras temeraire deguise.
  3. COUT : FPS serveur a moins de 20 % sous son niveau hors sonde.

## Ce qui se lit, et rien d autre

- Si une case a tir NON NUL est admissible : le gel vient de NOTRE COMMANDE. Les doctrines
  emettront des INTENTIONS — itineraire, posture, cible a supprimer — et le moteur resoudra la
  locomotion, haltes de visee comprises, qui redeviennent alors un FAIT DU MONDE et non notre
  script. C est l architecture qu on defend depuis le debut : le reseau emet des seuils et des
  intentions, jamais la motricite.
- Si AUCUNE case a tir non nul ne franchit : le gel est une propriete DU MOTEUR. Il entre au
  registre comme contrainte du monde, et la doctrine correcte devient « tirer depuis un couvert ».
  Ce serait alors un defaut de nos DOCTRINES, pas de nos actionneurs.

## Interdits

- Ne pas symetriser par le bas : faire taire ou figer tout le monde pareil egaliserait les
  handicaps pour mesurer un monde ou tout le monde se bat mal. Rejete d avance.
- Ne pas revenir au pilotage par velocite imposee : mesure anterieure, il ecroule le FPS.
- Ne pas conclure sur les DOCTRINES a partir de cette sonde : elle juge des ACTIONNEURS.
- La politique de feu de chaque executeur devient desormais un PARAMETRE DECLARE et journalise
  (jamais / natif / suppressif), jamais plus un accident decouvert dans un tableau de zeros.

## Regle permanente qui sort de cette affaire

EMPREINTE D ACTIONNEUR, au meme rang que l empreinte de monde : le sha256 du code des executeurs
entre dans chaque enregistrement, pour toujours. Un corpus sans empreinte d actionneur ne permet
pas de savoir a quoi ses politiques etaient handicapees.
