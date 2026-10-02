"""Un théâtre de PAPIER pour la porte de la guerre réelle ( porte_guerre_reelle.py ) : une base par camp, quatre avions par
camp ( deux en frappe ), une unité au sol par camp. Les fichiers .inst sont fournis au faux CMO par la porte."""
CAMPS = ("OTAN", "Russie-Chine")
PAYS = {"Poland": ("OTAN", 1.0, "papier"), "Russia [1992-]": ("Russie-Chine", 0.25, "papier")}
INSTALLATIONS = [("Test/Malbork.inst", "OTAN", "Poland", "chasse"),
                 ("Test/Tchkalovsk.inst", "Russie-Chine", "Russia [1992-]", "chasse")]
FLOTTES = [("Test/Malbork.inst", "Poland", 7087, 4, 0.5), ("Test/Tchkalovsk.inst", "Russia [1992-]", 6210, 4, 0.5)]
SOL = [("Poland", 3659, "HIMARS", 54.20, 19.80), ("Russia [1992-]", 254, "Iskander-M", 54.63, 21.81)]
LANCEURS = {254, 3659}
