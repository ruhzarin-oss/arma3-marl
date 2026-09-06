# CRITERES N1 — LE NIVEAU DE LA COURBE, REMESURE A `HitPart`

Ecrits AVANT tout chiffre. Arbitrage de Fable : `HitPart` sur cible invulnerable, un impact
par projectile, fait foi ; la courbe du 26/07 est « non verifiee en pente, fausse en niveau ».

## CE QUI CHANGE, ET RIEN D AUTRE
Les **18 conditions** du 26/07 (6 distances x 3 postures) rejouees **en ne changeant que le
CAPTEUR**. Meme site plat certifie, meme skill 0,5, meme plein jour, meme terrain nu.
Tout le reste est tenu fixe : c est la definition d une remesure d instrument.

## LES QUATRE GARDES, TOUTES DEJA PAYEES PAR LE PROJET
1. **Compter les BALLES TIREES** (`Fired`) autant que les impacts — sans denominateur on ne
   distingue pas « rate » de « pas tire ».
2. **UN impact par PROJECTILE** : `_this` de `HitPart` liste les PARTIES du corps touchees par
   une seule balle. Iterer dessus gonflait le taux de 0,32 a 0,615 — faute payee ce soir.
3. **N accepter un impact que si sa SOURCE est le tireur APPARIE** — sinon le tir croise d un
   duel voisin entre dans le compte. Garde du 26/07.
4. **Tireurs ET cibles invulnerables** : une cible qui tombe rend son bras muet, un tireur qui
   meurt supprime la condition. Les deux pieges sont dates du 28/07.

## CONTROLE POSITIF, JOUE EN BLOC 0
A **100 m, debout**, le taux doit retomber dans l intervalle de **55,9 %** mesure ce soir sur
le meme capteur (banc `loi_visibilite`, fraction de corps = 1). Bande acceptee **[0,45 ; 0,66]**
— large a dessein, elle teste la reproductibilite de l INSTRUMENT, pas une hypothese.
Si le bloc 0 sort de la bande, le capteur n est pas stable d une nuit a l autre et **rien de la
nuit n est lisible** : on inscrit ⛔ instrument et on lance la reserve.

## CE QUI FERAIT ECHOUER LA NUIT
- moins de **300 balles** dans une condition -> cette condition n est pas rendue ;
- le bloc 0 hors de [0,45 ; 0,66] -> nuit ⛔ instrument ;
- une condition ou le taux DEPASSE une condition plus proche a posture egale de plus de
  l intervalle de Wilson -> anomalie de monotonie, la condition est marquee, pas effacee.

## LE SECOND BRAS, EN FIN DE NUIT
`degat_par_impact` doit etre re-derive depuis l ACTE DE MORT, pas depuis 0,233 : un bras a
100 m avec cible VULNERABLE, on compte les impacts jusqu a la neutralisation.
Mediane attendue autour de 3 si le capteur d alors valait ; **toute autre valeur remplace 0,233**.

## CE QUE LA NUIT PRODUIT
`courbe_toucher_hitpart.json` (18 conditions, comptes bruts et intervalles de Wilson),
`degat_par_impact` re-derive, et le verdict : **la courbe du 26/07 est-elle sous-comptee, et
de combien**. Tout NIVEAU conclu depuis le 26/07 est rappele « sous-compte » jusqu a ce
verdict.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la prise, rien sur le couvert, rien sur le transfert. On remesure un instrument.
