"""PROVOQUER ( HMT-146, 29/09 ) : le geste du maitre du jeu. Younes, 26/09 : « le moteur ne decide de rien ; Younes et
Claude provoquent les evenements ( penuries, blocus, coupures ) ». Reprise du point 6 de Victoria 3 ( les aleas ).

Un catalogue : chaque nature dit quel domaine la porte et par quelle API EXISTANTE ( aucune n est modifiee ici ).
  - Les catastrophes naturelles ( seisme, inondation, secheresse, canicule ) entrent par le territoire ( domaine 8 ) :
    elles attendent minuit dans sa file et passent par les memes fonctions que la nature, ou les domaines qui lisent
    les catastrophes du jour ( 11 lignes, 12 routes, 13 batiments, 16 crues, 18 secours ) les voient comme les autres.
  - Les autres tombent tout de suite, dans le domaine qui les porte : feu de foret ( 18, allumer ), epidemie ( 16,
    introduire ), panne de centrales ( 11, forcer_panne ), coupure de ligne ( 11, couper_ligne ), choc sur les prix
    mondiaux ( 7, choc ).
Chaque ordre est note au journal du pays ( type « provocation », registre tenu par le domaine 8 : numero, nature, ile,
jour d effet, auteur, parametres ). Les bornes suivent le reel et sont verifiees par le domaine qui porte la nature ;
un parametre inconnu est refuse ( ValueError ), pour qu une faute de frappe ne passe pas en silence.
L archipel transmet l ordre a l ile : Ile.commande( « provoquer », nature, ile, { parametres } ).

   from monde.provoquer import provoquer
   provoquer(w, "seisme", "Altis", magnitude=6.5, lieu="<id d un lieu>", par="younes")"""

# nature -> ( domaine qui la porte, ce qu elle fait )
CATALOGUE = {
    "seisme": ("territoire", "un seisme ( magnitude, lieu ou x_km / y_km, profondeur_km ), au prochain minuit"),
    "inondation": ("territoire", "une crue du bassin d un lieu ( lieu, gravite 1 a 3 ), au prochain minuit"),
    "secheresse": ("territoire", "une secheresse ( jours, reserves, chaleur_c ), des le prochain minuit"),
    "canicule": ("territoire", "une vague de chaleur ( jours, chaleur_c, pluie ), des le prochain minuit"),
    "incendie_foret": ("securite_civile", "un feu de vegetation pres d un lieu ( lieu, cause ), maintenant"),
    "epidemie": ("medecine", "des cas importes d une maladie ( maladie, cas, lieu ), maintenant"),
    "panne_centrales": ("energie", "des groupes en panne ( technologie, groupes, heures ), maintenant"),
    "coupure_ligne": ("energie", "la ligne d un lieu coupee ( lieu, jours ), maintenant"),
    "choc_prix": ("exterieur", "les prix mondiaux multiplies ( facteur, famille ou biens, demi_vie_j ), maintenant"),
}
PAR_DEFAUT = "inconnu"
CAS_MAX = 100_000                       # borne d une epidemie importee ( ordre de grandeur, pas une donnee )
PANNE_H = (1.0, 24.0 * 90)              # une centrale arretee de 1 h a 90 jours ( CHOIX : un arret majeur, a calibrer )
COUPURE_J = (1.0 / 24, 90.0)            # une ligne coupee de 1 h a 90 jours ( CHOIX, a calibrer )


def _pays(w):
    p = getattr(w, "pays", None)
    if p is None: raise ValueError("provoquer : ce monde n a pas de pays ( domaines )")
    if not p.a("territoire"): raise ValueError("provoquer : le territoire ( domaine 8 ) tient le registre des provocations")
    return p


def _exige(p, domaine, nature):
    if not p.a(domaine): raise ValueError(f"provoquer : {nature} veut le domaine {domaine!r}, absent de ce monde")


def _lieu(p, lieu, ile, nature):
    lid = lieu if isinstance(lieu, str) else getattr(lieu, "id", None)
    l = p.w.carte.lieux.get(lid)
    if l is None or l.ile != ile: raise ValueError(f"provoquer : {nature} : lieu {lieu!r} hors de {ile}")
    return lid


def _borne(v, nom, bornes):
    v = float(v)
    if not bornes[0] <= v <= bornes[1]: raise ValueError(f"provoquer : {nom} = {v!r} hors [{bornes[0]} ; {bornes[1]}]")
    return v


def provoquer(w, nature, ile=None, par=PAR_DEFAUT, **parametres):
    """Provoque `nature` sur l ile `ile` du monde `w` ( voir CATALOGUE ). Rend la provocation notee ( numero, nature,
    ile, jour_effet, par, parametres ) ; pour une nature immediate, aussi « effet » : ce que le domaine a rendu."""
    from .pays import d08_territoire as TER
    p = _pays(w)
    if nature not in CATALOGUE: raise ValueError(f"provoquer : nature inconnue {nature!r} : {sorted(CATALOGUE)}")
    dom = CATALOGUE[nature][0]
    if dom == "territoire": return TER.provoquer(p, nature, ile, par=par, **parametres)
    _exige(p, dom, nature)
    if nature != "choc_prix" and ile not in w.carte.iles: raise ValueError(f"provoquer : ile inconnue {ile!r}")
    q = dict(parametres)
    if nature == "incendie_foret":
        from .pays import d18_securite_civile as SC
        lid = _lieu(p, q.pop("lieu", None), ile, nature)
        cause = q.pop("cause", "accidentelle")
        if cause not in SC.CAUSES: raise ValueError(f"provoquer : cause {cause!r} : {SC.CAUSES}")
        v = {"lieu": lid, "cause": cause}
        faire = lambda: SC.allumer(p, "foret", lieu=lid, cause=cause)
    elif nature == "epidemie":
        from .pays import d16_medecine as MD
        maladie = q.pop("maladie", None)
        if maladie not in MD.IM: raise ValueError(f"provoquer : maladie inconnue {maladie!r} : {MD.INFECTIEUSES}")
        cas = int(_borne(q.pop("cas", 1), "cas", (1, CAS_MAX)))
        lieu = q.pop("lieu", None)
        lid = None if lieu is None else _lieu(p, lieu, ile, nature)
        v = {"maladie": maladie, "cas": cas, "lieu": lid}
        faire = lambda: len(MD.introduire(p, maladie, cas, lid))
    elif nature == "panne_centrales":
        from .pays import d11_energie as EN
        tech = q.pop("technologie", None)
        if tech is not None and tech not in EN.NOMS_TECH: raise ValueError(f"provoquer : technologie {tech!r} : {EN.NOMS_TECH}")
        groupes = q.pop("groupes", None)
        if groupes is not None: groupes = int(_borne(groupes, "groupes", (1, 10_000)))
        heures = _borne(q.pop("heures", 24.0), "heures", PANNE_H)
        v = {"technologie": tech, "groupes": groupes, "heures": heures}
        faire = lambda: len(EN.forcer_panne(p, ile, tech, groupes, heures, cause="provoquee"))
    elif nature == "coupure_ligne":
        from .pays import d11_energie as EN
        lid = _lieu(p, q.pop("lieu", None), ile, nature)
        jours = _borne(q.pop("jours", 1.0), "jours", COUPURE_J)
        v = {"lieu": lid, "jours": jours}

        def faire():
            """L effet : les lignes du lieu dont la coupure s allonge. Une ligne deja coupee plus longtemps ( un seisme )
            garde sa coupure et d11 ne note rien : l effet vaut alors 0, et le maitre du jeu le voit ( 29/09, porte )."""
            charges = [c for c in p.domaine("energie").par_ile[ile].charges if c.lieu == lid]
            avant = [c.coupe_jusqu for c in charges]
            EN.couper_ligne(p, lid, jours, cause="provoquee")
            return sum(1 for a, c in zip(avant, charges) if c.coupe_jusqu > a)
    else:                                  # choc_prix : le monde entier ( les bornes sont celles de d07.choc )
        from .pays import d07_exterieur as EX
        facteur = float(q.pop("facteur", 0.0))
        famille, biens = q.pop("famille", None), q.pop("biens", None)
        if (famille is None) == (biens is None): raise ValueError("provoquer : choc_prix veut une famille OU des biens")
        demi = _borne(q.pop("demi_vie_j", EX.DEMI_VIE_CHOC_J), "demi_vie_j", (1.0, 3650.0))
        v = {"facteur": facteur, "famille": famille, "biens": None if biens is None else list(biens), "demi_vie_j": demi}
        faire = lambda: EX.choc(p, facteur, famille=famille, biens=biens, demi_vie_j=demi)
    if q: raise ValueError(f"provoquer : parametres inconnus pour {nature} : {sorted(q)}")
    effet = faire()                        # le domaine verifie ses propres bornes AVANT qu on note quoi que ce soit
    r = TER.noter_provocation(p, nature, ile, p.jour, par, v)
    r["effet"] = effet
    return r


def en_attente(w):
    """Les provocations du territoire qui n ont pas encore pris effet."""
    from .pays import d08_territoire as TER
    return TER.provocations_en_attente(_pays(w))
