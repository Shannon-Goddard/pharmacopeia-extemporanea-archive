"""
Auto-tag ailments based on recipe names, instructions, and notes.
Reads: data/recipes.csv
Outputs: data/recipes.csv (updated with ailments column filled)

Run: python tag_ailments.py
"""
import csv
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

# Keyword -> ailment tag mapping
# Order matters: more specific matches first
AILMENT_MAP = {
    # Specific conditions
    'cancer': 'cancer',
    'scrophul': 'scrofula',
    'strumae': 'scrofula',
    'scorbutic': 'scurvy',
    'scorbutick': 'scurvy',
    'scurvy': 'scurvy',
    'arthritic': 'arthritis',
    'podagric': 'gout',
    'gout': 'gout',
    'epileptic': 'epilepsy',
    'epilepsy': 'epilepsy',
    'hysteric': 'hysteria|nervous',
    'hydropic': 'dropsy|edema',
    'dropsie': 'dropsy|edema',
    'dropsy': 'dropsy|edema',
    'icteric': 'jaundice|liver',
    'jaundice': 'jaundice|liver',
    'pleuritic': 'pleurisy|respiratory',
    'pleuritick': 'pleurisy|respiratory',
    'pleurisy': 'pleurisy|respiratory',
    'pectoral': 'respiratory|cough',
    'bechic': 'cough|respiratory',
    'cough': 'cough|respiratory',
    'consumption': 'consumption|tuberculosis',
    'consumptive': 'consumption|tuberculosis',
    'phthisic': 'consumption|tuberculosis',
    'antiphthisic': 'consumption|tuberculosis',
    'asthmatic': 'asthma|respiratory',
    'asthma': 'asthma|respiratory',
    'catarrh': 'catarrh|respiratory',
    'quinsy': 'quinsy|throat',
    'cephalic': 'headache|neurological',
    'apoplectic': 'apoplexy|stroke',
    'apoplexy': 'apoplexy|stroke',
    'paralytic': 'palsy|paralysis',
    'palsy': 'palsy|paralysis',
    'nephritic': 'kidney|urinary',
    'gravel': 'kidney stones|urinary',
    'diuretic': 'urinary',
    'emmenagogue': 'menstrual',
    'chlorotic': 'anemia|menstrual',
    'chalybeate': 'anemia|iron',
    'ricket': 'rickets',
    'spleen': 'spleen',
    'splenic': 'spleen',
    'splenetic': 'spleen',
    'splanchnic': 'visceral|digestive',
    'stomachic': 'digestive|stomach',
    'stomach': 'digestive|stomach',
    'carminative': 'digestive|flatulence',
    'colic': 'colic|digestive',
    'dysenteric': 'dysentery',
    'dysentery': 'dysentery',
    'flux': 'dysentery|diarrhea',
    'diarrhea': 'diarrhea',
    'purging': 'purgative|digestive',
    'laxative': 'purgative|digestive',
    'cathartic': 'purgative',
    'emetic': 'emetic|vomiting',
    'vomit': 'emetic|vomiting',
    'antemetic': 'anti-emetic',
    'anthelminthic': 'worms|parasites',
    'worm': 'worms|parasites',
    'febrifuge': 'fever',
    'febrisic': 'fever',
    'fever': 'fever',
    'sudorific': 'fever|sweating',
    'diaphoretic': 'fever|sweating',
    'alexipharmac': 'poison|antidote',
    'alexiterial': 'poison|antidote',
    'antidote': 'poison|antidote',
    'bite': 'bites|poison',
    'styptic': 'bleeding|wounds',
    'astringent': 'bleeding|wounds',
    'haemorrhag': 'bleeding',
    'haemorrhoid': 'hemorrhoids',
    'hemorrhoid': 'hemorrhoids',
    'vulnerary': 'wounds',
    'bruise': 'bruises|wounds',
    'burn': 'burns',
    'ulcer': 'ulcers|wounds',
    'psoric': 'skin|itch',
    'erysipelas': 'erysipelas|skin',
    'small pox': 'smallpox',
    'variolose': 'smallpox',
    'cardiac': 'heart|tonic',
    'cordial': 'heart|tonic',
    'anodyne': 'pain|sedative',
    'pacific': 'pain|sedative',
    'somniferous': 'sleep|sedative',
    'opium': 'pain|sedative',
    'laudanum': 'pain|sedative',
    'paregoric': 'pain|sedative',
    'expectorating': 'expectorant|respiratory',
    'incrassating': 'expectorant|respiratory',
    'balsamic': 'wounds|respiratory',
    'detergent': 'cleansing',
    'mercurial': 'syphilis|purgative',
    'mercury': 'syphilis|purgative',
    'gonorrhoea': 'gonorrhea|venereal',
    'tooth': 'dental',
    'teeth': 'dental',
    'dentalgic': 'dental|pain',
    'eye': 'eye',
    'collyri': 'eye',
    'for the ear': 'ear',
    'acovistic': 'ear|deafness',
    'gargle': 'throat',
    'uvula': 'throat',
    'lotion': 'skin|external',
    'face': 'skin|cosmetic',
    'liniment': 'external|pain',
    'unguent': 'external|skin',
    'ointment': 'external|skin',
    'plaister': 'external|pain',
    'plaster': 'external|pain',
    'foment': 'external|pain',
    'cataplasm': 'external|poultice',
    'glyster': 'enema',
    'clyster': 'enema',
    'suppositories': 'rectal',
    'children': 'pediatric',
    'infant': 'pediatric',
    'child-bed': 'postpartum',
    'abortion': 'pregnancy',
    'stitch': 'pain|side',
    'hernia': 'hernia',
    'rheumatism': 'rheumatism',
    'tonic': 'general tonic',
}


def tag_recipe(name, instructions, notes):
    """Match ailments from recipe name, instructions, and notes."""
    # Prioritize name for matching
    text_to_search = f"{name} {name} {instructions[:200]} {notes[:200]}".lower()

    matched = set()
    for keyword, ailments in AILMENT_MAP.items():
        if keyword in text_to_search:
            for a in ailments.split('|'):
                matched.add(a.strip())

    # If nothing matched, tag as "general tonic"
    if not matched:
        matched.add('general tonic')

    return '|'.join(sorted(matched))


def main():
    recipes_csv = DATA_DIR / 'recipes.csv'

    # Read
    with open(recipes_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Tag
    tagged = 0
    for row in rows:
        ailments = tag_recipe(
            row.get('name', ''),
            row.get('instructions', ''),
            row.get('notes', '')
        )
        row['ailments'] = ailments
        tagged += 1

    # Write back
    with open(recipes_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    all_ailments = set()
    for row in rows:
        for a in row['ailments'].split('|'):
            if a.strip():
                all_ailments.add(a.strip())

    print(f"Tagged {tagged} recipes with ailments")
    print(f"Unique ailment tags: {len(all_ailments)}")
    print(f"\nAll tags:")
    for a in sorted(all_ailments):
        count = sum(1 for r in rows if a in r['ailments'].split('|'))
        print(f"  {a}: {count}")

    print(f"\nNext: run 'python convert.py' to update the website JSON")


if __name__ == '__main__':
    main()
