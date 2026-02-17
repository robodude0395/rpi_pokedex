# Pokemon ETL Pipeline

A complete Extract, Transform, Load (ETL) pipeline for processing Pokemon data from JSON files into a normalized SQLite database.

## Features

- **Extract**: Read Pokemon data from JSON files in the `raw_pokemon` folder
- **Transform**: Normalize data into relational database tables matching the schema
- **Load**: Insert transformed data into SQLite database
- **CSV Export**: Optionally export transformed data to CSV files
- **CLI Interface**: Easy-to-use command-line tool
- **Comprehensive Tests**: Full pytest test coverage for all modules

## Project Structure

```
pipeline/
├── extract.py          # Data extraction functions
├── transform.py        # Data transformation & normalization
├── load.py            # Database loading functions
├── main.py            # CLI orchestrator
├── test_extract.py    # Tests for extract.py
├── test_transform.py  # Tests for transform.py
├── test_load.py       # Tests for load.py
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Installation

No external dependencies required beyond Python standard library for the ETL pipeline itself. For testing:

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start from Repository Root

The simplest way to run the pipeline:

```bash
bash main.sh
```

This runs with default options including CSV export and database verification.

### Running with Custom Options from Repository Root

```bash
python pipeline/main.py --input web_scraping/raw_pokemon --output schema/pokemon.db
```

### With CSV Export

```bash
python pipeline/main.py --input web_scraping/raw_pokemon --output schema/pokemon.db --out_csv
```

### Custom CSV Directory

```bash
python pipeline/main.py --input web_scraping/raw_pokemon --output schema/pokemon.db --out_csv --csv_dir ./my_csv_files
```

### Verify Database After Loading

```bash
python pipeline/main.py --input web_scraping/raw_pokemon --output schema/pokemon.db --verify
```

### Running from Pipeline Directory

If you prefer to work from within the pipeline directory:

```bash
cd pipeline
python main.py --input ../web_scraping/raw_pokemon --output ../schema/pokemon.db
```

### All Options

```bash
python main.py -h
```

**Available options:**
- `--input, -i`: Input directory containing Pokemon JSON files (required)
- `--output, -o`: Output SQLite database file path (required)
- `--schema, -s`: Path to schema SQL file (default: ../schema/schema.sql)
- `--out_csv`: Export transformed data to CSV files
- `--csv_dir`: Directory for CSV output (default: ./output)
- `--no-reinit`: Skip database reinitialization (keeps existing data)
- `--verify`: Verify database after loading
- `--verbose, -v`: Enable verbose output

## Running Tests

Run all tests:

```bash
pytest
```

Run tests for a specific module:

```bash
pytest test_extract.py
pytest test_transform.py
pytest test_load.py
```

Run with verbose output:

```bash
pytest -v
```

Run with coverage report:

```bash
pytest --cov=. --cov-report=html
```

## Module Documentation

### extract.py

Handles data extraction from JSON files.

**Key Functions:**
- `find_pokemon_json_files(input_dir)`: Recursively find all details.json files
- `read_pokemon_json(json_path)`: Read and parse a Pokemon JSON file
- `extract_pokemon_basic_info(pokemon_data)`: Extract basic Pokemon info
- `extract_types(pokemon_data)`: Extract Pokemon types
- `extract_abilities(pokemon_data)`: Extract Pokemon abilities
- `extract_moves(pokemon_data)`: Extract Pokemon moves
- `extract_all_pokemon_data(input_dir)`: Extract all Pokemon from directory

### transform.py

Transforms extracted data into normalized database tables.

**Key Functions:**
- `DataTransformer`: Class managing the transformation process
  - `get_or_create_type(type_name)`: Get/create type entry
  - `get_or_create_ability(ability_name)`: Get/create ability entry
  - `get_or_create_move(move_name, is_tm)`: Get/create move entry
  - `transform_pokemon(extracted_data)`: Transform single Pokemon
  - `get_normalized_tables()`: Get all normalized tables
- `transform_all_pokemon(extracted_pokemon)`: Transform all Pokemon data
- `save_tables_to_csv(tables, output_dir)`: Save tables to CSV files
- `validate_transformed_data(tables)`: Validate data consistency

### load.py

Loads transformed data into SQLite database.

**Key Functions:**
- `create_database_connection(db_path)`: Create database connection
- `initialize_database(db_path, schema_path)`: Initialize database with schema
- `load_pokemon_table(conn, records)`: Load Pokemon records
- `load_type_table(conn, records)`: Load type records
- `load_ability_table(conn, records)`: Load ability records
- `load_move_table(conn, records)`: Load move records
- `load_pokemon_type_table(conn, records)`: Load pokemon-type relationships
- `load_pokemon_ability_table(conn, records)`: Load pokemon-ability relationships
- `load_pokemon_move_table(conn, records)`: Load pokemon-move relationships
- `load_all_tables(db_path, tables, reinitialize, schema_path)`: Load all tables
- `verify_database(db_path)`: Count records in each table
- `query_pokemon_by_id(db_path, pokemon_id)`: Query Pokemon with relationships

## Database Schema

The pipeline creates a normalized relational database with the following tables:

- **pokemon**: Core Pokemon data (stats, description, evolution)
- **type**: Pokemon types (name, color)
- **ability**: Pokemon abilities
- **move**: Pokemon moves (name, TM status)
- **pokemon_type**: Junction table linking Pokemon to types
- **pokemon_ability**: Junction table linking Pokemon to abilities
- **pokemon_move**: Junction table linking Pokemon to moves

## Data Flow

```
JSON Files → Extract → Transform → (Optional CSV) → Load → SQLite Database
```

1. **Extract**: Read all `details.json` files from the input directory
2. **Transform**: Normalize data into separate tables with proper IDs and relationships
3. **CSV Export** (optional): Save transformed data as CSV files
4. **Load**: Insert data into SQLite database respecting foreign key constraints

## Error Handling

The pipeline includes comprehensive error handling:

- File not found errors
- Invalid JSON errors
- Database constraint violations
- Data validation errors
- Foreign key violations

All errors are reported with clear messages to help debug issues.

## Performance

The pipeline is optimized for Gen 1 Pokemon (~151 Pokemon) but can handle much larger datasets. For very large datasets, consider:

- Batch processing in chunks
- Using database transactions efficiently
- Monitoring memory usage

## Example Output

```
╔═══════════════════════════════════════════════════╗
║         Pokemon Database ETL Pipeline            ║
║     Extract → Transform → Load Pokemon Data      ║
╚═══════════════════════════════════════════════════╝

📥 STEP 1: EXTRACTING Pokemon data...
✓ Extracted 151 Pokemon

🔄 STEP 2: TRANSFORMING data...
✓ Transformed into 7 tables

📄 STEP 3: SAVING CSV files to ./output...
Saved 151 records to ./output/pokemon.csv
Saved 18 records to ./output/type.csv
...
✓ Saved 7 CSV files

💾 STEP 4: LOADING data into database...
Loaded 151 Pokemon records
Loaded 18 type records
...
✓ Loaded all data into ../schema/pokemon.db

============================================================
ETL PIPELINE SUMMARY
============================================================

📥 EXTRACTION:
   Pokemon extracted: 151
   Time taken: 0.45s

🔄 TRANSFORMATION:
   Pokemon records: 151
   Types: 18
   Abilities: 266
   Moves: 558
   Time taken: 0.12s

💾 DATABASE LOADING:
   pokemon: 151 records
   type: 18 records
   ability: 266 records
   move: 558 records
   pokemon_type: 226 records
   pokemon_ability: 315 records
   pokemon_move: 2847 records
   Time taken: 0.89s

⏱️  Total pipeline time: 1.46s
============================================================

✅ ETL pipeline completed successfully!
```

## Troubleshooting

### Common Issues

**Issue**: "No details.json files found"
- **Solution**: Check that the input directory path is correct and contains Pokemon data

**Issue**: "Schema file not found"
- **Solution**: Ensure the schema.sql file exists at the specified path

**Issue**: "Foreign key constraint violation"
- **Solution**: Run with `--no-reinit` flag removed to reinitialize the database

**Issue**: "Invalid JSON in file"
- **Solution**: Check the specific JSON file for syntax errors

## Contributing

When adding new features:

1. Write unit tests for new functions
2. Update this README with usage examples
3. Ensure all existing tests still pass
4. Follow the existing code style

## License

Part of the rpi_pokedex project.
