# 🧪 The Pharmacopeia Extemporanea — Digital Archive

**The world's most comprehensive structured dataset of 18th-century medicinal recipes.**

977 recipes. 3,022 ingredients. Three original sources spanning 1710–1785. Every measurement converted to metric. Fully searchable. Open data.

---

## What Is This?

This is a complete digitization and structured database of three historically significant pharmacopeias from the 18th century:

| Source | Author | Year | Recipes |
|--------|--------|------|---------|
| *Pharmacopeia Extemporanea* | Thomas Fuller | 1710 | ~800 |
| *Domestic Medicine* | William Buchan | 1785 (2nd ed.) | ~166 |
| *Notebook* | Rev. William Twigge | c.1715 | 11 |

These texts represent the medical knowledge of an era — from Cancer Ales brewed with millipedes to Pleuritic Plaisters applied with frankincense. Every recipe has been extracted, parsed into individual ingredients, tagged with ailment categories, and converted from the apothecary measurement system into metric units.

The original texts were painstakingly digitized by **Stephen Hart** at [pascalbonenfant.com](https://www.pascalbonenfant.com/18c/medicine/pharmacopeia.html). This project structures that work into machine-readable, searchable, and citable data.

---

## Live Site

👉 **[View the searchable database](#)** *(GitHub Pages link here)*

Filter by ailment, ingredient, category, or source author. Checkbox multi-select with instant results.

---

## The Data

### `data/recipes.csv`

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `name` | Recipe name (e.g. "Epileptic Ale") |
| `category` | Preparation type (Ales, Decoctions, Pills, Powders, etc.) |
| `ailments` | Pipe-separated ailment tags (e.g. "epilepsy\|seizures") |
| `instructions` | Full recipe text as written in the original |
| `notes` | Author commentary or usage notes |
| `source_url` | Link to the digitized page |
| `source_author` | Original author |
| `source_work` | Publication title |
| `source_year` | Year of publication |
| `digitized_by` | Credit for digitization |
| `page_title` | HTML page title from source |
| `meta_description` | HTML meta description |
| `recipe_number` | Original numbering within the text |
| `full_text` | Complete page content (for re-parsing) |

### `data/ingredients.csv`

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `recipe_id` | Foreign key to recipes |
| `ingredient` | Ingredient name |
| `quantity_imperial` | Original quantity |
| `unit_imperial` | Original unit (ounces, drams, scruples, etc.) |
| `quantity_metric` | Converted metric quantity |
| `unit_metric` | Metric unit (g, ml) |
| `notes` | Additional notes |

### `data/recipes_full.json`

The nuclear backup — everything above plus `all_paragraphs` as arrays, `related_links`, and local cache file paths. If you need to re-parse anything, start here.

### `data/cache/`

Raw HTML of all 977 recipe pages. Preserved for reproducibility and future re-processing without hitting the original server.

---

## Measurement Conversions

All conversions use the **apothecary system** as documented in the original text:

| Imperial | Metric | Notes |
|----------|--------|-------|
| 1 pound | 373 g | Troy/apothecary pound (12 oz) |
| 1 ounce | 31.1 g | Apothecary ounce |
| 1 dram (drachm) | 3.89 g | |
| 1 scruple | 1.296 g | |
| 1 grain | 64.8 mg | |
| 1 pint | 473 ml | |
| 1 quart | 946 ml | |
| 1 gallon | 3,785 ml | |
| 1 minim | 0.062 ml | |
| 1 handful | — | No standard conversion; preserved as-is |

These are **not** modern avoirdupois measurements. The apothecary pound is 373g, not 453.6g.

---

## Ailment Taxonomy

Recipes are auto-tagged with 89 ailment categories derived from recipe names and content. Tags include:

`anemia` · `apoplexy` · `arthritis` · `asthma` · `bleeding` · `burns` · `cancer` · `catarrh` · `colic` · `consumption` · `cough` · `dental` · `diarrhea` · `digestive` · `dropsy` · `dysentery` · `ear` · `edema` · `emetic` · `epilepsy` · `erysipelas` · `external` · `eye` · `fever` · `gout` · `headache` · `heart` · `hemorrhoids` · `hysteria` · `jaundice` · `kidney` · `liver` · `menstrual` · `pain` · `palsy` · `parasites` · `pediatric` · `pleurisy` · `poison` · `purgative` · `respiratory` · `rheumatism` · `rickets` · `scrofula` · `scurvy` · `sedative` · `skin` · `smallpox` · `spleen` · `stomach` · `syphilis` · `throat` · `tuberculosis` · `ulcers` · `urinary` · `vomiting` · `worms` · `wounds` · and more.

---

## Setup & Usage

### View the site locally

Just open `index.html` in a browser. It's static HTML/CSS/JS — no server required.

### Rebuild from source

```bash
# Install dependencies
pip install -r requirements.txt

# Step 1: Collect all recipe URLs from index pages
python scrape_urls.py

# Step 2: Fetch each recipe page (cached — resume-safe)
python scrape_recipes.py

# Step 3: Auto-tag ailments from recipe names/content
python tag_ailments.py

# Step 4: Generate website JSON from CSVs
python convert.py
```

The scraper is **resume-safe** — pages are cached locally in `data/cache/`. If interrupted, just re-run. Use `--force` to re-download everything.

### Re-process without scraping

All 977 HTML pages are preserved in `data/cache/`. To re-parse with improved logic:

```bash
python scrape_recipes.py  # reads from cache, no network requests
python tag_ailments.py
python convert.py
```

---

## Project Structure

```
├── index.html              # Searchable web interface
├── css/style.css           # Styles
├── js/app.js               # Filter logic + rendering
├── data/
│   ├── cache/              # 977 raw HTML files (gitignored for size)
│   ├── recipe_urls.json    # All URLs + metadata
│   ├── recipes.csv         # Full recipe dataset
│   ├── ingredients.csv     # Parsed ingredients with metric
│   ├── recipes_full.json   # Complete backup (everything)
│   ├── recipes.json        # Website-optimized (excludes full_text)
│   └── ingredients.json    # Website-optimized
├── scrape_urls.py          # Step 1: collect URLs
├── scrape_recipes.py       # Step 2: fetch + parse + cache
├── tag_ailments.py         # Step 3: auto-tag ailments
├── convert.py              # Step 4: CSV → JSON
├── requirements.txt        # Python dependencies
├── LICENSE.md              # CC BY-NC-SA 4.0
└── README.md               # You are here
```

---

## For Researchers

This dataset is suitable for:

- **History of medicine** — study the pharmacological knowledge and practices of the early modern period
- **Ethnobotany** — catalog and cross-reference plant-based ingredients across 977 preparations
- **Historical linguistics** — analyze the technical vocabulary of 18th-century English medical texts
- **Data science** — network analysis of ingredient co-occurrence, NLP on historical text
- **Digital humanities** — structured data from previously unstructured historical sources

### Citing this dataset

If you use this data in academic work, please cite:

```
The Pharmacopeia Extemporanea Digital Archive (2026).
Original texts digitized by Stephen Hart (pascalbonenfant.com).
Structured dataset and tooling by Amazon Q & Shannon Goddard | Loyal9 LLC
Available at: [repository URL]
```

If a DOI is assigned, use that instead.

### Known limitations

- **Ingredient parsing is best-effort.** 18th-century recipe syntax is inconsistent. The parser captures ~80% of ingredients cleanly; some complex multi-ingredient clauses (e.g. "each 2 ounces" referring to several preceding items) may need manual review.
- **Ailment tagging is keyword-based.** Tags are derived from recipe names and first 200 characters. Some recipes may be mis-tagged or under-tagged.
- **"Handful" has no metric equivalent.** These are preserved as-is.
- **These are historical documents, not medical advice.** Many recipes contain toxic substances (mercury, antimony, arsenic, lead). Do not prepare or consume any of these recipes.

---

## Credits

| Contribution | Credit |
|---|---|
| Original texts | Thomas Fuller (1710), William Buchan (1785), Rev. William Twigge (c.1715) |
| Digitization of source material | **Stephen Hart** — [pascalbonenfant.com](https://www.pascalbonenfant.com) |
| Dataset structuring, scraping tools, metric conversion, web interface, ailment taxonomy | **Amazon Q** (AI assistant) |
| Project direction, curation, and data stewardship | **Shannon Goddard** — [Loyal9 LLC](https://loyal9.com) |

---

## ⚠️ Disclaimer

**These are historical documents preserved for scholarly purposes.**

These recipes frequently call for substances that are toxic, carcinogenic, or otherwise dangerous including (but not limited to): crude antimony, mercury, lead, arsenic, and opium. Many preparations involve unpasteurized animal products, raw minerals, and unidentified plant matter.

**Do not prepare, consume, or administer any recipe from this database.**

This project exists solely for historical research, education, and the preservation of cultural heritage.

---

## License

This project is licensed under [CC BY-NC-SA 4.0](LICENSE.md) — Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.

You are free to share and adapt this work for non-commercial purposes, with attribution, under the same license.

---

*"I have a thousand times observed that mild alteratives are used to much more advantage just before, after, or at meals, than at any other times."*
— Thomas Fuller, *Pharmacopeia Extemporanea*, 1710
