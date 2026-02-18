#!/bin/bash
# Pokemon ETL Pipeline - Main entry point

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Pokemon ETL Pipeline${NC}"
echo "=========================================="

# Get the repo root directory (parent of this script's directory)
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Change to repo root
cd "$REPO_ROOT" || exit 1

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Default paths (relative to repo root)
INPUT_DIR="web_scraping/raw_pokemon"
OUTPUT_DB="schema/pokedex.db"
SCHEMA_FILE="schema/schema.sql"

# Run the pipeline from repo root
echo -e "\n${GREEN}Running ETL pipeline from: $(pwd)${NC}\n"

python3 -m pipeline.main \
    --input "$INPUT_DIR" \
    --output "$OUTPUT_DB" \
    --schema "$SCHEMA_FILE" \
    --out_csv

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Pipeline completed successfully!${NC}"
    echo -e "Database created at: ${OUTPUT_DB}"
    echo -e "CSV files saved in: ./output/"
else
    echo -e "\n${RED}✗ Pipeline failed!${NC}"
    exit 1
fi
