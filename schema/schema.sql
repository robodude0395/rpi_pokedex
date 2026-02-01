-- PostgreSQL Schema for Pokemon Database

CREATE TABLE pokemon (
    pokemon_id SMALLINT NOT NULL PRIMARY KEY,  -- Manually inserted to match dex ID
    pokemon_name VARCHAR(255) NOT NULL,
    gen_number SMALLINT NOT NULL,
    base_hp SMALLINT NOT NULL,
    base_attack SMALLINT NOT NULL,
    base_defense SMALLINT NOT NULL,
    base_sp_attack SMALLINT NOT NULL,
    base_sp_def SMALLINT NOT NULL,
    base_speed SMALLINT NOT NULL,
    description TEXT NOT NULL,
    evolution TEXT NOT NULL
);

CREATE TABLE type (
    type_id BIGSERIAL PRIMARY KEY,
    type_name VARCHAR(255) NOT NULL,
    colour VARCHAR(255) NOT NULL
);

CREATE TABLE pokemon_type (
    pokemon_type_id BIGSERIAL PRIMARY KEY,
    pokemon_id SMALLINT NOT NULL,
    type_id BIGINT NOT NULL,
    CONSTRAINT pokemon_type_pokemon_id_foreign FOREIGN KEY (pokemon_id)
        REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    CONSTRAINT pokemon_type_type_id_foreign FOREIGN KEY (type_id) 
        REFERENCES type(type_id) ON DELETE CASCADE
);

CREATE TABLE ability (
    ability_id BIGSERIAL PRIMARY KEY,
    ability_name VARCHAR(255) NOT NULL
);

CREATE TABLE pokemon_ability (
    pokemon_ability_id BIGSERIAL PRIMARY KEY,
    pokemon_id SMALLINT NOT NULL,
    ability_id BIGINT NOT NULL,
    CONSTRAINT pokemon_ability_pokemon_id_foreign FOREIGN KEY (pokemon_id) 
        REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    CONSTRAINT pokemon_ability_ability_id_foreign FOREIGN KEY (ability_id) 
        REFERENCES ability(ability_id) ON DELETE CASCADE
);

CREATE TABLE move (
    move_id BIGSERIAL PRIMARY KEY,
    move_name VARCHAR(255) NOT NULL,
    is_tm BOOLEAN NOT NULL
);

CREATE TABLE pokemon_move (
    pokemon_move_id BIGSERIAL PRIMARY KEY,
    pokemon_id SMALLINT NOT NULL,
    move_id BIGINT NOT NULL,
    CONSTRAINT pokemon_move_pokemon_id_foreign FOREIGN KEY (pokemon_id) 
        REFERENCES pokemon(pokemon_id) ON DELETE CASCADE,
    CONSTRAINT pokemon_move_move_id_foreign FOREIGN KEY (move_id) 
        REFERENCES move(move_id) ON DELETE CASCADE
);