#!/usr/bin/env python3
"""LES FICHES DU MANUEL de CMO ( « CMO manual EBOOK.pdf », extrait en texte dans cmo_carte/manuel.txt ) :

1. la CARTE DES MÉCANISMES ( cmo_carte/carte_*.json, 922 mécanismes déjà résumés en français avec section et lignes du
   manuel ) : une fiche par mécanisme ;
2. le MANUEL lui-même, découpé en passages d'environ 150 mots anglais par section, traduits en français par un modèle de
   traduction LOCAL sur CPU ( Helsinki-NLP/opus-mt-en-fr, MarianMT ) ; le texte anglais d'origine reste dans la fiche
   ( champ texte_en ) pour les termes du jeu ( « Weapons Free », « Bingo », « WRA » ) que la traduction automatique abîme.

Le texte extrait du PDF code la ligature « f » en saut de page ( \\f ) : remise en « f ». Les numéros de page sont les
lignes qui ne portent qu'un nombre ( pied de page ), pris dans l'ordre croissant : la page d'une ligne est le premier
numéro qui la suit. Pagination IMPRIMÉE du manuel ( celle de sa table des matières ).

    OMP_NUM_THREADS=2 taskset -c 0,1 nice -n 19 /mnt/data/hmt/savoir_env/bin/python savoir/fiches_manuel.py [--sans-traduction]
    ( la guerre CMO tourne sur la même station : 2 fils au plus, sinon elle ralentit sous x0,9 )
"""
import glob
import json
import os
import re
import sys
import time

CARTE = "/mnt/data/hmt/etat/cmo_carte"
MANUEL = os.path.join(CARTE, "manuel.txt")
SORTIE = "/mnt/data/hmt/etat/cmo_savoir/fiches"
CACHE = "/mnt/data/hmt/etat/cmo_savoir/cache_traduction.json"
PDF = "CMO manual EBOOK.pdf"
MODELE_TRAD = "Helsinki-NLP/opus-mt-en-fr"
MOTS_PASSAGE, MOTS_MAX = 150, 190
# Ce qui n'est pas traduit : table des matières, introduction historique, raccourcis clavier.
SAUTER = [(1, 393), (10104, 10226)]
ENTETE = re.compile(r"^\s*f?\s*C\s*O\s*M\s*M?\s*AND\s+MOD\s*ERN", re.I)
NUMERO = re.compile(r"^\s*(\d{1,3})\s*$")
TITRE = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+([A-Z“\"][^\n]{1,70})$")
VERSION = re.compile(r"^\s*(VERSION\s+[\d.]+[^\n]{0,40}|BUILD\s+[\d.]+[^\n]{0,40})$")

# Corrections des contresens fréquents de la traduction automatique sur le vocabulaire de CMO ( relus sur des passages ).
POST = [("Armes gratuites", "Armes libres (Weapons Free)"), ("armes gratuites", "armes libres (Weapons Free)"),
        ("Armes serrées", "Armes restreintes (Weapons Tight)"), ("armes serrées", "armes restreintes (Weapons Tight)"),
        ("Autorité de libération des armes", "autorisation de tir des armes (WRA)"),
        ("autorité de libération des armes", "autorisation de tir des armes (WRA)"),
        ("Commandement : Opérations modernes", "Command: Modern Operations"), ("COMMANDE", "COMMAND"),
        ("la Commande", "Command"), ("Commande", "Command"),
        ("radar de contrôle des incendies", "radar de conduite de tir"), ("contrôle des incendies", "conduite de tir"),
        ("contrôle d'incendie", "conduite de tir"), ("système de lutte contre l'incendie", "système de conduite de tir"),
        ("commande d'incendie détaillée de l'arme à feu", "conduite de tir détaillée des canons"),
        ("portée d'incendie automatique", "portée de tir automatique"), ("En cas d'incendie d'occasion", "Avec le tir d'opportunité"),
        ("l'ensemble du côté", "tout le camp"), ("de tous les côtés", "de tout le camp")]


def lire():
    """( lignes, page de chaque ligne, indices des lignes « numéro de page » ). Un \\f en tête de ligne suivi d'un blanc,
    d'un chiffre ou de la fin de ligne est un vrai saut de page ; ailleurs c'est la ligature « f »."""
    brut = open(MANUEL, encoding="utf-8").read().split("\n")
    lignes = [re.sub(r"^\f(?=[\s\d]|$)", "", l).replace("\f", "f") for l in brut]
    marques, prec = [], None
    for i, l in enumerate(lignes):
        m = NUMERO.match(l)
        if m:
            n = int(m.group(1))
            if (prec is None and i > 300 and n < 40) or (prec is not None and prec < n <= prec + 4):
                marques.append((i, n))
                prec = n
    page, k = [0] * len(lignes), 0
    for i in range(len(lignes)):
        while k < len(marques) and marques[k][0] < i:
            k += 1
        page[i] = marques[k][1] if k < len(marques) else (marques[-1][1] + 1 if marques else 0)
    return lignes, page, {i for i, _ in marques}


def page_de(page, lignes_txt):
    """« 8411-8417 » ( numéros 1-based de manuel.txt ) -> « p. 281 » ou « p. 281-282 »."""
    nums = [int(x) for x in re.findall(r"\d+", str(lignes_txt or ""))][:2]
    if not nums:
        return ""
    a = page[max(0, min(len(page) - 1, nums[0] - 1))]
    b = page[max(0, min(len(page) - 1, nums[-1] - 1))]
    return f"p. {a}" if a == b else f"p. {a}-{b}"


# ============================================================================================ 1. LA CARTE
def fiches_carte(page):
    out = []
    for f in sorted(glob.glob(os.path.join(CARTE, "carte_*.json"))):
        court = os.path.basename(f)[6:-5]
        for k, x in enumerate(json.load(open(f)), 1):
            quoi = x.get("ce_que_cmo_simule") or x.get("ce_que_cmo_permet") or ""
            lignes_txt = x.get("lignes") or x.get("source", "")
            pg = page_de(page, lignes_txt)
            t = [f"{x['mecanisme']} ( domaine : {x['domaine']} ). {quoi}"]
            if x.get("version"):
                t.append(f"Apparu dans {x['version']} ; présent dans la 1.10 build 1900.20 : {x.get('present_en_1900_20', '?')}.")
            if x.get("leviers_lua"):
                t.append("Leviers Lua : " + ", ".join(x["leviers_lua"]) + ".")
            if x.get("notre_pont"):
                t.append(f"Notre pont HMT : {x['notre_pont']}.")
            if x.get("interet_guerre_reelle"):
                t.append(f"Intérêt pour la guerre réelle : {x['interet_guerre_reelle']}.")
            if x.get("piege"):
                t.append(f"Piège : {x['piege']}")
            sec = x.get("section_manuel", "")
            src = f"{PDF}" + (f", § {sec}" if sec else "") + (f", {pg}" if pg else "") + \
                  f" (manuel.txt l. {re.sub(r'^manuel l. ', '', str(lignes_txt))}) ; carte des mécanismes cmo_carte/{os.path.basename(f)} n° {k}"
            typ = "lua" if x["domaine"] in ("Lua",) else ("doctrine" if "doctrine" in x["domaine"] or x["domaine"] in ("EMCON", "WRA", "règles d'engagement") else "mecanisme")
            out.append({"id": f"meca-{court}-{k:03d}", "type": typ, "titre": f"{x['mecanisme']} — {x['domaine']} (carte CMO)",
                        "texte": " ".join(t), "source": src, "tags": ["mécanisme", x["domaine"], court] + ([f"§{sec}"] if sec else []),
                        "chiffres": {"section": sec, "lignes": lignes_txt, "page": pg}})
    return out


# ============================================================================================ 2. LE MANUEL
def passages(lignes, page, marques):
    """[ { section, titre, a, b, texte_en } ] : passages d'environ MOTS_PASSAGE mots, sans franchir une section."""
    sauter = set()
    for a, b in SAUTER:
        sauter.update(range(a - 1, b))
    out, cur = [], None
    section, titre, chapitre = "", "", ""

    def fermer():
        nonlocal cur
        if cur and len(" ".join(cur["paras"]).split()) >= 12:
            cur["texte_en"] = " ".join(p.strip() for p in cur["paras"] if p.strip())
            del cur["paras"]
            out.append(cur)
        cur = None

    para, debut = [], [0]

    def pousser_para(i):
        nonlocal para, cur
        if not para:
            return
        txt = ""
        for l in para:
            l = l.strip()
            if txt.endswith("-") and l[:1].islower():
                txt = txt + l
            else:
                txt = (txt + " " + l).strip()
        para = []
        if cur is None:
            cur = {"section": section, "titre": titre, "a": debut[0] + 1, "b": i + 1, "paras": []}
        cur["paras"].append(txt)
        cur["b"] = i + 1
        if len(" ".join(cur["paras"]).split()) >= MOTS_PASSAGE:
            fermer()

    for i, l in enumerate(lignes):
        if i in sauter or i in marques or ENTETE.match(l):
            continue
        s = l.strip()
        m = TITRE.match(l)
        v = VERSION.match(l)
        if m and not s.endswith(".") and len(s) < 80:
            num, t = m.group(1), m.group(2).strip()
            tup = tuple(int(x) for x in num.split("."))
            cur_t = tuple(int(x) for x in section.split(".")) if re.fullmatch(r"[\d.]+", section or "") else (0,)
            chap = cur_t[0]
            if "." not in num and t.upper() == t and num == chapitre:
                continue                                  # titre courant de chapitre en haut de page
            ok = tup > cur_t and tup[0] in (chap, chap + 1) and ("." in num or t.upper() == t)
            if ok:
                pousser_para(i)
                fermer()
                section, titre = num, t.title() if t.isupper() else t
                if "." not in num:
                    chapitre = num
                continue
        if v:
            pousser_para(i)
            fermer()
            section, titre = "historique", v.group(1).strip().title()
            continue
        if not s:
            pousser_para(i)
            continue
        if s.startswith("§") or s.startswith("•"):
            pousser_para(i)
        if not para:
            debut[0] = i
        para.append(s.lstrip("§• ").strip() if s[:1] in "§•" else s)
        if len(" ".join(para).split()) > MOTS_MAX:
            pousser_para(i)
    pousser_para(len(lignes) - 1)
    fermer()
    for p in out:
        p["page"] = f"p. {page[p['a'] - 1]}" if page[p["a"] - 1] == page[p["b"] - 1] else f"p. {page[p['a'] - 1]}-{page[p['b'] - 1]}"
    return out


PHRASE = re.compile(r"(?<=[.!?:;])\s+(?=[A-Z“\"(])")


def phrases(texte):
    out = []
    for p in PHRASE.split(texte):
        p = p.strip()
        while len(p.split()) > 80:                         # une phrase trop longue pour le modèle : coupée aux virgules
            mots = p.split()
            out.append(" ".join(mots[:60]))
            p = " ".join(mots[60:])
        if p:
            out.append(p)
    return out


class Traducteur:
    def __init__(self):
        import torch
        from transformers import MarianMTModel, MarianTokenizer
        torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))   # CMO tourne à côté : 2 fils au plus
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        self.torch = torch
        self.tok = MarianTokenizer.from_pretrained(MODELE_TRAD)
        self.m = MarianMTModel.from_pretrained(MODELE_TRAD).eval()
        self.cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

    def traduire(self, liste, lot=24):
        a_faire = sorted({p for p in liste if p not in self.cache}, key=len)
        t0, n = time.time(), 0
        for k in range(0, len(a_faire), lot):
            paquet = a_faire[k:k + lot]
            with self.torch.no_grad():
                b = self.tok(paquet, return_tensors="pt", padding=True, truncation=True, max_length=400)
                o = self.m.generate(**b, num_beams=2, max_new_tokens=min(512, int(b["input_ids"].shape[1] * 2) + 16))
            for src, out in zip(paquet, o):
                self.cache[src] = self.tok.decode(out, skip_special_tokens=True)
            n += len(paquet)
            if (k // lot) % 20 == 0:
                print(f"  traduit {n}/{len(a_faire)} phrases, {time.time() - t0:.0f} s", flush=True)
                json.dump(self.cache, open(CACHE, "w"), ensure_ascii=False)
        json.dump(self.cache, open(CACHE, "w"), ensure_ascii=False)
        return {p: self.cache.get(p, p) for p in liste}


def post(t):
    for a, b in POST:
        t = t.replace(a, b)
    return t


def fiches_manuel(lignes, page, marques, traduire=True):
    ps = passages(lignes, page, marques)
    toutes = [ph for p in ps for ph in phrases(p["texte_en"])]
    titres = sorted({p["titre"] for p in ps})
    print(f"{len(ps)} passages, {len(toutes)} phrases, {sum(len(p['texte_en'].split()) for p in ps)} mots", flush=True)
    tr = Traducteur().traduire(toutes + titres) if traduire else {x: x for x in toutes + titres}
    out = []
    for k, p in enumerate(ps, 1):
        fr = post(" ".join(tr[ph] for ph in phrases(p["texte_en"])))
        titre_fr = post(tr.get(p["titre"], p["titre"]))
        sec = p["section"]
        ent = f"§ {sec} « {p['titre']} »" if sec != "historique" else f"historique des versions « {p['titre']} »"
        out.append({"id": f"manuel-{k:04d}", "type": "mecanisme",
                    "titre": f"Manuel CMO {ent} — {titre_fr} ({p['page']})",
                    "texte": fr, "texte_en": p["texte_en"],
                    "source": f"{PDF}, {ent}, {p['page']} (manuel.txt l. {p['a']}-{p['b']}) ; traduction automatique locale {MODELE_TRAD}",
                    "tags": ["manuel", f"§{sec}", p["titre"]], "chiffres": {"section": sec, "page": p["page"], "lignes": f"{p['a']}-{p['b']}"}})
    return out


def ecrire(nom, fiches):
    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, f"{nom}.jsonl"), "w") as f:
        for x in fiches:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"{nom:20s} {len(fiches):6d} fiches", flush=True)


if __name__ == "__main__":
    lignes, page, marques = lire()
    ecrire("manuel_carte", fiches_carte(page))
    ecrire("manuel_passages", fiches_manuel(lignes, page, marques, traduire="--sans-traduction" not in sys.argv))
