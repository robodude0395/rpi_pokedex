"""
Extract module for Pokemon ETL pipeline.
Reads JSON files from raw_pokemon folder and extracts Pokemon data.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any


def find_pokemon_json_files(input_dir: str) -> List[Path]:
    """Recursively find all details.json files in the input directory."""
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    json_files = list(input_path.rglob("details.json"))

    if not json_files:
        raise ValueError(f"No details.json files found in {input_dir}")

    return json_files


def read_pokemon_json(json_path: Path) -> Dict[str, Any]:
    """Read and parse a single Pokemon JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {json_path}: {e}")
    except Exception as e:
        raise IOError(f"Error reading {json_path}: {e}")


def extract_pokemon_basic_info(pokemon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic Pokemon information for the pokemon table."""
    base_stats = pokemon_data.get("base_stats", {})

    # Join biology paragraphs into a single description
    biology = pokemon_data.get("biology", [])
    description = " ".join(biology) if isinstance(biology, list) else str(biology)

    # Get evolution info
    evolution = pokemon_data.get("evolution", "")

    return {
        "pokemon_id": pokemon_data.get("pokedex_number"),
        "pokemon_name": pokemon_data.get("name"),
        "gen_number": extract_generation_number(pokemon_data),
        "base_hp": base_stats.get("HP", -1),
        "base_attack": base_stats.get("Attack", -1),
        "base_defense": base_stats.get("Defense", -1),
        "base_sp_attack": base_stats.get("Sp. Atk", -1),
        "base_sp_def": base_stats.get("Sp. Def", -1),
        "base_speed": base_stats.get("Speed", -1),
        "description": description,
        "evolution": evolution
    }


def extract_generation_number(pokemon_data: Dict[str, Any]) -> int:
    """
    Extract generation number from Pokemon data.
    Determines generation based on pokedex number.
    """
    dex_num = pokemon_data.get("pokedex_number", 0)

    # Generation ranges based on National Pokedex numbers
    if 1 <= dex_num <= 151:
        return 1
    elif 152 <= dex_num <= 251:
        return 2
    elif 252 <= dex_num <= 386:
        return 3
    elif 387 <= dex_num <= 493:
        return 4
    elif 494 <= dex_num <= 649:
        return 5
    elif 650 <= dex_num <= 721:
        return 6
    elif 722 <= dex_num <= 809:
        return 7
    elif 810 <= dex_num <= 905:
        return 8
    elif 906 <= dex_num <= 1025:
        return 9
    else:
        return -1  # Default to Gen -1


def extract_types(pokemon_data: Dict[str, Any]) -> List[str]:
    """Extract Pokemon types, filtering out 'Unknown' types."""
    types = pokemon_data.get("types", [])
    # Filter out 'Unknown' types
    valid_types = [t for t in types if t and t != "Unknown"]
    return valid_types


def extract_abilities(pokemon_data: Dict[str, Any]) -> List[str]:
    """Extract Pokemon abilities (both regular and hidden)."""
    abilities = pokemon_data.get("abilities", [])
    ability_names = []

    for ability in abilities:
        if isinstance(ability, dict):
            name = ability.get("name")
            if name:
                ability_names.append(name)
        elif isinstance(ability, str):
            ability_names.append(ability)

    return ability_names


def extract_moves(pokemon_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract Pokemon moves with TM/HM information."""
    learnset = pokemon_data.get("learnset", [])
    moves = []

    for move in learnset:
        if isinstance(move, dict):
            move_name = move.get("name")
            is_tm = move.get("tm", False)

            if move_name:
                moves.append({
                    "move_name": move_name,
                    "is_tm": 1 if is_tm else 0  # SQLite boolean
                })

    return moves


def extract_all_pokemon_data(input_dir: str) -> List[Dict[str, Any]]:
    """Extract data from all Pokemon JSON files in the input directory."""
    json_files = find_pokemon_json_files(input_dir)
    all_pokemon = []

    for json_path in json_files:
        try:
            pokemon_data = read_pokemon_json(json_path)

            # Extract all components
            extracted = {
                "basic_info": extract_pokemon_basic_info(pokemon_data),
                "types": extract_types(pokemon_data),
                "abilities": extract_abilities(pokemon_data),
                "moves": extract_moves(pokemon_data),
                "raw_data": pokemon_data  # Keep for reference if needed
            }

            all_pokemon.append(extracted)

        except Exception as e:
            print(f"Warning: Failed to extract {json_path}: {e}")
            continue

    return all_pokemon
