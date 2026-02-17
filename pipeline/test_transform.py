"""
Unit tests for transform.py module.
Tests data transformation and normalization.
"""

import pytest
from tempfile import TemporaryDirectory
from pathlib import Path

from transform import (
    DataTransformer,
    get_type_color,
    transform_all_pokemon,
    save_tables_to_csv
)


@pytest.fixture
def sample_extracted_pokemon():
    """Fixture providing sample extracted Pokemon data."""
    return [
        {
            "basic_info": {
                "pokemon_id": 1,
                "pokemon_name": "Bulbasaur",
                "gen_number": 1,
                "base_hp": 45,
                "base_attack": 49,
                "base_defense": 49,
                "base_sp_attack": 65,
                "base_sp_def": 65,
                "base_speed": 45,
                "description": "A Grass/Poison-type Pokemon.",
                "evolution": "Evolves into Ivysaur."
            },
            "types": ["Grass", "Poison"],
            "abilities": ["Overgrow", "Chlorophyll"],
            "moves": [
                {"move_name": "Tackle", "is_tm": 0},
                {"move_name": "Solar Beam", "is_tm": 1}
            ]
        },
        {
            "basic_info": {
                "pokemon_id": 25,
                "pokemon_name": "Pikachu",
                "gen_number": 1,
                "base_hp": 35,
                "base_attack": 55,
                "base_defense": 30,
                "base_sp_attack": 50,
                "base_sp_def": 40,
                "base_speed": 90,
                "description": "An Electric-type Pokemon.",
                "evolution": "Evolves into Raichu."
            },
            "types": ["Electric"],
            "abilities": ["Static", "Lightning Rod"],
            "moves": [
                {"move_name": "Tackle", "is_tm": 0},  # Duplicate move
                {"move_name": "Thunder Shock", "is_tm": 0},
                {"move_name": "Thunder Wave", "is_tm": 1}
            ]
        }
    ]


class TestDataTransformer:
    """Tests for DataTransformer class."""

    def test_initialization(self):
        """Test DataTransformer initialization."""
        transformer = DataTransformer()

        assert transformer.pokemon_records == []
        assert transformer.types == {}
        assert transformer.abilities == {}
        assert transformer.moves == {}
        assert transformer.next_type_id == 1
        assert transformer.next_ability_id == 1
        assert transformer.next_move_id == 1

    def test_get_or_create_type(self):
        """Test type creation and retrieval."""
        transformer = DataTransformer()

        # Create new type
        type_id1 = transformer.get_or_create_type("Fire")
        assert type_id1 == 1
        assert "Fire" in transformer.types

        # Retrieve existing type
        type_id2 = transformer.get_or_create_type("Fire")
        assert type_id2 == type_id1

        # Create another type
        type_id3 = transformer.get_or_create_type("Water")
        assert type_id3 == 2

    def test_get_or_create_ability(self):
        """Test ability creation and retrieval."""
        transformer = DataTransformer()

        # Create new ability
        ability_id1 = transformer.get_or_create_ability("Overgrow")
        assert ability_id1 == 1
        assert "Overgrow" in transformer.abilities

        # Retrieve existing ability
        ability_id2 = transformer.get_or_create_ability("Overgrow")
        assert ability_id2 == ability_id1

    def test_get_or_create_move(self):
        """Test move creation and retrieval."""
        transformer = DataTransformer()

        # Create new move
        move_id1 = transformer.get_or_create_move("Tackle", 0)
        assert move_id1 == 1
        assert "Tackle" in transformer.moves
        assert transformer.moves["Tackle"]["is_tm"] == 0

        # Retrieve existing move and update TM status
        move_id2 = transformer.get_or_create_move("Tackle", 1)
        assert move_id2 == move_id1
        assert transformer.moves["Tackle"]["is_tm"] == 1

    def test_transform_pokemon(self, sample_extracted_pokemon):
        """Test transforming a single Pokemon."""
        transformer = DataTransformer()
        transformer.transform_pokemon(sample_extracted_pokemon[0])

        # Check pokemon record
        assert len(transformer.pokemon_records) == 1
        assert transformer.pokemon_records[0]["pokemon_name"] == "Bulbasaur"

        # Check types
        assert len(transformer.types) == 2
        assert "Grass" in transformer.types
        assert "Poison" in transformer.types

        # Check pokemon_type junction table
        assert len(transformer.pokemon_types) == 2

        # Check abilities
        assert len(transformer.abilities) == 2
        assert "Overgrow" in transformer.abilities

        # Check pokemon_ability junction table
        assert len(transformer.pokemon_abilities) == 2

        # Check moves
        assert len(transformer.moves) == 2
        assert "Tackle" in transformer.moves

        # Check pokemon_move junction table
        assert len(transformer.pokemon_moves) == 2

    def test_transform_multiple_pokemon_with_duplicates(self, sample_extracted_pokemon):
        """Test transforming multiple Pokemon with duplicate types/abilities/moves."""
        transformer = DataTransformer()

        for pokemon in sample_extracted_pokemon:
            transformer.transform_pokemon(pokemon)

        # Check pokemon records
        assert len(transformer.pokemon_records) == 2

        # Check types (3 unique: Grass, Poison, Electric)
        assert len(transformer.types) == 3

        # Check abilities (4 unique)
        assert len(transformer.abilities) == 4

        # Check moves (3 unique: Tackle, Solar Beam, Thunder Shock, Thunder Wave)
        # Wait, that's 4. Let me recount: Tackle (shared), Solar Beam, Thunder Shock, Thunder Wave = 4 unique
        assert len(transformer.moves) == 4

        # Tackle should appear in both Pokemon's move lists
        assert "Tackle" in transformer.moves

    def test_get_normalized_tables(self, sample_extracted_pokemon):
        """Test getting normalized tables."""
        transformer = DataTransformer()
        transformer.transform_pokemon(sample_extracted_pokemon[0])

        tables = transformer.get_normalized_tables()

        assert "pokemon" in tables
        assert "type" in tables
        assert "pokemon_type" in tables
        assert "ability" in tables
        assert "pokemon_ability" in tables
        assert "move" in tables
        assert "pokemon_move" in tables

        assert len(tables["pokemon"]) == 1
        assert len(tables["type"]) == 2
        assert len(tables["ability"]) == 2
        assert len(tables["move"]) == 2


class TestGetTypeColor:
    """Tests for get_type_color function."""

    @pytest.mark.parametrize("type_name,expected_color", [
        ("Fire", "#F08030"),
        ("Water", "#6890F0"),
        ("Grass", "#78C850"),
        ("Electric", "#F8D030"),
        ("Psychic", "#F85888"),
        ("Dragon", "#7038F8"),
    ])
    def test_known_types(self, type_name, expected_color):
        """Test colors for known types."""
        color = get_type_color(type_name)
        assert color == expected_color

    def test_unknown_type(self):
        """Test default color for unknown type."""
        color = get_type_color("UnknownType")
        assert color == "#777777"


class TestTransformAllPokemon:
    """Tests for transform_all_pokemon function."""

    def test_transform_all_pokemon(self, sample_extracted_pokemon):
        """Test transforming all Pokemon data."""
        tables = transform_all_pokemon(sample_extracted_pokemon)

        assert "pokemon" in tables
        assert len(tables["pokemon"]) == 2

        # Verify Pokemon names
        pokemon_names = [p["pokemon_name"] for p in tables["pokemon"]]
        assert "Bulbasaur" in pokemon_names
        assert "Pikachu" in pokemon_names

    def test_transform_empty_list(self):
        """Test transforming empty list."""
        tables = transform_all_pokemon([])

        assert len(tables["pokemon"]) == 0
        assert len(tables["type"]) == 0


class TestSaveTablesToCSV:
    """Tests for save_tables_to_csv function."""

    def test_save_tables_to_csv(self, sample_extracted_pokemon):
        """Test saving tables to CSV files."""
        tables = transform_all_pokemon(sample_extracted_pokemon)

        with TemporaryDirectory() as tmpdir:
            csv_paths = save_tables_to_csv(tables, tmpdir)

            # Check that CSV files were created
            assert len(csv_paths) == 7
            assert "pokemon" in csv_paths
            assert "type" in csv_paths

            # Verify files exist
            for csv_path in csv_paths.values():
                assert csv_path.exists()
                assert csv_path.suffix == ".csv"

            # Check content of pokemon.csv
            pokemon_csv = csv_paths["pokemon"]
            content = pokemon_csv.read_text()
            assert "Bulbasaur" in content
            assert "Pikachu" in content

    def test_save_to_nonexistent_directory(self, sample_extracted_pokemon):
        """Test saving to a directory that doesn't exist (should create it)."""
        tables = transform_all_pokemon(sample_extracted_pokemon)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output"
            csv_paths = save_tables_to_csv(tables, str(output_dir))

            assert output_dir.exists()
            assert len(csv_paths) > 0