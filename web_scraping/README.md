# To run:

    python -m venv .venv
    pip install -r requirements.txt
    python scrape_pokemon.py

This will scrape only one pokemon from Gen 1. To scrape all the pokemons set debug mode to 'False' in 'scrape_pokemon' line 663. To scrape pokemon from other generations set it to whichever gen number you prefer (Gen 5 is my favourite!).

scraper = BulbapediaScraper(generation=1, debug_mode=True)