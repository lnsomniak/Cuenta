import json
import argparse
from pathlib import Path
from typing import List, Optional
import sys
sys.path.append('../scrapers') # fix
# my hell. 
get_client = None  # Type hint for Pylance
try:
    from supabase_client import get_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


DATA_FILE = Path(__file__).parent / "aldi_products.json"
DEFAULT_STORE = "aldi-houston-ost"

def validate_product(product: dict) -> List[str]:
    issues = []
    
    required = ["external_id", "name", "category"]
    for field in required:
        if not product.get(field): 
            issues.append(f"Missing required field: {field}") # good code ethics
    
    nutrition_fields = ["calories", "protein", "price"]
    missing_nutrition = [f for f in nutrition_fields if product.get(f) is None]
    
    if missing_nutrition:
        issues.append(f"Missing nutrition: {', '.join(missing_nutrition)}") # for me, delete later 
    
    if product.get("_todo"):
        issues.append(f"TODO: {product['_todo']}")
    
    return issues


def validate_all(products: List[dict]) -> dict:
    complete = []
    incomplete = []
    
    for p in products:
        issues = validate_product(p)
        if issues:
            incomplete.append({"product": p["name"], "issues": issues})
        else:
            complete.append(p["name"])
    
    return {
        "total": len(products),
        "complete": len(complete),
        "incomplete": len(incomplete),
        "complete_products": complete,
        "incomplete_products": incomplete,
    }

def transform_for_supabase(product: dict, store_db_id: str) -> Optional[dict]:
    """Transform JSON product to Supabase schema."""
    
    # FIX: Skip incomplete products to avoid error, it did error. 
    if product.get("price") is None or product.get("protein") is None:
        return None
    
    # Calculate servings if not provided  
    servings = product.get("servings_per_container", 1)
    if servings is None:
        servings = 1
    
    return {
        "external_id": product["external_id"],
        "name": product["name"],
        "brand": product.get("brand"),
        "price": product["price"],
        "calories": product.get("calories", 0),
        "protein": product.get("protein", 0),
        "carbs": product.get("carbs", 0),
        "fat": product.get("fat", 0),
        "fiber": product.get("fiber", 0),
        "serving_size": product.get("serving_size", "1 serving"),
        "servings_per_container": servings,
        "category": product.get("category", "Other"),
        "tags": product.get("tags", []),
        "store_id": store_db_id,
    }
# function to upload the manual input of my hell to supabase database 
def upload_products(products: List[dict], store_id: str = DEFAULT_STORE, dry_run: bool = False) -> int:    
    if not HAS_SUPABASE:
        print(" Supabase not configured smart guy ")
        return 0
    
    client = get_client() 
    # get the store, if not found return store not found to lmk
    result = client.table("stores").select("id, name").eq("store_id", store_id).execute()
    
    if not result.data:
        print(f" Store not found: {store_id}")
        print("  Run seed.sql first to create stores smart guy ")
        return 0
    
    store = result.data[0]
    store_db_id = store["id"]
    print(f"   Found: {store['name']} ({store_db_id})")
    
    # Transform products
    to_upload = []
    skipped = 0
    
    for p in products:
        transformed = transform_for_supabase(p, store_db_id)
        if transformed:
            to_upload.append(transformed)
        else:
            skipped += 1
    
    print(f"\n Ready to upload: {len(to_upload)} products")
    print(f"   Skipped (incomplete): {skipped}")
    
    if dry_run:
        print("\n🔸 Dry run - not uploading")
        for p in to_upload:
            protein_per_dollar = (p["protein"] * p["servings_per_container"]) / p["price"] if p["price"] > 0 else 0
            print(f"   - {p['name'][:40]}... ${p['price']:.2f} | {p['protein']}g protein | {protein_per_dollar:.1f}g/$")
        return 0
    
    # Upsert 
    result = client.table("products").upsert(
        to_upload,
        on_conflict="external_id"
    ).execute()
    
    count = len(result.data) if result.data else 0
    print(f"  Uploaded {count} products")
    
    return count

def main():
    parser = argparse.ArgumentParser(description="Upload Aldi products from JSON to Supabase")
    parser.add_argument("--file", default=str(DATA_FILE), help="Path to JSON file")
    parser.add_argument("--store", default=DEFAULT_STORE, help="Store ID to upload to")
    parser.add_argument("--validate", action="store_true", help="Just validate, don't upload")
    parser.add_argument("--dry-run", action="store_true", help="Show what would upload")
    args = parser.parse_args()
    data_path = Path(args.file)
    if not data_path.exists():
        print(f" File not found: {data_path}")
        return
    # loads json ^ 
    print(f"\n Loading: {data_path}")
    with open(data_path) as f:
        data = json.load(f)
    
    products = data.get("products", [])
    print(f"   Found {len(products)} products")
    
    # Validate
    validation = validate_all(products)
    
    print(f"   Complete: {validation['complete']}/{validation['total']}")
    
    if validation["incomplete_products"]:
        print("\n  Incomplete products smart guy:")
        for item in validation["incomplete_products"]:
            print(f"     - {item['product']}")
            for issue in item["issues"]:
                print(f"       └─ {issue}")
    
    if args.validate:
        print("\n Validation complete")
        return
    
    # Upload complete products only
    complete_products = [p for p in products if not validate_product(p)]
    
    if not complete_products:
        print("\n No complete products to upload")
        print("  Fill in missing data in aldi_products.json")
        return
    # this will never happen, but if it does I'll know the code as whole is messed up- a GREAT measure i've learn to add 
    upload_products(complete_products, store_id=args.store, dry_run=args.dry_run)
    
    print("\n Success!")


if __name__ == "__main__":
    main()