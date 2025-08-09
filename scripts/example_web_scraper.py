#!/usr/bin/env python3
"""
Example web scraper simulation
Demonstrates a script that might run for a while and occasionally fail
"""

import time
import random


def scrape_website(url, pages=5):
    """Simulate scraping a website"""
    print(f"Starting to scrape: {url}")

    for page in range(1, pages + 1):
        print(f"Scraping page {page}/{pages}...")

        # Simulate network delay
        delay = random.uniform(2, 5)
        time.sleep(delay)

        # Simulate finding data
        items_found = random.randint(5, 20)
        print(f"   Found {items_found} items on page {page}")

        # Simulate occasional connection issues
        if random.random() < 0.15:  # 15% chance of issue
            print("Connection timeout, retrying...")
            time.sleep(3)
            print("Retry successful")

    print(f"Successfully scraped {url}")


def main():
    print("Starting web scraper...")

    websites = ["example.com", "demo-site.org", "test-data.net"]

    for i, site in enumerate(websites, 1):
        print(f"\nTarget {i}/{len(websites)}: {site}")
        scrape_website(site)

        if i < len(websites):
            wait_time = random.randint(3, 8)
            print(f"Waiting {wait_time} seconds before next site...")
            time.sleep(wait_time)

    print("\nWeb scraping completed!")
    print(f"Successfully processed {len(websites)} websites")


if __name__ == "__main__":
    main()
