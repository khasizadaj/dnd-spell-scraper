# DnD Spell Scraper

A simple tool to load and process Dungeons & Dragons spell lists from a JSON file.

> Disclaimer: Spells are scraped from dnd5e.wikidot.com. Spell names are preserved in the exact format they appear on the source site.

## Usage

The script expects a single JSON file path as argument.

```bash
python main.py [path_to_spells]
```

## JSON Format

Example structure of the input file:

```json
{
  "artificer": ["faerie-fire", "sanctuary", "vortex-warp"],
  "druid": ["resistance", "thunderclap", "mending"]
}
```

Each class is a key, and its value is a list of spell names.

## Error Handling

If you run the script incorrectly, you’ll see:

```
Usage: python dnd_spell_scraper.py [path_to_spells.json]
```

---

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```
