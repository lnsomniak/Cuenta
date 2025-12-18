# Cuenta 🧾

**Grocery Intelligence** — Options, not decisions.

Cuenta optimizes your grocery shopping by finding the most protein efficient products within your budget. Built for fitness focused students and budget conscious shoppers.

![Receipt UI](https://img.shields.io/badge/UI-Receipt%20Style-black)
![Python](https://img.shields.io/badge/Backend-FastAPI-009688)
![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E)

## What It Does

- **Protein Efficiency Metrics**: See `g/$` (protein per dollar) and `g/100cal` (protein per 100 calories) for every product
- **Budget Optimization**: Greedy algorithm finds the best protein sources within your weekly budget
- **Diet Filtering**: Vegan, Vegetarian, Pescatarian, Keto support
- **Allergy Exclusions**: Filter out Dairy, Eggs, Gluten, Nuts, Soy, Fish
- **Real Store Data**: 356+ products scraped from Kroger with live pricing
- **Recipe Suggestions**: Get meal ideas based on your optimized basket (Spoonacular API)
- **USDA Fallback**: Live data actively being cached and recovered to avoid API fatigue!!!!

## Live Data

| Store | Products | Top g/$ |
|-------|----------|---------|
| Kroger - Houston | 356 | 29.3 (Chunk Light Tuna) |

## 🏗️ Architecture

```python
Cuenta/
├── api/
│   ├── main.py              # FastAPI backend
│   └── scrapers/
│       ├── kroger.py        # Kroger API scraper
│       ├── kroger_bulk_scrape.py  # Bulk product scraper
│       └── nutrition_fallback.py  # USDA nutrition lookup
├── web/
│   ├── app/
│   │   ├── page.tsx         # Main receipt UI
│   │   └── browse/          # Product catalog
│   └── lib/
│       └── supabase.ts      # Database client
└── supabase/
    ├── schema.sql           # Database schema
    └── seed.sql             # Initial data
```

### Environment Variables

```env
# Backend (.env)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SPOONACULAR_API_KEY=your-spoonacular-key
KROGER_CLIENT_ID=your-kroger-client-id
KROGER_CLIENT_SECRET=your-kroger-secret
USDA_API_KEY=your-usda-key

# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🔧 Key Features

### Optimization Algorithm

Greedy selection prioritizing protein-per-dollar:

1. Fetch products from Supabase (filtered by diet/allergies)
2. Score each product by `total_protein / price`
3. Select highest scoring products until budget exhausted, with percentage provided of total use and remainder
4. Return basket with efficiency metrics

### Scraper Pipeline

```python
Kroger API → Product Data → USDA Enrichment → Supabase
     ↓              ↓              ↓
  Prices      Basic Nutrition   Full Macros
```

### Receipt UI

Distinctive receipt-style interface with:

- Torn paper edges
- Monospace typography
- Barcode generation
- Real time efficiency metrics

## 📈 Sample Output

```bash
BASKET [5]
─────────────────────────────────
KROGER CHUNK LIGHT TUNA        $0.99
1x @ $0.99                     #001
29g protein         29.3 g/$ 32.2 g/c

KROGER GREEK YOGURT            $0.89
1x @ $0.89                     #002
17g protein         19.1 g/$ 17.0 g/c
─────────────────────────────────
TOTAL                         $74.39
BUDGET UTILIZATION            99.2%
```

## 🛣️ Roadmap

- [x] Kroger scraper with USDA enrichment
- [x] Supabase integration
- [x] Diet/allergy filtering
- [x] Receipt-style UI
- [ ] Target scraper (API blocking issues)
- [ ] Geolocation for nearest stores
- [ ] Price history tracking
- [ ] Mobile app

## 👤 Author

**Sergio** — Poli Sci @ University of Houston '27

---

*The data is yours. The decision is too. Visca Barca*
