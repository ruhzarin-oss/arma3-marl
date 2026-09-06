# PRE-INSCRIPTION — banc de parallelisation, 01/09/2026 18:20

## La question
Faire tourner une SECONDE instance Arma sous charge degrade-t-il le debit de la premiere ?

## L'instrument
`debit.py` sur le RPT de l'instance 0 : temps de mur entre deux RESULT consecutifs,
remise a zero comprise. Controle passe : 17,00 s/ep contre 17,05 s/ep au journal,
deux derivations independantes, ecart 0,3 %.

## Le plan : ABAB, quatre blocs de 20 minutes
  A1 18:25-18:45   instance 1 allumee mais OISIVE
  B1 18:45-19:05   harnais en marche sur l'instance 1
  A2 19:05-19:25   oisive
  B2 19:25-19:45   en marche

### Pourquoi ABAB et pas avant/apres
Le debit de l'instance 0 N'EST PAS STATIONNAIRE : le lot est passe de 514 s a 306 s en
vingt mises a jour, sans que rien d'exterieur ne change — la politique se condense et ses
gestes raccourcissent. Un simple avant/apres crediterait la parallelisation d'une
acceleration qui vient de l'apprentissage, et masquerait un ralentissement reel.
Le biais irait donc dans le sens qui rassure. L'alternance l'annule.

## Ce que ce banc peut voir, et ce qu'il ne peut pas
ecart-type mesure 6,84 s/ep ; ~70 episodes par bloc, 140 par condition.
Erreur-type de la difference : 0,82 s  ->  **seuil de detection 1,6 s/ep, soit 9,4 %.**
En dessous de 9,4 % de degradation, CE BANC EST AVEUGLE. Je l'ecrirai tel quel :
« non detectee » ne voudra pas dire « nulle ».

## La charge de l'instance 1
Harnais reparti du DERNIER POINT de la graine 1 (copie), pas d'une politique neuve.
Une politique neuve fait des episodes plus longs : elle sous-estimerait le debit
atteignable. On veut le meme profil d'episode des deux cotes.
Ecrit dans un dossier de points jetable. Aucun gradient ne remonte vers la graine 1.

## Decision annoncee d'avance
  · degradation < 1,6 s/ep ET instance 1 >= 0,8x le debit de l'instance 0
        -> la parallelisation paie ; on passe a 3-4 instances
  · degradation >= 1,6 s/ep
        -> elle coute ; on chiffre le cout avant de decider
  · instance 1 nettement plus lente sans degradation de l'instance 0
        -> quelque chose d'autre limite ; on cherche avant de conclure
