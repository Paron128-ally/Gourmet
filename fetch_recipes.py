"""
One-time (or occasional) script to pull recipes from recipeapi.io and save
them to a local JSON file, so the Flask app can serve many recipes as cards
without burning your monthly API request quota on every page load.

Usage:
    python fetch_recipes.py                  # fetch default target (1000 recipes)
    python fetch_recipes.py --target 500     # fetch a custom number
    python fetch_recipes.py --per-page 10    # override page size (plan-dependent)

Run this whenever you want to refresh the local cache. Each run costs
roughly (target / per_page) API requests against your monthly quota.
"""

import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://recipeapi.io/api/v1"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "recipes_cache.json")


def get_api_key():
    api_key = os.environ.get("RECIPE_API_KEY")
    if not api_key:
        sys.exit(
            "RECIPE_API_KEY is not set. Create a .env file in this folder "
            "with a line like: RECIPE_API_KEY=sk_live_your_key_here"
        )
    return api_key


def fetch_all(target, per_page):
    headers = {"Authorization": f"Bearer {get_api_key()}"}
    all_recipes = []
    page = 1
    requests_made = 0

    while len(all_recipes) < target:
        params = {"per_page": per_page, "page": page}
        response = requests.get(f"{BASE_URL}/recipes", params=params, headers=headers, timeout=10)
        requests_made += 1

        if response.status_code != 200:
            print(f"Stopped early: got HTTP {response.status_code} on page {page}.")
            print(response.text[:300])
            break

        body = response.json()
        items = body.get("data", [])
        if not items:
            print(f"No more recipes returned at page {page}. Stopping.")
            break

        all_recipes.extend(items)
        meta = body.get("meta", {})
        last_page = meta.get("last_page")
        print(f"Fetched page {page} ({len(items)} recipes) — total so far: {len(all_recipes)}")

        if last_page and page >= last_page:
            print("Reached the last available page.")
            break

        page += 1
        time.sleep(0.2) 

    print(f"\nDone. Fetched {len(all_recipes)} recipes using {requests_made} API requests.")
    return all_recipes[:target]


def main():
    parser = argparse.ArgumentParser(description="Fetch and cache recipes from recipeapi.io")
    parser.add_argument("--target", type=int, default=1000, help="How many recipes to fetch (default: 1000)")
    parser.add_argument("--per-page", type=int, default=10, help="Results per page (default: 10, free plan max)")
    args = parser.parse_args()

    recipes = fetch_all(target=args.target, per_page=args.per_page)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(recipes)} recipes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
