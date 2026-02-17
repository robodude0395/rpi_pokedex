"""
Load module for Pokemon ETL pipeline.
Loads transformed data into SQLite database.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional


def create_database_connection(db_path: str) -> sqlite3.Connection:
    """
    Create a connection to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path: str, schema_path: str) -> None:
    """
    Initialize the database with the schema.
    Drops existing tables and recreates them.
    """
    if not Path(schema_path).exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = create_database_connection(db_path)

    try:
        # Drop existing tables in reverse order (respecting foreign keys)
        conn.execute("PRAGMA foreign_keys = OFF")

        tables = ["pokemon_move", "pokemon_ability", "pokemon_type",
                 "move", "ability", "type", "pokemon"]

        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {table}")

        conn.execute("PRAGMA foreign_keys = ON")

        # Execute schema
        conn.executescript(schema_sql)
        conn.commit()

        print(f"Database initialized successfully at {db_path}")

    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Failed to initialize database: {e}")

    finally:
        conn.close()


def load_pokemon_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """
    Load data into the pokemon table.
    """
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO pokemon (
            pokemon_id, pokemon_name, gen_number,
            base_hp, base_attack, base_defense,
            base_sp_attack, base_sp_def, base_speed,
            description, evolution
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["pokemon_id"],
            record["pokemon_name"],
            record["gen_number"],
            record["base_hp"],
            record["base_attack"],
            record["base_defense"],
            record["base_sp_attack"],
            record["base_sp_def"],
            record["base_speed"],
            record["description"],
            record["evolution"]
        ))

    return len(records)


def load_type_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Load data into the type table."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO type (type_id, type_name, colour)
        VALUES (?, ?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["type_id"],
            record["type_name"],
            record["colour"]
        ))

    return len(records)


def load_ability_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Load data into the ability table."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO ability (ability_id, ability_name)
        VALUES (?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["ability_id"],
            record["ability_name"]
        ))

    return len(records)


def load_move_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Load data into the move table."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO move (move_id, move_name, is_tm)
        VALUES (?, ?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["move_id"],
            record["move_name"],
            record["is_tm"]
        ))

    return len(records)


def load_pokemon_type_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Load data into the pokemon_type junction table."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO pokemon_type (pokemon_type_id, pokemon_id, type_id)
        VALUES (?, ?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["pokemon_type_id"],
            record["pokemon_id"],
            record["type_id"]
        ))

    return len(records)


def load_pokemon_ability_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Load data into the pokemon_ability junction table."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO pokemon_ability (pokemon_ability_id, pokemon_id, ability_id)
        VALUES (?, ?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["pokemon_ability_id"],
            record["pokemon_id"],
            record["ability_id"]
        ))

    return len(records)


def load_pokemon_move_table(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Load data into the pokemon_move junction table."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO pokemon_move (pokemon_move_id, pokemon_id, move_id)
        VALUES (?, ?, ?)
    """

    for record in records:
        cursor.execute(insert_sql, (
            record["pokemon_move_id"],
            record["pokemon_id"],
            record["move_id"]
        ))

    return len(records)


def load_all_tables(db_path: str, tables: Dict[str, List[Dict[str, Any]]],
                   reinitialize: bool = False, schema_path: Optional[str] = None) -> Dict[str, int]:
    """Load all normalized tables into the database."""
    if reinitialize:
        if not schema_path:
            raise ValueError("schema_path required when reinitialize=True")
        initialize_database(db_path, schema_path)

    conn = create_database_connection(db_path)
    insert_counts = {}

    try:
        # Load tables in correct order (respecting foreign keys)
        # Main tables first, then junction tables

        if "pokemon" in tables:
            count = load_pokemon_table(conn, tables["pokemon"])
            insert_counts["pokemon"] = count
            print(f"Loaded {count} Pokemon records")

        if "type" in tables:
            count = load_type_table(conn, tables["type"])
            insert_counts["type"] = count
            print(f"Loaded {count} type records")

        if "ability" in tables:
            count = load_ability_table(conn, tables["ability"])
            insert_counts["ability"] = count
            print(f"Loaded {count} ability records")

        if "move" in tables:
            count = load_move_table(conn, tables["move"])
            insert_counts["move"] = count
            print(f"Loaded {count} move records")

        if "pokemon_type" in tables:
            count = load_pokemon_type_table(conn, tables["pokemon_type"])
            insert_counts["pokemon_type"] = count
            print(f"Loaded {count} pokemon_type records")

        if "pokemon_ability" in tables:
            count = load_pokemon_ability_table(conn, tables["pokemon_ability"])
            insert_counts["pokemon_ability"] = count
            print(f"Loaded {count} pokemon_ability records")

        if "pokemon_move" in tables:
            count = load_pokemon_move_table(conn, tables["pokemon_move"])
            insert_counts["pokemon_move"] = count
            print(f"Loaded {count} pokemon_move records")

        conn.commit()
        print(f"\nSuccessfully loaded all data into {db_path}")

    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Failed to load data: {e}")

    finally:
        conn.close()

    return insert_counts