"""
Unit tests for load.py module.
Tests database loading functionality.
"""

import sqlite3
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from load import (
    create_database_connection,
    initialize_database,
    load_pokemon_table,
    load_type_table,
    load_ability_table,
    load_move_table,
    load_pokemon_type_table,
    load_pokemon_ability_table,
    load_pokemon_move_table,
    load_all_tables
)


@pytest.fixture
def schema_file():
    """Fixture providing a temporary schema file."""
    schema_sql = """
PRAGMA foreign_keys = ON;

CREATE TABLE pokemon (
    pokemon_id INTEGER NOT NULL PRIMARY KEY,
    pokemon_name TEXT NOT NULL,
    gen_number INTEGER NOT NULL,
    base_hp INTEGER NOT NULL,
    base_attack INTEGER NOT NULL,
    base_defense INTEGER NOT NULL,
    base_sp_attack INTEGER NOT NULL,
    base_sp_def INTEGER NOT NULL,
    base_speed INTEGER NOT NULL,
    description TEXT NOT NULL,
    evolution TEXT NOT NULL
);

CREATE TABLE type (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL,
    colour TEXT NOT NULL
);

CREATE TABLE pokemon_type (
    pokemon_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES type(type_id) ON DELETE CASCADE
);

CREATE TABLE ability (
    ability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ability_name TEXT NOT NULL
);

CREATE TABLE pokemon_ability (
    pokemon_ability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES ability(ability_id) ON DELETE CASCADE
);

CREATE TABLE move (
    move_id INTEGER PRIMARY KEY AUTOINCREMENT,
    move_name TEXT NOT NULL,
    is_tm INTEGER NOT NULL
);

CREATE TABLE pokemon_move (
    pokemon_move_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (move_id) REFERENCES move(move_id) ON DELETE CASCADE
);
"""
    with TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "schema.sql"
        schema_path.write_text(schema_sql)
        yield str(schema_path)


@pytest.fixture
def sample_tables():
    """Fixture providing sample normalized table data."""
    return {
        "pokemon": [
            {
                "pokemon_id": 1,
                "pokemon_name": "Bulbasaur",
                "gen_number": 1,
                "base_hp": 45,
                "base_attack": 49,
                "base_defense": 49,
                "base_sp_attack": 65,
                "base_sp_def": 65,
                "base_speed": 45,
                "description": "A Grass/Poison Pokemon.",
                "evolution": "Evolves into Ivysaur."
            },
            {
                "pokemon_id": 25,
                "pokemon_name": "Pikachu",
                "gen_number": 1,
                "base_hp": 35,
                "base_attack": 55,
                "base_defense": 30,
                "base_sp_attack": 50,
                "base_sp_def": 40,
                "base_speed": 90,
                "description": "An Electric Pokemon.",
                "evolution": "Evolves into Raichu."
            }
        ],
        "type": [
            {"type_id": 1, "type_name": "Grass", "colour": "#78C850"},
            {"type_id": 2, "type_name": "Poison", "colour": "#A040A0"},
            {"type_id": 3, "type_name": "Electric", "colour": "#F8D030"}
        ],
        "pokemon_type": [
            {"pokemon_type_id": 1, "pokemon_id": 1, "type_id": 1},
            {"pokemon_type_id": 2, "pokemon_id": 1, "type_id": 2},
            {"pokemon_type_id": 3, "pokemon_id": 25, "type_id": 3}
        ],
        "ability": [
            {"ability_id": 1, "ability_name": "Overgrow"},
            {"ability_id": 2, "ability_name": "Chlorophyll"},
            {"ability_id": 3, "ability_name": "Static"}
        ],
        "pokemon_ability": [
            {"pokemon_ability_id": 1, "pokemon_id": 1, "ability_id": 1},
            {"pokemon_ability_id": 2, "pokemon_id": 1, "ability_id": 2},
            {"pokemon_ability_id": 3, "pokemon_id": 25, "ability_id": 3}
        ],
        "move": [
            {"move_id": 1, "move_name": "Tackle", "is_tm": 0},
            {"move_id": 2, "move_name": "Solar Beam", "is_tm": 1},
            {"move_id": 3, "move_name": "Thunder Shock", "is_tm": 0}
        ],
        "pokemon_move": [
            {"pokemon_move_id": 1, "pokemon_id": 1, "move_id": 1},
            {"pokemon_move_id": 2, "pokemon_id": 1, "move_id": 2},
            {"pokemon_move_id": 3, "pokemon_id": 25, "move_id": 1},
            {"pokemon_move_id": 4, "pokemon_id": 25, "move_id": 3}
        ]
    }


class TestCreateDatabaseConnection:
    """Tests for create_database_connection function."""

    def test_create_connection(self):
        """Test creating a database connection."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            conn = create_database_connection(db_path)

            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

            # Test foreign keys are enabled
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            assert result[0] == 1

            conn.close()


class TestInitializeDatabase:
    """Tests for initialize_database function."""

    def test_initialize_database(self, schema_file):
        """Test database initialization with schema."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            initialize_database(db_path, schema_file)

            # Verify database was created
            assert Path(db_path).exists()

            # Verify tables exist
            conn = create_database_connection(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]

            assert "pokemon" in tables
            assert "type" in tables
            assert "ability" in tables
            assert "move" in tables

            conn.close()

    def test_initialize_with_nonexistent_schema(self):
        """Test error when schema file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            with pytest.raises(FileNotFoundError):
                initialize_database(db_path, "/nonexistent/schema.sql")


class TestLoadPokemonTable:
    """Tests for load_pokemon_table function."""

    def test_load_pokemon_records(self, schema_file, sample_tables):
        """Test loading Pokemon records."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)
            count = load_pokemon_table(conn, sample_tables["pokemon"])
            conn.commit()

            assert count == 2

            # Verify data was inserted
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pokemon")
            assert cursor.fetchone()[0] == 2

            cursor.execute("SELECT pokemon_name FROM pokemon WHERE pokemon_id = 1")
            assert cursor.fetchone()[0] == "Bulbasaur"

            conn.close()


class TestLoadTypeTable:
    """Tests for load_type_table function."""

    def test_load_type_records(self, schema_file, sample_tables):
        """Test loading type records."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)
            count = load_type_table(conn, sample_tables["type"])
            conn.commit()

            assert count == 3

            # Verify data
            cursor = conn.cursor()
            cursor.execute("SELECT type_name FROM type WHERE type_id = 1")
            assert cursor.fetchone()[0] == "Grass"

            conn.close()


class TestLoadAbilityTable:
    """Tests for load_ability_table function."""

    def test_load_ability_records(self, schema_file, sample_tables):
        """Test loading ability records."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)
            count = load_ability_table(conn, sample_tables["ability"])
            conn.commit()

            assert count == 3

            conn.close()


class TestLoadMoveTable:
    """Tests for load_move_table function."""

    def test_load_move_records(self, schema_file, sample_tables):
        """Test loading move records."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)
            count = load_move_table(conn, sample_tables["move"])
            conn.commit()

            assert count == 3

            # Verify TM status
            cursor = conn.cursor()
            cursor.execute("SELECT is_tm FROM move WHERE move_name = 'Solar Beam'")
            assert cursor.fetchone()[0] == 1

            conn.close()


class TestLoadJunctionTables:
    """Tests for junction table loading functions."""

    def test_load_pokemon_type_table(self, schema_file, sample_tables):
        """Test loading pokemon_type junction table."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)

            # Load dependencies first
            load_pokemon_table(conn, sample_tables["pokemon"])
            load_type_table(conn, sample_tables["type"])

            # Load junction table
            count = load_pokemon_type_table(conn, sample_tables["pokemon_type"])
            conn.commit()

            assert count == 3
            conn.close()

    def test_load_pokemon_ability_table(self, schema_file, sample_tables):
        """Test loading pokemon_ability junction table."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)

            load_pokemon_table(conn, sample_tables["pokemon"])
            load_ability_table(conn, sample_tables["ability"])

            count = load_pokemon_ability_table(conn, sample_tables["pokemon_ability"])
            conn.commit()

            assert count == 3
            conn.close()

    def test_load_pokemon_move_table(self, schema_file, sample_tables):
        """Test loading pokemon_move junction table."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            initialize_database(db_path, schema_file)

            conn = create_database_connection(db_path)

            load_pokemon_table(conn, sample_tables["pokemon"])
            load_move_table(conn, sample_tables["move"])

            count = load_pokemon_move_table(conn, sample_tables["pokemon_move"])
            conn.commit()

            assert count == 4
            conn.close()


class TestLoadAllTables:
    """Tests for load_all_tables function."""

    def test_load_all_tables_with_reinit(self, schema_file, sample_tables):
        """Test loading all tables with reinitialization."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            insert_counts = load_all_tables(
                db_path,
                sample_tables,
                reinitialize=True,
                schema_path=schema_file
            )

            assert insert_counts["pokemon"] == 2
            assert insert_counts["type"] == 3
            assert insert_counts["ability"] == 3
            assert insert_counts["move"] == 3
            assert insert_counts["pokemon_type"] == 3

    def test_load_all_tables_without_reinit(self, schema_file, sample_tables):
        """Test loading all tables without reinitialization."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            # Initialize database first
            initialize_database(db_path, schema_file)

            # Load without reinit
            insert_counts = load_all_tables(
                db_path,
                sample_tables,
                reinitialize=False
            )

            assert insert_counts["pokemon"] == 2

    def test_load_all_tables_reinit_without_schema(self, sample_tables):
        """Test error when reinitializing without schema path."""
        with TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            with pytest.raises(ValueError, match="schema_path required"):
                load_all_tables(
                    db_path,
                    sample_tables,
                    reinitialize=True,
                    schema_path=None
                )
