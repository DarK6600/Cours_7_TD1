"""Une recette à l'échelle : les ingrédients pour un nombre de personnes, en unités SI ou US."""

import argparse
import csv
from pathlib import Path
import subprocess

# ---- Les données -------------------------------------------------------------

PERSONNES_RECETTE = 4     # les recettes sont écrites pour 4 personnes

# Pour chaque unité : l'unité de l'autre système, et le nombre par lequel
# multiplier la quantité
VERS_US = {"g": ("oz", 1 / 28.3495), "ml": ("cup", 1 / 236.588)}
VERS_SI = {"oz": ("g", 28.3495), "cup": ("ml", 236.588)}

# Les chemins partent du dossier du script : __file__ est le chemin de ce fichier
RACINE = Path(__file__).parent
DONNEES = RACINE / "recettes"
SORTIE = RACINE / "sortie"


# ---- Les fonctions -----------------------------------------------------------

def lire_ingredients(chemin):
    """Les ingrédients du fichier CSV : une liste de (ingrédient, quantité, unité)."""
    ingredients = []
    with open(chemin, encoding="utf-8", newline="") as fichier:
        lecteur = csv.reader(fichier)
        next(lecteur)             # la première ligne nomme les colonnes
        for nom, quantite, unite in lecteur:
            ingredients.append((nom, float(quantite), unite))
    return ingredients


def ecrire_ingredients(chemin, ingredients):
    """Écrit les ingrédients dans un fichier CSV, avec les mêmes colonnes que les fichiers lus."""
    with open(chemin, "w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.writer(fichier)
        ecrivain.writerow(["ingredient", "quantite", "unite"])
        for nom, quantite, unite in ingredients:
            ecrivain.writerow([nom, round(quantite, 1), unite])


def afficher(ingredients):
    """Affiche une ligne par ingrédient : le nom, la quantité et l'unité."""
    for nom, quantite, unite in ingredients:
        print(nom, ":", round(quantite, 1), unite)


def adapter(ingredients, personnes_recette, personnes):
    """Les ingrédients pour `personnes` personnes, d'une recette écrite pour `personnes_recette` personnes."""
    facteur = personnes / personnes_recette
    resultat = []
    for nom, quantite, unite in ingredients:
        resultat.append((nom, quantite * facteur, unite))
    return resultat


def convertir(ingredients, table):
    """Les ingrédients, chaque unité présente dans `table` remplacée par celle de l'autre système."""
    resultat = []
    for nom, quantite, unite in ingredients:
        if unite in table:
            nouvelle_unite, facteur = table[unite]
            resultat.append((nom, quantite * facteur, nouvelle_unite))
        else:
            resultat.append((nom, quantite, unite))
    return resultat


def tableau(ingredients):
    rep = ["| Ingrédient | Quantité |\n", "|---|---|\n"]
    for ingredient, quantite, unite in ingredients:
        rep.append(f"| {ingredient} | {quantite} {unite} |\n")
    return rep


def ecrire_markdown(nom, quantite, unite, ingredients):
    tableau_ingredients = tableau(ingredients)
    with open((DONNEES / nom).with_suffix(".md"), "r", encoding="utf-8") as file:
        recette = file.read()

    texte = f"## Ingrédients pour {quantite} personnes, en unités {unite}\n\n{"".join(tableau_ingredients)}"
    recette = recette.replace("## Ingrédients", texte)
    with open((SORTIE / nom).with_suffix(".md"), "w", encoding="utf-8") as file:
        file.write(recette)

    return (SORTIE / nom).with_suffix(".md")


def ecrire_page(markdown):
    subprocess.run(["pandoc", markdown, "-o", markdown.with_suffix(".html"), "--standalone", "--css", RACINE / "style.css"])
    return markdown.with_suffix(".html")



# ---- Le programme -------------------------------------------------------------

# Les valeurs viennent de la ligne de commande
analyseur = argparse.ArgumentParser(description="Les ingrédients d'une recette pour un nombre de personnes, en unités SI ou US.")
analyseur.add_argument("nom", help="la recette : un fichier de recettes/, sans .csv")
analyseur.add_argument("-p", "--personnes", type=int, default=4, help="nombre de personnes (défaut : 4)")
analyseur.add_argument("-u", "--unites", choices=("SI", "US"), default="SI", help="système d'unités (défaut : SI)")
analyseur.add_argument("--page", action="store_true")
options = analyseur.parse_args()
NOM = options.nom
PERSONNES = options.personnes
UNITES = options.unites

ingredients = lire_ingredients(DONNEES / (NOM + ".csv"))
ingredients = adapter(ingredients, PERSONNES_RECETTE, PERSONNES)

if UNITES == "US":
    ingredients = convertir(ingredients, VERS_US)
else:
    ingredients = convertir(ingredients, VERS_SI)

print(NOM, "pour", PERSONNES, "personnes, en unités", UNITES)
afficher(ingredients)

# Le résultat, dans sortie/
SORTIE.mkdir(exist_ok=True)
fichier = SORTIE / (NOM + "_" + str(PERSONNES) + "_" + UNITES + ".csv")
ecrire_ingredients(fichier, ingredients)
print("écrit :", fichier)

if options.page:
    markdown = ecrire_markdown(NOM, PERSONNES, UNITES, ingredients)
    page = ecrire_page(markdown)