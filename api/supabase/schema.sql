-- ============================================================================
-- CUENTA MVP: Complete Schema
-- I am so excited for this to come alive. The moment I commit a supabase structure my god I will be so happy.
-- ============================================================================

-- PG VECTOR IMPLEMENTED ALREADY BECAUSE WHY WOULD WE EVER USE MYSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- STORES! this is where a bulk of my data will be essentially created table wise
-- Creating this gave me the idea to aggresively cache to workaround the tough and strict api 
-- ============================================================================

CREATE TABLE STORES (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL, -- "Target", "Aldi"
    store_id TEXT, -- External ID (Target store_id like "3375")
    zip_code TEXT,
    city TEXT,
    state TEXT,
    address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    cached_at TIMESTAMPTZ DEFAULT NOW()
);  

-- ====================================================================================
-- Product table!!
-- ====================================================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identity
    name TEXT NOT NULL,
    brand TEXT,
    barcode TEXT,
    external_id TEXT, -- TCIN for Target, SKU for Aldi
    store_id UUID REFERENCES stores(id),   -- Which store this product is from
    
    -- Price
    price FLOAT NOT NULL,
    unit_price TEXT, -- "$0.45/oz" etc etc 
    
    -- Nutrition (per serving)
    calories INTEGER DEFAULT 0,
    protein FLOAT DEFAULT 0,
    carbs FLOAT DEFAULT 0,
    fat FLOAT DEFAULT 0,
    fiber FLOAT DEFAULT 0,
    
    -- Serving info
    serving_size TEXT,
    servings_per_container FLOAT DEFAULT 1,
    
    -- Computed (stored for fast queries)
    protein_per_dollar FLOAT GENERATED ALWAYS AS (
        CASE WHEN price > 0 THEN (protein * servings_per_container) / price ELSE 0 END
    ) STORED,
    protein_per_100cal FLOAT GENERATED ALWAYS AS (
        CASE WHEN calories > 0 THEN (protein / calories) * 100 ELSE 0 END
    ) STORED,
    
    -- Classification
    category TEXT,
    tags TEXT[], -- {'meat', 'gluten', 'dairy'}, helpful identifiers 
        
    -- Meta deta 
    image_url TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- USER PROFILES
-- ============================================================================
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    zip_code TEXT,  -- For store recommendations
    dietary_restrictions TEXT[], -- {'vegan', 'gluten-free'}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- OPTIMIZATION HISTORY (saved baskets)
-- ============================================================================
CREATE TABLE baskets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
-- Input parameters
    budget FLOAT,
    daily_calories INTEGER,
    daily_protein INTEGER,
    diet TEXT,  -- 'vegan', 'keto', etc
    allergies TEXT[],
-- making comments in sql is so odd but I like the - so I move along
    -- Results
    total_cost FLOAT,
    total_protein FLOAT,
    total_calories FLOAT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE basket_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID REFERENCES baskets(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    
-- Snapshot at time of optimization (prices change)
    price_at_time FLOAT,
    protein_at_time FLOAT,
    calories_at_time FLOAT
);

-- ============================================================================
-- RECIPES (Spoonacular cache)
-- ============================================================================
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spoonacular_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    image_url TEXT,
    prep_minutes INTEGER,
    servings INTEGER,
    calories_per_serving INTEGER,
    protein_per_serving FLOAT,
    carbs_per_serving FLOAT,
    fat_per_serving FLOAT,
    cost_per_serving FLOAT,
    ingredients JSONB,  -- Stores the raw Json ingredient list
    cached_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MEAL PLANS
-- ============================================================================
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    week_start DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meal_plan_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id UUID REFERENCES recipes(id),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')) -- Good idea my friend recommendaed, this can play into the ingredient preferences i'm planning on adding son
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_protein_per_dollar ON products(protein_per_dollar DESC);
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_products_external_id ON products(external_id);
CREATE INDEX idx_baskets_user ON baskets(user_id);
CREATE INDEX idx_basket_items_basket ON basket_items(basket_id);
CREATE INDEX idx_stores_zip ON stores(zip_code);

-- ============================================================================
-- RLS because this is still a feature i really want to implement eventually especially given my direct user login thing I want to implement 
-- ============================================================================

-- Products: public read
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Products are public" ON products FOR SELECT USING (true);
CREATE POLICY "Service role can manage products" ON products FOR ALL 
    USING (auth.role() = 'service_role');

-- Stores: public read
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Stores are public" ON stores FOR SELECT USING (true);

-- Recipes: public read (cached from API)
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Recipes are public" ON recipes FOR SELECT USING (true);

-- Profiles: users own their own
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own their profile" ON profiles 
    FOR ALL USING (auth.uid() = id);

-- Baskets: users own their own data- plays into the whole "wanting to own my own data", eventually releasing a "request your own data" thing considering we're saving it
ALTER TABLE baskets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own their baskets" ON baskets 
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE basket_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access their basket items" ON basket_items
    FOR ALL USING (
        basket_id IN (SELECT id FROM baskets WHERE user_id = auth.uid())
    );

-- Meal plans: users own their own - same thiog
ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own their meal plans" ON meal_plans 
    FOR ALL USING (auth.uid() = user_id);

ALTER TABLE meal_plan_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access their meal plan items" ON meal_plan_items
    FOR ALL USING (
        meal_plan_id IN (SELECT id FROM meal_plans WHERE user_id = auth.uid())
    );

-- ============================================================================
-- INGREDIENT PREFERENCES (picky eater feature for later)
-- ============================================================================
CREATE TABLE ingredient_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ingredient TEXT NOT NULL, -- normalized: "cilantro", "shrimp"
    rating INTEGER CHECK (rating BETWEEN 1 AND 10),
    -- 1-3: hate/avoid, 4-6: neutral/okay, 7-10: love/prefer, will make this something that's well known, although would haev to think of ways to add this given my limited screen real estate. will come back. 
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, ingredient) -- new table! 
);

CREATE INDEX idx_preferences_user ON ingredient_preferences(user_id);
CREATE INDEX idx_preferences_ingredient ON ingredient_preferences(ingredient);
CREATE INDEX idx_preferences_rating ON ingredient_preferences(rating);

ALTER TABLE ingredient_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own their preferences" ON ingredient_preferences 
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- RECIPE CACHE (Spoonacular responses)
-- ============================================================================
CREATE TABLE recipe_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
-- Cache key (sorted ingredients or search query)
    cache_key TEXT UNIQUE NOT NULL,
    cache_type TEXT CHECK (cache_type IN ('ingredients', 'search', 'id')),
    
-- Cached response
    recipes JSONB NOT NULL, -- Full API response 
    recipe_count INTEGER,
    
-- Metadata
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    hit_count INTEGER DEFAULT 0
);

CREATE INDEX idx_recipe_cache_key ON recipe_cache(cache_key);
CREATE INDEX idx_recipe_cache_expires ON recipe_cache(expires_at);

-- Public read (no auth needed for cached recipes aka easy light work)
ALTER TABLE recipe_cache ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Recipe cache is public" ON recipe_cache FOR SELECT USING (true);
CREATE POLICY "Service role manages cache" ON recipe_cache FOR ALL 
    USING (auth.role() = 'service_role');

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-create profile on signup
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

-- Update last_updated on product changes
CREATE OR REPLACE FUNCTION update_product_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER product_updated
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_product_timestamp();