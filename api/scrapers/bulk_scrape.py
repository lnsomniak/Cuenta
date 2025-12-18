import argparse
import time
from typing import List
from target import search_products, fetch_cuenta_product, CuentaProduct, get_stores_near_zip

# Only import Supabase if not dry run, 
try:
    from supabase_client import get_or_create_store, save_target_products_batch, get_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("Use --dry-run mode ")
# reminder
#     python bulk_scrape.py                    Run with defaults
#    python bulk_scrape.py --queries "eggs"    Custom search
#    python bulk_scrape.py --dry-run           Don't save to DB

# =============================================================================
# CONFIG
# =============================================================================

DEFAULT_QUERIES = [
    # High protein
    "protein shake",
    "greek yogurt", 
    "cottage cheese",
    "eggs",
    "deli meat turkey",
    "deli meat chicken",
    "protein bar",
    "beef jerky",
    
    # Dairy
    "milk",
    "cheese",
    "string cheese",
    
    # Canned protein
    "canned tuna",
    "canned chicken",
    "canned salmon",
    
    # Frozen protein
    "frozen chicken",
    "frozen fish",
    "frozen shrimp",
    
    # Breakfast
    "oatmeal protein",
    "kodiak cakes",
]

# Houston store
DEFAULT_ZIP = "77021"
DEFAULT_STORE_ID = "3375"  # Target Houston Mon


# =============================================================================
# SCRAPER
# =============================================================================

def scrape_products(
    queries: List[str],
    store_id: str = DEFAULT_STORE_ID,
    products_per_query: int = 10,
    delay: float = 0.5,
) -> List[CuentaProduct]:
    all_products = []
    seen_tcins = set()
    
    for query in queries:
        try:
            results = search_products(query, store_id=store_id, count=products_per_query)
            print(f" Found {len(results)} results")
            
            for item in results:
                tcin = item.get("tcin")
                
                # Skip duplicates
                if not tcin or tcin in seen_tcins:
                    continue
                seen_tcins.add(tcin)
                
                # Fetch full product details
                time.sleep(delay)
                product = fetch_cuenta_product(tcin, store_id=store_id)
                
                if product:
                    # Only keep products with actual nutrition data
                    if product.protein > 0:
                        all_products.append(product)
                        print(f"   ✓ {product.name[:45]}...")
                        print(f"      ${product.price:.2f} | {product.protein}g protein | {product.protein_per_dollar:.1f}g/$")
                    else:
                        print(f"   ○ {product.name[:45]}... (no nutrition)")
                        
        except Exception as e:
            print(f"  Error searching '{query}': {e}")
            continue
    
    return all_products

def save_to_supabase(
    products: List[CuentaProduct], 
    store_name: str = "Target Houston Montrose",
    store_id: str = DEFAULT_STORE_ID,
    zip_code: str = DEFAULT_ZIP,
) -> int:
    if not HAS_SUPABASE:
        return 0

    store = get_or_create_store(
        name=store_name,
        store_id=store_id,
        zip_code=zip_code,
        city="Houston",
        state="TX"
    )
    store_db_id = store["id"]
    print(f"   Store ID: {store_db_id}")
    
    # Save products
    print(f"\n Saving {len(products)} products to Supabase...")
    count = save_target_products_batch(products, store_db_id=store_db_id)
    print(f" Saved {count} products")
    
    return count


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Bulk scrape Target products for Cuenta")
    parser.add_argument("--queries", nargs="+", help="Custom search queries")
    parser.add_argument("--zip", default=DEFAULT_ZIP, help="ZIP code for store lookup")
    parser.add_argument("--store-id", default=DEFAULT_STORE_ID, help="Target store ID")
    parser.add_argument("--count", type=int, default=10, help="Products per query")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to database")
    parser.add_argument("--find-stores", action="store_true", help="Just find nearby stores and exit")
    args = parser.parse_args()
    
    print("=" * 60)
    print("CUENTA BULK SCRAPER")
    print("=" * 67) # LOLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL
    
    if args.find_stores:
        print(f"\n Finding Target stores near {args.zip}...")
        stores = get_stores_near_zip(args.zip, limit=5)
        
        for store in stores:
            loc = store.get("location", {})
            name = loc.get("location_name", "Unknown")
            sid = loc.get("location_id", "?")
            addr = loc.get("address", {})
            city = addr.get("city", "")
            print(f"   {sid}: {name} - {city}")
        
        print("\nUse --store-id <ID> to scrape from a specific store")
        return
# at this point I am too tired to keep writing comments as I write, however do know that I will be back to clean this up since I know this isn't the best code
    queries = args.queries or DEFAULT_QUERIES
    print(f"\n Will search {len(queries)} queries")
    print(f" Store ID: {args.store_id}")
    print(f" Products per query: {args.count}")
    
    products = scrape_products(
        queries=queries,
        store_id=args.store_id,
        products_per_query=args.count,
        delay=args.delay,
    )
    
    print("\n" + "=" * 60)
    print(f"SCRAPED {len(products)} PRODUCTS WITH NUTRITION DATA")
    print("=" * 60)
    
    # Top 10 by protein per dollar
    if products:
        print("\n Top 10 by Protein/$:")
        sorted_products = sorted(products, key=lambda p: p.protein_per_dollar, reverse=True)
        for i, p in enumerate(sorted_products[:10], 1):
            print(f"   {i:2}. {p.name[:40]}... ({p.protein_per_dollar:.1f}g/$)")
    
    # Save or dry run
    if args.dry_run:
        print("\n🔸 Dry run - not saving to database")
    else:
        if HAS_SUPABASE:
            save_to_supabase(products, store_id=args.store_id, zip_code=args.zip)
        else:
            print("\n Supabase not configured. Add SUPABASE_URL and SUPABASE_SERVICE_KEY to .env")
    
    print("\n FInished ")


if __name__ == "__main__":
    main()