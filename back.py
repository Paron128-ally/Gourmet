import json
import os
import random

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
CACHE_PATH = os.path.join(BASE_DIR, "recipes_cache.json")

app = Flask(__name__, static_folder=None, template_folder=BASE_DIR)


_RAW_RECIPES = []
_RECIPES_BY_ID = {}

RECIPE_PHOTOS_DIR = os.path.join(ICONS_DIR, "recipe-photos")
_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _load_recipe_images():
    if not os.path.isdir(RECIPE_PHOTOS_DIR):
        return ["/icons/ingredients.jpg"]
    files = sorted(
        f for f in os.listdir(RECIPE_PHOTOS_DIR)
        if f.lower().endswith(_IMAGE_EXTENSIONS)
    )
    if not files:
        return ["/icons/ingredients.jpg"]
    return [f"/icons/recipe-photos/{f}" for f in files]


_RECIPE_IMAGES = _load_recipe_images()


def load_cache():
    global _RAW_RECIPES, _RECIPES_BY_ID
    if not os.path.exists(CACHE_PATH):
        print(
            f"WARNING: {CACHE_PATH} not found. Run `python fetch_recipes.py` "
            "first to populate the local recipe cache."
        )
        _RAW_RECIPES = []
        _RECIPES_BY_ID = {}
        return

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        _RAW_RECIPES = json.load(f)
    random.shuffle(_RAW_RECIPES)  
    _RECIPES_BY_ID = {item["id"]: item for item in _RAW_RECIPES}
    print(f"Loaded {len(_RAW_RECIPES)} recipes from cache.")


def _normalize_recipe(item):
    """Convert a recipeapi.io recipe object into the shape app.js already expects."""
    ingredients = item.get("ingredients") or []
    normalized_ingredients = []
    for ing in ingredients:
        if isinstance(ing, dict):
            quantity = ing.get("quantity")
            unit = ing.get("unit")
            name = ing.get("name", "")
            parts = [str(p) for p in (quantity, unit, name) if p not in (None, "")]
            normalized_ingredients.append({"original": " ".join(parts)})
        else:
            normalized_ingredients.append({"original": str(ing)})

    instructions = item.get("instructions") or []

    return {
        "id": item.get("id"),
        "title": item.get("name", "Untitled Recipe"),
        "image": random.choice(_RECIPE_IMAGES),  
        "readyInMinutes": (item.get("prep_time") or 0) + (item.get("cook_time") or 0),
        "servings": item.get("servings"),
        "dishTypes": [item.get("difficulty")] if item.get("difficulty") else [],
        "cuisines": [item.get("cuisine")] if item.get("cuisine") else [],
        "summary": item.get("description", ""),
        "extendedIngredients": normalized_ingredients,
        "analyzedInstructions": [
            {"steps": [{"step": step} for step in instructions]}
        ],
        "spoonacularScore": None,
    }


def _recipe_matches(item, query=None, cuisine=None):
    if query:
        q = query.lower()
        haystacks = [
            item.get("name", ""),
            item.get("description", ""),
            item.get("cuisine", ""),
            " ".join(ing.get("name", "") for ing in (item.get("ingredients") or []) if isinstance(ing, dict)),
        ]
        if not any(q in h.lower() for h in haystacks):
            return False

    if cuisine and cuisine.lower() != "all":
        if (item.get("cuisine") or "").lower() != cuisine.lower():
            return False

    return True


def query_recipes(query=None, cuisine=None, limit=None, offset=0):
    """Filter/paginate the in-memory cache, normalized for the frontend."""
    filtered = [item for item in _RAW_RECIPES if _recipe_matches(item, query=query, cuisine=cuisine)]
    if offset:
        filtered = filtered[offset:]
    if limit:
        filtered = filtered[:limit]
    return [_normalize_recipe(item) for item in filtered]


def get_recipe_detail(recipe_id):
    item = _RECIPES_BY_ID.get(recipe_id)
    return _normalize_recipe(item) if item else None


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
@app.route("/index.html")
def index_html():
    return render_template("index.html")


@app.route("/icons/<path:filename>")
def icons(filename):
    return send_from_directory(ICONS_DIR, filename)


@app.route("/<path:filename>")
def public_file(filename):
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(file_path):
        return send_from_directory(BASE_DIR, filename)
    return redirect("/", code=302)


@app.route("/api/recipes")
def api_recipes():
    query = request.args.get("query")
    cuisine = request.args.get("cuisine")
    limit = request.args.get("limit", type=int, default=10)
    offset = request.args.get("offset", type=int, default=0)

    recipes = query_recipes(query=query, cuisine=cuisine, limit=limit, offset=offset)
    return jsonify({"recipes": recipes, "count": len(recipes), "total_cached": len(_RAW_RECIPES)})


@app.route("/api/recipes/<int:recipe_id>")
def api_recipe_detail(recipe_id):
    recipe = get_recipe_detail(recipe_id)
    if recipe is None:
        return jsonify({"error": "Recipe not found."}), 404
    return jsonify(recipe)


@app.route("/api/featured")
def api_featured():
    recipes = query_recipes(limit=6)
    return jsonify({"recipes": recipes})


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "cached_recipes": len(_RAW_RECIPES)})


load_cache()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5500"))
    print(f"Starting Recipe app on http://127.0.0.1:{port}/")
    app.run(debug=True, port=port)