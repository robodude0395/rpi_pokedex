"""
Transform module for Pokemon ETL pipeline.
Normalizes extracted Pokemon data into relational database format.
"""

import csv
from pathlib import Path
from typing import Dict, List, Any, Tuple


class DataTransformer:
    """
    Transforms raw Pokemon data into normalized database tables.
    Handles deduplication and relationship mapping.
    """

    def __init__(self):
        """Initialize the transformer with empty data structures."""
        self.pokemon_records = []

        # Lookup tables for deduplication
        self.types = {}  # type_name -> type_id
        self.abilities = {}  # ability_name -> ability_id
        self.moves = {}  # move_name -> move_id

        # Junction table records
        self.pokemon_types = []
        self.pokemon_abilities = []
        self.pokemon_moves = []

        # ID counters
        self.next_type_id = 1
        self.next_ability_id = 1
        self.next_move_id = 1
        self.next_pokemon_type_id = 1
        self.next_pokemon_ability_id = 1
        self.next_pokemon_move_id = 1

    def get_or_create_type(self, type_name: str) -> int:
        """Get existing type ID or create new type entry."""
        if type_name in self.types:
            return self.types[type_name]["type_id"]

        type_id = self.next_type_id
        self.types[type_name] = {
            "type_id": type_id,
            "type_name": type_name,
            "colour": get_type_color(type_name)
        }
        self.next_type_id += 1

        return type_id

    def get_or_create_ability(self, ability_name: str) -> int:
        """Get existing ability ID or create new ability entry."""
        if ability_name in self.abilities:
            return self.abilities[ability_name]["ability_id"]

        ability_id = self.next_ability_id
        self.abilities[ability_name] = {
            "ability_id": ability_id,
            "ability_name": ability_name
        }
        self.next_ability_id += 1

        return ability_id

    def get_or_create_move(self, move_name: str, is_tm: int) -> int:
        """Get existing move ID or create new move entry."""
        if move_name in self.moves:
            # Update is_tm if this occurrence is a TM
            if is_tm == 1:
                self.moves[move_name]["is_tm"] = 1
            return self.moves[move_name]["move_id"]

        move_id = self.next_move_id
        self.moves[move_name] = {
            "move_id": move_id,
            "move_name": move_name,
            "is_tm": is_tm
        }
        self.next_move_id += 1

        return move_id

    def transform_pokemon(self, extracted_data: Dict[str, Any]) -> None:
        """Transform a single Pokemon's data and add to normalized tables."""

        basic_info = extracted_data["basic_info"]
        pokemon_id = basic_info["pokemon_id"]

        # Add to pokemon table
        self.pokemon_records.append(basic_info)

        # Process types
        for type_name in extracted_data["types"]:
            type_id = self.get_or_create_type(type_name)
            self.pokemon_types.append({
                "pokemon_type_id": self.next_pokemon_type_id,
                "pokemon_id": pokemon_id,
                "type_id": type_id
            })
            self.next_pokemon_type_id += 1

        # Process abilities
        for ability_name in extracted_data["abilities"]:
            ability_id = self.get_or_create_ability(ability_name)
            self.pokemon_abilities.append({
                "pokemon_ability_id": self.next_pokemon_ability_id,
                "pokemon_id": pokemon_id,
                "ability_id": ability_id
            })
            self.next_pokemon_ability_id += 1

        # Process moves
        for move in extracted_data["moves"]:
            move_id = self.get_or_create_move(
                move["move_name"],
                move["is_tm"]
            )
            self.pokemon_moves.append({
                "pokemon_move_id": self.next_pokemon_move_id,
                "pokemon_id": pokemon_id,
                "move_id": move_id
            })
            self.next_pokemon_move_id += 1

    def get_normalized_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all normalized table data."""
        return {
            "pokemon": self.pokemon_records,
            "type": list(self.types.values()),
            "pokemon_type": self.pokemon_types,
            "ability": list(self.abilities.values()),
            "pokemon_ability": self.pokemon_abilities,
            "move": list(self.moves.values()),
            "pokemon_move": self.pokemon_moves
        }


def get_type_color(type_name: str) -> str:
    """Get the color associated with a Pokemon type."""
    type_colors = {
        "Normal": "#A8A878",
        "Fire": "#F08030",
        "Water": "#6890F0",
        "Electric": "#F8D030",
        "Grass": "#78C850",
        "Ice": "#98D8D8",
        "Fighting": "#C03028",
        "Poison": "#A040A0",
        "Ground": "#E0C068",
        "Flying": "#A890F0",
        "Psychic": "#F85888",
        "Bug": "#A8B820",
        "Rock": "#B8A038",
        "Ghost": "#705898",
        "Dragon": "#7038F8",
        "Dark": "#705848",
        "Steel": "#B8B8D0",
        "Fairy": "#EE99AC"
    }

    return type_colors.get(type_name, "#777777")


def transform_all_pokemon(extracted_pokemon: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Transform all extracted Pokemon data into normalized tables."""
    transformer = DataTransformer()

    for pokemon_data in extracted_pokemon:
        transformer.transform_pokemon(pokemon_data)

    return transformer.get_normalized_tables()


def save_tables_to_csv(tables: Dict[str, List[Dict[str, Any]]], output_dir: str) -> Dict[str, Path]:
    """Save normalized tables to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_paths = {}

    for table_name, records in tables.items():
        if not records:
            print(f"Warning: No records for table {table_name}")
            continue

        csv_file = output_path / f"{table_name}.csv"

        # Get field names from first record
        fieldnames = list(records[0].keys())

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        csv_paths[table_name] = csv_file
        print(f"Saved {len(records)} records to {csv_file}")

    return csv_paths
