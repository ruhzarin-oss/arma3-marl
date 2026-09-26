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

        # Target: 8 days buffer normally, 12 days before weekend
        target_reserve = menages * 8
        if dow in (4, 5):
            target_reserve = menages * 12

        # === FOOD: buy from local market on open days ===
        if market_open and nour_reserve < target_reserve:
            budget_int = fin.get("budget", {}).get("interieur", {})
            credit_int = float(budget_int.get("credit", 0))
            exec_int = float(budget_int.get("execute", 0))
            avail = max(0.0, credit_int - exec_int)

            needed = target_reserve - nour_reserve
            qty1 = min(int(needed), 600)
            if qty1 > 10:
                actions.append({"type": "acheter", "bien": "nourriture", "quantite": qty1, "destination": "population"})

            remaining = target_reserve - nour_reserve - qty1
            if remaining > 100:
                qty2 = min(int(remaining), 400)
                if qty2 > 10:
                    actions.append({"type": "acheter", "bien": "nourriture", "quantite": qty2, "destination": "population"})

        # === FOOD: import to supplement ===
        if nour_reserve < menages * 5 and len(actions) < 6:
            budget_int = fin.get("budget", {}).get("interieur", {})
            credit_int = float(budget_int.get("credit", 0))
            exec_int = float(budget_int.get("execute", 0))
            avail = max(0.0, credit_int - exec_int)
            imp_price = prix_nour * 1.2
            qty_imp = min(400, int(avail / imp_price))
            if qty_imp > 20:
                actions.append({"type": "importer", "bien": "nourriture", "quantite": qty_imp})

        # === SUBVENTIONS: aggressive, primary anti-hunger tool ===
        budget_subv = fin.get("budget", {}).get("subventions", {})
        credit_subv = float(budget_subv.get("credit", 0))
        exec_subv = float(budget_subv.get("execute", 0))
        avail_subv = max(0.0, credit_subv - exec_subv)

        if avail_subv > 500:
            if menages_sans_nour > 0:
                montant = min(int(avail_subv), 600000)
            elif nour_reserve < menages * 3:
                montant = min(int(avail_subv * 0.9), 400000)
            elif marge_faim < 0.3:
                montant = min(int(avail_subv * 0.7), 250000)
            else:
                montant = min(int(avail_subv * 0.5), 150000)
            if montant > 100:
                actions.append({"type": "subvention", "cible": "menages_pauvres", "montant": montant})

        # === HEALTH ===
        infectes = int(sante.get("infectes", 0))
        nouveaux = int(sante.get("nouveaux_cas", 0))
        if (infectes >= 1 or nouveaux >= 1) and remedes_stock < 40:
            budget_sant = fin.get("budget", {}).get("sante", {})
            credit_sant = float(budget_sant.get("credit", 0))
            exec_sant = float(budget_sant.get("execute", 0))
            avail_sant = max(0.0, credit_sant - exec_sant)
            if avail_sant > prix_rem * 10:
                qty_rem = min(30, int(avail_sant / prix_rem) - 1)
                if qty_rem > 0:
                    actions.append({"type": "acheter", "bien": "remedes", "quantite": qty_rem, "destination": "hopitaux"})

        # === FINANCES: emergency only ===
        caisse = float(fin.get("caisse", 0))
        coussin = float(fin.get("coussin", 0))
        if caisse < coussin * 0.2:
            montant_d = min(int(coussin * 0.2 - caisse + 10000), 200000)
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
