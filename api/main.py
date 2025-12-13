## FastAPI server that exposes the optimization engine, once again. In theory. S
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os

from optimizer import OptimizationEngine

app = FastAPI(
    title="Fit-Econ API",
    description="Grocery optimization for fitness goals",
    version="0.1.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = OptimizationEngine()

class OptimizeRequest(BaseModel): # the request body, this is where we'll input data 
    budget: float = Field(default=75.0, ge=20, le=500, description="Weekly budget in dollars") 
    daily_calories: int = Field(default=2000, ge=1200, le=5000, description="Daily calorie target")
    daily_protein: Optional[int] = Field(default=None, ge=50, le=400, description="Daily protein target in grams")
    max_per_product: int = Field(default=3, ge=1, le=10, description="Maximum units of any single product")


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "healthy", "version": "0.1.0"} # testing testing 1 2 3


@app.post("/api/optimize") # optimizing a grocery basket for the given parameters, returns an optimal set of products to maximize the protein
async def optimize_basket(request: OptimizeRequest):
    try:
        result = engine.optimize(
            budget=request.budget,
            calorie_target=request.daily_calories,
            protein_target=request.daily_protein,
            max_per_product=request.max_per_product # while staying under budget and meeting caloric needs. 
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


if __name__ == "__main__": # testing 
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
