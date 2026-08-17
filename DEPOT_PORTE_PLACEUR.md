# DÉPÔT — LA PORTE-CERTIFICATION DU PLACEUR v2

17/08/2026, écrit **AVANT** de lancer. Socle `2.0.0`, commit `247f190`.
Correctifs 3 et 4 du plan, **fusionnés en un seul objet** ⟨Fable⟩.

## Ce qui est déjà acquis, et qui ne suffit pas

Le **smoke** de la règle 18 est passé : le placeur rejette les 3 lieux morts (8, 15, 3 m de
traverse), reçoit les 2 vivants (26, 21 m), et **sait refuser** — sous sabotage de
l'impulsion, les deux lieux reçus tombent à 0 m et sont rejetés.

**Ce n'est pas une certification** : ces cinq lieux ont été **choisis par le diagnostic**, donc
les tester revient à tester sur l'échantillon de découverte. Et « vivant » n'y signifiait que
« pas 100 % mort ».

## La grandeur qui décide — le FAUX-REÇU

> Un **faux-reçu** est un lieu que le placeur a **REÇU** et où **T5 échoue ensuite**.

C'est la seule faute qui compte : un lieu rejeté à tort ne coûte que du temps, un lieu reçu à
tort **contamine la mesure**.

## CRITÈRES, écrits avant — grandeur, statistique, seuil ET `n` minimum

- **grandeur** : nombre de faux-reçus
- **statistique** : proportion sur les tirages dont le lieu a été reçu
- **seuil** : **ZÉRO faux-reçu**. Par la règle de trois, `n ≥ 50` réceptions sans faute
  bornent le taux à 6 % — le plafond dérivé de la règle 19.
- **`n` minimum** : **50 réceptions**. En deçà, le critère **ne se lit pas**.
- **taille** : 50 tirages du prévol, lieu neuf à chaque appel (le placeur retire et mélange
  à chaque fois), régime de la campagne (réveil natif).

## Les trois issues, et elles PARTITIONNENT

- **0 faux-reçu sur ≥ 50** → le placeur **BORNE** le résidu sous 6 %. Le banc **sort de panne
  diagnostique** et passe en **domaine déclaré** : il mesure « le combat dans les mondes
  praticables au sens du placeur v2 », qualificatif porté par chaque verdict ultérieur.
- **1 ou 2 faux-reçus** → le placeur **réduit sans borner**. Le banc **reste en panne**, et le
  résidu devient le sujet : il faut nommer ce qui passe le placeur et tue T5 quand même.
- **≥ 3 faux-reçus** → le placeur v2 **ne suffit pas**. Ses deux actes ne capturent pas la
  cause, et il faut un troisième test — que ce banc devra désigner.

## Ce que la porte mesure AUSSI, sans que ça décide

- **le coût réel** : nombre de candidats essayés par réception. Prédiction de Fable :
  ~3 en espérance à un lieu praticable sur trois, soit 20-40 s par prévol. **Mon estimation
  de 96 s supposait un balayage exhaustif** — elle est déjà réfutée par conception, ce banc
  la chiffre.
- **le taux de rejet**, sous alarme économique.
- **l'atlas d'encombrement** : chaque lieu rejeté est journalisé avec sa cause. Gratuit, et
  il capitalise.

## Ce qu'elle NE mesure PAS, déclaré d'avance ⟨règle 20⟩

- **Un seul serveur** porte les 50 tirages. L'angle mort est donc **le résidu propre au
  serveur** : si quelque chose dépend encore de la naissance du serveur, cette porte ne le
  verra pas. Elle est légitime **parce que** la variable cachée était le lieu, et que le lieu
  varie maintenant à chaque tirage — mais un bras serveurs-neufs reste dû.
- **Le transitoire de rang 1** n'est pas expliqué par le lieu et reste ouvert. Le tirage
  sacrificiel reste au plan.
