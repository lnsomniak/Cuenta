import os
import base64
import re
from typing import Optional, List, Set, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# CONFIG
# =============================================================================

KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
KROGER_API_BASE = "https://api.kroger.com/v1"

from typing import Optional, Dict, Any
_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": None
}

# Nutrition fallback for missing data
enrich_product_nutrition: Optional[Callable] = None
try:
    from nutrition_fallback import enrich_product, lookup_nutrition_smart
    HAS_FALLBACK = True
except ImportError:
    HAS_FALLBACK = False

# =============================================================================
# AUTH
# =============================================================================

#  this should get OAuth2 access tokens using client_credentials grant
def get_access_token() -> str:
    global _token_cache
    # first, checks the cache and if it's expired
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            return _token_cache["access_token"]
    
    if not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET:
        raise ValueError("KROGER_CLIENT_ID or KROGER_CLIENT_SECRET not being identified smart guy")
    
    # Encode credentials for safety kinda mostly to learn for me
    credentials = f"{KROGER_CLIENT_ID}:{KROGER_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    response = requests.post(
        "https://api.kroger.com/v1/connect/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}"
        },
        data={
            "grant_type": "client_credentials",
            "scope": "product.compact"
        },
        timeout=10 # i am not a ddoser!!
    )
    
    response.raise_for_status()
    data = response.json()
    
    # Cache token
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = datetime.now() + timedelta(seconds=data.get("expires_in", 1800) - 60)
    
    return _token_cache["access_token"]

# headers to make me lookn like a real boy, thank you matt stiles
def get_headers() -> Dict[str, str]:
    token = get_access_token()
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

# =============================================================================
# CUENTA PRODUCT FORMAT
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
    tags: Set[str] = field(default_factory=set)
    
# Additional nutrition (can be enriched by USDA)
    fat: float = 0
    carbs: float = 0
    fiber: float = 0
    sodium: float = 0.0

# Kroger fields
    upc: Optional[str] = None
    product_id: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None

    @property
    def total_calories(self) -> float:
        return self.calories * self.servings
    
    @property
    def total_protein(self) -> float:
        return self.protein * self.servings
    
    @property
    def protein_per_dollar(self) -> float:
        if self.price > 0:
            return self.total_protein / self.price
        return 0
    
# =============================================================================
# TAG INFERENCE
# =============================================================================

def infer_tags(name: str, categories: Optional[List[str]] = None) -> Set[str]:
    # this is just a repeat of target.py with difference variable, most of this is the same and makes my job easier. thank you kroger for not being like aldi. 
    tags: Set[str] = set() # yes this is neccessary sonarqube said so
    text = name.lower()
    if categories:
        text += " " + " ".join(c.lower() for c in categories)
    
    # Protein sources
    if any(x in text for x in ['chicken', 'turkey', 'duck']):
        tags.add('poultry')
        tags.add('meat')
    if any(x in text for x in ['beef', 'steak', 'ground beef', 'pork', 'bacon', 'ham', 'sausage']):
        tags.add('meat')
    if any(x in text for x in ['salmon', 'tuna', 'tilapia', 'cod', 'shrimp', 'fish fillet', 'crab', 'lobster']):
        tags.add('fish')
    if any(x in text for x in ['milk', 'cheese', 'yogurt', 'cottage', 'cream']):
        tags.add('dairy')
    if 'egg' in text.split(): 
        tags.add('eggs')
    
    # Allergens
    if any(x in text for x in ['wheat', 'bread', 'flour', 'pasta', 'cereal']):
        tags.add('gluten')
    if any(x in text for x in ['peanut', 'almond', 'walnut', 'cashew', 'pecan', 'nut']):
        tags.add('nuts')
    if 'soy' in text or 'tofu' in text:
        tags.add('soy')
    
    # Diet indicators
    if 'organic' in text:
        tags.add('organic')
    if 'vegan' in text:
        tags.add('vegan')
    if 'keto' in text or 'low carb' in text:
        tags.add('keto')
    
    return tags

# maps the kroger stuff to my stuff, looks for tags and if finds anything related in the text, organize. a neat and organized way to do it for sure, probably could be faster but i'm only 19. 
def infer_category(categories: Optional[List[str]]) -> str:
    if not categories:
        return "other"
    
    text = " ".join(categories).lower()
    
    if any(x in text for x in ['meat', 'poultry', 'beef', 'pork', 'chicken']):
        return 'meat'
    if any(x in text for x in ['seafood', 'fish']):
        return 'seafood'
    if any(x in text for x in ['dairy', 'milk', 'cheese', 'yogurt']):
        return 'dairy'
    if any(x in text for x in ['egg']):
        return 'eggs'
    if any(x in text for x in ['bread', 'bakery']):
        return 'bread'
    if any(x in text for x in ['frozen']):
        return 'frozen'
    if any(x in text for x in ['produce', 'vegetable', 'fruit']):
        return 'produce'
    if any(x in text for x in ['snack', 'chip', 'cracker']):
        return 'snacks'
    if any(x in text for x in ['beverage', 'drink', 'juice', 'water']):
        return 'beverages'
    
    return 'other'

# =============================================================================
# LOCATIONS API
# =============================================================================

def get_stores_near_zip(
    zip_code: str,
    limit: int = 5,
    chain: Optional[str] = None
) -> List[Dict[str, Any]]: # looks prettier this way I tihnk
    # I don't like this blank space
    params = {
        "filter.zipCode.near": zip_code,
        "filter.limit": limit,
    }
    if chain:
        params["filter.chain"] = chain
    
    response = requests.get(
        f"{KROGER_API_BASE}/locations",
        headers=get_headers(),
        params=params,
        timeout=10
    )
    
    response.raise_for_status()
    data = response.json()
    
    stores: List[Dict[str, Any]] = []
    for loc in data.get("data", []):
        stores.append({
            "location_id": loc.get("locationId"),
            "name": loc.get("name"),
            "chain": loc.get("chain"),
            "address": loc.get("address", {}),
            "phone": loc.get("phone"),
        })
    
    return stores

# =============================================================================
# PRODUCTS API
# =============================================================================
# a search bar similar to the one on kroger api and returns the raw json for me to later organize!
def search_products(
    query: str,
    location_id: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    params = {
        "filter.term": query,
        "filter.locationId": location_id,
        "filter.limit": limit,
        "filter.fulfillment": "ais",  # Available in store
    }
    
    response = requests.get(
        f"{KROGER_API_BASE}/products",
        headers=get_headers(),
        params=params,
        timeout=10
    )
    
    response.raise_for_status()
    data = response.json()
    
    return data.get("data", [])

# checks my params and filters
def get_product_details(product_id: str, location_id: str) -> Optional[Dict[str, Any]]:
    params = {
        "filter.locationId": location_id,
    }
    
    response = requests.get(
        f"{KROGER_API_BASE}/products/{product_id}",
        headers=get_headers(),
        params=params,
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json().get("data")
    return None

# =============================================================================
# PARSING
# =============================================================================

# sees everything in ugly, converts to beautiful CuentaProduct! 
def parse_to_cuenta_product(
    product_data: Dict[str, Any],
    location_id: Optional[str] = None
) -> Optional[CuentaProduct]:
    try:
        # Basic info
        product_id = product_data.get("productId")
        upc = product_data.get("upc")
        name = product_data.get("description", "Unknown")
        brand = product_data.get("brand")
        
        # Categories
        categories = product_data.get("categories", [])
        category = infer_category(categories)
        tags = infer_tags(name, categories)
        
        # Price - get from items array
        price = 0.0
        items = product_data.get("items", [])
        if items:
            item = items[0]
            price_info = item.get("price", {})
            price = price_info.get("regular", 0) or price_info.get("promo", 0)
        
        # Nutrition - in items[0].nutrition or direct
        calories = 0
        protein = 0.0
        fat = 0.0
        carbs = 0.0
        fiber = 0.0
        serving_size = "1 serving"
        servings = 1.0
        
        # Try to get nutrition from items
        if items:
            item = items[0]
            nutrition = item.get("nutrition", {})
            
            # Serving info
            serving_size = nutrition.get("servingSize", "1 serving") or "1 serving"
            servings_str = nutrition.get("servingsPerContainer", "1") 
            if servings_str:
                servings_clean = re.sub(r'[^\d.]', '', str(servings_str))
                if servings_clean:
                    servings = float(servings_clean)
            
            # Nutrients
            nutrients = nutrition.get("nutrients", [])
            for n in nutrients:
                nutrient_name = n.get("name", "").lower()
                amount = n.get("amount", 0) or 0
                
                if "calorie" in nutrient_name:
                    calories = int(amount)
                elif nutrient_name == "protein":
                    protein = float(amount)
                elif "fat" in nutrient_name and "total" in nutrient_name:
                    fat = float(amount)
                elif "carbohydrate" in nutrient_name:
                    carbs = float(amount)
                elif "fiber" in nutrient_name:
                    fiber = float(amount)
        
        # Image
        images = product_data.get("images", [])
        image_url = None
        if images:
            for img in images:
                if img.get("perspective") == "front":
                    sizes = img.get("sizes", [])
                    if sizes:
                        image_url = sizes[0].get("url")
                        break
        # holy brute force LOLLLLLLLLLLLLLLLLLLLLL ^^^^^^^^^^^^^^^ THERE IS NO other way 
        return CuentaProduct(
            name=name,
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
            upc=upc,
            product_id=product_id,
            brand=brand,
            image_url=image_url,
        )
        # large but at least it's organized and very well 
    except Exception as e:
        print(f"Error parsing product: {e}")
        return None


# =============================================================================
# FUNCTIONS FOR MY CONVIENIENCE idk how you spell that
# =============================================================================

def fetch_cuenta_product(product_id: str, location_id: str) -> Optional[CuentaProduct]:
    raw = get_product_details(product_id, location_id)
    if raw:
        return parse_to_cuenta_product(raw, location_id)
    return None
# searches products and return as CuentaProducts.
def search_and_parse(
    query: str,
    location_id: str,
    limit: int = 20,
    min_protein: float = 0,
    enrich: bool = True,
    # it is 7:51am 12/17, and i've spent the last day working on everything as a whole howeever probably the last hour + a couple the night before building this feature of auto-enriching. It's made me realize I am a lot nerdier than I thought
) -> List[CuentaProduct]:
    raw_products = search_products(query, location_id, limit)
    
    products: List[CuentaProduct] = []
    for raw in raw_products:
        product = parse_to_cuenta_product(raw, location_id)
        if not product:
            continue
            #if enrich and HAS_FALLBACK and (product.calories == 0 or product.protein == 0):
            #    enrich_product(product)
                    # Enrich with USDA nutrition if available and needed
        # if you can't tell, this is a fix still written in because I'm not sure this works below
        if enrich and HAS_FALLBACK and (product.calories == 0 or product.protein == 0):
            nutrition = lookup_nutrition_smart(product.name, product.upc)
            if nutrition:
                product.calories = nutrition.calories
                product.protein = nutrition.protein
                product.fat = getattr(nutrition, 'fat', 0)
                product.carbs = getattr(nutrition, 'carbs', 0)
                product.fiber = getattr(nutrition, 'fiber', 0)
                product.serving_size = nutrition.serving_size
            
        if product.protein >= min_protein:
            products.append(product)
    
    return products

# exports products as Python code for my server.py
def export_for_server(products: List[CuentaProduct]) -> str:
    lines = ["# Kroger products - auto-generated", "KROGER_PRODUCTS = ["]
    
    for p in products:
        tags_str = "{" + ", ".join(f'"{t}"' for t in sorted(p.tags)) + "}"
        lines.append(f'''    Product(
        name="{p.name}",
        price={p.price:.2f},
        calories={p.calories},
        protein={p.protein:.1f},
        fat={p.fat:.1f},
        carbs={p.carbs:.1f},
        fiber={p.fiber:.1f},
        serving_size="{p.serving_size}",
        servings={p.servings:.1f},
        category="{p.category}",
        tags={tags_str},
    ),''')
    
    lines.append("]")
    return "\n".join(lines)


# =============================================================================
# MAIN - test! 
# =============================================================================

if __name__ == "__main__":
    import time
    
    # Check credentials
    if not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET:
        print("\n Missing Kroger credentials smart guy")
        exit(1)
    
    print(f"\n Nutrition fallback: {'✓ Enabled' if HAS_FALLBACK else '✗ Disabled'}")
    
    try:
        token = get_access_token()
        print(f"   ✓ Token: {token[:20]}...")
    except Exception as e:
        print(f"   ✗ Auth failed: {e}")
        exit(1)
    
    print("\n2. Finding Kroger stores near you...")
    try:
        stores = get_stores_near_zip("77021", limit=3)
        for s in stores:
            print(f"   - {s['location_id']}: {s['name']} ({s['chain']})")
        
        if not stores:
            print("   ✗ No stores found")
            exit(1)
        
        location_id = stores[0]["location_id"]
        print(f"\n   Using: {location_id}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        exit(1)
    
    time.sleep(0.5)
    
    # Search for products
    print("\n3. Searching for 'protein shake' (with USDA enrichment)...")
    try:
        products = search_and_parse("protein shake", location_id, limit=5, min_protein=0, enrich=True)
        
        for p in products:
            enriched = "🔄" if p.calories > 0 else "❌"
            print(f"\n   {enriched} {p.name[:50]}...")
            print(f"     ${p.price:.2f} | {p.calories} cal | {p.protein}g protein")
            if p.protein_per_dollar > 0:
                print(f"     Protein/$: {p.protein_per_dollar:.1f}g/$")
            print(f"     Tags: {p.tags}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Export sample
    if products:
        print("\n" + "=" * 60)
        print("EXPORT FOR SERVER.PY")
        print("=" * 60)
        print(export_for_server(products[:3]))
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)