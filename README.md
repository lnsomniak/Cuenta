# 🛒 Fit-Econ MVP

**AI-optimized grocery lists for your fitness goals.**

Input your budget and macro goals → Get the optimal ALDI(and later more) shopping list.

## Usage

1. Enter your **weekly budget** (e.g., $75)
2. Enter your **daily calorie goal** (e.g., 2000)
3. Enter your **daily protein goal** (e.g., 150g)
4. Click **"Optimize My Basket"**

The system will use Linear Programming to find the optimal combination of products that:

- Maximizes protein intake
- Stays under your budget
- Meets your calorie target (±10%)
- Maintains variety (at least 5 different items)

---

## How It Works

### The Optimization Engine

The engine uses **Linear Programming** (via PuLP) to solve:

```python
Maximize: Σ (quantity[i] × protein[i] × fitness_score[i])

Subject to:
  Σ (quantity[i] × price[i]) ≤ budget
  Σ (quantity[i] × calories[i]) ≥ 0.9 × weekly_calorie_target
  Σ (quantity[i] × calories[i]) ≤ 1.2 × weekly_calorie_target
  Σ (quantity[i] × protein[i]) ≥ 0.8 × weekly_protein_target
  quantity[i] ∈ {0, 1, 2, 3}  (max 3 of any product)
  variety ≥ 5 different products
```

### Fitness Score

Each product gets a "fitness score" (0-100) based on:

- **Protein per dollar** (0-50 points) - The only metric everyone follows
- **Caloric density** (0-20 points) - Good for bulking
- **Category bonus** (0-30 points) - Protein sources score higher

In a full version, this would be an **XGBoost model** trained on user preferences and outcomes.

---

## API Endpoints

### `POST /api/optimize`

Optimize a grocery basket.

**Request:**

```json
{
  "budget": 75.0,
  "daily_calories": 2000,
  "daily_protein": 150
}
```

**Response:**

```json
{
  "success": true,
  "summary": {
    "total_cost": 72.45,
    "total_protein": 1050,
    "total_calories": 14200,
    "budget_utilization": "96.6%"
  },
  "items": [
    {
      "name": "Kirkwood Chicken Breast (3 lb)",
      "quantity": 2,
      "total_price": 17.98,
      "total_protein": 624,
      "fitness_score": 85,
      "reason": "Exceptional protein value (34.7g/$)"
    }
  ]
}
```

### `GET /api/products`

List all available products sorted by protein efficiency.

---

## Next Steps

This MVP proves the core value prop. To make it production-ready:

- [ ] **User auth** - Save preferences across sessions
- [ ] **XGBoost model** - Replace heuristic scoring with ML
- [ ] **Real ALDI data** - Scraper or API integration
- [ ] **iOS app** - HealthKit integration for biometric adjustments
- [ ] **RAG coach** - PubMed-powered fitness advice
- [ ] **RLS Implementation** - True end to end enhanced data security & privacy

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | Python, FastAPI, PuLP |
| Database | Supabase (PostgreSQL + RLS) |
| Optimization | Linear Programming |

---
