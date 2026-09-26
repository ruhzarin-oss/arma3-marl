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
        is_sunday = (dow == 3)
        is_saturday = (dow == 2)
        is_friday = (dow == 5)
        market_open = not is_sunday

        # Best food price
        prix_nour = 4.0
        for m in marches.values():
            if isinstance(m, dict):
                n = m.get("nourriture", {})
                if isinstance(n, dict) and n.get("prix"):
                    p = float(n["prix"])
                    if p < prix_nour:
                        prix_nour = p

        menages = max(1, int(pop.get("menages", 5000)))
        menages_sans_nour = int(pop.get("menages_sans_nourriture", 0))
        marge_faim = float(pop.get("marge_faim", 0.0))
        nour_reserve = int(stocks.get("nourriture_population", 0))

        # Target reserve: build up before weekend
        if is_friday:
            target = menages * 3
        elif is_saturday:
            target = menages * 2
        elif menages_sans_nour > 0 or marge_faim < 0.1:
            target = menages * 2
        else:
            target = menages * 1

        # === FOOD: buy from market (PRIMARY) ===
        if market_open and nour_reserve < target:
            budget_int = fin.get("budget", {}).get("interieur", {})
            credit_int = float(budget_int.get("credit", 0))
            exec_int = float(budget_int.get("execute", 0))
            avail_int = max(0.0, credit_int - exec_int)

            needed = int(target - nour_reserve)
            max_affordable = int(avail_int / max(1.0, prix_nour))

            # Buy in chunks of 800, up to 5 chunks
            for _ in range(5):
                if needed <= 0 or max_affordable <= 0 or len(actions) >= 6:
                    break
                qty = min(800, needed, max_affordable)
                if qty > 80:
                    actions.append({"type": "acheter", "bien": "nourriture", "quantite": qty, "destination": "population"})
                    needed -= qty
                    max_affordable -= qty

        # === IMPORT as backup if still short ===
        if nour_reserve < menages * 1.5 and market_open and len(actions) < 7:
            budget_int = fin.get("budget", {}).get("interieur", {})
            credit_int = float(budget_int.get("credit", 0))
            exec_int = float(budget_int.get("execute", 0))
            avail_int = max(0.0, credit_int - exec_int)
            imp_price = prix_nour * 1.2
            qty_imp = min(500, int(avail_int / max(1.0, imp_price)))
            if qty_imp > 50:
                actions.append({"type": "importer", "bien": "nourriture", "quantite": qty_imp})

        # === SUBVENTIONS (helps all days, critical on Sunday) ===
        budget_subv = fin.get("budget", {}).get("subventions", {})
        credit_subv = float(budget_subv.get("credit", 0))
        exec_subv = float(budget_subv.get("execute", 0))
        avail_subv = max(0.0, credit_subv - exec_subv)

        if avail_subv > 500 and len(actions) < 8:
            if menages_sans_nour > 0:
                montant = min(int(avail_subv * 0.95), 500000)
            elif is_saturday or is_friday:
                montant = min(int(avail_subv * 0.7), 350000)
            elif marge_faim < 0.15:
                montant = min(int(avail_subv * 0.6), 250000)
            else:
                montant = min(int(avail_subv * 0.4), 150000)
            if montant > 500:
                actions.append({"type": "subvention", "cible": "menages_pauvres", "montant": montant})

        # === HEALTH ===
        infectes = int(sante.get("infectes", 0))
        nouveaux = int(sante.get("nouveaux_cas", 0))
        remedes_stock = int(stocks.get("remedes", 0))
        if (infectes >= 1 or nouveaux >= 1) and remedes_stock < 30 and len(actions) < 8:
            prix_rem = 35.0
            for m in marches.values():
                if isinstance(m, dict):
                    r = m.get("remedes", {})
                    if isinstance(r, dict) and r.get("prix"):
                        p = float(r["prix"])
                        if p < prix_rem:
                            prix_rem = p
            budget_sant = fin.get("budget", {}).get("sante", {})
            credit_sant = float(budget_sant.get("credit", 0))
            exec_sant = float(budget_sant.get("execute", 0))
            avail_sant = max(0.0, credit_sant - exec_sant)
            if avail_sant > prix_rem * 10:
                qty_rem = min(20, int(avail_sant / max(1.0, prix_rem)) - 2)
                if qty_rem > 0:
                    actions.append({"type": "acheter", "bien": "remedes", "quantite": qty_rem, "destination": "hopitaux"})

        # === FINANCES (emergency only) ===
        caisse = float(fin.get("caisse", 0))
        coussin = float(fin.get("coussin", 0))
        if coussin > 0 and caisse < coussin * 0.05 and len(actions) < 8:
            montant_d = int(min(coussin * 0.05, 150000))
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
