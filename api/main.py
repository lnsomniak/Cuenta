## FastAPI server that exposes the optimization engine, once again. In theory. S
from fastapi import FastAPI, HTTPException, Query # query saved me from sonarqube annoying alerts idk why i have it installed
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
import os
import httpx

from optimizer import OptimizationEngine

load_dotenv()

SPOONACULAR_KEY = os.getenv("SPOONACULAR_API_KEY")
SPOONACULAR_BASE = "https://api.spoonacular.com"

app = FastAPI(
    title="Cuenta API",
    description="Grocery optimization for fitness goals",
    version="0.1.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://cuenta-mu.vercel.app",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = OptimizationEngine()

class OptimizeRequest(BaseModel):
    budget: float = Field(default=75.0, ge=20, le=500)
    daily_calories: int = Field(default=2000, ge=1200, le=5000)
    daily_protein: Optional[int] = Field(default=None, ge=50, le=400)
    max_per_product: int = Field(default=3, ge=1, le=10)

# fixed these completely so they can actually request data from a database 
class MealPlanRequest(BaseModel):
    budget: float = Field(default=75.0, ge=20, le=500)
    daily_calories: int = Field(default=2000, ge=1200, le=5000)
    daily_protein: int = Field(default=150, ge=50, le=400)


async def spoonacular_request(endpoint: str, params: dict) -> dict:
    if not SPOONACULAR_KEY:
        raise HTTPException(status_code=500, detail="SPOONACULAR_API_KEY not configured")
    
    params["apiKey"] = SPOONACULAR_KEY
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SPOONACULAR_BASE}{endpoint}", params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Spoonacular error: {resp.text}")
        return resp.json()

# clean the data before the real data gets cleaned
def extract_ingredient_names(product_names: list[str]) -> list[str]:
    ingredients = []
    for name in product_names:
        # Remove brand names and weights
        clean = name.lower()
        # Common ALDI brand removals, can get edited if any go through 
        for brand in ["kirkwood", "friendly farms", "simply nature", "goldhen", "dakota's pride", 
                    "southern grove", "happy farms", "fremont fish market", "millville", 
                "elevation", "never any!", "appleton farms", "l'oven fresh"]:
            clean = clean.replace(brand, "")
        # Remove weight/count info
        import re
        clean = re.sub(r'\([^)]*\)', '', clean)  # Remove parentheses content
        clean = re.sub(r'\d+\s*(oz|lb|ct|count)', '', clean)  # Remove measurements
        clean = clean.strip()
        if clean: #  <- peep game 
            ingredients.append(clean)
    return ingredients

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "0.1.0",
        "spoonacular_configured": bool(SPOONACULAR_KEY)
    }
    
@app.post("/api/optimize")
async def optimize_basket(request: OptimizeRequest):
    try:
        result = engine.optimize(
            budget=request.budget,
            calorie_target=request.daily_calories,
            protein_target=request.daily_protein,
            max_per_product=request.max_per_product
        )
        if not result.success:
            raise HTTPException(status_code=400, detail=result.status)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products")
async def list_products(): # list all products possible 
    try:
        products = engine.fetch_products()
        return {
            "count": len(products),
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "calories": p.calories,
                    "protein": p.protein,
                    "protein_per_dollar": round(p.protein_per_dollar, 2),
                    "category": p.category,
                }
                for p in sorted(products, key=lambda x: x.protein_per_dollar, reverse=True)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# api/recipes.py

@app.get("/api/recipes/from-ingredients")
async def recipes_from_ingredients(
    ingredients: list[str] = Query(default=[], description="List of ingredient names"),
    number: int = Query(default=5, ge=1, le=10)
):
# this is the first flow i'm adding, essentially an answer to the first and main operation we need.
# passes ingredient names depsite format
    if not ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")
    # edge case ^
    # Clean ingredient names after recieving
    clean_ingredients = extract_ingredient_names(ingredients)
    data = await spoonacular_request("/recipes/findByIngredients", {
        "ingredients": ",".join(clean_ingredients),
        "number": number,
        "ranking": 2,  # Maximize used ingredients
        "ignorePantry": True
    })
    
    # Enrich with nutrition info read
    recipe_ids = [r["id"] for r in data]
    if recipe_ids:
        nutrition_data = await spoonacular_request("/recipes/informationBulk", {
            "ids": ",".join(map(str, recipe_ids)),
            "includeNutrition": True
        })
        nutrition_map = {r["id"]: r for r in nutrition_data}
    else:
        nutrition_map = {}
    
    results = []
    for recipe in data:
        rid = recipe["id"]
        info = nutrition_map.get(rid, {})
        nutrition = info.get("nutrition", {})
        nutrients = {n["name"]: n["amount"] for n in nutrition.get("nutrients", [])}
        
        results.append({
            "id": rid,
            "title": recipe["title"],
            "image": recipe.get("image"),
            "usedIngredients": [i["name"] for i in recipe.get("usedIngredients", [])],
            "missedIngredients": [i["name"] for i in recipe.get("missedIngredients", [])],
            "usedCount": recipe.get("usedIngredientCount", 0),
            "missedCount": recipe.get("missedIngredientCount", 0),
            "readyInMinutes": info.get("readyInMinutes"),
            "servings": info.get("servings"),
            "nutrition": {
            "calories": round(nutrients.get("Calories", 0)),
            "protein": round(nutrients.get("Protein", 0)),
            "carbs": round(nutrients.get("Carbohydrates", 0)),
                "fat": round(nutrients.get("Fat", 0)),
            }
        })
    
    return {
        "searchedIngredients": clean_ingredients,
        "count": len(results),
        "recipes": results
    }


@app.get("/api/recipes/search")
async def search_recipes(
    query: str,
    max_calories: Optional[int] = None,
    min_protein: Optional[int] = None,
    number: int = Query(default=5, ge=1, le=10)
):
#    Search recipes with optional macro filters
    params = {
        "query": query,
        "number": number,
        "addRecipeNutrition": True
    }
    
    if max_calories:
        params["maxCalories"] = max_calories
    if min_protein:
        params["minProtein"] = min_protein
    
    data = await spoonacular_request("/recipes/complexSearch", params)
    
    results = []
    for recipe in data.get("results", []):
        nutrition = recipe.get("nutrition", {})
        nutrients = {n["name"]: n["amount"] for n in nutrition.get("nutrients", [])}
        
        results.append({
            "id": recipe["id"],
            "title": recipe["title"],
            "image": recipe.get("image"),
            "readyInMinutes": recipe.get("readyInMinutes"),
            "servings": recipe.get("servings"),
            "nutrition": {
                "calories": round(nutrients.get("Calories", 0)),
                "protein": round(nutrients.get("Protein", 0)),
                "carbs": round(nutrients.get("Carbohydrates", 0)),
                "fat": round(nutrients.get("Fat", 0)),
            }
        })
    
    return {
        "query": query,
        "count": len(results),
        "recipes": results
    }


@app.post("/api/meal-plan/generate")
async def generate_meal_plan(request: MealPlanRequest):
    # generates a meal plan based off information we have at our disposal and pre-organized thanks to the functions written above
    data = await spoonacular_request("/mealplanner/generate", {
        "timeFrame": "day",
        "targetCalories": request.daily_calories,
    })
    
    # this just gets all the nutrition details for each meal 
    meal_ids = [meal["id"] for meal in data.get("meals", [])]
    if meal_ids:
        details = await spoonacular_request("/recipes/informationBulk", {
            "ids": ",".join(map(str, meal_ids)),
            "includeNutrition": True
        })
        details_map = {r["id"]: r for r in details}
    else:
        details_map = {}
    
    meals = []
    for meal in data.get("meals", []):
        info = details_map.get(meal["id"], {})
        nutrition = info.get("nutrition", {})
        nutrients = {n["name"]: n["amount"] for n in nutrition.get("nutrients", [])}
        
        meals.append({
            "id": meal["id"],
            "title": meal["title"],
            "readyInMinutes": meal.get("readyInMinutes"),
            "servings": meal.get("servings"),
            "sourceUrl": meal.get("sourceUrl"),
            "nutrition": {
                "calories": round(nutrients.get("Calories", 0)),
                "protein": round(nutrients.get("Protein", 0)),
                "carbs": round(nutrients.get("Carbohydrates", 0)),
                "fat": round(nutrients.get("Fat", 0)),
            }
        })
    
    # Calculate totals, nutrients and {}
    totals = data.get("nutrients", {})
    
    return {
        "meals": meals,
        "totals": {
            "calories": round(totals.get("calories", 0)),
            "protein": round(totals.get("protein", 0)),
            "carbs": round(totals.get("carbohydrates", 0)),
            "fat": round(totals.get("fat", 0)),
        }
    }
# return the tatals to be read off

if __name__ == "__main__": # testing 
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
