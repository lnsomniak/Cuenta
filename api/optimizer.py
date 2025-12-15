from typing import cast, Optional
from dataclasses import dataclass, field
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus, value as lp_value, PULP_CBC_CMD


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
    servings: float
    category: str
    
    @property
    def total_calories(self) -> int:
        return int(self.calories * self.servings)
    
    @property
    def total_protein(self) -> float:
        return self.protein * self.servings
    
    @property
    def protein_per_dollar(self) -> float:
        return self.total_protein / self.price if self.price > 0 else 0
    
    @property
    def protein_per_100cal(self) -> float:
        return (self.total_protein / self.total_calories * 100) if self.total_calories > 0 else 0


@dataclass
class OptimizationResult:
    success: bool
    status: str
    summary: dict = field(default_factory=dict)
    items: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "status": self.status,
            "summary": self.summary,
            "items": self.items
        }


# Mock ALDI products with nutrition data
PRODUCTS = [
    # PROTEIN
    Product("1", "Kirkwood Chicken Breast (3 lb)", 8.99, 120, 26, 12, "Protein"),
    Product("2", "Kirkwood Chicken Thighs (3 lb)", 5.99, 180, 22, 12, "Protein"),
    Product("3", "Never Any! Ground Turkey 93/7", 5.49, 170, 21, 4, "Protein"),
    Product("4", "Fresh Ground Beef 80/20", 5.99, 290, 19, 4, "Protein"),
    Product("5", "Fremont Fish Market Tilapia (2 lb)", 7.99, 110, 23, 8, "Protein"),
    Product("6", "Salmon Fillets (1 lb)", 8.99, 208, 20, 4, "Protein"),
    Product("7", "Fit & Active Canned Tuna (5 oz)", 0.99, 100, 25, 1, "Protein"),
    
    # DAIRY
    Product("10", "Goldhen Large Eggs (18 ct)", 3.29, 70, 6, 18, "Dairy"),
    Product("11", "Goldhen Large Eggs (36 ct)", 5.99, 70, 6, 36, "Dairy"),
    Product("12", "Friendly Farms Greek Yogurt (32 oz)", 4.49, 100, 17, 4, "Dairy"),
    Product("13", "Friendly Farms Cottage Cheese (24 oz)", 2.99, 110, 13, 6, "Dairy"),
    Product("14", "Happy Farms String Cheese (24 ct)", 6.99, 80, 7, 24, "Dairy"),
    Product("15", "Oikos Pro Yogurt Drink (7 oz)", 1.89, 140, 23, 1, "Dairy"),
    Product("16", "Friendly Farms Milk 2% (1 gal)", 3.19, 120, 8, 16, "Dairy"),
    
    # GRAINS
    Product("20", "Simply Nature Brown Rice (2 lb)", 3.29, 170, 4, 18, "Grains"),
    Product("21", "Jasmine Rice (5 lb)", 5.99, 160, 3, 45, "Grains"),
    Product("22", "Barilla Pasta (16 oz)", 1.29, 200, 7, 8, "Grains"),
    Product("23", "Millville Old Fashioned Oats (42 oz)", 2.99, 150, 5, 30, "Grains"),
    Product("24", "L'Oven Fresh Whole Wheat Bread", 1.49, 80, 4, 20, "Grains"),
    Product("25", "Simply Nature Quinoa (16 oz)", 4.29, 160, 6, 10, "Grains"),
    
    # PRODUCE
    Product("30", "Bananas (bunch ~3 lb)", 1.49, 105, 1, 7, "Produce"),
    Product("31", "Sweet Potatoes (3 lb bag)", 2.99, 112, 2, 5, "Produce"),
    Product("32", "Baby Spinach (16 oz)", 3.99, 7, 1, 16, "Produce"),
    Product("33", "Frozen Broccoli (12 oz)", 1.29, 30, 3, 3, "Produce"),
    Product("34", "Avocados (4 ct)", 3.29, 160, 2, 4, "Produce"),
    
    # LEGUMES
    Product("40", "Dakota's Pride Black Beans (15 oz)", 0.79, 110, 7, 3.5, "Legumes"),
    Product("41", "Dakota's Pride Chickpeas (15 oz)", 0.79, 110, 6, 3.5, "Legumes"),
    Product("42", "Simply Nature Lentils (16 oz)", 2.49, 170, 12, 13, "Legumes"),
    Product("43", "Southern Grove Peanut Butter (28 oz)", 3.49, 190, 7, 26, "Legumes"),
    
    # SNACKS
    Product("50", "Elevation Protein Bars (5 ct)", 5.99, 200, 20, 5, "Snacks"),
    Product("51", "Southern Grove Almonds (16 oz)", 5.99, 170, 6, 16, "Snacks"),
    Product("52", "Simply Nature Almond Butter (12 oz)", 4.99, 190, 7, 12, "Snacks"),
]


class OptimizationEngine:    
    def __init__(self):
        self.products = PRODUCTS
    
    def fetch_products(self) -> list[Product]:
        return self.products
    
    def _calculate_fitness_score(self, product: Product) -> float:
        protein_score = min(product.protein_per_dollar * 2, 50)
        
        protein_density_score = min(product.protein_per_100cal * 2, 20)
        
        bonuses = {
            "Protein": 30,
            "Dairy": 20, 
            "Legumes": 25,
            "Grains": 15,
            "Produce": 10,
            "Snacks": 5
        }
        category_score = bonuses.get(product.category, 10)
        
        return protein_score + protein_density_score + category_score
    
    def optimize(
        self,
        budget: float = 75.0,
        calorie_target: int = 2000,
        protein_target: Optional[int] = None,
        max_per_product: int = 3
    ) -> OptimizationResult:
        if protein_target is None:
            protein_target = 150  # Default reasonable target
            
        weekly_calories = calorie_target * 7
        weekly_protein = protein_target * 7
        
        # Calculate fitness scores
        scores = {p.id: self._calculate_fitness_score(p) for p in self.products}
        
        # Create LP problem
        prob = LpProblem("CuentaOptimization", LpMaximize)
        
        # Decision variables: quantity of each product
        qty = {
            p.id: LpVariable(f"qty_{p.id}", lowBound=0, upBound=max_per_product, cat="Integer")
            for p in self.products
        }
        
        # Objective: Maximize weighted protein (protein * fitness_score)
        prob += lpSum(
            qty[p.id] * p.total_protein * (scores[p.id] / 100)
            for p in self.products
        )
        
        # Constraints
        # 1. Budget constraint
        prob += lpSum(qty[p.id] * p.price for p in self.products) <= budget, "Budget"
        
        # 2. Minimum calories (90% of target)
        prob += lpSum(qty[p.id] * p.total_calories for p in self.products) >= weekly_calories * 0.9, "MinCalories"
        
        # 3. Maximum calories (120% of target)
        prob += lpSum(qty[p.id] * p.total_calories for p in self.products) <= weekly_calories * 1.2, "MaxCalories"
        
        # 4. Minimum protein (80% of target)
        prob += lpSum(qty[p.id] * p.total_protein for p in self.products) >= weekly_protein * 0.8, "MinProtein"
        
        # 5. Variety constraint (at least 5 different items)
        has_item = {p.id: LpVariable(f"has_{p.id}", cat="Binary") for p in self.products}
        for p in self.products:
            prob += qty[p.id] <= max_per_product * has_item[p.id]
        prob += lpSum(has_item.values()) >= 5, "MinVariety"
        
        # 6 Solve (suppress output)
        prob.solve(PULP_CBC_CMD(msg=0))
        
        # 7 LOLLLLLLLLLLLLLLLLLLLLLL this is always funny. 
        if LpStatus[prob.status] != "Optimal":
            return OptimizationResult(
                success=False,
                status=f"Optimization failed: {LpStatus[prob.status]}"
            )
        # Extract results
        items = []
        total_cost = 0
        total_protein = 0
        total_calories = 0
         
        for p in self.products:
            q = get_qty(qty[p.id])
            if q > 0:
                item_cost = p.price * q
                item_protein = p.total_protein * q
                item_calories = p.total_calories * q
                
                items.append({
                    "id": p.id,
                    "name": p.name,
                    "quantity": q,
                    "unit_price": p.price,
                    "total_price": round(item_cost, 2),
                    "total_protein": round(item_protein, 1),
                    "total_calories": item_calories,
                    "fitness_score": round(scores[p.id], 1),
                    "reason": f"{p.protein_per_dollar:.1f}g/$ | {p.protein_per_100cal:.1f}g/100cal",
                    "category": p.category
                })
                
                total_cost += item_cost
                total_protein += item_protein
                total_calories += item_calories
        
        # Sort by fitness score
        items.sort(key=lambda x: x["fitness_score"], reverse=True)
        
        # Calculate summary stats
        budget_util = (total_cost / budget * 100) if budget > 0 else 0
        calorie_achieve = (total_calories / weekly_calories * 100) if weekly_calories > 0 else 0
        protein_achieve = (total_protein / weekly_protein * 100) if weekly_protein > 0 else 0
        
        return OptimizationResult(
            success=True,
            status="Optimization complete",
            summary={
                "total_cost": round(total_cost, 2),
                "total_protein": round(total_protein, 1),
                "total_calories": total_calories,
                "budget": budget,
                "calorie_target": weekly_calories,
                "protein_target": weekly_protein,
                "budget_utilization": f"{budget_util:.1f}%",
                "calorie_achievement": f"{calorie_achieve:.1f}%",
                "protein_achievement": f"{protein_achieve:.1f}%"
            },
            items=items
        )


# CLI test
def main():
    print("\n" + "=" * 70)
    print("🧾 CUENTA OPTIMIZER TEST")
    print("=" * 70)
    
    engine = OptimizationEngine()
    
    result = engine.optimize(
        budget=75.0,
        calorie_target=2000,
        protein_target=150,
        max_per_product=3
    )
    
    if not result.success:
        print(f"\n❌ {result.status}")
        return
    
    print(f"\n✅ {result.status}")
    print("\n📊 Summary:")
    print(f"   Cost: ${result.summary['total_cost']:.2f} ({result.summary['budget_utilization']} of budget)")
    print(f"   Protein: {result.summary['total_protein']:.0f}g/week ({result.summary['total_protein']/7:.0f}g/day)")
    print(f"   Calories: {result.summary['total_calories']:,}/week ({result.summary['total_calories']//7:,}/day)")
    
    print(f"\n🛒 Basket ({len(result.items)} items):")
    print("-" * 70)
    
    for item in result.items:
        ppd = item['total_protein'] / item['total_price'] if item['total_price'] > 0 else 0
        ppc = (item['total_protein'] / item['total_calories'] * 100) if item['total_calories'] > 0 else 0
        print(f"\n   {item['name']}")
        print(f"   {item['quantity']}× @ ${item['unit_price']:.2f} = ${item['total_price']:.2f}")
        print(f"   → {item['total_protein']:.0f}g protein | {item['total_calories']:,} cal")
        print(f"   → {ppd:.1f} g/$ | {ppc:.1f} g/100cal | {item['category']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()