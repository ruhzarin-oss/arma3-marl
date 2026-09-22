"""L ecole et l eleve. On n entraine pas : on APPREND et on FORME. Chaque jour d ecole suit le cycle d une formation :
  8 h  instruction   l enseignant donne une lecon tiree du monde REEL du jour ( pas d un manuel fige )
  11 h exercice      une question a laquelle l eleve repond avec ce qu il sait et ce qu il a vu
  14 h debrief       l enseignant donne la bonne reponse et son explication ; l eleve corrige ses notes
  19 h vie           l eleve accompagne sa famille au marche : il VOIT les prix et les stocks, et le note
  tous les 3 jours, 15 h : QUALIFICATION sur des questions jamais posees en classe, notees contre la verite du monde.
L eleve apprend par sa memoire ( ses notes ), sans reentrainement. Trois eleves possibles : sans memoire ( temoin ),
a memoire simple ( mots-cles, deterministe, pour les tests ), et LLM ( Qwen + memoire par embeddings bge-m3 )."""
import json, math, re, urllib.request
from . import config as C

MODULES = ["geographie", "metiers", "economie", "lois", "sante", "gouvernement", "armee"]


def normaliser(t):
    t = str(t).lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("â", "a"), ("ô", "o"), ("î", "i"), ("ç", "c"), ("ù", "u")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9 ,.]", " ", t)


class Enseignant:
    """Fabrique les lecons, les exercices et les epreuves a partir de l etat vrai du monde."""
    def __init__(self, monde):
        self.monde = monde

    def lecon(self, module):
        w = self.monde; k = w.carte
        if module == "geographie":
            caps = ", ".join(c.id for c in k.capitales)
            return (f"Altis a trois capitales : {caps}. Le gouvernement siege a {k.gouvernement.id}. "
                    f"La mine est a {k.plus_proche(k.lieux['Mine01'], ('capitale', 'ville', 'village')).id}, "
                    f"le terminal petrolier pres de {k.plus_proche(k.lieux['terminal01'], ('capitale', 'ville', 'village')).id}, "
                    f"le port a Kavala. Chaque village a une ferme ; chaque village achete au marche de la capitale la plus proche.")
        if module == "metiers":
            r = ", ".join(f"{n} {role}s" for role, (n, _, _) in C.ROLES.items())
            return (f"Altis compte 500 habitants : {r}. Les soldats, policiers, medecins, infirmiers, enseignants, ministres "
                    "et le chef du gouvernement sont payes par l Etat. Les mineurs, petroliers et ouvriers sont payes par "
                    "leur entreprise ; les paysans partagent le revenu de leur ferme ; les marchands vivent du benefice du marche.")
        if module == "economie":
            rec = " ; ".join(f"une {t} transforme {', '.join(k2 for k2 in i) or 'du travail seul'} en {', '.join(o)}"
                             for t, (_, i, o) in C.RECETTES.items())
            prix = ", ".join(f"{m.lieu.id} {m.prix['nourriture']:.1f}" for m in w.marches.values())
            return (f"On produit avec du travail et des intrants : {rec}. Les convois portent les biens aux marches et brulent "
                    f"du carburant. Le prix monte quand la demande depasse l offre. Aujourd hui la nourriture coute : {prix} drachmes.")
        if module == "lois":
            L = w.gouv.lois
            return (f"Les lois en vigueur : couvre-feu {L['couvre_feu'] or 'aucun'} ; quarantaine {L['quarantaine'] or 'aucune'} ; "
                    f"rationnement {L['rationnement_nourriture'] or 'aucun'} ; l ecole est obligatoire. L impot sur le revenu est de "
                    f"{w.gouv.impot_revenu:.0%} et la TVA de {w.gouv.tva:.0%}.")
        if module == "sante":
            s = w.sitrep()["sante"]
            return (f"Une maladie se transmet par contact, quand on est au meme endroit qu un malade. Elle couve {C.INCUBATION_J:.0f} "
                    f"jours puis dure {C.MALADIE_J:.0f} jours ; un remede reduit sa duree de moitie et le risque de mourir. Les "
                    f"remedes sont fabriques a la pharmacie avec du zinc et de la nourriture. Aujourd hui : {s['infectes']} malades.")
        if module == "gouvernement":
            return (f"Le gouvernement : un chef et six ministres ( {', '.join(C.MINISTERES)} ). Il leve les impots, paie les "
                    f"fonctionnaires et les pensions, achete les remedes des hopitaux et le carburant de l armee, et fait les lois. "
                    f"Sa caisse contient {w.gouv.caisse:.0f} drachmes.")
        if module == "armee":
            return (f"L armee compte 5 officiers et 55 soldats repartis dans {len(k.de_type('base'))} bases. Le pays est en paix. "
                    f"Les patrouilles partent a 8 h et 20 h et brulent le carburant du depot de l armee ( storage01 ), "
                    f"qui en contient {w.publics['armee']['carburant']:.0f} unites.")
        raise ValueError(module)

    def questions(self, jeu):
        """Questions notables contre la verite du monde. `jeu` = 'classe' ( exercices ) ou 'epreuve' ( jamais en classe )."""
        w = self.monde; k = w.carte
        mine_ville = k.plus_proche(k.lieux["Mine01"], ("capitale", "ville", "village")).id
        m_cher = max(w.marches.values(), key=lambda m: m.prix["nourriture"]).lieu.id
        if jeu == "classe":
            return [
                ("Ou siege le gouvernement ?", ["kavala"], "texte"),
                ("Que faut-il pour produire du carburant ?", ["petrole", "electricite"], "tous"),
                ("Qui paie les soldats ?", ["etat", "gouvernement"], "un"),
                ("Combien de temps dure la maladie sans remede, en jours ?", [C.MALADIE_J], "nombre"),
                ("Combien de malades y a-t-il aujourd hui ?", [w.sitrep()["sante"]["infectes"]], "nombre"),
            ]
        return [   # EPREUVE : on n a jamais pose ces questions ; il faut RELIER ce qu on a appris
            ("Quel bien un mineur produit-il qui vaut le plus cher ?", ["or"], "texte"),
            ("Dans quel marche la nourriture est-elle la plus chere aujourd hui ?", [m_cher.lower()], "texte"),
            ("Si la raffinerie s arrete, le prix du carburant monte-t-il ou baisse-t-il ?", ["monte"], "texte"),
            ("Quelle ville est la plus proche de la mine ?", [mine_ville.lower()], "texte"),
            ("Un remede fait-il durer la maladie plus ou moins longtemps ?", ["moins"], "texte"),
            ("Qui achete le carburant de l armee ?", ["gouvernement", "etat"], "un"),
            ("De quoi la pharmacie a-t-elle besoin ?", ["zinc", "nourriture", "electricite"], "tous"),
            ("Combien d habitants vivent a Altis au depart ?", [500], "nombre"),
        ]

    @staticmethod
    def noter(reponse, attendu, mode):
        r = normaliser(reponse)
        if mode == "nombre":
            nums = [float(x) for x in re.findall(r"-?\d+(?:[.,]\d+)?", r.replace(",", "."))]
            return float(any(abs(n - float(attendu[0])) <= max(1.0, 0.1 * abs(float(attendu[0]))) for n in nums))
        if mode == "tous": return float(all(normaliser(a) in r for a in attendu))
        return float(any(normaliser(a) in r for a in attendu))


class EleveSansMemoire:
    """Le temoin : il ne garde rien. Toute qualification qu il reussit mesure le hasard ou la question trop facile."""
    nom = "sans_memoire"
    def __init__(self): self.notes = []
    def apprendre(self, texte, source): pass
    def repondre(self, question): return "je ne sais pas"


class EleveMemoire:
    """Apprend en gardant ses notes ; repond en retrouvant la note la plus proche par mots communs. Aucun reseau :
    c est l eleve deterministe des tests, et le plancher que l eleve LLM doit battre."""
    nom = "memoire"
    def __init__(self): self.notes = []
    def apprendre(self, texte, source): self.notes.append({"texte": texte, "source": source})
    def repondre(self, question):
        q = set(normaliser(question).split())
        if not self.notes: return "je ne sais pas"
        best = max(self.notes, key=lambda n: len(q & set(normaliser(n["texte"]).split())))
        return best["texte"]


class EleveLLM:
    """L eleve Qwen : ses notes sont indexees par bge-m3 ; pour repondre il relit ses 5 notes les plus proches."""
    nom = "llm"
    def __init__(self, modele="qwen2.5:14b", embed="bge-m3", hote="http://localhost:11434", sans_notes=False):
        self.modele, self.embed, self.hote, self.sans_notes = modele, embed, hote, sans_notes
        self.nom = "llm_sans_notes" if sans_notes else "llm"
        self.notes = []

    def _post(self, chemin, corps):
        req = urllib.request.Request(self.hote + chemin, data=json.dumps(corps).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=300).read())

    def _vec(self, t): return self._post("/api/embeddings", {"model": self.embed, "prompt": t})["embedding"]

    def apprendre(self, texte, source):
        if self.sans_notes: return        # le temoin LLM : il sait ce que sait Qwen, rien de ce qu il a vu a Altis
        self.notes.append({"texte": texte, "source": source, "v": self._vec(texte)})

    def repondre(self, question):
        v = self._vec(question) if self.notes else None
        def cos(a, b): return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) + 1e-9)
        top = sorted(self.notes, key=lambda n: -cos(v, n["v"]))[:5] if self.notes else []
        prompt = ("Tu es un eleve qui vit sur l ile d Altis. Reponds en une phrase courte, en t appuyant sur tes notes ; si tes "
                  "notes ne suffisent pas, raisonne a partir de ce que tu sais du pays.\nTes notes :\n"
                  + "\n".join("- " + n["texte"] for n in top) + f"\nQuestion : {question}\nReponse :")
        return self._post("/api/generate", {"model": self.modele, "prompt": prompt, "stream": False,
                                            "options": {"temperature": 0.1, "seed": 7}})["response"].strip()


class Ecole:
    def __init__(self, monde, eleve):
        self.monde, self.eleve = monde, eleve
        self.ens = Enseignant(monde)
        self.jour_cours = 0
        self.exercice = None
        self.bulletin = []           # notes de qualification par jour

    def instruction(self):
        module = MODULES[self.jour_cours % len(MODULES)]
        t = self.ens.lecon(module)
        self.eleve.apprendre(t, f"lecon {module}")
        self.monde.noter("ecole_lecon", module=module, texte=t[:300])

    def exercice_du_jour(self):
        qs = self.ens.questions("classe")
        q, attendu, mode = qs[self.jour_cours % len(qs)]
        r = self.eleve.repondre(q)
        self.exercice = (q, attendu, mode, r)
        self.monde.noter("ecole_exercice", question=q, reponse=str(r)[:300], note=Enseignant.noter(r, attendu, mode))

    def debrief(self):
        if not self.exercice: return
        q, attendu, mode, r = self.exercice
        correction = f"Question : {q} Bonne reponse : {', '.join(str(a) for a in attendu)}."
        self.eleve.apprendre(correction, "debrief")
        self.monde.noter("ecole_debrief", correction=correction)
        self.jour_cours += 1

    def observer_marche(self):
        w = self.monde; p = next(h for h in w.habitants if h.eleve)
        m = w.marches[p.domicile.marche.id]
        vu = (f"Jour {w.jour}, au marche de {m.lieu.id} : la nourriture coute {m.prix['nourriture']:.1f}, le carburant "
              f"{m.prix['carburant']:.1f}, les remedes {m.prix['remedes']:.1f} drachmes ; il reste {m.stocks['remedes']:.0f} remedes.")
        self.eleve.apprendre(vu, "observation")

    def qualification(self):
        qs = self.ens.questions("epreuve")
        notes = []
        for q, attendu, mode in qs:
            r = self.eleve.repondre(q)
            notes.append(Enseignant.noter(r, attendu, mode))
            self.monde.noter("ecole_epreuve_question", question=q, reponse=str(r)[:300], note=notes[-1])
        score = sum(notes) / len(notes)
        self.bulletin.append({"jour": self.monde.jour, "score": score, "eleve": self.eleve.nom})
        self.monde.noter("ecole_qualification", score=round(score, 3), eleve=self.eleve.nom, n=len(qs))
        return score
