"""
Step 2: Visit each recipe URL, cache the HTML locally, and extract all data.
Reads: data/recipe_urls.json
Outputs:
    data/cache/*.html         (raw HTML for every page - never re-scrape)
    data/recipes.csv          (full recipe data)
    data/ingredients.csv      (parsed ingredients with metric)
    data/recipes_full.json    (everything in one JSON for backup)

Run: python scrape_recipes.py

Resume-safe: skips pages already in cache/ unless --force flag is used.
"""
import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
import sys
from pathlib import Path
from urllib.parse import urlparse

DATA_DIR = Path(__file__).parent / 'data'
CACHE_DIR = DATA_DIR / 'cache'

# Apothecary unit patterns for ingredient parsing
UNITS = [
    'pounds', 'pound', 'ounces', 'ounce', 'drams', 'dram', 'drachms', 'drachm',
    'scruples', 'scruple', 'grains', 'grain', 'pints', 'pint', 'quarts', 'quart',
    'gallons', 'gallon', 'handfuls', 'handful', 'drops', 'drop', 'minims', 'minim',
]

# Using apothecary ounce (31.1g) as per the source site's own conversion table
METRIC_CONVERSIONS = {
    'pound': (373, 'g'),
    'pounds': (373, 'g'),
    'ounce': (31.1, 'g'),
    'ounces': (31.1, 'g'),
    'dram': (3.89, 'g'),
    'drams': (3.89, 'g'),
    'drachm': (3.89, 'g'),
    'drachms': (3.89, 'g'),
    'scruple': (1.296, 'g'),
    'scruples': (1.296, 'g'),
    'grain': (0.0648, 'g'),
    'grains': (0.0648, 'g'),
    'pint': (473, 'ml'),
    'pints': (473, 'ml'),
    'quart': (946, 'ml'),
    'quarts': (946, 'ml'),
    'gallon': (3785, 'ml'),
    'gallons': (3785, 'ml'),
    'drop': (0.062, 'ml'),
    'drops': (0.062, 'ml'),
    'minim': (0.062, 'ml'),
    'minims': (0.062, 'ml'),
    'handful': (1, 'handful'),
    'handfuls': (1, 'handfuls'),
}

NUMBER_WORDS = {
    'half': 0.5, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
    'twelve': 12, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
}


def url_to_cache_filename(url):
    """Convert URL to a safe local filename."""
    path = urlparse(url).path
    # e.g. /18c/medicine/recipes/tf_1_cancer_ale.html -> tf_1_cancer_ale.html
    return Path(path).name


def fetch_page(url, force=False):
    """Fetch page HTML, using cache if available."""
    cache_file = CACHE_DIR / url_to_cache_filename(url)

    if cache_file.exists() and not force:
        return cache_file.read_text(encoding='utf-8'), True  # (html, from_cache)

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text
        cache_file.write_text(html, encoding='utf-8')
        return html, False
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return None, False


def extract_all_data(html, url):
    """Extract everything useful from a recipe page."""
    soup = BeautifulSoup(html, 'html.parser')

    data = {
        'page_title': '',
        'meta_description': '',
        'full_text': '',
        'instructions': '',
        'notes': '',
        'recipe_number': None,
        'related_links': [],
        'all_paragraphs': [],
    }

    # Page title
    title_tag = soup.find('title')
    if title_tag:
        data['page_title'] = title_tag.get_text(strip=True)

    # Meta description
    meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)})
    if meta and meta.get('content'):
        data['meta_description'] = meta['content']

    # Content div
    content = soup.find('div', id='content')
    if not content:
        return data

    # Full text of content div (preserve for future re-parsing)
    data['full_text'] = content.get_text(separator='\n', strip=True)

    # All paragraphs as individual items
    paragraphs = content.find_all('p')
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text:
            data['all_paragraphs'].append(text)

    # Recipe number from h3 (e.g. "2. Cancer Ale.")
    h3 = content.find('h3')
    if h3:
        h3_text = h3.get_text(strip=True)
        num_match = re.match(r'^(\d+)\.?\s+', h3_text)
        if num_match:
            data['recipe_number'] = int(num_match.group(1))

    # Instructions: first paragraph starting with "Take"
    # Notes: subsequent paragraphs that aren't attribution or copyright
    attribution_keywords = [
        'Thomas Fuller', 'William Buchan', 'Reverend Twigge', 'Rev. Twigge',
        'Pharmacopeia Extemporanea', 'Domestic Medicine', 'Pharmacopoeia'
    ]
    found_instructions = False
    notes_parts = []

    for p in paragraphs:
        text = p.get_text(strip=True)
        if not text or text.startswith('©'):
            continue
        # Skip attribution
        if any(kw in text for kw in attribution_keywords):
            continue
        # First "Take..." is the recipe
        if text.startswith('Take') and not found_instructions:
            data['instructions'] = text
            found_instructions = True
        elif found_instructions:
            notes_parts.append(text)

    data['notes'] = ' '.join(notes_parts)

    # Related links (other recipe links within the page)
    for link in content.find_all('a'):
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        if href and link_text and 'recipes/' in href:
            data['related_links'].append({'text': link_text, 'href': href})

    return data


def parse_ingredients_from_text(text):
    """Best-effort parse of 18th century recipe text into ingredients."""
    ingredients = []
    if not text:
        return ingredients

    # Split on semicolons
    chunks = re.split(r';', text)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        found_in_chunk = False

        # Pattern: [quantity] [unit] — e.g. "4 ounces", "half a pound"
        for unit in UNITS:
            # Numeric quantity: "4 ounces"
            pattern = rf'(\d+\.?\d*)\s+{unit}\b'
            matches = list(re.finditer(pattern, chunk, re.IGNORECASE))
            for match in matches:
                qty = float(match.group(1))
                before = chunk[:match.start()].strip().rstrip(',').strip()
                before = re.sub(r'^Take\s+', '', before, flags=re.IGNORECASE)
                before = re.sub(r'\s*,?\s*each$', '', before, flags=re.IGNORECASE)
                before = re.sub(r'\s*,?\s*and$', '', before, flags=re.IGNORECASE)
                before = before.strip().rstrip(',').strip()

                if before and len(before) > 1:
                    ingredients.append({
                        'ingredient': before,
                        'quantity_imperial': qty,
                        'unit_imperial': unit,
                    })
                    found_in_chunk = True
                break
            if found_in_chunk:
                break

        # "half a pound", "half an ounce"
        if not found_in_chunk:
            half_pattern = rf'half\s+(?:a\s+|an\s+)?({"|".join(UNITS)})'
            half_match = re.search(half_pattern, chunk, re.IGNORECASE)
            if half_match:
                unit = half_match.group(1)
                before = chunk[:half_match.start()].strip().rstrip(',').strip()
                before = re.sub(r'^Take\s+', '', before, flags=re.IGNORECASE)
                before = before.strip().rstrip(',').strip()
                if before and len(before) > 1:
                    ingredients.append({
                        'ingredient': before,
                        'quantity_imperial': 0.5,
                        'unit_imperial': unit,
                    })

    return ingredients


def convert_to_metric(qty, unit):
    """Convert imperial apothecary measurement to metric."""
    if qty is None or not unit:
        return None, ''
    conv = METRIC_CONVERSIONS.get(unit.lower())
    if not conv:
        return qty, unit
    factor, metric_unit = conv
    return round(qty * factor, 2), metric_unit


def main():
    force = '--force' in sys.argv

    urls_file = DATA_DIR / 'recipe_urls.json'
    if not urls_file.exists():
        print("ERROR: Run scrape_urls.py first to generate recipe_urls.json")
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    with open(urls_file, 'r', encoding='utf-8') as f:
        recipe_urls = json.load(f)

    print(f"Loaded {len(recipe_urls)} recipe URLs")
    if force:
        print("FORCE mode: re-downloading all pages")
    else:
        print("Resume mode: using cached pages where available")
    print(f"Cache dir: {CACHE_DIR}\n")

    recipes_out = []
    ingredients_out = []
    full_backup = []
    recipe_id = 0
    ingredient_id = 0
    cached_count = 0
    fetched_count = 0
    failed_count = 0

    for i, entry in enumerate(recipe_urls):
        url = entry['url']
        name = entry['name']

        print(f"[{i+1}/{len(recipe_urls)}] {name}", end='')

        html, from_cache = fetch_page(url, force=force)

        if html is None:
            print(" - FAILED")
            failed_count += 1
            continue

        if from_cache:
            print(" (cached)")
            cached_count += 1
        else:
            print(" (fetched)")
            fetched_count += 1
            time.sleep(1)  # only delay on actual requests

        # Extract all data
        extracted = extract_all_data(html, url)

        if not extracted['instructions']:
            # Some pages might not have "Take..." — store full_text as instructions
            if extracted['full_text']:
                extracted['instructions'] = extracted['full_text'].split('\n')[0] if extracted['full_text'] else ''

        recipe_id += 1

        recipe_row = {
            'id': recipe_id,
            'name': name,
            'category': entry['category'],
            'ailments': '',
            'instructions': extracted['instructions'],
            'notes': extracted['notes'],
            'source_url': url,
            'source_author': entry['source_author'],
            'source_work': entry['source_work'],
            'source_year': entry['source_year'],
            'digitized_by': 'Stephen Hart (pascalbonenfant.com)',
            'page_title': extracted['page_title'],
            'meta_description': extracted['meta_description'],
            'recipe_number': extracted['recipe_number'],
            'full_text': extracted['full_text'],
        }
        recipes_out.append(recipe_row)

        # Full backup includes everything
        full_backup.append({
            **recipe_row,
            'all_paragraphs': extracted['all_paragraphs'],
            'related_links': extracted['related_links'],
            'cached_file': str(CACHE_DIR / url_to_cache_filename(url)),
        })

        # Parse ingredients
        parsed = parse_ingredients_from_text(extracted['instructions'])
        for ing in parsed:
            ingredient_id += 1
            m_qty, m_unit = convert_to_metric(ing['quantity_imperial'], ing['unit_imperial'])
            ingredients_out.append({
                'id': ingredient_id,
                'recipe_id': recipe_id,
                'ingredient': ing['ingredient'],
                'quantity_imperial': ing['quantity_imperial'],
                'unit_imperial': ing['unit_imperial'],
                'quantity_metric': m_qty,
                'unit_metric': m_unit,
                'notes': '',
            })

    # Write recipes CSV
    recipes_csv = DATA_DIR / 'recipes.csv'
    with open(recipes_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'name', 'category', 'ailments', 'instructions', 'notes',
            'source_url', 'source_author', 'source_work', 'source_year',
            'digitized_by', 'page_title', 'meta_description', 'recipe_number', 'full_text'
        ])
        writer.writeheader()
        writer.writerows(recipes_out)

    # Write ingredients CSV
    ingredients_csv = DATA_DIR / 'ingredients.csv'
    with open(ingredients_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'recipe_id', 'ingredient', 'quantity_imperial', 'unit_imperial',
            'quantity_metric', 'unit_metric', 'notes'
        ])
        writer.writeheader()
        writer.writerows(ingredients_out)

    # Write full backup JSON (everything, including paragraphs and links)
    full_json = DATA_DIR / 'recipes_full.json'
    with open(full_json, 'w', encoding='utf-8') as f:
        json.dump(full_backup, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"{'='*60}")
    print(f"  Recipes scraped:    {len(recipes_out)}")
    print(f"  Ingredients parsed: {len(ingredients_out)}")
    print(f"  Pages from cache:   {cached_count}")
    print(f"  Pages fetched:      {fetched_count}")
    print(f"  Pages failed:       {failed_count}")
    print(f"{'='*60}")
    print(f"  {recipes_csv}")
    print(f"  {ingredients_csv}")
    print(f"  {full_json}")
    print(f"  {CACHE_DIR}/ ({cached_count + fetched_count} HTML files)")
    print(f"\nNext: run 'python convert.py' to generate JSON for the website")


if __name__ == '__main__':
    main()
