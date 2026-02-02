-- SQLite Schema for Pokemon Database

-- Enable foreign key support (must be set each connection)
PRAGMA foreign_keys = ON;

CREATE TABLE pokemon (
    pokemon_id INTEGER NOT NULL PRIMARY KEY,  -- Manually inserted to match dex ID
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
    is_tm INTEGER NOT NULL  -- SQLite uses 0/1 for boolean
);

CREATE TABLE pokemon_move (
    pokemon_move_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    FOREIGN KEY (move_id) REFERENCES move(move_id) ON DELETE CASCADE
);

-- Optional: Create indexes for faster lookups
CREATE INDEX idx_pokemon_type_pokemon ON pokemon_type(pokemon_id);
CREATE INDEX idx_pokemon_type_type ON pokemon_type(type_id);
CREATE INDEX idx_pokemon_ability_pokemon ON pokemon_ability(pokemon_id);
CREATE INDEX idx_pokemon_move_pokemon ON pokemon_move(pokemon_id);