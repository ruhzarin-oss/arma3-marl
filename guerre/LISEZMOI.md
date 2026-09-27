# La guerre des îles (26-27/09/2026)

Vision de Younes : Windows est une **autre réalité**, plus lente, où les îles s'affrontent en temps réel dans Arma.
Le **moteur tourne à pleine vitesse** et **ne décide de rien**, et c'est l'**horloge murale** qui arbitre.
L'économie de chaque île paie ses soldats, et les zones prises dans Arma pèsent sur son économie.
On ne pilote pas le soldat : on donne des ordres par groupe.
Les îles se gouvernent elles-mêmes, avec le code de Qwen et le conseil de guerre, avec le moins d'intervention possible.

## La boucle

```
moteur (archipel Malden + Stratis, 100 000 hab. chacune, pleine vitesse)
   │ chaque minute : relevé (recettes, défense, faim, front), bourse → points ; achats payés par le Trésor
   │ toutes les 10 s : positions et morts de chaque soldat (un habitant du moteur par soldat d'Arma)
   ▼
Arma : GuerreIles.Malden (Warlords officiel de Malden, sans son argent), instance 10
   │ état-major de chaque camp : cible, garnison, ralliement, assaut à 3 contre 1 ; achats d'escouades et véhicules
   │ Warlords juge la capture des zones ; points sur la carte (bleu, rouge, jaune = joueur, croix = mort)
   ▼
moteur : zones occupées → fermes sous séquestre, villes en quarantaine, centrales en panne ; morts → deceder(…, "combat") ;
   │ au front → absents ; armes impayées → plus de points dans Arma
   │ gouvernement de chaque île (code de Qwen) : il voit la guerre et ses réserves de change dans son bulletin du matin
   ▼
conseil de guerre : Qwen réécrit le gouvernement de l'île en difficulté, joué sur une copie exacte de l'île (--reel) ;
                    adopté s'il bat celui en place d'au moins 1 point puis un examen de 8 jours ; l'horloge le pose
                    dans l'île vivante au tour suivant
```

| Fichier | Rôle |
|---|---|
| `zones.py` | Les 21 zones de Warlords et les lieux du moteur qu'elles tiennent (le carré, sinon le secteur à moins de 1 km). |
| `bourse.py` | Points par minute = f × part défense × recettes × euros/unité ÷ 100 (f = 100 / militaires). |
| `moteur.py` | Dans le processus de l'île : relevé, occupation (séquestre des fermes, choc de rendement pour les sites du moteur), soldats au front (mobiliser, suivre, morts au combat), paiement de la guerre (`d07.declarer_import`, import_armement), bulletin de guerre (`CerveauDeGuerre`), relève d'un gouvernement. |
| `arma.py` | Le pont (Liaison du labo, un seul écrivain) : tour, positions, identification ; `FauxGuerre` pour les portes. |
| `horloge.py` | La boucle. `--gouvernement <dossier>`, `--reprise`, `--instantane`, arrêt par le fichier `STOP`. Relit `/mnt/data/hmt/guerre/gouvernements/<Ile>.py` à chaque tour. Tant qu'une île doit des armes à son fournisseur, elle ne reçoit plus de points. |
| `conseil.py` | Le conseil de guerre (Qwen3.8-27B par Ollama) : scénario lu dans le journal de la guerre, entraînement sur de petits pays neufs en guerre, examen, adoption. |
| `mission/GuerreIles.Malden/` | `description.ext` (StartCP, CPMultiplier et MaxCP à 0, Progress 12, vote de l'IA) ; `fonctions.sqf` ; `suivi.sqf` et `doctrine.sqf`, **sans commentaire**, car le même texte s'envoie par le pont pour corriger une bataille en cours. |
| `fabriquer_mission.py` | Relit le `mission.sqm` de Bohemia dans le PBO du jeu (il n'est pas dans le dépôt). |
| `lancer_guerre.sh` / `.ps1`, `arreter_guerre.sh` | Serveur instance 10, `server_guerre.cfg`, sans mods. L'arrêt est à la main de Younes. |
| `porte_guerre.py` | 17 portes, sans Arma. |
| `porte_immobilier.py` | Le marché immobilier accéléré (×15) rend le même monde, au bit. |
| `monde/archipel.py` | Les commandes `guerre_*` de l'île. |
| `monde/pays/d06_etat.py` | Le passage d'année corrigé (`>`), import_armement rangé sur la ligne défense, bornes de `fixer_budget` à l'échelle du pays. |
| `monde/gouvernement.py`, `monde/monde.py`, `d07_exterieur.py` | Leviers à l'échelle (k = vivants / 500) ; `importer` vers la population (aide alimentaire distribuée) ; un import où rien n'entre est refusé, avec sa raison. |
| `monde/pays/d13_immobilier.py` | `_apparier` en tableaux (×15), l'ancien gardé comme `_apparier_reference`. |

## Portes (`python -m guerre.porte_guerre`) : 17 franchies

G1 zones · G2 bourse · G3 relevé · G4 occupation · G5 horloge · G6 pont · G7 mission · G8 passage d'année · G9 soldats suivis · G10 la guerre coûte au Trésor · G11 le gouvernement voit la guerre · G12 conseil de guerre · G13 villes occupées · G14 centrale occupée · G15 leviers à l'échelle · G16 aide alimentaire · G17 fournisseur impayé.

La porte d'identité des domaines (`python -m monde.porte_domaines --comparer /mnt/data/hmt/ref_domaines.json`) reste franchie : tout ce qui change est nouveau ou ne joue qu'à grande échelle.

Quatre portes ont échoué d'abord, et chaque échec a appris quelque chose :
- **G4** : la quarantaine ne retient pas un paysan qui vit sur sa ferme. L'occupation passe donc par le séquestre.
- **G8** : le bogue du 1er janvier dans d06.
- **G10** : la faute était dans le test (la base était déjà fixée par G9).
- **G12** : les armes des mondes d'entraînement n'étaient pas comptées dans le coût de la guerre.
- **G13, G14** : un lieu témoin sans emploi, puis une fonderie qui ne produit rien même en paix ; la centrale produit selon la demande du réseau, d'où la panne « occupation ».
- **G15** : le refus venait des crédits, pas de la borne.
- **G16** : l'import était « accepté » et rien n'arrivait. La banque centrale de Stratis n'avait plus de devises (voir Mesures).

## Leçons payées dans Arma

- Un ordre SAD en ligne droite laissait 7 groupes sur 9 immobiles. Les groupes marchent donc par la route (MOVE, SAFE, COLUMN) et passent à l'assaut à 600 m. Un groupe immobile une minute malgré deux nouveaux ordres est dégagé sur la route la plus proche.
- Un `exitWith` au niveau haut d'une commande du pont supprime son reçu.
- Une commande du pont est limitée à 9 Ko : `doctrine.sqf` s'envoie en morceaux.
- Assauts au compte-gouttes : Malden a perdu 31 hommes contre 1. D'où le ralliement et les 3 contre 1 face aux défenseurs **repérés** (`knowsAbout` du camp).
- La v8 annulait l'assaut à l'instant où il partait. Le repli ne se déclenche plus que si toute la force engagée tombe sous 1 contre 1.
- Le vote de l'IA de Warlords ne partait pas : Younes a dû choisir la cible. Depuis la v10, l'état-major choisit et fait voter ses chefs IA.

## Mesures

- À 100 000 habitants par île, en début de guerre : 5 à 8 jours du moteur par minute et environ 245 points par minute et par camp.
- Vers le jour 220 : 1 jour par minute seulement. 75 % du temps d'une journée passe dans `d13_immobilier._apparier`, qui fait 40 millions d'accès par jour.
- Nuit du 26 au 27/09, au jour 245 environ : faim de 39 % à Malden et 36,5 % à Stratis. Stratis était à 1,6 % au jour 231, sous les règles. La cause est en cours de mesure : comparaison règles contre code de Qwen depuis la même sauvegarde.
- Conseil de Malden : les versions 1 à 4 ne font pas mieux. La version 4 battait le gouvernement en place de 0,2 point à l'entraînement, puis a raté l'examen.
- **La famine de Stratis (98 %) est une crise de devises.** Au jour 349, ses réserves de change sont à −55 M€ (295 M€ au départ ; Malden : 0,68 M€). Le contrôle des changes bloque tout import, celui des négociants comme celui de l'État. Sur une copie, avec des réserves portées à 50 M€ et sans aide, la faim passe de 98 % à 46 %, puis à 0,8 % en deux jours.
- Ce qui sort encore sans contrôle des changes, une fois les réserves à zéro : les abris d'urgence que l'État achète à l'étranger (266 000 par jour), la santé (37 000), les envois des migrants (60 000).
- Le fond est structurel. L'île produit environ 8 000 rations par jour pour 61 000 mangées, et n'exporte rien. En paix (témoin, jour 190), il reste 186 M€ de réserves, mais la faim est déjà de 43 à 47 % : c'est la pauvreté (caisse médiane d'un ménage : 246 ; prix au plafond de 10).

## Ce qui n'est pas fait

- L'envahisseur ne reçoit pas ce que produit la zone (la voie : `d09.requisitionner`).
- Les blessés ne sont pas soignés au retour.
- Deux camps seulement par serveur : 6 îles demanderont 3 fronts, donc 3 serveurs.
- L'économie qui affame les îles (domaines 3, 4, 7, 9 : exportations, devises, prix plafond, pauvreté) : décision de Younes.
- Les abris d'urgence de l'État passent à côté du contrôle des changes (d13).
- Aucune voie pour faire entrer des devises : ni prêt extérieur, ni exportation.

## Lancer

1. `bash guerre/lancer_guerre.sh`, jusqu'à « GUERRE PRÊTE ».
2. `PYTHONPATH=. python -m guerre.horloge --arma vrai --echelle 200 --gouvernement monde/resultats/agent_codeur/six_iles --dossier /mnt/data/hmt/guerre/essaiN [--reprise …/instantane --instantane …]`
3. `PYTHONPATH=. python -m guerre.conseil --guerre <dossier d'un essai> --ile Stratis --reel <dossier>/instantane`
4. Arrêt : `touch <dossier>/STOP` (l'instantané est sauvé), puis `bash guerre/arreter_guerre.sh`.
