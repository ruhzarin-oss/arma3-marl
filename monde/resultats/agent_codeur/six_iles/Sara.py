def gouverner(b, memoire):
    actions = []
    try:
        pop = b.get("population", {})
        sante = b.get("sante", {})
        fin = b.get("finances", {})
        stocks = b.get("stocks_publics", {})
        jour = int(b.get("jour", 1))
        marches = b.get("marches", {})

        dow = jour % 7
        market_open = (dow != 3)

        prix_nour = 4.0
        prix_rem = 35.0
        for m in marches.values():
            if isinstance(m, dict):
                if "nourriture" in m and m["nourriture"].get("prix"):
                    prix_nour = float(m["nourriture"]["prix"])
                if "remedes" in m and m["remedes"].get("prix"):
                    prix_rem = float(m["remedes"]["prix"])

        menages = max(1, int(pop.get("menages", 5000)))
        menages_sans_nour = int(pop.get("menages_sans_nourriture", 0))
        marge_faim = float(pop.get("marge_faim", 0.0))
        nour_reserve = int(stocks.get("nourriture_population", 0))
        remedes_stock = int(stocks.get("remedes", 0))

        # Target: stock up before closure (dow 3)
        if dow in (1, 2):
            target = menages * 3
        elif dow == 0:
            target = menages * 2
        else:
            target = menages * 2

        # === FOOD: buy from market, max 1000 per action, up to 3 actions ===
        if market_open and nour_reserve < target:
            needed = target - nour_reserve
            max_q = 1000
            count = 0
            while needed > 0 and count < 3:
                q = min(max_q, needed)
                if q >= 50:
                    actions.append({"type": "acheter", "bien": "nourriture", "quantite": q, "destination": "population"})
                    needed -= q
                    count += 1

        # === IMPORT if reserve still critically low ===
        if nour_reserve < menages and len(actions) < 6:
            q = min(800, menages - nour_reserve)
            if q >= 50:
                actions.append({"type": "importer", "bien": "nourriture", "quantite": q})

        # === SUBVENTIONS: primary anti-hunger lever ===
        budget_subv = fin.get("budget", {}).get("subventions", {})
        credit_subv = float(budget_subv.get("credit", 0))
        exec_subv = float(budget_subv.get("execute", 0))
        avail_subv = max(0.0, credit_subv - exec_subv)

        if avail_subv > 500:
            if menages_sans_nour > 0 or nour_reserve < menages * 0.5:
                montant = min(int(avail_subv), 300000)
            elif marge_faim < 0.15:
                montant = min(int(avail_subv * 0.7), 250000)
            elif nour_reserve < menages:
                montant = min(int(avail_subv * 0.5), 200000)
            else:
                montant = min(int(avail_subv * 0.3), 150000)
            if montant > 500:
                actions.append({"type": "subvention", "cible": "menages_pauvres", "montant": montant})

        # === HEALTH: ensure remedies ===
        infectes = int(sante.get("infectes", 0))
        nouveaux = int(sante.get("nouveaux_cas", 0))
        if (infectes >= 1 or nouveaux >= 1) and remedes_stock < 30:
            qty_rem = min(15, max(5, 30 - remedes_stock))
            actions.append({"type": "acheter", "bien": "remedes", "quantite": qty_rem, "destination": "hopitaux"})

        # === FINANCES: emergency debt only ===
        caisse = float(fin.get("caisse", 0))
        coussin = float(fin.get("coussin", 0))
        if caisse < coussin * 0.12:
            montant_d = min(int(coussin * 0.12 - caisse + 30000), 80000)
            if montant_d > 0:
                actions.append({"type": "emettre_dette", "montant": montant_d, "duree_j": 364})

        # === MEMOIRE ===
        memoire["jour"] = jour
        memoire["nour_reserve"] = nour_reserve
        memoire["menages"] = menages
        memoire["menages_sans_nour"] = menages_sans_nour
        memoire["marge_faim"] = marge_faim

    except Exception:
        actions = []

    if not actions:
        actions.append({"type": "rien"})

    return actions[:8]
