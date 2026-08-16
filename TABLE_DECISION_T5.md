# TABLE DE DÉCISION T5 — écrite AVANT la sonde d'unité

17/08/2026, ~02 h 30. La sonde d'unité n'a pas tourné. Aucun de ses chiffres n'existe.

⟨audit Fable⟩ *« La question n'est pas mûre : les trois issues dépendent d'un fait que tu
n'as pas mesuré — l'unité du phénomène. Choisir maintenant, c'est choisir à l'aveugle. »*

## Ce qui déclenche quoi

### Si l'unité est la SESSION
T5 **reste tel quel**, tiré **une fois en tête de session**. Rouge → le serveur est **jeté et
relancé**, avec un plafond de relances écrit d'avance. Le **taux de serveurs jetés** est
journalisé et publié avec chaque campagne ; s'il dépasse son plafond sur fenêtre glissante,
**la campagne s'arrête d'elle-même**. T5 devient filtre **et** alarme de dérive.

### Si l'unité est le TIRAGE
T5 seul ne protège rien : il échantillonne un processus qui se re-tire à chaque consigne.
Le témoin **descend alors dans l'épisode** — la couture journalise **commandé contre rendu**
à chaque consigne, et un critère pré-écrit écarte l'épisode dont les jambes ont menti.
T5 peut alors se desserrer en majorité, **et uniquement parce que la couverture a déménagé
dans l'épisode**. C'est la règle 16 appliquée : juger l'ACTE, en situation.

### Retirer T5 — REFUSÉ dans les deux cas
Le banc des jambes certifie la primitive **dans son monde** ; la nuit vient d'établir que la
variable est **le monde**, pas la primitive. Retirer le seul instrument qui lit le monde
servi parce qu'il bloque, ce serait juger l'instrument **à la douleur qu'il inflige** — le
symétrique exact du « choix douloureux = choix rigoureux » déjà reproché.

### Clause de réalité
Si la sonde rend un taux de sessions mauvaises proche des **70 %** de la nuit, **aucune
option ne sauve une campagne** : 134 épisodes coûteraient des centaines de serveurs. Le
phénomène passe alors **devant tout épisode**, et la question T5 devient sans objet.

## Deux corrections au dépôt d'hier soir

1. **`ETAT_T5_INTERMITTENT.md` affirmait « deux sessions consécutives et identiques au code
   près ».** **C'est faux** : ce sont les deux bras d'échauffement, qui différaient par le
   délai (45 s contre 150 s). Ma seule pièce en faveur de l'effet-session était **confondue
   avec la variable que je testais**. Pièce retirée.

2. **La colonne « T5 rouge » et la prose « verts du prévol » comptaient deux choses
   différentes** sans le dire. À 45 s : **0 rouge sur T5**, et **3 prévols verts sur 4**, le
   quatrième échec portant sur **T7**. Les deux chiffres sont exacts ; la colonne était mal
   nommée. Toute table porte désormais le nom exact de ce qu'elle compte.

## Ce qui remplace la pièce retirée, et qui est plus fort

**Le diff `1.12.0 → 1.13.0` est purement instrumental** — un compteur `_nt`, deux champs de
format, rien d'autre (`db446bf`, lu ce soir). Or ces deux versions ont donné **17 rouges sur
20** puis **2 sur 16**, à contexte identique.

**Le plus grand écart de toute la nuit n'a aucune cause dans le code.** Ce n'est plus une
intuition sur l'effet-session : c'est un écart qu'aucune variable connue n'explique.
