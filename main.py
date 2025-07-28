"""
D&D 5e Spell Scraper

A Python script for scraping spell information from dnd5e.wikidot.com and saving
the data as Markdown files. This script can scrape individual spells or batch
process multiple spells with rate limiting and error handling.

Date: 2025
License: MIT

Dependencies:
    - requests: For HTTP requests
    - beautifulsoup4: For HTML parsing
    - time: For rate limiting delays
    - os: For file system operations
    - typing: For type hints
    - re: For regular expressions

Usage:
    python spell_scraper.py

Example:
    >>> scraper = DnDSpellScraper(delay=1.5)
    >>> spells = scraper.scrape_spells(['fire-bolt', 'magic-missile'])
    >>> scraper.create_combined_file(spells)
"""

import requests
from bs4 import BeautifulSoup
import time
import os
from typing import List, Dict, Optional
import re

SPELL_SCHOOLS = [
    "Abjuration",
    "Conjuration",
    "Divination",
    "Enchantment",
    "Evocation",
    "Illusion",
    "Necromancy",
    "Transmutation",
]


class DnDSpellScraper:
    """
    A web scraper for D&D 5e spells from dnd5e.wikidot.com.

    This class provides functionality to scrape spell information from the
    D&D 5e wikidot website, including spell titles and content. It supports
    both individual spell scraping and batch processing with built-in rate
    limiting and error handling.

    Attributes:
        base_url (str): The base URL for the D&D wiki site
        delay (float): Delay in seconds between HTTP requests for rate limiting
        session (requests.Session): HTTP session for making requests

    Example:
        >>> scraper = DnDSpellScraper(delay=2.0)
        >>> spell = scraper.scrape_spell('fireball')
        >>> print(spell['title'])
        'Fireball'
    """

    def __init__(
        self, base_url: str = "https://dnd5e.wikidot.com", delay: float = 1.0
    ):
        """
        Initialize the spell scraper.

        Args:
            base_url: Base URL for the D&D wiki
            delay: Delay between requests in seconds (rate limiting)
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def scrape_spell(self, spell_name: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single spell from the website.

        Args:
            spell_name: Name of the spell (e.g., "fire-bolt")

        Returns:
            Dictionary with 'title' and 'content' keys, or None if failed
        """
        url = f"{self.base_url}/spell:{spell_name}"

        try:
            print(f"Scraping: {spell_name}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title_element = soup.find("div", class_="page-title page-header")
            if not title_element:
                print(f"Warning: Could not find title for {spell_name}")
                title = spell_name.replace("-", " ").title()
            else:
                title = title_element.get_text(strip=True)

            # Extract content
            content_element = soup.find("div", id="page-content")
            if not content_element:
                print(f"Error: Could not find content for {spell_name}")
                return None

            # Clean up the content
            content = self._clean_content(content_element)

            return {"title": title, "content": content, "url": url}

        except requests.RequestException as e:
            print(f"Error fetching {spell_name}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error processing {spell_name}: {e}")
            return None

    def _clean_content(self, content_element) -> str:
        """
        Clean and format the spell content for Markdown.

        Args:
            content_element: BeautifulSoup element containing spell content

        Returns:
            Cleaned content as string
        """
        # Remove script and style elements
        for script in content_element(["script", "style"]):
            script.decompose()

        # Get text and clean it up
        content = content_element.get_text()

        # Clean up whitespace
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(self._format(line))

        # Join lines and clean up extra spaces
        content = "".join(cleaned_lines)
        content = re.sub(
            r"\n{3,}", "\n\n", content
        )  # Remove excessive newlines

        return content

    def _format(self, line: str) -> str:
        """
        Format a line for Markdown.

        Args:
            line: Line to format
        Returns:
            Formatted line
        """
        if line.startswith("Source"):
            return f"**Source:** {line.split(':')[1].strip()}\n\n"
        if any([x.lower() in line.lower() for x in SPELL_SCHOOLS]):
            if "level" in line:
                type_line = f"**Type:** Spell"
                level_line = f"**Level:** {line.split(' ')[0].strip()}"
                school_line = (
                    f"**School:** {line.split(' ')[1].strip().capitalize()}"
                )
                return f"{type_line}\n{level_line}\n{school_line}\n\n"
            else:
                type_line = f"**Type:** Cantrip"
                school_line = (
                    f"**School:** {line.split()[0].strip().capitalize()}"
                )
                return f"{type_line}\n{school_line}\n\n"
        if line.startswith("Casting Time"):
            return f"**Casting Time:** {line.split(':')[1].strip()}\n"
        if line.startswith("Range"):
            return f"**Range:** {line.split(':')[1].strip()}\n"
        if line.startswith("Components"):
            return f"**Components:** {line.split(':')[1].strip()}\n"
        if line.startswith("Duration"):
            return f"**Duration:** {line.split(':')[1].strip()}\n\n"
        if "At Higher Levels" in line:
            return f"\n**At Higher Levels:** {line.split('At Higher Levels.')[1].strip()}\n"
        if "Spell Lists" in line:
            return (
                f"\n**Spell Lists:** {line.split('Spell Lists.')[1].strip()}\n"
            )
        return f"{line}\n\n"

    def scrape_spells(
        self, spell_names: List[str], output_dir: str = "scraped_spells"
    ) -> List[Dict[str, str]]:
        """
        Scrape multiple spells and save them as individual Markdown files.

        Args:
            spell_names: List of spell names to scrape
            output_dir: Directory to save the files

        Returns:
            List of successfully scraped spells
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        scraped_spells = []

        for i, spell_name in enumerate(spell_names):
            spell_data = self.scrape_spell(spell_name)

            if spell_data:
                # Save individual file
                filename = f"{spell_name}.md"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {spell_data['title']}\n\n")
                    f.write(f"**Source:** {spell_data['url']}\n\n")
                    f.write(spell_data["content"])

                scraped_spells.append(spell_data)
                print(f"Saved: {filename}")

            # Rate limiting - sleep between requests
            if i < len(spell_names) - 1:  # Don't sleep after the last request
                time.sleep(self.delay)

        return scraped_spells

    def create_combined_file(
        self,
        scraped_spells: List[Dict[str, str]],
        output_path: str = "all_spells.md",
    ):
        """
        Create a single Markdown file containing all scraped spells.

        Args:
            scraped_spells: List of spell dictionaries
            output_path: Path for the combined file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# D&D 5e Spells\n\n")
            f.write(
                "This file contains spells scraped from "
                "[dnd5e.wikidot.com]()\n"
            )

            for spell in scraped_spells:
                f.write(f"## {spell['title']}\n\n")
                f.write(f"**URL:** {spell['url']}\n\n")
                f.write(f"{spell['content']}\n\n")

        print(f"Combined file saved: {output_path}")


def main():
    """
    Example usage of the DnDSpellScraper.
    """
    # Example spell list
    spell_names = [
        "resistance",
        "thunderclap",
        "mending",
        "fire-bolt",
        "magic-stone",
        "ray-of-sickness",
        "healing-word",
        "entangle",
        "faerie-fire",
        "earth-tremor",
        "charm-person",
        "pass-without-trace",
        "enlarge-reduce",
        "healing-spirit",
        "conjure-animals",
        "call-lightning",
        "divination",
        "blight"
    ]

    # Initialize scraper with 1.5 second delay between requests
    scraper = DnDSpellScraper(delay=1.5)

    print("Starting spell scraping...")
    print(f"Scraping {len(spell_names)} spells...")

    # Scrape spells and save individual files
    scraped_spells = scraper.scrape_spells(spell_names)

    # Create combined file
    if scraped_spells:
        scraper.create_combined_file(scraped_spells)
        print(
            f"\nSuccessfully scraped {len(scraped_spells)} out of {len(spell_names)} spells"
        )
    else:
        print("No spells were successfully scraped")


if __name__ == "__main__":
    main()
