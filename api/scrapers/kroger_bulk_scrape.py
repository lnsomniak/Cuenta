import os
import sys
import time
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # colorful sys path

from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# Kroger scraper + Supabase + Nutrition fallback
# =============================================================================

try:
    from kroger import (
        get_access_token,
        get_stores_near_zip,
        search_products,
        parse_to_cuenta_product,
        CuentaProduct,
        KROGER_CLIENT_ID,
        KROGER_CLIENT_SECRET,
    )
    HAS_KROGER = True
except ImportError as e:
    print(f" Missing kroger.py: {e}")
    HAS_KROGER = False

try:
    from supabase_client import get_client
    HAS_SUPABASE = True
except ImportError:
    print(" Supabase not configured - dry run only")
    HAS_SUPABASE = False

try:
    from nutrition_fallback import lookup_nutrition_smart, NutritionData
    HAS_NUTRITION = True
except ImportError:
    print(" Nutrition fallback not available")
    HAS_NUTRITION = False


# =============================================================================
# CONFIG
# =============================================================================

# High-protein search terms by category
SEARCH_QUERIES = {
    "meat": [
        "chicken breast",
        "ground beef",
        "ground turkey", 
        "steak",
        "pork chop",
    ],
    "seafood": [
        "salmon",
        "tuna",
        "tilapia",
        "shrimp",
    ],
    "dairy": [
        "greek yogurt",
        "cottage cheese",
        "cheese",
        "milk protein",
    ],
    "eggs": [
        "eggs",
        "egg whites",
    ],
    "protein": [
        "protein shake",
        "protein bar",
        "protein powder",
    ],
    "plant": [
        "tofu",
        "tempeh",
        "edamame",
        "lentils",
        "black beans",
    ],
}


# =============================================================================
# enrichment of the data, similar to my other scrapers
# =============================================================================

def enrich_product(product: CuentaProduct) -> CuentaProduct:
    if not HAS_NUTRITION:
        return product
    
    # Skip if already has nutrition
    if product.calories > 0 and product.protein > 0:
        return product
    
    nutrition = lookup_nutrition_smart(product.name, product.upc)
    
    if nutrition:
        product.calories = nutrition.calories
        product.protein = nutrition.protein
        product.fat = getattr(nutrition, 'fat', 0)
        product.carbs = getattr(nutrition, 'carbs', 0)
        product.fiber = getattr(nutrition, 'fiber', 0)
        product.serving_size = nutrition.serving_size
    
    return product

# =============================================================================
# SUPABASE UPLOAD
# =============================================================================
# I won't be explaining much, typically I run through it one last time and analyze and fix any issues I see AND highlight but this is getting repetitive
def get_or_create_store(location_id: str, name: str, chain: str, zip_code: str) -> Optional[int]:
    if not HAS_SUPABASE:
        return None
    
    client = get_client()
    result = client.table("stores").select("id").eq("external_id", location_id).execute()
    
    if result.data:
        return result.data[0]["id"]
    
    store_data = {
        "name": name,
        "chain": chain.lower(),
        "external_id": location_id,
        "zip_code": zip_code,
        "address": f"{name}, {zip_code}",
    }
    
    result = client.table("stores").insert(store_data).execute()
    
    if result.data:
        print(f"   Created store: {name} (ID: {result.data[0]['id']})")
        return result.data[0]["id"]
    
    return None


def upload_products(products: List[CuentaProduct], store_id: str, dry_run: bool = False) -> Dict[str, int]:
    stats = {"uploaded": 0, "skipped": 0, "errors": 0}
    
    if not HAS_SUPABASE or dry_run:
        stats["skipped"] = len(products)
        return stats
    
    client = get_client()
    
    for product in products:
        try:
            total_protein = product.protein * product.servings
            protein_per_dollar = total_protein / product.price if product.price > 0 else 0
            protein_per_100cal = (product.protein / product.calories * 100) if product.calories > 0 else 0
            
            product_data = {
                "store_id": store_id,
                "name": product.name[:255],
                "price": product.price,
                "calories": product.calories,
                "protein": product.protein,
                "fat": getattr(product, 'fat', 0),
                "carbs": getattr(product, 'carbs', 0),
                "fiber": getattr(product, 'fiber', 0),
                "serving_size": product.serving_size,
                "servings_per_container": product.servings,
                "category": product.category,
                "tags": list(product.tags),
                "barcode": product.upc,
                "external_id": product.product_id,
                "image_url": product.image_url,
                "brand": product.brand,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            
            # Upsert by store_id + external_id
            client.table("products").upsert(
                product_data,
                on_conflict="store_id,external_id"
            ).execute()
            
            stats["uploaded"] += 1
            
        except Exception as e:
            print(f"   ❌ Error uploading {product.name[:30]}: {e}")
            stats["errors"] += 1
    
    return stats

# =============================================================================
# MAIN SCRAPER
# =============================================================================

def scrape_kroger(
    zip_code: str = "77021",
    limit_per_query: int = 20,
    dry_run: bool = False,
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not HAS_KROGER:
        return {"error": "kroger.py not found"}
    
    if not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET:
        return {"error": "missing credentials"}
    
    stats = {
        "store": None,
        "queries": 0,
        "products_found": 0,
        "products_enriched": 0,
        "products_uploaded": 0,
        "errors": 0,
    }
    
    print("\n1. Authenticating ")
    try:
        token = get_access_token()
        print(f"   Token: {token[:20]}...")
    except Exception as e:
        print(f"   Auth failed: {e}")
        return {"error": str(e)}
    
    print(f"\n2. Finding Kroger stores near {zip_code}...")
    try:
        stores = get_stores_near_zip(zip_code, limit=1)
        if not stores:
            return {"error": "no stores found"}
        
        store = stores[0]
        location_id = store["location_id"]
        store_name = store["name"]
        chain = store["chain"]
        
        print(f"  Using: {store_name} ({location_id})")
        stats["store"] = store_name
        
    except Exception as e:
        print(f"  Error: {e}")
        return {"error": str(e)}
    
    store_id = None
    if HAS_SUPABASE and not dry_run: # important line
        print("\n3. Setting up store in Supabase...")
        store_id = get_or_create_store(location_id, store_name, chain, zip_code)
        if store_id:
            print(f"  Store ID: {store_id}")
    else:
        print("\n3. Skipping Supabase (dry run)")
        
    categories_to_scrape = categories or list(SEARCH_QUERIES.keys())
    all_products: List[CuentaProduct] = []
    seen_upcs: set = set()  # Dedupe by UPC
    
    for category in categories_to_scrape:
        if category not in SEARCH_QUERIES:
            print(f"  Unknown category: {category}")
            continue
        
        queries = SEARCH_QUERIES[category]
        print(f"\n  {category.upper()}")
        
        for query in queries:
            stats["queries"] += 1
            
            try:
                print(f"   '{query}'...", end=" ", flush=True)
                
                raw_products = search_products(query, location_id, limit=limit_per_query)
                
                count = 0
                for raw in raw_products:
                    product = parse_to_cuenta_product(raw, location_id)
                    if not product:
                        continue
                    
                    if product.upc and product.upc in seen_upcs:
                        continue
                    if product.upc:
                        seen_upcs.add(product.upc)
                    
                    # Enrich with nutrition
                    if HAS_NUTRITION:
                        product = enrich_product(product)
                        if product.protein > 0:
                            stats["products_enriched"] += 1
                    
                    all_products.append(product)
                    count += 1
                
                stats["products_found"] += count
                print(f"{count} products")
                
                # Rate limit
                time.sleep(0.3)
                
            except Exception as e:
                print(f"ERROR: {e}")
                stats["errors"] += 1
    # telling me how many for my liking
    print(f"\n5. Uploading {len(all_products)} products...")
    
    if dry_run:
        print("   (Dry run - skipping upload)")
        print("\n   Sample products:")
        for p in all_products[:5]:
            enriched = "✓" if p.protein > 0 else "✗"
            print(f"   {enriched} {p.name[:40]}... ${p.price:.2f} | {p.calories}cal | {p.protein}g")
    else: # still a good line
        upload_stats = upload_products(all_products, store_id, dry_run)
        stats["products_uploaded"] = upload_stats["uploaded"]
        stats["errors"] += upload_stats["errors"]
        print(f"  Uploaded: {upload_stats['uploaded']}")
        if upload_stats["errors"]:
            print(f"  Errors: {upload_stats['errors']}")
    
    print("=" * 60)
    print(f"   Store: {stats['store']}")
    print(f"   Queries: {stats['queries']}")
    print(f"   Products found: {stats['products_found']}")
    print(f"   Products enriched: {stats['products_enriched']}")
    print(f"   Products uploaded: {stats['products_uploaded']}")
    if stats["errors"]:
        print(f"   Errors: {stats['errors']}")
    
    return stats


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk scrape Kroger products for Cuenta")
    parser.add_argument("--zip", default="77021", help="ZIP code to find nearby store")
    parser.add_argument("--limit", type=int, default=20, help="Products per search query")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument("--categories", nargs="+", help="Categories to scrape (default: all)")
    
    args = parser.parse_args()
    
    scrape_kroger(
        zip_code=args.zip,
        limit_per_query=args.limit,
        dry_run=args.dry_run,
        categories=args.categories,
    )