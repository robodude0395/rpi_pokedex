"""
Unit tests for extract.py module.
Tests Pokemon data extraction from JSON files.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from extract import (
    find_pokemon_json_files,
    read_pokemon_json,
    extract_pokemon_basic_info,
    extract_generation_number,
    extract_types,
    extract_abilities,
    extract_moves,
    extract_all_pokemon_data
)


@pytest.fixture
def sample_pokemon_data():
    """Fixture providing sample Pokemon data."""
    return {
        "name": "Bulbasaur",
        "pokedex_number": 1,
        "types": ["Grass", "Poison"],
        "height": "0.7 m",
        "weight": "6.9 kg",
        "abilities": [
            {"name": "Overgrow", "hidden": False},
            {"name": "Chlorophyll", "hidden": True}
        ],
        "base_stats": {
            "HP": 45,
            "Attack": 49,
            "Defense": 49,
            "Sp. Atk": 65,
            "Sp. Def": 65,
            "Speed": 45
        },
        "biology": [
            "Bulbasaur is a small, quadrupedal amphibian Pokémon.",
            "It has been raised by humans from birth."
        ],
        "evolution": "Bulbasaur evolves into Ivysaur, which evolves into Venusaur.",
        "learnset": [
            {"name": "Tackle", "tm": False},
            {"name": "Vine Whip", "tm": False},
            {"name": "Solar Beam", "tm": True}
        ]
    }


@pytest.fixture
def temp_pokemon_dir(sample_pokemon_data):
    """Fixture providing a temporary directory with Pokemon JSON files."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create Gen_1/Bulbasaur/details.json
        bulbasaur_dir = tmppath / "Gen_1" / "Bulbasaur"
        bulbasaur_dir.mkdir(parents=True)

        with open(bulbasaur_dir / "details.json", 'w') as f:
            json.dump(sample_pokemon_data, f)

        # Create another Pokemon
        pikachu_data = sample_pokemon_data.copy()
        pikachu_data["name"] = "Pikachu"
        pikachu_data["pokedex_number"] = 25
        pikachu_data["types"] = ["Electric"]

        pikachu_dir = tmppath / "Gen_1" / "Pikachu"
        pikachu_dir.mkdir(parents=True)

        with open(pikachu_dir / "details.json", 'w') as f:
            json.dump(pikachu_data, f)

        yield tmppath


class TestFindPokemonJsonFiles:
    """Tests for find_pokemon_json_files function."""

    def test_find_json_files(self, temp_pokemon_dir):
        """Test finding JSON files in directory."""
        json_files = find_pokemon_json_files(str(temp_pokemon_dir))

        assert len(json_files) == 2
        assert all(f.name == "details.json" for f in json_files)

    def test_nonexistent_directory(self):
        """Test error when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            find_pokemon_json_files("/nonexistent/directory")

    def test_empty_directory(self):
        """Test error when no JSON files found."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="No details.json files found"):
                find_pokemon_json_files(tmpdir)


class TestReadPokemonJson:
    """Tests for read_pokemon_json function."""

    def test_read_valid_json(self, temp_pokemon_dir):
        """Test reading a valid JSON file."""
        json_path = list(temp_pokemon_dir.rglob("details.json"))[0]
        data = read_pokemon_json(json_path)

        assert isinstance(data, dict)
        assert "name" in data
        assert "pokedex_number" in data

    def test_read_invalid_json(self):
        """Test error when reading invalid JSON."""
        with TemporaryDirectory() as tmpdir:
            invalid_json = Path(tmpdir) / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(ValueError, match="Invalid JSON"):
                read_pokemon_json(invalid_json)


class TestExtractPokemonBasicInfo:
    """Tests for extract_pokemon_basic_info function."""

    def test_extract_basic_info(self, sample_pokemon_data):
        """Test extracting basic Pokemon information."""
        info = extract_pokemon_basic_info(sample_pokemon_data)

        assert info["pokemon_id"] == 1
        assert info["pokemon_name"] == "Bulbasaur"
        assert info["gen_number"] == 1
        assert info["base_hp"] == 45
        assert info["base_attack"] == 49
        assert info["base_defense"] == 49
        assert info["base_sp_attack"] == 65
        assert info["base_sp_def"] == 65
        assert info["base_speed"] == 45
        assert "Bulbasaur is a small" in info["description"]
        assert "Ivysaur" in info["evolution"]

    def test_extract_with_missing_stats(self):
        """Test extraction with missing base stats."""
        data = {"name": "Test", "pokedex_number": 999, "base_stats": {}}
        info = extract_pokemon_basic_info(data)

        assert info["base_hp"] == -1
        assert info["base_attack"] == -1

    def test_biology_list_concatenation(self, sample_pokemon_data):
        """Test that biology list is properly concatenated."""
        info = extract_pokemon_basic_info(sample_pokemon_data)

        assert isinstance(info["description"], str)
        assert "quadrupedal" in info["description"]
        assert "raised by humans" in info["description"]


class TestExtractGenerationNumber:
    """Tests for extract_generation_number function."""

    @pytest.mark.parametrize("dex_num,expected_gen", [
        (1, 1),      # Bulbasaur
        (151, 1),    # Mew
        (152, 2),    # Chikorita
        (251, 2),    # Celebi
        (252, 3),    # Treecko
        (386, 3),    # Deoxys
        (494, 5),    # Victini
        (722, 7),    # Rowlet
        (810, 8),    # Grookey
        (906, 9),    # Sprigatito
    ])
    def test_generation_ranges(self, dex_num, expected_gen):
        """Test generation number determination for various Pokedex numbers."""
        data = {"pokedex_number": dex_num}
        gen = extract_generation_number(data)
        assert gen == expected_gen

    def test_invalid_dex_number(self):
        """Test handling of invalid Pokedex number."""
        data = {"pokedex_number": 9999}
        gen = extract_generation_number(data)
        assert gen == -1  # Defaults to Gen 1


class TestExtractTypes:
    """Tests for extract_types function."""

    def test_extract_valid_types(self, sample_pokemon_data):
        """Test extracting valid types."""
        types = extract_types(sample_pokemon_data)

        assert len(types) == 2
        assert "Grass" in types
        assert "Poison" in types

    def test_filter_unknown_types(self):
        """Test that 'Unknown' types are filtered out."""
        data = {"types": ["Electric", "Unknown"]}
        types = extract_types(data)

        assert len(types) == 1
        assert "Electric" in types
        assert "Unknown" not in types

    def test_empty_types(self):
        """Test handling of empty types list."""
        data = {"types": []}
        types = extract_types(data)

        assert types == []


class TestExtractAbilities:
    """Tests for extract_abilities function."""

    def test_extract_abilities_dict_format(self, sample_pokemon_data):
        """Test extracting abilities in dictionary format."""
        abilities = extract_abilities(sample_pokemon_data)

        assert len(abilities) == 2
        assert "Overgrow" in abilities
        assert "Chlorophyll" in abilities

    def test_extract_abilities_string_format(self):
        """Test extracting abilities in string format."""
        data = {"abilities": ["Levitate", "Sturdy"]}
        abilities = extract_abilities(data)

        assert len(abilities) == 2
        assert "Levitate" in abilities
        assert "Sturdy" in abilities

    def test_empty_abilities(self):
        """Test handling of empty abilities list."""
        data = {"abilities": []}
        abilities = extract_abilities(data)

        assert abilities == []


class TestExtractMoves:
    """Tests for extract_moves function."""

    def test_extract_moves(self, sample_pokemon_data):
        """Test extracting moves with TM information."""
        moves = extract_moves(sample_pokemon_data)

        assert len(moves) == 3

        tackle = next(m for m in moves if m["move_name"] == "Tackle")
        assert tackle["is_tm"] == 0

        solar_beam = next(m for m in moves if m["move_name"] == "Solar Beam")
        assert solar_beam["is_tm"] == 1

    def test_empty_learnset(self):
        """Test handling of empty learnset."""
        data = {"learnset": []}
        moves = extract_moves(data)

        assert moves == []


class TestExtractAllPokemonData:
    """Tests for extract_all_pokemon_data function."""

    def test_extract_all_pokemon(self, temp_pokemon_dir):
        """Test extracting all Pokemon data from directory."""
        all_pokemon = extract_all_pokemon_data(str(temp_pokemon_dir))

        assert len(all_pokemon) == 2
        assert all("basic_info" in p for p in all_pokemon)
        assert all("types" in p for p in all_pokemon)
        assert all("abilities" in p for p in all_pokemon)
        assert all("moves" in p for p in all_pokemon)

    def test_extract_from_nonexistent_dir(self):
        """Test error when extracting from nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            extract_all_pokemon_data("/nonexistent/directory")
