-- ============================================================================
-- FIT-ECON MVP: Complete Schema
-- ============================================================================

-- PG VECTOR IMPLEMENTED ALREADY BECAUSE WHY WOULD WE EVER USE MYSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- PRODUCTS TABLE (ALDI inventory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    
    calories INTEGER NOT NULL DEFAULT 0,
    protein DECIMAL(10,1) NOT NULL DEFAULT 0,
    carbs DECIMAL(10,1) NOT NULL DEFAULT 0,
    fat DECIMAL(10,1) NOT NULL DEFAULT 0,
    fiber DECIMAL(10,1) DEFAULT 0,
    
    -- Serving info
    serving_size TEXT,
    servings_per_container DECIMAL(10,1) DEFAULT 1,
    
    -- Computed efficiency scores (for quick sorting)
    protein_per_dollar DECIMAL(10,2) GENERATED ALWAYS AS (
        CASE WHEN price > 0 THEN (protein * servings_per_container) / price ELSE 0 END
    ) STORED,
    calories_per_dollar DECIMAL(10,2) GENERATED ALWAYS AS (
        CASE WHEN price > 0 THEN (calories * servings_per_container) / price ELSE 0 END
    ) STORED,
    
    -- Metadata
    category TEXT,
    store TEXT DEFAULT 'ALDI',
    in_stock BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
--- BORING Stuff but creatiung user tables, this entire thing is boring I can see the sunrise
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    
    -- Goals
    weekly_budget DECIMAL(10,2) DEFAULT 75.00,
    daily_calories INTEGER DEFAULT 2000,
    protein_goal INTEGER DEFAULT 150,  -- grams per day
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- OPTIMIZED BASKETS
-- ============================================================================
CREATE TABLE IF NOT EXISTS baskets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Input parameters (what was requested)
    budget DECIMAL(10,2) NOT NULL,
    calorie_target INTEGER NOT NULL,
    protein_target INTEGER,
    
    -- Output summary
    total_cost DECIMAL(10,2),
    total_calories INTEGER,
    total_protein DECIMAL(10,1),
    
    -- Status
    status TEXT DEFAULT 'pending',  -- pending, optimizing, complete, failed
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- BASKET ITEMS (products in each basket)
-- ============================================================================
CREATE TABLE IF NOT EXISTS basket_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    
    quantity INTEGER NOT NULL DEFAULT 1,
    
    -- Snapshot of product data at time of optimization
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) GENERATED ALWAYS AS (unit_price * quantity) STORED,
    
    -- Why this item was chosen (for UI explanation)
    fitness_score DECIMAL(10,2),  -- XGBoost output
    selection_reason TEXT,         -- "High protein/$ ratio", "Budget filler", etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ROW LEVEL SECURITY AS A MEASURE THAT WILL GET IMPLEMENTED. 
-- ============================================================================

-- Products: Everyone can read (it's a product catalog)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view products" ON products FOR SELECT USING (true);

-- Profiles: Users only see their own
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own profile" ON profiles FOR ALL USING (auth.uid() = id);

-- Baskets: Users only see their own
ALTER TABLE baskets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own baskets" ON baskets FOR ALL USING (auth.uid() = user_id);

-- Basket Items: Access via parent basket
ALTER TABLE basket_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own basket items" ON basket_items FOR ALL 
USING (EXISTS (
    SELECT 1 FROM baskets WHERE baskets.id = basket_items.basket_id AND baskets.user_id = auth.uid()
));

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_protein_per_dollar ON products(protein_per_dollar DESC);
CREATE INDEX IF NOT EXISTS idx_baskets_user_id ON baskets(user_id);
CREATE INDEX IF NOT EXISTS idx_basket_items_basket_id ON basket_items(basket_id);

-- ============================================================================
-- AUTO-CREATE PROFILE ON SIGNUP
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
