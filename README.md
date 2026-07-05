
# Gourmet — Recipe Finder

A Flask + vanilla JS web app for browsing recipes by cuisine, searching by ingredient or name, viewing full recipe details, and saving favorites.

## Features

- Browse a home page of featured recipes
- Search recipes by name, ingredient, or cuisine
- Filter by cuisine
- View full recipe details: ingredients, instructions, prep/cook time, servings
- Save recipes to favorites (stored in the browser via `localStorage`)
- Recipes are served from a local JSON cache, so the app runs fast and doesn't burn API quota on every page load

## Project structure

```
.
├── back.py              # Flask app — serves pages + /api endpoints from the local cache
├── fetch_recipes.py      # One-off script to pull recipes from the API into recipes_cache.json
├── index.html            # Main page
├── app.js                # Frontend logic (search, filters, favorites, rendering)
├── styles.css             # Styling
├── icons/                # Icons and recipe photos
├── recipes_cache.json     # Local cache of fetched recipes (generated, not committed)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

1. **Clone the repo and enter the folder:**
   ```bash
   git clone <your-repo-url>
   cd Recipe_111
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and add your key:
   ```
   RECIPE_API_KEY=your_key_here
   ```

4. **Fetch recipes into the local cache** (only needed once, or whenever you want fresh data):
   ```bash
   python fetch_recipes.py
   ```
   This saves results to `recipes_cache.json`, which the app reads from at runtime instead of calling the API on every request. You can customize how many recipes to pull:
   ```bash
   python fetch_recipes.py --target 500
   ```

5. **Run the app:**
   ```bash
   python back.py
   ```

6. Open **http://127.0.0.1:5500** in your browser.

## API endpoints

| Route | Description |
|---|---|
| `GET /api/recipes` | List recipes. Supports `query`, `cuisine`, `limit`, `offset` params |
| `GET /api/recipes/<id>` | Get full detail for a single recipe |
| `GET /api/featured` | Get a small set of featured recipes |
| `GET /api/health` | Health check — returns cache size and status |

## Tech

- **Backend:** Flask, serving recipes from a locally cached JSON file
- **Frontend:** Vanilla JavaScript, HTML, CSS
- **Data:** Fetched once via `fetch_recipes.py` and normalized into a consistent shape for the frontend
