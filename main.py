#!/usr/bin/env python3
"""Pokemon Pokedex Application"""

import sqlite3
import sys
from pathlib import Path
from glob import glob

from GUI.menu_app import Menu, MenuApp, PokemonDescriptionPage

DB = "schema/pokedex.db"
RAW_POKEMON = "web_scraping/raw_pokemon"

def parse_color(color_str):
    """Parse hex color '#RRGGBB' to RGB tuple, default to grey."""
    try:
        hex_str = color_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, TypeError, AttributeError):
        return (128, 128, 128)

def query(sql, params=()):
    """Execute query and return results."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    results = conn.execute(sql, params).fetchall()
    conn.close()
    return results

def find_image(name, gen):
    """Find pokemon image in raw_pokemon directory."""
    pattern = f"{RAW_POKEMON}/Gen_{gen}/{name}/image.png"
    images = glob(pattern)
    return images[0] if images else ""

def build_root_menu():
    """Build menu from database."""
    # Get all generations
    gens = query("SELECT DISTINCT gen_number FROM pokemon ORDER BY gen_number")
    gen_items = []

    for gen in gens:
        gen_num = gen['gen_number']

        # Get all pokemon in this generation
        pokemon = query(
            "SELECT pokemon_id, pokemon_name FROM pokemon WHERE gen_number = ? ORDER BY pokemon_id",
            (gen_num,)
        )

        pokemon_items = []
        for p in pokemon:
            pid = p['pokemon_id']
            pname = p['pokemon_name']

            # Create pokemon page
            details = query(
                "SELECT * FROM pokemon WHERE pokemon_id = ?",
                (pid,)
            )[0]

            types = query(
                "SELECT type_name, colour FROM type JOIN pokemon_type ON type.type_id = pokemon_type.type_id WHERE pokemon_id = ?",
                (pid,)
            )
            type_list = [(t['type_name'], parse_color(t['colour'])) for t in types]

            image = find_image(pname, gen_num)

            page = PokemonDescriptionPage(
                name=pname,
                dex_number=pid,
                types=type_list,
                height=f"{details['base_hp']}",
                weight=f"{details['base_attack']}",
                description=details['description'],
                image_path=image,
            )
            pokemon_items.append((pname, page))

        gen_menu = Menu(pokemon_items, title=f"Generation {gen_num}")
        gen_items.append((f"Generation {gen_num}", gen_menu))

    return Menu(gen_items, title="Pokedex")

if __name__ == "__main__":
    if not Path(DB).exists():
        print(f"Error: Database not found at {DB}")
        print("Run 'bash main.sh' first to generate it")
        sys.exit(1)

    print("Loading Pokedex...")
    root_menu = build_root_menu()
    app = MenuApp(root_menu)

    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
