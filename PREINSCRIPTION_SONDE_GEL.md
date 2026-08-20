# LA SONDE DU GEL — pré-inscription écrite AVANT la mesure

**20/08/2026.** Dette contractée à `REPARATION_GEL.md` : *un correctif qui n'a pas été vu
agir n'est pas établi.*

## LA DETTE

Le gel est réparé — **effet établi par témoin** : même socle, la garde retirée, `gel` rend
**1/3 avec un VERT IMMÉRITÉ en 4,9 s** ; la garde en place, **3/3**. Mais l'attente **G2**
disait : *au moins un `VERDICT_TU` journalisé*. **Zéro.** J'ai l'**effet**, pas le **chemin**.

Trois hypothèses non départagées : (a) le prévol périmé meurt avec le serveur avant d'écrire ;
(b) la ligne de journal échoue silencieusement ; (c) la garde agit par un effet de timing
plutôt que par son test.

## L'INSTRUMENT — UNE COLLISION FABRIQUÉE, DÉTERMINISTE ⟨Fable⟩

On ne guette plus une collision fortuite : **on la fabrique**.

1. lancer un prévol par le chemin normal de `prevol.py` (garde comprise) ;
2. **incrémenter `HMT_PV_GEN` à la main, en plein vol** — le prévol courant devient périmé ;
3. attendre qu'il finisse et tente de déposer son verdict ;
4. **le témoin DOIT parler.**

⚠️ C'est la **règle 16 appliquée au témoin lui-même** : un témoin qu'on n'a jamais fait
crier ne prouve pas qu'il crierait.

## LES ATTENTES

| n° | attente |
|---|---|
| **S1** | sous **collision fabriquée**, `HMT|SOCLE|PREVOL|VERDICT_TU` apparaît — **3 fois sur 3** |
| **S2** | **sans** collision, **aucun** `VERDICT_TU` — 3 fois sur 3 (le témoin ne crie pas à tort) |
| **S3** | sous collision, `HMT_PV` reste **nil** — le verdict périmé n'est pas déposé |

## LE FALSIFICATEUR

> **Si S1 échoue — le témoin reste muet sous une collision qu'on a fabriquée nous-mêmes —
> alors le témoin est cassé, et le correctif du gel n'est PAS établi.** Il sera retiré ou
> remplacé, et l'hypothèse (c) — « la garde agit par un effet de timing » — deviendra le
> sujet, avec la question qui suit : **qu'est-ce qui a réellement réparé le gel ?**

⚠️ Dans ce cas, le `gel` PASSE en tampon sur une cause non identifiée, et la ligne 4 de la
porte s'appuie sur un contrôle dont on ne sait pas pourquoi il fonctionne.
