import os
import re
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
import requests
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

USDA_API_KEY = os.getenv("USDA_API_KEY") 
USDA_BASE = "https://api.nal.usda.gov/fdc/v1"
# these constraints are a fix that will never get noticed, but in the moment I will say I am proud of myself for it 
# Constants
DEFAULT_SERVING = "1 serving"
COOKED_SERVING = "4 oz cooked (112g)"

# In-memory cache (session only)
_memory_cache: Dict[str, Any] = {}

# Supabase for persistent cache
get_client: Optional[Callable] = None # Type hint for Pylance
try:
    from supabase_client import get_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NutritionData:
    calories: int = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0
    fiber: float = 0
    sodium: float = 0
    serving_size: str = DEFAULT_SERVING
    serving_grams: float = 100
    source: str = "usda"
    fdc_id: Optional[int] = None


# =============================================================================
# SUPABASE NUTRITION CACHE
# =============================================================================
# cleaning up the data, aka removing anything that'll confuse my supabase cache
def _normalize_key(name: str) -> str:
    key = re.sub(r'[®™©]', '', name)
    key = re.sub(r'\s+', ' ', key).strip().lower()
    key = re.sub(r'\d+\s*(oz|lb|g|ml|ct|count|pack)\b', '', key) # common size indicators
    key = re.sub(r'\s+', ' ', key).strip()
    return key
# checking my cache for a product
def _get_cached_nutrition(name: str, upc: Optional[str] = None) -> Optional[NutritionData]:
    if not HAS_SUPABASE or get_client is None:
        return None
    
    try:
        client = get_client()
# first, upc, then normalize namem, and if then return some nutritional data
        if upc:
            result = client.table("nutrition_cache").select("*").eq("upc", upc).execute()
            if result.data:
                row: Dict[str, Any] = result.data[0]
                return NutritionData(
                    calories=int(row.get("calories", 0) or 0),
                    protein=float(row.get("protein", 0) or 0),
                    fat=float(row.get("fat", 0) or 0),
                    carbs=float(row.get("carbs", 0) or 0),
                    fiber=float(row.get("fiber", 0) or 0),
                    sodium=float(row.get("sodium", 0) or 0),
                    serving_size=str(row.get("serving_size", DEFAULT_SERVING) or DEFAULT_SERVING),
                    source="cache",
                    fdc_id=int(row["fdc_id"]) if row.get("fdc_id") else None,
                )
        
        cache_key = _normalize_key(name)
        result = client.table("nutrition_cache").select("*").eq("cache_key", cache_key).execute()
        
        if result.data:
            row: Dict[str, Any] = result.data[0]
            return NutritionData(
                calories=int(row.get("calories", 0) or 0),
                protein=float(row.get("protein", 0) or 0),
                fat=float(row.get("fat", 0) or 0),
                carbs=float(row.get("carbs", 0) or 0),
                fiber=float(row.get("fiber", 0) or 0),
                sodium=float(row.get("sodium", 0) or 0),
                serving_size=str(row.get("serving_size", DEFAULT_SERVING) or DEFAULT_SERVING),
                source="cache",
                fdc_id=int(row["fdc_id"]) if row.get("fdc_id") else None,
            )
        
        return None
        
    except Exception as e:
        print(f"Cache read error: {e}")
        return None

# the "edge case" first being if doesn't have supabase, return and then if has then save, part of the fallback 
def _save_to_cache(name: str, nutrition: NutritionData, upc: Optional[str] = None) -> None:
    if not HAS_SUPABASE or get_client is None:
        return
    
    try:
        client = get_client()
        
        cache_key = _normalize_key(name)
        
        data = {
            "cache_key": cache_key,
            "product_name": name[:255], 
            "upc": upc,
            "calories": nutrition.calories,
            "protein": nutrition.protein,
            "fat": nutrition.fat,
            "carbs": nutrition.carbs,
            "fiber": nutrition.fiber,
            "sodium": nutrition.sodium,
            "serving_size": nutrition.serving_size,
            "fdc_id": nutrition.fdc_id,
            "source": nutrition.source,
        }
        
        client.table("nutrition_cache").upsert(data, on_conflict="cache_key").execute()
        
    except Exception as e:
        print(f"Cache write error: {e}")

# =============================================================================
# USDA API
# =============================================================================
# simple function to search usda
def search_usda(query: str, limit: int = 5, branded: bool = True) -> List[Dict[str, Any]]:
    query = re.sub(r'[®™©]', '', query)  # stripping it of the trademark stuff
    query = re.sub(r'\s+', ' ', query).strip()
    
    cache_key = f"{query}:{limit}:{branded}" # after, check the cache
    if cache_key in _memory_cache:
        return _memory_cache[cache_key]
    
    params: Dict[str, Any] = {
        "api_key": USDA_API_KEY,
        "query": query,
        "pageSize": limit,
    }
    
    if branded:
        params["dataType"] = ["Branded", "SR Legacy"]
    else: # good to know stuff 
        params["dataType"] = ["SR Legacy", "Foundation"] 
    
    try:
        response = requests.get(
            f"{USDA_BASE}/foods/search",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        results: List[Dict[str, Any]] = data.get("foods", [])
        _memory_cache[cache_key] = results
        return results
        
    except Exception as e:
        print(f"USDA search error: {e}")
        return []
# self explanatory
def get_food_details(fdc_id: int) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(
            f"{USDA_BASE}/food/{fdc_id}",
            params={"api_key": USDA_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"USDA detail error: {e}")
        return None

# =============================================================================
# PARSING
# =============================================================================
# extract the nutrition data from the cleaned and stripped data
def parse_nutrients(food_data: Dict[str, Any]) -> NutritionData:
    nutrition = NutritionData()
    nutrition.fdc_id = food_data.get("fdcId")
    nutrition.source = "usda"
    nutrients = food_data.get("foodNutrients", [])
    
    for n in nutrients:
        # Handle both search results and detail responses
        if "nutrientName" in n:
            name = n.get("nutrientName", "").lower()
            amount = n.get("value", 0) or 0
        elif "nutrient" in n:
            name = n.get("nutrient", {}).get("name", "").lower()
            amount = n.get("amount", 0) or 0
        else:
            continue
        
        # Map nutrients to make them easier later
        if "energy" in name or "calorie" in name:
            if "kcal" in name or "energy" in name:
                nutrition.calories = int(amount)
        elif name == "protein":
            nutrition.protein = float(amount)
        elif "total lipid" in name or name == "fat":
            nutrition.fat = float(amount)
        elif "carbohydrate" in name:
            nutrition.carbs = float(amount)
        elif "fiber" in name:
            nutrition.fiber = float(amount)
        elif "sodium" in name:
            nutrition.sodium = float(amount)
    
    # Serving size
    serving = food_data.get("servingSize")
    serving_unit = food_data.get("servingSizeUnit", "g")
    if serving:
        nutrition.serving_size = f"{serving} {serving_unit}"
        nutrition.serving_grams = float(serving) if serving_unit == "g" else 100
    
    # Household serving like "1 cup" or "1 bar"
    household = food_data.get("householdServingFullText")
    if household:
        nutrition.serving_size = household
    
    return nutrition

# =============================================================================
# LOOKUP FEATURE
# =============================================================================
# look up the nutrition for an item, returns either nutritiondata or none if not found
def lookup_nutrition(
    query: str,
    upc: Optional[str] = None,
    prefer_branded: bool = True,
    use_cache: bool = True,
) -> Optional[NutritionData]:
    # 6. Check Supabase cache first
    if use_cache:
        cached = _get_cached_nutrition(query, upc)
        if cached:
            return cached
    
    # 7. Try UPC search in USDA
    if upc:
        results = search_usda(upc, limit=1, branded=True)
        if results:
            nutrition = parse_nutrients(results[0])
            if use_cache:
                _save_to_cache(query, nutrition, upc)
            return nutrition
    
    # 6. Search by name
    results = search_usda(query, limit=5, branded=prefer_branded)
    
    if not results:
        # Fallback to generic if no branded results
        results = search_usda(query, limit=5, branded=False)
    
    if not results:
        return None
    
    # 7. Score results by relevance
    query_lower = query.lower()
    best_match: Optional[Dict[str, Any]] = None
    best_score = -1
    
    for food in results:
        description = food.get("description", "").lower()
        brand = food.get("brandName", "").lower() if food.get("brandName") else ""
        
        score = 0
        
        # 6. Exact match bonus
        if query_lower in description:
            score += 10
        
        # 7. Brand match bonus
        query_words = query_lower.split()
        if brand and any(w in brand for w in query_words):
            score += 5
        
        # 6. Word overlap
        desc_words = set(description.split())
        overlap = len(set(query_words) & desc_words)
        score += overlap * 2
        
        # 7. Prefer items with more nutrients reported
        nutrient_count = len(food.get("foodNutrients", []))
        score += min(nutrient_count / 10, 3)
        
        if score > best_score:
            best_score = score
            best_match = food
    
    if best_match:
        nutrition = parse_nutrients(best_match)
        if use_cache:
            _save_to_cache(query, nutrition, upc)
        return nutrition
    
    return None


# =============================================================================
# PRODUCT ENRICHMENT
# =============================================================================

# the bulk of it all, 300 lines in but nonetheless. point is this now enriches the product with nutrition data from the cache OR usda if missing 
# true if enriched, false if not needed
def enrich_product(product, force: bool = False) -> bool:
    # Check if enrichment needed
    needs_enrichment = (
        force or
        getattr(product, 'calories', 0) == 0 or
        getattr(product, 'protein', 0) == 0
    )
    
    if not needs_enrichment:
        return False

    name = getattr(product, 'name', '')
    upc = getattr(product, 'upc', None)
    
    nutrition = lookup_nutrition_smart(name, upc)
    
    if not nutrition:
        return False
    
    # Apply nutrition as needed
    if hasattr(product, 'calories'):
        product.calories = nutrition.calories
    if hasattr(product, 'protein'):
        product.protein = nutrition.protein
    if hasattr(product, 'fat'):
        product.fat = nutrition.fat
    if hasattr(product, 'carbs'):
        product.carbs = nutrition.carbs
    if hasattr(product, 'fiber'):
        product.fiber = nutrition.fiber
    if hasattr(product, 'serving_size'):
        product.serving_size = nutrition.serving_size
    
    return True

def enrich_products_batch(products: list, delay: float = 0.1) -> dict:
    import time
    
    stats = {"enriched": 0, "failed": 0, "skipped": 0, "cached": 0}
    
    for product in products:
        needs = getattr(product, 'calories', 0) == 0 or getattr(product, 'protein', 0) == 0
        
        if not needs:
            stats["skipped"] += 1
            continue
        
        # Checks if this came from cache 
        name = getattr(product, 'name', '')
        upc = getattr(product, 'upc', None)
        was_cached = _get_cached_nutrition(name, upc) is not None
        
        if enrich_product(product):
            if was_cached:
                stats["cached"] += 1
            else:
                stats["enriched"] += 1
                time.sleep(delay)  # only rate limit API calls 
        else:
            stats["failed"] += 1
    
    return stats


# =============================================================================
# COMMON FOODS (instant lookup, no API needed)
# =============================================================================

COMMON_FOODS = {
    # Poultry (cooked)
    "chicken breast": NutritionData(calories=165, protein=31, fat=3.6, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "chicken thigh": NutritionData(calories=177, protein=28, fat=6.5, carbs=0, serving_size=COOKED_SERVING, source="common"),
    
    # Beef (cooked) - different lean ratios
    "ground beef 96/4": NutritionData(calories=155, protein=24, fat=6, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground beef 93/7": NutritionData(calories=170, protein=23, fat=8, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground beef 90/10": NutritionData(calories=200, protein=23, fat=11, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground beef 85/15": NutritionData(calories=240, protein=21, fat=17, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground beef 80/20": NutritionData(calories=287, protein=19, fat=23, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground beef": NutritionData(calories=240, protein=21, fat=17, carbs=0, serving_size=COOKED_SERVING, source="common"),  # Default to 85/15
    
    # Turkey (cooked) - different lean ratios
    "ground turkey 99/1": NutritionData(calories=120, protein=26, fat=1.5, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground turkey 93/7": NutritionData(calories=160, protein=22, fat=8, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground turkey 85/15": NutritionData(calories=210, protein=22, fat=14, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "ground turkey": NutritionData(calories=210, protein=22, fat=14, carbs=0, serving_size=COOKED_SERVING, source="common"),  # Default to 85/15
    
    # Fish (cooked)
    "salmon": NutritionData(calories=208, protein=20, fat=13, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "tilapia": NutritionData(calories=140, protein=23, fat=3, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "tuna": NutritionData(calories=132, protein=29, fat=1, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "cod": NutritionData(calories=119, protein=26, fat=1, carbs=0, serving_size=COOKED_SERVING, source="common"),
    "shrimp": NutritionData(calories=120, protein=23, fat=2, carbs=1, serving_size=COOKED_SERVING, source="common"),
    
    # Eggs & Dairy
    "large egg": NutritionData(calories=70, protein=6, fat=5, carbs=0, serving_size="1 egg (50g)", source="common"),
    "egg white": NutritionData(calories=17, protein=4, fat=0, carbs=0, serving_size="1 white (33g)", source="common"),
    "greek yogurt nonfat": NutritionData(calories=100, protein=17, fat=0, carbs=6, serving_size="1 cup (170g)", source="common"),
    "greek yogurt": NutritionData(calories=100, protein=17, fat=0, carbs=6, serving_size="1 cup (170g)", source="common"),
    "cottage cheese": NutritionData(calories=110, protein=12, fat=5, carbs=4, serving_size="1/2 cup (113g)", source="common"),
    
    # Plant protein
    "tofu firm": NutritionData(calories=144, protein=17, fat=8, carbs=3, serving_size="1/2 cup (126g)", source="common"),
    "tofu": NutritionData(calories=144, protein=17, fat=8, carbs=3, serving_size="1/2 cup (126g)", source="common"),
    "tempeh": NutritionData(calories=195, protein=20, fat=11, carbs=8, serving_size="1/2 cup (83g)", source="common"),
    "black beans": NutritionData(calories=114, protein=8, fat=0, carbs=20, fiber=7, serving_size="1/2 cup cooked (86g)", source="common"),
    "lentils": NutritionData(calories=115, protein=9, fat=0, carbs=20, fiber=8, serving_size="1/2 cup cooked (99g)", source="common"),
    
    # Packaged protein (typical values)
    "protein shake": NutritionData(calories=160, protein=30, fat=3, carbs=4, serving_size="1 bottle (11 oz)", source="common"),
    "protein bar": NutritionData(calories=200, protein=20, fat=7, carbs=22, serving_size="1 bar", source="common"),
}
# fix: prevents "eggplant" from matching "egg"
EXACT_MATCH_TERMS = {
    "egg", "eggs", "tofu", "tempeh", "salmon", "tuna", "cod", "shrimp", "tilapia"
}

# smart matching!!!!! checking common foods cache 
def lookup_common(name: str) -> Optional[NutritionData]:
    name_lower = name.lower()
    name_words = set(name_lower.split())
    
    # 6. Exact match first
    if name_lower in COMMON_FOODS:
        return COMMON_FOODS[name_lower]
    
    # 7. check for lean ratio patterns like "93% lean", "93/7", "96% lean"
    ratio_match = re.search(r'(\d{2})[/%]?\s*(?:lean|/\s*\d+)?', name_lower)
    if ratio_match:
        ratio = ratio_match.group(1)
        # Try to match with ratio
        for key in COMMON_FOODS:
            if ratio in key and any(base in name_lower for base in ['beef', 'turkey', 'chicken']):
                if ('beef' in name_lower and 'beef' in key) or \
                ('turkey' in name_lower and 'turkey' in key):
                    return COMMON_FOODS[key]
    
    # 6. Word boundary match for exact terms (prevents "eggplant" matching "egg")
    for term in EXACT_MATCH_TERMS:
        if term in name_words:
            # Find the matching key
            for key, nutrition in COMMON_FOODS.items():
                if key == term or key.startswith(term + " "):
                    return nutrition
    
    # 7. Longest key match (more specific = more better)
    best_match = None
    best_length = 0
    
    for key, nutrition in COMMON_FOODS.items():
        if key in EXACT_MATCH_TERMS:
            continue  # alerady done above!
        
        key_words = key.split()
        if len(key_words) > 1:
            # Multi-word key: all words must be present or else
            if all(w in name_lower for w in key_words):
                if len(key) > best_length:
                    best_match = nutrition
                    best_length = len(key)
        else:
            # Single word key: must be whole word
            if key in name_words and len(key) > best_length:
                best_match = nutrition
                best_length = len(key)
    
    return best_match


def lookup_nutrition_smart(
    query: str,
    upc: Optional[str] = None,
) -> Optional[NutritionData]: # try my hardcoded, then cache, then api ``
    common = lookup_common(query)
    if common:
        return common
    
    # 2 & 3. Cache then USDA (lookup_nutrition handles both)
    return lookup_nutrition(query, upc, use_cache=True)


# =============================================================================
# CACHE STATS
# =============================================================================

def get_cache_stats() -> Dict[str, Any]:
    if not HAS_SUPABASE or get_client is None:
        return {"error": "Supabase not configured", "common_foods": len(COMMON_FOODS)}
    
    try:
        client = get_client()
        
        result = client.table("nutrition_cache").select("source", count="exact").execute()
        
        by_source = {}
        for row in result.data:
            src = row.get("source", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
        
        return {
            "cached_products": len(result.data),
            "by_source": by_source,
            "common_foods": len(COMMON_FOODS),
        }
        
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("USDA NUTRITION FALLBACK TEST")
    print("=" * 60)
    
    print(f"\n Supabase cache: {'✓ Enabled' if HAS_SUPABASE else '✗ Disabled (in-memory only)'}")
    print(f"Common foods: {len(COMMON_FOODS)} items")
    
    test_items = [
        "Premier Protein Chocolate Shake",
        "Fage Greek Yogurt",
        "chicken breast",
        "CLIF Builder Bar",
        "Oscar Mayer Turkey",
    ]
    
    for item in test_items:
        print(f"\n Looking up: {item}")
        
        nutrition = lookup_nutrition_smart(item)
        
        if nutrition:
            print(f"   ✓ {nutrition.calories} cal | {nutrition.protein}g protein")
            print(f"     Fat: {nutrition.fat}g | Carbs: {nutrition.carbs}g")
            print(f"     Serving: {nutrition.serving_size}")
            print(f"     Source: {nutrition.source}")
        else:
            print(" ✗ Not found")
    
    # Show cache stats
    print("\n" + "=" * 60)
    print("CACHE STATS")
    print("=" * 60)
    stats = get_cache_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print("\n" + "=" * 60)
    print("Done!")