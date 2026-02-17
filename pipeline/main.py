#!/usr/bin/env python3
"""
Pokemon ETL Pipeline - Main CLI Tool

Extracts Pokemon data from JSON files, transforms it into normalized tables,
and loads it into a SQLite database.

Usage:
    python main.py --input ../web_scraping/raw_pokemon --output ../schema/pokemon.db
    python main.py --input ../web_scraping/raw_pokemon --output ../schema/pokemon.db --out_csv
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add pipeline directory to path to support running from repo root
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import pipeline modules
from extract import extract_all_pokemon_data
from transform import transform_all_pokemon, save_tables_to_csv
from load import load_all_tables


def setup_argparse() -> argparse.ArgumentParser:
    """Setup command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Pokemon ETL Pipeline - Extract, Transform, and Load Pokemon data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from repo root
  python -m pipeline.main --input web_scraping/raw_pokemon --output schema/pokemon.db

  # With CSV export
  python -m pipeline.main --input web_scraping/raw_pokemon --output schema/pokemon.db --out_csv

  # From pipeline directory (legacy)
  cd pipeline && python main.py --input ../web_scraping/raw_pokemon --output ../schema/pokemon.db

  # Specify custom CSV output directory
  python -m pipeline.main --input web_scraping/raw_pokemon --output schema/pokemon.db --out_csv --csv_dir ./csv_output

  # Skip database reinitialization (append mode - use with caution)
  python -m pipeline.main --input web_scraping/raw_pokemon --output schema/pokemon.db --no-reinit
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input directory containing Pokemon JSON files (e.g., web_scraping/raw_pokemon or ../web_scraping/raw_pokemon)"
    )

    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output SQLite database file path (e.g., schema/pokemon.db or ../schema/pokemon.db)"
    )

    parser.add_argument(
        "--schema", "-s",
        default="schema/schema.sql",
        help="Path to schema SQL file (default: schema/schema.sql)"
    )

    parser.add_argument(
        "--out_csv",
        action="store_true",
        help="Export transformed data to CSV files"
    )

    parser.add_argument(
        "--csv_dir",
        default="./output",
        help="Directory for CSV output files (default: ./output)"
    )

    parser.add_argument(
        "--no-reinit",
        action="store_true",
        help="Skip database reinitialization (keeps existing data - use with caution)"
    )

    return parser


def print_banner():
    """Print a nice banner for the CLI."""
    banner = """
╔═══════════════════════════════════════════════════╗
║         Pokemon Database ETL Pipeline            ║
║     Extract → Transform → Load Pokemon Data      ║
╚═══════════════════════════════════════════════════╝
"""
    print(banner)


def print_summary(stats: dict):
    """
    Print a summary of the ETL process.

    Args:
        stats: Dictionary containing ETL statistics
    """
    print("\n" + "="*60)
    print("ETL PIPELINE SUMMARY")
    print("="*60)

    if "extract" in stats:
        print(f"\n📥 EXTRACTION:")
        print(f"   Pokemon extracted: {stats['extract']['pokemon_count']}")
        print(f"   Time taken: {stats['extract']['time']:.2f}s")

    if "transform" in stats:
        print(f"\n🔄 TRANSFORMATION:")
        print(f"   Pokemon records: {stats['transform']['pokemon']}")
        print(f"   Types: {stats['transform']['type']}")
        print(f"   Abilities: {stats['transform']['ability']}")
        print(f"   Moves: {stats['transform']['move']}")
        print(f"   Time taken: {stats['transform']['time']:.2f}s")

    if "load" in stats:
        print(f"\n💾 DATABASE LOADING:")
        for table, count in stats['load']['insert_counts'].items():
            print(f"   {table}: {count} records")
        print(f"   Time taken: {stats['load']['time']:.2f}s")

    if "csv" in stats:
        print(f"\n📄 CSV EXPORT:")
        print(f"   Files saved: {stats['csv']['file_count']}")
        print(f"   Output directory: {stats['csv']['directory']}")

    if "total_time" in stats:
        print(f"\n⏱️  Total pipeline time: {stats['total_time']:.2f}s")

    print("="*60)


def run_etl_pipeline(args) -> int:
    """Run the complete ETL pipeline."""
    stats = {}
    pipeline_start = datetime.now()

    try:
        # Validate paths
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ Error: Input directory does not exist: {args.input}")
            return 1

        schema_path = Path(args.schema)
        if not args.no_reinit and not schema_path.exists():
            print(f"❌ Error: Schema file does not exist: {args.schema}")
            return 1

        # Create output directory if needed
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # EXTRACT
        print("\n📥 STEP 1: EXTRACTING Pokemon data...")
        extract_start = datetime.now()

        extracted_pokemon = extract_all_pokemon_data(str(input_path))

        extract_time = (datetime.now() - extract_start).total_seconds()
        stats["extract"] = {
            "pokemon_count": len(extracted_pokemon),
            "time": extract_time
        }

        print(f"✓ Extracted {len(extracted_pokemon)} Pokemon")

        if len(extracted_pokemon) == 0:
            print("❌ Error: No Pokemon data extracted")
            return 1

        # TRANSFORM
        print("\n🔄 STEP 2: TRANSFORMING data...")
        transform_start = datetime.now()

        tables = transform_all_pokemon(extracted_pokemon)

        transform_time = (datetime.now() - transform_start).total_seconds()
        stats["transform"] = {
            "pokemon": len(tables.get("pokemon", [])),
            "type": len(tables.get("type", [])),
            "ability": len(tables.get("ability", [])),
            "move": len(tables.get("move", [])),
            "time": transform_time
        }

        print(f"✓ Transformed into {len(tables)} tables")

        # SAVE CSV (optional)
        if args.out_csv:
            print(f"\n📄 STEP 3: SAVING CSV files to {args.csv_dir}...")
            csv_paths = save_tables_to_csv(tables, args.csv_dir)
            stats["csv"] = {
                "file_count": len(csv_paths),
                "directory": args.csv_dir
            }
            print(f"✓ Saved {len(csv_paths)} CSV files")

        # LOAD
        print(f"\n💾 STEP {4 if args.out_csv else 3}: LOADING data into database...")
        load_start = datetime.now()

        if not args.no_reinit:
            print("   Reinitializing database...")

        insert_counts = load_all_tables(
            str(output_path),
            tables,
            reinitialize=not args.no_reinit,
            schema_path=str(schema_path) if not args.no_reinit else None
        )

        load_time = (datetime.now() - load_start).total_seconds()
        stats["load"] = {
            "insert_counts": insert_counts,
            "time": load_time
        }

        print(f"✓ Loaded all data into {args.output}")

        # Calculate total time
        total_time = (datetime.now() - pipeline_start).total_seconds()
        stats["total_time"] = total_time

        # Print summary
        print_summary(stats)

        print("\n✅ ETL pipeline completed successfully!")
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        return 1

    except ValueError as e:
        print(f"\n❌ Validation Error: {e}")
        return 1

    except RuntimeError as e:
        print(f"\n❌ Runtime Error: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        traceback.print_exc()
        return 1


def main():
    """Main entry point for the CLI."""
    parser = setup_argparse()
    args = parser.parse_args()

    print_banner()

    exit_code = run_etl_pipeline(args)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
