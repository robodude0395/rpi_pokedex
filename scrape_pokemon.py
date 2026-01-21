"""
Bulbapedia Pokemon Scraper
Scrapes Pokemon data from Bulbapedia for a specific generation
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import re


class BulbapediaScraper:
    """Scraper for Bulbapedia Pokemon data"""

    BASE_URL = "https://bulbapedia.bulbagarden.net"

    def __init__(self, generation: int, output_dir: str = "raw_pokemon", debug_mode: bool = False):
        """
        Initialize the scraper

        Args:
            generation: Pokemon generation number (1-9)
            output_dir: Base output directory for scraped data
            debug_mode: If True, only process one Pokemon for testing
        """
        self.generation = generation
        self.output_dir = output_dir
        self.gen_dir = os.path.join(output_dir, f"Gen_{generation}")
        self.debug_mode = debug_mode

        # Create necessary directories
        os.makedirs(self.gen_dir, exist_ok=True)

        # Headers to mimic a browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def get_generation_list_url(self) -> str:
        """Get the URL for the Pokemon list by National Pokedex number"""
        return f"{self.BASE_URL}/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_pokemon_list(self) -> List[Dict[str, str]]:
        """
        Get list of Pokemon from the main list page for the specified generation

        Returns:
            List of dictionaries containing pokemon name, number, and URL
        """
        list_url = self.get_generation_list_url()
        soup = self.fetch_page(list_url)

        if not soup:
            return []

        pokemon_list = []

        # Find the table with Pokemon data
        tables = soup.find_all('table', class_='roundy')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                # Look for rows with Pokemon data
                cells = row.find_all('td')

                if len(cells) >= 3:
                    # First cell usually contains the Pokedex number
                    number_cell = cells[0]
                    number_text = number_cell.get_text(strip=True)

                    # Try to extract number
                    number_match = re.search(r'#?(\d+)', number_text)
                    if not number_match:
                        continue

                    pokedex_number = int(number_match.group(1))

                    # Filter by generation ranges
                    gen_ranges = {
                        1: (1, 151),
                        2: (152, 251),
                        3: (252, 386),
                        4: (387, 493),
                        5: (494, 649),
                        6: (650, 721),
                        7: (722, 809),
                        8: (810, 905),
                        9: (906, 1025)
                    }

                    if self.generation not in gen_ranges:
                        print(f"Invalid generation: {self.generation}")
                        return []

                    min_num, max_num = gen_ranges[self.generation]
                    if not (min_num <= pokedex_number <= max_num):
                        continue


                    # The second cell (index 1) contains the image
                    image_url = None
                    if len(cells) > 1:
                        img_tag = cells[1].find('img')
                        if img_tag:
                            src = img_tag.get('src', '')
                            if src:
                                if src.startswith('//'):
                                    image_url = 'https:' + src
                                elif src.startswith('/'):
                                    image_url = 'https://bulbapedia.bulbagarden.net' + src
                                else:
                                    image_url = src

                    # The third cell (index 2) contains the Pokemon name
                    if len(cells) < 3:
                        continue
                    name_cell = cells[2]
                    # Find the Pokemon link in this cell
                    name_link = name_cell.find('a', href=re.compile(r'.*\(Pok.*mon.*\)'))
                    if name_link:
                        pokemon_name = name_link.get_text(strip=True)
                        href = name_link.get('href', '')
                        # Build full URL
                        if href.startswith('http'):
                            pokemon_url = href
                        else:
                            pokemon_url = self.BASE_URL + href
                        print(f"  Found: #{pokedex_number:03d} - {pokemon_name}")  # Debug log
                        pokemon_list.append({
                            'number': pokedex_number,
                            'name': pokemon_name,
                            'url': pokemon_url,
                            'table_image_url': image_url
                        })

        return pokemon_list

    def scrape_pokemon_details(self, pokemon_url: str) -> Dict[str, any]:
        """
        Scrape detailed information from a Pokemon's individual page

        Args:
            pokemon_url: URL to the Pokemon's page

        Returns:
            Dictionary containing Pokemon details
        """
        soup = self.fetch_page(pokemon_url)

        if not soup:
            return {}

        details = {}

        # Extract from the info box - look for the table that contains Pokédex data
        # The main infobox typically has specific styling and contains species/type info
        infobox = None
        tables = soup.find_all('table', class_='roundy')
        for table in tables:
            # Look for a table that contains "Species" or "Type" row
            if table.find('th', string=re.compile(r'Species|Type', re.IGNORECASE)):
                infobox = table
                break

        # Fallback to first roundy table if specific one not found
        if not infobox and tables:
            infobox = tables[0]

        if infobox:
            # Extract types
            types = []
            type_cells = infobox.find_all('a', href=re.compile(r'/wiki/.*\(type\)'))
            for type_cell in type_cells:
                type_name = type_cell.get_text(strip=True)
                if type_name and type_name not in types:
                    types.append(type_name)
            details['types'] = types[:2]  # Pokemon have max 2 types

            # Extract from table rows
            rows = infobox.find_all('tr')
            for row in rows:
                header = row.find('th')
                if not header:
                    continue

                header_text = header.get_text(strip=True).lower()
                cell = row.find('td')

                if not cell:
                    continue

                # Species
                if 'species' in header_text:
                    details['species'] = cell.get_text(strip=True)

                # Height
                elif 'height' in header_text:
                    details['height'] = cell.get_text(separator=' ', strip=True)

                # Weight
                elif 'weight' in header_text:
                    details['weight'] = cell.get_text(separator=' ', strip=True)

                # Gender ratio
                elif 'gender' in header_text:
                    details['gender_ratio'] = cell.get_text(strip=True)

                # Catch rate
                elif 'catch rate' in header_text:
                    catch_rate_text = cell.get_text(strip=True)
                    # Extract just the number
                    match = re.search(r'(\d+)', catch_rate_text)
                    if match:
                        details['catch_rate'] = match.group(1)
                    else:
                        details['catch_rate'] = catch_rate_text

                # Base friendship
                elif 'base friendship' in header_text or 'base happiness' in header_text:
                    details['base_friendship'] = cell.get_text(strip=True)

                # Base exp
                elif 'base exp' in header_text:
                    details['base_exp'] = cell.get_text(strip=True)

                # Growth rate
                elif 'growth rate' in header_text or 'leveling rate' in header_text:
                    details['leveling_rate'] = cell.get_text(strip=True)

                # Egg groups
                elif 'egg group' in header_text:
                    details['egg_groups'] = cell.get_text(strip=True)

                # Egg cycles
                elif 'egg cycles' in header_text:
                    details['egg_cycles'] = cell.get_text(strip=True)

                # Pokédex color
                elif 'color' in header_text and 'dex' in header_text.lower():
                    color_link = cell.find('a')
                    if color_link:
                        details['pokedex_color'] = color_link.get_text(strip=True)
                    else:
                        details['pokedex_color'] = cell.get_text(strip=True)

        # Extract Abilities from dedicated abilities section
        # Look for <b><a href="..." title="Abilities">...</a></b>
        abilities_header = soup.find('b', string=re.compile(r'Abilit', re.IGNORECASE))
        if not abilities_header:
            abilities_header = soup.find('a', attrs={'title': 'Abilities'})
            if abilities_header:
                abilities_header = abilities_header.find_parent('b')

        if abilities_header:
            # Find the next table after this header
            abilities_table = abilities_header.find_next('table', class_='roundy')
            if abilities_table:
                # Make sure the table doesn't have display: none
                table_style = abilities_table.get('style', '')
                if 'display: none' not in table_style:
                    abilities = []

                    # Get all td tags in this table
                    for cell in abilities_table.find_all('td'):
                        # Skip cells with display: none
                        cell_style = cell.get('style', '')
                        if 'display: none' in cell_style or 'display:none' in cell_style:
                            continue

                        # Get ability name from the link in this cell
                        ability_link = cell.find('a')
                        if ability_link:
                            ability_name = ability_link.get_text(strip=True)

                            # Check if it's hidden (look for <small>Hidden Ability</small>)
                            small_tag = cell.find('small', string=re.compile(r'Hidden', re.IGNORECASE))
                            is_hidden = small_tag is not None

                            abilities.append({
                                'name': ability_name,
                                'hidden': is_hidden
                            })

                    if abilities:
                        details['abilities'] = abilities

        # Extract base stats as a nested dict from the table below the 'Base stats' headline
        base_stats = {}
        base_stats_span = soup.find('span', id='Base_stats')
        if base_stats_span:
            # Find the next table after the base stats span (regardless of class)
            stats_table = base_stats_span.find_next('table')
            if stats_table:
                rows = stats_table.find_all('tr')
                for row in rows:
                    ths = row.find_all('th')
                    # Stat rows have a th with two divs: stat name and value
                    if len(ths) == 1:
                        divs = ths[0].find_all('div')
                        if len(divs) == 2:
                            stat_name = divs[0].get_text(strip=True).replace(':','')
                            stat_value = divs[1].get_text(strip=True)
                            # Only include main stats
                            if stat_name in ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"] and stat_value.isdigit():
                                base_stats[stat_name] = int(stat_value)
        if base_stats:
            details['base_stats'] = base_stats

        # Extract high-res official artwork image
        import unicodedata
        def normalize_name(name):
            return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()

        image_url = None
        image_tags = soup.find_all('img')
        # Try to find the img with alt matching the pokemon name (normalized)
        for img in image_tags:
            alt = img.get('alt', '')
            if normalize_name(alt) == normalize_name(details.get('species', '') or details.get('name', '')):
                srcset = img.get('srcset', '')
                if srcset:
                    # Get the largest image from srcset
                    candidates = [u.split(' ')[0] for u in srcset.split(',') if u.strip()]
                    if candidates:
                        image_url = candidates[-1]
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = 'https://bulbapedia.bulbagarden.net' + image_url
                        if image_url:
                            details['image_url'] = image_url
                            break
                # fallback to src if no srcset
                src = img.get('src', '')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://bulbapedia.bulbagarden.net' + src
                    if src:
                        details['image_url'] = src
                        break

        # If not found, fallback to previous logic for any archives png
        if 'image_url' not in details:
            for img in image_tags:
                src = img.get('src', '')
                if '.png' in src and 'archives' in src and 'MS' not in src:
                    if src:
                        details['image_url'] = 'https:' + src if src.startswith('//') else src
                        break

        # Helper function to clean text (remove citation references)
        def clean_text(text):
            # Remove citation references like [1], [2], etc.
            text = re.sub(r'\s*\[\s*\d+\s*\]\s*', '', text)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        # Extract Biology/Description
        biology_section = soup.find('span', id='Biology')
        if biology_section:
            # Find the parent heading and get the next sibling paragraphs
            heading = biology_section.find_parent(['h2', 'h3'])
            if heading:
                description_parts = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3']:  # Stop at next section
                        break
                    if sibling.name == 'p':
                        # Use separator to add spaces between inline elements
                        text = sibling.get_text(separator=' ', strip=True)
                        if text:
                            # Clean citation references
                            text = clean_text(text)
                            if text:
                                description_parts.append(text)
                if description_parts:
                    # Store as list of paragraphs
                    details['biology'] = description_parts[:3]

        # Extract Evolution information
        evolution_section = soup.find('span', id='Evolution')
        if evolution_section:
            heading = evolution_section.find_parent(['h2', 'h3'])
            if heading:
                # Look for evolution text in the next paragraph or list
                evolution_info = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3']:
                        break
                    if sibling.name == 'p':
                        # Use separator to add spaces between inline elements
                        text = sibling.get_text(separator=' ', strip=True)
                        if text and len(text) > 10:
                            # Clean citation references
                            text = clean_text(text)
                            if text:
                                evolution_info.append(text)
                                break
                if evolution_info:
                    details['evolution'] = evolution_info[0]

        # Extract Learnset (moves from level-up and TM)
        learnset = {}

        # Get level-up moves
        learnset_section = soup.find('span', id=re.compile(r'By_leveling_up'))
        if learnset_section:
            heading = learnset_section.find_parent(['h2', 'h3', 'h4'])
            if heading:
                # Find the next table after this heading
                moves_table = heading.find_next('table', class_='roundy')
                if moves_table:
                    rows = moves_table.find_all('tr')
                    for row in rows:
                        # Look for move name links
                        move_link = row.find('a', href=re.compile(r'/wiki/.*\(move\)'))
                        if move_link:
                            move_name = move_link.get_text(strip=True)
                            if move_name and move_name not in learnset:
                                learnset[move_name] = {'tm': False}

        # Get TM/HM moves
        tm_section = soup.find('span', id=re.compile(r'By_TM|By_Technical_Machine'))
        if tm_section:
            heading = tm_section.find_parent(['h2', 'h3', 'h4'])
            if heading:
                # Find the next table after this heading
                moves_table = heading.find_next('table', class_='roundy')
                if moves_table:
                    rows = moves_table.find_all('tr')
                    for row in rows:
                        # Look for move name links
                        move_link = row.find('a', href=re.compile(r'/wiki/.*\(move\)'))
                        if move_link:
                            move_name = move_link.get_text(strip=True)
                            if move_name:
                                # If already in learnset, mark it as also available via TM
                                if move_name in learnset:
                                    learnset[move_name]['tm'] = True
                                else:
                                    learnset[move_name] = {'tm': True}

        # Convert to list format with move name and TM flag
        if learnset:
            details['learnset'] = [
                {'name': move, 'tm': info['tm']}
                for move, info in learnset.items()
            ]

        return details

    def download_image(self, image_url: str, pokemon_name: str, pokemon_dir: str) -> bool:
        """
        Download Pokemon image

        Args:
            image_url: URL of the image
            pokemon_name: Name of the Pokemon
            pokemon_dir: Directory to save the image in

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(image_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Determine file extension
            ext = '.png'
            if '.jpg' in image_url or '.jpeg' in image_url:
                ext = '.jpg'

            filename = f"image{ext}"
            filepath = os.path.join(pokemon_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"  Downloaded image: {filename}")
            return True

        except requests.RequestException as e:
            print(f"  Error downloading image: {e}")
            return False

    def save_pokemon_details(self, pokemon_name: str, pokemon_number: int, details: Dict, pokemon_dir: str) -> None:
        """
        Save Pokemon details to a JSON file

        Args:
            pokemon_name: Name of the Pokemon
            pokemon_number: Pokedex number
            details: Dictionary of Pokemon details
            pokemon_dir: Directory to save the details file in
        """
        # Create details file
        details_path = os.path.join(pokemon_dir, 'details.json')

        # Build the complete data structure, excluding image_url
        details_copy = {k: v for k, v in details.items() if k != 'image_url'}
        pokemon_data = {
            'name': pokemon_name,
            'pokedex_number': pokemon_number,
            **details_copy  # Merge all the scraped details (without image_url)
        }

        # Write as JSON
        with open(details_path, 'w', encoding='utf-8') as f:
            json.dump(pokemon_data, f, indent=2, ensure_ascii=False)

        print(f"  Saved details to: {pokemon_name}/details.json")

    def scrape_generation(self) -> None:
        """
        Main method to scrape all Pokemon from the specified generation
        """
        print(f"Starting scrape for Generation {self.generation}...")
        print(f"Output directory: {self.gen_dir}\n")

        # Get list of Pokemon
        print("Fetching Pokemon list...")
        pokemon_list = self.get_pokemon_list()


        if not pokemon_list:
            print("No Pokemon found or error occurred.")
            return

        print(f"Found {len(pokemon_list)} Pokemon in Generation {self.generation}\n")

        # Log the Pokemon list
        print("Pokemon List:")
        for pokemon in pokemon_list:
            print(f"  #{pokemon['number']:03d} - {pokemon['name']}")
        print()

        # Scrape each Pokemon
        for i, pokemon in enumerate(pokemon_list, 1):
            name = pokemon['name']
            number = pokemon['number']
            url = pokemon['url']

            print(f"[{i}/{len(pokemon_list)}] Scraping {name} (#{number:03d})...")

            # Debug mode: only process first Pokemon
            if self.debug_mode and i > 1:
                print("\nDebug mode: Stopping after first Pokemon")
                break

            # Get detailed information
            details = self.scrape_pokemon_details(url)

            if details:
                # Create Pokemon-specific directory
                pokemon_dir = os.path.join(self.gen_dir, name)
                os.makedirs(pokemon_dir, exist_ok=True)

                # Save details
                self.save_pokemon_details(name, number, details, pokemon_dir)

                # Download image from table_image_url if available, else fallback to details['image_url']
                image_url = pokemon.get('table_image_url') or details.get('image_url')
                if image_url:
                    self.download_image(image_url, name, pokemon_dir)
                else:
                    print(f"  No image found for {name}")
            else:
                print(f"  Failed to scrape details for {name}")

            # Be polite - add a small delay between requests
            time.sleep(1)

        print(f"\nScraping complete! Data saved to: {self.gen_dir}")


def main():
    """Example usage"""
    # Scrape Generation 1
    # Set debug_mode=True to only process one Pokemon for testing
    scraper = BulbapediaScraper(generation=1, debug_mode=False)
    scraper.scrape_generation()


if __name__ == "__main__":
    main()