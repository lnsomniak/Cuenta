import os
import pulp
import httpx
from typing import Optional, cast
from dotenv import load_dotenv
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus, value as lp_value # ez fix but not so easy fix to lines 36 and 168

load_dotenv()
SPOONACULAR_KEY = os.getenv("SPOONACULAR_API_KEY")

# Suppress solver output
if pulp.LpSolverDefault is not None:
    pulp.LpSolverDefault.msg = False

app = FastAPI(
    title="Cuenta API",
    description="Grocery optimization for fitness goals",
    version="0.1.0"
)

# CORS - Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# safely extracts integer value from LP variable, let it be known sonarqube I HATE YOU. 
def get_qty(var: LpVariable) -> int:
    val = lp_value(var)
    if val is None:
        return 0
    return int(cast(float, val))

@dataclass
class Product:
    id: str
    name: str
    price: float
    calories: int
    protein: float
    carbs: float
    fat: float
    servings: float
    category: str
    tags: list[str] = field(default_factory=list) # <--- NEW: New tags for allergies & specific diets
    # itroducing ingredienties property
    @property
    def total_calories(self) -> int:
        return int(self.calories * self.servings)
    
    @property
    def total_protein(self) -> float:
        return self.protein * self.servings
    
    @property
    def protein_per_dollar(self) -> float:
        return self.total_protein / self.price if self.price > 0 else 0


class OptimizeRequest(BaseModel):
    budget: float = Field(default=75.0, ge=20, le=500)
    daily_calories: int = Field(default=2000, ge=1200, le=5000)
    daily_protein: Optional[int] = Field(default=150, ge=50, le=400)
    max_per_product: Optional[int] = Field(default=3, ge=1, le=10)
    allergies: list[str] = Field(default=[], description="List of product categories/ingredients to exclude") # New Allergy field, thank you adamaris
    diet: Optional[str] = Field(default=None, description="Single dietary restriction (e.g., 'Vegan', 'Keto')")

# mock data, should be same as seed.sql

PRODUCTS = [
    Product("1", "Kirkwood Chicken Breast (3 lb)", 8.99, 120, 26, 0, 1.5, 12, "Protein", tags=["meat", "poultry", "low_fat"]),
    Product("2", "Kirkwood Chicken Thighs (3 lb)", 5.99, 180, 22, 0, 10, 12, "Protein", tags=["meat", "poultry", "high_fat"]),
    Product("3", "Never Any! Ground Turkey 93/7", 5.49, 170, 21, 0, 9, 4, "Protein", tags=["meat", "poultry"]),
    Product("4", "Fresh Ground Beef 80/20", 5.99, 290, 19, 0, 23, 4, "Protein", tags=["meat", "beef", "high_fat"]),
    Product("5", "Fresh Ground Beef 93/7", 6.99, 170, 22, 0, 9, 4, "Protein", tags=["meat", "beef", "low_fat"]),
    Product("6", "Fremont Fish Market Tilapia (2 lb)", 7.99, 110, 23, 0, 2, 8, "Protein", tags=["fish", "low_fat"]),
    Product("7", "Fremont Fish Market Salmon", 8.99, 180, 25, 0, 8, 4, "Protein", tags=["fish", "omega3", "healthy_fat"]),
    Product("8", "Appleton Farms Bacon (16 oz)", 5.49, 80, 6, 0, 6, 16, "Protein", tags=["meat", "pork", "processed", "high_fat"]),
    Product("9", "Goldhen Large Eggs (18 ct)", 3.29, 70, 6, 0, 5, 18, "Dairy", tags=["dairy", "eggs", "protein"]),
    Product("10", "Goldhen Large Eggs (36 ct)", 5.99, 70, 6, 0, 5, 36, "Dairy", tags=["dairy", "eggs", "protein"]),
    Product("11", "Friendly Farms Greek Yogurt (32 oz)", 4.49, 100, 17, 6, 0, 4, "Dairy", tags=["dairy", "probiotic", "low_fat", "protein"]),
    Product("12", "Friendly Farms Cottage Cheese (24 oz)", 2.99, 110, 13, 5, 4, 6, "Dairy", tags=["dairy", "probiotic", "low_fat", "protein"]),
    Product("13", "Happy Farms String Cheese (24 ct)", 6.99, 80, 7, 1, 6, 24, "Dairy", tags=["dairy", "snack", "protein"]),
    Product("14", "Friendly Farms Whole Milk (gallon)", 3.49, 150, 8, 12, 8, 16, "Dairy", tags=["dairy", "calcium", "high_fat"]),
    Product("15", "Simply Nature Brown Rice (2 lb)", 3.29, 170, 4, 35, 1.5, 18, "Grains", tags=["gluten_free", "high_carb", "high_fiber"]),
    Product("16", "Jasmine Rice (5 lb)", 5.99, 160, 3, 36, 0, 45, "Grains", tags=["gluten_free", "high_carb"]),
    Product("17", "Barilla Pasta (16 oz)", 1.29, 200, 7, 42, 1, 8, "Grains", tags=["gluten", "high_carb", "wheat"]),
    Product("18", "L'Oven Fresh Whole Wheat Bread", 1.99, 70, 4, 13, 1, 20, "Grains", tags=["gluten", "high_fiber", "wheat"]),
    Product("19", "Millville Old Fashioned Oats (42 oz)", 2.99, 150, 5, 27, 3, 30, "Grains", tags=["gluten_free", "high_fiber", "breakfast"]),
    Product("20", "Tortillas Flour (10 ct)", 2.29, 140, 3, 24, 3, 10, "Grains", tags=["gluten", "high_carb", "wheat"]),
    Product("21", "Bananas (bunch)", 1.49, 105, 1, 27, 0, 7, "Produce", tags=["fruit", "potassium", "high_carb"]),
    Product("22", "Sweet Potatoes (3 lb bag)", 2.99, 112, 2, 26, 0, 5, "Produce", tags=["vegetable", "vitamin_a", "high_carb"]),
    Product("23", "Russet Potatoes (5 lb bag)", 2.99, 160, 4, 37, 0, 8, "Produce", tags=["vegetable", "high_carb", "versatile"]),
    Product("24", "Baby Spinach (16 oz)", 3.99, 7, 1, 1, 0, 16, "Produce", tags=["leafy_green", "iron", "low_carb"]),
    Product("25", "Broccoli Crowns (per lb)", 1.69, 55, 4, 11, 0, 3, "Produce", tags=["vegetable", "vitamin_c", "high_fiber"]),
    Product("26", "Frozen Broccoli (12 oz)", 1.29, 30, 3, 6, 0, 3, "Produce", tags=["vegetable", "vitamin_c", "frozen", "high_fiber"]),
    Product("27", "Frozen Mixed Vegetables (12 oz)", 1.19, 60, 2, 12, 0, 3, "Produce", tags=["vegetable", "frozen", "mixed", "convenient"]),
    Product("28", "Avocados (each)", 0.89, 234, 3, 12, 21, 1, "Produce", tags=["fruit", "healthy_fat", "fiber"]),
    Product("29", "Dakota's Pride Black Beans (15 oz)", 0.79, 110, 7, 20, 0, 3.5, "Legumes", tags=["legume", "protein", "fiber", "canned"]),
    Product("30", "Dakota's Pride Pinto Beans (15 oz)", 0.79, 110, 6, 20, 0, 3.5, "Legumes", tags=["legume", "protein", "fiber", "canned"]),
    Product("31", "Dakota's Pride Chickpeas (15 oz)", 0.89, 120, 6, 20, 2, 3.5, "Legumes", tags=["legume", "protein", "fiber", "canned"]),
    Product("32", "Simply Nature Lentils (16 oz)", 2.49, 170, 12, 30, 0, 13, "Legumes", tags=["legume", "protein", "fiber", "iron"]),
    Product("33", "Southern Grove Peanut Butter (28 oz)", 3.49, 190, 7, 7, 16, 26, "Legumes", tags=["legume", "healthy_fat", "protein", "spread"]),
    Product("34", "Simply Nature Organic Tofu (14 oz)", 2.29, 90, 10, 2, 5, 4.5, "Legumes", tags=["soy", "protein", "vegetarian", "vegan"]),
    Product("35", "Elevation Protein Bars (5 ct)", 5.99, 200, 20, 22, 7, 5, "Snacks", tags=["protein", "snack", "convenient"]),
    Product("36", "Southern Grove Almonds (16 oz)", 5.99, 170, 6, 6, 15, 16, "Snacks", tags=["tree_nuts", "nuts", "healthy_fat", "snack"]),
    Product("37", "SimplyNature Almond Milk (64 oz)", 2.79, 30, 1, 1, 2.5, 8, "Dairy", tags=["dairy_alternative", "vegan", "low_calorie", "nut_milk"]),
]
# followed by more logic to futher optimize
def calculate_fitness_score(product: Product) -> float:
    protein_score = min(product.protein_per_dollar * 2, 50)
    cal_per_dollar = product.total_calories / product.price
    calorie_score = min(cal_per_dollar / 50, 20)
    bonuses = {"Protein": 30, "Dairy": 20, "Legumes": 25, "Grains": 15, "Produce": 10, "Snacks": 5}
    category_score = bonuses.get(product.category, 10)
    return protein_score + calorie_score + category_score

def get_selection_reason(product: Product, score: float) -> str:
    if product.protein_per_dollar > 10:
        return f"Exceptional protein value ({product.protein_per_dollar:.1f}g/$)"
    elif product.protein_per_dollar > 5:
        return f"Strong protein/$ ratio ({product.protein_per_dollar:.1f}g/$)"
    elif product.category == "Produce":
        return "Essential micronutrients & fiber"
    elif product.category == "Grains":
        return "Cost-effective energy source"
    elif product.category == "Dairy":
        return "Complete protein + calcium"
    else:
        return f"Good overall value (score: {score:.0f})"
    
DIET_EXCLUSION_MAP = {
    "Vegan": ["meat", "poultry", "fish", "dairy", "eggs", "pork"],
    "Vegetarian": ["meat", "poultry", "fish", "pork"],
    "Pescatarian": ["meat", "poultry", "pork"], # Allows fish
    "Keto": ["high_carb", "grains", "sugar", "fruit"], # Focusing on removing high-carb items
}

# --- ALLERGY MAPPING ---
# Map common allergy strings (from the frontend dropdown) to your product tags.
ALLERGY_TAG_MAP = {
    "Dairy": ["dairy", "milk"],
    "Eggs": ["eggs"],
    "Gluten": ["gluten", "wheat"],
    "Nuts": ["nuts", "tree_nuts"],
    "Soy": ["soy"], 
    "Fish": ["fish"],
}

def run_optimization(
    budget: float, 
    daily_calories: int, 
    daily_protein: int, 
    max_per_product: int,
    allergies: list[str],
    diet: Optional[str] 
):
    
    available_products = PRODUCTS
    EXCLUSION_TAGS = set()
    
# --- Step 1: Apply DIET Filters (Mapping Diet to Tags) ---
    if diet and diet in DIET_EXCLUSION_MAP:
            EXCLUSION_TAGS.update(DIET_EXCLUSION_MAP[diet])

        # 2. Apply ALLERGY Filters (Mapping Allergies to Exclusion Tags)
    for allergy_key in allergies:
            # Normalize the allergy key (e.g., 'dairy' to 'Dairy' for lookup)
        key = allergy_key.capitalize()
        if key in ALLERGY_TAG_MAP:
            EXCLUSION_TAGS.update(ALLERGY_TAG_MAP[key])
            
        # --- Step 3: Filter Products ---
    if EXCLUSION_TAGS:
        available_products = [
            p for p in available_products 
            if not any(tag in EXCLUSION_TAGS for tag in p.tags)
        ]
    # 4. Check for empty list
    if not available_products:
        return None, "All products filtered by restrictions. Please adjust...please."
    
    weekly_calories = daily_calories * 7
    weekly_protein = daily_protein * 7
    
    scores = {p.id: calculate_fitness_score(p) for p in available_products} 
    
    prob = LpProblem("GroceryOptimization", LpMaximize)
# FIX: Defined variables ONLY for available products
    qty = {p.id: LpVariable(f"qty_{p.id}", lowBound=0, upBound=max_per_product, cat="Integer") for p in available_products}
# another fix for same issue
    prob += lpSum(qty[p.id] * p.total_protein * (scores[p.id] / 100) for p in available_products)
    
    # Constraints
    prob += lpSum(qty[p.id] * p.price for p in available_products) <= budget
    prob += lpSum(qty[p.id] * p.total_calories for p in available_products) >= weekly_calories * 0.9
    prob += lpSum(qty[p.id] * p.total_calories for p in available_products) <= weekly_calories * 1.2
    prob += lpSum(qty[p.id] * p.total_protein for p in available_products) >= weekly_protein * 0.8
    
    # Variety
    has = {p.id: LpVariable(f"has_{p.id}", cat="Binary") for p in available_products}
    for p in available_products:
        prob += qty[p.id] <= max_per_product * has[p.id]
    prob += lpSum(has.values()) >= 5
    
    prob.solve()
    
    if LpStatus[prob.status] != "Optimal":
        return None, LpStatus[prob.status]
    
    items = []
    total_cost = 0
    total_protein = 0
    total_calories = 0
    # new implementation ! 
    for p in available_products:
        q = get_qty(qty[p.id])
        if q > 0:
            score = scores[p.id]
            items.append({
                "id": p.id,
                "name": p.name,
                "quantity": q,
                "unit_price": p.price,
                "total_price": round(p.price * q, 2),
                "protein_per_item": round(p.total_protein, 1),
                "total_protein": round(p.total_protein * q, 1),
                "calories_per_item": p.total_calories,
                "total_calories": p.total_calories * q,
                "fitness_score": round(score, 1),
                "reason": get_selection_reason(p, score),
                "category": p.category,
            })
            total_cost += p.price * q
            total_protein += p.total_protein * q
            total_calories += p.total_calories * q
    
    items.sort(key=lambda x: x["fitness_score"], reverse=True)
    
    return {
        "success": True,
        "status": "Optimal solution found",
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_protein": round(total_protein, 1),
            "total_calories": total_calories,
            "budget": budget,
            "calorie_target": weekly_calories,
            "budget_utilization": f"{(total_cost / budget * 100):.1f}%",
            "calorie_achievement": f"{(total_calories / weekly_calories * 100):.1f}%",
        },
        "items": items
    }, "Optimal"
# endpoints and messages for myself
@app.get("/")
async def root():
    return {"message": "Cuenta API is running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0", "mode": "mock_data"}

@app.post("/api/optimize")
async def optimize(request: OptimizeRequest):
    # temp fix hopefully while I make a structure to hopefully start working on the supabase database tonight
    daily_protein_value = request.daily_protein if request.daily_protein is not None else 150
    max_per_product_value = request.max_per_product if request.max_per_product is not None else 3
    # this should fix my object object error, that was appearing because max_per_product wasn't being recieved by the frontend properly. converitng it into an optional integer should make this more viable. 
    result, status = run_optimization(
        budget=request.budget,
        daily_calories=request.daily_calories,
        daily_protein=daily_protein_value,
        max_per_product=max_per_product_value,
        allergies=request.allergies, 
        diet=request.diet
    )
    if result is None:
        raise HTTPException(status_code=400, detail=f"Optimization failed: {status}")
    
    return result

@app.get("/api/products")
async def list_products():
    return {
        "count": len(PRODUCTS),
        "products": sorted(
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "calories": p.calories,
                    "protein": p.protein,
                    "protein_per_dollar": round(p.protein_per_dollar, 2),
                    "category": p.category,
                }
                for p in PRODUCTS
            ],
            key=lambda x: x["protein_per_dollar"],
            reverse=True
        )
    }
    
@app.get("/api/recipes/from-ingredients")
async def recipes_from_ingredients(
    ingredients: list[str] = Query(default=[]),
    number: int = Query(default=5, ge=1, le=10)
):
    if not SPOONACULAR_KEY:
        raise HTTPException(status_code=500, detail="SPOONACULAR_API_KEY not set in .env")
    
    if not ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")
# edge cases thank you codepath ily 
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spoonacular.com/recipes/findByIngredients",
            params={
                "ingredients": ",".join(ingredients),
                "number": number,
                "ranking": 2,
                "apiKey": SPOONACULAR_KEY
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
    if not SPOONACULAR_KEY:
        raise HTTPException(status_code=500, detail="SPOONACULAR_API_KEY not set in .env")#
# search recipes feature, amazing but weird to implement? I love spoonacular  
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params={
                "query": query,
                "number": number,
                "addRecipeNutrition": True,
                "apiKey": SPOONACULAR_KEY
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
# test cases 
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Cuenta API (Mock Data Mode)")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs (Swagger UI)")
    print("\n   Press Ctrl+C to stop\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True) # needed to add reload TRUE 