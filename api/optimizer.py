from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING, cast
import os
from dotenv import load_dotenv
from pulp import (
    LpMaximize,
    LpProblem,
    LpStatus,
    LpVariable,
    lpSum,
    value as lp_value,
)
# I cannot wait to get rid of pulp so much unncesscary things I'd rather work with ANY tree model engine. 
if TYPE_CHECKING:
    from supabase import Client

load_dotenv()

@dataclass
class Product:
    id: str
    name: str
    price: float
    calories: int
    protein: float
    carbs: float
    fat: float
    servings_per_container: float
    protein_per_dollar: float
    category: str

    @property
    def total_calories(self) -> int:
        return int(self.calories * self.servings_per_container)

    @property
    def total_protein(self) -> float:
        return self.protein * self.servings_per_container


@dataclass
class BasketItem:
    product: Product
    quantity: int
    fitness_score: float
    selection_reason: str

    @property
    def total_price(self) -> float:
        return self.product.price * self.quantity

    @property
    def total_protein(self) -> float:
        return self.product.total_protein * self.quantity

    @property
    def total_calories(self) -> int:
        return self.product.total_calories * self.quantity

# results of everything above
@dataclass
class OptimizationResult:
    success: bool
    items: list[BasketItem]
    total_cost: float
    total_protein: float
    total_calories: int
    budget: float
    calorie_target: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "summary": {
                "total_cost": round(self.total_cost, 2),
                "total_protein": round(self.total_protein, 1),
                "total_calories": self.total_calories,
                "budget": self.budget,
                "calorie_target": self.calorie_target,
                "budget_utilization": f"{(self.total_cost / self.budget * 100):.1f}%",
                "calorie_achievement": f"{(self.total_calories / self.calorie_target * 100):.1f}%",
            },
            "items": [
                {
                    "id": item.product.id,
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.product.price,
                    "total_price": round(item.total_price, 2),
                    "protein_per_item": round(item.product.total_protein, 1),
                    "total_protein": round(item.total_protein, 1),
                    "calories_per_item": item.product.total_calories,
                    "total_calories": item.total_calories,
                    "fitness_score": round(item.fitness_score, 1),
                    "reason": item.selection_reason,
                    "category": item.product.category,
                }
                for item in sorted(self.items, key=lambda x: x.fitness_score, reverse=True)
            ],
        }

# telling it, parse a database row into a product with proper type handling pls!
def _parse_product(row: dict[str, Any]) -> Product:
    return Product(
        id=str(row["id"]),
        name=str(row["name"]),
        price=float(row["price"]),
        calories=int(row["calories"]),
        protein=float(row["protein"]),
        carbs=float(row["carbs"]),
        fat=float(row["fat"]),
        servings_per_container=float(row.get("servings_per_container") or 1),
        protein_per_dollar=float(row.get("protein_per_dollar") or 0),
        category=str(row.get("category") or "Other"),
    )

# main engine using linear programming to maximize protein while staying under budget, meeting minimum calorie req, and maintaining variety!
class OptimizationEngine:
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ) -> None:
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY"
        ) or os.getenv("SUPABASE_ANON_KEY")
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            if not self.supabase_url or not self.supabase_key:
                raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
            # did you know you can put this here? yeah me either it probably isn't optimasl but vs isn't giving me an error
            from supabase import create_client

            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client

    def fetch_products(self) -> list[Product]:
        """Fetch all available products from database"""
        response = (
            self.client.table("products").select("*").eq("in_stock", True).execute()
        )
        return [_parse_product(cast(dict[str, Any], row)) for row in response.data]
# Let it be known this is only test, the real version would be actually so much better with XG boost
    def calculate_fitness_score(self, product: Product) -> float:
        # Protein efficiency is the most important (0-50 points)
        protein_score = min(product.protein_per_dollar * 2, 50)

        # Caloric density bonus for bulking (0-20 points)
        calories_per_dollar = (
            product.calories * product.servings_per_container
        ) / max(product.price, 0.01)
        calorie_score = min(calories_per_dollar / 50, 20)

        # Category bonus (0-30 points)
        category_bonuses = {
            "Protein": 30,
            "Dairy": 20,
            "Legumes": 25,
            "Grains": 15,
            "Produce": 10,
            "Snacks": 5,
            "Pantry": 5,
        }
        category_score = category_bonuses.get(product.category, 10)

        return protein_score + calorie_score + category_score

    def get_selection_reason(self, product: Product, score: float) -> str: 
                            # Takes a product object(self, product:) and a floating-point score(Product, score:) as input and returns a string as output (-> str:) neat.
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

    def optimize(
        self,
        budget: float,
        calorie_target: int,
        protein_target: Optional[int] = None,
        max_per_product: int = 3,
        products: Optional[list[Product]] = None,
    ) -> OptimizationResult:
        # Fetch products if not provided
        # Anytime I have to reorganize fetch i play with Mandy
        if products is None:
            products = self.fetch_products()

        if not products:
            return OptimizationResult(
                success=False,
                items=[],
                total_cost=0,
                total_protein=0,
                total_calories=0,
                budget=budget,
                calorie_target=calorie_target * 7,
                status="No products available",
            )

        # Weekly targets
        weekly_calories = calorie_target * 7
        weekly_protein = (protein_target or 150) * 7

        # Calculate fitness scores
        scores = {p.id: self.calculate_fitness_score(p) for p in products}

        # Create the optimization problem
        prob = LpProblem("GroceryOptimization", LpMaximize)

        # Decision variables: how many of each product to buy
        product_vars = {
            p.id: LpVariable(
                f"qty_{p.id}", lowBound=0, upBound=max_per_product, cat="Integer"
            )
            for p in products
        }

        # Objective: Maximize total protein (weighted by fitness score)
        prob += lpSum(
            product_vars[p.id] * p.total_protein * (scores[p.id] / 100)
            for p in products
        ), "WeightedProtein"

        # Constraint 1: Stay under budget
        prob += (
            lpSum(product_vars[p.id] * p.price for p in products) <= budget,
            "Budget",
        )

        # Constraint 2: Meet minimum calories (within 10%)
        prob += (
            lpSum(product_vars[p.id] * p.total_calories for p in products)
            >= weekly_calories * 0.9,
            "MinCalories",
        )

        # Constraint 3: Don't exceed calories too much (within 20%)
        prob += (
            lpSum(product_vars[p.id] * p.total_calories for p in products)
            <= weekly_calories * 1.2,
            "MaxCalories",
        )

        # Constraint 4: Minimum protein target
        prob += (
            lpSum(product_vars[p.id] * p.total_protein for p in products)
            >= weekly_protein * 0.8,
            "MinProtein",
        )

        # Constraint 5: Require at least one protein source
        protein_products = [p for p in products if p.category == "Protein"]
        if protein_products:
            prob += (
                lpSum(product_vars[p.id] for p in protein_products) >= 1,
                "AtLeastOneProtein",
            )

        # Constraint 6: Require some variety (at least 5 different items)
        has_product = {
            p.id: LpVariable(f"has_{p.id}", cat="Binary") for p in products
        }
        for p in products:
            prob += product_vars[p.id] <= max_per_product * has_product[p.id]
        prob += lpSum(has_product.values()) >= 5, "MinVariety"

        # 6-7 lollllllllllllllllllllllllllllllllllllllllll solve
        prob.solve()

        if LpStatus[prob.status] != "Optimal":
            return OptimizationResult(
                success=False,
                items=[],
                total_cost=0,
                total_protein=0,
                total_calories=0,
                budget=budget,
                calorie_target=weekly_calories,
                status=f"Optimization failed: {LpStatus[prob.status]}",
            )

        # Extract results
        items: list[BasketItem] = []
        total_cost = 0.0
        total_protein = 0.0
        total_calories = 0

        for p in products:
            qty = int(lp_value(product_vars[p.id]) or 0) # type: ignore[arg-type]
            if qty > 0:
                score = scores[p.id]
                item = BasketItem(
                    product=p,
                    quantity=qty,
                    fitness_score=score,
                    selection_reason=self.get_selection_reason(p, score),
                )
                items.append(item)
                total_cost += item.total_price
                total_protein += item.total_protein
                total_calories += item.total_calories

        return OptimizationResult(
            success=True,
            items=items,
            total_cost=total_cost,
            total_protein=total_protein,
            total_calories=total_calories,
            budget=budget,
            calorie_target=weekly_calories,
            status="Optimal solution found",
        )


# CLI Interface for testing

if __name__ == "__main__":
    import sys

    # Default parameters
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 75.0
    calories = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

    print("\n🛒 Fit-Econ Optimizer")
    print(f"   Budget: ${budget:.2f}")
    print(f"   Daily Calories: {calories}")
    print("   Optimizing...\n")

    engine = OptimizationEngine()

    try:
        result = engine.optimize(budget=budget, calorie_target=calories)

        if result.success:
            data = result.to_dict()

            print("=" * 60)
            print("✅ OPTIMIZATION COMPLETE")
            print("=" * 60)
            print("\n📊 Summary:")
            print(f"   Total Cost: ${data['summary']['total_cost']:.2f} ({data['summary']['budget_utilization']})")
            print(f"   Total Protein: {data['summary']['total_protein']:.0f}g/week")
            print(f"   Total Calories: {data['summary']['total_calories']:,}/week ({data['summary']['calorie_achievement']})")

            print(f"\n🛒 Your Optimal Basket ({len(data['items'])} items):")
            print("-" * 60)

            for item in data["items"]:
                print(f"\n   {item['name']}")
                print(f"      Qty: {item['quantity']} × ${item['unit_price']:.2f} = ${item['total_price']:.2f}")
                print(f"      Protein: {item['total_protein']:.0f}g | Calories: {item['total_calories']}")
                print(f"      Score: {item['fitness_score']:.0f} - {item['reason']}")

            print("\n" + "=" * 60)

        else:
            print(f"❌ Optimization failed: {result.status}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you've set SUPABASE_URL and SUPABASE_KEY in your .env file")