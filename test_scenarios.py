from test_optimizer import optimize, PRODUCTS, get_qty  # my beautiful helper function doing something good
from pulp import LpStatus
import pulp


def run_scenario(name: str, budget: float, daily_cal: int, daily_prot: int) -> None:
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print(f"   Budget: ${budget} | Calories: {daily_cal}/day | Protein: {daily_prot}g/day")
    print("=" * 60)

    prob, qty, _ = optimize(budget, daily_cal, daily_prot)

    if LpStatus[prob.status] != "Optimal":
        print(f"   ❌ {LpStatus[prob.status]}")
        return

    total_cost = sum(p.price * get_qty(qty[p.id]) for p in PRODUCTS)
    total_protein = sum(p.total_protein * get_qty(qty[p.id]) for p in PRODUCTS)
    total_cal = sum(p.total_calories * get_qty(qty[p.id]) for p in PRODUCTS)
    items = [(p, get_qty(qty[p.id])) for p in PRODUCTS if get_qty(qty[p.id]) > 0]

    print("\n   ✅ OPTIMAL SOLUTION:")
    print(f"   Cost: ${total_cost:.2f} | Protein: {total_protein:.0f}g/wk | Calories: {total_cal:,}/wk")
    print(f"\n   Items ({len(items)}):")
    for p, q in sorted(items, key=lambda x: x[0].protein_per_dollar, reverse=True):
        print(f"      {q}× {p.name[:35]:<35} ${p.price*q:>6.2f}  {p.total_protein*q:>5.0f}g protein")


# Suppress solver output
if pulp.LpSolverDefault is not None:
    pulp.LpSolverDefault.msg = False

print("\n" + "🧪 CUENTA MULTI-SCENARIO TEST ".center(60, "="))

run_scenario("Tight Budget Student", 40, 1800, 100)
run_scenario("Standard Fitness", 75, 2000, 150)
run_scenario("Bulk Season", 100, 2800, 200)
run_scenario("Competition Prep", 60, 1600, 180)

print("\n" + "=" * 60)
print("✅ All scenarios complete!")
print("=" * 60 + "\n")