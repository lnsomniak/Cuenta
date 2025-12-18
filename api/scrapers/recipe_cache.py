import os
import json
import hashlib
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
SPOONACULAR_BASE = "https://api.spoonacular.com"

get_client: Optional[Callable] = None   # Type hint for Pylance
try:
    from supabase_client import get_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# NOTE: this is my workaround to a tough spoonacular api. 
# This wraps the spoonacular API with aggressive SUPABASE caching, therefore it should never hit spoonacular twice for the same query.
# It has its limitations yes, but it's a working effort. It's one of my favorite features so far LOLLLLLLLLLLLLLLLLLLLLLLLLLLL

# =============================================================================
# CACHE HELPERS
# =============================================================================
# first things first, creating a determinsttic cache key for the paramaters, sorting the paramaters for consistency
def _make_cache_key(cache_type: str, params: Dict[str, Any]) -> str:
    sorted_params = json.dumps(params, sort_keys=True)
    hash_input = f"{cache_type}:{sorted_params}"
    return hashlib.md5(hash_input.encode()).hexdigest()

# second things second, checking if it already exists
def _get_cached(cache_key: str) -> Optional[List[Dict[str, Any]]]:
    if not HAS_SUPABASE or get_client is None:
        return None
    
    try:
        client = get_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        result = client.table("recipe_cache").select("recipes, cached_at, hit_count").eq("cache_key", cache_key).gt("expires_at", now_iso).execute()
        
        if result.data:
            row: Dict[str, Any] = result.data[0]
            # Increment hit count (fire and forget)
            current_hits = int(row.get("hit_count", 0) or 0)
            client.table("recipe_cache").update({"hit_count": current_hits + 1}).eq("cache_key", cache_key).execute()
            recipes = row.get("recipes")
            if isinstance(recipes, list):
                return recipes
            return None
    except Exception as e:
        print(f"Cache read error: {e}")
    
    return None
# response is then saved to cache through this function, saving all the important things 
def _set_cached(cache_key: str, cache_type: str, recipes: List[Dict[str, Any]], ttl_days: int = 7) -> None:
    if not HAS_SUPABASE or get_client is None: # !!!!!!!!!!!
        return
    
    try:
        client = get_client()
        now = datetime.now(timezone.utc)
        client.table("recipe_cache").upsert({
            "cache_key": cache_key,
            "cache_type": cache_type,
            "recipes": recipes,
            "recipe_count": len(recipes),
            "cached_at": now.isoformat(),
            "expires_at": (now + timedelta(days=ttl_days)).isoformat(),
            "hit_count": 0,
        }, on_conflict="cache_key").execute()
    except Exception as e:
        print(f"Cache write error: {e}")


# =============================================================================
# SPOONACULAR API (with caching)
# =============================================================================

# the real genius behind it, this should solve my major issue. 
# cached aggressively, same ingredients = same response.
#  returns: List of recipe objects with id, title, image, usedIngredients, missedIngredients
def search_by_ingredients(
    ingredients: List[str],
    number: int = 10,
    ranking: int = 1,  # 1 = maximize used ingredients, 2 = minimize missing
    ignore_pantry: bool = True,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "ingredients": ",".join(sorted(ingredients)),
        "number": number,
        "ranking": ranking,
    }
    
    cache_key = _make_cache_key("ingredients", params)
    # Check cache first
    cached = _get_cached(cache_key)
    if cached:
        print(f"  [cache hit] {len(cached)} recipes for {ingredients[:3]}...")
        return cached
    
    # Call Spoonacular
    if not SPOONACULAR_API_KEY:
        print(" [no API key] Check if Spoon is configured smart guy ") # LOLLL this doesn't have to be here
        return []
    
    try:
        response = requests.get(
            f"{SPOONACULAR_BASE}/recipes/findByIngredients",
            params={
                "apiKey": SPOONACULAR_API_KEY,
                "ingredients": params["ingredients"],
                "number": number,
                "ranking": ranking,
                "ignorePantry": ignore_pantry,
            },
            timeout=10 # real boy mom
        )
        response.raise_for_status()
        recipes: List[Dict[str, Any]] = response.json() # pylance fix
        
        # Cache the response
        _set_cached(cache_key, "ingredients", recipes)
        print(f"  [API call] {len(recipes)} recipes cached")
        
        return recipes
        
    except Exception as e:
        print(f"  [API error] {e}")
        return []

def search_recipes(
    query: str,
    diet: Optional[str] = None,
    max_calories: Optional[int] = None,
    min_protein: Optional[int] = None,
    number: int = 10,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "query": query.lower().strip(),
        "diet": diet,
        "maxCalories": max_calories,
        "minProtein": min_protein,
        "number": number,
    }
    params = {k: v for k, v in params.items() if v is not None}
    cache_key = _make_cache_key("search", params)
    
    cached = _get_cached(cache_key)
    if cached is not None:
        print(f"  [cache hit] {len(cached)} recipes for '{query}'")
        return cached
    
    if not SPOONACULAR_API_KEY:
        return []
    
    try:
        api_params: Dict[str, Any] = {
            "apiKey": SPOONACULAR_API_KEY,
            "query": query,
            "number": number,
            "addRecipeNutrition": True,
        }
        if diet:
            api_params["diet"] = diet
        if max_calories:
            api_params["maxCalories"] = max_calories
        if min_protein:
            api_params["minProtein"] = min_protein
        
        response = requests.get(
            f"{SPOONACULAR_BASE}/recipes/complexSearch",
            params=api_params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        recipes: List[Dict[str, Any]] = data.get("results", [])
        
        # Cache
        _set_cached(cache_key, "search", recipes)
        print(f"  [API call] {len(recipes)} recipes cached")
        
        return recipes
        
    except Exception as e:
        print(f"  [API error] {e}")
        return []

# Gets the full recipe details including instructions and nutrition
def get_recipe_details(recipe_id: int) -> Optional[Dict[str, Any]]:
    params: Dict[str, Any] = {"id": recipe_id}
    cache_key = _make_cache_key("id", params)
    
    cached = _get_cached(cache_key)
    if cached is not None and len(cached) > 0:
        return cached[0] 
    
    if not SPOONACULAR_API_KEY:
        return None
    
    try:
        response = requests.get(
            f"{SPOONACULAR_BASE}/recipes/{recipe_id}/information",
            params={
                "apiKey": SPOONACULAR_API_KEY,
                "includeNutrition": True,
            },
            timeout=10 # REAL. boy. mom. 
        )
        response.raise_for_status()
        recipe = response.json()
        
        # Cache as a list (consistent with other cache entries)
        _set_cached(cache_key, "id", [recipe])
        
        return recipe
        
    except Exception as e:
        print(f"  [API error] {e}")
        return None

# =============================================================================
# PREFERENCE-AWARE RECIPES
# =============================================================================
#     If user_id provided, fetches their preferences from Supabase 
def get_recipes_for_user(
    ingredients: List[str],
    user_id: Optional[str] = None,
    number: int = 10,
) -> List[Dict[str, Any]]:
    recipes = search_by_ingredients(ingredients, number=number * 2)  # fetches more to filter
    
    if not user_id or not HAS_SUPABASE or get_client is None: # get_client seems random here and it defintely is
        return recipes[:number] 
    
    try:
        client = get_client()
        
        # Get avoided ingredients (rating <= 3 for preference, might tweak this depending on how tests go. saved in my notion
        prefs = client.table("ingredient_preferences").select("ingredient").eq("user_id", user_id).lte("rating", 3).execute()
        
        avoided: set[str] = { # fixed annoying sonarqube issue 
            str(p.get("ingredient", "")).lower() 
            for p in prefs.data 
            if isinstance(p, dict) and p.get("ingredient")
        }
        
        if not avoided:
            return recipes[:number]
        
        # Filter recipes
        filtered: List[Dict[str, Any]] = []
        for recipe in recipes:
            # Check used + missed ingredients
            recipe_ingredients: set[str] = set() # am I overcomplicating it? yes
            for ing in recipe.get("usedIngredients", []):
                recipe_ingredients.add(ing.get("name", "").lower())
            for ing in recipe.get("missedIngredients", []):
                recipe_ingredients.add(ing.get("name", "").lower())
            
            # Skip if contains avoided ingredient
            if not recipe_ingredients.intersection(avoided):
                filtered.append(recipe)
        
        return filtered[:number]
        
    except Exception as e:
        print(f"Preference filter error: {e}")
        return recipes[:number]

# =============================================================================
# CACHE STATS
# =============================================================================

def get_cache_stats() -> Dict[str, Any]:
    if not HAS_SUPABASE or get_client is None:
        return {"error": "Supabase not configured smart guy"}
    
    try:
        client = get_client()
        total = client.table("recipe_cache").select("id", count="exact").execute() # total entries
        hits = client.table("recipe_cache").select("hit_count").execute() # total hits
        total_hits = sum(r["hit_count"] for r in hits.data)
        by_type = client.table("recipe_cache").select("cache_type, id").execute() # By type 

        type_counts = {}
        for r in by_type.data:
            t = r["cache_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_entries": total.count,
            "total_hits": total_hits,
            "by_type": type_counts,
        }
        
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    
    # Testing ingredient search
    recipes = search_by_ingredients(["chicken", "rice"], number=3)
    for r in recipes:
        print(f"   - {r.get('title')}")
    
    # Test again (should hit cache)
    print("\n2. Same search (should be cached, double check):")
    recipes = search_by_ingredients(["chicken", "rice"], number=3)
    for r in recipes:
        print(f"   - {r.get('title')}")
    
    # Cache stats
    print("\n3. Cache stats:")
    stats = get_cache_stats()
    print(f"   {stats}")