porte: Loi couvert-tir lue dans la source CWR, confrontee a Arma 3
date: 2026-09-03
graines: n/a
chiffre: porte 0,63 refutee (237 impacts sur victime vivante, 29,5 % sous le seuil) ; exposant du couvert 0,72 au lieu de 2 ; ouie plafonnee a 1,35 en 1/d2
verdict: PASSE
depend_de: arc-tir-sursis, etre-vu-tue-2x
remplace_par: 
source: loi-de-tir-cwr-instanciee

Le mecanisme couvert-tir a ete LU dans le code d'un ancetre officiel du moteur, pas devine. Chaque equation reste une hypothese sur Arma 3, et elles ont ete confrontees.
Deux equations sont refutees. La porte de visibilite tombe : on EST touche au fusil en etant cache dans Arma 3, ce qui rend legitime un mecanisme de tir sur position connue.
L'exposant du couvert est mesure a 0,72 sur 18 181 coups, alors que la source le met au carre : le carre sur-punit le couvert d'un facteur 2,4.
Une equation est validee avec sa forme : le canal auditif plafonne a 1,35, sous le seuil d'identification du camp, et suit bien une loi en un sur distance au carre.
Consequence : l'ouie seule n'identifie jamais le camp, et le sursis de quatre secondes mesure au flanc s'explique comme un delai de RAPPORT au groupe, pas une interdiction de tirer.
Cliquets payes : une fenetre temporelle dans un moteur est presque toujours une peremption et non un droit ; et quand un controle de niveau echoue, on peut encore lire une pente si l'on dit laquelle des deux on prend.
Non teste, donc toujours en service : le plancher de decision, les horloges, le verrou de cible et la portee de designation visuelle.
