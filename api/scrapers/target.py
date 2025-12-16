import warnings
import re
import html
import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Set

# Cuenta Target Scraper
# Adapted from Matt Stiles' target_example.py (github.com/stiles/aldi)

# Thank you so much Matt !
warnings.filterwarnings('ignore', message='.*OpenSSL.*')
warnings.filterwarnings('ignore', category=DeprecationWarning) 

import requests
import urllib3
urllib3.disable_warnings()

def get_api_key() -> str: # extracts the api key from target's website and is able to handle rotation! once again couldn't have done it without Matt
    fallback_key = '9f36aeafbe60771e321a7cc95a78140772ab3e96'
# target explcititylllyyyy lets their key stay public, they are suprisingly dev friendly. Thank you Target. 
    try:
        response = requests.get(
            'https://www.target.com/p/-/A-12945916',
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            verify=False, # womp womp
            timeout=10
        )
        patterns = [
            r'apiKey["\']?\s*:\s*["\']([a-f0-9]{40})["\']',
            r'"key"\s*:\s*"([a-f0-9]{40})"',
            r'key:\s*["\']([a-f0-9]{40})["\']',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return fallback_key
        
    except Exception:
        return fallback_key

# UPDATE this. I need to remember that if I do add certain things they need to go here since this is just a direct copy of my server.py format except now with extra fields for target. End game this will be a much longer list full of different optionals
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
    
    # Target extra fields
    tcin: Optional[str] = None
    brand: Optional[str] = None
    unit_price: Optional[str] = None
    barcode: Optional[str] = None
    
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
# A good system that infers dietary tags based on product will be neccessary and is neccessary. 
def infer_tags(title: str, category: str, ingredients: str = "") -> Set[str]: 
    tags = set()
    text = f"{title} {category} {ingredients}".lower()
    
    # Protein sources
    if any(x in text for x in ['chicken', 'turkey', 'duck']):
        tags.add('poultry')
        tags.add('meat')
    if any(x in text for x in ['beef', 'steak', 'ground beef', 'pork', 'bacon', 'ham', 'sausage']):
        tags.add('meat')
    if any(x in text for x in ['salmon', 'tuna', 'tilapia', 'cod', 'shrimp', 'fish']):
        tags.add('fish')
    if any(x in text for x in ['milk', 'cheese', 'yogurt', 'cottage', 'cream']):
        tags.add('dairy')
    if 'egg' in text:
        tags.add('eggs')
    
    # ALLergens
    if any(x in text for x in ['wheat', 'bread', 'flour', 'pasta', 'cereal']):
        tags.add('gluten')
    if any(x in text for x in ['peanut', 'almond', 'walnut', 'cashew', 'pecan', 'tree nut']):
        tags.add('nuts')
    if 'soy' in text:
        tags.add('soy')
    
    # Diet indicators
    if 'vegan' in text:
        tags.add('vegan')
    if 'keto' in text or 'low carb' in text:
        tags.add('keto')
    if any(x in text for x in ['rice', 'bread', 'pasta', 'cereal', 'oat']):
        tags.add('high_carb')
    
    # Categories
    if any(x in text for x in ['bean', 'lentil', 'chickpea', 'tofu', 'tempeh']):
        tags.add('legume')
        tags.add('vegan')
    
    return tags

# this is the annoying part, but now that it's done I feel much better. 
# Mapping target cateogies to Cuenta categories
def infer_category(department: str, category: str) -> str:
    text = f"{department} {category}".lower()
    
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
    if any(x in text for x in ['cereal', 'breakfast', 'oat']):
        return 'breakfast'
    if any(x in text for x in ['canned', 'pantry']):
        return 'pantry'
    
    return 'other'
# 
HEADERS = {
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://www.target.com', # preventing a 403 forbidden error. I am lucky I did not have to think of this myself, thank you matt stiles. 
    'referer': 'https://www.target.com/',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"', 
    'sec-fetch-dest': 'empty', 
    'sec-fetch-mode': 'cors',      
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', # i am a real human boy pls let me in! 
}
# there has to be something said about how advanced things like these haVe become. This disctionary is used to impersonate a real web browser when making automated requests and like sure it's good and it's part of the plan, you show this to Benjamin Franklin and he burns you
def fetch_product(tcin: str, store_id: str = "3375", api_key: str = None) -> Optional[dict]:
# a function that takes the tcin aka "target commerce item number" as the primary input of it all
    if api_key is None:
        api_key = get_api_key()
    
    params = { # self explanatory but this shapes the data returned by the api
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
    
    response = requests.get(
        'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1', # a GREAT source of all the price and nutrition data for the optimization engine
        params=params,
        headers=HEADERS, # i'm a real boy mom! 
        verify=False, # yes i know this is unsafe this won't be false in production. 
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    return None
# a function that takes the data we have now, see all the .get stuff, and turns it into a CuentaProduct for quality of life
# taking the large messy data json response from the api's and converting it into clean standarized pythonic (if that's a word) object listed under CuentaProduct that my engine will be able to use
def parse_to_cuenta_product(raw_data: dict) -> Optional[CuentaProduct]:
    try: 
        product = raw_data.get('data', {}).get('product', {})
        item = product.get('item', {})
        price_data = product.get('price', {})
        nutrition = item.get('enrichment', {}).get('nutrition_facts', {})

        tcin = product.get('tcin')
        title = html.unescape(item.get('product_description', {}).get('title', 'Unknown')) # this is a change that will get overlooked, but fresh meat doesn't have nutrition data! 
        brand = item.get('primary_brand', {}).get('name')
        barcode = item.get('primary_barcode')
        
        price_str = price_data.get('formatted_current_price', '$0')
        price = float(re.sub(r'[^\d.]', '', price_str) or 0)
        unit_price = price_data.get('formatted_unit_price')
        
        department = item.get('merchandise_classification', {}).get('department_name', '')
        category_name = product.get('category', {}).get('name', '')
        category = infer_category(department, category_name)
        
        calories = 0
        protein = 0.0
        serving_size = "1 serving"
        servings = 1.0
        ingredients = ""
        
        if nutrition:
            ingredients = nutrition.get('ingredients', '')
            prepared_list = nutrition.get('value_prepared_list', [])
            
            if prepared_list:
                prep = prepared_list[0]
                
                # this dtermines if the product has 1 serving or 10 servings, which is vital since most people can't seem to make this distinction themselves 
                ss = prep.get('serving_size', '')
                ss_unit = prep.get('serving_size_unit_of_measurement', '')
                if ss:
                    serving_size = f"{ss} {ss_unit}".strip()
                
                spc = prep.get('servings_per_container')
                if spc:
                    spc_clean = re.sub(r'[^\d.]', '', str(spc)) # this is a bug fix the commits won't ever see since I tested it on local, but this makes it handle anything like "about 7" in terms of servings
                    if spc_clean:
                        servings = float(spc_clean)
                
                # Nutrients
                for nutrient in prep.get('nutrients', []):
                    name = nutrient.get('name', '').lower()
                    quantity = nutrient.get('quantity', 0) or 0
                    
                    if 'calorie' in name:
                        calories = int(quantity)
                    elif name == 'protein':
                        protein = float(quantity)
        
        # Tags
        tags = infer_tags(title, category_name, ingredients)
        
        return CuentaProduct(
            name=title,
            price=price,
            calories=calories,
            protein=protein,
            serving_size=serving_size,
            servings=servings,
            category=category,
            tags=tags,
            tcin=tcin,
            brand=brand,
            unit_price=unit_price,
            barcode=barcode,
        )
        # this is such a helpful thing i've learned to add, if a non food item in this case accidentally is fetched, the app won't break. all it takes is wrapping the function in a try..except block instead of breaking the entire script which is an issue i've had this ENTIRE project
    except Exception as e:
        print(f"Error parsing product: {e}")
        return None

# this is a continuation, this function is used to find the intial list of products based on a single keyword search, mimicking (however you spell that word) the target search bar
# basically a data harvesting step
def search_products(query: str, store_id: str = "3375", count: int = 24) -> List[dict]:
    api_key = get_api_key()
    
    params = {
        'key': api_key,
        'channel': 'WEB',
        'count': count,
        'default_purchasability_filter': 'true', #this will be huge, none of that out of stock bs
        'keyword': query,
        'offset': 0,
        'page': f'/s/{query}',
        'pricing_store_id': store_id,
        'store_ids': store_id, # simiarly, crucial for double checking that the search results returned are in stock and priced for the location where the user will be shopping 
        'visitor_id': 'guest', # mom i am a real boy!
    }
    
    response = requests.get(
        'https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2',
        params=params,
        headers=HEADERS,
        verify=False, # fix later
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('data', {}).get('search', {}).get('products', [])
    return []
# really self explan
def get_stores_near_zip(zip_code: str, limit: int = 5) -> List[dict]:
    api_key = get_api_key()
    
    params = {
        'key': api_key,
        'zip': zip_code,
        'limit': limit,
        'within': 50,
    }
    
    response = requests.get(
        'https://redsky.target.com/redsky_aggregations/v1/web/nearby_stores_v1',
        params=params,
        headers=HEADERS,
        verify=False,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('data', {}).get('nearby_stores', {}).get('stores', [])
    return []
# one liners are so nice to write. I will say it. 
def fetch_cuenta_product(tcin: str, store_id: str = "3375") -> Optional[CuentaProduct]: # this control function puts ti all together and it's so satisfying
    raw = fetch_product(tcin, store_id) # 
    if raw: # if successful, send it to the cleaner
        return parse_to_cuenta_product(raw)
    return None
# returns a clean CuentaProduct, if anything fails it just returns none 
# below is mostly a code gen tool, a tester if you will 
def export_for_server(products: List[CuentaProduct]) -> str:
    lines = ["# Target products - auto-generated", "TARGET_PRODUCTS = ["]
    
    for p in products:
        tags_str = "{" + ", ".join(f'"{t}"' for t in sorted(p.tags)) + "}"
        lines.append(f'''    Product(
        name="{p.name}",
        price={p.price:.2f},
        calories={p.calories},
        protein={p.protein:.1f},
        serving_size="{p.serving_size}",
        servings={p.servings:.1f},
        category="{p.category}",
        tags={tags_str},
    ),''')
    
    lines.append("]")
    return "\n".join(lines)


# =============================================================================
# MAIN - DEMO
# =============================================================================

if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("CUENTA TARGET SCRAPER")
    print("=" * 60)
    
    # High-protein products to scrape for Cuenta MVP
    HIGH_PROTEIN_TCINS = [
        "12945916",  # Oscar Mayer Turkey Bacon
        "86676070",  #  Fresh All Natural Boneless &#38; Skinless Chicken
        "54084681",  # Tyson Trimmed &#38; Ready Boneless &#38; Skinless
        "90902730",  # Wild Planet Organic Roasted Chicken Breast 
        "1006039739",  # ButcherBox - Organic Chicken Breast Bundle - Froze
    ]
    
    api_key = get_api_key()
    
    products = []
    
    for tcin in HIGH_PROTEIN_TCINS:        
        try:
            product = fetch_cuenta_product(tcin)
            
            if product:
                products.append(product)
                print(f"  ✓ {product.name[:50]}")
                print(f"    ${product.price:.2f} | {product.calories} cal | {product.protein}g protein")
                print(f"    Protein/$: {product.protein_per_dollar:.2f}g/$")
                print(f"    Tags: {product.tags}")
            else:
                print(" Could not fetch product ") # I GUESSS i won't use a formatted string here
                
        except Exception as e:
            print(f" Error: {e}")
        
        time.sleep(1)  # added this to really double down on the whole, don't think i'm a ddoser "i'm a real boy mom"! thing 
    
    # Export for server.py
    if products:
        print("\n" + "=" * 60)
        print("EXPORT FOR SERVER.PY")
        print("=" * 60)
        print(export_for_server(products))
    
    print("\n" + "=" * 60)
    print(f" Fetched {len(products)} products.")
    print("=" * 60)