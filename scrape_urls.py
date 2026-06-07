"""
Step 1: Scrape all recipe URLs from the Pharmacopeia index pages.
Outputs: data/recipe_urls.json

Run: python scrape_urls.py
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

BASE_URL = "https://www.pascalbonenfant.com/18c/medicine/"
DATA_DIR = Path(__file__).parent / 'data'

# All index pages from the main pharmacopeia page
INDEX_PAGES = [
    # Thomas Fuller - Pharmacopeia Extemporanea (1710)
    ("index_ale.html", "Ales", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_bag_cake.html", "Bags, Balsams, Boluses, Broths and Cakes", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_cataplasm_caudle.html", "Cataplasms and Caudles", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_decoction.html", "Decoctions", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_draught.html", "Diets and Draughts", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_electuary.html", "Electuaries", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_eleo_essence.html", "Eleosacchara, Elixirs, Emetics, Emulsions, Epithems, Errhines and Essences", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_expression.html", "Expressions and Extracts", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_foment_fume.html", "Foments, Frontals and Fumes", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_gargle.html", "Gargles", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_glyster.html", "Glysters", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_honey_infusion.html", "Honeys, Hydrogalas, Hydromels and Infusions", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_juice_julep.html", "Juices and Juleps", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_lambative_lohoch.html", "Lambatives, Laudanums, Lavaments, Liniments, Litus, Lixivia and Lohochs", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_lotion_masticatory.html", "Lotions, Lozenges and Masticatories", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_mixture.html", "Mixtures", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_nodule_pellet.html", "Nodules, Oils, Oxymels, Pastes and Pellets", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_pill.html", "Pills", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_plaister.html", "Plaisters", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_posset_potion.html", "Possets and Potions", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_powder.html", "Powders", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_ptisan_syrup.html", "Ptisans, Quilts, Robs, Sudorificks, Spirits, Stones, Sugars, Suppositories and Syrups", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_tincture_tobacco.html", "Tinctures and Tobaccos", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_unguent.html", "Unguents", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    ("index_vapour_wine.html", "Vapours, Wafers, Waters, Wheys and Wines", "Thomas Fuller", "Pharmacopeia Extemporanea", 1710),
    # William Buchan - Domestic Medicine (1785)
    ("index_balsam_collyrium.html", "Balsams, Boluses, Cataplasms, Clysters and Collyria", "William Buchan", "Domestic Medicine", 1785),
    ("index_confection_draught.html", "Confections, Conserves, Decoctions, Draughts", "William Buchan", "Domestic Medicine", 1785),
    ("index_electuary_gargle.html", "Electuaries, Emulsions, Extracts, Fomentations and Gargles", "William Buchan", "Domestic Medicine", 1785),
    ("index_infusion_mixture.html", "Infusions, Juleps and Mixtures", "William Buchan", "Domestic Medicine", 1785),
    ("index_ointment_pill.html", "Ointments and Pills", "William Buchan", "Domestic Medicine", 1785),
    ("index_plaster_powder.html", "Plasters and Powders", "William Buchan", "Domestic Medicine", 1785),
    ("index_simple_syrup.html", "Simple and Spirituous Waters and Syrups", "William Buchan", "Domestic Medicine", 1785),
    ("index_tincture.html", "Tinctures", "William Buchan", "Domestic Medicine", 1785),
    ("index_vinegar_wine.html", "Vinegars, Wheys and Wines", "William Buchan", "Domestic Medicine", 1785),
]

# Twigge recipes are linked directly from the main page, not from an index
TWIGGE_RECIPES = [
    ("recipes/wt_bloody_flux.html", "For the bloody flux"),
    ("recipes/wt_gravill_bath.html", "A bath for the gravill"),
    ("recipes/wt_plurisy_water.html", "The recept of the plurisy water"),
    ("recipes/wt_rickets_oyle.html", "To make the oyle for the rickets"),
    ("recipes/wt_snail_water.html", "To make the snaile water for the consumsion or cough of the lungs"),
    ("recipes/wt_surfeet_water.html", "A receipt to make surfeet water"),
    ("recipes/wt_burn_treatment.html", "To heale a burn without a scarr"),
    ("recipes/wt_jaundice_treatment.html", "For jaundice in children"),
    ("recipes/wt_purging_ale.html", "The ingredients of the purging ale"),
    ("recipes/wt_salve_for_ulcers.html", "A salve for old sores and ulcers"),
    ("recipes/wt_stitch_medicine.html", "An excellent medicine for a stitch"),
]


def scrape_index_page(index_file, category, author, work, year):
    """Scrape a single index page for recipe links."""
    url = BASE_URL + index_file
    print(f"  Fetching: {url}")

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    content = soup.find('div', id='content')
    if not content:
        print("    ERROR: No content div found")
        return []

    recipes = []
    for link in content.find_all('a'):
        href = link.get('href', '')
        name = link.get_text(strip=True)
        if href.startswith('recipes/') and name:
            full_url = BASE_URL + href
            recipes.append({
                'name': name.rstrip('.'),
                'url': full_url,
                'category': category,
                'source_author': author,
                'source_work': work,
                'source_year': year,
            })

    print(f"    Found {len(recipes)} recipes")
    return recipes


def main():
    all_recipes = []

    print("Scraping Fuller & Buchan index pages...\n")
    for index_file, category, author, work, year in INDEX_PAGES:
        recipes = scrape_index_page(index_file, category, author, work, year)
        all_recipes.extend(recipes)
        time.sleep(1)  # be polite

    # Add Twigge recipes manually
    print("\nAdding Rev. Twigge recipes...")
    for href, name in TWIGGE_RECIPES:
        all_recipes.append({
            'name': name,
            'url': BASE_URL + href,
            'category': 'Notebook Remedies',
            'source_author': 'Rev. William Twigge',
            'source_work': 'Notebook',
            'source_year': 1715,
        })

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_recipes:
        if r['url'] not in seen:
            seen.add(r['url'])
            unique.append(r)

    print(f"\n{'='*50}")
    print(f"Total unique recipe URLs found: {len(unique)}")
    print(f"{'='*50}")

    # Save
    DATA_DIR.mkdir(exist_ok=True)
    output = DATA_DIR / 'recipe_urls.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output}")


if __name__ == '__main__':
    main()
