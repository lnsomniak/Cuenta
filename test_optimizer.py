from typing import cast
from dataclasses import dataclass
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus, value as lp_value
# this is my removal of the need for a database for now, just hardcoded logic 

def get_qty(var: LpVariable) -> int:
    val = lp_value(var)
    if val is None:
        return 0
    return int(cast(float, val)) # done trying to fix this it works leave me alone. 

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


# Mock ALDI products (subset of seed data)
PRODUCTS = [
    Product("1", "Kirkwood Chicken Breast (3 lb)", 8.99, 120, 26, 12, "Protein"),
    Product("2", "Kirkwood Chicken Thighs (3 lb)", 5.99, 180, 22, 12, "Protein"),
    Product("3", "Never Any! Ground Turkey 93/7", 5.49, 170, 21, 4, "Protein"),
    Product("4", "Fresh Ground Beef 80/20", 5.99, 290, 19, 4, "Protein"),
    Product("5", "Fremont Fish Market Tilapia (2 lb)", 7.99, 110, 23, 8, "Protein"),
    Product("6", "Goldhen Large Eggs (18 ct)", 3.29, 70, 6, 18, "Dairy"),
    Product("7", "Goldhen Large Eggs (36 ct)", 5.99, 70, 6, 36, "Dairy"),
    Product("8", "Friendly Farms Greek Yogurt (32 oz)", 4.49, 100, 17, 4, "Dairy"),
    Product("9", "Friendly Farms Cottage Cheese (24 oz)", 2.99, 110, 13, 6, "Dairy"),
    Product("10", "Happy Farms String Cheese (24 ct)", 6.99, 80, 7, 24, "Dairy"),
    Product("11", "Simply Nature Brown Rice (2 lb)", 3.29, 170, 4, 18, "Grains"),
    Product("12", "Jasmine Rice (5 lb)", 5.99, 160, 3, 45, "Grains"),
    Product("13", "Barilla Pasta (16 oz)", 1.29, 200, 7, 8, "Grains"),
    Product("14", "Millville Old Fashioned Oats (42 oz)", 2.99, 150, 5, 30, "Grains"),
    Product("15", "Bananas (bunch)", 1.49, 105, 1, 7, "Produce"),
    Product("16", "Sweet Potatoes (3 lb bag)", 2.99, 112, 2, 5, "Produce"),
    Product("17", "Baby Spinach (16 oz)", 3.99, 7, 1, 16, "Produce"),
    Product("18", "Frozen Broccoli (12 oz)", 1.29, 30, 3, 3, "Produce"),
    Product("19", "Dakota's Pride Black Beans (15 oz)", 0.79, 110, 7, 3.5, "Legumes"),
    Product("20", "Simply Nature Lentils (16 oz)", 2.49, 170, 12, 13, "Legumes"),
    Product("21", "Southern Grove Peanut Butter (28 oz)", 3.49, 190, 7, 26, "Legumes"),
    Product("22", "Elevation Protein Bars (5 ct)", 5.99, 200, 20, 5, "Snacks"),
    Product("23", "Southern Grove Almonds (16 oz)", 5.99, 170, 6, 16, "Snacks"),
]


def calculate_fitness_score(product: Product) -> float:
    # Protein efficiency (0-50 points)
    protein_score = min(product.protein_per_dollar * 2, 50)
    
    # Caloric density (0-20 points)
    cal_per_dollar = product.total_calories / product.price
    calorie_score = min(cal_per_dollar / 50, 20)
    
    # Category bonus (0-30 points)
    bonuses = {"Protein": 30, "Dairy": 20, "Legumes": 25, "Grains": 15, "Produce": 10, "Snacks": 5}
    category_score = bonuses.get(product.category, 10)
    
    return protein_score + calorie_score + category_score


def optimize(budget: float, daily_calories: int, daily_protein: int = 150, max_per_product: int = 3):
    weekly_calories = daily_calories * 7
    weekly_protein = daily_protein * 7 # 6 7 LOLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL whydidithinkofthis.
    
    # 1 Calculate scores
    scores = {p.id: calculate_fitness_score(p) for p in PRODUCTS}
    
    # 2 Creates problem 
    prob = LpProblem("GroceryOptimization", LpMaximize)
    
    # 3 Decides variables
    qty = {p.id: LpVariable(f"qty_{p.id}", lowBound=0, upBound=max_per_product, cat="Integer") for p in PRODUCTS}
    
    # 4 Maximizes weighted protein
    prob += lpSum(qty[p.id] * p.total_protein * (scores[p.id] / 100) for p in PRODUCTS)
    
    # 5 All the constraints which is a wonderful work around btw.
    prob += lpSum(qty[p.id] * p.price for p in PRODUCTS) <= budget, "Budget"
    prob += lpSum(qty[p.id] * p.total_calories for p in PRODUCTS) >= weekly_calories * 0.9, "MinCal"
    prob += lpSum(qty[p.id] * p.total_calories for p in PRODUCTS) <= weekly_calories * 1.2, "MaxCal"
    prob += lpSum(qty[p.id] * p.total_protein for p in PRODUCTS) >= weekly_protein * 0.8, "MinProtein"
    
    # 6 variety
    has = {p.id: LpVariable(f"has_{p.id}", cat="Binary") for p in PRODUCTS}
    for p in PRODUCTS:
        prob += qty[p.id] <= max_per_product * has[p.id]
    prob += lpSum(has.values()) >= 5, "MinVariety"
    
    # 7 LOLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL solve
    prob.solve()
    
    return prob, qty, scores


def main():
    budget = 75.0
    daily_calories = 2000
    daily_protein = 150
    
    print("\n" + "=" * 70)
    print("🛒 FIT-ECON OPTIMIZER TEST")
    print("=" * 70)
    print(f"\n📋 Input Parameters:") 
    print(f"   Budget:         ${budget:.2f}/week")
    print(f"   Calorie Target: {daily_calories}/day ({daily_calories * 7:,}/week)")
    print(f"   Protein Target: {daily_protein}g/day ({daily_protein * 7:,}g/week)")
    
    print("\n⚙️  Running Linear Programming optimization...")
    prob, qty, scores = optimize(budget, daily_calories, daily_protein)
    
    if LpStatus[prob.status] != "Optimal":
        print(f"\n❌ Optimization failed: {LpStatus[prob.status]}")
        return
    
    print(f"✅ Solution found: {LpStatus[prob.status]}")
    
    # empty lists for results
    results = []
    total_cost = 0
    total_protein = 0
    total_calories = 0
    
    for p in PRODUCTS:
        q = get_qty(qty[p.id])
        if q > 0:
            cost = p.price * q
            prot = p.total_protein * q
            cals = p.total_calories * q
            results.append((p, q, cost, prot, cals, scores[p.id]))
            total_cost += cost
            total_protein += prot
            total_calories += cals
    
    # Sorts by fitness score end of all
    results.sort(key=lambda x: x[5], reverse=True)
    
    print("\n" + "=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    print(f"\n💰 Summary:")
    print(f"   Total Cost:     ${total_cost:.2f} ({total_cost/budget*100:.1f}% of budget)")
    print(f"   Total Protein:  {total_protein:.0f}g/week ({total_protein/7:.0f}g/day)")
    print(f"   Total Calories: {total_calories:,}/week ({total_calories//7:,}/day)")
    
    print(f"\n🛒 Optimized Basket ({len(results)} items):")
    print("-" * 70)
    
    for p, q, cost, prot, cals, score in results:
        print(f"\n   [{score:.0f}] {p.name}")
        print(f"       {q}× @ ${p.price:.2f} = ${cost:.2f}")
        print(f"       → {prot:.0f}g protein | {cals:,} calories")
        print(f"       → {p.protein_per_dollar:.1f}g protein/$ | Category: {p.category}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE - Core optimization logic works!")
    print("=" * 70)
    
    # Shows protein efficiency ranking
    print("\n📈 Top Protein-Per-Dollar Products in Selection:")
    for p, q, cost, prot, cals, score in sorted(results, key=lambda x: x[0].protein_per_dollar, reverse=True)[:5]:
        print(f"   {p.protein_per_dollar:.1f}g/$ - {p.name}")

# test main
if __name__ == "__main__":
    main()
