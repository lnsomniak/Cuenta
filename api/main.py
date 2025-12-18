from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import httpx  # For async HTTP calls to Spoonacular
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

if not SPOONACULAR_API_KEY:
    try:
        from api.scrapers.recipe_cache import SPOONACULAR_API_KEY as SPOON_KEY
        SPOONACULAR_API_KEY = SPOON_KEY
    except ImportError:
        SPOONACULAR_API_KEY = None

# really big lines that say, connect. 
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        HAS_SUPABASE = True
        print(" Connected to Supabase")
    else:
        HAS_SUPABASE = False
        print(" Supabase credentials not found smart guy")
except ImportError:
    HAS_SUPABASE = False
    print(" You aren't the brightest huh. ")

app = FastAPI(title="Cuenta API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# safely extracts integer value from LP variable, let it be known sonarqube I HATE YOU. 
# =============================================================================
# MODELS
# =============================================================================

class OptimizeRequest(BaseModel):
    budget: float = Field(default=75.0, ge=20, le=500)
    daily_calories: int = Field(default=2000, ge=1200, le=5000)
    daily_protein: int = Field(default=150, ge=50, le=400)
    max_per_product: int = Field(default=3, ge=1, le=10)
    diet: Optional[str] = Field(default=None, description="Dietary restriction (Vegan, Vegetarian, Pescatarian, Keto)")
    allergies: List[str] = Field(default=[], description="List of allergies to exclude")
    university_name: Optional[str] = Field(default=None)  
    selected_store: Optional[str] = Field(default=None)  


class BasketItem(BaseModel):
    id: str
    name: str
    quantity: int
    unit_price: float
    total_price: float
    total_protein: float
    total_calories: float
    fitness_score: float
    reason: str
    category: str

# my mock data GONE!!!
# =============================================================================
# TAG MAPPINGS
# =============================================================================

DIET_EXCLUDE_TAGS = {
    "Vegan": ["meat", "poultry", "fish", "dairy", "eggs"],
    "Vegetarian": ["meat", "poultry", "fish"],
    "Pescatarian": ["meat", "poultry"],
    "Keto": ["high_carb", "legume"],
}

ALLERGY_TAG_MAP = {
    "Dairy": ["dairy"],
    "Eggs": ["eggs"],
    "Gluten": ["gluten"],
    "Nuts": ["nuts"],
    "Soy": ["soy"],
    "Fish": ["fish"],
}


def get_products_from_supabase(
    diet: Optional[str] = None,
    allergies: Optional[List[str]] = None,
    store_chain: Optional[str] = None,
) -> List[dict]:    
    if not HAS_SUPABASE or supabase is None:
        return get_fallback_products()
    
    try:
        # Base query - only products with nutrition data
        query = supabase.table("products").select("*").gt("protein", 0).gt("price", 0)
        result = query.order("protein_per_dollar", desc=True).limit(500).execute()
        
        if not result.data:
            print("No products found in Supabase")
            return get_fallback_products()
        
        products = result.data
        print(f"✓ Loaded {len(products)} products from Supabase")
        
        # Apply diet filter
        if diet and diet in DIET_EXCLUDE_TAGS:
            exclude_tags = DIET_EXCLUDE_TAGS[diet]
            products = [
                p for p in products
                if not any(tag in (p.get("tags") or []) for tag in exclude_tags)
            ]
            print(f"  After {diet} filter: {len(products)} products")
        
        # Apply allergy filters
        if allergies:
            for allergy in allergies:
                if allergy in ALLERGY_TAG_MAP:
                    exclude_tags = ALLERGY_TAG_MAP[allergy]
                    products = [
                        p for p in products
                        if not any(tag in (p.get("tags") or []) for tag in exclude_tags)
                    ]
            print(f"  After allergy filters: {len(products)} products")
        
        return products
        
    except Exception as e:
        print(f"Supabase error: {e}")
        return get_fallback_products()

# most common things i've seen that need a fallback
def get_fallback_products() -> List[dict]:
    return [
        {
            "id": "fallback-1",
            "name": "Chicken Breast (fallback)",
            "price": 8.99,
            "protein": 31,
            "calories": 165,
            "servings_per_container": 4,
            "category": "meat",
            "tags": ["meat", "poultry"],
        },
        {
            "id": "fallback-2", 
            "name": "Greek Yogurt (fallback)",
            "price": 5.99,
            "protein": 17,
            "calories": 100,
            "servings_per_container": 4,
            "category": "dairy",
            "tags": ["dairy"],
        },
        {
            "id": "fallback-3",
            "name": "Eggs 12ct (fallback)",
            "price": 3.99,
            "protein": 6,
            "calories": 70,
            "servings_per_container": 12,
            "category": "eggs",
            "tags": ["eggs"],
        },
    ]
    
# =============================================================================
# OPTIMIZATION LOGIC
# =============================================================================

def optimize_basket(
    products: List[dict],
    budget: float,
    daily_calories: int,
    daily_protein: int,
    max_per_product: int = 3,
) -> dict:
    
    weekly_protein_target = daily_protein * 7
    weekly_calorie_target = daily_calories * 7
    
    # Score products by protein efficiency
    scored_products = []
    for p in products:
        price = p.get("price", 0)
        protein_per_serving = p.get("protein", 0)
        calories_per_serving = p.get("calories", 0)
        servings = p.get("servings_per_container", 1) or 1
        
        if price <= 0 or protein_per_serving <= 0:
            continue
        
        total_protein = protein_per_serving * servings
        total_calories = calories_per_serving * servings
        protein_per_dollar = total_protein / price
        
        scored_products.append({
            **p,
            "total_protein": total_protein,
            "total_calories": total_calories,
            "protein_per_dollar": protein_per_dollar,
            "score": protein_per_dollar,  
        })
    
    # neat  and sorts by protein efficiency
    scored_products.sort(key=lambda x: x["score"], reverse=True)
# greed is a sin     
    basket = []
    total_cost = 0
    total_protein = 0
    total_calories = 0
    selected_ids = {}
    
    for product in scored_products:
        product_id = product.get("id") or product.get("external_id") or product["name"]
        price = product["price"]
        
        # Check constraints
        if selected_ids.get(product_id, 0) >= max_per_product:
            continue
        
        if total_cost + price > budget:
            continue
        
        # Add to basket
        qty = selected_ids.get(product_id, 0) + 1
        selected_ids[product_id] = qty
        
        total_cost += price
        total_protein += product["total_protein"]
        total_calories += product["total_calories"]
        
        # Check if already in basket
        existing = next((item for item in basket if item["id"] == product_id), None)
        if existing:
            existing["quantity"] += 1
            existing["total_price"] = existing["quantity"] * existing["unit_price"]
            existing["total_protein"] = existing["quantity"] * product["total_protein"]
            existing["total_calories"] = existing["quantity"] * product["total_calories"]
        else:
            basket.append({
                "id": product_id,
                "name": product["name"],
                "quantity": 1,
                "unit_price": price,
                "total_price": price,
                "total_protein": product["total_protein"],
                "total_calories": product["total_calories"],
                "fitness_score": product["score"],
                "reason": f"{product['score']:.1f}g protein per dollar",
                "category": product.get("category", "other"),
            })
        
        # Stop if we've hit targets and therefore don't need more
        if total_protein >= weekly_protein_target and total_calories >= weekly_calorie_target * 0.8:
            break
    # good to calculate budget util
    budget_util = (total_cost / budget * 100) if budget > 0 else 0
    calorie_achievement = (total_calories / weekly_calorie_target * 100) if weekly_calorie_target > 0 else 0
    
    return {
        "success": True,
        "status": "optimized",
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_protein": round(total_protein, 1),
            "total_calories": round(total_calories, 0),
            "budget": budget,
            "calorie_target": weekly_calorie_target,
            "budget_utilization": f"{budget_util:.1f}%",
            "calorie_achievement": f"{calorie_achievement:.1f}%",
        },
        "items": basket,
    }

# =============================================================================
# API ROUTES
# =============================================================================

@app.get("/")
def root():
    return {
        "service": "Cuenta API",
        "version": "2.0",
        "database": "supabase" if HAS_SUPABASE else "fallback",
        "spoonacular": "configured" if SPOONACULAR_API_KEY else "not configured",
        "status": "healthy",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "connected" if HAS_SUPABASE else "fallback"}


@app.get("/api/products")
def get_products(
    category: Optional[str] = None,
    limit: int = 50,
):
    products = get_products_from_supabase()
    
    if category and category != "all":
        products = [p for p in products if p.get("category") == category]
    
    return {
        "success": True,
        "count": len(products[:limit]),
        "products": products[:limit],
    }


@app.post("/api/optimize")
def optimize(request: OptimizeRequest):
    products = get_products_from_supabase(
        diet=request.diet,
        allergies=request.allergies,
        store_chain=request.selected_store,
    )
    
    if not products:
        raise HTTPException(status_code=404, detail="No products available")
    
    result = optimize_basket(
        products=products,
        budget=request.budget,
        daily_calories=request.daily_calories,
        daily_protein=request.daily_protein,
        max_per_product=request.max_per_product,
    )
    
    return result


@app.get("/api/categories")
def get_categories():
    products = get_products_from_supabase()
    categories = list(set(p.get("category", "other") for p in products))
    return {"categories": sorted(categories)}

# =============================================================================
# RECIPE ROUTES (Spoonacular)
# =============================================================================    
    
@app.get("/api/recipes/from-ingredients")
async def recipes_from_ingredients(
    ingredients: List[str] = Query(default=[]),
    number: int = Query(default=5, ge=1, le=10)
):
    if not SPOONACULAR_API_KEY:
        raise HTTPException(status_code=500, detail="SPOONACULAR_API_KEY not configured")
    
    if not ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spoonacular.com/recipes/findByIngredients",
            params={
                "ingredients": ",".join(ingredients),
                "number": number,
                "ranking": 2,
                "apiKey": SPOONACULAR_API_KEY
            }
        )
        data = resp.json()
    
    return {
        "ingredients": ingredients,
        "count": len(data),
        "recipes": [
            {
                "id": r["id"],
                "title": r["title"],
                "image": r.get("image"),
                "usedIngredients": [i["name"] for i in r.get("usedIngredients", [])],
                "missedIngredients": [i["name"] for i in r.get("missedIngredients", [])],
            }
            for r in data
        ]
    }

@app.get("/api/recipes/search")
async def search_recipes(
    query: str,
    number: int = Query(default=5, ge=1, le=10)
):
    if not SPOONACULAR_API_KEY:
        raise HTTPException(status_code=500, detail="SPOONACULAR_API_KEY not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params={
                "query": query,
                "number": number,
                "addRecipeNutrition": True,
                "apiKey": SPOONACULAR_API_KEY
            }
        )
        data = resp.json()
    
    results = []
    for r in data.get("results", []):
        nutrition = r.get("nutrition", {})
        nutrients = {n["name"]: n["amount"] for n in nutrition.get("nutrients", [])}
        results.append({
            "id": r["id"],
            "title": r["title"],
            "image": r.get("image"),
            "calories": round(nutrients.get("Calories", 0)),
            "protein": round(nutrients.get("Protein", 0)),
        })
    
    return {"query": query, "count": len(results), "recipes": results}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print(f"   Database: {'Supabase' if HAS_SUPABASE else 'Fallback'}")
    print(f"   Spoonacular: {'Configured' if SPOONACULAR_API_KEY else 'Not configured'}")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs (Swagger UI)")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True) # love reload =true
