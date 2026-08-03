# CRITERES v2 — AUDIT DE CONTAMINATION DU CORPUS OUVERT

Amendement PROSPECTIF de la v1 (210f2d7b6bc8d124), dont l echec est consigne sans revision dans
REGISTRE_AUDIT_v1.md. La v2 ne gouverne que des corpus collectes APRES son enregistrement.

## Ce qui change, et pourquoi

La coupe « mort adossee a un impact dans les 5 s » est REMPLACEE. Elle mesurait quelle categorie
de degats declenche quel capteur — un sous-produit du moteur — au lieu de son intention : separer
une mort SIMULEE d une mort resolue par la comptabilite de virtualisation. Une mort par abstraction
ne fabrique pas d instigateur materialise et recense.

Nouvelle coupe seuillee : MORTS SANS TUEUR TRACABLE ET RECENSE.

## Les sept coupes seuillees

| quantite | numerateur | denominateur | seuil |
|---|---|---|---|
| fantomes | references entite-tick sans evenement d apparition | total des references entite-tick | < 1 % |
| morts_sans_tueur | morts dont le tueur est nul, egal a la victime, ou absent du corpus | total des morts | < 1 % |
| tireurs_intracables | impacts dont le tireur vaut -1 | total des impacts | < 1 % |
| teleportation | paires de ticks consecutifs a vitesse horizontale > 60 m/s | total des paires consecutives | < 1 % |
| tirs_sans_projectile | tirs dont le projectile est nul | total des tirs | < 1 % |
| couverture | ticks ou l ecart compte annonce / entites listees depasse 1 % | total des ticks | < 1 % |
| horloge | ecarts de temps hors de [0,8 ; 1,2] x nominal | total des ecarts | < 1 % |

CAS LIMITES de la coupe morts_sans_tueur, decides AVANT la mesure :
  - tueur = -1 (nul)                       -> NON TRACEE
  - tueur = la victime elle-meme           -> NON TRACEE (suicide, chute, degats poses)
  - tueur > 0 mais jamais recense           -> NON TRACEE (il n existait pas comme objet)
  - tueur > 0 et recense                    -> tracee, quelle que soit la cause des degats

## Indicateurs RAPPORTES, sans seuil la premiere nuit

- morts adossees a un impact dans les 5 s : part des morts par arme legere directe. Propriete du
  monde, utile au modele.
- FRONTIERE DE MATERIALISATION, qui vise la virtualisation mieux que la fenetre d impact :
    a) part des morts survenant moins de 10 s apres l apparition de la victime ;
    b) part des victimes qui disparaissent moins de 10 s apres leur mort.
  C est la que la comptabilite d abstraction fuirait : une unite materialisee deja condamnee, ou
  une resolution de rattrapage. Seuillee plus tard, quand on aura sa distribution.
- distribution des vitesses : p99,9, maximum, et part au-dela de 15 m/s (un fantassin ne depasse
  pas ~7 m/s).

## Les quatre controles de l audit lui-meme

1. CONTROLE NUL — corpus synthetique propre, les sept coupes a EXACTEMENT zero.
2. CANARI DE TELEPORTATION — bond delibere de +500 m puis suppression : exactement 1 teleportation
   et 1 disparition pour cette entite.
3. FAUSSETE DU CHAINAGE — impacts decales de +300 s : la part de morts adossees a un impact
   s effondre sous 5 %.
4. CANARI DE FALSIFIABILITE DE LA COUPE NEUVE — obligatoire, et c est le controle qui empeche de
   remplacer un critere falsifiable qui echoue par un critere infalsifiable qui passe.
   Une unite tuee par script SANS agresseur (degats poses directement) doit compter EXACTEMENT 1
   en morts_sans_tueur. Une coupe qui ne sait pas echouer n a pas le droit de passer.

## Mise en service

La collecte persistante demarre sous la v2. Le PREMIER audit horaire est un AUDIT DE MISE EN
SERVICE : v2 complete, les quatre controles rejoues, et lecture humaine des indicateurs de
frontiere avant que les heures suivantes ne comptent comme corpus. Un echec met l heure en
quarantaine et ouvre un diagnostic ; il n arrete pas la capture.

## Debit : ce qui est sacre et ce qui ne l est pas

Le cout de l emetteur (5 ms) est un TEMOIN D INGENIERIE, pas un critere. Ce qui decrit le dommage
reel au monde est le triplet : chute de FPS du serveur < 20 %, cadence observee dans +/- 20 % du
nominal, ZERO trou de numerotation de tick.
  - p95 <= 5 ms            -> affaire close
  - 5 a 10 ms              -> accepte, juge au triplet, cout journalise toutes les 300 ticks
  - au-dela de 10 ms       -> on NE BAISSE PAS la cadence (le desalignement du pas de temps entre
    corpus ouvert et banc est un cout architectural permanent contre un cout d ingenierie
    ponctuel). On decoupe l emetteur en tranches sur des images successives, toutes estampillees
    du meme temps de tick, apres avoir MESURE la bavure intra-tick sur un homme au sprint.

## Interdits

- L audit constate, il ne repare rien dans le monde.
- Ne pas blanchir les morts par explosion ou par chute : elles restent comptees comme elles sont.
- Ne pas ajuster le plafond de vitesse pour faire passer un taux.
- Ne pas appliquer la v2 a un corpus collecte avant son enregistrement.
