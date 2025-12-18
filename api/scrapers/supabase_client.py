import os
from typing import Optional, List
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
# one of the most useful features i've learned while developing- the power of .env 
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for backend operations

_client: Optional[Client] = None

def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("No URL or Service Key, fix")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def get_or_create_store(name: str, store_id: str, zip_code: str = None, city: str = None, state: str = None) -> dict:
    # get or create the store, getting or creating all the information needed ^
    client = get_client()
    # a helpful way to check if it actually exists
    result = client.table("stores").select("*").eq("store_id", store_id).execute()
    # if result dat, return
    if result.data:
        return result.data[0]
    
    # If new 
    new_store = {
        "name": name,
        "store_id": store_id,
        "zip_code": zip_code,
        "city": city,
        "state": state,
    }
    result = client.table("stores").insert(new_store).execute()
    return result.data[0]

# get stores by zip is just as listed, this function grabs the client and the return is a table of all stores near a zipcode
def get_stores_by_zip(zip_code: str) -> List[dict]:
    client = get_client()
    result = client.table("stores").select("*").eq("zip_code", zip_code).execute()
    return result.data

# ==========================================
# Products 
# ==========================================
# "upsert" a product, essentially using an external id for mtching and if we have it, check if the product even exists, which then should update the existing. 
def upsert_product(product: dict, store_id: str = None) -> dict:
    client = get_client()
    
    # If we have an external_id, check if product exists
    if product.get("external_id"):
        existing = client.table("products").select("id").eq("external_id", product["external_id"]).execute()
        if existing.data:
            # This is the real carry, updating the existing 
            result = client.table("products").update(product).eq("external_id", product["external_id"]).execute()
            return result.data[0] if result.data else None
    
    # This inserts new, and it's why it's outside of the if statement
    if store_id:
        product["store_id"] = store_id
    
    result = client.table("products").insert(product).execute()
    return result.data[0] if result.data else None

# batch the products, and return the count of the result data aka how many successful inserts
def upsert_products_batch(products: List[dict], store_id: str = None) -> int:
    client = get_client()
    
    # Add store_id to all products
    if store_id:
        for p in products:
            p["store_id"] = store_id
    
    # Supabase upsert with external_id as the conflict key
    result = client.table("products").upsert(
        products, 
        on_conflict="external_id"
    ).execute()
    
    return len(result.data) if result.data else 0


def get_products(
    category: str = None,
    store_id: str = None,
    min_protein_per_dollar: float = None,
    limit: int = 100,
    order_by: str = "protein_per_dollar",
    ascending: bool = False
) -> List[dict]:
# Query products with filters 
    client = get_client()
    
    query = client.table("products").select("*")
    
    if category:
        query = query.eq("category", category)
    if store_id:
        query = query.eq("store_id", store_id)
    if min_protein_per_dollar:
        query = query.gte("protein_per_dollar", min_protein_per_dollar)
    
    query = query.order(order_by, desc=not ascending).limit(limit)
    
    result = query.execute()
    return result.data

# function is self explanatory but bini isn't the brightest, this grabs those products that have passed the tests aka have nutrition data
def get_products_for_optimization(store_id: str = None, exclude_tags: List[str] = None) -> List[dict]:
    client = get_client()
    
    query = client.table("products").select("*").gt("protein", 0)
    
    if store_id:
        query = query.eq("store_id", store_id)
    
    result = query.execute()
    products = result.data
    
# Filter by tags in Python (Supabase array contains is weird as heck)
    if exclude_tags:
        products = [
            p for p in products 
            if not any(tag in (p.get("tags") or []) for tag in exclude_tags)
        ]
    
    return products


# =============================================================================
# SCRAPER INTEGRATION
# =============================================================================
# plays into what i made last night, saves a cuentaproduct from the target.py target scraper directly TO supabase
# cuenta product is a dataclass from target.py, and store_db_id: is the UUID of the store in supabase which can be confusing but it's very important it isn't the target store_id
def save_target_product(cuenta_product, store_db_id: str = None) -> dict:
    product_dict = {
        "name": cuenta_product.name,
        "brand": cuenta_product.brand,
        "barcode": cuenta_product.barcode,
        "external_id": cuenta_product.tcin,  # Target's TCIN
        "price": cuenta_product.price,
        "unit_price": cuenta_product.unit_price,
        "calories": cuenta_product.calories,
        "protein": cuenta_product.protein,
        "serving_size": cuenta_product.serving_size,
        "servings_per_container": cuenta_product.servings,
        "category": cuenta_product.category,
        "tags": list(cuenta_product.tags),  # Convert set to list for JSON
    }
    
    return upsert_product(product_dict, store_id=store_db_id)

# same thing just in batches
def save_target_products_batch(products, store_db_id: str = None) -> int:
    product_dicts = []
    
    for p in products:
        product_dicts.append({
            "name": p.name,
            "brand": p.brand,
            "barcode": p.barcode,
            "external_id": p.tcin,
            "price": p.price,
            "unit_price": p.unit_price,
            "calories": p.calories,
            "protein": p.protein,
            "serving_size": p.serving_size,
            "servings_per_container": p.servings,
            "category": p.category,
            "tags": list(p.tags),
        })
    
    return upsert_products_batch(product_dicts, store_id=store_db_id)


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":   # this is overlooked just a line. this will never not be true 
    try:
        client = get_client()
        
        result = client.table("stores").select("*").limit(5).execute()
        print(f" Found {len(result.data)} stores")
        
        for store in result.data:
            print(f" - {store['name']} ({store['store_id']})")
        
        products = get_products(limit=5)
        print(f"\n Found {len(products)} products")
        
        for p in products[:3]:
            print(f"  - {p['name'][:40]}... ({p['protein_per_dollar']:.1f}g/$)")
            
    except Exception as e:
        print(f" Error: {e}")
        print("\n probably a supabase error, check .env ")
