import argparse
import time
import warnings
import re
import uuid
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Set, Any
from dataclasses import dataclass

warnings.filterwarnings('ignore', message='.*OpenSSL.*')
warnings.filterwarnings('ignore', category=DeprecationWarning)

import requests
import urllib3
urllib3.disable_warnings()
# supabase
try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    import os
    load_dotenv()
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# =============================================================================
# CONFIGURATION
# =============================================================================

# High-protein search queries by category
SEARCH_QUERIES: Dict[str, List[str]] = {
    "meat": ["chicken breast", "ground beef", "ground turkey", "steak", "pork chop", "turkey breast"],
    "seafood": ["salmon", "tuna", "tilapia", "shrimp", "cod"],
    "dairy": ["greek yogurt", "cottage cheese", "string cheese", "milk protein"],
    "eggs": ["eggs", "egg whites", "liquid eggs"],
    "protein": ["protein shake", "protein bar", "protein powder", "premier protein"],
    "plant": ["tofu", "tempeh", "edamame", "lentils", "black beans", "chickpeas"],
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.target.com/',
}

session = requests.Session()
session.headers.update(HEADERS)

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CuentaProduct:
    name: str
    price: float
    calories: int
    protein: float
    serving_size: str
    servings: float
    category: str
    tags: Set[str]
    tcin: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    fat: float = 0
    carbs: float = 0
    fiber: float = 0

# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

_api_key_cache: Optional[str] = None

# =============================================================================
# API KEY MANAGEMENT (FIXED)
# =============================================================================

def get_api_key() -> str:
    global _api_key_cache
    if _api_key_cache and len(_api_key_cache) == 40:
            return _api_key_cache
        
    fallback_key = '9f36aeafbe60771e321a7cc95a78140772ab3e96'
    
    try:
        # We hit the main page to find the embedded configuration
        response = requests.get(
            'https://www.target.com/',
            headers=HEADERS,
            timeout=10
        )
        
        # Target's Redsky key is exactly 40 characters of hex (0-9, a-f)
        # I'll look for it specifically inside the "apiKey" field
        match = re.search(r'"apiKey":"([a-f0-9]{40})"', response.text)
        if match:
            _api_key_cache = match.group(1)
            return _api_key_cache
            
    except Exception as e:
        print(f"   Warning: Key fetch failed: {e}")
    
    return fallback_key

# =============================================================================
# TARGET API FUNCTIONS (FIXED PARSING)
# =============================================================================

def get_stores_near_zip(zip_code: str, limit: int = 5) -> List[dict]:
    # 1. HARD-CODED BYPASS FOR YOUR SPECIFIC AREA
    if zip_code == "77021":
        print(f"   Bypassing API: Using known Store ID 1336 for Houston.")
        # We must nest 'location_id' inside 'location' to match your script's parser
        return [{
            'location': {
                'location_id': '1336', 
                'location_name': 'Hermann Park (Houston)'
            }
        }]

    # 2. DYNAMIC LOOKUP (If zip is different)
    api_key = get_api_key()
    url = "https://redsky.target.com/redsky_aggregations/v1/web/nearby_stores_v1"
    params = {
        'key': api_key,
        'place': zip_code,
        'limit': limit,
        'visitor_id': str(uuid.uuid4()).replace('-', '')
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', {}).get('nearby_stores', {}).get('stores', [])
        print(f"   Store API Error: {response.status_code}")
    except Exception as e:
        print(f"   Connection Error: {e}")
    
    # Fallback to 1336 if everything fails
    return [{'location': {'location_id': '1336'}}]

SESSION_VISITOR_ID = str(uuid.uuid4()).replace('-', '').upper()[:32]

def search_products(query: str, store_id: str, count: int = 24):
    api_key = get_api_key()
    
    # Target expects the Referer to match the search page
    search_url = f"https://www.target.com/s?searchTerm={query}"
    
    params = {
        'key': api_key,
        'channel': 'WEB',
        'count': count,
        'keyword': query,
        'pricing_store_id': store_id,
        'visitor_id': SESSION_VISITOR_ID,
        'is_bot': 'false',
        'platform': 'desktop',
        'page': f'/s?searchTerm={query}'
    }

    # Spoof the referer for this specific search
    local_headers = {'Referer': search_url}

    # Small delay to mimic human reading speed
    time.sleep(random.uniform(2.0, 4.0)) 

    try:
        # Switching to the aggregations endpoint which is often more permissive
        response = session.get(
            'https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v1',
            params=params,
            headers=local_headers,
            timeout=15
        )
        
        if response.status_code == 404:
            print(f"   Blocked (404). Try changing your IP/VPN.")
            return []
            
        if response.status_code != 200:
            print(f"   Error {response.status_code}")
            return []
            
        return response.json().get('data', {}).get('search', {}).get('products', [])
    except Exception as e:
        print(f"   Search failed: {e}")
        return []


def fetch_product_details(tcin: str, store_id: str) -> Optional[dict]:
    api_key = get_api_key()
    
    params = {
        'key': api_key,
        'tcin': tcin,
        'is_bot': 'false',
        'store_id': store_id,
        'pricing_store_id': store_id,
        'has_pricing_store_id': 'true',
        'has_financing_options': 'true',
        'include_obsolete': 'true',
        'skip_personalized': 'true',
        'channel': 'WEB',
        'page': f'/p/A-{tcin}',
    }
    
    try:
        response = requests.get(
            'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1',
            params=params,
            headers=HEADERS,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"   Error fetching {tcin}: {e}")
    
    return None

# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def infer_tags(title: str, category: str, ingredients: str = "") -> Set[str]:
    tags: Set[str] = set()
    text = f"{title} {category} {ingredients}".lower()
    
    if any(x in text for x in ['chicken', 'turkey', 'duck']):
        tags.add('poultry')
        tags.add('meat')
    if any(x in text for x in ['beef', 'steak', 'ground beef', 'pork', 'bacon', 'ham', 'sausage']):
        tags.add('meat')
    if any(x in text for x in ['salmon', 'tuna', 'tilapia', 'cod', 'shrimp', 'fish', 'seafood']):
        tags.add('fish')
    if any(x in text for x in ['milk', 'cheese', 'yogurt', 'cottage', 'cream']):
        tags.add('dairy')
    if 'egg' in text:
        tags.add('eggs')
    if any(x in text for x in ['bean', 'lentil', 'chickpea', 'tofu', 'tempeh', 'edamame']):
        tags.add('legume')
        tags.add('plant-based')
    if any(x in text for x in ['protein shake', 'protein bar', 'protein powder', 'whey']):
        tags.add('supplement')
    
    return tags

def infer_category(department: str, category_name: str, title: str) -> str:
    text = f"{department} {category_name} {title}".lower()
    
    if any(x in text for x in ['meat', 'poultry', 'beef', 'pork', 'chicken', 'turkey']):
        return 'meat'
    if any(x in text for x in ['seafood', 'fish', 'salmon', 'tuna', 'shrimp']):
        return 'seafood'
    if any(x in text for x in ['dairy', 'milk', 'cheese', 'yogurt']):
        return 'dairy'
    if 'egg' in text:
        return 'eggs'
    if any(x in text for x in ['protein shake', 'protein bar', 'protein powder']):
        return 'protein'
    if any(x in text for x in ['bean', 'lentil', 'tofu', 'tempeh', 'pea', 'nut', 'edamame']):
        return 'plant'
    
    return 'other'

def parse_product(raw_data: dict, query_category: str) -> Optional[CuentaProduct]:
    try:
        product = raw_data.get('data', {}).get('product', {})
        item = product.get('item', {})
        price_data = product.get('price', {})
        enrichment = item.get('enrichment', {})
        nutrition = enrichment.get('nutrition_facts', {})
        
        tcin = product.get('tcin')
        if not tcin:
            return None
            
        title = item.get('product_description', {}).get('title', 'Unknown')
        title = title.replace('&#38;', '&').replace('&#8482;', '™').replace('&#174;', '®')
        
        brand = item.get('primary_brand', {}).get('name')
        barcode = item.get('primary_barcode')
        
        images = enrichment.get('images', {})
        image_url = images.get('primary_image_url')
        
        price = price_data.get('current_retail') or price_data.get('reg_retail') or 0
        if isinstance(price, str):
            price = float(re.sub(r'[^\d.]', '', price) or 0)
        
        # skip if no price good edge case
        if price <= 0:
            return None
        
        department = item.get('merchandise_classification', {}).get('department_name', '')
        category_name = product.get('category', {}).get('name', '')
        category = infer_category(department, category_name, title)
        if category == 'other':
            category = query_category  # usesss the search category as fallback which is a good feature thank you judy for the idea
        
        calories = 0
        protein = 0.0
        fat = 0.0
        carbs = 0.0
        fiber = 0.0
        serving_size = "1 serving"
        servings = 1.0
        ingredients = ""
        
        if nutrition:
            ingredients = nutrition.get('ingredients', '')
            prepared_list = nutrition.get('value_prepared_list', [])
            
            if prepared_list:
                prep = prepared_list[0]
                
                ss = prep.get('serving_size', '')
                ss_unit = prep.get('serving_size_unit_of_measurement', '')
                if ss:
                    serving_size = f"{ss} {ss_unit}".strip()
                
                spc = prep.get('servings_per_container')
                if spc:
                    try:
                        # Handle "About 6-7" type strings
                        spc_clean = re.sub(r'[^\d.]', '', str(spc))
                        if spc_clean:
                            servings = float(spc_clean)
                    except (ValueError, TypeError):
                        servings = 1.0
                
                for nutrient in prep.get('nutrients', []):
                    name = nutrient.get('name', '').lower()
                    quantity = nutrient.get('quantity', 0) or 0
                    
                    if 'calorie' in name:
                        calories = int(quantity)
                    elif name == 'protein':
                        protein = float(quantity)
                    elif 'total fat' in name:
                        fat = float(quantity)
                    elif 'total carbohydrate' in name or 'carbohydrate' in name:
                        carbs = float(quantity)
                    elif 'fiber' in name:
                        fiber = float(quantity)
        
        tags = infer_tags(title, category_name, ingredients)
        
        return CuentaProduct(
            name=title,
            price=price,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            fiber=fiber,
            serving_size=serving_size,
            servings=servings,
            category=category,
            tags=tags,
            tcin=tcin,
            brand=brand,
            barcode=barcode,
            image_url=image_url,
        )
        
    except Exception as e:
        print(f"      Error parsing product: {e}")
        return None

# =============================================================================
# SUPABASE FUNCTIONS
# =============================================================================

_supabase_client: Optional[Any] = None

def get_client() -> Any:
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        _supabase_client = create_client(url, key)
    return _supabase_client


def get_or_create_store(location_id: str, name: str, chain: str, zip_code: str) -> Optional[str]:
    if not HAS_SUPABASE:
        return None
    
    client = get_client()
    
    result = client.table("stores").select("id").eq("external_id", location_id).execute()
    
    if result.data:
        return result.data[0]["id"]
    
    new_store = {
        "name": name,
        "external_id": location_id,
        "chain": chain,
        "zip_code": zip_code,
    }
    
    result = client.table("stores").insert(new_store).execute()
    if result.data:
        return result.data[0]["id"]
    
    return None

# uploadded all the produicts to the supabase client unless dry run or doesn't need
def upload_products(products: List[CuentaProduct], store_id: str, dry_run: bool = False) -> Dict[str, int]:
    stats = {"uploaded": 0, "skipped": 0, "errors": 0}
    
    if not HAS_SUPABASE or dry_run:
        stats["skipped"] = len(products)
        return stats
    
    client = get_client()
    
    for product in products:
        try:
            product_data = {
                "store_id": store_id,
                "name": product.name[:255],
                "price": product.price,
                "calories": product.calories,
                "protein": product.protein,
                "fat": product.fat,
                "carbs": product.carbs,
                "fiber": product.fiber,
                "serving_size": product.serving_size,
                "servings_per_container": product.servings,
                "category": product.category,
                "tags": list(product.tags),
                "barcode": product.barcode,
                "external_id": product.tcin,
                "image_url": product.image_url,
                "brand": product.brand,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            
            client.table("products").upsert(
                product_data,
                on_conflict="store_id,external_id"
            ).execute()
            
            stats["uploaded"] += 1
            
        except Exception as e:
            print(f"   Error uploading {product.name[:30]}: {e}")
            stats["errors"] += 1
    
    return stats

# =============================================================================
# MAIN SCRAPER
# =============================================================================

def run_bulk_scrape(
    zip_code: str = "77021",
    products_per_query: int = 20,
    categories: Optional[List[str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:    
    results = {
        "store": None,
        "queries": 0,
        "products_found": 0,
        "products_with_nutrition": 0,
        "products_uploaded": 0,
        "errors": 0,
    }
    
    print("\n1. Getting API key...")
    api_key = get_api_key()
    print(f"   Key: {api_key[:20]}...")
    
    # Find store
    print(f"\n2. Finding Target stores near {zip_code}...")
    stores = get_stores_near_zip(zip_code)
    
    if not stores:
        print("   No stores found!")
        return results
    
# Target sometimes puts the data inside a 'store' key, sometimes directly
    first_store = stores[0]
    store_id = first_store.get('store_id') or first_store.get('location', {}).get('location_id')
    store_name = first_store.get('store_name') or first_store.get('location', {}).get('location_name', 'Unknown')
    
    if not store_id:
        print("   Could not parse Store ID from response!")
        return results

    print(f"   Using: {store_name} ({store_id})")
    results["store"] = store_name
    
    db_store_id = None
    if HAS_SUPABASE and not dry_run:
        print("\n3. Setting up store in Supabase...")
        try:
            db_store_id = get_or_create_store(store_id, f"Target - {store_name}", "Target", zip_code)
            print(f"  Store ID: {db_store_id}")
        except Exception as e:
            print(f"  ❌ Supabase error: {e}")
    
    if categories:
        search_categories = {k: v for k, v in SEARCH_QUERIES.items() if k in categories}
    else:
        search_categories = SEARCH_QUERIES
    
    all_products: List[CuentaProduct] = []
    seen_tcins: Set[str] = set()
    
    print(f"\n4. Scraping products...")
    
    for category, queries in search_categories.items():
        print(f"\n  {category.upper()}")
        
        for query in queries:
            print(f"   '{query}'...", end=" ", flush=True)
            
            try:
                search_results = search_products(query, store_id, count=products_per_query)
                results["queries"] += 1
                
                query_products = 0
                
                for item in search_results:
                    tcin = item.get('tcin')
                    if not tcin or tcin in seen_tcins:
                        continue
                    
                    seen_tcins.add(tcin)
                    
                    # Fetch full details (includes nutrition)
                    raw_data = fetch_product_details(tcin, store_id)
                    if not raw_data:
                        continue
                    
                    product = parse_product(raw_data, category)
                    if product and product.price > 0:
                        all_products.append(product)
                        query_products += 1
                        results["products_found"] += 1
                        
                        if product.protein > 0:
                            results["products_with_nutrition"] += 1
                    
                    time.sleep(0.3) # i am not a ddsoser 
                
                print(f"{query_products} products")
                
            except Exception as e:
                print(f"Error: {e}")
                results["errors"] += 1
            
            time.sleep(0.5)  # I AM A REAL BOY!!!!!!!!!!!!!!!!!!!!!
    # upload all products iinally
    if all_products:
        print(f"\n5. Uploading {len(all_products)} products...")
        
        if dry_run:
            print("   (Dry run - showing sample)")
            for p in all_products[:10]:
                status = "✓" if p.protein > 0 else "○"
                print(f"   {status} {p.name[:45]}... ${p.price:.2f} | {p.calories}cal | {p.protein}g")
            if len(all_products) > 10:
                print(f"   ... and {len(all_products) - 10} more")
            results["products_uploaded"] = 0
        elif db_store_id:
            upload_stats = upload_products(all_products, db_store_id, dry_run)
            results["products_uploaded"] = upload_stats["uploaded"]
            results["errors"] += upload_stats["errors"]
            print(f"  Uploaded: {upload_stats['uploaded']}")
            if upload_stats["errors"]:
                print(f"  Errors: {upload_stats['errors']}")
        else:
            print("   No Supabase connection - skipping upload")
    
    return results

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Bulk scrape Target products for Cuenta")
    parser.add_argument("--zip", default="77021", help="ZIP code to search near")
    parser.add_argument("--limit", type=int, default=20, help="Products per search query")
    parser.add_argument("--categories", nargs="+", choices=list(SEARCH_QUERIES.keys()),
                        help="Specific categories to scrape")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    
    args = parser.parse_args()
    
    results = run_bulk_scrape(
        zip_code=args.zip,
        products_per_query=args.limit,
        categories=args.categories,
        dry_run=args.dry_run,
    )
    
    print("\n" + "=" * 60)
    print(f"   Store: {results['store']}")
    print(f"   Queries: {results['queries']}")
    print(f"   Products found: {results['products_found']}")
    print(f"   With nutrition: {results['products_with_nutrition']}")
    print(f"   Products uploaded: {results['products_uploaded']}")
    if results["errors"]:
        print(f"   Errors: {results['errors']}")


if __name__ == "__main__":
    main()