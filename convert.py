"""
Convert CSV files to JSON for the Pharmacopeia site.
Run this after scraping or manually updating the CSV files:
    python convert.py

Generates:
    data/recipes.json      (for the website - excludes full_text to keep it light)
    data/ingredients.json  (for the website)
"""
import csv
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

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


def convert_to_metric(quantity, unit):
    if not quantity or not unit:
        return None, ''
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        return None, ''
    conversion = METRIC_CONVERSIONS.get(unit.lower().strip())
    if not conversion:
        return qty, unit
    factor, metric_unit = conversion
    return round(qty * factor, 2), metric_unit


def csv_to_json(csv_file, json_file, numeric_fields=None, auto_metric=False, exclude_fields=None):
    numeric_fields = numeric_fields or []
    exclude_fields = exclude_fields or []
    rows = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in numeric_fields:
                val = row.get(field, '').strip()
                if val:
                    try:
                        row[field] = float(val) if '.' in val else int(val)
                    except ValueError:
                        pass
                else:
                    row[field] = None

            if auto_metric and not row.get('quantity_metric'):
                m_qty, m_unit = convert_to_metric(
                    row.get('quantity_imperial'),
                    row.get('unit_imperial')
                )
                row['quantity_metric'] = m_qty
                row['unit_metric'] = m_unit

            # Remove bulky fields not needed for frontend
            for field in exclude_fields:
                row.pop(field, None)

            rows.append(row)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"  {csv_file.name} -> {json_file.name} ({len(rows)} records)")


def main():
    print("Converting CSVs to JSON for website...\n")

    csv_to_json(
        DATA_DIR / 'recipes.csv',
        DATA_DIR / 'recipes.json',
        numeric_fields=['id', 'source_year', 'recipe_number'],
        exclude_fields=['full_text', 'meta_description', 'page_title']
    )

    csv_to_json(
        DATA_DIR / 'ingredients.csv',
        DATA_DIR / 'ingredients.json',
        numeric_fields=['id', 'recipe_id', 'quantity_imperial', 'quantity_metric'],
        auto_metric=True
    )

    print("\nDone! Website JSON files are ready.")
    print("Serve index.html or push to GitHub Pages.")


if __name__ == '__main__':
    main()
